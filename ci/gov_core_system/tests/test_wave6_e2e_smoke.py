"""Minimal E2E smoke for Wave 6 envelope -> manifest -> QA-M1."""

from __future__ import annotations

from copy import deepcopy
import re
import unittest

from core.envelope_writer import FORBIDDEN_KEYS, SKU_BASIC, SKU_ENRICH, write_envelopes
from core.schemas.envelope_v2 import (
    ENRICHMENT_V0_1_SCHEMA_VERSION,
    BasicEnvelopeV2,
    EnrichEnvelopeV2,
)
from core.wave6_manifest_writer import write_manifest
from core.wave6_qa_manifest_m1 import run_m1_checks
from core.wave7_orch_pipeline_wire import run_wave6_pipeline
from core.wave7_report_summary_producer import build_summary_for_m1_checks, build_wave7_report

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64

_LEAKY_PATH_RE = re.compile(r"(?:^[a-zA-Z]:[\\/])|(?:://)|(?:^\\\\)")


def _basic_raw_file(
    *,
    file_id: str,
    sha: str,
    clean_status: str = "ok",
    stored_logical_path: str | None = None,
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
        "stored_logical_path": stored_logical_path or f"cleaned_full/{file_id}.py.json",
        "content_summary": {
            "line_count": 3,
            "char_count": 42,
            "imports": ["json"],
            "preview_lines": ["import json", "print('wave6')"],
        },
        "groq_used": False,
        "groq_reason": None,
        "parse_strategy": "ast",
        "warnings": [],
    }


def _present_enrichment(*, used_llm: bool = True, quality_score: int = 90) -> dict[str, object]:
    return {
        "schema_version": ENRICHMENT_V0_1_SCHEMA_VERSION,
        "present": True,
        "detected_language": "python",
        "domain_tags": ["backend"],
        "content_kind": "code",
        "quality_score": quality_score,
        "review_priority": "low" if quality_score >= 80 else "medium",
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
    stored_logical_path: str | None = None,
) -> dict[str, object]:
    payload = _basic_raw_file(
        file_id=file_id,
        sha=sha,
        clean_status=clean_status,
        stored_logical_path=stored_logical_path,
    )
    payload["groq_used"] = groq_used
    payload["groq_reason"] = groq_reason
    payload["enrichment"] = enrichment if enrichment is not None else _present_enrichment()
    return payload


def _qa_report_from_manifest(
    manifest: object,
    job_record: dict[str, object],
) -> dict[str, object]:
    return build_summary_for_m1_checks(manifest, job_record)


def _walk_keys(value: object) -> list[str]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(item))
        return keys
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_walk_keys(item))
        return out
    return []


def _assert_envelope_hygiene(
    test_case: unittest.TestCase,
    *,
    envelope: dict[str, object],
    sku: str,
) -> None:
    all_keys = set(_walk_keys(envelope))
    test_case.assertFalse(FORBIDDEN_KEYS & all_keys)
    test_case.assertNotIn("source_path", envelope)
    test_case.assertNotIn("stored_path", envelope)

    path = str(envelope.get("stored_logical_path", ""))
    test_case.assertFalse(_LEAKY_PATH_RE.search(path), msg=f"leaky path: {path!r}")

    if sku == SKU_BASIC:
        test_case.assertNotIn("enrichment", envelope)
        BasicEnvelopeV2.model_validate(envelope)
        return

    test_case.assertIn("enrichment", envelope)
    EnrichEnvelopeV2.model_validate(envelope)


def _failure_ids(result: dict[str, object]) -> list[str]:
    qa = result["qa"]
    failures = qa["failures"]
    return [item["check_id"] for item in failures]


class TestWave6E2ESmoke(unittest.TestCase):
    def test_basic_envelope_manifest_qa_smoke_passes(self) -> None:
        job_record = {"job_id": "wave6-e2e-basic-pass", "sku": SKU_BASIC}
        raw_files = [
            _basic_raw_file(file_id="ok-1", sha=SHA_A, clean_status="ok"),
            _basic_raw_file(file_id="reject-1", sha=SHA_B, clean_status="rejected"),
        ]

        envelopes = write_envelopes(job_record, raw_files)

        self.assertEqual(len(envelopes), 2)
        for envelope in envelopes:
            _assert_envelope_hygiene(self, envelope=envelope, sku=SKU_BASIC)
        self.assertIn("preview_lines", envelopes[0]["content_summary"])

        manifest = write_manifest(job_record, envelopes)

        self.assertEqual(manifest.accepted_units, 1)
        self.assertEqual(manifest.billing_units.U, 1)
        self.assertEqual(manifest.billing_units.L, 0)
        self.assertEqual(len(manifest.rows), 2)
        self.assertFalse(any("preview_lines" in row.content_summary.model_dump() for row in manifest.rows))

        summary = _qa_report_from_manifest(manifest, job_record)
        qa_out = run_m1_checks(manifest, job_record, summary)
        report_build = build_wave7_report(job_record, manifest.to_contract_dict(), qa_out)
        self.assertTrue(report_build["ok"])
        self.assertEqual(
            report_build["report"]["summary"]["accepted_units"],
            manifest.accepted_units,
        )

        self.assertEqual(set(qa_out.keys()), {"qa"})
        self.assertEqual(set(qa_out["qa"].keys()), {"manifest_integrity", "failures"})
        self.assertTrue(qa_out["qa"]["manifest_integrity"]["ok"])
        self.assertEqual(qa_out["qa"]["manifest_integrity"]["checked_rows"], 2)
        self.assertEqual(qa_out["qa"]["manifest_integrity"]["failed_rows"], 0)
        self.assertEqual(qa_out["qa"]["manifest_integrity"]["failed_checks"], 0)
        self.assertEqual(qa_out["qa"]["failures"], [])

    def test_basic_smoke_failure_emits_row_and_aggregate_failures(self) -> None:
        job_record = {"job_id": "wave6-e2e-basic-fail", "sku": SKU_BASIC}
        raw_files = [_basic_raw_file(file_id="ok-1", sha=SHA_A, clean_status="ok")]

        envelopes = write_envelopes(job_record, raw_files)
        manifest = write_manifest(job_record, envelopes)

        self.assertEqual(manifest.accepted_units, 1)
        self.assertEqual(manifest.billing_units.U, 1)
        self.assertEqual(manifest.billing_units.L, 0)

        qa_manifest = deepcopy(manifest.to_contract_dict())
        qa_manifest["rows"][0]["content_sha256"] = "bad-sha"

        bad_summary = _qa_report_from_manifest(manifest, job_record)
        bad_summary["accepted_units"] = manifest.accepted_units + 1
        qa_out = run_m1_checks(qa_manifest, job_record, bad_summary)

        self.assertFalse(qa_out["qa"]["manifest_integrity"]["ok"])
        self.assertEqual(qa_out["qa"]["manifest_integrity"]["checked_rows"], 1)
        self.assertEqual(qa_out["qa"]["manifest_integrity"]["failed_rows"], 1)
        self.assertEqual(qa_out["qa"]["manifest_integrity"]["failed_checks"], 3)

        failures = qa_out["qa"]["failures"]
        self.assertEqual(
            [failure["check_id"] for failure in failures],
            ["M1-SHA", "M1-OK-ONLY", "M1-COUNT"],
        )

        row_failure = failures[0]
        self.assertEqual(row_failure["file_id"], "ok-1")
        self.assertEqual(row_failure["stored_logical_path"], "cleaned_full/ok-1.py.json")
        self.assertEqual(row_failure["layer"], "M1")
        self.assertEqual(row_failure["severity"], "P0")

        aggregate_failure = failures[2]
        self.assertIsNone(aggregate_failure["file_id"])
        self.assertIsNone(aggregate_failure["content_sha256"])
        self.assertIsNone(aggregate_failure["stored_logical_path"])

    def test_wave6_e2e_enrich_and_duplicates(self) -> None:
        basic_job = {"job_id": "wave6-e2e-basic-mix", "sku": SKU_BASIC}
        basic_raw_files = [
            _basic_raw_file(file_id="basic-ok", sha=SHA_A, clean_status="ok"),
            _basic_raw_file(file_id="basic-reject", sha=SHA_B, clean_status="rejected"),
            _basic_raw_file(file_id="basic-dup-loser", sha=SHA_C, clean_status="parse_failed"),
            _basic_raw_file(file_id="basic-dup-winner", sha=SHA_C, clean_status="ok"),
        ]

        basic_envelopes = write_envelopes(basic_job, basic_raw_files)
        self.assertEqual(len(basic_envelopes), 4)
        for envelope in basic_envelopes:
            _assert_envelope_hygiene(self, envelope=envelope, sku=SKU_BASIC)

        basic_manifest = write_manifest(basic_job, basic_envelopes)
        self.assertEqual(len(basic_manifest.rows), 3)
        self.assertEqual({row.file_id for row in basic_manifest.rows}, {"basic-ok", "basic-reject", "basic-dup-winner"})
        self.assertEqual(basic_manifest.accepted_units, 2)
        self.assertEqual(basic_manifest.billing_units.U, 2)
        self.assertEqual(basic_manifest.billing_units.L, 0)

        basic_qa = run_m1_checks(
            basic_manifest,
            basic_job,
            _qa_report_from_manifest(basic_manifest, basic_job),
        )
        self.assertTrue(basic_qa["qa"]["manifest_integrity"]["ok"])
        self.assertEqual(basic_qa["qa"]["failures"], [])

        enrich_job = {"job_id": "wave6-e2e-enrich-mix", "sku": SKU_ENRICH}
        enrich_raw_files = [
            _enrich_raw_file(
                file_id="enrich-groq-ok",
                sha=SHA_A,
                groq_used=True,
                groq_reason="parse_failure_retry",
                enrichment=_present_enrichment(used_llm=True),
            ),
            _enrich_raw_file(
                file_id="enrich-plain-ok",
                sha=SHA_B,
                enrichment=_present_enrichment(used_llm=False, quality_score=75),
            ),
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
                enrichment=_present_enrichment(used_llm=True),
            ),
        ]

        enrich_envelopes = write_envelopes(enrich_job, enrich_raw_files)
        self.assertEqual(len(enrich_envelopes), 5)

        present_true = [item for item in enrich_envelopes if item["enrichment"]["present"] is True]
        present_false = [item for item in enrich_envelopes if item["enrichment"]["present"] is False]
        self.assertEqual(len(present_true), 3)
        self.assertEqual(len(present_false), 2)
        for envelope in enrich_envelopes:
            _assert_envelope_hygiene(self, envelope=envelope, sku=SKU_ENRICH)

        pipe = run_wave6_pipeline(enrich_job, enrich_raw_files)
        self.assertTrue(pipe["ok"], pipe.get("message"))
        enrich_manifest = pipe["manifest"]
        enrich_qa = pipe["qa"]

        self.assertEqual(len(enrich_manifest.rows), 4)
        self.assertEqual(
            {row.file_id for row in enrich_manifest.rows},
            {"enrich-groq-ok", "enrich-plain-ok", "enrich-reject-absent", "enrich-dup-winner"},
        )
        self.assertEqual(enrich_manifest.accepted_units, 3)
        self.assertEqual(enrich_manifest.billing_units.U, 3)
        self.assertEqual(enrich_manifest.billing_units.L, 2)

        ok_rows = [row for row in enrich_manifest.rows if row.clean_status == "ok"]
        self.assertTrue(all(row.has_enrichment for row in ok_rows))
        self.assertTrue(all(row.enrichment is not None for row in ok_rows))

        reject_row = next(row for row in enrich_manifest.rows if row.file_id == "enrich-reject-absent")
        self.assertEqual(reject_row.clean_status, "rejected")
        self.assertFalse(reject_row.has_enrichment)
        self.assertIsNone(reject_row.enrichment)

        self.assertTrue(enrich_qa["qa"]["manifest_integrity"]["ok"])
        self.assertEqual(enrich_qa["qa"]["manifest_integrity"]["checked_rows"], 4)
        self.assertEqual(enrich_qa["qa"]["failures"], [])

        report = pipe["report"]
        self.assertEqual(report["summary"]["accepted_units"], enrich_manifest.accepted_units)
        self.assertEqual(report["summary"]["billing_units"]["U"], 3)
        self.assertEqual(report["summary"]["billing_units"]["L"], 2)
        self.assertEqual(report["summary"]["qa_status"], "pass")
        self.assertFalse(report["summary"]["chargeable_hint"])

        corrupted_manifest = deepcopy(enrich_manifest.to_contract_dict())
        corrupted_rows = corrupted_manifest["rows"]

        corrupted_rows.append(deepcopy(corrupted_rows[0]))
        corrupted_rows[-1]["file_id"] = "enrich-dup-injected"

        corrupted_rows[1].pop("extension")
        corrupted_rows[2]["content_sha256"] = "not-a-valid-sha256"
        corrupted_rows[0]["has_enrichment"] = False

        qa_corrupt = run_m1_checks(
            corrupted_manifest,
            enrich_job,
            _qa_report_from_manifest(enrich_manifest, enrich_job),
        )

        self.assertFalse(qa_corrupt["qa"]["manifest_integrity"]["ok"])
        failure_ids = _failure_ids(qa_corrupt)
        self.assertIn("M1-DEDUP", failure_ids)
        self.assertIn("M1-KEYS", failure_ids)
        self.assertIn("M1-SHA", failure_ids)
        self.assertIn("M1-SKU-ENRICH", failure_ids)
        self.assertGreaterEqual(qa_corrupt["qa"]["manifest_integrity"]["failed_rows"], 3)
        self.assertGreaterEqual(qa_corrupt["qa"]["manifest_integrity"]["failed_checks"], 4)

        dedup_failure = next(item for item in qa_corrupt["qa"]["failures"] if item["check_id"] == "M1-DEDUP")
        self.assertEqual(dedup_failure["file_id"], "enrich-dup-injected")

        keys_failure = next(item for item in qa_corrupt["qa"]["failures"] if item["check_id"] == "M1-KEYS")
        self.assertEqual(keys_failure["file_id"], "enrich-plain-ok")
        self.assertIn("extension", keys_failure["message"])

        enrich_failure = next(item for item in qa_corrupt["qa"]["failures"] if item["check_id"] == "M1-SKU-ENRICH")
        self.assertEqual(enrich_failure["file_id"], "enrich-groq-ok")


if __name__ == "__main__":
    unittest.main()
