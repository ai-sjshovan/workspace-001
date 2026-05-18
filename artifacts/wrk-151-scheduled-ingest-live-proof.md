# WRK-151 Scheduled Ingest Live Proof

Acceptance evidence for `WRK-151` captured from the active `project/wayfinder` branch on `2026-05-18`.

## Scope

This task verified the existing production `scheduled-ingest` path only. No implementation changes were staged beyond this evidence artifact.

## Config and source health

The active config already keeps the unattended live path enabled:

```yaml
sources:
  hackernews:
    status: enabled
    kind: hackernews
  github:
    status: enabled
    kind: github

cron:
  enabled: true
  schedule: daily
  token_free: true
```

Command:

```text
python3 -m wayfinder --no-color sources list --health
```

Exit code: `0`

Relevant output:

```text
hackernews status=enabled kind=hackernews credentials=none terms=public-api-allowed rate_limits=low-volume-search scraping=api-search pii_ugc=reviewed-story-metadata hosted_dependencies=algolia-hn-api
  review=approved unattended=eligible why=Approved for unattended low-volume Algolia search using the configured story-only queries; normal and scheduled ingest use the live official endpoint while fixture-backed dry runs remain available for diagnostics.
github status=enabled kind=github credentials=none terms=public-api-allowed rate_limits=low-volume-public-search scraping=official-api pii_ugc=low-public-repo-metadata hosted_dependencies=github-public-api
  review=approved unattended=eligible why=Approved for daily anonymous public repository search at the configured low query volume; dry runs stay fixture-backed for diagnostics while scheduled and normal ingest use the live official API.
```

## Live unattended run

Command:

```text
python3 -m wayfinder --no-color scheduled-ingest
```

Exit code: `0`

Command output from the verified run:

```text
scheduled-ingest: sources=3 approved=3 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T19:25:25.438265+00:00
hackernews: raw=30 searchable_rows=30 inserted signals=30 products=0 opportunities=0
hackernews: searchable_rows_total=30 last_ingest_at=2026-05-18T19:25:28.568430+00:00
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T19:25:31.759658+00:00
scheduled-ingest: succeeded=3 skipped=0 failed=0 inserted_searchable_rows=67 inserted_signals=67 inserted_products=37 inserted_opportunities=37 duration_ms=5536.44 token_free=true llm_tokens=0
```

This run used the default unattended command with no `--dry-run` and no `--allow-disabled`.

## Operator-visible follow-through

Scheduler-ready recurrence command from the same checkout:

```text
@daily cd /mnt/d/AI/codex-foundry/workspace/tasks/WRK-151 && /usr/bin/python3 -m wayfinder --config /mnt/d/AI/codex-foundry/workspace/tasks/WRK-151/wayfinder.yaml --no-color scheduled-ingest >> /mnt/d/AI/codex-foundry/workspace/tasks/WRK-151/logs/wayfinder-cron.log 2>&1
```

Search output after the live run:

```text
1. gracp/saas-generator | github | market research SaaS ideas
2. marcoETmx/SaaS-Studio | github | market research SaaS ideas
3. sinan-mohammed/AI-SaaS-Idea-Validator | github | market research SaaS ideas
4. SaaS Company Uses Customer Pain Points for Content Creation Ideas | hackernews | founder-pain
5. ruanxinyang/micro-saas-validator | github | market research SaaS ideas
```

Opportunity output after the live run:

```text
1. Leverage reddit-research-mcp | score=58.95 | Codex Foundry operator
2. Inspect lefttree/reddit-pain-points for leverage | score=57.9 | Wayfinder operator
3. Inspect calvinrodrigues500/product-hunter for leverage | score=57.9 | Wayfinder operator
4. Inspect rizkiwijanarko/KickUp for leverage | score=56.7 | Wayfinder operator
5. Inspect PhumudzoSly/ray for leverage | score=55.75 | Wayfinder operator
```

Stats output after the same run:

```text
signals: 67
products: 37
opportunities: 37
ingest_runs: 3
source_activity:
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T19:25:31.759658+00:00 health=ok
  hackernews: signals=30 opportunities=0 last_ingest_at=2026-05-18T19:25:28.568430+00:00 health=ok
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T19:25:25.438265+00:00 health=ok
```

## Audit evidence

Tail from `logs/wayfinder-audit.log` immediately after the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 3, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T19:25:25.379573+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 64.651, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T19:25:25.446274+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 2230.997, "inserted_opportunities": 0, "inserted_products": 0, "inserted_searchable_rows": 30, "inserted_signals": 30, "llm_tokens": 0, "normalized": 30, "raw_records": 30, "source": "hackernews", "token_free": true, "ts": "2026-05-18T19:25:28.581495+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 3181.326, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T19:25:31.783200+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 3, "approved_sources": 3, "duration_ms": 5536.44, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 67, "inserted_signals": 67, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 0, "source_count": 3, "token_free": true, "ts": "2026-05-18T19:25:31.809279+00:00"}
```

## Acceptance mapping

- The unattended production path ran directly through `python3 -m wayfinder --no-color scheduled-ingest` without `--dry-run`.
- The approved live hosted sources `hackernews` and `github` both executed on the real source path and inserted searchable rows.
- Operator-visible output now exists across source health, scheduled-ingest stdout, `schedule-command`, search, opportunities, stats, and the audit log.
- The audit trail preserves source counts, per-source outcomes, duration, `token_free=true`, and `llm_tokens=0`.
