"""SQLite storage for lecture notes (response JSON from agents)."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from rec2note_cli.core.models import (
    Deadline,
    LectureSummary,
    StudentQA,
    StudyQuestion,
    VisualAidTimestamp,
)

# DB file under project root data/ (src/rec2note_cli/core/db.py -> 4 levels up = repo root)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_DIR = _REPO_ROOT / "data"
DB_PATH = DB_DIR / "rec2note.db"


def _get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db() -> None:
    """Create the lecture_notes table if it does not exist."""
    sql = """
    CREATE TABLE IF NOT EXISTS lecture_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        media_path TEXT NOT NULL,
        transcription_path TEXT,
        created_at TEXT NOT NULL,
        summary_json TEXT NOT NULL,
        deadlines_json TEXT NOT NULL,
        study_questions_json TEXT NOT NULL,
        student_qa_json TEXT NOT NULL,
        visual_aids_json TEXT NOT NULL
    )
    """
    with _get_connection() as conn:
        conn.execute(sql)
        conn.commit()


class LectureNoteRow(NamedTuple):
    """One row from the DB for listing (id, name, created_at)."""

    id: int
    name: str
    created_at: str


class LectureNoteRecord(NamedTuple):
    """Full record loaded from DB."""

    id: int
    name: str
    media_path: str
    transcription_path: str | None
    created_at: str
    summary: LectureSummary
    deadlines: list[Deadline]
    study_questions: list[StudyQuestion]
    student_qa: list[StudentQA]
    visual_aids: list[VisualAidTimestamp]


def save_note(
    name: str,
    media_path: str,
    transcription_path: str | None,
    summary: LectureSummary,
    deadlines: list[Deadline],
    study_questions: list[StudyQuestion],
    student_qa: list[StudentQA],
    visual_aids: list[VisualAidTimestamp],
) -> int:
    """Insert a lecture note and return its id."""
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary_json = summary.model_dump_json()
    deadlines_json = json.dumps([d.model_dump() for d in deadlines])
    study_questions_json = json.dumps([q.model_dump() for q in study_questions])
    student_qa_json = json.dumps([q.model_dump() for q in student_qa])
    visual_aids_json = json.dumps([v.model_dump() for v in visual_aids])

    with _get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO lecture_notes (
                name, media_path, transcription_path, created_at,
                summary_json, deadlines_json, study_questions_json,
                student_qa_json, visual_aids_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                media_path,
                transcription_path,
                created_at,
                summary_json,
                deadlines_json,
                study_questions_json,
                student_qa_json,
                visual_aids_json,
            ),
        )
        conn.commit()
        return cur.lastrowid or 0


def get_all_notes() -> list[LectureNoteRow]:
    """Return all notes as (id, name, created_at) for listing."""
    init_db()
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, created_at FROM lecture_notes ORDER BY created_at DESC"
        ).fetchall()
    return [LectureNoteRow(id=r[0], name=r[1], created_at=r[2]) for r in rows]


def _parse_note_row(row: tuple) -> LectureNoteRecord:
    (
        id_,
        name,
        media_path,
        transcription_path,
        created_at,
        summary_json,
        deadlines_json,
        study_questions_json,
        student_qa_json,
        visual_aids_json,
    ) = row
    summary = LectureSummary.model_validate_json(summary_json)
    deadlines = [Deadline.model_validate(d) for d in json.loads(deadlines_json)]
    study_questions = [
        StudyQuestion.model_validate(q) for q in json.loads(study_questions_json)
    ]
    student_qa = [StudentQA.model_validate(q) for q in json.loads(student_qa_json)]
    visual_aids = [
        VisualAidTimestamp.model_validate(v) for v in json.loads(visual_aids_json)
    ]
    return LectureNoteRecord(
        id=id_,
        name=name,
        media_path=media_path,
        transcription_path=transcription_path,
        created_at=created_at,
        summary=summary,
        deadlines=deadlines,
        study_questions=study_questions,
        student_qa=student_qa,
        visual_aids=visual_aids,
    )


def get_note_by_id(note_id: int) -> LectureNoteRecord | None:
    """Load a single note by id."""
    init_db()
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, media_path, transcription_path, created_at, "
            "summary_json, deadlines_json, study_questions_json, "
            "student_qa_json, visual_aids_json FROM lecture_notes WHERE id = ?",
            (note_id,),
        ).fetchone()
    if row is None:
        return None
    return _parse_note_row(row)


def delete_note(note_id: int) -> bool:
    """Delete a note by id. Returns True if a row was deleted."""
    with _get_connection() as conn:
        cur = conn.execute("DELETE FROM lecture_notes WHERE id = ?", (note_id,))
        conn.commit()
        return cur.rowcount > 0
