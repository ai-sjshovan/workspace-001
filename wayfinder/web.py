from __future__ import annotations

import html
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, quote, quote_plus, unquote, urlparse

from .adapters import build_adapter
from .config import source_configs, source_policy, source_review_summary, storage_path
from .db import (
    browse_signals,
    connect,
    counts,
    filtered_opportunities,
    filtered_products,
    opportunity_detail,
    opportunity_related_context,
    opportunity_score_filter_values,
    opportunity_filter_values,
    product_filter_values,
    search_signals,
    signal_filter_values,
    source_activity,
    source_detail,
)


SENSITIVE_CONFIG_KEYS = {
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "bearer",
    "client_secret",
    "cookie",
    "credential",
    "credentials",
    "password",
    "private_key",
    "secret",
    "token",
}


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
form.filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; margin: 0; }
input, select { width: 100%; min-width: 0; padding: 11px 12px; border: 1px solid #bfcab9; border-radius: 7px; font-size: 15px; background: #fff; box-sizing: border-box; }
textarea { width: 100%; min-height: 260px; padding: 11px 12px; border: 1px solid #bfcab9; border-radius: 7px; font-size: 14px; background: #fff; box-sizing: border-box; resize: vertical; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
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
.tag.active { background: #102523; color: #f6fbf2; }
.tag.good { background: #dff5df; color: #215228; }
.tag.warn { background: #fff2cf; color: #6a4d00; }
.tag.bad { background: #fde0de; color: #7a1f1a; }
.list-head { margin: 0 0 4px; font-size: 14px; text-transform: uppercase; letter-spacing: .06em; color: #66746a; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; }
.card-grid .row { height: 100%; }
.source-title { display: flex; justify-content: space-between; gap: 10px; align-items: start; }
.source-card { display: block; color: inherit; }
.source-card.active { border-color: #102523; box-shadow: 0 0 0 2px rgba(16, 37, 35, .12); }
.source-card h2 { color: #102523; }
.toolbar-links { display: flex; gap: 10px; flex-wrap: wrap; }
.run-list { display: grid; gap: 10px; }
@media (max-width: 760px) {
  header, main { padding-left: 18px; padding-right: 18px; }
  form.filters, .signal-head, .detail-grid { grid-template-columns: 1fr; }
  .score { text-align: left; }
  .source-title { flex-direction: column; }
}
"""


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


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
      <a href="/sources">Sources</a>
      <a href="/search">Search</a>
      <a href="/products">Products</a>
      <a href="/opportunities">Opportunities</a>
      <a href="/api/search?q=saas">API</a>
    </nav>
  </header>
  <main>{body}</main>
</body>
</html>""".encode("utf-8")


def is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return any(marker in normalized for marker in SENSITIVE_CONFIG_KEYS)


def sanitize_source_value(key: str, value: Any) -> Any:
    if is_sensitive_key(key):
        normalized = str(value).strip().lower()
        if normalized in {"", "none", "false", "0", "null"}:
            return value
        return "[redacted]"
    if isinstance(value, dict):
        return {str(child_key): sanitize_source_value(str(child_key), child_value) for child_key, child_value in value.items()}
    if isinstance(value, list):
        return [sanitize_source_value(key, item) for item in value]
    return value


def source_catalog_entry(name: str, cfg: dict[str, Any], *, cron_enabled: bool, token_free_default: bool) -> dict[str, Any]:
    policy = source_policy(cfg)
    review_state, unattended_state, review_reason = source_review_summary(policy)
    safe_config = {
        key: sanitize_source_value(key, value)
        for key, value in cfg.items()
        if key != "_config_dir"
    }
    return {
        "key": name,
        "kind": str(cfg.get("kind") or name),
        "status": policy.status,
        "policy_status": policy.status,
        "review": review_state,
        "unattended": unattended_state,
        "why": review_reason,
        "notes": policy.notes,
        "risk": {
            "credentials": policy.risk.credentials,
            "terms": policy.risk.terms,
            "rate_limits": policy.risk.rate_limits,
            "scraping": policy.risk.scraping,
            "pii_user_generated_content": policy.risk.pii_user_generated_content,
            "hosted_dependencies": policy.risk.hosted_dependencies,
        },
        "unattended_cron": {
            "eligible": unattended_state == "eligible",
            "global_cron_enabled": cron_enabled,
            "token_free_default": token_free_default,
        },
        "config": safe_config,
    }


def source_catalog_payload(config: dict[str, Any], source_name: str = "") -> dict[str, Any]:
    cron = config.get("cron") if isinstance(config.get("cron"), dict) else {}
    cron_enabled = bool(cron.get("enabled", False))
    token_free_default = bool(cron.get("token_free", False))
    catalog = {
        name: source_catalog_entry(name, cfg, cron_enabled=cron_enabled, token_free_default=token_free_default)
        for name, cfg in source_configs(config).items()
    }
    selected_name = source_name.strip()
    selected = catalog.get(selected_name) if selected_name else None
    return {
        "sources": [catalog[name] for name in sorted(catalog)],
        "source": selected,
        "requested_source": selected_name or None,
        "count": len(catalog),
        "cron": {
            "enabled": cron_enabled,
            "schedule": str(cron.get("schedule") or ""),
            "token_free_default": token_free_default,
        },
    }


def adapter_health_snapshot(name: str, cfg: dict[str, Any], policy_status: str) -> dict[str, Any]:
    if policy_status == "disabled":
        return {
            "ok": False,
            "label": "disabled",
            "message": "Health checks are skipped while this adapter is disabled.",
        }
    try:
        ok, message = build_adapter(name, cfg).healthcheck()
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "label": "fail",
            "message": str(exc),
        }
    return {
        "ok": ok,
        "label": "ok" if ok else "fail",
        "message": message,
    }


def source_status_overview(config: dict[str, Any]) -> dict[str, Any]:
    payload = source_catalog_payload(config)
    raw_sources = source_configs(config)
    counts = {
        "enabled": 0,
        "dry-run-only": 0,
        "needs-review": 0,
        "disabled": 0,
        "healthy": 0,
        "failing": 0,
    }
    sources: list[dict[str, Any]] = []
    for item in payload["sources"]:
        health = adapter_health_snapshot(item["key"], raw_sources.get(item["key"], {}), str(item["policy_status"]))
        counts[str(item["policy_status"])] = counts.get(str(item["policy_status"]), 0) + 1
        if health["label"] == "ok":
            counts["healthy"] += 1
        elif health["label"] == "fail":
            counts["failing"] += 1
        sources.append({**item, "health": health})
    return {
        **payload,
        "sources": sources,
        "counts": counts,
    }


def source_drill_in(source: str, label: str | None = None) -> str:
    source_name = (source or "").strip()
    if not source_name:
        return ""
    href = f"/sources/{quote(source_name, safe='')}"
    return f'<a class="tag" href="{href}">{esc(label or source_name)}</a>'


def source_path(source_name: str) -> str:
    return f"/sources/{quote(source_name.strip(), safe='')}"


def source_context_path(source_name: str, signal_id: str = "", source_url: str = "") -> str:
    query_parts: list[str] = []
    if signal_id.strip():
        query_parts.append(f"signal={quote_plus(signal_id.strip())}")
    elif source_url.strip():
        query_parts.append(f"record={quote_plus(source_url.strip())}")
    suffix = f"?{'&'.join(query_parts)}" if query_parts else ""
    return f"{source_path(source_name)}{suffix}"


def opportunity_source_context_path(source_name: str, category: str = "") -> str:
    source = source_name.strip()
    query_parts: list[str] = []
    if source:
        query_parts.append(f"source={quote_plus(source)}")
    if category.strip():
        query_parts.append(f"market={quote_plus(category.strip())}")
    suffix = f"?{'&'.join(query_parts)}" if query_parts else ""
    return f"/search{suffix}"


def parse_score_components(raw_value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def opportunity_export_payload(row: Any) -> dict[str, Any]:
    item = dict(row)
    score_components = parse_score_components(str(item.pop("score_components_json", "{}")))
    source_name = str(item.get("source") or "")
    category = str(item.get("category") or "")
    return {
        **item,
        "score_components": score_components,
        "source_context": {
            "source": source_name,
            "detail_path": source_path(source_name) if source_name else "",
            "search_path": opportunity_source_context_path(source_name, category),
        },
        "draft_task": {
            "title": str(item.get("title") or ""),
            "target_user": str(item.get("target_user") or ""),
            "problem": str(item.get("problem") or ""),
            "category": category,
            "source": source_name,
            "evidence_count": int(item.get("evidence_count") or 0),
            "iteration_angle": str(item.get("iteration_angle") or ""),
            "monetization_strategy": str(item.get("monetization_strategy") or ""),
            "foundry_task_suggestions": str(item.get("foundry_task_suggestions") or ""),
            "build_difficulty": str(item.get("build_difficulty") or ""),
            "replication_time_estimate": str(item.get("replication_time_estimate") or ""),
            "competing_products": str(item.get("competing_products") or ""),
            "what_products_do_right": str(item.get("what_products_do_right") or ""),
            "what_users_want_better": str(item.get("what_users_want_better") or ""),
        },
    }


def active_filter_summary(filters: list[tuple[str, str]]) -> str:
    active = [(label, value.strip()) for label, value in filters if value.strip()]
    if not active:
        return '<p class="subtle">No filters applied. Browse the highest-signal rows or jump into a source detail view.</p>'
    tags = "".join(f'<span class="tag active">{esc(label)}: {esc(value)}</span>' for label, value in active)
    return f'<div>{tags}</div>'


def source_directory(source_names: list[str], active_source: str, activity_lookup: dict[str, dict[str, Any]]) -> str:
    if not source_names:
        return ""
    cards: list[str] = []
    current = active_source.strip()
    for name in source_names:
        activity = activity_lookup.get(name, {})
        selected = ' active' if name == current else ""
        summary = (
            f"Signals {esc(activity.get('signal_count', 0))} · opportunities {esc(activity.get('opportunity_count', 0))}"
        )
        cards.append(
            f"""<a class="row source-card{selected}" href="{esc(source_path(name))}">
  <p class="list-head">Source detail</p>
  <h2>{esc(name)}</h2>
  <p class="subtle">{summary}</p>
  <p class="subtle">Avg score {esc(activity.get('avg_score', 0))} · latest {esc(activity.get('latest_signal_at') or 'none yet')}</p>
</a>"""
        )
    return (
        '<section class="panel"><section class="toolbar"><div><p class="list-head">Sources</p>'
        '<p class="subtle">Open a dedicated source detail page directly from the dashboard.</p></div></section>'
        f'<section class="card-grid">{"".join(cards)}</section></section>'
    )


def filter_form(
    action: str,
    *,
    query: str = "",
    source: str = "",
    category: str = "",
    pricing_model: str = "",
    complaint: str = "",
    product: str = "",
    pain_type: str = "",
    feature_request: str = "",
    values: dict[str, list[str]],
    placeholder: str = "Search titles, excerpts, products, categories",
    include_query: bool = True,
    include_source: bool = True,
    include_category: bool = True,
    include_pricing: bool = False,
    include_complaint: bool = False,
    include_product: bool = False,
    include_market: bool = False,
    include_pain_type: bool = False,
    include_feature_request: bool = False,
    submit_label: str = "Filter",
) -> str:
    def options(name: str, items: list[str], selected: str, label: str) -> str:
        html_options = [f'<option value="">{esc(label)}</option>']
        for item in items:
            active = ' selected="selected"' if item == selected else ""
            html_options.append(f'<option value="{esc(item)}"{active}>{esc(item)}</option>')
        return f'<select name="{esc(name)}">{"".join(html_options)}</select>'

    controls: list[str] = []
    if include_query:
        controls.append(f'<input name="q" value="{esc(query)}" placeholder="{esc(placeholder)}">')
    if include_source:
        controls.append(options("source", values.get("sources", []), source, "All sources"))
    if include_category:
        controls.append(options("category", values.get("categories", []), category, "All categories"))
    if include_pricing:
        controls.append(options("pricing", values.get("pricing_models", []), pricing_model, "All pricing"))
    if include_complaint:
        controls.append(options("complaint", values.get("complaints", []), complaint, "All complaint themes"))
    if include_product:
        controls.append(options("product", values.get("products", []), product, "All products"))
    if include_market:
        controls.append(options("market", values.get("categories", []), category, "All markets"))
    if include_pain_type:
        controls.append(options("pain", values.get("pain_types", []), pain_type, "All pains"))
    if include_feature_request:
        controls.append(
            options("feature_gap", values.get("feature_requests", []), feature_request, "All feature gaps")
        )
    controls.append(f"<button type=\"submit\">{esc(submit_label)}</button>")
    return f"""<section class="panel">
  <form class="filters" method="get" action="{esc(action)}">
    {''.join(controls)}
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
        source_context = source_context_path(str(row["source"]), str(row["source_id"] or ""), source_url)
        chunks.append(
            f"""<article class="row">
  <div class="signal-head">
    <div>
      <h2><a href="{esc(source_url)}">{esc(row['title'])}</a></h2>
      <div class="meta">{source_drill_in(str(row['source']))}<span class="tag">{esc(row['category'])}</span></div>
    </div>
    <div class="score">score {esc(row['score'])}</div>
  </div>
  <p class="source-link"><a href="{esc(source_url)}">{esc(source_url)}</a></p>
  <p class="subtle"><a href="{esc(source_context)}">View source context</a></p>
  <p class="excerpt">{body}</p>
</article>"""
        )
    return "\n".join(chunks)


def selected_source_record_panel(detail: dict[str, Any] | None) -> str:
    if not detail:
        return ""
    selected = detail.get("selected_signal")
    if not isinstance(selected, dict):
        return ""
    source_url = str(selected.get("source_url") or "").strip()
    return f"""<section class="panel">
  <section class="toolbar">
    <div>
      <p class="list-head">Selected record</p>
      <h2>{esc(selected.get('title') or 'Untitled record')}</h2>
    </div>
    <a href="{esc(source_url)}">Open original record</a>
  </section>
  <p class="meta"><span class="tag">{esc(selected.get('category') or 'uncategorized')}</span><span class="tag">{esc(selected.get('product') or 'no product')}</span>score {esc(selected.get('score') or 0)} · captured {esc(selected.get('collected_at') or 'unknown')}</p>
  <p class="excerpt">{esc(selected.get('body') or 'No excerpt captured for this record.')}</p>
  <p class="subtle">Pain: {esc(selected.get('pain_type') or 'n/a')} · feature gap: {esc(selected.get('feature_request') or 'n/a')}</p>
</section>"""


def source_detail_panel(detail: dict[str, Any] | None) -> str:
    if not detail:
        return ""
    recent_runs = detail.get("recent_runs", [])
    run_items = "".join(
        f"""<div class="mini-item">
  <strong>{esc(item['status'])}</strong>
  <div class="subtle">finished {esc(item['finished_at'] or 'unknown')} · collected {esc(item['collected'])} · signals +{esc(item['inserted_signals'])} · opportunities +{esc(item['inserted_opportunities'])}</div>
  <div class="subtle">{esc(item['message'] or ('dry run' if item['dry_run'] else 'no run notes'))}</div>
</div>"""
        for item in recent_runs
    ) or '<p class="subtle">No ingest history recorded yet.</p>'
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
  <section class="toolbar">
    <p class="subtle">Source detail drill-in for {esc(detail['source'])}.</p>
    <a href="{esc(source_path(str(detail['source'])))}">Open dedicated source view</a>
  </section>
  <div class="detail-grid">
    <div>
      <p class="list-head">Selected source</p>
      <h2>{esc(detail['source'])}</h2>
      <p class="subtle">Signals {esc(detail['signal_count'])} · opportunities {esc(detail['opportunity_count'])} · avg score {esc(detail['avg_score'])}</p>
      <p class="subtle">Latest signal captured: {esc(detail['latest_signal_at'] or 'unknown')}</p>
      <p class="subtle">Ingest health: {health_status_badge(str(detail.get('health_status') or 'unknown'))} latest run {esc(detail.get('last_ingest_at') or 'unknown')}</p>
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
      <p class="list-head">Recent ingest runs</p>
      <div class="run-list">{run_items}</div>
      <div class="mini-list">{opportunity_items}</div>
    </div>
  </div>
</section>"""


def source_status_tag(status: str) -> str:
    return f'<span class="tag">{esc(status or "unknown")}</span>'


def policy_status_badge(status: str) -> str:
    normalized = status.strip().lower()
    tone = {
        "enabled": "good",
        "dry-run-only": "warn",
        "needs-review": "warn",
        "disabled": "bad",
    }.get(normalized, "")
    class_name = f"tag {tone}".strip()
    return f'<span class="{class_name}">{esc(status or "unknown")}</span>'


def health_status_badge(status: str) -> str:
    normalized = status.strip().lower()
    tone = {
        "success": "good",
        "ok": "good",
        "healthy": "good",
        "partial": "warn",
        "warning": "warn",
        "dry-run": "warn",
        "dry_run": "warn",
        "failed": "bad",
        "error": "bad",
    }.get(normalized, "")
    class_name = f"tag {tone}".strip()
    return f'<span class="{class_name}">{esc(status or "unknown")}</span>'


def source_safety_panel(payload: dict[str, Any]) -> str:
    cron = payload["cron"]
    counts = payload["counts"]
    cron_state = "disabled by default" if not cron["enabled"] else "enabled"
    approved = counts.get("enabled", 0)
    review_pending = counts.get("dry-run-only", 0) + counts.get("needs-review", 0)
    return f"""<section class="panel">
  <section class="toolbar">
    <div>
      <p class="list-head">Source safety and cron status</p>
      <h2>Cron is {esc(cron_state)}</h2>
      <p class="subtle">This page is read-only. It does not start scheduling, enable adapters, or change unattended collection state.</p>
    </div>
    <div class="toolbar-links">
      {health_status_badge('ok' if not cron['enabled'] else 'warning')}
      {source_status_tag('token-free default' if cron['token_free_default'] else 'token-required')}
    </div>
  </section>
  <section class="grid">
    <div class="metric"><strong>{esc(approved)}</strong><span>Approved for unattended collection</span></div>
    <div class="metric"><strong>{esc(review_pending)}</strong><span>Still blocked on review or manual-only use</span></div>
    <div class="metric"><strong>{esc(counts.get('healthy', 0))}</strong><span>Adapters passing live health checks</span></div>
    <div class="metric"><strong>{esc(counts.get('disabled', 0))}</strong><span>Disabled adapters</span></div>
  </section>
  <div class="detail-grid">
    <div>
      <p class="list-head">Cron guardrails</p>
      <div class="mini-list">
        <div class="mini-item"><strong>Global cron switch</strong><div class="subtle">{esc(cron_state)}</div></div>
        <div class="mini-item"><strong>Configured schedule</strong><div class="subtle">{esc(cron['schedule'] or 'not set')}</div></div>
        <div class="mini-item"><strong>Token-free ingest default</strong><div class="subtle">{esc('enabled' if cron['token_free_default'] else 'disabled')}</div></div>
      </div>
    </div>
    <div>
      <p class="list-head">Operator notes</p>
      <div class="mini-list">
        <div class="mini-item"><strong>Approved sources only</strong><div class="subtle">Only sources with policy status <code>enabled</code> are eligible for unattended collection once the global cron switch is explicitly turned on later.</div></div>
        <div class="mini-item"><strong>Manual and review states stay manual</strong><div class="subtle"><code>dry-run-only</code>, <code>needs-review</code>, and <code>disabled</code> sources remain excluded from unattended scheduling.</div></div>
      </div>
    </div>
  </div>
</section>"""


def source_list_page(
    payload: dict[str, Any],
    activity_by_source: dict[str, dict[str, Any]],
    selected_source: str = "",
    selected_detail: dict[str, Any] | None = None,
) -> str:
    cards = []
    for item in payload["sources"]:
        activity = activity_by_source.get(item["key"], {})
        cards.append(
            f"""<article class="row">
  <div class="source-title">
    <div>
      <p class="list-head">Source</p>
      <h2><a href="{esc(source_path(item['key']))}">{esc(item['key'])}</a></h2>
      <p class="meta">{policy_status_badge(str(item['policy_status']))}{health_status_badge(str(item['health']['label']))}<span class="tag">{esc(item['kind'])}</span></p>
    </div>
    <div class="subtle">Signals {esc(activity.get('signal_count', 0))} · opportunities {esc(activity.get('opportunity_count', 0))} · dashboard health {esc(activity.get('health_status') or 'unknown')}</div>
  </div>
  <p>{esc(item['notes'] or 'No operator notes recorded.')}</p>
  <p class="subtle">Adapter health: {esc(item['health']['message'])}</p>
  <p class="subtle">Risk: credentials={esc(item['risk']['credentials'])}, terms={esc(item['risk']['terms'])}, rate_limits={esc(item['risk']['rate_limits'])}</p>
  <p class="subtle">Cron readiness: {esc('eligible once cron is explicitly enabled' if item['unattended_cron']['eligible'] else 'blocked pending review or disabled state')} · global cron {esc('enabled' if item['unattended_cron']['global_cron_enabled'] else 'disabled')}</p>
</article>"""
        )
    selected_html = ""
    if selected_source.strip():
        preview = selected_detail or activity_by_source.get(selected_source.strip())
        if preview:
            selected_html = (
                f'<section class="toolbar"><p class="subtle">Selected source preview for {esc(selected_source)}.</p>'
                f'<a href="{esc(source_path(selected_source))}">Open dedicated detail page</a></section>'
                f"{source_detail_panel(preview)}"
            )
    return (
        '<div class="stack">'
        f'{source_safety_panel(payload)}'
        '<section class="toolbar"><p class="subtle">Configured sources with current policy, live adapter health, and activity summaries.</p></section>'
        f"{selected_html}"
        f'<section class="card-grid">{"".join(cards) if cards else "<p>No configured sources found.</p>"}</section>'
        '</div>'
    )


def source_signal_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>No source-linked signals recorded yet.</p>"
    chunks = []
    for item in rows:
        chunks.append(
            f"""<article class="row">
  <h2><a href="{esc(item['source_url'])}">{esc(item['title'])}</a></h2>
  <p class="meta"><span class="tag">{esc(item['category'] or 'uncategorized')}</span>score {esc(item['score'])} · captured {esc(item['collected_at'] or 'unknown')}</p>
</article>"""
        )
    return "".join(chunks)


def source_opportunity_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>No source-linked opportunities indexed yet.</p>"
    chunks = []
    for item in rows:
        chunks.append(
            f"""<article class="row">
  <h2>{esc(item['title'])}</h2>
  <p class="meta"><span class="tag">{esc(item['category'] or 'uncategorized')}</span>{esc(item['target_user'])} · score {esc(item['opportunity_score'])} · evidence {esc(item['evidence_count'])}</p>
</article>"""
        )
    return "".join(chunks)


def source_detail_page(source_entry: dict[str, Any], detail: dict[str, Any]) -> str:
    risk = source_entry["risk"]
    config_items = "".join(
        f'<div class="mini-item"><strong>{esc(key)}</strong><div class="subtle">{esc(value)}</div></div>'
        for key, value in sorted(source_entry["config"].items())
    ) or '<p class="subtle">No source-specific config captured.</p>'
    return f"""<div class="stack">
  <section class="toolbar">
    <p class="subtle"><a href="/sources">Source list</a> / {esc(source_entry['key'])}</p>
    <a href="/opportunities?source={quote_plus(source_entry['key'])}">Open linked opportunities</a>
  </section>
  <section class="panel">
    <div class="detail-grid">
      <div>
        <p class="list-head">Policy status</p>
        <h2>{esc(source_entry['key'])}</h2>
        <p class="meta">{policy_status_badge(str(source_entry['policy_status']))}<span class="tag">{esc(source_entry['kind'])}</span></p>
        <p>{esc(source_entry['notes'] or 'No operator notes recorded.')}</p>
        <p class="subtle">Signals {esc(detail['signal_count'])} · opportunities {esc(detail['opportunity_count'])} · avg score {esc(detail['avg_score'])}</p>
        <p class="subtle">Latest signal captured: {esc(detail['latest_signal_at'] or 'none yet')}</p>
        <p class="subtle">Ingest health: {health_status_badge(str(detail.get('health_status') or 'unknown'))} latest run {esc(detail.get('last_ingest_at') or 'unknown')}</p>
      </div>
      <div>
        <p class="list-head">Safety metadata</p>
        <div class="mini-list">
          <div class="mini-item"><strong>Credentials</strong><div class="subtle">{esc(risk['credentials'])}</div></div>
          <div class="mini-item"><strong>Terms</strong><div class="subtle">{esc(risk['terms'])}</div></div>
          <div class="mini-item"><strong>Rate limits</strong><div class="subtle">{esc(risk['rate_limits'])}</div></div>
          <div class="mini-item"><strong>Scraping</strong><div class="subtle">{esc(risk['scraping'])}</div></div>
          <div class="mini-item"><strong>PII / UGC</strong><div class="subtle">{esc(risk['pii_user_generated_content'])}</div></div>
          <div class="mini-item"><strong>Hosted dependencies</strong><div class="subtle">{esc(risk['hosted_dependencies'])}</div></div>
        </div>
      </div>
    </div>
  </section>
  {source_detail_panel(detail)}
  {selected_source_record_panel(detail)}
  <section class="row">
    <section class="toolbar">
      <div>
        <p class="list-head">Recent source records</p>
        <p class="subtle">Review the latest source-linked signals and opportunity records without leaving the dashboard.</p>
      </div>
      <div class="toolbar-links">
        <a href="/search?source={quote_plus(source_entry['key'])}">Open search results</a>
        <a href="/opportunities?source={quote_plus(source_entry['key'])}">Open opportunity view</a>
      </div>
    </section>
    <div class="detail-grid">
      <div>
        <p class="list-head">Recent signals</p>
        <section class="row-grid">{source_signal_rows(detail["signals"])}</section>
      </div>
      <div>
        <p class="list-head">Recent opportunities</p>
        <section class="row-grid">{source_opportunity_rows(detail["opportunities"])}</section>
      </div>
    </div>
  </section>
  <section class="row">
    <p class="list-head">Config snapshot</p>
    <div class="mini-list">{config_items}</div>
  </section>
</div>"""


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
                ("pain", "pain"),
                ("freshness", "freshness"),
                ("recurrence", "recurrence"),
                ("source_quality", "source"),
                ("build_fit", "fit"),
            )
        )
        chunks.append(
            f"""<article class="row">
  <div class="signal-head">
    <div>
      <h2><a href="/opportunities/{esc(row['id'])}">{esc(row['title'])}</a></h2>
      <div class="meta">{source_drill_in(str(row['source']), str(row['source']) or 'source')}<span class="tag">{esc(row['target_user'])}</span> evidence={esc(row['evidence_count'])}</div>
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


def shortlist_rows(rows: list[Any]) -> str:
    if not rows:
        return '<p class="subtle">No opportunities match the current shortlist filters.</p>'
    chunks = []
    for row in rows:
        detail_path = f"/opportunities/{esc(row['id'])}"
        export_path = f"{detail_path}#task-draft-preview"
        chunks.append(
            f"""<article class="row">
  <div class="signal-head">
    <div>
      <h2><a href="{detail_path}">{esc(row['title'])}</a></h2>
      <div class="meta">{source_drill_in(str(row['source']), str(row['source']) or 'source')}<span class="tag">{esc(row['category'] or 'uncategorized')}</span><span class="tag">{esc(row['target_user'] or 'no target user')}</span></div>
    </div>
    <div class="score">score {esc(row['opportunity_score'])}</div>
  </div>
  <p class="subtle">{esc(row['problem'] or 'No problem statement captured.')}</p>
  <div class="toolbar-links">
    <a href="{detail_path}">View detail</a>
    <a href="{export_path}">Open export</a>
  </div>
</article>"""
        )
    return "".join(chunks)


def draft_preview_text(payload: dict[str, Any]) -> str:
    draft_task = payload["draft_task"]
    score_components = payload.get("score_components", {}).get("components", {})
    return "\n".join(
        [
            f"Title: {draft_task['title']}",
            f"Target user: {draft_task['target_user']}",
            f"Category: {draft_task['category']}",
            f"Source: {draft_task['source']}",
            f"Problem: {draft_task['problem']}",
            f"Evidence count: {draft_task['evidence_count']}",
            f"Score: {payload.get('opportunity_score', 0)}",
            (
                "Score breakdown: "
                f"pain {score_components.get('pain', 0)}, "
                f"freshness {score_components.get('freshness', 0)}, "
                f"recurrence {score_components.get('recurrence', 0)}, "
                f"source {score_components.get('source_quality', 0)}, "
                f"fit {score_components.get('build_fit', 0)}"
            ),
            f"Iteration angle: {draft_task['iteration_angle']}",
            f"Monetization strategy: {draft_task['monetization_strategy']}",
            f"Build difficulty: {draft_task['build_difficulty']}",
            f"Replication estimate: {draft_task['replication_time_estimate']}",
            f"Competing products: {draft_task['competing_products']}",
            f"What products do right: {draft_task['what_products_do_right']}",
            f"What users want better: {draft_task['what_users_want_better']}",
            f"Foundry task suggestion: {draft_task['foundry_task_suggestions']}",
        ]
    )


def linked_signal_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="subtle">No linked signal evidence matched this opportunity.</p>'
    chunks = []
    for item in rows:
        chunks.append(
            f"""<article class="row">
  <h2><a href="{esc(item['source_url'])}">{esc(item['title'])}</a></h2>
  <p class="meta">{source_drill_in(str(item['source']))}<span class="tag">{esc(item['product'] or 'no product')}</span><span class="tag">{esc(item['category'] or 'uncategorized')}</span>score {esc(item['score'])}</p>
  <p class="excerpt">{esc(item['body'] or 'No excerpt captured for this signal.')}</p>
  <p class="subtle">Pain: {esc(item['pain_type'] or 'n/a')} · feature gap: {esc(item['feature_request'] or 'n/a')}</p>
</article>"""
        )
    return "".join(chunks)


def linked_product_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="subtle">No linked products matched this opportunity.</p>'
    chunks = []
    for item in rows:
        chunks.append(
            f"""<article class="row">
  <h2><a href="{esc(item['url'])}">{esc(item['product_name'])}</a></h2>
  <p class="meta"><span class="tag">{esc(item['category'] or 'uncategorized')}</span>{esc(item['pricing_model'] or 'pricing n/a')} · {esc(item['audience'] or 'audience n/a')}</p>
  <p><strong>Strengths:</strong> {esc(item['strengths'] or 'No strengths captured.')}</p>
  <p><strong>Feature gaps:</strong> {esc(item['feature_gaps'] or 'No feature gaps captured.')}</p>
</article>"""
        )
    return "".join(chunks)


def opportunity_detail_page(payload: dict[str, Any], related: dict[str, list[dict[str, Any]]]) -> str:
    score_components = payload.get("score_components", {})
    components = score_components.get("components", {})
    inputs = score_components.get("inputs", {})
    weights = score_components.get("weights", {})
    draft_text = draft_preview_text(payload)
    linked_source = payload.get("linked_source_context") or {}
    source_context = payload["source_context"]
    return f"""<div class="stack">
  <section class="toolbar">
    <p class="subtle"><a href="/opportunities">Opportunity list</a> / {esc(payload['title'])}</p>
    <div class="toolbar-links">
      <a href="{esc(source_context['detail_path'])}">Open source detail</a>
      <a href="{esc(source_context['search_path'])}">Open source context</a>
    </div>
  </section>
  <section class="panel">
    <div class="detail-grid">
      <div>
        <p class="list-head">Opportunity</p>
        <h2>{esc(payload['title'])}</h2>
        <p class="meta">{source_drill_in(str(payload['source']))}<span class="tag">{esc(payload['category'] or 'uncategorized')}</span><span class="tag">{esc(payload['target_user'] or 'no target user')}</span> evidence {esc(payload['evidence_count'])}</p>
        <p>{esc(payload['problem'] or 'No problem statement captured.')}</p>
        <div class="mini-list">
          <div class="mini-item"><strong>Iteration angle</strong><div class="subtle">{esc(payload['iteration_angle'] or 'n/a')}</div></div>
          <div class="mini-item"><strong>Monetization strategy</strong><div class="subtle">{esc(payload['monetization_strategy'] or 'n/a')}</div></div>
          <div class="mini-item"><strong>Build difficulty</strong><div class="subtle">{esc(payload['build_difficulty'] or 'n/a')} · replication {esc(payload['replication_time_estimate'] or 'n/a')}</div></div>
          <div class="mini-item"><strong>Products in play</strong><div class="subtle">{esc(payload['competing_products'] or 'No linked products captured.')}</div></div>
        </div>
      </div>
      <div>
        <p class="list-head">Evidence summary</p>
        <div class="mini-list">
          <div class="mini-item"><strong>Score</strong><div class="subtle">{esc(payload['opportunity_score'])}</div></div>
          <div class="mini-item"><strong>Source context</strong><div class="subtle">{esc(linked_source.get('signal_count', 0))} signals · {esc(linked_source.get('opportunity_count', 0))} source-linked opportunities · avg signal score {esc(linked_source.get('avg_score', 0))}</div></div>
          <div class="mini-item"><strong>What products do right</strong><div class="subtle">{esc(payload['what_products_do_right'] or 'n/a')}</div></div>
          <div class="mini-item"><strong>What users want better</strong><div class="subtle">{esc(payload['what_users_want_better'] or 'n/a')}</div></div>
          <div class="mini-item"><strong>Foundry task suggestion</strong><div class="subtle">{esc(payload['foundry_task_suggestions'] or 'n/a')}</div></div>
        </div>
      </div>
    </div>
  </section>
  <section class="row">
    <section class="toolbar">
      <div>
        <p class="list-head">Score breakdown</p>
        <p class="subtle">Read-only scoring inputs and weighted contribution for this opportunity.</p>
      </div>
    </section>
    <div class="scan-grid">
      <div class="metric"><strong>{esc(components.get('pain', 0))}</strong><span>Pain contribution · input {esc(inputs.get('pain', 0))} · weight {esc(weights.get('pain', 0))}</span></div>
      <div class="metric"><strong>{esc(components.get('freshness', 0))}</strong><span>Freshness contribution · input {esc(inputs.get('freshness', 0))} · weight {esc(weights.get('freshness', 0))}</span></div>
      <div class="metric"><strong>{esc(components.get('recurrence', 0))}</strong><span>Recurrence contribution · input {esc(inputs.get('recurrence', 0))} · weight {esc(weights.get('recurrence', 0))}</span></div>
      <div class="metric"><strong>{esc(components.get('source_quality', 0))}</strong><span>Source quality contribution · input {esc(inputs.get('source_quality', 0))} · weight {esc(weights.get('source_quality', 0))}</span></div>
      <div class="metric"><strong>{esc(components.get('build_fit', 0))}</strong><span>Build fit contribution · input {esc(inputs.get('build_fit', 0))} · weight {esc(weights.get('build_fit', 0))}</span></div>
    </div>
  </section>
  <section class="row" id="task-draft-preview">
    <section class="toolbar">
      <div>
        <p class="list-head">Task draft preview</p>
        <p class="subtle">Copy-ready read-only export built from the current opportunity details.</p>
      </div>
    </section>
    <textarea readonly="readonly">{esc(draft_text)}</textarea>
  </section>
  <section class="row">
    <section class="toolbar">
      <div>
        <p class="list-head">Linked evidence</p>
        <p class="subtle">Signals and products matched from the current source, category, and referenced products.</p>
      </div>
    </section>
    <div class="detail-grid">
      <div>
        <p class="list-head">Signals</p>
        <section class="row-grid">{linked_signal_rows(related['signals'])}</section>
      </div>
      <div>
        <p class="list-head">Products</p>
        <section class="row-grid">{linked_product_rows(related['products'])}</section>
      </div>
    </div>
  </section>
</div>"""


def api_pagination_value(raw: str, *, default: int, minimum: int = 0, maximum: int = 100) -> int:
    try:
        value = int((raw or "").strip() or str(default))
    except ValueError:
        return default
    return max(minimum, min(value, maximum))


def api_search_filters(params: dict[str, list[str]]) -> dict[str, object]:
    return {
        "query": params.get("q", [""])[0],
        "source": params.get("source", [""])[0],
        "category": params.get("market", params.get("category", [""]))[0],
        "product": params.get("product", [""])[0],
        "pain_type": params.get("pain", params.get("pain_type", [""]))[0],
        "feature_request": params.get("feature_gap", params.get("feature_request", [""]))[0],
        "limit": api_pagination_value(params.get("limit", ["50"])[0], default=50, minimum=1),
        "offset": api_pagination_value(params.get("offset", ["0"])[0], default=0),
    }


def min_score_options(values: list[str], selected: str) -> str:
    options = ['<option value="">Any score</option>']
    for value in values:
        active = ' selected="selected"' if value == selected else ""
        options.append(f'<option value="{esc(value)}"{active}>Score {esc(value)}+</option>')
    return f'<select name="min_score">{"".join(options)}</select>'


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

    def health_payload(self) -> tuple[HTTPStatus, dict[str, Any]]:
        try:
            db_path = storage_path(self.config)
            conn = connect(db_path)
            conn.close()
        except Exception as exc:
            return (
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "ok": False,
                    "service": "wayfinder",
                    "config": "loaded",
                    "database": "unavailable",
                    "error": str(exc),
                },
            )
        return (
            HTTPStatus.OK,
            {
                "ok": True,
                "service": "wayfinder",
                "config": "loaded",
                "database": "ready",
                "storage_path": str(db_path),
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        selected_signal = params.get("signal", [""])[0]
        selected_record = params.get("record", [""])[0]
        if parsed.path == "/health":
            status, payload = self.health_payload()
            self.send_json(payload, status)
            return
        conn = connect(storage_path(self.config))
        try:
            if parsed.path == "/":
                query = params.get("q", [""])[0]
                source = params.get("source", [""])[0]
                category = params.get("market", params.get("category", [""]))[0]
                min_score_raw = params.get("min_score", [""])[0].strip()
                product = params.get("product", [""])[0]
                pain_type = params.get("pain", [""])[0]
                feature_request = params.get("feature_gap", [""])[0]
                try:
                    min_score = float(min_score_raw) if min_score_raw else None
                except ValueError:
                    min_score = None
                metric_html = "".join(
                    f'<div class="metric"><strong>{value}</strong><span>{esc(name)}</span></div>'
                    for name, value in counts(conn).items()
                )
                values = signal_filter_values(conn)
                opportunity_values = opportunity_filter_values(conn)
                source_payload = source_catalog_payload(self.config)
                dashboard_sources = [item["key"] for item in source_payload["sources"]]
                activity_by_source = {name: source_activity(conn, name) for name in dashboard_sources}
                rows = browse_signals(
                    conn,
                    query=query,
                    source=source,
                    category=category,
                    product=product,
                    pain_type=pain_type,
                    feature_request=feature_request,
                    limit=30,
                )
                shortlist = filtered_opportunities(
                    conn,
                    source=source,
                    category=category,
                    min_score=min_score,
                    limit=5,
                )
                detail = source_detail(conn, source, signal_id=selected_signal, source_url=selected_record)
                active_filters = active_filter_summary(
                    [
                        ("product", product),
                        ("market", category),
                        ("min score", min_score_raw),
                        ("source", source),
                        ("pain", pain_type),
                        ("feature gap", feature_request),
                    ]
                )
                summary = (
                    f'<section class="toolbar"><div><p class="subtle">Showing {len(rows)} signal rows across '
                    f'product, market, source, pain, and feature-gap filters.</p>{active_filters}</div>'
                    f'<div class="toolbar-links"><a href="/sources">Browse sources</a>'
                    f'<a href="/search?q={esc(query)}">Open search results</a><a href="/">Clear filters</a></div></section>'
                )
                body = (
                    f'<div class="stack"><section class="grid">{metric_html}</section>'
                    f'{filter_form("/", query=query, source=source, category=category, product=product, pain_type=pain_type, feature_request=feature_request, values=values, include_category=False, include_product=True, include_market=True, include_pain_type=True, include_feature_request=True)}'
                    f"""<section class="panel">
  <form class="filters" method="get" action="/">
    <input type="hidden" name="q" value="{esc(query)}">
    <input type="hidden" name="source" value="{esc(source)}">
    <input type="hidden" name="market" value="{esc(category)}">
    <input type="hidden" name="product" value="{esc(product)}">
    <input type="hidden" name="pain" value="{esc(pain_type)}">
    <input type="hidden" name="feature_gap" value="{esc(feature_request)}">
    {min_score_options(opportunity_values.get("min_scores", opportunity_score_filter_values(conn)), min_score_raw)}
    <button type="submit">Apply shortlist score floor</button>
  </form>
</section>"""
                    f"""<section class="row">
  <section class="toolbar">
    <div>
      <p class="list-head">Top opportunities</p>
      <p class="subtle">Highest-scoring read-only opportunities for the current source, market, and score filters.</p>
    </div>
    <div class="toolbar-links">
      <a href="/opportunities?source={quote_plus(source)}&category={quote_plus(category)}&min_score={quote_plus(min_score_raw)}">Open full opportunity view</a>
    </div>
  </section>
  <section class="row-grid">{shortlist_rows(shortlist)}</section>
</section>"""
                    f'{source_directory(dashboard_sources, source, activity_by_source)}'
                    f'{source_detail_panel(detail)}{summary}<section class="row-grid">{signal_rows(rows)}</section></div>'
                )
                self.send_html("Dashboard", body)
                return
            if parsed.path == "/search":
                query = params.get("q", [""])[0]
                source = params.get("source", [""])[0]
                category = params.get("market", params.get("category", [""]))[0]
                product = params.get("product", [""])[0]
                pain_type = params.get("pain", [""])[0]
                feature_request = params.get("feature_gap", [""])[0]
                values = signal_filter_values(conn)
                if (
                    not query.strip()
                    and not source.strip()
                    and not category.strip()
                    and not product.strip()
                    and not pain_type.strip()
                    and not feature_request.strip()
                ):
                    rows = search_signals(conn, query, 30)
                elif (
                    query.strip()
                    and not source.strip()
                    and not category.strip()
                    and not product.strip()
                    and not pain_type.strip()
                    and not feature_request.strip()
                ):
                    rows = search_signals(conn, query, 30)
                else:
                    rows = browse_signals(
                        conn,
                        query=query,
                        source=source,
                        category=category,
                        product=product,
                        pain_type=pain_type,
                        feature_request=feature_request,
                        limit=30,
                    )
                detail = source_detail(conn, source, signal_id=selected_signal, source_url=selected_record)
                form = filter_form(
                    "/search",
                    query=query,
                    source=source,
                    category=category,
                    product=product,
                    pain_type=pain_type,
                    feature_request=feature_request,
                    values=values,
                    placeholder="Search pains, products, markets",
                    include_category=True,
                    include_product=True,
                    include_pain_type=True,
                    include_feature_request=True,
                    submit_label="Search",
                )
                active_filters = active_filter_summary(
                    [
                        ("query", query),
                        ("source", source),
                        ("category", category),
                        ("product", product),
                        ("pain", pain_type),
                        ("feature gap", feature_request),
                    ]
                )
                source_payload = source_catalog_payload(self.config)
                search_sources = [item["key"] for item in source_payload["sources"]]
                activity_by_source = {name: source_activity(conn, name) for name in search_sources}
                summary = (
                    f'<section class="toolbar"><div><p class="subtle">Search returned {len(rows)} rows with URL-backed filters.</p>'
                    f'{active_filters}</div><div class="toolbar-links">'
                    f'<a href="/?q={esc(query)}&source={quote_plus(source)}&market={quote_plus(category)}&product={quote_plus(product)}&pain={quote_plus(pain_type)}&feature_gap={quote_plus(feature_request)}">Use dashboard browse view</a>'
                    f'<a href="/search">Clear filters</a></div></section>'
                )
                self.send_html(
                    "Search",
                    f'<div class="stack">{form}{source_directory(search_sources, source, activity_by_source)}{source_detail_panel(detail)}{summary}<section class="row-grid">{signal_rows(rows)}</section></div>',
                )
                return
            if parsed.path == "/api/search":
                filters = api_search_filters(params)
                query = str(filters["query"])
                if (
                    not query.strip()
                    and not str(filters["source"]).strip()
                    and not str(filters["category"]).strip()
                    and not str(filters["product"]).strip()
                    and not str(filters["pain_type"]).strip()
                    and not str(filters["feature_request"]).strip()
                ):
                    rows = search_signals(conn, query, int(filters["limit"]), offset=int(filters["offset"]))
                elif (
                    query.strip()
                    and not str(filters["source"]).strip()
                    and not str(filters["category"]).strip()
                    and not str(filters["product"]).strip()
                    and not str(filters["pain_type"]).strip()
                    and not str(filters["feature_request"]).strip()
                ):
                    rows = search_signals(conn, query, int(filters["limit"]), offset=int(filters["offset"]))
                else:
                    rows = browse_signals(
                        conn,
                        query=query,
                        source=str(filters["source"]),
                        category=str(filters["category"]),
                        product=str(filters["product"]),
                        pain_type=str(filters["pain_type"]),
                        feature_request=str(filters["feature_request"]),
                        limit=int(filters["limit"]),
                        offset=int(filters["offset"]),
                    )
                self.send_json([dict(row) for row in rows])
                return
            if parsed.path == "/api/sources":
                source_name = params.get("source", [""])[0]
                payload = source_catalog_payload(self.config, source_name)
                if source_name.strip() and payload["source"] is None:
                    self.send_json(
                        {
                            "error": "source_not_found",
                            "requested_source": source_name.strip(),
                            "available_sources": [item["key"] for item in payload["sources"]],
                        },
                        HTTPStatus.NOT_FOUND,
                    )
                    return
                self.send_json(payload)
                return
            if parsed.path == "/api/products":
                category = params.get("category", params.get("market", [""]))[0]
                limit = api_pagination_value(params.get("limit", ["50"])[0], default=50, minimum=1)
                offset = api_pagination_value(params.get("offset", ["0"])[0], default=0)
                rows = filtered_products(conn, category=category, limit=limit, offset=offset)
                self.send_json([dict(row) for row in rows])
                return
            if parsed.path == "/api/opportunities":
                source = params.get("source", [""])[0]
                category = params.get("category", params.get("market", [""]))[0]
                min_score_raw = params.get("min_score", [""])[0].strip()
                try:
                    min_score = float(min_score_raw) if min_score_raw else None
                except ValueError:
                    min_score = None
                limit = api_pagination_value(params.get("limit", ["50"])[0], default=50, minimum=1)
                offset = api_pagination_value(params.get("offset", ["0"])[0], default=0)
                rows = filtered_opportunities(
                    conn,
                    source=source,
                    category=category,
                    min_score=min_score,
                    limit=limit,
                    offset=offset,
                )
                payload = []
                for row in rows:
                    payload.append(opportunity_export_payload(row))
                self.send_json(payload)
                return
            if parsed.path.startswith("/api/opportunities/"):
                identifier = unquote(parsed.path.removeprefix("/api/opportunities/")).strip()
                row = opportunity_detail(conn, identifier)
                if row is None:
                    self.send_json(
                        {
                            "error": "opportunity_not_found",
                            "requested_identifier": identifier,
                        },
                        HTTPStatus.NOT_FOUND,
                    )
                    return
                payload = opportunity_export_payload(row)
                payload["linked_source_context"] = source_detail(
                    conn,
                    str(payload.get("source") or ""),
                )
                self.send_json(payload)
                return
            if parsed.path == "/sources":
                payload = source_status_overview(self.config)
                query = params.get("q", [""])[0]
                source = params.get("source", [""])[0]
                category = params.get("market", params.get("category", [""]))[0]
                product = params.get("product", [""])[0]
                pain_type = params.get("pain", [""])[0]
                feature_request = params.get("feature_gap", [""])[0]
                values = signal_filter_values(conn)
                detail = source_detail(conn, source, signal_id=selected_signal, source_url=selected_record)
                rows = (
                    browse_signals(
                        conn,
                        query=query,
                        source=source,
                        category=category,
                        product=product,
                        pain_type=pain_type,
                        feature_request=feature_request,
                        limit=30,
                    )
                    if source.strip()
                    else []
                )
                activity_by_source = {item["key"]: source_activity(conn, item["key"]) for item in payload["sources"]}
                body = (
                    f'<div class="stack">{source_list_page(payload, activity_by_source, source, detail)}'
                    f'{filter_form("/sources", query=query, source=source, category=category, product=product, pain_type=pain_type, feature_request=feature_request, values=values, include_category=False, include_product=True, include_market=True, include_pain_type=True, include_feature_request=True, submit_label="Inspect")}'
                    f'{source_detail_panel(detail)}'
                    f'<section class="toolbar"><p class="subtle">Showing {len(rows)} source-linked signal rows.</p><a href="/opportunities?source={quote_plus(source)}">Open source opportunities</a></section>'
                    f'<section class="row-grid">{signal_rows(rows) if source.strip() else "<p>Select a source to inspect its linked signals and opportunities.</p>"}</section></div>'
                )
                self.send_html("Sources", body)
                return
            if parsed.path.startswith("/sources/"):
                source_name = unquote(parsed.path.removeprefix("/sources/")).strip()
                payload = source_catalog_payload(self.config, source_name)
                source_entry = payload["source"]
                if source_entry is None:
                    self.send_html(
                        "Source Not Found",
                        (
                            f'<div class="stack"><section class="row"><h2>Source not found</h2>'
                            f'<p class="subtle">No configured source matches <code>{esc(source_name)}</code>.</p>'
                            f'<p><a href="/sources">Return to the source list</a></p></section></div>'
                        ),
                        HTTPStatus.NOT_FOUND,
                    )
                    return
                detail = source_activity(conn, source_name, signal_id=selected_signal, source_url=selected_record)
                self.send_html("Source Detail", source_detail_page(source_entry, detail))
                return
            if parsed.path == "/products":
                category = params.get("category", [""])[0]
                pricing_model = params.get("pricing", [""])[0]
                complaint = params.get("complaint", [""])[0]
                values = product_filter_values(conn)
                rows = filtered_products(
                    conn,
                    category=category,
                    pricing_model=pricing_model,
                    complaint=complaint,
                    limit=50,
                )
                filters = filter_form(
                    "/products",
                    category=category,
                    pricing_model=pricing_model,
                    complaint=complaint,
                    values=values,
                    include_query=False,
                    include_source=False,
                    include_pricing=True,
                    include_complaint=True,
                )
                browse_summary = active_filter_summary(
                    [("category", category), ("pricing", pricing_model), ("complaint", complaint)]
                )
                body = (
                    f'<div class="stack">{filters}<section class="toolbar"><div><p class="subtle">{len(rows)} products indexed.</p>'
                    f"{browse_summary}</div><div class=\"toolbar-links\"><a href=\"/products\">Clear filters</a></div></section>"
                    f'<section class="row-grid">{product_rows(rows)}</section></div>'
                )
                self.send_html("Products", body)
                return
            if parsed.path == "/opportunities":
                source = params.get("source", [""])[0]
                category = params.get("category", [""])[0]
                min_score_raw = params.get("min_score", [""])[0].strip()
                try:
                    min_score = float(min_score_raw) if min_score_raw else None
                except ValueError:
                    min_score = None
                values = opportunity_filter_values(conn)
                rows = filtered_opportunities(conn, source=source, category=category, min_score=min_score, limit=50)
                detail = source_detail(conn, source, signal_id=selected_signal, source_url=selected_record)
                filters = filter_form(
                    "/opportunities",
                    source=source,
                    category=category,
                    values=values,
                    include_query=False,
                )
                score_filter = f"""<section class="panel">
  <form class="filters" method="get" action="/opportunities">
    <input type="hidden" name="source" value="{esc(source)}">
    <input type="hidden" name="category" value="{esc(category)}">
    {min_score_options(values.get("min_scores", opportunity_score_filter_values(conn)), min_score_raw)}
    <button type="submit">Apply score floor</button>
  </form>
</section>"""
                browse_summary = (
                    f'<section class="toolbar"><div><p class="subtle">{len(rows)} opportunities indexed.</p>'
                    f'{active_filter_summary([("source", source), ("category", category), ("min score", min_score_raw)])}</div>'
                    f'<div class="toolbar-links"><a href="/sources{("?source=" + quote_plus(source)) if source.strip() else ""}">Open source view</a><a href="/opportunities">Clear filters</a></div></section>'
                )
                body = f'<div class="stack">{filters}{score_filter}{source_detail_panel(detail)}{browse_summary}<section class="row-grid">{opportunity_rows(rows)}</section></div>'
                self.send_html("Opportunities", body)
                return
            if parsed.path.startswith("/opportunities/"):
                identifier = unquote(parsed.path.removeprefix("/opportunities/")).strip()
                row = opportunity_detail(conn, identifier)
                if row is None:
                    self.send_html(
                        "Opportunity Not Found",
                        (
                            f'<div class="stack"><section class="row"><h2>Opportunity not found</h2>'
                            f'<p class="subtle">No opportunity matches <code>{esc(identifier)}</code>.</p>'
                            f'<p><a href="/opportunities">Return to opportunities</a></p></section></div>'
                        ),
                        HTTPStatus.NOT_FOUND,
                    )
                    return
                payload = opportunity_export_payload(row)
                payload["linked_source_context"] = source_detail(conn, str(payload.get("source") or ""))
                related = opportunity_related_context(conn, row)
                self.send_html("Opportunity Detail", opportunity_detail_page(payload, related))
                return
            self.send_html("Not Found", "<p>Not found.</p>", HTTPStatus.NOT_FOUND)
        finally:
            conn.close()


def serve(config: dict[str, Any], host: str = "127.0.0.1", port: int = 8766) -> None:
    WayfinderHandler.config = config
    server = ThreadingHTTPServer((host, port), WayfinderHandler)
    print(f"Wayfinder dashboard running at http://{host}:{port}")
    server.serve_forever()
