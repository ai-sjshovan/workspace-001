# Wayfinder Project Scope

## Product Promise

Wayfinder is an internal Codex Foundry research tool that collects public, non-token source signals about product problems, SaaS opportunities, competing tools, monetization patterns, and open-source leverage candidates. It should help decide what to build next without guessing.

## Target User

The first user is the Codex Foundry operator. Later users may be builders who want a local-first opportunity intelligence pipeline they can run against their own stack.

## Current Acceptance Target

- The current acceptance target for `project/wayfinder` is the completed V1 local-first research workflow that already exists on this branch.
- V1 remains the active gate until an operator explicitly reopens the project for V2 work.
- Authorized work at this stage is limited to preserving and documenting the existing deterministic, token-free ingest model, read-only dashboard, task export, and source-safety surfaces.
- Preserve the existing smoke surface, including `/`, `/health`, `python3 -m wayfinder sources list --health`, `python3 -m wayfinder ingest --source oss-ledger`, `search`, `products`, `opportunities`, `score`, `export`, and `scheduled-ingest --allow-disabled`.

## V2 Status

- New V2 implementation work is not authorized by default on the current branch.
- No active V2 slice is approved until an operator explicitly requests that the project be reopened for V2.
- When V2 is explicitly approved later, record exactly one smallest runnable slice with observable success criteria and the preserved V1 smoke checks before starting implementation work.

## MVP Workflows

1. Run source adapters without LLM calls.
2. Normalize collected records into local SQLite tables.
3. Search signals by product, market, source, pain, or feature gap.
4. Browse products and opportunities in a small dashboard.
5. Generate Foundry-ready implementation task ideas from strong opportunities.
6. Keep source safety visible so unattended collection does not accidentally use questionable sources.

## Architecture Boundaries

- Use dependency-light Python first.
- Use SQLite plus FTS5 for MVP storage and search.
- Keep ingest deterministic and token-free.
- Treat adapters as small modules with `healthcheck`, `collect`, and `normalize`.
- Keep the dashboard read-only until task export is ready.
- Do not add auth, billing, hosted services, or vector DB in the MVP unless explicitly requested later.

## Source Safety

- `oss-ledger`, Hacker News, and GitHub public search are acceptable early sources.
- Reddit, app-store reviews, Product Hunt, crawlers, and scraping adapters require explicit source/terms review before recurring cron.
- Credentials must be optional and documented.
- Cron should default to disabled until source safety and rate limits are reviewed.

## Validation Strategy

- CLI smoke: `sources list`, `ingest --source oss-ledger`, `search`, `products`, `opportunities`, `stats`.
- Web smoke: `/`, `/search?q=...`, `/api/search?q=...`, `/products`, `/opportunities`.
- Network adapters should support dry-run before DB writes.
- Every implementation task should preserve existing `/` and `/health` smoke checks once the app baseline exists.

## Initial Task Order

1. Foundation: move the Wayfinder prototype into `workspace-001` on `project/wayfinder`.
2. Source Adapter: harden Hacker News ingest.
3. Source Adapter: harden GitHub ingest.
4. Dashboard: add filters and source detail pages.
5. Opportunity Scoring: add deterministic scoring.
6. Research Safety: add source review checklist and adapter status.
7. Cron: add disabled-by-default daily ingest runner.
8. Export: create Foundry-ready task idea export.

## Deferred

- Hosted deployment.
- Authentication.
- User accounts.
- Paid subscriptions.
- Embeddings/vector DB.
- Broad crawling.
- Direct automatic task creation from opportunities.
