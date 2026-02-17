from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')  # Loads .env by default
    google_gemini_api_key: str

    # add prompts

settings = Settings()
