"""
The "Generate" view: drag-and-drop zone, file picker, generate action,
progress feedback.
"""
from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk

from app.gui.theme import ACCENT, ACCENT_HOVER, BORDER, PROGRESS_TRACK, SUCCESS, SURFACE, TEXT_MUTED, TEXT_PRIMARY

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

SUPPORTED_FILETYPES = [
    ("Video/Audio files", "*.mp4 *.mkv *.mov *.avi *.mp3 *.wav *.m4a *.flac"),
    ("All files", "*.*"),
]


class GenerateView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        font_family: str,
        on_file_selected: Callable[[Path], None],
        on_generate_clicked: Callable[[], None],
        on_toggle_appearance: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._font_family = font_family
        self._on_file_selected = on_file_selected
        self._on_generate_clicked = on_generate_clicked
        self._on_toggle_appearance = on_toggle_appearance
        self._selected_file: Optional[Path] = None

        self._build()

    def _font(self, size: int = 14, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family=self._font_family, size=size, weight=weight)

    # -------- Layout --------

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 10))
        header.grid_columnconfigure(0, weight=1)

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            title_col, text="Generate Subtitles", font=self._font(30, "bold"), text_color=TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text="Upload your video or audio file to generate subtitles automatically.",
            font=self._font(15),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(4, 0))

        self.theme_button = ctk.CTkButton(
            header, text="\U0001F319", width=42, height=42, corner_radius=21,
            font=self._font(16), fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white",
            command=self._on_toggle_appearance,
        )
        self.theme_button.grid(row=0, column=1, sticky="ne")

        self.drop_zone = ctk.CTkFrame(
            self, corner_radius=16, border_width=2, border_color=BORDER, fg_color=SURFACE,
        )
        self.drop_zone.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)
        self.drop_zone.grid_rowconfigure(0, weight=1)
        self.drop_zone.grid_columnconfigure(0, weight=1)

        self._build_drop_zone_content()

        if DND_AVAILABLE:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self._on_drop)

        # -------- Generate button + progress (below drop zone) --------
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=40, pady=(0, 30))
        action_frame.grid_columnconfigure(0, weight=1)

        self.generate_button = ctk.CTkButton(
            action_frame, text="Generate Subtitles", font=self._font(16, "bold"),
            height=48, corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_HOVER,
            state="disabled", command=self._on_generate_clicked,
        )
        self.generate_button.pack(fill="x", pady=(10, 10))

        # Progress bar is created but NOT packed here -- it should only be
        # visible while a job is actually running (see set_busy()), not
        # sitting empty on screen by default.
        self.progress_bar = ctk.CTkProgressBar(
            action_frame, mode="indeterminate", progress_color=ACCENT, fg_color=PROGRESS_TRACK,
        )
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(action_frame, text="", font=self._font(14), text_color=TEXT_MUTED)
        self.status_label.pack(anchor="w")

    def _build_drop_zone_content(self) -> None:
        for widget in self.drop_zone.winfo_children():
            widget.destroy()

        inner = ctk.CTkFrame(self.drop_zone, fg_color="transparent")
        inner.grid(row=0, column=0)

        ctk.CTkLabel(
            inner, text="\u2B06", width=64, height=64, corner_radius=14,
            fg_color=ACCENT, text_color="white", font=self._font(26, "bold"),
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            inner, text="Drag & Drop your file here", font=self._font(19, "bold"), text_color=TEXT_PRIMARY,
        ).pack()
        ctk.CTkLabel(
            inner, text="Supports video and audio files", font=self._font(14), text_color=TEXT_MUTED,
        ).pack(pady=(4, 20))

        divider = ctk.CTkFrame(inner, fg_color="transparent")
        divider.pack(fill="x", pady=(0, 20))
        divider.grid_columnconfigure((0, 2), weight=1)
        ctk.CTkFrame(divider, height=1, fg_color=BORDER).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(divider, text="or", font=self._font(13), text_color=TEXT_MUTED).grid(row=0, column=1)
        ctk.CTkFrame(divider, height=1, fg_color=BORDER).grid(row=0, column=2, sticky="ew", padx=(10, 0))

        ctk.CTkButton(
            inner, text="\U0001F4C1  Locate File", font=self._font(15, "bold"), width=200, height=42,
            corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self._on_locate_file_clicked,
        ).pack()

    def _show_selected_file_state(self) -> None:
        for widget in self.drop_zone.winfo_children():
            widget.destroy()

        inner = ctk.CTkFrame(self.drop_zone, fg_color="transparent")
        inner.grid(row=0, column=0)

        ctk.CTkLabel(
            inner, text="\u2713", width=64, height=64, corner_radius=14,
            fg_color=SUCCESS, text_color="white", font=self._font(26, "bold"),
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            inner, text=self._selected_file.name, font=self._font(19, "bold"), text_color=TEXT_PRIMARY,
        ).pack()
        ctk.CTkLabel(
            inner, text="Ready to generate subtitles", font=self._font(14), text_color=TEXT_MUTED,
        ).pack(pady=(4, 20))

        ctk.CTkButton(
            inner, text="Choose a Different File", font=self._font(13), width=200, height=36,
            corner_radius=8, fg_color="transparent", hover_color=("gray85", "gray25"),
            text_color=TEXT_PRIMARY, border_width=1, border_color=BORDER,
            command=self._on_locate_file_clicked,
        ).pack()

    # -------- Event handlers --------

    def _on_locate_file_clicked(self) -> None:
        chosen = filedialog.askopenfilename(title="Select a video or audio file", filetypes=SUPPORTED_FILETYPES)
        if not chosen:
            return
        self.set_selected_file(Path(chosen))

    def _on_drop(self, event) -> None:
        paths = self.tk.splitlist(event.data)
        if not paths:
            return
        self.set_selected_file(Path(paths[0]))

    # -------- Public API (called by MainWindow) --------

    def set_selected_file(self, path: Path) -> None:
        self._selected_file = path
        self._show_selected_file_state()
        self.generate_button.configure(state="normal")
        self.status_label.configure(text="")
        self._on_file_selected(path)

    def set_status(self, text: str, color=None) -> None:
        self.status_label.configure(text=text, text_color=color or TEXT_MUTED)

    def set_busy(self, busy: bool) -> None:
        """
        Shows/hides the progress bar entirely -- it should never sit idle
        on screen, only appear while a job is actually running.
        """
        self.generate_button.configure(state="disabled" if busy else "normal")
        if busy:
            self.progress_bar.pack(fill="x", pady=(0, 10), before=self.status_label)
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()

    def set_theme_icon(self, icon: str) -> None:
        self.theme_button.configure(text=icon)