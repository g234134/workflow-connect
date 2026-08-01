"""Unit tests for Intake Gate layer v1 (P75-G2)."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from routing.intake_gate_layer_v1 import evaluate_intake_gate
from routing.intake_gate_mapping_v1 import (
    compute_checkpoint_a_preview,
    map_internal_to_canonical,
)
from routing.intake_gate_outbox_v1 import EVENTS_FILENAME

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "intake_gate" / "intake_gate_result_v1.json"
)
_DEMO_PHASE = "cases/demo_phase"
_UNKNOWN_CASE = "cases/does_not_exist_zzzz"


def _load_schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _validate_required_keys(result: dict) -> None:
    schema = _load_schema()
    for key in schema.get("required") or []:
        assert key in result, f"missing required key: {key}"
    assert result["schema_version"] == "intake_gate_result_v1"
    assert result["decider"] == "intake_gate_layer_v1"
    assert result["decision"] in ("accept", "review_needed", "reject")
    assert result["decision_normalized"] == result["decision"]
    assert isinstance(result["reason_codes"], list)
    assert isinstance(result["gate_checks"], list)


class TestIntakeGateLayerV1(unittest.TestCase):
    def test_evaluate_intake_gate_demo_phase_review_needed_canonical(self) -> None:
        result = evaluate_intake_gate(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "review_needed")
        self.assertEqual(result["decision_internal"], "needs_review")
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertEqual(result["rules_engine"], "intake_decision_rules_v2")
        self.assertIn("manual_review_required", result["reason_codes"])
        cp_a = result.get("checkpoint_a") or {}
        self.assertTrue(cp_a.get("would_trigger"))
        self.assertEqual(cp_a.get("trigger_reason"), "decision_review_needed")

    def test_evaluate_intake_gate_maps_auto_accept_to_accept(self) -> None:
        result = evaluate_intake_gate(
            "tabular.intake.new_case",
            _DEMO_PHASE,
            mode="preview",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "accept")
        self.assertEqual(result["decision_internal"], "auto_accept")
        self.assertEqual(result["risk_level"], "low")
        cp_a = result.get("checkpoint_a") or {}
        self.assertFalse(cp_a.get("would_trigger"))

    def test_evaluate_intake_gate_reject_unsupported_task_type(self) -> None:
        result = evaluate_intake_gate(
            "tabular.unsupported.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "reject")
        self.assertIn("unsupported_task_type", result["reason_codes"])
        cp_a = result.get("checkpoint_a") or {}
        self.assertFalse(cp_a.get("would_trigger"))
        self.assertIsNone(result.get("suggested_route"))

    def test_evaluate_intake_gate_preview_mode_does_not_write_outbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = evaluate_intake_gate(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="preview",
                outbox_root_override=str(outbox),
            )
        self.assertIsNone(result.get("outbox_record_path"))
        self.assertFalse(list(outbox.rglob("intake_gate_decision_*.json")))
        self.assertFalse((outbox / EVENTS_FILENAME).is_file())

    def test_evaluate_intake_gate_run_mode_writes_outbox_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = evaluate_intake_gate(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                outbox_root_override=str(outbox),
            )
            self.assertTrue(result["ok"])
            record_path = result.get("outbox_record_path")
            self.assertIsNotNone(record_path)
            records = list(outbox.rglob("intake_gate_decision_*.json"))
            self.assertEqual(len(records), 1)
            payload = json.loads(records[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["record_type"], "intake_gate_decision")
            self.assertEqual(payload["intake_decision_id"], result["intake_decision_id"])
            self.assertEqual(payload["decision"], "review_needed")

    def test_intake_gate_events_jsonl_appended_in_run_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = evaluate_intake_gate(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                mode="run",
                outbox_root_override=str(outbox),
            )
            events_path = outbox / EVENTS_FILENAME
            self.assertTrue(events_path.is_file())
            lines = events_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 1)
            event = json.loads(lines[-1])
            self.assertEqual(event["intake_decision_id"], result["intake_decision_id"])
            self.assertEqual(event["case_ref"], "demo_phase")
            self.assertEqual(event["decision"], "review_needed")
            self.assertEqual(event["record_path"], result["outbox_record_path"])

    def test_intake_gate_result_matches_intake_gate_result_v1_schema(self) -> None:
        result = evaluate_intake_gate(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        _validate_required_keys(result)
        self.assertTrue(result["intake_decision_id"].startswith("igd_"))

    def test_intake_decision_id_format_is_stable(self) -> None:
        result = evaluate_intake_gate(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        iid = result["intake_decision_id"]
        pattern = r"^igd_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_demo_phase_tabular_cleaning_mvp_[0-9a-f]{8}$"
        self.assertRegex(iid, pattern)

        result2 = evaluate_intake_gate(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        self.assertNotEqual(result["intake_decision_id"], result2["intake_decision_id"])

    def test_checkpoint_a_would_trigger_flags_respect_g1_rules(self) -> None:
        cases = [
            ("reject", "high", False, "decision_reject"),
            ("review_needed", "medium", True, "decision_review_needed"),
            ("accept", "low", False, "low_risk_accept"),
            ("accept", "medium", True, "risk_level_override"),
            ("accept", "high", True, "risk_level_override"),
        ]
        for decision, risk, expected_trigger, expected_reason in cases:
            with self.subTest(decision=decision, risk=risk):
                preview = compute_checkpoint_a_preview(
                    decision=decision,  # type: ignore[arg-type]
                    risk_level=risk,
                )
                self.assertEqual(preview["would_trigger"], expected_trigger)
                self.assertEqual(preview["trigger_reason"], expected_reason)

        self.assertEqual(map_internal_to_canonical("needs_review"), "review_needed")
        self.assertEqual(map_internal_to_canonical("auto_accept"), "accept")


class TestIntakeGateOrchestratorIntegration(unittest.TestCase):
    """Gate layer wiring in run_agent_standard_case_experiment (S3)."""

    @classmethod
    def setUpClass(cls) -> None:
        import importlib.util
        import sys

        cli_path = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
        if not cli_path.is_file():
            raise unittest.SkipTest("orchestrator CLI missing")
        spec = importlib.util.spec_from_file_location(
            "run_agent_standard_case_experiment", cli_path
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules["run_agent_standard_case_experiment"] = mod
        spec.loader.exec_module(mod)
        cls.cli = mod

    def test_orchestrator_s3_includes_intake_gate_result(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        self.assertIn("intake_gate", result)
        gate = result["intake_gate"]
        self.assertEqual(gate["schema_version"], "intake_gate_result_v1")
        self.assertEqual(gate["decision"], "review_needed")
        self.assertEqual(result["decision"]["decision"], "needs_review")

    def test_orchestrator_reject_skips_checkpoint_a(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "gov.observability.eval",
            _DEMO_PHASE,
            mode="preview",
        )
        self.assertEqual(result["intake_gate"]["decision"], "reject")
        cp_a = result["checkpoint_a_status"]
        self.assertEqual(cp_a["status"], "not_applicable")
        self.assertFalse(cp_a["would_trigger"])

    def test_orchestrator_review_needed_triggers_checkpoint_a(self) -> None:
        result = self.cli.run_agent_standard_case_experiment(
            "tabular.cleaning.mvp",
            _DEMO_PHASE,
            mode="preview",
        )
        self.assertEqual(result["intake_gate"]["decision"], "review_needed")
        cp_a = result["checkpoint_a_status"]
        self.assertTrue(cp_a["would_trigger"])
        self.assertEqual(cp_a["status"], "would_pause")


if __name__ == "__main__":
    unittest.main()
