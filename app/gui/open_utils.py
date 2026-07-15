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


def reveal_file(path: Path) -> None:
    """
    Open the file's containing folder with the file itself highlighted/
    selected, rather than just opening the folder. Falls back to plain
    folder-opening where the OS/file manager has no "select" capability.
    """
    system = platform.system()

    if system == "Windows":
        subprocess.run(["explorer", f"/select,{path}"])
        return

    if system == "Darwin":
        subprocess.run(["open", "-R", str(path)])
        return

    # Linux has no universal "select in file manager" API -- different
    # file managers support different flags. Try common ones, then fall
    # back to just opening the containing folder.
    for command in (["nautilus", "--select", str(path)], ["dolphin", "--select", str(path)]):
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=3)
            return
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue

    subprocess.run(["xdg-open", str(path.parent)])