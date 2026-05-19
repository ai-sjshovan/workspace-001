# WRK-159 live ingest proof

Date: 2026-05-19
Branch validated: `wrk-159-live-ingest-proof`
Config: `wayfinder.yaml`

## Scope conclusion

The accepted production config is already present in `HEAD`:

- `sources.hackernews.status: enabled`
- `sources.github.status: enabled`
- `cron.enabled: true`
- `cron.token_free: true`

No config or code change was needed to satisfy the issue. This artifact records the required live validation on the production path.

## Validation commands

```bash
python3 -m wayfinder --no-color sources list --health
python3 -m wayfinder --no-color scheduled-ingest
python3 -m wayfinder --no-color search saas --limit 5
python3 -m wayfinder --no-color opportunities --limit 5
python3 -m wayfinder --no-color stats
```

## Key results

- `sources list --health` reported `hackernews` and `github` as `status=enabled`, `review=approved`, `unattended=eligible`, `credentials=none`.
- `scheduled-ingest` ran directly on the production config with no `--dry-run` and no `--allow-disabled`.
- `scheduled-ingest` reported `sources=3 approved=3 token_free=true llm_tokens=0`.
- Live source rows were written on the scheduled path:
  - `hackernews: raw=30 searchable_rows=30 inserted signals=30 products=0 opportunities=0`
  - `github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29`
- Final scheduled summary:
  - `scheduled-ingest: succeeded=3 skipped=0 failed=0 inserted_searchable_rows=67 inserted_signals=67 inserted_products=37 inserted_opportunities=37 duration_ms=5169.567 token_free=true llm_tokens=0`
- `search saas --limit 5` returned stored GitHub and Hacker News results.
- `opportunities --limit 5` returned stored opportunities after the scheduled run.
- `stats` reported:
  - `signals: 67`
  - `products: 37`
  - `opportunities: 37`
  - `ingest_runs: 3`
  - `scheduled_ingest: status=finished ... approved=3 skipped=0 failed=0`
  - `real_source_signal_count: 59`

## Audit log evidence

`logs/wayfinder-audit.log` recorded the required scheduled-ingest events:

- `wayfinder_scheduled_ingest_started`
- `wayfinder_scheduled_ingest_source` for `oss-ledger`
- `wayfinder_scheduled_ingest_source` for `hackernews`
- `wayfinder_scheduled_ingest_source` for `github`
- `wayfinder_scheduled_ingest_finished`

The recorded scheduled events include `token_free: true`, `llm_tokens: 0`, per-source outcomes, and inserted row counts from live sources.
