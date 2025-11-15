import uuid
import logging
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING
from git import Repo, GitCommandError

if TYPE_CHECKING:
    from agent import AgentManager

logger = logging.getLogger(__name__)


class GitOperations:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
    
    def get_pane_path(self, pane_id: int) -> Path:
        """Get the path to a pane's webapp directory."""
        return self.base_path / str(pane_id)
    
    def create_pane_branch(self, pane_id: int) -> Dict[str, str]:
        """
        Initialize a pane by:
        1. Checking out main
        2. Pulling latest changes
        3. Creating a new branch tmp-{id}-{uuid6}
        
        Returns dict with branch name and status.
        """
        pane_path = self.get_pane_path(pane_id)
        logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] Creating new pane branch")
        
        if not pane_path.exists():
            logger.error(f"[Pane {pane_id}] Pane directory does not exist: {pane_path}")
            raise ValueError(f"Pane directory {pane_path} does not exist")
        
        try:
            repo = Repo(pane_path)
            current_branch = repo.active_branch.name
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Starting create_pane_branch")
            
            # Force checkout main and reset any changes
            if repo.is_dirty():
                logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git reset --hard")
                repo.git.reset('--hard')
                logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git clean -fd")
                repo.git.clean('-fd')
            
            # Checkout main
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git checkout main")
            repo.git.checkout('main')
            current_branch = repo.active_branch.name
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Now on main branch")
            
            # Pull latest changes
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git pull origin main")
            origin = repo.remote('origin')
            pull_result = origin.pull('main')
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Pull result: {pull_result}")
            
            # Generate branch name
            uuid_part = str(uuid.uuid4())[:6]
            branch_name = f"tmp-{pane_id}-{uuid_part}"
            
            # Create and checkout new branch
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git checkout -b {branch_name}")
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            current_branch = repo.active_branch.name
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Successfully created and checked out branch")
            
            return {
                "branch": branch_name,
                "status": "success",
                "message": f"Created branch {branch_name}"
            }
        except Exception as e:
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] Failed to create pane branch: {str(e)}")
            return {
                "branch": "",
                "status": "error",
                "message": str(e)
            }
    
    def get_branch_status(self, pane_id: int) -> Dict:
        """
        Get the current status of a pane's git repository.
        Returns: branch name, ahead flag, stale flag.
        """
        pane_path = self.get_pane_path(pane_id)
        
        if not pane_path.exists():
            return {
                "active": False,
                "branch": None,
                "is_ahead": False,
                "is_stale": False
            }
        
        try:
            repo = Repo(pane_path)
            current_branch = repo.active_branch.name
            
            # Check if on main branch
            if current_branch == "main":
                return {
                    "active": False,
                    "branch": "main",
                    "is_ahead": False,
                    "is_stale": False
                }
            
            is_ahead = self.is_ahead(pane_id, repo)
            is_stale = self.is_stale(pane_id, repo)
            
            return {
                "active": True,
                "branch": current_branch,
                "is_ahead": is_ahead,
                "is_stale": is_stale
            }
        except Exception as e:
            return {
                "active": False,
                "branch": None,
                "is_ahead": False,
                "is_stale": False,
                "error": str(e)
            }
    
    def is_ahead(self, pane_id: int, repo: Optional[Repo] = None) -> bool:
        """Check if the current branch has commits not in main."""
        if repo is None:
            pane_path = self.get_pane_path(pane_id)
            repo = Repo(pane_path)
        
        try:
            current_branch = repo.active_branch.name
            if current_branch == "main":
                return False
            
            # Get commits in current branch but not in main
            commits_ahead = list(repo.iter_commits(f'origin/main..{current_branch}'))
            logger.debug(f"[Pane {pane_id}] Branch {current_branch} is {len(commits_ahead)} commits ahead of origin/main")
            return len(commits_ahead) > 0
        except Exception as e:
            logger.debug(f"[Pane {pane_id}] Error checking if ahead: {str(e)}")
            return False
    
    def is_stale(self, pane_id: int, repo: Optional[Repo] = None) -> bool:
        """Check if the current branch is missing commits from main."""
        if repo is None:
            pane_path = self.get_pane_path(pane_id)
            repo = Repo(pane_path)
        
        try:
            current_branch = repo.active_branch.name
            if current_branch == "main":
                return False
            
            # Fetch to get latest remote info
            repo.remote('origin').fetch()
            
            # Get commits in main but not in current branch
            commits_behind = list(repo.iter_commits(f'{current_branch}..origin/main'))
            logger.debug(f"[Pane {pane_id}] Branch {current_branch} is {len(commits_behind)} commits behind origin/main")
            return len(commits_behind) > 0
        except Exception as e:
            logger.debug(f"[Pane {pane_id}] Error checking if stale: {str(e)}")
            return False
    
    def commit_changes(self, pane_id: int, message: str = "Agent changes") -> Dict[str, str]:
        """
        Stage and commit all changes in the pane's working directory.
        
        Args:
            pane_id: The pane ID
            message: Commit message (default: "Agent changes")
        
        Returns:
            Dict with status and message
        """
        pane_path = self.get_pane_path(pane_id)
        
        try:
            repo = Repo(pane_path)
            current_branch = repo.active_branch.name
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Committing changes")
            
            # Check if there are any changes to commit
            if not repo.is_dirty(untracked_files=True):
                logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] No changes to commit")
                return {
                    "status": "success",
                    "message": "No changes to commit"
                }
            
            # Stage all changes (tracked and untracked)
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git add -A")
            repo.git.add(A=True)
            
            # Commit the changes
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git commit -m '{message}'")
            commit = repo.index.commit(message)
            
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Successfully committed: {commit.hexsha[:7]}")
            return {
                "status": "success",
                "message": f"Committed changes: {commit.hexsha[:7]}",
                "commit_sha": commit.hexsha
            }
        except GitCommandError as e:
            current_branch = repo.active_branch.name if repo else "unknown"
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git error during commit: {str(e)}")
            return {
                "status": "error",
                "message": f"Git error: {str(e)}"
            }
        except Exception as e:
            current_branch = repo.active_branch.name if repo and hasattr(repo, 'active_branch') else "unknown"
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Error during commit: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def update_pane_branch(self, pane_id: int) -> Dict[str, str]:
        """
        Update a pane's branch by pulling latest main and merging it:
        1. Fetch latest from origin
        2. Merge origin/main into current branch
        
        Returns status dict.
        """
        pane_path = self.get_pane_path(pane_id)
        
        try:
            repo = Repo(pane_path)
            current_branch = repo.active_branch.name
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Starting branch update")
            
            if current_branch == "main":
                logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Cannot update main branch")
                return {
                    "status": "error",
                    "message": "Cannot update main branch"
                }
            
            # Fetch latest from origin
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git fetch origin")
            origin = repo.remote('origin')
            origin.fetch()
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Fetch completed")
            
            # Merge origin/main into current branch
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git merge origin/main")
            merge_result = repo.git.merge('origin/main', '--no-edit')
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Merge result: {merge_result}")
            
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Successfully updated branch with latest from main")
            return {
                "status": "success",
                "message": f"Successfully updated {current_branch} with latest from main"
            }
        except GitCommandError as e:
            current_branch = repo.active_branch.name if repo else "unknown"
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git command error during update: {str(e)}")
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git error stderr: {e.stderr if hasattr(e, 'stderr') else 'N/A'}")
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git error stdout: {e.stdout if hasattr(e, 'stdout') else 'N/A'}")
            return {
                "status": "error",
                "message": f"Git error: {str(e)}"
            }
        except Exception as e:
            current_branch = repo.active_branch.name if repo else "unknown"
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Unexpected error during update: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def get_conflicted_files(self, pane_id: int, repo: Optional[Repo] = None) -> list[str]:
        """
        Get list of files with merge conflicts.
        
        Args:
            pane_id: The pane ID
            repo: Optional Repo instance (will create if not provided)
        
        Returns:
            List of file paths with conflicts
        """
        if repo is None:
            pane_path = self.get_pane_path(pane_id)
            repo = Repo(pane_path)
        
        conflicted_files = []
        try:
            # Get unmerged paths (files with conflicts)
            unmerged = repo.index.unmerged_blobs()
            conflicted_files = list(unmerged.keys())
            logger.debug(f"[Pane {pane_id}] Found {len(conflicted_files)} conflicted files")
        except Exception as e:
            logger.error(f"[Pane {pane_id}] Error getting conflicted files: {str(e)}")
        
        return conflicted_files
    
    def get_branch_diff(self, pane_id: int, branch_name: str, repo: Optional[Repo] = None) -> str:
        """
        Get full diff of changes from the branch compared to main.
        
        Args:
            pane_id: The pane ID
            branch_name: Name of the branch to diff
            repo: Optional Repo instance
        
        Returns:
            String containing the full diff
        """
        if repo is None:
            pane_path = self.get_pane_path(pane_id)
            repo = Repo(pane_path)
        
        try:
            # Get diff from origin/main to the branch
            diff = repo.git.diff('origin/main', branch_name)
            logger.debug(f"[Pane {pane_id}] Generated diff for branch {branch_name}, length: {len(diff)} chars")
            return diff
        except Exception as e:
            logger.error(f"[Pane {pane_id}] Error getting branch diff: {str(e)}")
            return f"Error getting diff: {str(e)}"
    
    def abort_merge(self, pane_id: int) -> Dict[str, str]:
        """
        Abort an in-progress merge and reset to clean state.
        
        Args:
            pane_id: The pane ID
        
        Returns:
            Dict with status and message
        """
        pane_path = self.get_pane_path(pane_id)
        logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] Aborting merge")
        
        try:
            repo = Repo(pane_path)
            current_branch = repo.active_branch.name
            
            # Abort the merge
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git merge --abort")
            repo.git.merge('--abort')
            
            # Reset to clean state
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git reset --hard")
            repo.git.reset('--hard')
            
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Merge aborted successfully")
            return {
                "status": "success",
                "message": "Merge aborted and repository reset"
            }
        except GitCommandError as e:
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] Git error aborting merge: {str(e)}")
            return {
                "status": "error",
                "message": f"Git error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] Error aborting merge: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def merge_pane(self, pane_id: int) -> Dict[str, str]:
        """
        Merge a pane's branch into main:
        1. Get current branch name
        2. Checkout main
        3. Pull latest
        4. Merge the branch
        5. Push to origin (moved to complete_merge if conflicts occur)
        
        Returns status dict with possible statuses:
        - "success": Merge completed successfully
        - "conflict": Merge conflict detected, needs resolution
        - "error": Other error occurred
        """
        pane_path = self.get_pane_path(pane_id)
        logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] Starting merge operation")
        
        try:
            repo = Repo(pane_path)
            branch_to_merge = repo.active_branch.name
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {branch_to_merge}] Starting merge to main")
            
            if branch_to_merge == "main":
                logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {branch_to_merge}] Already on main branch, cannot merge")
                return {
                    "status": "error",
                    "message": "Already on main branch"
                }
            
            # Checkout main
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {branch_to_merge}] Running: git checkout main")
            repo.git.checkout('main')
            current_branch = repo.active_branch.name
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Now on main branch")
            
            # Pull latest changes
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git pull origin main")
            origin = repo.remote('origin')
            pull_result = origin.pull('main')
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Pull result: {pull_result}")
            
            # Merge the branch
            merge_cmd = f"git merge {branch_to_merge} --no-ff -m 'Merge {branch_to_merge}'"
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: {merge_cmd}")
            merge_result = repo.git.merge(branch_to_merge, '--no-ff', '-m', f'Merge {branch_to_merge}')
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Merge result: {merge_result}")
            
            # Push to origin
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git push origin main")
            push_info = origin.push('main')
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Push result: {push_info}")
            for info in push_info:
                logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Push summary: {info.summary}")
            
            # Delete the temporary branch
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git branch -D {branch_to_merge}")
            repo.git.branch('-D', branch_to_merge)
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Deleted branch {branch_to_merge}")
            
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Successfully merged {branch_to_merge} into main and pushed")
            return {
                "status": "success",
                "message": f"Successfully merged {branch_to_merge} into main"
            }
        except GitCommandError as e:
            current_branch = repo.active_branch.name if repo else "unknown"
            stdout = e.stdout if hasattr(e, 'stdout') else ""
            stderr = e.stderr if hasattr(e, 'stderr') else ""
            
            # Check if this is a merge conflict
            if "CONFLICT" in stdout or "Automatic merge failed" in stdout:
                logger.warning(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Merge conflict detected")
                
                # Get conflicted files
                conflicted_files = self.get_conflicted_files(pane_id, repo)
                logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Conflicted files: {conflicted_files}")
                
                # Get full diff of the branch
                diff = self.get_branch_diff(pane_id, branch_to_merge, repo)
                
                return {
                    "status": "conflict",
                    "message": f"Merge conflict in {len(conflicted_files)} file(s)",
                    "branch": branch_to_merge,
                    "conflicted_files": conflicted_files,
                    "diff": diff
                }
            
            # Not a conflict, just a regular error
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git command error during merge: {str(e)}")
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git error stderr: {stderr}")
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git error stdout: {stdout}")
            return {
                "status": "error",
                "message": f"Git error: {str(e)}"
            }
        except Exception as e:
            current_branch = repo.active_branch.name if repo else "unknown"
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Unexpected error during merge: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def complete_merge(self, pane_id: int, branch_to_merge: str) -> Dict[str, str]:
        """
        Complete a merge after conflicts have been resolved.
        Assumes we're on main branch and merge is ready to be committed.
        
        Args:
            pane_id: The pane ID
            branch_to_merge: Name of the branch that was merged
        
        Returns:
            Dict with status and message
        """
        pane_path = self.get_pane_path(pane_id)
        logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] Completing merge of {branch_to_merge}")
        
        try:
            repo = Repo(pane_path)
            current_branch = repo.active_branch.name
            
            if current_branch != "main":
                logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Not on main branch")
                return {
                    "status": "error",
                    "message": f"Expected to be on main branch, but on {current_branch}"
                }
            
            # Check if there are still unresolved conflicts
            if repo.index.unmerged_blobs():
                logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Still has unresolved conflicts")
                return {
                    "status": "error",
                    "message": "Cannot complete merge: unresolved conflicts remain"
                }
            
            # Push to origin
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git push origin main")
            origin = repo.remote('origin')
            push_info = origin.push('main')
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Push result: {push_info}")
            for info in push_info:
                logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Push summary: {info.summary}")
            
            # Delete the temporary branch
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Running: git branch -D {branch_to_merge}")
            repo.git.branch('-D', branch_to_merge)
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Deleted branch {branch_to_merge}")
            
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Successfully completed merge of {branch_to_merge}")
            return {
                "status": "success",
                "message": f"Successfully merged {branch_to_merge} into main"
            }
        except GitCommandError as e:
            current_branch = repo.active_branch.name if repo else "unknown"
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git error completing merge: {str(e)}")
            return {
                "status": "error",
                "message": f"Git error: {str(e)}"
            }
        except Exception as e:
            current_branch = repo.active_branch.name if repo else "unknown"
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Error completing merge: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    async def resolve_merge_conflict(
        self, 
        pane_id: int, 
        branch_name: str, 
        conflicted_files: list[str],
        diff: str,
        agent_manager: 'AgentManager'
    ) -> Dict[str, str]:
        """
        Resolve merge conflicts using cursor-agent.
        
        Args:
            pane_id: The pane ID
            branch_name: Name of the branch being merged
            conflicted_files: List of files with conflicts
            diff: Full diff of the branch
            agent_manager: AgentManager instance to run the agent
        
        Returns:
            Dict with status and message
        """
        pane_path = self.get_pane_path(pane_id)
        logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] Starting conflict resolution with agent")
        
        # Build the prompt for the agent
        conflicted_files_str = '\n'.join([f"- {file}" for file in conflicted_files])
        
        # Truncate diff if it's too large (max 50000 chars to avoid overwhelming the agent)
        if len(diff) > 50000:
            diff = diff[:50000] + "\n\n... (diff truncated for brevity) ..."
        
        prompt = f"""A merge conflict has occurred while merging {branch_name} into main.

Conflicted files:
{conflicted_files_str}

Full diff of changes from {branch_name}:
```
{diff}
```

Your task:
1. Examine the conflicts in the files listed above
2. Resolve all conflicts by editing the files
3. Remove conflict markers (<<<<<<, =======, >>>>>>>)
4. Stage the resolved files with git add
5. Complete the merge by running: git commit --no-edit

Make sure the final result preserves the intent of the changes while resolving conflicts appropriately.
DO NOT push to origin - that will be done automatically after you complete the merge."""
        
        logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] Running agent with conflict resolution prompt")
        
        try:
            # Run agent synchronously
            result = await agent_manager.run_agent_sync(pane_id, prompt)
            
            if result["status"] == "error":
                logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] Agent failed: {result['message']}")
                return {
                    "status": "error",
                    "message": f"Agent failed: {result['message']}"
                }
            
            # Check if conflicts are resolved
            repo = Repo(pane_path)
            if repo.index.unmerged_blobs():
                logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] Conflicts still remain after agent run")
                return {
                    "status": "error",
                    "message": "Agent completed but conflicts still remain"
                }
            
            logger.info(f"[Pane {pane_id}] [cwd: {pane_path}] Agent successfully resolved conflicts")
            return {
                "status": "success",
                "message": "Conflicts resolved by agent",
                "output": result.get("output", "")
            }
        except Exception as e:
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] Error during conflict resolution: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }

