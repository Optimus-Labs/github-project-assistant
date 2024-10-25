import typer
import asyncio
from typing import Optional
from ..services.git_service import GitService
from ..services.github_service import GitHubService
from ..services.groq_service import GroqService
from ..utils.formatting import print_success, print_error, print_warning, confirm_action

app = typer.Typer()


@app.command()
def create(
    title: Optional[str] = typer.Option(None, "--title", "-t", help="PR title"),
    base: str = typer.Option(
        "master", "--base", "-b", help="Base branch (default: master)"
    ),
    preview: bool = typer.Option(
        False, "--preview", "-p", help="Preview PR description without creating"
    ),
) -> None:
    """
    Create a pull request with an AI-generated description based on your commits.
    """
    try:
        # Initialize git service and validate repository
        git_service = GitService()
        is_valid, validation_message = git_service.validate_repo()

        if not is_valid:
            print_error(validation_message)
            raise typer.Exit(1)

        # Get the current branch and commits
        current_branch = git_service.repo.active_branch.name
        print_success(f"Current branch: {current_branch}")

        # Get recent commits from the current branch
        commits = git_service.get_recent_commits(count=5)
        if not commits:
            print_error("No commits found in current branch")
            raise typer.Exit(1)

        print_success("Recent commits:")
        for commit in commits:
            print_warning(f"- {commit}")

        # Get the diff for changes
        try:
            diff = git_service.repo.git.diff(f"origin/{base}...{current_branch}")
        except Exception:
            # Fallback to local diff if origin comparison fails
            try:
                diff = git_service.repo.git.diff(f"{base}...{current_branch}")
            except Exception:
                # Final fallback: just get all changes in current branch
                diff = git_service.repo.git.diff()

        if not diff:
            print_warning(
                "No changes detected. Make sure you have committed your changes."
            )
            raise typer.Exit(1)

        # Generate PR description
        groq_service = GroqService()
        description = asyncio.run(groq_service.generate_pr_description(commits, diff))

        if preview:
            print_success("\nGenerated PR description:")
            typer.echo("-" * 50)
            typer.echo(description)
            typer.echo("-" * 50)
            return

        if not title:
            # Use first commit message as title if not provided
            title = commits[0] if commits else "Update"

        # Show summary and confirm
        print_warning("\nPR Details:")
        print_warning(f"Title: {title}")
        print_warning(f"From: {current_branch}")
        print_warning(f"To: {base}")

        if confirm_action("\nCreate pull request?"):
            github_service = GitHubService()
            pr_url = github_service.create_pull_request(
                title, description, base, current_branch
            )
            print_success(f"\nCreated PR: {pr_url}")
        else:
            print_warning("PR creation cancelled")

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)
