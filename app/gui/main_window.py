"""
CustomTkinter desktop interface for the subtitle generator.
"""
from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.core.pipeline import PipelineResult, run_pipeline

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

SUPPORTED_FILETYPES = [
    ("Video/Audio files", "*.mp4 *.mkv *.mov *.avi *.mp3 *.wav *.m4a *.flac"),
    ("All files", "*.*"),
]


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Subtitle Generator")
        self.geometry("560x340")
        self.resizable(False, False)

        self._selected_file: Path | None = None
        self._progress_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()

        self._build_layout()

    # -------- UI construction --------

    def _build_layout(self) -> None:
        padding = {"padx": 20, "pady": 10}

        self.title_label = ctk.CTkLabel(
            self, text="Subtitle Generator", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))

        self.select_button = ctk.CTkButton(
            self, text="Select Video or Audio File", command=self._on_select_file
        )
        self.select_button.pack(**padding)

        self.file_label = ctk.CTkLabel(self, text="No file selected", text_color="gray")
        self.file_label.pack(**padding)

        self.generate_button = ctk.CTkButton(
            self, text="Generate Subtitles", command=self._on_generate, state="disabled"
        )
        self.generate_button.pack(**padding)

        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=40, pady=(10, 0))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=(10, 20))

    # -------- Event handlers --------

    def _on_select_file(self) -> None:
        chosen = filedialog.askopenfilename(
            title="Select a video or audio file", filetypes=SUPPORTED_FILETYPES
        )
        if not chosen:
            return

        self._selected_file = Path(chosen)
        self.file_label.configure(text=self._selected_file.name, text_color="white")
        self.generate_button.configure(state="normal")
        self.status_label.configure(text="")

    def _on_generate(self) -> None:
        if self._selected_file is None:
            return

        self.select_button.configure(state="disabled")
        self.generate_button.configure(state="disabled")
        self.progress_bar.start()
        self.status_label.configure(text="Starting...", text_color="gray")

        threading.Thread(target=self._run_pipeline_thread, daemon=True).start()
        self.after(100, self._poll_progress)

    # -------- Background work --------

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
                    self.status_label.configure(text=payload, text_color="gray")
                elif kind == "done":
                    self._on_pipeline_done(payload)  # type: ignore[arg-type]
                    return
                elif kind == "error":
                    self._on_pipeline_error(payload)  # type: ignore[arg-type]
                    return
        except queue.Empty:
            pass

        self.after(100, self._poll_progress)

    # -------- Completion handlers --------

    def _on_pipeline_done(self, result: PipelineResult) -> None:
        self.progress_bar.stop()
        self.progress_bar.set(1)
        self.status_label.configure(
            text=f"Done — {result.segment_count} segments, language: {result.language}",
            text_color="green",
        )
        self.select_button.configure(state="normal")
        self.generate_button.configure(state="normal")
        messagebox.showinfo("Subtitles Generated", f"SRT file saved to:\n{result.srt_path}")

    def _on_pipeline_error(self, error_message: str) -> None:
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.status_label.configure(text="An error occurred.", text_color="red")
        self.select_button.configure(state="normal")
        self.generate_button.configure(state="normal")
        messagebox.showerror("Error", error_message)


def launch() -> None:
    app = MainWindow()
    app.mainloop()