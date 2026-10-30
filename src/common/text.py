"""Small shared text utilities (stdlib only, no dependencies)."""

import re

_WORD_STRIP = ".,;:!?()[]{}\"'`"

# Sentence splitter: good enough for extractive demos, not abbreviation-aware.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def tokens(text: str) -> set:
    """Lowercased token set, punctuation-stripped, stopwords-too-short removed."""
    out = set()
    for word in (text or "").lower().split():
        word = word.strip(_WORD_STRIP)
        if len(word) > 2:
            out.add(word)
    return out


def split_sentences(text: str) -> list:
    """Split text into sentences on ., !, ? boundaries."""
    return [p.strip() for p in _SENTENCE_SPLIT.split(text or "") if p.strip()]
