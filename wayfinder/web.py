from __future__ import annotations

import html
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .config import storage_path
from .db import browse_signals, connect, counts, list_rows, search_signals, signal_filter_values, source_detail


STYLE = """
:root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }
body { margin: 0; color: #172026; background: #f5f7f2; }
header { padding: 28px 36px 18px; background: #102523; color: #f6fbf2; border-bottom: 5px solid #d2f06f; }
h1 { margin: 0; font-size: 30px; letter-spacing: 0; }
nav { display: flex; gap: 14px; margin-top: 14px; flex-wrap: wrap; }
a { color: #006c67; font-weight: 700; text-decoration: none; }
header a { color: #d2f06f; }
main { padding: 28px 36px 48px; max-width: 1180px; }
.stack { display: grid; gap: 18px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
.metric, .row { background: #ffffff; border: 1px solid #dbe2d4; border-radius: 8px; padding: 14px 16px; box-shadow: 0 1px 0 rgba(16, 37, 35, .06); }
.metric strong { display: block; font-size: 26px; color: #102523; }
.metric span, .meta { color: #66746a; font-size: 13px; }
form.filters { display: grid; grid-template-columns: minmax(220px, 2.2fr) repeat(2, minmax(150px, 1fr)) auto; gap: 10px; margin: 0; }
input, select { width: 100%; min-width: 0; padding: 11px 12px; border: 1px solid #bfcab9; border-radius: 7px; font-size: 15px; background: #fff; box-sizing: border-box; }
button { padding: 11px 15px; border: 0; border-radius: 7px; background: #102523; color: #f6fbf2; font-weight: 800; cursor: pointer; }
.toolbar { display: flex; justify-content: space-between; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; }
.panel { background: #eef3e8; border: 1px solid #dbe2d4; border-radius: 10px; padding: 14px; }
.detail-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr); gap: 14px; align-items: start; }
.row h2 { margin: 0; font-size: 17px; }
.row p { margin: 6px 0 0; line-height: 1.45; }
.row-grid { display: grid; gap: 10px; }
.signal-head, .scan-grid { display: grid; gap: 8px; }
.signal-head { grid-template-columns: minmax(0, 1fr) auto; align-items: start; }
.scan-grid { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
.mini-list { display: grid; gap: 10px; margin-top: 12px; }
.mini-item { padding-top: 10px; border-top: 1px solid #dbe2d4; }
.mini-item:first-child { padding-top: 0; border-top: 0; }
.source-link { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; word-break: break-all; }
.excerpt { color: #22312b; }
.subtle { color: #66746a; font-size: 14px; }
.score { min-width: 78px; text-align: right; font-weight: 800; color: #102523; }
.tag { display: inline-block; margin-right: 6px; padding: 2px 7px; border-radius: 99px; background: #e9f2dc; color: #40502e; font-size: 12px; font-weight: 700; }
.list-head { margin: 0 0 4px; font-size: 14px; text-transform: uppercase; letter-spacing: .06em; color: #66746a; }
@media (max-width: 760px) {
  header, main { padding-left: 18px; padding-right: 18px; }
  form.filters, .signal-head, .detail-grid { grid-template-columns: 1fr; }
  .score { text-align: left; }
}
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


def filter_form(query: str, source: str, category: str, values: dict[str, list[str]]) -> str:
    def options(items: list[str], selected: str, label: str) -> str:
        html_options = [f'<option value="">{esc(label)}</option>']
        for item in items:
            active = ' selected="selected"' if item == selected else ""
            html_options.append(f'<option value="{esc(item)}"{active}>{esc(item)}</option>')
        return "".join(html_options)

    return f"""<section class="panel">
  <form class="filters" method="get" action="/">
    <input name="q" value="{esc(query)}" placeholder="Search titles, excerpts, products, categories">
    <select name="source">{options(values["sources"], source, "All sources")}</select>
    <select name="category">{options(values["categories"], category, "All categories")}</select>
    <button type="submit">Filter</button>
  </form>
</section>"""


def signal_rows(rows: list[Any]) -> str:
    if not rows:
        return "<p>No signals found yet. Run <code>wayfinder ingest --source oss-ledger</code>.</p>"
    chunks = []
    for row in rows:
        body = esc(row["body"])
        if len(body) > 320:
            body = body[:317] + "..."
        source_url = row["source_url"] or ""
        chunks.append(
            f"""<article class="row">
  <div class="signal-head">
    <div>
      <h2><a href="{esc(source_url)}">{esc(row['title'])}</a></h2>
      <div class="meta"><span class="tag">{esc(row['source'])}</span><span class="tag">{esc(row['category'])}</span></div>
    </div>
    <div class="score">score {esc(row['score'])}</div>
  </div>
  <p class="source-link"><a href="{esc(source_url)}">{esc(source_url)}</a></p>
  <p class="excerpt">{body}</p>
</article>"""
        )
    return "\n".join(chunks)


def source_detail_panel(detail: dict[str, Any] | None) -> str:
    if not detail:
        return ""
    category_chips = "".join(
        f'<span class="tag">{esc(item["category"])} {esc(item["total"])}</span>' for item in detail["categories"]
    ) or '<span class="subtle">No categories tagged yet.</span>'
    signal_items = "".join(
        f"""<div class="mini-item">
  <strong><a href="{esc(item['source_url'])}">{esc(item['title'])}</a></strong>
  <div class="meta"><span class="tag">{esc(item['category'] or 'uncategorized')}</span>score {esc(item['score'])}</div>
</div>"""
        for item in detail["signals"]
    )
    opportunity_items = "".join(
        f"""<div class="mini-item">
  <strong>{esc(item['title'])}</strong>
  <div class="meta"><span class="tag">{esc(item['category'] or 'uncategorized')}</span>{esc(item['target_user'])} · score {esc(item['opportunity_score'])} · evidence {esc(item['evidence_count'])}</div>
</div>"""
        for item in detail["opportunities"]
    ) or '<p class="subtle">No source-linked opportunities indexed yet.</p>'
    return f"""<section class="panel">
  <div class="detail-grid">
    <div>
      <p class="list-head">Selected source</p>
      <h2>{esc(detail['source'])}</h2>
      <p class="subtle">Signals {esc(detail['signal_count'])} · opportunities {esc(detail['opportunity_count'])} · avg score {esc(detail['avg_score'])}</p>
      <p class="subtle">Latest signal captured: {esc(detail['latest_signal_at'] or 'unknown')}</p>
      <p class="list-head">Top categories</p>
      <p>{category_chips}</p>
      <div class="mini-list">
        <p class="list-head">Recent high-signal items</p>
        {signal_items}
      </div>
    </div>
    <div>
      <p class="list-head">Source opportunity view</p>
      <p class="subtle">Highest opportunity score: {esc(detail['top_opportunity_score'])}</p>
      <div class="mini-list">{opportunity_items}</div>
    </div>
  </div>
</section>"""


def product_rows(rows: list[Any]) -> str:
    if not rows:
        return "<p>No product intel found yet.</p>"
    return "\n".join(
        f"""<article class="row">
  <div class="signal-head">
    <div>
      <h2><a href="{esc(row['url'])}">{esc(row['product_name'])}</a></h2>
      <div class="meta"><span class="tag">{esc(row['category'])}</span>{esc(row['pricing_model'])}</div>
    </div>
    <div class="subtle">{esc(row['audience'])}</div>
  </div>
  <div class="scan-grid">
    <div>
      <p class="list-head">Strengths</p>
      <p>{esc(row['strengths'])}</p>
    </div>
    <div>
      <p class="list-head">Feature gaps</p>
      <p>{esc(row['feature_gaps'])}</p>
    </div>
  </div>
</article>"""
        for row in rows
    )


def opportunity_rows(rows: list[Any]) -> str:
    if not rows:
        return "<p>No opportunities found yet.</p>"
    chunks = []
    for row in rows:
        try:
            score_data = json.loads(row["score_components_json"] or "{}")
        except json.JSONDecodeError:
            score_data = {}
        components = score_data.get("components") if isinstance(score_data, dict) else {}
        chips = " ".join(
            f'<span class="tag">{esc(label)} {esc(components.get(key, 0))}</span>'
            for key, label in (
                ("evidence_count", "evidence"),
                ("freshness", "freshness"),
                ("monetization_signal", "monetization"),
                ("source_quality", "source"),
                ("build_fit", "fit"),
            )
        )
        chunks.append(
            f"""<article class="row">
  <div class="signal-head">
    <div>
      <h2>{esc(row['title'])}</h2>
      <div class="meta"><span class="tag">{esc(row['target_user'])}</span> evidence={esc(row['evidence_count'])}</div>
    </div>
    <div class="score">score {esc(row['opportunity_score'])}</div>
  </div>
  <p class="meta">{chips}</p>
  <div class="scan-grid">
    <div>
      <p class="list-head">Problem</p>
      <p>{esc(row['problem'])}</p>
    </div>
    <div>
      <p class="list-head">Angle</p>
      <p>{esc(row['iteration_angle'])}</p>
    </div>
    <div>
      <p class="list-head">Monetization</p>
      <p>{esc(row['monetization_strategy'])}</p>
    </div>
  </div>
</article>"""
        )
    return "\n".join(chunks)


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
                query = params.get("q", [""])[0]
                source = params.get("source", [""])[0]
                category = params.get("category", [""])[0]
                metric_html = "".join(
                    f'<div class="metric"><strong>{value}</strong><span>{esc(name)}</span></div>'
                    for name, value in counts(conn).items()
                )
                values = signal_filter_values(conn)
                rows = browse_signals(conn, query=query, source=source, category=category, limit=30)
                detail = source_detail(conn, source)
                summary = f'<section class="toolbar"><p class="subtle">Showing {len(rows)} signal rows.</p><a href="/search?q={esc(query)}">Open search results</a></section>'
                body = f'<div class="stack"><section class="grid">{metric_html}</section>{filter_form(query, source, category, values)}{source_detail_panel(detail)}{summary}<section class="row-grid">{signal_rows(rows)}</section></div>'
                self.send_html("Dashboard", body)
                return
            if parsed.path == "/search":
                query = params.get("q", [""])[0]
                rows = search_signals(conn, query, 30)
                form = (
                    f'<section class="panel"><form class="filters" method="get" action="/search"><input name="q" value="{esc(query)}" '
                    'placeholder="Search pains, products, markets"><button>Search</button></form></section>'
                )
                summary = f'<section class="toolbar"><p class="subtle">Search returned {len(rows)} rows.</p><a href="/?q={esc(query)}">Use dashboard filters</a></section>'
                self.send_html("Search", f'<div class="stack">{form}{summary}<section class="row-grid">{signal_rows(rows)}</section></div>')
                return
            if parsed.path == "/api/search":
                query = params.get("q", [""])[0]
                rows = search_signals(conn, query, 50)
                self.send_json([dict(row) for row in rows])
                return
            if parsed.path == "/products":
                rows = list_rows(conn, "products", 50)
                body = f'<div class="stack"><section class="toolbar"><p class="subtle">{len(rows)} products indexed.</p></section><section class="row-grid">{product_rows(rows)}</section></div>'
                self.send_html("Products", body)
                return
            if parsed.path == "/opportunities":
                rows = list_rows(conn, "opportunities", 50)
                body = f'<div class="stack"><section class="toolbar"><p class="subtle">{len(rows)} opportunities indexed.</p></section><section class="row-grid">{opportunity_rows(rows)}</section></div>'
                self.send_html("Opportunities", body)
                return
            self.send_html("Not Found", "<p>Not found.</p>", HTTPStatus.NOT_FOUND)
        finally:
            conn.close()


def serve(config: dict[str, Any], host: str = "127.0.0.1", port: int = 8766) -> None:
    WayfinderHandler.config = config
    server = ThreadingHTTPServer((host, port), WayfinderHandler)
    print(f"Wayfinder dashboard running at http://{host}:{port}")
    server.serve_forever()
