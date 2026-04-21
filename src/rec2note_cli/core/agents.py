import json
from pathlib import Path

from rec2note_cli.config import get_settings
from rec2note_cli.core.llm import call_llm
from rec2note_cli.core.llm_models import TokenUsage
from rec2note_cli.core.models import (
    Deadline,
    KeyTerm,
    LectureSummary,
    LectureTopic,
    StudentQA,
    StudyQuestion,
    VisualAidTimestamp,
)
from rec2note_cli.enums.agent_enums import AgentType

settings = get_settings()


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------


def _load_prompt(agent_type: AgentType) -> str:
    """Read agent task instructions from the prompts directory.

    Args:
        agent_type: The type of agent for which to load the prompt.

    Returns:
        The task instruction text.
    """
    path = Path(settings.agent_instructions[agent_type])
    return path.read_text(encoding="utf-8")


def _load_shared_system_prompt() -> str:
    """Read the shared system prompt used by all agents for prompt caching.

    Returns:
        The shared system instruction text.
    """
    path = Path(settings.shared_system_prompt_path)
    return path.read_text(encoding="utf-8")


_SHARED_SYSTEM_PROMPT: str | None = None


def _get_shared_system_prompt() -> str:
    """Return the cached shared system prompt, loading it on first access."""
    global _SHARED_SYSTEM_PROMPT
    if _SHARED_SYSTEM_PROMPT is None:
        _SHARED_SYSTEM_PROMPT = _load_shared_system_prompt()
    return _SHARED_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _parse_json(raw: str, context: str = "agent") -> dict:
    """Parse a JSON string, raising ``ValueError`` on failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{context} returned non-JSON response:\n{raw}") from exc


def _require_key(data: dict, key: str, context: str = "response") -> list:
    """Return ``data[key]`` or raise ``ValueError`` if missing."""
    if key not in data:
        raise ValueError(
            f"Expected key '{key}' not found in {context}. "
            f"Keys present: {list(data.keys())}"
        )
    return data[key]


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


def visual_aids_agent(
    transcript: str,
    model_id: str | None = None,
) -> tuple[list[VisualAidTimestamp], TokenUsage]:
    """Identify timestamps where visual aids are needed for comprehension.

    Args:
        transcript: The full lecture transcript text.
        model_id: Override the default model from settings.

    Returns:
        Tuple of (list of :class:`VisualAidTimestamp`, :class:`TokenUsage`).

    Raises:
        ValueError: If the model response cannot be parsed.
    """
    prompt = _load_prompt(AgentType.VISUAL_AIDS_SEARCH)
    shared = _get_shared_system_prompt()
    response = call_llm(
        system_prompt=shared,
        user_prompt=transcript,
        task_prompt=prompt,
        model_id=model_id,
    )
    return _parse_visual_aids_response(response.content), response.usage


def summary_agent(
    transcript: str,
    model_id: str | None = None,
) -> tuple[LectureSummary, TokenUsage]:
    """Produce a structured summary of a lecture transcript.

    Args:
        transcript: The full lecture transcript text.
        model_id: Override the default model from settings.

    Returns:
        Tuple of (:class:`LectureSummary`, :class:`TokenUsage`).

    Raises:
        ValueError: If the model response cannot be parsed.
    """
    prompt = _load_prompt(AgentType.SUMMARY)
    shared = _get_shared_system_prompt()
    response = call_llm(
        system_prompt=shared,
        user_prompt=transcript,
        task_prompt=prompt,
        model_id=model_id,
    )
    return _parse_summary_response(response.content), response.usage


def deadline_agent(
    transcript: str,
    model_id: str | None = None,
) -> tuple[list[Deadline], TokenUsage]:
    """Extract all deadlines and deliverables from a lecture transcript.

    Args:
        transcript: The full lecture transcript text.
        model_id: Override the default model from settings.

    Returns:
        Tuple of (list of :class:`Deadline`, :class:`TokenUsage`).

    Raises:
        ValueError: If the model response cannot be parsed.
    """
    prompt = _load_prompt(AgentType.DEADLINE)
    shared = _get_shared_system_prompt()
    response = call_llm(
        system_prompt=shared,
        user_prompt=transcript,
        task_prompt=prompt,
        model_id=model_id,
    )
    return _parse_deadline_response(response.content), response.usage


def questions_agent(
    transcript: str,
    model_id: str | None = None,
) -> tuple[list[StudyQuestion], TokenUsage]:
    """Generate study questions from a lecture transcript.

    Args:
        transcript: The full lecture transcript text.
        model_id: Override the default model from settings.

    Returns:
        Tuple of (list of :class:`StudyQuestion`, :class:`TokenUsage`).

    Raises:
        ValueError: If the model response cannot be parsed.
    """
    prompt = _load_prompt(AgentType.QUESTIONS)
    shared = _get_shared_system_prompt()
    response = call_llm(
        system_prompt=shared,
        user_prompt=transcript,
        task_prompt=prompt,
        model_id=model_id,
    )
    return _parse_questions_response(response.content), response.usage


def student_qa_agent(
    transcript: str,
    model_id: str | None = None,
) -> tuple[list[StudentQA], TokenUsage]:
    """Extract genuine student questions and lecturer answers from a transcript.

    Only questions actually posed by students (audience members) are captured.
    Rhetorical questions and self-answered questions from the lecturer are
    excluded.  If no student questions are found, an empty list is returned.

    Args:
        transcript: The full lecture transcript text.
        model_id: Override the default model from settings.

    Returns:
        Tuple of (list of :class:`StudentQA`, :class:`TokenUsage`).
        Returns an empty list when no student questions are present.

    Raises:
        ValueError: If the model response cannot be parsed.
    """
    prompt = _load_prompt(AgentType.STUDENT_QA)
    shared = _get_shared_system_prompt()
    response = call_llm(
        system_prompt=shared,
        user_prompt=transcript,
        task_prompt=prompt,
        model_id=model_id,
    )
    return _parse_student_qa_response(response.content), response.usage


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------


def _parse_visual_aids_response(raw: str) -> list[VisualAidTimestamp]:
    data = _parse_json(raw, "visual_aids_agent")
    entries = _require_key(
        data, "timestamps_needing_context", "visual_aids_agent response"
    )
    results: list[VisualAidTimestamp] = []
    for i, entry in enumerate(entries):
        if "timestamp" not in entry or "reason" not in entry:
            raise ValueError(
                f"Entry {i} is missing 'timestamp' or 'reason' fields: {entry}"
            )
        results.append(
            VisualAidTimestamp(timestamp=entry["timestamp"], reason=entry["reason"])
        )
    return results


def _parse_summary_response(raw: str) -> LectureSummary:
    data = _parse_json(raw, "summary_agent")
    for key in ("title", "overview", "key_points", "topics", "key_terms"):
        if key not in data:
            raise ValueError(
                f"summary_agent response missing required key '{key}'. "
                f"Keys present: {list(data.keys())}"
            )
    topics = [
        LectureTopic(topic=t["topic"], details=t["details"]) for t in data["topics"]
    ]
    key_terms = [
        KeyTerm(term=k["term"], definition=k["definition"]) for k in data["key_terms"]
    ]
    return LectureSummary(
        title=data["title"],
        overview=data["overview"],
        key_points=data["key_points"],
        topics=topics,
        key_terms=key_terms,
    )


def _parse_deadline_response(raw: str) -> list[Deadline]:
    data = _parse_json(raw, "deadline_agent")
    entries = _require_key(data, "deadlines", "deadline_agent response")
    results: list[Deadline] = []
    for i, entry in enumerate(entries):
        for field in ("timestamp", "description", "type"):
            if field not in entry:
                raise ValueError(
                    f"Deadline entry {i} is missing required field '{field}': {entry}"
                )
        results.append(
            Deadline(
                timestamp=entry["timestamp"],
                description=entry["description"],
                due_date=entry.get("due_date"),
                type=entry["type"],
            )
        )
    return results


def _parse_questions_response(raw: str) -> list[StudyQuestion]:
    data = _parse_json(raw, "questions_agent")
    entries = _require_key(data, "questions", "questions_agent response")
    results: list[StudyQuestion] = []
    for i, entry in enumerate(entries):
        for field in ("question", "type", "answer", "timestamp_reference"):
            if field not in entry:
                raise ValueError(
                    f"Question entry {i} is missing required field '{field}': {entry}"
                )
        results.append(
            StudyQuestion(
                question=entry["question"],
                type=entry["type"],
                answer=entry["answer"],
                timestamp_reference=entry["timestamp_reference"],
            )
        )
    return results


def _parse_student_qa_response(raw: str) -> list[StudentQA]:
    data = _parse_json(raw, "student_qa_agent")
    entries = _require_key(data, "student_questions", "student_qa_agent response")
    results: list[StudentQA] = []
    for i, entry in enumerate(entries):
        for field in ("question_timestamp", "question", "answer_timestamp", "answer"):
            if field not in entry:
                raise ValueError(
                    f"StudentQA entry {i} is missing required field '{field}': {entry}"
                )
        results.append(
            StudentQA(
                question_timestamp=entry["question_timestamp"],
                question=entry["question"],
                answer_timestamp=entry["answer_timestamp"],
                answer=entry["answer"],
            )
        )
    return results


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from rec2note_cli.utils.read_file import read_file

    try:
        transcript = read_file("recordings/lecture1/Lecture5_020526.srt")
    except Exception:
        transcript = "This is a sample transcript for testing."

    try:
        result, usage = summary_agent(transcript=transcript)
        print("Summary:", result)
        print("Usage:", usage)
    except Exception as e:
        print(f"Error: {e}")
