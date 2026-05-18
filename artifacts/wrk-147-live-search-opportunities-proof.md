# WRK-147 Live Search And Opportunities Surface Proof

Acceptance evidence for `WRK-147` captured from the live `project/wayfinder` ingest path on `2026-05-18`.

## Scope

- Kept the task read-only and evidence-driven.
- Ran the project-branch CLI against the live unattended ingest path without `--dry-run`.
- Verified the stored rows then showed up on the search and opportunities CLI/web surfaces.

## Pre-run baseline

Commands:

```text
python3 -m wayfinder stats --no-color
python3 -m wayfinder search saas --limit 5 --no-color
python3 -m wayfinder opportunities --limit 5 --no-color
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
  oss-ledger: signals=0 opportunities=0 last_ingest_at=2026-05-18T18:54:59.907305+00:00 health=ok
```

```text
No rows found.
```

```text
No rows found.
```

This makes the post-run rows below attributable to the ingest execution captured in the next section rather than fixtures already present in the task workspace database.

## Live scheduled ingest

Command:

```text
python3 -m wayfinder --no-color scheduled-ingest
```

Output:

```text
scheduled-ingest: sources=3 approved=2 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T18:54:59.907305+00:00
hackernews: skipped status=dry-run-only
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T18:55:03.159141+00:00
scheduled-ingest: succeeded=2 skipped=1 failed=0 inserted_searchable_rows=37 inserted_signals=37 inserted_products=37 inserted_opportunities=37 duration_ms=3355.426 token_free=true llm_tokens=0
```

Exit code: `0`

Audit tail from `logs/wayfinder-audit.log` for the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 2, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T18:54:59.847676+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 69.262, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T18:54:59.918712+00:00"}
{"action": "wayfinder_scheduled_ingest_skipped", "llm_tokens": 0, "reason": "source_not_approved_for_unattended_ingest", "source": "hackernews", "status": "dry-run-only", "token_free": true, "ts": "2026-05-18T18:54:59.940620+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 3238.25, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T18:55:03.181116+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 2, "approved_sources": 2, "duration_ms": 3355.426, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 37, "inserted_signals": 37, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 1, "source_count": 3, "token_free": true, "ts": "2026-05-18T18:55:03.203540+00:00"}
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
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T18:55:03.159141+00:00 health=ok
  hackernews: signals=0 opportunities=0 last_ingest_at=never health=unknown
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T18:54:59.907305+00:00 health=ok
```

SQLite spot checks against `.ai-state/wayfinder/wayfinder.db`:

```text
signals
{"count": 29, "first_collected_at": "2026-05-18T18:55:03.130274+00:00", "last_collected_at": "2026-05-18T18:55:03.130712+00:00", "source": "github"}
{"count": 8, "first_collected_at": "2026-05-18T18:54:59.856218+00:00", "last_collected_at": "2026-05-18T18:54:59.856280+00:00", "source": "oss-ledger"}

sample_opportunities
{"collected_at": "2026-05-18T18:55:03.130715+00:00", "fingerprint": "aa9f49a85aa47c0aeb0f71baea73f42623b62cc79e069640c4e8e27504f58ed8", "scored_at": "2026-05-18T18:55:03.159067+00:00", "source": "github", "title": "Inspect yakuphankucukkesim/marketpulse-ai for leverage"}
{"collected_at": "2026-05-18T18:55:03.130706+00:00", "fingerprint": "0e2a136accef3d7a74ca089f85aeb04bf86b4cf41cba557a2bc37918aa4117f6", "scored_at": "2026-05-18T18:55:03.159045+00:00", "source": "github", "title": "Inspect xK3yx/Validata for leverage"}
{"collected_at": "2026-05-18T18:55:03.130693+00:00", "fingerprint": "05000804f77bd083711c39981823288d9d26dd3a9b192c32ae7da2bf1ff32bfb", "scored_at": "2026-05-18T18:55:03.159023+00:00", "source": "github", "title": "Inspect sudo-Harshk/MarketSense-AI for leverage"}

ingest_runs
{"collected": 87, "dry_run": 0, "finished_at": "2026-05-18T18:55:03.159141+00:00", "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "message": "raw=29", "source": "github", "started_at": "2026-05-18T18:54:59.941715+00:00", "status": "ok"}
{"collected": 24, "dry_run": 0, "finished_at": "2026-05-18T18:54:59.907305+00:00", "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "message": "raw=8", "source": "oss-ledger", "started_at": "2026-05-18T18:54:59.849575+00:00", "status": "ok"}
```

The `ingest_runs.dry_run = 0` rows plus the matching `collected_at` and `scored_at` timestamps are the key proof that the later search/opportunity results came from stored live ingest rows, not fixture-only dry runs.

## Surface proof

CLI search evidence:

```text
python3 -m wayfinder search saas --limit 5 --no-color
```

Observed rows:

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

Observed rows:

```text
1. Leverage reddit-research-mcp | score=58.95 | Codex Foundry operator
2. Inspect lefttree/reddit-pain-points for leverage | score=57.9 | Wayfinder operator
3. Inspect calvinrodrigues500/product-hunter for leverage | score=57.9 | Wayfinder operator
4. Inspect rizkiwijanarko/KickUp for leverage | score=56.7 | Wayfinder operator
5. Inspect PhumudzoSly/ray for leverage | score=55.75 | Wayfinder operator
```

Web route fetch proof from `python3 -m wayfinder serve --host 127.0.0.1 --port 8876`:

```text
GET /search?q=saas
- page reported Search returned 11 rows with URL-backed filters
- page included gracp/saas-generator
- page included marcoETmx/SaaS-Studio
- rows were tagged with source github

GET /api/search?q=saas&limit=3
- JSON payload returned gracp/saas-generator, marcoETmx/SaaS-Studio, and ruanxinyang/micro-saas-validator
- each row carried collected_at timestamps from 2026-05-18T18:55:03.1304..2026-05-18T18:55:03.1306+00:00

GET /opportunities?source=github
- page reported 29 opportunities indexed
- page included Inspect lefttree/reddit-pain-points for leverage
- page included Inspect calvinrodrigues500/product-hunter for leverage
- page included Inspect PhumudzoSly/ray for leverage

GET /
- dashboard body included Leverage reddit-research-mcp
- dashboard body included Inspect lefttree/reddit-pain-points for leverage
- dashboard body included gracp/saas-generator
```

## Acceptance conclusion

- The project-branch Wayfinder CLI ran the live scheduled-ingest path without `--dry-run`.
- The task workspace database started empty for `search` and `opportunities`, then stored 37 rows from the live ingest run.
- The proof ties the later surface output back to that run with `dry_run=0`, audit events, and matching GitHub `collected_at` / `scored_at` timestamps.
- `search`, `/search`, `/api/search`, `opportunities`, `/opportunities?source=github`, and the dashboard all exposed the stored live records from the same ingest evidence window.
