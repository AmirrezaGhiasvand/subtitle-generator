from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.audio_extractor import extract_audio

extract_audio(Path("E:/subtitle-generator/4_5864224552116041056.mp4"), Path("output/test.wav"))
print("Success — check output/test.wav")