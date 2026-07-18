"""
Downloads the Faster-Whisper model files (CTranslate2 format) from
Hugging Face on first run, so the packaged app doesn't need to bundle a
multi-gigabyte model file directly in the installer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from huggingface_hub import HfApi, hf_hub_download
from platformdirs import user_data_dir

DEFAULT_REPO_ID = "deepdml/faster-whisper-large-v3-turbo-ct2"

# Reports (bytes_downloaded_so_far, total_bytes) after each file completes.
# Progress granularity is per-file, not per-byte -- see download_model()
# docstring for why.
ProgressCallback = Callable[[int, int], None]


class ModelDownloadError(Exception):
    """Raised when the model fails to download or its file list can't be fetched."""


def get_model_dir(repo_id: str = DEFAULT_REPO_ID) -> Path:
    """
    The local directory where this model's files should live: a per-user
    app-data location, which stays writable even when the app itself is
    installed somewhere read-only (e.g. Program Files).
    """
    safe_name = repo_id.replace("/", "__")
    data_dir = Path(user_data_dir("Subtitle Generator", "subtitle-generator"))
    return data_dir / "models" / safe_name


def is_model_ready(repo_id: str = DEFAULT_REPO_ID) -> bool:
    """
    Best-effort check that the model appears fully downloaded: every file
    Hugging Face lists for this repo exists locally and is non-empty. Not
    a byte-perfect integrity check, but catches the common case of an
    interrupted first download.
    """
    model_dir = get_model_dir(repo_id)
    if not model_dir.exists():
        return False

    try:
        expected_files = _list_repo_files(repo_id)
    except Exception:
        # Can't reach Hugging Face right now -- fall back to "does
        # anything at all exist locally", so a machine that already
        # downloaded the model successfully once can still run fully
        # offline afterward.
        return any(model_dir.iterdir())

    return all((model_dir / name).exists() and (model_dir / name).stat().st_size > 0 for name in expected_files)


def download_model(repo_id: str = DEFAULT_REPO_ID, on_progress: Optional[ProgressCallback] = None) -> Path:
    """
    Download every file in `repo_id` into this app's per-user model
    directory, reporting cumulative progress after each file finishes.

    Progress is reported per-file rather than per-byte: hf_hub_download()
    downloads a whole file per call, and for this model that means ~5
    updates total (model.bin alone is the vast majority of the size).
    Byte-level smoothness would require bypassing huggingface_hub's
    built-in resumable-download handling -- not worth giving up for a
    slightly choppier progress bar.
    """
    model_dir = get_model_dir(repo_id)
    model_dir.mkdir(parents=True, exist_ok=True)

    try:
        files = _list_repo_files_with_sizes(repo_id)
    except Exception as e:
        raise ModelDownloadError(f"Could not reach Hugging Face to list model files: {e}") from e

    total_size = sum(size for _, size in files) or 1  # avoid div-by-zero if sizes are unknown
    downloaded_so_far = 0

    for filename, size in files:
        try:
            hf_hub_download(repo_id=repo_id, filename=filename, local_dir=model_dir)
        except Exception as e:
            raise ModelDownloadError(f"Failed to download {filename}: {e}") from e

        downloaded_so_far += size
        if on_progress:
            on_progress(downloaded_so_far, total_size)

    return model_dir


def _list_repo_files(repo_id: str) -> list[str]:
    return [name for name, _ in _list_repo_files_with_sizes(repo_id)]


def _list_repo_files_with_sizes(repo_id: str) -> list[tuple[str, int]]:
    info = HfApi().model_info(repo_id, files_metadata=True)
    return [(f.rfilename, f.size or 0) for f in info.siblings]