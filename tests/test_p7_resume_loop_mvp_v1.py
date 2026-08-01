"""Unit tests for P7 resume-loop MVP CLI (FP-G3 · G-1 primary + G-4 spot)."""
from __future__ import annotations

import unittest

from scripts.run_p7_resume_loop_mvp_v1 import run_p7_resume_loop_mvp_v1


class TestP7ResumeLoopMvpV1(unittest.TestCase):
    def test_g1_stale_checkpoint_mvp(self) -> None:
        result = run_p7_resume_loop_mvp_v1("G-1")
        self.assertTrue(result.get("ok"), msg=result)
        self.assertEqual(result.get("scenario"), "G-1")
        trace = result.get("trace_fields") or {}
        self.assertEqual(trace.get("resume_eligibility"), "stale_checkpoint")
        self.assertEqual(trace.get("final_status"), "stale_checkpoint")
        resume = result.get("resume_result") or {}
        self.assertFalse(resume.get("ok"))
        self.assertIn("expired", str(resume.get("message", "")).lower())

    def test_g4_checkpoint_load_error_mvp(self) -> None:
        result = run_p7_resume_loop_mvp_v1("G-4")
        self.assertTrue(result.get("ok"), msg=result)
        trace = result.get("trace_fields") or {}
        self.assertIn("checkpoint_load_error", trace)
        self.assertEqual(trace.get("final_status"), "blocked")
        self.assertEqual(trace.get("resume_eligibility"), "blocked")


if __name__ == "__main__":
    unittest.main()
