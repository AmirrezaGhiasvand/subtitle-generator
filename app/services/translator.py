"""
Translates transcript segments into a target language using an LLM via
the OpenRouter API (https://openrouter.ai).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import requests

from app.core.app_settings import get_openrouter_api_key, get_translation_model

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Segments are translated in batches to reduce API calls and give the
# model more surrounding context than translating one isolated line at a
# time, while staying well under typical context limits.
BATCH_SIZE = 25


class TranslationError(Exception):
    """Raised when translation fails (missing key, API error, bad response)."""


@dataclass
class TranslatedSegment:
    start: float
    end: float
    text: str


def translate_segments(segments: Sequence, target_language: str) -> list[TranslatedSegment]:
    """
    Translate a list of transcript segments (objects with .start, .end,
    .text) into `target_language`, preserving their original timing.
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        raise TranslationError(
            "No OpenRouter API key configured. Add one in the Settings tab before translating."
        )

    model = get_translation_model()
    translated: list[TranslatedSegment] = []

    for i in range(0, len(segments), BATCH_SIZE):
        batch = list(segments[i : i + BATCH_SIZE])
        translated_texts = _translate_batch([s.text for s in batch], target_language, api_key, model)

        if len(translated_texts) != len(batch):
            # Fall back to one-by-one if the model didn't return the exact
            # count we expect -- slower, but keeps timestamps correctly
            # aligned rather than risking silently mismatched subtitles.
            translated_texts = [
                _translate_batch([s.text], target_language, api_key, model)[0] for s in batch
            ]

        for seg, text in zip(batch, translated_texts):
            translated.append(TranslatedSegment(start=seg.start, end=seg.end, text=text))

    return translated


def _translate_batch(texts: list[str], target_language: str, api_key: str, model: str) -> list[str]:
    numbered_input = "\n".join(f"{idx + 1}. {text}" for idx, text in enumerate(texts))

    prompt = (
    f"You are translating subtitles into {target_language}.\n\n"
    "Translate each numbered line naturally, as if it were spoken in a real conversation. "
    "Use a friendly, informal tone whenever appropriate, you can change the words to sound natural in the target language, but keep the meaning,"
    "emotion, and context.\n\n"
    "Rules:\n"
    "- Keep the same numbering.\n"
    "- Use , when a sentence is unfinished to indicate continuation.\n"
    "- Output exactly one translated line for each input line.\n"
    "- Do not merge, split, remove, or reorder lines.\n"
    "- Keep subtitles concise and easy to read.\n"
    "- Do not add explanations, notes, or commentary.\n"
    "- If the original is casual or slangy, translate it into a natural equivalent rather than literally.\n\n"
    f"{numbered_input}"
)

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
            timeout=60,
        )
    except requests.RequestException as e:
        raise TranslationError(f"Could not reach OpenRouter: {e}") from e

    if response.status_code == 401:
        raise TranslationError("OpenRouter rejected the API key (401 Unauthorized). Check Settings.")
    if response.status_code != 200:
        raise TranslationError(f"OpenRouter API error ({response.status_code}): {response.text[:200]}")

    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as e:
        raise TranslationError(f"Unexpected response format from OpenRouter: {e}") from e

    return _parse_numbered_response(content, expected_count=len(texts))


def _parse_numbered_response(content: str, expected_count: int) -> list[str]:
    results: dict[int, str] = {}
    fallback_order: list[str] = []

    for line in (line.strip() for line in content.strip().splitlines() if line.strip()):
        prefix, _, rest = line.partition(". ")
        if prefix.isdigit() and rest:
            results[int(prefix)] = rest.strip()
        else:
            fallback_order.append(line)

    ordered = []
    fallback_iter = iter(fallback_order)
    for i in range(1, expected_count + 1):
        if i in results:
            ordered.append(results[i])
        else:
            ordered.append(next(fallback_iter, ""))

    return ordered