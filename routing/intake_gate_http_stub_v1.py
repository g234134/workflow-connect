"""P7.5 Intake Gate local HTTP stub v1 (P75-G7).

Exposes POST /api/intake/gate wrapping ``evaluate_intake_gate``.
Loopback-only; default mode=preview (no outbox write).

Design SSOT: docs/p75-intake-gate-http-stub-v1.md

Honest boundaries:
  - ≠ prod app_api / dark-ops HTTP surface
  - ≠ Web UI · ≠ Phase closure · ≠ mandatory CI
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple
from urllib.parse import urlparse

from delivery.notification_gateway_v1 import emit_intake_gate_decision_notification
from routing.intake_gate_layer_v1 import evaluate_intake_gate

SCHEMA_VERSION = "intake_gate_http_stub_v1"
DOC_REL = "docs/p75-intake-gate-http-stub-v1.md"
SERVICE_NAME = "intake_gate_http_stub_v1"
GATE_PATH = "/api/intake/gate"
ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return (repo_root or _REPO_ROOT).resolve()


def _error_body(
    message: str,
    *,
    http_status: int,
    code: str,
) -> Dict[str, Any]:
    return {
        "ok": False,
        "schema_version": SCHEMA_VERSION,
        "message": message,
        "error_code": code,
        "http": {
            "status": http_status,
            "path": GATE_PATH,
            "stub": True,
            "service": SERVICE_NAME,
        },
        "gate": None,
        "notification": None,
        "contract_ref": DOC_REL,
    }


def handle_gate_request(
    body: Mapping[str, Any],
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Evaluate intake gate from a JSON request body.

    Returns (http_status, response_dict).
    """
    root = _repo_root(repo_root)
    if not isinstance(body, Mapping):
        return 400, _error_body("body must be a JSON object", http_status=400, code="invalid_body")

    task_type = body.get("task_type")
    case_dir = body.get("case_dir")
    if not isinstance(task_type, str) or not task_type.strip():
        return 400, _error_body("task_type is required", http_status=400, code="missing_task_type")
    if not isinstance(case_dir, str) or not case_dir.strip():
        return 400, _error_body("case_dir is required", http_status=400, code="missing_case_dir")

    mode_raw = body.get("mode", "preview")
    mode = str(mode_raw or "preview").strip().lower()
    if mode not in ("preview", "run"):
        return 400, _error_body(
            "mode must be preview|run",
            http_status=400,
            code="invalid_mode",
        )

    policy_path = body.get("policy_path")
    if policy_path is not None and not isinstance(policy_path, str):
        return 400, _error_body(
            "policy_path must be a string when set",
            http_status=400,
            code="invalid_policy_path",
        )

    flags_raw = body.get("flags") if isinstance(body.get("flags"), Mapping) else {}
    flags: Dict[str, Any] = dict(flags_raw) if flags_raw else {}
    if body.get("include_extended_fixtures"):
        flags["include_extended_fixtures"] = True

    outbox = outbox_root_override
    if isinstance(body.get("outbox_root"), str) and body.get("outbox_root"):
        outbox = str(body["outbox_root"])

    use_v1_fallback = not bool(body.get("no_v1_fallback"))
    enable_notifications = bool(body.get("enable_notifications"))

    gate = evaluate_intake_gate(
        task_type.strip(),
        case_dir.strip(),
        mode=mode,  # type: ignore[arg-type]
        policy_path=policy_path,
        flags=flags or None,
        use_v1_fallback=use_v1_fallback,
        repo_root=root,
        outbox_root_override=outbox,
    )

    notification: Optional[Dict[str, Any]] = None
    if (
        mode == "run"
        and enable_notifications
        and gate.get("ok")
        and gate.get("outbox_record_path")
    ):
        notify_result = emit_intake_gate_decision_notification(
            gate,
            enabled=True,
            repo_root=root,
            outbox_root_override=outbox,
        )
        if notify_result is not None:
            notification = {
                "event_type": "intake.gate_decision",
                "ok": notify_result.get("ok"),
                "event_id": notify_result.get("event_id"),
                "path": (notify_result.get("sink_result") or {}).get("path"),
                "message": notify_result.get("message"),
            }

    http_status = 200 if gate.get("ok") else 422
    payload: Dict[str, Any] = {
        "ok": bool(gate.get("ok")),
        "schema_version": SCHEMA_VERSION,
        "message": "gate evaluated" if gate.get("ok") else str(gate.get("message") or "gate failed"),
        "http": {
            "status": http_status,
            "path": GATE_PATH,
            "stub": True,
            "service": SERVICE_NAME,
            "mode": mode,
        },
        "gate": gate,
        "notification": notification,
        "contract_ref": DOC_REL,
    }
    return http_status, payload


def make_handler(
    repo_root: Path,
    *,
    outbox_root_override: Optional[str] = None,
):
    root = _repo_root(repo_root)

    class IntakeGateHttpStubHandler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "service": SERVICE_NAME,
                        "schema_version": SCHEMA_VERSION,
                        "stub": True,
                        "endpoints": ["GET /health", f"POST {GATE_PATH}"],
                        "contract_ref": DOC_REL,
                    },
                )
                return
            self._send_json(404, {"ok": False, "error": "not_found", "stub": True})

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != GATE_PATH:
                self._send_json(404, {"ok": False, "error": "not_found", "stub": True})
                return

            length_raw = self.headers.get("Content-Length") or "0"
            try:
                length = int(length_raw)
            except ValueError:
                self._send_json(
                    400,
                    _error_body("invalid Content-Length", http_status=400, code="invalid_length"),
                )
                return

            raw = self.rfile.read(max(0, length)) if length > 0 else b"{}"
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(
                    400,
                    _error_body("body must be valid JSON", http_status=400, code="invalid_json"),
                )
                return

            status, payload = handle_gate_request(
                body if isinstance(body, dict) else {},
                repo_root=root,
                outbox_root_override=outbox_root_override,
            )
            self._send_json(status, payload)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    return IntakeGateHttpStubHandler


def create_server(
    host: str,
    port: int,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> ThreadingHTTPServer:
    """Create loopback HTTP stub server (does not start serving)."""
    host_norm = (host or "127.0.0.1").strip().lower()
    if host_norm not in ALLOWED_HOSTS:
        raise ValueError(
            f"host must be loopback only ({', '.join(sorted(ALLOWED_HOSTS))}); got {host!r}"
        )
    root = _repo_root(repo_root)
    handler = make_handler(root, outbox_root_override=outbox_root_override)
    return ThreadingHTTPServer((host_norm, port), handler)


def serve(
    port: int,
    *,
    host: str = "127.0.0.1",
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> None:
    import sys

    server = create_server(
        host,
        port,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "listening": f"http://{host}:{port}",
                "stub": True,
                "service": SERVICE_NAME,
                "endpoints": ["GET /health", f"POST {GATE_PATH}"],
                "default_mode": "preview",
                "contract_ref": DOC_REL,
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
