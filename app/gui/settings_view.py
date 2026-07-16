"""
Settings view: OpenRouter API key + translation model configuration.
"""
from __future__ import annotations

import customtkinter as ctk

from app.core.app_settings import (
    DEFAULT_MODEL,
    get_openrouter_api_key,
    get_translation_model,
    set_openrouter_api_key,
    set_translation_model,
)
from app.gui.theme import ACCENT, ACCENT_HOVER, SUCCESS, SURFACE, TEXT_MUTED, TEXT_PRIMARY

SUGGESTED_MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-haiku",
    "google/gemini-flash-1.5",
]


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, font_family: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._font_family = font_family
        self._build()

    def _font(self, size: int = 14, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family=self._font_family, size=size, weight=weight)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 10))
        ctk.CTkLabel(header, text="Settings", font=self._font(30, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Configure translation via OpenRouter.", font=self._font(15), text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(4, 0))

        card = ctk.CTkFrame(self, corner_radius=14, fg_color=SURFACE)
        card.grid(row=1, column=0, sticky="ew", padx=40, pady=10)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="OpenRouter API Key", font=self._font(15, "bold"), text_color=TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 4))
        ctk.CTkLabel(
            card, text="Get a key at openrouter.ai/keys. Stored securely on this device.",
            font=self._font(12), text_color=TEXT_MUTED, anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))

        self.key_entry = ctk.CTkEntry(
            card, show="\u2022", font=self._font(14), height=38, placeholder_text="sk-or-...",
        )
        self.key_entry.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 6))
        existing_key = get_openrouter_api_key()
        if existing_key:
            self.key_entry.insert(0, existing_key)

        self.show_key_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            card, text="Show key", variable=self.show_key_var, font=self._font(12),
            text_color=TEXT_MUTED, command=self._toggle_key_visibility,
        ).grid(row=3, column=0, sticky="w", padx=24, pady=(0, 16))

        ctk.CTkLabel(
            card, text="Translation Model", font=self._font(15, "bold"), text_color=TEXT_PRIMARY, anchor="w",
        ).grid(row=4, column=0, sticky="ew", padx=24, pady=(10, 4))
        ctk.CTkLabel(
            card, text="Any OpenRouter model ID. A cheap, capable default is pre-filled.",
            font=self._font(12), text_color=TEXT_MUTED, anchor="w",
        ).grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 10))

        self.model_combo = ctk.CTkComboBox(card, values=SUGGESTED_MODELS, font=self._font(14), height=38)
        self.model_combo.set(get_translation_model() or DEFAULT_MODEL)
        self.model_combo.grid(row=6, column=0, sticky="ew", padx=24, pady=(0, 20))

        self.save_button = ctk.CTkButton(
            card, text="Save Settings", font=self._font(14, "bold"), height=40,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self._on_save,
        )
        self.save_button.grid(row=7, column=0, sticky="ew", padx=24, pady=(0, 16))

        self.status_label = ctk.CTkLabel(card, text="", font=self._font(12), text_color=TEXT_MUTED)
        self.status_label.grid(row=8, column=0, sticky="w", padx=24, pady=(0, 20))

    def _toggle_key_visibility(self) -> None:
        self.key_entry.configure(show="" if self.show_key_var.get() else "\u2022")

    def _on_save(self) -> None:
        key = self.key_entry.get().strip()
        model = self.model_combo.get().strip() or DEFAULT_MODEL

        if key:
            set_openrouter_api_key(key)
        set_translation_model(model)

        self.status_label.configure(text="Saved.", text_color=SUCCESS)