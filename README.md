# Rec2Note
> **WIP - Active development**

Rec2Note is a CLI tool for transforming lecture recoding into student note that captures key concept delivered with visual aids (slides, whiteboard, ...), coursework related notices and questions from students. 

## Directory
```bash
Rec2Note/
├── .env                    # Secrets (API Keys) 
├── .gitignore
├── pyproject.toml          # Dependencies managed by uv
├── README.md
├── tests/                  # Pytest suite
│   ├── __init__.py
│   ├── test_cli.py
│   └── test_processor.py
├── recordings/             # Input recordings
│   └── .gitkeep
├── notes/                  # Output notes
│   └── .gitkeep
└── src/
    └── rec2note_cli/        # Main package
        ├── __init__.py
        ├── main.py         # Entry point (Typer app definition)
        ├── config.py       # Configuration management (Pydantic Settings)
        ├── constants.py    # Static paths, default model names
        │
        ├── cli/            # Interface Layer (Typer commands)
        │   ├── __init__.py
        │   ├── callbacks.py# Shared flags (--verbose, --version)
        │   └── process.py  # The main 'process' command logic
        │
        ├── core/           # Business Logic Layer
        │   ├── __init__.py
        │   ├── audio.py    # Audio transcription logic (Whisper/API)
        │   ├── llm.py      # LLM API Client wrapper
        │   └── pipeline.py # Orchestrates Audio -> Text -> Notes
        │
        ├── templates/      # LLM Assets
        │   ├── __init__.py
        │   └── prompts.py  # System prompts and Jinja2 templates
        │
        ├── ui/             # Presentation Layer (Rich)
        │   ├── __init__.py
        │   ├── console.py  # Global Rich Console instance
        │   ├── panels.py   # Custom Rich layouts (summaries, status)
        │   └── progress.py # Custom progress bar configurations
        │
        └── utils/          # Helpers
            ├── __init__.py
            └── file_ops.py # Safe file reading/writing logic
```

## Stack
- Package Manager: uv
- CLI: Typer + Rich
- LLM: Gemini API
