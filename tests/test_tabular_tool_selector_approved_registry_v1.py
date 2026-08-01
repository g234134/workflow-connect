"""Unit tests for Tabular Tool Selector approved-registry consumption (W10-T2)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.tabular_tool_selector import (
    TOOL_CLEAN_PHASE_DEMO,
    TOOL_VALIDATE_ELIGIBILITY,
    select_tabular_tools,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEMO_PHASE_DIR = _REPO_ROOT / "cases" / "demo_phase"
_ENV_REGISTRY_ENABLED = "TABULAR_APPROVED_REGISTRY_ENABLED"
_ENV_REGISTRY_STRICT = "TABULAR_APPROVED_REGISTRY_STRICT"


def _load_intake(case_dir: Path) -> dict:
    with (case_dir / "intake.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def _write_registry(path: Path, approved: list[dict]) -> None:
    payload = {
        "schema_version": "approved_skill_registry_v1",
        "registry_revision": "1.0.0",
        "approved": approved,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class TestTabularToolSelectorApprovedRegistryV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.demo_intake = _load_intake(_DEMO_PHASE_DIR)

    def setUp(self) -> None:
        self._env_patch = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        os.environ.pop(_ENV_REGISTRY_ENABLED, None)
        os.environ.pop(_ENV_REGISTRY_STRICT, None)

    def tearDown(self) -> None:
        self._env_patch.stop()

    def _enable_registry(self, *, strict: bool = False) -> None:
        os.environ[_ENV_REGISTRY_ENABLED] = "1"
        if strict:
            os.environ[_ENV_REGISTRY_STRICT] = "1"

    def test_empty_registry_degrades_without_blocking(self) -> None:
        self._enable_registry()
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "approved_registry.json"
            _write_registry(registry_path, [])
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                registry_path,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "clean",
                    intake=self.demo_intake,
                    gate_notes=["phase_like", "phase_demo"],
                )
        self.assertTrue(result["ok"])
        self.assertEqual(result["candidate_tools"][0]["tool_id"], TOOL_CLEAN_PHASE_DEMO)
        self.assertIn("approved_registry", result)
        self.assertTrue(result["approved_registry"]["degraded"])
        self.assertIn("empty", result["approved_registry"]["message"])

    def test_one_approved_entry_via_tool_ids(self) -> None:
        self._enable_registry()
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "approved_registry.json"
            _write_registry(
                registry_path,
                [
                    {
                        "skill_id": "test-clean-skill",
                        "version": "1.0.0",
                        "approved_at": "2026-06-15T00:00:00+00:00",
                        "tool_ids": [TOOL_CLEAN_PHASE_DEMO],
                        "selector_eligible": True,
                    }
                ],
            )
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                registry_path,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "clean",
                    intake=self.demo_intake,
                    gate_notes=["phase_like", "phase_demo"],
                )
        self.assertTrue(result["ok"])
        tool = result["candidate_tools"][0]
        self.assertEqual(tool["tool_id"], TOOL_CLEAN_PHASE_DEMO)
        self.assertEqual(tool["approval_status"], "approved")
        self.assertFalse(result["approved_registry"]["degraded"])

    def test_unapproved_tool_blocked(self) -> None:
        self._enable_registry()
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "approved_registry.json"
            _write_registry(
                registry_path,
                [
                    {
                        "skill_id": "only-clean-approved",
                        "version": "1.0.0",
                        "approved_at": "2026-06-15T00:00:00+00:00",
                        "tool_ids": [TOOL_CLEAN_PHASE_DEMO],
                        "selector_eligible": True,
                    }
                ],
            )
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                registry_path,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "gate_only",
                    intake=self.demo_intake,
                )
        self.assertFalse(result["ok"])
        self.assertEqual(result["selector_rule_id"], "error.registry_not_approved")
        self.assertEqual(result["candidate_tools"], [])

    def test_malformed_json_fallback(self) -> None:
        self._enable_registry()
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "approved_registry.json"
            registry_path.write_text("{not valid json", encoding="utf-8")
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                registry_path,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "clean",
                    intake=self.demo_intake,
                    gate_notes=["phase_like", "phase_demo"],
                )
        self.assertTrue(result["ok"])
        self.assertEqual(result["candidate_tools"][0]["tool_id"], TOOL_CLEAN_PHASE_DEMO)
        self.assertTrue(result["approved_registry"]["degraded"])
        self.assertIn("unreadable", result["approved_registry"]["message"])

    def test_skill_id_static_map_resolves_clean_tool(self) -> None:
        self._enable_registry()
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "approved_registry.json"
            _write_registry(
                registry_path,
                [
                    {
                        "skill_id": "draft-clean-basic-job-001",
                        "version": "1.0.0",
                        "approved_at": "2026-06-15T00:00:00+00:00",
                        "selector_eligible": True,
                    }
                ],
            )
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                registry_path,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "clean",
                    intake=self.demo_intake,
                    gate_notes=["phase_like", "phase_demo"],
                )
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["candidate_tools"][0]["tool_id"],
            TOOL_CLEAN_PHASE_DEMO,
        )
        self.assertEqual(result["candidate_tools"][0]["approval_status"], "approved")

    def test_disabled_env_matches_baseline_shape(self) -> None:
        result = select_tabular_tools(
            str(_DEMO_PHASE_DIR),
            "gate_only",
            intake=self.demo_intake,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["candidate_tools"][0]["tool_id"],
            TOOL_VALIDATE_ELIGIBILITY,
        )
        self.assertNotIn("approved_registry", result)
        self.assertNotIn("approval_status", result["candidate_tools"][0])

    def test_selector_eligible_false_entry_ignored(self) -> None:
        self._enable_registry()
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "approved_registry.json"
            _write_registry(
                registry_path,
                [
                    {
                        "skill_id": "blocked-skill",
                        "version": "1.0.0",
                        "approved_at": "2026-06-15T00:00:00+00:00",
                        "tool_ids": [TOOL_CLEAN_PHASE_DEMO],
                        "selector_eligible": False,
                    }
                ],
            )
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                registry_path,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "clean",
                    intake=self.demo_intake,
                    gate_notes=["phase_like", "phase_demo"],
                )
        self.assertTrue(result["ok"])
        self.assertTrue(result["approved_registry"]["degraded"])
        self.assertEqual(result["candidate_tools"][0]["tool_id"], TOOL_CLEAN_PHASE_DEMO)
        self.assertNotIn("approval_status", result["candidate_tools"][0])

    # Fail-closed policy tests (strict mode)

    def test_registry_missing_fail_closed_strict_mode(self) -> None:
        """TABULAR_APPROVED_REGISTRY_STRICT=1 blocks selector when registry file missing."""
        self._enable_registry(strict=True)
        with tempfile.TemporaryDirectory() as tmp:
            # Point to a non-existent registry path
            missing_registry = Path(tmp) / "nonexistent_registry.json"
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                missing_registry,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "clean",
                    intake=self.demo_intake,
                    gate_notes=["phase_like", "phase_demo"],
                )
        self.assertFalse(result["ok"])
        self.assertEqual(result["selector_rule_id"], "error.registry_fail_closed")
        self.assertIn("missing", result["message"].lower())
        self.assertEqual(result["candidate_tools"], [])

    def test_malformed_json_fail_closed_strict_mode(self) -> None:
        """TABULAR_APPROVED_REGISTRY_STRICT=1 blocks selector when registry is malformed."""
        self._enable_registry(strict=True)
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "approved_registry.json"
            registry_path.write_text("{not valid json", encoding="utf-8")
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                registry_path,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "gate_only",
                    intake=self.demo_intake,
                )
        self.assertFalse(result["ok"])
        self.assertEqual(result["selector_rule_id"], "error.registry_fail_closed")
        self.assertIn("unreadable", result["message"].lower())
        self.assertEqual(result["candidate_tools"], [])

    def test_empty_registry_fail_closed_strict_mode(self) -> None:
        """TABULAR_APPROVED_REGISTRY_STRICT=1 blocks selector when registry is empty."""
        self._enable_registry(strict=True)
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "approved_registry.json"
            _write_registry(registry_path, [])  # empty approved list
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                registry_path,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "clean",
                    intake=self.demo_intake,
                    gate_notes=["phase_like", "phase_demo"],
                )
        self.assertFalse(result["ok"])
        self.assertEqual(result["selector_rule_id"], "error.registry_fail_closed")
        self.assertIn("empty", result["message"].lower())
        self.assertEqual(result["candidate_tools"], [])

    def test_registry_missing_approved_key_fail_closed_strict_mode(self) -> None:
        """TABULAR_APPROVED_REGISTRY_STRICT=1 blocks when registry lacks approved field."""
        self._enable_registry(strict=True)
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "approved_registry.json"
            bad_payload = {
                "schema_version": "approved_skill_registry_v1",
                "registry_revision": "1.0.0",
                # missing "approved" field
            }
            registry_path.write_text(json.dumps(bad_payload, indent=2), encoding="utf-8")
            with mock.patch(
                "tools.tabular_tool_selector._REGISTRY_PATH",
                registry_path,
            ):
                result = select_tabular_tools(
                    str(_DEMO_PHASE_DIR),
                    "gate_only",
                    intake=self.demo_intake,
                )
        self.assertFalse(result["ok"])
        self.assertEqual(result["selector_rule_id"], "error.registry_fail_closed")
        self.assertIn("malformed", result["message"].lower())
        self.assertEqual(result["candidate_tools"], [])


if __name__ == "__main__":
    unittest.main()
