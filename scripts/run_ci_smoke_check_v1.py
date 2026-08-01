#!/usr/bin/env python3
"""CI smoke check wrapper v1 — single-case multi-phase smoke + metrics gate.

Contract: docs/smoke-and-regression-contract-v1.md (CI-SMOKE · L-local default;
CI-advisory when wired with continue-on-error — not PR required by default).

Orchestrates existing CLIs without modifying them:
  1. run_multi_phase_smoke_v1.py
  2. export_std_case_metrics_v1.py

Applies a minimal pass/fail policy for CI (non-zero exit on failure).

Usage:
    python scripts/run_ci_smoke_check_v1.py --format text
    python scripts/run_ci_smoke_check_v1.py --case-ref demo_phase --format json
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.export_std_case_metrics_v1 import export_std_case_metrics
from scripts.run_multi_phase_smoke_v1 import (
    DEFAULT_CASE_REF,
    DEFAULT_TASK_TYPE,
    run_multi_phase_smoke_v1,
)

SCHEMA_VERSION = "ci_smoke_check_v1"


def _failed_ack_count(metrics: Dict[str, Any]) -> Optional[int]:
    metric_values = metrics.get("std_case_metrics_v1") or {}
    failed_ack = metric_values.get("notifications_failed_ack_count")
    if failed_ack is None:
        return None
    return int(failed_ack)


def evaluate_ci_smoke_check(
    smoke: Dict[str, Any],
    metrics: Dict[str, Any],
    *,
    outbox_mode: str = "isolated",
    failed_ack_before: Optional[int] = None,
) -> Dict[str, Any]:
    """Apply CI pass/fail rules; returns structured check result."""
    failures: List[str] = []
    observations: List[str] = []

    if not smoke.get("ok"):
        failures.append("multi_phase_smoke ok=false")
        failed_steps = [
            s.get("step_id")
            for s in (smoke.get("steps") or [])
            if not s.get("ok")
        ]
        if failed_steps:
            failures.append(f"multi_phase_smoke failed steps: {', '.join(failed_steps)}")

    if not metrics.get("ok"):
        failures.append(
            f"std_case_metrics ok=false ({metrics.get('message', 'unknown')})"
        )

    failed_ack = _failed_ack_count(metrics)
    if failed_ack is None:
        failures.append("std_case_metrics missing notifications_failed_ack_count")
    elif outbox_mode == "isolated":
        if failed_ack != 0:
            failures.append(f"notifications_failed_ack_count={failed_ack} (expected 0)")
    else:
        before = 0 if failed_ack_before is None else failed_ack_before
        delta = failed_ack - before
        if delta > 0:
            failures.append(
                f"notifications_failed_ack_count delta={delta} "
                f"(before={before}, after={failed_ack})"
            )
        elif failed_ack > 0:
            observations.append(
                f"pre-existing notifications_failed_ack_count={failed_ack} "
                "(repo outbox historical drift; not counted as CI failure)"
            )

    passed = not failures
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": passed,
        "case_ref": smoke.get("case_ref") or metrics.get("case_ref"),
        "outbox_mode": outbox_mode,
        "checks": {
            "multi_phase_smoke_ok": bool(smoke.get("ok")),
            "std_case_metrics_ok": bool(metrics.get("ok")),
            "notifications_failed_ack_count": failed_ack,
            "notifications_failed_ack_before": failed_ack_before,
            "notifications_failed_ack_delta": (
                None
                if failed_ack is None or failed_ack_before is None
                else failed_ack - failed_ack_before
            ),
        },
        "observations": observations,
        "failures": failures,
        "multi_phase_smoke": smoke,
        "std_case_metrics": metrics,
        "message": "CI smoke check passed" if passed else "CI smoke check failed",
    }


def run_ci_smoke_check_v1(
    case_ref: str = DEFAULT_CASE_REF,
    *,
    task_type: str = DEFAULT_TASK_TYPE,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    enable_dispatch: bool = False,
    use_repo_outbox: bool = False,
) -> Dict[str, Any]:
    """Run smoke + metrics for one case and evaluate CI pass/fail."""
    root = Path(repo_root).resolve() if repo_root else _REPO_ROOT
    temp_outbox: Optional[tempfile.TemporaryDirectory[str]] = None
    effective_outbox = outbox_root_override
    outbox_mode = "repo" if use_repo_outbox and outbox_root_override is None else "isolated"

    if use_repo_outbox and outbox_root_override is None:
        effective_outbox = None
    elif outbox_root_override is None:
        temp_outbox = tempfile.TemporaryDirectory(prefix="ci_smoke_outbox_")
        effective_outbox = temp_outbox.name

    failed_ack_before: Optional[int] = None
    if outbox_mode == "repo":
        before_metrics = export_std_case_metrics(
            case_ref,
            repo_root=root,
            outbox_root_override=effective_outbox,
        )
        failed_ack_before = _failed_ack_count(before_metrics)

    smoke = run_multi_phase_smoke_v1(
        case_ref,
        task_type=task_type,
        repo_root=root,
        outbox_root_override=effective_outbox,
        enable_dispatch=enable_dispatch,
        write_summary=True,
    )
    metrics = export_std_case_metrics(
        case_ref,
        repo_root=root,
        outbox_root_override=effective_outbox,
    )
    result = evaluate_ci_smoke_check(
        smoke,
        metrics,
        outbox_mode=outbox_mode,
        failed_ack_before=failed_ack_before,
    )
    if temp_outbox is not None:
        result["outbox_root"] = effective_outbox
    return result


def _format_text(result: Dict[str, Any]) -> str:
    checks = result.get("checks") or {}
    lines = [
        "CI Smoke Check v1",
        f"case_ref: {result.get('case_ref')}",
        f"ok: {result.get('ok')}",
        "",
        "── checks ──",
        f"  multi_phase_smoke_ok: {checks.get('multi_phase_smoke_ok')}",
        f"  std_case_metrics_ok: {checks.get('std_case_metrics_ok')}",
        f"  notifications_failed_ack_count: {checks.get('notifications_failed_ack_count')}",
    ]
    observations = result.get("observations") or []
    if observations:
        lines.extend(["", "── observations ──"])
        for item in observations:
            lines.append(f"  - {item}")
    failures = result.get("failures") or []
    if failures:
        lines.extend(["", "── failures ──"])
        for item in failures:
            lines.append(f"  - {item}")
    lines.extend(["", f"message: {result.get('message')}"])
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="CI wrapper: multi-phase smoke + std-case metrics for one case."
    )
    parser.add_argument(
        "--case-ref",
        default=DEFAULT_CASE_REF,
        help=f"Case slug under cases/ (default: {DEFAULT_CASE_REF})",
    )
    parser.add_argument(
        "--task-type",
        default=DEFAULT_TASK_TYPE,
        help=f"Routing task_type (default: {DEFAULT_TASK_TYPE})",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional explicit outbox root (implies repo mode unless isolated temp is used)",
    )
    parser.add_argument(
        "--use-repo-outbox",
        action="store_true",
        help="Use repo outbox/ instead of isolated temp; failed_ack uses delta rule",
    )
    parser.add_argument(
        "--enable-dispatch",
        action="store_true",
        help="Enable post-emit notification dispatch during smoke run",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    parser.add_argument("--repo-root", default=None, help="Optional repo root override")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    result = run_ci_smoke_check_v1(
        args.case_ref,
        task_type=args.task_type,
        repo_root=repo_root,
        outbox_root_override=args.outbox_root,
        enable_dispatch=args.enable_dispatch,
        use_repo_outbox=args.use_repo_outbox,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
