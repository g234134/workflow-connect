"""Tests for CP-B sync between run-log and automation_state."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_checkpoint_sync_lib import run_log_path  # noqa: E402
from tabular_checkpoint_sync_lib import (  # noqa: E402
    sync_checkpoint_b_run_log_step,
    sync_checkpoint_b_state_and_readiness,
)
from tabular_automation_state_lib import load_state  # noqa: E402


def _seed_case(root: Path) -> Path:
    case_dir = root / "cases" / "demo_phase"
    case_dir.mkdir(parents=True)
    (case_dir / "intake.json").write_text(
        json.dumps({"case_id": "demo_phase", "client_ref": "internal-demo"}),
        encoding="utf-8",
    )
    reports = case_dir / "reports"
    reports.mkdir(parents=True)
    (reports / "automation_run_log.json").write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "step_name": "checkpoint_b",
                        "step_status": "awaiting_hitl",
                        "detail": {},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (case_dir / "automation_state.json").write_text(
        json.dumps(
            {
                "schema_version": "tabular-automation-state-v1",
                "case_id": "demo_phase",
                "automation_status": "paused",
                "checkpoint_b_status": "pending",
                "current_step": "checkpoint_b",
            }
        ),
        encoding="utf-8",
    )
    return case_dir


class TestCheckpointBSync(unittest.TestCase):
    def test_sync_aligns_run_log_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = _seed_case(root)
            result = sync_checkpoint_b_state_and_readiness(
                case_dir,
                checkpoint_b_status="approved",
                step_status="completed",
                current_step="approved_for_delivery",
                skip_readiness_eval=True,
            )
            self.assertTrue(result.get("ok"))

            state = load_state(case_dir)
            self.assertEqual(state.get("checkpoint_b_status"), "approved")

            run_log = json.loads(run_log_path(case_dir).read_text(encoding="utf-8"))
            step = run_log["steps"][-1]
            self.assertEqual(step["step_status"], "completed")
            self.assertEqual(step["detail"]["checkpoint_b_status"], "approved")

    def test_run_log_only_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = _seed_case(root)
            sync_checkpoint_b_run_log_step(
                case_dir,
                step_status="completed",
                checkpoint_b_status="approved",
            )
            run_log = json.loads(run_log_path(case_dir).read_text(encoding="utf-8"))
            step = run_log["steps"][-1]
            self.assertEqual(step["step_status"], "completed")
            self.assertEqual(step["detail"]["checkpoint_b_status"], "approved")


if __name__ == "__main__":
    unittest.main()
