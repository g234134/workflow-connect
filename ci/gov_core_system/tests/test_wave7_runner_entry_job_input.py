"""Unit tests for Wave 7 runner entry job input (RUNNER-ENTRY-JOB-INPUT)."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from core.envelope_writer import SKU_BASIC, SKU_ENRICH, FORBIDDEN_DELIVERY_PATH_KEYS
from core.schemas.envelope_v2 import ENRICHMENT_V0_1_SCHEMA_VERSION, _LEAKY_PATH_RE
from core.wave7_runner_entry_job_input import (
    ERR_EMPTY_BATCH,
    ERR_INTAKE_DEFER,
    ERR_INTAKE_REJECT,
    ERR_MISSING_SHA256,
    ERR_SKU_INTAKE_MISMATCH,
    ERR_UNKNOWN_SKU,
    build_runner_job_from_queue_file,
    build_runner_job_input,
    map_cleaned_record_to_raw_file,
    to_logical_path,
)

SHA_A = "a" * 64
SHA_B = "b" * 64


def _cleaned_record(
    *,
    file_id: str = "demo-1",
    sha: str = SHA_A,
    source_path: str | None = None,
    stored_path: str | None = None,
    stored_logical_path: str | None = None,
    with_enrichment: bool = False,
) -> dict:
    rec: dict = {
        "file_id": file_id,
        "content_sha256": sha,
        "clean_status": "ok",
        "name": f"{file_id}.py",
        "extension": ".py",
        "original_type": "python_source",
        "size_bytes": 100,
        "encoding": "utf-8",
        "content_summary": {
            "line_count": 2,
            "char_count": 20,
            "imports": [],
            "preview_lines": ["x = 1"],
        },
        "groq_used": False,
        "parse_strategy": "ast",
        "warnings": [],
    }
    if stored_logical_path:
        rec["stored_logical_path"] = stored_logical_path
    if source_path:
        rec["source_path"] = source_path
    if stored_path:
        rec["stored_path"] = stored_path
    if with_enrichment:
        rec["enrichment"] = {
            "schema_version": ENRICHMENT_V0_1_SCHEMA_VERSION,
            "present": True,
            "detected_language": "en",
            "domain_tags": ["python"],
            "content_kind": "code",
            "quality_score": 88,
            "review_priority": "low",
            "enrichment_provenance": "rules",
            "signals": {
                "has_parse_warnings": False,
                "used_llm": False,
                "line_count": 2,
                "import_count": 0,
            },
        }
    return rec


def _intake_accept_basic() -> dict:
    return {
        "description": "raw_inbound 碼源清洗 wave factory cleaned_full envelope",
        "tags": ["raw_inbound", "size_policy:acknowledged"],
        "explicit_task_type": "chariot.factory",
        "product_sku": "CLEAN-BASIC",
        "client_ref": "client-wave7-001",
        "inbound_path_hint": "raw_inbound/batch-42",
    }


class TestLogicalPathMapping(unittest.TestCase):
    def test_absolute_source_path_maps_to_cleaned_full(self) -> None:
        logical = to_logical_path(r"D:\agent\05_Temp_Cache\cleaned_full\demo.py.json")
        self.assertEqual(logical, "cleaned_full/demo.py.json")
        self.assertIsNone(_LEAKY_PATH_RE.search(logical or ""))

    def test_stored_path_wins_over_source_path(self) -> None:
        logical = to_logical_path(
            "raw_inbound/old.py",
            "cleaned_full/new.py.json",
        )
        self.assertEqual(logical, "cleaned_full/new.py.json")


class TestMapCleanedRecord(unittest.TestCase):
    def test_strips_legacy_path_keys(self) -> None:
        rec = _cleaned_record(
            source_path=r"C:\secrets\raw_inbound\demo.py",
            stored_path=r"C:\secrets\cleaned_full\demo.py.json",
        )
        raw, skip = map_cleaned_record_to_raw_file(rec, sku=SKU_BASIC, source_hint="demo.py.json")
        self.assertIsNone(skip)
        assert raw is not None
        for key in FORBIDDEN_DELIVERY_PATH_KEYS:
            self.assertNotIn(key, raw)
        self.assertEqual(raw["stored_logical_path"], "cleaned_full/demo.py.json")

    def test_missing_sha256_skips(self) -> None:
        rec = _cleaned_record(sha="")
        del rec["content_sha256"]
        _raw, skip = map_cleaned_record_to_raw_file(rec, sku=SKU_BASIC)
        self.assertIsNotNone(skip)
        assert skip is not None
        self.assertEqual(skip["error_code"], ERR_MISSING_SHA256)


class TestBuildRunnerJobInput(unittest.TestCase):
    def test_cli_cleaned_dir_scan_basic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpha.py.json").write_text(
                json.dumps(_cleaned_record(file_id="alpha", sha=SHA_A)),
                encoding="utf-8",
            )
            (root / "beta.py.json").write_text(
                json.dumps(_cleaned_record(file_id="beta", sha=SHA_B)),
                encoding="utf-8",
            )
            (root / "skip.py.json").write_text(
                json.dumps({"file_id": "skip", "name": "skip.py"}),
                encoding="utf-8",
            )

            out = build_runner_job_input(
                sku=SKU_BASIC,
                client_ref="cli-client-1",
                cleaned_dir=root,
                job_id="wave7-cli-job-001",
            )

        self.assertTrue(out["ok"])
        self.assertEqual(out["input_count"], 2)
        self.assertEqual(out["job_record"]["job_id"], "wave7-cli-job-001")
        self.assertEqual(out["job_record"]["sku"], SKU_BASIC)
        self.assertEqual(out["job_record"]["client_ref"], "cli-client-1")
        self.assertRegex(out["job_record"]["created_at"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertEqual(len(out["skipped"]), 1)
        self.assertEqual(out["skipped"][0]["error_code"], ERR_MISSING_SHA256)

        for raw in out["raw_files"]:
            self.assertNotIn("source_path", raw)
            self.assertNotIn("stored_path", raw)
            self.assertIsNone(_LEAKY_PATH_RE.search(raw["stored_logical_path"]))

    def test_empty_batch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = build_runner_job_input(
                sku=SKU_BASIC,
                client_ref="empty-client",
                cleaned_dir=tmp,
            )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error_code"], ERR_EMPTY_BATCH)

    def test_unknown_sku_fails(self) -> None:
        out = build_runner_job_input(
            sku="CLEAN-ULTIMATE",
            client_ref="x",
            queue_payload={"files": [_cleaned_record()]},
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error_code"], ERR_UNKNOWN_SKU)

    def test_queue_json_fixture_inline_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_path = Path(tmp) / "queue_minimal.json"
            queue_path.write_text(
                json.dumps(
                    {
                        "sku": SKU_ENRICH,
                        "client_ref": "queue-client-7",
                        "job_id": "wave7-queue-job",
                        "files": [
                            _cleaned_record(
                                file_id="q1",
                                sha=SHA_A,
                                with_enrichment=True,
                            ),
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = build_runner_job_from_queue_file(queue_path)

        self.assertTrue(out["ok"])
        self.assertEqual(out["job_record"]["sku"], SKU_ENRICH)
        self.assertEqual(out["job_record"]["job_id"], "wave7-queue-job")
        self.assertEqual(out["input_count"], 1)
        self.assertIn("enrichment", out["raw_files"][0])

    def test_intake_accept_builds_job(self) -> None:
        out = build_runner_job_input(
            sku=SKU_BASIC,
            client_ref="intake-accept",
            queue_payload={"files": [_cleaned_record(file_id="gate-ok")]},
            intake_request=_intake_accept_basic(),
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["input_count"], 1)

    def test_intake_defer_does_not_create_job(self) -> None:
        out = build_runner_job_input(
            sku=SKU_BASIC,
            client_ref="intake-defer",
            queue_payload={"files": [_cleaned_record()]},
            intake_request={
                "description": "raw_inbound wave 清洗 cleaned_full code_cleaning_pipeline_v2",
                "tags": ["碼源"],
            },
        )
        self.assertFalse(out["ok"])
        self.assertIsNone(out["job_record"])
        self.assertEqual(out["error_code"], ERR_INTAKE_DEFER)

    def test_intake_reject_does_not_create_job(self) -> None:
        out = build_runner_job_input(
            sku=SKU_BASIC,
            client_ref="intake-reject",
            queue_payload={"files": [_cleaned_record()]},
            intake_request={
                "description": "rag query graphrag ingest_verify",
                "product_sku": "CLEAN-BASIC",
            },
        )
        self.assertFalse(out["ok"])
        self.assertIsNone(out["job_record"])
        self.assertEqual(out["error_code"], ERR_INTAKE_REJECT)

    def test_sku_intake_mismatch_rejected(self) -> None:
        out = build_runner_job_input(
            sku=SKU_ENRICH,
            client_ref="sku-mismatch",
            queue_payload={"files": [_cleaned_record(with_enrichment=True)]},
            intake_request=_intake_accept_basic(),
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error_code"], ERR_SKU_INTAKE_MISMATCH)
        self.assertIsNone(out["job_record"])

    def test_manifest_json_list_of_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_name = "one.py.json"
            (root / json_name).write_text(
                json.dumps(
                    _cleaned_record(
                        file_id="one",
                        sha=SHA_A,
                        source_path=r"Z:\vault\cleaned_full\one.py.json",
                    )
                ),
                encoding="utf-8",
            )
            manifest = root / "batch_manifest.json"
            manifest.write_text(json.dumps([json_name]), encoding="utf-8")

            out = build_runner_job_input(
                sku=SKU_BASIC,
                client_ref="manifest-client",
                manifest_path=manifest,
                base_dir=root,
            )

        self.assertTrue(out["ok"])
        self.assertEqual(out["input_count"], 1)
        self.assertEqual(
            out["raw_files"][0]["stored_logical_path"],
            "cleaned_full/one.py.json",
        )


if __name__ == "__main__":
    unittest.main()
