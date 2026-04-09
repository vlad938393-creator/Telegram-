from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    openai_api_key: str
    openai_model: str
    database_path: Path


class SettingsError(RuntimeError):
    """Raised when required configuration is missing."""


def _get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip():
        raise SettingsError(f"Environment variable {name} is required.")
    return value.strip()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    telegram_token = _get_env("TELEGRAM_BOT_TOKEN")
    openai_api_key = _get_env("OPENAI_API_KEY")
    openai_model = _get_env("OPENAI_MODEL", "gpt-5.0-nano")
    database_path = Path(_get_env("DATABASE_PATH", "data/literature.db"))

    return Settings(
        telegram_token=telegram_token,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        database_path=database_path,
    )

