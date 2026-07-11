"""Unit tests for the Wave 6 manifest-only QA M1 checker."""

from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from core.wave6_qa_manifest_m1 import run_m1_checks

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


def _row(
    *,
    file_id: str,
    sha: str,
    clean_status: str = "ok",
    extension: str = ".py",
    stored_logical_path: str | None = None,
    schema_version: str = "2.0",
    has_enrichment: object = False,
    include_enrichment_key: bool = False,
    enrichment: object | None = None,
) -> dict:
    row = {
        "file_id": file_id,
        "content_sha256": sha,
        "clean_status": clean_status,
        "extension": extension,
        "stored_logical_path": stored_logical_path or f"deliverables/{file_id}.json",
        "schema_version": schema_version,
        "has_enrichment": has_enrichment,
    }
    if include_enrichment_key:
        row["enrichment"] = enrichment
    return row


def _manifest(rows: list[dict], *, billing_units: object | None = None) -> dict:
    manifest = {
        "schema_version": "manifest_v2.0",
        "job_id": "job-qa-m1-001",
        "product_sku": "CLEAN-BASIC",
        "accepted_units": 999,
        "rows": rows,
    }
    if billing_units is not None:
        manifest["billing_units"] = billing_units
    return manifest


def _job_record(*, sku: str) -> dict:
    return {"job_id": "job-qa-m1-001", "sku": sku}


def _failure_ids(result: dict) -> list[str]:
    return [item["check_id"] for item in result["qa"]["failures"]]


class TestWave6QaManifestM1(unittest.TestCase):
    def test_m1_keys_pass_minimal_row(self) -> None:
        result = run_m1_checks(
            _manifest([_row(file_id="f1", sha=SHA_A)]),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 1},
        )

        self.assertEqual(result["qa"]["manifest_integrity"]["checked_rows"], 1)
        self.assertEqual(result["qa"]["manifest_integrity"]["failed_rows"], 0)
        self.assertEqual(result["qa"]["manifest_integrity"]["failed_checks"], 0)
        self.assertEqual(result["qa"]["failures"], [])

    def test_m1_keys_fail_missing_required_key(self) -> None:
        bad_row = _row(file_id="f1", sha=SHA_A)
        bad_row.pop("stored_logical_path")

        result = run_m1_checks(
            _manifest([bad_row]),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 1},
        )

        self.assertEqual(_failure_ids(result), ["M1-KEYS"])
        self.assertEqual(result["qa"]["manifest_integrity"]["failed_rows"], 1)
        self.assertIn("stored_logical_path", result["qa"]["failures"][0]["message"])

    def test_m1_sha_pass_and_fail(self) -> None:
        passing = run_m1_checks(
            _manifest([_row(file_id="f1", sha=SHA_A)]),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 1},
        )
        failing = run_m1_checks(
            _manifest([_row(file_id="f1", sha="not-a-sha")]),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 1},
        )

        self.assertNotIn("M1-SHA", _failure_ids(passing))
        self.assertEqual(_failure_ids(failing), ["M1-SHA"])
        self.assertIsNone(failing["qa"]["failures"][0]["content_sha256"])

    def test_m1_ok_only_counts_only_exact_ok_rows(self) -> None:
        rows = [
            _row(file_id="f1", sha=SHA_A, clean_status="ok"),
            _row(file_id="f2", sha=SHA_B, clean_status="failed"),
        ]

        passing = run_m1_checks(
            _manifest(rows),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 1},
        )
        failing = run_m1_checks(
            _manifest(rows),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 2},
        )

        self.assertNotIn("M1-OK-ONLY", _failure_ids(passing))
        self.assertEqual(_failure_ids(failing), ["M1-OK-ONLY", "M1-COUNT"])
        self.assertEqual(failing["qa"]["manifest_integrity"]["failed_rows"], 0)

    def test_m1_sku_basic_rejects_enrichment_key(self) -> None:
        passing = run_m1_checks(
            _manifest([_row(file_id="f1", sha=SHA_A)]),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 1},
        )
        failing = run_m1_checks(
            _manifest(
                [
                    _row(
                        file_id="f1",
                        sha=SHA_A,
                        include_enrichment_key=True,
                        enrichment=None,
                    )
                ]
            ),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 1},
        )

        self.assertNotIn("M1-SKU-BASIC", _failure_ids(passing))
        self.assertEqual(_failure_ids(failing), ["M1-SKU-BASIC"])

    def test_m1_sku_enrich_requires_has_enrichment_true(self) -> None:
        passing = run_m1_checks(
            _manifest([_row(file_id="f1", sha=SHA_A, has_enrichment=True)]),
            _job_record(sku="CLEAN-ENRICH"),
            {"accepted_units": 1},
        )
        failing = run_m1_checks(
            _manifest([_row(file_id="f1", sha=SHA_A, has_enrichment=False)]),
            _job_record(sku="CLEAN-ENRICH"),
            {"accepted_units": 1},
        )

        self.assertNotIn("M1-SKU-ENRICH", _failure_ids(passing))
        self.assertEqual(_failure_ids(failing), ["M1-SKU-ENRICH"])

    def test_m1_dedup_flags_duplicate_sha_after_first_row(self) -> None:
        passing = run_m1_checks(
            _manifest(
                [
                    _row(file_id="f1", sha=SHA_A),
                    _row(file_id="f2", sha=SHA_B),
                ]
            ),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 2},
        )
        failing = run_m1_checks(
            _manifest(
                [
                    _row(file_id="f1", sha=SHA_A),
                    _row(file_id="f2", sha=SHA_A),
                ]
            ),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 2},
        )

        self.assertNotIn("M1-DEDUP", _failure_ids(passing))
        self.assertEqual(_failure_ids(failing), ["M1-DEDUP"])
        self.assertEqual(failing["qa"]["failures"][0]["file_id"], "f2")

    def test_m1_count_detects_aggregate_mismatch_without_failed_rows(self) -> None:
        result = run_m1_checks(
            _manifest([_row(file_id="f1", sha=SHA_A)]),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 0},
        )

        self.assertEqual(_failure_ids(result), ["M1-COUNT"])
        self.assertEqual(result["qa"]["manifest_integrity"]["failed_rows"], 0)
        self.assertEqual(result["qa"]["manifest_integrity"]["failed_checks"], 1)

    def test_manifest_integrity_counts_reconcile_distinct_rows(self) -> None:
        bad_row = _row(file_id="f1", sha="bad-sha")
        bad_row.pop("extension")

        result = run_m1_checks(
            _manifest([bad_row]),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 1},
        )

        self.assertEqual(_failure_ids(result), ["M1-KEYS", "M1-SHA"])
        self.assertEqual(result["qa"]["manifest_integrity"]["checked_rows"], 1)
        self.assertEqual(result["qa"]["manifest_integrity"]["failed_rows"], 1)
        self.assertEqual(result["qa"]["manifest_integrity"]["failed_checks"], 2)

    def test_output_never_emits_overall_ok(self) -> None:
        result = run_m1_checks(
            _manifest([_row(file_id="f1", sha=SHA_A)]),
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 1},
        )

        self.assertIn("qa", result)
        self.assertNotIn("overall_ok", result["qa"])
        self.assertEqual(set(result["qa"].keys()), {"manifest_integrity", "failures"})

    def test_billing_units_are_ignored(self) -> None:
        rows = [_row(file_id="f1", sha=SHA_A), _row(file_id="f2", sha=SHA_B)]
        manifest_a = _manifest(copy.deepcopy(rows), billing_units={"U": 999, "L": 123})
        manifest_b = _manifest(copy.deepcopy(rows), billing_units="not-used-by-m1")

        result_a = run_m1_checks(
            manifest_a,
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 2},
        )
        result_b = run_m1_checks(
            manifest_b,
            _job_record(sku="CLEAN-BASIC"),
            {"accepted_units": 2},
        )

        self.assertEqual(result_a, result_b)

    def test_m1_never_reads_envelope_or_filesystem(self) -> None:
        with patch("builtins.open", side_effect=AssertionError("filesystem access is not allowed")):
            result = run_m1_checks(
                _manifest([_row(file_id="f1", sha=SHA_A)]),
                _job_record(sku="CLEAN-BASIC"),
                {"accepted_units": 1},
            )

        self.assertTrue(result["qa"]["manifest_integrity"]["ok"])


if __name__ == "__main__":
    unittest.main()
