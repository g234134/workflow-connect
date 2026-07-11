"""Tabular Tool Executor v1 (W3-TL-T3).

Invokes enabled tools from tabular_tool_catalog_v1.json via subprocess and writes
standard outbox records. Does not modify MVP mainline CLI semantics.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.tabular_outbox_writer import (
    OUTBOX_SCHEMA_VERSION,
    append_event_line,
    build_event_line,
    build_outbox_rel_path,
    generate_run_id,
    write_run_record,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CATALOG_PATH = _REPO_ROOT / "tools" / "tabular_tool_catalog_v1.json"
_SUBPROCESS_TIMEOUT_SECONDS = 600

# Tools that require a case directory under cases/
_CASE_DIR_TOOLS = frozenset(
    {
        "validate.eligibility",
        "clean.phase_demo",
        "export.delivery_bundle",
        "orchestrate.e2e",
    }
)

# Tools with no standalone CLI in catalog (module-only)
_NO_CLI_TOOLS = frozenset({"validate.output_guard"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_catalog() -> Dict[str, Any]:
    with _CATALOG_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _find_tool(catalog: Dict[str, Any], tool_id: str) -> Optional[Dict[str, Any]]:
    for tool in catalog.get("tools", []):
        if str(tool.get("tool_id")) == tool_id:
            return tool
    return None


def resolve_case_dir(case_ref: str, extra_args: Optional[Dict[str, Any]] = None) -> Path:
    """Map case_ref to case directory path (repo-relative resolution)."""
    extra = extra_args or {}
    if "case_dir" in extra and extra["case_dir"]:
        case_path = Path(str(extra["case_dir"]))
        if not case_path.is_absolute():
            case_path = _REPO_ROOT / case_path
        return case_path.resolve()

    safe_ref = case_ref.replace("\\", "/").strip("/")
    return (_REPO_ROOT / "cases" / safe_ref).resolve()


def resolve_case_ref(case_dir: Path, extra_args: Optional[Dict[str, Any]] = None) -> str:
    """Derive case_ref slug from case_dir relative to cases/ or intake."""
    extra = extra_args or {}
    if extra.get("case_ref"):
        return str(extra["case_ref"]).replace("\\", "/").strip("/")

    try:
        rel = case_dir.resolve().relative_to((_REPO_ROOT / "cases").resolve())
        return rel.as_posix()
    except ValueError:
        return case_dir.name


def _case_dir_rel(case_dir: Path) -> str:
    try:
        return case_dir.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return case_dir.as_posix()


def _load_intake(case_dir: Path) -> Optional[Dict[str, Any]]:
    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        return None
    with intake_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _artifact(path: str, kind: str, *, logical_key: Optional[str] = None) -> Dict[str, Any]:
    item: Dict[str, Any] = {"kind": kind, "path": path.replace("\\", "/")}
    if logical_key:
        item["logical_key"] = logical_key
    return item


def _expected_artifacts(tool_id: str, case_dir_rel: str) -> List[Dict[str, Any]]:
    """Known artifact paths after successful tool runs (repo-relative)."""
    prefix = case_dir_rel.replace("\\", "/")
    mapping: Dict[str, List[Dict[str, Any]]] = {
        "validate.eligibility": [
            _artifact(f"{prefix}/reports/eligibility_result.json", "report", logical_key="eligibility_result"),
        ],
        "clean.phase_demo": [
            _artifact(f"{prefix}/cleaned/Phase_cleaned.csv", "cleaned_csv", logical_key="cleaned_csv"),
            _artifact(f"{prefix}/reports/report.json", "report", logical_key="report"),
            _artifact(f"{prefix}/reports/cleaning_stats.json", "report", logical_key="cleaning_stats"),
        ],
        "export.delivery_bundle": [
            _artifact(f"{prefix}/reports/report.json", "report", logical_key="report"),
            _artifact(f"{prefix}/delivery_signoff.md", "signoff", logical_key="delivery_signoff"),
        ],
        "index.cases": [
            _artifact("cases/index.json", "index", logical_key="cases_index"),
        ],
        "orchestrate.e2e": [
            _artifact(f"{prefix}/reports/eligibility_result.json", "report", logical_key="eligibility_result"),
            _artifact(f"{prefix}/reports/report.json", "report", logical_key="report"),
        ],
    }
    return list(mapping.get(tool_id, []))


def _build_cli_argv(
    tool: Dict[str, Any],
    case_dir: Optional[Path],
    extra_args: Optional[Dict[str, Any]],
) -> List[str]:
    """Build subprocess argv from catalog cli_invocation template."""
    extra = extra_args or {}
    cli = tool.get("cli_invocation")
    if not cli or not isinstance(cli, str):
        raise ValueError(f"tool {tool.get('tool_id')} has no cli_invocation")

    cmd = cli
    # Catalog templates may include bracketed optional flags or alternates — strip for argv.
    cmd = re.sub(r"\[[^\]]*\]", "", cmd)
    cmd = re.sub(r"\s*\|\s*", " ", cmd)
    cmd = " ".join(cmd.split())
    tool_id = str(tool["tool_id"])

    if case_dir is not None:
        case_rel = _case_dir_rel(case_dir)
        cmd = cmd.replace("<case_dir>", case_rel)

    if tool_id == "clean.phase_demo":
        flags: List[str] = []
        if extra.get("skip_eligibility", True):
            flags.append("--skip-eligibility")
        if extra.get("force"):
            flags.append("--force")
        if flags:
            cmd = f"{cmd} {' '.join(flags)}"

    if tool_id in {"validate.eligibility", "export.delivery_bundle", "index.cases"}:
        if extra.get("json", True):
            if "--json" not in cmd:
                cmd = f"{cmd} --json"

    if tool_id == "orchestrate.e2e" and extra.get("force_review"):
        cmd = f"{cmd} --force-review"

    if extra.get("cli_suffix"):
        cmd = f"{cmd} {extra['cli_suffix']}"

    argv = shlex.split(cmd, posix=(sys.platform != "win32"))
    if argv[0] == "python":
        argv[0] = sys.executable
    return argv


def _build_record(
    *,
    case_ref: str,
    run_id: str,
    tool_id: str,
    started_at: str,
    finished_at: str,
    ok: bool,
    exit_code: Optional[int],
    message: str,
    artifacts: List[Dict[str, Any]],
    dry_run: bool = False,
    planned_command: Optional[List[str]] = None,
    stderr_tail: Optional[str] = None,
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "schema_version": OUTBOX_SCHEMA_VERSION,
        "case_ref": case_ref,
        "run_id": run_id,
        "tool_id": tool_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "ok": ok,
        "exit_code": exit_code,
        "message": message,
        "artifacts": artifacts,
        "dry_run": dry_run,
        "outbox_path": build_outbox_rel_path(case_ref, run_id),
    }
    if planned_command is not None:
        record["planned_command"] = planned_command
    if stderr_tail:
        record["stderr_tail"] = stderr_tail
    return record


def _execute_result_dict(record: Dict[str, Any]) -> Dict[str, Any]:
    """Public return shape (includes outbox_path at top level)."""
    return {
        "ok": record["ok"],
        "message": record["message"],
        "tool_id": record["tool_id"],
        "case_ref": record["case_ref"],
        "run_id": record["run_id"],
        "schema_version": record["schema_version"],
        "exit_code": record["exit_code"],
        "started_at": record["started_at"],
        "finished_at": record["finished_at"],
        "artifacts": record["artifacts"],
        "outbox_path": record["outbox_path"],
        "dry_run": record.get("dry_run", False),
    }


def execute_tabular_tool(
    case_ref: str,
    tool_id: str,
    dry_run: bool = False,
    extra_args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute (or dry-run plan) a catalog tabular tool and write outbox record.

    Parameters
    ----------
    case_ref:
        Case slug under ``cases/`` (e.g. ``demo_phase``, ``sampleco/2026-0001``).
        Ignored for global tools like ``index.cases`` when no case_dir is required.
    tool_id:
        Catalog ``tool_id`` (e.g. ``validate.eligibility``).
    dry_run:
        When True, build plan only — no subprocess, no outbox file on disk.
    extra_args:
        Optional overrides: ``case_dir``, ``outbox_root``, ``force``, ``json``, etc.

    Returns
    -------
    dict
        Stable result with ok, message, tool_id, exit_code, timestamps, artifacts,
        outbox_path, run_id, schema_version.
    """
    extra = dict(extra_args or {})
    repo_root = Path(extra["repo_root"]) if extra.get("repo_root") else _REPO_ROOT
    outbox_override = extra.get("outbox_root")
    started_at = _utc_now_iso()
    run_id = generate_run_id(tool_id, started_at)

    catalog = _load_catalog()
    tool = _find_tool(catalog, tool_id)
    if tool is None:
        finished_at = _utc_now_iso()
        record = _build_record(
            case_ref=case_ref,
            run_id=run_id,
            tool_id=tool_id,
            started_at=started_at,
            finished_at=finished_at,
            ok=False,
            exit_code=None,
            message=f"unknown tool_id: {tool_id}",
            artifacts=[],
        )
        write_run_record(record, repo_root=repo_root, outbox_root_override=outbox_override)
        append_event_line(
            build_event_line(record),
            repo_root=repo_root,
            outbox_root_override=outbox_override,
        )
        return _execute_result_dict(record)

    if not tool.get("enabled", False):
        finished_at = _utc_now_iso()
        record = _build_record(
            case_ref=case_ref,
            run_id=run_id,
            tool_id=tool_id,
            started_at=started_at,
            finished_at=finished_at,
            ok=False,
            exit_code=None,
            message=f"tool disabled in catalog: {tool_id}",
            artifacts=[],
        )
        write_run_record(record, repo_root=repo_root, outbox_root_override=outbox_override)
        append_event_line(
            build_event_line(record),
            repo_root=repo_root,
            outbox_root_override=outbox_override,
        )
        return _execute_result_dict(record)

    if tool_id in _NO_CLI_TOOLS:
        finished_at = _utc_now_iso()
        record = _build_record(
            case_ref=case_ref,
            run_id=run_id,
            tool_id=tool_id,
            started_at=started_at,
            finished_at=finished_at,
            ok=False,
            exit_code=None,
            message=f"tool {tool_id} has no standalone CLI; invoked via bundle only",
            artifacts=[],
        )
        write_run_record(record, repo_root=repo_root, outbox_root_override=outbox_override)
        append_event_line(
            build_event_line(record),
            repo_root=repo_root,
            outbox_root_override=outbox_override,
        )
        return _execute_result_dict(record)

    needs_case = tool_id in _CASE_DIR_TOOLS or bool(
        tool.get("applicable_conditions", {}).get("case_dir_required")
    )
    case_dir: Optional[Path] = None
    resolved_case_ref = case_ref

    if needs_case:
        case_dir = resolve_case_dir(case_ref, extra)
        resolved_case_ref = resolve_case_ref(case_dir, extra)
        intake = _load_intake(case_dir)
        if intake is None:
            finished_at = _utc_now_iso()
            record = _build_record(
                case_ref=resolved_case_ref,
                run_id=run_id,
                tool_id=tool_id,
                started_at=started_at,
                finished_at=finished_at,
                ok=False,
                exit_code=2,
                message=f"missing intake.json under { _case_dir_rel(case_dir) }",
                artifacts=[],
            )
            write_run_record(record, repo_root=repo_root, outbox_root_override=outbox_override)
            append_event_line(
                build_event_line(record),
                repo_root=repo_root,
                outbox_root_override=outbox_override,
            )
            return _execute_result_dict(record)

    try:
        argv = _build_cli_argv(tool, case_dir, extra)
    except ValueError as exc:
        finished_at = _utc_now_iso()
        record = _build_record(
            case_ref=resolved_case_ref,
            run_id=run_id,
            tool_id=tool_id,
            started_at=started_at,
            finished_at=finished_at,
            ok=False,
            exit_code=None,
            message=str(exc),
            artifacts=[],
        )
        write_run_record(record, repo_root=repo_root, outbox_root_override=outbox_override)
        append_event_line(
            build_event_line(record),
            repo_root=repo_root,
            outbox_root_override=outbox_override,
        )
        return _execute_result_dict(record)

    case_dir_rel = _case_dir_rel(case_dir) if case_dir else ""
    planned_artifacts = _expected_artifacts(tool_id, case_dir_rel)

    if dry_run:
        finished_at = _utc_now_iso()
        record = _build_record(
            case_ref=resolved_case_ref,
            run_id=run_id,
            tool_id=tool_id,
            started_at=started_at,
            finished_at=finished_at,
            ok=True,
            exit_code=0,
            message="dry-run plan only; subprocess not spawned",
            artifacts=planned_artifacts,
            dry_run=True,
            planned_command=argv,
        )
        return _execute_result_dict(record)

    try:
        proc = subprocess.run(
            argv,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        finished_at = _utc_now_iso()
        stderr_tail = (exc.stderr or "")[-500:] if exc.stderr else None
        record = _build_record(
            case_ref=resolved_case_ref,
            run_id=run_id,
            tool_id=tool_id,
            started_at=started_at,
            finished_at=finished_at,
            ok=False,
            exit_code=None,
            message=(
                f"subprocess_timeout after {_SUBPROCESS_TIMEOUT_SECONDS}s "
                f"for tool_id={tool_id}"
            ),
            artifacts=[],
            stderr_tail=stderr_tail,
        )
        write_run_record(record, repo_root=repo_root, outbox_root_override=outbox_override)
        append_event_line(
            build_event_line(record),
            repo_root=repo_root,
            outbox_root_override=outbox_override,
        )
        return _execute_result_dict(record)

    finished_at = _utc_now_iso()
    exit_code = proc.returncode
    stderr_tail = (proc.stderr or "")[-500:] if proc.stderr else None

    if tool_id == "validate.eligibility" and exit_code in (0, 1, 2):
        ok = True
        message = f"eligibility gate completed with exit_code={exit_code}"
    else:
        ok = exit_code == 0
        message = "completed successfully" if ok else f"subprocess exited with code {exit_code}"

    record = _build_record(
        case_ref=resolved_case_ref,
        run_id=run_id,
        tool_id=tool_id,
        started_at=started_at,
        finished_at=finished_at,
        ok=ok,
        exit_code=exit_code,
        message=message,
        artifacts=planned_artifacts if ok else [],
        stderr_tail=stderr_tail if not ok else None,
    )
    write_run_record(record, repo_root=repo_root, outbox_root_override=outbox_override)
    append_event_line(
        build_event_line(record),
        repo_root=repo_root,
        outbox_root_override=outbox_override,
    )
    return _execute_result_dict(record)
