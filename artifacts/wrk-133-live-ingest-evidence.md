## `python3 -m wayfinder sources list --health --no-color`

```text
oss-ledger status=enabled kind=static_ledger credentials=none terms=reviewed-public-data rate_limits=none-local-file scraping=none pii_ugc=low-curated-public-metadata hosted_dependencies=none
  review=approved unattended=eligible why=Curated local ledger with explicit repository inputs and no unattended network dependency.
  notes=Curated local ledger with explicit repository inputs and no unattended network dependency.
  health=ok /mnt/d/AI/codex-foundry/workspace/tasks/WRK-133/research/open-source-intel-ledger.yaml
hackernews status=dry-run-only kind=hackernews credentials=none terms=review-required rate_limits=review-required scraping=api-search pii_ugc=medium-user-generated-content hosted_dependencies=algolia-hn-api
  review=pending unattended=blocked why=Manual testing only until review items are cleared. unresolved=terms,rate_limits notes=Deterministic fixture-backed dry runs are allowed; unattended live Algolia ingest still needs review for UGC handling and query-rate expectations.
  notes=Deterministic fixture-backed dry runs are allowed; unattended live Algolia ingest still needs review for UGC handling and query-rate expectations.
  health=ok HN deterministic fixture configured with 3 queries via /mnt/d/AI/codex-foundry/workspace/tasks/WRK-133/research/hackernews-sample.json
github status=enabled kind=github credentials=none terms=public-api-allowed rate_limits=low-volume-public-search scraping=official-api pii_ugc=low-public-repo-metadata hosted_dependencies=github-public-api
  review=approved unattended=eligible why=Approved for daily anonymous public repository search at the configured low query volume; dry runs stay fixture-backed for diagnostics while scheduled and normal ingest use the live official API.
  notes=Approved for daily anonymous public repository search at the configured low query volume; dry runs stay fixture-backed for diagnostics while scheduled and normal ingest use the live official API.
  health=ok GitHub deterministic fixture configured with 3 queries via /mnt/d/AI/codex-foundry/workspace/tasks/WRK-133/research/github-sample.json
```

Exit code: 0

## `python3 -m wayfinder scheduled-ingest --no-color`

```text
oss-ledger: raw=8 inserted signals=8 products=8 opportunities=8
hackernews: skipped status=dry-run-only
github: raw=29 inserted signals=29 products=29 opportunities=29
```

Exit code: 0

## `python3 -m wayfinder search saas --limit 5 --no-color`

```text
1. gracp/saas-generator | github | market research SaaS ideas
   source_url: https://github.com/gracp/saas-generator
   body: AI-powered SaaS idea generator — from market research to launch; stars=0, updated=2026-04-09T02:49:11Z, language=TypeScript, license=unknown; market research SaaS ideas
2. marcoETmx/SaaS-Studio | github | market research SaaS ideas
   source_url: https://github.com/marcoETmx/SaaS-Studio
   body: Transform your SaaS idea into a thriving business with our proven 7-stage methodology. From initial research to market launch, SaaS Studio provides the structure, templates, and guidance indie hackers and entrepreneur...
3. ruanxinyang/micro-saas-validator | github | market research SaaS ideas
   source_url: https://github.com/ruanxinyang/micro-saas-validator
   body: Claude Code skill: validate product ideas with real market research; stars=1, updated=2026-04-14T07:48:56Z, language=unknown, license=unknown; market research SaaS ideas
4. sinan-mohammed/AI-SaaS-Idea-Validator | github | market research SaaS ideas
   source_url: https://github.com/sinan-mohammed/AI-SaaS-Idea-Validator
   body: AI-SaaS-Idea-Validator is a multi-agent AI system designed to automatically evaluate startup ideas by performing structured market research, competitor analysis, monetization planning, and risk assessment.; stars=0, u...
5. PhumudzoSly/ray | github | ai, saas, saas-application, validation
   source_url: https://github.com/PhumudzoSly/ray
   body: Ray is an open-source SaaS idea validation and product development platform that combines project management with AI-powered market research and validation tools. It helps entrepreneurs and product teams validate thei...
```

Exit code: 0

## `python3 -m wayfinder opportunities --limit 5 --no-color`

```text
1. Leverage reddit-research-mcp | score=58.95 | Codex Foundry operator
   components: pain=10.5 freshness=15.0 recurrence=6.6 source=14.25 fit=12.6
   inputs: pain=0.3 freshness=1.0 recurrence=0.33 source_quality=0.95 build_fit=0.84
   weights: pain=0.35 freshness=0.15 recurrence=0.2 source=0.15 fit=0.15
   reference_time: 2026-05-18T13:05:10.509519+00:00
   problem: Need reddit-research-mcp capability without rebuilding from scratch.
   iteration_angle: Review and adapt reddit-research-mcp patterns into Wayfinder adapters.
   monetization_strategy: internal leverage first; no subscription dependency by default
2. Inspect lefttree/reddit-pain-points for leverage | score=57.9 | Wayfinder operator
   components: pain=11.55 freshness=15.0 recurrence=6.6 source=14.55 fit=10.2
   inputs: pain=0.33 freshness=1.0 recurrence=0.33 source_quality=0.97 build_fit=0.68
   weights: pain=0.35 freshness=0.15 recurrence=0.2 source=0.15 fit=0.15
   reference_time: 2026-05-18T13:05:10.509519+00:00
   problem: 🎯 Discover software product ideas by mining Reddit for user pain points. AI-powered analysis with Gemini.
   iteration_angle: Reuse repository patterns, docs, or architecture from lefttree/reddit-pain-points where safe.
   monetization_strategy: open-source leverage or competitor/tool intelligence for future product bets
3. Inspect calvinrodrigues500/product-hunter for leverage | score=57.9 | Wayfinder operator
   components: pain=11.55 freshness=15.0 recurrence=6.6 source=14.55 fit=10.2
   inputs: pain=0.33 freshness=1.0 recurrence=0.33 source_quality=0.97 build_fit=0.68
   weights: pain=0.35 freshness=0.15 recurrence=0.2 source=0.15 fit=0.15
   reference_time: 2026-05-18T13:05:10.509519+00:00
   problem: A simple, local-first AI agent that analyzes WordPress and WooCommerce forum discussions to identify user pain points and generate 5 actionable plugin or startup ideas.
   iteration_angle: Reuse repository patterns, docs, or architecture from calvinrodrigues500/product-hunter where safe.
   monetization_strategy: open-source leverage or competitor/tool intelligence for future product bets
4. Inspect rizkiwijanarko/KickUp for leverage | score=56.7 | Wayfinder operator
   components: pain=11.55 freshness=15.0 recurrence=6.6 source=13.35 fit=10.2
   inputs: pain=0.33 freshness=1.0 recurrence=0.33 source_quality=0.89 build_fit=0.68
   weights: pain=0.35 freshness=0.15 recurrence=0.2 source=0.15 fit=0.15
   reference_time: 2026-05-18T13:05:10.509519+00:00
   problem: A Multi-Agent System for Autonomous Startup Discovery. The system mines real pain points from Reddit/HN, clusters them by theme with LLM, generates startup ideas via Qwen3-35B-A3B, and produces investor-ready pitch br...
   iteration_angle: Reuse repository patterns, docs, or architecture from rizkiwijanarko/KickUp where safe.
   monetization_strategy: open-source leverage or competitor/tool intelligence for future product bets
5. Inspect PhumudzoSly/ray for leverage | score=55.75 | Wayfinder operator
   components: pain=8.4 freshness=15.0 recurrence=7.6 source=14.55 fit=10.2
   inputs: pain=0.24 freshness=1.0 recurrence=0.38 source_quality=0.97 build_fit=0.68
   weights: pain=0.35 freshness=0.15 recurrence=0.2 source=0.15 fit=0.15
   reference_time: 2026-05-18T13:05:10.509519+00:00
   problem: Ray is an open-source SaaS idea validation and product development platform that combines project management with AI-powered market research and validation tools. It helps entrepreneurs and product teams validate thei...
   iteration_angle: Reuse repository patterns, docs, or architecture from PhumudzoSly/ray where safe.
   monetization_strategy: open-source leverage or competitor/tool intelligence for future product bets
```

Exit code: 0

## `python3 -m wayfinder stats --no-color`

```text
signals: 37
products: 37
opportunities: 37
ingest_runs: 2
source_activity:
  github: signals=29 opportunities=29 last_ingest_at=2026-05-18T13:05:10.540689+00:00 health=ok
  hackernews: signals=0 opportunities=0 last_ingest_at=never health=unknown
  oss-ledger: signals=8 opportunities=8 last_ingest_at=2026-05-18T13:05:06.802320+00:00 health=ok
```

Exit code: 0

## `curl -sSf http://127.0.0.1:8766/`

```text
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard - Wayfinder</title>
  <style>
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
.status-card { border-left: 6px solid #bfcab9; }
.status-card.good { border-left-color: #215228; background: #f4fbf2; }
.status-card.warn { border-left-color: #a66b00; background: #fff8e6; }
.status-card.bad { border-left-color: #7a1f1a; background: #fff1f0; }
.status-kicker { margin: 0 0 6px; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: #66746a; }
.source-card h2 { color: #102523; }
.toolbar-links { display: flex; gap: 10px; flex-wrap: wrap; }
.run-list { display: grid; gap: 10px; }
.copy-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.copy-status[data-state="ready"] { color: #66746a; }
.copy-status[data-state="success"] { color: #215228; font-weight: 700; }
.copy-status[data-state="error"] { color: #7a1f1a; font-weight: 700; }
@media (max-width: 760px) {
  header, main { padding-left: 18px; padding-right: 18px; }
  form.filters, .signal-head, .detail-grid { grid-template-columns: 1fr; }
  .score { text-align: left; }
  .source-title { flex-direction: column; }
}
</style>
</head>
<body>
  <header>
    <h1>Wayfinder</h1>
    <nav>
      <a href="/">Dashboard</a>
      <a href="/sources">Sources</a>
      <a href="/source-safety">Source Safety</a>
      <a href="/search">Search</a>
      <a href="/products">Products</a>
      <a href="/opportunities">Opportunities</a>
      <a href="/api/search?q=saas">API</a>
    </nav>
  </header>
  <main><div class="stack"><section class="grid"><div class="metric"><strong>0</strong><span>signals</span></div><div class="metric"><strong>0</strong><span>products</span></div><div class="metric"><strong>0</strong><span>opportunities</span></div><div class="metric"><strong>0</strong><span>ingest_runs</span></div></section><section class="panel">
  <form class="filters" method="get" action="/">
    <input name="q" value="" placeholder="Search titles, excerpts, products, categories"><select name="source"><option value="">All sources</option></select><select name="product"><option value="">All products</option></select><select name="market"><option value="">All markets</option></select><select name="pain"><option value="">All pains</option></select><select name="feature_gap"><option value="">All feature gaps</option></select><button type="submit">Filter</button>
  </form>
</section><section class="panel">
  <form class="filters" method="get" action="/">
    <input type="hidden" name="q" value="">
    <input type="hidden" name="source" value="">
    <input type="hidden" name="market" value="">
    <input type="hidden" name="product" value="">
    <input type="hidden" name="pain" value="">
    <input type="hidden" name="feature_gap" value="">
    <select name="freshness"><option value="" selected="selected">Any freshness</option><option value="7">Last 7 days</option><option value="30">Last 30 days</option><option value="90">Last 90 days</option></select>
    <select name="min_score"><option value="">Any score</option></select>
    <select name="max_score"><option value="">Any ceiling</option></select>
    <select name="opportunity_sort"><option value="score" selected="selected">Top score</option><option value="freshest">Freshest first</option><option value="evidence">Most evidence</option><option value="score_asc">Lowest score first</option></select>
    <button type="submit">Apply opportunity filters</button>
  </form>
</section><section class="row">
  <section class="toolbar">
    <div>
      <p class="list-head">Top opportunities</p>
      <p class="subtle">Read-only opportunities for the current source, freshness, and score filters.</p>
    </div>
    <div class="toolbar-links">
      <a href="/opportunities?source=&category=&min_score=">Open full opportunity view</a>
    </div>
  </section>
  <section class="row-grid"><p class="subtle">No opportunities match the current shortlist filters.</p></section>
</section><section class="panel"><section class="toolbar"><div><p class="list-head">Sources</p><p class="subtle">Open a dedicated source detail page directly from the dashboard.</p></div></section><section class="card-grid"><a class="row source-card" href="/sources/github">
  <p class="list-head">Source detail</p>
  <h2>github</h2>
  <p class="subtle">Signals 0 · opportunities 0</p>
  <p class="subtle">Avg score 0 · latest none yet</p>
</a><a class="row source-card" href="/sources/hackernews">
  <p class="list-head">Source detail</p>
  <h2>hackernews</h2>
  <p class="subtle">Signals 0 · opportunities 0</p>
  <p class="subtle">Avg score 0 · latest none yet</p>
</a><a class="row source-card" href="/sources/oss-ledger">
  <p class="list-head">Source detail</p>
  <h2>oss-ledger</h2>
  <p class="subtle">Signals 0 · opportunities 0</p>
  <p class="subtle">Avg score 0 · latest none yet</p>
</a></section></section><section class="toolbar"><div><p class="subtle">Showing 0 signal rows across product, market, source, freshness, pain, and feature-gap filters.</p><p class="subtle">No filters applied. Browse the highest-signal rows or jump into a source detail view.</p></div><div class="toolbar-links"><a href="/sources">Browse sources</a><a href="/search?q=">Open search results</a><a href="/">Clear filters</a></div></section><section class="row-grid"><p>No signals found yet. Run <code>wayfinder ingest --source oss-ledger</code>.</p></section></div></main>
</body>
</html>```

Exit code: 0

## `curl -sSf http://127.0.0.1:8766/search?q=saas`

```text
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Search - Wayfinder</title>
  <style>
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
.status-card { border-left: 6px solid #bfcab9; }
.status-card.good { border-left-color: #215228; background: #f4fbf2; }
.status-card.warn { border-left-color: #a66b00; background: #fff8e6; }
.status-card.bad { border-left-color: #7a1f1a; background: #fff1f0; }
.status-kicker { margin: 0 0 6px; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: #66746a; }
.source-card h2 { color: #102523; }
.toolbar-links { display: flex; gap: 10px; flex-wrap: wrap; }
.run-list { display: grid; gap: 10px; }
.copy-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.copy-status[data-state="ready"] { color: #66746a; }
.copy-status[data-state="success"] { color: #215228; font-weight: 700; }
.copy-status[data-state="error"] { color: #7a1f1a; font-weight: 700; }
@media (max-width: 760px) {
  header, main { padding-left: 18px; padding-right: 18px; }
  form.filters, .signal-head, .detail-grid { grid-template-columns: 1fr; }
  .score { text-align: left; }
  .source-title { flex-direction: column; }
}
</style>
</head>
<body>
  <header>
    <h1>Wayfinder</h1>
    <nav>
      <a href="/">Dashboard</a>
      <a href="/sources">Sources</a>
      <a href="/source-safety">Source Safety</a>
      <a href="/search">Search</a>
      <a href="/products">Products</a>
      <a href="/opportunities">Opportunities</a>
      <a href="/api/search?q=saas">API</a>
    </nav>
  </header>
  <main><div class="stack"><section class="panel">
  <form class="filters" method="get" action="/search">
    <input name="q" value="saas" placeholder="Search pains, products, markets"><select name="source"><option value="">All sources</option></select><select name="category"><option value="">All categories</option></select><select name="product"><option value="">All products</option></select><select name="pain"><option value="">All pains</option></select><select name="feature_gap"><option value="">All feature gaps</option></select><button type="submit">Search</button>
  </form>
</section><section class="panel"><section class="toolbar"><div><p class="list-head">Sources</p><p class="subtle">Open a dedicated source detail page directly from the dashboard.</p></div></section><section class="card-grid"><a class="row source-card" href="/sources/github">
  <p class="list-head">Source detail</p>
  <h2>github</h2>
  <p class="subtle">Signals 0 · opportunities 0</p>
  <p class="subtle">Avg score 0 · latest none yet</p>
</a><a class="row source-card" href="/sources/hackernews">
  <p class="list-head">Source detail</p>
  <h2>hackernews</h2>
  <p class="subtle">Signals 0 · opportunities 0</p>
  <p class="subtle">Avg score 0 · latest none yet</p>
</a><a class="row source-card" href="/sources/oss-ledger">
  <p class="list-head">Source detail</p>
  <h2>oss-ledger</h2>
  <p class="subtle">Signals 0 · opportunities 0</p>
  <p class="subtle">Avg score 0 · latest none yet</p>
</a></section></section><section class="toolbar"><div><p class="subtle">Search returned 0 rows with URL-backed filters.</p><div><span class="tag active">query: saas</span></div></div><div class="toolbar-links"><a href="/?q=saas&source=&market=&product=&pain=&feature_gap=">Use dashboard browse view</a><a href="/search">Clear filters</a></div></section><section class="row-grid"><p>No signals found yet. Run <code>wayfinder ingest --source oss-ledger</code>.</p></section></div></main>
</body>
</html>```

Exit code: 0

## `tail -n 12 logs/wayfinder-audit.log`

```text
{"action": "wayfinder_scheduled_ingest_blocked", "llm_tokens": 0, "reason": "cron_disabled", "token_free": true, "ts": "2026-05-18T12:59:23.646881+00:00"}
{"action": "wayfinder_scheduled_ingest_started", "approved_source_count": 2, "enabled": true, "llm_tokens": 0, "schedule": "daily", "source_count": 3, "token_free": true, "ts": "2026-05-18T13:05:06.775508+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 33.038, "inserted_opportunities": 8, "inserted_products": 8, "inserted_signals": 8, "llm_tokens": 0, "normalized": 24, "raw_records": 8, "source": "oss-ledger", "token_free": true, "ts": "2026-05-18T13:05:06.810491+00:00"}
{"action": "wayfinder_scheduled_ingest_skipped", "llm_tokens": 0, "reason": "source_not_approved_for_unattended_ingest", "source": "hackernews", "status": "dry-run-only", "token_free": true, "ts": "2026-05-18T13:05:06.813722+00:00"}
{"action": "wayfinder_scheduled_ingest_source", "duration_ms": 3746.326, "inserted_opportunities": 29, "inserted_products": 29, "inserted_signals": 29, "llm_tokens": 0, "normalized": 87, "raw_records": 29, "source": "github", "token_free": true, "ts": "2026-05-18T13:05:10.562978+00:00"}
{"action": "wayfinder_scheduled_ingest_finished", "approved_sources": 2, "duration_ms": 3793.1, "enabled": true, "failed_sources": 0, "llm_tokens": 0, "schedule": "daily", "skipped_sources": 1, "token_free": true, "ts": "2026-05-18T13:05:10.566831+00:00"}
```

Exit code: 0

## `python3 -m wayfinder serve --port 8876` route proof

```text
/health
{
  "config": "loaded",
  "database": "ready",
  "ok": true,
  "service": "wayfinder",
  "storage_path": "/mnt/d/AI/codex-foundry/workspace/tasks/WRK-133/.ai-state/wayfinder/wayfinder.db"
}
```

Exit code: 0

```text
/search?q=saas summary
87:gracp/saas-generator
87:gracp/saas-generator
87:PhumudzoSly/ray
87:PhumudzoSly/ray
104:Search returned 11 rows
107:gracp/saas-generator
107:gracp/saas-generator
112:gracp/saas-generator
112:gracp/saas-generator
155:PhumudzoSly/ray
155:PhumudzoSly/ray
160:PhumudzoSly/ray

```

Exit code: 0

```text
/ dashboard summary
87:github
87:github
87:oss-ledger
87:oss-ledger
117:oss-ledger
117:oss-ledger
130:github
130:github
143:github
143:github
156:github
156:github
169:github
169:github
179:github
181:github
182:Signals 29
182:opportunities 29
189:oss-ledger
191:oss-ledger

```

Exit code: 0
