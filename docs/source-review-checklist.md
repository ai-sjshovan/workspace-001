# Wayfinder Source Review Checklist

Use this checklist before changing any source from `dry-run-only` to `enabled` for unattended cron ingest.

This guide is additive to the current source policies in `wayfinder.yaml`. It does not change the meaning of any policy field, and it does not override the need for an explicit top-level cron decision in config.

## Review Surfaces

- `wayfinder.yaml` is the source of truth for `status`, `notes`, and `risk.*` policy fields.
- `python3 -m wayfinder sources list --health` is the operator review surface for the configured source policies, and it prints `review=...`, `unattended=...`, and `why=...` summaries for each adapter.
- The source catalog in `wayfinder/web.py` exposes the same safety metadata under `policy_status`, `risk`, and `unattended_cron`.
- `python3 -m wayfinder scheduled-ingest` is the unattended path and follows the current top-level `cron.enabled` setting.

## Current Adapter Status

Use this summary when deciding whether a source is safe for recurring cron today:

| Source | Current status | Recurring cron stance | Why |
| --- | --- | --- | --- |
| `oss-ledger` | Healthy | Included in the configured daily run | Curated local ledger, no credentials, no hosted dependency, and risk fields are already reviewed. |
| `hackernews` | `dry-run-only` | Not safe for recurring cron yet | Manual dry runs are acceptable, but unattended live Algolia use still needs terms, rate-limit, and user-generated-content review. |
| `github` | Healthy | Included in the configured daily run | Anonymous public repository search is approved at the configured low daily volume, with no credentials required and fixture-backed dry runs preserved for diagnostics. |
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

The CLI source review summary should be interpreted as:

- `review=approved`: the adapter is reviewed for unattended use.
- `review=pending`: the adapter is still limited to manual or review-only usage.
- `review=blocked`: the adapter is intentionally disabled in config.
- `unattended=eligible`: the adapter may participate in unattended ingest whenever the top-level cron switch is enabled.
- `unattended=blocked`: the adapter must stay out of unattended ingest because it is pending review or disabled.

## Promotion Rules

A source can move from `dry-run-only` to `enabled` only when all of the following are true:

- The checklist above has been reviewed against the live policy fields in `wayfinder.yaml`.
- `risk.terms`, `risk.rate_limits`, `risk.scraping`, `risk.credentials`, `risk.pii_user_generated_content`, and `risk.hosted_dependencies` all reflect an acceptable unattended posture rather than unresolved review work.
- Manual dry runs are already acceptable for the source and there is no remaining note that limits it to review-only or ad hoc use.
- The source is safe to include in `approved_scheduled_sources()`, which means it is acceptable for normal ingest without `--dry-run`.
- The top-level `cron.enabled` choice in `wayfinder.yaml` matches the intended operator posture for the environment where the review is being applied.

Promotion to `enabled` does not by itself change the top-level cron switch. The source gate and the global scheduler gate stay separate.

## Approval Or Rejection Decision

Use the checklist to make an explicit go/no-go decision before a new source is added to unattended ingest:

- Approve: keep the source in `wayfinder.yaml`, set `status: enabled`, retain the reviewed risk fields, and leave clear `notes` describing why unattended ingest is acceptable.
- Reject for now: keep the source at `dry-run-only`, `needs-review`, or `disabled`, update `notes` with the unresolved safety or rate-limit reason, and do not include it in recurring ingest.
- Reject entirely: remove the candidate from cron consideration, document the reason in operator notes or the issue/PR, and leave the README/checklist posture unchanged until a later review reopens it.

Until a source reaches the approved path above, it must stay out of unattended ingest even if manual dry runs are acceptable.

## Scheduled Ingest Guardrails

The current unattended guardrails must remain unchanged:

- `cron.enabled` controls whether `python3 -m wayfinder scheduled-ingest` runs directly or requires `--allow-disabled` for manual validation.
- Scheduled ingest only runs `status: enabled` sources through `approved_scheduled_sources()`.
- `dry-run-only`, `needs-review`, and `disabled` sources are skipped with audit log entries.
- Scheduled ingest records `token_free=true` and `llm_tokens=0` audit metadata for the unattended path.

If any checklist item is unresolved, keep the source at `dry-run-only`, `needs-review`, or `disabled`; do not bypass the status gate or the top-level cron guard.
