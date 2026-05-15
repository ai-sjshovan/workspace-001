from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from wayfinder.db import connect, insert_opportunities
from wayfinder.models import Opportunity, scoring_weights


class ExportCommandTests(unittest.TestCase):
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

    def export_output(self, config_path: Path, *args: str) -> str:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "wayfinder",
                "--config",
                str(config_path),
                "export",
                "--no-color",
                *args,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def test_export_is_filterable_deterministic_and_markdown_only(self) -> None:
        weights = scoring_weights({})
        opportunities = [
            Opportunity(
                title="Alpha reporting opportunity",
                source="oss-ledger",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=4,
                build_difficulty="low",
                monetization_strategy="Subscription reporting workflow",
                iteration_angle="Turn the top evidence into an operator-ready task draft.",
                foundry_task_suggestions="Review the current evidence and promote the clearest next task.",
                collected_at="2026-01-21T12:00:00+00:00",
                raw={"verdict": "high-leverage market research", "useful_outputs": ["dashboard", "analytics"]},
            ),
            Opportunity(
                title="Zulu reporting opportunity",
                source="oss-ledger",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=4,
                build_difficulty="low",
                monetization_strategy="Subscription reporting workflow",
                iteration_angle="Keep the draft ordering stable for the same database contents.",
                foundry_task_suggestions="Confirm deterministic output across repeat exports.",
                collected_at="2026-01-20T12:00:00+00:00",
                raw={"verdict": "high-leverage market research", "useful_outputs": ["dashboard", "analytics"]},
            ),
            Opportunity(
                title="Filtered out by score",
                source="oss-ledger",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=1,
                build_difficulty="medium",
                monetization_strategy="Subscription reporting workflow",
                iteration_angle="This row should be dropped by the score filter.",
                foundry_task_suggestions="None.",
                collected_at="2026-01-10T12:00:00+00:00",
                raw={"verdict": "market research", "useful_outputs": ["dashboard"]},
            ),
            Opportunity(
                title="Filtered out by source",
                source="github",
                category="reporting",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=4,
                build_difficulty="low",
                monetization_strategy="Subscription reporting workflow",
                iteration_angle="This row should be dropped by the source filter.",
                foundry_task_suggestions="None.",
                collected_at="2026-01-20T12:00:00+00:00",
                raw={"verdict": "high-leverage market research", "useful_outputs": ["dashboard", "analytics"]},
            ),
            Opportunity(
                title="Filtered out by category",
                source="oss-ledger",
                category="automation",
                target_user="Agency operator",
                problem="Teams need quicker reporting loops.",
                evidence_count=4,
                build_difficulty="low",
                monetization_strategy="Subscription reporting workflow",
                iteration_angle="This row should be dropped by the category filter.",
                foundry_task_suggestions="None.",
                collected_at="2026-01-20T12:00:00+00:00",
                raw={"verdict": "high-leverage market research", "useful_outputs": ["dashboard", "analytics"]},
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "wayfinder.db"
            config_path = Path(tmpdir) / "wayfinder.yaml"
            conn = connect(storage_path)
            try:
                self.assertEqual(insert_opportunities(conn, opportunities, weights), 5)
                conn.commit()
            finally:
                conn.close()

            self.write_config(config_path, storage_path)

            args = ("--limit", "5", "--min-score", "60", "--source", "oss-ledger", "--category", "reporting")
            first_output = self.export_output(config_path, *args)
            second_output = self.export_output(config_path, *args)

        self.assertEqual(first_output, second_output)
        self.assertIn("## Task Draft 1: Alpha reporting opportunity for reporting", first_output)
        self.assertIn("## Task Draft 2: Zulu reporting opportunity for reporting", first_output)
        self.assertLess(
            first_output.index("Alpha reporting opportunity for reporting"),
            first_output.index("Zulu reporting opportunity for reporting"),
        )
        self.assertNotIn("Filtered out by score", first_output)
        self.assertNotIn("Filtered out by source", first_output)
        self.assertNotIn("Filtered out by category", first_output)
        self.assertIn("### Goal", first_output)
        self.assertIn("### Validation", first_output)
        self.assertIn("### Scope Boundaries", first_output)
        self.assertIn("### Delivery Expectation", first_output)
        self.assertIn("Do not call LLMs.", first_output)
        self.assertIn("Do not create Linear issues directly from this command.", first_output)
        self.assertIn("Keep the output Markdown-only and operator-editable.", first_output)
        self.assertNotIn('"title":', first_output)
