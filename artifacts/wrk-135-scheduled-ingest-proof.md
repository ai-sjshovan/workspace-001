# WRK-135 Scheduled Ingest Proof

Branch proof note for `WRK-135`. The live scheduled-ingest path is already working on `project/wayfinder`, so this task records the current acceptance evidence instead of changing product behavior.

## Source health

Command:

```text
python3 -m wayfinder sources list --health --no-color
```

Key result:

- `oss-ledger` is `enabled`, `review=approved`, `unattended=eligible`
- `github` is `enabled`, `review=approved`, `unattended=eligible`
- `hackernews` remains `dry-run-only` and is skipped from unattended ingest

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

## Search and opportunities smoke

Commands:

```text
python3 -m wayfinder search saas --limit 5 --no-color
python3 -m wayfinder opportunities --limit 5 --no-color
python3 -m wayfinder stats --no-color
```

Observed result:

- `search saas` returned five stored GitHub-backed rows, including `gracp/saas-generator` and `marcoETmx/SaaS-Studio`
- `opportunities --limit 5` returned five stored opportunity rows with deterministic scores
- `stats` reported:

```text
signals: 37
products: 37
opportunities: 37
ingest_runs: 2
source_activity:
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T16:58:22.643587+00:00 health=ok
  hackernews: signals=0 opportunities=0 last_ingest_at=never health=unknown
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T16:58:19.925333+00:00 health=ok
```

## Audit log proof

Tail inspected from `logs/wayfinder-audit.log` after the scheduled run:

```json
{"action":"wayfinder_scheduled_ingest_started","approved_source_count":2,"enabled":true,"llm_tokens":0,"schedule":"daily","source_count":3,"token_free":true}
{"action":"wayfinder_scheduled_ingest_source","duration_ms":66.9,"inserted_opportunities":8,"inserted_products":8,"inserted_signals":8,"llm_tokens":0,"normalized":24,"raw_records":8,"source":"oss-ledger","token_free":true}
{"action":"wayfinder_scheduled_ingest_skipped","llm_tokens":0,"reason":"source_not_approved_for_unattended_ingest","source":"hackernews","status":"dry-run-only","token_free":true}
{"action":"wayfinder_scheduled_ingest_source","duration_ms":2729.659,"inserted_opportunities":29,"inserted_products":29,"inserted_signals":29,"llm_tokens":0,"normalized":87,"raw_records":29,"source":"github","token_free":true}
{"action":"wayfinder_scheduled_ingest_finished","approved_sources":2,"duration_ms":2810.006,"enabled":true,"failed_sources":0,"llm_tokens":0,"schedule":"daily","skipped_sources":1,"token_free":true}
```

Acceptance proof from those audit events:

- source counts are present via `source_count` and `approved_source_count`
- failures are present via `failed_sources`
- duration is present on per-source and finished events
- every scheduled-ingest audit event records `token_free=true`
- every scheduled-ingest audit event records `llm_tokens=0`
