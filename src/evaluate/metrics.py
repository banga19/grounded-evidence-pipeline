"""Evaluation harness: every run reports quality, provenance coverage and latency.

Metrics (simple but real - the point is the habit, not the sophistication):

- precision_at_k      : share of retrieved evidence scoring at/above threshold
- grounded_rate       : share of evidence flagged grounded
- provenance_coverage : share of records with every provenance field filled
- latency_seconds     : wall-clock per pipeline stage (search / extract_score / store)
- dedupe handling     : UNIQUE (query_id, url) in the store prevents duplicates
"""

import json
import pathlib

from ..evidence.models import utcnow

REQUIRED_PROVENANCE_FIELDS = (
    "provider",
    "provider_rank",
    "retrieval_query",
    "retrieved_at",
    "extraction_method",
    "content_origin",
)


def _get(row, name):
    """Row can be a dict (from the store) or an Evidence dataclass."""
    return row[name] if isinstance(row, dict) else getattr(row, name)


def _provenance(row) -> dict:
    p = _get(row, "provenance") if "provenance" in _row_keys(row) else None
    if p is None:
        p = _get(row, "provenance_json") if "provenance_json" in _row_keys(row) else {}
    if isinstance(p, str):
        p = json.loads(p) if p else {}
    return p or {}


def _row_keys(row) -> set:
    return row.keys() if isinstance(row, dict) else set(vars(row))


def _safe_div(a: float, b: float) -> float:
    return round(a / b, 3) if b else 0.0


def evaluate(rows: list, latencies: dict, top_k: int, threshold: float = 0.5) -> dict:
    n = len(rows)
    relevant = sum(1 for r in rows if _get(r, "relevance_score") >= threshold)
    grounded = sum(1 for r in rows if _get(r, "grounded"))
    prov_complete = sum(
        1
        for r in rows
        if all(field in _provenance(r) for field in REQUIRED_PROVENANCE_FIELDS)
    )
    return {
        "n_evidence": n,
        "top_k": top_k,
        "relevance_threshold": threshold,
        "precision_at_k": _safe_div(relevant, n),
        "grounded_rate": _safe_div(grounded, n),
        "provenance_coverage": _safe_div(prov_complete, n),
        "latency_seconds": {k: round(v, 4) for k, v in latencies.items()},
        "total_latency_seconds": round(sum(latencies.values()), 4),
        # TODO(banga19): add cost estimate once the LLM scorer is wired in
        # (tokens per call x price, plus search API cost per query).
    }


def write_report(path: str, query_text: str, provider: str, metrics: dict, rows: list) -> str:
    """Write a markdown evaluation report a reviewer can read in 60 seconds."""
    lines = [
        "# Evaluation report",
        "",
        f"- Query: **{query_text}**",
        f"- Provider: `{provider}`",
        f"- Generated: {utcnow()}",
        "",
        "## Run metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    for key, value in metrics.items():
        if key != "latency_seconds":
            lines.append(f"| {key} | {value} |")
    for key, value in metrics["latency_seconds"].items():
        lines.append(f"| latency_{key} (s) | {value} |")

    lines += ["", "## Evidence (by relevance)", "", "| rank | score | grounded | url |", "|---|---|---|---|"]
    ranked = sorted(rows, key=lambda r: _get(r, "relevance_score"), reverse=True)
    for i, r in enumerate(ranked, 1):
        lines.append(
            f"| {i} | {_get(r, 'relevance_score')} "
            f"| {'yes' if _get(r, 'grounded') else 'no'} | {_get(r, 'url')} |"
        )

    lines += [
        "",
        "## How to read this",
        "",
        "- **precision_at_k** - share of retrieved evidence at or above the relevance threshold.",
        "- **grounded_rate** - share of evidence the assessor flagged as sufficiently grounded.",
        "- **provenance_coverage** - share of records carrying complete provenance (who/when/how).",
        "- Latency is wall-clock per pipeline stage. A cost column follows once the LLM scorer is wired in.",
        "",
    ]
    out = pathlib.Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)
