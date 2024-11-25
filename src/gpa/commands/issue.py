import typer
import asyncio
from typing import Optional, List
from pathlib import Path
from ..services.git_service import GitService
from ..services.github_service import GitHubService
from ..services.groq_service import GroqService
from ..utils.formatting import print_success, print_error, print_warning, confirm_action

app = typer.Typer()


@app.command()
def create(
    title: str = typer.Option(..., "--title", "-t", help="Issue title"),
    context_file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="File path for context"
    ),
    preview: bool = typer.Option(
        False, "--preview", "-p", help="Preview issue without creating"
    ),
) -> None:
    """
    Create a new issue with AI-generated description and suggested labels.
    """
    try:
        # Get context from file if provided
        context = ""
        if context_file:
            if not context_file.exists():
                print_error(f"File not found: {context_file}")
                raise typer.Exit(1)
            context = context_file.read_text()

        # Initialize services
        git_service = GitService()
        github_service = GitHubService()
        groq_service = GroqService()

        # Generate description and labels
        description = asyncio.run(
            groq_service.generate_issue_description(context, title)
        )
        labels = asyncio.run(groq_service.suggest_issue_labels(title, description))

        if preview:
            print_success("\nGenerated Issue:")
            print_warning(f"Title: {title}")
            print_warning("Description:")
            typer.echo(description)
            print_warning("\nSuggested Labels:")
            for label in labels:
                print_warning(f"- {label}")
            return

        if confirm_action("\nCreate issue with these details?"):
            issue_url = github_service.create_issue(title, description, labels)
            print_success(f"Created issue: {issue_url}")
        else:
            print_warning("Issue creation cancelled")

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)


@app.command()
def summarize(
    state: str = typer.Option(
        "open", "--state", "-s", help="Issue state (open/closed)"
    ),
    labels: List[str] = typer.Option(None, "--label", "-l", help="Filter by labels"),
) -> None:
    """
    Summarize and categorize repository issues.
    """
    try:
        github_service = GitHubService()
        groq_service = GroqService()

        # Get issues
        issues = github_service.get_issues(state=state, labels=labels)
        if not issues:
            print_warning(f"No {state} issues found")
            return

        # Generate categorization
        summary = asyncio.run(groq_service.categorize_issues(issues))

        print_success("\nIssue Analysis:")
        typer.echo(summary)

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)


@app.command()
def label(
    issue_number: int = typer.Argument(..., help="Issue number to label"),
    preview: bool = typer.Option(
        True, "--preview/--no-preview", help="Preview labels before applying"
    ),
) -> None:
    """
    Suggest and add labels for an existing issue.
    """
    try:
        github_service = GitHubService()
        groq_service = GroqService()

        # Get issue details
        issues = github_service.get_issues()
        issue = next((i for i in issues if i["number"] == issue_number), None)

        if not issue:
            print_error(f"Issue #{issue_number} not found")
            raise typer.Exit(1)

        # Generate label suggestions
        labels = asyncio.run(
            groq_service.suggest_issue_labels(issue["title"], issue["body"])
        )

        print_success(f"\nSuggested labels for issue #{issue_number}:")
        for label in labels:
            print_warning(f"- {label}")

        if not preview and confirm_action("\nAdd these labels to the issue?"):
            github_service.add_issue_labels(issue_number, labels)
            print_success("Labels added successfully")

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)
