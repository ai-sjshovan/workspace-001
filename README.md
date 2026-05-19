# Wayfinder

Wayfinder is the local-first research pipeline for finding product problems, SaaS opportunities, competitor patterns, and source material we can use when deciding what Codex Foundry should build next.

The first version is intentionally simple:

- deterministic collection and storage, with no LLM calls during ingest
- source adapters normalize raw records into SQLite tables
- SQLite FTS powers local search before we add embeddings or a vector database
- a small read-only dashboard makes the database browsable
- external sources are explicit in `wayfinder.yaml`

## Current Acceptance Target

Wayfinder is currently operating against the V1 acceptance target already present on `project/wayfinder`: deterministic, token-free ingest; explicit source-safety controls; read-only browse/detail/export surfaces; and the existing CLI and web smoke checks.

V2 implementation work is not authorized by default. Unless an operator explicitly reopens the project for V2, the current branch should only preserve and clarify the V1 baseline rather than start a new feature slice.

## Commands

From the repository root:

```bash
python3 -m wayfinder sources list --health
python3 -m wayfinder scheduled-ingest
python3 -m wayfinder search leverage --limit 5
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
- Confirmed routes: `/` renders the dashboard and `/health` returns a readiness payload with `ok`, `service`, `config`, `database`, and `storage_path`
- Confirmed CLI smoke path from the repo root: `python3 -m wayfinder sources list --health`, `python3 -m wayfinder scheduled-ingest`, `python3 -m wayfinder search leverage --limit 5`, `python3 -m wayfinder products --limit 20`, `python3 -m wayfinder opportunities --limit 20`, and `python3 -m wayfinder stats`
- Current approved ingest baseline: `oss-ledger` is enabled; `hackernews` is `dry-run-only`; `github` is `dry-run-only`
- Follow-on adapter gap: only `oss-ledger` is approved for unattended writes today, so Hacker News and GitHub still need safety/rate-limit promotion before they can join the daily run
- Setup drift to note: `.codex-foundry/REPO_PROFILE.md` can lag `HEAD`; treat it as a map and verify exact files before follow-on implementation

Use `python3 -m wayfinder search leverage --limit 5` or `python3 -m wayfinder search pain --limit 5` after a scheduled run when you want to confirm the default `oss-ledger` dataset is actually searchable.

## Adapter Contract

Each adapter implements three methods:

- `healthcheck()` reports whether the source is configured.
- `collect()` fetches raw records without using tokens or authenticated API access.
- `normalize()` converts raw records into `Signal`, `ProductIntel`, and `Opportunity` records.

New sources should start as `dry-run-only` adapters before being enabled in recurring cron. Sources that require credentials, scrape pages, or collect user-generated content need an explicit safety review before unattended collection.

The GitHub adapter stays anonymous by default, even if `GITHUB_TOKEN` is present in the environment. To intentionally enable documented credentials for manual testing, set `allow_credentials: true` on the `github` source and then provide either `token:` or `token_env:`. If GitHub returns a rate-limit response, Wayfinder surfaces the HTTP status plus the reset time when GitHub provides it so the adapter can fail clearly without guessing.

## Scheduled Ingest

The production daily runner is `python3 -m wayfinder scheduled-ingest`. In the checked-in v1 config, this command is approved for unattended use because it only runs sources with `status: enabled`, and the default approved set is currently just `oss-ledger`.

Daily operator workflow:

```bash
python3 -m wayfinder sources list --health --no-color
python3 -m wayfinder scheduled-ingest --no-color
python3 -m wayfinder stats --no-color
```

What the scheduled runner does:

- runs approved sources only (`status: enabled`)
- skips `dry-run-only`, `needs-review`, and `disabled` sources with audit log entries
- writes source-level counts, duration, and error details to `logs/wayfinder-audit.log`
- writes records into `.ai-state/wayfinder/wayfinder.db`
- records `token_free=true` and `llm_tokens=0` for the scheduled run path

How to verify the run was real and stored:

- `python3 -m wayfinder stats --no-color` should show non-zero `signals`, `products`, `opportunities`, and `ingest_runs` after the daily run.
- `python3 -m wayfinder search leverage --limit 5 --no-color` or `python3 -m wayfinder search pain --limit 5 --no-color` should return stored `oss-ledger` records rather than `No rows found.`.
- `python3 -m wayfinder opportunities --limit 5 --no-color` should show scored rows sourced from `oss-ledger`.
- `tail -n 20 logs/wayfinder-audit.log` should show the scheduled-ingest event history and any blocked/manual-only sources.

The default approved run stays token-free and local-first. It does not enable paid sources, credential-required sources, or manual-review sources by default.

Minimal cron example:

```cron
17 4 * * * cd /path/to/workspace-001 && /usr/bin/python3 -m wayfinder scheduled-ingest --no-color >> logs/wayfinder-cron.log 2>&1
```

Minimal systemd service/timer example:

```ini
# /etc/systemd/system/wayfinder-daily.service
[Unit]
Description=Wayfinder daily ingest

[Service]
Type=oneshot
WorkingDirectory=/path/to/workspace-001
ExecStart=/usr/bin/python3 -m wayfinder scheduled-ingest --no-color

# /etc/systemd/system/wayfinder-daily.timer
[Unit]
Description=Run Wayfinder daily ingest

[Timer]
OnCalendar=*-*-* 04:17:00
Persistent=true

[Install]
WantedBy=timers.target
```

Foundry-compatible operator note:

- Keep the schedule pointed at the repo root and use the repo-local CLI entrypoint `python3 -m wayfinder`.
- If you need to pause daily ingest, set `cron.enabled: false` in `wayfinder.yaml` rather than editing source policy states.
- If you need to review a candidate source manually, use `python3 -m wayfinder ingest --source <name> --dry-run`; that path is for source review and tests, not the production daily run.

## Source Safety

Promotion and review steps for unattended ingest live in `docs/source-review-checklist.md`.

`python3 -m wayfinder sources list --health` is the operator-facing audit view for configured adapters. It prints `review=...`, `unattended=...`, and `why=...` summaries so approved, blocked, and pending-review sources are visibly distinct without inferring meaning from raw risk fields alone.

Each source carries a review status in `wayfinder.yaml`:

- `enabled`: approved for unattended ingest and eligible for the production daily run.
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

A source can move to `enabled` for daily scheduling only after its terms, rate limits, collection method, hosted dependencies, and user-data exposure are reviewed and the unattended behavior is considered acceptable.

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

## Current Supported Sources

| Source | Adapter status | Recurring cron stance | Notes |
| --- | --- | --- | --- |
| `oss-ledger` | Healthy | Safe for recurring cron in the checked-in production config | Curated open-source source/tool ledger with offline local ingest. |
| `hackernews` | `dry-run-only` | Not safe for recurring cron yet | Public HN Algolia search with user-generated content and external rate-limit review still required. |
| `github` | `dry-run-only` | Not safe for recurring cron yet | Anonymous public GitHub repository search; hosted dependency and API-rate review still required before unattended ingest. |
| Reddit / app-store reviews / Product Hunt / broader crawl/search sources | Deferred | Do not schedule | Out of the current Wayfinder scope until safety and terms review are complete. |

The source review checklist in `docs/source-review-checklist.md` is the canonical promotion guide for moving a source from manual testing into unattended cron eligibility.

New sources do not enter unattended ingest by default. Add a candidate source as `dry-run-only`, `needs-review`, or `disabled`, record the risk fields and notes in `wayfinder.yaml`, and promote it to `enabled` only after the checklist approves unattended use. If the review is not acceptable, keep it out of recurring ingest and document the rejection reason in `notes`.

## Web Smoke

Start the dashboard with `python3 -m wayfinder serve --port 8766`, then validate:

- `/`
- `/health`
- `/search?q=reddit`
- `/api/search?q=reddit`
- `/products`
- `/opportunities`
