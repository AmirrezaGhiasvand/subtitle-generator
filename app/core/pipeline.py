"""
Orchestrates the full subtitle generation pipeline:
extract audio -> transcribe -> write SRT -> (optionally) translate ->
write translated SRT.

Kept separate from the GUI so this logic is testable and reusable
independent of any specific interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from app.core.srt_writer import write_srt
from app.services.audio_extractor import extract_audio
from app.services.transcriber import TranscriptionResult, transcribe_audio


@dataclass
class PipelineResult:
    srt_path: Path
    translated_srt_path: Optional[Path]
    target_language: Optional[str]
    language: str
    language_probability: float
    segment_count: int


ProgressCallback = Callable[[str], None]


def run_pipeline(
    source_path: Path,
    output_dir: Optional[Path] = None,
    target_language: Optional[str] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> PipelineResult:
    """
    Run the full video/audio -> SRT pipeline, with an optional translation
    pass producing a second SRT file alongside the original-language one.

    Args:
        source_path: path to the input video or audio file.
        output_dir: where to write intermediate audio + final SRT(s).
            Defaults to a sibling "output" folder next to the source file.
        target_language: if given, also produce a translated SRT in this
            language via OpenRouter. The original-language SRT is always
            produced regardless -- translation never replaces it.
        on_progress: optional callback invoked with short status strings.
    """
    def report(message: str) -> None:
        if on_progress:
            on_progress(message)

    if output_dir is None:
        output_dir = source_path.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    report("Extracting audio...")
    audio_path = extract_audio(source_path, output_dir / f"{source_path.stem}.wav")

    report("Transcribing (this may take a while for longer files)...")
    result: TranscriptionResult = transcribe_audio(audio_path)

    report("Writing subtitle file...")
    srt_path = write_srt(result.segments, output_dir / f"{source_path.stem}.srt")

    translated_srt_path: Optional[Path] = None
    if target_language:
        report(f"Translating to {target_language}...")
        from app.services.translator import translate_segments

        translated_segments = translate_segments(result.segments, target_language)

        report("Writing translated subtitle file...")
        lang_suffix = target_language.lower().replace(" ", "_")
        translated_srt_path = write_srt(
            translated_segments, output_dir / f"{source_path.stem}.{lang_suffix}.srt"
        )

    report("Done.")

    return PipelineResult(
        srt_path=srt_path,
        translated_srt_path=translated_srt_path,
        target_language=target_language,
        language=result.language,
        language_probability=result.language_probability,
        segment_count=len(result.segments),
    )