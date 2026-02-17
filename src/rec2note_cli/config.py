from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')  # Loads .env by default
    google_gemini_api_key: str

    # add prompts

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
