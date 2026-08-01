"""Unit / integration tests for Wave 3 smoke chain v1."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.wave3_smoke_chain_v1 import (  # noqa: E402
    SCHEMA_VERSION,
    STEP_IDS,
    run_wave3_smoke_chain_v1,
)


class TestWave3SmokeChainV1(unittest.TestCase):
    def test_chain_without_mp_smoke_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = run_wave3_smoke_chain_v1(
                "demo_phase",
                repo_root=_REPO_ROOT,
                outbox_root_override=str(outbox),
                include_mp_smoke=False,
            )
            self.assertTrue(result.get("ok"), result.get("message"))
            self.assertEqual(result.get("schema_version"), SCHEMA_VERSION)
            ids = [s["step_id"] for s in result.get("steps") or []]
            self.assertEqual(ids, list(STEP_IDS))
            parity = next(
                s for s in result["steps"] if s["step_id"] == "gate_layer_preview_parity"
            )
            self.assertTrue(parity["ok"])
            self.assertEqual(
                parity["detail"]["g7_decision"],
                parity["detail"]["layer_decision"],
            )
            sink = next(s for s in result["steps"] if s["step_id"] == "alert_sink_file")
            self.assertTrue(sink["ok"])
            sink_path = Path(sink["artifact_paths"]["sink_path"])
            self.assertTrue(sink_path.is_file())
            lines = sink_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 1)
            event = json.loads(lines[-1])
            self.assertEqual(event.get("schema_version"), "p75_alert_sink_event_v1")
            self.assertTrue((event.get("sink") or {}).get("delivered"))

            run_step = next(
                s for s in result["steps"] if s["step_id"] == "g7_http_run_notify"
            )
            self.assertTrue(run_step["ok"])
            self.assertIn("outbox_record_path", run_step.get("artifact_paths") or {})

    def test_full_chain_with_mp_smoke_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = run_wave3_smoke_chain_v1(
                "demo_phase",
                repo_root=_REPO_ROOT,
                outbox_root_override=str(outbox),
                include_mp_smoke=True,
            )
            self.assertTrue(result.get("ok"), result.get("message"))
            self.assertEqual(result.get("failed_steps"), [])
            mp = next(s for s in result["steps"] if s["step_id"] == "mp_smoke")
            self.assertTrue(mp["ok"])
            self.assertFalse((mp.get("detail") or {}).get("skipped"))
            self.assertGreaterEqual((mp.get("detail") or {}).get("step_count") or 0, 7)


if __name__ == "__main__":
    unittest.main()
