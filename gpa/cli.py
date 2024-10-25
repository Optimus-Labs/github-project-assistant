from os import name
import typer
from rich.console import Console
from . import __version__
from .commands.commit import commit_command
from .commands.pr import app as pr_app

app = typer.Typer(
    help="GitHub Project Assistant (GPA) - A CLI tool for managing GitHub projects",
    no_args_is_help=True,
)

console = Console()


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False, "--version", "-V", help="Print version information"
    ),
) -> None:
    """
    GitHub Project Assistant (GPA) - A CLI tool for managing GitHub projects
    """
    if version:
        console.print(f"GPA version: {__version__}")
        raise typer.Exit()


# Add commands directly to the main app
app.command(name="commit")(commit_command)
app.add_typer(pr_app, name="pr", help="Manage pull requests")

if __name__ == "__main__":
    app()
