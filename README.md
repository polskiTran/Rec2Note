# Rec2Note
> **WIP - Active development**

Rec2Note is a CLI tool for transforming lecture recordings into student notes that capture key concepts delivered with visual aids (slides, whiteboard, …), coursework-related notices, and questions from students.

## Current State

The app is in active development. Currently available:
- CLI interface for processing transcripts
- Minimal pipeline (summary generation)
- Full pipeline — two-phase execution for cost efficiency:
  - **Phase 1 (cache warmup):** the deadline agent runs first, warming the LLM provider's prompt cache with the shared transcript prefix.
  - **Phase 2 (cache-harvested concurrent):** the remaining agents (summary, study questions, student Q&A) run concurrently, reusing the cached prefix tokens to reduce input-token cost.
- Rich terminal output with preview

Planned features (not yet implemented):
- Textual TUI
- Auto-transcription from media files
- SQLite database for storing notes

Features:
- Generate detailed summaries (title, key points, topics, key terms) from transcripts
- Extract important deadlines (exam dates, assignment due dates, …)
- Extract student questions and answers
- Generate study questions
- Optional: include media file path for future visual-aid timestamp extraction
- Preview generated notes directly in terminal

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

Install dependencies, then run the CLI:

```bash
# Install the package in development mode
uv pip install -e .

# Process a transcript with minimal pipeline (summary only)
rec2note process run -tr path/to/transcript.txt

# Process with full pipeline and preview output
rec2note process run -tr path/to/transcript.txt --full --preview

# Include media file for reference
rec2note process run -media path/to/lecture.mp4 -tr path/to/transcript.txt --full

# Custom output directory
rec2note process run -tr path/to/transcript.txt -o ./my-notes
```

### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--transcript` | `-tr` | Path to transcript file (`.txt` or `.md`) — **required** |
| `--media` | `-media` | Path to audio/video file (optional, for metadata) |
| `--minimal` | `-m` | Run minimal pipeline (summary only) — default |
| `--full` | `-f` | Run full pipeline (summary + deadlines + study questions + student Q&A) |
| `--preview` | `-pr` | Render generated markdown in terminal |
| `--output-dir` | `-o` | Output directory for generated notes (default: `./notes`) |

### Current limitations

- Auto-transcription from media is not yet supported — a transcript file is required.
- Streamlit UI and TUI are planned but not yet implemented.


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
        ├── main.py         # Entry point (Typer CLI)
        ├── config.py       # Configuration (Pydantic Settings)
        ├── cli/            # CLI commands (process run)
        ├── core/           # Business logic
        │   ├── agents.py   # LLM agents (summary, deadlines, etc.)
        │   ├── db.py       # SQLite storage for lecture notes
        │   ├── llm.py      # LLM API client
        │   ├── models.py   # Pydantic models and LectureNoteResult
        │   └── pipeline.py # Orchestrates transcript → agents → DB
        ├── enums/
        ├── prompts/        # LLM instruction files
        ├── ui/             # Rich console UI
        └── utils/          # read_file, timestamp (HH:MM:SS → seconds)
```

## Stack

- Package manager: uv
- CLI: Typer + Rich
- LLM: Bring your own API (openai compatible)
- DB: SQLite (built-in, `data/rec2note.db`)
