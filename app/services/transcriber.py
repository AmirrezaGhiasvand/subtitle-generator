"""
Wraps Faster-Whisper for speech-to-text transcription with automatic
spoken-language detection.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from app.config.settings import settings


@dataclass
class TranscriptSegment:
    """A single timestamped chunk of transcribed speech."""
    start: float          # seconds
    end: float            # seconds
    text: str
    confidence: float     # 0.0-1.0, derived from avg_logprob


@dataclass
class TranscriptionResult:
    language: str               # ISO 639-1 code, e.g. "en", "fa"
    language_probability: float
    segments: list[TranscriptSegment]


def _resolve_device() -> str:
    """Resolve 'auto' into an actual device by checking for a usable GPU."""
    if settings.whisper_device != "auto":
        return settings.whisper_device

    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _resolve_compute_type(device: str) -> str:
    """Resolve 'auto' into a compute type appropriate for the device."""
    if settings.whisper_compute_type != "auto":
        return settings.whisper_compute_type
    # int8 is fastest/lightest on CPU; float16 is the standard fast choice on GPU
    return "float16" if device == "cuda" else "int8"


# Loading model weights is expensive — cache instances instead of reloading
# on every call.
_model_cache: dict[tuple[str, str, str], WhisperModel] = {}


def _get_model() -> WhisperModel:
    device = _resolve_device()
    compute_type = _resolve_compute_type(device)
    cache_key = (settings.whisper_model_size, device, compute_type)

    if cache_key not in _model_cache:
        _model_cache[cache_key] = WhisperModel(
            settings.whisper_model_size,
            device=device,
            compute_type=compute_type,
        )

    return _model_cache[cache_key]


def transcribe_audio(audio_path: Path) -> TranscriptionResult:
    """
    Transcribe a 16kHz mono WAV file, auto-detecting the spoken language.

    Args:
        audio_path: Path to a WAV file (as produced by audio_extractor.extract_audio).

    Returns:
        TranscriptionResult with the detected language and timestamped segments.
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _get_model()

    segments_iter, info = model.transcribe(
        str(audio_path),
        language=None,     # None = auto-detect
        word_timestamps=False,
        vad_filter=True,   # skip silent stretches
    )

    segments = [
        TranscriptSegment(
            start=seg.start,
            end=seg.end,
            text=seg.text.strip(),
            confidence=_avg_logprob_to_confidence(seg.avg_logprob),
        )
        for seg in segments_iter
    ]

    return TranscriptionResult(
        language=info.language,
        language_probability=info.language_probability,
        segments=segments,
    )


def _avg_logprob_to_confidence(avg_logprob: float) -> float:
    """
    Faster-Whisper reports avg_logprob (a negative number; closer to 0 means
    more confident). Convert to an intuitive 0.0-1.0 confidence score.
    """
    return max(0.0, min(1.0, 1.0 + avg_logprob))