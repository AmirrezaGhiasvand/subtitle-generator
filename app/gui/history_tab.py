"""
History view: browse previously generated subtitle files.
"""
from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from app.core.history import HistoryEntry, load_history
from app.gui.open_utils import open_path, reveal_file

ACCENT = ("#5B5FEF", "#4A4FD6")


class HistoryTab(ctk.CTkFrame):
    def __init__(self, master, font_family: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._font_family = font_family
        self._build()
        self.refresh()

    def _font(self, size: int = 14, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family=self._font_family, size=size, weight=weight)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 10))
        ctk.CTkLabel(header, text="History", font=self._font(30, "bold")).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Previously generated subtitle files.", font=self._font(15), text_color="gray",
        ).pack(anchor="w", pady=(4, 0))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=(10, 30))

    def refresh(self) -> None:
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        entries = load_history()

        if not entries:
            ctk.CTkLabel(
                self.scroll_frame, text="No files processed yet.", font=self._font(14), text_color="gray",
            ).pack(pady=20)
            return

        for entry in entries:
            self._build_row(entry)

    def _build_row(self, entry: HistoryEntry) -> None:
        row = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
        row.pack(fill="x", pady=6, padx=2)

        text_col = ctk.CTkFrame(row, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True, padx=16, pady=14)

        ctk.CTkLabel(
            text_col, text=Path(entry.source_file).name, font=self._font(16, "bold"), anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            text_col,
            text=f"{entry.created_at}   ·   {entry.language}   ·   {entry.segment_count} segments",
            font=self._font(13), text_color="gray", anchor="w",
        ).pack(fill="x", pady=(2, 0))

        button_frame = ctk.CTkFrame(row, fg_color="transparent")
        button_frame.pack(side="right", padx=16, pady=14)

        ctk.CTkButton(
            button_frame, text="Open SRT", width=100, height=34, corner_radius=8,
            font=self._font(13), fg_color=ACCENT,
            command=lambda p=entry.srt_path: open_path(Path(p)),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_frame, text="Show in Folder", width=130, height=34, corner_radius=8,
            font=self._font(13), fg_color="transparent", border_width=1,
            command=lambda p=entry.srt_path: reveal_file(Path(p)),
        ).pack(side="left")