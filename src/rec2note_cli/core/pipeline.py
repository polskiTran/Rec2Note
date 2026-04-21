import asyncio
import time
from collections.abc import Callable
from functools import partial
from typing import Any

from rec2note_cli.config import get_settings
from rec2note_cli.core.agents import (
    deadline_agent,
    questions_agent,
    student_qa_agent,
    summary_agent,
)
from rec2note_cli.core.models import Deadline, LectureSummary, StudentQA, StudyQuestion
from rec2note_cli.core.pipeline_models import AgentOutcome, PipelineResult
from rec2note_cli.enums.agent_enums import AgentType
from rec2note_cli.utils.read_file import read_file

settings = get_settings()

_PANEL_WIDTH = 106

# ---------------------------------------------------------------------------
# Type alias for progress callbacks
# ---------------------------------------------------------------------------

ProgressCallback = Callable[[AgentType, str, float], None]


# ---------------------------------------------------------------------------
# Async runner helpers
# ---------------------------------------------------------------------------


async def _run_agent_timed(
    semaphore: asyncio.Semaphore,
    agent_func: Callable,
    transcript: str,
    agent_type: AgentType,
    model_id: str | None,
    on_progress: ProgressCallback | None,
) -> tuple[AgentOutcome, Any]:
    """Run a single agent inside the semaphore and return its outcome.

    Args:
        semaphore: Concurrency limiter shared across all agents.
        agent_func: The agent callable to execute.
        transcript: Full lecture transcript text.
        agent_type: Enum value identifying the agent.
        model_id: Override model for this agent.
        on_progress: Optional callback invoked with (agent_type, status, elapsed).

    Returns:
        A tuple of (:class:`AgentOutcome`, result_payload). result_payload is
        the agent's typed return value on success, or ``None`` on failure.
    """
    async with semaphore:
        if on_progress:
            on_progress(agent_type, "running", 0.0)

        loop = asyncio.get_event_loop()
        start = time.perf_counter()
        try:
            result, usage = await loop.run_in_executor(
                None, partial(agent_func, transcript=transcript, model_id=model_id)
            )
            elapsed = time.perf_counter() - start
            if on_progress:
                on_progress(agent_type, "done", elapsed)
            return AgentOutcome(
                agent=agent_type,
                success=True,
                usage=usage,
                elapsed_seconds=elapsed,
            ), result
        except Exception as exc:
            elapsed = time.perf_counter() - start
            if on_progress:
                on_progress(agent_type, "failed", elapsed)
            return AgentOutcome(
                agent=agent_type,
                success=False,
                error=str(exc),
                elapsed_seconds=elapsed,
            ), None


# ---------------------------------------------------------------------------
# Public pipeline functions
# ---------------------------------------------------------------------------


def run_minimal_pipeline(
    note_name: str,
    transcription_path: str,
    on_progress: ProgressCallback | None = None,
) -> PipelineResult:
    """Run the minimal pipeline — summary agent only.

    Args:
        note_name: Display name for the note being created.
        transcription_path: Path to the plain-text transcript file.
        on_progress: Optional callback ``(agent_type, status, elapsed)`` invoked
            on agent state transitions (``"running"``, ``"done"``, ``"failed"``).

    Returns:
        A :class:`PipelineResult`. ``summary`` is None if the agent failed.

    Raises:
        ValueError: If the transcript file is empty.
    """
    transcript = read_file(transcription_path)
    if not transcript.strip():
        raise ValueError("Transcription file is empty.")

    pipeline_start = time.perf_counter()

    async def _run() -> PipelineResult:
        semaphore = asyncio.Semaphore(1)
        outcome: AgentOutcome
        result: LectureSummary | None
        outcome, result = await _run_agent_timed(
            semaphore,
            summary_agent,
            transcript,
            AgentType.SUMMARY,
            settings.agent_model_id[AgentType.SUMMARY],
            on_progress,
        )
        return PipelineResult(
            summary=result,
            outcomes=[outcome],
            total_elapsed_seconds=time.perf_counter() - pipeline_start,
        )

    return asyncio.run(_run())


def run_full_pipeline(
    note_name: str,
    transcription_path: str,
    on_progress: ProgressCallback | None = None,
) -> PipelineResult:
    """Run the full pipeline — summary, deadlines, study questions, student Q&A.

    The deadline agent runs first to warm the LLM prompt cache. Once it
    completes, a brief settle period allows the provider to persist the cache.
    The remaining three agents (summary, study questions, student Q&A) then run
    concurrently so they can reuse the cached prefix tokens, reducing cost.
    A failed agent does not abort the pipeline; its slot in
    :class:`PipelineResult` will hold the default (None / empty list) and the
    corresponding :class:`AgentOutcome` will have ``success=False``.

    Args:
        note_name: Display name for the note being created.
        transcription_path: Path to the plain-text transcript file.
        on_progress: Optional callback ``(agent_type, status, elapsed)`` invoked
            on agent state transitions. Status values: ``"warming_cache"``,
            ``"waiting"``, ``"running"``, ``"done"``, ``"failed"``.

    Returns:
        A :class:`PipelineResult` with whatever agents succeeded.

    Raises:
        ValueError: If the transcript file is empty.
    """
    transcript = read_file(transcription_path)
    if not transcript.strip():
        raise ValueError("Transcription file is empty.")

    pipeline_start = time.perf_counter()

    async def _run() -> PipelineResult:
        semaphore = asyncio.Semaphore(3)

        # Mark remaining agents as waiting before cache warmup begins
        if on_progress:
            on_progress(AgentType.SUMMARY, "waiting", 0.0)
            on_progress(AgentType.QUESTIONS, "waiting", 0.0)
            on_progress(AgentType.STUDENT_QA, "waiting", 0.0)

        # Phase 1: deadline agent warms the prompt cache
        warmup_callback: ProgressCallback | None = None
        if on_progress:

            def _warmup_progress(
                agent_type: AgentType, status: str, elapsed: float
            ) -> None:
                if agent_type == AgentType.DEADLINE and status == "running":
                    on_progress(agent_type, "warming_cache", elapsed)
                else:
                    on_progress(agent_type, status, elapsed)

            warmup_callback = _warmup_progress

        outcome_dl: AgentOutcome
        deadlines: list[Deadline] | None
        outcome_dl, deadlines = await _run_agent_timed(
            semaphore,
            deadline_agent,
            transcript,
            AgentType.DEADLINE,
            settings.agent_model_id[AgentType.DEADLINE],
            warmup_callback,
        )

        # Phase 2: remaining agents run concurrently (cache warm)
        outcome_summary: AgentOutcome
        summary: LectureSummary | None
        outcome_sq: AgentOutcome
        study_qs: list[StudyQuestion] | None
        outcome_qa: AgentOutcome
        student_qa: list[StudentQA] | None

        (
            (outcome_summary, summary),
            (outcome_sq, study_qs),
            (outcome_qa, student_qa),
        ) = await asyncio.gather(
            _run_agent_timed(
                semaphore,
                summary_agent,
                transcript,
                AgentType.SUMMARY,
                settings.agent_model_id[AgentType.SUMMARY],
                on_progress,
            ),
            _run_agent_timed(
                semaphore,
                questions_agent,
                transcript,
                AgentType.QUESTIONS,
                settings.agent_model_id[AgentType.QUESTIONS],
                on_progress,
            ),
            _run_agent_timed(
                semaphore,
                student_qa_agent,
                transcript,
                AgentType.STUDENT_QA,
                settings.agent_model_id[AgentType.STUDENT_QA],
                on_progress,
            ),
        )

        return PipelineResult(
            summary=summary,
            deadlines=deadlines or [],
            study_questions=study_qs or [],
            student_qa=student_qa or [],
            outcomes=[outcome_summary, outcome_dl, outcome_sq, outcome_qa],
            total_elapsed_seconds=time.perf_counter() - pipeline_start,
        )

    return asyncio.run(_run())
