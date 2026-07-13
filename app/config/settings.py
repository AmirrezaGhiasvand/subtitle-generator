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
    # Used only if whisper_model_path is not set (triggers a download-by-name).
    whisper_model_size: str = "small"
    # Path to a local CTranslate2 model directory (config.json, model.bin,
    # tokenizer.json, vocabulary.txt). Preferred — fully offline.
    whisper_model_path: str = ""
    # CPU-only by design: this app targets lightweight video/audio files,
    # so CPU inference is fast enough and avoids the CUDA-runtime
    # dependency headaches most users' machines aren't set up for.
    whisper_device: Literal["cpu", "cuda"] = "cpu"
    whisper_compute_type: str = "int8"


settings = Settings()