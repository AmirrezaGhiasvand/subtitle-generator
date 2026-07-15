"""
History tab: browse previously generated subtitle files.
"""
from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from app.core.history import HistoryEntry, load_history
from app.gui.open_utils import open_path


class HistoryTab(ctk.CTkFrame):
    def __init__(self, master, font_family: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._font_family = font_family

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.refresh()

    def refresh(self) -> None:
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        entries = load_history()

        if not entries:
            ctk.CTkLabel(
                self.scroll_frame,
                text="No files processed yet.",
                font=ctk.CTkFont(family=self._font_family, size=13),
                text_color="gray",
            ).pack(pady=20)
            return

        for entry in entries:
            self._build_row(entry)

    def _build_row(self, entry: HistoryEntry) -> None:
        row = ctk.CTkFrame(self.scroll_frame)
        row.pack(fill="x", pady=5, padx=5)

        source_name = Path(entry.source_file).name
        info_text = f"{source_name}\n{entry.created_at}  ·  {entry.language}  ·  {entry.segment_count} segments"

        ctk.CTkLabel(
            row, text=info_text, font=ctk.CTkFont(family=self._font_family, size=13),
            justify="left", anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=10, pady=10)

        button_frame = ctk.CTkFrame(row, fg_color="transparent")
        button_frame.pack(side="right", padx=10, pady=10)

        ctk.CTkButton(
            button_frame, text="Open SRT", width=90,
            font=ctk.CTkFont(family=self._font_family, size=12),
            command=lambda p=entry.srt_path: open_path(Path(p)),
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            button_frame, text="Open Folder", width=100,
            font=ctk.CTkFont(family=self._font_family, size=12),
            command=lambda p=entry.srt_path: open_path(Path(p).parent),
        ).pack(side="left")