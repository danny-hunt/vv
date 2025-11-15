import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Optional
import git
from git import Repo, GitCommandError

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
    
    def merge_pane(self, pane_id: int) -> Dict[str, str]:
        """
        Merge a pane's branch into main:
        1. Get current branch name
        2. Checkout main
        3. Pull latest
        4. Merge the branch
        5. Push to origin
        
        Returns status dict.
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
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git command error during merge: {str(e)}")
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git error stderr: {e.stderr if hasattr(e, 'stderr') else 'N/A'}")
            logger.error(f"[Pane {pane_id}] [cwd: {pane_path}] [branch: {current_branch}] Git error stdout: {e.stdout if hasattr(e, 'stdout') else 'N/A'}")
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

