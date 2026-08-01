"""Unit tests for P4 dispatch replay min v1."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "scripts" / "run_p4_dispatch_replay_min_v1.py"
_DOC = _REPO_ROOT / "docs" / "p4-dispatch-replay-min-v1.md"
_TICKET = (
    _REPO_ROOT / "04_Workflows" / "tickets" / "P4-DISPATCH-REPLAY-MIN-v1_state.md"
)

# Stable ticket known to exist (Wave A smoke pack · in review)
_SAMPLE_TICKET = "P4-MULTI-CHAT-SMOKE-PACK-v1"


class TestP4DispatchReplayMinV1(unittest.TestCase):
    def test_assets_exist(self) -> None:
        for path in (_SCRIPT, _DOC, _TICKET):
            self.assertTrue(path.is_file(), msg=f"missing {path}")

    def test_doc_has_non_claims_and_commands(self) -> None:
        text = _DOC.read_text(encoding="utf-8")
        self.assertIn("non_claims", text.lower())
        self.assertIn("run_p4_dispatch_replay_min_v1.py", text)
        self.assertIn("O → B → C → D", text)
        self.assertIn("apply_phase_pct", text)

    def test_build_replay_for_sample_ticket(self) -> None:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from run_p4_dispatch_replay_min_v1 import (  # noqa: WPS433
            build_dispatch_replay_min,
        )

        result = build_dispatch_replay_min(ticket_id=_SAMPLE_TICKET)
        self.assertTrue(result.get("ok"), msg=result)
        self.assertEqual(result.get("ticket_id"), _SAMPLE_TICKET)
        self.assertEqual(result.get("schema_version"), "p4_dispatch_replay_min_v1")
        self.assertFalse(result.get("apply_phase_pct"))
        seq = result.get("replay_sequence") or []
        self.assertEqual(len(seq), 4)
        self.assertEqual([s["code"] for s in seq], ["O", "B", "C", "D"])
        self.assertIn("≠ prod multi-agent runtime", result.get("non_claims") or [])
        # Smoke pack is in review → expect reviewer suggestion
        self.assertEqual(result.get("recommended_role"), "reviewer")

    def test_missing_ticket_returns_ok_false(self) -> None:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from run_p4_dispatch_replay_min_v1 import (  # noqa: WPS433
            build_dispatch_replay_min,
        )

        result = build_dispatch_replay_min(ticket_id="NO-SUCH-TICKET-XYZ-999")
        self.assertFalse(result.get("ok"))
        self.assertIn("not found", (result.get("message") or "").lower())

    def test_cli_json_ok(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT),
                "--ticket-id",
                _SAMPLE_TICKET,
                "--pretty",
            ],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload.get("ok"))
        self.assertEqual(payload.get("ticket_id"), _SAMPLE_TICKET)


if __name__ == "__main__":
    unittest.main()
