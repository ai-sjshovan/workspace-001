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

PRICING_DATA = {
    "app_name": "BriefLift",
    "plans": [
        {
            "name": "Starter",
            "price": "$29/mo",
            "features": [
                "Weekly brief generation for one brand workspace",
                "Campaign-ready outlines and angle suggestions",
                "Export summaries for client review",
            ],
        },
        {
            "name": "Pro",
            "price": "$99/mo",
            "features": [
                "Unlimited briefs across multiple campaigns",
                "Collaborative review notes and approval handoffs",
                "Priority refreshes for fast-moving launch calendars",
            ],
        },
        {
            "name": "Scale",
            "price": "Custom",
            "features": [
                "Multi-team workflow visibility with shared operating views",
                "Launch planning support for high-volume content programs",
                "Dedicated onboarding and rollout guidance",
            ],
        },
    ],
}
TRUST_DATA = {
    "app_name": "BriefLift",
    "sections": [
        {
            "title": "Security",
            "details": "BriefLift uses scoped access controls, encrypted transport, and routine operational review to keep campaign workflows protected.",
        },
        {
            "title": "Data Handling",
            "details": "Customer inputs stay limited to the workflow needed to generate and review briefs, with clear boundaries around storage and retention.",
        },
        {
            "title": "Reliability",
            "details": "The product is operated with health monitoring, build visibility, and resilient delivery practices to support dependable team access.",
        },
        {
            "title": "Support",
            "details": "Teams get a direct path for support and escalation when operational questions, incidents, or rollout needs require fast response.",
        },
    ],
}
CUSTOMERS_DATA = {
    "app_name": "BriefLift",
    "customers": [
        {
            "name": "Avery Cole, Content Director at Northstar Health",
            "company": "Northstar Health",
            "industry": "Healthcare",
            "use_case": "Launching patient education campaigns across regional clinics",
            "outcome": "Standardized campaign briefs and reduced bottlenecks between strategy and review teams.",
            "metric": "41% faster brief approvals",
        },
        {
            "name": "Mina Patel, Growth Lead at HarborStay",
            "company": "HarborStay",
            "industry": "Hospitality",
            "use_case": "Coordinating seasonal promotion briefs for local property teams",
            "outcome": "Gave every market a shared planning structure and clearer launch sequencing.",
            "metric": "22% lift in campaign conversion",
        },
        {
            "name": "Jordan Lee, VP Marketing at FieldSupply",
            "company": "FieldSupply",
            "industry": "B2B SaaS",
            "use_case": "Managing product launch narratives for multiple sales segments",
            "outcome": "Improved alignment between product marketing, content operations, and field enablement.",
            "metric": "9 fewer review cycles per launch",
        },
    ],
}
CUSTOMERS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift Customers</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f6f1e8;
            --ink: #182126;
            --muted: #5f676e;
            --panel: rgba(255, 255, 255, 0.9);
            --panel-strong: #ffffff;
            --line: #d8d0c3;
            --line-strong: #bcae98;
            --accent: #1f6b5f;
            --accent-deep: #123d37;
            --accent-soft: #d9ebe6;
            --sand: #f0e7d8;
            --shadow: 0 20px 55px rgba(24, 33, 38, 0.10);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(31, 107, 95, 0.18), transparent 28%),
                linear-gradient(180deg, #fbf8f1 0%, var(--bg) 100%);
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            z-index: -1;
            opacity: 0.35;
            background-image:
                linear-gradient(rgba(24, 33, 38, 0.04) 1px, transparent 1px),
                linear-gradient(90deg, rgba(24, 33, 38, 0.04) 1px, transparent 1px);
            background-size: 48px 48px;
            mask-image: linear-gradient(to bottom, black, transparent 72%);
        }
        h1, h2, h3, p, blockquote { margin: 0; }
        a { color: inherit; }
        .page {
            width: min(1120px, calc(100% - 40px));
            margin: 0 auto;
            padding: 28px 0 72px;
        }
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding-bottom: 24px;
        }
        .brand {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-weight: 800;
            text-decoration: none;
        }
        .brand-mark {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            display: grid;
            place-items: center;
            background: var(--accent-deep);
            color: #fff;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.16);
        }
        .top-link {
            color: var(--muted);
            text-decoration: none;
            font-size: 0.96rem;
        }
        .hero, .section-card, .story-card, .quote-card, .metric-card {
            border: 1px solid var(--line);
            background: var(--panel);
            box-shadow: var(--shadow);
            backdrop-filter: blur(10px);
        }
        .hero {
            display: grid;
            grid-template-columns: 1.35fr 0.95fr;
            gap: 18px;
            border-radius: 32px;
            padding: 18px;
        }
        .hero-copy,
        .hero-side {
            border-radius: 26px;
            padding: 28px;
        }
        .hero-copy {
            background: var(--panel-strong);
            border: 1px solid var(--line);
        }
        .hero-side {
            background: linear-gradient(145deg, var(--accent-deep) 0%, var(--accent) 100%);
            color: #fff;
        }
        .eyebrow {
            display: inline-block;
            margin-bottom: 14px;
            color: var(--accent-deep);
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .hero-side .eyebrow {
            color: rgba(255, 255, 255, 0.74);
        }
        .hero h1 {
            max-width: 11ch;
            font-size: clamp(2.7rem, 7vw, 5rem);
            line-height: 0.95;
        }
        .hero p {
            margin-top: 16px;
            color: var(--muted);
            line-height: 1.7;
            font-size: 1.04rem;
        }
        .hero-side p {
            color: rgba(255, 255, 255, 0.82);
        }
        .hero-stat {
            display: block;
            margin-top: 20px;
            font-size: 2.7rem;
            font-weight: 800;
        }
        .hero-notes {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 22px;
            padding: 0;
            list-style: none;
        }
        .hero-notes li {
            padding: 10px 14px;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: var(--sand);
            color: var(--muted);
            font-size: 0.92rem;
        }
        .section-card {
            margin-top: 24px;
            border-radius: 28px;
            padding: 28px;
        }
        .section-card > p {
            margin-top: 10px;
            color: var(--muted);
            line-height: 1.6;
        }
        .stories-grid,
        .results-grid,
        .use-case-grid {
            display: grid;
            gap: 18px;
            margin-top: 20px;
        }
        .stories-grid,
        .results-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .use-case-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .story-card,
        .quote-card,
        .metric-card {
            border-radius: 24px;
            padding: 22px;
        }
        .story-card h3,
        .metric-card h3 {
            font-size: 1.2rem;
        }
        .story-meta,
        .metric-label {
            color: var(--accent-deep);
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .story-card p,
        .metric-card p,
        .quote-card p,
        .quote-card footer {
            margin-top: 12px;
            color: var(--muted);
            line-height: 1.6;
        }
        .metric-value {
            display: block;
            margin-top: 14px;
            font-size: 2.3rem;
            font-weight: 800;
            color: var(--accent-deep);
        }
        .quote-card {
            margin-top: 20px;
            background: linear-gradient(180deg, rgba(217, 235, 230, 0.8) 0%, rgba(255, 255, 255, 0.96) 100%);
            border-color: rgba(31, 107, 95, 0.28);
        }
        blockquote {
            font-size: 1.3rem;
            line-height: 1.55;
            color: var(--ink);
        }
        footer {
            font-size: 0.96rem;
        }
        @media (max-width: 900px) {
            .hero,
            .stories-grid,
            .results-grid,
            .use-case-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="page">
        <header class="topbar">
            <a class="brand" href="/">
                <span class="brand-mark">B</span>
                <span>BriefLift</span>
            </a>
            <a class="top-link" href="/pricing">Explore plans</a>
        </header>

        <main>
            <section class="hero" aria-labelledby="customers-hero-title">
                <div class="hero-copy">
                    <div class="eyebrow">Customer Stories</div>
                    <h1 id="customers-hero-title">Customers use BriefLift to move from draft chaos to launch-ready momentum.</h1>
                    <p>BriefLift gives lean marketing teams a calmer operating rhythm for campaign planning, review, and execution. These customer outcomes show how teams use the platform to improve briefing quality, reduce review drag, and reach measurable results faster.</p>
                    <ul class="hero-notes" aria-label="Customer outcome highlights">
                        <li>Featured customer outcomes</li>
                        <li>Use cases across three industries</li>
                        <li>Measurable results teams can point to</li>
                    </ul>
                </div>
                <div class="hero-side">
                    <div class="eyebrow">Average Result</div>
                    <span class="hero-stat">24%</span>
                    <p>Average improvement across approval speed, conversion performance, and launch efficiency reported by featured BriefLift customers.</p>
                </div>
            </section>

            <section class="section-card" aria-labelledby="featured-outcomes-title">
                <div class="eyebrow">Featured Outcomes</div>
                <h2 id="featured-outcomes-title">Three customer stories grounded in real operating pain</h2>
                <p>Each customer adopted BriefLift to solve a different workflow problem, but all three needed clearer planning, faster alignment, and better campaign outcomes.</p>
                <div class="stories-grid">
                    <article class="story-card">
                        <div class="story-meta">Healthcare customer</div>
                        <h3>Avery Cole at Northstar Health</h3>
                        <p>Used BriefLift to standardize patient education campaigns across regional clinic teams and reduce friction between intake, drafting, and review.</p>
                    </article>
                    <article class="story-card">
                        <div class="story-meta">Hospitality customer</div>
                        <h3>Mina Patel at HarborStay</h3>
                        <p>Created a shared process for seasonal offers so local property teams could launch with consistent messaging and fewer last-minute brief revisions.</p>
                    </article>
                    <article class="story-card">
                        <div class="story-meta">B2B SaaS customer</div>
                        <h3>Jordan Lee at FieldSupply</h3>
                        <p>Connected product marketing and field teams with clearer launch narratives, reusable brief structures, and fewer review resets.</p>
                    </article>
                </div>
            </section>

            <section class="section-card" aria-labelledby="use-cases-title">
                <div class="eyebrow">Use Cases</div>
                <h2 id="use-cases-title">Where customer teams rely on BriefLift</h2>
                <div class="use-case-grid">
                    <article class="story-card">
                        <h3>Campaign operations</h3>
                        <p>Marketing leaders use BriefLift to centralize brief intake, give reviewers a single operating format, and keep launch schedules visible.</p>
                    </article>
                    <article class="story-card">
                        <h3>Product and lifecycle launches</h3>
                        <p>Cross-functional teams use BriefLift to align launch messaging, assign reviewers earlier, and cut wasted cycles before release.</p>
                    </article>
                </div>
            </section>

            <section class="section-card" aria-labelledby="results-title">
                <div class="eyebrow">Results</div>
                <h2 id="results-title">Measurable results customers can report back to leadership</h2>
                <div class="results-grid">
                    <article class="metric-card">
                        <div class="metric-label">Approval outcome</div>
                        <h3>Northstar Health</h3>
                        <span class="metric-value">41%</span>
                        <p>Faster brief approvals after standardizing planning inputs across clinic campaign teams.</p>
                    </article>
                    <article class="metric-card">
                        <div class="metric-label">Growth outcome</div>
                        <h3>HarborStay</h3>
                        <span class="metric-value">22%</span>
                        <p>Lift in campaign conversion after local teams launched seasonal offers from one shared brief workflow.</p>
                    </article>
                    <article class="metric-card">
                        <div class="metric-label">Efficiency outcome</div>
                        <h3>FieldSupply</h3>
                        <span class="metric-value">9</span>
                        <p>Fewer review cycles per launch once product marketing and sales enablement worked from the same source brief.</p>
                    </article>
                </div>
            </section>

            <section class="section-card" aria-labelledby="testimonial-title">
                <div class="eyebrow">Testimonial</div>
                <h2 id="testimonial-title">A short customer quote from the review process itself</h2>
                <article class="quote-card">
                    <blockquote>"BriefLift gave us a usable briefing system instead of another planning document. Our team saw the outcome in the first campaign cycle."</blockquote>
                    <footer>Jordan Lee, VP Marketing at FieldSupply</footer>
                </article>
            </section>
        </main>
    </div>
</body>
</html>
"""
PRICING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift Pricing</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f7f5ef;
            --surface: rgba(255, 255, 255, 0.88);
            --surface-strong: #ffffff;
            --surface-soft: #f0ece2;
            --ink: #171a1d;
            --muted: #5d646b;
            --line: #ded9cd;
            --line-strong: #c7c0b3;
            --accent: #285f57;
            --accent-dark: #153b36;
            --accent-soft: #dceae4;
            --shadow: 0 22px 60px rgba(30, 34, 38, 0.10);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Inter, "Segoe UI", Arial, sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top right, rgba(40, 95, 87, 0.16), transparent 28%),
                linear-gradient(180deg, #fbfaf7 0%, var(--bg) 100%);
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            z-index: -1;
            background-image:
                linear-gradient(rgba(23, 26, 29, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(23, 26, 29, 0.03) 1px, transparent 1px);
            background-size: 44px 44px;
            mask-image: linear-gradient(to bottom, black, transparent 74%);
        }
        a { color: inherit; }
        h1, h2, h3, p, ul { margin-top: 0; }
        .page {
            width: min(1120px, calc(100% - 40px));
            margin: 0 auto;
            padding: 28px 0 72px;
        }
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding-bottom: 28px;
        }
        .brand {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-weight: 750;
            text-decoration: none;
        }
        .brand-mark {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            color: var(--surface-strong);
            background: var(--accent-dark);
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.16);
        }
        .top-link {
            color: var(--muted);
            text-decoration: none;
            font-size: 0.96rem;
        }
        .hero, .faq, .card {
            border: 1px solid var(--line);
            background: var(--surface);
            backdrop-filter: blur(8px);
            box-shadow: var(--shadow);
        }
        .hero {
            border-radius: 28px;
            padding: 36px;
        }
        .eyebrow {
            display: inline-block;
            margin-bottom: 14px;
            color: var(--accent-dark);
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .hero h1 {
            max-width: 12ch;
            margin-bottom: 16px;
            font-size: clamp(2.8rem, 7vw, 4.9rem);
            line-height: 0.96;
        }
        .hero p {
            max-width: 42rem;
            color: var(--muted);
            font-size: 1.08rem;
            line-height: 1.7;
        }
        .hero-points {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 24px;
            padding: 0;
            list-style: none;
        }
        .hero-points li {
            padding: 10px 14px;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.75);
            color: var(--muted);
            font-size: 0.92rem;
        }
        .pricing-section {
            margin-top: 26px;
        }
        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
        }
        .card {
            border-radius: 24px;
            padding: 24px;
        }
        .card.featured {
            background: linear-gradient(180deg, rgba(220, 234, 228, 0.88) 0%, rgba(255, 255, 255, 0.96) 100%);
            border-color: rgba(40, 95, 87, 0.26);
        }
        .plan-name {
            font-size: 1.45rem;
        }
        .price {
            margin: 14px 0 16px;
            font-size: 2.4rem;
            font-weight: 780;
            line-height: 1;
        }
        .price span {
            color: var(--muted);
            font-size: 0.98rem;
            font-weight: 500;
        }
        .card p {
            color: var(--muted);
            line-height: 1.6;
        }
        .feature-list {
            margin: 18px 0 0;
            padding-left: 18px;
            color: var(--ink);
        }
        .feature-list li {
            margin-top: 10px;
            line-height: 1.5;
        }
        .faq {
            margin-top: 24px;
            border-radius: 28px;
            padding: 30px;
        }
        .faq-list {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px;
            margin-top: 18px;
        }
        .faq-item {
            padding: 18px;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: var(--surface-strong);
        }
        .faq-item p {
            margin-bottom: 0;
            color: var(--muted);
            line-height: 1.6;
        }
        @media (max-width: 920px) {
            .pricing-grid, .faq-list {
                grid-template-columns: 1fr;
            }
            .hero {
                padding: 28px;
            }
        }
        @media (max-width: 640px) {
            .page {
                width: min(100% - 24px, 1120px);
                padding-top: 18px;
            }
            .topbar {
                flex-direction: column;
                align-items: flex-start;
            }
            .hero h1 {
                max-width: none;
            }
        }
    </style>
</head>
<body>
    <main class="page">
        <header class="topbar">
            <a class="brand" href="/">
                <span class="brand-mark">B</span>
                <span>BriefLift</span>
            </a>
            <a class="top-link" href="/insights">See product insights</a>
        </header>
        <section class="hero" aria-labelledby="pricing-heading">
            <div class="eyebrow">Pricing</div>
            <h1 id="pricing-heading">Plans for teams shipping sharper briefs with less drag.</h1>
            <p>BriefLift gives strategy and content teams one place to move from intake to launch-ready messaging. Start lean, upgrade when review cycles and campaign volume increase.</p>
            <ul class="hero-points" aria-label="Pricing highlights">
                <li>No setup fee</li>
                <li>Built for campaign workflows</li>
                <li>Shared visibility across content teams</li>
            </ul>
        </section>
        <section class="pricing-section" aria-labelledby="plans-heading">
            <h2 id="plans-heading">Choose the right operating pace</h2>
            <div class="pricing-grid">
                <article class="card">
                    <h3 class="plan-name">Starter</h3>
                    <div class="price">$29<span>/month</span></div>
                    <p>For small teams replacing scattered brief docs with one focused workflow.</p>
                    <ul class="feature-list">
                        <li>Weekly brief generation for one brand workspace</li>
                        <li>Campaign-ready outlines and angle suggestions</li>
                        <li>Export summaries for client review</li>
                    </ul>
                </article>
                <article class="card featured">
                    <h3 class="plan-name">Pro</h3>
                    <div class="price">$99<span>/month</span></div>
                    <p>For marketing teams managing multiple launches and faster review handoffs.</p>
                    <ul class="feature-list">
                        <li>Unlimited briefs across multiple campaigns</li>
                        <li>Collaborative review notes and approval handoffs</li>
                        <li>Priority refreshes for fast-moving launch calendars</li>
                    </ul>
                </article>
                <article class="card">
                    <h3 class="plan-name">Scale</h3>
                    <div class="price">Custom<span> engagement</span></div>
                    <p>For organizations coordinating high-volume content programs across teams.</p>
                    <ul class="feature-list">
                        <li>Multi-team workflow visibility with shared operating views</li>
                        <li>Launch planning support for high-volume content programs</li>
                        <li>Dedicated onboarding and rollout guidance</li>
                    </ul>
                </article>
            </div>
        </section>
        <section class="faq" aria-labelledby="faq-heading">
            <div class="eyebrow">FAQ</div>
            <h2 id="faq-heading">Short answers before you commit</h2>
            <div class="faq-list">
                <article class="faq-item">
                    <h3>Does every plan include the full BriefLift interface?</h3>
                    <p>Yes. Each plan keeps the same core workspace experience, with plan limits based on usage and team complexity.</p>
                </article>
                <article class="faq-item">
                    <h3>Can we change plans as our workload grows?</h3>
                    <p>Yes. Teams can move from Starter to Pro or into Scale support when campaign velocity and review volume increase.</p>
                </article>
                <article class="faq-item">
                    <h3>Is onboarding included for larger teams?</h3>
                    <p>Yes. Scale includes rollout guidance so multi-team programs can adopt BriefLift without disrupting current launch operations.</p>
                </article>
            </div>
        </section>
    </main>
</body>
</html>
"""
TRUST_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift Trust Center</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f4f7f5;
            --surface: rgba(255, 255, 255, 0.9);
            --surface-strong: #ffffff;
            --surface-soft: #e6efe9;
            --ink: #162126;
            --muted: #5d6a71;
            --line: #d4ddd8;
            --line-strong: #bccbc3;
            --accent: #1f6b5c;
            --accent-deep: #0f3f38;
            --accent-soft: #d9ebe5;
            --shadow: 0 22px 60px rgba(22, 33, 38, 0.10);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Inter, "Segoe UI", Arial, sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(31, 107, 92, 0.16), transparent 30%),
                linear-gradient(180deg, #fafcfb 0%, var(--bg) 100%);
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            z-index: -1;
            background-image:
                linear-gradient(rgba(15, 63, 56, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(15, 63, 56, 0.03) 1px, transparent 1px);
            background-size: 42px 42px;
            mask-image: linear-gradient(to bottom, black, transparent 76%);
        }
        a { color: inherit; }
        h1, h2, h3, p, ul { margin-top: 0; }
        .page {
            width: min(1140px, calc(100% - 40px));
            margin: 0 auto;
            padding: 28px 0 72px;
        }
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding-bottom: 28px;
        }
        .brand {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-weight: 750;
            text-decoration: none;
        }
        .brand-mark {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            color: var(--surface-strong);
            background: var(--accent-deep);
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.16);
        }
        .top-link {
            color: var(--muted);
            text-decoration: none;
            font-size: 0.96rem;
        }
        .hero, .highlights, .section-card, .faq-card {
            border: 1px solid var(--line);
            background: var(--surface);
            backdrop-filter: blur(8px);
            box-shadow: var(--shadow);
        }
        .hero {
            display: grid;
            grid-template-columns: 1.4fr 0.9fr;
            gap: 20px;
            border-radius: 30px;
            padding: 36px;
        }
        .eyebrow {
            display: inline-block;
            margin-bottom: 14px;
            color: var(--accent-deep);
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .hero h1 {
            max-width: 13ch;
            margin-bottom: 16px;
            font-size: clamp(2.8rem, 7vw, 4.7rem);
            line-height: 0.98;
        }
        .hero p {
            max-width: 40rem;
            color: var(--muted);
            font-size: 1.06rem;
            line-height: 1.72;
        }
        .assurance-list {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin: 24px 0 0;
            padding: 0;
            list-style: none;
        }
        .assurance-list li {
            padding: 10px 14px;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.78);
            color: var(--muted);
            font-size: 0.92rem;
        }
        .highlights {
            border-radius: 24px;
            padding: 24px;
            background: linear-gradient(180deg, rgba(217, 235, 229, 0.92) 0%, rgba(255, 255, 255, 0.98) 100%);
        }
        .highlights strong {
            display: block;
            font-size: 2.2rem;
            line-height: 1;
            margin: 18px 0 12px;
        }
        .highlights p {
            color: var(--muted);
            line-height: 1.65;
        }
        .section-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
            margin-top: 24px;
        }
        .section-card {
            border-radius: 24px;
            padding: 24px;
        }
        .section-card p {
            color: var(--muted);
            line-height: 1.65;
            margin-bottom: 0;
        }
        .faq {
            margin-top: 24px;
        }
        .faq-shell {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px;
            margin-top: 18px;
        }
        .faq-card {
            border-radius: 20px;
            padding: 20px;
            background: var(--surface-strong);
        }
        .faq-card p {
            margin-bottom: 0;
            color: var(--muted);
            line-height: 1.6;
        }
        @media (max-width: 920px) {
            .hero, .section-grid, .faq-shell {
                grid-template-columns: 1fr;
            }
            .hero {
                padding: 28px;
            }
        }
        @media (max-width: 640px) {
            .page {
                width: min(100% - 24px, 1140px);
                padding-top: 18px;
            }
            .topbar {
                flex-direction: column;
                align-items: flex-start;
            }
            .hero h1 {
                max-width: none;
            }
        }
    </style>
</head>
<body>
    <main class="page">
        <header class="topbar">
            <a class="brand" href="/">
                <span class="brand-mark">B</span>
                <span>BriefLift</span>
            </a>
            <a class="top-link" href="/pricing">View plans</a>
        </header>
        <section class="hero" aria-labelledby="trust-heading">
            <div>
                <div class="eyebrow">Trust Center</div>
                <h1 id="trust-heading">Security and reliability practices for teams running BriefLift in production.</h1>
                <p>BriefLift is designed to give marketing and content teams a dependable workspace for campaign operations. This page outlines how we approach security posture, data handling, reliability, and support when teams rely on the platform day to day.</p>
                <ul class="assurance-list" aria-label="Trust highlights">
                    <li>Encrypted in transit</li>
                    <li>Role-aware operational access</li>
                    <li>Health visibility for core services</li>
                </ul>
            </div>
            <aside class="highlights" aria-label="Trust summary">
                <div class="eyebrow">Assurance</div>
                <strong>Operational clarity</strong>
                <p>We keep trust communication concise: protect customer data, keep the service stable, and provide direct support when incidents or urgent questions need escalation.</p>
            </aside>
        </section>
        <section class="section-grid" aria-label="Trust sections">
            <article class="section-card">
                <div class="eyebrow">Security Posture</div>
                <h2>Layered controls for everyday platform use</h2>
                <p>BriefLift uses encrypted transport, scoped access controls, and routine operational review to reduce risk around campaign workflows and internal tooling access.</p>
            </article>
            <article class="section-card">
                <div class="eyebrow">Data Handling</div>
                <h2>Focused collection with clear workflow boundaries</h2>
                <p>We handle customer data in support of brief generation and review flows, limit storage to what the product needs to operate, and keep data usage aligned with customer-facing workflow expectations.</p>
            </article>
            <article class="section-card">
                <div class="eyebrow">Uptime And Reliability</div>
                <h2>Monitored delivery for dependable team access</h2>
                <p>Health checks, build visibility, and resilient delivery practices support reliable access so teams can review, approve, and ship work without losing operational context.</p>
            </article>
            <article class="section-card">
                <div class="eyebrow">Support And Escalation</div>
                <h2>Clear paths for operational help</h2>
                <p>When teams need support, product questions, or incident escalation, BriefLift provides a direct response path so issues can be triaged quickly and communicated clearly.</p>
            </article>
        </section>
        <section class="faq" aria-labelledby="faq-heading">
            <div class="eyebrow">FAQ</div>
            <h2 id="faq-heading">Short assurances for procurement and team leads</h2>
            <div class="faq-shell">
                <article class="faq-card">
                    <h3>Is this page a high-level summary or a legal policy?</h3>
                    <p>This trust page is a concise operational summary. It is intended to explain how BriefLift approaches security, data, reliability, and support at a production SaaS level.</p>
                </article>
                <article class="faq-card">
                    <h3>How should teams handle urgent support needs?</h3>
                    <p>Escalation should go through the designated BriefLift support channel so incidents, reliability concerns, and rollout blockers can be triaged with the right urgency.</p>
                </article>
                <article class="faq-card">
                    <h3>What matters most in the current assurance model?</h3>
                    <p>Protecting customer data, maintaining reliability, and keeping support communication direct are the core commitments reflected in this page.</p>
                </article>
            </div>
        </section>
    </main>
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

        if parsed.path == "/pricing":
            self.write_html(HTTPStatus.OK, PRICING_HTML)
            return

        if parsed.path == "/customers":
            self.write_html(HTTPStatus.OK, CUSTOMERS_HTML)
            return

        if parsed.path == "/trust":
            self.write_html(HTTPStatus.OK, TRUST_HTML)
            return

        if parsed.path == "/api/pricing":
            self.write_json(HTTPStatus.OK, PRICING_DATA)
            return

        if parsed.path == "/api/customers":
            self.write_json(HTTPStatus.OK, CUSTOMERS_DATA)
            return

        if parsed.path == "/api/trust":
            self.write_json(HTTPStatus.OK, TRUST_DATA)
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
