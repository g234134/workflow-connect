"""Unit tests for Wave 7 orchestrator pipeline wire (Wave 6 in-memory chain)."""

from __future__ import annotations

from copy import deepcopy
import unittest
from pathlib import Path

from tests._repo_bootstrap import bootstrap_gov_core_tests

bootstrap_gov_core_tests(test_file=Path(__file__))

from core.envelope_writer import SKU_BASIC, SKU_ENRICH  # noqa: E402
from core.schemas.envelope_v2 import ENRICHMENT_V0_1_SCHEMA_VERSION  # noqa: E402
from core.wave7_orch_pipeline_wire import (  # noqa: E402
    ERR_ENVELOPE,
    STAGE_ENVELOPE,
    STAGE_MANIFEST,
    build_qa_report_stub_bridge,
    normalize_envelope_for_manifest,
    run_wave6_pipeline,
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
) -> dict[str, object]:
    payload = _basic_raw_file(file_id=file_id, sha=sha, clean_status=clean_status)
    payload["groq_used"] = groq_used
    payload["groq_reason"] = groq_reason
    payload["enrichment"] = enrichment if enrichment is not None else _present_enrichment()
    return payload


class TestNormalizeEnvelopeForManifest(unittest.TestCase):
    def test_present_true_strips_present_key(self) -> None:
        env = {"file_id": "x", "enrichment": {"present": True, "detected_language": "py", "extra": 1}}
        out = normalize_envelope_for_manifest(env)
        self.assertNotIn("present", out["enrichment"])
        self.assertEqual(out["enrichment"]["detected_language"], "py")

    def test_present_false_drops_enrichment(self) -> None:
        env = {"file_id": "x", "enrichment": {"present": False, "domain_tags": []}}
        out = normalize_envelope_for_manifest(env)
        self.assertNotIn("enrichment", out)


class TestWave7OrchPipelineWire(unittest.TestCase):
    def test_basic_happy_path_matches_e2e_smoke(self) -> None:
        job_record = {"job_id": "w7-pipe-basic-pass", "sku": SKU_BASIC}
        raw_files = [
            _basic_raw_file(file_id="ok-1", sha=SHA_A, clean_status="ok"),
            _basic_raw_file(file_id="reject-1", sha=SHA_B, clean_status="rejected"),
        ]

        out = run_wave6_pipeline(job_record, raw_files)

        self.assertTrue(out["ok"])
        self.assertIsNone(out["error_code"])
        self.assertEqual(len(out["envelopes"]), 2)
        manifest = out["manifest"]
        self.assertEqual(manifest.accepted_units, 1)
        self.assertEqual(manifest.billing_units.U, 1)
        self.assertEqual(manifest.billing_units.L, 0)
        self.assertEqual(len(manifest.rows), 2)

        qa = out["qa"]["qa"]
        self.assertTrue(qa["manifest_integrity"]["ok"])
        self.assertEqual(qa["failures"], [])

        report = out["report"]
        self.assertEqual(report["summary"]["accepted_units"], manifest.accepted_units)
        self.assertEqual(report["summary"]["qa_status"], "pass")
        self.assertFalse(report["summary"]["chargeable_hint"])

    def test_enrich_present_true_false_normalization_via_pipeline(self) -> None:
        job_record = {"job_id": "w7-pipe-enrich-mix", "sku": SKU_ENRICH}
        raw_files = [
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

        out = run_wave6_pipeline(job_record, raw_files)
        self.assertTrue(out["ok"])

        present_true = [
            item for item in out["envelopes"] if item["enrichment"]["present"] is True
        ]
        present_false = [
            item for item in out["envelopes"] if item["enrichment"]["present"] is False
        ]
        self.assertEqual(len(present_true), 3)
        self.assertEqual(len(present_false), 2)

        manifest = out["manifest"]
        self.assertEqual(len(manifest.rows), 4)
        self.assertEqual(
            {row.file_id for row in manifest.rows},
            {"enrich-groq-ok", "enrich-plain-ok", "enrich-reject-absent", "enrich-dup-winner"},
        )
        self.assertEqual(manifest.accepted_units, 3)
        self.assertEqual(manifest.billing_units.U, 3)
        self.assertEqual(manifest.billing_units.L, 2)

        reject_row = next(
            row for row in manifest.rows if row.file_id == "enrich-reject-absent"
        )
        self.assertEqual(reject_row.clean_status, "rejected")
        self.assertFalse(reject_row.has_enrichment)
        self.assertIsNone(reject_row.enrichment)

        ok_rows = [row for row in manifest.rows if row.clean_status == "ok"]
        self.assertTrue(all(row.has_enrichment for row in ok_rows))
        self.assertTrue(all(row.enrichment is not None for row in ok_rows))

        self.assertTrue(out["qa"]["qa"]["manifest_integrity"]["ok"])

    def test_basic_duplicate_sha_behavior_matches_e2e(self) -> None:
        job_record = {"job_id": "w7-pipe-basic-dedup", "sku": SKU_BASIC}
        raw_files = [
            _basic_raw_file(file_id="basic-ok", sha=SHA_A, clean_status="ok"),
            _basic_raw_file(file_id="basic-reject", sha=SHA_B, clean_status="rejected"),
            _basic_raw_file(file_id="basic-dup-loser", sha=SHA_C, clean_status="parse_failed"),
            _basic_raw_file(file_id="basic-dup-winner", sha=SHA_C, clean_status="ok"),
        ]

        out = run_wave6_pipeline(job_record, raw_files)
        self.assertTrue(out["ok"])
        manifest = out["manifest"]
        self.assertEqual(len(manifest.rows), 3)
        self.assertEqual(
            {row.file_id for row in manifest.rows},
            {"basic-ok", "basic-reject", "basic-dup-winner"},
        )
        self.assertEqual(manifest.accepted_units, 2)
        self.assertEqual(manifest.billing_units.U, 2)

    def test_qa_stub_bridge_m1_count_mismatch_surfaces_in_qa_not_stage_fail(self) -> None:
        job_record = {"job_id": "w7-pipe-qa-count", "sku": SKU_BASIC}
        raw_files = [_basic_raw_file(file_id="ok-1", sha=SHA_A)]

        out = run_wave6_pipeline(
            job_record,
            raw_files,
            qa_report_stub=build_qa_report_stub_bridge(accepted_units=99),
        )
        self.assertTrue(out["ok"])
        self.assertFalse(out["qa"]["qa"]["manifest_integrity"]["ok"])
        failure_ids = [f["check_id"] for f in out["qa"]["qa"]["failures"]]
        self.assertIn("M1-COUNT", failure_ids)

    def test_envelope_stage_failure_returns_stage_and_error_code(self) -> None:
        job_record = {"job_id": "w7-pipe-bad-sku", "sku": "CLEAN-UNKNOWN"}
        raw_files = [_basic_raw_file(file_id="ok-1", sha=SHA_A)]

        out = run_wave6_pipeline(job_record, raw_files)

        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], STAGE_ENVELOPE)
        self.assertEqual(out["error_code"], ERR_ENVELOPE)
        self.assertIsNone(out["manifest"])
        self.assertIsNone(out["qa"])
        self.assertIn("unsupported sku", out["message"])

    def test_manifest_stage_failure_invalid_job_record(self) -> None:
        job_record = {"sku": SKU_BASIC}
        raw_files = [_basic_raw_file(file_id="ok-1", sha=SHA_A)]

        out = run_wave6_pipeline(job_record, raw_files)

        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], STAGE_MANIFEST)
        self.assertIsNotNone(out["envelopes"])
        self.assertIsNone(out["qa"])

    def test_basic_envelope_rejects_billing_truth_fields(self) -> None:
        job_record = {"job_id": "w7-pipe-forbidden", "sku": SKU_BASIC}
        raw = _basic_raw_file(file_id="ok-1", sha=SHA_A)
        raw["billable_u"] = 1

        out = run_wave6_pipeline(job_record, [raw])

        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], STAGE_ENVELOPE)
        self.assertIn("billing truth", out["message"])


class TestPipelineWireVsManualQaCorruption(unittest.TestCase):
    """Ensure pipeline output matches manual QA on corrupted manifest (post-pipeline)."""

    def test_corrupted_manifest_qa_failures_match_e2e(self) -> None:
        from core.wave6_qa_manifest_m1 import run_m1_checks

        job_record = {"job_id": "w7-pipe-enrich-corrupt", "sku": SKU_ENRICH}
        raw_files = [
            _enrich_raw_file(file_id="enrich-groq-ok", sha=SHA_A, groq_used=True, groq_reason="x"),
            _enrich_raw_file(file_id="enrich-plain-ok", sha=SHA_B),
            _enrich_raw_file(
                file_id="enrich-reject-absent",
                sha=SHA_D,
                clean_status="rejected",
                enrichment=_absent_enrichment(),
            ),
        ]

        out = run_wave6_pipeline(job_record, raw_files)
        self.assertTrue(out["ok"])
        manifest = out["manifest"]

        corrupted = deepcopy(manifest.to_contract_dict())
        rows = corrupted["rows"]
        rows.append(deepcopy(rows[0]))
        rows[-1]["file_id"] = "enrich-dup-injected"
        rows[1].pop("extension")
        rows[2]["content_sha256"] = "not-a-valid-sha256"
        rows[0]["has_enrichment"] = False

        from core.wave7_report_summary_producer import build_summary_for_m1_checks

        qa_corrupt = run_m1_checks(
            corrupted,
            job_record,
            build_summary_for_m1_checks(manifest, job_record),
        )
        failure_ids = [item["check_id"] for item in qa_corrupt["qa"]["failures"]]
        self.assertIn("M1-DEDUP", failure_ids)
        self.assertIn("M1-KEYS", failure_ids)
        self.assertIn("M1-SHA", failure_ids)
        self.assertIn("M1-SKU-ENRICH", failure_ids)


if __name__ == "__main__":
    unittest.main()
