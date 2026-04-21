from pydantic import BaseModel

from rec2note_cli.core.llm_models import TokenUsage
from rec2note_cli.core.models import Deadline, LectureSummary, StudentQA, StudyQuestion
from rec2note_cli.enums.agent_enums import AgentType


# ---------------------------------------------------------------------------
# Per-agent outcome
# ---------------------------------------------------------------------------


class AgentOutcome(BaseModel):
    """Record of a single agent's execution within a pipeline run.

    Attributes:
        agent: Which agent produced this outcome.
        success: Whether the agent completed without error.
        error: Human-readable error description when ``success`` is False.
        usage: Token usage from the LLM call, or None on failure.
        elapsed_seconds: Wall-clock seconds the agent took to complete.
    """

    agent: AgentType
    success: bool
    error: str | None = None
    usage: TokenUsage | None = None
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict:
        return self.model_dump()


# ---------------------------------------------------------------------------
# Full pipeline result
# ---------------------------------------------------------------------------


class PipelineResult(BaseModel):
    """Aggregated result returned by the pipeline after all agents run.

    Attributes:
        summary: Lecture summary, or None if the summary agent failed.
        deadlines: Extracted deadlines (empty if the agent failed).
        study_questions: Generated study questions (empty if the agent failed).
        student_qa: Extracted student Q&A pairs (empty if the agent failed).
        outcomes: One :class:`AgentOutcome` per agent that was invoked.
        total_elapsed_seconds: Wall-clock time for the full pipeline run.
    """

    summary: LectureSummary | None = None
    deadlines: list[Deadline] = []
    study_questions: list[StudyQuestion] = []
    student_qa: list[StudentQA] = []
    outcomes: list[AgentOutcome] = []
    total_elapsed_seconds: float = 0.0

    def to_dict(self) -> dict:
        return self.model_dump()

    @property
    def succeeded_count(self) -> int:
        """Number of agents that completed successfully."""
        return sum(1 for o in self.outcomes if o.success)

    @property
    def total_count(self) -> int:
        """Total number of agents that were invoked."""
        return len(self.outcomes)
