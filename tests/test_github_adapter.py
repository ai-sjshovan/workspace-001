from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

from wayfinder.adapters.github import GitHubAdapter, GitHubCollectError


class GitHubAdapterTests(unittest.TestCase):
    def test_healthcheck_handles_missing_config(self) -> None:
        adapter = GitHubAdapter("github", None)

        ok, message = adapter.healthcheck()

        self.assertFalse(ok)
        self.assertEqual(message, "github source requires a non-empty queries list")

    def test_healthcheck_reports_invalid_timeout_cleanly(self) -> None:
        adapter = GitHubAdapter("github", {"queries": ["market research"], "timeout_seconds": "fast"})

        ok, message = adapter.healthcheck()

        self.assertFalse(ok)
        self.assertEqual(message, "github source timeout_seconds must be a positive number")

    def test_headers_keep_anonymous_fallback_and_support_optional_token(self) -> None:
        anonymous = GitHubAdapter("github", {"queries": ["market research"]})
        authenticated = GitHubAdapter("github", {"queries": ["market research"], "token": "secret-token"})

        self.assertNotIn("Authorization", anonymous._headers())
        self.assertEqual(authenticated._headers()["Authorization"], "Bearer secret-token")

    def test_collect_reports_timeout_with_query_context(self) -> None:
        adapter = GitHubAdapter(
            "github",
            {
                "base_url": "https://api.github.com/search/repositories",
                "timeout_seconds": "3",
                "queries": ["founder pain"],
            },
        )

        with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
            with self.assertRaises(GitHubCollectError) as ctx:
                adapter.collect()

        self.assertEqual(str(ctx.exception), "GitHub timeout for query 'founder pain' after 3s")

    def test_collect_dedupes_duplicate_repositories_and_merges_query_context(self) -> None:
        adapter = GitHubAdapter(
            "github",
            {
                "base_url": "https://api.github.com/search/repositories",
                "queries": [
                    {"query": "founder pain", "label": "pain-research"},
                    {"query": "competitor analysis", "label": "competitor-research"},
                ],
            },
        )

        responses = iter(
            [
                {"items": [{"full_name": "org/acme", "description": "Short", "topics": ["analytics"], "stargazers_count": 12, "updated_at": "2026-05-14T12:00:00Z"}]},
                {"items": [{"full_name": "org/acme", "description": "Longer repository description", "topics": ["founder-tools"], "stargazers_count": 30, "updated_at": "2026-05-14T12:30:00Z"}]},
            ]
        )

        class FakeResponse:
            def __init__(self, payload: dict[str, object]) -> None:
                self.payload = payload

            def read(self) -> bytes:
                import json

                return json.dumps(self.payload).encode("utf-8")

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

        def fake_urlopen(request, timeout):
            self.assertIn("api.github.com/search/repositories", request.full_url)
            self.assertGreater(timeout, 0)
            return FakeResponse(next(responses))

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            records = adapter.collect()

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["full_name"], "org/acme")
        self.assertEqual(record["description"], "Longer repository description")
        self.assertEqual(record["stargazers_count"], 30)
        self.assertEqual(record["updated_at"], "2026-05-14T12:30:00Z")
        self.assertEqual(record["topics"], ["analytics", "founder-tools"])
        self.assertEqual(record["_wayfinder_queries"], ["founder pain", "competitor analysis"])
        self.assertEqual(record["_wayfinder_categories"], ["pain-research", "competitor-research"])

    def test_normalize_emits_searchable_signal_product_and_opportunity_records(self) -> None:
        adapter = GitHubAdapter("github", {"queries": ["founder pain"]})
        raw_records = [
            {
                "name": "acme",
                "full_name": "org/acme",
                "html_url": "https://github.com/org/acme",
                "description": " Founder pain tracker ",
                "topics": ["analytics", "founder-tools", "analytics"],
                "stargazers_count": 12,
                "updated_at": "2026-05-14T12:00:00Z",
                "language": "Python",
                "homepage": "https://acme.example",
                "license": {"spdx_id": "MIT"},
                "_wayfinder_query": "founder pain",
                "_wayfinder_category": "pain-research",
                "_wayfinder_queries": ["founder pain", "competitor analysis"],
                "_wayfinder_categories": ["pain-research", "competitor-research"],
            }
        ]

        batch = adapter.normalize(raw_records)

        self.assertEqual(len(batch.signals), 1)
        self.assertEqual(len(batch.products), 1)
        self.assertEqual(len(batch.opportunities), 1)
        signal = batch.signals[0]
        product = batch.products[0]
        opportunity = batch.opportunities[0]
        self.assertEqual(signal.source, "github")
        self.assertEqual(signal.source_id, "org/acme")
        self.assertEqual(signal.source_url, "https://github.com/org/acme")
        self.assertEqual(signal.title, "org/acme")
        self.assertIn("Founder pain tracker", signal.body)
        self.assertIn("stars=12", signal.body)
        self.assertIn("language=Python", signal.body)
        self.assertIn("license=MIT", signal.body)
        self.assertIn("founder pain, competitor analysis", signal.body)
        self.assertEqual(signal.score, 12.0)
        self.assertEqual(signal.product, "org/acme")
        self.assertEqual(signal.category, "analytics, founder-tools")
        self.assertEqual(signal.feature_request, "founder pain, competitor analysis")
        self.assertEqual(signal.monetization_signal, "MIT")
        self.assertEqual(product.product_name, "org/acme")
        self.assertEqual(product.url, "https://github.com/org/acme")
        self.assertEqual(product.category, "analytics, founder-tools")
        self.assertEqual(product.audience, "pain-research, competitor-research")
        self.assertIn("repo=acme", product.strengths)
        self.assertIn("homepage=https://acme.example", product.strengths)
        self.assertEqual(product.feature_gaps, "Matched GitHub queries: founder pain, competitor analysis")
        self.assertEqual(product.monetization_notes, "GitHub repo org/acme topics=analytics, founder-tools")
        self.assertEqual(opportunity.title, "Inspect org/acme for leverage")
        self.assertEqual(opportunity.source, "github")
        self.assertEqual(opportunity.category, "analytics, founder-tools")
        self.assertEqual(opportunity.evidence_count, 2)
        self.assertEqual(opportunity.competing_products, "org/acme")
        self.assertIn("Matched public GitHub demand: founder pain, competitor analysis", opportunity.what_users_want_better)


if __name__ == "__main__":
    unittest.main()
