"""
Application entry point — launches the desktop GUI.
"""
import sys
import io

# When packaged as a windowed (console=False) executable, Windows gives the
# process no stdout/stderr at all -- they're None, not just hidden. Any
# library that tries to print or show a progress bar (e.g. huggingface_hub's
# download progress via tqdm) then crashes with "'NoneType' object has no
# attribute 'write'" the moment it runs. Giving them harmless dummy streams
# instead avoids that entire class of crash.
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

from app.gui.main_window import launch

if __name__ == "__main__":
    launch()