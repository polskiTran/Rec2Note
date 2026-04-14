from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from rec2note_cli.enums.agent_enums import AgentType


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model_id: str = "gpt-4.1-mini"
    llm_max_tokens: int = 8192
    llm_temperature: float = 0.3

    # models for agents
    agent_model_id: dict[AgentType, str] = {
        AgentType.DEADLINE: "gpt-5.4-nano",
        AgentType.QUESTIONS: "gpt-5.4-nano",
        AgentType.STUDENT_QA: "gpt-5.4-nano",
        AgentType.SUMMARY: "gpt-5.4",
        AgentType.VISUAL_AIDS_SEARCH: "gpt-5.4-nano",
    }

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
    output_summary: bool = False


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
