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

    def test_normalize_emits_stable_signal_and_product_records(self) -> None:
        adapter = GitHubAdapter("github", {"queries": ["founder pain"]})
        raw_records = [
            {
                "name": "acme",
                "full_name": "org/acme",
                "html_url": "https://github.com/org/acme",
                "description": "Founder pain tracker",
                "topics": ["analytics", "founder-tools"],
                "stargazers_count": 12,
                "updated_at": "2026-05-14T12:00:00Z",
                "_wayfinder_query": "founder pain",
                "_wayfinder_category": "pain-research",
            },
            {
                "name": "acme",
                "full_name": "org/acme",
                "html_url": "https://github.com/org/acme",
                "description": "Duplicate row should be ignored",
                "topics": ["duplicate"],
                "stargazers_count": 99,
                "updated_at": "2026-05-14T12:01:00Z",
                "_wayfinder_query": "founder pain",
                "_wayfinder_category": "zzz",
            },
        ]

        batch = adapter.normalize(raw_records)

        self.assertEqual(len(batch.signals), 1)
        self.assertEqual(len(batch.products), 1)
        signal = batch.signals[0]
        product = batch.products[0]
        self.assertEqual(signal.source, "github")
        self.assertEqual(signal.source_id, "org/acme")
        self.assertEqual(signal.source_url, "https://github.com/org/acme")
        self.assertEqual(signal.title, "org/acme")
        self.assertEqual(signal.body, "Founder pain tracker")
        self.assertEqual(signal.score, 12.0)
        self.assertEqual(signal.product, "org/acme")
        self.assertEqual(signal.category, "analytics, founder-tools")
        self.assertEqual(product.product_name, "org/acme")
        self.assertEqual(product.url, "https://github.com/org/acme")
        self.assertEqual(product.category, "analytics, founder-tools")
        self.assertEqual(product.audience, "pain-research")
        self.assertEqual(product.strengths, "repo=acme; stars=12; updated=2026-05-14T12:00:00Z")
        self.assertEqual(product.monetization_notes, "GitHub repo org/acme topics=analytics, founder-tools")


if __name__ == "__main__":
    unittest.main()
