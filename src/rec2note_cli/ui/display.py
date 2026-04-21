from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import NoReturn

import typer
from rich.console import Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from rec2note_cli.core.llm_models import TokenUsage
from rec2note_cli.core.pipeline_models import AgentOutcome, PipelineResult
from rec2note_cli.enums.agent_enums import AgentType
from rec2note_cli.ui.console import console

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_AGENT_LABELS: dict[AgentType, str] = {
    AgentType.SUMMARY: "summary",
    AgentType.DEADLINE: "deadlines",
    AgentType.QUESTIONS: "study questions",
    AgentType.STUDENT_QA: "student q&a",
    AgentType.VISUAL_AIDS_SEARCH: "visual aids",
}

# _SPINNER_FRAMES = ["◐", "◑", "◒", "◓"]
_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

_LABEL_WIDTH = 20
_DIM_RULE_STYLE = "bright_black"

# ---------------------------------------------------------------------------
# Blackhole ASCII art
# ---------------------------------------------------------------------------

_BLACKHOLE = r"""

                                  ___               __
                   ________  ____|__ \ ____  ____  / /____
                  / ___/ _ \/ ___/_/ // __ \/ __ \/ __/ _ \
                 / /  /  __/ /__/ __// / / / /_/ / /_/  __/
                /_/   \___/\___/____/_/ /_/\____/\__/\___/



            ********
        ****************
      *******************
      ********************
       ********************
          \\   //  ********
           \\\//  *******
             \\\////
              |||//                       ,
              |||||                    __/
  ,,,,,,,,,,,//||||\,,,,,,,,,,,,,,,,,,o==o
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;"""

_TAGLINE = (
    "[bright_black]lecture recordings  →  structured markdown notes[/bright_black]"
)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def print_header(
    note_name: str,
    transcript: Path,
    media: Path | None,
    mode: str,
    agents: list[str],
    model_summary: str,
    model_agents: str,
    preview: bool,
    output_path: Path,
) -> None:
    """Print the blackhole art, tagline, and flat setup block.

    Args:
        note_name: Derived display name for the note.
        transcript: Path to the transcript file.
        media: Optional path to the source media file.
        mode: Human-readable pipeline mode label.
        agents: List of agent name strings that will run.
        model_summary: Model identifier used for the summary agent.
        model_agents: Model identifier used for supporting agents.
        preview: Whether preview is enabled.
        output_path: Where the markdown note will be saved.
    """
    console.print()
    console.print(_BLACKHOLE)
    console.print(_TAGLINE, justify="center")
    console.print()
    console.print(Rule(style=_DIM_RULE_STYLE))
    console.print()

    kw = 14

    def _row(key: str, value: str) -> None:
        console.print(
            f"  [r2n.muted]{key:<{kw}}[/r2n.muted]  [r2n.value]{value}[/r2n.value]"
        )

    _row("note", note_name)
    _row("transcript", str(transcript))
    if media:
        _row("media", str(media))
    _row("mode", mode)
    _row("agents", "  ·  ".join(agents))
    _row("model", model_summary)
    if model_agents != model_summary:
        _row("model (agents)", model_agents)
    _row("output", str(output_path))
    _row("started", datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
    if preview:
        _row("preview", "on")

    console.print()
    console.print(Rule(style=_DIM_RULE_STYLE))
    console.print()


# ---------------------------------------------------------------------------
# Live progress block
# ---------------------------------------------------------------------------


class AgentProgressTracker:
    """Thread-safe state container for the live progress display.

    Attributes:
        _states: Maps AgentType to current status string.
        _elapsed: Maps AgentType to elapsed seconds.
        _start_times: Maps AgentType to perf_counter start (when running).
        _lock: Mutex for thread-safe updates from asyncio executor threads.
    """

    _ACTIVE_STATUSES = {"running", "warming_cache"}

    def __init__(self, agents: list[AgentType]) -> None:
        self._states: dict[AgentType, str] = {a: "pending" for a in agents}
        self._elapsed: dict[AgentType, float] = {a: 0.0 for a in agents}
        self._errors: dict[AgentType, str] = {}
        self._start_times: dict[AgentType, float] = {}
        self._lock = threading.Lock()

    def update(self, agent: AgentType, status: str, elapsed: float) -> None:
        """Update state from the pipeline's progress callback."""
        with self._lock:
            self._states[agent] = status
            if status in self._ACTIVE_STATUSES:
                self._start_times[agent] = time.perf_counter()
            else:
                self._elapsed[agent] = elapsed

    def set_error(self, agent: AgentType, error: str) -> None:
        with self._lock:
            self._errors[agent] = error

    def render(self) -> Group:
        """Build the renderable group representing the current progress state."""
        lines: list[Text | str] = []
        now = time.perf_counter()
        with self._lock:
            for agent, status in self._states.items():
                label = _AGENT_LABELS.get(agent, agent.value)
                t = Text()

                if status == "pending":
                    t.append(f"  {'·':2}  ", style="bright_black")
                    t.append(f"{label:<{_LABEL_WIDTH}}", style="bright_black")
                    t.append("  —", style="bright_black")

                elif status == "waiting":
                    t.append(f"  {'·':2}  ", style="bright_black")
                    t.append(f"{label:<{_LABEL_WIDTH}}", style="dim cyan")
                    t.append("  queued", style="dim cyan")

                elif status == "warming_cache":
                    frame_idx = int(now * 6) % len(_SPINNER_FRAMES)
                    spinner = _SPINNER_FRAMES[frame_idx]
                    elapsed = now - self._start_times.get(agent, now)
                    t.append(f"  {spinner}   ", style="yellow")
                    t.append(f"{label:<{_LABEL_WIDTH}}", style="yellow")
                    t.append(f"  {elapsed:.1f}s  warming cache", style="dim yellow")

                elif status == "running":
                    frame_idx = int(now * 6) % len(_SPINNER_FRAMES)
                    spinner = _SPINNER_FRAMES[frame_idx]
                    elapsed = now - self._start_times.get(agent, now)
                    t.append(f"  {spinner}   ", style="cyan")
                    t.append(f"{label:<{_LABEL_WIDTH}}", style="white")
                    t.append(f"  {elapsed:.1f}s", style="bright_black")

                elif status == "done":
                    elapsed = self._elapsed.get(agent, 0.0)
                    t.append(f"  {'✓':2}  ", style="green")
                    t.append(f"{label:<{_LABEL_WIDTH}}", style="green")
                    t.append(f"  {elapsed:.1f}s", style="bright_black")

                elif status == "failed":
                    elapsed = self._elapsed.get(agent, 0.0)
                    err = self._errors.get(agent, "")
                    short_err = (err[:42] + "…") if len(err) > 42 else err
                    t.append(f"  {'✗':2}  ", style="red")
                    t.append(f"{label:<{_LABEL_WIDTH}}", style="red")
                    t.append(f"  {elapsed:.1f}s", style="bright_black")
                    if short_err:
                        t.append(f"  [{short_err}]", style="dim red")

                lines.append(t)

        return Group(*lines)


def run_with_live_progress(
    pipeline_func,
    agents: list[AgentType],
    **kwargs,
) -> PipelineResult:
    """Run a pipeline function while rendering live progress to the terminal.

    Args:
        pipeline_func: ``run_minimal_pipeline`` or ``run_full_pipeline``.
        agents: The agents this pipeline will invoke.
        **kwargs: Forwarded to ``pipeline_func``.

    Returns:
        The :class:`PipelineResult` from the pipeline.
    """
    tracker = AgentProgressTracker(agents)

    def _callback(agent_type: AgentType, status: str, elapsed: float) -> None:
        tracker.update(agent_type, status, elapsed)

    result_holder: list[PipelineResult] = []
    exc_holder: list[Exception] = []

    def _target() -> None:
        try:
            result = pipeline_func(on_progress=_callback, **kwargs)
            result_holder.append(result)
        except Exception as exc:
            exc_holder.append(exc)

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()

    with Live(tracker.render(), console=console, refresh_per_second=10) as live:
        while thread.is_alive():
            live.update(tracker.render())
            time.sleep(0.1)
        live.update(tracker.render())

    thread.join()

    if exc_holder:
        raise exc_holder[0]

    result = result_holder[0]

    for outcome in result.outcomes:
        if not outcome.success and outcome.error:
            tracker.set_error(outcome.agent, outcome.error)

    console.print()
    return result


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


def print_preview(markdown_content: str) -> None:
    """Render the generated markdown in the terminal.

    Args:
        markdown_content: The full markdown string to render.
    """
    console.print()
    console.print(Rule("[bright_black]preview[/bright_black]", style=_DIM_RULE_STYLE))
    console.print()
    console.print(
        Panel(
            Markdown(markdown_content),
            border_style="bright_black",
            padding=(1, 2),
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Usage dashboard
# ---------------------------------------------------------------------------


def _fmt_tokens(n: int | None) -> str:
    if n is None:
        return "—"
    return f"{n:,}"


def print_dashboard(result: PipelineResult, output_path: Path) -> None:
    """Print the post-run token usage dashboard and result summary.

    Args:
        result: The completed :class:`PipelineResult`.
        output_path: Path where the note was saved.
    """
    console.print(Rule("[bright_black]usage[/bright_black]", style=_DIM_RULE_STYLE))
    console.print()

    outcome_map: dict[AgentType, AgentOutcome] = {o.agent: o for o in result.outcomes}

    col_agent = 20
    col_num = 10

    header = Text()
    header.append(f"  {'agent':<{col_agent}}", style="bright_black")
    header.append(f"{'prompt':>{col_num}}", style="bright_black")
    header.append(f"{'cached':>{col_num}}", style="bright_black")
    header.append(f"{'compl.':>{col_num}}", style="bright_black")
    header.append(f"{'total':>{col_num}}", style="bright_black")
    console.print(header)
    console.print(f"  {'─' * (col_agent + col_num * 4)}", style="bright_black")

    totals = TokenUsage(
        prompt_tokens=0, completion_tokens=0, total_tokens=0, cached_tokens=0
    )
    any_usage = False

    for agent_type in AgentType:
        if agent_type not in outcome_map:
            continue
        outcome = outcome_map[agent_type]
        label = _AGENT_LABELS.get(agent_type, agent_type.value)
        row = Text()
        row.append(
            f"  {label:<{col_agent}}",
            style="white" if outcome.success else "bright_black",
        )

        if outcome.success and outcome.usage:
            u = outcome.usage
            row.append(f"{_fmt_tokens(u.prompt_tokens):>{col_num}}", style="dim white")
            row.append(f"{_fmt_tokens(u.cached_tokens):>{col_num}}", style="cyan")
            row.append(
                f"{_fmt_tokens(u.completion_tokens):>{col_num}}", style="dim white"
            )
            row.append(f"{_fmt_tokens(u.total_tokens):>{col_num}}", style="white")
            totals.prompt_tokens += u.prompt_tokens
            totals.completion_tokens += u.completion_tokens
            totals.total_tokens += u.total_tokens
            totals.cached_tokens += u.cached_tokens
            any_usage = True
        else:
            dash = f"{'—':>{col_num}}"
            row.append(dash * 4, style="bright_black")
            row.append("  ✗", style="red")

        console.print(row)

    if any_usage:
        console.print(f"  {'─' * (col_agent + col_num * 4)}", style="bright_black")
        total_row = Text()
        total_row.append(f"  {'total':<{col_agent}}", style="bright_black")
        total_row.append(
            f"{_fmt_tokens(totals.prompt_tokens):>{col_num}}", style="dim white"
        )
        total_row.append(
            f"{_fmt_tokens(totals.cached_tokens):>{col_num}}", style="cyan"
        )
        total_row.append(
            f"{_fmt_tokens(totals.completion_tokens):>{col_num}}", style="dim white"
        )
        total_row.append(
            f"{_fmt_tokens(totals.total_tokens):>{col_num}}", style="bold white"
        )
        console.print(total_row)

    console.print()

    if any_usage and totals.prompt_tokens > 0:
        hit_rate = totals.cached_tokens / totals.prompt_tokens * 100
        console.print(
            Rule("[bright_black]insights[/bright_black]", style=_DIM_RULE_STYLE)
        )
        console.print()
        kw = 20
        console.print(
            f"  [bright_black]{'cache hit rate':<{kw}}[/bright_black]"
            f"  [cyan]{hit_rate:.1f}%[/cyan]"
        )
        console.print()

    console.print(Rule("[bright_black]result[/bright_black]", style=_DIM_RULE_STYLE))
    console.print()

    total_s = result.total_elapsed_seconds
    elapsed_str = (
        f"{int(total_s) // 60}m {int(total_s) % 60}s"
        if total_s >= 60
        else f"{total_s:.1f}s"
    )

    kw = 14
    console.print(
        f"  [bright_black]{'saved':<{kw}}[/bright_black]  [white]{output_path}[/white]"
    )
    console.print(
        f"  [bright_black]{'elapsed':<{kw}}[/bright_black]"
        f"  [white]{elapsed_str}[/white]"
    )
    console.print(
        f"  [bright_black]{'agents':<{kw}}[/bright_black]"
        f"  [white]{result.succeeded_count}[/white][bright_black]/{result.total_count} succeeded[/bright_black]"
    )
    console.print()
    console.print(Rule(style=_DIM_RULE_STYLE))
    console.print()


# ---------------------------------------------------------------------------
# Error / abort
# ---------------------------------------------------------------------------


def abort(message: str) -> NoReturn:
    """Print a minimal error block and exit with code 1.

    Args:
        message: Human-readable description of the error.
    """
    console.print()
    console.print(f"  [red]✗[/red]  [white]{message}[/white]")
    console.print()
    raise typer.Exit(code=1)
