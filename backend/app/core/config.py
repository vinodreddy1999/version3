import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Metam ERP"
    environment: str = "development"

    database_url: str = "sqlite:///./metam.db"

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    refresh_token_expire_minutes: int = 60 * 24 * 7

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    rate_limit_enabled: bool = True

settings = Settings()

if not settings.jwt_secret:
    # No secret configured (e.g. local dev without a .env). Generate a random
    # per-process secret rather than shipping a hardcoded literal; tokens
    # simply won't survive a process restart in that case. Cached on the
    # settings instance so every call in this process sees the same value.
    settings.jwt_secret = secrets.token_urlsafe(32)
