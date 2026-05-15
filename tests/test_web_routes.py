from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from wayfinder.config import load_config, source_configs
from wayfinder.db import connect, insert_opportunities, insert_products, insert_signals
from wayfinder.models import Opportunity, ProductIntel, Signal, scoring_weights
from wayfinder.web import WayfinderHandler


class WayfinderRouteSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base_config = load_config()
        cls.source_name = sorted(source_configs(base_config))[0]
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.storage_path = Path(cls.temp_dir.name) / "wayfinder-test.db"
        cls.config = dict(base_config)
        cls.config["wayfinder"] = {
            **(base_config.get("wayfinder") if isinstance(base_config.get("wayfinder"), dict) else {}),
            "storage_path": str(cls.storage_path),
        }
        conn = connect(cls.storage_path)
        try:
            insert_signals(
                conn,
                [
                    Signal(
                        source=cls.source_name,
                        source_id="dashboard-smoke",
                        source_url="https://example.com/dashboard-smoke",
                        title="Wayfinder dashboard smoke signal",
                        body="Signal fixture for dashboard browse filters.",
                        score=7,
                        product="Pain Radar",
                        category="market-research",
                        pain_type="reporting delays",
                        feature_request="deeper source drill-ins",
                    )
                ],
            )
            insert_products(
                conn,
                [
                    ProductIntel(
                        product_name="Pain Radar",
                        url="https://example.com/pain-radar",
                        category="market-research",
                        pricing_model="subscription",
                        strengths="Turns browseable source evidence into product intel quickly.",
                        feature_gaps="Needs deeper source drill-ins in the read-only dashboard.",
                        audience="Local SEO operators",
                    )
                ],
            )
            insert_opportunities(
                conn,
                [
                    Opportunity(
                        title="Source evidence drill-ins for research operators",
                        source=cls.source_name,
                        category="market-research",
                        target_user="Agency research lead",
                        problem="Operators need source-specific evidence to validate product bets.",
                        evidence_count=4,
                        competing_products="Pain Radar",
                        what_products_do_right="Keeps a focused read-only dashboard workflow.",
                        what_users_want_better="Faster source-specific evidence review.",
                        build_difficulty="low",
                        iteration_angle="Add source detail pages with recent records and status.",
                        monetization_strategy="Subscription research workflow",
                        foundry_task_suggestions="Add focused source detail browse views",
                        raw={"verdict": "high-leverage market research", "useful_outputs": ["dashboard", "analytics"]},
                    )
                ],
                scoring_weights(cls.config),
            )
            conn.commit()
        finally:
            conn.close()
        WayfinderHandler.config = cls.config
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), WayfinderHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=5)
        cls.temp_dir.cleanup()

    def fetch(self, path: str) -> tuple[int, str]:
        try:
            with urlopen(f"{self.base_url}{path}", timeout=5) as response:
                return response.status, response.read().decode("utf-8")
        except HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")

    def test_smoke_routes_and_source_routes(self) -> None:
        status, body = self.fetch("/")
        self.assertEqual(status, 200)
        self.assertIn("Wayfinder", body)
        self.assertIn('name="product"', body)
        self.assertIn('name="market"', body)
        self.assertIn('name="pain"', body)
        self.assertIn('name="feature_gap"', body)

        status, body = self.fetch(
            f"/?source={quote(self.source_name)}&product=Pain%20Radar&market=market-research&pain=reporting%20delays&feature_gap=deeper%20source%20drill-ins"
        )
        self.assertEqual(status, 200)
        self.assertIn("Wayfinder dashboard smoke signal", body)
        self.assertIn("Open dedicated source view", body)

        status, body = self.fetch("/health")
        self.assertEqual(status, 200)
        self.assertEqual(
            json.loads(body),
            {
                "ok": True,
                "service": "wayfinder",
                "config": "loaded",
                "database": "ready",
                "storage_path": str(self.storage_path),
            },
        )

        status, body = self.fetch("/api/sources")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertGreater(payload["count"], 0)
        self.assertIn(self.source_name, [item["key"] for item in payload["sources"]])

        status, body = self.fetch(f"/api/sources?source={quote(self.source_name)}")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["source"]["key"], self.source_name)

        status, body = self.fetch(f"/sources/{quote(self.source_name)}")
        self.assertEqual(status, 200)
        self.assertIn(self.source_name, body)
        self.assertIn("Recent source records", body)
        self.assertIn("Wayfinder dashboard smoke signal", body)

        status, body = self.fetch(
            f"/search?source={quote(self.source_name)}&category=market-research&product=Pain%20Radar"
        )
        self.assertEqual(status, 200)
        self.assertIn('name="source"', body)
        self.assertIn('name="category"', body)
        self.assertIn("URL-backed filters", body)
        self.assertIn("Wayfinder dashboard smoke signal", body)
        self.assertIn(f'/sources/{quote(self.source_name)}', body)

        status, body = self.fetch("/products")
        self.assertEqual(status, 200)
        self.assertIn("Pain Radar", body)
        self.assertIn('name="category"', body)

        status, body = self.fetch("/products?category=market-research")
        self.assertEqual(status, 200)
        self.assertIn("Pain Radar", body)
        self.assertIn('selected="selected">market-research</option>', body)

        status, body = self.fetch(f"/opportunities?source={quote(self.source_name)}&category=market-research")
        self.assertEqual(status, 200)
        self.assertIn("Source evidence drill-ins for research operators", body)
        self.assertIn(f"/sources/{quote(self.source_name)}", body)
        self.assertIn("source", body)
        self.assertIn("category", body)

        status, body = self.fetch("/api/sources?source=missing-source")
        self.assertEqual(status, 404)
        payload = json.loads(body)
        self.assertEqual(payload["error"], "source_not_found")
        self.assertEqual(payload["requested_source"], "missing-source")

        status, body = self.fetch("/sources/missing-source")
        self.assertEqual(status, 404)
        self.assertIn("Source not found", body)
