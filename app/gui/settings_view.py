"""
Settings view: OpenRouter API key + translation model configuration,
and the speech recognition model file location.
"""
from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.core.app_settings import (
    DEFAULT_MODEL,
    clear_custom_model_path,
    get_custom_model_path,
    get_openrouter_api_key,
    get_translation_model,
    set_custom_model_path,
    set_openrouter_api_key,
    set_translation_model,
)
from app.gui.theme import ACCENT, ACCENT_HOVER, BORDER, SUCCESS, SURFACE, TEXT_MUTED, TEXT_PRIMARY
from app.services.model_downloader import (
    MODEL_DOWNLOAD_URL,
    get_default_model_dir,
    is_valid_model_folder,
    resolve_model_path,
)

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
            header, text="Configure the speech recognition model and translation.",
            font=self._font(15), text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(4, 0))

        self._build_model_card()
        self._build_translation_card()

    def _build_model_card(self) -> None:
        card = ctk.CTkFrame(self, corner_radius=14, fg_color=SURFACE)
        card.grid(row=1, column=0, sticky="ew", padx=40, pady=10)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Speech Recognition Model", font=self._font(15, "bold"), text_color=TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 4))

        self.model_status_label = ctk.CTkLabel(
            card, text="", font=self._font(12), text_color=TEXT_MUTED, anchor="w", justify="left",
        )
        self.model_status_label.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))
        self._refresh_model_status()

        button_row = ctk.CTkFrame(card, fg_color="transparent")
        button_row.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))

        ctk.CTkButton(
            button_row, text="Locate Model Folder...", font=self._font(13), height=36,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self._on_locate_model_clicked,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_row, text="Use Default Location", font=self._font(13), height=36,
            fg_color="transparent", hover_color=("gray85", "gray25"),
            text_color=TEXT_PRIMARY, border_width=1, border_color=BORDER,
            command=self._on_use_default_clicked,
        ).pack(side="left")

    def _refresh_model_status(self) -> None:
        resolved = resolve_model_path()
        custom = get_custom_model_path()

        if resolved:
            source = "custom folder" if (custom and Path(custom) == resolved) else "default location"
            self.model_status_label.configure(
                text=f"\u2713 Model files found ({source}):\n{resolved}", text_color=SUCCESS,
            )
        else:
            self.model_status_label.configure(
                text=(
                    f"Model files not found. Download them from:\n{MODEL_DOWNLOAD_URL}\n\n"
                    f"Default location:\n{get_default_model_dir()}"
                ),
                text_color=TEXT_MUTED,
            )

    def _on_locate_model_clicked(self) -> None:
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
        self._refresh_model_status()

    def _on_use_default_clicked(self) -> None:
        clear_custom_model_path()
        self._refresh_model_status()

    def _build_translation_card(self) -> None:
        card = ctk.CTkFrame(self, corner_radius=14, fg_color=SURFACE)
        card.grid(row=2, column=0, sticky="ew", padx=40, pady=10)
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