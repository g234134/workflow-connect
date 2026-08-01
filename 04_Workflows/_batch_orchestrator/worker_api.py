"""Batch Worker API v1 — real callable HTTP worker for batch orchestrator.

Serves ``POST /api/batch/worker/run`` and returns a stable dict matching the
batch ``ExecutionResult`` contract. This is the non-mock worker surface that
``runner_worker_api`` calls over HTTP.

Honest boundaries:
  - Executes the Worker *API contract* (prompt build + structured result).
  - Does **not** spawn Cursor Multi-Chat / write ticket state / Progress.
  - ≠ production remote fleet; local or env-configured base URL only.
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

SCHEMA_VERSION = "batch_worker_api_v1"
DEFAULT_PATH = "/api/batch/worker/run"
ENV_WORKER_API_URL = "GOV_BATCH_WORKER_API_URL"


def handle_worker_run(body: Mapping[str, Any]) -> dict[str, Any]:
    """In-process Worker API handler (also used by the HTTP server).

    Expected body keys (partial OK):
      - subtask_id / subtask
      - prompt (optional; built when missing)
      - parent_frame (optional)
      - force_fail (optional bool; test hook)
    """
    started = time.perf_counter()
    result: dict[str, Any] = {
        "ok": False,
        "schema_version": SCHEMA_VERSION,
        "status": "failed",
        "subtask_id": "",
        "message": "",
        "latency_ms": 0.0,
        "prompt": None,
        "error": None,
        "worker": SCHEMA_VERSION,
        "writes_ticket_state": False,
    }

    if not isinstance(body, Mapping):
        result["message"] = "body must be a JSON object"
        result["error"] = "invalid_body"
        result["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 3)
        return result

    subtask = body.get("subtask")
    if not isinstance(subtask, Mapping):
        subtask = {}
    subtask = dict(subtask)

    sid = str(body.get("subtask_id") or subtask.get("subtask_id") or "").strip()
    if not sid:
        sid = "anon"
    result["subtask_id"] = sid

    parent_frame = body.get("parent_frame")
    if not isinstance(parent_frame, Mapping):
        parent_frame = {}
    parent_frame = dict(parent_frame)

    prompt = body.get("prompt")
    if not isinstance(prompt, dict):
        from .prompt_builder import build_implementer_prompt

        prompt = build_implementer_prompt(subtask, parent_frame)
    result["prompt"] = prompt

    if bool(body.get("force_fail")):
        result.update(
            {
                "ok": False,
                "status": "failed",
                "message": f"worker forced failure for {sid}",
                "error": "force_fail",
            }
        )
    else:
        result.update(
            {
                "ok": True,
                "status": "success",
                "message": f"worker_api accepted subtask {sid}",
                "error": None,
            }
        )

    result["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 3)
    return result


class _WorkerAPIHandler(BaseHTTPRequestHandler):
    """HTTP adapter around :func:`handle_worker_run`."""

    server_version = "BatchWorkerAPI/1.0"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/healthz", "/health"):
            self._json_response(200, {"ok": True, "schema_version": SCHEMA_VERSION})
            return
        self._json_response(404, {"ok": False, "message": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != DEFAULT_PATH:
            self._json_response(
                404,
                {
                    "ok": False,
                    "message": f"unknown path {parsed.path!r}; expected {DEFAULT_PATH}",
                },
            )
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json_response(
                400,
                {"ok": False, "message": "invalid JSON body", "error": "invalid_json"},
            )
            return

        if not isinstance(body, dict):
            self._json_response(
                400,
                {"ok": False, "message": "JSON body must be an object", "error": "invalid_body"},
            )
            return

        payload = handle_worker_run(body)
        # Contract failures still return HTTP 200 with ok=false (bridge-style).
        self._json_response(200, payload)

    def _json_response(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class WorkerAPIServer:
    """Threading HTTP server for the batch Worker API (tests / local probe)."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        self.host = host
        self.port = port
        self.server: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.base_url: str = ""

    def __enter__(self) -> "WorkerAPIServer":
        self.server = ThreadingHTTPServer((self.host, self.port), _WorkerAPIHandler)
        self.port = int(self.server.server_address[1])
        self.base_url = f"http://{self.host}:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=2)

    @property
    def run_url(self) -> str:
        return f"{self.base_url}{DEFAULT_PATH}"


def serve_forever(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Blocking server entry (CLI helper)."""
    httpd = ThreadingHTTPServer((host, port), _WorkerAPIHandler)
    print(
        json.dumps(
            {
                "ok": True,
                "schema_version": SCHEMA_VERSION,
                "message": "batch worker API listening",
                "base_url": f"http://{host}:{port}",
                "run_path": DEFAULT_PATH,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    httpd.serve_forever()
