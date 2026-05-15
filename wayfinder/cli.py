from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from typing import Any

from . import __version__
from .adapters import build_adapter
from .adapters.github import GitHubCollectError
from .adapters.hackernews import HackerNewsCollectError
from .audit import write_event
from .config import audit_log_path, load_config, source_configs, source_policy, source_review_summary, storage_path
from .db import (
    connect,
    counts,
    filtered_opportunities,
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


def runnable_sources(config: dict[str, Any], dry_run: bool = False) -> dict[str, dict[str, Any]]:
    allowed_statuses = {"enabled", "dry-run-only"} if dry_run else {"enabled"}
    return {
        name: cfg
        for name, cfg in source_configs(config).items()
        if source_policy(cfg).status in allowed_statuses
    }


def approved_scheduled_sources(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return runnable_sources(config, dry_run=False)


def score_summary(row: sqlite3.Row) -> str:
    try:
        score_data = json.loads(row["score_components_json"] or "{}")
    except json.JSONDecodeError:
        score_data = {}
    components = score_data.get("components") if isinstance(score_data, dict) else {}
    if not isinstance(components, dict):
        return ""
    ordered = ("pain", "freshness", "recurrence", "source_quality", "build_fit")
    aliases = {
        "pain": "pain",
        "freshness": "freshness",
        "recurrence": "recurrence",
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


def draft_title(row: sqlite3.Row) -> str:
    category = str(row["category"] or "").replace("-", " ").strip()
    if category:
        return f"{row['title']} for {category}"
    return str(row["title"])


def draft_goal(row: sqlite3.Row) -> str:
    parts = [str(row["problem"] or "").strip(), str(row["iteration_angle"] or "").strip()]
    return " ".join(part for part in parts if part) or f"Review {row['title']} and decide whether it merits a follow-on Foundry task."


def draft_acceptance_criteria(row: sqlite3.Row) -> list[str]:
    criteria = [
        f"Review the opportunity context for `{row['title']}` and capture the concrete reuse angle for `{row['target_user'] or 'the operator'}`.",
        f"Use the existing evidence, competition, and user-want signals to decide whether this should become a follow-on Foundry task.",
    ]
    if row["foundry_task_suggestions"]:
        criteria.append(f"Translate the existing suggestion into an operator-ready next step: {row['foundry_task_suggestions']}.")
    else:
        criteria.append("Produce a specific next step that can be reviewed by Hermes or pasted into Linear without further rewriting.")
    return criteria


def draft_validation(row: sqlite3.Row) -> list[str]:
    return [
        f"Confirm the draft references the source opportunity score (`{row['opportunity_score']}`) and the relevant evidence fields.",
        "Confirm the draft is specific enough for Hermes review or direct paste into Linear.",
    ]


def draft_scope_boundaries(row: sqlite3.Row) -> list[str]:
    boundaries = [
        "Do not auto-stage follow-on tasks.",
        "Do not call LLMs.",
        "Do not create Linear issues directly from this command.",
    ]
    if row["source"]:
        boundaries.append(f"Do not broaden this draft beyond the `{row['source']}` source material without explicit operator review.")
    return boundaries


def draft_delivery_expectation() -> list[str]:
    return [
        "Keep the output Markdown-only and operator-editable.",
        "Hand the draft to Hermes for review or paste it into Linear manually when ready.",
    ]


def format_task_draft(row: sqlite3.Row, index: int) -> str:
    metadata = [
        f"source={row['source'] or 'unknown'}",
        f"category={row['category'] or 'uncategorized'}",
        f"score={row['opportunity_score']}",
    ]
    lines = [
        f"## Task Draft {index}: {draft_title(row)}",
        "",
        f"Metadata: {' | '.join(metadata)}",
        "",
        "### Goal",
        draft_goal(row),
        "",
        "### Acceptance Criteria",
    ]
    lines.extend(f"- {item}" for item in draft_acceptance_criteria(row))
    lines.extend(
        [
            "",
            "### Validation",
        ]
    )
    lines.extend(f"- {item}" for item in draft_validation(row))
    lines.extend(
        [
            "",
            "### Scope Boundaries",
        ]
    )
    lines.extend(f"- {item}" for item in draft_scope_boundaries(row))
    lines.extend(
        [
            "",
            "### Delivery Expectation",
        ]
    )
    lines.extend(f"- {item}" for item in draft_delivery_expectation())
    return "\n".join(lines)


def cmd_sources(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    sources = source_configs(config)
    if args.json:
        print(json.dumps(sources, indent=2, sort_keys=True))
        return 0
    for name, cfg in sources.items():
        policy = source_policy(cfg)
        status_color = {
            "enabled": GREEN,
            "dry-run-only": YELLOW,
            "needs-review": YELLOW,
            "disabled": RED,
        }.get(policy.status, YELLOW)
        status = color(policy.status, status_color, not args.no_color)
        kind = str(cfg.get("kind") or name)
        risk = policy.risk
        print(
            f"{color(name, BOLD, not args.no_color)} status={status} kind={kind} "
            f"credentials={risk.credentials} terms={risk.terms} rate_limits={risk.rate_limits} "
            f"scraping={risk.scraping} pii_ugc={risk.pii_user_generated_content} "
            f"hosted_dependencies={risk.hosted_dependencies}"
        )
        review_state, unattended_state, review_reason = source_review_summary(policy)
        print(f"  review={review_state} unattended={unattended_state} why={review_reason}")
        if policy.notes:
            print(f"  notes={policy.notes}")
        if args.health and policy.status != "disabled":
            try:
                ok, message = build_adapter(name, cfg).healthcheck()
                state = color("ok", GREEN, not args.no_color) if ok else color("fail", RED, not args.no_color)
                print(f"  health={state} {message}")
            except Exception as exc:  # noqa: BLE001
                print(f"  health={color('fail', RED, not args.no_color)} {exc}")
    return 0


def ingest_source(
    name: str,
    cfg: dict[str, Any],
    args: argparse.Namespace,
    config: dict[str, Any],
    audit_action: str | None = None,
) -> tuple[int, str]:
    started = utc_now()
    started_monotonic = time.perf_counter()
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
            audit_action or "wayfinder_ingest_dry_run",
            source=name,
            raw_records=len(raw),
            normalized=collected,
            normalized_signals=normalized_signals,
            normalized_products=normalized_products,
            normalized_opportunities=normalized_opportunities,
            duration_ms=round((time.perf_counter() - started_monotonic) * 1000, 3),
            token_free=True,
            llm_tokens=0,
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
        audit_action or "wayfinder_ingest",
        source=name,
        raw_records=len(raw),
        normalized=collected,
        inserted_signals=inserted_signals,
        inserted_products=inserted_products,
        inserted_opportunities=inserted_opportunities,
        duration_ms=round((time.perf_counter() - started_monotonic) * 1000, 3),
        token_free=True,
        llm_tokens=0,
    )
    return inserted_signals + inserted_products + inserted_opportunities, (
        f"{name}: raw={len(raw)} inserted signals={inserted_signals} "
        f"products={inserted_products} opportunities={inserted_opportunities}"
    )


def cmd_ingest(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    sources = runnable_sources(config, dry_run=args.dry_run)
    all_sources = source_configs(config)
    selected = list(sources) if args.all else [args.source or "oss-ledger"]
    rc = 0
    for name in selected:
        cfg = sources.get(name)
        if cfg is None:
            configured = all_sources.get(name)
            if configured is None:
                message = f"Unknown source: {name}"
            else:
                status = source_policy(configured).status
                if status == "dry-run-only" and not args.dry_run:
                    message = f"Source requires --dry-run before ingest: {name}"
                else:
                    message = f"Source not runnable for this ingest mode: {name} status={status}"
            print(color(message, RED, not args.no_color), file=sys.stderr)
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


def cmd_scheduled_ingest(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    cron_cfg = config.get("cron") if isinstance(config.get("cron"), dict) else {}
    if not bool(cron_cfg.get("enabled", False)) and not args.allow_disabled:
        message = "Scheduled ingest is disabled in config; rerun with --allow-disabled for manual validation."
        write_event(
            audit_log_path(config),
            "wayfinder_scheduled_ingest_blocked",
            reason="cron_disabled",
            token_free=True,
            llm_tokens=0,
        )
        print(color(message, RED, not args.no_color), file=sys.stderr)
        return 1

    started_monotonic = time.perf_counter()
    all_sources = source_configs(config)
    approved = approved_scheduled_sources(config)
    skipped = 0
    succeeded = 0
    failed = 0

    write_event(
        audit_log_path(config),
        "wayfinder_scheduled_ingest_started",
        enabled=bool(cron_cfg.get("enabled", False)),
        schedule=str(cron_cfg.get("schedule") or "daily"),
        source_count=len(all_sources),
        approved_source_count=len(approved),
        token_free=True,
        llm_tokens=0,
    )

    for name, cfg in all_sources.items():
        if name not in approved:
            status = source_policy(cfg).status
            write_event(
                audit_log_path(config),
                "wayfinder_scheduled_ingest_skipped",
                source=name,
                status=status,
                reason="source_not_approved_for_unattended_ingest",
                token_free=True,
                llm_tokens=0,
            )
            print(color(f"{name}: skipped status={status}", YELLOW, not args.no_color))
            skipped += 1
            continue
        try:
            _, message = ingest_source(name, cfg, args, config, audit_action="wayfinder_scheduled_ingest_source")
            print(color(message, GREEN, not args.no_color))
            succeeded += 1
        except HackerNewsCollectError as exc:
            write_event(
                audit_log_path(config),
                "wayfinder_scheduled_ingest_error",
                source=name,
                error=str(exc),
                duration_ms=round((time.perf_counter() - started_monotonic) * 1000, 3),
                token_free=True,
                llm_tokens=0,
            )
            print(color(f"{name}: network failure: {exc}", RED, not args.no_color), file=sys.stderr)
            failed += 1
        except GitHubCollectError as exc:
            write_event(
                audit_log_path(config),
                "wayfinder_scheduled_ingest_error",
                source=name,
                error=str(exc),
                duration_ms=round((time.perf_counter() - started_monotonic) * 1000, 3),
                token_free=True,
                llm_tokens=0,
            )
            print(color(f"{name}: GitHub ingest failed: {exc}", RED, not args.no_color), file=sys.stderr)
            failed += 1
        except Exception as exc:  # noqa: BLE001
            write_event(
                audit_log_path(config),
                "wayfinder_scheduled_ingest_error",
                source=name,
                error=str(exc),
                duration_ms=round((time.perf_counter() - started_monotonic) * 1000, 3),
                token_free=True,
                llm_tokens=0,
            )
            print(color(f"{name}: failed: {exc}", RED, not args.no_color), file=sys.stderr)
            failed += 1

    write_event(
        audit_log_path(config),
        "wayfinder_scheduled_ingest_finished",
        enabled=bool(cron_cfg.get("enabled", False)),
        schedule=str(cron_cfg.get("schedule") or "daily"),
        approved_sources=succeeded,
        skipped_sources=skipped,
        failed_sources=failed,
        duration_ms=round((time.perf_counter() - started_monotonic) * 1000, 3),
        token_free=True,
        llm_tokens=0,
    )
    return 1 if failed else 0


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


def cmd_export(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    conn = connect(storage_path(config))
    try:
        rows = filtered_opportunities(
            conn,
            limit=args.limit,
            min_score=args.min_score,
            category=args.category,
            source=args.source,
        )
        if not rows:
            return 0
        print("\n\n---\n\n".join(format_task_draft(row, index) for index, row in enumerate(rows, start=1)))
    finally:
        conn.close()
    return 0


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

    scheduled = subparsers.add_parser(
        "scheduled-ingest",
        help="Run the daily unattended ingest for approved sources only",
    )
    leaf_options(scheduled)
    scheduled.add_argument(
        "--allow-disabled",
        action="store_true",
        help="Run manually even when cron.enabled is false in config",
    )
    scheduled.set_defaults(func=cmd_scheduled_ingest, dry_run=False)

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

    export = subparsers.add_parser("export", help="Generate Foundry-ready Markdown task drafts")
    leaf_options(export)
    export.add_argument("--limit", type=int, default=10)
    export.add_argument("--min-score", type=float, default=None, help="Only export opportunities at or above this score")
    export.add_argument("--category", default="", help="Only export opportunities in this category")
    export.add_argument("--source", default="", help="Only export opportunities from this source")
    export.set_defaults(func=cmd_export)

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
