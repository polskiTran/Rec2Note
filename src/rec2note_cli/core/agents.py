import json
from dataclasses import asdict, dataclass
from pathlib import Path

from google.genai import types

from rec2note_cli.core.llm import call_llm, create_llm_cache

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Read a prompt file from the prompts directory and return its text."""
    path = _PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gemini-2.5-flash"


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


def _build_cache(
    transcript: str | None,
    cache_name: str | None,
    prompt_file: str,
    model_id: str,
    ttl: str,
) -> str:
    """Resolve or create a cache for the given transcript + prompt pair."""
    if not transcript and not cache_name:
        raise ValueError("Provide either 'transcript' or 'cache_name'.")
    if cache_name:
        return cache_name
    return create_llm_cache(
        model_id=model_id,
        input_data=transcript,
        sys_prompt=_load_prompt(prompt_file),
        ttl=ttl,
    )


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------


@dataclass
class VisualAidTimestamp:
    """A moment in the transcript where a visual aid is likely needed."""

    timestamp: str
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LectureTopic:
    """A topic or section covered in the lecture."""

    topic: str
    details: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class KeyTerm:
    """A key term or concept introduced in the lecture."""

    term: str
    definition: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LectureSummary:
    """Structured summary of a lecture transcript."""

    title: str
    overview: str
    key_points: list[str]
    topics: list[LectureTopic]
    key_terms: list[KeyTerm]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "overview": self.overview,
            "key_points": self.key_points,
            "topics": [t.to_dict() for t in self.topics],
            "key_terms": [k.to_dict() for k in self.key_terms],
        }


@dataclass
class Deadline:
    """A deadline or deliverable mentioned in the lecture."""

    timestamp: str
    description: str
    due_date: str | None
    type: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StudyQuestion:
    """A study question generated from the lecture content."""

    question: str
    type: str
    answer: str
    timestamp_reference: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StudentQA:
    """A genuine student question and the lecturer's answer."""

    question_timestamp: str
    question: str
    answer_timestamp: str
    answer: str

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def create_visual_aids_cache(
    transcript: str,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
) -> str:
    """
    Create a Gemini context cache for the visual aids agent.

    The visual-aids system prompt is baked into the cache so that
    ``system_instruction`` does not need to be sent with each request
    (the Gemini API forbids this when ``cached_content`` is present).

    Args:
        transcript: Full transcript text (SRT-style or similar).
        model_id:   Gemini model ID — must match the one used in
                    :func:`visual_aids_agent`.
        ttl:        Cache time-to-live, e.g. ``"3600s"``.

    Returns:
        Opaque cache name string to pass to :func:`visual_aids_agent`.
    """
    return create_llm_cache(
        model_id=model_id,
        input_data=transcript,
        sys_prompt=_load_prompt("visual_aids_search.md"),
        ttl=ttl,
    )


def create_summary_cache(
    transcript: str,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
) -> str:
    """
    Create a Gemini context cache for the summary agent.

    Args:
        transcript: Full transcript text.
        model_id:   Gemini model ID — must match the one used in
                    :func:`summary_agent`.
        ttl:        Cache time-to-live, e.g. ``"3600s"``.

    Returns:
        Opaque cache name string to pass to :func:`summary_agent`.
    """
    return create_llm_cache(
        model_id=model_id,
        input_data=transcript,
        sys_prompt=_load_prompt("summary.md"),
        ttl=ttl,
    )


def create_deadline_cache(
    transcript: str,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
) -> str:
    """
    Create a Gemini context cache for the deadline agent.

    Args:
        transcript: Full transcript text.
        model_id:   Gemini model ID — must match the one used in
                    :func:`deadline_agent`.
        ttl:        Cache time-to-live, e.g. ``"3600s"``.

    Returns:
        Opaque cache name string to pass to :func:`deadline_agent`.
    """
    return create_llm_cache(
        model_id=model_id,
        input_data=transcript,
        sys_prompt=_load_prompt("deadline.md"),
        ttl=ttl,
    )


def create_questions_cache(
    transcript: str,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
) -> str:
    """
    Create a Gemini context cache for the questions agent.

    Args:
        transcript: Full transcript text.
        model_id:   Gemini model ID — must match the one used in
                    :func:`questions_agent`.
        ttl:        Cache time-to-live, e.g. ``"3600s"``.

    Returns:
        Opaque cache name string to pass to :func:`questions_agent`.
    """
    return create_llm_cache(
        model_id=model_id,
        input_data=transcript,
        sys_prompt=_load_prompt("questions.md"),
        ttl=ttl,
    )


def create_student_qa_cache(
    transcript: str,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
) -> str:
    """
    Create a Gemini context cache for the student Q&A agent.

    Args:
        transcript: Full transcript text.
        model_id:   Gemini model ID — must match the one used in
                    :func:`student_qa_agent`.
        ttl:        Cache time-to-live, e.g. ``"3600s"``.

    Returns:
        Opaque cache name string to pass to :func:`student_qa_agent`.
    """
    return create_llm_cache(
        model_id=model_id,
        input_data=transcript,
        sys_prompt=_load_prompt("student_qa.md"),
        ttl=ttl,
    )


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


def visual_aids_agent(
    transcript: str | None = None,
    cache_name: str | None = None,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
    config: types.GenerateContentConfig | None = None,
) -> list[VisualAidTimestamp]:
    """
    Identify timestamps where visual aids are needed for comprehension.

    Args:
        transcript:  Raw transcript text.  Used to create a fresh cache when
                     ``cache_name`` is not provided.
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
    resolved = _build_cache(
        transcript, cache_name, "visual_aids_search.md", model_id, ttl
    )
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=(
            "Analyse the cached transcript and return all timestamps where "
            "visual context is needed, following the JSON schema exactly. "
        ),
        cache_name=resolved,
    )
    return _parse_visual_aids_response(raw)


def summary_agent(
    transcript: str | None = None,
    cache_name: str | None = None,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
    config: types.GenerateContentConfig | None = None,
) -> LectureSummary:
    """
    Produce a structured summary of a lecture transcript.

    Args:
        transcript:  Raw transcript text.  Used to create a fresh cache when
                     ``cache_name`` is not provided.
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
    resolved = _build_cache(transcript, cache_name, "summary.md", model_id, ttl)
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=(
            "Analyse the cached transcript and produce a comprehensive structured "
            "summary following the JSON schema exactly."
        ),
        cache_name=resolved,
    )
    return _parse_summary_response(raw)


def deadline_agent(
    transcript: str | None = None,
    cache_name: str | None = None,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
    config: types.GenerateContentConfig | None = None,
) -> list[Deadline]:
    """
    Extract all deadlines and deliverables from a lecture transcript.

    Args:
        transcript:  Raw transcript text.  Used to create a fresh cache when
                     ``cache_name`` is not provided.
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
    resolved = _build_cache(transcript, cache_name, "deadline.md", model_id, ttl)
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=(
            "Analyse the cached transcript and extract every deadline or "
            "deliverable, following the JSON schema exactly. "
            "Exclude timestamp milliseconds."
        ),
        cache_name=resolved,
    )
    return _parse_deadline_response(raw)


def questions_agent(
    transcript: str | None = None,
    cache_name: str | None = None,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
    config: types.GenerateContentConfig | None = None,
) -> list[StudyQuestion]:
    """
    Generate study questions from a lecture transcript.

    Args:
        transcript:  Raw transcript text.  Used to create a fresh cache when
                     ``cache_name`` is not provided.
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
    resolved = _build_cache(transcript, cache_name, "questions.md", model_id, ttl)
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=(
            "Analyse the cached transcript and generate a comprehensive set of "
            "study questions following the JSON schema exactly. "
            "Exclude timestamp milliseconds."
        ),
        cache_name=resolved,
    )
    return _parse_questions_response(raw)


def student_qa_agent(
    transcript: str | None = None,
    cache_name: str | None = None,
    model_id: str = DEFAULT_MODEL,
    ttl: str = "3600s",
    config: types.GenerateContentConfig | None = None,
) -> list[StudentQA]:
    """
    Extract genuine student questions and lecturer answers from a transcript.

    Only questions actually posed by students (audience members) are captured.
    Rhetorical questions and self-answered questions from the lecturer are
    excluded.  If no student questions are found, an empty list is returned.

    Args:
        transcript:  Raw transcript text.  Used to create a fresh cache when
                     ``cache_name`` is not provided.
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
    resolved = _build_cache(transcript, cache_name, "student_qa.md", model_id, ttl)
    raw = call_llm(
        model_id=model_id,
        config=_make_request_config(config),
        user_prompt=(
            "Analyse the cached transcript and extract every genuine student "
            "question with the lecturer's answer, following the JSON schema "
            "exactly. Exclude timestamp milliseconds. "
            'If no student questions exist, return {"student_questions": []}.'
        ),
        cache_name=resolved,
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
        results.append(VisualAidTimestamp(entry["timestamp"], entry["reason"]))
    return results


def _parse_summary_response(raw: str) -> LectureSummary:
    data = _parse_json(raw, "summary_agent")
    for key in ("title", "overview", "key_points", "topics", "key_terms"):
        if key not in data:
            raise ValueError(
                f"summary_agent response missing required key '{key}'. "
                f"Keys present: {list(data.keys())}"
            )
    topics = [LectureTopic(t["topic"], t["details"]) for t in data["topics"]]
    key_terms = [KeyTerm(k["term"], k["definition"]) for k in data["key_terms"]]
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
    from rec2note_cli.utils.read_file import read_file

    transcript = read_file("recordings/lecture2/Lecture6_021726.srt")
    TTL = "300s"

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    summary = summary_agent(transcript=transcript, ttl=TTL)
    print(f"Title   : {summary.title}")
    print(f"Overview: {summary.overview}\n")
    print("Key points:")
    for pt in summary.key_points:
        print(f"  - {pt}")
    print("\nTopics:")
    for t in summary.topics:
        print(f"  [{t.topic}] {t.details}")
    print("\nKey terms:")
    for k in summary.key_terms:
        print(f"  {k.term}: {k.definition}")

    print("\n" + "=" * 60)
    print("DEADLINES")
    print("=" * 60)
    deadlines = deadline_agent(transcript=transcript, ttl=TTL)
    if deadlines:
        for d in deadlines:
            print(
                f"  [{d.timestamp}] ({d.type}) {d.description} — due: {d.due_date or 'not specified'}"
            )
    else:
        print("  No deadlines found.")

    print("\n" + "=" * 60)
    print("STUDY QUESTIONS")
    print("=" * 60)
    questions = questions_agent(transcript=transcript, ttl=TTL)
    for q in questions:
        print(f"\n  [{q.type}] {q.question}")
        print(f"  Answer: {q.answer}")
        print(f"  Ref: {q.timestamp_reference}")

    print("\n" + "=" * 60)
    print("VISUAL AIDS")
    print("=" * 60)
    visual_aids = visual_aids_agent(transcript=transcript, ttl=TTL)
    for v in visual_aids:
        print(f"  [{v.timestamp}] {v.reason}")

    print("\n" + "=" * 60)
    print("STUDENT Q&A")
    print("=" * 60)
    student_qas = student_qa_agent(transcript=transcript, ttl=TTL)
    if student_qas:
        for qa in student_qas:
            print(f"\n  Q [{qa.question_timestamp}]: {qa.question}")
            print(f"  A [{qa.answer_timestamp}]: {qa.answer}")
    else:
        print("  None — no student questions found in this transcript.")
