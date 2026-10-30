"""Offline provider used for the zero-key demo and the test suite.

Ranks a small local corpus (sample_corpus/*.json) by token overlap with
the query. Swap in a live provider when API access exists; the pipeline
code does not change. That is the point of the provider interface.
"""

import json
import pathlib

from ..common.text import tokens
from .base import SearchProvider, SearchResult


class LocalCorpusProvider(SearchProvider):
    """Ranks local JSON documents by lexical overlap. No network, no keys."""

    name = "local_corpus"

    def __init__(self, corpus_dir: str = "sample_corpus"):
        self.corpus_dir = pathlib.Path(corpus_dir)
        self.docs: list = []
        if not self.corpus_dir.exists():
            raise FileNotFoundError(
                f"corpus dir not found: {self.corpus_dir.resolve()} "
                "(run from the repo root, or pass corpus_dir=...)"
            )
        for path in sorted(self.corpus_dir.glob("*.json")):
            self.docs.extend(json.loads(path.read_text(encoding="utf-8")))

    def search(self, query: str, top_k: int = 5) -> list:
        q_tokens = tokens(query)
        scored = []
        for doc in self.docs:
            text = f"{doc.get('title', '')} {doc.get('snippet', '')}"
            overlap = q_tokens & tokens(text)
            score = len(overlap) / max(len(q_tokens), 1)
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            SearchResult(
                title=doc["title"],
                url=doc["url"],
                snippet=doc["snippet"],
                rank=i + 1,
                provider=self.name,
            )
            for i, (_, doc) in enumerate(scored[:top_k])
        ]
