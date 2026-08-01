"""Unit tests for Tabular intake tool path dry-run CLI v1 (W4-T3-A)."""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "run_tabular_intake_tool_path.py"
_DEMO_PHASE = "cases/demo_phase"
_SAMPLECO = "cases/sampleco/2026-0001"
_OUTBOX_DIR = _REPO_ROOT / "outbox"

_MVP_PLANNED_TOOLS = [
    "validate.eligibility",
    "clean.phase_demo",
    "export.delivery_bundle",
]

_FORBIDDEN_IMPORT_PREFIXES = (
    "core.routing_policy_loader",
    "scripts.run_routing_eval",
    "tools.tabular_tool_executor",
)


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("run_tabular_intake_tool_path", _CLI_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_tabular_intake_tool_path"] = mod
    spec.loader.exec_module(mod)
    return mod


def _snapshot_tree(root: Path) -> dict[str, float]:
    if not root.exists():
        return {}
    out: dict[str, float] = {}
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            out[rel] = path.stat().st_mtime
    return out


def _run_cli_json(task_type: str, case_dir: str) -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(_CLI_PATH),
            "--task-type",
            task_type,
            "--case-dir",
            case_dir,
            "--json",
        ],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"CLI exit {proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return json.loads(proc.stdout)


class TestTabularIntakeToolPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _CLI_PATH.is_file():
            raise unittest.SkipTest(f"missing CLI: {_CLI_PATH}")
        cls.cli = _load_cli_module()

    def test_cli_module_does_not_import_forbidden_modules(self) -> None:
        source = _CLI_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        for name in imported:
            for forbidden in _FORBIDDEN_IMPORT_PREFIXES:
                self.assertFalse(
                    name == forbidden or name.startswith(forbidden + "."),
                    f"forbidden import detected: {name}",
                )

    def test_demo_phase_mvp_preview_ok(self) -> None:
        result = self.cli.run_tabular_intake_tool_path(
            "tabular.cleaning.mvp", _DEMO_PHASE
        )
        self.assertTrue(result["ok"], msg=result.get("message"))
        self.assertEqual(result["task_type"], "tabular.cleaning.mvp")
        self.assertEqual(result["case_dir"], _DEMO_PHASE)
        glue = result["glue_plan"]
        self.assertEqual(glue["planned_tools"], _MVP_PLANNED_TOOLS)
        self.assertEqual(glue["selector_task_type"], "e2e")
        self.assertEqual(glue["case_profile"], "demo_phase")
        executor_ids = [step["tool_id"] for step in result["executor_plan"]]
        self.assertEqual(executor_ids, _MVP_PLANNED_TOOLS)
        for step in result["executor_plan"]:
            self.assertTrue(step["dry_run"])
            self.assertTrue(step.get("planned_command"))
            self.assertIsInstance(step.get("expected_artifacts"), list)

    def test_demo_phase_subprocess_json(self) -> None:
        result = _run_cli_json("tabular.cleaning.mvp", _DEMO_PHASE)
        self.assertTrue(result["ok"])
        self.assertEqual(result["glue_plan"]["planned_tools"], _MVP_PLANNED_TOOLS)

    def test_sampleco_mvp_preview_notes(self) -> None:
        result = self.cli.run_tabular_intake_tool_path(
            "tabular.cleaning.mvp", _SAMPLECO
        )
        self.assertTrue(result["ok"], msg=result.get("message"))
        glue_notes = " ".join(result["glue_plan"].get("notes") or [])
        self.assertIn("multi_row_export", glue_notes)
        self.assertIn("schema_ambiguous", glue_notes)
        gate_notes = result["glue_plan"].get("inferred_gate_notes") or []
        self.assertIn("multi_row_export", gate_notes)
        self.assertIn("schema_ambiguous", gate_notes)
        clean_step = next(
            s for s in result["executor_plan"] if s["tool_id"] == "clean.phase_demo"
        )
        self.assertTrue(clean_step.get("human_review_required"))

    def test_unsupported_family_gov_eval(self) -> None:
        result = self.cli.run_tabular_intake_tool_path(
            "gov.observability.eval", _DEMO_PHASE
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "unsupported_family")

    def test_unsupported_family_subprocess_exit_zero(self) -> None:
        result = _run_cli_json("gov.observability.eval", _DEMO_PHASE)
        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "unsupported_family")

    def test_no_disk_writes_to_case_or_outbox(self) -> None:
        demo_before = _snapshot_tree(_REPO_ROOT / _DEMO_PHASE)
        sampleco_before = _snapshot_tree(_REPO_ROOT / _SAMPLECO)
        outbox_before = _snapshot_tree(_OUTBOX_DIR)

        self.cli.run_tabular_intake_tool_path("tabular.cleaning.mvp", _DEMO_PHASE)
        self.cli.run_tabular_intake_tool_path("tabular.cleaning.mvp", _SAMPLECO)
        _run_cli_json("tabular.cleaning.mvp", _DEMO_PHASE)

        demo_after = _snapshot_tree(_REPO_ROOT / _DEMO_PHASE)
        sampleco_after = _snapshot_tree(_REPO_ROOT / _SAMPLECO)
        outbox_after = _snapshot_tree(_OUTBOX_DIR)

        self.assertEqual(demo_before, demo_after)
        self.assertEqual(sampleco_before, sampleco_after)
        self.assertEqual(outbox_before, outbox_after)

    def test_selector_view_has_candidates_for_demo_phase(self) -> None:
        result = self.cli.run_tabular_intake_tool_path(
            "tabular.cleaning.mvp", _DEMO_PHASE
        )
        view = result["selector_view"]
        self.assertTrue(view.get("ok"))
        candidates = view.get("candidates") or []
        tool_ids = {c["tool_id"] for c in candidates}
        self.assertIn("clean.phase_demo", tool_ids)


if __name__ == "__main__":
    unittest.main()
