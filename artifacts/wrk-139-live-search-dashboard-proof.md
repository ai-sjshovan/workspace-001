# WRK-139 Live Search And Dashboard Proof

Acceptance evidence for `WRK-139` captured from the live `project/wayfinder` scheduled-ingest path on `2026-05-18`.

## Source health

Command:

```text
python3 -m wayfinder sources list --health --no-color
```

Key result:

- `oss-ledger` is `enabled`, `review=approved`, `unattended=eligible`
- `github` is `enabled`, `review=approved`, `unattended=eligible`
- `hackernews` remains `dry-run-only` and is skipped from unattended ingest

## Pre-run baseline

Command:

```text
python3 -m wayfinder stats --no-color
```

Observed result before the ingest:

```text
signals: 0
products: 0
opportunities: 0
ingest_runs: 0
source_activity:
  github: signals=0 opportunities=0 last_ingest_at=never health=unknown
  hackernews: signals=0 opportunities=0 last_ingest_at=never health=unknown
  oss-ledger: signals=0 opportunities=0 last_ingest_at=never health=unknown
```

This makes the post-run rows traceable to the same ingest execution below.

## Live scheduled ingest

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

Audit tail from `logs/wayfinder-audit.log` for the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 2, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T17:31:13.494709+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 65.143, "inserted_opportunities": 8, "inserted_products": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T17:31:13.561572+00:00"}
{"action": "wayfinder_scheduled_ingest_skipped", "llm_tokens": 0, "reason": "source_not_approved_for_unattended_ingest", "source": "hackernews", "status": "dry-run-only", "token_free": true, "ts": "2026-05-18T17:31:13.565717+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 3138.81, "inserted_opportunities": 29, "inserted_products": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T17:31:16.706671+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_sources": 2, "duration_ms": 3216.261, "enabled": true, "failed_sources": 0, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 1, "token_free": true, "ts": "2026-05-18T17:31:16.710068+00:00"}
```

## Stored rows after ingest

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
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T17:31:16.684394+00:00 health=ok
  hackernews: signals=0 opportunities=0 last_ingest_at=never health=unknown
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T17:31:13.553016+00:00 health=ok
```

SQLite spot checks against `.ai-state/wayfinder/wayfinder.db`:

```text
select source, count(*) as count from signals group by source order by source
{"count": 29, "source": "github"}
{"count": 8, "source": "oss-ledger"}

select source, count(*) as count from opportunities group by source order by source
{"count": 29, "source": "github"}
{"count": 8, "source": "oss-ledger"}

select source, started_at, finished_at, collected, inserted_signals, inserted_products, inserted_opportunities, dry_run, status, message from ingest_runs order by id desc
{"collected": 87, "dry_run": 0, "finished_at": "2026-05-18T17:31:16.684394+00:00", "inserted_opportunities": 29, "inserted_products": 29, "inserted_signals": 29, "message": "raw=29", "source": "github", "started_at": "2026-05-18T17:31:13.567138+00:00", "status": "ok"}
{"collected": 24, "dry_run": 0, "finished_at": "2026-05-18T17:31:13.553016+00:00", "inserted_opportunities": 8, "inserted_products": 8, "inserted_signals": 8, "message": "raw=8", "source": "oss-ledger", "started_at": "2026-05-18T17:31:13.495856+00:00", "status": "ok"}
```

## Search and dashboard proof

CLI search evidence:

```text
python3 -m wayfinder search saas --limit 5 --no-color
```

Observed rows include live GitHub records written by the same ingest:

```text
1. gracp/saas-generator | github | market research SaaS ideas
2. marcoETmx/SaaS-Studio | github | market research SaaS ideas
3. ruanxinyang/micro-saas-validator | github | market research SaaS ideas
4. sinan-mohammed/AI-SaaS-Idea-Validator | github | market research SaaS ideas
5. PhumudzoSly/ray | github | ai, saas, saas-application, validation
```

CLI opportunities evidence:

```text
python3 -m wayfinder opportunities --limit 5 --no-color
```

Observed top rows include both approved sources from the same ingest window:

```text
1. Leverage reddit-research-mcp | score=58.95 | Codex Foundry operator
2. Inspect lefttree/reddit-pain-points for leverage | score=57.9 | Wayfinder operator
3. Inspect calvinrodrigues500/product-hunter for leverage | score=57.9 | Wayfinder operator
```

Dashboard and route fetch proof from `python3 -m wayfinder serve --host 127.0.0.1 --port 8876`:

```text
GET /
- metric cards showed 37 signals, 37 products, 37 opportunities, 2 ingest_runs
- dashboard body included github and oss-ledger source cards
- dashboard shortlist included Leverage reddit-research-mcp and Inspect lefttree/reddit-pain-points for leverage
- dashboard signal rows included gracp/saas-generator

GET /search?q=saas
- page reported Search returned 11 rows with URL-backed filters
- page included gracp/saas-generator and marcoETmx/SaaS-Studio
- rows were tagged with source github

GET /api/search?q=saas&limit=3
- JSON payload returned collected_at=2026-05-18T17:31:16.* rows for gracp/saas-generator, marcoETmx/SaaS-Studio, and ruanxinyang/micro-saas-validator

GET /opportunities?source=github
- page reported 29 opportunities indexed
- page included Inspect lefttree/reddit-pain-points for leverage and Inspect calvinrodrigues500/product-hunter for leverage
```

## Acceptance conclusion

- The approved live scheduled-ingest path completed without `--dry-run`.
- Real rows were inserted into SQLite for both approved sources, with timestamps and per-source counts captured above.
- `search`, `/search`, `/api/search`, `/`, and `/opportunities?source=github` all exposed rows traceable to the same live ingest.
- The evidence is recorded in this linked task artifact instead of relying on fixture-only output.
