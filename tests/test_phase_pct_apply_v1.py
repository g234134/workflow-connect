"""Unit tests for 04_Workflows/_phase_pct_apply.py (Phase% estimate/verify/apply)."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "04_Workflows" / "_phase_pct_apply.py"


def _load():
    spec = importlib.util.spec_from_file_location("phase_pct_apply", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase_pct_apply"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestPhasePctApply(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _load()

    def test_normalize_and_parse_delta(self):
        self.assertEqual(self.m._normalize_phase("p8.5"), "P8.5")
        self.assertEqual(self.m._normalize_phase("08"), "P8")
        d = self.m.parse_delta_args(["P8.5=+2", "P4=+1"])
        self.assertEqual(d, {"P8.5": 2, "P4": 1})

    def test_parse_proposed_delta_pct(self):
        d = self.m.parse_proposed_delta_pct("P8.5 +2 · P9 +2（保守端）")
        self.assertEqual(d["P8.5"], 2)
        self.assertEqual(d["P9"], 2)
        d2 = self.m.parse_proposed_delta_pct("+8", ["P8.5"])
        self.assertEqual(d2, {"P8.5": 8})

    def test_parse_ticket_frame_gates(self):
        text = """
apply_phase_pct: false
phase_targets: [P4, P10]
baseline_pct: "07-13 SSOT"
proposed_delta_pct: "P4 +2 · P10 +2"
evidence_gate: L-local
"""
        frame = self.m.parse_ticket_frame(text)
        self.assertFalse(frame["apply_phase_pct"])
        self.assertEqual(frame["phase_targets"], ["P4", "P10"])
        self.assertEqual(frame["deltas"]["P4"], 2)
        self.assertFalse(frame["authorized_marker"])

        text2 = text.replace("false", "true") + "\n**已授權寫入**\n"
        frame2 = self.m.parse_ticket_frame(text2)
        self.assertTrue(frame2["apply_phase_pct"])
        self.assertTrue(frame2["authorized_marker"])

    def test_heuristic_estimate_table(self):
        self.assertEqual(self.m.HEURISTIC_STATUS, "approved")
        self.assertEqual(self.m.HEURISTIC_VERSION, "v0.1")
        self.assertNotIn("待定稿", self.m.HEURISTIC_NOTE)
        self.assertNotIn("待尚書省定稿", self.m.HEURISTIC_NOTE)
        self.assertIn("approved", self.m.HEURISTIC_NOTE)

        sample = (
            "phase_targets: [P4, P10]\n"
            "evidence_gate: L-local\n"
            "impact_size: medium\n"
            "apply_phase_pct: false\n"
        )
        est = self.m.estimate_deltas_for_ticket(sample)
        self.assertTrue(est["ok"])
        self.assertTrue(est["heuristic"])
        self.assertEqual(est["heuristic_status"], "approved")
        self.assertEqual(est["deltas"], {"P4": 2, "P10": 2})

        micro = (
            "phase_targets: [P4]\n"
            "impact_size: micro\n"
            "evidence_gate: L-local\n"
        )
        est2 = self.m.estimate_deltas_for_ticket(micro)
        self.assertEqual(est2["deltas"]["P4"], 0)

        blocked = (
            "phase_targets: [P8.5]\n"
            "impact_size: xl\n"
            "evidence_gate: blocked\n"
        )
        est3 = self.m.estimate_deltas_for_ticket(blocked)
        self.assertEqual(est3["deltas"]["P8.5"], 0)

        # size / gate caps (定稿表)
        self.assertEqual(self.m.SIZE_BASE_DELTA["small"], 1)
        self.assertEqual(self.m.SIZE_BASE_DELTA["large"], 5)
        self.assertEqual(self.m.SIZE_BASE_DELTA["xl"], 8)
        self.assertEqual(self.m.GATE_CAP["l-local"], 2)
        self.assertEqual(self.m.GATE_CAP["ci-advisory"], 5)
        self.assertEqual(self.m.GATE_CAP["ga-remote"], 8)

    def test_estimate_verify_refuse_apply_rhythm(self):
        """estimate → apply(no verify) fail → verify → dry-run apply ok; no Dashboard write."""
        tid = "__unittest_phase_pct_estimate_v1"
        tpath = self.m._ticket_path(ROOT, tid)
        body = (
            "# TICKET STATE · unittest estimate rhythm\n\n"
            "## FRAME\n\n"
            "phase_targets: [P4]\n"
            "baseline_pct: \"unittest\"\n"
            "evidence_gate: L-local\n"
            "impact_size: medium\n"
            "apply_phase_pct: true\n"
            "**已授權寫入**\n"
        )
        dash_before = self.m._dashboard_path(ROOT).read_text(encoding="utf-8")
        try:
            tpath.write_text(body, encoding="utf-8")
            est = self.m.cmd_estimate(ROOT, tid, write_back=True, force_heuristic=True)
            self.assertTrue(est["ok"], est)
            self.assertEqual(est["deltas"]["P4"], 2)
            self.assertEqual(est["lifecycle"], self.m.LIFECYCLE_ESTIMATED)

            refused = self.m.cmd_apply(
                ROOT,
                ticket_id=tid,
                deltas=None,
                authorize=True,
                label=None,
                max_delta=15,
                allow_large_delta=False,
                dry_run=False,
            )
            self.assertFalse(refused["ok"], refused)
            self.assertIn("verified", refused["message"].lower())

            bad_verify = self.m.cmd_verify(ROOT, tid, checks_ok=False, write_back=False)
            self.assertFalse(bad_verify["ok"], bad_verify)

            verified = self.m.cmd_verify(ROOT, tid, checks_ok=True, write_back=True)
            self.assertTrue(verified["ok"], verified)
            self.assertEqual(verified["lifecycle"], self.m.LIFECYCLE_VERIFIED)
            self.assertTrue(verified["write_candidate"])

            preview = self.m.cmd_apply(
                ROOT,
                ticket_id=tid,
                deltas=None,
                authorize=True,
                label=None,
                max_delta=15,
                allow_large_delta=False,
                dry_run=True,
            )
            self.assertTrue(preview["ok"], preview)
            self.assertTrue(preview["dry_run"])
        finally:
            if tpath.is_file():
                tpath.unlink()
        dash_after = self.m._dashboard_path(ROOT).read_text(encoding="utf-8")
        self.assertEqual(dash_before, dash_after)

    def test_read_and_self_test(self):
        r = self.m.cmd_read(ROOT)
        self.assertTrue(r["ok"], r.get("message"))
        self.assertGreaterEqual(r["phase_count"], 17)
        self.assertIn("P8.5", {p["phase"] for p in r["phases"]})
        st = self.m.cmd_self_test(ROOT)
        self.assertTrue(st["ok"], st)

    def test_from_ticket_wprog_b_propose(self):
        tid = "W-PROG-war-status-phase-refresh-2026-07-13"
        out = self.m.cmd_from_ticket(
            ROOT, tid, max_delta=15, allow_large_delta=False
        )
        self.assertTrue(out["ok"], out.get("message"))
        self.assertTrue(out["frame"]["apply_phase_pct"])
        self.assertIn("P8.5", out["frame"]["phase_targets"])


if __name__ == "__main__":
    unittest.main()
