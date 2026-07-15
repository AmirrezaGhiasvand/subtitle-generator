"""
Tracks previously generated subtitle files so users can revisit them from
the History tab.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

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


def add_entry(source_file: Path, srt_path: Path, language: str, segment_count: int) -> None:
    entry = HistoryEntry(
        source_file=str(source_file),
        srt_path=str(srt_path),
        language=language,
        segment_count=segment_count,
        created_at=datetime.now().isoformat(timespec="seconds"),
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