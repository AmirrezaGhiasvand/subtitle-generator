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
from app.gui.model_missing_dialog import ModelMissingDialog
from app.gui.settings_view import SettingsView
from app.gui.sidebar import Sidebar
from app.gui.theme import SUCCESS
from app.services.model_downloader import ModelLoadError, ModelNotFoundError

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

        self._build_layout()

        self.after(0, self._maximize_on_start)

    def report_callback_exception(self, exc, val, tb):
        """
        Tkinter's default behavior for exceptions raised inside widget
        callbacks (button commands, after() callbacks, etc.) is to print
        to stderr and otherwise continue silently -- invisible in a
        packaged windowed exe. Log it to a real file instead.
        """
        import traceback
        from app.main import LOG_FILE

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n--- Tkinter callback exception ---\n")
            traceback.print_exception(exc, val, tb, file=f)

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

        self.settings_view = SettingsView(self.content_container, font_family=self._font_family)
        self.settings_view.grid(row=0, column=0, sticky="nsew")

        self._show_view("Generate")

    def _show_view(self, name: str) -> None:
        if name == "Generate":
            self.generate_view.tkraise()
        elif name == "History":
            self.history_tab.refresh()
            self.history_tab.tkraise()
        elif name == "Settings":
            self.settings_view.tkraise()

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

        target_language = self.generate_view.get_target_language()

        self.generate_view.set_busy(True)
        self.generate_view.set_status("Starting...")

        threading.Thread(target=self._run_pipeline_thread, args=(target_language,), daemon=True).start()
        self.after(100, self._poll_progress)

    def _run_pipeline_thread(self, target_language: str | None) -> None:
        try:
            result = run_pipeline(
                self._selected_file,
                target_language=target_language,
                on_progress=lambda msg: self._progress_queue.put(("progress", msg)),
            )
            self._progress_queue.put(("done", result))
        except ModelNotFoundError as e:
            self._progress_queue.put(("model_missing", e))
        except ModelLoadError as e:
            self._progress_queue.put(("model_corrupted", e))
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
                elif kind == "model_missing":
                    self._on_model_missing(payload, corrupted=False)
                    return
                elif kind == "model_corrupted":
                    self._on_model_missing(payload, corrupted=True)
                    return
                elif kind == "error":
                    self._on_pipeline_error(payload)
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_progress)

    def _on_pipeline_done(self, result: PipelineResult) -> None:
        self.generate_view.set_busy(False)
        self.generate_view.set_status(
            f"Done \u2014 {result.segment_count} segments, language: {result.language}", color=SUCCESS,
        )

        try:
            add_entry(
                source_file=self._selected_file,
                srt_path=result.srt_path,
                language=result.language,
                segment_count=result.segment_count,
                translated_srt_path=result.translated_srt_path,
                target_language=result.target_language,
            )
        except Exception:
            # A history-write failure shouldn't prevent the user from
            # seeing their (already successfully generated) files.
            import traceback
            from app.main import LOG_FILE
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write("\n--- add_entry failed ---\n")
                traceback.print_exc(file=f)

        message = f"SRT file saved to:\n{result.srt_path}"
        if result.translated_srt_path:
            message += f"\n\nTranslated ({result.target_language}) SRT saved to:\n{result.translated_srt_path}"

        messagebox.showinfo("Subtitles Generated", message)

    def _on_model_missing(self, error, corrupted: bool) -> None:
        self.generate_view.set_busy(False)
        status = "Speech recognition model files are corrupted." if corrupted else "Speech recognition model not found."
        self.generate_view.set_status(status, color="red")
        ModelMissingDialog(
            self, font_family=self._font_family, model_dir=error.model_dir,
            download_url=error.download_url, corrupted=corrupted,
        )

    def _on_pipeline_error(self, error_message: str) -> None:
        self.generate_view.set_busy(False)
        self.generate_view.set_status("An error occurred.", color="red")
        messagebox.showerror("Error", error_message)


def launch() -> None:
    app = MainWindow()
    app.mainloop()