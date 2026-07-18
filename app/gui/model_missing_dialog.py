"""
Dialog shown when the Whisper model files are missing or corrupted --
walks the user through the one-time manual download/fix, or lets them
point the app at model files they've already downloaded elsewhere.
"""
from __future__ import annotations

import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Optional

import customtkinter as ctk

from app.core.app_settings import set_custom_model_path
from app.gui.open_utils import open_path
from app.gui.theme import ACCENT, ACCENT_HOVER, BORDER, SUCCESS, SURFACE, TEXT_MUTED, TEXT_PRIMARY
from app.services.model_downloader import is_valid_model_folder


class ModelMissingDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        font_family: str,
        model_dir: Path,
        download_url: str,
        corrupted: bool = False,
        on_model_located: Optional[Callable[[], None]] = None,
    ):
        super().__init__(master)
        self._font_family = font_family
        self._on_model_located = on_model_located

        self.title("Speech Recognition Model Files Corrupted" if corrupted else "Speech Recognition Model Required")
        self.geometry("560x480")
        self.resizable(False, False)

        self._build(model_dir, download_url, corrupted)

        self.after(100, self.grab_set)

    def _font(self, size: int = 14, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family=self._font_family, size=size, weight=weight)

    def _build(self, model_dir: Path, download_url: str, corrupted: bool) -> None:
        if corrupted:
            heading = "Model Files Are Corrupted or Incomplete"
            description = (
                "The downloaded model files can't be read correctly -- most likely an "
                "interrupted or partial download. Delete the files in the folder below, "
                "then download them fresh -- or point the app at a working copy elsewhere."
            )
            steps_text = (
                "1.  Click \u201cOpen Models Folder\u201d and delete everything inside it\n"
                "2.  Click \u201cOpen Download Page\u201d below\n"
                "3.  Download every file listed on that page into the now-empty folder\n"
                "4.  Come back here and click Generate Subtitles again"
            )
        else:
            heading = "One-Time Setup Required"
            description = (
                "This app needs the speech recognition model files (about 1.6GB), "
                "downloaded once and reused for every file after that."
            )
            steps_text = (
                "1.  Click \u201cOpen Download Page\u201d below\n"
                "2.  Download every file listed on that page\n"
                "3.  Click \u201cOpen Models Folder\u201d and move the downloaded files there\n"
                "4.  Come back here and click Generate Subtitles again"
            )

        ctk.CTkLabel(
            self, text=heading, font=self._font(19, "bold"), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            self, text=description, font=self._font(13), text_color=TEXT_MUTED, wraplength=500, justify="left",
        ).pack(anchor="w", padx=24, pady=(0, 16))

        steps_card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=10)
        steps_card.pack(fill="x", padx=24)
        ctk.CTkLabel(
            steps_card, text=steps_text, font=self._font(13), text_color=TEXT_PRIMARY, justify="left",
        ).pack(anchor="w", padx=18, pady=16)

        ctk.CTkLabel(
            self, text="Target folder:", font=self._font(12, "bold"), text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=24, pady=(16, 2))
        ctk.CTkLabel(
            self, text=str(model_dir), font=self._font(12), text_color=TEXT_MUTED,
            wraplength=500, justify="left",
        ).pack(anchor="w", padx=24)

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkButton(
            button_row, text="Open Download Page", font=self._font(13, "bold"), height=38,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=lambda: webbrowser.open(download_url),
        ).pack(side="left", padx=(0, 10))

        def _open_folder() -> None:
            model_dir.mkdir(parents=True, exist_ok=True)
            open_path(model_dir)

        ctk.CTkButton(
            button_row, text="Open Models Folder", font=self._font(13), height=38,
            fg_color="transparent", hover_color=("gray85", "gray25"),
            text_color=TEXT_PRIMARY, border_width=1, border_color=BORDER,
            command=_open_folder,
        ).pack(side="left")

        divider_row = ctk.CTkFrame(self, fg_color="transparent")
        divider_row.pack(fill="x", padx=24, pady=(16, 4))
        ctk.CTkLabel(
            divider_row, text="Already have the model files somewhere else?",
            font=self._font(12), text_color=TEXT_MUTED,
        ).pack(anchor="w")

        ctk.CTkButton(
            self, text="Locate Model Folder...", font=self._font(13), height=36,
            fg_color="transparent", hover_color=("gray85", "gray25"),
            text_color=TEXT_PRIMARY, border_width=1, border_color=BORDER,
            command=self._on_locate_clicked,
        ).pack(anchor="w", padx=24, pady=(0, 8))

        self.status_label = ctk.CTkLabel(self, text="", font=self._font(12), text_color=TEXT_MUTED)
        self.status_label.pack(anchor="w", padx=24)

        ctk.CTkButton(
            self, text="Close", font=self._font(13), width=100, height=34,
            fg_color="transparent", hover_color=("gray85", "gray25"),
            text_color=TEXT_PRIMARY, border_width=1, border_color=BORDER,
            command=self.destroy,
        ).pack(pady=(12, 20))

    def _on_locate_clicked(self) -> None:
        chosen = filedialog.askdirectory(title="Select the folder containing the model files")
        if not chosen:
            return

        chosen_path = Path(chosen)
        if not is_valid_model_folder(chosen_path):
            messagebox.showerror(
                "Invalid Folder",
                f"That folder doesn't contain valid model files.\n\n"
                f"Expected to find model.bin and config.json directly inside:\n{chosen_path}",
            )
            return

        set_custom_model_path(str(chosen_path))
        self.status_label.configure(text=f"Using model files from: {chosen_path}", text_color=SUCCESS)

        if self._on_model_located:
            self._on_model_located()