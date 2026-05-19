from __future__ import annotations

import json
import pathlib
from typing import Any

from .models import utc_now


def write_event(path: pathlib.Path, action: str, **fields: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": utc_now(), "action": action, **fields}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")


def read_events(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def latest_scheduled_ingest_summary(path: pathlib.Path) -> dict[str, Any] | None:
    current: dict[str, Any] | None = None
    attempts: list[dict[str, Any]] = []

    for event in read_events(path):
        action = str(event.get("action") or "")
        if action == "wayfinder_scheduled_ingest_blocked":
            attempts.append(
                {
                    "status": "blocked",
                    "started_at": str(event.get("ts") or ""),
                    "finished_at": str(event.get("ts") or ""),
                    "schedule": "",
                    "enabled": False,
                    "reason": str(event.get("reason") or "cron_disabled"),
                    "approved_sources": 0,
                    "skipped_sources": 0,
                    "failed_sources": 0,
                    "source_outcomes": [],
                }
            )
            current = None
            continue
        if action == "wayfinder_scheduled_ingest_started":
            current = {
                "status": "started",
                "started_at": str(event.get("ts") or ""),
                "finished_at": "",
                "schedule": str(event.get("schedule") or ""),
                "enabled": bool(event.get("enabled", False)),
                "reason": "",
                "approved_sources": 0,
                "skipped_sources": 0,
                "failed_sources": 0,
                "source_outcomes": [],
            }
            continue
        if current is None:
            continue
        if action == "wayfinder_scheduled_ingest_skipped":
            current["source_outcomes"].append(
                {
                    "source": str(event.get("source") or ""),
                    "status": "skipped",
                    "reason": str(event.get("reason") or ""),
                    "policy_status": str(event.get("status") or ""),
                    "inserted_signals": 0,
                    "inserted_products": 0,
                    "inserted_opportunities": 0,
                    "normalized": 0,
                    "raw_records": 0,
                }
            )
            continue
        if action == "wayfinder_scheduled_ingest_source":
            current["source_outcomes"].append(
                {
                    "source": str(event.get("source") or ""),
                    "status": "ok",
                    "reason": "",
                    "policy_status": "enabled",
                    "inserted_signals": int(event.get("inserted_signals") or 0),
                    "inserted_products": int(event.get("inserted_products") or 0),
                    "inserted_opportunities": int(event.get("inserted_opportunities") or 0),
                    "normalized": int(event.get("normalized") or 0),
                    "raw_records": int(event.get("raw_records") or 0),
                }
            )
            continue
        if action == "wayfinder_scheduled_ingest_error":
            current["source_outcomes"].append(
                {
                    "source": str(event.get("source") or ""),
                    "status": "error",
                    "reason": str(event.get("error") or ""),
                    "policy_status": "",
                    "inserted_signals": 0,
                    "inserted_products": 0,
                    "inserted_opportunities": 0,
                    "normalized": 0,
                    "raw_records": 0,
                }
            )
            continue
        if action == "wayfinder_scheduled_ingest_finished":
            current["status"] = "finished" if int(event.get("failed_sources") or 0) == 0 else "partial"
            current["finished_at"] = str(event.get("ts") or "")
            current["approved_sources"] = int(event.get("approved_sources") or 0)
            current["skipped_sources"] = int(event.get("skipped_sources") or 0)
            current["failed_sources"] = int(event.get("failed_sources") or 0)
            attempts.append(current)
            current = None

    if current is not None:
        attempts.append(current)
    return attempts[-1] if attempts else None
