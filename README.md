# Grounded Evidence Pipeline

Web-search grounded evidence retrieval with **full provenance** — search, extract, score, store, evaluate. Built to demonstrate exactly the shape of work enterprise AI teams ask for: grounded answers, traceable sources, measured quality.

**Status:** working prototype, runs end-to-end offline (no API keys). Live provider stubs included for [Azure AI Foundry "Grounding with Bing"](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/bing-grounding).

![CI](https://github.com/banga19/grounded-evidence-pipeline/actions/workflows/ci.yml/badge.svg)

## Why this exists

Enterprise AI deployments fail for boring reasons: nobody can trace where a fact came from, nobody measured whether retrieval actually worked, and the demo only worked on the author's laptop. This project takes the opposite stance:

- **Provenance-first** — every stored record carries who retrieved it, when, from where, and how it was extracted.
- **Evaluation-first** — every run emits precision@k, grounded rate, provenance coverage and per-stage latency. Quality is reported, not claimed.
- **Swappable providers** — the demo runs on a local corpus today; switching to Azure AI Foundry Bing Grounding later changes zero pipeline code.

## Architecture

```text
query
  |
  v
+---------------------+     +----------------------+     +---------------------+
| src/search/         | --> | src/evidence/        | --> | src/assess/         |
| SearchProvider      |     | fetch + strip HTML   |     | relevance score +   |
| local corpus (now), |     | + capture provenance |     | groundedness flag   |
| Foundry grounding   |     +----------------------+     +---------------------+
| (stub, later)       |                                          |
+---------------------+                                          v
                    +----------------------+     +---------------------+
                    | src/evaluate/        | <-- | src/storage/        |
                    | precision@k, proven- |     | SQLite (UNIQUE      |
                    | ance coverage,       |     | query_id + url      |
                    | stage latency        |     | dedupe)             |
                    +----------------------+     +---------------------+
                              |
                              v
              reports/evaluation_report_*.md  +  dashboard/app.py (Streamlit)
```

See [docs/architecture.md](docs/architecture.md) for design decisions and the roadmap.

## Quickstart (60 seconds, zero API keys)

```bash
git clone https://github.com/banga19/grounded-evidence-pipeline.git
cd grounded-evidence-pipeline
pip install -r requirements.txt

python -m src.pipeline --query "How does Kenya regulate AI and personal data?"
```

Output from the current build:

```text
Pipeline run q_4f7ea16e93 via local_corpus
  evidence collected : 5 of top_k=5
  precision@k        : 0.2
  grounded rate      : 0.2
  provenance coverage: 1.0
  total latency      : 0.0008s
  report             : reports/evaluation_report_kenya_ai.md
```

Yes, precision@k is low — that is the honest number for a naive lexical baseline on a mixed two-topic corpus, and it is reported instead of hidden. The improvement path (better tokenization, embeddings, LLM-as-judge) is on the roadmap below, and the evaluation harness already exists to prove whether each step helps.

Try the dashboard:

```bash
pip install -r requirements-dashboard.txt
streamlit run dashboard/app.py
```

The **Grounded Answers** tab returns extractive answers with numbered citations — the no-LLM baseline for grounded question answering.

## What is implemented

| Layer | Module | State |
|---|---|---|
| Search providers | `src/search/` | Local corpus (works), Foundry Bing Grounding (documented stub) |
| Evidence + provenance | `src/evidence/` | Working: fetch, HTML strip, provenance capture, snippet fallback on failure |
| Assessment | `src/assess/` | Working: lexical relevance, groundedness, LLM-judge hook (stub) |
| Storage | `src/storage/` | Working: SQLite, dedupe via UNIQUE(query_id, url), provenance persisted |
| Evaluation | `src/evaluate/` | Working: precision@k, grounded rate, provenance coverage, stage latency |
| Orchestration + report | `src/pipeline.py` | Working: CLI, markdown evaluation report |
| UI | `dashboard/app.py` | Working: pipeline explorer + cited answers (Streamlit) |
| CI | `.github/workflows/ci.yml` | Runs demo + tests on every push |

## Tests

```bash
pytest -q          # or: python tests/test_scorer.py && python tests/test_storage.py
```

9 tests cover scoring math, sentence splitting, storage dedupe and provenance persistence.

## Roadmap

- [ ] Wire `FoundryGroundingProvider` to a real Azure AI Foundry project (`azure-ai-projects` SDK, Bing Grounding tool)
- [ ] LLM-as-judge scoring via the `llm_score_hook`, with per-call token + latency logging (cost column in the report)
- [ ] Swap SQLite for PostgreSQL (schema is intentionally simple)
- [ ] Embedding-based retrieval next to the lexical baseline, measured by the same harness
- [ ] Copilot Studio front-end over the evidence store (agent with repo README + docs as knowledge)

## License

MIT — see [LICENSE](LICENSE).
