from __future__ import annotations

import argparse
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from wayfinder.cli import cmd_sources, cmd_stats
from wayfinder.db import connect, insert_opportunities, insert_signals
from wayfinder.models import Opportunity, Signal


REPO_ROOT = Path(__file__).resolve().parents[1]


class SourceStatusCliTests(unittest.TestCase):
    def write_config(self, root: Path) -> Path:
        config_path = root / "wayfinder.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "wayfinder:",
                    "  storage_path: .ai-state/wayfinder/test.db",
                    "  audit_log: logs/test-audit.log",
                    "sources:",
                    "  approved-source:",
                    "    status: enabled",
                    "    kind: static_ledger",
                    "    path: research/open-source-intel-ledger.yaml",
                    "    notes: Reviewed local ledger with no hosted dependency.",
                    "    risk:",
                    "      credentials: none",
                    "      terms: reviewed-public-data",
                    "      rate_limits: none-local-file",
                    "      scraping: none",
                    "      pii_user_generated_content: none",
                    "      hosted_dependencies: none",
                    "  review-source:",
                    "    status: dry-run-only",
                    "    kind: github",
                    "    notes: Manual dry runs only until hosted dependency review is complete.",
                    "    fixture_path: research/github-sample.json",
                    "    risk:",
                    "      credentials: none",
                    "      terms: review-required",
                    "      rate_limits: api-rate-review",
                    "      scraping: official-api",
                    "      pii_user_generated_content: low-public-repo-metadata",
                    "      hosted_dependencies: github-api",
                    "  disabled-source:",
                    "    status: disabled",
                    "    kind: static_ledger",
                    "    path: research/open-source-intel-ledger.yaml",
                    "    notes: Blocked until a fresh safety review is recorded.",
                    "    risk:",
                    "      credentials: none",
                    "      terms: review-required",
                    "      rate_limits: unknown",
                    "      scraping: none",
                    "      pii_user_generated_content: none",
                    "      hosted_dependencies: none",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return config_path

    def test_sources_list_shows_review_and_unattended_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = self.write_config(Path(tmpdir))
            args = argparse.Namespace(config=str(config_path), json=False, health=False, no_color=True)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                rc = cmd_sources(args)

        self.assertEqual(rc, 0)
        output = stdout.getvalue()
        self.assertIn("approved-source status=enabled", output)
        self.assertIn("review=approved unattended=eligible", output)
        self.assertIn("why=Reviewed local ledger with no hosted dependency.", output)
        self.assertIn("review-source status=dry-run-only", output)
        self.assertIn("review=pending unattended=blocked", output)
        self.assertIn("unresolved=terms,rate_limits", output)

    def test_sources_list_health_marks_disabled_sources_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = self.write_config(Path(tmpdir))
            args = argparse.Namespace(config=str(config_path), json=False, health=True, no_color=True)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                rc = cmd_sources(args)

        self.assertEqual(rc, 0)
        output = stdout.getvalue()
        self.assertIn("disabled-source status=disabled", output)
        self.assertIn("review=blocked unattended=blocked", output)
        self.assertIn("health=disabled Health checks are skipped while this adapter is disabled.", output)
        self.assertIn("latest_run=none status=unknown last_ingest_at=never", output)

    def test_sources_list_health_shows_last_ingest_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = self.write_config(root)
            conn = connect(root / ".ai-state" / "wayfinder" / "test.db")
            try:
                conn.execute(
                    """
                    INSERT INTO ingest_runs (
                      source, started_at, finished_at, collected, inserted_searchable_rows, inserted_signals,
                      inserted_products, inserted_opportunities, dry_run, status, message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "approved-source",
                        "2026-05-18T00:00:00Z",
                        "2026-05-18T00:01:00Z",
                        4,
                        2,
                        2,
                        1,
                        1,
                        0,
                        "ok",
                        "fixture",
                    ),
                )
                conn.commit()
            finally:
                conn.close()
            args = argparse.Namespace(config=str(config_path), json=False, health=True, no_color=True)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                rc = cmd_sources(args)

        self.assertEqual(rc, 0)
        output = stdout.getvalue()
        self.assertIn("approved-source status=enabled", output)
        self.assertIn("health=fail", output)
        self.assertIn("latest_run=live status=ok last_ingest_at=2026-05-18T00:01:00Z", output)
        self.assertIn("collected=4 searchable_rows=2 signals=2 products=1 opportunities=1", output)

    def test_module_entrypoint_runs_help_from_repo_root(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "wayfinder", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage: wayfinder", completed.stdout)

    def test_stats_prints_source_activity_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = self.write_config(root)
            conn = connect(root / ".ai-state" / "wayfinder" / "test.db")
            try:
                insert_signals(
                    conn,
                    [
                        Signal(
                            source="approved-source",
                            source_id="sig-1",
                            source_url="https://example.com/signal",
                            title="Example SaaS pain",
                            body="Need a better workflow",
                            category="market-research",
                        )
                    ],
                )
                insert_opportunities(
                    conn,
                    [
                        Opportunity(
                            title="Workflow gap for research teams",
                            source="approved-source",
                            category="market-research",
                            target_user="research operators",
                            problem="Need a better workflow",
                            evidence_count=2,
                            iteration_angle="Turn repeated pain into a productized workflow",
                        )
                    ],
                    {
                        "evidence_count_weight": 0.35,
                        "freshness_weight": 0.15,
                        "monetization_signal_weight": 0.20,
                        "source_quality_weight": 0.15,
                        "build_fit_weight": 0.15,
                    },
                )
                conn.execute(
                    """
                    INSERT INTO ingest_runs (
                      source, started_at, finished_at, collected, inserted_searchable_rows, inserted_signals,
                      inserted_products, inserted_opportunities, dry_run, status, message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "approved-source",
                        "2026-05-18T00:00:00Z",
                        "2026-05-18T00:01:00Z",
                        2,
                        1,
                        1,
                        0,
                        1,
                        0,
                        "ok",
                        "fixture",
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            args = argparse.Namespace(config=str(config_path), json=False, no_color=True)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                rc = cmd_stats(args)

        self.assertEqual(rc, 0)
        output = stdout.getvalue()
        self.assertIn("signals: 1", output)
        self.assertIn("opportunities: 1", output)
        self.assertIn("ingest_runs: 1", output)
        self.assertIn("source_activity:", output)
        self.assertIn("approved-source: signals=1 opportunities=1", output)
        self.assertIn("last_ingest_at=2026-05-18T00:01:00Z", output)


if __name__ == "__main__":
    unittest.main()
