"""Unit tests for intake gate policy evaluator v1 (P75-G3)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from routing.intake_gate_policy_evaluator_v1 import evaluate_policy
from routing.intake_gate_policy_loader_v1 import load_intake_gate_policy
from routing.intake_decision_rules_v2 import evaluate_intake_decision_v2

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEMO_PHASE = "cases/demo_phase"
_SAMPLECO = "cases/sampleco/2026-0001"
_ADDITIONAL_DEMO = "cases/additional_demo"
_UNKNOWN_CLIENT = "cases/acme/2026-0001"


def _policy() -> dict:
    loaded = load_intake_gate_policy()
    assert loaded["ok"] and loaded["policy"] is not None
    return loaded["policy"]


def _write_case(root: Path, rel: str, intake: dict) -> str:
    case_dir = root / rel
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "intake.json").write_text(json.dumps(intake, ensure_ascii=False), encoding="utf-8")
    return case_dir.relative_to(root).as_posix()


class TestIntakeGatePolicyEvaluatorV1(unittest.TestCase):
    def test_allowlist_demo_phase_tier_a_matches_v2(self) -> None:
        policy = _policy()
        v2 = evaluate_intake_decision_v2("tabular.cleaning.mvp", _DEMO_PHASE)
        result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir=_DEMO_PHASE,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.profile_id, "demo_phase")
        self.assertEqual(result.profile_tier, "A")
        self.assertEqual(result.profile_maturity, "stable")
        self.assertEqual(v2.get("fixture_profile_tier"), "A")

    def test_allowlist_sampleco_tier_b_matches_v2(self) -> None:
        policy = _policy()
        v2 = evaluate_intake_decision_v2("tabular.cleaning.mvp", _SAMPLECO)
        result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir=_SAMPLECO,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.profile_id, "sampleco")
        self.assertEqual(result.profile_tier, "B")
        self.assertEqual(v2.get("fixture_profile_tier"), "B")

    def test_tier_c_fixture_needs_review_without_extended_flag(self) -> None:
        policy = _policy()
        result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir=_ADDITIONAL_DEMO,
            flags={"include_extended_fixtures": False},
        )
        tier_hits = [h for h in result.hits if h.rule_id == "POLICY-TIER-EXT-01"]
        self.assertTrue(tier_hits)
        self.assertFalse(tier_hits[0].passed)
        self.assertEqual(tier_hits[0].suggested_action, "review_needed")

    def test_unknown_client_review_needed_pm_d6(self) -> None:
        policy = _policy()
        result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir=_UNKNOWN_CLIENT,
        )
        unknown_hits = [h for h in result.hits if h.rule_id == "POLICY-UNKNOWN-01"]
        self.assertTrue(unknown_hits)
        self.assertFalse(unknown_hits[0].passed)
        self.assertEqual(unknown_hits[0].reason_code, "unknown_client_profile")
        self.assertEqual(unknown_hits[0].suggested_action, "review_needed")

    def test_deny_phi_reject_pm_d3(self) -> None:
        policy = _policy()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = _write_case(
                root,
                "cases/phi_case",
                {
                    "case_id": "phi_case",
                    "client_ref": "phi-client",
                    "sensitivity": "phi",
                    "provenance": {"source_type": "owned"},
                    "structure": "text_only",
                },
            )
            result = evaluate_policy(
                policy,
                task_type="tabular.cleaning.mvp",
                case_dir=str(root / rel),
                intake=json.loads((root / rel / "intake.json").read_text(encoding="utf-8")),
            )
        deny = next(h for h in result.hits if h.rule_id == "POLICY-DENY-PHI")
        self.assertFalse(deny.passed)
        self.assertEqual(deny.reason_code, "policy_deny_phi")
        self.assertEqual(deny.suggested_action, "reject")

    def test_deny_web_scraping_reject_pm_d3(self) -> None:
        policy = _policy()
        intake = {
            "case_id": "scrape_case",
            "client_ref": "scrape-client",
            "sensitivity": "internal",
            "provenance": {"source_type": "web_scraping"},
            "structure": "text_only",
        }
        result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir="cases/scrape_case",
            intake=intake,
        )
        deny = next(h for h in result.hits if h.rule_id == "POLICY-DENY-WEB-SCRAPING")
        self.assertFalse(deny.passed)
        self.assertEqual(deny.reason_code, "policy_deny_web_scraping")

    def test_deny_audio_video_reject_pm_d3(self) -> None:
        policy = _policy()
        intake = {
            "case_id": "av_case",
            "client_ref": "av-client",
            "sensitivity": "internal",
            "provenance": {"source_type": "owned"},
            "structure": "audio_video",
        }
        result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir="cases/av_case",
            intake=intake,
        )
        deny = next(h for h in result.hits if h.rule_id == "POLICY-DENY-AUDIO-VIDEO")
        self.assertFalse(deny.passed)
        self.assertEqual(deny.reason_code, "policy_deny_audio_video")

    def test_deny_scale_exceeds_reject_pm_d3(self) -> None:
        policy = _policy()
        intake = {
            "case_id": "scale_case",
            "client_ref": "scale-client",
            "sensitivity": "internal",
            "provenance": {"source_type": "owned"},
            "structure": "text_only",
            "scale": {"row_count": 20000000, "file_size_bytes": 1000},
        }
        result = evaluate_policy(
            policy,
            task_type="tabular.cleaning.mvp",
            case_dir="cases/scale_case",
            intake=intake,
        )
        deny = next(h for h in result.hits if h.rule_id == "POLICY-DENY-SCALE")
        self.assertFalse(deny.passed)
        self.assertEqual(deny.reason_code, "policy_deny_scale_exceeds")

    def test_unsupported_task_type_reject_pm_d2(self) -> None:
        policy = _policy()
        result = evaluate_policy(
            policy,
            task_type="gov.observability.eval",
            case_dir=_DEMO_PHASE,
        )
        task_hit = next(h for h in result.hits if h.rule_id == "POLICY-TASK-01")
        self.assertFalse(task_hit.passed)
        self.assertEqual(task_hit.reason_code, "unsupported_task_type")
        self.assertEqual(task_hit.suggested_action, "reject")

    def test_non_tabular_without_extended_flag_reject_pm_d4(self) -> None:
        policy = _policy()
        result = evaluate_policy(
            policy,
            task_type="non_tabular.document.extract",
            case_dir="cases/docu-corp/2026-0001",
            flags={"include_extended_fixtures": False},
        )
        nt_hit = next(h for h in result.hits if h.rule_id == "POLICY-NT-01")
        self.assertFalse(nt_hit.passed)
        self.assertEqual(nt_hit.reason_code, "non_tabular_without_flag")
        self.assertEqual(nt_hit.suggested_action, "reject")


if __name__ == "__main__":
    unittest.main()
