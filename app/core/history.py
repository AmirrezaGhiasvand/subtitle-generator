"""
Tracks previously generated subtitle files so users can revisit them from
the History tab.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from platformdirs import user_data_dir


def _history_file() -> Path:
    data_dir = Path(user_data_dir("Subtitle Generator", "subtitle-generator"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "history.json"


@dataclass
class HistoryEntry:
    source_file: str
    srt_path: str
    language: str
    segment_count: int
    created_at: str  # ISO format
    # Added when translation support was introduced -- defaults to None so
    # older history.json entries (written before this field existed) still
    # load correctly instead of raising a missing-argument error.
    translated_srt_path: Optional[str] = None
    target_language: Optional[str] = None


def add_entry(
    source_file: Path,
    srt_path: Path,
    language: str,
    segment_count: int,
    translated_srt_path: Optional[Path] = None,
    target_language: Optional[str] = None,
) -> None:
    entry = HistoryEntry(
        source_file=str(source_file),
        srt_path=str(srt_path),
        language=language,
        segment_count=segment_count,
        created_at=datetime.now().isoformat(timespec="seconds"),
        translated_srt_path=str(translated_srt_path) if translated_srt_path else None,
        target_language=target_language,
    )
    entries = load_history()
    entries.insert(0, entry)  # newest first
    _save_history(entries)


def load_history() -> list[HistoryEntry]:
    path = _history_file()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [HistoryEntry(**item) for item in raw]
    except (json.JSONDecodeError, TypeError):
        # A corrupt history file shouldn't crash the app -- start fresh.
        return []


def _save_history(entries: list[HistoryEntry]) -> None:
    path = _history_file()
    path.write_text(json.dumps([asdict(e) for e in entries], indent=2), encoding="utf-8")