"""
Optional FastAPI HTTP trace middleware (gov-trace-v2).

Enable with ``GOV_TRACE_MIDDLEWARE_ENABLED=1``. Never raises; adds response
headers ``X-Trace-Id`` / ``X-Span-Id`` when possible.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any

from observability.trace_schema import (
    GOV_TRACE_SCHEMA_VERSION,
    build_trace_event,
    new_span_id,
    new_trace_id,
)

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_LOG = logging.getLogger("gov_core.observability")


def is_trace_middleware_enabled() -> bool:
    return (os.environ.get("GOV_TRACE_MIDDLEWARE_ENABLED") or "").strip().lower() in _TRUTHY


def _emit(event: dict[str, Any]) -> None:
    _LOG.info("%s", json.dumps(event, default=str, ensure_ascii=False))


def _header_session_id(request: Any) -> str | None:
    for key in ("X-Session-Id", "X-Thread-Id"):
        val = request.headers.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return None


def _header_task_id(request: Any) -> str | None:
    val = request.headers.get("X-Task-Id")
    return str(val).strip() if val and str(val).strip() else None


def _header_user_id(request: Any) -> str | None:
    val = request.headers.get("X-User-Id")
    return str(val).strip() if val and str(val).strip() else None


class TraceMiddleware:
    """Starlette-compatible middleware wrapping HTTP requests."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        if not is_trace_middleware_enabled():
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request

        request = Request(scope, receive=receive)
        trace_id = request.headers.get("X-Trace-Id") or new_trace_id()
        span_id = new_span_id()
        task_id = _header_task_id(request) or trace_id
        session_id = _header_session_id(request)
        user_id = _header_user_id(request)
        workflow_name = request.url.path
        agent_name = "gov_core_api"
        started = time.perf_counter()

        _emit(
            build_trace_event(
                event="http_request_start",
                trace_id=trace_id,
                span_id=span_id,
                task_id=task_id,
                session_id=session_id,
                user_id=user_id,
                agent_name=agent_name,
                workflow_name=workflow_name,
                status="running",
                tool_name=request.method,
            )
        )

        status_code = 500
        error_type: str | None = None

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 500))
                headers = list(message.get("headers") or [])
                headers.append((b"x-trace-id", trace_id.encode()))
                headers.append((b"x-span-id", span_id.encode()))
                headers.append(
                    (b"x-trace-schema-version", GOV_TRACE_SCHEMA_VERSION.encode())
                )
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            error_type = "unknown"
            raise
        finally:
            latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
            success = 200 <= status_code < 400
            _emit(
                build_trace_event(
                    event="http_request_end",
                    trace_id=trace_id,
                    span_id=span_id,
                    task_id=task_id,
                    session_id=session_id,
                    user_id=user_id,
                    agent_name=agent_name,
                    workflow_name=workflow_name,
                    tool_name=request.method,
                    latency_ms=latency_ms,
                    status="success" if success else "failed",
                    error_type=error_type if not success else None,
                    http_status_code=status_code,
                )
            )
