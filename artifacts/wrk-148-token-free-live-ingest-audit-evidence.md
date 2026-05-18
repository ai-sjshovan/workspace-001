# WRK-148 Token-Free Live Ingest Audit Evidence

Acceptance evidence for `WRK-148` captured from a real `project/wayfinder` scheduled-ingest run on `2026-05-18`.

## Validation command

```text
python3 -m wayfinder --config wayfinder.yaml --no-color scheduled-ingest
```

Exit code: `0`

Command output from the verified run:

```text
scheduled-ingest: sources=3 approved=2 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T19:02:33.145597+00:00
hackernews: skipped status=dry-run-only
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T19:02:36.139306+00:00
scheduled-ingest: succeeded=2 skipped=1 failed=0 inserted_searchable_rows=37 inserted_signals=37 inserted_products=37 inserted_opportunities=37 duration_ms=3103.514 token_free=true llm_tokens=0
```

## Audit record evidence

Audit log inspected from `logs/wayfinder-audit.log` immediately after the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 2, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T19:02:33.081190+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 72.224, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T19:02:33.155357+00:00"}
{"action": "wayfinder_scheduled_ingest_skipped", "llm_tokens": 0, "reason": "source_not_approved_for_unattended_ingest", "source": "hackernews", "status": "dry-run-only", "token_free": true, "ts": "2026-05-18T19:02:33.178380+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2981.017, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T19:02:36.161004+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 2, "approved_sources": 2, "duration_ms": 3103.514, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 37, "inserted_signals": 37, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 1, "source_count": 3, "token_free": true, "ts": "2026-05-18T19:02:36.185520+00:00"}
```

## Acceptance mapping

- Real approved live source path: `github` ran without `--dry-run` and wrote `raw_records=29`, `normalized=87`, and inserted row counts in `wayfinder_scheduled_ingest_source`.
- Source counts: `source_count=3` and `approved_source_count=2` are present in `wayfinder_scheduled_ingest_started` and `wayfinder_scheduled_ingest_finished`.
- Failures: `failed_sources=0` is present in `wayfinder_scheduled_ingest_finished`.
- Duration: `duration_ms` is present in both the live `github` source row and the finished row.
- Token-free proof: every shown scheduled-ingest audit row records `token_free=true` and `llm_tokens=0`.
- Evidence path: this note plus `logs/wayfinder-audit.log` record the exact command output and audit rows used for verification.
