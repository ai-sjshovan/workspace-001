from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from wayfinder.db import connect, filtered_opportunities, insert_opportunities, rescore_opportunities
from wayfinder.models import Opportunity, scoring_weights


class OpportunityScoringTests(unittest.TestCase):
    def write_config(self, config_path: Path, storage_path: Path) -> None:
        config_path.write_text(
            "\n".join(
                [
                    "wayfinder:",
                    f"  storage_path: {storage_path}",
                ]
            ),
            encoding="utf-8",
        )

    def test_rescore_is_deterministic_for_same_inputs_and_orders_newer_opportunity_first(self) -> None:
        weights = scoring_weights({})
        opportunities = [
            Opportunity(
                title="Older agency reporting workflow",
                source="oss-ledger",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=4,
                build_difficulty="low",
                monetization_strategy="Subscription reporting workflow",
                collected_at="2026-01-10T12:00:00+00:00",
                raw={"verdict": "high-leverage market research", "useful_outputs": ["dashboard", "analytics"]},
            ),
            Opportunity(
                title="Newer agency reporting workflow",
                source="oss-ledger",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=4,
                build_difficulty="low",
                monetization_strategy="Subscription reporting workflow",
                collected_at="2026-01-20T12:00:00+00:00",
                raw={"verdict": "high-leverage market research", "useful_outputs": ["dashboard", "analytics"]},
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            conn = connect(Path(tmpdir) / "wayfinder.db")
            try:
                self.assertEqual(insert_opportunities(conn, opportunities, weights), 2)

                first_rows = filtered_opportunities(conn, limit=2)
                first_scores = [row["opportunity_score"] for row in first_rows]
                first_components = [json.loads(row["score_components_json"]) for row in first_rows]

                updated = rescore_opportunities(conn, weights)
                second_rows = filtered_opportunities(conn, limit=2)
                second_scores = [row["opportunity_score"] for row in second_rows]
                second_components = [json.loads(row["score_components_json"]) for row in second_rows]
            finally:
                conn.close()

        self.assertEqual(updated, 2)
        self.assertEqual(first_scores, second_scores)
        self.assertEqual(first_components, second_components)
        self.assertEqual(second_rows[0]["title"], "Newer agency reporting workflow")
        self.assertGreater(second_rows[0]["opportunity_score"], second_rows[1]["opportunity_score"])

    def test_score_command_prints_ranked_opportunities_in_score_order(self) -> None:
        weights = scoring_weights({})
        opportunities = [
            Opportunity(
                title="Lower evidence opportunity",
                source="oss-ledger",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=1,
                build_difficulty="medium",
                monetization_strategy="Subscription reporting workflow",
                collected_at="2026-01-15T12:00:00+00:00",
                raw={"verdict": "market research", "useful_outputs": ["dashboard"]},
            ),
            Opportunity(
                title="Higher evidence opportunity",
                source="oss-ledger",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=4,
                build_difficulty="low",
                monetization_strategy="Subscription reporting workflow",
                collected_at="2026-01-20T12:00:00+00:00",
                raw={"verdict": "high-leverage market research", "useful_outputs": ["dashboard", "analytics"]},
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "wayfinder.db"
            config_path = Path(tmpdir) / "wayfinder.yaml"
            conn = connect(storage_path)
            try:
                self.assertEqual(insert_opportunities(conn, opportunities, weights), 2)
                conn.commit()
            finally:
                conn.close()

            self.write_config(config_path, storage_path)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "wayfinder",
                    "--config",
                    str(config_path),
                    "score",
                    "--limit",
                    "2",
                    "--no-color",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        output = result.stdout
        self.assertIn("score=", output)
        self.assertIn("pain=", output)
        self.assertIn("freshness=", output)
        self.assertIn("recurrence=", output)
        self.assertIn("source=", output)
        self.assertIn("fit=", output)
        self.assertLess(output.index("Higher evidence opportunity"), output.index("Lower evidence opportunity"))

    def test_export_command_prints_foundry_ready_drafts_in_ranked_order(self) -> None:
        weights = scoring_weights({})
        opportunities = [
            Opportunity(
                title="Lower evidence opportunity",
                source="oss-ledger",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=1,
                build_difficulty="medium",
                monetization_strategy="Subscription reporting workflow",
                iteration_angle="Make weekly reporting faster for small agencies.",
                foundry_task_suggestions="Validate whether teams want a lighter review queue.",
                collected_at="2026-01-15T12:00:00+00:00",
                raw={"verdict": "market research", "useful_outputs": ["dashboard"]},
            ),
            Opportunity(
                title="Higher evidence opportunity",
                source="oss-ledger",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=4,
                build_difficulty="low",
                monetization_strategy="Subscription reporting workflow",
                iteration_angle="Turn the top evidence into an operator-ready task draft.",
                foundry_task_suggestions="Review the current evidence and promote the clearest next task.",
                collected_at="2026-01-20T12:00:00+00:00",
                raw={"verdict": "high-leverage market research", "useful_outputs": ["dashboard", "analytics"]},
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "wayfinder.db"
            config_path = Path(tmpdir) / "wayfinder.yaml"
            conn = connect(storage_path)
            try:
                self.assertEqual(insert_opportunities(conn, opportunities, weights), 2)
                conn.commit()
            finally:
                conn.close()

            self.write_config(config_path, storage_path)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "wayfinder",
                    "--config",
                    str(config_path),
                    "export",
                    "--limit",
                    "2",
                    "--min-score",
                    "0",
                    "--no-color",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        output = result.stdout
        self.assertIn("## Task Draft 1: Higher evidence opportunity for reporting", output)
        self.assertIn("Metadata: source=oss-ledger | category=reporting | score=", output)
        self.assertIn("### Goal", output)
        self.assertIn("### Acceptance Criteria", output)
        self.assertIn("### Validation", output)
        self.assertIn("### Scope Boundaries", output)
        self.assertIn("Do not call LLMs.", output)
        self.assertLess(output.index("Higher evidence opportunity for reporting"), output.index("Lower evidence opportunity for reporting"))
