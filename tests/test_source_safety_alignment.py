from __future__ import annotations

import argparse
import io
import unittest
from contextlib import redirect_stdout

from wayfinder.cli import approved_scheduled_sources, cmd_sources
from wayfinder.config import DEFAULT_CONFIG, load_config, source_configs, source_policy


class SourceSafetyAlignmentTests(unittest.TestCase):
    def test_repo_config_preserves_review_states_and_scheduled_sources(self) -> None:
        config = load_config(DEFAULT_CONFIG)
        sources = source_configs(config)

        self.assertEqual(source_policy(sources["oss-ledger"]).status, "enabled")
        self.assertEqual(source_policy(sources["hackernews"]).status, "dry-run-only")
        self.assertEqual(source_policy(sources["github"]).status, "dry-run-only")
        self.assertEqual(source_policy(sources["oss-ledger"]).risk.credentials, "none")
        self.assertEqual(source_policy(sources["hackernews"]).risk.credentials, "none")
        self.assertEqual(source_policy(sources["github"]).risk.credentials, "none")
        self.assertEqual(sorted(approved_scheduled_sources(config)), ["oss-ledger"])

    def test_sources_list_health_surfaces_review_and_risk_metadata(self) -> None:
        args = argparse.Namespace(config=str(DEFAULT_CONFIG), json=False, health=True, no_color=True)
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            rc = cmd_sources(args)

        self.assertEqual(rc, 0)
        output = stdout.getvalue()
        self.assertIn("oss-ledger status=enabled", output)
        self.assertIn("review=approved unattended=eligible", output)
        self.assertIn("hackernews status=dry-run-only", output)
        self.assertIn("github status=dry-run-only", output)
        self.assertIn("review=pending unattended=blocked", output)
        self.assertIn("credentials=none", output)
        self.assertIn("hosted_dependencies=algolia-hn-api", output)
        self.assertIn("hosted_dependencies=github-api", output)
        self.assertGreaterEqual(output.count("health=ok"), 3)

    def test_readme_matches_configured_safety_posture(self) -> None:
        readme = DEFAULT_CONFIG.parent.joinpath("README.md").read_text(encoding="utf-8")

        self.assertIn("cron.enabled: false", readme)
        self.assertIn("skips `dry-run-only`, `needs-review`, and `disabled` sources", readme)
        self.assertIn("| `oss-ledger` | Healthy | Safe for recurring cron after separate approval of `cron.enabled` |", readme)
        self.assertIn("| `hackernews` | `dry-run-only` | Not safe for recurring cron yet |", readme)
        self.assertIn("| `github` | `dry-run-only` | Not safe for recurring cron yet |", readme)


if __name__ == "__main__":
    unittest.main()
