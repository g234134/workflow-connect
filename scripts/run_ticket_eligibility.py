#!/usr/bin/env python3
"""CLI / minimal REST for ticket eligibility (WC-T1).

Usage:
    python scripts/run_ticket_eligibility.py --ticket W1-T2
    python scripts/run_ticket_eligibility.py --ticket TEST-BLK --requested-role implementer
    python scripts/run_ticket_eligibility.py --ticket W1-T1 --context-json '{"requested_role":"reviewer"}'
    python scripts/run_ticket_eligibility.py --serve 8765
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / "04_Workflows"
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))

from ticket_eligibility import (  # noqa: E402
    EligibilityContext,
    check_ticket_eligibility,
)


def _parse_context_json(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("context-json must be a JSON object")
    return data


def _build_context(args: argparse.Namespace) -> dict[str, Any] | None:
    ctx: dict[str, Any] = {}
    if args.context_json:
        ctx.update(_parse_context_json(args.context_json) or {})
    if args.requested_role:
        ctx["requested_role"] = args.requested_role
    if args.wave:
        ctx["wave"] = args.wave
    if args.phase:
        ctx["phase"] = args.phase
    if args.notes:
        ctx["notes"] = [n.strip() for n in args.notes.split(",") if n.strip()]
    return ctx or None


def run_check(
    ticket_id: str,
    *,
    repo_root: Path,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return check_ticket_eligibility(ticket_id, repo_root, context=context)


def _format_text(result: dict[str, Any]) -> str:
    lines = [
        "Ticket Eligibility (WC-T1)",
        f"ticket_id: {result.get('ticket_id')}",
        f"eligible: {result.get('eligible')}",
        f"bucket: {result.get('bucket', '—')}",
        f"recommended_role: {result.get('recommended_role', '—')}",
        "",
        "reasons:",
    ]
    for reason in result.get("reasons") or []:
        lines.append(f"  - {reason}")
    if result.get("warnings"):
        lines.extend(["", "warnings:"])
        for w in result["warnings"]:
            lines.append(f"  - {w}")
    lines.append("")
    lines.append(f"message: {result.get('message', '')}")
    return "\n".join(lines)


def make_handler(repo_root: Path):
    class EligibilityHandler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("request body must be a JSON object")
            return data

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._send_json(200, {"ok": True, "service": "ticket_eligibility_v1"})
                return

            prefix = "/api/v1/tickets/"
            suffix = "/eligibility"
            if not parsed.path.startswith(prefix) or not parsed.path.endswith(suffix):
                self._send_json(404, {"ok": False, "message": "not_found"})
                return

            ticket_id = parsed.path[len(prefix) : -len(suffix)]
            if not ticket_id:
                self._send_json(400, {"ok": False, "message": "ticket_id_required"})
                return

            qs = parse_qs(parsed.query)
            context: dict[str, Any] = {}
            if "requested_role" in qs:
                context["requested_role"] = qs["requested_role"][0]
            if "wave" in qs:
                context["wave"] = qs["wave"][0]
            if "phase" in qs:
                context["phase"] = qs["phase"][0]

            result = run_check(ticket_id, repo_root=repo_root, context=context or None)
            status = 200 if result.get("ok", True) else 404
            self._send_json(status, result)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/api/v1/tickets/eligibility":
                self._send_json(404, {"ok": False, "message": "not_found"})
                return
            try:
                body = self._read_json_body()
            except (json.JSONDecodeError, ValueError) as exc:
                self._send_json(400, {"ok": False, "message": str(exc)})
                return

            ticket_id = str(body.get("ticket_id") or "").strip()
            if not ticket_id:
                self._send_json(400, {"ok": False, "message": "ticket_id_required"})
                return

            context_raw = body.get("context")
            context = context_raw if isinstance(context_raw, dict) else None
            if body.get("requested_role") and context is None:
                context = {"requested_role": body["requested_role"]}
            elif body.get("requested_role") and context is not None:
                context.setdefault("requested_role", body["requested_role"])

            result = run_check(ticket_id, repo_root=repo_root, context=context)
            status = 200 if result.get("ok", True) else 404
            self._send_json(status, result)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    return EligibilityHandler


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether a Multi-Chat ticket is eligible for acceptance (WC-T1).",
    )
    parser.add_argument("--ticket", help="Ticket id (e.g. W1-T2, TEST-BLK)")
    parser.add_argument(
        "--requested-role",
        choices=("implementer", "reviewer", "scribe", "orchestrator"),
        help="Supplemental context: role requesting acceptance",
    )
    parser.add_argument("--wave", help="Override inferred wave label")
    parser.add_argument("--phase", help="Override inferred phase label")
    parser.add_argument("--notes", help="Comma-separated context notes")
    parser.add_argument("--context-json", help="JSON object with supplemental context")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument(
        "--serve",
        type=int,
        metavar="PORT",
        help="Start minimal REST server on PORT (GET/POST eligibility endpoints)",
    )
    args = parser.parse_args()

    if args.serve:
        handler = make_handler(_REPO_ROOT)
        server = ThreadingHTTPServer(("127.0.0.1", args.serve), handler)
        print(
            json.dumps(
                {
                    "ok": True,
                    "listening": f"http://127.0.0.1:{args.serve}",
                    "endpoints": [
                        "GET /health",
                        "GET /api/v1/tickets/<ticket_id>/eligibility",
                        "POST /api/v1/tickets/eligibility",
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
        return 0

    if not args.ticket:
        parser.error("--ticket is required unless --serve is used")

    context = _build_context(args)
    result = run_check(args.ticket, repo_root=_REPO_ROOT, context=context)

    if args.format == "text":
        print(_format_text(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
