# WRK-152 Stored Live Ingest Surface Proof

Acceptance evidence for `WRK-152`, captured from the live `project/wayfinder` unattended ingest path on `2026-05-18`.

## Scope

- Kept the task narrow and evidence-only.
- Revalidated the current repo behavior instead of relying on older proof files.
- Confirmed that the local SQLite store exposes live ingest rows through search and opportunities surfaces without using dry-run fixtures.

## Current source policy

Command:

```text
python3 -m wayfinder sources list --health --no-color
```

Current result on `2026-05-18`:

- `oss-ledger` is `enabled`, `review=approved`, `unattended=eligible`
- `hackernews` is `enabled`, `review=approved`, `unattended=eligible`
- `github` is `enabled`, `review=approved`, `unattended=eligible`

This matters because older same-day proof files were recorded before the current `hackernews` approval state. This artifact reflects the latest repo/config truth in this task workspace.

## Pre-run baseline

Command:

```text
python3 -m wayfinder stats --no-color
```

Observed result before ingest:

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

This makes the later surface output attributable to the live ingest run below rather than pre-seeded rows.

## Live unattended ingest

Command:

```text
python3 -m wayfinder --no-color scheduled-ingest
```

Output:

```text
scheduled-ingest: sources=3 approved=3 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T19:33:53.411771+00:00
hackernews: raw=30 searchable_rows=30 inserted signals=30 products=0 opportunities=0
hackernews: searchable_rows_total=30 last_ingest_at=2026-05-18T19:33:55.622930+00:00
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T19:33:58.527431+00:00
scheduled-ingest: succeeded=3 skipped=0 failed=0 inserted_searchable_rows=67 inserted_signals=67 inserted_products=37 inserted_opportunities=37 duration_ms=5183.307 token_free=true llm_tokens=0
```

Exit code: `0`

Audit tail from `logs/wayfinder-audit.log` for the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 3, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T19:33:53.387028+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 31.349, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T19:33:53.420026+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2197.621, "inserted_opportunities": 0, "inserted_products": 0, "inserted_searchable_rows": 30, "inserted_signals": 30, "llm_tokens": 0, "normalized": 30, "raw_records": 30, "source": "hackernews", "token_free": true, "ts": "2026-05-18T19:33:55.634260+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2896.572, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T19:33:58.549211+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 3, "approved_sources": 3, "duration_ms": 5183.307, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 67, "inserted_signals": 67, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 0, "source_count": 3, "token_free": true, "ts": "2026-05-18T19:33:58.570907+00:00"}
```

## Stored rows in SQLite after ingest

Command:

```text
python3 -m wayfinder stats --no-color
```

Observed result:

```text
signals: 67
products: 37
opportunities: 37
ingest_runs: 3
source_activity:
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T19:33:58.527431+00:00 health=ok
  hackernews: signals=30 opportunities=0 last_ingest_at=2026-05-18T19:33:55.622930+00:00 health=ok
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T19:33:53.411771+00:00 health=ok
```

SQLite spot checks against `.ai-state/wayfinder/wayfinder.db`:

```text
signals_by_source
{"count": 29, "first_collected_at": "2026-05-18T19:33:58.492257+00:00", "last_collected_at": "2026-05-18T19:33:58.492752+00:00", "source": "github"}
{"count": 30, "first_collected_at": "2026-05-18T19:33:55.601477+00:00", "last_collected_at": "2026-05-18T19:33:55.602070+00:00", "source": "hackernews"}
{"count": 8, "first_collected_at": "2026-05-18T19:33:53.394519+00:00", "last_collected_at": "2026-05-18T19:33:53.394570+00:00", "source": "oss-ledger"}

opportunities_by_source
{"count": 29, "first_collected_at": "2026-05-18T19:33:58.492277+00:00", "last_collected_at": "2026-05-18T19:33:58.492755+00:00", "source": "github"}
{"count": 8, "first_collected_at": "2026-05-18T19:33:53.394535+00:00", "last_collected_at": "2026-05-18T19:33:53.394572+00:00", "source": "oss-ledger"}

sample_opportunities
{"collected_at": "2026-05-18T19:33:58.492755+00:00", "fingerprint": "aa9f49a85aa47c0aeb0f71baea73f42623b62cc79e069640c4e8e27504f58ed8", "scored_at": "2026-05-18T19:33:58.527369+00:00", "source": "github", "title": "Inspect yakuphankucukkesim/marketpulse-ai for leverage"}
{"collected_at": "2026-05-18T19:33:58.492744+00:00", "fingerprint": "0e2a136accef3d7a74ca089f85aeb04bf86b4cf41cba557a2bc37918aa4117f6", "scored_at": "2026-05-18T19:33:58.527348+00:00", "source": "github", "title": "Inspect xK3yx/Validata for leverage"}
{"collected_at": "2026-05-18T19:33:58.492727+00:00", "fingerprint": "05000804f77bd083711c39981823288d9d26dd3a9b192c32ae7da2bf1ff32bfb", "scored_at": "2026-05-18T19:33:58.527325+00:00", "source": "github", "title": "Inspect sudo-Harshk/MarketSense-AI for leverage"}

ingest_runs
{"collected": 87, "dry_run": 0, "finished_at": "2026-05-18T19:33:58.527431+00:00", "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "message": "raw=29", "source": "github", "started_at": "2026-05-18T19:33:55.652095+00:00", "status": "ok"}
{"collected": 30, "dry_run": 0, "finished_at": "2026-05-18T19:33:55.622930+00:00", "inserted_opportunities": 0, "inserted_products": 0, "inserted_searchable_rows": 30, "inserted_signals": 30, "message": "raw=30", "source": "hackernews", "started_at": "2026-05-18T19:33:53.436029+00:00", "status": "ok"}
{"collected": 24, "dry_run": 0, "finished_at": "2026-05-18T19:33:53.411771+00:00", "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "message": "raw=8", "source": "oss-ledger", "started_at": "2026-05-18T19:33:53.388220+00:00", "status": "ok"}
```

The `ingest_runs.dry_run = 0` rows plus the matching `collected_at` and `scored_at` timestamps are the key proof that the later search and opportunities results came from stored live ingest rows, not dry-run fixtures.

## Surface proof

CLI search evidence:

```text
python3 -m wayfinder search saas --limit 5 --no-color
```

Observed rows:

```text
1. gracp/saas-generator | github | market research SaaS ideas
2. marcoETmx/SaaS-Studio | github | market research SaaS ideas
3. sinan-mohammed/AI-SaaS-Idea-Validator | github | market research SaaS ideas
4. SaaS Company Uses Customer Pain Points for Content Creation Ideas | hackernews | founder-pain
5. ruanxinyang/micro-saas-validator | github | market research SaaS ideas
```

CLI opportunities evidence:

```text
python3 -m wayfinder opportunities --limit 5 --no-color
```

Observed rows:

```text
1. Leverage reddit-research-mcp | score=58.95 | Codex Foundry operator
2. Inspect lefttree/reddit-pain-points for leverage | score=57.9 | Wayfinder operator
3. Inspect calvinrodrigues500/product-hunter for leverage | score=57.9 | Wayfinder operator
4. Inspect rizkiwijanarko/KickUp for leverage | score=56.7 | Wayfinder operator
5. Inspect PhumudzoSly/ray for leverage | score=55.75 | Wayfinder operator
```

Route fetch proof from `python3 -m wayfinder serve --host 127.0.0.1 --port 8876`:

```text
GET /search?q=saas
- page reported Search returned 22 rows with URL-backed filters
- page included gracp/saas-generator
- page included marcoETmx/SaaS-Studio
- page included sinan-mohammed/AI-SaaS-Idea-Validator
- page included a live Hacker News row: SaaS Company Uses Customer Pain Points for Content Creation Ideas
- rows linked back to /sources/github for GitHub-backed records

GET /api/search?q=saas&limit=3
- JSON payload returned gracp/saas-generator, marcoETmx/SaaS-Studio, and sinan-mohammed/AI-SaaS-Idea-Validator
- each row carried github source tags and collected_at timestamps from 2026-05-18T19:33:58.4924..2026-05-18T19:33:58.4926+00:00

GET /opportunities?source=github
- page reported 29 opportunities indexed
- page included Inspect lefttree/reddit-pain-points for leverage
- page included Inspect calvinrodrigues500/product-hunter for leverage
- page included Inspect PhumudzoSly/ray for leverage

GET /api/opportunities?source=github&limit=3
- JSON payload returned Inspect lefttree/reddit-pain-points for leverage, Inspect calvinrodrigues500/product-hunter for leverage, and Inspect rizkiwijanarko/KickUp for leverage
- each row carried github source tags, collected_at timestamps from 2026-05-18T19:33:58.4924..2026-05-18T19:33:58.4926+00:00, and scored_at timestamps from 2026-05-18T19:33:58.5268..2026-05-18T19:33:58.5272+00:00

GET /
- dashboard body included Leverage reddit-research-mcp
- dashboard body included Inspect lefttree/reddit-pain-points for leverage
- dashboard body included gracp/saas-generator in the lower signal list
```

## Acceptance conclusion

- The current `project/wayfinder` unattended ingest path ran live without `--dry-run`.
- The local SQLite store persisted 67 searchable rows and 37 opportunities from the same run.
- `search`, `/search`, `/api/search`, `opportunities`, `/opportunities?source=github`, `/api/opportunities?source=github`, and the dashboard all exposed rows traceable to that stored live ingest data.
- Operators can inspect stored live suggestions locally from SQLite-backed surfaces without falling back to dry-run fixtures.
