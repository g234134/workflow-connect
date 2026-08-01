"""Integration tests for intake gate policy + layer (P75-G3 · W1-P75 deny trace MVP)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from routing.intake_gate_layer_v1 import evaluate_intake_gate, merge_policy_with_v2
from routing.intake_gate_policy_bridge_v1 import bridge_policy_eval
from routing.intake_gate_policy_evaluator_v1 import evaluate_policy
from routing.intake_gate_policy_loader_v1 import load_intake_gate_policy
from routing.intake_decision_rules_v2 import evaluate_intake_decision_v2

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_DIR = _REPO_ROOT / "tests" / "golden" / "intake_gate_policy"
_CLI = _REPO_ROOT / "scripts" / "run_intake_gate_cli.py"

_DENY_GOLDEN_FIXTURES = (
    "deny_phi.json",
    "deny_web_scraping.json",
    "deny_audio_video.json",
    "deny_scale_exceeds.json",
)

_DENY_INTAKE_BY_GOLDEN = {
    "deny_phi.json": {
        "case_id": "phi_case",
        "client_ref": "phi-client",
        "sensitivity": "phi",
        "provenance": {"source_type": "owned"},
        "structure": "text_only",
    },
    "deny_web_scraping.json": {
        "case_id": "scrape_case",
        "client_ref": "scrape-client",
        "sensitivity": "internal",
        "provenance": {"source_type": "web_scraping"},
        "structure": "text_only",
    },
    "deny_audio_video.json": {
        "case_id": "av_case",
        "client_ref": "av-client",
        "sensitivity": "internal",
        "provenance": {"source_type": "owned"},
        "structure": "audio_video",
    },
    "deny_scale_exceeds.json": {
        "case_id": "scale_case",
        "client_ref": "scale-client",
        "sensitivity": "internal",
        "provenance": {"source_type": "owned"},
        "structure": "text_only",
        "scale": {"row_count": 20000000, "file_size_bytes": 1000},
    },
}


def _policy() -> dict:
    loaded = load_intake_gate_policy()
    assert loaded["ok"] and loaded["policy"] is not None
    return loaded["policy"]


def _policy_deny_gate_checks(gate_checks: list) -> list:
    return [
        check
        for check in gate_checks
        if str(check.get("rule_id") or "").startswith("POLICY-DENY-")
    ]


def _write_case(root: Path, rel: str, intake: dict) -> str:
    case_dir = root / rel
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "intake.json").write_text(json.dumps(intake, ensure_ascii=False), encoding="utf-8")
    return rel


class TestIntakeGatePolicyIntegrationV1(unittest.TestCase):
    def test_layer_merge_deny_overrides_v2_accept(self) -> None:
        policy = _policy()
        with tempfile.TemporaryDirectory(dir=_REPO_ROOT / "cases") as tmp:
            root = Path(tmp)
            rel = _write_case(
                root,
                "phi_override",
                {
                    "case_id": "phi_override",
                    "client_ref": "phi-override",
                    "sensitivity": "phi",
                    "provenance": {"source_type": "owned"},
                    "structure": "text_only",
                },
            )
            case_dir = str(root / rel)
            v2 = evaluate_intake_decision_v2("tabular.intake.new_case", case_dir)
            self.assertEqual(v2["decision"], "auto_accept")

            gate = evaluate_intake_gate(
                "tabular.intake.new_case",
                case_dir,
                mode="preview",
                policy_path=str(_REPO_ROOT / "routing" / "intake_gate_policy_v1.yaml"),
            )
            self.assertTrue(gate["ok"])
            self.assertEqual(gate["decision"], "reject")
            self.assertIn("policy_deny_phi", gate["reason_codes"])
            self.assertEqual(gate["p75_policy_decision"], "policy_deny")
            self.assertEqual(gate["deny_reason"], "policy_deny_phi")
            self.assertEqual(gate["policy_version"], "intake_gate_policy_v1")

    def test_phi_demo_intake_matches_policy_deny_trace(self) -> None:
        """MC-SMOKE phi_demo synthetic intake → same deny trace as PHI golden."""
        with tempfile.TemporaryDirectory(dir=_REPO_ROOT / "cases") as tmp:
            root = Path(tmp)
            rel = _write_case(
                root,
                "phi_demo",
                {
                    "case_id": "phi_demo",
                    "client_ref": "phi-override",
                    "sensitivity": "phi",
                    "provenance": {"source_type": "owned"},
                    "structure": "text_only",
                },
            )
            gate = evaluate_intake_gate(
                "tabular.intake.new_case",
                str(root / rel),
                mode="preview",
            )
            self.assertTrue(gate["ok"])
            self.assertEqual(gate["decision"], "reject")
            self.assertEqual(gate["p75_policy_decision"], "policy_deny")
            self.assertEqual(gate["deny_reason"], "policy_deny_phi")

    def test_golden_deny_fixtures_snapshot(self) -> None:
        policy = _policy()
        for golden_name in _DENY_GOLDEN_FIXTURES:
            golden_path = _GOLDEN_DIR / golden_name
            self.assertTrue(golden_path.is_file(), f"missing golden: {golden_path}")
            golden = json.loads(golden_path.read_text(encoding="utf-8"))
            intake = _DENY_INTAKE_BY_GOLDEN[golden_name]
            with tempfile.TemporaryDirectory(dir=_REPO_ROOT / "cases") as tmp:
                root = Path(tmp)
                rel = _write_case(root, intake["case_id"], intake)
                gate = evaluate_intake_gate(
                    "tabular.cleaning.mvp",
                    str(root / rel),
                    mode="preview",
                )
                self.assertTrue(gate["ok"], golden_name)
                self.assertEqual(gate.get("decision"), golden.get("decision"), golden_name)
                self.assertEqual(
                    sorted(gate.get("reason_codes") or []),
                    sorted(golden.get("reason_codes") or []),
                    golden_name,
                )
                self.assertEqual(
                    _policy_deny_gate_checks(gate.get("gate_checks") or []),
                    _policy_deny_gate_checks(golden.get("gate_checks") or []),
                    golden_name,
                )
                self.assertEqual(gate.get("policy_version"), golden.get("policy_version"), golden_name)
                self.assertEqual(gate["p75_policy_decision"], "policy_deny", golden_name)
                self.assertIsNotNone(gate["deny_reason"], golden_name)

    def test_cli_explain_lists_matched_rules(self) -> None:
        if not _CLI.is_file():
            self.skipTest("run_intake_gate_cli.py missing")
        proc = subprocess.run(
            [
                sys.executable,
                str(_CLI),
                "--task-type",
                "tabular.cleaning.mvp",
                "--case-dir",
                "cases/demo_phase",
                "--explain",
            ],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("matched_policy_rules", proc.stdout)
        self.assertIn("POLICY-ALLOW-01", proc.stdout)
        self.assertIn("reason_codes", proc.stdout)

    def test_golden_demo_phase_snapshot(self) -> None:
        gate = evaluate_intake_gate(
            "tabular.cleaning.mvp",
            "cases/demo_phase",
            mode="preview",
        )
        golden_path = _GOLDEN_DIR / "demo_phase.json"
        self.assertTrue(golden_path.is_file(), f"missing golden: {golden_path}")
        golden = json.loads(golden_path.read_text(encoding="utf-8"))
        for key in ("decision", "reason_codes", "gate_checks", "policy_version"):
            self.assertEqual(gate.get(key), golden.get(key), key)

    def test_merge_policy_helper_reject_on_deny(self) -> None:
        policy = _policy()
        eval_result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir="cases/demo_phase",
            intake={"sensitivity": "phi", "provenance": {"source_type": "owned"}},
        )
        bridge = bridge_policy_eval(eval_result)
        merged = merge_policy_with_v2({"decision": "auto_accept"}, bridge)
        self.assertEqual(merged, "reject")


if __name__ == "__main__":
    unittest.main()
