# Wayfinder

Wayfinder is the local-first research pipeline for finding product problems, SaaS opportunities, competitor patterns, and source material we can use when deciding what Codex Foundry should build next.

The first version is intentionally simple:

- deterministic collection and storage, with no LLM calls during ingest
- source adapters normalize raw records into SQLite tables
- SQLite FTS powers local search before we add embeddings or a vector database
- a small read-only dashboard makes the database browsable
- external sources are explicit in `wayfinder.yaml`

## Commands

From the repository root:

```bash
python3 -m wayfinder sources list --health
python3 -m wayfinder ingest --source oss-ledger
python3 -m wayfinder ingest --source hackernews --dry-run
python3 -m wayfinder search "reddit pain"
python3 -m wayfinder products --limit 20
python3 -m wayfinder opportunities --limit 20
python3 -m wayfinder score --limit 10
python3 -m wayfinder stats
python3 -m wayfinder serve --port 8766
```

## Paths

- Config: `wayfinder.yaml`
- Architecture: `docs/architecture.md`
- OSS source ledger: `research/open-source-intel-ledger.yaml`
- SQLite database: `.ai-state/wayfinder/wayfinder.db`
- Audit log: `logs/wayfinder-audit.log`
- Repo-local CLI: `python3 -m wayfinder`

## Adapter Contract

Each adapter implements three methods:

- `healthcheck()` reports whether the source is configured.
- `collect()` fetches raw records without using tokens.
- `normalize()` converts raw records into `Signal`, `ProductIntel`, and `Opportunity` records.

New sources should start as `dry-run-only` adapters before being enabled in recurring cron. Sources that require credentials, scrape pages, or collect user-generated content need an explicit safety review before unattended collection.

## Source Safety

Each source carries a review status in `wayfinder.yaml`:

- `enabled`: approved for unattended ingest and eligible for cron once the broader cron switch is enabled.
- `dry-run-only`: safe to test manually, but must not write unattended data without a follow-up review.
- `needs-review`: visible in source health output but excluded from `ingest --all`.
- `disabled`: intentionally off and excluded from `ingest --all`.

Each source should also document these risk fields before promotion to cron:

- `credentials`
- `terms`
- `rate_limits`
- `scraping`
- `pii_user_generated_content`
- `hosted_dependencies`

A source can move to `enabled` for cron only after its terms, rate limits, collection method, hosted dependencies, and user-data exposure are reviewed and the unattended behavior is considered acceptable.

## Opportunity Scoring

Wayfinder ranks opportunities with a deterministic weighted model configured under `scoring:` in `wayfinder.yaml`. The current score is a weighted blend of:

- `evidence_count`: normalizes direct evidence volume.
- `freshness`: favors recently collected opportunities.
- `monetization_signal`: scores monetization-oriented keywords and penalizes dependency-heavy language.
- `source_quality`: rewards clearer licensing, useful outputs, and lower risk.
- `build_fit`: rewards lower complexity plus better reuse/code-fit signals.

`python3 -m wayfinder score` rescales existing rows in place and prints ranked opportunities with per-component contributions. Re-running ingest updates the existing opportunity row by fingerprint and refreshes the deterministic score instead of inserting a duplicate.

## Current Sources

- `oss-ledger`: `enabled`, curated open-source source/tool ledger, safe for offline ingest.
- `hackernews`: `needs-review`, public HN Algolia search with user-generated content and external rate-limit considerations.
- `github`: `dry-run-only`, public GitHub repository search with hosted dependency and API-rate review still required before unattended ingest.

Reddit, app-store reviews, Product Hunt, and broader crawl/search sources are deferred until safety and terms review.

## Web Smoke

Start the dashboard with `python3 -m wayfinder serve --port 8766`, then validate:

- `/`
- `/health`
- `/search?q=reddit`
- `/api/search?q=reddit`
- `/products`
- `/opportunities`
