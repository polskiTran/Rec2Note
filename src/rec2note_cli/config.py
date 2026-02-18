from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")  # Loads .env by default
    google_gemini_api_key: str = ""
    google_gemini_model_id: str = "gemini-2.5-flash"
    google_gemini_cache_ttl: str = "300s"  # seconds

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
