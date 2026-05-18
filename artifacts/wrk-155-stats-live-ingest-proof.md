# WRK-155 Stats Live-Ingest Proof

Acceptance evidence for `WRK-155`, captured from the active `project/wayfinder` branch on `2026-05-18`.

## Scope

This task verifies the existing `stats` surface only. No implementation changes were required; the task stayed read-only aside from writing fresh local ingest state and this evidence note.

## Commands run

```text
python3 -m wayfinder --no-color scheduled-ingest
python3 -m wayfinder --no-color stats
tail -n 10 logs/wayfinder-audit.log
python3 - <<'PY'
import sqlite3, json
conn = sqlite3.connect('.ai-state/wayfinder/wayfinder.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
print('COUNTS')
for row in cur.execute("select 'signals' as name, count(*) as total from signals union all select 'products', count(*) from products union all select 'opportunities', count(*) from opportunities union all select 'ingest_runs', count(*) from ingest_runs"):
    print(json.dumps(dict(row), sort_keys=True))
print('INGEST_RUNS')
for row in cur.execute("select source, finished_at, collected, inserted_searchable_rows, inserted_signals, inserted_products, inserted_opportunities, dry_run, status from ingest_runs order by id desc limit 3"):
    print(json.dumps(dict(row), sort_keys=True))
conn.close()
PY
```

## Live scheduled-ingest evidence

Command:

```text
python3 -m wayfinder --no-color scheduled-ingest
```

Output:

```text
scheduled-ingest: sources=3 approved=3 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T22:24:40.319674+00:00
hackernews: raw=30 searchable_rows=30 inserted signals=30 products=0 opportunities=0
hackernews: searchable_rows_total=30 last_ingest_at=2026-05-18T22:24:42.578992+00:00
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T22:24:45.331309+00:00
scheduled-ingest: succeeded=3 skipped=0 failed=0 inserted_searchable_rows=67 inserted_signals=67 inserted_products=37 inserted_opportunities=37 duration_ms=5182.407 token_free=true llm_tokens=0
```

This is the latest live-ingest evidence used for the comparison.

## Stats smoke output

Command:

```text
python3 -m wayfinder --no-color stats
```

Output after the same run:

```text
signals: 67
products: 37
opportunities: 37
ingest_runs: 3
source_activity:
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T22:24:45.331309+00:00 health=ok
  hackernews: signals=30 opportunities=0 last_ingest_at=2026-05-18T22:24:42.578992+00:00 health=ok
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T22:24:40.319674+00:00 health=ok
```

## Stored-row comparison

Counts read directly from `.ai-state/wayfinder/wayfinder.db` after the same run:

```text
COUNTS
{"name": "signals", "total": 67}
{"name": "products", "total": 37}
{"name": "opportunities", "total": 37}
{"name": "ingest_runs", "total": 3}
INGEST_RUNS
{"collected": 87, "dry_run": 0, "finished_at": "2026-05-18T22:24:45.331309+00:00", "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "source": "github", "status": "ok"}
{"collected": 30, "dry_run": 0, "finished_at": "2026-05-18T22:24:42.578992+00:00", "inserted_opportunities": 0, "inserted_products": 0, "inserted_searchable_rows": 30, "inserted_signals": 30, "source": "hackernews", "status": "ok"}
{"collected": 24, "dry_run": 0, "finished_at": "2026-05-18T22:24:40.319674+00:00", "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "source": "oss-ledger", "status": "ok"}
```

The aggregate table counts match the `stats` surface exactly:

- `signals: 67`
- `products: 37`
- `opportunities: 37`
- `ingest_runs: 3`

The per-source `source_activity` rows also match the latest persisted ingest rows:

- `github`: `signals=29`, `opportunities=29`, `last_ingest_at=2026-05-18T22:24:45.331309+00:00`
- `hackernews`: `signals=30`, `opportunities=0`, `last_ingest_at=2026-05-18T22:24:42.578992+00:00`
- `oss-ledger`: `signals=8`, `opportunities=8`, `last_ingest_at=2026-05-18T22:24:40.319674+00:00`

## Audit-log comparison

Tail from `logs/wayfinder-audit.log` for the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 3, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T22:24:40.239483+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 88.634, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T22:24:40.332125+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2238.541, "inserted_opportunities": 0, "inserted_products": 0, "inserted_searchable_rows": 30, "inserted_signals": 30, "llm_tokens": 0, "normalized": 30, "raw_records": 30, "source": "hackernews", "token_free": true, "ts": "2026-05-18T22:24:42.599588+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2739.699, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T22:24:45.376265+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 3, "approved_sources": 3, "duration_ms": 5182.407, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 67, "inserted_signals": 67, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 0, "source_count": 3, "token_free": true, "ts": "2026-05-18T22:24:45.423892+00:00"}
```

These audit totals match both the live `scheduled-ingest` stdout and the persisted DB counts used by `stats`.

## Conclusion

- `python3 -m wayfinder --no-color stats` reflects the current live-ingest totals after the approved sources run.
- Aggregate totals and per-source `last_ingest_at` values match the latest ingest evidence and stored rows.
- No code changes were necessary on the active Wayfinder project branch.
