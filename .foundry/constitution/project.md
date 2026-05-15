# Project Rules

- This repo contains Wayfinder, a local-first product intelligence pipeline for Codex Foundry.
- Keep collection, scoring, search, export, and dashboard behavior deterministic and easy to validate.
- Prefer public, non-token source signals and token-free ingest paths by default.
- Keep the dashboard read-only unless an issue explicitly asks for a write path.
- Preserve source safety policy: unreviewed or dry-run-only sources must not run unattended.
- Preserve the project-local `.foundry/` directory as the portable agent contract.
- Keep generated runtime state, local caches, logs, and task workspaces outside the tracked project contract.
- Prefer small changes that ship through a task branch and PR into the configured project branch.
- Do not add auth, billing, hosting, vector DB, LLM ranking, broad automation, or generic hardening unless the issue explicitly asks for it.
