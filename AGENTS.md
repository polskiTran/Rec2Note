# AGENTS.md — Rec2Note Development Guide

## Project Overview

Rec2Note is a Python CLI tool that transforms lecture recordings into structured markdown notes using LLM agents. It uses a pipeline architecture: transcript input → LLM agent processing → markdown output.

## Tech Stack

- **Python 3.13+**
- **Package manager**: uv (NOT pip)
- **CLI framework**: Typer
- **Terminal UI**: Rich
- **LLM**: OpenAI-compatible API via the `openai` SDK — any provider (OpenAI, Azure, Google Vertex, Ollama, Groq, Together, etc.)
- **Settings**: pydantic-settings (loads `.env`)
- **Models**: Pydantic v2
- **Retry logic**: tenacity
- **Testing**: pytest

## Project Structure

```
src/rec2note_cli/
├── main.py           # Typer app entry point
├── config.py         # Pydantic Settings (singleton via lru_cache)
├── cli/              # CLI commands (process.py)
├── core/             # Business logic
│   ├── agents.py     # LLM agents (summary, deadlines, questions, student_qa)
│   ├── llm.py        # OpenAI-compatible API client
│   ├── models.py     # Pydantic models (LectureSummary, Deadline, etc.)
│   ├── pipeline.py   # Orchestrates agents → markdown
│   └── db.py         # SQLite storage
├── enums/            # AgentType enum
├── prompts/          # Markdown instruction files per agent
├── ui/               # Rich console, panels, progress
└── utils/            # read_file, timestamp, markdown_builder
```

## LLM Configuration

Rec2Note uses the OpenAI SDK with a configurable `base_url`, so it works with any OpenAI-compatible provider. Configure via environment variables in `.env`:

```bash
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1   # or your provider's endpoint
LLM_MODEL_ID=gpt-4.1-mini                 # any model your provider supports
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=8192
```

### Provider Examples

| Provider | `LLM_BASE_URL` | Notes |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | Default |
| Azure OpenAI | `https://<resource>.openai.azure.com/v1` | Uses Azure AD or API key auth |
| Google Vertex | `https://<region>-aiplatform.googleapis.com/v1beta1/openapi/` | Requires ADC or service account |
| Ollama (local) | `http://localhost:11434/v1` | Runs open-weight models locally |
| Groq | `https://api.groq.com/openai/v1` | Fast inference for open models |
| Together | `https://api.together.xyz/v1` | Managed inference |
| SillyTavern | `http://localhost:11400/v1` | Local inference server |

**Note:** The previous `google-gemini` SDK is no longer used. Gemini can still be accessed via its OpenAI-compatible endpoint:
```
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL_ID=gemini-2.5-flash
```

## Commands

### Setup & Install

```bash
uv sync                          # Install all dependencies (uses uv.lock)
uv sync --group dev              # Install dev dependencies too
```

### Run the CLI

```bash
uv run rec2note -tr path/to/transcript.txt -m       # Minimal pipeline
uv run rec2note -tr path/to/transcript.txt -f -pr    # Full pipeline with preview
```

### Tests

```bash
uv run pytest                     # Run all tests
uv run pytest tests/ -v           # Verbose output
uv run pytest tests/test_llm.py    # LLM module tests
uv run pytest tests/test_markdown_builder.py  # Markdown builder tests
```

### Lint & Format

```bash
uv run ruff check .               # Lint
uv run ruff format .              # Format
uv run ty check .                 # ty check
```

## Code Conventions

### Python Style

- **Type hints everywhere**: All function signatures must include parameter and return types.
- **Use `pathlib.Path`** instead of `os.path` for file paths.
- **Use `str | None`** syntax (Python 3.13 union) over `Optional[str]`.
- **Use `list[X]`** over `List[X]` from typing.
- **No comments** unless explicitly requested.
- **Docstrings**: Use Google-style docstrings with Args/Returns/Raises sections for public functions and classes (see `agents.py` for reference).
- **Section separators**: Use `# ---...---` comment blocks to divide logical sections within a file.
- **Async patterns**: Use `asyncio.Semaphore` for concurrent agent calls; wrap sync agents with `run_in_executor`.

### Pydantic Models

- All data models inherit from `BaseModel`.
- Add a `to_dict()` method that delegates to `self.model_dump()`.
- Prefer Pydantic models over raw dicts for all structured data flowing through the pipeline.

### CLI (Typer)

- Use `typer.Option` for all flags — never positional args.
- Validate inputs early and abort with `_abort()` which prints a Rich panel and raises `typer.Exit(code=1)`.
- `no_args_is_help=True` on the app.

### Configuration

- All settings in `config.py` via `pydantic-settings` `BaseSettings`.
- Secrets loaded from `.env` file.
- Access settings through the cached `get_settings()` singleton.
- Never hardcode API keys or model IDs.
- Settings uses `extra="ignore"` to gracefully ignore deprecated env var names during migrations.

### Error Handling

- Raise `ValueError` for expected validation failures (empty transcript, missing keys in LLM response).
- Catch exceptions at the CLI boundary (`process.py`) and display user-friendly Rich panels.
- Use `_parse_json()` and `_require_key()` helpers when parsing LLM responses — they raise `ValueError` with clear context.
- Never swallow exceptions silently.

### Rich UI

- Use `console.print()` with Rich markup for all terminal output.
- Use `Panel`, `Rule`, `Table`, `Progress`, and `Align` for structured output.
- `_PANEL_WIDTH = 106` for consistent panel sizing.
- Keep UI code in `ui/` and `cli/process.py`; keep `core/` free of Rich imports.

### Testing

- Tests live in `tests/` at the project root.
- Use `pytest` fixtures for reusable test data (see `test_markdown_builder.py`).
- Organize tests into classes by feature area (`TestTitleAndSummary`, `TestDeadline`, etc.).
- Test that optional sections are omitted when empty, not just present when provided.
- Use `MagicMock(spec=...)` when verifying attribute access on mock objects.

### File I/O

- Read files with `path.read_text(encoding="utf-8")`.
- Write files with `path.write_text(content, encoding="utf-8")`.
- Create parent dirs with `path.parent.mkdir(parents=True, exist_ok=True)`.

## uv Usage (NOT pip)

- **Always use `uv`** instead of `pip`, `pip install`, `venv`, or `python -m`.
- Add dependencies: `uv add <package>`
- Add dev dependencies: `uv add --group dev <package>`
- Run scripts: `uv run <command>`
- Remove dependencies: `uv remove <package>`
- Lock file (`uv.lock`) must be committed.
- Never use `pip install -e .` — use `uv sync` instead.

## Architecture Notes

- **LLM client** (`llm.py`): Single `call_llm()` function wrapping the `openai` SDK. All agents call this one function. JSON mode is enabled by default via `response_format={"type": "json_object"}`.
- **Agent pattern**: Each agent function takes a `transcript: str` and returns a typed Pydantic model. Parsing is separated into `_parse_*_response()` helpers.
- **No server-side caching**: Each agent call sends the full transcript as the user message. This is simpler and universally compatible with all OpenAI-compatible providers.
- **Pipeline orchestration**: `pipeline.py` coordinates agent calls. Minimal pipeline runs summary only; full pipeline runs all four agents concurrently via `asyncio.gather`.
- **Markdown builder**: `utils/markdown_builder.py` assembles the final note from Pydantic model outputs. Optional sections (deadlines, student QA, study questions) are omitted when empty.
