from __future__ import annotations

import argparse
import json
import shlex
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

from . import __version__
from .adapters import build_adapter
from .adapters.github import GitHubCollectError
from .adapters.hackernews import HackerNewsCollectError
from .audit import latest_scheduled_ingest_summary, write_event
from .config import audit_log_path, load_config, source_configs, source_policy, source_review_summary, storage_path
from .drafts import format_task_draft
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
    source_activity,
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


def source_evidence_mode(cfg: dict[str, Any], activity: dict[str, Any] | None = None) -> str:
    kind = str(cfg.get("kind") or "").strip().lower()
    if kind == "static_ledger":
        return "static-ledger"
    run = activity or {}
    if run.get("last_ingest_at") and not run.get("last_run_dry_run"):
        return "real-source"
    status = str(cfg.get("status") or "").strip().lower()
    if status == "enabled":
        return "real-source"
    if cfg.get("fixture_path"):
        return "fixture-backed"
    return "real-source"


def runtime_source_config(cfg: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    if dry_run or "fixture_path" not in cfg:
        return cfg
    kind = str(cfg.get("kind") or "").strip().lower()
    if kind not in {"github", "hackernews"}:
        return cfg
    live_cfg = dict(cfg)
    live_cfg.pop("fixture_path", None)
    return live_cfg


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


def score_trace_summary(row: sqlite3.Row, key: str, aliases: dict[str, str] | None = None) -> str:
    try:
        score_data = json.loads(row["score_components_json"] or "{}")
    except json.JSONDecodeError:
        score_data = {}
    section = score_data.get(key) if isinstance(score_data, dict) else {}
    if not isinstance(section, dict):
        return ""
    ordered = ("pain", "freshness", "recurrence", "source_quality", "build_fit")
    names = aliases or {item: item for item in ordered}
    return " ".join(f"{names[item]}={section.get(item, 0)}" for item in ordered)


def print_opportunities(rows: list[sqlite3.Row], no_color: bool = False) -> None:
    if not rows:
        print(color("No rows found.", DIM, not no_color))
        return
    for index, row in enumerate(rows, start=1):
        heading = f"{row['title']} | score={row['opportunity_score']} | {row['target_user']}"
        print(color(f"{index}. {heading}", BOLD + CYAN, not no_color))
        print(f"   {color('components:', DIM, not no_color)} {score_summary(row)}")
        inputs = score_trace_summary(row, "inputs")
        if inputs:
            print(f"   {color('inputs:', DIM, not no_color)} {inputs}")
        weights = score_trace_summary(
            row,
            "weights",
            aliases={"pain": "pain", "freshness": "freshness", "recurrence": "recurrence", "source_quality": "source", "build_fit": "fit"},
        )
        if weights:
            print(f"   {color('weights:', DIM, not no_color)} {weights}")
        try:
            score_data = json.loads(row["score_components_json"] or "{}")
        except json.JSONDecodeError:
            score_data = {}
        reference_time = score_data.get("reference_time") if isinstance(score_data, dict) else ""
        if reference_time:
            print(f"   {color('reference_time:', DIM, not no_color)} {reference_time}")
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
    conn = connect(storage_path(config)) if args.health else None
    try:
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
            if args.health:
                if policy.status == "disabled":
                    print(
                        "  health="
                        f"{color('disabled', RED, not args.no_color)} "
                        "Health checks are skipped while this adapter is disabled."
                    )
                else:
                    try:
                        ok, message = build_adapter(name, cfg).healthcheck()
                        state = color("ok", GREEN, not args.no_color) if ok else color("fail", RED, not args.no_color)
                        print(f"  health={state} {message}")
                    except Exception as exc:  # noqa: BLE001
                        print(f"  health={color('fail', RED, not args.no_color)} {exc}")
                activity = source_activity(conn, name) if conn is not None else {}
                if activity:
                    last_ingest_at = str(activity.get("last_ingest_at") or "never")
                    last_status = str(activity.get("last_run_status") or "unknown")
                    if activity.get("last_ingest_at"):
                        run_label = "dry-run" if activity.get("last_run_dry_run") else "live"
                    else:
                        run_label = "none"
                    print(
                        "  latest_run="
                        f"{run_label} status={last_status} last_ingest_at={last_ingest_at} "
                        f"collected={int(activity.get('last_run_collected') or 0)} "
                        f"searchable_rows={int(activity.get('last_run_inserted_searchable_rows') or 0)} "
                        f"signals={int(activity.get('last_run_inserted_signals') or 0)} "
                        f"products={int(activity.get('last_run_inserted_products') or 0)} "
                        f"opportunities={int(activity.get('last_run_inserted_opportunities') or 0)}"
                    )
                    print(
                        "  totals="
                        f"signals={int(activity.get('signal_count') or 0)} "
                        f"opportunities={int(activity.get('opportunity_count') or 0)} "
                        f"latest_signal_at={activity.get('latest_signal_at') or 'never'}"
                    )
    finally:
        if conn is not None:
            conn.close()
    return 0


def ingest_source(
    name: str,
    cfg: dict[str, Any],
    args: argparse.Namespace,
    config: dict[str, Any],
    audit_action: str | None = None,
) -> tuple[dict[str, int], str]:
    started = utc_now()
    started_monotonic = time.perf_counter()
    adapter = build_adapter(name, runtime_source_config(cfg, dry_run=bool(args.dry_run)))
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
        return {
            "raw_records": len(raw),
            "normalized": collected,
            "inserted_searchable_rows": 0,
            "inserted_signals": 0,
            "inserted_products": 0,
            "inserted_opportunities": 0,
        }, (
            f"{name}: dry-run queries={query_count} collected={len(raw)} normalized={collected} "
            f"signals={normalized_signals} products={normalized_products} "
            f"opportunities={normalized_opportunities}"
        )

    conn = connect(storage_path(config))
    try:
        inserted_signals = insert_signals(conn, batch.signals)
        inserted_searchable_rows = inserted_signals
        inserted_products = insert_products(conn, batch.products)
        inserted_opportunities = insert_opportunities(conn, batch.opportunities, scoring_weights(config))
        conn.execute(
            """
            INSERT INTO ingest_runs (
              source, started_at, finished_at, collected, inserted_searchable_rows, inserted_signals,
              inserted_products, inserted_opportunities, dry_run, status, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                started,
                utc_now(),
                collected,
                inserted_searchable_rows,
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
        inserted_searchable_rows=inserted_searchable_rows,
        inserted_signals=inserted_signals,
        inserted_products=inserted_products,
        inserted_opportunities=inserted_opportunities,
        duration_ms=round((time.perf_counter() - started_monotonic) * 1000, 3),
        token_free=True,
        llm_tokens=0,
    )
    return {
        "raw_records": len(raw),
        "normalized": collected,
        "inserted_searchable_rows": inserted_searchable_rows,
        "inserted_signals": inserted_signals,
        "inserted_products": inserted_products,
        "inserted_opportunities": inserted_opportunities,
    }, (
        f"{name}: raw={len(raw)} searchable_rows={inserted_searchable_rows} inserted signals={inserted_signals} "
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
    inserted_searchable_rows = 0
    inserted_signals = 0
    inserted_products = 0
    inserted_opportunities = 0

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
    print(
        color(
            "scheduled-ingest: "
            f"sources={len(all_sources)} approved={len(approved)} token_free=true llm_tokens=0",
            CYAN,
            not args.no_color,
        )
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
            source_counts, message = ingest_source(name, cfg, args, config, audit_action="wayfinder_scheduled_ingest_source")
            print(color(message, GREEN, not args.no_color))
            inserted_searchable_rows += source_counts["inserted_searchable_rows"]
            inserted_signals += source_counts["inserted_signals"]
            inserted_products += source_counts["inserted_products"]
            inserted_opportunities += source_counts["inserted_opportunities"]
            conn = connect(storage_path(config))
            try:
                activity = source_activity(conn, name)
            finally:
                conn.close()
            print(
                color(
                    f"{name}: searchable_rows_total={int(activity['signal_count'])} "
                    f"last_ingest_at={activity['last_ingest_at'] or 'unknown'}",
                    DIM,
                    not args.no_color,
                )
            )
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

    duration_ms = round((time.perf_counter() - started_monotonic) * 1000, 3)
    write_event(
        audit_log_path(config),
        "wayfinder_scheduled_ingest_finished",
        enabled=bool(cron_cfg.get("enabled", False)),
        schedule=str(cron_cfg.get("schedule") or "daily"),
        source_count=len(all_sources),
        approved_source_count=len(approved),
        approved_sources=succeeded,
        skipped_sources=skipped,
        failed_sources=failed,
        inserted_searchable_rows=inserted_searchable_rows,
        inserted_signals=inserted_signals,
        inserted_products=inserted_products,
        inserted_opportunities=inserted_opportunities,
        duration_ms=duration_ms,
        token_free=True,
        llm_tokens=0,
    )
    print(
        color(
            "scheduled-ingest: "
            f"succeeded={succeeded} skipped={skipped} failed={failed} "
            f"inserted_searchable_rows={inserted_searchable_rows} "
            f"inserted_signals={inserted_signals} inserted_products={inserted_products} "
            f"inserted_opportunities={inserted_opportunities} "
            f"duration_ms={duration_ms} "
            f"token_free=true llm_tokens=0",
            CYAN if not failed else YELLOW,
            not args.no_color,
        )
    )
    return 1 if failed else 0


def cmd_schedule_command(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    config_path = Path(args.config).resolve() if args.config else Path.cwd() / "wayfinder.yaml"
    config_path = config_path.resolve()
    repo_root = config_path.parent
    audit_path = audit_log_path(config)
    cron_log_path = audit_path.parent / "wayfinder-cron.log"
    schedule = str((config.get("cron") or {}).get("schedule") or "daily").strip() or "daily"
    schedule_prefix = {
        "hourly": "@hourly",
        "daily": "@daily",
        "weekly": "@weekly",
        "monthly": "@monthly",
    }.get(schedule.lower(), schedule)
    runner = (
        f"cd {shlex.quote(str(repo_root))} && "
        f"{shlex.quote(sys.executable)} -m wayfinder --config {shlex.quote(str(config_path))} "
        "--no-color scheduled-ingest"
    )
    print(f"{schedule_prefix} {runner} >> {shlex.quote(str(cron_log_path))} 2>&1")
    return 0


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
        sources = source_configs(config)
        activity_by_source = {name: source_activity(conn, name) for name in sorted(sources)}
        searchable_updated_at = max(
            (str(activity.get("latest_signal_at") or "") for activity in activity_by_source.values()),
            default="",
        )
        scheduled = latest_scheduled_ingest_summary(audit_log_path(config))
        source_rows = []
        real_source_signal_count = 0
        for name, cfg in sorted(sources.items()):
            kind = str(cfg.get("kind") or name)
            activity = activity_by_source[name]
            evidence_mode = source_evidence_mode(cfg, activity)
            source_rows.append(
                {
                    "source": name,
                    "kind": kind,
                    "evidence_mode": evidence_mode,
                    "signal_count": int(activity.get("signal_count", 0)),
                    "opportunity_count": int(activity.get("opportunity_count", 0)),
                    "last_signal_at": str(activity.get("latest_signal_at") or ""),
                    "last_ingest_at": str(activity.get("last_ingest_at") or ""),
                    "latest_ingest_status": str(activity.get("health_status") or "unknown"),
                }
            )
            if evidence_mode == "real-source":
                real_source_signal_count += int(activity.get("signal_count", 0))
        if args.json:
            print(
                json.dumps(
                    {
                        **data,
                        "searchable_data_last_updated": searchable_updated_at,
                        "real_source_signal_count": real_source_signal_count,
                        "scheduled_ingest": scheduled,
                        "sources": source_rows,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            for key, value in data.items():
                print(f"{color(key + ':', BOLD, not args.no_color)} {value}")
            print(f"{color('searchable_data_last_updated:', BOLD, not args.no_color)} {searchable_updated_at or 'none'}")
            if scheduled is None:
                print(f"{color('scheduled_ingest:', BOLD, not args.no_color)} no audit history")
            else:
                finished_at = scheduled.get("finished_at") or scheduled.get("started_at") or "unknown"
                print(
                    f"{color('scheduled_ingest:', BOLD, not args.no_color)} "
                    f"status={scheduled.get('status', 'unknown')} finished_at={finished_at} "
                    f"approved={scheduled.get('approved_sources', 0)} skipped={scheduled.get('skipped_sources', 0)} "
                    f"failed={scheduled.get('failed_sources', 0)}"
                )
                for item in scheduled.get("source_outcomes", []):
                    print(
                        "  "
                        f"{item['source']}: status={item['status']} signals+{item['inserted_signals']} "
                        f"products+{item['inserted_products']} opportunities+{item['inserted_opportunities']}"
                    )
            print(f"{color('real_source_signal_count:', BOLD, not args.no_color)} {real_source_signal_count}")
            for item in source_rows:
                print(
                    "  "
                    f"{item['source']} mode={item['evidence_mode']} signals={item['signal_count']} "
                    f"opportunities={item['opportunity_count']} last_signal={item['last_signal_at'] or 'none'} "
                    f"last_ingest={item['last_ingest_at'] or 'none'}"
                )
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

    schedule_command = subparsers.add_parser(
        "schedule-command",
        help="Print the scheduler command for the approved daily ingest path",
    )
    leaf_options(schedule_command)
    schedule_command.set_defaults(func=cmd_schedule_command)

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
