from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from wayfinder.audit import latest_scheduled_ingest_summary, write_event


class ScheduledIngestAuditSummaryTests(unittest.TestCase):
    def test_latest_scheduled_ingest_summary_returns_last_completed_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.log"
            write_event(audit_path, "wayfinder_scheduled_ingest_blocked", reason="cron_disabled")
            write_event(audit_path, "wayfinder_scheduled_ingest_started", enabled=False, schedule="daily")
            write_event(audit_path, "wayfinder_scheduled_ingest_source", source="oss-ledger", inserted_signals=2, inserted_products=1, inserted_opportunities=1, normalized=4, raw_records=2)
            write_event(audit_path, "wayfinder_scheduled_ingest_skipped", source="github", status="dry-run-only", reason="source_not_approved_for_unattended_ingest")
            write_event(audit_path, "wayfinder_scheduled_ingest_finished", approved_sources=1, skipped_sources=1, failed_sources=0)

            summary = latest_scheduled_ingest_summary(audit_path)

        assert summary is not None
        self.assertEqual(summary["status"], "finished")
        self.assertEqual(summary["approved_sources"], 1)
        self.assertEqual(summary["skipped_sources"], 1)
        self.assertEqual(summary["source_outcomes"][0]["source"], "oss-ledger")
        self.assertEqual(summary["source_outcomes"][0]["inserted_signals"], 2)
        self.assertEqual(summary["source_outcomes"][1]["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
