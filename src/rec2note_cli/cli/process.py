import typer
from pathlib import Path
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from rec2note_cli.ui.console import console
from rec2note_cli.core.pipeline import run_pipeline

# Create a sub-app for processing commands
app = typer.Typer()

@app.command(name="run")
def process_audio(
    file: Path = typer.Argument(..., help="Path to the audio recording", exists=True),
):
    """
    Process an audio file and generate meeting notes.
    """
    console.print(f"[info]Starting pipeline for:[/info] [highlight]{file.name}[/highlight]")

    # Using Rich Progress Bar to show steps
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        task1 = progress.add_task("[cyan]Transcribing audio...", total=None)
        # Call core logic (this would be split up in a real app for granular progress)
        result = run_pipeline(file)
        progress.update(task1, completed=100, visible=False)

    # Output the result nicely
    note_content = f"[bold]Summary:[/bold]\n{result['summary']}\n\n[bold]Action Items:[/bold]"
    for item in result['action_items']:
        note_content += f"\n• {item}"

    console.print(Panel(note_content, title=result["title"], border_style="success"))
    console.print("[success]✓ Processing complete![/success]")
