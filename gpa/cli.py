import typer
from rich.console import Console
from . import __version__
from .commands.commit import commit_command

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

if __name__ == "__main__":
    app()
