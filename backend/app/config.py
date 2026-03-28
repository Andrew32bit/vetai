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
    DATABASE_URL: str = "sqlite+aiosqlite:////data/vetai.db"

    # ML / AI — HuggingFace Inference API
    HF_API_TOKEN: str = ""
    HF_CHAT_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    HF_VISION_MODEL: str = "Qwen/Qwen2.5-VL-72B-Instruct"
    HF_PROVIDER: str = "together"  # HF Inference Provider (chat)
    HF_VISION_PROVIDER: str = "hyperbolic"  # HF Inference Provider (vision)

    # HuggingFace Hub storage for uploads
    HF_REPO_ID: str = ""  # e.g. "username/vetai-uploads"

    # OCR
    OCR_ENGINE: str = "paddleocr"  # paddleocr | tesseract

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
