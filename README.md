# Rec2Note
> **WIP - Active development**

Rec2Note is an app (Streamlit + optional TUI) for transforming lecture recordings into student notes that capture key concepts delivered with visual aids (slides, whiteboard, …), coursework-related notices, and questions from students.

Features:
- Extract visual aids from media (slides, whiteboard, illustration) mentioned in the lecture via key timestamps.
- From a lecture recording (audio or video) and its transcription, Rec2Note generates:
  - A detailed summary (title, key points, topics, key terms)
  - Important deadlines (exam dates, assignment due dates, …)
  - Student questions and answers
  - Study questions
- Add new lecture notes (name, path to media, path to transcription). A transcription file is required for processing (.srt or .txt).
- Preview the generated note and browse all saved notes in a local SQLite database.
- In the note view, the video or audio is shown side-by-side with the parsed note; clicking a visual-aid timestamp jumps playback to that time in the media.

## Prerequisites

- **Python 3.13+**
- **uv** (recommended) or **pip** to install dependencies
- **Google Gemini API key** — create a `.env` file in the project root with:
  ```bash
  GOOGLE_GEMINI_API_KEY=your_api_key_here
  ```
  (The app loads this via pydantic-settings; see [config](src/rec2note_cli/config.py).)

No build step is required: install deps and run. The SQLite DB and `data/` directory are created automatically on first use.

## Running the app

Install dependencies, then run the Streamlit app (recommended) or the TUI.

**Streamlit (recommended)** — with uv:

```bash
uv sync
uv run streamlit run src/rec2note_cli/streamlit_app.py
```

The Streamlit app provides:
- **Add new lecture note** — Lecture name, path to media (audio or video), and path to transcription (required; .srt or .txt). The pipeline runs and the note is saved to the database.
- **Preview** — View the last generated note (summary, deadlines, study questions, student Q&A, visual aids).
- **Browse lecture notes** — List saved notes and open one in the note view. In the note view, media is shown side-by-side with the parsed note; clicking a visual-aid timestamp jumps the video or audio to that time.

## Directory

```bash
Rec2Note/
├── .env                    # Secrets (API keys)
├── .gitignore
├── pyproject.toml          # Dependencies (uv)
├── README.md
├── data/                   # SQLite DB (rec2note.db), gitignored
├── recordings/             # Input recordings
│   └── .gitkeep
├── notes/                  # Output notes (gitignored)
│   └── .gitkeep
├── tests/
│   └── ...
└── src/
    └── rec2note_cli/       # Main package
        ├── __init__.py
        ├── main.py         # Entry point (launches Textual TUI)
        ├── streamlit_app.py # Streamlit UI (add, preview, browse, note view)
        ├── config.py       # Configuration (Pydantic Settings)
        ├── cli/            # Legacy CLI (process command)
        ├── core/           # Business logic
        │   ├── agents.py   # LLM agents (summary, deadlines, etc.)
        │   ├── db.py       # SQLite storage for lecture notes
        │   ├── llm.py      # Gemini API client
        │   ├── models.py   # Pydantic models and LectureNoteResult
        │   └── pipeline.py # Orchestrates transcript → agents → DB
        ├── enums/
        ├── prompts/        # LLM instruction files
        ├── tui/            # Textual TUI
        │   ├── app.py      # Rec2NoteApp
        │   └── screens/    # Home, Add, Processing, Preview, Browse, Detail
        ├── ui/             # Rich console (legacy)
        └── utils/          # read_file, timestamp (HH:MM:SS → seconds)
```

## Stack

- Package manager: uv
- UI: Streamlit (primary), Typer + Rich
- LLM: Gemini API
- DB: SQLite (built-in, `data/rec2note.db`)
