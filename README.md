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
python3 -m wayfinder scheduled-ingest --allow-disabled
python3 -m wayfinder ingest --source hackernews --dry-run
python3 -m wayfinder search "reddit pain"
python3 -m wayfinder products --limit 20
python3 -m wayfinder opportunities --limit 20
python3 -m wayfinder score --limit 10
python3 -m wayfinder export --min-score 40 --source oss-ledger
python3 -m wayfinder stats
python3 -m wayfinder serve --port 8766
```

## Paths

- Config: `wayfinder.yaml`
- Architecture: `docs/architecture.md`
- Source review checklist: `docs/source-review-checklist.md`
- OSS source ledger: `research/open-source-intel-ledger.yaml`
- SQLite database: `.ai-state/wayfinder/wayfinder.db`
- Audit log: `logs/wayfinder-audit.log`
- Repo-local CLI: `python3 -m wayfinder`
- Foundry target mapping: `.codex-foundry/TARGET_REPO` -> `workspace-001` on `project/wayfinder`

## Verified Baseline

Verified in `workspace-001` on the configured `project/wayfinder` branch.

- Entrypoints: repo-local CLI via `python3 -m wayfinder` and the read-only dashboard via `python3 -m wayfinder serve --port 8766`
- Confirmed routes: `/` renders the dashboard and `/health` returns `{"ok": true, "service": "wayfinder"}`
- Confirmed CLI smoke path: `sources list --health`, `ingest --source oss-ledger`, `search`, `products`, `opportunities`, and `stats`
- Current approved ingest baseline: `oss-ledger` is enabled; `hackernews` is `dry-run-only`; `github` is `dry-run-only`
- Follow-on adapter gap: only `oss-ledger` is approved for normal writes today, so Hacker News and GitHub adapter work still needs safety/rate-limit promotion before unattended ingest
- Setup drift to note: `.codex-foundry/REPO_PROFILE.md` can lag `HEAD`; treat it as a map and verify exact files before follow-on implementation

The sample `search "reddit pain"` command is still a valid CLI smoke check, but it may return no rows after `oss-ledger` ingest alone because that phrase is not guaranteed to exist in the curated local ledger.

## Adapter Contract

Each adapter implements three methods:

- `healthcheck()` reports whether the source is configured.
- `collect()` fetches raw records without using tokens or authenticated API access.
- `normalize()` converts raw records into `Signal`, `ProductIntel`, and `Opportunity` records.

New sources should start as `dry-run-only` adapters before being enabled in recurring cron. Sources that require credentials, scrape pages, or collect user-generated content need an explicit safety review before unattended collection.

The GitHub adapter stays anonymous by default, even if `GITHUB_TOKEN` is present in the environment. To intentionally enable documented credentials for manual testing, set `allow_credentials: true` on the `github` source and then provide either `token:` or `token_env:`. If GitHub returns a rate-limit response, Wayfinder surfaces the HTTP status plus the reset time when GitHub provides it so the adapter can fail clearly without guessing.

## Scheduled Ingest

The daily runner is `python3 -m wayfinder scheduled-ingest`. It is intentionally guarded by `cron.enabled: false` in `wayfinder.yaml`, so unattended ingest stays off until someone explicitly approves it.

Manual validation while the guard is off:

```bash
python3 -m wayfinder scheduled-ingest --allow-disabled
```

Behavior:

- runs approved sources only (`status: enabled`)
- skips `dry-run-only`, `needs-review`, and `disabled` sources with audit log entries
- writes source-level counts, duration, and error details to `logs/wayfinder-audit.log`
- records `token_free=true` and `llm_tokens=0` for the scheduled run path

Example cron entry, left disabled by default:

```cron
# Daily Wayfinder ingest; remove the leading # only after cron.enabled is set to true
# 17 4 * * * cd /path/to/workspace-001 && /usr/bin/python3 -m wayfinder scheduled-ingest >> logs/wayfinder-cron.log 2>&1
```

## Source Safety

Promotion and review steps for unattended ingest live in `docs/source-review-checklist.md`.

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

## Task Draft Export

`python3 -m wayfinder export` turns stored opportunities into deterministic Markdown task drafts for operator review. Filters are optional and composable:

- `--min-score` keeps only opportunities at or above a threshold.
- `--category` keeps only a matching opportunity category.
- `--source` keeps only a matching opportunity source.

The export is intentionally read-only: it prints editable Markdown, does not auto-stage work, does not call LLMs, and does not create Linear issues.

## Current Sources

- `oss-ledger`: `enabled`, curated open-source source/tool ledger, safe for offline ingest.
- `hackernews`: `dry-run-only`, public HN Algolia search with user-generated content and external rate-limit considerations.
- `github`: `dry-run-only`, anonymous public GitHub repository search with hosted dependency and API-rate review still required before unattended ingest.

Reddit, app-store reviews, Product Hunt, and broader crawl/search sources are deferred until safety and terms review.

## Web Smoke

Start the dashboard with `python3 -m wayfinder serve --port 8766`, then validate:

- `/`
- `/health`
- `/search?q=reddit`
- `/api/search?q=reddit`
- `/products`
- `/opportunities`
