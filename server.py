import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
INDEX_FILE = ROOT / "index.html"
MAILING_LIST_FILE = ROOT / "mailing-list.csv"
EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", re.IGNORECASE)
WRITE_LOCK = Lock()


def ensure_mailing_list_file() -> None:
    if MAILING_LIST_FILE.exists():
        return

    with MAILING_LIST_FILE.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["submitted_at", "email"])


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(email))


def append_email_if_new(email: str) -> bool:
    ensure_mailing_list_file()

    with WRITE_LOCK:
        with MAILING_LIST_FILE.open("r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            existing_emails = {row["email"].strip().lower() for row in reader if row.get("email")}

        if email in existing_emails:
            return False

        with MAILING_LIST_FILE.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([datetime.now(timezone.utc).isoformat(), email])

    return True


def current_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.SubprocessError, OSError):
        return "unknown"


class LandingPageHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.serve_index()
            return

        if parsed.path == "/health":
            self.write_json(
                HTTPStatus.OK,
                {
                    "app": "BriefLift",
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "git_commit": current_git_commit(),
                    "waitlist_storage_exists": MAILING_LIST_FILE.exists(),
                },
            )
            return

        if parsed.path == "/version":
            self.write_json(
                HTTPStatus.OK,
                {
                    "app_name": "BriefLift",
                    "git_commit": current_git_commit(),
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "api_version": "1",
                },
            )
            return

        if parsed.path == "/ping":
            self.write_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "app_name": "BriefLift",
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "health_path": "/health",
                },
            )
            return

        if parsed.path == "/ready":
            self.write_json(
                HTTPStatus.OK,
                {
                    "app": "BriefLift",
                    "status": "ready",
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "health_path": "/health",
                },
            )
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/signup":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self.write_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "message": "Request body must be valid JSON."},
            )
            return

        email = str(payload.get("email", "")).strip().lower()
        if not is_valid_email(email):
            self.write_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "message": "Enter a valid email address."},
            )
            return

        created = append_email_if_new(email)
        if created:
            self.write_json(
                HTTPStatus.CREATED,
                {"ok": True, "message": "You are on the founding beta list."},
            )
            return

        self.write_json(
            HTTPStatus.OK,
            {"ok": True, "message": "That email is already on the list."},
        )

    def serve_index(self) -> None:
        content = INDEX_FILE.read_text(encoding="utf-8")
        body = content.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def write_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    ensure_mailing_list_file()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), LandingPageHandler)
    print("Serving on http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
