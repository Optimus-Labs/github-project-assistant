import git
from typing import List, Optional, Tuple
from pathlib import Path
from git.exc import InvalidGitRepositoryError, NoSuchPathError


class GitService:
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or Path.cwd()
        self.repo = None

    def validate_repo(self) -> Tuple[bool, str]:
        """
        Validates if the current directory is a git repository.
        Returns a tuple of (is_valid, message).
        """
        try:
            self.repo = git.Repo(self.repo_path)
            return True, "Valid git repository"
        except InvalidGitRepositoryError:
            return False, "Not a git repository"
        except NoSuchPathError:
            return False, "Path does not exist"
        except Exception as e:
            return False, f"Error validating repository: {str(e)}"

    def init_repo(self) -> Tuple[bool, str]:
        """
        Initializes a new git repository in the current directory.
        Returns a tuple of (success, message).
        """
        try:
            self.repo = git.Repo.init(self.repo_path)
            return True, "Initialized new git repository"
        except Exception as e:
            return False, f"Error initializing repository: {str(e)}"

    def get_staged_diff(self) -> str:
        if not self.repo:
            raise ValueError("Repository not initialized")
        return self.repo.git.diff("--staged")

    def get_recent_commits(self, count: int = 5) -> List[str]:
        if not self.repo:
            raise ValueError("Repository not initialized")
        commits = []
        for commit in self.repo.iter_commits(max_count=count):
            commits.append(commit.message)
        return commits

    def create_commit(self, message: str) -> None:
        if not self.repo:
            raise ValueError("Repository not initialized")
        self.repo.index.commit(message)
