# WRK-149 Approved GitHub Unattended Ingest Proof

Acceptance evidence for `WRK-149` captured from the active `project/wayfinder` branch on `2026-05-18`.

## Config verification

`wayfinder.yaml` on the verified branch keeps the approved GitHub public-search source in the unattended daily path:

```yaml
sources:
  github:
    status: enabled
    kind: github
    notes: Approved for daily anonymous public repository search at the configured low query volume; dry runs stay fixture-backed for diagnostics while scheduled and normal ingest use the live official API.
    risk:
      credentials: none
      terms: public-api-allowed
      rate_limits: low-volume-public-search
      scraping: official-api
      pii_user_generated_content: low-public-repo-metadata
      hosted_dependencies: github-public-api

cron:
  enabled: true
  schedule: daily
  token_free: true
```

## Health and status output

Command:

```text
python3 -m wayfinder --no-color sources list --health
```

Exit code: `0`

Relevant output:

```text
github status=enabled kind=github credentials=none terms=public-api-allowed rate_limits=low-volume-public-search scraping=official-api pii_ugc=low-public-repo-metadata hosted_dependencies=github-public-api
  review=approved unattended=eligible why=Approved for daily anonymous public repository search at the configured low query volume; dry runs stay fixture-backed for diagnostics while scheduled and normal ingest use the live official API.
  notes=Approved for daily anonymous public repository search at the configured low query volume; dry runs stay fixture-backed for diagnostics while scheduled and normal ingest use the live official API.
  health=ok GitHub deterministic fixture configured with 3 queries via /mnt/d/AI/codex-foundry/workspace/tasks/WRK-149/research/github-sample.json
```

## Live unattended ingest

Command:

```text
python3 -m wayfinder --no-color scheduled-ingest
```

Exit code: `0`

Command output from the verified run:

```text
scheduled-ingest: sources=3 approved=2 token_free=true llm_tokens=0
oss-ledger: raw=8 searchable_rows=8 inserted signals=8 products=8 opportunities=8
oss-ledger: searchable_rows_total=8 last_ingest_at=2026-05-18T19:09:28.775642+00:00
hackernews: skipped status=dry-run-only
github: raw=29 searchable_rows=29 inserted signals=29 products=29 opportunities=29
github: searchable_rows_total=29 last_ingest_at=2026-05-18T19:09:32.173143+00:00
scheduled-ingest: succeeded=2 skipped=1 failed=0 inserted_searchable_rows=37 inserted_signals=37 inserted_products=37 inserted_opportunities=37 duration_ms=3486.933 token_free=true llm_tokens=0
```

The run used the default unattended path with no `--dry-run` and no `--allow-disabled`.

## Audit log outcome

Audit tail from `logs/wayfinder-audit.log` immediately after the same run:

```json
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 2, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T19:09:28.730183+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 51.61, "inserted_opportunities": 8, "inserted_products": 8, "inserted_searchable_rows": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T19:09:28.783460+00:00"}
{"action": "wayfinder_scheduled_ingest_skipped", "llm_tokens": 0, "reason": "source_not_approved_for_unattended_ingest", "source": "hackernews", "status": "dry-run-only", "token_free": true, "ts": "2026-05-18T19:09:28.803385+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 3389.106, "inserted_opportunities": 29, "inserted_products": 29, "inserted_searchable_rows": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T19:09:32.194417+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_source_count": 2, "approved_sources": 2, "duration_ms": 3486.933, "enabled": true, "failed_sources": 0, "inserted_opportunities": 37, "inserted_products": 37, "inserted_searchable_rows": 37, "inserted_signals": 37, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 1, "source_count": 3, "token_free": true, "ts": "2026-05-18T19:09:32.217953+00:00"}
```

## Acceptance mapping

- The approved GitHub public-search source is configured on the active project branch with `status: enabled` and `credentials: none`.
- The source is visible in health/status output as `review=approved` and `unattended=eligible`.
- The live ingest path used the source without `--dry-run` or `--allow-disabled` and wrote GitHub rows during `scheduled-ingest`.
- The audit output records the GitHub source outcome directly and preserves `token_free=true` plus `llm_tokens=0`.
