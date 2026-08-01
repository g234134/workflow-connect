#!/usr/bin/env python3
"""Internal staging HMAC webhook receiver (non-prod only · P7 S3).

Stdlib HTTP server that verifies Gov signed POSTs via webhook_hmac_receiver_v1.
Supports response modes: ok (200), always_503, sequential_503_then_200.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.webhook_hmac_receiver_v1 import ReplayCache, verify_gov_webhook

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8765
DEFAULT_PATH = "/webhooks/gov/staging"
ENV_SECRET = "GOV_STAGING_RECEIVER_HMAC_SECRET"
ENV_MODE = "GOV_STAGING_RECEIVER_MODE"
ENV_TLS_CERT = "GOV_STAGING_RECEIVER_TLS_CERT"
ENV_TLS_KEY = "GOV_STAGING_RECEIVER_TLS_KEY"


class StagingReceiverState:
    def __init__(self) -> None:
        self.mode = "ok"
        self.secret = ""
        self.replay_cache = ReplayCache()
        self.received: List[Dict[str, Any]] = []
        self.call_count = 0
        self.lock = threading.Lock()

    def set_mode(self, mode: str) -> None:
        with self.lock:
            self.mode = mode

    def record(self, entry: Dict[str, Any]) -> None:
        with self.lock:
            self.received.append(entry)


STATE = StagingReceiverState()


def _build_handler(state: StagingReceiverState) -> type[BaseHTTPRequestHandler]:
    class StagingWebhookHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            headers = {k: v for k, v in self.headers.items()}

            with state.lock:
                state.call_count += 1
                call_no = state.call_count
                mode = state.mode

            verify_result = verify_gov_webhook(
                body_bytes=body_bytes,
                headers=headers,
                shared_secret=state.secret,
                replay_cache=state.replay_cache,
            )

            entry = {
                "call_no": call_no,
                "path": self.path,
                "mode": mode,
                "verify": verify_result.to_dict(),
            }
            state.record(entry)

            if not verify_result.ok:
                payload = json.dumps({"status": "rejected", "reason": verify_result.reason})
                self.send_response(verify_result.status_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload.encode("utf-8"))
                return

            if mode == "always_503":
                payload = json.dumps({"status": "injected_503"})
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload.encode("utf-8"))
                return

            if mode == "sequential_503_then_200" and call_no == 1:
                payload = json.dumps({"status": "injected_503_first"})
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload.encode("utf-8"))
                return

            payload = json.dumps(
                {
                    "status": "ok",
                    "idempotent": verify_result.idempotent,
                    "event_id": verify_result.event_id,
                }
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))

        def log_message(self, format: str, *args: Any) -> None:
            return

    return StagingWebhookHandler


class StagingWebhookReceiver:
    def __init__(
        self,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        path: str = DEFAULT_PATH,
        secret: str,
        mode: str = "ok",
        tls_cert: Optional[str] = None,
        tls_key: Optional[str] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.path = path
        self.secret = secret
        self.mode = mode
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.use_tls = bool(tls_cert and tls_key)
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        STATE.secret = secret
        STATE.set_mode(mode)
        STATE.received = []
        STATE.call_count = 0
        STATE.replay_cache = ReplayCache()

    @property
    def base_url(self) -> str:
        scheme = "https" if self.use_tls else "http"
        return f"{scheme}://{self.host}:{self.port}{self.path}"

    @property
    def allowlist_entry(self) -> str:
        return f"{self.host}:{self.port}{self.path}"

    def start(self) -> None:
        handler = _build_handler(STATE)
        self.server = HTTPServer((self.host, self.port), handler)
        if self.use_tls and self.tls_cert and self.tls_key:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(self.tls_cert, self.tls_key)
            self.server.socket = ctx.wrap_socket(self.server.socket, server_side=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread is not None:
            self.thread.join(timeout=5)
            self.thread = None

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        STATE.set_mode(mode)

    def get_received(self) -> List[Dict[str, Any]]:
        with STATE.lock:
            return list(STATE.received)


def main() -> int:
    parser = argparse.ArgumentParser(description="P7 internal staging webhook receiver")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--path", default=DEFAULT_PATH)
    parser.add_argument("--mode", default=os.getenv(ENV_MODE, "ok"))
    args = parser.parse_args()

    secret = os.getenv(ENV_SECRET, "").strip()
    if not secret:
        print(f"[FAILED] {ENV_SECRET} not set", file=sys.stderr)
        return 1

    receiver = StagingWebhookReceiver(
        host=args.host,
        port=args.port,
        path=args.path,
        secret=secret,
        mode=args.mode,
    )
    receiver.start()
    print(f"[OK] staging receiver listening on {receiver.base_url} mode={args.mode}")
    try:
        if receiver.thread is not None:
            receiver.thread.join()
    except KeyboardInterrupt:
        receiver.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
