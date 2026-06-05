"""Unit tests for tools.enf_preview_wrapper (ENF-RULE + C3-05 L1 warnings)."""

from __future__ import annotations

import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

from tools.enf_preview_wrapper import (
    DECISION_SUMMARY_PREFIX,
    ENF_RULE_1_NAME,
    ENF_RULE_2_NAME,
    ENF_RULE_C3_05_NAME,
    ENF_WARN_PREFIX,
    LOG_PREFIX,
    build_decision_summary_payload,
    classify_preview_outcome,
    main,
    should_emit_c3_05_warning,
)


def _per_record_row(**overrides: object) -> dict:
    base = {
        "task_id": "t-sample",
        "trace_id": "tr-sample",
        "actual_verdict": "allow",
        "ideal_verdict": "allow",
        "verdict_match": True,
        "dryrun_rule": "gate_ok_score_high",
        "gate_result": "pass",
        "tags": [],
        "metrics": {
            "success": True,
            "retry_count": 0,
            "handoff_count": 0,
            "error_type": None,
            "trace_completeness_score": 0.95,
        },
    }
    base.update(overrides)
    return base


class TestC305InfraRiskSuccess(unittest.TestCase):
    def test_infra_risk_allow_emits_c3_05_warning(self) -> None:
        row = _per_record_row(tags=["infra_risk"], actual_verdict="allow")
        self.assertTrue(should_emit_c3_05_warning(row))
        outcome, rule = classify_preview_outcome(row, min_score=0.7)
        self.assertEqual(outcome, "noop")
        self.assertIsNone(rule)

    def test_infra_risk_deny_does_not_emit_c3_05(self) -> None:
        row = _per_record_row(
            tags=["infra_risk"],
            actual_verdict="fail",
            ideal_verdict="deny",
            dryrun_rule="gate_fail_deny",
            metrics={
                "success": False,
                "retry_count": 0,
                "handoff_count": 0,
                "error_type": "timeout",
                "trace_completeness_score": 0.95,
            },
        )
        self.assertFalse(should_emit_c3_05_warning(row))

    def test_no_infra_risk_tag_does_not_emit_c3_05(self) -> None:
        row = _per_record_row(tags=["high_retry"], actual_verdict="allow")
        self.assertFalse(should_emit_c3_05_warning(row))

    def test_gate_fail_deny_without_fail_verdict_still_skips_c3_05(self) -> None:
        row = _per_record_row(
            tags=["infra_risk"],
            actual_verdict="allow",
            dryrun_rule="gate_fail_deny",
        )
        self.assertFalse(should_emit_c3_05_warning(row))


class TestEnfPreviewWrapperIntegration(unittest.TestCase):
    def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8",
        )

    def test_run_preview_emits_c3_05_warn_line(self) -> None:
        rows = [
            _per_record_row(task_id="t-allow-infra", tags=["infra_risk"]),
            _per_record_row(
                task_id="t-deny-infra",
                tags=["infra_risk"],
                actual_verdict="fail",
                dryrun_rule="gate_fail_deny",
                metrics={
                    "success": False,
                    "retry_count": 0,
                    "handoff_count": 0,
                    "error_type": "timeout",
                    "trace_completeness_score": 0.95,
                },
            ),
            _per_record_row(task_id="t-clean", tags=[]),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "sample_per_record.jsonl"
            self._write_jsonl(input_path, rows)

            stdout = StringIO()
            with mock.patch("sys.stdout", stdout):
                code = main(["--input", str(input_path), "--verbose"])

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            enf_warn_lines = [
                line for line in output.splitlines() if line.startswith(ENF_WARN_PREFIX)
            ]
            self.assertEqual(len(enf_warn_lines), 1)
            self.assertIn(f"rule={ENF_RULE_C3_05_NAME}", enf_warn_lines[0])
            self.assertIn("task_id=t-allow-infra", enf_warn_lines[0])
            self.assertNotIn("task_id=t-deny-infra", enf_warn_lines[0])
            self.assertTrue(
                any(
                    ENF_RULE_C3_05_NAME in line and "would_warn=1" in line
                    for line in output.splitlines()
                )
            )

    def test_enf_rule_1_and_2_unchanged(self) -> None:
        rule1_row = _per_record_row(
            task_id="t-rule1",
            tags=["infra_risk"],
            dryrun_rule="gate_fail_deny",
            actual_verdict="fail",
            metrics={
                "success": False,
                "retry_count": 0,
                "handoff_count": 0,
                "error_type": "timeout",
                "trace_completeness_score": 0.95,
            },
        )
        outcome1, name1 = classify_preview_outcome(rule1_row, min_score=0.7)
        self.assertEqual(outcome1, "block")
        self.assertEqual(name1, ENF_RULE_1_NAME)

        rule2_row = _per_record_row(
            task_id="t-rule2",
            tags=["high_retry"],
            dryrun_rule="gate_fail_needs_review",
            actual_verdict="warn",
            metrics={
                "success": True,
                "retry_count": 2,
                "handoff_count": 0,
                "error_type": None,
                "trace_completeness_score": 0.9,
            },
        )
        outcome2, name2 = classify_preview_outcome(rule2_row, min_score=0.7)
        self.assertEqual(outcome2, "warn")
        self.assertEqual(name2, ENF_RULE_2_NAME)

    def test_decision_summary_json_line_in_shadow_run(self) -> None:
        rows = [
            _per_record_row(
                task_id="t-rule1-a",
                tags=["infra_risk"],
                dryrun_rule="gate_fail_deny",
                actual_verdict="fail",
                gate_result="deny",
                metrics={
                    "success": False,
                    "retry_count": 0,
                    "handoff_count": 0,
                    "error_type": "timeout",
                    "trace_completeness_score": 0.95,
                },
            ),
            _per_record_row(
                task_id="t-rule1-b",
                tags=["security:critical"],
                dryrun_rule="gate_fail_deny",
                actual_verdict="fail",
                gate_result="deny",
                metrics={
                    "success": False,
                    "retry_count": 1,
                    "handoff_count": 0,
                    "error_type": "infra_risk",
                    "trace_completeness_score": 0.88,
                },
            ),
            _per_record_row(
                task_id="t-rule2",
                tags=["high_retry"],
                dryrun_rule="gate_fail_needs_review",
                actual_verdict="warn",
                metrics={
                    "success": True,
                    "retry_count": 2,
                    "handoff_count": 0,
                    "error_type": None,
                    "trace_completeness_score": 0.9,
                },
            ),
            _per_record_row(task_id="t-clean", tags=[]),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "sample_per_record.jsonl"
            self._write_jsonl(input_path, rows)

            stdout = StringIO()
            with mock.patch("sys.stdout", stdout):
                code = main(["--input", str(input_path)])

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            summary_lines = [
                line
                for line in output.splitlines()
                if line.startswith(DECISION_SUMMARY_PREFIX)
            ]
            self.assertEqual(len(summary_lines), 1)

            payload = json.loads(summary_lines[0][len(DECISION_SUMMARY_PREFIX) + 1 :])
            self.assertEqual(payload["mode"], "shadow")
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["exit_policy"], "preview_only")
            self.assertEqual(payload["total"], 4)
            self.assertEqual(payload["would_block"], 2)
            self.assertEqual(payload["would_warn"], 1)
            self.assertEqual(payload["rules"][ENF_RULE_1_NAME]["would_block"], 2)
            self.assertEqual(payload["rules"][ENF_RULE_2_NAME]["would_warn"], 1)
            self.assertEqual(payload["rules"][ENF_RULE_2_NAME]["shadow_retries"], 1)

            samples = payload["samples"]["would_block"]
            self.assertEqual(len(samples), 2)
            self.assertEqual(samples[0]["task_id"], "t-rule1-a")
            self.assertEqual(samples[0]["dryrun_rule"], "gate_fail_deny")
            self.assertEqual(samples[0]["error_type"], "timeout")
            self.assertIn("infra_risk", samples[0]["tags"])

    def test_build_decision_summary_payload_skipped(self) -> None:
        payload = build_decision_summary_payload(status="skipped", reason="input_not_found")
        self.assertEqual(payload["mode"], "shadow")
        self.assertEqual(payload["status"], "skipped")
        self.assertEqual(payload["reason"], "input_not_found")
        self.assertNotIn("samples", payload)

    def test_main_skips_when_gov_enf_enable_off(self) -> None:
        rows = [_per_record_row(task_id="t-allow-infra", tags=["infra_risk"])]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "sample_per_record.jsonl"
            self._write_jsonl(input_path, rows)

            stdout = StringIO()
            env = {"GOV_ENF_ENABLE": "0"}
            with mock.patch.dict("os.environ", env, clear=False):
                with mock.patch("sys.stdout", stdout):
                    code = main(["--input", str(input_path), "--verbose"])

            self.assertEqual(code, 0)
            output = stdout.getvalue()
            self.assertIn("[ENF] config:", output)
            self.assertIn("GOV_ENF_ENABLE=0", output)
            self.assertIn("(skipped)", output)
            self.assertIn("[ENF] WARNING:", output)
            self.assertIn("ENF is DISABLED", output)
            self.assertIn(f"{LOG_PREFIX} event=skip", output)
            self.assertNotIn(ENF_WARN_PREFIX, output)


if __name__ == "__main__":
    unittest.main()
