"""Contract test: logging_adapter trace lifecycle → eval_gate compatibility.

Verifies that the record shape produced by a full logging_adapter trace lifecycle
meets the implicit contract expected by observability/eval_gate.py.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from metrics.metrics_collector import MetricsCollector, reset_collector
from observability.eval_gate import (
    CONTEXT_HEAVY_TOKEN_THRESHOLD,
    evaluate_task_record,
)
from observability.logging_adapter import (
    agent_run_trace,
    end_trace,
    log_event,
    log_metric,
    reset_active_trace,
    start_span,
    end_span,
    start_trace,
)


class TestEvalGateContract(unittest.TestCase):
    """End-to-end contract: a record from logging_adapter MUST be evaluable."""

    def setUp(self) -> None:
        reset_collector()
        reset_active_trace()

    def tearDown(self) -> None:
        reset_active_trace()

    # ── Happy path: full trace lifecycle → eval_gate pass ───────────────────

    def test_healthy_record_from_full_trace_passes_eval_gate(self) -> None:
        """A normal successful trace should pass eval_gate with no tags."""
        col = MetricsCollector()
        with agent_run_trace("ask_pipeline", task_id="ctr-healthy", collector=col) as ctx:
            log_event("retrieve_start", {"k": 1}, trace_ctx=ctx)
            start_span(ctx, "retrieve")
            end_span(
                ctx,
                duration_ms=12.5,
                token_delta={"prompt_tokens": 10, "completion_tokens": 0, "total_tokens": 10},
            )

        # Extract record from collector (same object end_trace writes to)
        task = col.get_task("ctr-healthy")
        self.assertTrue(task["ok"], task.get("message"))
        record = task["record"]

        # Feed into eval_gate
        result = evaluate_task_record(record)

        # Contract assertions
        self.assertIsInstance(result["pass"], bool)
        self.assertIsInstance(result["tags"], list)
        self.assertIsInstance(result["reasons"], list)
        self.assertTrue(result["pass"], f"unexpected tags: {result['tags']}")
        self.assertEqual(result["tags"], [])
        self.assertEqual(result["reasons"], [])

    # ── Failing traces produce correct tags ─────────────────────────────────

    def test_high_retry_record_fails_eval_gate(self) -> None:
        """retry_count >= 2 should fire high_retry tag."""
        col = MetricsCollector()
        with agent_run_trace("data_agent", task_id="ctr-retry", collector=col) as ctx:
            log_event("step_a", trace_ctx=ctx, as_step=True)
            log_metric("retry_count", 2, trace_ctx=ctx, collector=col)

        task = col.get_task("ctr-retry")
        self.assertTrue(task["ok"])
        record = task["record"]

        result = evaluate_task_record(record)
        self.assertFalse(result["pass"])
        self.assertIn("high_retry", result["tags"])

    def test_many_handoffs_record_fails_eval_gate(self) -> None:
        """handoff_count >= 3 should fire many_handoffs tag."""
        col = MetricsCollector()
        with agent_run_trace("orchestrator", task_id="ctr-handoff", collector=col) as ctx:
            log_event("handoff_A", trace_ctx=ctx, as_step=True)
            log_metric("handoff_count", 1, trace_ctx=ctx, collector=col)
            log_metric("handoff_count", 1, trace_ctx=ctx, collector=col)
            log_metric("handoff_count", 1, trace_ctx=ctx, collector=col)

        task = col.get_task("ctr-handoff")
        self.assertTrue(task["ok"])
        record = task["record"]

        result = evaluate_task_record(record)
        self.assertFalse(result["pass"])
        self.assertIn("many_handoffs", result["tags"])

    def test_context_overflow_triggers_infra_risk(self) -> None:
        """error_type=context_overflow should fire infra_risk tag."""
        col = MetricsCollector()
        # Use explicit start/end (not context manager) to inject error_type
        started = start_trace("worker", task_id="ctr-overflow", collector=col)
        self.assertTrue(started["ok"], started.get("message"))
        ctx = started["trace_ctx"]

        log_event("overflowing_step", trace_ctx=ctx, as_step=True)
        ended = end_trace(ctx, success=False, error_type="context_overflow", collector=col)
        self.assertTrue(ended["ok"], ended.get("message"))
        record = ended["record"]

        result = evaluate_task_record(record)
        self.assertFalse(result["pass"])
        self.assertIn("infra_risk", result["tags"])

    def test_context_heavy_token_usage_fails_eval_gate(self) -> None:
        """context_token_usage above threshold should fire context_heavy."""
        col = MetricsCollector()
        with agent_run_trace("heavy_agent", task_id="ctr-heavy", collector=col) as ctx:
            # One step with a large enough token delta to push over threshold
            log_event(
                "big_step",
                trace_ctx=ctx,
                as_step=True,
                collector=col,
            )
            # directly inflate via collector
            col.log_step(
                "ctr-heavy",
                "inflate",
                token_delta={
                    "prompt_tokens": CONTEXT_HEAVY_TOKEN_THRESHOLD + 1,
                    "completion_tokens": 0,
                    "total_tokens": CONTEXT_HEAVY_TOKEN_THRESHOLD + 1,
                },
            )

        task = col.get_task("ctr-heavy")
        self.assertTrue(task["ok"])
        record = task["record"]

        result = evaluate_task_record(record)
        self.assertFalse(result["pass"])
        self.assertIn("context_heavy", result["tags"])

    # ── Malformed / edge-case records ───────────────────────────────────────

    def test_non_dict_record_flags_invalid_record(self) -> None:
        """Non-dict input must return pass=False with 'invalid_record' tag."""
        result = evaluate_task_record(None)
        self.assertFalse(result["pass"])
        self.assertIn("invalid_record", result["tags"])

        result = evaluate_task_record("not a dict")
        self.assertFalse(result["pass"])
        self.assertIn("invalid_record", result["tags"])

        result = evaluate_task_record(42)
        self.assertFalse(result["pass"])
        self.assertIn("invalid_record", result["tags"])

    def test_empty_dict_record_fails_malformed(self) -> None:
        """Empty dict lacks all required fields → malformed_record."""
        result = evaluate_task_record({})
        self.assertFalse(result["pass"])
        self.assertIn("malformed_record", result["tags"])
        reasons = result["reasons"]
        self.assertGreaterEqual(len(reasons), 3)
        self.assertTrue(any("success" in r for r in reasons))
        self.assertTrue(any("retry_count" in r for r in reasons))
        self.assertTrue(any("handoff_count" in r for r in reasons))

    def test_missing_success_field_malformed(self) -> None:
        """Record lacking 'success' key → malformed_record."""
        result = evaluate_task_record({"retry_count": 0, "handoff_count": 0})
        self.assertFalse(result["pass"])
        self.assertIn("malformed_record", result["tags"])
        self.assertTrue(any("success" in r for r in result["reasons"]))

    def test_retry_count_wrong_type_malformed(self) -> None:
        """String retry_count instead of int → malformed_record."""
        result = evaluate_task_record({"success": True, "retry_count": "2", "handoff_count": 0})
        self.assertFalse(result["pass"])
        self.assertIn("malformed_record", result["tags"])
        self.assertTrue(
            any("retry_count" in r and "int" in r for r in result["reasons"])
        )

    def test_missing_context_token_usage_does_not_crash(self) -> None:
        """Record missing context_token_usage should not raise."""
        record = {"success": True, "retry_count": 0, "handoff_count": 0}
        result = evaluate_task_record(record)
        self.assertIsInstance(result["pass"], bool)
        self.assertIsInstance(result["tags"], list)

    def test_trace_completeness_none_defaults_to_pass(self) -> None:
        """When trace_completeness is absent, _float_field defaults to 1.0 → no gap."""
        record = {
            "success": True,
            "retry_count": 0,
            "handoff_count": 0,
            "context_token_usage": {"total_tokens": 100},
            "trace_completeness": None,
        }
        result = evaluate_task_record(record)
        # trace_completeness is None → isinstance(node, dict) False → returns default 1.0
        # which is >= 0.8 → no observability_gap
        self.assertTrue(result["pass"])

    # ── Boundary values ─────────────────────────────────────────────────────

    def test_retry_count_at_threshold_minus_one_does_not_fire(self) -> None:
        """retry_count = 1 (< 2) should not fire high_retry."""
        col = MetricsCollector()
        with agent_run_trace("agent", task_id="ctr-border", collector=col) as ctx:
            log_event("step", trace_ctx=ctx, as_step=True)
            log_metric("retry_count", 1, trace_ctx=ctx, collector=col)

        record = col.get_task("ctr-border")["record"]
        result = evaluate_task_record(record)
        self.assertTrue(result["pass"])

    def test_handoff_count_at_threshold_minus_one_does_not_fire(self) -> None:
        """handoff_count = 2 (< 3) should not fire many_handoffs."""
        col = MetricsCollector()
        with agent_run_trace("agent", task_id="ctr-hand-border", collector=col) as ctx:
            log_event("step", trace_ctx=ctx, as_step=True)
            log_metric("handoff_count", 1, trace_ctx=ctx, collector=col)
            log_metric("handoff_count", 1, trace_ctx=ctx, collector=col)

        record = col.get_task("ctr-hand-border")["record"]
        result = evaluate_task_record(record)
        self.assertTrue(result["pass"])

    # ── P2 features: version field + disabled_tags ─────────────────────────

    def test_eval_gate_version_present_and_stable(self) -> None:
        """evaluate_task_record must include eval_gate_version in every response."""
        col = MetricsCollector()
        with agent_run_trace("ask_pipeline", task_id="ctr-ver", collector=col) as ctx:
            log_event("step", trace_ctx=ctx, as_step=True)

        record = col.get_task("ctr-ver")["record"]
        result = evaluate_task_record(record)

        self.assertIn("eval_gate_version", result)
        self.assertIsInstance(result["eval_gate_version"], str)
        self.assertEqual(result["eval_gate_version"], "0.2")

    def test_disabled_tags_skips_high_retry_rule(self) -> None:
        """disabled_tags=frozenset({'high_retry'}) should suppress that rule's tag and reason."""
        col = MetricsCollector()
        with agent_run_trace("data_agent", task_id="ctr-disable", collector=col) as ctx:
            log_event("step", trace_ctx=ctx, as_step=True)
            log_metric("retry_count", 2, trace_ctx=ctx, collector=col)

        record = col.get_task("ctr-disable")["record"]

        # Without disabled_tags — fires high_retry
        result = evaluate_task_record(record)
        self.assertFalse(result["pass"])
        self.assertIn("high_retry", result["tags"])

        # With disabled_tags — high_retry suppressed, result is pass
        result = evaluate_task_record(record, disabled_tags=frozenset({"high_retry"}))
        self.assertNotIn("high_retry", result["tags"])
        self.assertFalse(any("high retry" in r.lower() for r in result["reasons"]))
        self.assertTrue(result["pass"])


if __name__ == "__main__":
    unittest.main()