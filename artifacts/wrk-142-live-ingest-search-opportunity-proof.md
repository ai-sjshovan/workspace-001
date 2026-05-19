# WRK-142 Live Ingest Search And Opportunity Proof

Acceptance evidence for `WRK-142` captured from the live `project/wayfinder` scheduled-ingest path on `2026-05-18`.

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

This makes the post-run search and opportunity rows traceable to the same ingest execution below.

## Live scheduled ingest

Command:

```text
python3 -m wayfinder scheduled-ingest --no-color
```

Output:

```text
scheduled-ingest: sources=3 approved=2 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T18:24:39.157559+00:00
hackernews: skipped status=dry-run-only
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T18:24:42.511107+00:00
scheduled-ingest: succeeded=2 skipped=1 failed=0 inserted_searchable_rows=37 inserted_signals=37 inserted_products=37 inserted_opportunities=37 duration_ms=3432.143 token_free=true llm_tokens=0
```

Exit code: `0`

Audit tail from `logs/wayfinder-audit.log` for the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 2, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T18:24:39.132322+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 32.534, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T18:24:39.166988+00:00"}
{"action": "wayfinder_scheduled_ingest_skipped", "llm_tokens": 0, "reason": "source_not_approved_for_unattended_ingest", "source": "hackernews", "status": "dry-run-only", "token_free": true, "ts": "2026-05-18T18:24:39.188062+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 3344.935, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T18:24:42.534843+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 2, "approved_sources": 2, "duration_ms": 3432.143, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 37, "inserted_signals": 37, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 1, "source_count": 3, "token_free": true, "ts": "2026-05-18T18:24:42.566257+00:00"}
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
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T18:24:42.511107+00:00 health=ok
  hackernews: signals=0 opportunities=0 last_ingest_at=never health=unknown
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T18:24:39.157559+00:00 health=ok
```

DB spot checks against `.ai-state/wayfinder/wayfinder.db`:

```text
signals
{"count": 29, "source": "github"}
{"count": 8, "source": "oss-ledger"}

opportunities
{"count": 29, "source": "github"}
{"count": 8, "source": "oss-ledger"}

ingest_runs
{"collected": 87, "dry_run": 0, "finished_at": "2026-05-18T18:24:42.511107+00:00", "inserted_opportunities": 29, "inserted_products": 29, "inserted_signals": 29, "message": "raw=29", "source": "github", "started_at": "2026-05-18T18:24:39.189319+00:00", "status": "ok"}
{"collected": 24, "dry_run": 0, "finished_at": "2026-05-18T18:24:39.157559+00:00", "inserted_opportunities": 8, "inserted_products": 8, "inserted_signals": 8, "message": "raw=8", "source": "oss-ledger", "started_at": "2026-05-18T18:24:39.133793+00:00", "status": "ok"}
```

## Search and opportunity proof

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

Observed top rows include stored opportunities from the same ingest window:

```text
1. Leverage reddit-research-mcp | score=58.95 | Codex Foundry operator
2. Inspect lefttree/reddit-pain-points for leverage | score=57.9 | Wayfinder operator
3. Inspect calvinrodrigues500/product-hunter for leverage | score=57.9 | Wayfinder operator
4. Inspect rizkiwijanarko/KickUp for leverage | score=56.7 | Wayfinder operator
5. Inspect PhumudzoSly/ray for leverage | score=55.75 | Wayfinder operator
```

Route fetch proof from `python3 -m wayfinder serve --host 127.0.0.1 --port 8876`:

```text
GET /
- dashboard body included Leverage reddit-research-mcp
- dashboard body included Inspect lefttree/reddit-pain-points for leverage
- dashboard body included gracp/saas-generator

GET /search?q=saas
- page reported Search returned 11 rows with URL-backed filters
- page included gracp/saas-generator and marcoETmx/SaaS-Studio
- rows were tagged with source github

GET /api/search?q=saas&limit=3
- JSON payload returned gracp/saas-generator, marcoETmx/SaaS-Studio, and ruanxinyang/micro-saas-validator
- each row carried collected_at timestamps from 2026-05-18T18:24:42.*+00:00

GET /opportunities?source=github
- page reported 29 opportunities indexed
- page included Inspect lefttree/reddit-pain-points for leverage
- page included Inspect calvinrodrigues500/product-hunter for leverage
```

## Automated validation path

Focused regression added in `tests/test_scheduled_ingest.py`:

- runs approved non-dry-run `scheduled-ingest` against a live-like GitHub source record
- verifies `search` reads the stored searchable row from SQLite
- verifies `opportunities` reads the stored opportunity row from the same ingest
- preserves the token-free contract by keeping `scheduled-ingest` non-LLM and deterministic

## Acceptance conclusion

- Approved live scheduled ingest completed without `--dry-run`.
- Real rows were inserted into SQLite for both approved sources, with per-source counts and ingest timestamps captured above.
- `search`, `opportunities`, `/`, `/search`, `/api/search`, and `/opportunities?source=github` all exposed rows traceable to the same live ingest.
- The closeout evidence is recorded in this linked task artifact, and the same path is now covered by a focused automated regression.
