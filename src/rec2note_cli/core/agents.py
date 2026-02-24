import json
from pathlib import Path

from google.genai import types

from rec2note_cli.config import get_settings
from rec2note_cli.core.llm import call_llm, create_transcript_cache
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


def _load_prompt(agentType: AgentType) -> str:
    """
    Read agent prompt from the prompts directory and return its texts.

    Args:
        agentType: The type of agent for which to load the prompt.

    Returns:
        The prompt text.
    """
    path = Path(settings.agent_instructions[agentType])
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_request_config(
    config: types.GenerateContentConfig | None,
) -> types.GenerateContentConfig:
    """Return a config with ``response_mime_type`` forced to JSON.

    ``system_instruction`` must NOT be set here — it lives inside the cache.
    """
    if config is None:
        return types.GenerateContentConfig(response_mime_type="application/json")
    return config.model_copy(update={"response_mime_type": "application/json"})


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
    cache_name: str,
    model_id: str = settings.google_gemini_model_id,
    ttl: str = settings.google_gemini_cache_ttl,
    config: types.GenerateContentConfig | None = None,
) -> list[VisualAidTimestamp]:
    """
    Identify timestamps where visual aids are needed for comprehension.

    Args:
        cache_name:  Pre-built cache from :func:`create_visual_aids_cache`.
                     When supplied, ``transcript`` and ``ttl`` are ignored.
        model_id:    Gemini model identifier.
        ttl:         Cache TTL used when creating a new cache.
        config:      Optional generation config.  ``system_instruction`` and
                     ``response_mime_type`` are managed automatically.

    Returns:
        List of :class:`VisualAidTimestamp` objects.

    Raises:
        ValueError: If neither ``transcript`` nor ``cache_name`` is given, or
                    the model response cannot be parsed.
    """
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=(
            "Analyse the cached transcript and return all timestamps where "
            "visual context is needed, following the JSON schema exactly. "
        ),
        cache_name=cache_name,
    )
    return _parse_visual_aids_response(raw)


def summary_agent(
    cache_name: str,
    model_id: str = settings.google_gemini_model_id,
    ttl: str = "3600s",
    config: types.GenerateContentConfig | None = None,
) -> LectureSummary:
    """
    Produce a structured summary of a lecture transcript.

    Args:
        cache_name:  Pre-built cache from :func:`create_summary_cache`.
                     When supplied, ``transcript`` and ``ttl`` are ignored.
        model_id:    Gemini model identifier.
        ttl:         Cache TTL used when creating a new cache.
        config:      Optional generation config.  ``system_instruction`` and
                     ``response_mime_type`` are managed automatically.

    Returns:
        A :class:`LectureSummary` with title, overview, key points, topics,
        and key terms.

    Raises:
        ValueError: If neither ``transcript`` nor ``cache_name`` is given, or
                    the model response cannot be parsed.
    """
    summary_agent_prompt = _load_prompt(AgentType.SUMMARY)
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=summary_agent_prompt,
        cache_name=cache_name,
    )
    return _parse_summary_response(raw)


def deadline_agent(
    cache_name: str,
    model_id: str = settings.google_gemini_model_id,
    ttl: str = "3600s",
    config: types.GenerateContentConfig | None = None,
) -> list[Deadline]:
    """
    Extract all deadlines and deliverables from a lecture transcript.

    Args:
        cache_name:  Pre-built cache from :func:`create_deadline_cache`.
                     When supplied, ``transcript`` and ``ttl`` are ignored.
        model_id:    Gemini model identifier.
        ttl:         Cache TTL used when creating a new cache.
        config:      Optional generation config.  ``system_instruction`` and
                     ``response_mime_type`` are managed automatically.

    Returns:
        List of :class:`Deadline` objects.

    Raises:
        ValueError: If neither ``transcript`` nor ``cache_name`` is given, or
                    the model response cannot be parsed.
    """
    deadline_agent_prompt = _load_prompt(AgentType.DEADLINE)
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=deadline_agent_prompt,
        cache_name=cache_name,
    )
    return _parse_deadline_response(raw)


def questions_agent(
    cache_name: str | None = None,
    model_id: str = settings.google_gemini_model_id,
    ttl: str = "3600s",
    config: types.GenerateContentConfig | None = None,
) -> list[StudyQuestion]:
    """
    Generate study questions from a lecture transcript.

    Args:
        cache_name:  Pre-built cache from :func:`create_questions_cache`.
                     When supplied, ``transcript`` and ``ttl`` are ignored.
        model_id:    Gemini model identifier.
        ttl:         Cache TTL used when creating a new cache.
        config:      Optional generation config.  ``system_instruction`` and
                     ``response_mime_type`` are managed automatically.

    Returns:
        List of :class:`StudyQuestion` objects.

    Raises:
        ValueError: If neither ``transcript`` nor ``cache_name`` is given, or
                    the model response cannot be parsed.
    """
    question_agent_prompt = _load_prompt(AgentType.QUESTIONS)
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=question_agent_prompt,
        cache_name=cache_name,
    )
    return _parse_questions_response(raw)


def student_qa_agent(
    cache_name: str,
    model_id: str = settings.google_gemini_model_id,
    ttl: str = "3600s",
    config: types.GenerateContentConfig | None = None,
) -> list[StudentQA]:
    """
    Extract genuine student questions and lecturer answers from a transcript.

    Only questions actually posed by students (audience members) are captured.
    Rhetorical questions and self-answered questions from the lecturer are
    excluded.  If no student questions are found, an empty list is returned.

    Args:
        cache_name:  Pre-built cache from :func:`create_student_qa_cache`.
                     When supplied, ``transcript`` and ``ttl`` are ignored.
        model_id:    Gemini model identifier.
        ttl:         Cache TTL used when creating a new cache.
        config:      Optional generation config.  ``system_instruction`` and
                     ``response_mime_type`` are managed automatically.

    Returns:
        List of :class:`StudentQA` objects, each with ``question_timestamp``,
        ``question``, ``answer_timestamp``, and ``answer``.  Returns an empty
        list when no student questions are present in the transcript.

    Raises:
        ValueError: If neither ``transcript`` nor ``cache_name`` is given, or
                    the model response cannot be parsed.
    """
    student_qa_agent_prompt = _load_prompt(AgentType.STUDENT_QA)
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=student_qa_agent_prompt,
        cache_name=cache_name,
    )
    return _parse_student_qa_response(raw)


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
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from typing import List

    from rich import print

    from rec2note_cli.utils.read_file import read_file

    # load transcript
    try:
        large_context = read_file("recordings/lecture1/Lecture5_020526.srt")
        cache_name = create_transcript_cache(
            model_id=settings.google_gemini_model_id,
            transcript=large_context,
            ttl=settings.google_gemini_cache_ttl,
        )
        print("Cache created:", cache_name)
    except Exception as e:
        print(f"Error creating cache: {e}")

    # test student_qa agent
    try:
        student_qa_agent_responses: List[StudentQA] = student_qa_agent(
            model_id=settings.google_gemini_model_id,
            cache_name=cache_name,
            ttl=settings.google_gemini_cache_ttl,
        )
        print(student_qa_agent_responses)

    except Exception as e:
        print(f"Error creating question model: {e}")
