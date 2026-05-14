from __future__ import annotations

import html
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .config import storage_path
from .db import connect, counts, list_rows, search_signals


STYLE = """
:root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }
body { margin: 0; color: #172026; background: #f5f7f2; }
header { padding: 28px 36px 18px; background: #102523; color: #f6fbf2; border-bottom: 5px solid #d2f06f; }
h1 { margin: 0; font-size: 30px; letter-spacing: 0; }
nav { display: flex; gap: 14px; margin-top: 14px; flex-wrap: wrap; }
a { color: #006c67; font-weight: 700; text-decoration: none; }
header a { color: #d2f06f; }
main { padding: 28px 36px 48px; max-width: 1180px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-bottom: 24px; }
.metric, .row { background: #ffffff; border: 1px solid #dbe2d4; border-radius: 8px; padding: 14px 16px; box-shadow: 0 1px 0 rgba(16, 37, 35, .06); }
.metric strong { display: block; font-size: 26px; color: #102523; }
.metric span, .meta { color: #66746a; font-size: 13px; }
form { display: flex; gap: 8px; margin: 0 0 18px; }
input { flex: 1; min-width: 180px; padding: 11px 12px; border: 1px solid #bfcab9; border-radius: 7px; font-size: 15px; }
button { padding: 11px 15px; border: 0; border-radius: 7px; background: #102523; color: #f6fbf2; font-weight: 800; cursor: pointer; }
.row { margin-bottom: 10px; }
.row h2 { margin: 0 0 6px; font-size: 17px; }
.row p { margin: 6px 0 0; line-height: 1.45; }
.tag { display: inline-block; margin-right: 6px; padding: 2px 7px; border-radius: 99px; background: #e9f2dc; color: #40502e; font-size: 12px; font-weight: 700; }
"""


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def layout(title: str, body: str) -> bytes:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} - Wayfinder</title>
  <style>{STYLE}</style>
</head>
<body>
  <header>
    <h1>Wayfinder</h1>
    <nav>
      <a href="/">Dashboard</a>
      <a href="/search">Search</a>
      <a href="/products">Products</a>
      <a href="/opportunities">Opportunities</a>
      <a href="/api/search?q=saas">API</a>
    </nav>
  </header>
  <main>{body}</main>
</body>
</html>""".encode("utf-8")


def signal_rows(rows: list[Any]) -> str:
    if not rows:
        return "<p>No signals found yet. Run <code>wayfinder ingest --source oss-ledger</code>.</p>"
    chunks = []
    for row in rows:
        body = esc(row["body"])
        if len(body) > 320:
            body = body[:317] + "..."
        chunks.append(
            f"""<article class="row">
  <h2><a href="{esc(row['source_url'])}">{esc(row['title'])}</a></h2>
  <div class="meta"><span class="tag">{esc(row['source'])}</span><span class="tag">{esc(row['category'])}</span> score={esc(row['score'])}</div>
  <p>{body}</p>
</article>"""
        )
    return "\n".join(chunks)


def product_rows(rows: list[Any]) -> str:
    if not rows:
        return "<p>No product intel found yet.</p>"
    return "\n".join(
        f"""<article class="row">
  <h2><a href="{esc(row['url'])}">{esc(row['product_name'])}</a></h2>
  <div class="meta"><span class="tag">{esc(row['category'])}</span>{esc(row['pricing_model'])}</div>
  <p>{esc(row['strengths'])}</p>
  <p>{esc(row['feature_gaps'])}</p>
</article>"""
        for row in rows
    )


def opportunity_rows(rows: list[Any]) -> str:
    if not rows:
        return "<p>No opportunities found yet.</p>"
    return "\n".join(
        f"""<article class="row">
  <h2>{esc(row['title'])}</h2>
  <div class="meta"><span class="tag">{esc(row['target_user'])}</span> evidence={esc(row['evidence_count'])}</div>
  <p><strong>Problem:</strong> {esc(row['problem'])}</p>
  <p><strong>Angle:</strong> {esc(row['iteration_angle'])}</p>
  <p><strong>Monetization:</strong> {esc(row['monetization_strategy'])}</p>
</article>"""
        for row in rows
    )


class WayfinderHandler(BaseHTTPRequestHandler):
    config: dict[str, Any] = {}

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def send_html(self, title: str, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = layout(title, body)
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(value, indent=2, sort_keys=True, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/health":
            self.send_json({"ok": True, "service": "wayfinder"})
            return
        conn = connect(storage_path(self.config))
        try:
            if parsed.path == "/":
                metric_html = "".join(
                    f'<div class="metric"><strong>{value}</strong><span>{esc(name)}</span></div>'
                    for name, value in counts(conn).items()
                )
                rows = list_rows(conn, "signals", 12)
                self.send_html("Dashboard", f'<section class="grid">{metric_html}</section>{signal_rows(rows)}')
                return
            if parsed.path == "/search":
                query = params.get("q", [""])[0]
                rows = search_signals(conn, query, 30)
                form = (
                    f'<form method="get" action="/search"><input name="q" value="{esc(query)}" '
                    'placeholder="Search pains, products, markets"><button>Search</button></form>'
                )
                self.send_html("Search", form + signal_rows(rows))
                return
            if parsed.path == "/api/search":
                query = params.get("q", [""])[0]
                rows = search_signals(conn, query, 50)
                self.send_json([dict(row) for row in rows])
                return
            if parsed.path == "/products":
                self.send_html("Products", product_rows(list_rows(conn, "products", 50)))
                return
            if parsed.path == "/opportunities":
                self.send_html("Opportunities", opportunity_rows(list_rows(conn, "opportunities", 50)))
                return
            self.send_html("Not Found", "<p>Not found.</p>", HTTPStatus.NOT_FOUND)
        finally:
            conn.close()


def serve(config: dict[str, Any], host: str = "127.0.0.1", port: int = 8766) -> None:
    WayfinderHandler.config = config
    server = ThreadingHTTPServer((host, port), WayfinderHandler)
    print(f"Wayfinder dashboard running at http://{host}:{port}")
    server.serve_forever()
