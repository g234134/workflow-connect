"""Unit tests for TAB-W3-I4 copy_case_rules_from_history (history rules copy)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from copy_case_rules_from_history import copy_case_rules_from_history  # noqa: E402
from lookup_case_history import load_case_rules  # noqa: E402

_SOURCE = _REPO_ROOT / "cases" / "sampleco" / "2026-0001"
_TARGET = _REPO_ROOT / "cases" / "internal" / "generic-low-risk"
_COPY_CLI = _REPO_ROOT / "scripts" / "copy_case_rules_from_history.py"

_INTAKE_IDENTITY_KEYS = (
    "case_id",
    "client_ref",
    "product_sku",
    "data_file",
    "file_format",
    "encoding",
    "delimiter",
    "scale",
    "provenance",
    "sensitivity",
    "structure",
    "security_compliance",
)


def _run_copy_cli(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(_COPY_CLI), *args],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"copy CLI failed rc={proc.returncode} stderr={proc.stderr}")
    return json.loads(proc.stdout)


class TestCopyCaseRulesFromHistoryV1(unittest.TestCase):
    def test_load_case_rules_sampleco_has_rules(self) -> None:
        loaded = load_case_rules(_SOURCE, _REPO_ROOT)
        self.assertTrue(loaded["ok"])
        self.assertEqual(loaded["case_id"], "2026-0001")
        self.assertEqual(loaded["client_ref"], "sampleco")
        self.assertIn("cleaning_goals", loaded)
        self.assertIn("schema_hints", loaded)
        self.assertGreaterEqual(len(loaded.get("cleaning_rules") or []), 1)
        self.assertTrue(loaded["sources"]["intake.json"])
        self.assertTrue(loaded["sources"]["reports/report.json"])

    def test_copy_rules_from_sampleco_to_generic_low_risk_dry_run(self) -> None:
        result = copy_case_rules_from_history(
            from_case_dir=_SOURCE,
            to_case_dir=_TARGET,
            dry_run=True,
            repo_root=_REPO_ROOT,
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["from_case_id"], "2026-0001")
        self.assertEqual(result["to_case_id"], "generic-low-risk")
        self.assertIn("cleaning_goals.json", result["copied_files"])
        self.assertIn("schema_hints.json", result["copied_files"])
        self.assertIn("cleaning_rules.json", result["copied_files"])
        self.assertIn("intake.json", result["copied_files"])
        self.assertIn("overwrite", result["message"])

        cli_result = _run_copy_cli(
            "--from-case-dir",
            "cases/sampleco/2026-0001",
            "--to-case-dir",
            "cases/internal/generic-low-risk",
            "--dry-run",
            "--json",
        )
        self.assertTrue(cli_result["ok"])
        self.assertTrue(cli_result["dry_run"])

    def test_copy_rules_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            target = tmp_root / "cases" / "internal" / "new-demo-case"
            target.mkdir(parents=True)
            shutil.copytree(_SOURCE / "raw", target / "raw")
            shutil.copy2(_TARGET / "intake.json", target / "intake.json")

            result = copy_case_rules_from_history(
                from_case_dir=_SOURCE,
                to_case_dir=target,
                repo_root=tmp_root,
            )
            self.assertTrue(result["ok"])
            self.assertFalse(result["dry_run"])
            self.assertEqual(result["from_case_id"], "2026-0001")
            self.assertEqual(result["to_case_id"], "generic-low-risk")

            for filename in ("cleaning_goals.json", "schema_hints.json", "cleaning_rules.json", "intake.json"):
                path = target / filename
                self.assertTrue(path.is_file(), msg=f"missing {filename}")
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(payload, dict)

            goals = json.loads((target / "cleaning_goals.json").read_text(encoding="utf-8"))
            self.assertEqual(goals.get("cleaning_profile"), "sampleco_order_profile")
            self.assertIn("SampleCo milestone export", goals.get("goals", ""))

            rules = json.loads((target / "cleaning_rules.json").read_text(encoding="utf-8"))
            rule_ids = [
                item.get("rule") if isinstance(item, dict) else item
                for item in rules.get("cleaning_rules") or []
            ]
            self.assertIn("dedup_by_phase", rule_ids)

    def test_copy_rules_does_not_break_existing_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            target = tmp_root / "cases" / "internal" / "generic-low-risk"
            target.mkdir(parents=True)
            original_intake = json.loads((_TARGET / "intake.json").read_text(encoding="utf-8"))
            shutil.copy2(_TARGET / "intake.json", target / "intake.json")

            result = copy_case_rules_from_history(
                from_case_dir=_SOURCE,
                to_case_dir=target,
                repo_root=tmp_root,
            )
            self.assertTrue(result["ok"])

            updated_intake = json.loads((target / "intake.json").read_text(encoding="utf-8"))
            for key in _INTAKE_IDENTITY_KEYS:
                self.assertEqual(
                    updated_intake.get(key),
                    original_intake.get(key),
                    msg=f"identity key changed: {key}",
                )

            self.assertEqual(updated_intake.get("cleaning_profile"), "sampleco_order_profile")
            self.assertIn("SampleCo milestone export", updated_intake.get("cleaning_goals", ""))
            self.assertIn("percent_columns", updated_intake.get("schema") or {})


if __name__ == "__main__":
    unittest.main()
