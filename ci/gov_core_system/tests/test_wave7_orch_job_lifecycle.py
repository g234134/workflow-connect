"""Unit tests for Wave 7 single-job orchestrator lifecycle (ORCH-JOB-LIFECYCLE)."""

from __future__ import annotations

import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from tests._repo_bootstrap import bootstrap_gov_core_tests

bootstrap_gov_core_tests(test_file=Path(__file__))

from core.envelope_writer import SKU_BASIC  # noqa: E402
from core.wave7_orch_job_lifecycle import (  # noqa: E402
    COMPLETION_COMPLETED_WITH_FAILURES,
    ERR_QA_P0,
    P0_POLICY_BLOCKED,
    STAGE_QA,
    STAGE_STORAGE,
    STATUS_BLOCKED,
    STATUS_DONE,
    STATUS_FAILED,
    JobRunContext,
    run_wave7_job,
)

SHA_A = "a" * 64
SHA_B = "b" * 64


def _repo_root() -> Path:
    from core.repo_paths import find_repo_root

    root = find_repo_root(start=Path(__file__).resolve())
    assert root is not None
    return root


def _paths_resolved(repo: Path) -> dict[str, str]:
    scratch = repo / "05_Temp_Cache" / "staging" / "wave7" / "_ut_lifecycle"
    scratch.mkdir(parents=True, exist_ok=True)
    delivery = scratch / "delivery"
    staging = scratch / "staging"
    delivery.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    return {
        "cleaned_full": "05_Temp_Cache/cleaned_full",
        "staging_root": staging.relative_to(repo).as_posix(),
        "delivery_root": delivery.relative_to(repo).as_posix(),
    }


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


def _intake_accept_basic() -> dict[str, object]:
    return {
        "description": "raw_inbound 碼源清洗 wave factory cleaned_full envelope",
        "tags": ["raw_inbound", "size_policy:acknowledged"],
        "explicit_task_type": "chariot.factory",
        "product_sku": "CLEAN-BASIC",
        "client_ref": "client-wave7-001",
        "inbound_path_hint": "raw_inbound/batch-42",
    }


class TestWave7OrchJobLifecycle(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _repo_root()
        self.paths = _paths_resolved(self.repo)
        self.job_id = f"w7-lc-{uuid.uuid4().hex[:10]}"

    def _job_input(
        self,
        *,
        with_reject: bool = False,
        intake: bool = False,
    ) -> dict[str, object]:
        raw_files = [_basic_raw_file(file_id="ok-1", sha=SHA_A)]
        if with_reject:
            raw_files.append(_basic_raw_file(file_id="reject-1", sha=SHA_B, clean_status="rejected"))
        payload: dict[str, object] = {
            "job_record": {"job_id": self.job_id, "sku": SKU_BASIC},
            "raw_files": raw_files,
        }
        if intake:
            return {
                "sku": SKU_BASIC,
                "client_ref": "lc-intake",
                "queue_payload": {"files": raw_files},
                "intake_request": _intake_accept_basic(),
                "job_id": self.job_id,
            }
        return payload

    def test_happy_path_intake_to_done(self) -> None:
        out = run_wave7_job(
            self._job_input(intake=True),
            paths_resolved=self.paths,
            repo_root=self.repo,
        )
        self.assertTrue(out["ok"], out.get("message"))
        self.assertEqual(out["status"], STATUS_DONE)
        self.assertIsNone(out.get("completion_variant"))
        self.assertIn("manifest_ref", out["artifacts"])
        self.assertIn("report_ref", out["artifacts"])
        self.assertTrue(out["qa"]["qa"]["manifest_integrity"]["ok"])
        self.assertEqual(out["envelope_compute_count"], 1)

    def test_happy_path_direct_job_record(self) -> None:
        out = run_wave7_job(
            self._job_input(),
            paths_resolved=self.paths,
            repo_root=self.repo,
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], STATUS_DONE)
        self.assertEqual(out["job_record"]["status"], STATUS_DONE)

    def test_completed_with_failures_when_rejected_rows_and_m1_ok(self) -> None:
        out = run_wave7_job(
            self._job_input(with_reject=True),
            paths_resolved=self.paths,
            repo_root=self.repo,
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], STATUS_DONE)
        self.assertEqual(out["completion_variant"], COMPLETION_COMPLETED_WITH_FAILURES)
        self.assertTrue(out["qa"]["qa"]["manifest_integrity"]["ok"])

    def test_qa_p0_failure_default_failed_not_retryable(self) -> None:
        def corrupt(ctx: JobRunContext) -> None:
            assert ctx.manifest is not None
            from core.schemas.wave6_manifest import ManifestV20

            contract = ctx.manifest.to_contract_dict()
            contract["accepted_units"] = 999
            ctx.manifest = ManifestV20.model_validate(contract)

        out = run_wave7_job(
            self._job_input(),
            paths_resolved=self.paths,
            repo_root=self.repo,
            hooks={"after_manifest": corrupt},
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["status"], STATUS_FAILED)
        self.assertEqual(out["stage"], STAGE_QA)
        self.assertEqual(out["error_code"], ERR_QA_P0)
        self.assertFalse(out["retryable"])

    def test_qa_p0_failure_blocked_policy(self) -> None:
        def corrupt(ctx: JobRunContext) -> None:
            assert ctx.manifest is not None
            from core.schemas.wave6_manifest import ManifestV20

            contract = ctx.manifest.to_contract_dict()
            contract["accepted_units"] = 999
            ctx.manifest = ManifestV20.model_validate(contract)

        out = run_wave7_job(
            self._job_input(),
            paths_resolved=self.paths,
            repo_root=self.repo,
            p0_failure_policy=P0_POLICY_BLOCKED,
            hooks={"after_manifest": corrupt},
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["status"], STATUS_BLOCKED)
        self.assertFalse(out["retryable"])

    def test_storage_io_retry_skips_envelope_recompute(self) -> None:
        write_calls: list[int] = []

        def counting_envelopes(job_record, raw_files):
            write_calls.append(1)
            from core.envelope_writer import write_envelopes as real_write

            return real_write(job_record, raw_files)

        report_writes = {"n": 0}

        def flaky_writer(path: Path, text: str) -> None:
            if path.name == "report.json":
                report_writes["n"] += 1
                if report_writes["n"] == 1:
                    raise OSError("simulated transient report io failure")
            path.write_text(text, encoding="utf-8")

        with patch("core.wave7_orch_job_lifecycle.write_envelopes", side_effect=counting_envelopes):
            out = run_wave7_job(
                self._job_input(),
                max_retries=2,
                paths_resolved=self.paths,
                repo_root=self.repo,
                json_writer=flaky_writer,
            )

        self.assertTrue(out["ok"], out.get("message"))
        self.assertEqual(out["status"], STATUS_DONE)
        self.assertEqual(len(write_calls), 1)
        self.assertGreaterEqual(out["storage_attempts"], 2)
        self.assertEqual(out["stage"], STAGE_STORAGE)

if __name__ == "__main__":
    unittest.main()
