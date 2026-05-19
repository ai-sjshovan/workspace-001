# WRK-145 Live Ingest Audit Proof

Acceptance evidence for `WRK-145` captured from the live `project/wayfinder` scheduled-ingest path on `2026-05-18`.

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

This makes the post-run stored rows and audit records traceable to the same ingest execution below.

## Live scheduled ingest

Command:

```text
python3 -m wayfinder scheduled-ingest --no-color
```

Output:

```text
scheduled-ingest: sources=3 approved=2 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T18:32:18.823252+00:00
hackernews: skipped status=dry-run-only
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T18:32:21.948000+00:00
scheduled-ingest: succeeded=2 skipped=1 failed=0 inserted_searchable_rows=37 inserted_signals=37 inserted_products=37 inserted_opportunities=37 duration_ms=3210.83 token_free=true llm_tokens=0
```

Exit code: `0`

Audit tail from `logs/wayfinder-audit.log` for the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 2, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T18:32:18.792284+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 38.254, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T18:32:18.832793+00:00"}
{"action": "wayfinder_scheduled_ingest_skipped", "llm_tokens": 0, "reason": "source_not_approved_for_unattended_ingest", "source": "hackernews", "status": "dry-run-only", "token_free": true, "ts": "2026-05-18T18:32:18.853183+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 3120.147, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T18:32:21.975189+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 2, "approved_sources": 2, "duration_ms": 3210.83, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 37, "inserted_signals": 37, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 1, "source_count": 3, "token_free": true, "ts": "2026-05-18T18:32:22.003796+00:00"}
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
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T18:32:21.948000+00:00 health=ok
  hackernews: signals=0 opportunities=0 last_ingest_at=never health=unknown
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T18:32:18.823252+00:00 health=ok
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
{"collected": 87, "dry_run": 0, "finished_at": "2026-05-18T18:32:21.948000+00:00", "inserted_opportunities": 29, "inserted_products": 29, "inserted_signals": 29, "message": "raw=29", "source": "github", "started_at": "2026-05-18T18:32:18.854314+00:00", "status": "ok"}
{"collected": 24, "dry_run": 0, "finished_at": "2026-05-18T18:32:18.823252+00:00", "inserted_opportunities": 8, "inserted_products": 8, "inserted_signals": 8, "message": "raw=8", "source": "oss-ledger", "started_at": "2026-05-18T18:32:18.793607+00:00", "status": "ok"}
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

CLI opportunity evidence:

```text
python3 -m wayfinder opportunities --limit 5 --no-color
```

Observed rows include stored opportunities from the same ingest window:

```text
1. Leverage reddit-research-mcp | score=58.95 | Codex Foundry operator
2. Inspect lefttree/reddit-pain-points for leverage | score=57.9 | Wayfinder operator
3. Inspect calvinrodrigues500/product-hunter for leverage | score=57.9 | Wayfinder operator
4. Inspect rizkiwijanarko/KickUp for leverage | score=56.7 | Wayfinder operator
5. Inspect PhumudzoSly/ray for leverage | score=55.75 | Wayfinder operator
```

## Acceptance conclusion

- The project branch ran approved `scheduled-ingest` without `--dry-run` or `--allow-disabled`.
- Real rows were written for at least one approved live source; this run wrote rows for both `oss-ledger` and `github`.
- `search` and `opportunities` both exposed records traceable to the same ingest run.
- The audit evidence captures source counts, skipped/failure counts, per-source and overall duration, `token_free=true`, and `llm_tokens=0`.
