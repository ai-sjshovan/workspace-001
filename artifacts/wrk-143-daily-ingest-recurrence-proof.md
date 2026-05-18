# WRK-143 Daily Ingest Recurrence Proof

Acceptance evidence for `WRK-143` captured from the live `project/wayfinder` branch on `2026-05-18`.

This issue is a verification follow-up to `WRK-140`: confirm that the operator-runnable daily ingest path still works, emits token-free audit evidence, and exposes a reproducible recurrence command for release closeout.

## Repo Truth

- `wayfinder.yaml` sets `cron.enabled: true`
- `wayfinder.yaml` sets `cron.schedule: daily`
- approved unattended sources on this branch remain `oss-ledger` and `github`
- `hackernews` remains `dry-run-only`, so the unattended path should skip it with an audit row rather than collect it

## Validation Commands

Commands run once from the repo root on `2026-05-18`:

```bash
python3 -m wayfinder --no-color schedule-command
python3 -m wayfinder --no-color scheduled-ingest
tail -n 20 logs/wayfinder-audit.log
```

## `python3 -m wayfinder --no-color schedule-command`

```text
@daily cd /mnt/d/AI/codex-foundry/workspace/tasks/WRK-143 && /usr/bin/python3 -m wayfinder --config /mnt/d/AI/codex-foundry/workspace/tasks/WRK-143/wayfinder.yaml --no-color scheduled-ingest >> /mnt/d/AI/codex-foundry/workspace/tasks/WRK-143/logs/wayfinder-cron.log 2>&1
```

This is the reproducible operator recurrence path for release closeout on the current checkout: it is derived from the live config, includes the repo-root `cd`, pins the config path, and appends output to the resolved `logs/wayfinder-cron.log` path.

## `python3 -m wayfinder --no-color scheduled-ingest`

```text
scheduled-ingest: sources=3 approved=2 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T18:39:35.457677+00:00
hackernews: skipped status=dry-run-only
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T18:39:38.382096+00:00
scheduled-ingest: succeeded=2 skipped=1 failed=0 inserted_searchable_rows=37 inserted_signals=37 inserted_products=37 inserted_opportunities=37 duration_ms=3038.352 token_free=true llm_tokens=0
```

## Audit Tail

Tail inspected from `logs/wayfinder-audit.log` after the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 2, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T18:39:35.407455+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 56.533, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T18:39:35.465880+00:00"}
{"action": "wayfinder_scheduled_ingest_skipped", "llm_tokens": 0, "reason": "source_not_approved_for_unattended_ingest", "source": "hackernews", "status": "dry-run-only", "token_free": true, "ts": "2026-05-18T18:39:35.488720+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2925.876, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T18:39:38.416692+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 2, "approved_sources": 2, "duration_ms": 3038.352, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 37, "inserted_signals": 37, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 1, "source_count": 3, "token_free": true, "ts": "2026-05-18T18:39:38.446977+00:00"}
```

## Acceptance Readout

- The operator recurrence command resolves to `@daily` on the current `cron.schedule: daily` config.
- The command points at the current repo root and explicit `wayfinder.yaml`, so it is reproducible across release closeout and future operator runs.
- The live unattended path completed on the project branch without `--dry-run` or `--allow-disabled`.
- The unattended path kept the source-safety boundary intact by skipping `hackernews` as `dry-run-only`.
- The scheduled run stayed token-free end to end: every scheduled-ingest audit event recorded `token_free=true` and `llm_tokens=0`.
