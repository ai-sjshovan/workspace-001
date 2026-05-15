from __future__ import annotations

import argparse
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wayfinder.adapters.hackernews import HackerNewsAdapter, HackerNewsCollectError
from wayfinder.cli import ingest_source
from wayfinder.config import load_config, source_configs
from wayfinder.db import connect, insert_signals, search_signals
from wayfinder.models import Signal


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

    def test_healthcheck_fails_when_fixture_misses_configured_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "hn-fixture.json"
            fixture_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "query": "SaaS pain points",
                                "hits": [{"objectID": "4001", "title": "Example"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            adapter = HackerNewsAdapter(
                "hackernews",
                {
                    "fixture_path": str(fixture_path),
                    "queries": ["SaaS pain points", "startup idea validation"],
                },
            )

            ok, message = adapter.healthcheck()

        self.assertFalse(ok)
        self.assertEqual(
            message,
            "hackernews fixture_path is missing hits for configured queries: startup idea validation",
        )

    def test_collect_keeps_multi_query_metadata_stable_across_repeated_merges(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "hn-fixture.json"
            fixture_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {"query": "founder pain", "hits": [{"objectID": "42", "title": "Ask HN: Founder pain"}]},
                            {"query": "startup idea validation", "hits": [{"objectID": "42", "title": "Ask HN: Founder pain"}]},
                            {"query": "competitor analysis tool", "hits": [{"objectID": "42", "story_title": "Ask HN: Founder pain"}]},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            adapter = HackerNewsAdapter(
                "hackernews",
                {
                    "fixture_path": str(fixture_path),
                    "queries": [
                        {"query": "founder pain", "label": "zeta"},
                        {"query": "startup idea validation", "label": "alpha"},
                        {"query": "competitor analysis tool", "label": "beta"},
                    ],
                },
            )

            records = adapter.collect()
            batch = adapter.normalize(records)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["_wayfinder_queries"], ["founder pain", "startup idea validation", "competitor analysis tool"])
        self.assertEqual(records[0]["_wayfinder_categories"], ["zeta", "alpha", "beta"])
        self.assertEqual(len(batch.signals), 1)
        self.assertEqual(batch.signals[0].category, "alpha")
        self.assertEqual(
            batch.signals[0].raw["_wayfinder_queries"],
            ["competitor analysis tool", "founder pain", "startup idea validation"],
        )

    def test_fixture_healthcheck_collect_normalize_allows_zero_hit_query_and_keeps_schema_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "hn-fixture.json"
            fixture_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {"query": "SaaS pain points", "hits": []},
                            {
                                "query": "startup idea validation",
                                "hits": [
                                    {
                                        "objectID": "4003",
                                        "title": "What startup idea validation misses",
                                        "story_title": "What startup idea validation misses",
                                        "story_text": "People collect wish lists but not operational proof from public discussions.",
                                        "comment_text": "",
                                        "url": "https://example.com/startup-idea-validation-misses",
                                        "author": "rowan",
                                        "points": 57,
                                        "created_at": "2026-05-12T08:15:00Z",
                                    }
                                ],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            adapter = HackerNewsAdapter(
                "hackernews",
                {
                    "fixture_path": str(fixture_path),
                    "queries": [
                        {"query": "SaaS pain points", "label": "founder-pain"},
                        {"query": "startup idea validation", "label": "idea-validation"},
                    ],
                },
            )

            ok, message = adapter.healthcheck()
            records = adapter.collect()
            batch = adapter.normalize(records)
            conn = connect(Path(":memory:"))
            try:
                inserted = insert_signals(conn, batch.signals)
                rows = search_signals(conn, "operational proof", limit=5)
            finally:
                conn.close()

        self.assertTrue(ok)
        self.assertIn("HN deterministic fixture configured with 2 queries", message)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["objectID"], "4003")
        self.assertEqual(records[0]["_wayfinder_query"], "startup idea validation")
        self.assertEqual(records[0]["_wayfinder_queries"], ["startup idea validation"])
        self.assertEqual(len(batch.signals), 1)
        self.assertEqual(batch.signals[0].category, "idea-validation")
        self.assertEqual(inserted, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source"], "hackernews")
        self.assertEqual(rows[0]["source_id"], "4003")

    def test_normalize_keeps_sparse_public_hits_deterministic(self) -> None:
        adapter = HackerNewsAdapter("hackernews", {"queries": ["startup idea validation"]})
        raw_records = [
            {
                "story_id": 8055654,
                "story_title": "",
                "title": "",
                "story_url": "http://cayenneapps.com",
                "url": "",
                "author": "sangria",
                "points": None,
                "created_at": "2014-07-18T21:10:54Z",
                "comment_text": "startup idea validation in the wild",
                "_wayfinder_query": "startup idea validation",
                "_wayfinder_category": "validation",
            }
        ]

        batch = adapter.normalize(raw_records)

        self.assertEqual(len(batch.signals), 1)
        signal = batch.signals[0]
        self.assertEqual(signal.source_id, "8055654")
        self.assertEqual(signal.title, "HN item 8055654")
        self.assertEqual(signal.source_url, "http://cayenneapps.com")
        self.assertEqual(signal.author, "sangria")
        self.assertEqual(signal.category, "validation")
        self.assertEqual(signal.raw["objectID"], "8055654")

    def test_normalize_skips_malformed_hits_without_losing_valid_records(self) -> None:
        adapter = HackerNewsAdapter("hackernews", {"queries": ["startup idea validation"]})
        raw_records = [
            {
                "objectID": {"bad": "shape"},
                "title": "Bad item",
                "comment_text": "should be skipped",
                "_wayfinder_query": "startup idea validation",
                "_wayfinder_category": "validation",
            },
            {
                "story_id": 8055654,
                "story_title": "",
                "title": "",
                "story_url": "http://cayenneapps.com",
                "url": "",
                "author": "sangria",
                "points": None,
                "created_at": "2014-07-18T21:10:54Z",
                "comment_text": "startup idea validation in the wild",
                "_wayfinder_query": "startup idea validation",
                "_wayfinder_category": "validation",
            },
        ]

        batch = adapter.normalize(raw_records)

        self.assertEqual(len(batch.signals), 1)
        self.assertEqual(batch.signals[0].source_id, "8055654")

    def test_dry_run_does_not_write_db_and_live_insert_is_searchable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fixture_path = root / "hn-fixture.json"
            storage_path = root / "wayfinder.db"
            audit_path = root / "audit.log"
            fixture_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "query": "SaaS pain points",
                                "hits": [
                                    {
                                        "objectID": "4001",
                                        "title": "Founders keep paying for SaaS pain twice",
                                        "story_title": "Founders keep paying for SaaS pain twice",
                                        "story_text": "B2B teams still glue together point solutions instead of one reporting workflow.",
                                        "comment_text": "",
                                        "url": "https://example.com/founders-paying-for-saas-pain",
                                        "author": "atlas",
                                        "points": 84,
                                        "created_at": "2026-05-10T12:00:00Z",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config_path = root / "wayfinder.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "wayfinder:",
                        f"  storage_path: {storage_path.name}",
                        f"  audit_log: {audit_path.name}",
                        "sources:",
                        "  hackernews:",
                        "    status: dry-run-only",
                        "    kind: hackernews",
                        f"    fixture_path: {fixture_path.name}",
                        "    queries:",
                        '      - "SaaS pain points"',
                    ]
                ),
                encoding="utf-8",
            )
            config = load_config(config_path)
            cfg = source_configs(config)["hackernews"]
            args = argparse.Namespace(dry_run=True, config=str(config_path), no_color=True)

            rc, message = ingest_source("hackernews", cfg, args, config)

            self.assertEqual(rc, 0)
            self.assertIn("hackernews: dry-run queries=1 collected=1 normalized=1 signals=1", message)
            self.assertFalse(storage_path.exists())

            adapter = HackerNewsAdapter("hackernews", cfg)
            batch = adapter.normalize(adapter.collect())
            conn = connect(storage_path)
            try:
                inserted = insert_signals(conn, batch.signals)
                rows = search_signals(conn, "reporting workflow", limit=5)
            finally:
                conn.close()

            self.assertEqual(inserted, 1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source"], "hackernews")
            self.assertEqual(rows[0]["source_id"], "4001")

    def test_live_insert_upserts_same_hn_item_without_duplicate_drift(self) -> None:
        conn = connect(Path(":memory:"))
        try:
            first = Signal(
                source="hackernews",
                source_id="42",
                source_url="https://example.com/original",
                title="Ask HN: Founder pain",
                body="Need a better workflow",
                author="alice",
                score=8,
                category="alpha",
                raw={"objectID": "42", "title": "Ask HN: Founder pain"},
            )
            second = Signal(
                source="hackernews",
                source_id="42",
                source_url="https://example.com/updated",
                title="Ask HN: Founder pain updated",
                body="Need a better workflow with better normalization",
                author="alice",
                score=12,
                category="alpha",
                raw={"objectID": "42", "title": "Ask HN: Founder pain updated"},
            )

            first_inserted = insert_signals(conn, [first])
            second_inserted = insert_signals(conn, [second])
            rows = conn.execute(
                "SELECT source_id, source_url, title, body, score FROM signals WHERE source = ?",
                ("hackernews",),
            ).fetchall()
        finally:
            conn.close()

        self.assertEqual(first_inserted, 1)
        self.assertEqual(second_inserted, 0)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_id"], "42")
        self.assertEqual(rows[0]["source_url"], "https://example.com/updated")
        self.assertEqual(rows[0]["title"], "Ask HN: Founder pain updated")
        self.assertEqual(rows[0]["score"], 12)


if __name__ == "__main__":
    unittest.main()
