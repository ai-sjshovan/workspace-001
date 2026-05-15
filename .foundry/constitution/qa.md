# QA Rules

- Every implementation handoff needs concrete validation evidence.
- Backend changes need focused route/API or automated test evidence.
- Frontend changes need route evidence and screenshot evidence when user-visible.
- Visual polish work must state which UI skills were loaded and where screenshots were saved.
- Source ingestion or external data work must preserve dry-run-first and safety-gated behavior unless the issue explicitly changes that policy.
- Preserve the Wayfinder smoke surface: `python3 -m wayfinder sources list --health`, `ingest --source oss-ledger`, `products`, `opportunities`, `score`, `export`, `scheduled-ingest --allow-disabled`, and web routes `/`, `/health`, `/search`, `/api/search`, `/products`, `/opportunities` when relevant.
- `No rows found.` after a dry-run or empty search is acceptable when the command exits successfully and the task does not require seeded results.
- Do not treat Ready for Review as Done. Ready for Review is the independent QA queue.
- A project version is complete only when its configured acceptance gate passes, no release-blocking PR or Linear state remains, and the operator accepts remaining ideas into a later backlog.
