from datetime import datetime
from pathlib import Path
from typing import NoReturn, Optional

import typer
from rich.align import Align
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from rec2note_cli.core.pipeline import (
    _PANEL_WIDTH,
    run_full_pipeline,
    run_minimal_pipeline,
)
from rec2note_cli.ui.console import console

# ---------------------------------------------------------------------------
# Sub-app
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LOGO = (
    r"[bold blue] ____  _____ ____ ____  _   _  ___ _____ _____ [/bold blue]" + "\n"
    r"[bold blue]|  _ \| ____/ ___|___ \| \ | |/ _ \_   _| ____|[/bold blue]" + "\n"
    r"[bold blue]| |_) |  _|| |     __) |  \| | | | || | |  _|  [/bold blue]" + "\n"
    r"[bold cyan]|  _ <| |__| |___ / __/| |\  | |_| || | | |___ [/bold cyan]" + "\n"
    r"[bold cyan]|_| \_\_____\____|_____|_| \_|\___/ |_| |_____|[/bold cyan]"
)

_TAGLINE = "[dim]Transform lecture recordings into markdown notes.[/dim]"

_NOTES_DIR = Path("notes")

_SUPPORTED_AUDIO = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".opus"}
_SUPPORTED_VIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_banner() -> None:
    console.print()
    console.print(Rule(style="bold blue"))
    console.print(_LOGO, justify="center")
    console.print(_TAGLINE, justify="center")
    console.print(Rule(style="bold blue"))
    console.print()


def _media_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in _SUPPORTED_AUDIO:
        return "🎙️  Audio"
    if suffix in _SUPPORTED_VIDEO:
        return "🎬  Video"
    return "📄  Unknown"


def _print_job_table(
    note_name: str,
    media: Optional[Path],
    transcript: Optional[Path],
    mode: str,
    preview: bool,
    output_path: Path,
) -> None:
    table = Table(
        title="[bold]Job Configuration[/bold]",
        title_style="bold blue",
        border_style="blue",
        show_header=True,
        header_style="bold cyan",
        min_width=54,
    )
    table.add_column("Setting", style="bold", no_wrap=True)
    table.add_column("Value")

    table.add_row("📝  Note name", f"[cyan]{note_name}[/cyan]")
    table.add_row(
        "🎧  Media file",
        f"[yellow]{media}[/yellow] [dim]({_media_kind(media)})[/dim]"
        if media
        else "[dim]—  not provided[/dim]",
    )
    table.add_row(
        "📄  Transcript",
        f"[yellow]{transcript}[/yellow]"
        if transcript
        else "[dim]—  not provided[/dim]",
    )
    table.add_row(
        "⚙️   Pipeline mode",
        f"[bold green]{mode}[/bold green]",
    )
    table.add_row(
        "👁️   Preview markdown", "[green]yes[/green]" if preview else "[dim]no[/dim]"
    )
    table.add_row("💾  Output path", f"[magenta]{output_path}[/magenta]")
    table.add_row(
        "🕐  Started at", f"[dim]{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}[/dim]"
    )

    console.print(Align.center(table))
    console.print()


def _abort(message: str) -> NoReturn:
    console.print(
        Panel(
            f"[bold red]✗[/bold red]  {message}",
            title="[bold red]Error[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
    )
    raise typer.Exit(code=1)


def _save_note(output_path: Path, content: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def _print_preview(markdown_content: str, note_name: str) -> None:
    console.print()
    console.print(
        Rule(f"[bold yellow]👁️  Preview — {note_name}[/bold yellow]", style="yellow")
    )
    console.print()
    console.print(
        Panel(
            Markdown(markdown_content),
            border_style="yellow",
            padding=(1, 2),
        )
    )
    console.print(Rule(style="yellow"))
    console.print()


def _print_success(output_path: Path, mode: str, elapsed_hint: str) -> None:
    lines = (
        f"[bold green]✓[/bold green]  Pipeline finished successfully\n"
        f"[bold green]✓[/bold green]  Mode  :  [bold]{mode}[/bold]\n"
        f"[bold green]✓[/bold green]  Saved :  [bold magenta]{output_path}[/bold magenta]\n"
        f"[bold green]✓[/bold green]  Time  :  [dim]{elapsed_hint}[/dim]"
    )
    console.print(
        Panel(
            lines,
            title="[bold green]All done![/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(Rule("[bold green]✓  Rec2Note complete[/bold green]", style="green"))
    console.print()


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


def process_run(
    # ── inputs ───────────────────────────────────────────────────────────
    media: Optional[Path] = typer.Option(
        None,
        "-media",
        "--media",
        help="Path to the source audio or video recording.",
        show_default=False,
        metavar="PATH",
    ),
    transcript: Optional[Path] = typer.Option(
        None,
        "-tr",
        "--transcript",
        help="Path to a plain-text transcript file (.txt / .md).",
        show_default=False,
        metavar="PATH",
    ),
    # ── pipeline mode ────────────────────────────────────────────────────
    minimal: bool = typer.Option(
        False,
        "-m",
        "--minimal",
        help="Run the minimal pipeline — summary agent only.",
        is_flag=True,
    ),
    full: bool = typer.Option(
        False,
        "-f",
        "--full",
        help="Run the full pipeline — summary + deadlines + study Qs + student Q&A.",
        is_flag=True,
    ),
    # ── output ───────────────────────────────────────────────────────────
    preview: bool = typer.Option(
        False,
        "-pr",
        "--preview",
        help="Render the generated markdown directly in the terminal.",
        is_flag=True,
    ),
    output_dir: Path = typer.Option(
        _NOTES_DIR,
        "-o",
        "--output-dir",
        help="Directory where the generated .md file is saved.",
        show_default=True,
        metavar="DIR",
    ),
):
    """
    Process a lecture recording or transcript and generate markdown notes.

    \b
    Examples
    --------
    Minimal pipeline from a transcript:
        rec2note process run -tr lecture.txt -m

    Full pipeline with preview:
        rec2note process run -tr lecture.txt -f -pr

    Full pipeline with media metadata:
        rec2note process run -media lecture.mp4 -tr lecture.txt -f -pr
    """
    started_at = datetime.now()

    # ── banner ────────────────────────────────────────────────────────────
    _print_banner()

    # ── validate: at least one input ─────────────────────────────────────
    if media is None and transcript is None:
        _abort(
            "You must supply at least one input.\n\n"
            "  Provide a transcript with [bold]-tr[/bold] / [bold]--transcript[/bold], "
            "or a media file with [bold]-media[/bold] / [bold]--media[/bold].\n\n"
            "  Run [bold]rec2note process run --help[/bold] for full usage."
        )

    # ── validate: transcript is required to run the pipeline ─────────────
    if transcript is None:
        _abort(
            "A [bold]transcript file[/bold] is required to run the pipeline.\n\n"
            "  [dim]Auto-transcription from media is coming in a future release.[/dim]\n\n"
            "  Supply a transcript with [bold]-tr[/bold] / [bold]--transcript[/bold]."
        )

    if not transcript.exists():
        _abort(f"Transcript file not found:\n\n  [dim]{transcript}[/dim]")

    if media is not None and not media.exists():
        _abort(f"Media file not found:\n\n  [dim]{media}[/dim]")

    # ── validate: pipeline mode ───────────────────────────────────────────
    if minimal and full:
        _abort(
            "[bold]-m / --minimal[/bold] and [bold]-f / --full[/bold] are mutually exclusive.\n\n"
            "  Pick one pipeline mode and try again."
        )

    if not minimal and not full:
        console.print(
            Panel(
                "[yellow]⚠[/yellow]  No pipeline mode selected — "
                "defaulting to [bold]minimal[/bold].\n"
                "[dim]  Pass [bold]-f[/bold] / [bold]--full[/bold] to run all agents.[/dim]",
                border_style="yellow",
                padding=(0, 2),
            )
        )
        console.print()
        minimal = True

    mode_label = (
        "Minimal  (summary only)"
        if minimal
        else "Full  (summary · deadlines · study Qs · student Q&A)"
    )

    # ── derive note name & output path ────────────────────────────────────
    source = transcript
    note_name = source.stem.replace("_", " ").replace("-", " ").title()
    timestamp = started_at.strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{source.stem}_{timestamp}.md"

    # ── job summary ───────────────────────────────────────────────────────
    _print_job_table(
        note_name=note_name,
        media=media,
        transcript=transcript,
        mode=mode_label,
        preview=preview,
        output_path=output_path,
    )
    start_panel = Panel(
        "[bold]Ready to process.[/bold]  The pipeline will now process your transcript"
        "and invoke the configured Gemini agents.  Sit tight, this may take"
        " [italic]30 s – 2 min[/italic] depending on transcript length and model load.",
        title="[bold blue]Starting[/bold blue]",
        border_style="blue",
        padding=(1, 2),
        width=_PANEL_WIDTH,
    )
    console.print(Align.center(start_panel))
    console.print()

    # ── run pipeline ──────────────────────────────────────────────────────
    try:
        if minimal:
            markdown = run_minimal_pipeline(
                note_name=note_name,
                transcription_path=str(transcript),
            )
        else:
            markdown = run_full_pipeline(
                note_name=note_name,
                transcription_path=str(transcript),
            )
    except ValueError as exc:
        _abort(str(exc))
    except Exception as exc:
        _abort(
            f"An unexpected error occurred during the pipeline:\n\n"
            f"  [dim]{exc}[/dim]\n\n"
            "  Check your API key, model settings, and transcript file."
        )

    # ── save ──────────────────────────────────────────────────────────────
    _save_note(output_path, markdown)

    # ── optional preview ──────────────────────────────────────────────────
    if preview:
        _print_preview(markdown, note_name)

    # ── success ───────────────────────────────────────────────────────────
    elapsed = datetime.now() - started_at
    total_seconds = int(elapsed.total_seconds())
    elapsed_str = (
        f"{total_seconds // 60} min {total_seconds % 60} s"
        if total_seconds >= 60
        else f"{total_seconds} s"
    )
    _print_success(output_path=output_path, mode=mode_label, elapsed_hint=elapsed_str)
