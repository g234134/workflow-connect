"""Tests for Wave 8 Skill Card draft generator (04_Workflows)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "04_Workflows" / "_wave8_generate_skill_card_draft.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("wave8_skill_draft", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pass_summary(
    *,
    job_id: str = "w8-test-job-001",
    product_sku: str = "CLEAN-BASIC",
    row_count: int = 500,
    file_count: int = 2,
    qa_status: str = "pass",
    overall_ok: bool = True,
    job_status: str = "done",
) -> dict:
    return {
        "schema_version": "clean_run_summary_v0.1",
        "generated_at": "2026-06-05T12:00:00Z",
        "identity": {
            "job_id": job_id,
            "product_sku": product_sku,
            "intake_id": None,
            "order_id": None,
            "client_ref": "test-client",
            "batch_tag": None,
        },
        "input_volume": {
            "file_count": file_count,
            "row_count": row_count,
            "size_bytes": None,
            "skipped_file_count": 0,
        },
        "outcome": {
            "accepted_units": row_count,
            "rejected_units": 0,
            "billing_units": {"U": row_count, "L": 0},
            "qa_status": qa_status,
            "completion_variant": "completed",
            "overall_ok": overall_ok,
            "orch_status": "DONE",
            "job_status": job_status,
        },
        "qa_layers": {
            "m1_summary": {"ok": True, "checked_rows": row_count},
            "m2_summary": {"status": "skipped", "ok": True},
        },
        "runtime_stats": {
            "storage_retry_count": 1,
            "envelope_compute_count": 1,
            "checkpoint_hit": False,
        },
        "artifacts": {
            "manifest_ref": f"w6://delivery/{job_id}/manifest",
            "deliverable_refs": [f"w6://delivery/{job_id}/deliverables"],
        },
    }


class TestSkillCardDraftLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_pass_summary_generates_draft(self) -> None:
        summary = _pass_summary()
        ok, draft, msg = self.mod.generate_skill_card_draft(summary)
        self.assertTrue(ok, msg)
        assert draft is not None
        self.assertEqual(draft["schema_version"], "skill_card_v0.1")
        self.assertEqual(draft["card_meta"]["derived_from_job_id"], "w8-test-job-001")
        self.assertEqual(draft["card_meta"]["confidence_level"], "low")
        self.assertEqual(draft["scope"]["product_sku_scope"], "CLEAN-BASIC")
        self.assertEqual(draft["success_signals"]["qa_criteria"]["expected_qa_status"], "pass")
        self.assertEqual(draft["evidence"]["sample_job_ids"], ["w8-test-job-001"])
        self.assertEqual(draft["evidence"]["historical_success_rate"], 1.0)
        self.assertIn("Auto-generated", draft["evidence"]["notes"])
        self.assertEqual(
            draft["card_meta"]["skill_id"],
            "draft-clean-basic-w8-test-job-001",
        )

    def test_fail_summary_not_eligible(self) -> None:
        summary = _pass_summary(qa_status="fail", overall_ok=False)
        ok, draft, _ = self.mod.generate_skill_card_draft(summary)
        self.assertFalse(ok)
        self.assertIsNone(draft)
        self.assertFalse(self.mod.is_eligible_for_draft(summary)[0])

    def test_pass_with_warnings_not_eligible(self) -> None:
        summary = _pass_summary(qa_status="pass_with_warnings")
        ok, draft, _ = self.mod.generate_skill_card_draft(summary)
        self.assertFalse(ok)
        self.assertIsNone(draft)

    def test_high_volume_summary(self) -> None:
        summary = _pass_summary(row_count=150_000, file_count=3)
        draft = self.mod.build_skill_card_draft(summary)
        indicators = draft["input_profile"]["complexity_indicators"]
        self.assertTrue(indicators["is_high_volume"])
        self.assertIn("high-volume", draft["input_profile"]["description"].lower())

    def test_high_volume_by_file_count(self) -> None:
        summary = _pass_summary(row_count=100, file_count=12)
        self.assertTrue(self.mod.is_high_volume(summary))

    def test_runtime_stats_in_source_snapshot(self) -> None:
        summary = _pass_summary()
        draft = self.mod.build_skill_card_draft(summary)
        self.assertIn("source_snapshot", draft)
        self.assertIn("runtime_stats", draft["source_snapshot"])


class TestSkillCardDraftCli(unittest.TestCase):
    def _run_cli(self, summary: dict, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "run_summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            cmd = [sys.executable, str(_SCRIPT), "--run-summary", str(summary_path)]
            if extra_args:
                cmd.extend(extra_args)
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=str(_REPO_ROOT),
            )

    def test_cli_pass_exit_zero(self) -> None:
        proc = self._run_cli(_pass_summary(), ["--pretty"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["schema_version"], "skill_card_v0.1")

    def test_cli_fail_exit_one(self) -> None:
        proc = self._run_cli(_pass_summary(qa_status="fail"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not eligible for draft generation", proc.stderr)

    def test_cli_high_volume(self) -> None:
        proc = self._run_cli(_pass_summary(row_count=200_000))
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertTrue(
            data["input_profile"]["complexity_indicators"]["is_high_volume"]
        )

    def test_cli_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "run_summary.json"
            out_path = Path(tmp) / "draft.json"
            summary_path.write_text(json.dumps(_pass_summary()), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPT),
                    "--run-summary",
                    str(summary_path),
                    "--output",
                    str(out_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=str(_REPO_ROOT),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(out_path.is_file())
            written = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(written["schema_version"], "skill_card_v0.1")
            self.assertTrue(proc.stdout.strip())


class TestLoadRunSummary(unittest.TestCase):
    def test_invalid_json_raises(self) -> None:
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{", encoding="utf-8")
            with self.assertRaises(ValueError):
                mod.load_run_summary(bad)


class TestStderrMessage(unittest.TestCase):
    def test_not_eligible_stderr_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "run_summary.json"
            summary_path.write_text(
                json.dumps(_pass_summary(qa_status="fail")),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPT),
                    "--run-summary",
                    str(summary_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=str(_REPO_ROOT),
            )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not eligible for draft generation", proc.stderr)


if __name__ == "__main__":
    unittest.main()
