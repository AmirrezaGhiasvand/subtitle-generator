"""
CustomTkinter desktop interface for the subtitle generator.
"""
from __future__ import annotations

import platform
import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.core.history import add_entry
from app.core.pipeline import PipelineResult, run_pipeline
from app.gui.fonts import setup_fonts
from app.gui.history_tab import HistoryTab

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

SUPPORTED_FILETYPES = [
    ("Video/Audio files", "*.mp4 *.mkv *.mov *.avi *.mp3 *.wav *.m4a *.flac"),
    ("All files", "*.*"),
]


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self._font_family = setup_fonts()

        self.title("Subtitle Generator")
        self.minsize(640, 480)
        self.resizable(True, True)
        self._maximize_on_start()

        self._selected_file: Path | None = None
        self._progress_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()

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
            # Fall back to a large centered window if the OS/window manager
            # doesn't support a "maximized" state flag.
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            self.geometry(f"{int(screen_w * 0.85)}x{int(screen_h * 0.85)}+50+50")

    def _font(self, size: int = 13, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family=self._font_family, size=size, weight=weight)

    # -------- UI construction --------

    def _build_layout(self) -> None:
        self.tabview = ctk.CTkTabview(self, command=self._on_tab_changed)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.generate_tab = self.tabview.add("Generate")
        self.history_tab_container = self.tabview.add("History")

        self._build_generate_tab()

        self.history_tab = HistoryTab(self.history_tab_container, font_family=self._font_family)
        self.history_tab.pack(fill="both", expand=True)

    def _build_generate_tab(self) -> None:
        container = ctk.CTkFrame(self.generate_tab, fg_color="transparent")
        container.pack(expand=True)

        ctk.CTkLabel(container, text="Subtitle Generator", font=self._font(24, "bold")).pack(pady=(10, 20))

        self.select_button = ctk.CTkButton(
            container, text="Select Video or Audio File", font=self._font(14),
            command=self._on_select_file, width=280, height=40,
        )
        self.select_button.pack(pady=10)

        self.file_label = ctk.CTkLabel(container, text="No file selected", font=self._font(13), text_color="gray")
        self.file_label.pack(pady=10)

        self.generate_button = ctk.CTkButton(
            container, text="Generate Subtitles", font=self._font(14, "bold"),
            command=self._on_generate, state="disabled", width=280, height=40,
        )
        self.generate_button.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(container, mode="indeterminate", width=320)
        self.progress_bar.pack(pady=(20, 0))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(container, text="", font=self._font(13), text_color="gray")
        self.status_label.pack(pady=(10, 20))

    # -------- Tab handling --------

    def _on_tab_changed(self) -> None:
        if self.tabview.get() == "History":
            self.history_tab.refresh()

    # -------- Event handlers --------

    def _on_select_file(self) -> None:
        chosen = filedialog.askopenfilename(title="Select a video or audio file", filetypes=SUPPORTED_FILETYPES)
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

        add_entry(
            source_file=self._selected_file,
            srt_path=result.srt_path,
            language=result.language,
            segment_count=result.segment_count,
        )
        self.history_tab.refresh()

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