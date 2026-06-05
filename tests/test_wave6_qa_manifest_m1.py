"""Unit tests for Wave 6 manifest-integrity gate (M1 only)."""

from __future__ import annotations

from unittest import mock
import unittest

from wave6.qa_manifest_m1 import run_m1_checks


def _sha(seed: str) -> str:
    return (seed * 64)[:64]


def _row(
    *,
    file_id: str = "file-1",
    content_sha256: str = _sha("a"),
    clean_status: str = "ok",
    extension: str = ".json",
    stored_logical_path: str = "clean/file-1.json",
    schema_version: str = "1.0",
    **extra: object,
) -> dict[str, object]:
    row = {
        "file_id": file_id,
        "content_sha256": content_sha256,
        "clean_status": clean_status,
        "extension": extension,
        "stored_logical_path": stored_logical_path,
        "schema_version": schema_version,
        "billing_units": 999,  # Must be ignored by M1.
    }
    row.update(extra)
    return row


def _run(
    manifest_rows: list[dict[str, object]],
    *,
    sku: str = "CLEAN-BASIC",
    accepted_units: int | str = 0,
    **job_extras: object,
) -> dict[str, object]:
    job_record = {"sku": sku, **job_extras}
    report = {
        "summary": {
            "accepted_units": accepted_units,
            "billing_units": 12345,  # Must be ignored by M1.
        }
    }
    return run_m1_checks(manifest_rows, job_record, report)


class TestWave6QaManifestM1(unittest.TestCase):
    def test_m1_keys_pass_minimal_row(self) -> None:
        out = _run([_row()], accepted_units=1)

        self.assertTrue(out["qa"]["manifest_integrity"]["ok"])
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_checks"], 0)
        self.assertEqual(out["qa"]["failures"], [])

    def test_m1_keys_fail_missing_required_key(self) -> None:
        row = _row()
        del row["schema_version"]

        out = _run([row], accepted_units=1)
        failure = out["qa"]["failures"][0]

        self.assertEqual(failure["check_id"], "M1-KEYS")
        self.assertIn("schema_version", failure["message"])
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_rows"], 1)

    def test_m1_sha_pass_valid_hex64(self) -> None:
        out = _run([_row(content_sha256=_sha("b"))], accepted_units=1)

        check_ids = [failure["check_id"] for failure in out["qa"]["failures"]]
        self.assertNotIn("M1-SHA", check_ids)
        self.assertTrue(out["qa"]["manifest_integrity"]["ok"])

    def test_m1_sha_fail_non_hex_or_wrong_length(self) -> None:
        out = _run([_row(content_sha256="not-a-valid-sha")], accepted_units=1)

        self.assertEqual(out["qa"]["failures"][0]["check_id"], "M1-SHA")
        self.assertFalse(out["qa"]["manifest_integrity"]["ok"])

    def test_m1_ok_only_pass_counts_only_clean_status_ok_via_m1_count(self) -> None:
        rows = [
            _row(file_id="ok-1", content_sha256=_sha("a"), clean_status="ok"),
            _row(file_id="skip-1", content_sha256=_sha("b"), clean_status="rejected"),
        ]

        out = _run(rows, accepted_units=1)
        check_ids = [failure["check_id"] for failure in out["qa"]["failures"]]

        self.assertTrue(out["qa"]["manifest_integrity"]["ok"])
        self.assertNotIn("M1-COUNT", check_ids)
        self.assertNotIn("M1-OK-ONLY", check_ids)

    def test_m1_ok_only_fail_when_non_ok_rows_are_counted_via_m1_count(self) -> None:
        rows = [
            _row(file_id="ok-1", content_sha256=_sha("a"), clean_status="ok"),
            _row(file_id="skip-1", content_sha256=_sha("b"), clean_status="error"),
        ]

        out = _run(rows, accepted_units=2)
        failures = out["qa"]["failures"]

        self.assertEqual([failure["check_id"] for failure in failures], ["M1-COUNT"])
        self.assertIsNone(failures[0]["file_id"])
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_rows"], 0)

    def test_m1_sku_basic_pass_without_enrichment_key(self) -> None:
        out = _run([_row()], sku="CLEAN-BASIC", accepted_units=1)

        check_ids = [failure["check_id"] for failure in out["qa"]["failures"]]
        self.assertNotIn("M1-SKU-BASIC", check_ids)
        self.assertTrue(out["qa"]["manifest_integrity"]["ok"])

    def test_m1_sku_basic_rejects_enrichment_key(self) -> None:
        out = _run(
            [_row(enrichment={"schema_version": "enrich-1"})],
            sku="CLEAN-BASIC",
            accepted_units=1,
        )

        self.assertEqual(out["qa"]["failures"][0]["check_id"], "M1-SKU-BASIC")
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_rows"], 1)

    def test_m1_sku_enrich_pass_with_has_enrichment_true(self) -> None:
        out = _run(
            [_row(has_enrichment=True)],
            sku="CLEAN-ENRICH",
            accepted_units=1,
        )

        check_ids = [failure["check_id"] for failure in out["qa"]["failures"]]
        self.assertNotIn("M1-SKU-ENRICH", check_ids)
        self.assertTrue(out["qa"]["manifest_integrity"]["ok"])

    def test_m1_sku_enrich_requires_has_enrichment_true(self) -> None:
        out = _run(
            [_row(has_enrichment=False)],
            sku="CLEAN-ENRICH",
            accepted_units=1,
        )

        self.assertEqual(out["qa"]["failures"][0]["check_id"], "M1-SKU-ENRICH")
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_rows"], 1)

    def test_m1_dedup_pass_unique_sha(self) -> None:
        rows = [
            _row(file_id="file-1", content_sha256=_sha("a")),
            _row(file_id="file-2", content_sha256=_sha("b"), stored_logical_path="clean/file-2.json"),
        ]

        out = _run(rows, accepted_units=2)
        check_ids = [failure["check_id"] for failure in out["qa"]["failures"]]

        self.assertNotIn("M1-DEDUP", check_ids)
        self.assertTrue(out["qa"]["manifest_integrity"]["ok"])

    def test_m1_dedup_flags_duplicate_sha_after_first_row(self) -> None:
        rows = [
            _row(file_id="file-1", content_sha256=_sha("a"), stored_logical_path="clean/file-1.json"),
            _row(file_id="file-2", content_sha256=_sha("A"), stored_logical_path="clean/file-2.json"),
        ]

        out = _run(rows, accepted_units=2)

        self.assertEqual(out["qa"]["failures"][0]["check_id"], "M1-DEDUP")
        self.assertEqual(out["qa"]["failures"][0]["file_id"], "file-2")
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_rows"], 1)

    def test_m1_count_pass_matches_report_summary_accepted_units(self) -> None:
        rows = [
            _row(file_id="file-1", content_sha256=_sha("a")),
            _row(file_id="file-2", content_sha256=_sha("b"), clean_status="error"),
        ]

        out = _run(rows, accepted_units=1)
        check_ids = [failure["check_id"] for failure in out["qa"]["failures"]]

        self.assertNotIn("M1-COUNT", check_ids)
        self.assertTrue(out["qa"]["manifest_integrity"]["ok"])

    def test_m1_count_fail_mismatch_emits_aggregate_failure(self) -> None:
        out = _run([_row(file_id="file-1", content_sha256=_sha("a"))], accepted_units=0)

        self.assertEqual(out["qa"]["failures"][0]["check_id"], "M1-COUNT")
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_checks"], 1)
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_rows"], 0)

    def test_manifest_integrity_counts_reconcile(self) -> None:
        rows = [
            _row(file_id="file-1", content_sha256="bad-sha"),
            _row(file_id="file-2", content_sha256=_sha("a"), enrichment={"x": 1}),
            _row(file_id="file-3", content_sha256=_sha("A")),
        ]

        out = _run(rows, accepted_units=1)

        self.assertEqual(out["qa"]["manifest_integrity"]["checked_rows"], 3)
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_rows"], 3)
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_checks"], 4)
        self.assertEqual(
            [failure["check_id"] for failure in out["qa"]["failures"]],
            ["M1-SHA", "M1-SKU-BASIC", "M1-DEDUP", "M1-COUNT"],
        )

    def test_m1_never_emits_overall_ok(self) -> None:
        out = _run([_row()], accepted_units=1)

        self.assertIn("qa", out)
        self.assertEqual(set(out["qa"].keys()), {"manifest_integrity", "failures"})
        self.assertNotIn("overall_ok", out["qa"])

    def test_m1_never_reads_envelope_or_filesystem(self) -> None:
        with mock.patch("builtins.open", side_effect=AssertionError("filesystem access is forbidden")):
            out = _run(
                [_row()],
                accepted_units=1,
                deliverables={"envelope_path": "deliverables/file-1.json"},
            )

        self.assertTrue(out["qa"]["manifest_integrity"]["ok"])

    def test_aggregate_failure_does_not_inflate_failed_rows(self) -> None:
        out = _run([_row(file_id="file-1", content_sha256=_sha("a"))], accepted_units=3)

        self.assertEqual(out["qa"]["manifest_integrity"]["failed_checks"], 1)
        self.assertEqual(out["qa"]["manifest_integrity"]["failed_rows"], 0)
        self.assertEqual(out["qa"]["failures"][0]["check_id"], "M1-COUNT")

    def test_failure_record_shape_is_stable(self) -> None:
        row = _row(content_sha256="bad-sha")

        out = _run([row], accepted_units=1)
        failure = out["qa"]["failures"][0]

        self.assertEqual(
            list(failure.keys()),
            [
                "layer",
                "check_id",
                "severity",
                "file_id",
                "content_sha256",
                "stored_logical_path",
                "message",
                "remediation_hint",
            ],
        )
        self.assertEqual(failure["layer"], "M1")
        self.assertEqual(failure["severity"], "P0")


if __name__ == "__main__":
    unittest.main()
