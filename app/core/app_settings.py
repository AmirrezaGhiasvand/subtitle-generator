"""
Persists app-level settings: the OpenRouter API key (stored securely via
the OS keyring where available) and the translation model choice.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from platformdirs import user_data_dir

try:
    import keyring
    KEYRING_AVAILABLE = True
except Exception:
    KEYRING_AVAILABLE = False

KEYRING_SERVICE = "subtitle-generator"
KEYRING_USERNAME = "openrouter-api-key"

DEFAULT_MODEL = "openai/gpt-4o-mini"


def _settings_file() -> Path:
    data_dir = Path(user_data_dir("Subtitle Generator", "subtitle-generator"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "app_settings.json"


def _load_json() -> dict:
    path = _settings_file()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_json(data: dict) -> None:
    _settings_file().write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_openrouter_api_key() -> Optional[str]:
    if KEYRING_AVAILABLE:
        try:
            key = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if key:
                return key
        except Exception:
            pass  # fall through to the JSON fallback below
    return _load_json().get("openrouter_api_key")


def set_openrouter_api_key(key: str) -> None:
    if KEYRING_AVAILABLE:
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)
            return
        except Exception:
            pass  # fall through to the JSON fallback below

    # Fallback: plain local file. Not as secure as the OS keyring, but
    # keeps the feature working on systems without a keyring backend
    # available (e.g. some minimal Linux setups).
    data = _load_json()
    data["openrouter_api_key"] = key
    _save_json(data)


def get_translation_model() -> str:
    return _load_json().get("translation_model", DEFAULT_MODEL)


def set_translation_model(model: str) -> None:
    data = _load_json()
    data["translation_model"] = model
    _save_json(data)