"""Unit tests for multi-phase smoke runner v1 (MP-SMOKE)."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SMOKE_CLI = _REPO_ROOT / "scripts" / "run_multi_phase_smoke_v1.py"

_EXPECTED_STEP_IDS = (
    "gate_preview",
    "gate_run_notify",
    "std_case_experiment",
    "workflow_events_inspect",
    "feedback_ingest_dry_run",
    "p89_verification_bundle",
    "operator_backlog",
)


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location(
        "run_multi_phase_smoke_v1", _SMOKE_CLI
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_multi_phase_smoke_v1"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestMultiPhaseSmokeV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _SMOKE_CLI.is_file():
            raise unittest.SkipTest(f"missing CLI: {_SMOKE_CLI}")
        cls.smoke = _load_smoke_module()

    def test_smoke_script_produces_summary_json_and_does_not_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            outbox_root = tmp_path / "outbox"
            result = self.smoke.run_multi_phase_smoke_v1(
                "demo_phase",
                repo_root=tmp_path,
                outbox_root_override=str(outbox_root),
                enable_dispatch=True,
                write_summary=True,
            )
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("schema_version"), "multi_phase_smoke_v1")
            self.assertIn("steps", result)

            summary_path = (
                tmp_path
                / "outbox"
                / "verification"
                / "demo_phase"
                / "multi_phase_smoke_run.json"
            )
            self.assertTrue(summary_path.is_file(), "expected written summary artifact")
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary.get("schema_version"), "multi_phase_smoke_v1")
            self.assertEqual(summary.get("case_ref"), "demo_phase")
            self.assertIn("steps", summary)

    def test_smoke_summary_contains_all_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            outbox_root = tmp_path / "outbox"
            result = self.smoke.run_multi_phase_smoke_v1(
                "demo_phase",
                repo_root=tmp_path,
                outbox_root_override=str(outbox_root),
                enable_dispatch=True,
            )
            step_ids = [s.get("step_id") for s in result.get("steps") or []]
            self.assertEqual(step_ids, list(_EXPECTED_STEP_IDS))
            for step in result.get("steps") or []:
                self.assertIn("ok", step)
                self.assertIn("message", step)
                self.assertIn("artifact_paths", step)
                self.assertIsInstance(step.get("artifact_paths"), dict)

            self.assertTrue(result.get("ok"), msg=result.get("message"))


if __name__ == "__main__":
    unittest.main()
