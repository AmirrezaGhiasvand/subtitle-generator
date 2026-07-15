"""
Cross-platform loading of the bundled Inter font for a consistent UI look.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONT_FAMILY = "Inter"

_FONT_FILES = [
    "Inter-Regular.ttf",
    "Inter-Medium.ttf",
    "Inter-SemiBold.ttf",
    "Inter-Bold.ttf",
]


def setup_fonts() -> str:
    """
    Ensure a good-looking UI font is available and return the family name
    the app should use for all CTkFont(...) calls.
    """
    system = platform.system()

    if system == "Darwin":
        # macOS already ships San Francisco as its default UI font.
        return ".AppleSystemUIFont"

    if system == "Windows":
        return FONT_FAMILY if _load_fonts_windows() else "Segoe UI"

    if system == "Linux":
        return FONT_FAMILY if _install_fonts_linux() else "DejaVu Sans"

    return "Helvetica"


def _load_fonts_windows() -> bool:
    try:
        import ctypes

        gdi32 = ctypes.WinDLL("gdi32")
        FR_PRIVATE = 0x10

        all_loaded = True
        for filename in _FONT_FILES:
            font_path = FONTS_DIR / filename
            if not font_path.exists():
                all_loaded = False
                continue
            if gdi32.AddFontResourceExW(str(font_path), FR_PRIVATE, 0) == 0:
                all_loaded = False

        return all_loaded
    except Exception:
        return False


def _install_fonts_linux() -> bool:
    try:
        target_dir = Path.home() / ".local" / "share" / "fonts" / "subtitle-generator-inter"
        target_dir.mkdir(parents=True, exist_ok=True)

        for filename in _FONT_FILES:
            source = FONTS_DIR / filename
            if source.exists():
                shutil.copy(source, target_dir / filename)

        subprocess.run(["fc-cache", "-f", str(target_dir)], capture_output=True, timeout=10)
        return True
    except Exception:
        return False