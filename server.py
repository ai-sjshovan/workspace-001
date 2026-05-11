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
INSIGHTS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift Insights</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f3f6fb;
            --panel: #ffffff;
            --panel-alt: #eef3ff;
            --text: #14213d;
            --muted: #5c6b89;
            --accent: #2563eb;
            --accent-soft: #dbeafe;
            --success: #15803d;
            --warning: #b45309;
            --border: #d7dfef;
            --shadow: 0 18px 40px rgba(20, 33, 61, 0.08);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: "Segoe UI", Arial, sans-serif;
            background: linear-gradient(180deg, #f8fbff 0%, var(--bg) 100%);
            color: var(--text);
        }
        .page {
            max-width: 1120px;
            margin: 0 auto;
            padding: 24px;
        }
        .topbar, .panel, .metric, .activity-item {
            background: var(--panel);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            border-radius: 24px;
            padding: 18px 22px;
        }
        .brand {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }
        .nav {
            display: flex;
            gap: 12px;
            color: var(--muted);
            font-size: 0.95rem;
        }
        .hero {
            display: grid;
            grid-template-columns: 1.6fr 1fr;
            gap: 20px;
            margin-top: 24px;
        }
        .panel {
            border-radius: 28px;
            padding: 24px;
        }
        h1, h2, h3, p {
            margin: 0;
        }
        .eyebrow, .label {
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
            font-weight: 700;
        }
        .hero-copy h1 {
            margin-top: 12px;
            font-size: clamp(2rem, 4vw, 3.4rem);
            line-height: 1.05;
        }
        .hero-copy p {
            margin-top: 14px;
            color: var(--muted);
            max-width: 44rem;
            line-height: 1.6;
        }
        .hero-side {
            background: linear-gradient(135deg, #1d4ed8 0%, #0f172a 100%);
            color: #fff;
        }
        .hero-side .label, .hero-side p {
            color: rgba(255, 255, 255, 0.8);
        }
        .hero-side strong {
            display: block;
            margin-top: 18px;
            font-size: 2.2rem;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
            margin-top: 20px;
        }
        .metric {
            border-radius: 24px;
            padding: 20px;
        }
        .metric strong {
            display: block;
            margin-top: 10px;
            font-size: 2rem;
        }
        .metric span {
            color: var(--muted);
            font-size: 0.95rem;
        }
        .content {
            display: grid;
            grid-template-columns: 1.3fr 0.9fr;
            gap: 20px;
            margin-top: 20px;
        }
        .workflow-list {
            display: grid;
            gap: 14px;
            margin-top: 18px;
        }
        .workflow-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding: 16px 18px;
            border-radius: 18px;
            background: var(--panel-alt);
        }
        .status-pill {
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 0.85rem;
            font-weight: 700;
        }
        .status-live {
            background: #dcfce7;
            color: var(--success);
        }
        .status-review {
            background: #fef3c7;
            color: var(--warning);
        }
        .activity-list {
            display: grid;
            gap: 12px;
            margin-top: 18px;
        }
        .activity-item {
            border-radius: 18px;
            padding: 16px;
        }
        .activity-item p {
            margin-top: 6px;
            color: var(--muted);
            line-height: 1.5;
        }
        @media (max-width: 860px) {
            .hero, .content, .metrics {
                grid-template-columns: 1fr;
            }
            .topbar {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <div class="page">
        <header class="topbar">
            <div>
                <div class="brand">BriefLift</div>
                <div class="nav">Insights Dashboard · Workflow Monitor · Recent Activity</div>
            </div>
            <div class="status-pill status-live">System Healthy</div>
        </header>
        <section class="hero">
            <div class="panel hero-copy">
                <div class="eyebrow">Insights</div>
                <h1>Campaign performance and workflow status in one view.</h1>
                <p>Track active briefs, watch publishing velocity, and review the latest workflow movement without leaving the BriefLift operating dashboard.</p>
            </div>
            <div class="panel hero-side">
                <div class="label">Weekly Throughput</div>
                <strong>128 briefs</strong>
                <p>Up 14% from last week with faster review handoffs across content teams.</p>
            </div>
        </section>
        <section class="metrics" aria-label="Metric summary">
            <article class="metric">
                <div class="label">Active Briefs</div>
                <strong>42</strong>
                <span>Across strategy, content, and launch workflows</span>
            </article>
            <article class="metric">
                <div class="label">Approval Rate</div>
                <strong>91%</strong>
                <span>Accepted in first review cycle this month</span>
            </article>
            <article class="metric">
                <div class="label">Time to Publish</div>
                <strong>2.8d</strong>
                <span>Average from intake to approved release</span>
            </article>
        </section>
        <section class="content">
            <article class="panel">
                <div class="eyebrow">Workflow Status</div>
                <h2 style="margin-top: 10px;">Current pipeline health</h2>
                <div class="workflow-list">
                    <div class="workflow-item">
                        <div>
                            <h3>Intake Review</h3>
                            <p style="margin-top: 4px; color: var(--muted);">9 new requests waiting for prioritization.</p>
                        </div>
                        <div class="status-pill status-review">Needs Review</div>
                    </div>
                    <div class="workflow-item">
                        <div>
                            <h3>Draft Generation</h3>
                            <p style="margin-top: 4px; color: var(--muted);">24 briefs are moving through automated drafting.</p>
                        </div>
                        <div class="status-pill status-live">On Track</div>
                    </div>
                    <div class="workflow-item">
                        <div>
                            <h3>Publishing Queue</h3>
                            <p style="margin-top: 4px; color: var(--muted);">7 approved briefs are scheduled for release today.</p>
                        </div>
                        <div class="status-pill status-live">Ready</div>
                    </div>
                </div>
            </article>
            <aside class="panel">
                <div class="eyebrow">Recent Activity</div>
                <h2 style="margin-top: 10px;">Latest changes</h2>
                <div class="activity-list">
                    <div class="activity-item">
                        <div class="label">Content Ops</div>
                        <p>Homepage refresh brief moved from Draft Generation to Review.</p>
                    </div>
                    <div class="activity-item">
                        <div class="label">SEO Team</div>
                        <p>Q3 editorial roadmap approved and queued for publishing.</p>
                    </div>
                    <div class="activity-item">
                        <div class="label">Lifecycle</div>
                        <p>Retention experiment brief marked complete after stakeholder sign-off.</p>
                    </div>
                </div>
            </aside>
        </section>
    </div>
</body>
</html>
"""


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

        if parsed.path == "/insights":
            self.write_html(HTTPStatus.OK, INSIGHTS_HTML)
            return

        if parsed.path == "/build":
            self.write_json(
                HTTPStatus.OK,
                {
                    "app_name": "BriefLift",
                    "environment": "development",
                    "git_commit": current_git_commit(),
                    "server_time": datetime.now(timezone.utc).isoformat(),
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

    def write_html(self, status: HTTPStatus, content: str) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
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
