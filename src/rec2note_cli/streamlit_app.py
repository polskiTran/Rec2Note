"""Streamlit UI for Rec2Note: add, preview, browse, and view lecture notes with media."""

from pathlib import Path

import streamlit as st

from rec2note_cli.core import db
from rec2note_cli.core.models import LectureNoteResult
from rec2note_cli.core.pipeline import run_pipeline
from rec2note_cli.utils.timestamp import timestamp_to_seconds

# Video and audio extensions for media player choice
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}

# Session state keys
KEY_PREVIEW_RESULT = "preview_result"
KEY_VIDEO_SEEK_SECONDS = "video_seek_seconds"
KEY_CURRENT_NOTE_ID = "current_note_id"
KEY_PAGE = "page"

PAGE_ADD = "Add note"
PAGE_PREVIEW = "Preview"
PAGE_BROWSE = "Browse"
PAGE_DETAIL = "Note view"


def _record_to_result(record: db.LectureNoteRecord) -> LectureNoteResult:
    """Build LectureNoteResult from a DB record."""
    return LectureNoteResult(
        name=record.name,
        media_path=record.media_path,
        transcription_path=record.transcription_path,
        summary=record.summary,
        deadlines=record.deadlines,
        study_questions=record.study_questions,
        student_qa=record.student_qa,
        visual_aids=record.visual_aids,
    )


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def _is_audio(path: str) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTENSIONS


def _render_note_markdown(result: LectureNoteResult) -> None:
    """Render lecture note as markdown (summary, deadlines, study questions, student Q&A)."""
    s = result.summary
    st.markdown(f"# {s.title}")
    st.markdown("## Overview")
    st.markdown(s.overview)
    st.markdown("## Key points")
    for pt in s.key_points:
        st.markdown(f"- {pt}")
    st.markdown("## Topics")
    for t in s.topics:
        st.markdown(f"**{t.topic}** — {t.details}")
    st.markdown("## Key terms")
    for k in s.key_terms:
        st.markdown(f"- **{k.term}**: {k.definition}")

    if result.deadlines:
        st.markdown("## Deadlines")
        for d in result.deadlines:
            due = f" — due: {d.due_date}" if d.due_date else ""
            st.markdown(f"- [{d.timestamp}] ({d.type}) {d.description}{due}")

    if result.study_questions:
        st.markdown("## Study questions")
        for q in result.study_questions:
            st.markdown(f"**[{q.type}]** {q.question}")
            st.markdown(f"  Answer: {q.answer}")
            st.markdown(f"  Ref: {q.timestamp_reference}")

    if result.student_qa:
        st.markdown("## Student Q&A")
        for qa in result.student_qa:
            st.markdown(f"**Q** [{qa.question_timestamp}]: {qa.question}")
            st.markdown(f"**A** [{qa.answer_timestamp}]: {qa.answer}")


def _render_visual_aids_with_buttons(result: LectureNoteResult) -> None:
    """Render visual aids section with clickable buttons that seek media."""
    if not result.visual_aids:
        st.markdown("## Visual aids")
        st.caption("None")
        return
    st.markdown("## Visual aids (click to jump in media)")
    for v in result.visual_aids:
        if st.button(
            f"{v.timestamp} — {v.reason}",
            key=f"va_{v.timestamp}_{hash(v.reason) % 10**6}",
        ):
            sec = timestamp_to_seconds(v.timestamp)
            st.session_state[KEY_VIDEO_SEEK_SECONDS] = sec
            st.rerun()


def page_add() -> None:
    st.header("Add new lecture note")
    st.caption("Transcription path is required for processing (.srt or .txt).")

    with st.form("add_note_form"):
        name = st.text_input("Lecture name", placeholder="e.g. CS101 Week 3")
        media_path = st.text_input(
            "Path to media (audio or video)",
            placeholder="/path/to/recording.mp4",
        )
        transcription_path = st.text_input(
            "Path to transcription (.srt or .txt)",
            placeholder="/path/to/transcript.srt",
        )
        submitted = st.form_submit_button("Submit")

    if not submitted:
        return

    name = (name or "").strip()
    media_path = (media_path or "").strip()
    transcription_path = (transcription_path or "").strip() or None

    if not name:
        st.error("Please enter a lecture name.")
        return
    if not media_path:
        st.error("Please enter a path to the media file.")
        return
    if not Path(media_path).exists():
        st.error(f"Media path does not exist: {media_path}")
        return
    if not transcription_path:
        st.error("A transcription file is required. Provide a path to .srt or .txt.")
        return
    if not Path(transcription_path).exists():
        st.error(f"Transcription path does not exist: {transcription_path}")
        return

    progress_placeholder = st.empty()
    messages: list[str] = []

    def on_progress(msg: str) -> None:
        messages.append(msg)
        progress_placeholder.markdown("\n".join(messages))

    with st.status("Processing...", expanded=True) as status:
        try:
            result = run_pipeline(
                name=name,
                media_path=media_path,
                transcription_path=transcription_path,
                progress_callback=on_progress,
            )
            st.session_state[KEY_PREVIEW_RESULT] = result
            st.session_state[KEY_VIDEO_SEEK_SECONDS] = 0
            status.update(label="Done.", state="complete")
        except Exception as e:
            st.error(str(e))
            status.update(label="Error", state="error")
            return

    st.success("Note saved. You can Preview it or Browse lecture notes.")
    if st.button("Go to Preview"):
        st.session_state[KEY_PAGE] = PAGE_PREVIEW
        st.rerun()
    if st.button("Go to Browse"):
        st.session_state[KEY_PAGE] = PAGE_BROWSE
        st.rerun()


def page_preview() -> None:
    st.header("Preview")
    result: LectureNoteResult | None = st.session_state.get(KEY_PREVIEW_RESULT)
    if result is None:
        st.info("No note to preview. Add a new lecture note first.")
        return
    _render_note_markdown(result)
    if result.visual_aids:
        st.markdown("## Visual aids")
        for v in result.visual_aids:
            st.markdown(f"- [{v.timestamp}] {v.reason}")


def page_browse() -> None:
    st.header("Browse lecture notes")
    db.init_db()
    rows = db.get_all_notes()
    if not rows:
        st.info("No notes yet. Add a new lecture note first.")
        return

    options = [f"{r.name} ({r.created_at})" for r in rows]
    ids = [r.id for r in rows]
    choice = st.selectbox(
        "Select a note",
        range(len(options)),
        format_func=lambda i: options[i],
    )
    if choice is None:
        return
    note_id = ids[choice]
    if st.button("Open note view"):
        st.session_state[KEY_CURRENT_NOTE_ID] = note_id
        st.session_state[KEY_VIDEO_SEEK_SECONDS] = 0
        st.session_state[KEY_PAGE] = PAGE_DETAIL
        st.rerun()


def page_detail() -> None:
    note_id = st.session_state.get(KEY_CURRENT_NOTE_ID)
    if note_id is None:
        st.warning("No note selected.")
        st.session_state[KEY_PAGE] = PAGE_BROWSE
        st.rerun()
        return

    record = db.get_note_by_id(note_id)
    if record is None:
        st.error("Note not found.")
        st.session_state[KEY_PAGE] = PAGE_BROWSE
        st.rerun()
        return

    result = _record_to_result(record)
    seek = st.session_state.get(KEY_VIDEO_SEEK_SECONDS, 0)

    st.subheader(result.name)

    col_media, col_note = st.columns([1, 1])

    with col_media:
        media_path = record.media_path
        if not Path(media_path).exists():
            st.error(f"Media file not found: {media_path}")
        elif _is_video(media_path):
            st.video(media_path, start_time=seek)
        elif _is_audio(media_path):
            st.audio(media_path, start_time=seek)
        else:
            st.caption("Unsupported media type. Provide path to video or audio file.")

    with col_note:
        with st.container():
            _render_note_markdown(result)
            _render_visual_aids_with_buttons(result)

    if st.button("Back to list"):
        st.session_state[KEY_PAGE] = PAGE_BROWSE
        st.session_state[KEY_CURRENT_NOTE_ID] = None
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Rec2Note", layout="wide")
    st.title("Rec2Note")
    st.caption("Transform lecture recordings into notes.")

    if KEY_PAGE not in st.session_state:
        st.session_state[KEY_PAGE] = PAGE_ADD

    # When viewing a note (detail), show that view; sidebar still shows Add/Preview/Browse
    if st.session_state[KEY_PAGE] == PAGE_DETAIL:
        page_detail()
        return

    page = st.sidebar.radio(
        "Navigate",
        [PAGE_ADD, PAGE_PREVIEW, PAGE_BROWSE],
        index=[PAGE_ADD, PAGE_PREVIEW, PAGE_BROWSE].index(
            st.session_state[KEY_PAGE]
        ),
    )
    st.session_state[KEY_PAGE] = page

    if page == PAGE_ADD:
        page_add()
    elif page == PAGE_PREVIEW:
        page_preview()
    else:
        page_browse()


if __name__ == "__main__":
    main()
