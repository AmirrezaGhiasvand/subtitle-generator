# Subtitle Generator

A simple desktop app: drop in a video or audio file, get back an accurate
`.srt` subtitle file. Runs fully offline using local, open-source speech
recognition (Faster-Whisper), with optional AI-powered translation into
another language.

![Generate Subtitles screenshot](docs/screenshot-generate.png)

## Features

- Drag & drop (or browse) video/audio files — MP4, MKV, MOV, AVI, MP3, WAV, M4A, FLAC, and more
- Automatic language detection
- Word-accurate subtitle timing, capped at ~7 words per line for readability
- Optional translation into 14+ languages (via OpenRouter, requires a free API key)
- History tab — revisit and re-open any past result
- Runs entirely on your machine — no video/audio ever leaves your computer (translation text is the only thing sent to a third-party API, and only if you use that feature)

## Download

Grab the latest `.exe` from the [v1.0.0 release](https://github.com/AmirrezaGhiasvand/subtitle-generator/releases/tag/v1.0.0). No installation required — just run it.

**Requirements:**

- Windows 10/11
- [FFmpeg](https://ffmpeg.org/download.html) installed and on your system PATH
- ~2GB free disk space for the speech recognition model (one-time download, see below)

## First-time setup

The app needs the Faster-Whisper model files (~1.6GB), downloaded once and reused for every file after that:

1. Open the app — if the model isn't found, it'll show you exactly what to do
2. Click **Open Download Page**, download every file listed there
3. Click **Open Models Folder**, move the downloaded files in
4. Come back and click **Generate Subtitles**

Already have the model files somewhere else on your machine? Use **Locate Model Folder** (in that same dialog, or under **Settings**) to point the app at them instead — no need to move anything.

## Using the app

1. **Generate tab** — drag a video/audio file onto the drop zone, or click _Locate File_
2. _(Optional)_ Choose a language under **Translate to** if you want a second, translated subtitle file
3. Click **Generate Subtitles** and wait — progress is shown live
4. You'll get an `.srt` file (and a translated one, if selected) saved next to your source file in an `output` folder
5. **History tab** — see everything you've generated, with quick buttons to open the file or reveal it in your file explorer

## Setting up translation (optional)

Translation uses [OpenRouter](https://openrouter.ai) — a small per-request cost, no subscription.

1. Get a free API key at [openrouter.ai/keys](https://openrouter.ai/keys)
2. Go to **Settings** in the app, paste your key, save
3. Pick a target language on the Generate tab from then on

## Troubleshooting

Something not working? Go to **Settings → Open Log File** — it has the technical details of anything that went wrong, useful if you're reporting a bug.

## Tech stack

Python · CustomTkinter · Faster-Whisper (CTranslate2) · FFmpeg · OpenRouter · PyInstaller

## License

MIT
