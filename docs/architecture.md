# Architecture and design decisions

## Data flow

```text
user query
    |
    v
SearchProvider.search(query, top_k)          # swappable: local corpus | Foundry Bing Grounding
    |
    v
fetch_and_extract(result, query_id, ...)     # page fetch + HTML strip; provenance captured here
    |                                        #   provider, rank, retrieval_query, retrieved_at,
    |                                        #   extraction_method, content_origin (+ fetch_error)
    v
assess: lexical_relevance(query, content)    # 0..1; grounded = score >= 0.5
    |                                        # llm_score_hook() overrides when an LLM is configured
    v
EvidenceStore.save_evidence(ev)              # SQLite; UNIQUE(query_id, url) dedupes re-runs
    |
    v
evaluate(rows, latencies)                    # precision@k, grounded rate, provenance coverage,
    |                                        # per-stage latency
    v
reports/evaluation_report_*.md               # reviewer-readable markdown, committed as evidence
```

## Design decisions

**Why provenance is a first-class column, not a log line.** In enterprise deployments the first question about any AI answer is "where did that come from?". Here every evidence row answers it directly: which provider, which rank, which query, retrieved when, extracted how, and from what origin (live web vs demo corpus). Provenance coverage is measured per run — a silent provenance gap becomes a visible metric instead of a support ticket.

**Why the search provider is an interface.** The classic Bing Search API was retired on 11 Aug 2025; Microsoft's supported path for Bing-grounded agents is the "Grounding with Bing" tool inside Azure AI Foundry Agent Service, which requires a Foundry project, a connection and an agent model. That setup has real prerequisites. The provider interface means the pipeline ships and runs today (local corpus), and the live provider slots in without touching orchestration, storage or evaluation. Honest stubs beat fake live calls.

**Why scoring starts with lexical overlap.** It is explainable, free and instant — the baseline every heavier method must beat. The evaluation harness is already in place, so replacing it with embeddings or an LLM judge becomes a measured decision, not a vibe. Cost and latency per LLM call are planned as first-class report columns for the same reason.

**Why SQLite now, PostgreSQL later.** Zero-config storage keeps the demo runnable anywhere and the CI honest. The schema is deliberately simple (two tables, one index, a UNIQUE constraint that does deduping) so the PostgreSQL migration is an infrastructure step, not a redesign.

**Why the answers are extractive first.** The dashboard's Grounded Answers tab returns sentences retrieved and cited directly from the evidence store — nothing generated. It demonstrates the grounded-answer contract (every claim cites a source) before any generative model enters the loop, which is exactly how grounded RAG systems should be built and evaluated.

## Roadmap mapping (to a typical enterprise stack)

| This repo | Enterprise equivalent |
|---|---|
| `FoundryGroundingProvider` (stub) | Azure AI Foundry Agent Service + Grounding with Bing |
| `llm_score_hook` (stub) | Azure OpenAI / Claude rubric-based judge, cost+latency logged |
| SQLite store | PostgreSQL / Databricks ingestion for analytics |
| Streamlit Grounded Answers | Copilot Studio agent over the same evidence store |
| GitHub Actions CI | Full DevOps pipeline (lint, test, containerize, deploy) |
