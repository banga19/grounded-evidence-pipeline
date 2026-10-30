"""End-to-end orchestrator: query -> search -> extract -> score -> store -> report.

Usage (demo mode, no API keys needed):
    python -m src.pipeline --query "How does Kenya regulate AI and personal data?"

Options:
    --top-k 5                results per run
    --db data/evidence.db    SQLite path
    --report path.md         markdown evaluation report output
"""

import argparse
import time
import uuid

from .assess.scorer import llm_score_hook, lexical_relevance
from .evidence.extractor import fetch_and_extract
from .evidence.models import utcnow
from .evaluate.metrics import evaluate, write_report
from .search.local_corpus_provider import LocalCorpusProvider
from .storage.database import EvidenceStore

GROUNDING_THRESHOLD = 0.5


def run_pipeline(
    query: str,
    top_k: int = 5,
    provider=None,
    db_path: str = "data/evidence.db",
    report_path: str = "reports/evaluation_report.md",
) -> dict:
    provider = provider or LocalCorpusProvider()
    query_id = f"q_{uuid.uuid4().hex[:10]}"

    latencies = {}

    t0 = time.perf_counter()
    results = provider.search(query, top_k=top_k)
    latencies["search"] = time.perf_counter() - t0

    store = EvidenceStore(db_path)
    store.save_query(query_id, query, provider.name, top_k, run_at=utcnow())

    latencies["extract_score"] = 0.0
    latencies["store"] = 0.0
    for res in results:
        t1 = time.perf_counter()
        ev = fetch_and_extract(res, query_id, query)
        ev.relevance_score = lexical_relevance(query, ev.content or ev.snippet, ev.snippet)
        llm_score = llm_score_hook(ev)
        if llm_score is not None:  # LLM judge overrides the lexical baseline
            ev.relevance_score = llm_score
        ev.grounded = ev.relevance_score >= GROUNDING_THRESHOLD
        latencies["extract_score"] += time.perf_counter() - t1

        t2 = time.perf_counter()
        store.save_evidence(ev)
        latencies["store"] += time.perf_counter() - t2

    rows = store.evidence_for_query(query_id)
    metrics = evaluate(rows, latencies, top_k, GROUNDING_THRESHOLD)
    if report_path:
        write_report(report_path, query, provider.name, metrics, rows)

    return {
        "query_id": query_id,
        "provider": provider.name,
        "metrics": metrics,
        "evidence": rows,
        "report_path": report_path,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Grounded evidence pipeline (demo mode needs no API keys)."
    )
    parser.add_argument("--query", required=True, help="natural-language query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--db", default="data/evidence.db")
    parser.add_argument("--report", default="reports/evaluation_report.md")
    args = parser.parse_args()

    result = run_pipeline(args.query, args.top_k, db_path=args.db, report_path=args.report)
    m = result["metrics"]
    print(f"\nPipeline run {result['query_id']} via {result['provider']}")
    print(f"  evidence collected : {m['n_evidence']} of top_k={m['top_k']}")
    print(f"  precision@k        : {m['precision_at_k']}")
    print(f"  grounded rate      : {m['grounded_rate']}")
    print(f"  provenance coverage: {m['provenance_coverage']}")
    print(f"  total latency      : {m['total_latency_seconds']}s")
    print(f"  report             : {result['report_path']}")

    print("\nTop evidence:")
    for i, row in enumerate(
        sorted(result["evidence"], key=lambda r: r["relevance_score"], reverse=True), 1
    ):
        print(f"  {i}. [{row['relevance_score']:.2f}] {row['title']}")
        print(f"     {row['url']}")


if __name__ == "__main__":
    main()
