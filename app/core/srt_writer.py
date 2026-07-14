"""
Converts transcript segments into a valid SubRip (.srt) subtitle file.
"""
from __future__ import annotations

from pathlib import Path


def _format_timestamp(seconds: float) -> str:
    """Convert seconds (float) into SRT's HH:MM:SS,mmm timestamp format."""
    if seconds < 0:
        seconds = 0

    total_ms = round(seconds * 1000)
    hours, remainder_ms = divmod(total_ms, 3_600_000)
    minutes, remainder_ms = divmod(remainder_ms, 60_000)
    secs, ms = divmod(remainder_ms, 1_000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def segments_to_srt(segments) -> str:
    """
    Build the full text content of an .srt file from a list of segments.

    Each segment needs `.start`, `.end`, `.text` attributes (matches
    TranscriptSegment from services/transcriber.py, but this module stays
    decoupled from that specific type — any object shaped this way works).
    """
    non_empty = [seg for seg in segments if seg.text.strip()]

    blocks = []
    for index, segment in enumerate(non_empty, start=1):
        start_ts = _format_timestamp(segment.start)
        end_ts = _format_timestamp(segment.end)
        blocks.append(f"{index}\n{start_ts} --> {end_ts}\n{segment.text.strip()}\n")

    return "\n".join(blocks)


def write_srt(segments, output_path: Path) -> Path:
    """Write transcript segments to a .srt file on disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(segments_to_srt(segments), encoding="utf-8")
    return output_path