# WRK-158 Token-Free Ingest Outcomes And Inserted Rows

Acceptance evidence for `WRK-158` captured from the active `project/wayfinder` branch on `2026-05-19`.

## Scope

This task records operator-readable proof for one real scheduled ingest run only. No product code or config changes were required in this checkout.

## Validation commands

```bash
python3 -m wayfinder --no-color sources list --health
python3 -m wayfinder --no-color scheduled-ingest
python3 -m wayfinder --no-color search saas --limit 5
python3 -m wayfinder --no-color opportunities --limit 5
python3 -m wayfinder --no-color stats
python3 - <<'PY'
import sqlite3
conn = sqlite3.connect('.ai-state/wayfinder/wayfinder.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
print('latest_ingest_runs:')
for row in cur.execute("select source, finished_at, collected, inserted_searchable_rows, inserted_signals, inserted_products, inserted_opportunities, dry_run, status from ingest_runs order by id desc limit 3"):
    print(dict(row))
print('search_hits:')
for row in cur.execute("select source, title from signals where lower(title) like '%saas%' order by collected_at desc limit 5"):
    print(dict(row))
print('opportunity_hits:')
for row in cur.execute("select title, opportunity_score from opportunities order by opportunity_score desc limit 5"):
    print(dict(row))
PY
tail -n 10 logs/wayfinder-audit.log
```

## Source health before the run

```text
oss-ledger status=enabled kind=static_ledger credentials=none terms=reviewed-public-data rate_limits=none-local-file scraping=none pii_ugc=low-curated-public-metadata hosted_dependencies=none
  review=approved unattended=eligible why=Curated local ledger with explicit repository inputs and no unattended network dependency.
  latest_run=none status=unknown last_ingest_at=never collected=0 searchable_rows=0 signals=0 products=0 opportunities=0
hackernews status=enabled kind=hackernews credentials=none terms=public-api-allowed rate_limits=low-volume-search scraping=api-search pii_ugc=reviewed-story-metadata hosted_dependencies=algolia-hn-api
  review=approved unattended=eligible why=Approved for unattended low-volume Algolia search using the configured story-only queries; normal and scheduled ingest use the live official endpoint while fixture-backed dry runs remain available for diagnostics.
  latest_run=none status=unknown last_ingest_at=never collected=0 searchable_rows=0 signals=0 products=0 opportunities=0
github status=enabled kind=github credentials=none terms=public-api-allowed rate_limits=low-volume-public-search scraping=official-api pii_ugc=low-public-repo-metadata hosted_dependencies=github-public-api
  review=approved unattended=eligible why=Approved for daily anonymous public repository search at the configured low query volume; dry runs stay fixture-backed for diagnostics while scheduled and normal ingest use the live official API.
  latest_run=none status=unknown last_ingest_at=never collected=0 searchable_rows=0 signals=0 products=0 opportunities=0
```

## Live scheduled-ingest output

```text
scheduled-ingest: sources=3 approved=3 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-19T18:09:11.842194+00:00
hackernews: raw=30 searchable_rows=30 inserted signals=30 products=0 opportunities=0
hackernews: searchable_rows_total=30 last_ingest_at=2026-05-19T18:09:14.722687+00:00
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-19T18:09:20.438951+00:00
scheduled-ingest: succeeded=3 skipped=0 failed=0 inserted_searchable_rows=67 inserted_signals=67 inserted_products=37 inserted_opportunities=37 duration_ms=5993.003 token_free=true llm_tokens=0
```

This run used the production operator path directly, without `--dry-run` and without `--allow-disabled`.

## Search and opportunities proof

The inserted live rows are visible through both operator-facing CLI surfaces required by the issue.

`python3 -m wayfinder --no-color search saas --limit 5`:

```text
1. gracp/saas-generator | github | market research SaaS ideas
2. marcoETmx/SaaS-Studio | github | market research SaaS ideas
3. sinan-mohammed/AI-SaaS-Idea-Validator | github | market research SaaS ideas
4. SaaS Company Uses Customer Pain Points for Content Creation Ideas | hackernews | founder-pain
5. ruanxinyang/micro-saas-validator | github | market research SaaS ideas
```

`python3 -m wayfinder --no-color opportunities --limit 5`:

```text
1. Leverage reddit-research-mcp | score=58.95 | Codex Foundry operator
2. Inspect lefttree/reddit-pain-points for leverage | score=57.9 | Wayfinder operator
3. Inspect calvinrodrigues500/product-hunter for leverage | score=57.9 | Wayfinder operator
4. Inspect rizkiwijanarko/KickUp for leverage | score=56.7 | Wayfinder operator
5. Inspect PhumudzoSly/ray for leverage | score=55.75 | Wayfinder operator
```

## Stats and persisted local-store proof

`python3 -m wayfinder --no-color stats`:

```text
signals: 67
products: 37
opportunities: 37
ingest_runs: 3
searchable_data_last_updated: 2026-05-19T18:09:20.402086+00:00
scheduled_ingest: status=finished finished_at=2026-05-19T18:09:20.491134+00:00 approved=3 skipped=0 failed=0
  oss-ledger: status=ok signals+8 products+8 opportunities+8
  hackernews: status=ok signals+30 products+0 opportunities+0
  github: status=ok signals+29 products+29 opportunities+29
real_source_signal_count: 59
```

SQLite check against `.ai-state/wayfinder/wayfinder.db` from the same run:

```text
latest_ingest_runs:
{'source': 'github', 'finished_at': '2026-05-19T18:09:20.438951+00:00', 'collected': 87, 'inserted_searchable_rows': 29, 'inserted_signals': 29, 'inserted_products': 29, 'inserted_opportunities': 29, 'dry_run': 0, 'status': 'ok'}
{'source': 'hackernews', 'finished_at': '2026-05-19T18:09:14.722687+00:00', 'collected': 30, 'inserted_searchable_rows': 30, 'inserted_signals': 30, 'inserted_products': 0, 'inserted_opportunities': 0, 'dry_run': 0, 'status': 'ok'}
{'source': 'oss-ledger', 'finished_at': '2026-05-19T18:09:11.842194+00:00', 'collected': 24, 'inserted_searchable_rows': 8, 'inserted_signals': 8, 'inserted_products': 8, 'inserted_opportunities': 8, 'dry_run': 0, 'status': 'ok'}
search_hits:
{'source': 'github', 'title': 'sinan-mohammed/AI-SaaS-Idea-Validator'}
{'source': 'github', 'title': 'ruanxinyang/micro-saas-validator'}
{'source': 'github', 'title': 'marcoETmx/SaaS-Studio'}
{'source': 'github', 'title': 'liyajaleel/AI-SaaS-Idea-Validator'}
{'source': 'github', 'title': 'gracp/saas-generator'}
opportunity_hits:
{'title': 'Leverage reddit-research-mcp', 'opportunity_score': 58.95}
{'title': 'Inspect calvinrodrigues500/product-hunter for leverage', 'opportunity_score': 57.9}
{'title': 'Inspect lefttree/reddit-pain-points for leverage', 'opportunity_score': 57.9}
{'title': 'Inspect rizkiwijanarko/KickUp for leverage', 'opportunity_score': 56.7}
{'title': 'Inspect PhumudzoSly/ray for leverage', 'opportunity_score': 55.75}
```

## Audit trail

Tail from `logs/wayfinder-audit.log` immediately after the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 3, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-19T18:09:11.812501+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 36.148, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-19T18:09:11.850330+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2866.001, "inserted_opportunities": 0, "inserted_products": 0, "inserted_searchable_rows": 30, "inserted_signals": 30, "llm_tokens": 0, "normalized": 30, "raw_records": 30, "source": "hackernews", "token_free": true, "ts": "2026-05-19T18:09:14.734310+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 3022.502, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-19T18:09:20.462333+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 3, "approved_sources": 3, "duration_ms": 5993.003, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 67, "inserted_signals": 67, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 0, "source_count": 3, "token_free": true, "ts": "2026-05-19T18:09:20.491134+00:00"}
```

## Acceptance mapping

- The audit trail records a real scheduled ingest run on the live operator path.
- Source counts, failures, duration, `inserted_searchable_rows`, and `token_free=true` / `llm_tokens=0` are present in the command output and the audit log.
- `search` and `opportunities` both surface the inserted live records after the run.
- The persisted `ingest_runs` rows in the local SQLite store match the same per-source outcomes and inserted counts.
