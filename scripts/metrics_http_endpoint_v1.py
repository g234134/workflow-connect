#!/usr/bin/env python3
"""Minimal read-only HTTP endpoint for standard-case metrics v1 (MP-METRICS-HTTP).

Exposes GET /metrics with Prometheus text from `export_std_case_metrics_v1`.
No mutations.

Usage:
    python scripts/metrics_http_endpoint_v1.py --port 9090
    curl 'http://127.0.0.1:9090/metrics?case_ref=demo_phase'
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional, Tuple
from urllib.parse import parse_qs, urlparse

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.export_std_case_metrics_v1 import (
    export_std_case_metrics,
    format_std_case_metrics_prometheus,
)

DEFAULT_CASE_REF = "demo_phase"
SERVICE_NAME = "metrics_http_endpoint_v1"


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return (repo_root or _REPO_ROOT).resolve()


def get_metrics_text(
    *,
    case_ref: str = DEFAULT_CASE_REF,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Tuple[int, str]:
    """Build HTTP status and Prometheus text body for /metrics.

    Always returns HTTP 200 so Prometheus scrapes succeed; exporter failures
    are surfaced as ``# error: ...`` comment lines with zeroed gauge values.
    """
    result = export_std_case_metrics(
        case_ref,
        repo_root=_repo_root(repo_root),
        outbox_root_override=outbox_root_override,
    )
    return 200, format_std_case_metrics_prometheus(result)


def make_handler(
    repo_root: Path,
    *,
    default_case_ref: str = DEFAULT_CASE_REF,
    outbox_root_override: Optional[str] = None,
):
    root = _repo_root(repo_root)

    class MetricsHandler(BaseHTTPRequestHandler):
        def _send_text(self, status: int, body: str, content_type: str = "text/plain") -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._send_text(
                    200,
                    json.dumps(
                        {"ok": True, "service": SERVICE_NAME, "read_only": True},
                        ensure_ascii=False,
                    ),
                    content_type="application/json",
                )
                return

            if parsed.path != "/metrics":
                self._send_text(404, "# error: not_found\n")
                return

            qs = parse_qs(parsed.query)
            case_ref = qs.get("case_ref", [default_case_ref])[0] or default_case_ref

            http_status, body = get_metrics_text(
                case_ref=case_ref,
                repo_root=root,
                outbox_root_override=outbox_root_override,
            )
            self._send_text(http_status, body)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    return MetricsHandler


def serve(
    port: int,
    *,
    host: str = "127.0.0.1",
    repo_root: Optional[Path] = None,
    default_case_ref: str = DEFAULT_CASE_REF,
    outbox_root_override: Optional[str] = None,
) -> ThreadingHTTPServer:
    root = _repo_root(repo_root)
    handler = make_handler(
        root,
        default_case_ref=default_case_ref,
        outbox_root_override=outbox_root_override,
    )
    server = ThreadingHTTPServer((host, port), handler)
    print(
        json.dumps(
            {
                "ok": True,
                "listening": f"http://{host}:{server.server_address[1]}",
                "read_only": True,
                "default_case_ref": default_case_ref,
                "endpoints": [
                    "GET /health",
                    f"GET /metrics?case_ref=<slug> (default: {default_case_ref})",
                ],
                "error_policy": "HTTP 200 with # error: comment when export fails",
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only HTTP endpoint for standard-case Prometheus metrics.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9090,
        help="Listen port (default: 9090)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Listen host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--default-case-ref",
        default=DEFAULT_CASE_REF,
        help=f"Default case_ref when query param omitted (default: {DEFAULT_CASE_REF})",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument("--outbox-root", default=None, help="Optional outbox root override")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    server = serve(
        args.port,
        host=args.host,
        repo_root=repo_root,
        default_case_ref=args.default_case_ref,
        outbox_root_override=args.outbox_root,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
