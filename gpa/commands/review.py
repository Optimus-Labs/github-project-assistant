import typer
import asyncio
from typing import Optional
from ..services.git_service import GitService
from ..services.github_service import GitHubService
from ..services.groq_service import GroqService
from ..utils.formatting import print_success, print_error, print_warning, confirm_action

app = typer.Typer()


@app.command()
def analyze(
    pr_number: int = typer.Argument(..., help="Pull request number to analyze"),
    explain: bool = typer.Option(
        False, "--explain", "-e", help="Explain changes in simple terms"
    ),
    comments: bool = typer.Option(
        False, "--comments", "-c", help="Generate review comments"
    ),
) -> None:
    """
    Analyze a pull request and provide improvement suggestions.
    """
    try:
        github_service = GitHubService()
        groq_service = GroqService()

        # Get PR details
        pr_details = github_service.get_pull_request(pr_number)
        if not pr_details:
            print_error(f"PR #{pr_number} not found")
            raise typer.Exit(1)

        # Get diff and analyze
        diff = pr_details["diff"]
        analysis = asyncio.run(groq_service.analyze_code_changes(str(diff), {}))

        print_success(f"\nAnalysis for PR #{pr_number}:")
        typer.echo(analysis)

        # Provide simple explanation if requested
        if explain:
            explanation = asyncio.run(groq_service.explain_changes(str(diff)))
            print_success("\nSimple Explanation:")
            typer.echo(explanation)

        # Generate review comments if requested
        if comments:
            review_comments = asyncio.run(
                groq_service.generate_review_comments(str(diff))
            )
            print_success("\nSuggested Review Comments:")
            for comment in review_comments:
                print_warning(f"\n{comment['type'].upper()}:")
                typer.echo(comment["content"])

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)


@app.command()
def merge(
    pr_number: int = typer.Argument(..., help="Pull request number to merge"),
    method: str = typer.Option(
        "squash", "--method", "-m", help="Merge method (merge/squash/rebase)"
    ),
    analyze_first: bool = typer.Option(
        True, "--analyze/--no-analyze", help="Analyze before merging"
    ),
) -> None:
    """
    Analyze and merge a pull request.
    """
    try:
        github_service = GitHubService()
        groq_service = GroqService()

        # Get PR details
        pr_details = github_service.get_pull_request(pr_number)
        if not pr_details:
            print_error(f"PR #{pr_number} not found")
            raise typer.Exit(1)

        if analyze_first:
            # Quick analysis before merge
            diff = pr_details["diff"]
            analysis = asyncio.run(groq_service.analyze_code_changes(str(diff), {}))
            print_warning("\nPre-merge Analysis:")
            typer.echo(analysis)

        if not pr_details["mergeable"]:
            print_error("PR is not mergeable. Please resolve conflicts first.")
            raise typer.Exit(1)

        if confirm_action(f"\nMerge PR #{pr_number} using {method} method?"):
            success = github_service.merge_pull_request(pr_number, method)
            if success:
                print_success(f"Successfully merged PR #{pr_number}")
            else:
                print_error("Merge failed")

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)
