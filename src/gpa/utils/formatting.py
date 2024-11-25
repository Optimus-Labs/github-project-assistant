from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm

console = Console()


def print_success(message: str) -> None:
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    console.print(f"[yellow]![/yellow] {message}")


def print_diff(diff: str) -> None:
    syntax = Syntax(diff, "diff", theme="monokai")
    console.print(Panel(syntax, title="Staged Changes", border_style="blue"))


def confirm_action(message: str) -> bool:
    return Confirm.ask(message)
