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

New sources should start as dry-run adapters before being enabled in recurring cron. Sources that require credentials, scrape pages, or collect user-generated content need an explicit safety review before unattended collection.

## Current Sources

- `oss-ledger`: curated open-source source/tool ledger, safe for offline ingest.
- `hackernews`: public HN Algolia search, useful for market and founder-problem chatter.
- `github`: public GitHub repository search, useful for open-source leverage and competitor/tool discovery.

Reddit, app-store reviews, Product Hunt, and broader crawl/search sources are deferred until safety and terms review.

## Web Smoke

Start the dashboard with `python3 -m wayfinder serve --port 8766`, then validate:

- `/`
- `/health`
- `/search?q=reddit`
- `/api/search?q=reddit`
- `/products`
- `/opportunities`
