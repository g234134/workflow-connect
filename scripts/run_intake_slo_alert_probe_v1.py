#!/usr/bin/env python3
"""Intake Gate SLO / alert probe v1 (P75-G5) — local dry-run only.

Design SSOT: docs/p75-intake-gate-slo-alert-probe-v1.md

Does NOT send external alerts, mutate gate layer, or write production sinks.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SCHEMA_VERSION = "intake_slo_alert_probe_v1"
DOC_REL = "docs/p75-intake-gate-slo-alert-probe-v1.md"
DEFAULT_FIXTURE_REL = "tests/fixtures/intake_slo_probe_sample_v1.json"

THRESHOLDS = {
    "latency_ms_p95": 2000,
    "latency_ms_critical": 5000,
    "error_rate": 0.05,
    "error_rate_critical": 0.20,
}


def _p95(values: List[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(values)
    # nearest-rank
    idx = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    return float(ordered[idx])


def _load_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture root must be object")
    return payload


def evaluate_slo_probe(
    fixture: Mapping[str, Any],
    *,
    dry_run: bool = True,
    emit_alert: bool = False,
) -> Dict[str, Any]:
    """Evaluate local fixture samples against MVP SLO thresholds."""
    samples = fixture.get("samples") or []
    if not isinstance(samples, list):
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "probe_mode": "error",
            "message": "fixture.samples must be a list",
            "slo": {},
            "alerts": [{"level": "critical", "code": "bad_fixture", "detail": "samples"}],
            "would_emit": False,
            "doc": DOC_REL,
        }

    latencies: List[float] = []
    errors = 0
    for item in samples:
        if not isinstance(item, Mapping):
            continue
        try:
            latencies.append(float(item.get("latency_ms", 0)))
        except (TypeError, ValueError):
            latencies.append(0.0)
        if item.get("ok") is False or item.get("error"):
            errors += 1

    sample_count = len(latencies)
    error_rate = (errors / sample_count) if sample_count else 1.0
    p95 = _p95(latencies)

    alerts: List[Dict[str, Any]] = []
    if sample_count < 1:
        alerts.append(
            {
                "level": "warn",
                "code": "no_samples",
                "detail": "gate_decision_coverage < 1",
            }
        )
    if p95 > THRESHOLDS["latency_ms_critical"]:
        alerts.append(
            {
                "level": "critical",
                "code": "latency_p95_critical",
                "detail": f"p95={p95} > {THRESHOLDS['latency_ms_critical']}",
            }
        )
    elif p95 > THRESHOLDS["latency_ms_p95"]:
        alerts.append(
            {
                "level": "warn",
                "code": "latency_p95_warn",
                "detail": f"p95={p95} > {THRESHOLDS['latency_ms_p95']}",
            }
        )
    if error_rate > THRESHOLDS["error_rate_critical"]:
        alerts.append(
            {
                "level": "critical",
                "code": "error_rate_critical",
                "detail": f"error_rate={error_rate:.4f}",
            }
        )
    elif error_rate > THRESHOLDS["error_rate"]:
        alerts.append(
            {
                "level": "warn",
                "code": "error_rate_warn",
                "detail": f"error_rate={error_rate:.4f}",
            }
        )

    has_critical = any(a.get("level") == "critical" for a in alerts)
    ok = not has_critical and sample_count >= 1
    would_emit = bool(emit_alert and alerts)
    probe_mode = "dry_run" if dry_run else "local_only"
    # Never actually emit externally
    message = (
        f"probe {probe_mode} · samples={sample_count} · alerts={len(alerts)} · "
        f"would_emit={would_emit} · ≠ production alert sink"
    )

    return {
        "ok": ok,
        "schema_version": SCHEMA_VERSION,
        "probe_mode": probe_mode,
        "message": message,
        "slo": {
            "latency_ms_p95": p95,
            "error_rate": round(error_rate, 6),
            "sample_count": sample_count,
            "mean_latency_ms": round(statistics.fmean(latencies), 3) if latencies else 0.0,
            "thresholds": {
                "latency_ms_p95": THRESHOLDS["latency_ms_p95"],
                "error_rate": THRESHOLDS["error_rate"],
            },
        },
        "alerts": alerts,
        "would_emit": would_emit,
        "doc": DOC_REL,
    }


def run_intake_slo_alert_probe(
    *,
    fixture_path: Path | None = None,
    dry_run: bool = True,
    emit_alert: bool = False,
) -> Dict[str, Any]:
    path = fixture_path or (_REPO_ROOT / DEFAULT_FIXTURE_REL)
    if not path.is_file():
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "probe_mode": "error",
            "message": f"fixture not found: {path.as_posix()}",
            "slo": {},
            "alerts": [{"level": "critical", "code": "fixture_missing"}],
            "would_emit": False,
            "doc": DOC_REL,
        }
    try:
        fixture = _load_fixture(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "probe_mode": "error",
            "message": f"fixture load failed: {exc}",
            "slo": {},
            "alerts": [{"level": "critical", "code": "fixture_load_error"}],
            "would_emit": False,
            "doc": DOC_REL,
        }
    result = evaluate_slo_probe(fixture, dry_run=dry_run, emit_alert=emit_alert)
    result["fixture"] = path.relative_to(_REPO_ROOT).as_posix() if path.is_relative_to(_REPO_ROOT) else path.name
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="P75-G5 Intake Gate SLO/alert probe (local)")
    parser.add_argument(
        "--fixture",
        default=DEFAULT_FIXTURE_REL,
        help="Repo-relative fixture JSON path",
    )
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument(
        "--emit-alert",
        action="store_true",
        help="Mark would_emit when alerts present (still no external send)",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    fixture_path = Path(args.fixture)
    if not fixture_path.is_absolute():
        fixture_path = _REPO_ROOT / fixture_path

    result = run_intake_slo_alert_probe(
        fixture_path=fixture_path,
        dry_run=True,
        emit_alert=bool(args.emit_alert),
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"ok={result.get('ok')} mode={result.get('probe_mode')} "
            f"alerts={len(result.get('alerts') or [])} msg={result.get('message')}"
        )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
