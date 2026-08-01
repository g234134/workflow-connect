"""Unit tests for intake gate policy loader v1 (P75-G3)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from routing.intake_gate_policy_loader_v1 import default_policy_path, load_intake_gate_policy

_REPO_ROOT = Path(__file__).resolve().parents[1]


class TestIntakeGatePolicyLoaderV1(unittest.TestCase):
    def test_load_default_policy_ok(self) -> None:
        result = load_intake_gate_policy()
        self.assertTrue(result["ok"], result.get("error"))
        policy = result["policy"]
        assert policy is not None
        self.assertEqual(policy["policy_version"], "intake_gate_policy_v1")
        self.assertIn("allowlist_tiers", policy)
        self.assertIn("deny_rules", policy)

    def test_load_policy_missing_file_returns_error_dict(self) -> None:
        result = load_intake_gate_policy("routing/does_not_exist_policy.yaml")
        self.assertFalse(result["ok"])
        self.assertIsNone(result["policy"])
        self.assertIn("not found", str(result["error"]))

    def test_load_policy_invalid_yaml_returns_error_dict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "bad_policy.yaml"
            bad_path.write_text("policy_version: [unclosed", encoding="utf-8")
            result = load_intake_gate_policy(bad_path, validate_schema=False)
        self.assertFalse(result["ok"])
        self.assertIn("invalid yaml", str(result["error"]).lower())

    def test_load_policy_schema_rejects_unknown_deny_code(self) -> None:
        default_text = default_policy_path(repo_root=_REPO_ROOT).read_text(encoding="utf-8")
        mutated = default_text.replace(
            "reason_code: policy_deny_phi",
            "reason_code: policy_deny_unknown_future",
            1,
        )
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "mutated_policy.yaml"
            bad_path.write_text(mutated, encoding="utf-8")
            result = load_intake_gate_policy(bad_path, validate_schema=True)
        self.assertFalse(result["ok"])
        self.assertIn("reason_code", str(result["error"]))


if __name__ == "__main__":
    unittest.main()
