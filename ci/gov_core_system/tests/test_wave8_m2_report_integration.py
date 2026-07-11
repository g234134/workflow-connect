"""Tests for Wave 8 M2 report integration (W8-M2-REPORT-INTEGRATION)."""

from __future__ import annotations

import unittest
from pathlib import Path

from tests._repo_bootstrap import bootstrap_gov_core_tests

bootstrap_gov_core_tests(test_file=Path(__file__))

from core.envelope_writer import SKU_BASIC, write_envelopes  # noqa: E402
from core.wave6_manifest_writer import write_manifest  # noqa: E402
from core.wave6_qa_manifest_m1 import run_m1_checks  # noqa: E402
from core.wave7_report_summary_producer import (  # noqa: E402
    M2_SAMPLE_VALIDATION_SKIPPED,
    QA_STATUS_FAIL,
    QA_STATUS_PASS,
    QA_STATUS_PASS_WITH_WARNINGS,
    build_summary_for_m1_checks,
    build_wave7_report,
    merge_m1_m2_results,
)

SHA_A = "a" * 64


def _basic_raw_file(*, file_id: str, sha: str, clean_status: str = "ok") -> dict[str, object]:
    return {
        "file_id": file_id,
        "content_sha256": sha,
        "clean_status": clean_status,
        "name": f"{file_id}.py",
        "extension": ".py",
        "original_type": "python_source",
        "size_bytes": 128,
        "encoding": "utf-8",
        "stored_logical_path": f"cleaned_full/{file_id}.py.json",
        "content_summary": {
            "line_count": 3,
            "char_count": 42,
            "imports": ["json"],
            "preview_lines": ["import json"],
        },
        "groq_used": False,
        "groq_reason": None,
        "parse_strategy": "ast",
        "warnings": [],
    }


def _m1_pass_qa() -> dict[str, object]:
    return {
        "qa": {
            "manifest_integrity": {
                "ok": True,
                "checked_rows": 1,
                "failed_rows": 0,
                "failed_checks": 0,
            },
            "failures": [],
        }
    }


def _m1_fail_qa() -> dict[str, object]:
    return {
        "qa": {
            "manifest_integrity": {
                "ok": False,
                "checked_rows": 1,
                "failed_rows": 1,
                "failed_checks": 1,
            },
            "failures": [
                {
                    "layer": "M1",
                    "check_id": "M1-COUNT",
                    "severity": "P0",
                    "file_id": None,
                    "content_sha256": None,
                    "stored_logical_path": None,
                    "message": "accepted_units mismatch",
                    "remediation_hint": "fix_manifest",
                }
            ],
        }
    }


def _m2_failure(*, severity: str, check_id: str = "M2-QUALITY") -> dict[str, object]:
    return {
        "layer": "M2",
        "check_id": check_id,
        "severity": severity,
        "file_id": "file-sample-1",
        "content_sha256": SHA_A,
        "stored_logical_path": "cleaned_full/file-sample-1.py.json",
        "message": f"{check_id} failed",
        "remediation_hint": "review_sample",
    }


def _m2_result(*, severity: str, check_id: str = "M2-QUALITY") -> dict[str, object]:
    failure = _m2_failure(severity=severity, check_id=check_id)
    sev = severity.upper()
    has_blocking = sev in ("P0", "P1")
    sample_ok = sev not in ("P0", "P1")
    return {
        "ok": sample_ok,
        "sample_validation": {
            "status": "completed",
            "ok": sample_ok,
            "N": 10,
            "sample_size": 5,
            "seed": "w8-test-seed",
            "failed_checks": 0 if sample_ok else 1,
            "failures": [],
        },
        "failures": [failure] if has_blocking else [],
    }


class TestMergeM1M2Results(unittest.TestCase):
    def test_without_m2_uses_skipped_sample_validation(self) -> None:
        merged = merge_m1_m2_results(_m1_pass_qa(), None)
        self.assertEqual(merged["sample_validation"]["status"], "skipped")
        self.assertEqual(merged["sample_validation"]["reason"], M2_SAMPLE_VALIDATION_SKIPPED["reason"])
        self.assertTrue(merged["overall_ok"])
        self.assertEqual(merged["failures"], [])

    def test_m2_p1_merges_failures_and_sets_overall_ok_false(self) -> None:
        m2 = _m2_result(severity="P1")
        merged = merge_m1_m2_results(_m1_pass_qa(), m2)
        self.assertEqual(merged["sample_validation"]["status"], "completed")
        self.assertFalse(merged["overall_ok"])
        self.assertEqual(len(merged["failures"]), 1)
        self.assertEqual(merged["failures"][0]["layer"], "M2")
        self.assertEqual(merged["failures"][0]["severity"], "P1")


class TestWave8M2ReportIntegration(unittest.TestCase):
    def _build(
        self,
        qa_m1: dict[str, object],
        *,
        m2: dict[str, object] | None = None,
    ) -> dict[str, object]:
        job_record = {"job_id": "w8-m2-report", "sku": SKU_BASIC}
        raw_files = [_basic_raw_file(file_id="ok-1", sha=SHA_A)]
        manifest = write_manifest(job_record, write_envelopes(job_record, raw_files))
        built = build_wave7_report(job_record, manifest.to_contract_dict(), qa_m1, m2_result=m2)
        self.assertTrue(built["ok"])
        return built["report"]

    def test_m1_pass_m2_skipped(self) -> None:
        report = self._build(_m1_pass_qa())
        self.assertEqual(report["summary"]["qa_status"], QA_STATUS_PASS)
        self.assertTrue(report["qa"]["overall_ok"])
        self.assertEqual(report["qa"]["sample_validation"]["status"], "skipped")
        self.assertFalse(report["summary"]["chargeable_hint"])

    def test_m1_pass_m2_p1_pass_with_warnings(self) -> None:
        report = self._build(_m1_pass_qa(), m2=_m2_result(severity="P1"))
        self.assertEqual(report["summary"]["qa_status"], QA_STATUS_PASS_WITH_WARNINGS)
        self.assertFalse(report["qa"]["overall_ok"])
        self.assertEqual(report["qa"]["sample_validation"]["status"], "completed")
        self.assertEqual(report["qa"]["failures"][0]["severity"], "P1")
        self.assertFalse(report["summary"]["chargeable_hint"])

    def test_m1_pass_m2_p0_fail(self) -> None:
        report = self._build(_m1_pass_qa(), m2=_m2_result(severity="P0", check_id="M2-SCHEMA-20"))
        self.assertEqual(report["summary"]["qa_status"], QA_STATUS_FAIL)
        self.assertFalse(report["qa"]["overall_ok"])
        self.assertFalse(report["qa"]["sample_validation"]["ok"])
        severities = {f["severity"] for f in report["qa"]["failures"]}
        self.assertIn("P0", severities)

    def test_m1_fail_m2_skipped(self) -> None:
        report = self._build(_m1_fail_qa())
        self.assertEqual(report["summary"]["qa_status"], QA_STATUS_FAIL)
        self.assertFalse(report["qa"]["overall_ok"])
        self.assertEqual(report["qa"]["sample_validation"]["status"], "skipped")
        failure_ids = [f["check_id"] for f in report["qa"]["failures"]]
        self.assertIn("M1-COUNT", failure_ids)

    def test_pipeline_m1_pass_without_m2_still_skipped(self) -> None:
        job_record = {"job_id": "w8-m2-pipeline", "sku": SKU_BASIC}
        raw_files = [_basic_raw_file(file_id="ok-1", sha=SHA_A)]
        manifest = write_manifest(job_record, write_envelopes(job_record, raw_files))
        summary = build_summary_for_m1_checks(manifest, job_record)
        qa_out = run_m1_checks(manifest, job_record, summary)
        built = build_wave7_report(job_record, manifest.to_contract_dict(), qa_out)
        report = built["report"]
        self.assertEqual(report["summary"]["qa_status"], QA_STATUS_PASS)
        self.assertEqual(report["qa"]["sample_validation"]["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
