import typer
import asyncio
from typing import Optional, Dict, List
import os
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from github import Github, GithubException
import base64
from ..services.groq_service import GroqService
from ..config import config

app = typer.Typer()
console = Console()


class RepoScanner:
    def __init__(
        self, github_token: Optional[str] = None, repo_name: Optional[str] = None
    ):
        # Try to get token from parameter, then environment, then config
        self.github_token = (
            github_token or os.getenv("GITHUB_TOKEN") or config.github_token
        )
        if not self.github_token:
            raise ValueError(
                "GitHub token not found. Please provide it via --github-token or set GITHUB_TOKEN environment variable"
            )

        self.github = Github(self.github_token)
        self.repo_name = repo_name
        self.console = Console()

    async def get_repo_info(self) -> Dict:
        """Gather repository information using PyGithub"""
        try:
            repo_info = {"files": [], "commit_history": [], "repo_metadata": {}}

            # Get repository
            repo = self.github.get_repo(self.repo_name)

            # Add repository metadata
            repo_info["repo_metadata"] = {
                "name": repo.name,
                "description": repo.description,
                "default_branch": repo.default_branch,
                "language": repo.language,
                "created_at": repo.created_at.isoformat(),
                "last_updated": repo.updated_at.isoformat(),
            }

            # Get default branch
            default_branch = repo.default_branch

            # Get all files in repository
            contents = repo.get_contents("")
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    try:
                        contents.extend(repo.get_contents(file_content.path))
                    except GithubException as e:
                        print_warning(
                            f"Skipping directory {file_content.path}: {str(e)}"
                        )
                        continue

                elif file_content.type == "file":
                    try:
                        # Skip binary files and large files
                        if any(
                            file_content.path.endswith(ext)
                            for ext in [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"]
                        ):
                            continue

                        if file_content.size > 1000000:  # Skip files larger than 1MB
                            print_warning(f"Skipping large file {file_content.path}")
                            continue

                        # Get file content
                        file_data = base64.b64decode(file_content.content).decode(
                            "utf-8"
                        )

                        # Get recent commits for this file
                        commits = repo.get_commits(
                            path=file_content.path, sha=default_branch
                        )
                        commit_info = []

                        for commit in list(commits)[
                            :3
                        ]:  # Get last 3 commits for the file
                            commit_info.append(
                                {
                                    "sha": commit.sha,
                                    "message": commit.commit.message,
                                    "author": commit.commit.author.name,
                                    "date": commit.commit.author.date.isoformat(),
                                }
                            )

                        repo_info["files"].append(
                            {
                                "path": file_content.path,
                                "content": file_data,
                                "size": file_content.size,
                                "last_modified": file_content.last_modified,
                                "commits": commit_info,
                            }
                        )

                    except (GithubException, UnicodeDecodeError) as e:
                        print_warning(f"Skipping file {file_content.path}: {str(e)}")
                        continue

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

    async def analyze_repo(self, repo_info: Dict) -> List[Dict]:
        """Analyze repository and return findings"""
        try:
            # Create analysis using Groq service
            groq_service = GroqService()
            response = await groq_service.generate_scanned_result(repo_info)

            # Parse the response
            try:
                if isinstance(response, str):
                    # Try to find a JSON-like structure in the response
                    import re

                    json_str = re.search(r"\[.*\]|\{.*\}", response.replace("\n", ""))
                    if json_str:
                        findings = eval(json_str.group())
                    else:
                        raise ValueError("No valid JSON structure found in response")
                else:
                    findings = response

                if not isinstance(findings, (list, dict)):
                    raise ValueError("Response is neither a list nor a dict")

                # Convert to list if it's a dict
                if isinstance(findings, dict):
                    findings = [findings]

                # Validate each finding has required fields
                for finding in findings:
                    required_fields = [
                        "severity",
                        "category",
                        "description",
                        "location",
                        "recommendation",
                    ]
                    for field in required_fields:
                        if field not in finding:
                            finding[field] = "Unknown"

            except Exception as parsing_error:
                print_warning(f"Error parsing analysis results: {str(parsing_error)}")
                findings = [
                    {
                        "severity": "Medium",
                        "category": "Quality",
                        "description": "Analysis completed but results parsing failed",
                        "location": "N/A",
                        "recommendation": "Please check the scan logs for details",
                    }
                ]

            return findings

        except Exception as e:
            print_error(f"Analysis failed: {str(e)}")
            return [
                {
                    "severity": "High",
                    "category": "Error",
                    "description": f"Analysis failed: {str(e)}",
                    "location": "N/A",
                    "recommendation": "Please check your configuration and try again",
                }
            ]


def print_warning(message: str) -> None:
    """Print a warning message"""
    console.print(f"[yellow]WARNING:[/yellow] {message}")


def print_error(message: str) -> None:
    """Print an error message"""
    console.print(f"[red]ERROR:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message"""
    console.print(f"[green]SUCCESS:[/green] {message}")


@app.command()
def run(
    github_token: Optional[str] = typer.Option(
        None,
        "--github-token",
        "-t",
        help="GitHub personal access token (can also be set via GITHUB_TOKEN environment variable)",
        envvar="GITHUB_TOKEN",
    ),
    repo_name: str = typer.Option(
        ..., "--repo", "-r", help="Repository name in format 'owner/repo'"
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter results by category (security/quality/data)",
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        "-s",
        help="Filter results by severity (critical/high/medium/low)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output format (table/json)"
    ),
) -> None:
    """
    Run a security and code quality scan on a GitHub repository
    """
    try:
        # Initialize scanner
        scanner = RepoScanner(github_token=github_token, repo_name=repo_name)

        with Progress() as progress:
            # Create progress tasks
            repo_task = progress.add_task(
                "[cyan]Gathering repository information...", total=100
            )
            analysis_task = progress.add_task("[green]Analyzing code...", total=100)

            # Gather repository information
            repo_info = asyncio.run(scanner.get_repo_info())
            progress.update(repo_task, completed=100)

            # Analyze repository
            findings = asyncio.run(scanner.analyze_repo(repo_info))
            progress.update(analysis_task, completed=100)

        # Filter findings
        if category:
            findings = [
                f for f in findings if f.get("category", "").lower() == category.lower()
            ]
        if severity:
            findings = [
                f for f in findings if f.get("severity", "").lower() == severity.lower()
            ]

        # Display results
        if findings:
            if output == "json":
                import json

                console.print(json.dumps(findings, indent=2))
            else:
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
            critical = sum(
                1 for f in findings if f.get("severity", "").lower() == "critical"
            )
            high = sum(1 for f in findings if f.get("severity", "").lower() == "high")
            medium = sum(
                1 for f in findings if f.get("severity", "").lower() == "medium"
            )
            low = sum(1 for f in findings if f.get("severity", "").lower() == "low")

            print_success(f"\nScan completed!")
            console.print(f"Found {total_issues} issues:")
            console.print(f"- Critical: {critical}")
            console.print(f"- High: {high}")
            console.print(f"- Medium: {medium}")
            console.print(f"- Low: {low}")
        else:
            print_success("\nScan completed! No issues found.")

    except Exception as e:
        print_error(f"Scan failed: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
