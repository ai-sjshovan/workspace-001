# WRK-137 Real Ingest Audit Evidence

Fresh acceptance proof for `WRK-137` from the live `project/wayfinder` scheduled-ingest path on `2026-05-18`.

## Source health

Command:

```text
python3 -m wayfinder sources list --health --no-color
```

Key result:

- `oss-ledger` is `enabled`, `review=approved`, `unattended=eligible`
- `github` is `enabled`, `review=approved`, `unattended=eligible`
- `hackernews` remains `dry-run-only` and is excluded from unattended ingest

## Scheduled ingest

Command:

```text
python3 -m wayfinder scheduled-ingest --no-color
```

Output:

```text
oss-ledger: raw=8 inserted signals=8 products=8 opportunities=8
hackernews: skipped status=dry-run-only
github: raw=29 inserted signals=29 products=29 opportunities=29
```

Exit code: `0`

## Stored rows

Command:

```text
python3 -m wayfinder stats --no-color
```

Observed result:

```text
signals: 37
products: 37
opportunities: 37
ingest_runs: 2
source_activity:
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T17:23:20.376401+00:00 health=ok
  hackernews: signals=0 opportunities=0 last_ingest_at=never health=unknown
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T17:23:17.451508+00:00 health=ok
```

SQLite spot checks after the same run:

```text
select source, count(*) as count from signals group by source order by source
{"count": 29, "source": "github"}
{"count": 8, "source": "oss-ledger"}

select source, collected, inserted_signals, inserted_products, inserted_opportunities, dry_run, status, message from ingest_runs order by id desc
{"collected": 87, "dry_run": 0, "inserted_opportunities": 29, "inserted_products": 29, "inserted_signals": 29, "message": "raw=29", "source": "github", "status": "ok"}
{"collected": 24, "dry_run": 0, "inserted_opportunities": 8, "inserted_products": 8, "inserted_signals": 8, "message": "raw=8", "source": "oss-ledger", "status": "ok"}
```

## Audit trail

Tail inspected from `logs/wayfinder-audit.log` after the scheduled run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 2, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T17:23:17.392125+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 66.041, "inserted_opportunities": 8, "inserted_products": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T17:23:17.460059+00:00"}
{"action": "wayfinder_scheduled_ingest_skipped", "llm_tokens": 0, "reason": "source_not_approved_for_unattended_ingest", "source": "hackernews", "status": "dry-run-only", "token_free": true, "ts": "2026-05-18T17:23:17.463827+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2931.72, "inserted_opportunities": 29, "inserted_products": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T17:23:20.398571+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_sources": 2, "duration_ms": 3010.54, "enabled": true, "failed_sources": 0, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 1, "token_free": true, "ts": "2026-05-18T17:23:20.401845+00:00"}
```

Acceptance proof from those audit rows:

- approved live sources wrote real rows into SQLite
- source-level outcome details include `raw_records`, `normalized`, and inserted row counts
- duration is present on per-source and finished audit events
- skipped-source outcome details are preserved for `hackernews`
- every scheduled-ingest audit event records `token_free=true`
- every scheduled-ingest audit event records `llm_tokens=0`
