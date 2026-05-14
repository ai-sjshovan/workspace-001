from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
from typing import Iterable

from .models import Opportunity, ProductIntel, Signal


SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_url TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL DEFAULT '',
  author TEXT NOT NULL DEFAULT '',
  score REAL NOT NULL DEFAULT 0,
  product TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT '',
  pain_type TEXT NOT NULL DEFAULT '',
  feature_request TEXT NOT NULL DEFAULT '',
  monetization_signal TEXT NOT NULL DEFAULT '',
  collected_at TEXT NOT NULL,
  fingerprint TEXT NOT NULL UNIQUE,
  raw_json TEXT NOT NULL DEFAULT '{}'
);

CREATE VIRTUAL TABLE IF NOT EXISTS signals_fts
USING fts5(title, body, source_url, fingerprint UNINDEXED);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_name TEXT NOT NULL,
  url TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT '',
  pricing_model TEXT NOT NULL DEFAULT '',
  strengths TEXT NOT NULL DEFAULT '',
  complaints TEXT NOT NULL DEFAULT '',
  feature_gaps TEXT NOT NULL DEFAULT '',
  audience TEXT NOT NULL DEFAULT '',
  monetization_notes TEXT NOT NULL DEFAULT '',
  collected_at TEXT NOT NULL,
  fingerprint TEXT NOT NULL UNIQUE,
  raw_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS opportunities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  target_user TEXT NOT NULL DEFAULT '',
  problem TEXT NOT NULL DEFAULT '',
  evidence_count INTEGER NOT NULL DEFAULT 0,
  competing_products TEXT NOT NULL DEFAULT '',
  what_products_do_right TEXT NOT NULL DEFAULT '',
  what_users_want_better TEXT NOT NULL DEFAULT '',
  build_difficulty TEXT NOT NULL DEFAULT '',
  replication_time_estimate TEXT NOT NULL DEFAULT '',
  iteration_angle TEXT NOT NULL DEFAULT '',
  monetization_strategy TEXT NOT NULL DEFAULT '',
  foundry_task_suggestions TEXT NOT NULL DEFAULT '',
  collected_at TEXT NOT NULL,
  fingerprint TEXT NOT NULL UNIQUE,
  raw_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS ingest_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL,
  collected INTEGER NOT NULL DEFAULT 0,
  inserted_signals INTEGER NOT NULL DEFAULT 0,
  inserted_products INTEGER NOT NULL DEFAULT 0,
  inserted_opportunities INTEGER NOT NULL DEFAULT 0,
  dry_run INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  message TEXT NOT NULL DEFAULT ''
);
"""


def connect(path: pathlib.Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def stable_fingerprint(*parts: str) -> str:
    joined = "\x1f".join(part.strip() for part in parts if part is not None)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def signal_fingerprint(signal: Signal) -> str:
    return stable_fingerprint(signal.source, signal.source_id, signal.source_url, signal.title)


def product_fingerprint(product: ProductIntel) -> str:
    return stable_fingerprint(product.product_name, product.url, product.category)


def opportunity_fingerprint(opportunity: Opportunity) -> str:
    return stable_fingerprint(opportunity.title, opportunity.target_user, opportunity.problem)


def insert_signals(conn: sqlite3.Connection, signals: Iterable[Signal]) -> int:
    inserted = 0
    for signal in signals:
        fingerprint = signal_fingerprint(signal)
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO signals (
              source, source_id, source_url, title, body, author, score, product, category,
              pain_type, feature_request, monetization_signal, collected_at, fingerprint, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal.source,
                signal.source_id,
                signal.source_url,
                signal.title,
                signal.body,
                signal.author,
                signal.score,
                signal.product,
                signal.category,
                signal.pain_type,
                signal.feature_request,
                signal.monetization_signal,
                signal.collected_at,
                fingerprint,
                json.dumps(signal.raw, sort_keys=True, default=str),
            ),
        )
        if cur.rowcount:
            conn.execute(
                "INSERT INTO signals_fts(title, body, source_url, fingerprint) VALUES (?, ?, ?, ?)",
                (signal.title, signal.body, signal.source_url, fingerprint),
            )
            inserted += 1
    return inserted


def insert_products(conn: sqlite3.Connection, products: Iterable[ProductIntel]) -> int:
    inserted = 0
    for product in products:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO products (
              product_name, url, category, pricing_model, strengths, complaints,
              feature_gaps, audience, monetization_notes, collected_at, fingerprint, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product.product_name,
                product.url,
                product.category,
                product.pricing_model,
                product.strengths,
                product.complaints,
                product.feature_gaps,
                product.audience,
                product.monetization_notes,
                product.collected_at,
                product_fingerprint(product),
                json.dumps(product.raw, sort_keys=True, default=str),
            ),
        )
        inserted += int(bool(cur.rowcount))
    return inserted


def insert_opportunities(conn: sqlite3.Connection, opportunities: Iterable[Opportunity]) -> int:
    inserted = 0
    for opportunity in opportunities:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO opportunities (
              title, target_user, problem, evidence_count, competing_products,
              what_products_do_right, what_users_want_better, build_difficulty,
              replication_time_estimate, iteration_angle, monetization_strategy,
              foundry_task_suggestions, collected_at, fingerprint, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity.title,
                opportunity.target_user,
                opportunity.problem,
                opportunity.evidence_count,
                opportunity.competing_products,
                opportunity.what_products_do_right,
                opportunity.what_users_want_better,
                opportunity.build_difficulty,
                opportunity.replication_time_estimate,
                opportunity.iteration_angle,
                opportunity.monetization_strategy,
                opportunity.foundry_task_suggestions,
                opportunity.collected_at,
                opportunity_fingerprint(opportunity),
                json.dumps(opportunity.raw, sort_keys=True, default=str),
            ),
        )
        inserted += int(bool(cur.rowcount))
    return inserted


def search_signals(conn: sqlite3.Connection, query: str, limit: int = 20) -> list[sqlite3.Row]:
    if not query.strip():
        return conn.execute(
            "SELECT * FROM signals ORDER BY collected_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    try:
        return conn.execute(
            """
            SELECT signals.*
            FROM signals_fts
            JOIN signals ON signals.fingerprint = signals_fts.fingerprint
            WHERE signals_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        like = f"%{query}%"
        return conn.execute(
            """
            SELECT *
            FROM signals
            WHERE title LIKE ? OR body LIKE ? OR source_url LIKE ? OR product LIKE ? OR category LIKE ?
            ORDER BY collected_at DESC, id DESC
            LIMIT ?
            """,
            (like, like, like, like, like, limit),
        ).fetchall()


def list_rows(conn: sqlite3.Connection, table: str, limit: int = 50) -> list[sqlite3.Row]:
    if table not in {"signals", "products", "opportunities", "ingest_runs"}:
        raise ValueError(f"Unsupported table: {table}")
    return conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)).fetchall()


def counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        name: int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
        for name in ("signals", "products", "opportunities", "ingest_runs")
    }
