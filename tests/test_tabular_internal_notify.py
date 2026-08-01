"""Unit tests for tabular internal notify hook (v1)."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from tabular_automation_state_lib import start_automation  # noqa: E402
from tabular_internal_notify_lib import (  # noqa: E402
    EVENT_CASE_IDLE_TO_RUNNING,
    INTERNAL_NOTIFY_SCHEMA,
    notify_internal,
    notify_log_path,
)


class TestTabularInternalNotify(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.case_dir = self.tmp / "cases" / "demo_client" / "2026-0001"
        self.case_dir.mkdir(parents=True)
        shutil.copy2(
            _REPO_ROOT / "cases" / "demo_phase" / "intake.json",
            self.case_dir / "intake.json",
        )
        intake = json.loads((self.case_dir / "intake.json").read_text(encoding="utf-8"))
        intake["case_id"] = "2026-0001"
        (self.case_dir / "intake.json").write_text(
            json.dumps(intake, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_notify_internal_appends_log(self) -> None:
        result = notify_internal(
            self.case_dir,
            EVENT_CASE_IDLE_TO_RUNNING,
            {"previous_status": "idle", "requested_by": "test_op", "restart": False},
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["logged"])
        log_path = notify_log_path(self.case_dir)
        self.assertTrue(log_path.is_file())
        doc = json.loads(log_path.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema_version"], INTERNAL_NOTIFY_SCHEMA)
        self.assertEqual(len(doc["entries"]), 1)
        entry = doc["entries"][0]
        self.assertEqual(entry["event"], EVENT_CASE_IDLE_TO_RUNNING)
        self.assertEqual(entry["case_id"], "2026-0001")
        self.assertEqual(entry["payload"]["requested_by"], "test_op")

    def test_start_from_idle_triggers_notify(self) -> None:
        start = start_automation(self.case_dir, requested_by="operator")
        self.assertTrue(start["ok"])
        log_path = notify_log_path(self.case_dir)
        self.assertTrue(log_path.is_file())
        doc = json.loads(log_path.read_text(encoding="utf-8"))
        events = [e["event"] for e in doc["entries"]]
        self.assertIn(EVENT_CASE_IDLE_TO_RUNNING, events)

    def test_unknown_event_returns_ok_false(self) -> None:
        result = notify_internal(self.case_dir, "not.a.real.event", {})
        self.assertFalse(result["ok"])
        self.assertFalse(notify_log_path(self.case_dir).is_file())


if __name__ == "__main__":
    unittest.main()
