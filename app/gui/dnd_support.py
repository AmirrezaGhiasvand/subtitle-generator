"""
Enables real OS-level drag-and-drop (accepting dropped files) on top of
CustomTkinter, which has no built-in drag-and-drop support of its own.
"""
from __future__ import annotations

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD


class DnDCTk(ctk.CTk, TkinterDnD.DnDWrapper):
    """A CustomTkinter root window that also supports native drag-and-drop."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)