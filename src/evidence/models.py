"""Evidence data model.

Design principle: provenance-first. Every record answers who retrieved it,
when, from where, how it was extracted and how it scored. An enterprise
reviewer should be able to trace any stored fact back to its source.
"""

import datetime
import json
import uuid
from dataclasses import dataclass, field


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


@dataclass
class Evidence:
    """One retrieved, scored piece of evidence with full provenance."""

    query_id: str
    query_text: str
    provider: str
    provider_rank: int
    url: str
    title: str
    snippet: str
    content: str = ""  # extracted page text (not persisted; used for scoring)
    content_chars: int = 0
    relevance_score: float = 0.0
    grounded: bool = False
    evidence_id: str = field(default_factory=lambda: new_id("ev"))
    extracted_at: str = field(default_factory=utcnow)
    provenance: dict = field(default_factory=dict)

    def as_row(self) -> tuple:
        """Tuple matching the evidence table column order."""
        return (
            self.evidence_id,
            self.query_id,
            self.url,
            self.title,
            self.snippet,
            self.content_chars,
            self.relevance_score,
            int(self.grounded),
            self.extracted_at,
            self.provider,
            json.dumps(self.provenance),
        )
