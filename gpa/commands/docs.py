import typer
import asyncio
from typing import Optional, List
from pathlib import Path
from ..services.git_service import GitService
from ..services.github_service import GitHubService
from ..services.groq_service import GroqService
from ..services.file_service import FileService
from ..utils.formatting import print_success, print_error, print_warning, confirm_action

app = typer.Typer()


@app.command()
def readme(
    output: str = typer.Option("README.md", "--output", "-o", help="Output file path"),
    preview: bool = typer.Option(
        False, "--preview", "-p", help="Preview without saving"
    ),
) -> None:
    """
    Generate or update project README file.
    """
    try:
        file_service = FileService()
        git_service = GitService()
        groq_service = GroqService()

        # Get project files and git info
        project_files = file_service.get_project_files([".py", ".md", ".txt"])

        # Safely get git information with fallbacks
        git_info = {}
        try:
            repo = git_service.repo
            git_info = {
                "description": getattr(repo, "description", None)
                or "No description available",
                "default_branch": getattr(repo, "default_branch", None) or "main",
                "topics": repo.get_topics() if hasattr(repo, "get_topics") else [],
            }
        except Exception as e:
            print_warning(f"Could not fetch complete git information: {str(e)}")
            git_info = {
                "description": "No description available",
                "default_branch": "main",
                "topics": [],
            }

        # Generate README
        content = asyncio.run(groq_service.generate_readme(project_files, git_info))

        if preview:
            print_success("\nGenerated README:")
            typer.echo(content)
            return

        if confirm_action(f"\nSave README to {output}?"):
            if file_service.save_file(output, content):
                print_success(f"README saved to {output}")
            else:
                print_error("Failed to save README")

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)


@app.command()
def suggest(
    path: str = typer.Argument(..., help="Path to documentation file"),
    diff: Optional[str] = typer.Option(None, "--diff", "-d", help="Path to diff file"),
) -> None:
    """
    Suggest improvements for existing documentation.
    """
    try:
        file_service = FileService()
        git_service = GitService()
        groq_service = GroqService()

        # Get current documentation
        docs = Path(path).read_text()

        # Get code changes
        if diff:
            changes = Path(diff).read_text()
        else:
            try:
                changes = git_service.repo.git.diff()
            except Exception:
                print_warning("Could not fetch git diff, proceeding with empty changes")
                changes = ""

        # Generate suggestions
        suggestions = asyncio.run(groq_service.suggest_doc_improvements(docs, changes))

        print_success(f"\nSuggested improvements for {path}:")
        typer.echo(suggestions)

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)


@app.command()
def generate(
    path: str = typer.Argument(..., help="Path to Python file"),
    style: str = typer.Option(
        "google", "--style", "-s", help="Documentation style (google/numpy/sphinx)"
    ),
    preview: bool = typer.Option(
        False, "--preview", "-p", help="Preview without saving"
    ),
) -> None:
    """
    Generate code documentation for Python files.
    """
    try:
        file_service = FileService()
        groq_service = GroqService()

        # Read Python file
        code = Path(path).read_text()

        # Generate documentation
        docs = asyncio.run(groq_service.generate_code_docs(code, style))

        if preview:
            print_success(f"\nGenerated documentation ({style} style):")
            typer.echo(docs)
            return

        # Save to file with _docs suffix
        output_path = str(Path(path).with_suffix("")) + "_docs.py"
        if confirm_action(f"\nSave documentation to {output_path}?"):
            if file_service.save_file(output_path, docs):
                print_success(f"Documentation saved to {output_path}")
            else:
                print_error("Failed to save documentation")

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        raise typer.Exit(1)
