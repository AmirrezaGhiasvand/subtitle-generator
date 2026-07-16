"""
Left navigation sidebar: app branding + Generate/History nav items.
"""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.gui.theme import ACCENT, ACCENT_HOVER, SIDEBAR_HOVER, TEXT_PRIMARY

NAV_ITEMS = ["Generate", "History", "Settings"]
NAV_ICONS = {"Generate": "\u2728", "History": "\U0001F553", "Settings": "\u2699"}


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, font_family: str, on_navigate: Callable[[str], None], **kwargs):
        super().__init__(master, width=220, corner_radius=0, **kwargs)
        self.grid_propagate(False)

        self._font_family = font_family
        self._on_navigate = on_navigate
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._active = "Generate"

        self._build()

    def _font(self, size: int = 14, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family=self._font_family, size=size, weight=weight)

    def _build(self) -> None:
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=(24, 30))

        ctk.CTkLabel(
            brand_frame, text="\U0001F3AC  Subtitle Generator", font=self._font(17, "bold"),
            text_color=TEXT_PRIMARY, anchor="w",
        ).pack(fill="x")

        for item in NAV_ITEMS:
            btn = ctk.CTkButton(
                self,
                text=f"{NAV_ICONS[item]}   {item}",
                font=self._font(15),
                anchor="w",
                fg_color="transparent",
                text_color=TEXT_PRIMARY,
                hover_color=SIDEBAR_HOVER,
                corner_radius=8,
                height=42,
                command=lambda name=item: self._handle_click(name),
            )
            btn.pack(fill="x", padx=14, pady=4)
            self._nav_buttons[item] = btn

        self._update_active_styles()

    def _handle_click(self, name: str) -> None:
        self._active = name
        self._update_active_styles()
        self._on_navigate(name)

    def _update_active_styles(self) -> None:
        for name, btn in self._nav_buttons.items():
            if name == self._active:
                btn.configure(fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white")
            else:
                btn.configure(fg_color="transparent", hover_color=SIDEBAR_HOVER, text_color=TEXT_PRIMARY)