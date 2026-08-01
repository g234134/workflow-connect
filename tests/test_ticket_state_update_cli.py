"""CLI integration test for WC-T2 ticket state update + comms path."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from ticket_comms.message_generator import SCHEMA_VERSION  # noqa: E402

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "ticket_comms"
_CLI = _REPO_ROOT / "scripts" / "run_ticket_state_update_with_comms.py"

_REQUIRED_PAYLOAD_KEYS = (
    "schema_version",
    "ticket_id",
    "title",
    "summary",
    "ticket_ref",
    "status",
    "changed_fields",
    "diff",
    "generated_at",
)


class TestTicketStateUpdateCli(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.outbox = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _run_cli(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(_CLI),
                "--before",
                str(_FIXTURES / "wc_t2_before_state.md"),
                "--after",
                str(_FIXTURES / "wc_t2_after_state.md"),
                "--outbox-dir",
                str(self.outbox),
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(_REPO_ROOT),
        )

    def test_cli_writes_ticket_comms_v01_jsonl(self) -> None:
        proc = self._run_cli()
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)

        result = json.loads(proc.stdout)
        self.assertTrue(result["ok"])
        self.assertTrue(result["sent"])
        self.assertEqual(result["ticket_id"], "WC-T2-COMMS")
        self.assertEqual(result["message"], "written_to_file_log")

        log_path = self.outbox / "ticket_comms.jsonl"
        self.assertTrue(log_path.is_file())

        lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)

        record = json.loads(lines[0])
        self.assertEqual(record["channel"], "file_log")
        self.assertTrue(record["simulated"])
        self.assertFalse(record["external_dispatch"])
        self.assertIn("sent_at", record)

        payload = record["payload"]
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        for key in _REQUIRED_PAYLOAD_KEYS:
            self.assertIn(key, payload, msg=f"missing payload key: {key}")

        self.assertEqual(payload["status"]["before"]["overall_status"], "in_progress")
        self.assertEqual(payload["status"]["after"]["overall_status"], "review")
        self.assertIn("overall_status", payload["changed_fields"])
        self.assertIn("current_owner", payload["changed_fields"])
        self.assertIn("WC-T2-COMMS", payload["summary"])

    def test_dry_run_skips_jsonl(self) -> None:
        proc = self._run_cli("--dry-run")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)

        result = json.loads(proc.stdout)
        self.assertTrue(result["ok"])
        self.assertTrue(result["sent"])
        self.assertIsNotNone(result["payload"])
        self.assertEqual(result["payload"]["schema_version"], SCHEMA_VERSION)
        self.assertFalse((self.outbox / "ticket_comms.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
