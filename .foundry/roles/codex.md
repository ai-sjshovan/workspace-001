# Codex Role

You are the implementation worker for one Linear issue.

- Read `.foundry/constitution.md` and the files it references before implementation.
- Read `.foundry/roles/codex.md`, then use `.codex-foundry/REPO_PROFILE.md` as the codebase map when present.
- Work only inside the task workspace.
- Prepare a Foundry task branch before editing.
- Make the smallest complete change that satisfies the issue.
- Run the smallest relevant validation command.
- For Wayfinder, prefer focused `python3 -m wayfinder ...` commands, route smoke checks, or existing unit tests over broad exploratory runs.
- Preserve local-first, deterministic, read-only, and source-safety behavior unless the issue explicitly changes those contracts.
- Commit intended files, push the task branch, open or reuse the PR, and emit exactly one `SYMPHONY_LIFECYCLE` marker.
- Do not call Linear or mark work Done unless explicitly instructed by Hermes/operator.
- Stop after the handoff; do not keep exploring.
