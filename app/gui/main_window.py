"""
CustomTkinter desktop interface for the subtitle generator.
"""
from __future__ import annotations

import platform
import queue
import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from app.core.history import add_entry
from app.core.pipeline import PipelineResult, run_pipeline
from app.gui.dnd_support import DnDCTk
from app.gui.fonts import setup_fonts
from app.gui.generate_view import GenerateView
from app.gui.history_tab import HistoryTab
from app.gui.sidebar import Sidebar

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MainWindow(DnDCTk):
    def __init__(self):
        super().__init__()

        self._font_family = setup_fonts()
        self._selected_file: Path | None = None
        self._progress_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self._appearance = "dark"

        self.title("Subtitle Generator")
        self.minsize(900, 600)
        self.resizable(True, True)
        self._maximize_on_start()

        self._build_layout()

    # -------- Startup helpers --------

    def _maximize_on_start(self) -> None:
        system = platform.system()
        try:
            if system in ("Windows", "Darwin"):
                self.state("zoomed")
            else:
                self.attributes("-zoomed", True)
        except Exception:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            self.geometry(f"{int(screen_w * 0.85)}x{int(screen_h * 0.85)}+50+50")

    # -------- Layout --------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, font_family=self._font_family, on_navigate=self._on_navigate)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self.generate_view = GenerateView(
            self.content_container,
            font_family=self._font_family,
            on_file_selected=self._on_file_selected,
            on_generate_clicked=self._on_generate_clicked,
            on_toggle_appearance=self._on_toggle_appearance,
        )
        self.generate_view.grid(row=0, column=0, sticky="nsew")

        self.history_tab = HistoryTab(self.content_container, font_family=self._font_family)
        self.history_tab.grid(row=0, column=0, sticky="nsew")

        self._show_view("Generate")

    def _show_view(self, name: str) -> None:
        if name == "Generate":
            self.generate_view.tkraise()
        else:
            self.history_tab.refresh()
            self.history_tab.tkraise()

    # -------- Navigation / theme --------

    def _on_navigate(self, name: str) -> None:
        self._show_view(name)

    def _on_toggle_appearance(self) -> None:
        self._appearance = "light" if self._appearance == "dark" else "dark"
        ctk.set_appearance_mode(self._appearance)
        self.generate_view.set_theme_icon("\u2600\uFE0F" if self._appearance == "light" else "\U0001F319")

    # -------- File selection / generation --------

    def _on_file_selected(self, path: Path) -> None:
        self._selected_file = path

    def _on_generate_clicked(self) -> None:
        if self._selected_file is None:
            return

        self.generate_view.set_busy(True)
        self.generate_view.set_status("Starting...")

        threading.Thread(target=self._run_pipeline_thread, daemon=True).start()
        self.after(100, self._poll_progress)

    def _run_pipeline_thread(self) -> None:
        try:
            result = run_pipeline(
                self._selected_file,
                on_progress=lambda msg: self._progress_queue.put(("progress", msg)),
            )
            self._progress_queue.put(("done", result))
        except Exception as e:
            self._progress_queue.put(("error", str(e)))

    def _poll_progress(self) -> None:
        try:
            while True:
                kind, payload = self._progress_queue.get_nowait()
                if kind == "progress":
                    self.generate_view.set_status(payload)
                elif kind == "done":
                    self._on_pipeline_done(payload)
                    return
                elif kind == "error":
                    self._on_pipeline_error(payload)
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_progress)

    def _on_pipeline_done(self, result: PipelineResult) -> None:
        self.generate_view.set_busy(False)
        self.generate_view.complete_progress()
        self.generate_view.set_status(
            f"Done \u2014 {result.segment_count} segments, language: {result.language}", color="green",
        )

        add_entry(
            source_file=self._selected_file,
            srt_path=result.srt_path,
            language=result.language,
            segment_count=result.segment_count,
        )

        messagebox.showinfo("Subtitles Generated", f"SRT file saved to:\n{result.srt_path}")

    def _on_pipeline_error(self, error_message: str) -> None:
        self.generate_view.set_busy(False)
        self.generate_view.reset_progress()
        self.generate_view.set_status("An error occurred.", color="red")
        messagebox.showerror("Error", error_message)


def launch() -> None:
    app = MainWindow()
    app.mainloop()