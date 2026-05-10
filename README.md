# Agency Reporting Copilot MVP

Tiny local landing-page MVP for testing interest in an agency reporting copilot.

## Run locally

```powershell
python server.py
```

Then open `http://127.0.0.1:8000`.

## Signup data

Submitted emails are stored in `mailing-list.csv`.

## Notes

- No external services or secrets required.
- Duplicate emails are ignored.
- Invalid emails are rejected before writing to the CSV.
