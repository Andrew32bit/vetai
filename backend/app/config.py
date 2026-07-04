import secrets
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "VetAI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBAPP_URL: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vetai.db"

    # Groq API
    GROQ_API_KEY: str = ""
    GROQ_CHAT_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Claude API (fallback when Groq rate-limited)
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Admin (loaded from env — never hardcode the secret in source)
    ADMIN_KEY: str = ""

    # Alerting
    ADMIN_TELEGRAM_ID: int = 418149698  # Andrew

    # HuggingFace (for DB backup)
    HF_API_TOKEN: str = ""

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def verify_admin_key(provided: str) -> bool:
    """Constant-time check of an admin key against ADMIN_KEY from env.

    Fails closed: if ADMIN_KEY is not configured, no key is ever accepted.
    """
    configured = get_settings().ADMIN_KEY
    if not configured:
        return False
    return secrets.compare_digest(provided, configured)
