import asyncio
import subprocess
from pathlib import Path
from typing import Dict, AsyncIterator, Optional
import logging

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.running_agents: Dict[int, asyncio.subprocess.Process] = {}
        self.agent_outputs: Dict[int, asyncio.Queue] = {}
    
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

