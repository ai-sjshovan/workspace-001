from __future__ import annotations

import argparse
import io
import json
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
                    "  review-source:",
                    "    status: needs-review",
                    "    kind: static_ledger",
                    "    path: research/open-source-intel-ledger.yaml",
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

    def read_audit_events(self, root: Path) -> list[dict[str, object]]:
        audit_path = root / "logs" / "test-audit.log"
        return [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]

    def test_scheduled_ingest_is_blocked_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = self.write_config(root, cron_enabled=False)
            args = argparse.Namespace(config=str(config_path), no_color=True, allow_disabled=False, dry_run=False)
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                rc = cmd_scheduled_ingest(args)

            events = self.read_audit_events(root)

            self.assertEqual(rc, 1)
            self.assertIn("Scheduled ingest is disabled in config", stderr.getvalue())
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["action"], "wayfinder_scheduled_ingest_blocked")
            self.assertEqual(events[0]["reason"], "cron_disabled")
            self.assertIs(events[0]["token_free"], True)
            self.assertEqual(events[0]["llm_tokens"], 0)

    def test_scheduled_ingest_only_runs_enabled_sources_when_manually_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = self.write_config(root, cron_enabled=False)
            args = argparse.Namespace(config=str(config_path), no_color=True, allow_disabled=True, dry_run=False)
            stdout = io.StringIO()

            with patch("wayfinder.cli.ingest_source", return_value=(3, "oss-ledger: ok")) as ingest_mock:
                with redirect_stdout(stdout):
                    rc = cmd_scheduled_ingest(args)

            events = self.read_audit_events(root)

            self.assertEqual(rc, 0)
            self.assertEqual(ingest_mock.call_count, 1)
            self.assertEqual(ingest_mock.call_args.args[0], "oss-ledger")
            self.assertIn("hackernews: skipped status=dry-run-only", stdout.getvalue())
            self.assertIn("review-source: skipped status=needs-review", stdout.getvalue())
            self.assertIn("blocked-source: skipped status=disabled", stdout.getvalue())
            self.assertEqual(
                [event["action"] for event in events],
                [
                    "wayfinder_scheduled_ingest_started",
                    "wayfinder_scheduled_ingest_skipped",
                    "wayfinder_scheduled_ingest_skipped",
                    "wayfinder_scheduled_ingest_skipped",
                    "wayfinder_scheduled_ingest_finished",
                ],
            )
            for event in events:
                self.assertIs(event["token_free"], True)
                self.assertEqual(event["llm_tokens"], 0)
            skipped_statuses = {
                str(event["source"]): str(event["status"])
                for event in events
                if event["action"] == "wayfinder_scheduled_ingest_skipped"
            }
            self.assertEqual(
                skipped_statuses,
                {
                    "hackernews": "dry-run-only",
                    "review-source": "needs-review",
                    "blocked-source": "disabled",
                },
            )
            self.assertFalse(events[0]["enabled"])


if __name__ == "__main__":
    unittest.main()
