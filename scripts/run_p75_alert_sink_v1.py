#!/usr/bin/env python3
"""CLI for P7.5 local alert sink (P75-G6).

Design SSOT: docs/p75-alert-sink-contract-v1.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.p75_alert_sink_v1 import (  # noqa: E402
    DOC_REL,
    alerts_from_probe_result,
    emit_alerts,
)


def _load_alerts_from_probe(
    *,
    fixture: Optional[str] = None,
) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    from scripts.run_intake_slo_alert_probe_v1 import run_intake_slo_alert_probe

    fixture_path = None
    if fixture:
        fixture_path = Path(fixture)
        if not fixture_path.is_absolute():
            fixture_path = _REPO_ROOT / fixture_path
    probe = run_intake_slo_alert_probe(
        fixture_path=fixture_path,
        dry_run=True,
        emit_alert=True,
    )
    alerts = alerts_from_probe_result(probe)
    snapshot = probe.get("slo") if isinstance(probe.get("slo"), dict) else None
    return alerts, snapshot


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="P75-G6 local alert sink CLI")
    parser.add_argument(
        "--mode",
        choices=("file", "stub_http"),
        default="file",
        help="Sink mode (default: file)",
    )
    parser.add_argument(
        "--from-probe",
        action="store_true",
        help="Run G5 probe and emit its alerts[]",
    )
    parser.add_argument(
        "--fixture",
        default=None,
        help="Optional probe fixture (with --from-probe)",
    )
    parser.add_argument(
        "--alert-json",
        default=None,
        help="JSON array of alerts (alternative to --from-probe)",
    )
    parser.add_argument(
        "--sink-path",
        default=None,
        help="Override file sink path (repo-relative or absolute)",
    )
    parser.add_argument(
        "--stub-url",
        default=None,
        help="Optional loopback URL for stub_http (default: in-process)",
    )
    parser.add_argument(
        "--force-fail",
        action="store_true",
        help="Force stub_http failure (test hook)",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    alerts: List[Dict[str, Any]] = []
    probe_snapshot: Optional[Dict[str, Any]] = None

    if args.from_probe:
        alerts, probe_snapshot = _load_alerts_from_probe(fixture=args.fixture)
    elif args.alert_json:
        try:
            parsed = json.loads(args.alert_json)
        except json.JSONDecodeError as exc:
            err = {
                "ok": False,
                "message": f"invalid --alert-json: {exc}",
                "doc": DOC_REL,
                "emitted": 0,
                "events": [],
            }
            print(json.dumps(err, ensure_ascii=False, indent=2))
            return 1
        if not isinstance(parsed, list):
            err = {
                "ok": False,
                "message": "--alert-json must be a JSON array",
                "doc": DOC_REL,
                "emitted": 0,
                "events": [],
            }
            print(json.dumps(err, ensure_ascii=False, indent=2))
            return 1
        alerts = [x for x in parsed if isinstance(x, dict)]
    else:
        err = {
            "ok": False,
            "message": "provide --from-probe or --alert-json",
            "doc": DOC_REL,
            "emitted": 0,
            "events": [],
        }
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 1

    result = emit_alerts(
        alerts,
        mode=args.mode,
        probe_snapshot=probe_snapshot,
        sink_path_override=args.sink_path,
        stub_url=args.stub_url,
        force_fail=bool(args.force_fail),
        repo_root=_REPO_ROOT,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"ok={result.get('ok')} mode={result.get('sink_mode')} "
            f"emitted={result.get('emitted')} msg={result.get('message')}"
        )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
