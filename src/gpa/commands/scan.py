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


# Utility functions for consistent message formatting
def print_warning(message: str) -> None:
    """Print a warning message in yellow"""
    console.print(f"[yellow]WARNING:[/yellow] {message}")


def print_error(message: str) -> None:
    """Print an error message in red"""
    console.print(f"[red]ERROR:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message in green"""
    console.print(f"[green]SUCCESS:[/green] {message}")


def print_info(message: str) -> None:
    """Print an info message in blue"""
    console.print(f"[blue]INFO:[/blue] {message}")


class RepoScanner:
    def __init__(
        self,
        github_token: Optional[str] = None,
        repo_name: Optional[str] = None,
        max_file_size: int = 100000,  # 100KB default max file size
        max_files_per_batch: int = 5,  # Process 5 files per batch
        file_extensions: List[str] = None,  # Filterable file extensions
    ):
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
        self.max_file_size = max_file_size
        self.max_files_per_batch = max_files_per_batch
        self.file_extensions = file_extensions or [
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".go",
            ".rb",
            ".php",
            ".swift",
            ".kt",
            ".rs",
        ]

    def is_analyzable_file(self, file_path: str, file_size: int) -> bool:
        """Check if file should be included in analysis"""
        if file_size > self.max_file_size:
            return False

        extension = os.path.splitext(file_path)[1].lower()
        if not extension or extension not in self.file_extensions:
            return False

        return True

    async def get_repo_files(self) -> List[Dict]:
        """Gather repository files in batches"""
        try:
            repo = self.github.get_repo(self.repo_name)
            contents = repo.get_contents("")
            all_files = []

            with Progress() as progress:
                scan_task = progress.add_task(
                    "[cyan]Scanning repository...", total=None
                )

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
                        if not self.is_analyzable_file(
                            file_content.path, file_content.size
                        ):
                            continue

                        try:
                            file_data = base64.b64decode(file_content.content).decode(
                                "utf-8"
                            )
                            all_files.append(
                                {
                                    "path": file_content.path,
                                    "content": file_data,
                                    "size": file_content.size,
                                }
                            )
                            print_info(f"Added file: {file_content.path}")
                        except (GithubException, UnicodeDecodeError) as e:
                            print_warning(
                                f"Skipping file {file_content.path}: {str(e)}"
                            )
                            continue

                progress.update(scan_task, completed=100)

            print_success(f"Found {len(all_files)} analyzable files")
            return all_files

        except Exception as e:
            raise Exception(f"Failed to gather repository files: {str(e)}")

    def chunk_files(self, files: List[Dict]) -> List[List[Dict]]:
        """Split files into smaller batches"""
        return [
            files[i : i + self.max_files_per_batch]
            for i in range(0, len(files), self.max_files_per_batch)
        ]

    async def analyze_batch(self, file_batch: List[Dict]) -> List[Dict]:
        """Analyze a batch of files"""
        try:
            groq_service = GroqService()

            # Create a simplified context for this batch
            batch_context = {
                "files": file_batch,
                "repo_metadata": {
                    "name": self.repo_name,
                    "analyzed_files": len(file_batch),
                },
            }

            response = await groq_service.generate_scanned_result(batch_context)

            # Parse and validate findings
            findings = self.parse_findings(response)
            return findings

        except Exception as e:
            print_warning(f"Batch analysis failed: {str(e)}")
            return []

    def parse_findings(self, response: str) -> List[Dict]:
        """Parse and validate analysis findings"""
        try:
            if isinstance(response, str):
                import re
                import json

                # Try to find JSON structure
                json_str = re.search(r"\[.*\]|\{.*\}", response.replace("\n", ""))
                if json_str:
                    findings = json.loads(json_str.group())
                else:
                    return []

            else:
                findings = response

            if isinstance(findings, dict):
                findings = [findings]

            # Validate and normalize findings
            normalized_findings = []
            for finding in findings:
                if all(
                    key in finding for key in ["severity", "category", "description"]
                ):
                    normalized_findings.append(
                        {
                            "severity": finding.get("severity", "Unknown"),
                            "category": finding.get("category", "Unknown"),
                            "description": finding.get("description", ""),
                            "location": finding.get("location", "N/A"),
                            "recommendation": finding.get("recommendation", ""),
                        }
                    )

            return normalized_findings

        except Exception as e:
            print_warning(f"Failed to parse findings: {str(e)}")
            return []

    async def analyze_repo(self) -> List[Dict]:
        """Analyze repository in batches"""
        try:
            # Get all analyzable files
            print_info("Starting repository analysis...")
            all_files = await self.get_repo_files()
            if not all_files:
                print_warning("No analyzable files found in repository")
                return []

            # Split into batches
            batches = self.chunk_files(all_files)
            print_info(f"Processing {len(batches)} batches of files...")
            all_findings = []

            with Progress() as progress:
                analyze_task = progress.add_task(
                    "[green]Analyzing files...", total=len(batches)
                )

                # Process each batch
                for i, batch in enumerate(batches, 1):
                    print_info(
                        f"Analyzing batch {i}/{len(batches)} ({len(batch)} files)"
                    )
                    batch_findings = await self.analyze_batch(batch)
                    all_findings.extend(batch_findings)
                    progress.update(analyze_task, advance=1)

            return all_findings

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


def display_results(findings: List[Dict], output_format: Optional[str]) -> None:
    """Display scan results in specified format"""
    if output_format == "json":
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
                finding["severity"],
                finding["category"],
                finding["description"],
                finding["location"],
                finding["recommendation"],
            )

        console.print("\n")
        console.print(table)

    # Print summary
    total_issues = len(findings)
    severity_counts = {
        "critical": sum(1 for f in findings if f["severity"].lower() == "critical"),
        "high": sum(1 for f in findings if f["severity"].lower() == "high"),
        "medium": sum(1 for f in findings if f["severity"].lower() == "medium"),
        "low": sum(1 for f in findings if f["severity"].lower() == "low"),
    }

    print_success(f"\nScan completed!")
    console.print(f"Found {total_issues} issues:")
    for severity, count in severity_counts.items():
        console.print(f"- {severity.capitalize()}: {count}")


@app.command()
def run(
    github_token: Optional[str] = typer.Option(
        None,
        "--github-token",
        "-t",
        help="GitHub personal access token",
        envvar="GITHUB_TOKEN",
    ),
    repo_name: str = typer.Option(
        ..., "--repo", "-r", help="Repository name in format 'owner/repo'"
    ),
    max_file_size: int = typer.Option(
        100000, "--max-file-size", help="Maximum file size to analyze (bytes)"
    ),
    files_per_batch: int = typer.Option(
        5, "--files-per-batch", help="Number of files to analyze per batch"
    ),
    category: Optional[str] = typer.Option(
        None, "--category", "-c", help="Filter results by category"
    ),
    severity: Optional[str] = typer.Option(
        None, "--severity", "-s", help="Filter results by severity"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output format (table/json)"
    ),
) -> None:
    """Run a security and code quality scan on a GitHub repository"""
    try:
        scanner = RepoScanner(
            github_token=github_token,
            repo_name=repo_name,
            max_file_size=max_file_size,
            max_files_per_batch=files_per_batch,
        )

        findings = asyncio.run(scanner.analyze_repo())

        # Filter findings
        if category:
            findings = [
                f for f in findings if f["category"].lower() == category.lower()
            ]
        if severity:
            findings = [
                f for f in findings if f["severity"].lower() == severity.lower()
            ]

        # Display results
        if findings:
            display_results(findings, output)
        else:
            print_success("\nScan completed! No issues found.")

    except Exception as e:
        print_error(f"Scan failed: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
