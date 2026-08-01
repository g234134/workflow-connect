"""Unit tests for intake decision rules v2 (W8-T2 + W9-T2)."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from routing.intake_decision_rules_v1 import evaluate_intake_decision
from routing.intake_decision_rules_v2 import evaluate_intake_decision_v2

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = _REPO_ROOT / "routing" / "intake_decision_rules_v2.py"
_DEMO_PHASE = "cases/demo_phase"
_SAMPLECO = "cases/sampleco/2026-0001"
_ADDITIONAL_DEMO = "cases/additional_demo"
_SANDBOX_CLIENT = "cases/sandbox_client"
_BAD_CASE_DIR = "cases/does_not_exist_zzzz"

_FORBIDDEN_IMPORT_PREFIXES = (
    "scripts.new_cleaning_case",
    "app.local_ui",
    "tools.tabular_tool_executor",
)


def _assert_v2_shape(result: dict) -> None:
    for key in (
        "ok",
        "rules_version",
        "task_type",
        "case_dir",
        "decision",
        "risk_level",
        "rationale",
        "fixture_profile_tier",
        "profile_maturity",
        "signals",
    ):
        assert key in result, f"missing key: {key}"
    assert result["ok"] is True
    assert result["decision"] in ("auto_accept", "needs_review", "reject")
    assert result["risk_level"] in ("low", "medium", "high")
    assert isinstance(result["rationale"], list)
    assert isinstance(result["signals"], dict)
    if result["decision"] != "reject":
        route = result.get("suggested_route")
        assert isinstance(route, dict)
        assert "planned_tools" in route


def _write_nt_fixture(
    root: Path,
    *,
    client_segment: str,
    case_id: str,
    intake: dict | None,
) -> str:
    case_dir = root / "cases" / client_segment / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    if intake is not None:
        (case_dir / "intake.json").write_text(
            json.dumps(intake, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return case_dir.relative_to(root).as_posix()


class TestIntakeDecisionRulesV2(unittest.TestCase):
    def test_module_does_not_import_forbidden_modules(self) -> None:
        source = _MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        for name in imported:
            for forbidden in _FORBIDDEN_IMPORT_PREFIXES:
                self.assertFalse(
                    name == forbidden or name.startswith(forbidden + "."),
                    f"forbidden import detected: {name}",
                )

    def test_demo_phase_tier_a_needs_review_consistent_with_v1(self) -> None:
        v1 = evaluate_intake_decision("tabular.cleaning.mvp", _DEMO_PHASE)
        v2 = evaluate_intake_decision_v2("tabular.cleaning.mvp", _DEMO_PHASE)
        _assert_v2_shape(v2)
        self.assertEqual(v2["fixture_profile_tier"], "A")
        self.assertEqual(v2["profile_maturity"], "stable")
        self.assertEqual(v2["decision"], v1["decision"])
        self.assertEqual(v2["risk_level"], v1["risk_level"])
        self.assertIn("manual_review_required", v2["signals"]["medium"])

    def test_sampleco_tier_b_needs_review_consistent_with_v1(self) -> None:
        v1 = evaluate_intake_decision("tabular.cleaning.mvp", _SAMPLECO)
        v2 = evaluate_intake_decision_v2("tabular.cleaning.mvp", _SAMPLECO)
        _assert_v2_shape(v2)
        self.assertEqual(v2["fixture_profile_tier"], "B")
        self.assertEqual(v2["profile_maturity"], "stable")
        self.assertEqual(v2["decision"], v1["decision"])
        self.assertEqual(v2["decision"], "needs_review")
        medium = v2["signals"]["medium"]
        self.assertTrue(
            "human_review_required" in medium or "schema_ambiguous" in medium,
            f"expected medium signals: {medium}",
        )

    def test_additional_demo_tier_c_needs_review_not_reject(self) -> None:
        v2 = evaluate_intake_decision_v2("tabular.cleaning.mvp", _ADDITIONAL_DEMO)
        _assert_v2_shape(v2)
        self.assertEqual(v2["fixture_profile_tier"], "C")
        self.assertEqual(v2["profile_maturity"], "experimental")
        self.assertEqual(v2["decision"], "needs_review")
        self.assertNotEqual(v2["decision"], "reject")
        self.assertIn("experimental_fixture_profile", v2["signals"]["medium"])
        rationale_text = " ".join(v2["rationale"])
        self.assertNotIn("unknown_fixture_profile", rationale_text)

    def test_sandbox_client_tier_d_needs_review_not_reject(self) -> None:
        v2 = evaluate_intake_decision_v2("tabular.cleaning.mvp", _SANDBOX_CLIENT)
        _assert_v2_shape(v2)
        self.assertEqual(v2["fixture_profile_tier"], "D")
        self.assertEqual(v2["profile_maturity"], "experimental")
        self.assertEqual(v2["decision"], "needs_review")
        self.assertEqual(v2["risk_level"], "medium")
        self.assertIn("experimental_fixture_profile", v2["signals"]["medium"])

    def test_non_tabular_family_reject_with_shadow_hook(self) -> None:
        v2 = evaluate_intake_decision_v2("gov.observability.eval", _DEMO_PHASE)
        _assert_v2_shape(v2)
        self.assertEqual(v2["decision"], "reject")
        self.assertEqual(v2["message"], "non_tabular_family")
        self.assertEqual(v2["flow_family"], "non_tabular")
        hook = v2.get("shadow_flow_hook") or {}
        self.assertFalse(hook.get("eligible"))
        self.assertIn("W8-T5", hook.get("future_ticket", ""))

    def test_nt_a_document_extract_needs_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = _write_nt_fixture(
                root,
                client_segment="docu-corp",
                case_id="2026-0001",
                intake={
                    "case_id": "docu-2026-0001",
                    "client_ref": "docu-corp",
                    "content_type": "mixed_documents",
                    "schema_hint": "schema-free",
                    "sensitivity": "internal",
                },
            )
            with mock.patch(
                "routing.intake_decision_rules_v2._REPO_ROOT",
                root,
            ):
                v2 = evaluate_intake_decision_v2(
                    "non_tabular.document.extract",
                    case_dir,
                )
            _assert_v2_shape(v2)
            self.assertEqual(v2["flow_family"], "non_tabular")
            self.assertEqual(v2["fixture_profile_tier"], "NT-A")
            self.assertEqual(v2["case_profile_tier"], "NT-A")
            self.assertEqual(v2["decision"], "needs_review")
            self.assertEqual(v2["risk_level"], "medium")
            self.assertIn("document_extraction_profile", v2["signals"]["medium"])
            hook = v2.get("shadow_flow_hook") or {}
            self.assertTrue(hook.get("eligible"))

    def test_nt_b_log_analyze_needs_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = _write_nt_fixture(
                root,
                client_segment="log-analytics-co",
                case_id="logs-2026-0001",
                intake={
                    "case_id": "logs-2026-0001",
                    "client_ref": "log-analytics-co",
                    "content_type": "server_logs",
                    "schema_hint": "semi-structured",
                    "sensitivity": "internal",
                },
            )
            with mock.patch(
                "routing.intake_decision_rules_v2._REPO_ROOT",
                root,
            ):
                v2 = evaluate_intake_decision_v2(
                    "non_tabular.log.analyze",
                    case_dir,
                )
            _assert_v2_shape(v2)
            self.assertEqual(v2["fixture_profile_tier"], "NT-B")
            self.assertEqual(v2["case_profile_tier"], "NT-B")
            self.assertEqual(v2["decision"], "needs_review")
            self.assertEqual(v2["risk_level"], "medium")
            self.assertIn("log_analysis_profile", v2["signals"]["medium"])

    def test_nt_a_reject_on_corrupt_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = _write_nt_fixture(
                root,
                client_segment="docu-corp",
                case_id="2026-0002",
                intake={
                    "case_id": "docu-2026-0002",
                    "client_ref": "docu-corp",
                    "_corrupt": True,
                },
            )
            with mock.patch(
                "routing.intake_decision_rules_v2._REPO_ROOT",
                root,
            ):
                v2 = evaluate_intake_decision_v2(
                    "non_tabular.document.extract",
                    case_dir,
                )
            self.assertEqual(v2["decision"], "reject")
            self.assertEqual(v2["message"], "content_corrupt_or_unreadable")
            self.assertEqual(v2["risk_level"], "high")

    def test_nt_b_reject_on_unparseable_intake_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = root / "cases" / "log-analytics-co" / "2026-0003"
            case_dir.mkdir(parents=True)
            (case_dir / "intake.json").write_text("{not valid json", encoding="utf-8")
            rel = case_dir.relative_to(root).as_posix()
            with mock.patch(
                "routing.intake_decision_rules_v2._REPO_ROOT",
                root,
            ):
                v2 = evaluate_intake_decision_v2("non_tabular.log.analyze", rel)
            self.assertEqual(v2["decision"], "reject")
            self.assertEqual(v2["message"], "intake_unparseable")
            self.assertEqual(v2["risk_level"], "high")

    def test_bad_case_dir_reject(self) -> None:
        v2 = evaluate_intake_decision_v2("tabular.cleaning.mvp", _BAD_CASE_DIR)
        self.assertEqual(v2["decision"], "reject")
        self.assertEqual(v2["message"], "case_dir_not_found")
        self.assertIsNone(v2.get("suggested_route"))

    def test_intake_new_case_auto_accept_all_tiers(self) -> None:
        for case_dir, tier in (
            (_DEMO_PHASE, "A"),
            (_SANDBOX_CLIENT, "D"),
        ):
            v2 = evaluate_intake_decision_v2("tabular.intake.new_case", case_dir)
            _assert_v2_shape(v2)
            self.assertEqual(v2["fixture_profile_tier"], tier)
            self.assertEqual(v2["decision"], "auto_accept")
            self.assertEqual(v2["risk_level"], "low")

    def test_v1_fallback_on_internal_error(self) -> None:
        with mock.patch(
            "routing.intake_decision_rules_v2._evaluate_intake_decision_v2_core",
            side_effect=RuntimeError("simulated v2 failure"),
        ):
            result = evaluate_intake_decision_v2(
                "tabular.cleaning.mvp",
                _DEMO_PHASE,
                use_v1_fallback=True,
            )
        self.assertEqual(result["rules_version"], "v1_fallback")
        self.assertIn("simulated v2 failure", result.get("v2_fallback_reason", ""))
        self.assertEqual(result["decision"], "needs_review")

    def test_v1_fallback_disabled_raises(self) -> None:
        with mock.patch(
            "routing.intake_decision_rules_v2._evaluate_intake_decision_v2_core",
            side_effect=RuntimeError("simulated v2 failure"),
        ):
            with self.assertRaises(RuntimeError):
                evaluate_intake_decision_v2(
                    "tabular.cleaning.mvp",
                    _DEMO_PHASE,
                    use_v1_fallback=False,
                )

    def test_cli_json_sandbox_client(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_MODULE_PATH),
                "--task-type",
                "tabular.cleaning.mvp",
                "--case-dir",
                _SANDBOX_CLIENT,
                "--json",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        _assert_v2_shape(payload)
        self.assertEqual(payload["fixture_profile_tier"], "D")


if __name__ == "__main__":
    unittest.main()
