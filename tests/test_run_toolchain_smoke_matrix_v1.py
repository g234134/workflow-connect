"""Unit tests for scripts/run_toolchain_smoke_matrix.py (WC-PRE-05)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RUNNER_PATH = _REPO_ROOT / "scripts" / "run_toolchain_smoke_matrix.py"
_MATRIX_PATH = _REPO_ROOT / "routing" / "toolchain_smoke_matrix_v1.yaml"


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_toolchain_smoke_matrix", _RUNNER_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_toolchain_smoke_matrix_test"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestRunToolchainSmokeMatrixV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _RUNNER_PATH.is_file():
            raise unittest.SkipTest(f"missing runner: {_RUNNER_PATH}")
        cls.mod = _load_runner()

    def test_load_matrix_ok(self) -> None:
        loaded = self.mod._load_matrix(_MATRIX_PATH)
        self.assertTrue(loaded["ok"])
        self.assertGreaterEqual(len(loaded["entries"]), 10)

    def test_dry_run_lists_local_recommended_entries(self) -> None:
        report = self.mod.run_toolchain_smoke_matrix(
            tier="local_recommended",
            dry_run=True,
        )
        self.assertTrue(report["ok"])
        self.assertTrue(report["dry_run"])
        self.assertGreater(report["entries_requested"], 0)
        self.assertEqual(report["entries_run"], 0)
        for item in report["results"]:
            self.assertEqual(item["tier"], "local_recommended")
            self.assertTrue(item["skipped"])
            self.assertTrue(item["command"])

    def test_smoke_id_filter_not_found(self) -> None:
        report = self.mod.run_toolchain_smoke_matrix(
            smoke_id="TS-NONEXISTENT",
            dry_run=True,
        )
        self.assertFalse(report["ok"])
        self.assertIn("not found", report["message"])

    def test_smoke_id_filter_found(self) -> None:
        report = self.mod.run_toolchain_smoke_matrix(
            smoke_id="TS-W3TL-UNIT",
            dry_run=True,
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["entries_requested"], 1)
        self.assertEqual(report["results"][0]["smoke_id"], "TS-W3TL-UNIT")

    def test_execute_single_entry_mocked_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            matrix = tmp + "/matrix.yaml"
            Path(matrix).write_text(
                """
schema_version: toolchain_smoke_matrix_v1
matrix_revision: test
entries:
  - smoke_id: TS-TEST-ONE
    command: python -m unittest tests.test_run_toolchain_smoke_matrix_v1 -v
    tier: local_recommended
    gate_class: optional
    blocks_mainline: false
""".strip(),
                encoding="utf-8",
            )
            with patch.object(self.mod.subprocess, "run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=["python"],
                    returncode=0,
                    stdout="ok",
                    stderr="",
                )
                report = self.mod.run_toolchain_smoke_matrix(
                    smoke_id="TS-TEST-ONE",
                    dry_run=False,
                    matrix_path=Path(matrix),
                )
        self.assertTrue(report["ok"])
        self.assertEqual(report["entries_run"], 1)
        self.assertEqual(report["entries_passed"], 1)
        mock_run.assert_called_once()

    def test_main_list_exit_zero(self) -> None:
        rc = self.mod.main(["--list", "--format", "json"])
        self.assertEqual(rc, 0)

    def test_runner_result_has_stable_schema(self) -> None:
        report = self.mod.run_toolchain_smoke_matrix(dry_run=True, tier="all")
        for key in (
            "ok",
            "message",
            "schema_version",
            "dry_run",
            "tier",
            "entries_requested",
            "results",
        ):
            self.assertIn(key, report)
        self.assertEqual(report["schema_version"], "toolchain_smoke_runner_v1")


if __name__ == "__main__":
    unittest.main()
