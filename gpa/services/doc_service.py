from github import Github
import os


class GitService:
    def __init__(self):
        # Initialize GitHub connection
        github_token = os.getenv("GITHUB_TOKEN")
        self.github = Github(github_token) if github_token else None

        # Initialize GitPython repository
        try:
            from git import Repo

            self.repo = Repo(".")
        except Exception:
            self.repo = None

    def get_repo_info(self):
        """
        Retrieve repository information with fallbacks.

        :return: Dictionary with repository metadata
        """
        try:
            # Try GitHub API first
            if self.github:
                github_repo = self.github.get_repo(
                    f"{self.repo.active_branch.name}/{self.repo.remotes.origin.url.split('/')[-1].replace('.git', '')}"
                )
                return {
                    "description": github_repo.description
                    or "No description available",
                    "default_branch": github_repo.default_branch,
                    "topics": github_repo.get_topics(),
                }

            # Fallback to local git info
            return {
                "description": self.repo.description
                if hasattr(self.repo, "description")
                else "No description available",
                "default_branch": self.repo.active_branch.name,
                "topics": [],
            }
        except Exception:
            # Completely fallback to default values
            return {
                "description": "No description available",
                "default_branch": "main",
                "topics": [],
            }
