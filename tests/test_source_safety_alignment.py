from __future__ import annotations

import argparse
import io
import unittest
from contextlib import redirect_stdout

from wayfinder.cli import approved_scheduled_sources, cmd_sources
from wayfinder.config import DEFAULT_CONFIG, load_config, source_configs, source_policy, source_review_summary
from wayfinder.web import source_catalog_payload


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

    def test_cli_health_metadata_matches_web_source_catalog_for_reviewed_sources(self) -> None:
        config = load_config(DEFAULT_CONFIG)
        payload = source_catalog_payload(config)
        catalog = {item["key"]: item for item in payload["sources"]}

        for source_name in ("oss-ledger", "hackernews", "github"):
            cfg = source_configs(config)[source_name]
            policy = source_policy(cfg)
            review_state, unattended_state, review_reason = source_review_summary(policy)
            item = catalog[source_name]

            self.assertEqual(item["status"], policy.status)
            self.assertEqual(item["policy_status"], policy.status)
            self.assertEqual(item["notes"], policy.notes)
            self.assertEqual(item["review"], review_state)
            self.assertEqual(item["unattended"], unattended_state)
            self.assertEqual(item["why"], review_reason)
            self.assertEqual(item["risk"]["credentials"], policy.risk.credentials)
            self.assertEqual(item["risk"]["terms"], policy.risk.terms)
            self.assertEqual(item["risk"]["rate_limits"], policy.risk.rate_limits)
            self.assertEqual(item["risk"]["scraping"], policy.risk.scraping)
            self.assertEqual(item["risk"]["pii_user_generated_content"], policy.risk.pii_user_generated_content)
            self.assertEqual(item["risk"]["hosted_dependencies"], policy.risk.hosted_dependencies)

        self.assertTrue(catalog["oss-ledger"]["unattended_cron"]["eligible"])
        self.assertFalse(catalog["hackernews"]["unattended_cron"]["eligible"])
        self.assertFalse(catalog["github"]["unattended_cron"]["eligible"])

    def test_readme_matches_configured_safety_posture(self) -> None:
        readme = DEFAULT_CONFIG.parent.joinpath("README.md").read_text(encoding="utf-8")

        self.assertIn("cron.enabled: false", readme)
        self.assertIn("skips `dry-run-only`, `needs-review`, and `disabled` sources", readme)
        self.assertIn("| `oss-ledger` | Healthy | Safe for recurring cron after separate approval of `cron.enabled` |", readme)
        self.assertIn("| `hackernews` | `dry-run-only` | Not safe for recurring cron yet |", readme)
        self.assertIn("| `github` | `dry-run-only` | Not safe for recurring cron yet |", readme)


if __name__ == "__main__":
    unittest.main()
