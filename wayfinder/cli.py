from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from typing import Any

from . import __version__
from .adapters import build_adapter
from .adapters.github import GitHubCollectError
from .adapters.hackernews import HackerNewsCollectError
from .audit import write_event
from .config import audit_log_path, load_config, source_configs, storage_path
from .db import (
    connect,
    counts,
    insert_opportunities,
    insert_products,
    insert_signals,
    list_rows,
    ranked_opportunities,
    rescore_opportunities,
    search_signals,
)
from .models import scoring_weights, utc_now


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"


def color(value: str, code: str, enabled: bool = True) -> str:
    return f"{code}{value}{RESET}" if enabled else value


def print_rows(rows: list[sqlite3.Row], fields: list[str], no_color: bool = False) -> None:
    if not rows:
        print(color("No rows found.", DIM, not no_color))
        return
    for index, row in enumerate(rows, start=1):
        heading = " | ".join(str(row[field]) for field in fields if field in row.keys() and row[field])
        print(color(f"{index}. {heading}", BOLD + CYAN, not no_color))
        for field in ("source_url", "body", "problem", "what_users_want_better", "iteration_angle", "strengths"):
            if field in row.keys() and row[field]:
                value = str(row[field]).replace("\n", " ").strip()
                if len(value) > 220:
                    value = value[:217] + "..."
                print(f"   {color(field + ':', DIM, not no_color)} {value}")


def enabled_sources(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {name: cfg for name, cfg in source_configs(config).items() if cfg.get("enabled", True)}


def score_summary(row: sqlite3.Row) -> str:
    try:
        score_data = json.loads(row["score_components_json"] or "{}")
    except json.JSONDecodeError:
        score_data = {}
    components = score_data.get("components") if isinstance(score_data, dict) else {}
    if not isinstance(components, dict):
        return ""
    ordered = ("evidence_count", "freshness", "monetization_signal", "source_quality", "build_fit")
    aliases = {
        "evidence_count": "evidence",
        "freshness": "freshness",
        "monetization_signal": "monetization",
        "source_quality": "source",
        "build_fit": "fit",
    }
    return " ".join(f"{aliases[key]}={components.get(key, 0)}" for key in ordered)


def print_opportunities(rows: list[sqlite3.Row], no_color: bool = False) -> None:
    if not rows:
        print(color("No rows found.", DIM, not no_color))
        return
    for index, row in enumerate(rows, start=1):
        heading = f"{row['title']} | score={row['opportunity_score']} | {row['target_user']}"
        print(color(f"{index}. {heading}", BOLD + CYAN, not no_color))
        print(f"   {color('components:', DIM, not no_color)} {score_summary(row)}")
        for field in ("problem", "iteration_angle", "monetization_strategy"):
            if row[field]:
                value = str(row[field]).replace("\n", " ").strip()
                if len(value) > 220:
                    value = value[:217] + "..."
                print(f"   {color(field + ':', DIM, not no_color)} {value}")


def cmd_sources(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    sources = source_configs(config)
    if args.json:
        print(json.dumps(sources, indent=2, sort_keys=True))
        return 0
    for name, cfg in sources.items():
        enabled = bool(cfg.get("enabled", True))
        status = color("enabled", GREEN, not args.no_color) if enabled else color("disabled", YELLOW, not args.no_color)
        kind = str(cfg.get("kind") or name)
        print(f"{color(name, BOLD, not args.no_color)} {status} kind={kind}")
        if args.health and enabled:
            try:
                ok, message = build_adapter(name, cfg).healthcheck()
                state = color("ok", GREEN, not args.no_color) if ok else color("fail", RED, not args.no_color)
                print(f"  health={state} {message}")
            except Exception as exc:  # noqa: BLE001
                print(f"  health={color('fail', RED, not args.no_color)} {exc}")
    return 0


def ingest_source(name: str, cfg: dict[str, Any], args: argparse.Namespace, config: dict[str, Any]) -> tuple[int, str]:
    started = utc_now()
    adapter = build_adapter(name, cfg)
    raw = adapter.collect()
    batch = adapter.normalize(raw)
    query_count = len(cfg.get("queries", [])) if isinstance(cfg.get("queries"), list) else 0
    normalized_signals = len(batch.signals)
    normalized_products = len(batch.products)
    normalized_opportunities = len(batch.opportunities)
    collected = normalized_signals + normalized_products + normalized_opportunities
    if args.dry_run:
        write_event(
            audit_log_path(config),
            "wayfinder_ingest_dry_run",
            source=name,
            raw_records=len(raw),
            normalized=collected,
            normalized_signals=normalized_signals,
            normalized_products=normalized_products,
            normalized_opportunities=normalized_opportunities,
        )
        return 0, (
            f"{name}: dry-run queries={query_count} collected={len(raw)} normalized={collected} "
            f"signals={normalized_signals} products={normalized_products} "
            f"opportunities={normalized_opportunities}"
        )

    conn = connect(storage_path(config))
    try:
        inserted_signals = insert_signals(conn, batch.signals)
        inserted_products = insert_products(conn, batch.products)
        inserted_opportunities = insert_opportunities(conn, batch.opportunities, scoring_weights(config))
        conn.execute(
            """
            INSERT INTO ingest_runs (
              source, started_at, finished_at, collected, inserted_signals,
              inserted_products, inserted_opportunities, dry_run, status, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                started,
                utc_now(),
                collected,
                inserted_signals,
                inserted_products,
                inserted_opportunities,
                0,
                "ok",
                f"raw={len(raw)}",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    write_event(
        audit_log_path(config),
        "wayfinder_ingest",
        source=name,
        raw_records=len(raw),
        normalized=collected,
        inserted_signals=inserted_signals,
        inserted_products=inserted_products,
        inserted_opportunities=inserted_opportunities,
    )
    return inserted_signals + inserted_products + inserted_opportunities, (
        f"{name}: raw={len(raw)} inserted signals={inserted_signals} "
        f"products={inserted_products} opportunities={inserted_opportunities}"
    )


def cmd_ingest(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    sources = enabled_sources(config)
    selected = list(sources) if args.all else [args.source or "oss-ledger"]
    rc = 0
    for name in selected:
        cfg = sources.get(name)
        if cfg is None:
            print(color(f"Unknown or disabled source: {name}", RED, not args.no_color), file=sys.stderr)
            rc = 1
            continue
        try:
            _, message = ingest_source(name, cfg, args, config)
            print(color(message, GREEN, not args.no_color))
        except HackerNewsCollectError as exc:
            write_event(audit_log_path(config), "wayfinder_ingest_error", source=name, error=str(exc))
            print(color(f"{name}: network failure: {exc}", RED, not args.no_color), file=sys.stderr)
            rc = 1
        except GitHubCollectError as exc:
            write_event(audit_log_path(config), "wayfinder_ingest_error", source=name, error=str(exc))
            print(color(f"{name}: GitHub ingest failed: {exc}", RED, not args.no_color), file=sys.stderr)
            rc = 1
        except Exception as exc:  # noqa: BLE001
            write_event(audit_log_path(config), "wayfinder_ingest_error", source=name, error=str(exc))
            print(color(f"{name}: failed: {exc}", RED, not args.no_color), file=sys.stderr)
            rc = 1
    return rc


def cmd_search(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    conn = connect(storage_path(config))
    try:
        rows = search_signals(conn, args.query, args.limit)
        if args.json:
            print(json.dumps([dict(row) for row in rows], indent=2, sort_keys=True))
        else:
            print_rows(rows, ["title", "source", "category"], args.no_color)
    finally:
        conn.close()
    return 0


def cmd_list(args: argparse.Namespace, table: str, fields: list[str]) -> int:
    config = load_config(args.config)
    conn = connect(storage_path(config))
    try:
        rows = list_rows(conn, table, args.limit)
        if args.json:
            print(json.dumps([dict(row) for row in rows], indent=2, sort_keys=True))
        else:
            print_rows(rows, fields, args.no_color)
    finally:
        conn.close()
    return 0


def cmd_opportunities(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    weights = scoring_weights(config)
    conn = connect(storage_path(config))
    try:
        if args.rescore:
            updated = rescore_opportunities(conn, weights)
            if not args.json:
                print(color(f"rescored={updated}", GREEN, not args.no_color))
        rows = ranked_opportunities(conn, args.limit)
        if args.json:
            payload = []
            for row in rows:
                item = dict(row)
                try:
                    item["score_components"] = json.loads(item.pop("score_components_json", "{}"))
                except json.JSONDecodeError:
                    item["score_components"] = {}
                payload.append(item)
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print_opportunities(rows, args.no_color)
    finally:
        conn.close()
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    args.rescore = True
    return cmd_opportunities(args)


def cmd_stats(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    conn = connect(storage_path(config))
    try:
        data = counts(conn)
        if args.json:
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            for key, value in data.items():
                print(f"{color(key + ':', BOLD, not args.no_color)} {value}")
    finally:
        conn.close()
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .web import serve

    config = load_config(args.config)
    serve(config, host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wayfinder", description="Local-first SaaS/product research intelligence.")
    parser.add_argument("--config", help="Path to wayfinder.yaml")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument("--version", action="version", version=f"wayfinder {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def leaf_options(leaf: argparse.ArgumentParser) -> None:
        leaf.add_argument("--no-color", action="store_true", help=argparse.SUPPRESS)

    sources = subparsers.add_parser("sources", help="Inspect configured sources")
    sources_sub = sources.add_subparsers(dest="sources_command", required=True)
    sources_list = sources_sub.add_parser("list", help="List configured sources")
    leaf_options(sources_list)
    sources_list.add_argument("--health", action="store_true", help="Run adapter health checks")
    sources_list.add_argument("--json", action="store_true")
    sources_list.set_defaults(func=cmd_sources)

    ingest = subparsers.add_parser("ingest", help="Collect and normalize source data")
    leaf_options(ingest)
    ingest.add_argument("--source", help="Source name to ingest")
    ingest.add_argument("--all", action="store_true", help="Ingest all enabled sources")
    ingest.add_argument("--dry-run", action="store_true", help="Collect and normalize without writing the DB")
    ingest.set_defaults(func=cmd_ingest)

    search = subparsers.add_parser("search", help="Search stored signals")
    leaf_options(search)
    search.add_argument("query", nargs="?", default="", help="FTS query")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--json", action="store_true")
    search.set_defaults(func=cmd_search)

    products = subparsers.add_parser("products", help="List product intel")
    leaf_options(products)
    products.add_argument("--limit", type=int, default=20)
    products.add_argument("--json", action="store_true")
    products.set_defaults(func=lambda args: cmd_list(args, "products", ["product_name", "category"]))

    opportunities = subparsers.add_parser("opportunities", help="List opportunities")
    leaf_options(opportunities)
    opportunities.add_argument("--limit", type=int, default=20)
    opportunities.add_argument("--rescore", action="store_true", help="Recompute deterministic scores before listing")
    opportunities.add_argument("--json", action="store_true")
    opportunities.set_defaults(func=cmd_opportunities)

    score = subparsers.add_parser("score", help="Rescore and rank opportunities")
    leaf_options(score)
    score.add_argument("--limit", type=int, default=20)
    score.add_argument("--json", action="store_true")
    score.set_defaults(func=cmd_score)

    stats = subparsers.add_parser("stats", help="Show local database counts")
    leaf_options(stats)
    stats.add_argument("--json", action="store_true")
    stats.set_defaults(func=cmd_stats)

    serve_cmd = subparsers.add_parser("serve", help="Start the local dashboard")
    leaf_options(serve_cmd)
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8766)
    serve_cmd.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
