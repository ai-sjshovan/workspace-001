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
FAQ_DATA = {
    "app_name": "BriefLift",
    "faqs": [
        {
            "question": "How do I set up BriefLift for a new team?",
            "answer": "Start with one workspace, define your brief template, and invite reviewers so new campaigns follow the same setup from day one.",
            "category": "setup",
        },
        {
            "question": "Which integrations does BriefLift support?",
            "answer": "BriefLift connects with tools like Slack, Asana, Google Drive, HubSpot, Zapier, and Figma for handoffs and context sharing.",
            "category": "integrations",
        },
        {
            "question": "How does billing work?",
            "answer": "Billing is subscription-based with plans for small teams, growing programs, and custom enterprise rollout needs.",
            "category": "billing",
        },
        {
            "question": "How does BriefLift approach security?",
            "answer": "BriefLift uses encrypted transport, scoped access, and operational review practices to protect workflow data.",
            "category": "security",
        },
        {
            "question": "Where can I get support?",
            "answer": "Customers can contact the BriefLift support team for onboarding help, rollout questions, and issue escalation.",
            "category": "support",
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
INTEGRATIONS_DATA = {
    "app_name": "BriefLift",
    "integrations": [
        {
            "name": "Slack",
            "category": "Team Communication",
            "status": "Available",
            "description": "Send brief approvals, launch reminders, and workflow handoff updates into campaign channels.",
        },
        {
            "name": "Asana",
            "category": "Project Management",
            "status": "Available",
            "description": "Turn approved briefs into tracked launch tasks with owners, due dates, and review checkpoints.",
        },
        {
            "name": "Google Drive",
            "category": "Document Collaboration",
            "status": "Available",
            "description": "Attach shared research docs, source notes, and exported brief summaries to active workflows.",
        },
        {
            "name": "HubSpot",
            "category": "CRM and Campaign Ops",
            "status": "Pilot",
            "description": "Sync campaign context and audience details so briefs reflect the latest lifecycle priorities.",
        },
        {
            "name": "Zapier",
            "category": "Automation",
            "status": "Available",
            "description": "Connect BriefLift to internal tools with trigger-based workflow automation and alert routing.",
        },
        {
            "name": "Figma",
            "category": "Creative Collaboration",
            "status": "Beta",
            "description": "Keep messaging briefs aligned with design exploration by linking creative review artifacts.",
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
RESOURCES_DATA = {
    "app_name": "BriefLift",
    "resources": [
        {
            "title": "Quarterly Campaign Planning Playbook",
            "type": "Playbook",
            "audience": "Marketing leadership",
            "summary": "A step-by-step planning structure for aligning campaign goals, owners, and review milestones before work enters production.",
            "status": "Available",
        },
        {
            "title": "Product Launch Brief Template",
            "type": "Template",
            "audience": "Product marketing teams",
            "summary": "A reusable launch brief format covering audience, positioning, channels, and handoff requirements for release-ready messaging.",
            "status": "Available",
        },
        {
            "title": "Editorial Workflow Operating Guide",
            "type": "Guide",
            "audience": "Content operations",
            "summary": "Operational guidance for intake, prioritization, approvals, and publishing across recurring editorial programs.",
            "status": "Available",
        },
        {
            "title": "Regional Campaign Localization Checklist",
            "type": "Template",
            "audience": "Field and regional marketers",
            "summary": "A checklist for adapting central campaign briefs to local audiences without losing message consistency or launch timing.",
            "status": "Pilot",
        },
        {
            "title": "Stakeholder Review Cadence Playbook",
            "type": "Playbook",
            "audience": "Cross-functional launch teams",
            "summary": "A practical review rhythm for reducing approval churn and keeping strategy, legal, and creative stakeholders aligned.",
            "status": "Available",
        },
        {
            "title": "Measurement Readiness Guide",
            "type": "Guide",
            "audience": "Growth and analytics teams",
            "summary": "A pre-launch guide for confirming KPIs, reporting views, and ownership before campaign briefs move into execution.",
            "status": "Beta",
        },
    ],
}
ROADMAP_DATA = {
    "app_name": "BriefLift",
    "items": [
        {
            "title": "Live performance scorecards",
            "timeframe": "Q3 2026",
            "status": "Planned",
            "summary": "Give teams a shared scorecard view for campaign throughput, approval speed, and publish readiness.",
        },
        {
            "title": "Approval SLA alerts",
            "timeframe": "Q3 2026",
            "status": "In Design",
            "summary": "Notify stakeholders when reviews stall so launch-critical briefs do not sit unnoticed in approval queues.",
        },
        {
            "title": "Reusable brief templates",
            "timeframe": "Q4 2026",
            "status": "Planned",
            "summary": "Let operators create repeatable campaign brief templates for launches, editorial work, and localization handoffs.",
        },
        {
            "title": "CRM context sync",
            "timeframe": "Q4 2026",
            "status": "Research",
            "summary": "Pull audience, segment, and campaign context into BriefLift so new briefs start from current customer data.",
        },
    ],
}
CHANGELOG_DATA = {
    "app_name": "BriefLift",
    "releases": [
        {
            "version": "1.4.0",
            "date": "2026-05-10",
            "title": "Workflow visibility refresh",
            "notes": "Added the insights dashboard with workflow health, recent activity, and throughput visibility for content teams.",
        },
        {
            "version": "1.3.0",
            "date": "2026-05-03",
            "title": "Resource center launch",
            "notes": "Published a dedicated resources experience and API endpoint for rollout guides, templates, and operating materials.",
        },
        {
            "version": "1.2.0",
            "date": "2026-04-25",
            "title": "Trust and customer proof pages",
            "notes": "Released trust and customer routes to centralize security posture, support expectations, and customer outcomes.",
        },
        {
            "version": "1.1.0",
            "date": "2026-04-18",
            "title": "Pricing and FAQ expansion",
            "notes": "Added public pricing and FAQ endpoints to help teams evaluate plans, billing, setup, and support.",
        },
    ],
}
AI_REVIEW_DATA = {
    "app_name": "BriefLift",
    "page": "ai-review",
    "metrics": [
        {
            "value": "68%",
            "label": "faster campaign intake",
            "detail": "Teams move from request to usable brief in hours instead of days.",
        },
        {
            "value": "34%",
            "label": "fewer review cycles",
            "detail": "Stakeholders get aligned briefs before content production begins.",
        },
        {
            "value": "4.6x",
            "label": "more reusable launch knowledge",
            "detail": "Past launches become searchable operating context for the next one.",
        },
        {
            "value": "92%",
            "label": "clearer handoffs",
            "detail": "Teams report stronger downstream clarity across creative, legal, and lifecycle.",
        },
    ],
    "features": [
        {
            "title": "Briefs that start with context",
            "summary": "Turn fragmented requests, research, and channel notes into structured launch briefs.",
        },
        {
            "title": "Fixes before review churn",
            "summary": "Surface missing inputs, conflicting goals, and approval gaps before a campaign stalls.",
        },
        {
            "title": "Executive-ready summaries",
            "summary": "Generate concise recaps for approvals, handoffs, and cross-functional visibility.",
        },
        {
            "title": "Agentic campaign assistance",
            "summary": "Draft follow-ups, next steps, and reusable launch recommendations from existing work.",
        },
        {
            "title": "Custom review playbooks",
            "summary": "Adapt workflows for product launches, editorial calendars, field marketing, and retention.",
        },
        {
            "title": "Operational reporting",
            "summary": "Track intake speed, review health, and launch readiness across active campaigns.",
        },
    ],
    "testimonials": [
        {
            "quote": "BriefLift gave our launch team one source of truth before the first draft ever hit review.",
            "name": "Naomi Park",
            "role": "Head of Campaign Operations",
            "company": "Lattice Harbor",
        },
        {
            "quote": "We cut stakeholder back-and-forth because every brief arrived with the context legal and creative needed.",
            "name": "Rafael Soto",
            "role": "Director of Brand Systems",
            "company": "Northline Studio",
        },
        {
            "quote": "The reporting layer helped us see which handoffs were slowing launches, not just which assets were late.",
            "name": "Imani Brooks",
            "role": "VP, Growth Programs",
            "company": "Signal Forge",
        },
    ],
}
AI_REVIEW_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift AI Review</title>
    <style>
        :root {
            color-scheme: dark;
            --bg: #08111f;
            --bg-soft: #0d1728;
            --panel: rgba(13, 23, 40, 0.86);
            --panel-strong: #0f1b2f;
            --panel-glow: rgba(70, 127, 255, 0.16);
            --line: rgba(165, 190, 255, 0.14);
            --line-strong: rgba(165, 190, 255, 0.24);
            --text: #f5f7fb;
            --muted: #9aa8c7;
            --muted-strong: #c5d0ea;
            --blue: #6b8cff;
            --cyan: #69e3ff;
            --mint: #67f5c0;
            --amber: #ffd166;
            --shadow: 0 26px 80px rgba(1, 7, 18, 0.48);
            --radius-xl: 32px;
            --radius-lg: 24px;
            --radius-md: 18px;
            --max: 1180px;
        }
        * { box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body {
            margin: 0;
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(107, 140, 255, 0.18), transparent 28%),
                radial-gradient(circle at top right, rgba(105, 227, 255, 0.12), transparent 26%),
                radial-gradient(circle at 50% 20%, rgba(103, 245, 192, 0.08), transparent 24%),
                linear-gradient(180deg, #060d18 0%, var(--bg) 42%, #091321 100%);
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            z-index: -2;
            background-image:
                linear-gradient(rgba(255, 255, 255, 0.028) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.028) 1px, transparent 1px);
            background-size: 72px 72px;
            mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.8), transparent 78%);
        }
        a { color: inherit; }
        h1, h2, h3, p { margin: 0; }
        .page { padding-bottom: 48px; }
        .shell, .band-inner {
            width: min(var(--max), calc(100% - 32px));
            margin: 0 auto;
        }
        .topbar {
            position: sticky;
            top: 0;
            z-index: 10;
            backdrop-filter: blur(18px);
            background: rgba(6, 13, 24, 0.72);
            border-bottom: 1px solid rgba(165, 190, 255, 0.08);
        }
        .nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 18px 0;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 800;
            letter-spacing: 0.02em;
        }
        .brand-mark {
            width: 36px;
            height: 36px;
            border-radius: 11px;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, var(--blue), var(--cyan));
            color: #08111f;
            font-size: 0.84rem;
        }
        .nav-links {
            display: flex;
            align-items: center;
            gap: 18px;
            color: var(--muted);
            font-size: 0.95rem;
        }
        .nav-links a {
            text-decoration: none;
        }
        .nav-cta, .hero-actions a, .final-cta a {
            border-radius: 999px;
            text-decoration: none;
            font-weight: 800;
        }
        .nav-cta {
            padding: 12px 18px;
            color: #06111f;
            background: linear-gradient(135deg, var(--mint), var(--cyan));
        }
        .hero {
            display: grid;
            grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.95fr);
            gap: 34px;
            padding: 72px 0 34px;
            align-items: center;
        }
        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 22px;
            color: var(--muted-strong);
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }
        .eyebrow::before {
            content: "";
            width: 9px;
            height: 9px;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--mint), var(--cyan));
            box-shadow: 0 0 16px rgba(103, 245, 192, 0.65);
        }
        h1 {
            max-width: 12ch;
            font-size: clamp(3rem, 7vw, 5.6rem);
            line-height: 0.94;
            letter-spacing: -0.04em;
        }
        .hero-copy p {
            max-width: 44rem;
            margin-top: 22px;
            color: var(--muted);
            font-size: 1.08rem;
            line-height: 1.72;
        }
        .hero-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            margin-top: 28px;
        }
        .hero-actions a {
            min-height: 50px;
            padding: 0 22px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .hero-actions .primary,
        .final-cta a {
            color: #06111f;
            background: linear-gradient(135deg, var(--mint), var(--cyan));
        }
        .hero-actions .secondary {
            border: 1px solid var(--line-strong);
            color: var(--text);
            background: rgba(255, 255, 255, 0.03);
        }
        .micro-proof {
            margin-top: 16px;
            color: var(--muted);
            font-size: 0.94rem;
        }
        .hero-visual,
        .card,
        .proof-band,
        .testimonial,
        .cta-panel,
        .footer {
            border: 1px solid var(--line);
            background: var(--panel);
            box-shadow: var(--shadow);
        }
        .hero-visual {
            position: relative;
            overflow: hidden;
            border-radius: var(--radius-xl);
            padding: 24px;
            background:
                radial-gradient(circle at top right, rgba(105, 227, 255, 0.24), transparent 28%),
                linear-gradient(160deg, rgba(12, 24, 43, 0.96), rgba(9, 18, 33, 0.9));
        }
        .hero-visual::after {
            content: "";
            position: absolute;
            inset: 20px;
            border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.04);
            pointer-events: none;
        }
        .visual-header,
        .workflow-row,
        .signal-row,
        .mini-card,
        .proof-items,
        .final-cta,
        .footer-grid {
            display: grid;
        }
        .visual-header {
            grid-template-columns: 1fr auto;
            gap: 16px;
            align-items: start;
        }
        .label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .visual-title {
            margin-top: 10px;
            font-size: 1.4rem;
            line-height: 1.2;
        }
        .pill {
            padding: 10px 14px;
            border-radius: 999px;
            color: #08111f;
            background: linear-gradient(135deg, var(--amber), #fff0b2);
            font-size: 0.85rem;
            font-weight: 800;
        }
        .workflow-board {
            display: grid;
            gap: 14px;
            margin-top: 24px;
        }
        .workflow-row {
            grid-template-columns: 1.2fr 0.8fr;
            gap: 14px;
        }
        .mini-card {
            gap: 10px;
            min-height: 138px;
            padding: 18px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(165, 190, 255, 0.12);
        }
        .mini-card strong {
            font-size: 2rem;
            line-height: 1;
        }
        .mini-card p,
        .capability p,
        .quote p,
        .footer p,
        .footer a,
        .signal-copy p,
        .trust-note,
        .proof-text,
        .section-head p {
            color: var(--muted);
            line-height: 1.65;
        }
        .signal-stack {
            display: grid;
            gap: 12px;
            margin-top: 14px;
        }
        .signal-row {
            grid-template-columns: 1fr auto;
            gap: 12px;
            padding: 14px 16px;
            border-radius: 16px;
            background: rgba(107, 140, 255, 0.08);
            border: 1px solid rgba(107, 140, 255, 0.14);
        }
        .signal-row span:last-child {
            color: var(--muted-strong);
            font-weight: 700;
        }
        .band {
            padding: 28px 0 0;
        }
        .proof-band {
            border-radius: var(--radius-lg);
            padding: 24px;
        }
        .proof-items {
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
        }
        .proof-item {
            padding: 8px 0;
        }
        .proof-item strong {
            display: block;
            margin-bottom: 8px;
            color: var(--text);
            font-size: 1.9rem;
        }
        .section {
            padding: 76px 0 0;
        }
        .section-head {
            max-width: 44rem;
            margin-bottom: 28px;
        }
        .section-head h2 {
            margin-bottom: 12px;
            font-size: clamp(2rem, 4vw, 3rem);
            line-height: 1.04;
            letter-spacing: -0.03em;
        }
        .customer-grid,
        .problem-grid,
        .feature-grid,
        .workflow-grid,
        .security-grid,
        .testimonial-grid,
        .footer-grid {
            display: grid;
            gap: 18px;
        }
        .customer-grid,
        .feature-grid,
        .security-grid,
        .testimonial-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .problem-grid,
        .workflow-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .card,
        .testimonial,
        .cta-panel,
        .footer {
            border-radius: var(--radius-lg);
        }
        .card {
            padding: 24px;
        }
        .quote {
            display: grid;
            gap: 16px;
        }
        .quote strong,
        .capability h3,
        .workflow-panel h3,
        .security-grid h3 {
            font-size: 1.15rem;
        }
        .proof-chip {
            display: inline-flex;
            align-items: center;
            width: fit-content;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(103, 245, 192, 0.1);
            color: var(--mint);
            font-size: 0.84rem;
            font-weight: 800;
        }
        .problem-card {
            min-height: 100%;
            padding: 30px;
            border-radius: var(--radius-xl);
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(14, 25, 43, 0.94), rgba(9, 18, 32, 0.9));
            box-shadow: var(--shadow);
        }
        .problem-card h3 {
            margin-bottom: 14px;
            font-size: 1.6rem;
        }
        .problem-list {
            display: grid;
            gap: 14px;
            margin-top: 22px;
        }
        .problem-list div {
            padding: 14px 16px;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.03);
            color: var(--muted-strong);
        }
        .feature-grid .card:nth-child(1),
        .feature-grid .card:nth-child(4) {
            background:
                linear-gradient(180deg, rgba(15, 27, 47, 0.96), rgba(11, 20, 36, 0.9)),
                var(--panel);
        }
        .capability span,
        .security-kicker {
            display: inline-block;
            margin-bottom: 12px;
            color: var(--cyan);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .workflow-panel {
            padding: 28px;
            border-radius: var(--radius-xl);
            border: 1px solid var(--line);
            background:
                radial-gradient(circle at top right, rgba(107, 140, 255, 0.18), transparent 24%),
                linear-gradient(180deg, rgba(13, 23, 40, 0.96), rgba(8, 17, 31, 0.92));
            box-shadow: var(--shadow);
        }
        .workflow-steps {
            display: grid;
            gap: 12px;
            margin-top: 22px;
        }
        .workflow-steps div {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            padding: 14px 16px;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.04);
        }
        .workflow-steps strong {
            color: var(--muted-strong);
            font-size: 0.95rem;
        }
        .trust-note {
            margin-top: 14px;
        }
        .testimonial {
            padding: 24px;
        }
        .testimonial p {
            font-size: 1rem;
        }
        .person {
            margin-top: 18px;
            color: var(--muted-strong);
            font-size: 0.94rem;
            font-weight: 700;
        }
        .cta-panel {
            margin-top: 76px;
            padding: 34px;
            background:
                radial-gradient(circle at top left, rgba(103, 245, 192, 0.14), transparent 22%),
                linear-gradient(135deg, rgba(13, 23, 40, 0.96), rgba(9, 18, 33, 0.96));
        }
        .final-cta {
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 18px;
            align-items: center;
        }
        .final-cta h2 {
            margin-bottom: 10px;
            font-size: clamp(2rem, 4vw, 3.2rem);
            line-height: 1.02;
        }
        .final-cta a {
            min-height: 54px;
            padding: 0 24px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .footer {
            margin-top: 18px;
            padding: 22px 24px;
        }
        .footer-grid {
            grid-template-columns: 1.2fr repeat(3, 1fr);
            align-items: start;
        }
        .footer-title {
            margin-bottom: 8px;
            color: var(--muted-strong);
            font-size: 0.9rem;
            font-weight: 800;
        }
        .footer-links {
            display: grid;
            gap: 8px;
        }
        .footer a {
            text-decoration: none;
        }
        @media (max-width: 1040px) {
            .hero,
            .problem-grid,
            .workflow-grid,
            .final-cta,
            .footer-grid {
                grid-template-columns: 1fr;
            }
            .customer-grid,
            .feature-grid,
            .security-grid,
            .testimonial-grid,
            .proof-items {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 720px) {
            .nav {
                flex-wrap: wrap;
            }
            .nav-links {
                width: 100%;
                justify-content: space-between;
                overflow-x: auto;
                padding-bottom: 4px;
            }
            .hero {
                padding-top: 48px;
            }
            .workflow-row,
            .customer-grid,
            .feature-grid,
            .security-grid,
            .testimonial-grid,
            .proof-items {
                grid-template-columns: 1fr;
            }
            .shell, .band-inner {
                width: min(100%, calc(100% - 24px));
            }
            .hero-visual,
            .problem-card,
            .workflow-panel,
            .cta-panel {
                border-radius: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="page">
        <div class="topbar">
            <nav class="nav shell" aria-label="BriefLift AI Review navigation">
                <div class="brand">
                    <div class="brand-mark">BL</div>
                    <span>BriefLift AI Review</span>
                </div>
                <div class="nav-links">
                    <a href="#metrics">Results</a>
                    <a href="#proof">Proof</a>
                    <a href="#features">Capabilities</a>
                    <a href="#security">Trust</a>
                    <a href="/#waitlist" class="nav-cta">Join the waitlist</a>
                </div>
            </nav>
        </div>
        <main class="shell">
            <section class="hero">
                <div class="hero-copy">
                    <div class="eyebrow">Campaign briefs with operational intelligence</div>
                    <h1>Launch work with fewer review loops and cleaner handoffs.</h1>
                    <p>BriefLift turns scattered intake requests, stakeholder feedback, and launch history into AI-assisted campaign briefs your team can actually ship from. Operators get structure, reviewers get clarity, and every launch leaves behind reusable knowledge for the next one.</p>
                    <div class="hero-actions">
                        <a href="/#waitlist" class="primary">Get early access</a>
                        <a href="/api/ai-review" class="secondary">View page data</a>
                    </div>
                    <div class="micro-proof">No new workflow to learn. Bring your intake, review rhythm, and launch context into one operating surface.</div>
                </div>
                <div class="hero-visual" aria-label="BriefLift workflow preview">
                    <div class="visual-header">
                        <div>
                            <div class="label">AI Review Workspace</div>
                            <div class="visual-title">Campaign launch board for message, review, and handoff readiness.</div>
                        </div>
                        <div class="pill">Ready for launch</div>
                    </div>
                    <div class="workflow-board">
                        <div class="workflow-row">
                            <div class="mini-card">
                                <div class="label">Review compression</div>
                                <strong>2.3 cycles</strong>
                                <p>Average approval path after aligning intake details, goals, and owner feedback up front.</p>
                            </div>
                            <div class="mini-card">
                                <div class="label">Handoff clarity</div>
                                <strong>92%</strong>
                                <p>Stakeholders report fewer clarification requests when briefs reach downstream teams.</p>
                            </div>
                        </div>
                        <div class="mini-card">
                            <div class="label">Live workflow signals</div>
                            <div class="signal-stack">
                                <div class="signal-row"><span>Audience context synced</span><span>Complete</span></div>
                                <div class="signal-row"><span>Channel assumptions verified</span><span>6 checks</span></div>
                                <div class="signal-row"><span>Creative handoff summary</span><span>Generated</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </main>
        <section class="band" id="metrics">
            <div class="band-inner">
                <div class="proof-band">
                    <div class="proof-items">
                        <div class="proof-item">
                            <strong>68%</strong>
                            <div class="proof-text">Faster campaign intake for teams replacing scattered briefs and email chains.</div>
                        </div>
                        <div class="proof-item">
                            <strong>34%</strong>
                            <div class="proof-text">Fewer review cycles before launch content reaches production.</div>
                        </div>
                        <div class="proof-item">
                            <strong>4.6x</strong>
                            <div class="proof-text">More reusable launch knowledge captured from each completed workflow.</div>
                        </div>
                        <div class="proof-item">
                            <strong>92%</strong>
                            <div class="proof-text">Clearer handoffs across strategy, creative, legal, and lifecycle teams.</div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        <main class="shell">
            <section class="section" id="proof">
                <div class="section-head">
                    <h2>Built for teams that ship through coordination, not guesswork.</h2>
                    <p>BriefLift is designed for dense marketing workflows where launch quality depends on clear context, predictable reviews, and shared operating memory across functions.</p>
                </div>
                <div class="customer-grid">
                    <article class="card quote">
                        <span class="proof-chip">Product marketing</span>
                        <strong>Standardize launch requests before they create downstream churn.</strong>
                        <p>Operators capture goals, channels, constraints, and stakeholder requirements in one repeatable intake structure.</p>
                    </article>
                    <article class="card quote">
                        <span class="proof-chip">Content operations</span>
                        <strong>Reduce avoidable review loops across campaign production.</strong>
                        <p>Teams move forward with summaries, decision trails, and AI-assisted fixes instead of fragmented follow-up threads.</p>
                    </article>
                    <article class="card quote">
                        <span class="proof-chip">Growth and lifecycle</span>
                        <strong>Make each launch reusable instead of starting from zero.</strong>
                        <p>Completed briefs become searchable knowledge for future campaigns, variants, and regional handoffs.</p>
                    </article>
                </div>
            </section>
            <section class="section">
                <div class="problem-grid">
                    <article class="problem-card">
                        <div class="eyebrow">The problem</div>
                        <h3>Campaign work slows down when the brief is the weakest link.</h3>
                        <p class="trust-note">Requests arrive incomplete, reviewers ask for different things, and launch knowledge stays trapped in chat, docs, and memory. Teams spend their time reconciling context instead of moving work forward.</p>
                        <div class="problem-list">
                            <div>Scattered intake from forms, docs, and direct messages</div>
                            <div>Repeated stakeholder clarifications before production starts</div>
                            <div>No durable trail of why a launch brief changed</div>
                        </div>
                    </article>
                    <article class="problem-card">
                        <div class="eyebrow">The BriefLift approach</div>
                        <h3>One AI-assisted operating layer for brief quality, review health, and launch memory.</h3>
                        <p class="trust-note">BriefLift turns every campaign into a structured workflow: intake, validation, summary, handoff, and reporting. Teams gain speed without losing the detail needed for high-stakes launches.</p>
                        <div class="problem-list">
                            <div>Intelligent intake that identifies missing context early</div>
                            <div>Summaries and recommendations tailored to each review stage</div>
                            <div>Reusable launch knowledge linked to future campaigns</div>
                        </div>
                    </article>
                </div>
            </section>
            <section class="section" id="features">
                <div class="section-head">
                    <h2>Dense capability coverage without adding operational drag.</h2>
                    <p>Every section of the workflow is designed to remove review friction, preserve context, and keep campaign owners aligned from request to release.</p>
                </div>
                <div class="feature-grid">
                    <article class="card capability">
                        <span>Structured intake</span>
                        <h3>Briefs that start with complete context</h3>
                        <p>Collect goals, audience, offer, channels, launch risks, and dependencies before work enters production.</p>
                    </article>
                    <article class="card capability">
                        <span>Fast fixes</span>
                        <h3>Catch missing inputs before stakeholders do</h3>
                        <p>Flag unresolved assumptions, missing approvals, and unclear handoffs while the brief is still easy to correct.</p>
                    </article>
                    <article class="card capability">
                        <span>Summaries</span>
                        <h3>Generate executive-ready recaps instantly</h3>
                        <p>Share campaign intent, critical decisions, and launch status in a concise format for approvals and updates.</p>
                    </article>
                    <article class="card capability">
                        <span>Agentic assistance</span>
                        <h3>Ask for next steps, rewrites, and follow-up actions</h3>
                        <p>Use AI to draft clarifications, synthesize past launches, and recommend workflow moves that unblock teams.</p>
                    </article>
                    <article class="card capability">
                        <span>Customization</span>
                        <h3>Adapt review logic to your operating model</h3>
                        <p>Support different launch templates for editorial, product marketing, field campaigns, and lifecycle programs.</p>
                    </article>
                    <article class="card capability">
                        <span>Reporting</span>
                        <h3>See intake speed, review health, and launch readiness</h3>
                        <p>Measure where campaigns stall and where process improvements actually shorten time to market.</p>
                    </article>
                </div>
            </section>
            <section class="section">
                <div class="section-head">
                    <h2>Operate across planning, review, and execution environments.</h2>
                    <p>BriefLift helps teams work across their real campaign rhythm: not just content generation, but intake quality, stakeholder alignment, and production readiness.</p>
                </div>
                <div class="workflow-grid">
                    <article class="workflow-panel">
                        <div class="eyebrow">Workflow coverage</div>
                        <h3>Move from request intake to launch handoff without losing the thread.</h3>
                        <div class="workflow-steps">
                            <div><span>Campaign request arrives</span><strong>Normalize inputs</strong></div>
                            <div><span>Stakeholders review intent</span><strong>Summarize decisions</strong></div>
                            <div><span>Creative and channel owners align</span><strong>Generate handoff notes</strong></div>
                            <div><span>Launch closes out</span><strong>Store reusable knowledge</strong></div>
                        </div>
                    </article>
                    <article class="workflow-panel">
                        <div class="eyebrow">Context intelligence</div>
                        <h3>Bring prior launches, review history, and reusable patterns into every new brief.</h3>
                        <div class="signal-copy">
                            <p>BriefLift doesn’t treat each campaign as an isolated prompt. It connects the why behind past decisions, the language that performed, and the review patterns that slowed teams down, then applies that context to the next launch.</p>
                            <p class="trust-note">That means fewer repeated mistakes, better campaign consistency, and stronger adaptation for channels, segments, and stakeholders.</p>
                        </div>
                    </article>
                </div>
            </section>
            <section class="section" id="security">
                <div class="section-head">
                    <h2>Trust, security, and operational discipline built into the workflow.</h2>
                    <p>BriefLift is positioned for teams that need visibility and control when campaign planning touches sensitive launches, legal review, or cross-functional approvals.</p>
                </div>
                <div class="security-grid">
                    <article class="card">
                        <div class="security-kicker">Scoped access</div>
                        <h3>Keep campaign context limited to the right operators and reviewers.</h3>
                        <p>Access controls are designed around workspaces, responsibilities, and clear review boundaries.</p>
                    </article>
                    <article class="card">
                        <div class="security-kicker">Auditability</div>
                        <h3>Preserve decision trails across changing drafts and approvals.</h3>
                        <p>Teams can understand what changed, why it changed, and who needed to weigh in before launch.</p>
                    </article>
                    <article class="card">
                        <div class="security-kicker">Operational resilience</div>
                        <h3>Support repeatable launches with health visibility and dependable delivery patterns.</h3>
                        <p>Marketing operations get a clearer view of workflow state, response expectations, and process reliability.</p>
                    </article>
                </div>
            </section>
            <section class="section">
                <div class="section-head">
                    <h2>Proof from teams running high-context campaign work.</h2>
                    <p>These are fictional examples created for this page, designed to show the kinds of outcomes BriefLift targets without using external customer assets or claims.</p>
                </div>
                <div class="testimonial-grid">
                    <article class="testimonial">
                        <p>"BriefLift gave our launch team one source of truth before the first draft ever hit review."</p>
                        <div class="person">Naomi Park · Head of Campaign Operations, Lattice Harbor</div>
                    </article>
                    <article class="testimonial">
                        <p>"We cut stakeholder back-and-forth because every brief arrived with the context legal and creative needed."</p>
                        <div class="person">Rafael Soto · Director of Brand Systems, Northline Studio</div>
                    </article>
                    <article class="testimonial">
                        <p>"The reporting layer helped us see which handoffs were slowing launches, not just which assets were late."</p>
                        <div class="person">Imani Brooks · VP, Growth Programs, Signal Forge</div>
                    </article>
                </div>
            </section>
            <section class="cta-panel">
                <div class="final-cta">
                    <div>
                        <div class="eyebrow">Final call</div>
                        <h2>Bring order to campaign briefs before launch complexity compounds.</h2>
                        <p>BriefLift helps teams move faster by making intake cleaner, reviews shorter, and launch knowledge reusable across every campaign that follows.</p>
                    </div>
                    <a href="/#waitlist">Request access</a>
                </div>
            </section>
            <footer class="footer">
                <div class="footer-grid">
                    <div>
                        <div class="brand">
                            <div class="brand-mark">BL</div>
                            <span>BriefLift</span>
                        </div>
                        <p style="margin-top: 12px;">AI campaign brief and content operations software for teams that need better launch coordination.</p>
                    </div>
                    <div>
                        <div class="footer-title">Product</div>
                        <div class="footer-links">
                            <a href="#features">Capabilities</a>
                            <a href="#metrics">Results</a>
                            <a href="#security">Trust</a>
                        </div>
                    </div>
                    <div>
                        <div class="footer-title">Explore</div>
                        <div class="footer-links">
                            <a href="/roadmap">Roadmap</a>
                            <a href="/changelog">Changelog</a>
                            <a href="/faq">FAQ</a>
                        </div>
                    </div>
                    <div>
                        <div class="footer-title">Start</div>
                        <div class="footer-links">
                            <a href="/">Homepage</a>
                            <a href="/#waitlist">Waitlist</a>
                            <a href="/api/ai-review">API</a>
                        </div>
                    </div>
                </div>
            </footer>
        </main>
    </div>
</body>
</html>
"""
ROADMAP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift Roadmap</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f7f5ef;
            --surface: #ffffff;
            --surface-soft: #f0ece2;
            --ink: #171a1d;
            --muted: #5d646b;
            --line: #ded9cd;
            --accent: #285f57;
            --accent-dark: #153b36;
            --accent-soft: #dceae4;
            --shadow: 0 18px 55px rgba(30, 34, 38, 0.1);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top right, rgba(40, 95, 87, 0.14), transparent 28%),
                linear-gradient(180deg, #fbfaf7 0%, var(--bg) 100%);
        }
        .page {
            width: min(1040px, calc(100% - 40px));
            margin: 0 auto;
            padding: 36px 0 72px;
        }
        .hero, .item {
            border: 1px solid var(--line);
            border-radius: 24px;
            background: var(--surface);
            box-shadow: var(--shadow);
        }
        .hero {
            padding: 32px;
        }
        .eyebrow {
            color: var(--accent-dark);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        h1, h2, h3, p {
            margin: 0;
        }
        h1 {
            margin-top: 14px;
            font-size: clamp(2.3rem, 5vw, 4rem);
            line-height: 1.02;
        }
        .hero p {
            margin-top: 16px;
            max-width: 46rem;
            color: var(--muted);
            line-height: 1.7;
        }
        .list {
            display: grid;
            gap: 18px;
            margin-top: 24px;
        }
        .item {
            padding: 24px;
        }
        .meta {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 14px;
        }
        .pill {
            padding: 7px 12px;
            border-radius: 999px;
            background: var(--surface-soft);
            color: var(--accent-dark);
            font-size: 0.84rem;
            font-weight: 700;
        }
        .item p {
            margin-top: 10px;
            color: var(--muted);
            line-height: 1.65;
        }
        @media (max-width: 720px) {
            .page {
                width: min(100%, calc(100% - 24px));
                padding-top: 24px;
            }
            .hero, .item {
                border-radius: 20px;
            }
        }
    </style>
</head>
<body>
    <main class="page">
        <section class="hero">
            <div class="eyebrow">BriefLift Roadmap</div>
            <h1>What the team is building next.</h1>
            <p>Upcoming roadmap work focuses on clearer campaign visibility, faster approvals, and stronger reuse for recurring launch workflows.</p>
        </section>
        <section class="list" aria-label="Upcoming roadmap items">
            <article class="item">
                <div class="meta">
                    <span class="pill">Q3 2026</span>
                    <span class="pill">Planned</span>
                </div>
                <h2>Live performance scorecards</h2>
                <p>Give teams a shared scorecard view for campaign throughput, approval speed, and publish readiness.</p>
            </article>
            <article class="item">
                <div class="meta">
                    <span class="pill">Q3 2026</span>
                    <span class="pill">In Design</span>
                </div>
                <h2>Approval SLA alerts</h2>
                <p>Notify stakeholders when reviews stall so launch-critical briefs do not sit unnoticed in approval queues.</p>
            </article>
            <article class="item">
                <div class="meta">
                    <span class="pill">Q4 2026</span>
                    <span class="pill">Planned</span>
                </div>
                <h2>Reusable brief templates</h2>
                <p>Let operators create repeatable campaign brief templates for launches, editorial work, and localization handoffs.</p>
            </article>
            <article class="item">
                <div class="meta">
                    <span class="pill">Q4 2026</span>
                    <span class="pill">Research</span>
                </div>
                <h2>CRM context sync</h2>
                <p>Pull audience, segment, and campaign context into BriefLift so new briefs start from current customer data.</p>
            </article>
        </section>
    </main>
</body>
</html>
"""
CHANGELOG_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift Changelog</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f7f5ef;
            --surface: #ffffff;
            --surface-soft: #f0ece2;
            --ink: #171a1d;
            --muted: #5d646b;
            --line: #ded9cd;
            --accent: #285f57;
            --accent-dark: #153b36;
            --shadow: 0 18px 55px rgba(30, 34, 38, 0.1);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--ink);
            background: linear-gradient(180deg, #fbfaf7 0%, var(--bg) 100%);
        }
        .page {
            width: min(860px, calc(100% - 32px));
            margin: 0 auto;
            padding: 48px 0 72px;
        }
        h1, h2, p { margin-top: 0; }
        .eyebrow {
            margin-bottom: 14px;
            color: var(--accent-dark);
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .intro {
            max-width: 42rem;
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.65;
        }
        .timeline {
            display: grid;
            gap: 18px;
            margin-top: 32px;
        }
        .entry {
            padding: 22px;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: var(--surface);
            box-shadow: var(--shadow);
        }
        .meta {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 10px;
            color: var(--muted);
            font-size: 0.92rem;
        }
        .version {
            padding: 4px 10px;
            border-radius: 999px;
            background: var(--surface-soft);
            color: var(--accent-dark);
            font-weight: 700;
        }
        h2 {
            margin-bottom: 10px;
            font-size: 1.4rem;
        }
        .notes {
            color: var(--muted);
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <main class="page">
        <div class="eyebrow">BriefLift Release Notes</div>
        <h1>Changelog</h1>
        <p class="intro">Recent BriefLift product changes, organized as release notes for workflow, visibility, and public product surface updates.</p>
        <section class="timeline" aria-label="BriefLift changelog entries">
            <article class="entry">
                <div class="meta"><span class="version">v1.4.0</span><span>2026-05-10</span></div>
                <h2>Workflow visibility refresh</h2>
                <p class="notes">Added the insights dashboard with workflow health, recent activity, and throughput visibility for content teams.</p>
            </article>
            <article class="entry">
                <div class="meta"><span class="version">v1.3.0</span><span>2026-05-03</span></div>
                <h2>Resource center launch</h2>
                <p class="notes">Published a dedicated resources experience and API endpoint for rollout guides, templates, and operating materials.</p>
            </article>
            <article class="entry">
                <div class="meta"><span class="version">v1.2.0</span><span>2026-04-25</span></div>
                <h2>Trust and customer proof pages</h2>
                <p class="notes">Released trust and customer routes to centralize security posture, support expectations, and customer outcomes.</p>
            </article>
            <article class="entry">
                <div class="meta"><span class="version">v1.1.0</span><span>2026-04-18</span></div>
                <h2>Pricing and FAQ expansion</h2>
                <p class="notes">Added public pricing and FAQ endpoints to help teams evaluate plans, billing, setup, and support.</p>
            </article>
        </section>
    </main>
</body>
</html>
"""
FAQ_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift FAQ</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f5f7fb;
            --panel: rgba(255, 255, 255, 0.94);
            --panel-strong: #ffffff;
            --text: #132238;
            --muted: #5b6c84;
            --line: #d7e1ef;
            --accent: #0f766e;
            --accent-deep: #134e4a;
            --accent-soft: #d9f3ef;
            --shadow: 0 22px 50px rgba(19, 34, 56, 0.10);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top right, rgba(15, 118, 110, 0.10), transparent 32%),
                linear-gradient(180deg, #fcfdff 0%, var(--bg) 100%);
        }
        h1, h2, h3, p { margin: 0; }
        .page {
            width: min(980px, calc(100% - 36px));
            margin: 0 auto;
            padding: 28px 0 56px;
        }
        .topbar, .hero, .faq-item {
            border: 1px solid var(--line);
            background: var(--panel);
            box-shadow: var(--shadow);
        }
        .topbar {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: center;
            padding: 18px 22px;
            border-radius: 24px;
        }
        .brand {
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: 0.02em;
        }
        .topbar span, .eyebrow, .category {
            color: var(--muted);
        }
        .hero {
            margin-top: 22px;
            border-radius: 30px;
            padding: 32px;
            background: linear-gradient(135deg, #eff6ff 0%, #ecfeff 54%, #f8fafc 100%);
        }
        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.09em;
            font-size: 0.78rem;
            font-weight: 700;
        }
        .hero h1 {
            margin-top: 14px;
            font-size: clamp(2.2rem, 5vw, 3.7rem);
            line-height: 0.98;
        }
        .hero p {
            margin-top: 14px;
            max-width: 42rem;
            line-height: 1.65;
        }
        .faq-list {
            display: grid;
            gap: 16px;
            margin-top: 22px;
        }
        .faq-item {
            border-radius: 24px;
            padding: 22px;
            background: var(--panel-strong);
        }
        .faq-item h2 {
            font-size: 1.2rem;
            line-height: 1.35;
        }
        .faq-item p {
            margin-top: 10px;
            line-height: 1.65;
            color: var(--muted);
        }
        .category {
            display: inline-block;
            margin-top: 12px;
            padding: 7px 10px;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent-deep);
            font-size: 0.84rem;
            font-weight: 700;
            text-transform: capitalize;
        }
        .support-note {
            margin-top: 20px;
            padding: 18px 20px;
            border-radius: 20px;
            background: #10263f;
            color: #f8fbff;
        }
        .support-note p {
            margin-top: 8px;
            color: rgba(248, 251, 255, 0.84);
        }
        @media (max-width: 720px) {
            .topbar {
                flex-direction: column;
                align-items: flex-start;
            }
            .hero {
                padding: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="page">
        <header class="topbar">
            <div class="brand">BriefLift</div>
            <span>FAQ · Setup · Integrations · Billing · Security · Support</span>
        </header>
        <section class="hero">
            <div class="eyebrow">FAQ</div>
            <h1>Answers for teams launching BriefLift with confidence.</h1>
            <p>Review the essentials for setup, integrations, billing, security, and support before your team scales campaign planning in BriefLift.</p>
        </section>
        <section class="faq-list" aria-label="Frequently asked questions">
            <article class="faq-item">
                <h2>How do I set up BriefLift for a new team?</h2>
                <p>Start with one workspace, define your brief template, and invite reviewers so every new campaign follows the same setup and approval flow.</p>
                <div class="category">setup</div>
            </article>
            <article class="faq-item">
                <h2>Which integrations does BriefLift support?</h2>
                <p>BriefLift supports integrations with Slack, Asana, Google Drive, HubSpot, Zapier, and Figma to keep briefs connected to the tools your team already uses.</p>
                <div class="category">integrations</div>
            </article>
            <article class="faq-item">
                <h2>How does billing work?</h2>
                <p>Billing is subscription-based, with options for smaller teams, growing campaign programs, and larger organizations that need custom rollout support.</p>
                <div class="category">billing</div>
            </article>
            <article class="faq-item">
                <h2>What security practices does BriefLift follow?</h2>
                <p>BriefLift uses encrypted transport, scoped access, and routine operational review to keep workflow data protected as teams collaborate.</p>
                <div class="category">security</div>
            </article>
            <article class="faq-item">
                <h2>How do I contact support?</h2>
                <p>The support team helps with onboarding, rollout planning, and issue escalation so customers can keep launch work moving without delay.</p>
                <div class="category">support</div>
            </article>
        </section>
        <section class="support-note">
            <strong>Need more help?</strong>
            <p>BriefLift support can guide implementation details, integration planning, and operational questions for active customers.</p>
        </section>
    </div>
</body>
</html>
"""
INTEGRATIONS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift Integrations</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f4f7fb;
            --ink: #132238;
            --muted: #5b6c84;
            --panel: rgba(255, 255, 255, 0.94);
            --panel-strong: #ffffff;
            --line: #d7e1ef;
            --line-strong: #b9c9df;
            --accent: #0f766e;
            --accent-deep: #134e4a;
            --accent-soft: #d9f3ef;
            --accent-warm: #f59e0b;
            --hero: linear-gradient(135deg, #eff6ff 0%, #ecfeff 52%, #f8fafc 100%);
            --shadow: 0 22px 50px rgba(19, 34, 56, 0.10);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 28%),
                linear-gradient(180deg, #fcfdff 0%, var(--bg) 100%);
        }
        h1, h2, h3, p, ul { margin: 0; }
        .page {
            width: min(1120px, calc(100% - 36px));
            margin: 0 auto;
            padding: 28px 0 64px;
        }
        .topbar, .hero, .section-card, .tile, .step, .safeguard {
            border: 1px solid var(--line);
            background: var(--panel);
            box-shadow: var(--shadow);
        }
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding: 18px 22px;
            border-radius: 24px;
        }
        .brand {
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: 0.02em;
        }
        .topbar span {
            color: var(--muted);
            font-size: 0.95rem;
        }
        .hero {
            margin-top: 22px;
            border-radius: 30px;
            padding: 18px;
            background: var(--hero);
        }
        .hero-grid {
            display: grid;
            grid-template-columns: 1.25fr 0.95fr;
            gap: 18px;
        }
        .hero-copy, .hero-panel {
            border-radius: 24px;
            padding: 26px;
            background: var(--panel-strong);
            border: 1px solid var(--line);
        }
        .eyebrow {
            display: inline-block;
            color: var(--accent-deep);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
            font-weight: 800;
        }
        h1 {
            margin-top: 12px;
            font-size: clamp(2.4rem, 5vw, 4.2rem);
            line-height: 0.98;
            max-width: 10ch;
        }
        .hero-copy p, .section-card > p, .tile p, .step p, .safeguard p {
            color: var(--muted);
            line-height: 1.65;
        }
        .hero-copy p {
            margin-top: 16px;
            max-width: 48rem;
        }
        .hero-notes {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
            padding: 0;
            list-style: none;
        }
        .hero-notes li {
            padding: 10px 14px;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent-deep);
            font-size: 0.92rem;
            font-weight: 700;
        }
        .hero-panel {
            background: linear-gradient(160deg, var(--accent-deep) 0%, var(--accent) 100%);
            color: #fff;
        }
        .hero-panel .eyebrow,
        .hero-panel p {
            color: rgba(255, 255, 255, 0.82);
        }
        .hero-panel strong {
            display: block;
            margin-top: 18px;
            font-size: 2.6rem;
        }
        .section-card {
            margin-top: 20px;
            border-radius: 28px;
            padding: 26px;
        }
        .section-card h2 {
            margin-top: 10px;
            font-size: 1.8rem;
        }
        .grid {
            display: grid;
            gap: 16px;
            margin-top: 18px;
        }
        .tools-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .category-grid,
        .safeguard-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .setup-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .tile, .step, .safeguard {
            border-radius: 22px;
            padding: 20px;
        }
        .label-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }
        .status {
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 0.8rem;
            font-weight: 800;
        }
        .status-available {
            background: #dcfce7;
            color: #166534;
        }
        .status-pilot,
        .status-beta {
            background: #fef3c7;
            color: #92400e;
        }
        .step-number {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            display: grid;
            place-items: center;
            margin-bottom: 14px;
            background: var(--accent-soft);
            color: var(--accent-deep);
            font-weight: 800;
        }
        .safeguard {
            border-top: 4px solid var(--accent-warm);
        }
        @media (max-width: 900px) {
            .hero-grid,
            .tools-grid,
            .category-grid,
            .setup-grid,
            .safeguard-grid {
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
                <span>Integrations for workflow teams, publishing tools, and operating visibility</span>
            </div>
            <span>Connected systems overview</span>
        </header>
        <main>
            <section class="hero" aria-labelledby="integrations-hero-title">
                <div class="hero-grid">
                    <div class="hero-copy">
                        <div class="eyebrow">Integrations</div>
                        <h1 id="integrations-hero-title">Connect BriefLift to the tools already running your workflow.</h1>
                        <p>BriefLift integrations help marketing, content, and operations teams move campaign context, review signals, and launch decisions between the systems they use every day without rebuilding their process from scratch.</p>
                        <ul class="hero-notes" aria-label="Integration highlights">
                            <li>Workflow-aware setup</li>
                            <li>Tool-ready handoffs</li>
                            <li>Operational safeguards</li>
                        </ul>
                    </div>
                    <aside class="hero-panel" aria-label="Integration summary">
                        <div class="eyebrow">Active Coverage</div>
                        <strong>6 integrations</strong>
                        <p>Covering communication, project management, creative collaboration, automation, and campaign operations for cross-functional teams.</p>
                    </aside>
                </div>
            </section>
            <section class="section-card" aria-labelledby="workflow-tools-title">
                <div class="eyebrow">Connected Workflow Tools</div>
                <h2 id="workflow-tools-title">Systems that support intake, review, and launch coordination</h2>
                <p>Each integration is designed to keep brief details usable in the downstream tool while preserving the review rhythm teams expect.</p>
                <div class="grid tools-grid">
                    <article class="tile">
                        <div class="label-row">
                            <h3>Slack</h3>
                            <span class="status status-available">Available</span>
                        </div>
                        <p>Post brief approvals, workflow status changes, and launch reminders directly into team channels.</p>
                    </article>
                    <article class="tile">
                        <div class="label-row">
                            <h3>Asana</h3>
                            <span class="status status-available">Available</span>
                        </div>
                        <p>Create actionable delivery tasks from approved briefs so campaign work keeps moving without manual re-entry.</p>
                    </article>
                    <article class="tile">
                        <div class="label-row">
                            <h3>Google Drive</h3>
                            <span class="status status-available">Available</span>
                        </div>
                        <p>Keep shared source material, exported summaries, and review references attached to the active setup.</p>
                    </article>
                    <article class="tile">
                        <div class="label-row">
                            <h3>Zapier</h3>
                            <span class="status status-available">Available</span>
                        </div>
                        <p>Route brief events into internal workflow tools when teams need broader automation coverage.</p>
                    </article>
                </div>
            </section>
            <section class="section-card" aria-labelledby="categories-title">
                <div class="eyebrow">Integration Categories</div>
                <h2 id="categories-title">Support across the key systems behind campaign execution</h2>
                <p>BriefLift focuses on realistic integration categories that matter for operating cadence, team visibility, and tool handoffs.</p>
                <div class="grid category-grid">
                    <article class="tile">
                        <h3>Communication</h3>
                        <p>Share review decisions and workflow updates where stakeholders already coordinate daily work.</p>
                    </article>
                    <article class="tile">
                        <h3>Project Management</h3>
                        <p>Carry approved briefs into planning tools with owners, due dates, and operational context intact.</p>
                    </article>
                    <article class="tile">
                        <h3>Automation and Creative Ops</h3>
                        <p>Bridge setup tasks, creative references, and downstream delivery steps without expanding manual work.</p>
                    </article>
                </div>
            </section>
            <section class="section-card" aria-labelledby="setup-title">
                <div class="eyebrow">Setup Expectations</div>
                <h2 id="setup-title">A straightforward setup path for customer teams</h2>
                <p>Integration setup is intentionally narrow: connect the right workspace, confirm the workflow destination, and validate the operating rules before launch.</p>
                <div class="grid setup-grid">
                    <article class="step">
                        <div class="step-number">1</div>
                        <h3>Authorize access</h3>
                        <p>Admins connect the target tool with the minimum workspace scope needed for routing brief events.</p>
                    </article>
                    <article class="step">
                        <div class="step-number">2</div>
                        <h3>Map workflow destinations</h3>
                        <p>Teams choose the channels, projects, or folders that should receive brief updates and tool outputs.</p>
                    </article>
                    <article class="step">
                        <div class="step-number">3</div>
                        <h3>Validate launch behavior</h3>
                        <p>BriefLift confirms the setup sends the right signals before the integration becomes part of live operations.</p>
                    </article>
                </div>
            </section>
            <section class="section-card" aria-labelledby="safeguards-title">
                <div class="eyebrow">Operational Safeguards</div>
                <h2 id="safeguards-title">Controls that keep integrations predictable and supportable</h2>
                <p>Operational safeguards are built into the integration model so teams can trust the workflow and troubleshoot issues quickly.</p>
                <div class="grid safeguard-grid">
                    <article class="safeguard">
                        <h3>Scoped access</h3>
                        <p>Connections are limited to the setup required for workflow delivery instead of broad unrestricted access.</p>
                    </article>
                    <article class="safeguard">
                        <h3>Status visibility</h3>
                        <p>Teams can see which integration is available, in pilot, or in beta before relying on it in production workflow.</p>
                    </article>
                    <article class="safeguard">
                        <h3>Reviewable setup</h3>
                        <p>BriefLift expects a clear setup review so operational changes do not silently alter customer-facing launch behavior.</p>
                    </article>
                </div>
            </section>
        </main>
    </div>
</body>
</html>
"""
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
RESOURCES_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BriefLift Resources</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f6f4ef;
            --surface: rgba(255, 255, 255, 0.92);
            --surface-strong: #ffffff;
            --text: #172033;
            --muted: #60708a;
            --line: #d8dfeb;
            --accent: #0f766e;
            --accent-deep: #134e4a;
            --accent-soft: #d9f3ef;
            --highlight: #f59e0b;
            --shadow: 0 24px 52px rgba(23, 32, 51, 0.10);
            --hero: linear-gradient(135deg, #fff8eb 0%, #effcf7 48%, #eef4ff 100%);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(245, 158, 11, 0.18), transparent 28%),
                radial-gradient(circle at top right, rgba(15, 118, 110, 0.18), transparent 34%),
                linear-gradient(180deg, #fcfbf8 0%, var(--bg) 100%);
        }
        h1, h2, h3, p, ul { margin: 0; }
        .page {
            max-width: 1120px;
            margin: 0 auto;
            padding: 28px 20px 56px;
        }
        .hero, .section, .next-steps {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 28px;
            box-shadow: var(--shadow);
        }
        .hero {
            padding: 28px;
            background-image: var(--hero);
        }
        .eyebrow {
            color: var(--accent);
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .hero-grid {
            display: grid;
            grid-template-columns: 1.4fr 0.9fr;
            gap: 22px;
            align-items: end;
            margin-top: 12px;
        }
        h1 {
            font-size: clamp(2.1rem, 5vw, 3.8rem);
            line-height: 1.03;
            max-width: 12ch;
        }
        .hero p {
            margin-top: 14px;
            color: var(--muted);
            line-height: 1.65;
            max-width: 46rem;
        }
        .hero-card {
            padding: 20px;
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(19, 78, 74, 0.14);
        }
        .hero-card strong {
            display: block;
            font-size: 2.4rem;
            margin-top: 8px;
        }
        .hero-card span {
            color: var(--muted);
            line-height: 1.5;
        }
        .section-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
            margin-top: 20px;
        }
        .section {
            padding: 24px;
        }
        h2 {
            margin-top: 10px;
            font-size: 1.45rem;
        }
        .section p {
            margin-top: 10px;
            color: var(--muted);
            line-height: 1.6;
        }
        .resource-list {
            list-style: none;
            padding: 0;
            margin-top: 16px;
            display: grid;
            gap: 12px;
        }
        .resource-list li {
            padding: 14px 16px;
            background: var(--surface-strong);
            border: 1px solid var(--line);
            border-radius: 18px;
        }
        .resource-list strong {
            display: block;
            font-size: 1rem;
        }
        .resource-list span {
            display: block;
            margin-top: 6px;
            color: var(--muted);
            line-height: 1.5;
        }
        .next-steps {
            margin-top: 20px;
            padding: 24px;
            background: linear-gradient(135deg, #102542 0%, #134e4a 100%);
            color: #ffffff;
        }
        .next-steps .eyebrow,
        .next-steps p,
        .next-steps li {
            color: rgba(255, 255, 255, 0.84);
        }
        .next-steps ul {
            margin-top: 16px;
            padding-left: 20px;
            display: grid;
            gap: 10px;
            line-height: 1.55;
        }
        .pill {
            display: inline-block;
            margin-top: 12px;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(245, 158, 11, 0.16);
            color: var(--highlight);
            font-size: 0.84rem;
            font-weight: 700;
        }
        @media (max-width: 860px) {
            .hero-grid, .section-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <main class="page">
        <section class="hero" aria-labelledby="resources-heading">
            <div class="eyebrow">BriefLift resources</div>
            <div class="hero-grid">
                <div>
                    <h1 id="resources-heading">Operational resources for teams building better briefs.</h1>
                    <p>Explore BriefLift playbooks, templates, and guides designed to help strategy, content, and launch teams move from intake to execution with less ambiguity and faster approvals.</p>
                </div>
                <aside class="hero-card" aria-label="Resource library summary">
                    <div class="eyebrow">Library snapshot</div>
                    <strong>6 core resources</strong>
                    <span>Built for campaign planning, workflow design, stakeholder reviews, and launch readiness.</span>
                    <div class="pill">Customer-facing resource hub</div>
                </aside>
            </div>
        </section>
        <section class="section-grid" aria-label="Resource categories">
            <section class="section" aria-labelledby="featured-playbooks">
                <div class="eyebrow">Featured</div>
                <h2 id="featured-playbooks">Playbooks for repeatable campaign operations</h2>
                <p>These featured playbooks help teams standardize how they plan work, route approvals, and keep cross-functional contributors aligned.</p>
                <ul class="resource-list">
                    <li>
                        <strong>Quarterly Campaign Planning Playbook</strong>
                        <span>Align campaign priorities, owners, and milestones before work enters production.</span>
                    </li>
                    <li>
                        <strong>Stakeholder Review Cadence Playbook</strong>
                        <span>Reduce review churn with a clearer sequence for comments, approvals, and sign-off.</span>
                    </li>
                </ul>
            </section>
            <section class="section" aria-labelledby="templates">
                <div class="eyebrow">Templates</div>
                <h2 id="templates">Templates teams can adapt quickly</h2>
                <p>BriefLift templates give marketers a reliable starting point for launch planning, localization, and message handoffs.</p>
                <ul class="resource-list">
                    <li>
                        <strong>Product Launch Brief Template</strong>
                        <span>Capture audience, positioning, channels, and dependencies in one reusable structure.</span>
                    </li>
                    <li>
                        <strong>Regional Campaign Localization Checklist</strong>
                        <span>Adapt central messaging to local teams while preserving timing and campaign intent.</span>
                    </li>
                </ul>
            </section>
            <section class="section" aria-labelledby="operational-guides">
                <div class="eyebrow">Operational guides</div>
                <h2 id="operational-guides">Guides for day-to-day workflow clarity</h2>
                <p>These guides support the operational details that keep brief production healthy once intake volume and stakeholders expand.</p>
                <ul class="resource-list">
                    <li>
                        <strong>Editorial Workflow Operating Guide</strong>
                        <span>Define intake, prioritization, approvals, and publishing for recurring editorial programs.</span>
                    </li>
                    <li>
                        <strong>Measurement Readiness Guide</strong>
                        <span>Confirm KPIs, reporting views, and ownership before campaign execution begins.</span>
                    </li>
                </ul>
            </section>
            <section class="section" aria-labelledby="recommended-next-steps">
                <div class="eyebrow">Recommended next steps</div>
                <h2 id="recommended-next-steps">What to do after browsing the resources</h2>
                <p>Use the resource hub to identify the operating gap your team needs to solve first, then move into a smaller pilot before scaling process changes.</p>
                <ul class="resource-list">
                    <li>
                        <strong>Choose one planning workflow to standardize</strong>
                        <span>Start with a single campaign or launch motion to prove the process with lower operational risk.</span>
                    </li>
                    <li>
                        <strong>Pair a template with a review playbook</strong>
                        <span>Teams move faster when content structure and approval rhythm improve together.</span>
                    </li>
                </ul>
            </section>
        </section>
        <section class="next-steps" aria-labelledby="next-steps-heading">
            <div class="eyebrow">Next steps</div>
            <h2 id="next-steps-heading">Build a cleaner brief workflow with the right starting materials.</h2>
            <p>Whether the immediate need is better playbooks, stronger templates, or more reliable operational guides, BriefLift gives teams a practical foundation for improving how work gets planned and approved.</p>
            <ul>
                <li>Use featured playbooks to clarify operating expectations across stakeholders.</li>
                <li>Adopt templates to speed up intake and keep briefs consistent across teams.</li>
                <li>Follow the guides to strengthen execution, measurement, and next-step decisions.</li>
            </ul>
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

        if parsed.path == "/integrations":
            self.write_html(HTTPStatus.OK, INTEGRATIONS_HTML)
            return

        if parsed.path == "/faq":
            self.write_html(HTTPStatus.OK, FAQ_HTML)
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

        if parsed.path == "/resources":
            self.write_html(HTTPStatus.OK, RESOURCES_HTML)
            return

        if parsed.path == "/changelog":
            self.write_html(HTTPStatus.OK, CHANGELOG_HTML)
            return

        if parsed.path == "/roadmap":
            self.write_html(HTTPStatus.OK, ROADMAP_HTML)
            return

        if parsed.path == "/ai-review":
            self.write_html(HTTPStatus.OK, AI_REVIEW_HTML)
            return

        if parsed.path == "/api/pricing":
            self.write_json(HTTPStatus.OK, PRICING_DATA)
            return

        if parsed.path == "/api/integrations":
            self.write_json(HTTPStatus.OK, INTEGRATIONS_DATA)
            return

        if parsed.path == "/api/faq":
            self.write_json(HTTPStatus.OK, FAQ_DATA)
            return

        if parsed.path == "/api/customers":
            self.write_json(HTTPStatus.OK, CUSTOMERS_DATA)
            return

        if parsed.path == "/api/trust":
            self.write_json(HTTPStatus.OK, TRUST_DATA)
            return

        if parsed.path == "/api/resources":
            self.write_json(HTTPStatus.OK, RESOURCES_DATA)
            return

        if parsed.path == "/api/changelog":
            self.write_json(HTTPStatus.OK, CHANGELOG_DATA)
            return

        if parsed.path == "/api/roadmap":
            self.write_json(HTTPStatus.OK, ROADMAP_DATA)
            return

        if parsed.path == "/api/ai-review":
            self.write_json(HTTPStatus.OK, AI_REVIEW_DATA)
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
