# src/rec2note_cli/main.py
import typer
from rec2note_cli.cli import process
from rec2note_cli.ui.console import console

# The main application
app = typer.Typer(
    name="rec2note",
    help="Rec2Note transforms lecture recording into markdown notes.",
    no_args_is_help=True
)

# Register the sub-commands
app.add_typer(process.app, name="process")

@app.callback()
def main_callback(verbose: bool = False):
    """
    Global flags like --verbose can be handled here.
    """
    if verbose:
        console.print("[info]Verbose mode enabled[/info]")

if __name__ == "__main__":
    app()
