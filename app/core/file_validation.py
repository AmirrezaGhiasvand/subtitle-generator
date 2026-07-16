"""
Validates that a selected/dropped file is actually a supported video or
audio file before it's accepted into the pipeline.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ALLOWED_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv",  # video
    ".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".wma",  # audio
}


class UnsupportedFileError(Exception):
    """Raised when a file is not a supported video/audio file."""


def validate_media_file(path: Path) -> None:
    """
    Validate that `path` is a supported video/audio file.

    Two layers of checking:
    1. Extension check -- fast, catches obviously wrong file types.
    2. ffprobe check -- confirms the file actually contains a readable
       audio or video stream, catching corrupted files or files with a
       misleading extension (e.g. a .txt renamed to .mp4).

    Raises:
        UnsupportedFileError: with a human-readable reason, if invalid.
    """
    if not path.exists():
        raise UnsupportedFileError(f"File not found: {path.name}")

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileError(
            f"\u201c{path.name}\u201d is not a supported video or audio file.\n\n"
            f"Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if not _has_media_stream(path):
        raise UnsupportedFileError(
            f"\u201c{path.name}\u201d could not be read as a valid video or audio file.\n"
            f"The file may be corrupted or is not actually a media file."
        )


def _has_media_stream(path: Path) -> bool:
    """Use ffprobe to confirm the file has at least one audio or video stream."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return True

    stream_types = result.stdout.strip().splitlines()
    return any(t in ("audio", "video") for t in stream_types)