"""
Application entry point — launches the desktop GUI.
"""
import sys
import io
import traceback
from pathlib import Path
from platformdirs import user_log_dir

# When packaged as a windowed (console=False) executable, Windows gives the
# process no stdout/stderr at all -- they're None, not just hidden. Any
# library that tries to print crashes immediately on that None. Dummy
# streams avoid that crash, but they also mean Tkinter's default behavior
# of printing callback exceptions to stderr now goes nowhere -- exceptions
# inside button/after() callbacks fail completely silently. We fix that
# below by writing them to a real log file instead.
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

LOG_DIR = Path(user_log_dir("Subtitle Generator", "subtitle-generator"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "error.log"


def _log_uncaught_exception(exc_type, exc_value, exc_tb) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n--- Uncaught exception ---\n")
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)


sys.excepthook = _log_uncaught_exception

from app.gui.main_window import launch

if __name__ == "__main__":
    launch()