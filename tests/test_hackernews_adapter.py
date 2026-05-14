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

    def test_collect_reports_timeout_with_query_context(self) -> None:
        adapter = HackerNewsAdapter(
            "hackernews",
            {
                "base_url": "https://example.com/api",
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


if __name__ == "__main__":
    unittest.main()
