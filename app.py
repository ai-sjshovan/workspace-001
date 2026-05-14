import csv
import io
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def get_client_pulse_clients() -> list[dict[str, str]]:
    return [
        {
            "name": "Northstar Advisory",
            "owner": "Mina Chen",
            "health": "Stable",
            "tone": "good",
            "arr": "$12.4k",
            "last_touch": "2 days ago",
            "next_action": "Share Q2 metrics summary before Friday review.",
        },
        {
            "name": "Harbor & Finch",
            "owner": "Evan Ross",
            "health": "Watch",
            "tone": "watch",
            "arr": "$8.1k",
            "last_touch": "5 days ago",
            "next_action": "Confirm training date and resend adoption checklist.",
        },
        {
            "name": "Lattice Studio",
            "owner": "Priya Nair",
            "health": "At Risk",
            "tone": "risk",
            "arr": "$6.7k",
            "last_touch": "8 days ago",
            "next_action": "Escalate delayed launch blockers with product lead.",
        },
        {
            "name": "Summit Peak Ops",
            "owner": "Jon Park",
            "health": "Stable",
            "tone": "good",
            "arr": "$15.9k",
            "last_touch": "Yesterday",
            "next_action": "Prepare renewal options and attach utilization snapshot.",
        },
        {
            "name": "Cedar Grove Legal",
            "owner": "Ava Patel",
            "health": "Growth",
            "tone": "growth",
            "arr": "$9.8k",
            "last_touch": "Today",
            "next_action": "Pitch expanded onboarding support for new practice area.",
        },
    ]


def get_client_pulse_summary(clients: list[dict[str, str]]) -> dict[str, int]:
    return {
        "total_clients": len(clients),
        "stable_clients": sum(client["health"] == "Stable" for client in clients),
        "watch_clients": sum(client["health"] == "Watch" for client in clients),
        "risk_clients": sum(client["health"] == "At Risk" for client in clients),
        "growth_clients": sum(client["health"] == "Growth" for client in clients),
    }


def get_client_pulse_payload() -> dict[str, object]:
    clients = get_client_pulse_clients()
    return {
        "app": "Client Pulse",
        "status": "ok",
        "summary": get_client_pulse_summary(clients),
        "clients": clients,
    }


def get_client_pulse_actions_payload() -> dict[str, object]:
    clients = get_client_pulse_clients()
    health_rank = {"At Risk": 0, "Watch": 1, "Growth": 2, "Stable": 3}
    priority_by_health = {
        "At Risk": "Critical",
        "Watch": "High",
        "Growth": "Medium",
        "Stable": "Low",
    }
    actions = [
        {
            "client": client["name"],
            "owner": client["owner"],
            "health": client["health"],
            "priority": priority_by_health[client["health"]],
            "next_action": client["next_action"],
            "last_touch": client["last_touch"],
        }
        for client in sorted(clients, key=lambda client: (health_rank[client["health"]], client["name"]))
    ]
    return {
        "app": "Client Pulse",
        "status": "ok",
        "total_actions": len(actions),
        "actions": actions,
    }


def render_client_pulse_csv() -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["name", "owner", "health", "arr", "last_touch", "next_action"],
    )
    writer.writeheader()
    for client in get_client_pulse_clients():
        writer.writerow({field: client[field] for field in writer.fieldnames})
    return output.getvalue()


def render_client_pulse() -> str:
    payload = get_client_pulse_payload()
    clients = payload["clients"]
    summary = payload["summary"]

    cards = []
    for client in clients:
        cards.append(
            f"""
            <article class="client-card">
              <div class="client-heading">
                <div>
                  <h3>{client["name"]}</h3>
                  <p>{client["owner"]} • {client["arr"]} MRR</p>
                </div>
                <span class="pill {client["tone"]}">{client["health"]}</span>
              </div>
              <dl class="client-meta">
                <div>
                  <dt>Last touch</dt>
                  <dd>{client["last_touch"]}</dd>
                </div>
                <div>
                  <dt>Next action</dt>
                  <dd>{client["next_action"]}</dd>
                </div>
              </dl>
            </article>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Client Pulse</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f3f6fb;
      --panel: #ffffff;
      --panel-alt: #eef3f9;
      --text: #162132;
      --muted: #66758a;
      --border: #d9e3ef;
      --accent: #2563eb;
      --good-bg: #e8f7ef;
      --good-fg: #20744a;
      --watch-bg: #fff4dc;
      --watch-fg: #996b00;
      --risk-bg: #fde7e7;
      --risk-fg: #a13737;
      --growth-bg: #e7f0ff;
      --growth-fg: #305cc7;
      font-family: "Segoe UI", Arial, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, #dce9ff 0, rgba(220, 233, 255, 0) 28%),
        linear-gradient(180deg, #f7f9fc 0%, var(--bg) 100%);
      color: var(--text);
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .hero {{
      display: grid;
      gap: 20px;
      grid-template-columns: minmax(0, 1.8fr) minmax(280px, 1fr);
      align-items: stretch;
      margin-bottom: 24px;
    }}
    .panel {{
      background: rgba(255, 255, 255, 0.94);
      border: 1px solid var(--border);
      border-radius: 20px;
      box-shadow: 0 16px 40px rgba(20, 34, 58, 0.07);
    }}
    .hero-copy {{
      padding: 28px;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 14px;
      padding: 6px 10px;
      border-radius: 999px;
      background: #e8f0ff;
      color: #3054a7;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.01em;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: clamp(2rem, 4vw, 3rem);
      line-height: 1.05;
    }}
    .hero-copy p {{
      margin: 0;
      max-width: 62ch;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.6;
    }}
    .summary {{
      display: grid;
      gap: 14px;
      padding: 20px;
      background: linear-gradient(180deg, #162132 0%, #1d2c43 100%);
      color: #f8fbff;
    }}
    .summary h2,
    .client-section h2 {{
      margin: 0;
      font-size: 1rem;
    }}
    .metric-grid {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .metric {{
      padding: 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .metric strong {{
      display: block;
      margin-top: 6px;
      font-size: 1.55rem;
      line-height: 1;
    }}
    .metric span,
    .summary-note,
    .client-card p,
    dt {{
      color: inherit;
      opacity: 0.78;
    }}
    .summary-note {{
      margin: 0;
      font-size: 0.95rem;
      line-height: 1.5;
    }}
    .client-section {{
      padding: 24px;
    }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: baseline;
      margin-bottom: 18px;
    }}
    .section-head p {{
      margin: 0;
      color: var(--muted);
      font-size: 0.95rem;
    }}
    .client-grid {{
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    }}
    .client-card {{
      padding: 18px;
      border-radius: 18px;
      background: var(--panel);
      border: 1px solid var(--border);
      min-height: 220px;
    }}
    .client-heading {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 18px;
    }}
    .client-heading h3 {{
      margin: 0 0 6px;
      font-size: 1.05rem;
    }}
    .client-heading p {{
      margin: 0;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .pill {{
      flex-shrink: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 7px 10px;
      border-radius: 999px;
      font-size: 0.79rem;
      font-weight: 700;
    }}
    .good {{ background: var(--good-bg); color: var(--good-fg); }}
    .watch {{ background: var(--watch-bg); color: var(--watch-fg); }}
    .risk {{ background: var(--risk-bg); color: var(--risk-fg); }}
    .growth {{ background: var(--growth-bg); color: var(--growth-fg); }}
    .client-meta {{
      display: grid;
      gap: 16px;
      margin: 0;
    }}
    .client-meta div {{
      padding: 12px 14px;
      border-radius: 14px;
      background: var(--panel-alt);
    }}
    dt {{
      margin-bottom: 8px;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }}
    dd {{
      margin: 0;
      font-size: 0.95rem;
      line-height: 1.5;
    }}
    @media (max-width: 820px) {{
      .hero {{
        grid-template-columns: 1fr;
      }}
      .section-head {{
        flex-direction: column;
        align-items: flex-start;
      }}
    }}
    @media (max-width: 560px) {{
      main {{
        padding: 22px 14px 40px;
      }}
      .hero-copy,
      .summary,
      .client-section {{
        padding: 18px;
      }}
      .metric-grid {{
        grid-template-columns: 1fr 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="panel hero-copy">
        <div class="eyebrow">Weekly snapshot</div>
        <h1>Client Pulse</h1>
        <p>
          Track account health, keep follow-ups visible, and spot renewals that need attention before they drift.
          This compact view is tuned for consultants and small agency teams working a short but high-touch client list.
        </p>
      </div>
      <aside class="panel summary" aria-label="Client summary">
        <h2>Portfolio summary</h2>
        <div class="metric-grid">
          <div class="metric"><span>Total clients</span><strong>{summary["total_clients"]}</strong></div>
          <div class="metric"><span>Healthy or growing</span><strong>{summary["stable_clients"] + summary["growth_clients"]}</strong></div>
          <div class="metric"><span>Needs attention</span><strong>{summary["watch_clients"] + summary["risk_clients"]}</strong></div>
          <div class="metric"><span>Renewals this month</span><strong>2</strong></div>
        </div>
        <p class="summary-note">
          Highest priority: unblock Lattice Studio before Thursday's steering call and close the training date with Harbor & Finch.
        </p>
      </aside>
    </section>

    <section class="panel client-section" aria-labelledby="client-list-heading">
      <div class="section-head">
        <div>
          <h2 id="client-list-heading">Accounts in motion</h2>
          <p>Static sample data showing health, ownership, and the next recommended action for each client.</p>
        </div>
      </div>
      <div class="client-grid">
        {''.join(cards)}
      </div>
    </section>
  </main>
</body>
</html>"""


class RequestHandler(BaseHTTPRequestHandler):
    def _send(self, status_code: int, body: bytes, content_type: str) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            body = b"<!DOCTYPE html><html lang='en'><head><title>Foundry Smoke</title></head><body><h1>Foundry Smoke</h1></body></html>"
            self._send(200, body, "text/html; charset=utf-8")
            return

        if self.path == "/health":
            body = json.dumps({"status": "ok"}).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return

        if self.path == "/api/client-pulse":
            body = json.dumps(get_client_pulse_payload()).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return

        if self.path == "/api/client-pulse/actions":
            body = json.dumps(get_client_pulse_actions_payload()).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return

        if self.path == "/api/client-pulse.csv":
            body = render_client_pulse_csv().encode("utf-8")
            self._send(200, body, "text/csv; charset=utf-8")
            return

        if self.path == "/client-pulse":
            body = render_client_pulse().encode("utf-8")
            self._send(200, body, "text/html; charset=utf-8")
            return

        body = b"Not Found"
        self._send(404, body, "text/plain; charset=utf-8")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), RequestHandler)
    print(f"Serving on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
