"""Unit tests for P3 local trace harden v1."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "scripts" / "run_p3_trace_local_harden_v1.py"
_DOC = _REPO_ROOT / "docs" / "p3-trace-local-harden-v1.md"
_TICKET = (
    _REPO_ROOT / "04_Workflows" / "tickets" / "P3-TRACE-LOCAL-HARDEN-v1_state.md"
)
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "trace" / "sample_traces.jsonl"


class TestP3TraceLocalHardenV1(unittest.TestCase):
    def test_assets_exist(self) -> None:
        for path in (_SCRIPT, _DOC, _TICKET, _FIXTURE):
            self.assertTrue(path.is_file(), msg=f"missing {path}")

    def test_doc_has_non_claims_and_commands(self) -> None:
        text = _DOC.read_text(encoding="utf-8")
        self.assertIn("non_claims", text.lower())
        self.assertIn("run_p3_trace_local_harden_v1.py", text)
        self.assertIn("Langfuse", text)
        self.assertIn("apply_phase_pct", text)

    def test_harden_default_fixture_ok(self) -> None:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from run_p3_trace_local_harden_v1 import (  # noqa: WPS433
            run_p3_trace_local_harden,
        )

        result = run_p3_trace_local_harden()
        self.assertTrue(result.get("ok"), msg=result)
        self.assertEqual(result.get("schema_version"), "p3_trace_local_harden_v1")
        self.assertFalse(result.get("apply_phase_pct"))
        names = [c["name"] for c in (result.get("checks") or [])]
        self.assertEqual(
            names,
            ["schema_fixture", "query_by_trace_id", "query_by_task_id"],
        )
        self.assertTrue(all(c.get("ok") for c in result["checks"]))
        claims = result.get("non_claims") or []
        self.assertTrue(any("Langfuse" in c for c in claims))
        self.assertTrue(any("Phase%" in c for c in claims))

    def test_bad_jsonl_ok_false(self) -> None:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from run_p3_trace_local_harden_v1 import (  # noqa: WPS433
            run_p3_trace_local_harden,
        )

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.jsonl"
            bad.write_text("{not json\n", encoding="utf-8")
            result = run_p3_trace_local_harden(file=bad)
            self.assertFalse(result.get("ok"))
            self.assertIn("schema_fixture", result.get("failed_checks") or [])
            schema = next(
                c for c in result["checks"] if c["name"] == "schema_fixture"
            )
            self.assertFalse(schema.get("ok"))
            self.assertTrue(schema.get("invalid"))

    def test_missing_required_key_ok_false(self) -> None:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from run_p3_trace_local_harden_v1 import (  # noqa: WPS433
            run_p3_trace_local_harden,
        )

        with tempfile.TemporaryDirectory() as tmp:
            incomplete = Path(tmp) / "incomplete.jsonl"
            incomplete.write_text(
                json.dumps(
                    {
                        "trace_schema_version": "gov-trace-v2",
                        "event": "trace_start",
                        "timestamp": "2026-07-15T00:00:00Z",
                        "trace_id": "t-missing-task",
                        # missing task_id + status → validate_trace_event fails
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = run_p3_trace_local_harden(file=incomplete)
            self.assertFalse(result.get("ok"))
            schema = next(
                c for c in result["checks"] if c["name"] == "schema_fixture"
            )
            self.assertFalse(schema.get("ok"))
            reasons = " ".join(
                str(row.get("reason") or "") for row in (schema.get("invalid") or [])
            )
            self.assertIn("missing required", reasons.lower())

    def test_cli_text_ok(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_SCRIPT), "--format", "text"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        self.assertIn("ok: True", proc.stdout)
        self.assertIn("p3_trace_local_harden_v1", proc.stdout)
        self.assertIn("Langfuse", proc.stdout)

    def test_cli_json_ok(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_SCRIPT), "--pretty"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload.get("ok"))
        self.assertEqual(payload.get("schema_version"), "p3_trace_local_harden_v1")
        self.assertEqual(payload.get("failed_checks"), [])


if __name__ == "__main__":
    unittest.main()
