# WRK-154 Dashboard Freshness And Source Evidence Proof

Acceptance evidence for `WRK-154`, captured from the active `project/wayfinder` checkout on `2026-05-18`.

## Scope

- Ran the approved live unattended ingest path once from this task workspace.
- Verified the dashboard home surface shows fresh ingest timing and source evidence from that run.
- Added a narrow regression assertion so the home route keeps exposing that evidence.

## Live ingest run

Command:

```text
python3 -m wayfinder --no-color scheduled-ingest
```

Exit code: `0`

Observed output:

```text
scheduled-ingest: sources=3 approved=3 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T21:23:41.462719+00:00
hackernews: raw=30 searchable_rows=30 inserted signals=30 products=0 opportunities=0
hackernews: searchable_rows_total=30 last_ingest_at=2026-05-18T21:23:43.543809+00:00
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T21:23:46.294529+00:00
scheduled-ingest: succeeded=3 skipped=0 failed=0 inserted_searchable_rows=67 inserted_signals=67 inserted_products=37 inserted_opportunities=37 duration_ms=4927.837 token_free=true llm_tokens=0
```

Matching audit tail:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 3, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T21:23:41.414351+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 55.105, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T21:23:41.471371+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2065.931, "inserted_opportunities": 0, "inserted_products": 0, "inserted_searchable_rows": 30, "inserted_signals": 30, "llm_tokens": 0, "normalized": 30, "raw_records": 30, "source": "hackernews", "token_free": true, "ts": "2026-05-18T21:23:43.558321+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2735.947, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T21:23:46.318639+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 3, "approved_sources": 3, "duration_ms": 4927.837, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 67, "inserted_signals": 67, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 0, "source_count": 3, "token_free": true, "ts": "2026-05-18T21:23:46.343492+00:00"}
```

## Dashboard home proof

Route checked from a disposable local server:

```text
python3 -m wayfinder serve --host 127.0.0.1 --port 8876
curl -s 'http://127.0.0.1:8876/?source=github'
```

Observed dashboard strings on `/` with `source=github`:

```text
Signals 29 · opportunities 29
Latest ingest evidence: ok at 2026-05-18T21:23:46.294529+00:00 · searchable +29 · opportunities +29
Latest ingest evidence: ok at 2026-05-18T21:23:43.543809+00:00 · searchable +30 · opportunities +0
Latest ingest evidence: ok at 2026-05-18T21:23:41.462719+00:00 · searchable +8 · opportunities +8
Open dedicated source view
Signals 29 · opportunities 29 · avg score 1.0
Latest signal captured: 2026-05-18T21:23:46.254902+00:00
Ingest health: ok latest run 2026-05-18T21:23:46.294529+00:00
finished 2026-05-18T21:23:46.294529+00:00 · collected 87 · searchable +29 · signals +29 · opportunities +29
```

Screenshot captured from the same route:

```text
/tmp/wrk-154-dashboard-home.png
```

## Regression coverage

Command:

```text
python3 -m unittest tests.test_web_routes
```

Exit code: `0`

The updated smoke now asserts that the dashboard home surface exposes:

- the source-card `Latest ingest evidence: ...` line
- searchable and opportunity insert deltas on the home source cards
- the selected-source panel freshness and latest-run evidence

## Acceptance conclusion

- The approved live ingest path ran successfully in this workspace and wrote fresh `ingest_runs` rows for all three enabled sources.
- The dashboard home surface now shows source-level ingest freshness and inserted-row evidence directly on the source cards.
- Filtering the dashboard to `source=github` also shows the selected-source freshness, latest-run health, and recent-run evidence without leaving the home route.
