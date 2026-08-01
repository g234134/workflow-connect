"""Unit tests for Non-Tabular preview orchestrator v1 (W9-T4)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "run_non_tabular_experiment_preview.py"
_OUTBOX_ROOT = _REPO_ROOT / "outbox" / "non_tabular_experiment"

_NT_A_TASK = "non_tabular.document.extract"
_NT_B_TASK = "non_tabular.log.analyze"
_TABULAR_TASK = "tabular.cleaning.mvp"

_REQUIRED_TOP_KEYS = (
    "ok",
    "experiment_id",
    "case_ref",
    "task_type",
    "decision",
    "planned_route",
    "planned_tools",
    "risk",
    "content_summary",
    "final_status",
)


def _load_cli_module():
    spec = importlib.util.spec_from_file_location(
        "run_non_tabular_experiment_preview", _CLI_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_non_tabular_experiment_preview"] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_cli_json(
    task_type: str,
    case_dir: str,
    *,
    extra_args: list[str] | None = None,
) -> dict:
    cmd = [
        sys.executable,
        str(_CLI_PATH),
        "--task-type",
        task_type,
        "--case-dir",
        case_dir,
        "--format",
        "json",
    ]
    if extra_args:
        cmd.extend(extra_args)
    proc = subprocess.run(
        cmd,
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        raise AssertionError(
            f"CLI failed rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return json.loads(proc.stdout)


class NonTabularOrchestratorPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._mod = _load_cli_module()

    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="nt_preview_")
        self._case_nt_a = Path(self._tmpdir) / "nt_docu_stub"
        self._case_nt_b = Path(self._tmpdir) / "nt_log_stub"
        self._case_nt_a.mkdir(parents=True)
        self._case_nt_b.mkdir(parents=True)
        (self._case_nt_a / "intake.json").write_text(
            json.dumps(
                {
                    "case_id": "docu-2026-0001",
                    "client_ref": "docu-corp",
                    "content_type": "mixed_documents",
                    "schema_hint": "schema-free",
                    "sensitivity": "internal",
                }
            ),
            encoding="utf-8",
        )
        (self._case_nt_b / "intake.json").write_text(
            json.dumps(
                {
                    "case_id": "logs-2026-0001",
                    "client_ref": "log-analytics-co",
                    "content_type": "server_logs",
                    "schema_hint": "semi-structured",
                    "sensitivity": "internal",
                    "volume_gb": 2,
                }
            ),
            encoding="utf-8",
        )
        (self._case_nt_a / "docs").mkdir(parents=True, exist_ok=True)
        (self._case_nt_a / "images").mkdir(parents=True, exist_ok=True)
        (self._case_nt_a / "docs" / "sample.pdf").write_bytes(b"x" * 128)
        (self._case_nt_a / "docs" / "brief.docx").write_bytes(b"y" * 64)
        (self._case_nt_a / "images" / "scan.png").write_bytes(b"z" * 32)
        (self._case_nt_b / "raw" / "server_logs").mkdir(parents=True, exist_ok=True)
        (self._case_nt_b / "raw" / "server_logs" / "access-2026-05-01.log").write_bytes(
            b"line\n" * 20
        )
        (self._case_nt_b / "raw" / "server_logs" / "error-2026-05-02.log").write_bytes(
            b"err\n" * 10
        )

    def tearDown(self) -> None:
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_nt_a_preview_json_structure(self) -> None:
        result = self._mod.run_non_tabular_experiment_preview(
            _NT_A_TASK,
            str(self._case_nt_a),
            write_outbox=False,
        )
        for key in _REQUIRED_TOP_KEYS:
            self.assertIn(key, result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["task_type"], _NT_A_TASK)
        self.assertEqual(result["final_status"], "preview_ready")
        self.assertEqual(result["decision"]["decision"], "needs_review")
        self.assertIsInstance(result["planned_tools"], list)
        self.assertGreater(len(result["planned_tools"]), 0)
        route = result["planned_route"]
        self.assertTrue(route["ok"])
        self.assertEqual(route["selector_task_type"], "document_extract")
        self.assertEqual(route["skill_card"], "NT-A")
        self.assertIn("validate.content_accessible", route["planned_tools"])
        self.assertTrue(
            set(result["planned_tools"]).issubset({"text_extractor", "doc_classifier"})
        )
        summary = result["content_summary"]
        self.assertTrue(summary["ok"])
        self.assertTrue(summary["metadata_only"])
        self.assertEqual(summary["extension_distribution"]["pdf"], 1)
        self.assertEqual(summary["extension_distribution"]["docx"], 1)
        self.assertEqual(summary["extension_distribution"]["png"], 1)
        self.assertIn("S4_lite_content_summary", result["steps_run"])

    def test_nt_b_preview_json_structure(self) -> None:
        result = self._mod.run_non_tabular_experiment_preview(
            _NT_B_TASK,
            str(self._case_nt_b),
            write_outbox=False,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["task_type"], _NT_B_TASK)
        self.assertEqual(result["final_status"], "preview_ready")
        route = result["planned_route"]
        self.assertTrue(route["ok"])
        self.assertEqual(route["selector_task_type"], "log_analyze")
        self.assertEqual(route["skill_card"], "NT-B")
        self.assertIn("parse.log_structure", route["planned_tools"])
        self.assertTrue(
            set(result["planned_tools"]).issubset({"log_parser", "anomaly_summarizer"})
        )
        summary = result["content_summary"]
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["extension_distribution"]["log"], 2)
        self.assertIn("date_in_filename", summary["filename_pattern_hints"])

    def test_outbox_path_written(self) -> None:
        outbox_root = Path(self._tmpdir) / "sandbox_outbox"
        result = self._mod.run_non_tabular_experiment_preview(
            _NT_A_TASK,
            str(self._case_nt_a),
            write_outbox=True,
            outbox_root=str(outbox_root),
        )
        self.assertIn("outbox_path", result)
        outbox_file = outbox_root / Path(result["outbox_path"]).name
        if not outbox_file.is_file():
            outbox_file = Path(result["outbox_path"])
        self.assertTrue(outbox_file.is_file(), msg=f"missing {outbox_file}")
        payload = json.loads(outbox_file.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "non_tabular_experiment_preview_v1")
        self.assertTrue(payload["preview_only"])
        self.assertEqual(payload["task_type"], _NT_A_TASK)
        self.assertIn("planned_tools", payload)
        self.assertIn("content_summary", payload)
        self.assertTrue(payload["content_summary"]["metadata_only"])
        self.assertNotIn("client_secret", payload)

    def test_non_non_tabular_task_type_blocked(self) -> None:
        result = self._mod.run_non_tabular_experiment_preview(
            _TABULAR_TASK,
            str(self._case_nt_a),
            write_outbox=False,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["final_status"], "blocked")
        self.assertEqual(result["message"], "blocked_non_non_tabular_task_type")

    def test_cli_subprocess_nt_a(self) -> None:
        result = _run_cli_json(_NT_A_TASK, str(self._case_nt_a), extra_args=["--no-outbox"])
        self.assertEqual(result["final_status"], "preview_ready")

    def test_no_metadata_extraction_without_flag(self) -> None:
        result = self._mod.run_non_tabular_experiment_preview(
            _NT_A_TASK,
            str(self._case_nt_a),
            write_outbox=False,
        )
        self.assertNotIn("processing_summary", result)
        self.assertNotIn("S7_metadata_extraction", result["steps_run"])
        self.assertEqual(result["mode"], "preview")

    def test_metadata_extraction_with_flag_and_allowlist(self) -> None:
        result = self._mod.run_non_tabular_experiment_preview(
            _NT_A_TASK,
            str(self._case_nt_a),
            write_outbox=False,
            with_metadata_extraction=True,
        )
        self.assertEqual(result["mode"], "preview+meta")
        self.assertIn("S7_metadata_extraction", result["steps_run"])
        proc = result["processing_summary"]
        self.assertTrue(proc["executed"])
        self.assertEqual(proc["tool_id"], "document_metadata_extractor_v1")
        self.assertGreaterEqual(proc["files_processed"], 2)
        paths = {d["path"] for d in proc["documents"]}
        self.assertIn("docs/sample.pdf", paths)
        self.assertIn("docs/brief.docx", paths)

    def test_metadata_extraction_skipped_for_nt_b_even_with_flag(self) -> None:
        result = self._mod.run_non_tabular_experiment_preview(
            _NT_B_TASK,
            str(self._case_nt_b),
            write_outbox=False,
            with_metadata_extraction=True,
        )
        proc = result["processing_summary"]
        self.assertFalse(proc["executed"])
        self.assertIn("task_type_not_nt_a", proc["message"])

    def test_metadata_extraction_skipped_for_non_allowlist_case(self) -> None:
        other = Path(self._tmpdir) / "other_docu"
        other.mkdir()
        (other / "intake.json").write_text(
            json.dumps({"client_ref": "docu-corp"}),
            encoding="utf-8",
        )
        result = self._mod.run_non_tabular_experiment_preview(
            _NT_A_TASK,
            str(other),
            write_outbox=False,
            with_metadata_extraction=True,
        )
        proc = result["processing_summary"]
        self.assertFalse(proc["executed"])
        self.assertIn("case_dir_not_allowlisted", proc["message"])

    def test_outbox_includes_processing_summary(self) -> None:
        outbox_root = Path(self._tmpdir) / "sandbox_meta_outbox"
        result = self._mod.run_non_tabular_experiment_preview(
            _NT_A_TASK,
            str(self._case_nt_a),
            write_outbox=True,
            outbox_root=str(outbox_root),
            with_metadata_extraction=True,
        )
        outbox_file = outbox_root / Path(result["outbox_path"]).name
        payload = json.loads(outbox_file.read_text(encoding="utf-8"))
        self.assertIn("processing_summary", payload)
        self.assertTrue(payload["processing_summary"]["executed"])
        self.assertEqual(payload["schema_version"], "non_tabular_experiment_preview_v1")
        self.assertTrue(payload["preview_only"])
        self.assertNotIn("outbox/tabular", str(outbox_file).replace("\\", "/"))

    def test_cli_mode_preview_meta(self) -> None:
        result = _run_cli_json(
            _NT_A_TASK,
            str(self._case_nt_a),
            extra_args=["--no-outbox", "--mode", "preview+meta"],
        )
        self.assertEqual(result["mode"], "preview+meta")
        self.assertTrue(result["processing_summary"]["executed"])


if __name__ == "__main__":
    unittest.main()
