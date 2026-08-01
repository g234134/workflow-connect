#!/usr/bin/env python3
"""Controlled delivery / notify experiment CLI v1 (W7-T3).

Simulates S15 client notify for internal sandbox cases only (demo_phase /
sampleco). Reads existing delivery_signoff and bundle artifacts; writes
notify payload to outbox/ when --no-dry-run is set. Never calls real notify.

Usage:
    python scripts/run_controlled_delivery_notify_experiment.py \\
        --case-dir cases/demo_phase
    python scripts/run_controlled_delivery_notify_experiment.py \\
        --case-dir cases/demo_phase --no-dry-run --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.controlled_notify_experiment_v1 import run_controlled_notify_experiment


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Controlled delivery/notify experiment (internal sandbox only)",
    )
    parser.add_argument(
        "--case-dir",
        required=True,
        help="Case directory under cases/ (e.g. cases/demo_phase)",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Simulate only; do not write outbox JSON (default: true)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    return parser


def _text_output(result: Dict[str, Any]) -> str:
    lines = [
        f"ok: {result.get('ok')}",
        f"message: {result.get('message')}",
        f"case_ref: {result.get('case_ref')}",
        f"dry_run: {result.get('dry_run')}",
        f"simulated: {result.get('simulated')}",
        f"external_dispatch: {result.get('external_dispatch')}",
    ]
    if result.get("outbox_path"):
        lines.append(f"outbox_path: {result.get('outbox_path')}")
    if result.get("blocked"):
        lines.append("blocked: true")
    lines.extend(["", "--- client summary (simulated) ---", ""])
    lines.append(str(result.get("client_summary_text") or ""))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_controlled_notify_experiment(
        args.case_dir,
        dry_run=args.dry_run,
        repo_root=_REPO_ROOT,
    )

    if args.format == "json":
        payload = {k: v for k, v in result.items() if k != "record"}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_text_output(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
