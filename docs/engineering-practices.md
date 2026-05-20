# Wayfinder Engineering Practices

Wayfinder stays intentionally small and reviewable. The working posture is Pythonic, stdlib-first, deterministic by default, and biased toward local operator control instead of hosted orchestration.

## Python Mantra

- Review changes against the Zen of Python: explicit, simple, readable, and practical beats clever.
- Prefer small functions, stable data shapes, and obvious control flow.
- Keep deterministic local behavior as the default path; any token spend or hosted-only path needs explicit approval.

## Implementation Defaults

- Use the Python standard library first.
- Keep SQLite as the system of record.
- Prefer `dataclasses` for internal records and `argparse` for CLI surfaces.
- Preserve the existing stdlib `http.server` implementation for the read-only web surface.
- Additive and idempotent SQLite schema changes only. New migrations must be safe to apply more than once.

## Product Surface Order

- API-first.
- CLI-second.
- UI-last.

The API and storage model define the system. CLI commands are operator tooling over that model. The web UI remains a small read-only inspection surface, not the center of the product.

## Sources And Engines

- `sources` are approved ingest adapters that collect and normalize evidence.
- `engines` are external sensors that can be registered and inspected without copying their core logic into Wayfinder.
- Engines do not replace Wayfinder's deterministic ingest, import, or scoring core.
- Registry behavior must stay deterministic and fixture/local-output friendly; importability checks are acceptable, hidden network work is not.

## Determinism And Safety

- Ingest, import, and scoring remain token-free and deterministic unless an operator explicitly approves a different contract.
- Scheduled ingest must continue to record `llm_tokens=0`.
- Preserve source-safety review fields and approved unattended source posture unless a task explicitly changes them.
