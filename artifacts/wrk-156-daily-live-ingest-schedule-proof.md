# WRK-156 Daily Live-Ingest Schedule Proof

Acceptance evidence for `WRK-156`, captured from the active `project/wayfinder` branch on `2026-05-18`.

## Scope

This task documents the operator-run daily ingest path and the exact evidence QA should inspect for the live-ingest acceptance gate. It does not re-prove the separate dashboard freshness work.

## Repo truth

The verified config on this branch keeps the daily unattended path enabled without widening source scope:

```yaml
sources:
  oss-ledger:
    status: enabled
  hackernews:
    status: enabled
  github:
    status: enabled

cron:
  enabled: true
  schedule: daily
  token_free: true
```

## Operator recurrence command

Command:

```text
python3 -m wayfinder --no-color schedule-command
```

Output:

```text
@daily cd /mnt/d/AI/codex-foundry/workspace/tasks/WRK-156 && /usr/bin/python3 -m wayfinder --config /mnt/d/AI/codex-foundry/workspace/tasks/WRK-156/wayfinder.yaml --no-color scheduled-ingest >> /mnt/d/AI/codex-foundry/workspace/tasks/WRK-156/logs/wayfinder-cron.log 2>&1
```

This is the scheduler-ready command operators should wire for the current checkout.

## Live scheduled-ingest proof

Command:

```text
python3 -m wayfinder --no-color scheduled-ingest
```

Successful output from the verified live run:

```text
scheduled-ingest: sources=3 approved=3 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T21:33:56.115881+00:00
hackernews: raw=30 searchable_rows=30 inserted signals=30 products=0 opportunities=0
hackernews: searchable_rows_total=30 last_ingest_at=2026-05-18T21:33:59.178681+00:00
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T21:34:01.954522+00:00
scheduled-ingest: succeeded=3 skipped=0 failed=0 inserted_searchable_rows=67 inserted_signals=67 inserted_products=37 inserted_opportunities=37 duration_ms=5935.287 token_free=true llm_tokens=0
```

QA should treat the final line as the primary pass signal: it preserves source count, inserted-row totals, duration, `token_free=true`, and `llm_tokens=0` on the live unattended path.

## Source-health confirmation

Command:

```text
python3 -m wayfinder --no-color sources list --health
```

Relevant output from the same verification window:

```text
oss-ledger status=enabled kind=static_ledger credentials=none terms=reviewed-public-data rate_limits=none-local-file scraping=none pii_ugc=low-curated-public-metadata hosted_dependencies=none
  review=approved unattended=eligible why=Curated local ledger with explicit repository inputs and no unattended network dependency.
  latest_run=live status=ok last_ingest_at=2026-05-18T21:33:56.115881+00:00 collected=24 searchable_rows=8 signals=8 products=8 opportunities=8
hackernews status=enabled kind=hackernews credentials=none terms=public-api-allowed rate_limits=low-volume-search scraping=api-search pii_ugc=reviewed-story-metadata hosted_dependencies=algolia-hn-api
  review=approved unattended=eligible why=Approved for unattended low-volume Algolia search using the configured story-only queries; normal and scheduled ingest use the live official endpoint while fixture-backed dry runs remain available for diagnostics.
  latest_run=live status=ok last_ingest_at=2026-05-18T21:33:59.178681+00:00 collected=30 searchable_rows=30 signals=30 products=0 opportunities=0
github status=enabled kind=github credentials=none terms=public-api-allowed rate_limits=low-volume-public-search scraping=official-api pii_ugc=low-public-repo-metadata hosted_dependencies=github-public-api
  review=approved unattended=eligible why=Approved for daily anonymous public repository search at the configured low query volume; dry runs stay fixture-backed for diagnostics while scheduled and normal ingest use the live official API.
  latest_run=live status=ok last_ingest_at=2026-05-18T21:34:01.954522+00:00 collected=87 searchable_rows=29 signals=29 products=29 opportunities=29
```

## Stats confirmation

Command:

```text
python3 -m wayfinder --no-color stats
```

Output:

```text
signals: 67
products: 37
opportunities: 37
ingest_runs: 3
source_activity:
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T21:34:01.954522+00:00 health=ok
  hackernews: signals=30 opportunities=0 last_ingest_at=2026-05-18T21:33:59.178681+00:00 health=ok
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T21:33:56.115881+00:00 health=ok
```

This is supporting evidence only. The acceptance gate remains the operator schedule command plus the live scheduled-ingest and audit evidence above.

## Audit trail

Tail from `logs/wayfinder-audit.log` immediately after the same successful run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 3, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T21:33:56.087998+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 35.354, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T21:33:56.124989+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 3048.902, "inserted_opportunities": 0, "inserted_products": 0, "inserted_searchable_rows": 30, "inserted_signals": 30, "llm_tokens": 0, "normalized": 30, "raw_records": 30, "source": "hackernews", "token_free": true, "ts": "2026-05-18T21:33:59.192582+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2772.283, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T21:34:01.987886+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 3, "approved_sources": 3, "duration_ms": 5935.287, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 67, "inserted_signals": 67, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 0, "source_count": 3, "token_free": true, "ts": "2026-05-18T21:34:02.025911+00:00"}
```

## Acceptance mapping

- Operators have an exact scheduler-ready recurrence command for the current checkout.
- The documented live path uses `scheduled-ingest` directly, not `--dry-run` and not `--allow-disabled`.
- QA can verify source counts, inserted rows, duration, `token_free=true`, and `llm_tokens=0` from stdout and the audit log.
- The current real source posture remains intact: `oss-ledger`, `hackernews`, and `github` are the only approved unattended sources, and this task does not weaken source safety.
