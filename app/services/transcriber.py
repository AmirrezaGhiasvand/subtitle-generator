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
    start: float
    end: float
    text: str
    confidence: float


@dataclass
class TranscriptionResult:
    language: str
    language_probability: float
    segments: list[TranscriptSegment]
    words: list[Word]


_model_cache: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model_cache
    if _model_cache is None:
        from app.services.model_downloader import get_default_model_dir, resolve_model_path

        # pipeline.py already verified resolve_model_path() is not None
        # before calling into transcription -- fall back to the default
        # location's path string here only as a defensive last resort.
        model_path = resolve_model_path()
        model_source = str(model_path) if model_path else str(get_default_model_dir())

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

    from app.services.model_downloader import ModelLoadError, get_default_model_dir, resolve_model_path

    model_dir_for_error = resolve_model_path() or get_default_model_dir()

    try:
        model = _get_model()

        segments_iter, info = model.transcribe(
            str(audio_path),
            language=None,
            word_timestamps=True,
            vad_filter=True,
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
            for w in seg.words:
                words.append(Word(start=w.start, end=w.end, text=w.word.strip()))
    except RuntimeError as e:
        global _model_cache
        _model_cache = None
        raise ModelLoadError(model_dir=model_dir_for_error, original_error=e) from e

    return TranscriptionResult(
        language=info.language,
        language_probability=info.language_probability,
        segments=segments,
        words=words,
    )


def _avg_logprob_to_confidence(avg_logprob: float) -> float:
    return max(0.0, min(1.0, 1.0 + avg_logprob))