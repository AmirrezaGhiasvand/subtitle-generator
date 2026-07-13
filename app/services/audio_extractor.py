from __future__ import annotations

import subprocess
from pathlib import Path


class AudioExtractionError(Exception):
    """Raised when ffmpeg fails to extract/convert audio from a source file."""

    def __init__(self, message: str, stderr: str = ""):
        self.stderr = stderr
        super().__init__(message)


# Whisper expects 16kHz mono PCM audio — extracting/converting directly to
# this format avoids Faster-Whisper having to resample internally.
WHISPER_SAMPLE_RATE = 16_000


def extract_audio(source_path: Path, output_path: Path) -> Path:
    """
    Extract (from video) or convert (from audio) a 16kHz mono WAV track
    using ffmpeg. Works for both video files and audio-only files, since
    ffmpeg handles both the same way — `-vn` is simply ignored if there's
    no video stream to drop.

    Args:
        source_path: Path to the source video or audio file.
        output_path: Path where the extracted .wav file should be written.
                      Parent directory is created if it doesn't exist.

    Returns:
        The output_path, for convenient chaining.

    Raises:
        FileNotFoundError: if source_path doesn't exist.
        AudioExtractionError: if ffmpeg exits non-zero (corrupt file, no
            audio stream, unsupported codec, etc.)
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",                           # overwrite output without prompting
        "-i", str(source_path),
        "-vn",                          # drop video stream if present — audio only
        "-acodec", "pcm_s16le",         # uncompressed 16-bit PCM
        "-ar", str(WHISPER_SAMPLE_RATE),
        "-ac", "1",                     # mono
        str(output_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise AudioExtractionError(
            f"ffmpeg failed to process {source_path.name}",
            stderr=result.stderr,
        )

    if not output_path.exists():
        raise AudioExtractionError(
            f"ffmpeg reported success but no output file was created: {output_path}"
        )

    return output_path