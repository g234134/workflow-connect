"""Unified tabular cleaning automation driver (v1).

Chains existing CLI scripts for low-risk allowlist cases. Reads/writes
``automation_state.json`` and ``reports/automation_run_log.json``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
_CSV_CLEANING = _REPO_ROOT / "notebooks" / "csv_cleaning"

if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_CSV_CLEANING) not in sys.path:
    sys.path.insert(0, str(_CSV_CLEANING))

from tabular_automation_state_lib import (  # noqa: E402
    PAUSE_REASON_CHECKPOINT_A,
    PAUSE_REASON_CHECKPOINT_B,
    load_state,
    read_intake_case_id,
    save_state,
    utc_now_iso,
    validate_case_dir,
)
from tabular_automation_retry_dlq_lib import (  # noqa: E402
    MAX_TRANSIENT_RETRIES,
    backoff_seconds,
    classify_step_failure,
    enqueue_dlq,
)
from tabular_checkpoint_sync_lib import sync_checkpoint_b_state_and_readiness  # noqa: E402
from tabular_delivery_approval_lib import (  # noqa: E402
    load_approval,
    maybe_update_delivery_readiness,
)
from tabular_internal_notify_lib import (  # noqa: E402
    EVENT_CASE_DLQ_ENQUEUED,
    EVENT_CHECKPOINT_PENDING,
    maybe_notify_completed_delivery_ready,
    notify_internal,
)

from tabular_tool_executor_hook_lib import (  # noqa: E402
    DEFAULT_CLEANING_TOOL_ID,
    maybe_invoke_tool_executor,
)
from tabular_warning_guard_lib import (  # noqa: E402
    evaluate_guard_policy,
    resolve_warning_guard_profile,
    should_auto_skip_checkpoint_b,
)
from routing.intake_decision_rules_v1 import evaluate_intake_decision  # noqa: E402
from hitl.checkpoint_a_integration_v1 import (  # noqa: E402
    case_ref_from_case_dir,
    maybe_create_checkpoint_a,
)
from hitl.checkpoint_b_integration_v1 import maybe_create_checkpoint_b  # noqa: E402

RUN_LOG_SCHEMA = "tabular-automation-run-log-v1"
RUN_LOG_FILENAME = "automation_run_log.json"
DEFAULT_TASK_TYPE = "tabular.cleaning.mvp"

_ALLOWLIST_PROFILES = frozenset({"demo_phase", "sampleco", "internal", "generic-low-risk"})
_ALLOWLIST_CASE_KEYS = frozenset(
    {
        "cases/demo_phase",
        "cases/sampleco/2026-0001",
        "cases/internal/generic-low-risk",
    }
)

_STEP_ALIASES: dict[str, str] = {
    "intake": "intake",
    "gate": "eligibility",
    "eligibility": "eligibility",
    "checkpoint_a": "checkpoint_a",
    "checkpoint-a": "checkpoint_a",
    "clean": "cleaning",
    "cleaning": "cleaning",
    "stats": "report",
    "report": "report",
    "bundle": "bundle",
    "e2e": "e2e",
    "checkpoint_b": "checkpoint_b",
    "checkpoint-b": "checkpoint_b",
}

STEP_ORDER: list[str] = [
    "intake",
    "eligibility",
    "checkpoint_a",
    "cleaning",
    "report",
    "bundle",
    "e2e",
    "checkpoint_b",
]

_GATE_SCRIPT = _SCRIPTS / "check_case_eligibility.py"
_CLEAN_SCRIPT = _CSV_CLEANING / "clean_phase_demo.py"
_BUNDLE_SCRIPT = _SCRIPTS / "build_case_delivery_bundle.py"
_E2E_SCRIPT = _SCRIPTS / "run_case_e2e_validation.py"


def _resolve_cleaning_profile_id(case_dir: Path) -> tuple[str | None, str | None]:
    from cleaning_profiles_v1 import resolve_cleaning_profile  # noqa: WPS433

    intake: dict[str, Any] = {}
    intake_path = case_dir / "intake.json"
    if intake_path.is_file():
        try:
            raw = json.loads(intake_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                intake = raw
        except (OSError, json.JSONDecodeError):
            pass
    profile_cfg, err = resolve_cleaning_profile(case_dir, intake, repo_root=_REPO_ROOT)
    if profile_cfg is None:
        return None, err
    return str(profile_cfg.get("profile_id") or ""), None


def normalize_step_name(name: str) -> str | None:
    key = name.strip().lower().replace(" ", "_")
    return _STEP_ALIASES.get(key)


def resolve_case_dir(*, case_id: str | None = None, case_dir: Path | None = None) -> Path | None:
    if case_dir is not None:
        return case_dir.resolve()
    if not case_id:
        return None

    cases_root = _REPO_ROOT / "cases"
    direct = cases_root / case_id
    if direct.is_dir() and (direct / "intake.json").is_file():
        return direct.resolve()

    if "/" in case_id or "\\" in case_id:
        nested = cases_root / Path(case_id.replace("\\", "/"))
        if nested.is_dir() and (nested / "intake.json").is_file():
            return nested.resolve()

    for intake_path in cases_root.rglob("intake.json"):
        parent = intake_path.parent
        if parent.name == case_id:
            return parent.resolve()
        try:
            data = json.loads(intake_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("case_id", "")) == case_id:
            return parent.resolve()
    return None


def _rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_REPO_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def _parse_json_output(text: str) -> dict[str, Any]:
    start = text.find("{")
    if start < 0:
        return {}
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    return {}


def _run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout, proc.stderr


def _case_profile(case_dir: Path) -> str:
    rel = _rel_path(case_dir).replace("\\", "/")
    if rel.startswith("cases/"):
        rel = rel[len("cases/") :]
    parts = rel.split("/")
    if len(parts) == 1:
        return parts[0]
    return parts[0]


def _is_allowlisted(case_dir: Path) -> bool:
    rel = _rel_path(case_dir).replace("\\", "/")
    if rel in _ALLOWLIST_CASE_KEYS:
        return True
    profile = _case_profile(case_dir)
    if profile in _ALLOWLIST_PROFILES:
        return True
    case_id = read_intake_case_id(case_dir) or case_dir.name
    if case_id in _ALLOWLIST_PROFILES:
        return True
    profile_id, _ = _resolve_cleaning_profile_id(case_dir)
    if profile_id == "generic_low_risk_profile":
        return True
    return False


def run_log_path(case_dir: Path) -> Path:
    return case_dir / "reports" / RUN_LOG_FILENAME


def _new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}_{uuid.uuid4().hex[:8]}"


def _step_record(
    step_name: str,
    *,
    step_status: str,
    started_at: str,
    ended_at: str | None = None,
    artifacts: dict[str, Any] | None = None,
    error: str | None = None,
    detail: dict[str, Any] | None = None,
    retry_count: int = 0,
    last_error: str | None = None,
    last_error_at: str | None = None,
    dlq_status: str = "none",
    retry_attempts: list[dict[str, Any]] | None = None,
    attempt: int = 1,
    error_if_any: str | None = None,
    dlq_if_any: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "step_name": step_name,
        "step_status": step_status,
        "started_at": started_at,
        "ended_at": ended_at or utc_now_iso(),
        "artifacts": artifacts or {},
        "error": error,
        "attempt": attempt,
        "error_if_any": error_if_any,
        "dlq_if_any": dlq_if_any,
        "retry_count": retry_count,
        "last_error": last_error,
        "last_error_at": last_error_at,
        "dlq_status": dlq_status,
    }
    if detail:
        rec["detail"] = detail
    if retry_attempts:
        rec["retry_attempts"] = retry_attempts
    return rec


def _save_run_log(case_dir: Path, run_log: dict[str, Any]) -> Path:
    path = run_log_path(case_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _update_automation_state(
    case_dir: Path,
    *,
    current_step: str | None,
    automation_status: str | None = None,
    last_error: str | None = None,
    last_error_at: str | None = None,
    retry_count: int | None = None,
    dlq_status: str | None = None,
    requires_hitl_checkpoint: bool | None = None,
    allowed_to_auto_proceed: bool | None = None,
    pause_reason: str | None = None,
    checkpoint_a_status: str | None = None,
    checkpoint_b_status: str | None = None,
    checkpoint_resume_step: str | None = None,
    clear_last_error: bool = False,
) -> dict[str, Any]:
    state = load_state(case_dir)
    if state.get("ok") is False:
        return state

    state["current_step"] = current_step
    state["last_transition_ts"] = utc_now_iso()
    if automation_status is not None:
        state["automation_status"] = automation_status
    if clear_last_error:
        state["last_error"] = None
        state["last_error_at"] = None
    elif last_error is not None:
        state["last_error"] = last_error
    if last_error_at is not None:
        state["last_error_at"] = last_error_at
    if retry_count is not None:
        state["retry_count"] = retry_count
    if dlq_status is not None:
        state["dlq_status"] = dlq_status
    if requires_hitl_checkpoint is not None:
        state["requires_hitl_checkpoint"] = requires_hitl_checkpoint
    if allowed_to_auto_proceed is not None:
        state["allowed_to_auto_proceed"] = allowed_to_auto_proceed
    if pause_reason is not None:
        state["pause_reason"] = pause_reason
    if checkpoint_a_status is not None:
        state["checkpoint_a_status"] = checkpoint_a_status
    if checkpoint_b_status is not None:
        state["checkpoint_b_status"] = checkpoint_b_status
    if checkpoint_resume_step is not None:
        state["checkpoint_resume_step"] = checkpoint_resume_step

    save_state(case_dir, state)
    return state


def _check_control_plane(case_dir: Path) -> dict[str, Any] | None:
    """Return stop dict if driver must halt between steps."""
    state = load_state(case_dir)
    if state.get("ok") is False:
        return {
            "ok": False,
            "stopped": True,
            "reason": "invalid_state",
            "message": state.get("message", "invalid automation state"),
        }

    status = state.get("automation_status", "idle")
    if status == "stopped":
        return {
            "ok": False,
            "stopped": True,
            "reason": "human_stop",
            "message": "automation_status=stopped; halting between steps",
            "state": state,
        }
    if status == "paused":
        return {
            "ok": False,
            "stopped": True,
            "reason": "human_pause",
            "message": "automation_status=paused; halting after current step",
            "state": state,
        }
    if status != "running":
        return {
            "ok": False,
            "stopped": True,
            "reason": "not_running",
            "message": f"automation_status={status}; expected running",
            "state": state,
        }
    if not state.get("allowed_to_auto_proceed", False):
        return {
            "ok": False,
            "stopped": True,
            "reason": "auto_proceed_blocked",
            "message": "allowed_to_auto_proceed=false; awaiting control plane or HITL",
            "state": state,
        }
    return None


def _check_intake_structure(case_dir: Path) -> dict[str, Any]:
    missing: list[str] = []
    if not case_dir.is_dir():
        missing.append("case_dir")
    if not (case_dir / "intake.json").is_file():
        missing.append("intake.json")
    if not (case_dir / "raw").is_dir():
        missing.append("raw")

    intake: dict[str, Any] = {}
    data_file: str | None = None
    if not missing or "intake.json" not in missing:
        try:
            intake = json.loads((case_dir / "intake.json").read_text(encoding="utf-8"))
            data_file = intake.get("data_file")
        except (OSError, json.JSONDecodeError) as exc:
            return {
                "ok": False,
                "message": f"intake.json unreadable: {exc}",
                "artifacts": {},
            }

    raw_ok = False
    if data_file and (case_dir / data_file).is_file():
        raw_ok = True
    elif data_file:
        missing.append(data_file)

    return {
        "ok": len(missing) == 0 and raw_ok,
        "message": "intake structure ok" if not missing and raw_ok else f"missing: {', '.join(missing)}",
        "artifacts": {
            "intake_json": _rel_path(case_dir / "intake.json"),
            "data_file": data_file,
            "raw_present": raw_ok,
        },
        "intake": intake,
    }


def _step_intake(case_dir: Path) -> dict[str, Any]:
    result = _check_intake_structure(case_dir)
    return {
        "ok": result["ok"],
        "artifacts": result.get("artifacts", {}),
        "error": None if result["ok"] else result.get("message"),
        "detail": {"intake_case_id": result.get("intake", {}).get("case_id")},
    }


def _step_eligibility(case_dir: Path) -> dict[str, Any]:
    rc, out, err = _run_cmd(
        [sys.executable, str(_GATE_SCRIPT), "--case-dir", str(case_dir), "--json"]
    )
    data = _parse_json_output(out)
    eligibility = data.get("eligibility", "unknown")
    ok = rc in (0, 2) and data.get("ok") is True
    artifacts = {
        "eligibility_result_json": _rel_path(case_dir / "reports" / "eligibility_result.json"),
        "eligibility": eligibility,
        "exit_code": rc,
    }
    return {
        "ok": ok,
        "artifacts": artifacts,
        "error": None if ok else (data.get("message") or err[:500] or f"gate exit {rc}"),
        "detail": data,
        "terminal": eligibility == "rejected",
    }


def _step_checkpoint_a(case_dir: Path, *, force: bool, eligibility: str) -> dict[str, Any]:
    decision = evaluate_intake_decision(DEFAULT_TASK_TYPE, _rel_path(case_dir))
    if not decision.get("ok"):
        return {
            "ok": False,
            "artifacts": {},
            "error": decision.get("message", "intake decision failed"),
            "detail": decision,
            "terminal": True,
        }

    if decision.get("decision") == "reject":
        return {
            "ok": False,
            "artifacts": {},
            "error": "intake decision reject",
            "detail": decision,
            "terminal": True,
        }

    cleaning_profile_id, _ = _resolve_cleaning_profile_id(case_dir)
    generic_low_risk_accepted = (
        eligibility == "accepted" and cleaning_profile_id == "generic_low_risk_profile"
    )

    auto_approve = force or generic_low_risk_accepted or (
        decision.get("decision") == "auto_accept"
        and decision.get("risk_level") == "low"
        and _is_allowlisted(case_dir)
        and eligibility == "accepted"
    )

    cp_result = maybe_create_checkpoint_a(
        DEFAULT_TASK_TYPE,
        _rel_path(case_dir),
        decision,
        auto_approve=auto_approve,
    )

    status = cp_result.get("status", "")
    awaiting = status == "awaiting_human"
    ok = cp_result.get("ok") is True and not awaiting

    artifacts = {
        "checkpoint_status": status,
        "checkpoint_id": cp_result.get("checkpoint_id"),
        "auto_approve": auto_approve,
    }
    if cp_result.get("checkpoint_path"):
        artifacts["checkpoint_path"] = cp_result["checkpoint_path"]

    return {
        "ok": ok,
        "artifacts": artifacts,
        "error": None if ok else cp_result.get("message", "checkpoint A awaiting human"),
        "detail": {"decision": decision, "checkpoint": cp_result},
        "hitl_blocked": awaiting,
        "terminal": awaiting and not force,
    }


def _step_cleaning(
    case_dir: Path,
    *,
    force: bool,
    eligibility: str,
    profile_id: str | None = None,
    use_tool_executor: bool = False,
) -> dict[str, Any]:
    hook = maybe_invoke_tool_executor(
        use_tool_executor=use_tool_executor,
        tool_id=DEFAULT_CLEANING_TOOL_ID,
        case_dir=case_dir,
        step_name="cleaning",
    )
    if use_tool_executor and hook.get("invoked") and hook.get("ok"):
        cleaned = list((case_dir / "cleaned").glob("*_cleaned.csv"))
        stats_path = case_dir / "reports" / "cleaning_stats.json"
        artifacts: dict[str, Any] = {
            "tool_executor": True,
            "cleaned_csv_count": len(cleaned),
        }
        if profile_id:
            artifacts["cleaning_profile_id"] = profile_id
        if stats_path.is_file():
            artifacts["cleaning_stats_json"] = _rel_path(stats_path)
        if cleaned:
            artifacts["output_path"] = _rel_path(cleaned[0])
        return {
            "ok": len(cleaned) > 0,
            "artifacts": artifacts,
            "error": None if cleaned else "tool_executor produced no cleaned csv",
            "detail": {"tool_executor_hook": hook},
            "tool_executor_hook": hook,
        }

    cmd = [
        sys.executable,
        str(_CLEAN_SCRIPT),
        "--case-dir",
        str(case_dir),
        "--skip-eligibility",
    ]
    if profile_id:
        cmd.extend(["--profile-id", profile_id])
    if eligibility == "review_needed" or force:
        cmd.append("--force")

    rc, out, err = _run_cmd(cmd)
    data = _parse_json_output(out)
    ok = rc == 0 and data.get("ok") is True
    artifacts: dict[str, Any] = {}
    if data.get("cleaning_profile_id"):
        artifacts["cleaning_profile_id"] = data["cleaning_profile_id"]
    for key in ("output_path", "report_json", "report_md"):
        if data.get(key):
            artifacts[key] = data[key]
    if (case_dir / "reports" / "cleaning_stats.json").is_file():
        artifacts["cleaning_stats_json"] = _rel_path(case_dir / "reports" / "cleaning_stats.json")

    return {
        "ok": ok,
        "artifacts": artifacts,
        "error": None if ok else (data.get("message") or err[:500] or f"clean exit {rc}"),
        "detail": data,
        "tool_executor_hook": hook,
    }


def _step_report(case_dir: Path) -> dict[str, Any]:
    report_json = case_dir / "reports" / "report.json"
    stats_json = case_dir / "reports" / "cleaning_stats.json"
    report_md = case_dir / "reports" / "report.md"

    missing = [p.name for p in (report_json, stats_json) if not p.is_file()]
    if missing:
        return {
            "ok": False,
            "artifacts": {},
            "error": f"missing report artifacts: {', '.join(missing)}",
        }

    try:
        report = json.loads(report_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "artifacts": {}, "error": f"report.json unreadable: {exc}"}

    guard = report.get("output_guard") or {}
    summary = report.get("summary") or {}
    qa_status = report.get("qa_status") or summary.get("qa_status")
    artifacts = {
        "report_json": _rel_path(report_json),
        "cleaning_stats_json": _rel_path(stats_json),
        "qa_status": qa_status,
        "output_guard_status": guard.get("status"),
    }
    if report_md.is_file():
        artifacts["report_md"] = _rel_path(report_md)

    return {
        "ok": True,
        "artifacts": artifacts,
        "error": None,
        "detail": {"output_guard": guard, "qa_status": qa_status},
    }


def _step_bundle(case_dir: Path) -> dict[str, Any]:
    rc, out, err = _run_cmd(
        [sys.executable, str(_BUNDLE_SCRIPT), "--case-dir", str(case_dir), "--json"]
    )
    data = _parse_json_output(out)
    ok = rc == 0 and data.get("ok") is True
    return {
        "ok": ok,
        "artifacts": data.get("artifacts") or {},
        "error": None if ok else (data.get("message") or err[:500] or f"bundle exit {rc}"),
        "detail": data,
    }


def _step_e2e(case_dir: Path, *, force: bool, eligibility: str) -> dict[str, Any]:
    from run_case_e2e_validation import run_case_e2e_validation  # noqa: E402

    force_review = force or eligibility == "review_needed"
    data = run_case_e2e_validation(case_dir, force_review=force_review)
    ok = data.get("ok") is True
    return {
        "ok": ok,
        "artifacts": data.get("artifacts") or {},
        "error": None if ok else data.get("message", "e2e validation failed"),
        "detail": data,
    }


def _step_checkpoint_b(case_dir: Path, *, force: bool) -> dict[str, Any]:
    report_path = case_dir / "reports" / "report.json"
    if not report_path.is_file():
        return {"ok": False, "artifacts": {}, "error": "report.json missing for checkpoint B"}

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "artifacts": {}, "error": f"report.json unreadable: {exc}"}

    output_guard = report.get("output_guard") or {}
    guard_profile = resolve_warning_guard_profile(case_dir)
    guard_policy = evaluate_guard_policy(guard_profile, output_guard.get("status"))
    artifacts_map = {
        "cleaned_csv": _rel_path(p)
        for p in (case_dir / "cleaned").glob("*_cleaned.csv")
    }
    execution_summary = {
        "case_ref": case_ref_from_case_dir(_rel_path(case_dir)),
        "qa_status": report.get("qa_status"),
        "tools_executed": ["clean.phase_demo", "export.delivery_bundle"],
    }

    auto_approve = should_auto_skip_checkpoint_b(
        policy=guard_policy,
        qa_status=report.get("qa_status"),
        removal_ratio=output_guard.get("removal_ratio"),
        force=force,
    )

    cp_result = maybe_create_checkpoint_b(
        case_dir,
        execution_summary,
        output_guard,
        artifacts_map,
        auto_approve=auto_approve,
        write_state=True,
    )

    awaiting = cp_result.get("checkpoint_created") is True
    ok = cp_result.get("ok") is True and not awaiting

    return {
        "ok": ok,
        "artifacts": {
            "checkpoint_created": cp_result.get("checkpoint_created"),
            "skip_reason": cp_result.get("skip_reason"),
            "output_guard_status": output_guard.get("status"),
            "warning_guard_profile": guard_profile,
            "warning_guard_policy": guard_policy,
        },
        "error": None if ok else cp_result.get("delivery_plan", {}).get("message", "checkpoint B blocked"),
        "detail": cp_result,
        "hitl_blocked": awaiting,
        "terminal": awaiting and not force,
    }


StepRunner = Callable[..., dict[str, Any]]


def _build_step_runners(
    *,
    force: bool,
    eligibility: str,
    profile_id: str | None,
    use_tool_executor: bool = False,
) -> dict[str, StepRunner]:
    return {
        "intake": lambda cd: _step_intake(cd),
        "eligibility": lambda cd: _step_eligibility(cd),
        "checkpoint_a": lambda cd: _step_checkpoint_a(cd, force=force, eligibility=eligibility),
        "cleaning": lambda cd: _step_cleaning(
            cd,
            force=force,
            eligibility=eligibility,
            profile_id=profile_id,
            use_tool_executor=use_tool_executor,
        ),
        "report": lambda cd: _step_report(cd),
        "bundle": lambda cd: _step_bundle(cd),
        "e2e": lambda cd: _step_e2e(cd, force=force, eligibility=eligibility),
        "checkpoint_b": lambda cd: _step_checkpoint_b(cd, force=force),
    }


def _steps_to_run(
    *,
    start_from: str,
    stop_after: str | None,
    resume: bool,
    current_step: str | None,
    resume_step: str | None = None,
) -> list[str]:
    if resume_step and resume_step in STEP_ORDER:
        start_idx = STEP_ORDER.index(resume_step)
    elif resume and current_step:
        try:
            idx = STEP_ORDER.index(current_step)
            start_idx = min(idx + 1, len(STEP_ORDER) - 1)
            if current_step == STEP_ORDER[-1]:
                start_idx = len(STEP_ORDER)
        except ValueError:
            start_idx = STEP_ORDER.index(start_from)
    else:
        start_idx = STEP_ORDER.index(start_from)

    end_idx = len(STEP_ORDER)
    if stop_after:
        end_idx = STEP_ORDER.index(stop_after) + 1

    return STEP_ORDER[start_idx:end_idx]


def _invoke_step_runner(runner: StepRunner, case_dir: Path) -> dict[str, Any]:
    try:
        return runner(case_dir)
    except Exception as exc:  # noqa: BLE001 — record and fail closed
        return {"ok": False, "artifacts": {}, "error": str(exc)}


def _run_step_with_retry(
    case_dir: Path,
    step_name: str,
    runner: StepRunner,
    *,
    run_id: str,
    case_id: str,
    cleaning_profile_id: str | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Execute one step with transient retry and optional DLQ enqueue."""
    retry_attempts: list[dict[str, Any]] = []
    step_started = utc_now_iso()
    transient_retries = 0
    last_error_at: str | None = None
    dlq_status = "none"
    dlq_detail: dict[str, Any] | None = None
    step_result: dict[str, Any] = {"ok": False, "artifacts": {}, "error": "not executed"}

    while True:
        attempt_started = utc_now_iso()
        step_result = _invoke_step_runner(runner, case_dir)

        if step_result.get("ok") is True:
            _update_automation_state(
                case_dir,
                current_step=step_name,
                retry_count=0,
                clear_last_error=True,
                dlq_status="none",
            )
            return {
                "step_result": step_result,
                "step_started": step_started,
                "retry_count": transient_retries,
                "last_error": None,
                "last_error_at": None,
                "dlq_status": "none",
                "retry_attempts": retry_attempts,
                "dlq_detail": None,
            }

        error_msg = step_result.get("error")
        last_error_at = utc_now_iso()
        failure_class = classify_step_failure(step_result)

        retry_attempts.append(
            {
                "attempt": len(retry_attempts) + 1,
                "started_at": attempt_started,
                "ended_at": last_error_at,
                "error": error_msg,
                "failure_class": failure_class,
            }
        )

        _update_automation_state(
            case_dir,
            current_step=step_name,
            last_error=error_msg,
            last_error_at=last_error_at,
            retry_count=transient_retries,
        )

        if failure_class == "transient" and transient_retries < MAX_TRANSIENT_RETRIES:
            transient_retries += 1
            _update_automation_state(
                case_dir,
                current_step=step_name,
                retry_count=transient_retries,
                last_error=error_msg,
                last_error_at=last_error_at,
            )
            sleep_fn(backoff_seconds(transient_retries))
            continue

        should_dlq = failure_class in ("transient", "immediate_dlq")
        if should_dlq:
            dlq_status = "queued"
            dlq_detail = enqueue_dlq(
                case_dir,
                case_id=case_id,
                case_dir_rel=_rel_path(case_dir),
                run_id=run_id,
                step_name=step_name,
                error=error_msg,
                failure_class=failure_class,
                retry_count=transient_retries,
                last_error_at=last_error_at,
                run_log_path=_rel_path(run_log_path(case_dir)),
                cleaning_profile_id=cleaning_profile_id,
            )
            notify_internal(
                case_dir,
                EVENT_CASE_DLQ_ENQUEUED,
                {
                    "run_id": run_id,
                    "step_name": step_name,
                    "failure_class": failure_class,
                    "retry_count": transient_retries,
                    "error": error_msg,
                    "entry_id": dlq_detail.get("entry_id"),
                    "dlq_index_path": dlq_detail.get("dlq_index_path"),
                },
                case_id=case_id,
            )
            _update_automation_state(
                case_dir,
                current_step=step_name,
                last_error=error_msg,
                last_error_at=last_error_at,
                retry_count=transient_retries,
                dlq_status="queued",
            )

        return {
            "step_result": step_result,
            "step_started": step_started,
            "retry_count": transient_retries,
            "last_error": error_msg,
            "last_error_at": last_error_at,
            "dlq_status": dlq_status,
            "retry_attempts": retry_attempts,
            "dlq_detail": dlq_detail,
            "failure_class": failure_class,
        }


def run_tabular_automation(
    case_dir: Path,
    *,
    start_from: str = "intake",
    stop_after: str | None = None,
    resume: bool = False,
    dry_run: bool = False,
    force: bool = False,
    skip_control_check: bool = False,
    use_tool_executor: bool = False,
) -> dict[str, Any]:
    """Execute the tabular cleaning automation chain for one case directory."""
    err = validate_case_dir(case_dir)
    if err:
        return {**err, "command": "run"}

    case_dir = case_dir.resolve()
    case_id = read_intake_case_id(case_dir) or case_dir.name

    if not force and not _is_allowlisted(case_dir):
        return {
            "ok": False,
            "command": "run",
            "case_dir": _rel_path(case_dir),
            "case_id": case_id,
            "message": (
                f"case profile {_case_profile(case_dir)!r} not in low-risk allowlist; "
                "use --force for internal demo bypass"
            ),
        }

    state = load_state(case_dir)
    if state.get("ok") is False:
        return {**state, "command": "run"}

    if not dry_run and not skip_control_check:
        if state.get("automation_status") != "running":
            return {
                "ok": False,
                "command": "run",
                "case_dir": _rel_path(case_dir),
                "case_id": case_id,
                "automation_status": state.get("automation_status"),
                "message": (
                    "automation_status must be running; "
                    "use manage_tabular_automation_state.py start first"
                ),
                "state": state,
            }

    if resume and state.get("requires_hitl_checkpoint") and not force:
        resume_step = state.get("checkpoint_resume_step")
        if not resume_step:
            return {
                "ok": False,
                "command": "run",
                "case_dir": _rel_path(case_dir),
                "case_id": case_id,
                "message": (
                    "requires_hitl_checkpoint=true; apply approve-a/b then "
                    "resume-after-checkpoint, or use --force (demo only)"
                ),
                "state": state,
            }

    explicit_resume_step = None
    if resume:
        explicit_resume_step = state.get("checkpoint_resume_step")
    elif start_from in STEP_ORDER and state.get("checkpoint_resume_step") == start_from:
        explicit_resume_step = start_from

    run_id = _new_run_id()
    started_at = utc_now_iso()
    cleaning_profile_id, profile_err = _resolve_cleaning_profile_id(case_dir)
    run_log: dict[str, Any] = {
        "schema_version": RUN_LOG_SCHEMA,
        "run_id": run_id,
        "case_id": case_id,
        "case_dir": _rel_path(case_dir),
        "cleaning_profile_id": cleaning_profile_id,
        "cleaning_profile_error": profile_err,
        "started_at": started_at,
        "ended_at": None,
        "dry_run": dry_run,
        "force": force,
        "resume": resume,
        "start_from": start_from,
        "stop_after": stop_after,
        "steps": [],
        "automation_status": None,
        "retry_count": 0,
        "last_error": None,
        "last_error_at": None,
        "dlq_status": "none",
        "ok": False,
        "message": "",
    }

    steps = _steps_to_run(
        start_from=start_from,
        stop_after=stop_after,
        resume=resume,
        current_step=state.get("current_step"),
        resume_step=explicit_resume_step,
    )

    if dry_run:
        run_log["steps"] = [
            _step_record(
                step,
                step_status="planned",
                started_at=started_at,
                ended_at=started_at,
                artifacts={"planned": True},
            )
            for step in steps
        ]
        run_log["ended_at"] = utc_now_iso()
        run_log["ok"] = True
        run_log["message"] = f"dry-run planned {len(steps)} step(s)"
        run_log["automation_status"] = state.get("automation_status")
        log_path = _save_run_log(case_dir, run_log)
        return {
            "ok": True,
            "command": "run",
            "dry_run": True,
            "case_dir": _rel_path(case_dir),
            "case_id": case_id,
            "run_id": run_id,
            "run_log_path": _rel_path(log_path),
            "planned_steps": steps,
            "run_log": run_log,
            "message": run_log["message"],
        }

    eligibility = "accepted"
    eligibility_path = case_dir / "reports" / "eligibility_result.json"
    if eligibility_path.is_file():
        try:
            elig_data = json.loads(eligibility_path.read_text(encoding="utf-8"))
            eligibility = elig_data.get("status", eligibility)
        except (OSError, json.JSONDecodeError):
            pass

    runners = _build_step_runners(
        force=force,
        eligibility=eligibility,
        profile_id=cleaning_profile_id,
        use_tool_executor=use_tool_executor,
    )
    overall_ok = True
    stop_reason: str | None = None

    for step_name in steps:
        control = _check_control_plane(case_dir)
        if control:
            stop_reason = control.get("reason")
            run_log["message"] = control.get("message", "control plane halt")
            overall_ok = False
            break

        step_started = utc_now_iso()
        _update_automation_state(case_dir, current_step=step_name)

        exec_result = _run_step_with_retry(
            case_dir,
            step_name,
            runners[step_name],
            run_id=run_id,
            case_id=case_id,
            cleaning_profile_id=cleaning_profile_id,
        )
        step_result = exec_result["step_result"]
        step_started = exec_result.get("step_started", step_started)

        if step_name == "eligibility" and step_result.get("detail"):
            eligibility = step_result["detail"].get("eligibility", eligibility)

        step_ok = step_result.get("ok") is True
        step_status = "completed" if step_ok else "failed"
        if step_result.get("hitl_blocked"):
            step_status = "awaiting_hitl"

        retry_attempts = exec_result.get("retry_attempts") or []
        attempt = len(retry_attempts) + 1 if step_ok else max(len(retry_attempts), 1)
        error_if_any = None if step_ok else exec_result.get("last_error")
        dlq_detail = exec_result.get("dlq_detail")
        dlq_if_any: dict[str, Any] | None = None
        if exec_result.get("dlq_status") == "queued" and dlq_detail:
            dlq_if_any = {
                "entry_id": dlq_detail.get("entry_id"),
                "entry_path": dlq_detail.get("entry_path"),
                "dlq_index_path": dlq_detail.get("dlq_index_path"),
                "failure_class": exec_result.get("failure_class"),
            }

        rec = _step_record(
            step_name,
            step_status=step_status,
            started_at=step_started,
            artifacts=step_result.get("artifacts") or {},
            error=step_result.get("error"),
            detail=step_result.get("detail"),
            retry_count=exec_result.get("retry_count", 0),
            last_error=exec_result.get("last_error"),
            last_error_at=exec_result.get("last_error_at"),
            dlq_status=exec_result.get("dlq_status", "none"),
            retry_attempts=retry_attempts or None,
            attempt=attempt,
            error_if_any=error_if_any,
            dlq_if_any=dlq_if_any,
        )
        if dlq_detail:
            rec["detail"] = dict(rec.get("detail") or {})
            rec["detail"]["dlq"] = dlq_detail
        run_log["steps"].append(rec)

        if step_result.get("hitl_blocked"):
            cp_field = (
                "checkpoint_a_status"
                if step_name == "checkpoint_a"
                else "checkpoint_b_status"
            )
            pause_reason = (
                PAUSE_REASON_CHECKPOINT_A
                if step_name == "checkpoint_a"
                else PAUSE_REASON_CHECKPOINT_B
            )
            cp_updates: dict[str, Any] = {cp_field: "pending"}
            _update_automation_state(
                case_dir,
                current_step=step_name,
                automation_status="paused",
                pause_reason=pause_reason,
                requires_hitl_checkpoint=True,
                allowed_to_auto_proceed=False,
                last_error=step_result.get("error"),
                checkpoint_resume_step=None,
                **cp_updates,
            )
            if step_name == "checkpoint_b":
                readiness = maybe_update_delivery_readiness(
                    case_dir, updated_by="tabular_automation_driver"
                )
                rec["detail"] = dict(rec.get("detail") or {})
                rec["detail"]["delivery_readiness"] = readiness
            notify_internal(
                case_dir,
                EVENT_CHECKPOINT_PENDING,
                {
                    "checkpoint": "a" if step_name == "checkpoint_a" else "b",
                    "checkpoint_status": "pending",
                    "step_name": step_name,
                    "pause_reason": pause_reason,
                    "error": step_result.get("error"),
                },
                case_id=case_id,
            )
            overall_ok = False
            run_log["message"] = step_result.get("error") or f"blocked at {step_name}"
            break

        if step_name == "checkpoint_b" and step_ok:
            artifacts = step_result.get("artifacts") or {}
            skip_reason = artifacts.get("skip_reason")
            cp_b_status = "not_required" if skip_reason else "approved"
            sync_checkpoint_b_state_and_readiness(
                case_dir,
                checkpoint_b_status=cp_b_status,
                step_status="completed",
                current_step="delivery",
                updated_by="tabular_automation_driver",
            )

        if not step_ok:
            overall_ok = False
            _update_automation_state(
                case_dir,
                current_step=step_name,
                automation_status="failed",
                last_error=step_result.get("error"),
                last_error_at=exec_result.get("last_error_at"),
                retry_count=exec_result.get("retry_count", 0),
                dlq_status=exec_result.get("dlq_status", "none"),
                allowed_to_auto_proceed=False,
            )
            run_log["retry_count"] = exec_result.get("retry_count", 0)
            run_log["last_error"] = exec_result.get("last_error")
            run_log["last_error_at"] = exec_result.get("last_error_at")
            run_log["dlq_status"] = exec_result.get("dlq_status", "none")
            run_log["message"] = step_result.get("error") or f"failed at {step_name}"
            if step_result.get("terminal"):
                break
            break

        if step_name == "eligibility" and step_result.get("terminal"):
            overall_ok = False
            _update_automation_state(
                case_dir,
                current_step=step_name,
                automation_status="failed",
                last_error=step_result.get("error"),
                allowed_to_auto_proceed=False,
            )
            run_log["message"] = "eligibility rejected"
            break

    else:
        partial = stop_after is not None and stop_after != STEP_ORDER[-1]
        _update_automation_state(
            case_dir,
            current_step=steps[-1] if steps else STEP_ORDER[-1],
            automation_status="running" if partial else "completed",
            requires_hitl_checkpoint=False,
            allowed_to_auto_proceed=True if partial else False,
            clear_last_error=True,
            retry_count=0,
            dlq_status="none",
        )
        run_log["message"] = (
            f"stopped after {steps[-1]}" if partial else "automation chain completed"
        )
        overall_ok = True
        if not partial:
            approval = load_approval(case_dir)
            if approval.get("ok") is not False:
                maybe_notify_completed_delivery_ready(
                    case_dir,
                    previous_delivery_ready=bool(approval.get("delivery_ready")),
                    delivery_ready=bool(approval.get("delivery_ready")),
                    automation_status="completed",
                    previous_automation_status="running",
                    case_id=case_id,
                    source="driver_chain_complete",
                    extra={"run_id": run_id},
                )

    if stop_reason:
        overall_ok = False

    run_log["ended_at"] = utc_now_iso()
    run_log["ok"] = overall_ok
    if not run_log.get("message"):
        run_log["message"] = "completed" if overall_ok else "failed"

    final_state = load_state(case_dir)
    run_log["automation_status"] = final_state.get("automation_status")
    run_log["retry_count"] = final_state.get("retry_count", run_log.get("retry_count", 0))
    run_log["last_error"] = final_state.get("last_error", run_log.get("last_error"))
    run_log["last_error_at"] = final_state.get("last_error_at", run_log.get("last_error_at"))
    run_log["dlq_status"] = final_state.get("dlq_status", run_log.get("dlq_status", "none"))

    log_path = _save_run_log(case_dir, run_log)

    return {
        "ok": overall_ok,
        "command": "run",
        "case_dir": _rel_path(case_dir),
        "case_id": case_id,
        "cleaning_profile_id": cleaning_profile_id,
        "run_id": run_id,
        "run_log_path": _rel_path(log_path),
        "automation_status": final_state.get("automation_status"),
        "current_step": final_state.get("current_step"),
        "steps_executed": [s["step_name"] for s in run_log["steps"]],
        "run_log": run_log,
        "message": run_log["message"],
        "stop_reason": stop_reason,
    }
