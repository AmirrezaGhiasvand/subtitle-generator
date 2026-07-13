from pathlib import Path
from app.services.audio_extractor import extract_audio

extract_audio(Path("E:/subtitle-generator/4_5864224552116041056.mp4"), Path("output/test.wav"))
print("Success — check output/test.wav")