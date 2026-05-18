from __future__ import annotations

import argparse
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from wayfinder.cli import cmd_opportunities, cmd_schedule_command, cmd_scheduled_ingest, cmd_search


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
                    "    status: enabled",
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

    def seed_research(self, root: Path) -> None:
        research = root / "research"
        research.mkdir(parents=True, exist_ok=True)
        (research / "open-source-intel-ledger.yaml").write_text(
            "\n".join(
                [
                    "repos:",
                    "  - name: sample-ledger-entry",
                    "    url: https://example.com/sample-ledger-entry",
                    "    category: sample-category",
                    "    useful_outputs:",
                    "      - one useful output",
                    "    safety_risks:",
                    "      - low risk",
                    "    api_keys_required: none",
                    "    install_complexity: low",
                    "    verdict: safe sample verdict",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (research / "github-sample.json").write_text('{"results":[]}', encoding="utf-8")

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

            with patch(
                "wayfinder.cli.ingest_source",
                return_value=(
                    {
                        "raw_records": 1,
                        "normalized": 3,
                        "inserted_searchable_rows": 1,
                        "inserted_signals": 1,
                        "inserted_products": 1,
                        "inserted_opportunities": 1,
                    },
                    "oss-ledger: ok",
                ),
            ) as ingest_mock:
                with redirect_stdout(stdout):
                    rc = cmd_scheduled_ingest(args)

            events = self.read_audit_events(root)

            self.assertEqual(rc, 0)
            self.assertEqual(ingest_mock.call_count, 2)
            self.assertEqual([call.args[0] for call in ingest_mock.call_args_list], ["oss-ledger", "hackernews"])
            self.assertIn("review-source: skipped status=needs-review", stdout.getvalue())
            self.assertIn("blocked-source: skipped status=disabled", stdout.getvalue())
            self.assertEqual(
                [event["action"] for event in events],
                [
                    "wayfinder_scheduled_ingest_started",
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
                    "review-source": "needs-review",
                    "blocked-source": "disabled",
                },
            )
            self.assertFalse(events[0]["enabled"])

    def test_scheduled_ingest_records_real_source_outcomes_in_audit_trail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.seed_research(root)
            config_path = self.write_config(root, cron_enabled=True)
            args = argparse.Namespace(config=str(config_path), no_color=True, allow_disabled=False, dry_run=False)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                rc = cmd_scheduled_ingest(args)

            events = self.read_audit_events(root)
            source_events = [event for event in events if event["action"] == "wayfinder_scheduled_ingest_source"]
            finished_event = next(event for event in events if event["action"] == "wayfinder_scheduled_ingest_finished")

            self.assertEqual(rc, 0)
            self.assertIn("scheduled-ingest: sources=4 approved=2 token_free=true llm_tokens=0", stdout.getvalue())
            self.assertIn(
                "oss-ledger: raw=1 searchable_rows=1 inserted signals=1 products=1 opportunities=1",
                stdout.getvalue(),
            )
            self.assertIn("oss-ledger: searchable_rows_total=1", stdout.getvalue())
            self.assertIn("hackernews: raw=10 searchable_rows=10 inserted signals=10 products=0 opportunities=0", stdout.getvalue())
            self.assertIn("hackernews: searchable_rows_total=10", stdout.getvalue())
            self.assertIn(
                "scheduled-ingest: succeeded=2 skipped=2 failed=0 inserted_searchable_rows=11 "
                "inserted_signals=11 inserted_products=1 inserted_opportunities=1 ",
                stdout.getvalue(),
            )
            self.assertIn("duration_ms=", stdout.getvalue())
            self.assertIn("token_free=true llm_tokens=0", stdout.getvalue())
            self.assertEqual(len(source_events), 2)
            self.assertEqual([event["source"] for event in source_events], ["oss-ledger", "hackernews"])
            self.assertEqual(source_events[0]["raw_records"], 1)
            self.assertEqual(source_events[0]["normalized"], 3)
            self.assertEqual(source_events[0]["inserted_searchable_rows"], 1)
            self.assertEqual(source_events[0]["inserted_signals"], 1)
            self.assertEqual(source_events[0]["inserted_products"], 1)
            self.assertEqual(source_events[0]["inserted_opportunities"], 1)
            self.assertEqual(source_events[1]["raw_records"], 10)
            self.assertEqual(source_events[1]["normalized"], 10)
            self.assertEqual(source_events[1]["inserted_searchable_rows"], 10)
            self.assertEqual(source_events[1]["inserted_signals"], 10)
            self.assertEqual(source_events[1]["inserted_products"], 0)
            self.assertEqual(source_events[1]["inserted_opportunities"], 0)
            self.assertIn("duration_ms", source_events[0])
            self.assertGreaterEqual(float(source_events[0]["duration_ms"]), 0.0)
            self.assertIs(source_events[0]["token_free"], True)
            self.assertEqual(source_events[0]["llm_tokens"], 0)
            self.assertIn("duration_ms", source_events[1])
            self.assertGreaterEqual(float(source_events[1]["duration_ms"]), 0.0)
            self.assertIs(source_events[1]["token_free"], True)
            self.assertEqual(source_events[1]["llm_tokens"], 0)
            self.assertEqual(finished_event["source_count"], 4)
            self.assertEqual(finished_event["approved_source_count"], 2)
            self.assertEqual(finished_event["approved_sources"], 2)
            self.assertEqual(finished_event["skipped_sources"], 2)
            self.assertEqual(finished_event["failed_sources"], 0)
            self.assertEqual(finished_event["inserted_searchable_rows"], 11)
            self.assertEqual(finished_event["inserted_signals"], 11)
            self.assertEqual(finished_event["inserted_products"], 1)
            self.assertEqual(finished_event["inserted_opportunities"], 1)
            self.assertIn("duration_ms", finished_event)
            self.assertGreaterEqual(float(finished_event["duration_ms"]), 0.0)
            self.assertIs(finished_event["token_free"], True)
            self.assertEqual(finished_event["llm_tokens"], 0)

    def test_scheduled_ingest_reports_live_github_searchable_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.seed_research(root)
            config_path = root / "wayfinder.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "wayfinder:",
                        "  storage_path: .ai-state/wayfinder/test.db",
                        "  audit_log: logs/test-audit.log",
                        "sources:",
                        "  github:",
                        "    status: enabled",
                        "    kind: github",
                        "    fixture_path: research/github-sample.json",
                        "    queries:",
                        '      - "startup ideas pain points"',
                        "cron:",
                        "  enabled: true",
                        "  schedule: daily",
                        "  token_free: true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(config=str(config_path), no_color=True, allow_disabled=False, dry_run=False)
            stdout = io.StringIO()
            raw_records = [
                {
                    "name": "pain-radar",
                    "full_name": "acme/pain-radar",
                    "html_url": "https://github.com/acme/pain-radar",
                    "description": "Founder pain search workflow for live ingest evidence",
                    "stargazers_count": 58,
                    "_wayfinder_queries": ["startup ideas pain points"],
                    "_wayfinder_categories": ["market-research"],
                }
            ]

            with patch("wayfinder.adapters.github.GitHubAdapter.collect", return_value=raw_records):
                with redirect_stdout(stdout):
                    rc = cmd_scheduled_ingest(args)

            events = self.read_audit_events(root)
            source_event = next(event for event in events if event["action"] == "wayfinder_scheduled_ingest_source")
            finished_event = next(event for event in events if event["action"] == "wayfinder_scheduled_ingest_finished")

            self.assertEqual(rc, 0)
            self.assertIn(
                "github: raw=1 searchable_rows=1 inserted signals=1 products=1 opportunities=1",
                stdout.getvalue(),
            )
            self.assertIn("github: searchable_rows_total=1", stdout.getvalue())
            self.assertEqual(source_event["source"], "github")
            self.assertEqual(source_event["inserted_searchable_rows"], 1)
            self.assertEqual(source_event["inserted_signals"], 1)
            self.assertEqual(source_event["inserted_products"], 1)
            self.assertEqual(source_event["inserted_opportunities"], 1)
            self.assertEqual(finished_event["source_count"], 1)
            self.assertEqual(finished_event["approved_source_count"], 1)
            self.assertEqual(finished_event["approved_sources"], 1)
            self.assertEqual(finished_event["failed_sources"], 0)
            self.assertEqual(finished_event["inserted_searchable_rows"], 1)

    def test_scheduled_ingest_populates_search_and_opportunity_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "wayfinder.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "wayfinder:",
                        "  storage_path: .ai-state/wayfinder/test.db",
                        "  audit_log: logs/test-audit.log",
                        "sources:",
                        "  github:",
                        "    status: enabled",
                        "    kind: github",
                        "    fixture_path: research/github-sample.json",
                        "    queries:",
                        '      - "startup ideas pain points"',
                        "cron:",
                        "  enabled: true",
                        "  schedule: daily",
                        "  token_free: true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            research = root / "research"
            research.mkdir(parents=True, exist_ok=True)
            (research / "github-sample.json").write_text('{"results":[]}', encoding="utf-8")
            raw_records = [
                {
                    "name": "pain-radar",
                    "full_name": "acme/pain-radar",
                    "html_url": "https://github.com/acme/pain-radar",
                    "description": "Founder pain search workflow for live ingest evidence",
                    "stargazers_count": 58,
                    "_wayfinder_queries": ["startup ideas pain points"],
                    "_wayfinder_categories": ["market-research"],
                }
            ]
            ingest_args = argparse.Namespace(config=str(config_path), no_color=True, allow_disabled=False, dry_run=False)
            search_args = argparse.Namespace(config=str(config_path), no_color=True, query="pain", limit=5, json=False)
            opportunities_args = argparse.Namespace(config=str(config_path), no_color=True, limit=5, json=False, rescore=False)
            search_stdout = io.StringIO()
            opportunities_stdout = io.StringIO()

            with patch("wayfinder.adapters.github.GitHubAdapter.collect", return_value=raw_records):
                rc = cmd_scheduled_ingest(ingest_args)

            self.assertEqual(rc, 0)

            with redirect_stdout(search_stdout):
                self.assertEqual(cmd_search(search_args), 0)
            self.assertIn("acme/pain-radar | github | market-research", search_stdout.getvalue())
            self.assertIn("Founder pain search workflow for live ingest evidence", search_stdout.getvalue())
            self.assertIn("startup ideas pain points", search_stdout.getvalue())

            with redirect_stdout(opportunities_stdout):
                self.assertEqual(cmd_opportunities(opportunities_args), 0)
            self.assertIn("Inspect acme/pain-radar for leverage", opportunities_stdout.getvalue())
            self.assertIn("Founder pain search workflow for live ingest evidence", opportunities_stdout.getvalue())

    def test_schedule_command_prints_cron_ready_operator_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = self.write_config(root, cron_enabled=True)
            args = argparse.Namespace(config=str(config_path), no_color=True)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                rc = cmd_schedule_command(args)

        self.assertEqual(rc, 0)
        expected = (
            f"@daily cd {root} && {sys.executable} -m wayfinder --config {config_path} "
            f"--no-color scheduled-ingest >> {root / 'logs' / 'wayfinder-cron.log'} 2>&1"
        )
        self.assertEqual(stdout.getvalue().strip(), expected)


if __name__ == "__main__":
    unittest.main()
