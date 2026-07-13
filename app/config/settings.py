"""
Typed application configuration.

Loaded from environment variables / .env if present, otherwise sensible
defaults are used — this app runs standalone as a packaged exe, so it
shouldn't require a .env file to exist for normal use.
"""
from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # -------- Whisper --------
    # tiny | base | small | medium | large-v3 — bigger = more accurate, slower, more RAM/VRAM
    whisper_model_size: str = "small"
    # cpu | cuda | auto
    whisper_device: Literal["cpu", "cuda", "auto"] = "auto"
    # int8 | int8_float16 | float16 | float32 | auto
    whisper_compute_type: str = "auto"


settings = Settings()