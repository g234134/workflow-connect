#!/usr/bin/env python3
"""P5 health bundle CLI v1 — one entry for health + metrics + grafana stub.

Ticket: P5-HEALTH-BUNDLE-CLI-v1
Design: docs/p5-health-bundle-cli-v1.md

Usage:
    python scripts/run_p5_health_bundle_cli_v1.py --format json
    python scripts/run_p5_health_bundle_cli_v1.py --format text
    python scripts/run_p5_health_bundle_cli_v1.py --write
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from observability.p5_metrics_grafana_stub_v1 import (  # noqa: E402
    DEFAULT_CASE_REF,
    build_grafana_stub,
)
from scripts.export_std_case_metrics_v1 import export_std_case_metrics  # noqa: E402
from scripts.metrics_http_endpoint_v1 import get_metrics_text  # noqa: E402
from scripts.run_toolchain_health_dashboard import build_toolchain_health  # noqa: E402

_SCHEMA_VERSION = "p5_health_bundle_v1"
_DOC_REL = "docs/p5-health-bundle-cli-v1.md"
_DEFAULT_ARTIFACT = "artifacts/p5_health/health_bundle.latest.json"
_NON_CLAIMS = (
    "≠ live Grafana deployed",
    "≠ PG soak / prod Prometheus",
    "≠ DarkOps monitoring takeover",
    "≠ Phase% apply",
)


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_health_bundle(
    *,
    case_ref: str = DEFAULT_CASE_REF,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    write_artifact: bool = False,
    artifact_path_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble health + metrics scrape + grafana stub into one dict."""
    root = (repo_root or _REPO_ROOT).resolve()
    norm_case = (case_ref or DEFAULT_CASE_REF).replace("\\", "/").strip("/") or DEFAULT_CASE_REF

    health = build_toolchain_health(repo_root=root, dry_run=True)
    exported = export_std_case_metrics(
        norm_case,
        repo_root=root,
        outbox_root_override=outbox_root_override,
    )
    http_status, body = get_metrics_text(
        case_ref=norm_case,
        repo_root=root,
        outbox_root_override=outbox_root_override,
    )
    has_error = "# error:" in (body or "")
    scrape_ok = bool(exported.get("ok")) and not has_error and http_status == 200
    metrics_block: Dict[str, Any] = {
        "scrape_ok": scrape_ok,
        "source": "std_case_metrics_v1",
        "http_status": http_status,
        "has_error_comment": has_error,
        "prometheus_line_count": len([ln for ln in (body or "").splitlines() if ln.strip()]),
        "message": str(exported.get("message") or "metrics text assembled"),
    }
    stub = build_grafana_stub(
        case_ref=norm_case,
        repo_root=root,
        outbox_root_override=outbox_root_override,
        write_artifact=False,
    )

    health_ok = bool(health.get("ok"))
    stub_ok = bool(stub.get("ok"))
    overall_ok = health_ok and scrape_ok and stub_ok
    parts = []
    if not health_ok:
        parts.append("health.ok=false")
    if not scrape_ok:
        parts.append("metrics.scrape_ok=false")
    if not stub_ok:
        parts.append("stub.ok=false")
    message = (
        "p5 health bundle assembled"
        if overall_ok
        else "p5 health bundle degraded: " + ", ".join(parts)
    )

    result: Dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "ok": overall_ok,
        "mode": "local_bundle",
        "generated_at": _utc_now_iso(),
        "case_ref": norm_case,
        "sections": {
            "health": {
                "ok": health_ok,
                "source": "toolchain_health_v1",
                "schema_version": health.get("schema_version"),
                "gate_class": health.get("gate_class"),
                "message": health.get("message"),
            },
            "metrics": metrics_block,
            "grafana_stub": {
                "ok": stub_ok,
                "source": "p5_metrics_grafana_stub_v1",
                "schema_version": stub.get("schema_version"),
                "mode": stub.get("mode"),
                "message": stub.get("message"),
            },
        },
        "artifact_path": None,
        "doc": _DOC_REL,
        "message": message,
        "non_claims": list(_NON_CLAIMS),
    }

    if write_artifact:
        out = (
            Path(artifact_path_override)
            if artifact_path_override
            else root / _DEFAULT_ARTIFACT
        )
        if not out.is_absolute():
            out = root / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            result["artifact_path"] = str(out.relative_to(root)).replace("\\", "/")
        except ValueError:
            result["artifact_path"] = str(out)

    return result


def _format_text(result: Dict[str, Any]) -> str:
    sections = result.get("sections") or {}
    health = sections.get("health") or {}
    metrics = sections.get("metrics") or {}
    stub = sections.get("grafana_stub") or {}
    lines = [
        "P5 Health Bundle CLI v1 (local only)",
        f"doc: {result.get('doc') or _DOC_REL}",
        f"ok: {result.get('ok')}",
        f"case_ref: {result.get('case_ref')}",
        f"health.ok: {health.get('ok')} (source={health.get('source')})",
        f"metrics.scrape_ok: {metrics.get('scrape_ok')} (source={metrics.get('source')})",
        f"stub.ok: {stub.get('ok')} (source={stub.get('source')})",
        f"message: {result.get('message')}",
    ]
    if result.get("artifact_path"):
        lines.append(f"artifact_path: {result.get('artifact_path')}")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="P5 health+metrics+stub one-entry CLI (≠ live Grafana / PG soak).",
    )
    parser.add_argument(
        "--case-ref",
        default=DEFAULT_CASE_REF,
        help=f"Case for metrics scrape (default: {DEFAULT_CASE_REF})",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=f"Write {_DEFAULT_ARTIFACT}",
    )
    parser.add_argument(
        "--artifact-path",
        default=None,
        help="Optional repo-relative artifact override",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    parser.add_argument("--outbox-root", default=None, help="Optional outbox root override")
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    result = build_health_bundle(
        case_ref=args.case_ref,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
        write_artifact=bool(args.write),
        artifact_path_override=args.artifact_path,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
