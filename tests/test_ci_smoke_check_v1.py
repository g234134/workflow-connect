"""Unit tests for CI smoke check wrapper v1 (CI-SMOKE)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.run_ci_smoke_check_v1 import (
    evaluate_ci_smoke_check,
    main,
    run_ci_smoke_check_v1,
)

_GOOD_SMOKE = {
    "ok": True,
    "case_ref": "demo_phase",
    "steps": [{"step_id": "gate_preview", "ok": True}],
}

_GOOD_METRICS = {
    "ok": True,
    "case_ref": "demo_phase",
    "std_case_metrics_v1": {
        "pending_cases_count": 0,
        "blocked_cases_count": 0,
        "completed_cases_count": 1,
        "notifications_emitted_count": 2,
        "notifications_with_pending_ack_count": 0,
        "notifications_failed_ack_count": 0,
    },
}


class TestCiSmokeCheckV1(unittest.TestCase):
    def test_evaluate_passes_when_all_rules_met(self) -> None:
        result = evaluate_ci_smoke_check(_GOOD_SMOKE, _GOOD_METRICS, outbox_mode="isolated")
        self.assertTrue(result["ok"])
        self.assertEqual(result["failures"], [])
        self.assertTrue(result["checks"]["multi_phase_smoke_ok"])
        self.assertTrue(result["checks"]["std_case_metrics_ok"])
        self.assertEqual(result["checks"]["notifications_failed_ack_count"], 0)

    def test_evaluate_fails_when_notifications_failed_ack_nonzero(self) -> None:
        metrics = {
            **_GOOD_METRICS,
            "std_case_metrics_v1": {
                **_GOOD_METRICS["std_case_metrics_v1"],
                "notifications_failed_ack_count": 2,
            },
        }
        result = evaluate_ci_smoke_check(_GOOD_SMOKE, metrics, outbox_mode="isolated")
        self.assertFalse(result["ok"])
        self.assertTrue(
            any("notifications_failed_ack_count=2" in f for f in result["failures"])
        )

    def test_evaluate_repo_outbox_allows_preexisting_failed_ack(self) -> None:
        metrics = {
            **_GOOD_METRICS,
            "std_case_metrics_v1": {
                **_GOOD_METRICS["std_case_metrics_v1"],
                "notifications_failed_ack_count": 1,
            },
        }
        result = evaluate_ci_smoke_check(
            _GOOD_SMOKE,
            metrics,
            outbox_mode="repo",
            failed_ack_before=1,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["checks"]["notifications_failed_ack_delta"], 0)
        self.assertTrue(result["observations"])

    def test_evaluate_repo_outbox_fails_on_delta(self) -> None:
        metrics = {
            **_GOOD_METRICS,
            "std_case_metrics_v1": {
                **_GOOD_METRICS["std_case_metrics_v1"],
                "notifications_failed_ack_count": 2,
            },
        }
        result = evaluate_ci_smoke_check(
            _GOOD_SMOKE,
            metrics,
            outbox_mode="repo",
            failed_ack_before=1,
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any("delta=1" in f for f in result["failures"]))

    @patch("scripts.run_ci_smoke_check_v1.export_std_case_metrics")
    @patch("scripts.run_ci_smoke_check_v1.run_multi_phase_smoke_v1")
    def test_ci_smoke_check_exits_zero_when_smoke_and_metrics_ok(
        self,
        mock_smoke,
        mock_metrics,
    ) -> None:
        mock_smoke.return_value = _GOOD_SMOKE
        mock_metrics.return_value = _GOOD_METRICS

        result = run_ci_smoke_check_v1("demo_phase")
        self.assertTrue(result["ok"])
        self.assertEqual(main(["--format", "json"]), 0)

    @patch("scripts.run_ci_smoke_check_v1.export_std_case_metrics")
    @patch("scripts.run_ci_smoke_check_v1.run_multi_phase_smoke_v1")
    def test_ci_smoke_check_exits_one_when_failed_ack_count_nonzero(
        self,
        mock_smoke,
        mock_metrics,
    ) -> None:
        mock_smoke.return_value = _GOOD_SMOKE
        mock_metrics.return_value = {
            **_GOOD_METRICS,
            "std_case_metrics_v1": {
                **_GOOD_METRICS["std_case_metrics_v1"],
                "notifications_failed_ack_count": 1,
            },
        }

        result = run_ci_smoke_check_v1("demo_phase")
        self.assertFalse(result["ok"])
        self.assertEqual(main(["--format", "text"]), 1)


if __name__ == "__main__":
    unittest.main()
