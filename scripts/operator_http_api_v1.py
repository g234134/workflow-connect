#!/usr/bin/env python3
"""Minimal read-only HTTP API for operator backlog v1 (P8-API).

Exposes GET /operator/backlog with the same JSON shape as
`list_operator_backlog_v1.py --format json`. No mutations.

Usage:
    python scripts/operator_http_api_v1.py --port 8080
    curl 'http://127.0.0.1:8080/operator/backlog?status=pending'
    curl 'http://127.0.0.1:8080/operator/backlog?case_ref=demo_phase'
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.list_operator_backlog_v1 import list_operator_backlog

VALID_STATUSES = frozenset({"pending", "blocked", "completed"})
SERVICE_NAME = "operator_http_api_v1"


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return (repo_root or _REPO_ROOT).resolve()


def get_operator_backlog(
    *,
    status: Optional[str] = None,
    case_ref: Optional[str] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Build HTTP status and JSON body for operator backlog read model."""
    if status is not None and status not in VALID_STATUSES:
        return 400, {"error": "invalid status"}

    result = list_operator_backlog(
        case_ref=case_ref,
        status=status,
        repo_root=_repo_root(repo_root),
        outbox_root_override=outbox_root_override,
    )
    return 200, result


def make_handler(
    repo_root: Path,
    *,
    outbox_root_override: Optional[str] = None,
):
    root = _repo_root(repo_root)

    class OperatorBacklogHandler(BaseHTTPRequestHandler):
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
                    {"ok": True, "service": SERVICE_NAME, "read_only": True},
                )
                return

            if parsed.path != "/operator/backlog":
                self._send_json(404, {"error": "not_found"})
                return

            qs = parse_qs(parsed.query)
            status = qs.get("status", [None])[0]
            case_ref = qs.get("case_ref", [None])[0]

            http_status, payload = get_operator_backlog(
                status=status,
                case_ref=case_ref,
                repo_root=root,
                outbox_root_override=outbox_root_override,
            )
            self._send_json(http_status, payload)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    return OperatorBacklogHandler


def serve(
    port: int,
    *,
    host: str = "127.0.0.1",
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> None:
    root = _repo_root(repo_root)
    handler = make_handler(root, outbox_root_override=outbox_root_override)
    server = ThreadingHTTPServer((host, port), handler)
    print(
        json.dumps(
            {
                "ok": True,
                "listening": f"http://{host}:{port}",
                "read_only": True,
                "endpoints": [
                    "GET /health",
                    "GET /operator/backlog?status=pending|blocked|completed",
                    "GET /operator/backlog?case_ref=<slug>",
                ],
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only HTTP API for operator backlog (operator_backlog_v1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Listen port (default: 8080)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Listen host (default: 127.0.0.1)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument("--outbox-root", default=None, help="Optional outbox root override")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    serve(
        args.port,
        host=args.host,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
