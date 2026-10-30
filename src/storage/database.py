"""SQLite storage for queries and evidence (zero-config; upgrade path: PostgreSQL).

Schema notes:
- UNIQUE (query_id, url) means re-runs dedupe instead of duplicating rows.
- provenance_json keeps the full retrieval/extraction provenance dict;
  flatten selected keys into columns later when analytics need them.
- relevance_score is stored at write time so the assess layer stays
  swappable without changing stored-history semantics.
"""

import json
import pathlib
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS queries (
    query_id    TEXT PRIMARY KEY,
    query_text  TEXT NOT NULL,
    run_at      TEXT NOT NULL,
    provider    TEXT NOT NULL,
    top_k       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id     TEXT PRIMARY KEY,
    query_id        TEXT NOT NULL REFERENCES queries(query_id),
    url             TEXT NOT NULL,
    title           TEXT,
    snippet         TEXT,
    content_chars   INTEGER,
    relevance_score REAL,
    grounded        INTEGER,
    extracted_at    TEXT,
    provider        TEXT,
    provenance_json TEXT,
    UNIQUE (query_id, url)
);

CREATE INDEX IF NOT EXISTS idx_evidence_query ON evidence(query_id);
"""


class EvidenceStore:
    def __init__(self, db_path: str = "data/evidence.db"):
        pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def save_query(self, query_id: str, query_text: str, provider: str, top_k: int, run_at: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO queries VALUES (?, ?, ?, ?, ?)",
            (query_id, query_text, run_at, provider, top_k),
        )
        self.conn.commit()

    def save_evidence(self, ev) -> bool:
        """Insert one Evidence; returns False if deduped by (query_id, url)."""
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ev.as_row(),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def evidence_for_query(self, query_id: str) -> list:
        rows = self.conn.execute(
            "SELECT * FROM evidence WHERE query_id = ? ORDER BY relevance_score DESC",
            (query_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def counts(self) -> dict:
        q = self.conn.execute("SELECT COUNT(*) AS n FROM queries").fetchone()["n"]
        e = self.conn.execute("SELECT COUNT(*) AS n FROM evidence").fetchone()["n"]
        return {"queries": q, "evidence": e}
