"""_ops_cycle.py — 副官營運週期 CLI（HQ-P4-OPS-CYCLE）"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Callable

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from gov_paths import get_tang_gov_root  # type: ignore  # noqa: E402
from boot_context import build_boot_context  # type: ignore  # noqa: E402
from ops_cycle import (  # type: ignore  # noqa: E402
    append_battle_report,
    get_archive_checklist,
    get_cycle_artifact_paths,
    render_battle_report_markdown,
    validate_archive,
    validate_battle_report,
    write_review_template,
)


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def _emit(result: dict, pretty: bool) -> None:
    if pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))


def _repo_root() -> str:
    return get_tang_gov_root()


def _run_subprocess(
    cmd: list[str],
    *,
    cwd: str,
    timeout: int = 120,
) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _run_subprocess_check(
    *,
    step_id: str,
    title: str,
    cmd: list[str],
    cwd: str,
    pass_if: Callable[[int, str, str], bool],
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        rc, stdout, stderr = _run_subprocess(cmd, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "step_id": step_id,
            "title": title,
            "status": "fail",
            "message": str(exc),
            "details": details or {},
        }
    ok = pass_if(rc, stdout, stderr)
    message = (stdout or stderr or "").strip()
    if len(message) > 500:
        message = message[:500] + "..."
    return {
        "step_id": step_id,
        "title": title,
        "status": "pass" if ok else "fail",
        "message": message or f"exit_code={rc}",
        "details": {"exit_code": rc, **(details or {})},
    }


def _parse_json_stdout(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        pass
    for line in reversed(text.splitlines()):
        candidate = line.strip()
        if candidate.startswith("{"):
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
    start = text.find("{")
    if start >= 0:
        try:
            data = json.loads(text[start:])
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            pass
    return {}


def run_wave1_readiness_checks(repo_root: str) -> dict[str, Any]:
    """Wave 1 接戰就緒檢查；以 subprocess 呼叫既有 runner，不修改 02_Agents_Core。"""
    py = sys.executable
    checks: list[dict[str, Any]] = []

    checks.append(
        _run_subprocess_check(
            step_id="smoke_keys",
            title="三鑰盲測",
            cmd=[py, os.path.join("04_Workflows", "_smoke_test_keys.py")],
            cwd=repo_root,
            pass_if=lambda rc, out, _err: rc == 0 and "[FAILED]" not in out,
        )
    )

    checks.append(
        _run_subprocess_check(
            step_id="routing_policy_validate",
            title="routing_policy validate",
            cmd=[py, "-m", "core.routing_policy_loader", "validate", "--format", "json"],
            cwd=repo_root,
            pass_if=lambda rc, out, _err: rc == 0 and _parse_json_stdout(out).get("ok") is True,
        )
    )

    checks.append(
        _run_subprocess_check(
            step_id="eval_gate_ci_subset",
            title="eval-gate CI check (fixture)",
            cmd=[
                py,
                "-m",
                "observability.eval_ci_check",
                os.path.join("tests", "fixtures", "eval", "ibridge_records.jsonl"),
                "--limit",
                "50",
                "--max-needs-review-ratio",
                "0.9",
            ],
            cwd=repo_root,
            pass_if=lambda rc, out, _err: rc == 0 and _parse_json_stdout(out).get("ok") is True,
        )
    )

    rc, stdout, _stderr = _run_subprocess(
        [py, os.path.join("04_Workflows", "_route_task.py"), "--type", "dark.infra"],
        cwd=repo_root,
    )
    dark = _parse_json_stdout(stdout)
    assignable = dark.get("assignable")
    blocked = dark.get("blocked")
    # _route_task returns exit 1 when blocked+not assignable; that is expected for Wave 1.
    dark_ok = dark.get("ok") is True and ((assignable is False) or bool(blocked))
    checks.append(
        {
            "step_id": "darkops_route_gate",
            "title": "DarkOps route gate",
            "status": "pass" if dark_ok else "fail",
            "message": f"assignable={assignable} blocked={blocked}",
            "details": {
                "exit_code": rc,
                "assignable": assignable,
                "blocked": blocked,
            },
            "darkops_blocked_expected": True,
        }
    )

    ok = all(c.get("status") == "pass" for c in checks)
    return {"ok": ok, "checks": checks}


def _build_checklist_result(mode: str) -> dict[str, Any]:
    archive = get_archive_checklist(mode)
    if mode != "full":
        return archive

    wave1 = run_wave1_readiness_checks(_repo_root())
    return {
        "ok": bool(archive.get("ok")) and bool(wave1.get("ok")),
        "mode": mode,
        "ops_cycle_schema_version": archive.get("ops_cycle_schema_version"),
        "archive_checklist": archive,
        "wave1_readiness": wave1,
        "message": (
            f"Archive checklist ({mode}) + Wave 1 readiness: "
            f"archive_ok={archive.get('ok')} wave1_ok={wave1.get('ok')}"
        ),
    }


def _save_checklist_json(result: dict[str, Any], repo_root: str) -> str:
    rel_dir = os.path.join("artifacts", "ops")
    abs_dir = os.path.join(repo_root, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = f"checklist_full.{ts}.json"
    full = os.path.join(abs_dir, fname)
    payload = {
        **result,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(full, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return full


def main() -> int:
    parser = argparse.ArgumentParser(description="HQ Phase 4 ops cycle (battle report / archive / review).")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate-report", parents=[common], help="Validate battle report JSON")
    p_val.add_argument("--json", dest="json_path", required=True, help="Path to report JSON")

    p_render = sub.add_parser("render-report", parents=[common], help="Render battle report markdown to stdout")
    p_render.add_argument("--json", dest="json_path", required=True)

    p_append = sub.add_parser("append-report", parents=[common], help="Append battle report to Progress")
    p_append.add_argument("--json", dest="json_path", required=True)
    p_append.add_argument("--dry-run", action="store_true")

    p_list = sub.add_parser("checklist", parents=[common], help="Evaluate archive checklist")
    p_list.add_argument("--mode", choices=["minimal", "full"], default="full")
    p_list.add_argument(
        "--save-json",
        action="store_true",
        help="Write checklist JSON to artifacts/ops/checklist_full.<timestamp>.json",
    )

    p_arch = sub.add_parser("validate-archive", parents=[common], help="Validate archive readiness")
    p_arch.add_argument("--mode", choices=["minimal", "full"], default="full")

    p_rev = sub.add_parser("new-review", parents=[common], help="Create review template under project_status/reviews")
    p_rev.add_argument("--type", dest="review_type", required=True)
    p_rev.add_argument("--project", dest="project_id", required=True)
    p_rev.add_argument("--ticket", default=None)
    p_rev.add_argument("--dry-run", action="store_true")

    sub.add_parser("paths", parents=[common], help="Print ops cycle artifact paths")

    p_boot = sub.add_parser(
        "bootstrap",
        parents=[common],
        help="Three-tier boot: route + read_plan + Progress tail (alias: _boot_context.py)",
    )
    p_boot.add_argument("--type", dest="task_type", help="Canonical task_type")
    p_boot.add_argument("--text", dest="text", help="Task description for keyword matching")
    p_boot.add_argument(
        "--mode",
        choices=["full", "light"],
        default="full",
        help="full=完整接戰（預設）；light=續棒輕量",
    )
    p_boot.add_argument("--ticket-id", help="light: ticket id → tickets/<id>_state.md")
    p_boot.add_argument("--ticket-state", help="light: ticket state relative path")
    p_boot.add_argument(
        "--role",
        default="orchestrator",
        help="light: orchestrator|implementer|reviewer|scribe",
    )
    p_boot.add_argument(
        "--progress-tail",
        type=int,
        default=80,
        help="Progress tail lines (default: 80；light 忽略）",
    )

    args = parser.parse_args()

    if args.command == "bootstrap":
        result = build_boot_context(
            task_type=getattr(args, "task_type", None),
            text=getattr(args, "text", None),
            progress_tail_lines=getattr(args, "progress_tail", 80),
            mode=getattr(args, "mode", "full"),
            ticket_id=getattr(args, "ticket_id", None),
            ticket_state=getattr(args, "ticket_state", None),
            role=getattr(args, "role", None),
        )
        _emit(result, args.pretty)
        if not result.get("ok"):
            return 2
        if result.get("blocked") and not result.get("assignable"):
            return 1
        return 0

    if args.command == "paths":
        _emit(get_cycle_artifact_paths(), args.pretty)
        return 0

    if args.command == "validate-report":
        data = _load_json(args.json_path)
        result = validate_battle_report(data)
        _emit(result, args.pretty)
        return 0 if result.get("ok") else 2

    if args.command == "render-report":
        data = _load_json(args.json_path)
        validation = validate_battle_report(data)
        if not validation.get("ok"):
            _emit({"ok": False, "validation": validation}, args.pretty)
            return 2
        print(render_battle_report_markdown(data))
        return 0

    if args.command == "append-report":
        data = _load_json(args.json_path)
        result = append_battle_report(data, dry_run=args.dry_run)
        _emit(result, args.pretty)
        return 0 if result.get("ok") else 2

    if args.command == "checklist":
        result = _build_checklist_result(args.mode)
        if getattr(args, "save_json", False):
            saved = _save_checklist_json(result, _repo_root())
            result["saved_json"] = saved
        _emit(result, args.pretty)
        return 0 if result.get("ok") else 1

    if args.command == "validate-archive":
        result = validate_archive(args.mode)
        _emit(result, args.pretty)
        return 0 if result.get("ready_for_archive") else 1

    if args.command == "new-review":
        result = write_review_template(
            args.review_type,
            args.project_id,
            ticket=args.ticket,
            dry_run=args.dry_run,
        )
        _emit(result, args.pretty)
        return 0 if result.get("ok") else 2

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
