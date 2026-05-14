# Wayfinder Architecture

Wayfinder is a local-first product intelligence pipeline for Codex Foundry. Its job is to collect public, token-free research signals on a schedule, normalize them, store them in a searchable database, and make the resulting evidence available to Codex, Hermes, and the operator when discussing what to build next.

## Principles

- Daily ingestion does not call LLMs.
- Every source is an adapter with the same contract.
- Evidence is stored before interpretation.
- SQLite FTS is the first search layer; vector search is optional later.
- Paid or fragile sources are disabled until reviewed.
- Sources move through explicit safety states before unattended cron use.

## Flow

1. Source adapters collect raw public records.
2. Records normalize into `signals`, `products`, or `opportunities`.
3. Fingerprints deduplicate inserts, and opportunity upserts refresh deterministic scores in place.
4. Search, ranking, and dashboard read from SQLite.
5. LLM-generated briefs are interactive/user-triggered, not cron defaults.

## Adapter Contract

Each adapter exposes:

- `healthcheck()` to confirm availability.
- `collect()` to fetch raw records.
- `normalize(raw)` to emit normalized records.
- `fingerprint(record)` to produce a stable dedupe key.

Adapters may read API keys from environment variables, but v1 sources should work without secrets.

## Source Safety

Every configured source includes a review policy with:

- `status`: `enabled`, `dry-run-only`, `needs-review`, or `disabled`
- `risk.credentials`
- `risk.terms`
- `risk.rate_limits`
- `risk.scraping`
- `risk.pii_user_generated_content`
- `risk.hosted_dependencies`

`sources list --health` is the operator review surface for these fields. `ingest --all` only runs sources approved for the current mode:

- normal ingest: `enabled`
- dry-run ingest: `enabled` and `dry-run-only`

Sources marked `needs-review` or `disabled` are never included in unattended `ingest --all`. A source is only cron-ready once its risk fields have been reviewed and its status is promoted to `enabled`.

## Storage

SQLite database:

- `signals`: public evidence from forums, repos, issues, reviews, and pages.
- `products`: product/app/SaaS records.
- `opportunities`: promoted ideas or imported opportunity records.
- `opportunities.opportunity_score`, `score_components_json`, and `scored_at`: persisted deterministic ranking state.
- `ingest_runs`: audit of adapter runs.
- `signals_fts`: full-text search over signal title/body/source URL.

## Ranking

Opportunity ranking is deterministic and local-only. A score is computed from configurable weights in `wayfinder.yaml` across five components:

- evidence count
- freshness
- monetization signal
- source quality
- build fit

The ingest path computes the score on insert/update, and the CLI `score` command can rescore the existing `opportunities` table without creating duplicate rows.

## UI

The v1 web UI is intentionally small:

- dashboard with recent signals and counts
- search page
- products page
- opportunities page

The CLI remains the primary automation surface.
