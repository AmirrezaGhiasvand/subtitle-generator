from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.audio_extractor import extract_audio
from app.services.transcriber import transcribe_audio
from app.core.srt_writer import write_srt

wav_path = extract_audio(Path("E:/subtitle-generator/4_5864224552116041056.mp4"), Path("output/test.wav"))
result = transcribe_audio(wav_path)

srt_path = write_srt(result.segments, Path("output/subtitles.srt"))
print(f"Detected language: {result.language} (confidence: {result.language_probability:.2f})")
print(f"SRT written to: {srt_path}")