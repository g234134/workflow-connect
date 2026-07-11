"""Tests for Wave 7 report.summary producer (REPORT-SUMMARY-PRODUCER)."""

from __future__ import annotations

import unittest
from pathlib import Path

from tests._repo_bootstrap import bootstrap_gov_core_tests

bootstrap_gov_core_tests(test_file=Path(__file__))

from core.envelope_writer import SKU_BASIC, SKU_ENRICH, write_envelopes  # noqa: E402
from core.schemas.envelope_v2 import ENRICHMENT_V0_1_SCHEMA_VERSION  # noqa: E402
from core.wave6_manifest_writer import write_manifest  # noqa: E402
from core.wave6_qa_manifest_m1 import run_m1_checks  # noqa: E402
from core.wave7_orch_pipeline_wire import (  # noqa: E402
    normalize_manifest_inputs,
    run_wave6_pipeline,
)
from core.wave7_report_summary_producer import (  # noqa: E402
    QA_STATUS_FAIL,
    QA_STATUS_PASS,
    WAVE7_REPORT_SCHEMA_VERSION,
    build_summary_for_m1_checks,
    build_wave7_report,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64


def _basic_raw_file(
    *,
    file_id: str,
    sha: str,
    clean_status: str = "ok",
) -> dict[str, object]:
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


def _present_enrichment(*, used_llm: bool = True) -> dict[str, object]:
    return {
        "schema_version": ENRICHMENT_V0_1_SCHEMA_VERSION,
        "present": True,
        "detected_language": "python",
        "domain_tags": ["backend"],
        "content_kind": "code",
        "quality_score": 90,
        "review_priority": "low",
        "enrichment_provenance": "llm" if used_llm else "rules",
        "signals": {
            "has_parse_warnings": False,
            "used_llm": used_llm,
            "line_count": 10,
            "import_count": 1,
        },
    }


def _absent_enrichment() -> dict[str, object]:
    return {
        "schema_version": ENRICHMENT_V0_1_SCHEMA_VERSION,
        "present": False,
        "domain_tags": [],
        "quality_score": None,
        "review_priority": None,
        "detected_language": None,
        "content_kind": None,
        "enrichment_provenance": None,
        "signals": None,
    }


def _enrich_raw_file(
    *,
    file_id: str,
    sha: str,
    clean_status: str = "ok",
    groq_used: bool = False,
    groq_reason: str | None = None,
    enrichment: dict[str, object] | None = None,
) -> dict[str, object]:
    payload = _basic_raw_file(file_id=file_id, sha=sha, clean_status=clean_status)
    payload["groq_used"] = groq_used
    payload["groq_reason"] = groq_reason
    payload["enrichment"] = enrichment if enrichment is not None else _present_enrichment()
    return payload


class TestWave7ReportSummaryProducer(unittest.TestCase):
    def test_basic_summary_matches_manifest_and_m1_count_passes(self) -> None:
        job_record = {"job_id": "w7-report-basic", "sku": SKU_BASIC}
        raw_files = [
            _basic_raw_file(file_id="ok-1", sha=SHA_A, clean_status="ok"),
            _basic_raw_file(file_id="reject-1", sha=SHA_B, clean_status="rejected"),
        ]

        envelopes = write_envelopes(job_record, raw_files)
        manifest = write_manifest(job_record, envelopes)
        summary = build_summary_for_m1_checks(manifest, job_record)
        qa_out = run_m1_checks(manifest, job_record, summary)
        built = build_wave7_report(job_record, manifest.to_contract_dict(), qa_out)

        self.assertTrue(built["ok"])
        report = built["report"]
        self.assertEqual(report["schema_version"], WAVE7_REPORT_SCHEMA_VERSION)

        s = report["summary"]
        self.assertEqual(s["job_id"], "w7-report-basic")
        self.assertEqual(s["sku"], SKU_BASIC)
        self.assertEqual(s["accepted_units"], 1)
        self.assertEqual(s["rejected_units"], 1)
        self.assertEqual(s["total_rows"], 2)
        self.assertEqual(s["billing_units"], {"U": 1, "L": 0})
        self.assertEqual(s["qa_status"], QA_STATUS_PASS)
        self.assertFalse(s["chargeable_hint"])
        self.assertFalse(s["cost"]["chargeable_hint"])
        self.assertIsNone(s["cost"]["amount_total"])

        ok_rows = sum(1 for row in manifest.rows if row.clean_status == "ok")
        self.assertEqual(s["accepted_units"], ok_rows)
        self.assertEqual(s["accepted_units"], manifest.accepted_units)

        self.assertTrue(report["qa"]["overall_ok"])
        self.assertTrue(report["qa"]["manifest_integrity"]["ok"])
        self.assertEqual(report["qa"]["sample_validation"]["status"], "skipped")
        self.assertEqual(qa_out["qa"]["failures"], [])

    def test_enrich_e2e_fixture_summary_and_pipeline_report(self) -> None:
        job_record = {"job_id": "w7-report-enrich", "sku": SKU_ENRICH}
        raw_files = [
            _enrich_raw_file(
                file_id="enrich-groq-ok",
                sha=SHA_A,
                groq_used=True,
                groq_reason="parse_failure_retry",
            ),
            _enrich_raw_file(file_id="enrich-plain-ok", sha=SHA_B),
            _enrich_raw_file(
                file_id="enrich-reject-absent",
                sha=SHA_D,
                clean_status="rejected",
                enrichment=_absent_enrichment(),
            ),
            _enrich_raw_file(
                file_id="enrich-dup-loser",
                sha=SHA_E,
                clean_status="parse_failed",
                enrichment=_absent_enrichment(),
            ),
            _enrich_raw_file(
                file_id="enrich-dup-winner",
                sha=SHA_E,
                groq_used=True,
                groq_reason="llm_assist",
            ),
        ]

        out = run_wave6_pipeline(job_record, raw_files)
        self.assertTrue(out["ok"])
        manifest = out["manifest"]
        report = out["report"]

        s = report["summary"]
        self.assertEqual(s["accepted_units"], 3)
        self.assertEqual(s["rejected_units"], 1)
        self.assertEqual(s["total_rows"], 4)
        self.assertEqual(s["billing_units"]["U"], 3)
        self.assertEqual(s["billing_units"]["L"], 2)
        self.assertEqual(s["qa_status"], QA_STATUS_PASS)

        summary = build_summary_for_m1_checks(manifest, job_record)
        qa_recheck = run_m1_checks(manifest, job_record, summary)
        self.assertTrue(qa_recheck["qa"]["manifest_integrity"]["ok"])
        self.assertNotIn(
            "M1-COUNT",
            [f["check_id"] for f in qa_recheck["qa"]["failures"]],
        )

    def test_m1_fail_maps_qa_status_fail(self) -> None:
        job_record = {"job_id": "w7-report-fail", "sku": SKU_BASIC}
        raw_files = [_basic_raw_file(file_id="ok-1", sha=SHA_A)]

        envelopes = write_envelopes(job_record, raw_files)
        manifest = write_manifest(job_record, envelopes)

        bad_summary = build_summary_for_m1_checks(manifest, job_record)
        bad_summary["accepted_units"] = manifest.accepted_units + 1
        qa_out = run_m1_checks(manifest, job_record, bad_summary)
        built = build_wave7_report(job_record, manifest.to_contract_dict(), qa_out)

        self.assertTrue(built["ok"])
        self.assertEqual(built["report"]["summary"]["qa_status"], QA_STATUS_FAIL)
        self.assertFalse(built["report"]["qa"]["overall_ok"])
        failure_ids = [f["check_id"] for f in built["report"]["qa"]["failures"]]
        self.assertIn("M1-COUNT", failure_ids)

    def test_basic_dedup_billing_units_locked(self) -> None:
        job_record = {"job_id": "w7-report-dedup", "sku": SKU_BASIC}
        raw_files = [
            _basic_raw_file(file_id="basic-ok", sha=SHA_A, clean_status="ok"),
            _basic_raw_file(file_id="basic-reject", sha=SHA_B, clean_status="rejected"),
            _basic_raw_file(file_id="basic-dup-loser", sha=SHA_C, clean_status="parse_failed"),
            _basic_raw_file(file_id="basic-dup-winner", sha=SHA_C, clean_status="ok"),
        ]

        envelopes = write_envelopes(job_record, raw_files)
        manifest_inputs = normalize_manifest_inputs(envelopes, sku=SKU_BASIC)
        manifest = write_manifest(job_record, manifest_inputs)

        self.assertEqual(manifest.accepted_units, 2)
        self.assertEqual(manifest.billing_units.U, 2)

        summary = build_summary_for_m1_checks(manifest, job_record)
        qa_out = run_m1_checks(manifest, job_record, summary)
        built = build_wave7_report(job_record, manifest.to_contract_dict(), qa_out)

        s = built["report"]["summary"]
        self.assertEqual(s["accepted_units"], 2)
        self.assertEqual(s["billing_units"]["U"], 2)
        self.assertEqual(s["billing_units"]["L"], 0)
        self.assertEqual(s["total_rows"], 3)
        self.assertEqual(s["rejected_units"], 1)


if __name__ == "__main__":
    unittest.main()
