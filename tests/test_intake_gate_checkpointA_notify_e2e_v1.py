"""E2E regression: Intake Gate three-state + Checkpoint A + intake.gate_decision (P75-REGRESSION).

Guards the wired behavior across gate layer, CP-A integration, and notification gateway
without modifying gate contract, CP-A schema, or notify emit schema.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.notification_gateway_v1 import (
    EVENT_TYPE_INTAKE_GATE_DECISION,
    emit_intake_gate_decision_notification,
)
from delivery.workflow_event_consumer_v1 import load_workflow_events
from hitl.checkpoint_a_integration_v1 import maybe_create_checkpoint_a
from routing.intake_gate_layer_v1 import evaluate_intake_gate
from routing.intake_gate_mapping_v1 import decision_result_from_gate

_CASES_ROOT = _REPO_ROOT / "cases"


def _write_phi_deny_case(root: Path) -> tuple[str, str]:
    """Synthetic case: v2 accept overridden by policy deny (PM-D3 PHI)."""
    rel = "p75_regression_phi_deny"
    case_dir = root / rel
    case_dir.mkdir(parents=True, exist_ok=True)
    intake = {
        "case_id": rel,
        "client_ref": "phi-override",
        "sensitivity": "phi",
        "provenance": {"source_type": "owned"},
        "structure": "text_only",
    }
    (case_dir / "intake.json").write_text(
        json.dumps(intake, ensure_ascii=False),
        encoding="utf-8",
    )
    return rel, str(case_dir)


def _resolve_checkpoint_path(checkpoint_path: str, *, outbox_root: Path) -> Path:
    path = Path(checkpoint_path)
    if path.is_file():
        return path
    candidate = outbox_root / checkpoint_path
    if candidate.is_file():
        return candidate
    return outbox_root / path.name


def _run_gate_checkpoint_notify_scenario(
    *,
    task_type: str,
    case_dir: str,
    repo_root: Path,
    outbox_root: Path,
    case_ref: str,
) -> dict[str, Any]:
    """Mirror S3 gate run + G4 notify + S4 CP-A wiring used by orchestrator."""
    gate = evaluate_intake_gate(
        task_type,
        case_dir,
        mode="run",
        repo_root=repo_root,
        outbox_root_override=str(outbox_root),
    )
    notify = emit_intake_gate_decision_notification(
        gate,
        enabled=True,
        repo_root=repo_root,
        outbox_root_override=str(outbox_root),
    )

    cp_a: dict[str, Any]
    if gate.get("decision") == "reject":
        # Orchestrator S3 early-exit: canonical reject never reaches CP-A writer.
        cp_a = {
            "ok": True,
            "status": "not_applicable",
            "checkpoint_id": "A-intake-confirmation",
            "case_ref": case_ref,
            "message": "decision=reject",
            "would_trigger": False,
        }
    else:
        adapted = decision_result_from_gate(gate)
        cp_a = maybe_create_checkpoint_a(
            task_type,
            case_dir,
            adapted,
            repo_root=repo_root,
            outbox_root_override=str(outbox_root),
        )

    workflow = load_workflow_events(
        str(gate.get("case_ref") or case_ref),
        event_type=EVENT_TYPE_INTAKE_GATE_DECISION,
        repo_root=repo_root,
        outbox_root_override=str(outbox_root),
    )
    checkpoint_files = list(outbox_root.rglob("checkpoint_*.json"))
    gate_records = list(outbox_root.rglob("intake_gate_decision_*.json"))
    return {
        "gate": gate,
        "notify": notify,
        "cp_a": cp_a,
        "workflow": workflow,
        "checkpoint_files": checkpoint_files,
        "gate_records": gate_records,
    }


class TestIntakeGateCheckpointANotifyE2EV1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.outbox = self.repo_root / "outbox"
        self.outbox.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _assert_intake_gate_decision_event(
        self,
        *,
        workflow: dict,
        gate: dict,
        case_ref: str,
    ) -> dict:
        self.assertTrue(workflow.get("ok"))
        timeline = workflow.get("timeline") or []
        self.assertGreaterEqual(len(timeline), 1, "expected intake.gate_decision in workflow ledger")
        row = timeline[-1]
        self.assertEqual(row.get("event_type"), EVENT_TYPE_INTAKE_GATE_DECISION)
        self.assertEqual(row.get("case_ref"), case_ref)

        jsonl_path = self.outbox / "notification_events.jsonl"
        self.assertTrue(jsonl_path.is_file())
        events = [
            json.loads(line)
            for line in jsonl_path.read_text(encoding="utf-8").strip().split("\n")
            if line.strip()
        ]
        gate_events = [e for e in events if e.get("event_type") == EVENT_TYPE_INTAKE_GATE_DECISION]
        self.assertGreaterEqual(len(gate_events), 1)
        event = gate_events[-1]
        self.assertEqual(event["case_ref"], case_ref)
        self.assertEqual(event["status_summary"]["decision"], gate["decision"])
        self.assertEqual(event["artifacts"]["decision"], gate["decision"])
        self.assertEqual(event["artifacts"]["intake_decision_id"], gate["intake_decision_id"])
        self.assertEqual(event["artifacts"]["reason_codes"], gate["reason_codes"])
        self.assertIsNotNone(event["artifacts"].get("outbox_record_path"))
        return event

    def test_accept_low_risk_skips_checkpoint_a_and_emits_gate_notify(self) -> None:
        task_type = "tabular.intake.new_case"
        case_dir = "cases/demo_phase"
        case_ref = "demo_phase"

        result = _run_gate_checkpoint_notify_scenario(
            task_type=task_type,
            case_dir=case_dir,
            repo_root=_REPO_ROOT,
            outbox_root=self.outbox,
            case_ref=case_ref,
        )
        gate = result["gate"]
        cp_a = result["cp_a"]

        self.assertTrue(gate["ok"])
        self.assertEqual(gate["decision"], "accept")
        self.assertEqual(gate["risk_level"], "low")
        self.assertFalse(gate["checkpoint_a"]["would_trigger"])
        self.assertIsNotNone(gate.get("outbox_record_path"))

        self.assertTrue(cp_a["ok"])
        self.assertEqual(cp_a["status"], "skipped")
        self.assertNotIn("checkpoint_path", cp_a)
        self.assertEqual(result["checkpoint_files"], [])

        notify = result["notify"]
        self.assertIsNotNone(notify)
        assert notify is not None
        self.assertTrue(notify.get("ok"))

        self._assert_intake_gate_decision_event(
            workflow=result["workflow"],
            gate=gate,
            case_ref=case_ref,
        )

    def test_review_needed_triggers_checkpoint_a_and_emits_gate_notify(self) -> None:
        task_type = "tabular.cleaning.mvp"
        case_dir = "cases/demo_phase"
        case_ref = "demo_phase"

        result = _run_gate_checkpoint_notify_scenario(
            task_type=task_type,
            case_dir=case_dir,
            repo_root=_REPO_ROOT,
            outbox_root=self.outbox,
            case_ref=case_ref,
        )
        gate = result["gate"]
        cp_a = result["cp_a"]

        self.assertTrue(gate["ok"])
        self.assertEqual(gate["decision"], "review_needed")
        self.assertTrue(gate["checkpoint_a"]["would_trigger"])
        self.assertIn("manual_review_required", gate["reason_codes"])

        self.assertTrue(cp_a["ok"])
        self.assertEqual(cp_a["status"], "awaiting_human")
        self.assertIn("checkpoint_path", cp_a)
        self.assertEqual(len(result["checkpoint_files"]), 1)

        checkpoint_path = _resolve_checkpoint_path(
            cp_a["checkpoint_path"],
            outbox_root=self.outbox,
        )
        self.assertTrue(checkpoint_path.is_file())
        saved = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "awaiting_human")
        intake_gate = saved["agent_output"].get("intake_gate") or {}
        self.assertEqual(intake_gate.get("decision"), "review_needed")
        self.assertEqual(intake_gate.get("intake_decision_id"), gate["intake_decision_id"])

        self._assert_intake_gate_decision_event(
            workflow=result["workflow"],
            gate=gate,
            case_ref=case_ref,
        )

    def test_policy_deny_reject_skips_checkpoint_a_and_emits_gate_notify(self) -> None:
        with tempfile.TemporaryDirectory(dir=_CASES_ROOT) as tmp:
            case_ref, case_dir = _write_phi_deny_case(Path(tmp))
            task_type = "tabular.intake.new_case"

            result = _run_gate_checkpoint_notify_scenario(
                task_type=task_type,
                case_dir=case_dir,
                repo_root=_REPO_ROOT,
                outbox_root=self.outbox,
                case_ref=case_ref,  # rel slug; gate may use absolute case_ref for temp dirs
            )
            gate = result["gate"]
            cp_a = result["cp_a"]
            workflow_case_ref = str(gate["case_ref"])

            self.assertTrue(gate["ok"])
            self.assertEqual(gate["decision"], "reject")
            self.assertIn("policy_deny_phi", gate["reason_codes"])
            self.assertFalse(gate["checkpoint_a"]["would_trigger"])

            self.assertTrue(cp_a["ok"])
            self.assertEqual(cp_a["status"], "not_applicable")
            self.assertNotIn("checkpoint_path", cp_a)
            self.assertEqual(result["checkpoint_files"], [])

            event = self._assert_intake_gate_decision_event(
                workflow=result["workflow"],
                gate=gate,
                case_ref=workflow_case_ref,
            )
            self.assertIn("policy_deny_phi", event["status_summary"]["reason_codes"])
            self.assertIn("policy_deny_phi", event["artifacts"]["reason_codes"])


if __name__ == "__main__":
    unittest.main()
