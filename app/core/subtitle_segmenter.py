"""
Splits word-level transcription timestamps into subtitle-appropriately
sized chunks (a max word count per line), instead of using Whisper's own
segment boundaries directly. Whisper's segments are sentence/pause-based
and can run much longer than what's comfortable to read as an on-screen
subtitle.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

DEFAULT_MAX_WORDS_PER_SEGMENT = 7

# Splitting mid-sentence still looks better if it happens at a natural
# pause -- prefer to break right after these punctuation marks even if
# the word count hasn't hit the max yet.
SENTENCE_END_CHARS = (".", "!", "?")


@dataclass
class SubtitleSegment:
    start: float
    end: float
    text: str


def resegment_by_word_count(words: Sequence, max_words: int = DEFAULT_MAX_WORDS_PER_SEGMENT) -> list[SubtitleSegment]:
    """
    Group word-level timestamps (objects with .start, .end, .text) into
    subtitle segments of at most `max_words` words each, breaking early at
    sentence-ending punctuation when possible.
    """
    if max_words < 1:
        raise ValueError("max_words must be at least 1")

    segments: list[SubtitleSegment] = []
    current: list = []

    for word in words:
        current.append(word)

        ends_sentence = word.text.rstrip().endswith(SENTENCE_END_CHARS)
        at_max = len(current) >= max_words

        if at_max or ends_sentence:
            segments.append(_build_segment(current))
            current = []

    if current:
        segments.append(_build_segment(current))

    return segments


def _build_segment(words: list) -> SubtitleSegment:
    text = " ".join(w.text.strip() for w in words).strip()
    return SubtitleSegment(start=words[0].start, end=words[-1].end, text=text)