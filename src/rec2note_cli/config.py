from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from rec2note_cli.enums.agent_enums import AgentType


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")  # Loads .env by default
    google_gemini_api_key: str = ""
    google_gemini_model_id: str = "gemini-2.5-flash"
    google_gemini_cache_ttl: str = "300s"  # seconds

    # prompts path
    prompts_dir_path: str = str(Path(__file__).parent / "prompts")
    agent_instructions: dict[AgentType, str] = {
        AgentType.DEADLINE: prompts_dir_path + "/deadline_instructions.md",
        AgentType.QUESTIONS: prompts_dir_path + "/questions_instructions.md",
        AgentType.STUDENT_QA: prompts_dir_path + "/student_qa_instructions.md",
        AgentType.SUMMARY: prompts_dir_path + "/summary_instructions.md",
        AgentType.VISUAL_AIDS_SEARCH: prompts_dir_path
        + "/visual_aids_search_instructions.md",
    }
    current_date: str = datetime.now().strftime("%Y-%m-%d")

    # debugging
    output_summary: bool = True


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached singleton of the application settings.

    Usage::

        from config import get_settings

        settings = get_settings()
        print(settings.aws_region)
        print(settings.aws_bedrock_api_key.get_secret_value())
    """
    return Settings()
