# Workspace 001

Clean Codex Foundry seed workspace. Project branches are created from this branch, and task branches open PRs into the active project branch.

## Run locally

Start the app with:

```bash
python3 app.py
```

If port `8000` is already in use in your workspace, override it:

```bash
PORT=8001 python3 app.py
```

Then check the routes:

```bash
curl -fsS http://127.0.0.1:8000/
curl -fsS http://127.0.0.1:8000/health
```
