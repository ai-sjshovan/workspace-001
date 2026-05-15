from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from wayfinder.cli import cmd_scheduled_ingest


class ScheduledIngestTests(unittest.TestCase):
    def write_config(self, root: Path, *, cron_enabled: bool) -> Path:
        config_path = root / "wayfinder.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "wayfinder:",
                    "  storage_path: .ai-state/wayfinder/test.db",
                    "  audit_log: logs/test-audit.log",
                    "sources:",
                    "  oss-ledger:",
                    "    status: enabled",
                    "    kind: static_ledger",
                    "    path: research/open-source-intel-ledger.yaml",
                    "  hackernews:",
                    "    status: dry-run-only",
                    "    kind: hackernews",
                    "    fixture_path: research/hackernews-sample.json",
                    "    queries:",
                    "      - query: founder pain",
                    "  blocked-source:",
                    "    status: disabled",
                    "    kind: static_ledger",
                    "    path: research/open-source-intel-ledger.yaml",
                    "cron:",
                    f"  enabled: {'true' if cron_enabled else 'false'}",
                    "  schedule: daily",
                    "  token_free: true",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return config_path

    def test_scheduled_ingest_is_blocked_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = self.write_config(Path(tmpdir), cron_enabled=False)
            args = argparse.Namespace(config=str(config_path), no_color=True, allow_disabled=False, dry_run=False)
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                rc = cmd_scheduled_ingest(args)

        self.assertEqual(rc, 1)
        self.assertIn("Scheduled ingest is disabled in config", stderr.getvalue())

    def test_scheduled_ingest_only_runs_enabled_sources_when_manually_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = self.write_config(Path(tmpdir), cron_enabled=False)
            args = argparse.Namespace(config=str(config_path), no_color=True, allow_disabled=True, dry_run=False)
            stdout = io.StringIO()

            with patch("wayfinder.cli.ingest_source", return_value=(3, "oss-ledger: ok")) as ingest_mock:
                with redirect_stdout(stdout):
                    rc = cmd_scheduled_ingest(args)

        self.assertEqual(rc, 0)
        self.assertEqual(ingest_mock.call_count, 1)
        self.assertEqual(ingest_mock.call_args.args[0], "oss-ledger")
        self.assertIn("hackernews: skipped status=dry-run-only", stdout.getvalue())
        self.assertIn("blocked-source: skipped status=disabled", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
