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
    # Path prefix the API app is mounted under when served by uvicorn.
    # Set to "" or "/" to serve at the root (e.g. http://localhost:8000/).
    # Default serves at http://localhost:8000/toiage-core/
    API_PREFIX: str = "/toiage-core"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/toiage"
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 10
    LOG_LEVEL: str = "INFO"
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://us.i.posthog.com"

    # Education Engine
    EDUCATION_ENGINE_URL: str = "http://localhost:8001"
    EDUCATION_ENGINE_ENABLED: bool = True

    # Security
    CORS_ALLOWED_ORIGINS: list[str] = ["*"]
    MAX_REQUEST_BODY_SIZE_BYTES: int = 1_048_576  # 1 MB for JSON bodies (< uploads handled separately)

    # Education Engine / LLM Provider settings
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    LLM_PROVIDER: str = "openrouter"
    LLM_DEFAULT_MODEL: str = "google/gemini-2.0-flash-lite"


settings = Settings()
