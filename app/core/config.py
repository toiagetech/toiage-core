from pydantic_settings import BaseSettings, SettingsConfigDict


from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".secrets"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "ToiageCore"
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/toiage"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_DEFAULT_MODEL: str = "google/gemini-2.0-flash-001"
    LLM_TIMEOUT_SECONDS: int = 30
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 10
    LOG_LEVEL: str = "INFO"
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://us.i.posthog.com"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_DEFAULT_MODEL: str = "deepseek-chat"

    # Security
    CORS_ALLOWED_ORIGINS: list[str] = ["*"]
    MAX_REQUEST_BODY_SIZE_BYTES: int = 1_048_576  # 1 MB for JSON bodies (< uploads handled separately)


settings = Settings()
