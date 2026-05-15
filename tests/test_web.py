from __future__ import annotations

import unittest

from wayfinder.drafts import format_task_draft
from wayfinder.web import opportunity_detail_page


class OpportunityDetailPageTests(unittest.TestCase):
    def test_detail_page_uses_export_markdown_and_copy_controls(self) -> None:
        payload = {
            "title": "Agency reporting workflow",
            "source": "oss-ledger",
            "category": "reporting",
            "target_user": "Agency operator",
            "problem": "Teams need quicker reporting loops.",
            "evidence_count": 4,
            "competing_products": "Acme Analytics",
            "what_products_do_right": "Fast trend summaries",
            "what_users_want_better": "Clearer client-ready exports",
            "build_difficulty": "low",
            "replication_time_estimate": "2 weeks",
            "iteration_angle": "Turn the evidence into an operator-ready draft.",
            "monetization_strategy": "Subscription reporting workflow",
            "foundry_task_suggestions": "Promote the clearest next reporting task.",
            "opportunity_score": 84.2,
            "score_components": {
                "components": {
                    "pain": 29.4,
                    "freshness": 11.3,
                    "recurrence": 18.0,
                    "source_quality": 13.0,
                    "build_fit": 12.5,
                },
                "inputs": {
                    "pain": 0.84,
                    "freshness": 0.75,
                    "recurrence": 0.9,
                    "source_quality": 0.87,
                    "build_fit": 0.83,
                },
                "weights": {
                    "pain": 0.35,
                    "freshness": 0.15,
                    "recurrence": 0.2,
                    "source_quality": 0.15,
                    "build_fit": 0.15,
                },
            },
            "source_context": {
                "detail_path": "/sources/oss-ledger",
                "search_path": "/search?source=oss-ledger&market=reporting",
            },
            "linked_source_context": {
                "signal_count": 3,
                "opportunity_count": 1,
                "avg_score": 8.4,
            },
        }
        related = {"signals": [], "products": []}

        html = opportunity_detail_page(payload, related)
        expected = format_task_draft(payload, 1)

        self.assertIn("Copy Markdown draft", html)
        self.assertIn('data-state="ready"', html)
        self.assertIn('id="task-draft-markdown"', html)
        self.assertIn("same Markdown formatter as <code>wayfinder export</code>", html)
        self.assertIn(expected, html)

