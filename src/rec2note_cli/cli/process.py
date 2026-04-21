from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from rec2note_cli.config import get_settings
from rec2note_cli.core.pipeline import run_full_pipeline, run_minimal_pipeline
from rec2note_cli.core.pipeline_models import PipelineResult
from rec2note_cli.enums.agent_enums import AgentType
from rec2note_cli.ui import display
from rec2note_cli.utils.markdown_builder import build_markdown

settings = get_settings()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NOTES_DIR = Path("notes")

_SUPPORTED_AUDIO = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".opus"}
_SUPPORTED_VIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}

_MINIMAL_AGENTS = [AgentType.SUMMARY]
_FULL_AGENTS = [
    AgentType.SUMMARY,
    AgentType.DEADLINE,
    AgentType.QUESTIONS,
    AgentType.STUDENT_QA,
]

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
        rec2note -tr lecture.txt -m

    Full pipeline with preview:
        rec2note -tr lecture.txt -f -pr

    Full pipeline with media metadata:
        rec2note -media lecture.mp4 -tr lecture.txt -f -pr
    """
    started_at = datetime.now()

    # ── validate: at least one input ─────────────────────────────────────
    if media is None and transcript is None:
        display.abort(
            "You must supply at least one input.  "
            "Use -tr / --transcript or -media / --media."
        )

    if transcript is None:
        display.abort(
            "A transcript file is required to run the pipeline.  "
            "Supply one with -tr / --transcript."
        )

    if not transcript.exists():
        display.abort(f"Transcript file not found: {transcript}")

    if media is not None and not media.exists():
        display.abort(f"Media file not found: {media}")

    # ── validate: pipeline mode ───────────────────────────────────────────
    if minimal and full:
        display.abort("-m / --minimal and -f / --full are mutually exclusive.")

    if not minimal and not full:
        minimal = True

    # ── derive metadata ───────────────────────────────────────────────────
    source = transcript
    note_name = source.stem.replace("_", " ").replace("-", " ").title()
    timestamp = started_at.strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{source.stem}_{timestamp}.md"

    active_agents = _MINIMAL_AGENTS if minimal else _FULL_AGENTS
    mode_label = "minimal" if minimal else "full"
    agent_labels = [_label(a) for a in active_agents]

    model_summary = settings.agent_model_id.get(
        AgentType.SUMMARY, settings.llm_model_id
    )
    model_agents = settings.agent_model_id.get(
        AgentType.DEADLINE, settings.llm_model_id
    )

    # ── header ────────────────────────────────────────────────────────────
    display.print_header(
        note_name=note_name,
        transcript=transcript,
        media=media,
        mode=mode_label,
        agents=agent_labels,
        model_summary=model_summary,
        model_agents=model_agents,
        preview=preview,
        output_path=output_path,
    )

    # ── run pipeline with live progress ───────────────────────────────────
    try:
        if minimal:
            result: PipelineResult = display.run_with_live_progress(
                run_minimal_pipeline,
                active_agents,
                note_name=note_name,
                transcription_path=str(transcript),
            )
        else:
            result = display.run_with_live_progress(
                run_full_pipeline,
                active_agents,
                note_name=note_name,
                transcription_path=str(transcript),
            )
    except ValueError as exc:
        display.abort(str(exc))
    except Exception as exc:
        display.abort(
            f"Pipeline error: {exc}  —  check your API key, model, and transcript."
        )

    # ── abort if summary failed (mandatory backbone) ──────────────────────
    if result.summary is None:
        display.abort("Summary agent failed — cannot build note without a summary.")

    # ── build markdown from successful results only ───────────────────────
    markdown = build_markdown(
        note_name=note_name,
        summary=result.summary,
        student_qa=result.student_qa,
        deadline=result.deadlines,
        study_qs=result.study_questions,
    )

    # ── save ──────────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    # ── optional preview ──────────────────────────────────────────────────
    if preview:
        display.print_preview(markdown)

    # ── dashboard ─────────────────────────────────────────────────────────
    display.print_dashboard(result, output_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _label(agent: AgentType) -> str:
    labels = {
        AgentType.SUMMARY: "summary",
        AgentType.DEADLINE: "deadlines",
        AgentType.QUESTIONS: "study questions",
        AgentType.STUDENT_QA: "student q&a",
        AgentType.VISUAL_AIDS_SEARCH: "visual aids",
    }
    return labels.get(agent, agent.value)
