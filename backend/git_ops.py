import os
import uuid
from pathlib import Path
from typing import Dict, Optional
import git
from git import Repo, GitCommandError


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
        
        if not pane_path.exists():
            raise ValueError(f"Pane directory {pane_path} does not exist")
        
        try:
            repo = Repo(pane_path)
            
            # Force checkout main and reset any changes
            if repo.is_dirty():
                repo.git.reset('--hard')
                repo.git.clean('-fd')
            
            # Checkout main
            repo.git.checkout('main')
            
            # Pull latest changes
            origin = repo.remote('origin')
            origin.pull('main')
            
            # Generate branch name
            uuid_part = str(uuid.uuid4())[:6]
            branch_name = f"tmp-{pane_id}-{uuid_part}"
            
            # Create and checkout new branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            return {
                "branch": branch_name,
                "status": "success",
                "message": f"Created branch {branch_name}"
            }
        except Exception as e:
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
            return len(commits_ahead) > 0
        except Exception:
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
            return len(commits_behind) > 0
        except Exception:
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
            
            # Check if there are any changes to commit
            if not repo.is_dirty(untracked_files=True):
                return {
                    "status": "success",
                    "message": "No changes to commit"
                }
            
            # Stage all changes (tracked and untracked)
            repo.git.add(A=True)
            
            # Commit the changes
            commit = repo.index.commit(message)
            
            return {
                "status": "success",
                "message": f"Committed changes: {commit.hexsha[:7]}",
                "commit_sha": commit.hexsha
            }
        except GitCommandError as e:
            return {
                "status": "error",
                "message": f"Git error: {str(e)}"
            }
        except Exception as e:
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
        
        try:
            repo = Repo(pane_path)
            branch_to_merge = repo.active_branch.name
            
            if branch_to_merge == "main":
                return {
                    "status": "error",
                    "message": "Already on main branch"
                }
            
            # Checkout main
            repo.git.checkout('main')
            
            # Pull latest changes
            origin = repo.remote('origin')
            origin.pull('main')
            
            # Merge the branch
            repo.git.merge(branch_to_merge, '--no-ff', '-m', f'Merge {branch_to_merge}')
            
            # Push to origin
            origin.push('main')
            
            # Delete the temporary branch
            repo.git.branch('-D', branch_to_merge)
            
            return {
                "status": "success",
                "message": f"Successfully merged {branch_to_merge} into main"
            }
        except GitCommandError as e:
            return {
                "status": "error",
                "message": f"Git error: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }

