"""Unit tests for the Wave 6 manifest writer."""

from __future__ import annotations

import unittest

from core.wave6_manifest_writer import write_manifest

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64


def _summary(*, chars: int = 120, lines: int = 10, imports: list[str] | None = None) -> dict:
    return {
        "char_count": chars,
        "line_count": lines,
        "imports": imports or ["os"],
    }


def _enrichment(*, quality_score: int = 90) -> dict:
    return {
        "schema_version": "enrichment_v0.1",
        "detected_language": "python",
        "domain_tags": ["backend"],
        "content_kind": "code",
        "quality_score": quality_score,
        "review_priority": "low" if quality_score >= 80 else "medium",
        "enrichment_provenance": "llm",
        "signals": {
            "has_parse_warnings": False,
            "used_llm": True,
            "line_count": 10,
            "import_count": 1,
        },
    }


def _row(
    *,
    file_id: str,
    sha: str,
    clean_status: str = "ok",
    stored_logical_path: str | None = None,
    groq_used: bool = False,
    groq_reason: str | None = None,
    enrichment: dict | None = None,
    schema_version: str = "2.0",
) -> dict:
    return {
        "file_id": file_id,
        "name": f"{file_id}.py",
        "extension": ".py",
        "original_type": "python_source",
        "size_bytes": 128,
        "encoding": "utf-8",
        "content_sha256": sha,
        "schema_version": schema_version,
        "clean_status": clean_status,
        "stored_logical_path": stored_logical_path or f"deliverables/{file_id}.json",
        "parse_strategy": "ast",
        "warnings": [],
        "content_summary": _summary(),
        "groq_used": groq_used,
        "groq_reason": groq_reason,
        "enrichment": enrichment,
    }


class TestWave6ManifestWriter(unittest.TestCase):
    def test_basic_pure_job_counts_accepted_and_billable_u(self) -> None:
        manifest = write_manifest(
            {"job_id": "job-basic-001", "sku": "CLEAN-BASIC"},
            [
                _row(file_id="f1", sha=SHA_A),
                _row(file_id="f2", sha=SHA_B),
            ],
            {"billing_table_version": "w6_billing_v0.1"},
        )

        self.assertEqual(manifest.accepted_units, 2)
        self.assertEqual(manifest.billing_units.U, 2)
        self.assertEqual(manifest.billing_units.L, 0)
        self.assertEqual(len(manifest.rows), 2)
        dumped = manifest.to_contract_dict()
        self.assertNotIn("enrichment", dumped["rows"][0])
        self.assertFalse(dumped["rows"][0]["has_enrichment"])

    def test_basic_groq_violation_excludes_row_from_billable_u(self) -> None:
        manifest = write_manifest(
            {"job_id": "job-basic-002", "sku": "CLEAN-BASIC"},
            [
                _row(file_id="f1", sha=SHA_A, groq_used=True, groq_reason="llm_assist"),
                _row(file_id="f2", sha=SHA_B),
            ],
        )

        self.assertEqual(manifest.accepted_units, 2)
        self.assertEqual(manifest.billing_units.U, 1)
        self.assertEqual(manifest.billing_units.L, 0)
        self.assertTrue(manifest.rows[0].groq_used)

    def test_duplicate_sha_keeps_best_candidate_and_dedupes_output(self) -> None:
        manifest = write_manifest(
            {"job_id": "job-basic-003", "sku": "CLEAN-BASIC"},
            [
                _row(file_id="dup-fail", sha=SHA_C, clean_status="failed"),
                _row(file_id="dup-ok", sha=SHA_C, clean_status="ok"),
                _row(file_id="unique-ok", sha=SHA_D, clean_status="ok"),
            ],
        )

        self.assertEqual(len(manifest.rows), 2)
        self.assertEqual({row.file_id for row in manifest.rows}, {"dup-ok", "unique-ok"})
        self.assertEqual(manifest.accepted_units, 2)
        self.assertEqual(manifest.billing_units.U, 2)

    def test_enrich_normal_counts_u_and_l(self) -> None:
        manifest = write_manifest(
            {"job_id": "job-enrich-001", "sku": "CLEAN-ENRICH"},
            [
                _row(file_id="f1", sha=SHA_A, groq_used=True, groq_reason="parse_failure_retry", enrichment=_enrichment()),
                _row(file_id="f2", sha=SHA_B, enrichment=_enrichment(quality_score=75)),
            ],
        )

        self.assertEqual(manifest.accepted_units, 2)
        self.assertEqual(manifest.billing_units.U, 2)
        self.assertEqual(manifest.billing_units.L, 1)
        self.assertTrue(all(row.has_enrichment for row in manifest.rows))
        self.assertTrue(all(row.enrichment is not None for row in manifest.rows))

    def test_enrich_missing_enrichment_block_is_not_billable_u(self) -> None:
        manifest = write_manifest(
            {"job_id": "job-enrich-002", "sku": "CLEAN-ENRICH"},
            [
                _row(file_id="f1", sha=SHA_E, enrichment=None),
            ],
        )

        self.assertEqual(manifest.accepted_units, 1)
        self.assertEqual(manifest.billing_units.U, 0)
        self.assertEqual(manifest.billing_units.L, 0)
        self.assertFalse(manifest.rows[0].has_enrichment)


if __name__ == "__main__":
    unittest.main()
