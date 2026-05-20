from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from wayfinder.cli import cmd_engines
from wayfinder.config import engine_configs, load_config


class EngineRegistryCliTests(unittest.TestCase):
    def write_config(self, root: Path) -> Path:
        config_path = root / "wayfinder.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "wayfinder:",
                    "  storage_path: .ai-state/wayfinder/test.db",
                    "  audit_log: logs/test-audit.log",
                    "engines:",
                    "  example-engine:",
                    "    module: wayfinder.engines.example",
                    "    object: ExamplePainEngineSensor",
                    "    sensors_only: true",
                    "    notes: Local importable sensor stub.",
                    "  missing-engine:",
                    "    module: wayfinder.engines.missing",
                    "    object: MissingEngine",
                    "    sensors_only: true",
                    "    notes: Expected to fail importability checks.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return config_path

    def test_engine_configs_parse_separately_from_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config(self.write_config(Path(tmpdir)))

        engines = engine_configs(config)
        self.assertEqual(sorted(engines), ["example-engine", "missing-engine"])
        self.assertEqual(engines["example-engine"].module, "wayfinder.engines.example")
        self.assertEqual(engines["example-engine"].object_name, "ExamplePainEngineSensor")
        self.assertTrue(engines["example-engine"].sensors_only)

    def test_engines_list_reports_importability(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = self.write_config(Path(tmpdir))
            args = argparse.Namespace(config=str(config_path), json=False, no_color=True)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                rc = cmd_engines(args)

        self.assertEqual(rc, 0)
        output = stdout.getvalue()
        self.assertIn("example-engine module=wayfinder.engines.example object=ExamplePainEngineSensor importable=yes", output)
        self.assertIn("missing-engine module=wayfinder.engines.missing object=MissingEngine importable=no", output)
        self.assertIn("notes=Local importable sensor stub.", output)
        self.assertIn("error=No module named 'wayfinder.engines.missing'", output)

    def test_engines_list_json_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = self.write_config(Path(tmpdir))
            args = argparse.Namespace(config=str(config_path), json=True, no_color=True)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                rc = cmd_engines(args)

        self.assertEqual(rc, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual([item["name"] for item in payload], ["example-engine", "missing-engine"])
        self.assertTrue(payload[0]["importable"])
        self.assertFalse(payload[1]["importable"])


if __name__ == "__main__":
    unittest.main()
