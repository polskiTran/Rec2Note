from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from rec2note_cli.config import get_settings
from rec2note_cli.core.agents import (
    deadline_agent,
    questions_agent,
    student_qa_agent,
    summary_agent,
)
from rec2note_cli.utils.markdown_builder import build_markdown
from rec2note_cli.utils.read_file import read_file

console = Console()
settings = get_settings()

_PANEL_WIDTH = 106


def run_minimal_pipeline(note_name: str, transcription_path: str) -> str:
    """
    Run minimal pipline - only run summary agent

    Args:
        note_name (str): Name of the note to be created.
        transcription_path (str): Path to the transcription file.

    Returns:
        str: Markdown content of the note.

    Raises:
        ValueError: If the transcription file is empty.
    """
    console.print(Rule("[bold blue]Rec2Note[/bold blue] [dim]— Minimal Pipeline[/dim]"))
    console.print()
    job_panel = Panel(
        f"[bold]Note:[/bold]       [cyan]{note_name}[/cyan]\n"
        f"[bold]Transcript:[/bold] [dim]{transcription_path}[/dim]",
        title="[bold blue]Job Details[/bold blue]",
        border_style="blue",
        width=_PANEL_WIDTH,
        padding=(1, 2),
    )
    console.print(Align.center(job_panel))

    console.print("\n[bold cyan]📄 Reading transcript...[/bold cyan]")
    transcript = read_file(transcription_path)
    if not transcript.strip():
        raise ValueError("Transcription file is empty.")
    console.print(
        f"[green]✓[/green] Transcript loaded "
        f"[dim]({len(transcript):,} characters)[/dim]"
    )

    ttl = settings.google_gemini_cache_ttl

    console.print()
    with console.status("[yellow]🤖 Running summary agent...[/yellow]", spinner="dots"):
        summary = summary_agent(transcript=transcript, ttl=ttl)
    console.print("[green]✓[/green] [bold]Summary[/bold] complete.")

    console.print()
    console.print(
        Rule("[bold green]✓ Minimal pipeline complete[/bold green]", style="green")
    )

    return build_markdown(note_name, summary)


def run_full_pipeline(note_name: str, transcription_path: str) -> str:
    """
    Run full pipline - summary + student QA + deadline + study Qs

    Args:
        note_name (str): Name of the note to be created.
        transcription_path (str): Path to the transcription file.

    Returns:
        str: Markdown content of the note.

    Raises:
        ValueError: If the transcription file is empty.
    """
    console.print(Rule("[bold blue]Rec2Note[/bold blue] [dim]— Full Pipeline[/dim]"))
    console.print()
    job_panel = Panel(
        f"[bold]Note:[/bold]       [cyan]{note_name}[/cyan]\n"
        f"[bold]Transcript:[/bold] [dim]{transcription_path}[/dim]\n"
        f"[bold]Agents:[/bold]     summary, deadlines, study questions, student Q&A",
        title="[bold blue]Job Details[/bold blue]",
        border_style="blue",
        width=_PANEL_WIDTH,
    )
    console.print(Align.center(job_panel))

    console.print("\n[bold cyan]📄 Reading transcript...[/bold cyan]")
    transcript = read_file(transcription_path)
    if not transcript.strip():
        raise ValueError("Transcription file is empty.")
    console.print(
        f"[green]✓[/green] Transcript loaded "
        f"[dim]({len(transcript):,} characters)[/dim]"
    )

    ttl = settings.google_gemini_cache_ttl

    agents = [
        ("🤖 Running summary agent...", "Summary"),
        ("📅 Running deadline agent...", "Deadlines"),
        ("📚 Running study questions agent...", "Study questions"),
        ("🙋 Running student Q&A agent...", "Student Q&A"),
    ]
    total = len(agents)

    console.print()

    with console.status(f"[yellow]{agents[0][0]}[/yellow]", spinner="dots") as status:
        summary = summary_agent(transcript=transcript, ttl=ttl)
        console.print(
            f"[green]✓[/green] [bold]{agents[0][1]}[/bold] complete. [dim](1/{total})[/dim]"
        )

        status.update(f"[yellow]{agents[1][0]}[/yellow]")
        deadlines = deadline_agent(transcript=transcript, ttl=ttl)
        console.print(
            f"[green]✓[/green] [bold]{agents[1][1]}[/bold] complete. [dim](2/{total})[/dim]"
        )

        status.update(f"[yellow]{agents[2][0]}[/yellow]")
        study_questions = questions_agent(transcript=transcript, ttl=ttl)
        console.print(
            f"[green]✓[/green] [bold]{agents[2][1]}[/bold] complete. [dim](3/{total})[/dim]"
        )

        status.update(f"[yellow]{agents[3][0]}[/yellow]")
        student_qa = student_qa_agent(transcript=transcript, ttl=ttl)
        console.print(
            f"[green]✓[/green] [bold]{agents[3][1]}[/bold] complete. [dim](4/{total})[/dim]"
        )

    console.print()

    result_panel = Panel(
        f"[green]✓[/green] Summary\n"
        f"[green]✓[/green] {len(deadlines)} deadline(s) found\n"
        f"[green]✓[/green] {len(study_questions)} study question(s) generated\n"
        f"[green]✓[/green] {len(student_qa)} student Q&A pair(s) extracted",
        title="[bold green]Results[/bold green]",
        border_style="green",
        width=_PANEL_WIDTH,
    )
    console.print(Align.center(result_panel))
    console.print(
        Rule("[bold green]✓ Full pipeline complete[/bold green]", style="green")
    )

    return build_markdown(note_name, summary, student_qa, deadlines, study_questions)
