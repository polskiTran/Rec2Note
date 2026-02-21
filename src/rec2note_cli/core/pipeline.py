"""Orchestrates transcript -> agents -> DB and returns LectureNoteResult."""

from collections.abc import Callable
from pathlib import Path

from rec2note_cli.config import get_settings
from rec2note_cli.core import db
from rec2note_cli.core.agents import (
    deadline_agent,
    questions_agent,
    student_qa_agent,
    summary_agent,
    visual_aids_agent,
)
from rec2note_cli.core.models import LectureNoteResult
from rec2note_cli.utils.read_file import read_file

settings = get_settings()


def run_pipeline(
    name: str,
    media_path: str,
    transcription_path: str | None,
    progress_callback: Callable[[str], None] | None = None,
) -> LectureNoteResult:
    """
    Load transcript, run all agents, save to DB, and return the result.

    If transcription_path is None or empty, raises ValueError (transcription
    required for now).
    """
    if not transcription_path or not Path(transcription_path).exists():
        raise ValueError(
            "A path to an existing transcription file is required. "
            "Provide a .srt or .txt path."
        )
    media = Path(media_path)
    if not media.exists():
        raise ValueError(f"Media path does not exist: {media_path}")

    def step(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    step("Reading transcript...")
    transcript = read_file(transcription_path)
    if not transcript.strip():
        raise ValueError("Transcription file is empty.")

    ttl = settings.google_gemini_cache_ttl

    step("Running summary agent...")
    summary = summary_agent(transcript=transcript, ttl=ttl)
    step("Running deadline agent...")
    deadlines = deadline_agent(transcript=transcript, ttl=ttl)
    step("Running study questions agent...")
    study_questions = questions_agent(transcript=transcript, ttl=ttl)
    step("Running student Q&A agent...")
    student_qa = student_qa_agent(transcript=transcript, ttl=ttl)
    step("Running visual aids agent...")
    visual_aids = visual_aids_agent(transcript=transcript, ttl=ttl)

    result = LectureNoteResult(
        name=name,
        media_path=media_path,
        transcription_path=transcription_path,
        summary=summary,
        deadlines=deadlines,
        study_questions=study_questions,
        student_qa=student_qa,
        visual_aids=visual_aids,
    )

    step("Saving to database...")
    db.init_db()
    db.save_note(
        name=name,
        media_path=media_path,
        transcription_path=transcription_path,
        summary=summary,
        deadlines=deadlines,
        study_questions=study_questions,
        student_qa=student_qa,
        visual_aids=visual_aids,
    )
    step("Done.")
    return result
