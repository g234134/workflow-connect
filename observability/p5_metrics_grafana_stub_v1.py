"""P5 local Grafana/JSON对照 stub v1.

Design SSOT: docs/p5-metrics-grafana-stub-contract-v1.md
Schema: shared/schemas/p5_metrics_grafana_stub_v1.json

Aggregates (read-only):
  - toolchain_health_v1 → health.ok
  - std_case_metrics Prometheus text → metrics.scrape_ok
  - optional P75 alert sink JSONL → alert_budget_summary

Honest boundaries:
  - Local stub only; ≠ Grafana deploy · ≠ PG soak · ≠ UI · ≠ Phase closure.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "p5_metrics_grafana_stub_v1"
DOC_REL = "docs/p5-metrics-grafana-stub-contract-v1.md"
DEFAULT_CASE_REF = "demo_phase"
DEFAULT_ARTIFACT_REL = Path("artifacts") / "p5_metrics" / "grafana_stub.latest.json"
DEFAULT_ALERT_SINK_REL = Path("outbox") / "p75_alert_sink" / "events.jsonl"

_REPO_ROOT = Path(__file__).resolve().parents[1]

NON_CLAIMS = [
    "≠ Grafana deployed",
    "≠ PG soak",
    "≠ Web UI",
    "≠ P5 Phase closure",
    "≠ dark-ops monitoring takeover",
]

GRAFANA_READ_HINTS = [
    {"field": "health.ok", "panel_role": "stat"},
    {"field": "metrics.scrape_ok", "panel_role": "stat"},
    {"field": "alert_budget_summary", "panel_role": "table"},
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return (repo_root or _REPO_ROOT).resolve()


def _rel_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _build_health_block(*, repo_root: Path) -> Dict[str, Any]:
    try:
        from scripts.run_toolchain_health_dashboard import build_toolchain_health

        health = build_toolchain_health(repo_root=repo_root, dry_run=True)
    except Exception as exc:  # noqa: BLE001 — fail-soft for stub
        return {
            "ok": False,
            "source": "toolchain_health_v1",
            "sections_ok": None,
            "aggregated_health_score": None,
            "gate_class": None,
            "message": f"toolchain health failed: {exc}",
        }

    return {
        "ok": bool(health.get("ok")),
        "source": "toolchain_health_v1",
        "sections_ok": health.get("sections_ok"),
        "aggregated_health_score": health.get("aggregated_health_score"),
        "gate_class": health.get("gate_class"),
        "message": str(health.get("message") or "toolchain health assembled"),
    }


def _build_metrics_block(
    *,
    repo_root: Path,
    case_ref: str,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        from scripts.export_std_case_metrics_v1 import export_std_case_metrics
        from scripts.metrics_http_endpoint_v1 import get_metrics_text

        exported = export_std_case_metrics(
            case_ref,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
        )
        http_status, body = get_metrics_text(
            case_ref=case_ref,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "scrape_ok": False,
            "source": "std_case_metrics_v1",
            "http_status": None,
            "has_error_comment": True,
            "prometheus_line_count": None,
            "std_case_metrics_v1": {},
            "message": f"metrics scrape failed: {exc}",
        }

    has_error = "# error:" in (body or "")
    lines = [ln for ln in (body or "").splitlines() if ln.strip()]
    scrape_ok = bool(exported.get("ok")) and not has_error and http_status == 200

    return {
        "scrape_ok": scrape_ok,
        "source": "std_case_metrics_v1",
        "http_status": http_status,
        "has_error_comment": has_error,
        "prometheus_line_count": len(lines),
        "std_case_metrics_v1": exported.get("std_case_metrics_v1") or {},
        "message": str(exported.get("message") or "metrics text assembled"),
    }


def _scan_alert_budget(
    *,
    repo_root: Path,
    alert_sink_override: Optional[str] = None,
) -> Dict[str, Any]:
    note = (
        "severity narrative aligned to alert_event_v1; "
        "≠ dark-ops takeover / ≠ prod PagerDuty"
    )
    if alert_sink_override:
        path = Path(alert_sink_override)
        if not path.is_absolute():
            path = repo_root / path
    else:
        path = repo_root / DEFAULT_ALERT_SINK_REL

    if not path.is_file():
        return {
            "source": "narrative_stub",
            "warn_count": 0,
            "critical_count": 0,
            "total_events": 0,
            "note": note,
            "path": None,
        }

    warn_count = 0
    critical_count = 0
    total = 0
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            total += 1
            sev = str(row.get("severity") or "").strip().lower()
            if sev == "critical":
                critical_count += 1
            elif sev in ("warn", "warning"):
                warn_count += 1
    except OSError as exc:
        return {
            "source": "narrative_stub",
            "warn_count": 0,
            "critical_count": 0,
            "total_events": 0,
            "note": f"{note}; scan failed: {exc}",
            "path": _rel_posix(path, repo_root),
        }

    return {
        "source": "p75_alert_sink_scan",
        "warn_count": warn_count,
        "critical_count": critical_count,
        "total_events": total,
        "note": note,
        "path": _rel_posix(path, repo_root),
    }


def build_grafana_stub(
    *,
    case_ref: str = DEFAULT_CASE_REF,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    alert_sink_override: Optional[str] = None,
    write_artifact: bool = False,
    artifact_path_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble p5_metrics_grafana_stub_v1 dict (read-only by default)."""
    root = _repo_root(repo_root)
    norm_case = (case_ref or DEFAULT_CASE_REF).replace("\\", "/").strip("/") or DEFAULT_CASE_REF

    health = _build_health_block(repo_root=root)
    metrics = _build_metrics_block(
        repo_root=root,
        case_ref=norm_case,
        outbox_root_override=outbox_root_override,
    )
    alert_budget = _scan_alert_budget(
        repo_root=root,
        alert_sink_override=alert_sink_override,
    )

    overall_ok = bool(health.get("ok")) and bool(metrics.get("scrape_ok"))
    message_parts: List[str] = []
    if not health.get("ok"):
        message_parts.append("health.ok=false")
    if not metrics.get("scrape_ok"):
        message_parts.append("metrics.scrape_ok=false")
    message = (
        "local grafana stub assembled"
        if overall_ok
        else "local grafana stub degraded: " + ", ".join(message_parts)
    )

    result: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ok": overall_ok,
        "mode": "local_stub",
        "generated_at": _utc_now_iso(),
        "case_ref": norm_case,
        "health": health,
        "metrics": metrics,
        "alert_budget_summary": alert_budget,
        "grafana_read_hints": list(GRAFANA_READ_HINTS),
        "artifact_path": None,
        "doc": DOC_REL,
        "message": message,
        "non_claims": list(NON_CLAIMS),
    }

    if write_artifact:
        if artifact_path_override:
            out = Path(artifact_path_override)
            if not out.is_absolute():
                out = root / out
        else:
            out = root / DEFAULT_ARTIFACT_REL
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result["artifact_path"] = _rel_posix(out, root)
        except OSError as exc:
            result["ok"] = False
            result["message"] = f"artifact write failed: {exc}"

    return result
