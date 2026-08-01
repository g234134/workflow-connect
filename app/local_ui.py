#!/usr/bin/env python3
"""Minimal local Web UI — wraps MVP CLI scripts via subprocess (W-MVP-W5-LOCAL-UI).

Usage:
    python app/local_ui.py
    python app/local_ui.py --port 8765

INTERNAL · LOCAL MVP · NOT PROD · single-user localhost only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_REPO_ROOT = Path(__file__).resolve().parents[1]
_APP_DIR = Path(__file__).resolve().parent
_SCRIPTS = {
    "lookup": _REPO_ROOT / "scripts" / "lookup_case_history.py",
    "new_case": _REPO_ROOT / "scripts" / "new_cleaning_case.py",
    "e2e": _REPO_ROOT / "scripts" / "run_case_e2e_validation.py",
    "reindex": _REPO_ROOT / "scripts" / "build_cases_index.py",
}

_SUMMARY_RE = re.compile(r"^case_dir:\s*(.+)$", re.MULTILINE)


def _parse_json_from_stdout(text: str) -> dict[str, Any]:
    """Extract the first JSON object from subprocess stdout."""
    start = text.find("{")
    if start < 0:
        return {}
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    return {}


def _run_cli(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _api_response(
    *,
    ok: bool,
    action: str,
    data: dict[str, Any] | list[Any] | None = None,
    stderr: str = "",
    message: str = "",
    exit_code: int | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "ok": ok,
        "action": action,
        "data": data if data is not None else {},
    }
    if message:
        body["message"] = message
    if stderr:
        body["stderr"] = stderr[:2000]
    if exit_code is not None:
        body["exit_code"] = exit_code
    return body


def run_lookup(
    *,
    client_ref: str | None = None,
    product_sku: str | None = None,
    schema_headers: str | None = None,
    list_all: bool = False,
) -> dict[str, Any]:
    cmd = [sys.executable, str(_SCRIPTS["lookup"])]
    if list_all:
        cmd.append("--list-all")
    if client_ref:
        cmd.extend(["--client-ref", client_ref])
    if product_sku:
        cmd.extend(["--product-sku", product_sku])
    if schema_headers:
        cmd.extend(["--schema-headers", schema_headers])
    if not list_all and not any([client_ref, product_sku, schema_headers]):
        return _api_response(
            ok=False,
            action="lookup",
            message="Specify at least one filter or list_all",
        )

    run = _run_cli(cmd)
    data = _parse_json_from_stdout(run["stdout"])
    ok = bool(data.get("ok")) and run["exit_code"] == 0
    return _api_response(
        ok=ok,
        action="lookup",
        data=data,
        stderr=run["stderr"],
        message=data.get("message", "") if not ok else "",
        exit_code=run["exit_code"],
    )


def run_new_case(
    *,
    source_file: str,
    client_ref: str,
    product_sku: str,
    encoding: str = "utf-8",
    delimiter: str = ",",
    file_format: str | None = None,
    run_gate: bool = True,
) -> dict[str, Any]:
    src = Path(source_file)
    if not src.is_absolute():
        src = (_REPO_ROOT / src).resolve()
    cmd = [
        sys.executable,
        str(_SCRIPTS["new_case"]),
        "--client-ref",
        client_ref,
        "--product-sku",
        product_sku,
        "--source-file",
        str(src),
        "--encoding",
        encoding,
        "--delimiter",
        delimiter,
    ]
    if file_format:
        cmd.extend(["--file-format", file_format])
    if run_gate:
        cmd.append("--run-gate")

    run = _run_cli(cmd)
    gate_data = _parse_json_from_stdout(run["stdout"]) if run_gate else {}
    case_dir_rel = ""
    match = _SUMMARY_RE.search(run["stdout"])
    if match:
        case_dir_rel = match.group(1).strip()

    gate_status = gate_data.get("eligibility", "not_run" if not run_gate else "unknown")
    schema = (gate_data.get("dimensions") or {}).get("schema") or {}

    summary = {
        "case_dir": case_dir_rel or gate_data.get("case_dir", ""),
        "gate_status": gate_status,
        "schema": {
            "notes": schema.get("notes") or [],
            "warnings": schema.get("warnings") or [],
        },
        "gate": gate_data,
        "stdout_tail": run["stdout"][-1500:] if run["stdout"] else "",
    }

    ok = run["exit_code"] == 0
    return _api_response(
        ok=ok,
        action="new-case",
        data=summary,
        stderr=run["stderr"],
        message=run["stderr"].strip() or ("" if ok else "new_cleaning_case failed"),
        exit_code=run["exit_code"],
    )


def _gate_schema_fields(case_dir: Path) -> dict[str, list[str]]:
    """Read-only gate subprocess for UI display (no eligibility logic in UI)."""
    gate_script = _REPO_ROOT / "scripts" / "check_case_eligibility.py"
    run = _run_cli(
        [sys.executable, str(gate_script), "--case-dir", str(case_dir), "--json"]
    )
    gate = _parse_json_from_stdout(run["stdout"])
    schema = (gate.get("dimensions") or {}).get("schema") or {}
    notes = schema.get("notes")
    warnings = schema.get("warnings")
    return {
        "notes": notes if isinstance(notes, list) else [],
        "warnings": warnings if isinstance(warnings, list) else [],
    }


def run_e2e(*, case_dir: str) -> dict[str, Any]:
    path = Path(case_dir)
    if not path.is_absolute():
        path = (_REPO_ROOT / path).resolve()
    cmd = [
        sys.executable,
        str(_SCRIPTS["e2e"]),
        "--case-dir",
        str(path),
        "--json",
    ]
    run = _run_cli(cmd)
    data = _parse_json_from_stdout(run["stdout"])
    if data:
        data["overall_ok"] = data.get("ok")
        data["gate_status"] = data.get("eligibility")
        schema_fields = _gate_schema_fields(path)
        data["schema_notes"] = schema_fields["notes"]
        data["schema_warnings"] = schema_fields["warnings"]
    ok = bool(data.get("ok")) and run["exit_code"] == 0
    return _api_response(
        ok=ok,
        action="e2e",
        data=data,
        stderr=run["stderr"],
        message=data.get("message", "") if data else run["stderr"].strip(),
        exit_code=run["exit_code"],
    )


def run_reindex() -> dict[str, Any]:
    cmd = [sys.executable, str(_SCRIPTS["reindex"])]
    run = _run_cli(cmd)
    data = _parse_json_from_stdout(run["stdout"])
    if not data and run["stdout"].strip():
        data = {"stdout": run["stdout"].strip()}
    ok = run["exit_code"] == 0
    return _api_response(
        ok=ok,
        action="reindex",
        data=data,
        stderr=run["stderr"],
        exit_code=run["exit_code"],
    )


def _read_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", 0))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _send_json(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _send_bytes(
    handler: BaseHTTPRequestHandler,
    data: bytes,
    content_type: str,
    status: int = 200,
) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class LocalUIHandler(BaseHTTPRequestHandler):
    server_version = "LocalMVPUI/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[local-ui] " + (fmt % args) + "\n")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            html_path = _APP_DIR / "templates" / "local-ui.html"
            _send_bytes(self, html_path.read_bytes(), "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            rel = path[len("/static/") :]
            static_path = (_APP_DIR / "static" / rel).resolve()
            if not str(static_path).startswith(str((_APP_DIR / "static").resolve())):
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            if not static_path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            ctype = "text/css" if rel.endswith(".css") else "application/javascript"
            _send_bytes(self, static_path.read_bytes(), ctype)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = _read_body(self)
        if path == "/api/lookup":
            _send_json(
                self,
                run_lookup(
                    client_ref=(body.get("client_ref") or "").strip() or None,
                    product_sku=(body.get("product_sku") or "").strip() or None,
                    schema_headers=(body.get("schema_headers") or "").strip() or None,
                    list_all=bool(body.get("list_all")),
                ),
            )
            return
        if path == "/api/new-case":
            _send_json(
                self,
                run_new_case(
                    source_file=(body.get("source_file") or "").strip(),
                    client_ref=(body.get("client_ref") or "").strip(),
                    product_sku=(body.get("product_sku") or "CLEAN-BASIC").strip(),
                    encoding=(body.get("encoding") or "utf-8").strip(),
                    delimiter=(body.get("delimiter") or ",").strip(),
                    file_format=(body.get("file_format") or "").strip() or None,
                    run_gate=body.get("run_gate", True) is not False,
                ),
            )
            return
        if path == "/api/e2e":
            case_dir = (body.get("case_dir") or "").strip()
            if not case_dir:
                _send_json(
                    self,
                    _api_response(ok=False, action="e2e", message="case_dir is required"),
                    status=400,
                )
                return
            _send_json(self, run_e2e(case_dir=case_dir))
            return
        if path == "/api/reindex":
            _send_json(self, run_reindex())
            return
        self.send_error(HTTPStatus.NOT_FOUND)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local MVP Web UI (CLI wrapper · NOT PROD)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765)")
    args = parser.parse_args(argv)

    server = ThreadingHTTPServer((args.host, args.port), LocalUIHandler)
    url = f"http://{args.host}:{args.port}/"
    print("=== Local MVP UI ===")
    print("INTERNAL · LOCAL MVP · NOT PROD · single-user localhost only")
    print(f"Open in browser: {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
