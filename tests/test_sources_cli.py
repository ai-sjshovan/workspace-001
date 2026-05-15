from __future__ import annotations

import argparse
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from wayfinder.cli import cmd_sources


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


if __name__ == "__main__":
    unittest.main()
