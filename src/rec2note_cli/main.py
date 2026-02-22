# src/rec2note_cli/main.py
import typer

from rec2note_cli.cli.process import process_run

# Single-command app — Typer auto-promotes the sole command to the root,
# so the user types  `rec2note [OPTIONS]`  with no subcommand name at all.
app = typer.Typer(
    name="rec2note",
    help="Rec2Note — transform lecture recordings into beautiful markdown notes.",
    no_args_is_help=True,
    add_completion=False,
)

app.command(name="rec2note")(process_run)

if __name__ == "__main__":
    app()
