# Wayfinder

Wayfinder is the local-first research pipeline for finding product problems, SaaS opportunities, competitor patterns, and source material we can use when deciding what Codex Foundry should build next.

The first version is intentionally simple:

- deterministic collection and storage, with no LLM calls during ingest
- source adapters normalize raw records into SQLite tables
- SQLite FTS powers local search before we add embeddings or a vector database
- a small read-only dashboard makes the database browsable
- external sources are explicit in `wayfinder.yaml`
- external engines are registered separately from sources

## Current Acceptance Target

Wayfinder is currently operating against the V1 acceptance target already present on `project/wayfinder`: deterministic, token-free ingest; explicit source-safety controls; read-only browse/detail/export surfaces; and the existing CLI and web smoke checks.

This slice adds V2 foundation only where it supports the existing internal API/CLI tool shape: standard pip packaging plus a separate external-engine registry surface. It does not add tmux workflow, dashboard polish, paid services, or required LLM execution.

## Commands

From the repository root:

```bash
python3 -m pip install --user --break-system-packages -e .
wayfinder --help
python3 -m wayfinder sources list --health
python3 -m wayfinder engines list --no-color
python3 -m wayfinder ingest --source oss-ledger
python3 -m wayfinder scheduled-ingest
python3 -m wayfinder ingest --source github
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
- Engineering practices: `docs/engineering-practices.md`
- Source review checklist: `docs/source-review-checklist.md`
- OSS source ledger: `research/open-source-intel-ledger.yaml`
- SQLite database: `.ai-state/wayfinder/wayfinder.db`
- Audit log: `logs/wayfinder-audit.log`
- Installed CLI: `wayfinder`
- Repo-local CLI: `python3 -m wayfinder`
- Foundry target mapping: `.codex-foundry/TARGET_REPO` -> `workspace-001` on `project/wayfinder`

## Verified Baseline

Verified in `workspace-001` on the configured `project/wayfinder` branch.

- Entrypoints: repo-local CLI via `python3 -m wayfinder` and the read-only dashboard via `python3 -m wayfinder serve --port 8766`
- Packaging: editable installs expose the same CLI as `wayfinder ...` through `pyproject.toml`
- Confirmed routes: `/` renders the dashboard and `/health` returns a readiness payload with `ok`, `service`, `config`, `database`, and `storage_path`
- Confirmed CLI smoke path from the repo root: `python3 -m wayfinder sources list --health`, `python3 -m wayfinder scheduled-ingest`, `python3 -m wayfinder search saas`, `python3 -m wayfinder products --limit 20`, `python3 -m wayfinder opportunities --limit 20`, and `python3 -m wayfinder stats`
- Current approved ingest baseline: `oss-ledger`, `hackernews`, and `github` are enabled for unattended ingest
- Daily ingest now includes real anonymous GitHub public-search and Hacker News Algolia sources while preserving fixture-backed dry runs for diagnostics
- Setup drift to note: `.codex-foundry/REPO_PROFILE.md` can lag `HEAD`; treat it as a map and verify exact files before follow-on implementation

The sample `search "reddit pain"` command remains useful for ad hoc exploration, but the supported repo-root smoke example is `python3 -m wayfinder search saas`. After a successful scheduled ingest, it should return stored rows from the approved live GitHub source.

## Adapter Contract

Each adapter implements three methods:

- `healthcheck()` reports whether the source is configured.
- `collect()` fetches raw records without using tokens or authenticated API access.
- `normalize()` converts raw records into `Signal`, `ProductIntel`, and `Opportunity` records.

New sources should start as `dry-run-only` adapters before being enabled in recurring cron. Sources that require credentials, scrape pages, or collect user-generated content need an explicit safety review before unattended collection.

## Engine Registry

Wayfinder now keeps external engines in a separate `engines:` section in `wayfinder.yaml`.

- Engines are sensors, not copied core logic.
- Engines are inspected independently from approved ingest sources.
- The current foundation only lists configured engines and reports importability.
- Registry checks stay deterministic and local-only.

Use:

```bash
python3 -m wayfinder engines list --no-color
```

The approved unattended Hacker News configuration in `wayfinder.yaml` is:

- `status: enabled`
- `kind: hackernews`
- `queries`: `SaaS pain points`, `startup idea validation`, and `competitor analysis tool`, all constrained to `tags: story` with `hits_per_page: 10`
- `hits_per_query: 10`
- `risk.credentials: none`
- `risk.terms: public-api-allowed`
- `risk.rate_limits: low-volume-search`
- `risk.scraping: api-search`
- `risk.pii_user_generated_content: reviewed-story-metadata`
- `risk.hosted_dependencies: algolia-hn-api`

Normal and scheduled ingest drop `fixture_path` for the live run path, while manual diagnostics can still use the fixture-backed `--dry-run` mode.

The GitHub adapter stays anonymous by default, even if `GITHUB_TOKEN` is present in the environment. To intentionally enable documented credentials for manual testing, set `allow_credentials: true` on the `github` source and then provide either `token:` or `token_env:`. If GitHub returns a rate-limit response, Wayfinder surfaces the HTTP status plus the reset time when GitHub provides it so the adapter can fail clearly without guessing.

## Scheduled Ingest

The exact daily production ingest command is `python3 -m wayfinder --no-color scheduled-ingest`. In the current repo config, `cron.enabled: true` and `cron.schedule: daily` keep that operator-runnable daily path active for approved sources only.

Behavior:

- runs approved sources only (`status: enabled`)
- skips `dry-run-only`, `needs-review`, and `disabled` sources with audit log entries
- writes source-level counts, duration, and error details to `logs/wayfinder-audit.log`
- records `token_free=true` and `llm_tokens=0` for the scheduled run path

The scheduler wiring should come from the live helper output, not a copied historical cron line:

```bash
python3 -m wayfinder --no-color schedule-command
```

Current output shape:

```cron
@daily cd /path/to/workspace-001 && /usr/bin/python3 -m wayfinder --config /path/to/workspace-001/wayfinder.yaml --no-color scheduled-ingest >> /path/to/workspace-001/logs/wayfinder-cron.log 2>&1
```

Use that helper to derive the exact recurrence line for the current checkout, interpreter, config path, and log path instead of copying an older artifact from a different workspace. Recurrence is triggered when cron or another scheduler runs the emitted line, which `cd`s into the repo and invokes the approved non-dry-run `scheduled-ingest` path.

## Daily Operator Runbook

Use these commands from the repository root when checking or running the daily ingest.

Print the exact recurrence command for this checkout:

```bash
python3 -m wayfinder --no-color schedule-command
```

Run or confirm the scheduled path:

```bash
python3 -m wayfinder --no-color scheduled-ingest
```

Verify source health before or after the run:

```bash
python3 -m wayfinder --no-color sources list --health
```

The health output includes the latest persisted ingest evidence for each source, including `last_ingest_at` and the most recent inserted counts.

Check the latest aggregate database counts and per-source last-ingest timestamps:

```bash
python3 -m wayfinder --no-color stats
```

Inspect the most recent scheduled-ingest audit events, including started, skipped, per-source, error, and finished records:

```bash
tail -n 20 logs/wayfinder-audit.log
```

If the daily recurrence fails, check these first:

- rerun `python3 -m wayfinder --no-color schedule-command` and confirm the installed scheduler still matches the emitted line
- run `python3 -m wayfinder --no-color scheduled-ingest` from the repo root to confirm the production path still starts cleanly
- inspect `tail -n 20 logs/wayfinder-audit.log` for `wayfinder_scheduled_ingest_error`, skipped-source reasons, or a missing `wayfinder_scheduled_ingest_finished`
- verify `python3 -m wayfinder --no-color sources list --health` still shows the intended sources as approved for unattended runs

Check the latest persisted ingest-run rows for exact inserted counts by source:

```bash
python3 - <<'PY'
import sqlite3

conn = sqlite3.connect(".ai-state/wayfinder/wayfinder.db")
conn.row_factory = sqlite3.Row
for row in conn.execute(
    """
    SELECT source, status, collected, inserted_searchable_rows, inserted_signals, inserted_products,
           inserted_opportunities, started_at, finished_at
    FROM ingest_runs
    ORDER BY id DESC
    LIMIT 5
    """
):
    print(dict(row))
conn.close()
PY
```

Filter the audit log down to failures only:

```bash
rg "wayfinder_scheduled_ingest_error|wayfinder_ingest_error" logs/wayfinder-audit.log || true
```

Confirm the unattended path stayed deterministic and spent no LLM tokens:

```bash
rg '"action": "wayfinder_scheduled_ingest_(started|source|skipped|finished|error)"|"token_free": true|"llm_tokens": 0' logs/wayfinder-audit.log
```

The unattended ingest boundary stays unchanged: the daily path is deterministic, records `token_free=true`, records `llm_tokens=0`, and does not spend LLM tokens.

## Daily Ingest Acceptance Evidence

Use this checklist when QA needs to verify the live daily-ingest gate without redoing the separate dashboard freshness work.

- `python3 -m wayfinder --no-color schedule-command` prints the scheduler-ready `@daily ... scheduled-ingest >> .../logs/wayfinder-cron.log 2>&1` line for the current checkout.
- `python3 -m wayfinder --no-color scheduled-ingest` runs directly, without `--dry-run` and without `--allow-disabled`, and prints the top-line source counts plus final `inserted_searchable_rows`, `inserted_signals`, `inserted_products`, `inserted_opportunities`, `duration_ms`, `token_free=true`, and `llm_tokens=0`.
- `python3 -m wayfinder --no-color sources list --health` shows the current source posture and latest per-source persisted run evidence, including `review=approved`, `unattended=eligible`, `latest_run=live`, `last_ingest_at`, and inserted totals.
- `python3 -m wayfinder --no-color stats` confirms the aggregate stored counts plus `source_activity` timestamps after the same run.
- `tail -n 20 logs/wayfinder-audit.log` shows the matching `wayfinder_scheduled_ingest_started`, `wayfinder_scheduled_ingest_source`, and `wayfinder_scheduled_ingest_finished` events for that run.

Pass criteria for the current live-source posture:

- `wayfinder.yaml` keeps `cron.enabled: true` and `cron.schedule: daily`.
- Approved sources remain `oss-ledger`, `hackernews`, and `github`; the daily path does not widen scope beyond those reviewed sources.
- The scheduled run preserves source safety and determinism: it stays token-free, records `llm_tokens=0`, and emits per-source counts and total duration in the audit trail.
- QA does not need to re-prove dashboard cards or page freshness here; the acceptance gate is the operator schedule command plus CLI and audit evidence above.

## Source Safety

Promotion and review steps for unattended ingest live in `docs/source-review-checklist.md`.

`python3 -m wayfinder sources list --health` is the operator-facing audit view for configured adapters. It prints `review=...`, `unattended=...`, and `why=...` summaries so approved, blocked, and pending-review sources are visibly distinct without inferring meaning from raw risk fields alone.

Each source carries a review status in `wayfinder.yaml`:

- `enabled`: approved for unattended ingest and eligible for the configured daily runner.
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

## Current Supported Sources

| Source | Adapter status | Recurring cron stance | Notes |
| --- | --- | --- | --- |
| `oss-ledger` | Healthy | Included in the configured daily run | Curated open-source source/tool ledger with offline local ingest. |
| `hackernews` | Healthy | Included in the configured daily run | Public HN Algolia story search is approved at the configured low volume with token-free live ingest and fixture-backed dry runs preserved for diagnostics. |
| `github` | Healthy | Included in the configured daily run | Anonymous public GitHub repository search at low daily volume, with fixture-backed dry runs preserved for diagnostics and the live official API used for normal ingest. |
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
