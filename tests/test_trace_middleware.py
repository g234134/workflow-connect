"""Unit tests for observability/trace_middleware (gov-trace-v2 HTTP layer)."""

from __future__ import annotations

import os
import unittest
from unittest import mock

from observability.trace_middleware import is_trace_middleware_enabled
from observability.trace_schema import GOV_TRACE_SCHEMA_VERSION, build_trace_event, validate_trace_event


class TestTraceMiddleware(unittest.TestCase):
    def test_middleware_disabled_by_default(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOV_TRACE_MIDDLEWARE_ENABLED", None)
            self.assertFalse(is_trace_middleware_enabled())

    def test_middleware_enabled_truthy_values(self) -> None:
        for val in ("1", "true", "YES", "on"):
            with self.subTest(val=val):
                with mock.patch.dict(os.environ, {"GOV_TRACE_MIDDLEWARE_ENABLED": val}):
                    self.assertTrue(is_trace_middleware_enabled())

    def test_http_request_event_pair_validates(self) -> None:
        trace_id = "trace-http-1"
        span_id = "span-http-1"
        start = build_trace_event(
            event="http_request_start",
            trace_id=trace_id,
            span_id=span_id,
            task_id="task-http-1",
            session_id="sess-1",
            agent_name="gov_core_api",
            workflow_name="/api/ask",
            tool_name="POST",
            status="running",
        )
        end = build_trace_event(
            event="http_request_end",
            trace_id=trace_id,
            span_id=span_id,
            task_id="task-http-1",
            session_id="sess-1",
            agent_name="gov_core_api",
            workflow_name="/api/ask",
            tool_name="POST",
            latency_ms=120.5,
            status="success",
            http_status_code=200,
        )
        self.assertEqual(start["trace_schema_version"], GOV_TRACE_SCHEMA_VERSION)
        self.assertTrue(validate_trace_event(start)["ok"])
        self.assertTrue(validate_trace_event(end)["ok"])
        self.assertEqual(end["latency_ms"], 120.5)


if __name__ == "__main__":
    unittest.main()
