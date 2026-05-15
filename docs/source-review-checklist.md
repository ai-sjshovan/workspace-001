# Wayfinder Source Review Checklist

Use this checklist before changing any source from `dry-run-only` to `enabled` for unattended cron ingest.

This guide is additive to the current source policies in `wayfinder.yaml`. It does not change the meaning of any policy field, and it does not override the default guardrail that keeps `cron.enabled: false` until unattended ingest is explicitly approved.

## Review Surfaces

- `wayfinder.yaml` is the source of truth for `status`, `notes`, and `risk.*` policy fields.
- `python3 -m wayfinder sources list --health` is the operator review surface for the configured source policies.
- The source catalog in `wayfinder/web.py` exposes the same safety metadata under `policy_status`, `risk`, and `unattended_cron`.
- `python3 -m wayfinder scheduled-ingest` is the unattended path and must stay blocked by `cron.enabled: false` until approval is complete.

## Current Adapter Status

Use this summary when deciding whether a source is safe for recurring cron today:

| Source | Current status | Recurring cron stance | Why |
| --- | --- | --- | --- |
| `oss-ledger` | Healthy | Safe for recurring cron after the separate `cron.enabled` switch is explicitly approved | Curated local ledger, no credentials, no hosted dependency, and risk fields are already reviewed. |
| `hackernews` | `dry-run-only` | Not safe for recurring cron yet | Manual dry runs are acceptable, but unattended live Algolia use still needs terms, rate-limit, and user-generated-content review. |
| `github` | `dry-run-only` | Not safe for recurring cron yet | Anonymous public search is acceptable for manual dry runs, but unattended API use still needs hosted-dependency and rate-limit review. |
| Reddit / app-store reviews / Product Hunt / broader crawl-search sources | Deferred | Do not add to recurring cron | These sources remain outside the current Wayfinder scope until source safety and terms review are completed. |

## Checklist

Review and record each item for the source being evaluated:

- Terms: confirm the source's terms allow this collection pattern, storage pattern, and unattended recurring use.
- Rate limits: confirm expected request volume, backoff expectations, and whether the configured query count is safe for recurring use.
- Scraping method: confirm whether the adapter uses a local file, an official API, search API, or page scraping, and verify that the method is acceptable for unattended use.
- Credential use: confirm whether secrets are required, whether token-free mode is possible, and whether unattended runs would introduce credential handling or secret-rotation risk.
- User-generated-content exposure: confirm whether the source carries comments, posts, reviews, or other user-authored text and whether that exposure is acceptable for unattended ingest.
- Hosted dependencies: confirm whether the source depends on third-party availability, hosted APIs, or external search infrastructure that could fail or change behavior in cron.
- Notes quality: update `notes` so the next reviewer can see why the current status is appropriate and what remains to be reviewed.

## Interpreting Safety Metadata

`wayfinder.yaml` keeps the canonical policy values for each source:

- `status`: promotion gate for ingest modes.
- `risk.credentials`: whether unattended use would rely on secrets or can remain token-free.
- `risk.terms`: whether terms have been reviewed or still need review.
- `risk.rate_limits`: whether recurring access volume is known and acceptable.
- `risk.scraping`: how collection happens, such as `none`, `official-api`, or `api-search`.
- `risk.pii_user_generated_content`: expected exposure to user-authored or potentially sensitive public content.
- `risk.hosted_dependencies`: third-party systems the source depends on for unattended runs.

The web source catalog mirrors these values:

- `policy_status` matches the source `status`.
- `risk.*` mirrors the configured risk fields for the selected source.
- `unattended_cron.eligible` is true only when `status: enabled`.
- `unattended_cron.global_cron_enabled` reflects the top-level `cron.enabled` switch.
- `unattended_cron.token_free_default` reflects the top-level `cron.token_free` setting.

## Promotion Rules

A source can move from `dry-run-only` to `enabled` only when all of the following are true:

- The checklist above has been reviewed against the live policy fields in `wayfinder.yaml`.
- `risk.terms`, `risk.rate_limits`, `risk.scraping`, `risk.credentials`, `risk.pii_user_generated_content`, and `risk.hosted_dependencies` all reflect an acceptable unattended posture rather than unresolved review work.
- Manual dry runs are already acceptable for the source and there is no remaining note that limits it to review-only or ad hoc use.
- The source is safe to include in `approved_scheduled_sources()`, which means it is acceptable for normal ingest without `--dry-run`.
- The default-disabled cron stance is still preserved until an operator separately enables `cron.enabled: true`.

Promotion to `enabled` does not by itself turn cron on. The unattended path remains blocked until the separate top-level cron switch is explicitly approved.

## Scheduled Ingest Guardrails

The current unattended guardrails must remain unchanged:

- `cron.enabled: false` blocks `python3 -m wayfinder scheduled-ingest` unless an operator uses `--allow-disabled` for manual validation.
- Scheduled ingest only runs `status: enabled` sources through `approved_scheduled_sources()`.
- `dry-run-only`, `needs-review`, and `disabled` sources are skipped with audit log entries.
- Scheduled ingest records `token_free=true` and `llm_tokens=0` audit metadata for the unattended path.

If any checklist item is unresolved, keep the source at `dry-run-only`, `needs-review`, or `disabled`; do not bypass the status gate or the top-level cron guard.
