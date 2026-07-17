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
class Word:
    """A single word with its own timestamp, used for subtitle resegmentation."""
    start: float
    end: float
    text: str


@dataclass
class TranscriptSegment:
    """A single timestamped chunk of transcribed speech (Whisper's own
    sentence/pause-based segmentation -- kept for reference, but subtitle
    output uses word-level resegmentation instead, see subtitle_segmenter.py)."""
    start: float          # seconds
    end: float            # seconds
    text: str
    confidence: float     # 0.0-1.0, derived from avg_logprob


@dataclass
class TranscriptionResult:
    language: str               # ISO 639-1 code, e.g. "en", "fa"
    language_probability: float
    segments: list[TranscriptSegment]
    words: list[Word]           # flat word-level timestamps across the whole transcript


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
        language=None,       # None = auto-detect
        word_timestamps=True,  # needed for subtitle resegmentation into short lines
        vad_filter=True,     # skip silent stretches
    )

    segments: list[TranscriptSegment] = []
    words: list[Word] = []

    for seg in segments_iter:
        segments.append(
            TranscriptSegment(
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
                confidence=_avg_logprob_to_confidence(seg.avg_logprob),
            )
        )
        # seg.words is populated because word_timestamps=True above.
        for w in seg.words:
            words.append(Word(start=w.start, end=w.end, text=w.word.strip()))

    return TranscriptionResult(
        language=info.language,
        language_probability=info.language_probability,
        segments=segments,
        words=words,
    )


def _avg_logprob_to_confidence(avg_logprob: float) -> float:
    """
    Faster-Whisper reports avg_logprob (a negative number; closer to 0 means
    more confident). Convert to an intuitive 0.0-1.0 confidence score.
    """
    return max(0.0, min(1.0, 1.0 + avg_logprob))