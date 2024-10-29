import typer
import asyncio
from typing import Optional, Dict, List
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from github import Github, GithubException
import base64
import httpx
from ..services.groq_service import GroqService

app = typer.Typer()
console = Console()


class RepoScanner:
    def _init_(self, api_key: str, github_token: str, repo_name: str):
        self.base_url = "https://api.on-demand.io/chat/v1"
        self.api_key = api_key
        self.console = Console()
        self.github = Github(github_token)
        self.repo_name = repo_name

    async def get_repo_info(self) -> Dict:
        """
        Gather repository information using PyGithub
        """
        try:
            repo_info = {"files": [], "commit_history": []}

            # Get repository
            repo = self.github.get_repo(self.repo_name)

            # Get default branch
            default_branch = repo.default_branch
            branch = repo.get_branch(default_branch)

            # Get all files in repository
            contents = repo.get_contents("")
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    try:
                        # Get file content
                        file_data = base64.b64decode(file_content.content).decode(
                            "utf-8"
                        )

                        # Get recent commits for this file
                        commits = repo.get_commits(
                            path=file_content.path, sha=default_branch
                        )
                        if commits.totalCount >= 2:
                            # Get diff between last two commits
                            latest_commit = commits[0]
                            previous_commit = commits[1]
                            comparison = repo.compare(
                                previous_commit.sha, latest_commit.sha
                            )
                            diff = comparison.diff_url
                        else:
                            diff = None

                        repo_info["files"].append(
                            {
                                "path": file_content.path,
                                "content": file_data,
                                "diff": diff,
                            }
                        )
                    except (GithubException, UnicodeDecodeError) as e:
                        print_warning(f"Skipping file {file_content.path}: {str(e)}")

            # Get recent commits
            commits = repo.get_commits()
            for commit in commits[:10]:  # Get last 10 commits
                repo_info["commit_history"].append(
                    {
                        "sha": commit.sha,
                        "message": commit.commit.message,
                        "author": commit.commit.author.name,
                        "date": commit.commit.author.date.isoformat(),
                    }
                )

            return repo_info

        except Exception as e:
            raise Exception(f"Failed to gather repository information: {str(e)}")

    async def create_session(self) -> str:
        """Create a chat session and return session ID"""
        url = f"{self.base_url}/sessions"

        data = {"externalUserId": "repo-scanner", "pluginIds": []}

        headers = {"Content-Type": "application/json", "apikey": self.api_key}

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json().get("sessionId")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create session: {str(e)}")

    async def analyze_repo(self, session_id: str, repo_info: Dict) -> List[Dict]:
        """Send repository information for analysis"""
        print(repo_info)

        # Create analysis prompt
        prompt = """
        Analyze this repository's files and changes for potential issues and vulnerabilities.
        Focus on:

        1. Code Security:
           - Potential security vulnerabilities
           - Input validation issues
           - Data exposure risks
           - Common security anti-patterns

        2. Code Quality:
           - Best practices violations
           - Error handling
           - Performance issues
           - Maintainability concerns

        3. Sensitive Data:
           - Hardcoded credentials
           - API keys
           - Private information
           - Configuration secrets

        Provide findings in this format:
        {
            "severity": "Critical/High/Medium/Low",
            "category": "Security/Quality/Data",
            "description": "Detailed issue description",
            "location": "File path or location",
            "recommendation": "How to fix"
        }
        """

        try:
            # Send the request to Groq
            groq_service = GroqService()
            response = groq_service.generate_scanned_result(repo_info)

            print(response)

        except requests.exceptions.RequestException as e:
            print(f"Error: {str(e)}")


async def generate_session():
    url = "https://api.on-demand.io/chat/v1/sessions"
    data = {"externalUserId": "06931013-9ae4-449d-87e8-4224508ba0d0", "pluginIds": []}
    headers = {
        "Content-Type": "application/json",
        "apikey": "yvbWJTQQgdb9hKfYI1OsuviwzVF2BhMT",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response_data = response.json()
        session_id = response_data["data"]["id"]

    return session_id


def print_warning(message: str) -> None:
    """Print a warning message"""
    console.print(f"[yellow]WARNING:[/yellow] {message}")


def print_error(message: str) -> None:
    """Print an error message"""
    console.print(f"[red]ERROR:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message"""
    console.print(f"[green]SUCCESS:[/green] {message}")


@app.callback(invoke_without_command=True)
def scan_callback():
    """
    Scan repository for vulnerabilities and code quality issues
    """
    pass


@app.command()
def run(
    github_token: str = typer.Option(
        ...,
        "--github-token",
        "-t",
        help="GitHub personal access token",
        envvar="GITHUB_TOKEN",
    ),
    repo_name: str = typer.Option(
        ..., "--repo", "-r", help="Repository name in format 'owner/repo'"
    ),
    quick: bool = typer.Option(
        False, "--quick", "-q", help="Perform a quick scan of recent changes only"
    ),
    category: str = typer.Option(
        None, "--category", "-c", help="Scan specific category (security/quality/data)"
    ),
) -> None:
    """
    Run a security and code quality scan on a GitHub repository
    """
    try:
        # Initialize scanner
        scanner = RepoScanner(
            api_key="yvbWJTQQgdb9hKfYI1OsuviwzVF2BhMT",
            github_token=github_token,
            repo_name=repo_name,
        )

        with Progress() as progress:
            # Create progress tasks
            repo_task = progress.add_task(
                "[cyan]Gathering repository information...", total=100
            )
            analysis_task = progress.add_task("[green]Analyzing code...", total=100)

            # Gather repository information
            repo_info = asyncio.run(scanner.get_repo_info())
            progress.update(repo_task, completed=100)

            # Create session and analyze
            session_id = asyncio.run(generate_session())
            findings = asyncio.run(scanner.analyze_repo(session_id, repo_info))
            progress.update(analysis_task, completed=100)

        # Filter findings by category if specified
        if category:
            findings = [
                f
                for f in findings
                if f.get("category", "").lower().startswith(category.lower())
            ]

        # Display results
        table = Table(title="Scan Results")
        table.add_column("Severity", style="bold")
        table.add_column("Category", style="cyan")
        table.add_column("Issue", style="red")
        table.add_column("Location")
        table.add_column("Recommendation", style="green")

        for finding in findings:
            table.add_row(
                finding.get("severity", "Unknown"),
                finding.get("category", "Unknown"),
                finding.get("description", ""),
                finding.get("location", ""),
                finding.get("recommendation", ""),
            )

        console.print("\n")
        console.print(table)

        # Print summary
        total_issues = len(findings)
        critical = sum(1 for f in findings if f.get("severity") == "Critical")
        high = sum(1 for f in findings if f.get("severity") == "High")

        print_success(f"\nScan completed!")
        console.print(f"Found {total_issues} issues:")
        console.print(f"- Critical: {critical}")
        console.print(f"- High: {high}")
        console.print(f"- Other: {total_issues - critical - high}")

    except Exception as e:
        print_error(f"Scan failed: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
