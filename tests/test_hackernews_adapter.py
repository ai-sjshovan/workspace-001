from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

from wayfinder.adapters.hackernews import HackerNewsAdapter, HackerNewsCollectError


class HackerNewsAdapterTests(unittest.TestCase):
    def test_healthcheck_handles_malformed_config(self) -> None:
        adapter = HackerNewsAdapter("hackernews", None)

        ok, message = adapter.healthcheck()

        self.assertFalse(ok)
        self.assertEqual(message, "hackernews source requires a non-empty queries list")

    def test_healthcheck_rejects_non_official_endpoint(self) -> None:
        adapter = HackerNewsAdapter(
            "hackernews",
            {
                "base_url": "https://example.com/api/v1/search",
                "queries": ["founder pain"],
            },
        )

        ok, message = adapter.healthcheck()

        self.assertFalse(ok)
        self.assertEqual(message, "hackernews source requires the official https://hn.algolia.com search endpoint")

    def test_healthcheck_rejects_invalid_hits_per_page(self) -> None:
        adapter = HackerNewsAdapter(
            "hackernews",
            {
                "queries": [
                    {
                        "query": "founder pain",
                        "hits_per_page": "many",
                    }
                ],
            },
        )

        ok, message = adapter.healthcheck()

        self.assertFalse(ok)
        self.assertEqual(message, "hackernews source hits_per_page must be an integer between 1 and 100")

    def test_collect_reports_timeout_with_query_context(self) -> None:
        adapter = HackerNewsAdapter(
            "hackernews",
            {
                "base_url": "https://hn.algolia.com/api/v1/search",
                "timeout_seconds": "2",
                "queries": ["founder pain"],
            },
        )

        with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
            with self.assertRaises(HackerNewsCollectError) as ctx:
                adapter.collect()

        self.assertEqual(str(ctx.exception), "timeout for query 'founder pain' after 2s")

    def test_normalize_dedupes_duplicates_into_stable_signal(self) -> None:
        adapter = HackerNewsAdapter("hackernews", {"queries": ["founder pain"]})
        raw_records = [
            {
                "objectID": "42",
                "title": "Ask HN: Founder pain",
                "url": "",
                "author": "alice",
                "points": 8,
                "story_text": "",
                "comment_text": "Need a better workflow",
                "_wayfinder_query": "founder pain",
                "_wayfinder_category": "zeta",
                "created_at": "2026-05-14T12:00:00Z",
            },
            {
                "objectID": "42",
                "story_title": "Ask HN: Founder pain",
                "url": "https://example.com/founder-pain",
                "author": "alice",
                "points": 12,
                "story_text": "Need a better workflow",
                "comment_text": "",
                "_wayfinder_query": "founder pain",
                "_wayfinder_category": "alpha",
                "created_at": "2026-05-14T12:01:00Z",
            },
        ]

        batch = adapter.normalize(raw_records)

        self.assertEqual(len(batch.signals), 1)
        signal = batch.signals[0]
        self.assertEqual(signal.source_id, "42")
        self.assertEqual(signal.source_url, "https://example.com/founder-pain")
        self.assertEqual(signal.title, "Ask HN: Founder pain")
        self.assertEqual(signal.author, "alice")
        self.assertEqual(signal.score, 12.0)
        self.assertEqual(signal.category, "alpha")
        self.assertEqual(
            signal.body,
            "Need a better workflow\nhttps://example.com/founder-pain\nhttps://news.ycombinator.com/item?id=42",
        )

    def test_normalize_is_stable_when_duplicate_records_share_same_primary_keys(self) -> None:
        adapter = HackerNewsAdapter("hackernews", {"queries": ["founder pain"]})
        raw_records = [
            {
                "objectID": "42",
                "title": "Ask HN: Founder pain B",
                "url": "https://example.com/b",
                "author": "alice",
                "points": 5,
                "story_text": "Later body",
                "comment_text": "",
                "_wayfinder_query": "founder pain",
                "_wayfinder_category": "alpha",
                "created_at": "2026-05-14T12:00:00Z",
            },
            {
                "objectID": "42",
                "title": "Ask HN: Founder pain A",
                "url": "https://example.com/a",
                "author": "alice",
                "points": 5,
                "story_text": "Earlier body",
                "comment_text": "",
                "_wayfinder_query": "founder pain",
                "_wayfinder_category": "alpha",
                "created_at": "2026-05-14T12:00:00Z",
            },
        ]

        batch = adapter.normalize(raw_records)

        self.assertEqual(len(batch.signals), 1)
        signal = batch.signals[0]
        self.assertEqual(signal.source_url, "https://example.com/a")
        self.assertEqual(signal.title, "Ask HN: Founder pain A")
        self.assertEqual(signal.raw["url"], "https://example.com/a")
        self.assertEqual(signal.raw["title"], "Ask HN: Founder pain A")


if __name__ == "__main__":
    unittest.main()
