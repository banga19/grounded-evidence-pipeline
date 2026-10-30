"""Run with:  pytest -q   OR   python tests/test_storage.py"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evidence.models import Evidence
from src.storage.database import EvidenceStore

RUN_AT = "2026-10-31T00:00:00+00:00"


def _sample_evidence(url="https://corpus.example.com/a", query_id="q_test"):
    return Evidence(
        query_id=query_id,
        query_text="test query",
        provider="local_corpus",
        provider_rank=1,
        url=url,
        title="A",
        snippet="snippet text",
        content_chars=12,
        relevance_score=0.75,
        grounded=True,
        provenance={
            "provider": "local_corpus",
            "provider_rank": 1,
            "retrieval_query": "test query",
            "retrieved_at": RUN_AT,
            "extraction_method": "corpus_offline",
            "content_origin": "local_demo_corpus",
        },
    )


def test_save_and_fetch():
    with tempfile.TemporaryDirectory() as tmp:
        store = EvidenceStore(os.path.join(tmp, "t.db"))
        store.save_query("q_test", "test query", "local_corpus", 5, RUN_AT)
        assert store.save_evidence(_sample_evidence()) is True
        rows = store.evidence_for_query("q_test")
        assert len(rows) == 1
        assert rows[0]["relevance_score"] == 0.75
        assert rows[0]["grounded"] == 1
        assert rows[0]["provenance_json"]  # provenance persisted alongside the row


def test_dedupe_on_same_query_and_url():
    with tempfile.TemporaryDirectory() as tmp:
        store = EvidenceStore(os.path.join(tmp, "t.db"))
        store.save_query("q_test", "test query", "local_corpus", 5, RUN_AT)
        assert store.save_evidence(_sample_evidence()) is True
        assert store.save_evidence(_sample_evidence()) is False  # second insert deduped
        assert store.counts() == {"queries": 1, "evidence": 1}


def test_same_url_across_queries_is_kept():
    with tempfile.TemporaryDirectory() as tmp:
        store = EvidenceStore(os.path.join(tmp, "t.db"))
        store.save_query("q_1", "first query", "local_corpus", 5, RUN_AT)
        store.save_query("q_2", "second query", "local_corpus", 5, RUN_AT)
        store.save_evidence(_sample_evidence(query_id="q_1"))
        store.save_evidence(_sample_evidence(query_id="q_2"))
        assert store.counts() == {"queries": 2, "evidence": 2}


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
