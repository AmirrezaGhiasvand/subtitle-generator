# Subtitle Generator

A simple, open-source desktop app: drop in a video or audio file, get back an
`.srt` subtitle file — spoken language auto-detected, with an optional
translation into a language of your choice. Runs fully locally using
open-source AI models, packaged as a single desktop executable.

🔗 **Repo:** [github.com/<your-username>/subtitle-generator](https://github.com/AmirrezaGhiasvand/subtitle-generator)

> 🚧 **Status: early development.** Currently building the core pipeline
> (FFmpeg → Faster-Whisper → SRT). See [Roadmap](#roadmap) below.

---

## The Journey

This project actually started out scoped as a full web application — FastAPI
backend, React frontend, Docker, the works. Partway through building the
foundation, the scope was deliberately cut down to what the project actually
needed to be: a focused, single-purpose desktop tool. Simpler, more shippable,
and more useful for the actual use case (a local file in, a subtitle file out)
than a web app would have been.

While evaluating translation options, the initial pick — Argos Translate —
turned out to pull in a full PyTorch + CUDA toolkit stack (multiple GB) just
for sentence-boundary detection. Swapped to CTranslate2-based OPUS-MT models
instead, reusing the same lightweight inference engine already used for
transcription (Faster-Whisper) — keeping the whole app's runtime footprint
small and torch-free.

---

## Features

**In progress:**
- [ ] Upload/select a video or audio file
- [ ] Extract audio via FFmpeg
- [ ] Transcribe with Faster-Whisper, auto-detecting the spoken language
- [ ] Generate a valid `.srt` file
- [ ] Optional translation into a chosen target language (CTranslate2 / OPUS-MT)
- [ ] Simple, modern desktop UI (CustomTkinter)
- [ ] Packaged as a standalone `.exe` (PyInstaller)

---

## Tech Stack

- **GUI:** CustomTkinter
- **Speech recognition:** Faster-Whisper (local, auto language detection)
- **Translation:** CTranslate2 + OPUS-MT models (local, no PyTorch required)
- **Audio extraction:** FFmpeg
- **Packaging:** PyInstaller

---

## Getting Started

*Not yet runnable end-to-end — filled in as the pipeline comes together.*

### Prerequisites
- Python 3.11+
- [FFmpeg](https://ffmpeg.org/) installed and on your system PATH
- Linux only: `tkinter` may need a separate install (`sudo apt install python3-tk`) —
  it ships by default with Python on Windows and macOS

### Setup
```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements-dev.txt
```

---

## Roadmap

1. FFmpeg audio extraction service
2. Faster-Whisper transcription (with language auto-detection)
3. SRT formatter
4. CTranslate2/OPUS-MT translation service
5. CustomTkinter desktop UI wired to the pipeline
6. Progress reporting during processing
7. PyInstaller packaging into a standalone `.exe`

---

## License

MIT
