"""
Cross-platform helpers for opening files/folders in the OS's default
file manager or application.
"""
from __future__ import annotations

import platform
import subprocess
from pathlib import Path


def open_path(path: Path) -> None:
    """Open a file or folder using the OS's default handler."""
    system = platform.system()

    if system == "Windows":
        import os
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.run(["open", str(path)])
    else:
        subprocess.run(["xdg-open", str(path)])