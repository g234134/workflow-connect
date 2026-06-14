#!/usr/bin/env python3
"""Local toolchain smoke matrix runner (WC-PRE-05 · WB-T7).

Reads ``routing/toolchain_smoke_matrix_v1.yaml`` and optionally executes
matrix commands locally. Optional gate only — not wired to PR CI.

Usage:
    python scripts/run_toolchain_smoke_matrix.py --list
    python scripts/run_toolchain_smoke_matrix.py --tier local_recommended --dry-run
    python scripts/run_toolchain_smoke_matrix.py --smoke-id TS-W3TL-UNIT --format json
    python scripts/run_toolchain_smoke_matrix.py --tier local_recommended --format json
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MATRIX_PATH = _REPO_ROOT / "routing" / "toolchain_smoke_matrix_v1.yaml"

Format = Literal["text", "json"]
Tier = Literal["local_recommended", "optional_ci", "release_only", "all"]


def _load_matrix(matrix_path: Optional[Path] = None) -> Dict[str, Any]:
    path = matrix_path or _MATRIX_PATH
    if not path.is_file():
        return {
            "ok": False,
            "message": f"matrix file not found: {path.relative_to(_REPO_ROOT).as_posix()}",
            "schema_version": "toolchain_smoke_runner_v1",
            "entries": [],
        }
    try:
        import yaml  # type: ignore
    except ImportError:
        return {
            "ok": False,
            "message": "pyyaml not installed; cannot load toolchain smoke matrix",
            "schema_version": "toolchain_smoke_runner_v1",
            "entries": [],
        }
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {
            "ok": False,
            "message": "matrix root must be a mapping",
            "schema_version": "toolchain_smoke_runner_v1",
            "entries": [],
        }
    entries = data.get("entries")
    if not isinstance(entries, list):
        return {
            "ok": False,
            "message": "matrix entries must be a list",
            "schema_version": "toolchain_smoke_runner_v1",
            "entries": [],
        }
    return {
        "ok": True,
        "message": "matrix loaded",
        "schema_version": "toolchain_smoke_runner_v1",
        "matrix_schema_version": data.get("schema_version"),
        "matrix_revision": data.get("matrix_revision"),
        "entries": entries,
    }


def _filter_entries(
    entries: List[Dict[str, Any]],
    *,
    tier: Tier,
    smoke_id: Optional[str],
) -> List[Dict[str, Any]]:
    if smoke_id:
        return [e for e in entries if str(e.get("smoke_id")) == smoke_id]
    if tier == "all":
        return list(entries)
    return [e for e in entries if str(e.get("tier")) == tier]


def _parse_command(command: str) -> List[str]:
    posix = sys.platform != "win32"
    argv = shlex.split(command.strip(), posix=posix)
    if argv and argv[0] == "python":
        argv[0] = sys.executable
    return argv


def run_toolchain_smoke_matrix(
    *,
    tier: Tier = "local_recommended",
    smoke_id: Optional[str] = None,
    dry_run: bool = False,
    repo_root: Optional[Path] = None,
    matrix_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load matrix, filter entries, and optionally execute smoke commands."""
    root = repo_root or _REPO_ROOT
    loaded = _load_matrix(matrix_path)
    if not loaded.get("ok"):
        return {
            "ok": False,
            "message": loaded.get("message", "matrix load failed"),
            "schema_version": "toolchain_smoke_runner_v1",
            "dry_run": dry_run,
            "tier": tier,
            "smoke_id": smoke_id,
            "entries_requested": 0,
            "entries_run": 0,
            "entries_passed": 0,
            "entries_failed": 0,
            "results": [],
        }

    entries = _filter_entries(loaded["entries"], tier=tier, smoke_id=smoke_id)
    if smoke_id and not entries:
        return {
            "ok": False,
            "message": f"smoke_id not found: {smoke_id}",
            "schema_version": "toolchain_smoke_runner_v1",
            "dry_run": dry_run,
            "tier": tier,
            "smoke_id": smoke_id,
            "entries_requested": 0,
            "entries_run": 0,
            "entries_passed": 0,
            "entries_failed": 0,
            "results": [],
        }

    results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    for entry in entries:
        smoke = str(entry.get("smoke_id") or "")
        command = str(entry.get("command") or "").strip()
        item: Dict[str, Any] = {
            "smoke_id": smoke,
            "tier": entry.get("tier"),
            "gate_class": entry.get("gate_class"),
            "blocks_mainline": entry.get("blocks_mainline"),
            "command": command,
            "dry_run": dry_run,
            "skipped": dry_run,
            "ok": True if dry_run else None,
            "exit_code": None,
            "message": "planned" if dry_run else None,
        }
        if not dry_run and command:
            argv = _parse_command(command)
            proc = subprocess.run(
                argv,
                cwd=str(root),
                capture_output=True,
                text=True,
            )
            item["skipped"] = False
            item["exit_code"] = proc.returncode
            item["ok"] = proc.returncode == 0
            item["message"] = (
                "completed"
                if proc.returncode == 0
                else f"exit_code={proc.returncode}"
            )
            if proc.returncode == 0:
                passed += 1
            else:
                failed += 1
        results.append(item)

    run_count = 0 if dry_run else len(entries)
    return {
        "ok": failed == 0 and bool(entries),
        "message": (
            f"dry-run listed {len(entries)} entries"
            if dry_run
            else f"ran {run_count} entries; passed={passed} failed={failed}"
        ),
        "schema_version": "toolchain_smoke_runner_v1",
        "matrix_schema_version": loaded.get("matrix_schema_version"),
        "matrix_revision": loaded.get("matrix_revision"),
        "dry_run": dry_run,
        "tier": tier,
        "smoke_id": smoke_id,
        "entries_requested": len(entries),
        "entries_run": run_count,
        "entries_passed": passed if not dry_run else 0,
        "entries_failed": failed if not dry_run else 0,
        "results": results,
    }


def _format_text(report: Dict[str, Any]) -> str:
    lines = [
        "Toolchain Smoke Matrix Runner (WC-PRE-05 · optional local)",
        f"ok: {report.get('ok')}",
        f"dry_run: {report.get('dry_run')}",
        f"tier: {report.get('tier')}",
        f"entries_requested: {report.get('entries_requested')}",
        "",
    ]
    for item in report.get("results") or []:
        lines.append(
            f"- {item.get('smoke_id')}: "
            f"ok={item.get('ok')} skipped={item.get('skipped')} "
            f"gate_class={item.get('gate_class')}"
        )
        if item.get("command"):
            lines.append(f"  command: {item.get('command')}")
    lines.append("")
    lines.append(f"message: {report.get('message')}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Local optional runner for routing/toolchain_smoke_matrix_v1.yaml "
            "(WB-T7). Not a PR gate."
        ),
    )
    parser.add_argument(
        "--tier",
        choices=("local_recommended", "optional_ci", "release_only", "all"),
        default="local_recommended",
        help="Filter matrix entries by tier (default: local_recommended)",
    )
    parser.add_argument(
        "--smoke-id",
        default=None,
        help="Run a single smoke_id from the matrix",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List planned commands without executing subprocess",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Alias for --dry-run --tier all",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--matrix-path",
        default=None,
        help="Optional override path to toolchain_smoke_matrix_v1.yaml",
    )
    args = parser.parse_args(argv)

    tier: Tier = "all" if args.list else args.tier
    dry_run = args.dry_run or args.list
    matrix_path = Path(args.matrix_path).resolve() if args.matrix_path else None

    report = run_toolchain_smoke_matrix(
        tier=tier,
        smoke_id=args.smoke_id,
        dry_run=dry_run,
        matrix_path=matrix_path,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(_format_text(report))

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
