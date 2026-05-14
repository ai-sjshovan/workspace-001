# Wayfinder Architecture

Wayfinder is a local-first product intelligence pipeline for Codex Foundry. Its job is to collect public, token-free research signals on a schedule, normalize them, store them in a searchable database, and make the resulting evidence available to Codex, Hermes, and the operator when discussing what to build next.

## Principles

- Daily ingestion does not call LLMs.
- Every source is an adapter with the same contract.
- Evidence is stored before interpretation.
- SQLite FTS is the first search layer; vector search is optional later.
- Paid or fragile sources are disabled until reviewed.

## Flow

1. Source adapters collect raw public records.
2. Records normalize into `signals`, `products`, or `opportunities`.
3. Fingerprints deduplicate inserts.
4. Search and dashboard read from SQLite.
5. LLM-generated briefs are interactive/user-triggered, not cron defaults.

## Adapter Contract

Each adapter exposes:

- `healthcheck()` to confirm availability.
- `collect()` to fetch raw records.
- `normalize(raw)` to emit normalized records.
- `fingerprint(record)` to produce a stable dedupe key.

Adapters may read API keys from environment variables, but v1 sources should work without secrets.

## Storage

SQLite database:

- `signals`: public evidence from forums, repos, issues, reviews, and pages.
- `products`: product/app/SaaS records.
- `opportunities`: promoted ideas or imported opportunity records.
- `ingest_runs`: audit of adapter runs.
- `signals_fts`: full-text search over signal title/body/source URL.

## UI

The v1 web UI is intentionally small:

- dashboard with recent signals and counts
- search page
- products page
- opportunities page

The CLI remains the primary automation surface.
