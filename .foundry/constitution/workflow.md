# Workflow Rules

- Linear owns task state. Git owns code state. Symphony owns active lifecycle. Hermes owns manager recovery and QA. Codex owns implementation only.
- Runnable work moves through `Todo -> Staged -> In Progress -> Ready for Review -> Done`.
- Codex workers must commit, push a `foundry/` task branch, and open or reuse a PR into `project/wayfinder` before reporting complete.
- Do not push directly from `project/wayfinder`.
- Do not mark Linear issues Done from a Codex worker. Done requires independent Hermes/operator QA and a merged PR.
- Handoffs should include the issue id, branch, commit SHA when available, PR URL when available, validation evidence, and the exact blocker or next action.
- If a request arrives while a role is busy, preserve it as pending context instead of dropping it.
- New work should remain in Todo until the PR gate is clear and the scheduler stages it.
