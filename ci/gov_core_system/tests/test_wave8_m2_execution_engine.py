"""Unit tests for Wave 8 M2 execution engine."""

from __future__ import annotations

import unittest
from pathlib import Path

from tests._repo_bootstrap import bootstrap_gov_core_tests

bootstrap_gov_core_tests(test_file=Path(__file__))

from core.envelope_writer import SKU_BASIC, SKU_ENRICH  # noqa: E402
from core.schemas.envelope_v2 import ENRICHMENT_V0_1_SCHEMA_VERSION  # noqa: E402
from core.wave8_m2_execution_engine import (  # noqa: E402
    recompute_quality_score,
    run_m2_checks,
)
from core.wave8_m2_sampling_design import build_sampling_plan  # noqa: E402

SHA_A = "a" * 64
SHA_B = "b" * 64


def _manifest_row(
    *,
    file_id: str,
    sha: str,
    stored_logical_path: str,
    extension: str = ".py",
) -> dict:
    return {
        "file_id": file_id,
        "content_sha256": sha,
        "clean_status": "ok",
        "extension": extension,
        "stored_logical_path": stored_logical_path,
        "schema_version": "2.0",
        "has_enrichment": False,
    }


def _basic_envelope(
    *,
    file_id: str = "f1",
    sha: str = SHA_A,
    stored_logical_path: str = "delivery/job/envelopes/f1.json",
) -> dict:
    return {
        "schema_version": "2.0",
        "file_id": file_id,
        "content_sha256": sha,
        "clean_status": "ok",
        "name": f"{file_id}.py",
        "extension": ".py",
        "original_type": "python_source",
        "size_bytes": 100,
        "encoding": "utf-8",
        "stored_logical_path": stored_logical_path,
        "content_summary": {
            "line_count": 5,
            "char_count": 120,
            "imports": [],
            "preview_lines": ["x = 1"],
        },
        "groq_used": False,
        "warnings": [],
        "parse_strategy": "ast",
    }


def _enrich_envelope(
    *,
    quality_score: int,
    stored_logical_path: str = "delivery/job/envelopes/e1.json",
    file_id: str = "e1",
    sha: str = SHA_A,
) -> dict:
    env = _basic_envelope(
        file_id=file_id,
        sha=sha,
        stored_logical_path=stored_logical_path,
    )
    env["groq_used"] = False
    env["enrichment"] = {
        "schema_version": ENRICHMENT_V0_1_SCHEMA_VERSION,
        "present": True,
        "detected_language": "en",
        "domain_tags": [],
        "content_kind": "code",
        "quality_score": quality_score,
        "review_priority": "low" if quality_score >= 80 else "medium",
        "enrichment_provenance": "rules",
        "signals": {
            "has_parse_warnings": False,
            "used_llm": False,
            "line_count": 5,
            "import_count": 0,
        },
    }
    return env


class TestRecomputeQualityScore(unittest.TestCase):
    def test_matches_present_enrichment_payload(self) -> None:
        env = _enrich_envelope(quality_score=0)
        env["enrichment"]["quality_score"] = recompute_quality_score(env)
        self.assertEqual(recompute_quality_score(env), 100)


class TestRunM2ChecksHappyPath(unittest.TestCase):
    def test_basic_sample_all_pass(self) -> None:
        rows = [
            _manifest_row(
                file_id="f1",
                sha=SHA_A,
                stored_logical_path="delivery/job/envelopes/f1.json",
            ),
            _manifest_row(
                file_id="f2",
                sha=SHA_B,
                stored_logical_path="delivery/job/envelopes/f2.json",
            ),
        ]
        envelopes = {
            rows[0]["stored_logical_path"]: _basic_envelope(
                file_id="f1", sha=SHA_A, stored_logical_path=rows[0]["stored_logical_path"]
            ),
            rows[1]["stored_logical_path"]: _basic_envelope(
                file_id="f2",
                sha=SHA_B,
                stored_logical_path=rows[1]["stored_logical_path"],
            ),
        }
        plan = build_sampling_plan(len(rows))
        out = run_m2_checks(
            rows,
            plan,
            job_record={"job_id": "j-happy", "sku": SKU_BASIC},
            envelope_loader=lambda ref: envelopes.get(ref),
        )

        self.assertTrue(out["ok"])
        self.assertEqual(out["sample_validation"]["status"], "completed")
        self.assertTrue(out["sample_validation"]["ok"])
        self.assertEqual(out["sample_validation"]["failed_checks"], 0)
        self.assertEqual(out["failures"], [])


class TestRunM2ChecksFailures(unittest.TestCase):
    def test_missing_envelope_is_p0(self) -> None:
        row = _manifest_row(
            file_id="missing",
            sha=SHA_A,
            stored_logical_path="delivery/job/envelopes/missing.json",
        )
        plan = build_sampling_plan(1)
        out = run_m2_checks(
            [row],
            plan,
            job_record={"job_id": "j-miss", "sku": SKU_BASIC},
            envelope_loader=lambda _ref: None,
        )

        self.assertFalse(out["ok"])
        self.assertEqual(out["sample_validation"]["status"], "completed")
        self.assertFalse(out["sample_validation"]["ok"])
        self.assertEqual(len(out["failures"]), 1)
        failure = out["failures"][0]
        self.assertEqual(failure["layer"], "M2")
        self.assertEqual(failure["severity"], "P0")
        self.assertEqual(failure["check_id"], "M2-SCHEMA-20")
        self.assertEqual(failure["content_sha256"], SHA_A)

    def test_enrich_quality_mismatch_is_p1(self) -> None:
        path = "delivery/job/envelopes/e1.json"
        row = _manifest_row(file_id="e1", sha=SHA_A, stored_logical_path=path)
        row["has_enrichment"] = True
        env = _enrich_envelope(quality_score=50, stored_logical_path=path)
        expected = recompute_quality_score(env)
        self.assertNotEqual(50, expected)

        plan = build_sampling_plan(1)
        out = run_m2_checks(
            [row],
            plan,
            job_record={"job_id": "j-p1", "sku": SKU_ENRICH},
            envelope_loader=lambda _ref: env,
        )

        self.assertFalse(out["ok"])
        p1 = [f for f in out["failures"] if f["check_id"] == "M2-QUALITY"]
        self.assertEqual(len(p1), 1)
        self.assertEqual(p1[0]["severity"], "P1")


class TestRunM2ChecksSkipPaths(unittest.TestCase):
    def test_n_zero_skipped_no_io(self) -> None:
        plan = build_sampling_plan(0)
        loader_calls: list[str] = []

        def _loader(ref: str) -> None:
            loader_calls.append(ref)
            return None

        out = run_m2_checks(
            [],
            plan,
            job_record={"job_id": "j-empty", "sku": SKU_BASIC},
            envelope_loader=_loader,
        )

        self.assertTrue(out["ok"])
        self.assertEqual(out["sample_validation"]["status"], "skipped")
        self.assertEqual(out["sample_validation"]["reason"], "no_sample")
        self.assertEqual(loader_calls, [])
        self.assertEqual(out["failures"], [])

    def test_m1_failed_skipped_no_io(self) -> None:
        row = _manifest_row(
            file_id="f1",
            sha=SHA_A,
            stored_logical_path="delivery/job/envelopes/f1.json",
        )
        plan = build_sampling_plan(1)
        loader_calls: list[str] = []

        out = run_m2_checks(
            [row],
            plan,
            job_record={"job_id": "j-m1", "sku": SKU_BASIC},
            envelope_loader=lambda ref: loader_calls.append(ref) or None,
            manifest_integrity_ok=False,
        )

        self.assertTrue(out["ok"])
        self.assertEqual(out["sample_validation"]["status"], "skipped")
        self.assertEqual(out["sample_validation"]["reason"], "m1_failed")
        self.assertEqual(loader_calls, [])
        self.assertEqual(out["failures"], [])


if __name__ == "__main__":
    unittest.main()
