# Wayfinder Plan

## Current Acceptance Target

- `project/wayfinder` remains on the completed V1 acceptance target already present on this branch.
- The active acceptance gate is the existing local-first workflow: deterministic, token-free ingest; explicit source-safety controls; read-only browse/detail/export surfaces; and the current CLI and web smoke checks.
- New implementation work should preserve that V1 baseline rather than expand scope.

## V2 Authorization Status

- Wayfinder is still V1-frozen unless an operator explicitly reopens the project for V2.
- No V2 implementation slice is authorized now.
- Do not start a new V2 slice, adapter, dashboard enhancement, scoring change, auth surface, billing surface, hosted deployment work, or cron expansion without that explicit operator request.

## Preserved Validation Surface

- Keep the existing `/` and `/health` smoke checks intact.
- Keep the current deterministic, token-free ingest model intact.
- Keep the current source-safety boundaries intact, including optional credentials, dry-run-first behavior, and cron remaining safety-gated by review status plus `cron.enabled: false` by default.
- Preserve the existing V1 smoke path:
  - `python3 -m wayfinder sources list --health`
  - `python3 -m wayfinder ingest --source oss-ledger`
  - `python3 -m wayfinder search ...`
  - `python3 -m wayfinder products ...`
  - `python3 -m wayfinder opportunities ...`
  - `python3 -m wayfinder score ...`
  - `python3 -m wayfinder export ...`
  - `python3 -m wayfinder scheduled-ingest --allow-disabled`
  - `/`
  - `/health`

## Next Slice Rule

- If an operator explicitly authorizes V2 later, update this file before implementation to name exactly one smallest runnable slice, its observable success criteria, and the V1 smoke checks that must still pass.
- Until that request exists, there is no active V2 slice.
