# Engineering Rules

- Inspect narrowly, change only what the issue asks for, validate once with the smallest relevant check, and stop.
- Read the repo profile first when available, then open only the specific files needed for the task.
- Prefer existing project patterns over new frameworks or abstractions.
- For Wayfinder CLI or adapter work, preserve dry-run-first behavior and focused fixture-backed tests.
- For dashboard work, stay inside the existing lightweight server-rendered Python approach unless the issue explicitly asks for heavier frontend changes.
- For scoring work, keep results local, deterministic, explainable, and visible in CLI or dashboard output.
- Keep command output bounded: targeted file ranges, short status output, failure-focused test output, and exact route/API checks.
- Do not rely on model memory for repo facts. Verify the live checkout before editing.
- Do not read secrets or modify unrelated files.
- If requirements, validation, credentials, or repo context are insufficient, block clearly instead of guessing.
