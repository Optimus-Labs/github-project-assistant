from github import Github
from typing import List, Dict, Optional
from pathlib import Path
from ..config import config


class GitHubService:
    def __init__(self):
        self.client = Github(config.github_token)
        self.repo = self._get_current_repo()

    def _get_current_repo(self):
        """Get the GitHub repository for the current directory."""
        try:
            with open(Path.cwd() / ".git" / "config", "r") as f:
                config_content = f.read()
                # Extract repo URL from git config
                repo_url = (
                    [line for line in config_content.split("\n") if "url = " in line][0]
                    .split("github.com/")[-1]
                    .strip()
                )
                repo_url = repo_url.replace(".git", "")
                return self.client.get_repo(repo_url)
        except Exception as e:
            raise ValueError(f"Failed to get GitHub repository: {str(e)}")

    def create_pull_request(
        self, title: str, body: str, base: str = "main", head: str = None
    ) -> str:
        """Create a new pull request."""
        if head is None:
            # Get current branch name
            import git

            repo = git.Repo(Path.cwd())
            head = repo.active_branch.name

        pr = self.repo.create_pull(title=title, body=body, base=base, head=head)
        return pr.html_url

    def get_pull_request_files(self, pr_number: int) -> List[str]:
        """Get list of files changed in a PR."""
        pr = self.repo.get_pull(pr_number)
        return [f.filename for f in pr.get_files()]

    def get_file_contributors(self, filepath: str) -> List[str]:
        """Get list of contributors who have modified a file."""
        commits = self.repo.get_commits(path=filepath)
        contributors = set()
        for commit in commits:
            if commit.author:
                contributors.add(commit.author.login)
        return list(contributors)

    def create_issue(self, title: str, body: str, labels: List[str] = None) -> str:
        """Create a new issue with the given title, body, and labels."""
        issue = self.repo.create_issue(title=title, body=body, labels=labels)
        return issue.html_url

    def get_issues(self, state: str = "open", labels: List[str] = None) -> List[dict]:
        """Get repository issues with optional filters."""
        issues = self.repo.get_issues(state=state, labels=labels)
        return [
            {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "labels": [label.name for label in issue.labels],
            }
            for issue in issues
        ]

    def add_issue_labels(self, issue_number: int, labels: List[str]) -> None:
        """Add labels to an existing issue."""
        issue = self.repo.get_issue(issue_number)
        issue.add_to_labels(*labels)
