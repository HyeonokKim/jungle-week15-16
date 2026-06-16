from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Haripool API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/haripool"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    frontend_auth_redirect_url: str = "http://localhost:5173/"
    auth_dev_mode: bool = True
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8000/auth/google/callback"
    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_ai_explanation_model: str = "gpt-4o-mini"
    ai_explanation_candidate_count: int = 3
    notion_token: str | None = None
    notion_version: str = "2026-03-11"
    notion_page_id: str | None = None
    notion_oauth_client_id: str | None = None
    notion_oauth_client_secret: str | None = None
    notion_oauth_redirect_uri: str = "http://127.0.0.1:8000/auth/notion/callback"
    notion_token_encryption_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
