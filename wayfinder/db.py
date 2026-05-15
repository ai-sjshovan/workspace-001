from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
from typing import Iterable

from .models import Opportunity, ProductIntel, Signal, opportunity_from_row_data, parse_timestamp, score_opportunity, utc_now


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
  source TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT '',
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
  opportunity_score REAL NOT NULL DEFAULT 0,
  score_components_json TEXT NOT NULL DEFAULT '{}',
  scored_at TEXT NOT NULL DEFAULT '',
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
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(opportunities)").fetchall()}
    for name, definition in (
        ("source", "TEXT NOT NULL DEFAULT ''"),
        ("category", "TEXT NOT NULL DEFAULT ''"),
        ("opportunity_score", "REAL NOT NULL DEFAULT 0"),
        ("score_components_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("scored_at", "TEXT NOT NULL DEFAULT ''"),
    ):
        if name not in columns:
            conn.execute(f"ALTER TABLE opportunities ADD COLUMN {name} {definition}")
    conn.commit()


def stable_fingerprint(*parts: str) -> str:
    joined = "\x1f".join(part.strip() for part in parts if part is not None)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def signal_fingerprint(signal: Signal) -> str:
    if signal.source_id:
        return stable_fingerprint(signal.source, signal.source_id)
    return stable_fingerprint(signal.source, signal.source_url, signal.title)


def product_fingerprint(product: ProductIntel) -> str:
    raw_fingerprint = str(product.raw.get("_wayfinder_product_fingerprint") or "").strip()
    if raw_fingerprint:
        return stable_fingerprint(raw_fingerprint)
    return stable_fingerprint(product.product_name, product.url, product.category)


def opportunity_fingerprint(opportunity: Opportunity) -> str:
    raw_fingerprint = str(opportunity.raw.get("_wayfinder_opportunity_fingerprint") or "").strip()
    if raw_fingerprint:
        return stable_fingerprint(raw_fingerprint)
    return stable_fingerprint(opportunity.title, opportunity.target_user, opportunity.problem)


def _scoring_reference_time(opportunities: Iterable[Opportunity]):
    timestamps = []
    for opportunity in opportunities:
        try:
            timestamps.append(parse_timestamp(opportunity.collected_at))
        except ValueError:
            continue
    return max(timestamps) if timestamps else None


def _rescore_opportunity_rows(
    conn: sqlite3.Connection,
    rows: list[sqlite3.Row],
    weights: dict[str, float],
) -> int:
    opportunities: list[tuple[sqlite3.Row, Opportunity]] = []
    for row in rows:
        raw = json.loads(row["raw_json"] or "{}")
        opportunity = opportunity_from_row_data(dict(row), raw if isinstance(raw, dict) else {})
        opportunities.append((row, opportunity))

    reference_time = _scoring_reference_time(opportunity for _, opportunity in opportunities)
    updated = 0
    for row, opportunity in opportunities:
        score_data = score_opportunity(opportunity, weights, reference_time=reference_time)
        conn.execute(
            """
            UPDATE opportunities
            SET opportunity_score = ?, score_components_json = ?, scored_at = ?
            WHERE id = ?
            """,
            (score_data["score"], json.dumps(score_data, sort_keys=True), utc_now(), row["id"]),
        )
        updated += 1
    return updated


def insert_signals(conn: sqlite3.Connection, signals: Iterable[Signal]) -> int:
    inserted = 0
    for signal in signals:
        fingerprint = signal_fingerprint(signal)
        exists = conn.execute("SELECT 1 FROM signals WHERE fingerprint = ?", (fingerprint,)).fetchone() is not None
        conn.execute(
            """
            INSERT INTO signals (
              source, source_id, source_url, title, body, author, score, product, category,
              pain_type, feature_request, monetization_signal, collected_at, fingerprint, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
              source = excluded.source,
              source_id = excluded.source_id,
              source_url = excluded.source_url,
              title = excluded.title,
              body = excluded.body,
              author = excluded.author,
              score = excluded.score,
              product = excluded.product,
              category = excluded.category,
              pain_type = excluded.pain_type,
              feature_request = excluded.feature_request,
              monetization_signal = excluded.monetization_signal,
              collected_at = excluded.collected_at,
              raw_json = excluded.raw_json
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
        conn.execute("DELETE FROM signals_fts WHERE fingerprint = ?", (fingerprint,))
        conn.execute(
            "INSERT INTO signals_fts(title, body, source_url, fingerprint) VALUES (?, ?, ?, ?)",
            (signal.title, signal.body, signal.source_url, fingerprint),
        )
        inserted += int(not exists)
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


def insert_opportunities(conn: sqlite3.Connection, opportunities: Iterable[Opportunity], weights: dict[str, float]) -> int:
    inserted = 0
    buffered = list(opportunities)
    reference_time = _scoring_reference_time(buffered)
    for opportunity in buffered:
        fingerprint = opportunity_fingerprint(opportunity)
        score_data = score_opportunity(opportunity, weights, reference_time=reference_time)
        exists = conn.execute("SELECT 1 FROM opportunities WHERE fingerprint = ?", (fingerprint,)).fetchone() is not None
        cur = conn.execute(
            """
            INSERT INTO opportunities (
              title, source, category, target_user, problem, evidence_count, competing_products,
              what_products_do_right, what_users_want_better, build_difficulty,
              replication_time_estimate, iteration_angle, monetization_strategy,
              foundry_task_suggestions, opportunity_score, score_components_json,
              scored_at, collected_at, fingerprint, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
              title = excluded.title,
              source = excluded.source,
              category = excluded.category,
              target_user = excluded.target_user,
              problem = excluded.problem,
              evidence_count = excluded.evidence_count,
              competing_products = excluded.competing_products,
              what_products_do_right = excluded.what_products_do_right,
              what_users_want_better = excluded.what_users_want_better,
              build_difficulty = excluded.build_difficulty,
              replication_time_estimate = excluded.replication_time_estimate,
              iteration_angle = excluded.iteration_angle,
              monetization_strategy = excluded.monetization_strategy,
              foundry_task_suggestions = excluded.foundry_task_suggestions,
              opportunity_score = excluded.opportunity_score,
              score_components_json = excluded.score_components_json,
              scored_at = excluded.scored_at,
              collected_at = excluded.collected_at,
              raw_json = excluded.raw_json
            """,
            (
                opportunity.title,
                opportunity.source,
                opportunity.category,
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
                score_data["score"],
                json.dumps(score_data, sort_keys=True),
                utc_now(),
                opportunity.collected_at,
                fingerprint,
                json.dumps(opportunity.raw, sort_keys=True, default=str),
            ),
        )
        inserted += int(bool(cur.rowcount) and not exists)
    rows = conn.execute("SELECT * FROM opportunities").fetchall()
    _rescore_opportunity_rows(conn, rows, weights)
    return inserted


def ranked_opportunities(conn: sqlite3.Connection, limit: int = 50) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM opportunities
        ORDER BY opportunity_score DESC, evidence_count DESC, collected_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def filtered_opportunities(
    conn: sqlite3.Connection,
    *,
    limit: int = 50,
    min_score: float | None = None,
    category: str = "",
    source: str = "",
) -> list[sqlite3.Row]:
    clauses: list[str] = []
    params: list[object] = []

    if min_score is not None:
        clauses.append("opportunity_score >= ?")
        params.append(min_score)
    if category.strip():
        clauses.append("category = ?")
        params.append(category.strip())
    if source.strip():
        clauses.append("source = ?")
        params.append(source.strip())

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return conn.execute(
        f"""
        SELECT *
        FROM opportunities
        {where}
        ORDER BY opportunity_score DESC, evidence_count DESC, collected_at DESC, id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()


def opportunity_score_filter_values(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT MAX(opportunity_score) AS max_score
        FROM opportunities
        """
    ).fetchone()
    max_score = float(rows["max_score"] or 0) if rows else 0.0
    presets = [40, 55, 70, 85]
    return [str(value) for value in presets if max_score >= value]


def rescore_opportunities(conn: sqlite3.Connection, weights: dict[str, float]) -> int:
    rows = conn.execute("SELECT * FROM opportunities").fetchall()
    updated = _rescore_opportunity_rows(conn, rows, weights)
    conn.commit()
    return updated


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


def browse_signals(
    conn: sqlite3.Connection,
    query: str = "",
    source: str = "",
    category: str = "",
    product: str = "",
    pain_type: str = "",
    feature_request: str = "",
    limit: int = 50,
) -> list[sqlite3.Row]:
    clauses: list[str] = []
    params: list[object] = []

    if source.strip():
        clauses.append("source = ?")
        params.append(source.strip())
    if category.strip():
        clauses.append("category = ?")
        params.append(category.strip())
    if product.strip():
        clauses.append("product = ?")
        params.append(product.strip())
    if pain_type.strip():
        clauses.append("pain_type = ?")
        params.append(pain_type.strip())
    if feature_request.strip():
        clauses.append("feature_request = ?")
        params.append(feature_request.strip())
    if query.strip():
        like = f"%{query}%"
        clauses.append(
            "("
            "title LIKE ? OR body LIKE ? OR source_url LIKE ? OR product LIKE ? OR category LIKE ? "
            "OR pain_type LIKE ? OR feature_request LIKE ?"
            ")"
        )
        params.extend([like, like, like, like, like, like, like])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return conn.execute(
        f"""
        SELECT *
        FROM signals
        {where}
        ORDER BY score DESC, collected_at DESC, id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()


def signal_filter_values(conn: sqlite3.Connection) -> dict[str, list[str]]:
    return {
        "sources": [
            row[0]
            for row in conn.execute("SELECT DISTINCT source FROM signals WHERE source != '' ORDER BY source COLLATE NOCASE")
        ],
        "products": [
            row[0]
            for row in conn.execute("SELECT DISTINCT product FROM signals WHERE product != '' ORDER BY product COLLATE NOCASE")
        ],
        "categories": [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT category FROM signals WHERE category != '' ORDER BY category COLLATE NOCASE"
            )
        ],
        "pain_types": [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT pain_type FROM signals WHERE pain_type != '' ORDER BY pain_type COLLATE NOCASE"
            )
        ],
        "feature_requests": [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT feature_request FROM signals WHERE feature_request != '' ORDER BY feature_request COLLATE NOCASE"
            )
        ],
    }


def product_filter_values(conn: sqlite3.Connection) -> dict[str, list[str]]:
    return {
        "categories": [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT category FROM products WHERE category != '' ORDER BY category COLLATE NOCASE"
            )
        ]
    }


def opportunity_filter_values(conn: sqlite3.Connection) -> dict[str, list[str]]:
    return {
        "sources": [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT source FROM opportunities WHERE source != '' ORDER BY source COLLATE NOCASE"
            )
        ],
        "categories": [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT category FROM opportunities WHERE category != '' ORDER BY category COLLATE NOCASE"
            )
        ],
        "min_scores": opportunity_score_filter_values(conn),
    }


def source_detail(conn: sqlite3.Connection, source: str) -> dict[str, object] | None:
    selected = source.strip()
    if not selected:
        return None

    signal_summary = conn.execute(
        """
        SELECT COUNT(*) AS signal_count, COALESCE(ROUND(AVG(score), 1), 0) AS avg_score, MAX(collected_at) AS latest_signal_at
        FROM signals
        WHERE source = ?
        """,
        (selected,),
    ).fetchone()
    if signal_summary is None or not signal_summary["signal_count"]:
        return None

    opportunity_summary = conn.execute(
        """
        SELECT COUNT(*) AS opportunity_count, COALESCE(MAX(opportunity_score), 0) AS top_opportunity_score
        FROM opportunities
        WHERE source = ?
        """,
        (selected,),
    ).fetchone()
    categories = conn.execute(
        """
        SELECT category, COUNT(*) AS total
        FROM signals
        WHERE source = ? AND category != ''
        GROUP BY category
        ORDER BY total DESC, category COLLATE NOCASE
        LIMIT 5
        """,
        (selected,),
    ).fetchall()
    signals = conn.execute(
        """
        SELECT title, category, score, source_url, collected_at
        FROM signals
        WHERE source = ?
        ORDER BY score DESC, collected_at DESC, id DESC
        LIMIT 5
        """,
        (selected,),
    ).fetchall()
    opportunities = conn.execute(
        """
        SELECT title, category, target_user, opportunity_score, evidence_count
        FROM opportunities
        WHERE source = ?
        ORDER BY opportunity_score DESC, evidence_count DESC, collected_at DESC, id DESC
        LIMIT 3
        """,
        (selected,),
    ).fetchall()
    recent_runs = conn.execute(
        """
        SELECT started_at, finished_at, status, collected, inserted_signals, inserted_products,
               inserted_opportunities, dry_run, message
        FROM ingest_runs
        WHERE source = ?
        ORDER BY finished_at DESC, id DESC
        LIMIT 5
        """,
        (selected,),
    ).fetchall()
    latest_run = recent_runs[0] if recent_runs else None
    return {
        "source": selected,
        "signal_count": int(signal_summary["signal_count"]),
        "avg_score": signal_summary["avg_score"],
        "latest_signal_at": signal_summary["latest_signal_at"] or "",
        "opportunity_count": int(opportunity_summary["opportunity_count"]) if opportunity_summary else 0,
        "top_opportunity_score": opportunity_summary["top_opportunity_score"] if opportunity_summary else 0,
        "categories": [dict(row) for row in categories],
        "signals": [dict(row) for row in signals],
        "opportunities": [dict(row) for row in opportunities],
        "health_status": str(latest_run["status"]) if latest_run else "unknown",
        "last_ingest_at": str(latest_run["finished_at"]) if latest_run else "",
        "recent_runs": [dict(row) for row in recent_runs],
    }


def source_activity(conn: sqlite3.Connection, source: str) -> dict[str, object]:
    selected = source.strip()
    signal_summary = conn.execute(
        """
        SELECT COUNT(*) AS signal_count, COALESCE(ROUND(AVG(score), 1), 0) AS avg_score, MAX(collected_at) AS latest_signal_at
        FROM signals
        WHERE source = ?
        """,
        (selected,),
    ).fetchone()
    opportunity_summary = conn.execute(
        """
        SELECT COUNT(*) AS opportunity_count, COALESCE(MAX(opportunity_score), 0) AS top_opportunity_score
        FROM opportunities
        WHERE source = ?
        """,
        (selected,),
    ).fetchone()
    categories = conn.execute(
        """
        SELECT category, COUNT(*) AS total
        FROM signals
        WHERE source = ? AND category != ''
        GROUP BY category
        ORDER BY total DESC, category COLLATE NOCASE
        LIMIT 5
        """,
        (selected,),
    ).fetchall()
    signals = conn.execute(
        """
        SELECT title, category, score, source_url, collected_at
        FROM signals
        WHERE source = ?
        ORDER BY collected_at DESC, score DESC, id DESC
        LIMIT 5
        """,
        (selected,),
    ).fetchall()
    opportunities = conn.execute(
        """
        SELECT title, category, target_user, opportunity_score, evidence_count
        FROM opportunities
        WHERE source = ?
        ORDER BY opportunity_score DESC, evidence_count DESC, collected_at DESC, id DESC
        LIMIT 5
        """,
        (selected,),
    ).fetchall()
    recent_runs = conn.execute(
        """
        SELECT started_at, finished_at, status, collected, inserted_signals, inserted_products,
               inserted_opportunities, dry_run, message
        FROM ingest_runs
        WHERE source = ?
        ORDER BY finished_at DESC, id DESC
        LIMIT 5
        """,
        (selected,),
    ).fetchall()
    latest_run = recent_runs[0] if recent_runs else None
    return {
        "source": selected,
        "signal_count": int(signal_summary["signal_count"]) if signal_summary else 0,
        "avg_score": signal_summary["avg_score"] if signal_summary else 0,
        "latest_signal_at": signal_summary["latest_signal_at"] or "" if signal_summary else "",
        "opportunity_count": int(opportunity_summary["opportunity_count"]) if opportunity_summary else 0,
        "top_opportunity_score": opportunity_summary["top_opportunity_score"] if opportunity_summary else 0,
        "categories": [dict(row) for row in categories],
        "signals": [dict(row) for row in signals],
        "opportunities": [dict(row) for row in opportunities],
        "health_status": str(latest_run["status"]) if latest_run else "unknown",
        "last_ingest_at": str(latest_run["finished_at"]) if latest_run else "",
        "recent_runs": [dict(row) for row in recent_runs],
    }


def list_rows(conn: sqlite3.Connection, table: str, limit: int = 50) -> list[sqlite3.Row]:
    if table not in {"signals", "products", "opportunities", "ingest_runs"}:
        raise ValueError(f"Unsupported table: {table}")
    if table == "opportunities":
        return ranked_opportunities(conn, limit)
    return conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)).fetchall()


def filtered_products(conn: sqlite3.Connection, *, category: str = "", limit: int = 50) -> list[sqlite3.Row]:
    clauses: list[str] = []
    params: list[object] = []

    if category.strip():
        clauses.append("category = ?")
        params.append(category.strip())

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return conn.execute(
        f"""
        SELECT *
        FROM products
        {where}
        ORDER BY id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()


def counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        name: int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
        for name in ("signals", "products", "opportunities", "ingest_runs")
    }
