# WRK-116 Wayfinder V1 Smoke Evidence

- Date: 2026-05-15
- Repo: `workspace-001`
- Target branch: `project/wayfinder`
- Task branch: `foundry/wrk-116-qa-record-wayfinder-v1-smoke-evidence-against-th`
- Validated commit: `319f326fec50488cd64757c452d91df7d45da1af`

## Scope

This artifact records the current Wayfinder v1 smoke baseline after the `python3 -m wayfinder` entrypoint/docs cleanup. No product code was changed for this task.

## CLI Smoke

Command source: `README.md` "Commands" section in the repo root. A root `codex-foundry.yaml` file is not present in this checkout, so the documented repo-local smoke commands were used as the live acceptance source.

| Command | Status | Evidence |
| --- | --- | --- |
| `python3 -m wayfinder sources list --health` | PASS | `oss-ledger` reported `status=enabled`, `review=approved`, `unattended=eligible`, `health=ok`. |
| `python3 -m wayfinder ingest --source oss-ledger` | PASS | Reported `raw=8 inserted signals=8 products=8 opportunities=8`. |
| `python3 -m wayfinder search saas` | PASS | Command completed successfully and printed `No rows found.` after `oss-ledger` ingest. |
| `python3 -m wayfinder products --limit 20` | PASS | Returned ranked product rows beginning with `RivalSearchMCP` and `crawlbase-mcp`. |
| `python3 -m wayfinder opportunities --limit 20` | PASS | Returned ranked opportunity rows beginning with `Leverage reddit-research-mcp | score=58.95`. |
| `python3 -m wayfinder score --limit 10` | PASS | Reported `rescored=8` and reprinted the ranked opportunity list. |
| `python3 -m wayfinder export --min-score 40 --source oss-ledger` | PASS | Emitted Markdown task drafts; first draft was `Leverage reddit-research-mcp for reddit research mcp`. |
| `python3 -m wayfinder scheduled-ingest --allow-disabled` | PASS | Ran `oss-ledger` and skipped `hackernews` / `github` as `dry-run-only`. |

## Web Smoke

Server command: `python3 -m wayfinder serve --port 8766`

| Route | Status | Evidence |
| --- | --- | --- |
| `GET /` | PASS | HTTP 200; page includes `Wayfinder` and `Top opportunities`. |
| `GET /health` | PASS | HTTP 200; JSON reported `ok: true`, `config: loaded`, `database: ready`. |
| `GET /search?q=reddit` | PASS | HTTP 200; page includes `Wayfinder` and `URL-backed filters`. |
| `GET /api/search?q=reddit` | PASS | HTTP 200; JSON payload returned search records. |
| `GET /products` | PASS | HTTP 200; page includes `Wayfinder`. |
| `GET /opportunities` | PASS | HTTP 200; page includes `Wayfinder`. |

## Focused Automated Check

| Check | Status | Evidence |
| --- | --- | --- |
| `python3 -m unittest tests.test_web_routes` | PASS | `Ran 1 test in 0.604s` / `OK`. |

## Residual Notes

- Gap: the acceptance text references v1 CLI smoke commands in `codex-foundry.yaml`, but no root `codex-foundry.yaml` exists in this checkout. The current repo-local smoke source is `README.md`.
- Expected behavior: `python3 -m wayfinder search saas` returned `No rows found.` even after `oss-ledger` ingest; this was a successful command run, not a shell failure.
- Source-safety boundary remained intact during smoke validation: `scheduled-ingest --allow-disabled` skipped `hackernews` and `github` because both remain `dry-run-only`.
