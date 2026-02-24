import asyncio
from collections.abc import Callable
from functools import partial

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.rule import Rule

from rec2note_cli.config import get_settings
from rec2note_cli.core.agents import (
    deadline_agent,
    questions_agent,
    student_qa_agent,
    summary_agent,
)
from rec2note_cli.core.llm import create_transcript_cache
from rec2note_cli.core.models import Deadline, LectureSummary, StudentQA, StudyQuestion
from rec2note_cli.utils.markdown_builder import build_markdown
from rec2note_cli.utils.read_file import read_file

console = Console()
settings = get_settings()

_PANEL_WIDTH = 106


async def _run_agent_with_semaphore(
    semaphore: asyncio.Semaphore,
    agent_func: Callable[
        ..., LectureSummary | list[Deadline] | list[StudentQA] | list[StudyQuestion]
    ],
    cache_name: str,
) -> LectureSummary | list[Deadline] | list[StudentQA] | list[StudyQuestion]:
    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(agent_func, cache_name=cache_name)
        )


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

    console.print("\n[bold cyan]📦 Creating transcript cache...[/bold cyan]")
    cache_name = create_transcript_cache(
        model_id=settings.google_gemini_model_id,
        transcript=transcript,
    )
    console.print(f"[green]✓[/green] Cache created: [dim]{cache_name}[/dim]")

    console.print()
    with console.status("[yellow]🤖 Running summary agent...[/yellow]", spinner="dots"):
        summary = summary_agent(cache_name=cache_name)
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

    # reading transcript and build transcript cache
    console.print("\n[bold cyan]📄 Reading transcript...[/bold cyan]")
    transcript = read_file(transcription_path)
    if not transcript.strip():
        raise ValueError("Transcription file is empty.")
    console.print(
        f"[green]✓[/green] Transcript loaded "
        f"[dim]({len(transcript):,} characters)[/dim]"
    )

    console.print("\n[bold cyan]📦 Creating transcript cache...[/bold cyan]")
    cache_name = create_transcript_cache(
        model_id=settings.google_gemini_model_id,
        transcript=transcript,
    )
    console.print(f"[green]✓[/green] Cache created: [dim]{cache_name}[/dim]")

    # call agents concurrently
    async def run_agents_with_progress(progress: Progress, tasks: dict):
        semaphore = asyncio.Semaphore(3)

        async def run_and_update(agent_func, task_key, agent_name):
            progress.update(
                tasks[task_key], description=f"[yellow]⏳ {agent_name}", completed=0
            )
            try:
                result = await _run_agent_with_semaphore(
                    semaphore, agent_func, cache_name
                )
                progress.update(
                    tasks[task_key],
                    completed=1,
                    description=f"[green]✓ {agent_name}",
                )
                return result
            except Exception:
                progress.update(
                    tasks[task_key],
                    description=f"[red]✗ {agent_name} failed",
                )
                raise

        results = await asyncio.gather(
            run_and_update(summary_agent, "summary", "Summary"),
            run_and_update(deadline_agent, "deadlines", "Deadlines"),
            run_and_update(questions_agent, "questions", "Study Questions"),
            run_and_update(student_qa_agent, "student_qa", "Student Q&A"),
            return_exceptions=True,
        )

        agent_names = ["Summary", "Deadlines", "Study Questions", "Student Q&A"]
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                raise RuntimeError(f"{agent_names[i]} failed: {result}")

        summary: LectureSummary = results[0]  # type: ignore[assignment]
        deadlines: list[Deadline] = results[1]  # type: ignore[assignment]
        study_questions: list[StudyQuestion] = results[2]  # type: ignore[assignment]
        student_qa: list[StudentQA] = results[3]  # type: ignore[assignment]

        return summary, deadlines, study_questions, student_qa

    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        tasks = {
            "summary": progress.add_task("[cyan]Summary Agent", total=1),
            "deadlines": progress.add_task("[cyan]Deadline Agent", total=1),
            "questions": progress.add_task("[cyan]Study Questions Agent", total=1),
            "student_qa": progress.add_task("[cyan]Student Q&A Agent", total=1),
        }

        summary, deadlines, study_questions, student_qa = asyncio.run(
            run_agents_with_progress(progress, tasks)
        )

    console.print("[green]✓[/green] All agents complete.")

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
