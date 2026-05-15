from __future__ import annotations

import argparse
import io
import socket
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from wayfinder.adapters.github import GitHubAdapter, GitHubCollectError
from wayfinder.cli import ingest_source
from wayfinder.config import load_config, source_configs
from wayfinder.db import connect, counts, insert_opportunities, insert_products, insert_signals, search_signals


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

    def test_collect_treats_missing_or_partial_items_payloads_as_empty(self) -> None:
        adapter = GitHubAdapter(
            "github",
            {
                "base_url": "https://api.github.com/search/repositories",
                "queries": ["founder pain"],
            },
        )

        class FakeResponse:
            def __init__(self, payload: object) -> None:
                self.payload = payload

            def read(self) -> bytes:
                import json

                return json.dumps(self.payload).encode("utf-8")

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

        for payload in ({}, {"items": None}, {"items": "oops"}):
            with self.subTest(payload=payload):
                with patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
                    self.assertEqual(adapter.collect(), [])

    def test_collect_allows_empty_fixture_results_for_configured_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "github-fixture.json"
            fixture_path.write_text(
                '{"results":[{"query":"founder pain","items":[]}]}',
                encoding="utf-8",
            )
            adapter = GitHubAdapter(
                "github",
                {
                    "fixture_path": str(fixture_path),
                    "queries": ["founder pain"],
                },
            )

            self.assertEqual(adapter.collect(), [])

    def test_collect_surfaces_rate_limit_from_headers_even_with_sparse_body(self) -> None:
        adapter = GitHubAdapter(
            "github",
            {
                "base_url": "https://api.github.com/search/repositories",
                "queries": ["founder pain"],
            },
        )

        error = urllib.error.HTTPError(
            url="https://api.github.com/search/repositories?q=founder+pain",
            code=403,
            msg="Forbidden",
            hdrs={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1715774400"},
            fp=io.BytesIO(b'{"message":"Forbidden"}'),
        )

        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(GitHubCollectError) as ctx:
                adapter.collect()

        self.assertIn("HTTP 403 rate limit exceeded", str(ctx.exception))
        self.assertIn("rate limit resets at 2024-05-15T12:00:00Z", str(ctx.exception))

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

    def test_collect_dedupes_duplicate_repositories_case_insensitively(self) -> None:
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
                {"items": [{"full_name": "Org/Acme", "description": "Short", "stargazers_count": 12, "updated_at": "2026-05-14T12:00:00Z"}]},
                {"items": [{"full_name": "org/acme", "description": "Longer repository description", "stargazers_count": 30, "updated_at": "2026-05-14T12:30:00Z"}]},
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

        with patch("urllib.request.urlopen", side_effect=lambda request, timeout: FakeResponse(next(responses))):
            records = adapter.collect()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["full_name"], "org/acme")
        self.assertEqual(records[0]["description"], "Longer repository description")

    def test_healthcheck_fails_when_fixture_misses_configured_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "github-fixture.json"
            fixture_path.write_text(
                '{"results":[{"query":"startup ideas pain points","items":[{"full_name":"org/acme"}]}]}',
                encoding="utf-8",
            )
            adapter = GitHubAdapter(
                "github",
                {
                    "fixture_path": str(fixture_path),
                    "queries": ["startup ideas pain points", "market research SaaS ideas"],
                },
            )

            ok, message = adapter.healthcheck()

        self.assertFalse(ok)
        self.assertEqual(
            message,
            "github fixture_path is missing items for configured queries: market research SaaS ideas",
        )

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

    def test_dry_run_does_not_write_db_and_normalized_rows_are_searchable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fixture_path = root / "github-fixture.json"
            storage_path = root / "wayfinder.db"
            audit_path = root / "audit.log"
            fixture_path.write_text(
                """
                {
                  "results": [
                    {
                      "query": "startup ideas pain points",
                      "items": [
                        {
                          "name": "pain-radar",
                          "full_name": "acme/pain-radar",
                          "html_url": "https://github.com/acme/pain-radar",
                          "description": "Founder pain search workflow for B2B SaaS teams.",
                          "topics": ["market-research", "founder-tools"],
                          "stargazers_count": 58,
                          "updated_at": "2026-05-11T09:15:00Z",
                          "language": "Python",
                          "homepage": "https://pain-radar.example",
                          "license": {"spdx_id": "MIT"}
                        }
                      ]
                    }
                  ]
                }
                """.strip(),
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
                        "  github:",
                        "    status: dry-run-only",
                        "    kind: github",
                        f"    fixture_path: {fixture_path.name}",
                        "    queries:",
                        '      - "startup ideas pain points"',
                    ]
                ),
                encoding="utf-8",
            )
            config = load_config(config_path)
            cfg = source_configs(config)["github"]
            args = argparse.Namespace(dry_run=True, config=str(config_path), no_color=True)

            rc, message = ingest_source("github", cfg, args, config)

            self.assertEqual(rc, 0)
            self.assertIn("github: dry-run queries=1 collected=1 normalized=3 signals=1 products=1 opportunities=1", message)
            self.assertFalse(storage_path.exists())

            adapter = GitHubAdapter("github", cfg)
            batch = adapter.normalize(adapter.collect())
            conn = connect(storage_path)
            try:
                inserted_signals = insert_signals(conn, batch.signals)
                inserted_products = insert_products(conn, batch.products)
                inserted_opportunities = insert_opportunities(conn, batch.opportunities, {})
                totals = counts(conn)
                rows = search_signals(conn, "founder pain search workflow", limit=5)
            finally:
                conn.close()

            self.assertEqual(inserted_signals, 1)
            self.assertEqual(inserted_products, 1)
            self.assertEqual(inserted_opportunities, 1)
            self.assertEqual(
                totals,
                {"signals": 1, "products": 1, "opportunities": 1, "ingest_runs": 0},
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source"], "github")
            self.assertEqual(rows[0]["source_id"], "acme/pain-radar")

    def test_normalize_skips_malformed_records_and_keeps_valid_items(self) -> None:
        adapter = GitHubAdapter("github", {"queries": ["founder pain"]})
        raw_records = [
            "not-a-dict",
            {"full_name": "org/missing-name", "html_url": "https://github.com/org/missing-name", "stargazers_count": 4},
            {"name": "missing-url", "full_name": "org/missing-url", "stargazers_count": 4},
            {
                "name": "bad-stars",
                "full_name": "org/bad-stars",
                "html_url": "https://github.com/org/bad-stars",
                "stargazers_count": "many",
            },
            {
                "name": "acme",
                "full_name": "org/acme",
                "html_url": "https://github.com/org/acme",
                "description": " Founder pain tracker ",
                "stargazers_count": 12,
                "_wayfinder_queries": ["founder pain"],
                "_wayfinder_categories": ["pain-research"],
            },
        ]

        batch = adapter.normalize(raw_records)  # type: ignore[arg-type]

        self.assertEqual(len(batch.signals), 1)
        self.assertEqual(len(batch.products), 1)
        self.assertEqual(len(batch.opportunities), 1)
        self.assertEqual(batch.signals[0].source_id, "org/acme")


if __name__ == "__main__":
    unittest.main()
