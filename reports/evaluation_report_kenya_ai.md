# Evaluation report

- Query: **How does Kenya regulate AI and personal data?**
- Provider: `local_corpus`
- Generated: 2026-10-30T21:11:48+00:00

## Run metrics

| Metric | Value |
|---|---|
| n_evidence | 5 |
| top_k | 5 |
| relevance_threshold | 0.5 |
| precision_at_k | 0.2 |
| grounded_rate | 0.2 |
| provenance_coverage | 1.0 |
| total_latency_seconds | 0.0008 |
| latency_search (s) | 0.0002 |
| latency_extract_score (s) | 0.0002 |
| latency_store (s) | 0.0004 |

## Evidence (by relevance)

| rank | score | grounded | url |
|---|---|---|---|
| 1 | 0.714 | yes | https://corpus.example.com/kenya/dpa-2019 |
| 2 | 0.429 | no | https://corpus.example.com/ecommerce/payments-regulation |
| 3 | 0.429 | no | https://corpus.example.com/kenya/infrastructure |
| 4 | 0.286 | no | https://corpus.example.com/ecommerce/social-commerce |
| 5 | 0.286 | no | https://corpus.example.com/kenya/digital-masterplan |

## How to read this

- **precision_at_k** - share of retrieved evidence at or above the relevance threshold.
- **grounded_rate** - share of evidence the assessor flagged as sufficiently grounded.
- **provenance_coverage** - share of records carrying complete provenance (who/when/how).
- Latency is wall-clock per pipeline stage. A cost column follows once the LLM scorer is wired in.
