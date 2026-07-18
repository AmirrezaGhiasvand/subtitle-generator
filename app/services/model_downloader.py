"""
Locates the Faster-Whisper model files (CTranslate2 format) that the user
downloads and places manually -- either in the app's default per-user
location, or in any folder of their choosing via "Locate Model Folder".

Auto-downloading was tried and dropped: model.bin (~1.6GB) downloads
reliably in development, but real end users hit flaky connections, CDN
timeouts, and slow mirrors that turned "click Generate" into an
unpredictable, unattended multi-minute network operation with failure
modes that are hard to recover from cleanly inside a packaged desktop
app. A one-time manual download with clear instructions is simpler and
more reliable for a v1.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from platformdirs import user_data_dir

DEFAULT_REPO_ID = "deepdml/faster-whisper-large-v3-turbo-ct2"
MODEL_DOWNLOAD_URL = f"https://huggingface.co/{DEFAULT_REPO_ID}/tree/main"

REQUIRED_FILENAMES = ("model.bin", "config.json")


class ModelNotFoundError(Exception):
    """Raised when the Whisper model files aren't present in any known location."""

    def __init__(self, model_dir: Path, download_url: str = MODEL_DOWNLOAD_URL):
        self.model_dir = model_dir
        self.download_url = download_url
        super().__init__(
            f"Speech recognition model not found.\n\n"
            f"Download the model files from:\n{download_url}\n\n"
            f"and place them in:\n{model_dir}\n\n"
            f"(or use \"Locate Model Folder\" to point at files you've already downloaded elsewhere)"
        )


class ModelLoadError(Exception):
    """
    Raised when model files exist locally but fail to actually load --
    most commonly a corrupted or incomplete download (e.g. an interrupted
    transfer left a truncated model.bin, which passes the "file exists
    and is non-empty" check but fails once ctranslate2 tries to read the
    missing bytes).
    """

    def __init__(self, model_dir: Path, original_error: Exception, download_url: str = MODEL_DOWNLOAD_URL):
        self.model_dir = model_dir
        self.download_url = download_url
        self.original_error = original_error
        super().__init__(
            f"The speech recognition model files appear to be corrupted or incomplete.\n\n"
            f"Delete everything in:\n{model_dir}\n\n"
            f"then download fresh files from:\n{download_url}\n\n"
            f"(Technical detail: {original_error})"
        )


def get_default_model_dir(repo_id: str = DEFAULT_REPO_ID) -> Path:
    """
    The app's default suggested location for model files: a per-user
    app-data location, which stays writable even when the app itself is
    installed somewhere read-only (e.g. Program Files).
    """
    safe_name = repo_id.replace("/", "__")
    data_dir = Path(user_data_dir("Subtitle Generator", "subtitle-generator"))
    return data_dir / "models" / safe_name


# Kept as an alias -- earlier versions of this module only supported the
# default location, and other modules refer to this name.
get_model_dir = get_default_model_dir


def is_valid_model_folder(path: Path) -> bool:
    """
    Check that a given folder actually contains the required model files
    (non-empty). Used both for the default location and for any custom
    folder a user points the app at via "Locate Model Folder".
    """
    if not path.exists() or not path.is_dir():
        return False
    return all((path / name).exists() and (path / name).stat().st_size > 0 for name in REQUIRED_FILENAMES)


def is_model_ready(repo_id: str = DEFAULT_REPO_ID) -> bool:
    """Check the default location specifically (kept for backward compatibility)."""
    return is_valid_model_folder(get_default_model_dir(repo_id))


def resolve_model_path(repo_id: str = DEFAULT_REPO_ID) -> Optional[Path]:
    """
    Resolve which folder to actually load the model from, in priority order:
      1. A developer override via .env (settings.whisper_model_path)
      2. A user-configured custom folder (set via "Locate Model Folder")
      3. The app's default per-user download location, if valid files are there
      4. None -- caller should treat this as "not set up yet"
    """
    from app.config.settings import settings

    if settings.whisper_model_path:
        candidate = Path(settings.whisper_model_path)
        if is_valid_model_folder(candidate):
            return candidate

    from app.core.app_settings import get_custom_model_path

    custom = get_custom_model_path()
    if custom and is_valid_model_folder(Path(custom)):
        return Path(custom)

    default_dir = get_default_model_dir(repo_id)
    if is_valid_model_folder(default_dir):
        return default_dir

    return None