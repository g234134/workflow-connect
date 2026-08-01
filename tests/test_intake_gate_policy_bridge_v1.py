"""Unit tests for intake gate policy bridge v1 (P75-G3)."""

from __future__ import annotations

import unittest

from routing.intake_gate_policy_bridge_v1 import (
    bridge_policy_eval,
    bridge_has_deny_failure,
    derive_p75_policy_trace,
)
from routing.intake_gate_policy_evaluator_v1 import evaluate_policy, g1_reason_codes
from routing.intake_gate_policy_loader_v1 import load_intake_gate_policy
from routing.intake_gate_policy_types_v1 import PolicyEvalResult, PolicyHit


def _policy() -> dict:
    loaded = load_intake_gate_policy()
    assert loaded["ok"] and loaded["policy"] is not None
    return loaded["policy"]


class TestIntakeGatePolicyBridgeV1(unittest.TestCase):
    def test_bridge_emits_gate_checks_shape(self) -> None:
        policy = _policy()
        eval_result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir="cases/demo_phase",
        )
        bridge = bridge_policy_eval(eval_result)
        self.assertTrue(bridge["ok"])
        self.assertIsInstance(bridge["gate_checks"], list)
        self.assertGreater(len(bridge["gate_checks"]), 0)
        for check in bridge["gate_checks"]:
            self.assertIn("rule_id", check)
            self.assertIn("passed", check)
            self.assertIn("detail", check)

    def test_bridge_deny_sets_passed_false(self) -> None:
        eval_result = PolicyEvalResult(
            ok=True,
            policy_version="intake_gate_policy_v1",
            hits=[
                PolicyHit(
                    rule_id="POLICY-DENY-PHI",
                    passed=False,
                    detail="sensitivity=phi",
                    reason_code="policy_deny_phi",
                    suggested_action="reject",
                    hit_kind="deny",
                )
            ],
        )
        bridge = bridge_policy_eval(eval_result)
        deny_check = bridge["gate_checks"][0]
        self.assertFalse(deny_check["passed"])
        self.assertTrue(bridge_has_deny_failure(bridge))
        self.assertIn("policy_deny_phi", bridge["reason_codes"])

    def test_bridge_reason_codes_subset_of_g1_enum(self) -> None:
        policy = _policy()
        eval_result = evaluate_policy(
            policy,
            task_type="gov.observability.eval",
            case_dir="cases/demo_phase",
        )
        bridge = bridge_policy_eval(eval_result)
        allowed = g1_reason_codes()
        for code in bridge["reason_codes"]:
            self.assertIn(code, allowed)

    def test_derive_p75_policy_trace_deny_phi(self) -> None:
        eval_result = PolicyEvalResult(
            ok=True,
            policy_version="intake_gate_policy_v1",
            hits=[
                PolicyHit(
                    rule_id="POLICY-DENY-PHI",
                    passed=False,
                    detail="sensitivity=phi",
                    reason_code="policy_deny_phi",
                    suggested_action="reject",
                    hit_kind="deny",
                )
            ],
        )
        bridge = bridge_policy_eval(eval_result)
        trace = derive_p75_policy_trace(bridge)
        self.assertEqual(trace["p75_policy_decision"], "policy_deny")
        self.assertEqual(trace["deny_reason"], "policy_deny_phi")

    def test_derive_p75_policy_trace_pass_demo_phase(self) -> None:
        policy = _policy()
        eval_result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir="cases/demo_phase",
        )
        bridge = bridge_policy_eval(eval_result)
        trace = derive_p75_policy_trace(bridge)
        self.assertEqual(trace["p75_policy_decision"], "policy_pass")
        self.assertIsNone(trace["deny_reason"])


if __name__ == "__main__":
    unittest.main()
