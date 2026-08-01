"""Unit tests for P5 health bundle CLI v1."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Import after path is repo root for script package layout
sys.path.insert(0, str(_REPO_ROOT))

from scripts.run_p5_health_bundle_cli_v1 import (  # noqa: E402
    _DOC_REL,
    _SCHEMA_VERSION,
    build_health_bundle,
)


class TestP5HealthBundleCliV1(unittest.TestCase):
    def test_build_bundle_shape(self) -> None:
        result = build_health_bundle(case_ref="demo_phase", repo_root=_REPO_ROOT)
        self.assertEqual(result["schema_version"], _SCHEMA_VERSION)
        self.assertEqual(result["mode"], "local_bundle")
        self.assertEqual(result["doc"], _DOC_REL)
        self.assertIn("ok", result)
        sections = result["sections"]
        self.assertIn("health", sections)
        self.assertIn("metrics", sections)
        self.assertIn("grafana_stub", sections)
        self.assertIn("ok", sections["health"])
        self.assertIn("scrape_ok", sections["metrics"])
        self.assertIn("ok", sections["grafana_stub"])
        self.assertTrue(any("≠ live Grafana" in c for c in result["non_claims"]))
        self.assertIsNone(result.get("artifact_path"))

    def test_write_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bundle.json"
            result = build_health_bundle(
                case_ref="demo_phase",
                repo_root=_REPO_ROOT,
                write_artifact=True,
                artifact_path_override=str(out),
            )
            self.assertTrue(out.is_file())
            loaded = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema_version"], _SCHEMA_VERSION)
            self.assertIsNotNone(result.get("artifact_path"))

    def test_cli_json_exit(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "run_p5_health_bundle_cli_v1.py"),
                "--format",
                "json",
                "--case-ref",
                "demo_phase",
            ],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload.get("ok"))
        self.assertEqual(payload.get("schema_version"), _SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
