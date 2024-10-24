import typer
import asyncio
from typing import Optional
from ..services.git_service import GitService
from ..services.groq_service import GroqService
from ..utils.formatting import (
    print_success,
    print_error,
    print_diff,
    print_warning,
    confirm_action,
)


def commit_command(
    message: Optional[str] = typer.Option(
        None, "--message", "-m", help="Manually specify commit message"
    ),
    preview: bool = typer.Option(
        False, "--preview", "-p", help="Preview the commit message without committing"
    ),
    history_context: bool = typer.Option(
        True, "--history/--no-history", help="Use commit history for context"
    ),
) -> None:
    """
    Generate and create a commit with an AI-generated message based on staged changes.
    """
    try:
        # Initialize git service
        git_service = GitService()

        # Validate git repository
        is_valid, validation_message = git_service.validate_repo()

        if not is_valid:
            print_warning(validation_message)
            if confirm_action("Would you like to initialize a new git repository?"):
                success, init_message = git_service.init_repo()
                if success:
                    print_success(init_message)
                else:
                    print_error(init_message)
                    raise typer.Exit(1)
            else:
                print_error("Cannot proceed without a git repository")
                raise typer.Exit(1)

        # Check for staged changes
        diff = git_service.get_staged_diff()

        if not diff:
            print_error(
                "No staged changes found. Stage your changes first with 'git add'"
            )
            raise typer.Exit(1)

        print_diff(diff)

        if message:
            commit_message = message
        else:
            commit_history = (
                git_service.get_recent_commits() if history_context else None
            )
            groq_service = GroqService()

            try:
                commit_message = asyncio.run(
                    groq_service.generate_commit_message(diff, commit_history)
                )
            except Exception as e:
                print_error(f"Failed to generate commit message: {str(e)}")
                raise typer.Exit(1)

        if preview:
            print_success("Generated commit message:")
            typer.echo(commit_message)
            return

        git_service.create_commit(commit_message)
        print_success(f"Created commit with message: {commit_message}")

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)
