"""
Wraps Faster-Whisper for speech-to-text transcription with automatic
spoken-language detection. CPU-only by design — see settings.py.
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


# Loading model weights is expensive — cache the instance instead of
# reloading it on every call.
_model_cache: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model_cache
    if _model_cache is None:
        model_source = settings.whisper_model_path or settings.whisper_model_size
        _model_cache = WhisperModel(
            model_source,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    return _model_cache


def transcribe_audio(audio_path: Path) -> TranscriptionResult:
    """
    Transcribe a 16kHz mono WAV file, auto-detecting the spoken language.
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