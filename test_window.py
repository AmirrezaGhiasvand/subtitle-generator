import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.gui.dnd_support import DnDCTk

print("Creating window...")
app = DnDCTk()
print("Window created, TkdndVersion:", app.TkdndVersion)
app.title("Test")
app.geometry("400x300")
print("About to enter mainloop...")
app.mainloop()
print("Mainloop exited")