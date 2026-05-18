# WRK-157 WRK-154 PR Gate Clearance Proof

Acceptance evidence for `WRK-157`, captured from the active `project/wayfinder` line on `2026-05-18`.

## Scope

This task does not change Wayfinder behavior. It records the release-close truth for the stale `WRK-154` PR gate:

- `WRK-154` PR `#108` is already merged into `project/wayfinder`.
- There are no remaining open pull requests targeting `project/wayfinder`.
- The current branch still passes the configured Wayfinder smoke checks after a live unattended ingest run.

## Upstream PR truth

GitHub state for `WRK-154` PR `#108`:

- PR: `https://github.com/ai-sjshovan/workspace-001/pull/108`
- Title: `WRK-154: Verify dashboard freshness and source evidence are visible after live ingest`
- State: `closed`
- Merged: `true`
- Merged at: `2026-05-18T21:30:35Z`
- Merge commit: `b39ec053c6a1172f0ecd1e826ed2e47778a52ba3`
- Base: `project/wayfinder`
- Head: `WRK-154-dashboard-freshness-evidence`

Open-PR verification against the same base returned no results:

```text
repo=ai-sjshovan/workspace-001
query=base:project/wayfinder
state=open
result_count=0
```

Local branch history also shows the merged PR already present on the project branch:

```text
e6bb22a (origin/project/wayfinder, project/wayfinder) Merge PR #109: WRK-156
449988b WRK-156 document daily live-ingest schedule evidence
b39ec05 Merge PR #108: WRK-154
c208a6f WRK-154 show dashboard ingest freshness evidence
```

## Release smoke

These are the configured acceptance smoke checks for this repo. They were run once from this task workspace after confirming the merged PR state above.

### `python3 -m wayfinder sources list --health --no-color`

Exit code: `0`

Key result:

```text
github ... latest_run=live status=ok last_ingest_at=2026-05-18T21:54:44.989038+00:00 collected=87 searchable_rows=29 signals=29 products=29 opportunities=29
hackernews ... latest_run=live status=ok last_ingest_at=2026-05-18T21:54:42.265563+00:00 collected=30 searchable_rows=30 signals=30 products=0 opportunities=0
oss-ledger ... latest_run=live status=ok last_ingest_at=2026-05-18T21:54:40.005078+00:00 collected=24 searchable_rows=8 signals=8 products=8 opportunities=8
```

### `python3 -m wayfinder scheduled-ingest --no-color`

Exit code: `0`

Observed output:

```text
scheduled-ingest: sources=3 approved=3 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T21:54:40.005078+00:00
hackernews: raw=30 searchable_rows=30 inserted signals=30 products=0 opportunities=0
hackernews: searchable_rows_total=30 last_ingest_at=2026-05-18T21:54:42.265563+00:00
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T21:54:44.989038+00:00
scheduled-ingest: succeeded=3 skipped=0 failed=0 inserted_searchable_rows=67 inserted_signals=67 inserted_products=37 inserted_opportunities=37 duration_ms=5146.872 token_free=true llm_tokens=0
```

Matching audit tail:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 3, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T21:54:39.948869+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 69.998, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T21:54:40.021923+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2224.95, "inserted_opportunities": 0, "inserted_products": 0, "inserted_searchable_rows": 30, "inserted_signals": 30, "llm_tokens": 0, "normalized": 30, "raw_records": 30, "source": "hackernews", "token_free": true, "ts": "2026-05-18T21:54:42.290015+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2711.104, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T21:54:45.042533+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 3, "approved_sources": 3, "duration_ms": 5146.872, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 67, "inserted_signals": 67, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 0, "source_count": 3, "token_free": true, "ts": "2026-05-18T21:54:45.100508+00:00"}
```

### `python3 -m wayfinder search saas --limit 5 --no-color`

Exit code: `0`

Representative result:

```text
1. gracp/saas-generator | github | market research SaaS ideas
2. marcoETmx/SaaS-Studio | github | market research SaaS ideas
3. sinan-mohammed/AI-SaaS-Idea-Validator | github | market research SaaS ideas
4. SaaS Company Uses Customer Pain Points for Content Creation Ideas | hackernews | founder-pain
5. ruanxinyang/micro-saas-validator | github | market research SaaS ideas
```

### `python3 -m wayfinder opportunities --limit 5 --no-color`

Exit code: `0`

Representative result:

```text
1. Leverage reddit-research-mcp | score=58.95 | Codex Foundry operator
2. Inspect lefttree/reddit-pain-points for leverage | score=57.9 | Wayfinder operator
3. Inspect calvinrodrigues500/product-hunter for leverage | score=57.9 | Wayfinder operator
4. Inspect rizkiwijanarko/KickUp for leverage | score=56.7 | Wayfinder operator
5. Inspect PhumudzoSly/ray for leverage | score=55.75 | Wayfinder operator
```

### `python3 -m wayfinder stats --no-color`

Exit code: `0`

Output:

```text
signals: 67
products: 37
opportunities: 37
ingest_runs: 3
source_activity:
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T21:54:44.989038+00:00 health=ok
  hackernews: signals=30 opportunities=0 last_ingest_at=2026-05-18T21:54:42.265563+00:00 health=ok
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T21:54:40.005078+00:00 health=ok
```

## Conclusion

- The `WRK-154` release gate is no longer blocked by an open GitHub PR. PR `#108` is already merged into `project/wayfinder`.
- GitHub currently reports zero open pull requests targeting `project/wayfinder`.
- The project branch remains healthy after that merge: the configured live ingest, search, opportunities, and stats smoke paths all pass in this workspace.
