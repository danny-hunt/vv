import asyncio
from pathlib import Path
from typing import Dict, AsyncIterator, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from git_ops import GitOperations

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(self, base_path: str, git_ops: Optional['GitOperations'] = None):
        self.base_path = Path(base_path)
        self.running_agents: Dict[int, asyncio.subprocess.Process] = {}
        self.agent_outputs: Dict[int, asyncio.Queue] = {}
        self.agent_prompts: Dict[int, str] = {}  # Store user prompts for commit messages
        self.git_ops = git_ops
    
    def get_pane_path(self, pane_id: int) -> Path:
        """Get the path to a pane's webapp directory."""
        return self.base_path / str(pane_id)
    
    def is_agent_running(self, pane_id: int) -> bool:
        """Check if an agent is currently running for a pane."""
        return pane_id in self.running_agents and self.running_agents[pane_id].returncode is None
    
    async def start_agent(self, pane_id: int, user_prompt: str) -> Dict[str, str]:
        """
        Start a cursor-agent run for the given pane.
        
        Args:
            pane_id: The pane ID (1-6)
            user_prompt: The user's prompt for the agent
        
        Returns:
            Dict with status and message
        """
        if self.is_agent_running(pane_id):
            return {
                "status": "error",
                "message": "Agent already running for this pane"
            }
        
        pane_path = self.get_pane_path(pane_id)
        
        if not pane_path.exists():
            return {
                "status": "error",
                "message": f"Pane directory {pane_path} does not exist"
            }
        
        try:
            # Create output queue for this pane
            self.agent_outputs[pane_id] = asyncio.Queue()
            
            # Store the user prompt for commit message
            self.agent_prompts[pane_id] = user_prompt
            
            # Start cursor-agent as subprocess
            process = await asyncio.create_subprocess_exec(
                'cursor-agent',
                user_prompt,
                cwd=str(pane_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            self.running_agents[pane_id] = process
            
            # Start task to read output
            asyncio.create_task(self._read_agent_output(pane_id, process))
            
            return {
                "status": "success",
                "message": "Agent started"
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "cursor-agent CLI not found in PATH"
            }
        except Exception as e:
            logger.error(f"Error starting agent for pane {pane_id}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _read_agent_output(self, pane_id: int, process: asyncio.subprocess.Process):
        """
        Read output from the agent process and add to queue.
        After the agent completes, automatically stage and commit all changes.
        """
        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                decoded_line = line.decode('utf-8').rstrip()
                await self.agent_outputs[pane_id].put(decoded_line)
            
            # Wait for process to complete
            await process.wait()
            
            # After agent completes, auto-commit changes
            if self.git_ops is not None:
                logger.info(f"Agent completed for pane {pane_id}, staging and committing changes...")
                
                try:
                    # Get the user's prompt for the commit message
                    commit_message = self.agent_prompts.get(pane_id, "Agent changes")
                    
                    # Run git operations in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, 
                        self.git_ops.commit_changes, 
                        pane_id,
                        commit_message
                    )
                    
                    if result["status"] == "success":
                        logger.info(f"Successfully committed changes for pane {pane_id}: {result['message']}")
                        await self.agent_outputs[pane_id].put(f"\n✓ {result['message']}")
                    else:
                        logger.warning(f"Commit returned status for pane {pane_id}: {result['message']}")
                        # Don't add to output queue if no changes
                        if "No changes to commit" not in result["message"]:
                            await self.agent_outputs[pane_id].put(f"\n⚠ Commit status: {result['message']}")
                except Exception as commit_error:
                    logger.error(f"Error committing changes for pane {pane_id}: {commit_error}")
                    await self.agent_outputs[pane_id].put(f"\n✗ Error committing changes: {str(commit_error)}")
            
            # Signal end of output
            await self.agent_outputs[pane_id].put(None)
            
        except Exception as e:
            logger.error(f"Error reading agent output for pane {pane_id}: {e}")
            await self.agent_outputs[pane_id].put(f"Error: {str(e)}")
            await self.agent_outputs[pane_id].put(None)
        finally:
            # Clean up
            if pane_id in self.running_agents:
                del self.running_agents[pane_id]
            if pane_id in self.agent_prompts:
                del self.agent_prompts[pane_id]
    
    async def stream_agent_output(self, pane_id: int) -> AsyncIterator[str]:
        """
        Stream agent output for SSE endpoint.
        
        Yields lines of output as they become available.
        """
        if pane_id not in self.agent_outputs:
            # No agent running or output queue not initialized
            return
        
        queue = self.agent_outputs[pane_id]
        
        try:
            while True:
                line = await queue.get()
                
                if line is None:
                    # End of output
                    break
                
                yield line
        except Exception as e:
            logger.error(f"Error streaming agent output for pane {pane_id}: {e}")
            yield f"Error: {str(e)}"
        finally:
            # Clean up queue
            if pane_id in self.agent_outputs:
                del self.agent_outputs[pane_id]
    
    async def stop_agent(self, pane_id: int) -> Dict[str, str]:
        """
        Stop a running agent for a pane.
        """
        if pane_id not in self.running_agents:
            return {
                "status": "error",
                "message": "No agent running for this pane"
            }
        
        try:
            process = self.running_agents[pane_id]
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5.0)
            
            return {
                "status": "success",
                "message": "Agent stopped"
            }
        except asyncio.TimeoutError:
            # Force kill if terminate didn't work
            process.kill()
            return {
                "status": "success",
                "message": "Agent force killed"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def run_agent_sync(self, pane_id: int, user_prompt: str) -> Dict[str, any]:
        """
        Run cursor-agent synchronously and wait for completion.
        This is designed for use in conflict resolution where we need to wait.
        
        Args:
            pane_id: The pane ID
            user_prompt: The user's prompt for the agent
        
        Returns:
            Dict with status, message, exit_code, and output
        """
        pane_path = self.get_pane_path(pane_id)
        
        if not pane_path.exists():
            return {
                "status": "error",
                "message": f"Pane directory {pane_path} does not exist",
                "exit_code": -1,
                "output": ""
            }
        
        try:
            logger.info(f"[Pane {pane_id}] Starting synchronous cursor-agent run")
            
            # Start cursor-agent as subprocess
            process = await asyncio.create_subprocess_exec(
                'cursor-agent',
                user_prompt,
                cwd=str(pane_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Read output and wait for completion
            output_lines = []
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                decoded_line = line.decode('utf-8').rstrip()
                output_lines.append(decoded_line)
                logger.debug(f"[Pane {pane_id}] Agent output: {decoded_line}")
            
            # Wait for process to complete
            exit_code = await process.wait()
            
            full_output = '\n'.join(output_lines)
            
            # After agent completes, auto-commit changes if successful
            if exit_code == 0 and self.git_ops is not None:
                logger.info(f"[Pane {pane_id}] Agent completed successfully, committing changes...")
                
                try:
                    # Use a descriptive commit message for merge conflict resolution
                    commit_message = "Resolved merge conflicts"
                    
                    # Run git operations in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, 
                        self.git_ops.commit_changes, 
                        pane_id,
                        commit_message
                    )
                    
                    if result["status"] == "success":
                        logger.info(f"[Pane {pane_id}] Successfully committed conflict resolution: {result['message']}")
                        full_output += f"\n\n✓ {result['message']}"
                    else:
                        logger.warning(f"[Pane {pane_id}] Commit returned status: {result['message']}")
                        if "No changes to commit" not in result["message"]:
                            full_output += f"\n\n⚠ Commit status: {result['message']}"
                except Exception as commit_error:
                    logger.error(f"[Pane {pane_id}] Error committing changes: {commit_error}")
                    full_output += f"\n\n✗ Error committing changes: {str(commit_error)}"
            
            logger.info(f"[Pane {pane_id}] Agent completed with exit code {exit_code}")
            
            return {
                "status": "success" if exit_code == 0 else "error",
                "message": "Agent completed" if exit_code == 0 else f"Agent failed with exit code {exit_code}",
                "exit_code": exit_code,
                "output": full_output
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "cursor-agent CLI not found in PATH",
                "exit_code": -1,
                "output": ""
            }
        except Exception as e:
            logger.error(f"[Pane {pane_id}] Error running agent: {e}")
            return {
                "status": "error",
                "message": str(e),
                "exit_code": -1,
                "output": ""
            }

