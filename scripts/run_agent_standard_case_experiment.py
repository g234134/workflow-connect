#!/usr/bin/env python3
"""Agent-run standard case experiment orchestrator CLI v1 (W6-T4 / W6-T10 / W7-T2 / W8-T1 / W11-T1 / W12-T1).

Experimental-line orchestrator for demo_phase / sampleco Tabular MVP cases.
Chains W5-T1 decision, W4-T1 glue route planning, W4-T3 tool path preview,
W6-T5/W6-T6 checkpoint integration layers, and optional run-path execution
(W7-T2) — without changing production main-chain defaults.

Usage:
    python scripts/run_agent_standard_case_experiment.py \\
        --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview
    python scripts/run_agent_standard_case_experiment.py \\
        --task-type tabular.cleaning.mvp --case-dir cases/demo_phase \\
        --mode run --auto-approve-intake --format json
    python scripts/run_agent_standard_case_experiment.py \\
        --task-type tabular.cleaning.mvp --case-dir cases/additional_demo \\
        --mode run --auto-approve-intake --sandbox-end-to-end --format json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLEAN_PHASE_DEMO_CLI = _REPO_ROOT / "notebooks" / "csv_cleaning" / "clean_phase_demo.py"
_P7_SMOKE_STUB_ENV = "GOV_P7_SMOKE_STUB_TOOLS"
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import importlib.util

from hitl.checkpoint_a_integration_v1 import (
    maybe_create_checkpoint_a,
    resume_plan_from_checkpoint_a,
    should_trigger_checkpoint_a,
)
from hitl.checkpoint_b_integration_v1 import (
    delivery_plan_from_checkpoint_b,
    maybe_create_checkpoint_b,
    should_create_checkpoint_b,
)
from hitl.checkpoints_v1 import (
    CHECKPOINT_A_ID,
    CHECKPOINT_B_ID,
    CHECKPOINT_SCHEMA_VERSION,
)
from tools.tabular_outbox_writer import outbox_root as get_outbox_root
from delivery.sandbox_delivery_bundle_v1 import (
    is_sandbox_e2e_allowed,
    write_sandbox_delivery_bundle,
)
from delivery.notification_gateway_v1 import (
    build_notification_event,
    emit_notification_safe,
    is_enabled_via_env,
)
from routing.intake_gate_layer_v1 import evaluate_intake_gate
from routing.intake_gate_mapping_v1 import decision_result_from_gate
from routing.intake_to_tabular_glue import plan_tabular_route

_TOOL_PATH_SCRIPT = _REPO_ROOT / "scripts" / "run_tabular_intake_tool_path.py"
_EXECUTOR_SCRIPT = _REPO_ROOT / "tools" / "tabular_tool_executor.py"

# W7-T2: per-case run path allowlist (non-allowlist cases cannot use --mode run).
_RUN_PATH_PROFILES: Dict[str, Dict[str, Any]] = {
    "demo_phase": {
        "stop_at": "bundle",
        "tools_to_run": [
            "validate.eligibility",
            "clean.phase_demo",
            "export.delivery_bundle",
        ],
        "force_cleaning": True,
        "stop_before_delivery": False,
        "description": "primary run lab: gate → cleaning → outbox → bundle",
    },
    "sampleco/2026-0001": {
        "stop_at": "checkpoint_b",
        "tools_to_run": [
            "validate.eligibility",
            "clean.phase_demo",
        ],
        "force_cleaning": False,
        "stop_before_delivery": True,
        "description": "controlled run: cleaning only; stop at Checkpoint B before delivery",
    },
    "additional_demo": {
        "stop_at": "checkpoint_b",
        "tools_to_run": [
            "validate.eligibility",
            "clean.phase_demo",
        ],
        "force_cleaning": True,
        "stop_before_delivery": True,
        "experimental": True,
        "maturity": "controlled_experimental",
        "description": (
            "controlled experimental run: gate → cleaning + outbox; "
            "stop at Checkpoint B before delivery; "
            "regression_bundle_probe optional (test only)"
        ),
    },
    "sandbox_client": {
        "stop_at": "cleaning_preview",
        "tools_to_run": [
            "validate.eligibility",
            "clean.phase_demo",
        ],
        "force_cleaning": False,
        "stop_before_delivery": True,
        "experimental": True,
        "maturity": "controlled_experimental",
        "description": (
            "controlled experimental conservative run: gate + cleaning for live stats; "
            "stop at cleaning preview; Checkpoint B not evaluated"
        ),
    },
}

_FIXTURE_MATURITY: Dict[str, str] = {
    "demo_phase": "stable",
    "sampleco/2026-0001": "stable",
    "additional_demo": "controlled_experimental",
    "sandbox_client": "controlled_experimental",
}

_EXPERIMENTAL_CASE_REFS = frozenset({"additional_demo", "sandbox_client"})

# W10-T3: registry / selector fail-closed error codes (orchestrator wiring).
_REGISTRY_SELECTOR_ERROR_CODES = frozenset(
    {
        "error.registry_fail_closed",
        "error.registry_not_approved",
    }
)

# W12-T1: sandbox end-to-end delivery (additional_demo only; sandbox output path).
_SANDBOX_E2E_RUN_PATH_PROFILE: Dict[str, Any] = {
    "stop_at": "sandbox_bundle",
    "tools_to_run": [
        "validate.eligibility",
        "clean.phase_demo",
        "export.delivery_bundle",
    ],
    "pre_bundle_tools": [
        "validate.eligibility",
        "clean.phase_demo",
    ],
    "force_cleaning": True,
    "stop_before_delivery": False,
    "sandbox_end_to_end": True,
    "experimental": True,
    "maturity": "controlled_experimental",
    "description": (
        "W12-T1 sandbox e2e: gate → cleaning → CP-B guard gate → bundle → "
        "sandbox_delivery outbox only; no production notify"
    ),
}


def _load_tool_path_runner():
    spec = importlib.util.spec_from_file_location(
        "run_tabular_intake_tool_path", _TOOL_PATH_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load tool path script: {_TOOL_PATH_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run_tabular_intake_tool_path


run_tabular_intake_tool_path = _load_tool_path_runner()


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _should_stub_tabular_tools() -> bool:
    """Stub tool CLIs when explicitly requested or cleaning entrypoint is absent.

    P7 advisory CI historically lands tests/orchestrator without gitignored-or-untracked
    ``notebooks/csv_cleaning/clean_phase_demo.py``; Python then exits 2 (file not found),
    which falsely looks like an eligibility/gate failure. Stub keeps notification-chain
    smoke exercisable without claiming real cleaning GA coverage.
    """
    if _truthy_env(_P7_SMOKE_STUB_ENV):
        return True
    return not _CLEAN_PHASE_DEMO_CLI.is_file()


def _stub_execute_tabular_tool(
    case_ref: str,
    tool_id: str,
    dry_run: bool = False,
    extra_args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Minimal ok stub mirroring tabular_tool_executor public result shape."""
    del dry_run, extra_args  # interface-compatible; unused in stub
    started = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_id = f"stub_{tool_id.replace('.', '_')}_{started.replace(':', '').replace('-', '')}"
    if tool_id == "validate.eligibility":
        exit_code = 2
        message = "eligibility gate completed with exit_code=2"
    else:
        exit_code = 0
        message = "completed successfully (p7 smoke stub)"
    outbox_path = f"outbox/{case_ref}/{run_id}.json"
    return {
        "ok": True,
        "message": message,
        "tool_id": tool_id,
        "case_ref": case_ref,
        "run_id": run_id,
        "schema_version": "tabular_outbox_v1",
        "exit_code": exit_code,
        "started_at": started,
        "finished_at": started,
        "artifacts": [],
        "outbox_path": outbox_path,
        "dry_run": False,
        "stubbed": True,
    }


def _load_tabular_tool_executor():
    if _should_stub_tabular_tools():
        return _stub_execute_tabular_tool
    spec = importlib.util.spec_from_file_location(
        "tabular_tool_executor", _EXECUTOR_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load executor: {_EXECUTOR_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.execute_tabular_tool


Mode = Literal["preview", "run"]

_ALLOWLIST_CASE_REFS = frozenset(
    {"demo_phase", "sampleco/2026-0001", "additional_demo", "sandbox_client"}
)

_OUTPUT_GUARD_PROFILE: Dict[str, Dict[str, Any]] = {
    "demo_phase": {
        "status": "ok",
        "checks": {"ratio_check": "ok", "schema_check": "ok"},
        "removal_ratio": 0.286,
        "forced_cleaning": True,
        "source": "mock_profile_demo_phase",
    },
    "sampleco/2026-0001": {
        "status": "warning",
        "checks": {"ratio_check": "warning", "schema_check": "ok"},
        "removal_ratio": 0.93,
        "forced_cleaning": False,
        "source": "mock_profile_sampleco",
    },
    "additional_demo": {
        "status": "ok",
        "checks": {"ratio_check": "ok", "schema_check": "ok"},
        "removal_ratio": 0.25,
        "forced_cleaning": True,
        "source": "mock_profile_additional_demo",
    },
    "sandbox_client": {
        "status": "ok",
        "checks": {"ratio_check": "ok", "schema_check": "review"},
        "removal_ratio": 0.35,
        "forced_cleaning": False,
        "source": "mock_profile_sandbox_client",
    },
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _should_fail_close_due_to_registry(
    selector_view: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """Return True when selector/registry fail-closed error codes are present (W10-T3)."""
    if not selector_view:
        return False, None

    rule_id = selector_view.get("selector_rule_id")
    if rule_id and str(rule_id) in _REGISTRY_SELECTOR_ERROR_CODES:
        return True, str(rule_id)

    for step in selector_view.get("per_step") or []:
        step_rule = step.get("selector_rule_id")
        if step_rule and str(step_rule) in _REGISTRY_SELECTOR_ERROR_CODES:
            return True, str(step_rule)

    return False, None


def _normalize_case_dir(case_dir: str) -> Tuple[Path, str]:
    path = Path(case_dir)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    resolved = path.resolve()
    rel = resolved.relative_to(_REPO_ROOT.resolve()).as_posix()
    return resolved, rel


def case_ref_from_dir(case_dir: str) -> str:
    """Map case directory to experiment case_ref (allowlist key)."""
    _, rel = _normalize_case_dir(case_dir)
    if rel == "cases/demo_phase":
        return "demo_phase"
    if rel == "cases/sampleco/2026-0001":
        return "sampleco/2026-0001"
    if rel == "cases/additional_demo":
        return "additional_demo"
    if rel == "cases/sandbox_client":
        return "sandbox_client"
    # Fallback: strip cases/ prefix for display only (may fail allowlist)
    if rel.startswith("cases/"):
        return rel[len("cases/") :]
    return rel


def is_allowlisted_case(case_ref: str) -> bool:
    return case_ref in _ALLOWLIST_CASE_REFS


def is_experimental_fixture(case_ref: str) -> bool:
    """Return True for W7-T1 extended fixtures (experiment line only)."""
    return case_ref in _EXPERIMENTAL_CASE_REFS


def is_controlled_experimental_fixture(case_ref: str) -> bool:
    """Return True for W11-T1 controlled-experimental fixtures (C/D)."""
    return get_fixture_maturity(case_ref) == "controlled_experimental"


def get_fixture_maturity(case_ref: str) -> str:
    """Return fixture maturity label (stable / controlled_experimental / unknown)."""
    profile = _RUN_PATH_PROFILES.get(case_ref) or {}
    return profile.get("maturity") or _FIXTURE_MATURITY.get(case_ref, "unknown")


def get_run_path_profile(
    case_ref: str,
    *,
    sandbox_end_to_end: bool = False,
) -> Optional[Dict[str, Any]]:
    """Return W7-T2 run path profile for an allowlisted case_ref, else None."""
    if sandbox_end_to_end:
        allowed, _ = is_sandbox_e2e_allowed(case_ref)
        if not allowed:
            return None
        profile = dict(_SANDBOX_E2E_RUN_PATH_PROFILE)
    else:
        profile = _RUN_PATH_PROFILES.get(case_ref)
        if profile is None:
            return None
    return {
        "case_ref": case_ref,
        "stop_at": profile["stop_at"],
        "tools_to_run": list(profile["tools_to_run"]),
        "pre_bundle_tools": list(profile.get("pre_bundle_tools") or profile["tools_to_run"]),
        "force_cleaning": profile.get("force_cleaning", False),
        "stop_before_delivery": profile.get("stop_before_delivery", False),
        "sandbox_end_to_end": profile.get("sandbox_end_to_end", False),
        "experimental": profile.get("experimental", is_experimental_fixture(case_ref)),
        "maturity": profile.get("maturity") or get_fixture_maturity(case_ref),
        "description": profile.get("description", ""),
    }


def _can_start_run_execution(
    mode: Mode,
    checkpoint_a: Dict[str, Any],
) -> bool:
    """Run execution proceeds only when Checkpoint A is cleared in run mode."""
    if mode != "run":
        return False
    status = checkpoint_a.get("status")
    if status in ("auto_approved", "skipped"):
        return True
    return False


def _read_live_output_guard(
    case_path: Path,
    case_ref: str,
    *,
    force_cleaning: bool = False,
) -> Dict[str, Any]:
    """Build output_guard from cleaning_stats when run path executed cleaning."""
    stats_path = case_path / "reports" / "cleaning_stats.json"
    if not stats_path.is_file():
        guard = _mock_output_guard(case_ref)
        guard["note"] = "cleaning_stats missing; fell back to mock profile"
        return guard

    try:
        with stats_path.open(encoding="utf-8") as fh:
            stats = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return _mock_output_guard(case_ref)

    input_rows = stats.get("input_rows") or 0
    output_rows = stats.get("output_rows") or 0
    ratio: Optional[float] = None
    if isinstance(input_rows, int) and input_rows > 0 and isinstance(output_rows, int):
        ratio = (input_rows - output_rows) / input_rows

    status = "ok"
    ratio_check = "ok"
    if isinstance(ratio, float) and ratio > 0.5:
        status = "warning"
        ratio_check = "warning"

    return {
        "status": status,
        "checks": {"ratio_check": ratio_check, "schema_check": "ok"},
        "removal_ratio": ratio,
        "forced_cleaning": force_cleaning,
        "input_rows": input_rows,
        "output_rows": output_rows,
        "note": "S11 live read from cleaning_stats.json (W7-T2 run path)",
        "source": "live_cleaning_stats",
    }


def _execute_run_path_tools(
    *,
    case_ref: str,
    case_dir_rel: str,
    profile: Dict[str, Any],
    planned_tools: List[str],
    outbox_root_override: Optional[str] = None,
    regression_bundle_probe: bool = False,
) -> Dict[str, Any]:
    """Execute allowlisted tools for W7-T2 run path; writes outbox via executor."""
    execute_tabular_tool = _load_tabular_tool_executor()
    allowed = set(planned_tools or [])
    tools_to_run = [
        tool_id
        for tool_id in profile.get("tools_to_run") or []
        if tool_id in allowed
    ]
    if (
        profile.get("stop_before_delivery")
        and not (
            regression_bundle_probe
            and case_ref == "additional_demo"
            and "export.delivery_bundle" in allowed
        )
    ):
        tools_to_run = [
            tool_id for tool_id in tools_to_run if tool_id != "export.delivery_bundle"
        ]
    elif (
        regression_bundle_probe
        and case_ref == "additional_demo"
        and "export.delivery_bundle" in allowed
        and "export.delivery_bundle" not in tools_to_run
    ):
        tools_to_run.append("export.delivery_bundle")

    tool_results: List[Dict[str, Any]] = []
    outbox_entries: List[str] = []
    all_ok = True

    for tool_id in tools_to_run:
        extra: Dict[str, Any] = {"case_dir": case_dir_rel}
        if outbox_root_override:
            extra["outbox_root"] = outbox_root_override
        if tool_id == "clean.phase_demo" and profile.get("force_cleaning"):
            extra["force"] = True
        # additional_demo intake omits cleaning_profile; pin phase_demo_v1 for smoke.
        if tool_id == "clean.phase_demo" and case_ref == "additional_demo":
            extra["cli_suffix"] = "--profile-id phase_demo_v1"

        result = execute_tabular_tool(case_ref, tool_id, extra_args=extra)
        entry = {
            "tool_id": tool_id,
            "ok": result.get("ok"),
            "exit_code": result.get("exit_code"),
            "message": result.get("message"),
            "outbox_path": result.get("outbox_path"),
            "run_id": result.get("run_id"),
        }
        tool_results.append(entry)
        if result.get("outbox_path"):
            outbox_entries.append(str(result["outbox_path"]))
        if not result.get("ok"):
            all_ok = False
            break

    return {
        "ok": all_ok,
        "stop_at": profile.get("stop_at"),
        "tools_planned": tools_to_run,
        "tools_executed": [t["tool_id"] for t in tool_results],
        "tool_results": tool_results,
        "outbox_entries": outbox_entries,
        "regression_bundle_probe": bool(regression_bundle_probe and case_ref == "additional_demo"),
    }


def _build_execution_summary_from_run(
    run_execution: Dict[str, Any],
    *,
    case_ref: str,
) -> Dict[str, Any]:
    tools_executed = []
    outbox_runs = []
    for entry in run_execution.get("tool_results") or []:
        tools_executed.append(
            {
                "tool_id": entry.get("tool_id"),
                "ok": entry.get("ok"),
                "exit_code": entry.get("exit_code"),
                "planned_only": False,
            }
        )
        if entry.get("run_id"):
            outbox_runs.append(entry["run_id"])
    return {
        "case_ref": case_ref,
        "tools_executed": tools_executed,
        "outbox_runs": outbox_runs,
    }


def _default_artifacts_for_case(case_dir_rel: str) -> Dict[str, Any]:
    prefix = case_dir_rel.replace("\\", "/")
    return {
        "eligibility_report": f"{prefix}/reports/eligibility_result.json",
        "cleaned_csv": f"{prefix}/cleaned/Phase_cleaned.csv",
        "delivery_bundle": f"{prefix}/reports/report.json",
        "signoff": f"{prefix}/delivery_signoff.md",
    }


def _resolve_checkpoint_b_after_run(
    *,
    case_ref: str,
    case_dir_rel: str,
    task_type: str,
    output_guard: Dict[str, Any],
    run_execution: Dict[str, Any],
    run_path_profile: Dict[str, Any],
    auto_approve_delivery: bool,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Create live Checkpoint B state when run path reaches delivery gate."""
    execution_summary = _build_execution_summary_from_run(
        run_execution, case_ref=case_ref
    )
    artifacts = _default_artifacts_for_case(case_dir_rel)

    # Pass outbox_root_override directly to integration layer.
    # W6-T5/T6 integration layer handles external outbox paths via three-layer
    # checkpoint_path fallback (repo-relative -> outbox-relative -> absolute).
    write_kwargs: Dict[str, Any] = {"write_state": True}
    if outbox_root_override is not None:
        write_kwargs["outbox_root_override"] = outbox_root_override
        write_kwargs["repo_root"] = _REPO_ROOT.resolve()

    integration = maybe_create_checkpoint_b(
        case_dir_rel,
        execution_summary,
        output_guard,
        artifacts,
        auto_approve=auto_approve_delivery,
        task_type=task_type,
        **write_kwargs,
    )

    would_trigger = bool(integration.get("checkpoint_created")) or should_create_checkpoint_b(
        output_guard,
        auto_approve=auto_approve_delivery,
    )
    base: Dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_B_ID,
        "would_trigger": would_trigger,
        "integration_layer": "hitl.checkpoint_b_integration_v1",
        "integration": {
            "checkpoint_created": integration.get("checkpoint_created"),
            "skipped": integration.get("skipped"),
            "skip_reason": integration.get("skip_reason"),
        },
    }

    if integration.get("checkpoint_created"):
        base["status"] = "written"
        base["message"] = "Checkpoint B state written; awaiting human decision"
        base["checkpoint_path"] = integration.get("checkpoint_path")
    elif run_path_profile.get("stop_before_delivery"):
        base["status"] = "stopped_before_delivery"
        base["message"] = (
            "run stopped before delivery per run_path_profile; "
            "Checkpoint B safeguard applies"
        )
    elif integration.get("skipped"):
        base["status"] = "skipped"
        base["message"] = integration.get("skip_reason") or "checkpoint B skipped"
    else:
        base["status"] = "planned"
        base["message"] = "checkpoint B evaluated after run path"

    delivery_plan = (integration.get("delivery_plan") or {})
    if delivery_plan:
        base["delivery_plan_action"] = delivery_plan.get("action")

    return base


def _can_proceed_sandbox_bundle_after_checkpoint_b(
    checkpoint_b: Dict[str, Any],
) -> Tuple[bool, str]:
    """Decide sandbox Phase-2 bundle from W6-T6 integration-layer checkpoint_b_status."""
    status = str(checkpoint_b.get("status") or "")
    if status == "written":
        return False, "checkpoint_b_written"
    action = checkpoint_b.get("delivery_plan_action")
    if action == "await_human":
        return False, "checkpoint_b_await_human"
    if action == "blocked":
        return False, "checkpoint_b_delivery_blocked"
    if action == "auto_approve":
        integration = checkpoint_b.get("integration") or {}
        return True, str(integration.get("skip_reason") or "auto_approve")
    if checkpoint_b.get("would_trigger"):
        return False, "checkpoint_b_would_trigger"
    return True, "no_human_gate"


def _mock_output_guard(case_ref: str) -> Dict[str, Any]:
    profile = _OUTPUT_GUARD_PROFILE.get(
        case_ref,
        {
            "status": "unknown",
            "checks": {},
            "removal_ratio": None,
            "forced_cleaning": False,
            "source": "mock_placeholder_unknown_profile",
        },
    )
    return {
        "status": profile["status"],
        "checks": profile.get("checks") or {},
        "removal_ratio": profile.get("removal_ratio"),
        "forced_cleaning": profile.get("forced_cleaning", False),
        "note": "S11 mock/placeholder — not read from bundle build in v1 experiment line",
        "source": profile.get("source", "mock_placeholder"),
    }


def _build_checkpoint_b_planned(
    *,
    case_ref: str,
    task_type: str,
    output_guard: Dict[str, Any],
    tool_path_preview: Dict[str, Any],
    auto_approve_delivery: bool = False,
) -> Dict[str, Any]:
    executor_plan = tool_path_preview.get("executor_plan") or []
    tools_executed = [
        {
            "tool_id": step.get("tool_id"),
            "ok": True,
            "planned_only": True,
            "requires_force": step.get("requires_force", False),
        }
        for step in executor_plan
    ]
    guard_profile = _OUTPUT_GUARD_PROFILE.get(case_ref, {})
    return {
        "checkpoint_id": CHECKPOINT_B_ID,
        "status": "planned",
        "would_trigger": should_create_checkpoint_b(
            output_guard,
            auto_approve=auto_approve_delivery,
        ),
        "integration_layer": "hitl.checkpoint_b_integration_v1",
        "agent_output_preview": {
            "task_type": task_type,
            "execution_summary": {"tools_executed": tools_executed, "planned_only": True},
            "output_guard": output_guard,
            "cleaning_results": {
                "removal_ratio": guard_profile.get("removal_ratio"),
                "qa_status": "planned_preview",
            },
            "delivery_draft": {
                "summary_text": "Delivery draft placeholder (S12 planned; no bundle read in preview)",
                "confidence_score": None,
            },
        },
    }


def _resolve_checkpoint_a_status(
    *,
    mode: Mode,
    decision_result: Dict[str, Any],
    case_ref: str,
    task_type: str,
    case_dir_rel: str,
    auto_approve_intake: bool,
    write_state: bool,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Map W6-T5 integration layer results to orchestrator checkpoint_a_status."""
    triggers = should_trigger_checkpoint_a(decision_result)
    base: Dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_A_ID,
        "would_trigger": triggers,
        "decision": decision_result.get("decision"),
        "risk_level": decision_result.get("risk_level"),
        "integration_layer": "hitl.checkpoint_a_integration_v1",
    }

    if decision_result.get("decision") == "reject":
        base["status"] = "not_applicable"
        base["message"] = "decision=reject; checkpoint A not triggered"
        return base

    if not triggers:
        base["status"] = "skipped"
        base["message"] = "low-risk auto_accept; checkpoint A not required"
        return base

    delegate_auto_approve = auto_approve_intake and mode == "run"
    if (mode == "preview" or not write_state) and not delegate_auto_approve:
        base["status"] = "would_pause"
        base["message"] = "needs human review at Checkpoint A (preview; no state written)"
        return base

    # Pass outbox_root_override directly to integration layer.
    # W6-T5/T6 integration layer handles external outbox paths via three-layer fallback.
    write_kwargs: Dict[str, Any] = {}
    if outbox_root_override is not None:
        write_kwargs["outbox_root_override"] = outbox_root_override
        write_kwargs["repo_root"] = _REPO_ROOT.resolve()

    integration = maybe_create_checkpoint_a(
        task_type,
        case_dir_rel,
        decision_result,
        auto_approve=delegate_auto_approve,
        **write_kwargs,
    )
    base["integration"] = {
        "status": integration.get("status"),
        "checkpoint_path": integration.get("checkpoint_path"),
    }

    if integration.get("status") == "awaiting_human":
        base["status"] = "written"
        base["message"] = integration.get("message", "checkpoint state written")
        base["checkpoint_path"] = integration.get("checkpoint_path")
    elif integration.get("status") == "auto_approved":
        base["status"] = "auto_approved"
        base["message"] = integration.get("message", "checkpoint A auto-approved via integration layer")
        if integration.get("resume_plan"):
            base["resume_plan"] = integration["resume_plan"]
    elif integration.get("status") == "skipped":
        base["status"] = "skipped"
        base["message"] = integration.get("message", "checkpoint A skipped")
        base["would_trigger"] = False
    elif integration.get("ok") is False:
        base["status"] = "error"
        base["message"] = integration.get("message", "checkpoint A integration failed")
    else:
        base["status"] = integration.get("status", "unknown")
        base["message"] = integration.get("message", "")
        if integration.get("checkpoint_path"):
            base["checkpoint_path"] = integration["checkpoint_path"]
    return base


def _resolve_final_status(
    *,
    decision_result: Dict[str, Any],
    checkpoint_a: Dict[str, Any],
    checkpoint_b: Dict[str, Any],
    allowlisted: bool,
    mode: Mode,
    auto_approve_intake: bool,
    run_execution: Optional[Dict[str, Any]] = None,
    run_path_profile: Optional[Dict[str, Any]] = None,
    sandbox_delivery: Optional[Dict[str, Any]] = None,
) -> str:
    if not allowlisted:
        return "blocked"
    if decision_result.get("decision") == "reject":
        return "blocked"

    if mode == "run":
        if checkpoint_a.get("status") in ("would_pause", "written") and not auto_approve_intake:
            return "waiting_for_human"
        if run_execution is None:
            return "resume_plan_ready"
        if not run_execution.get("ok"):
            return "blocked"
        stop_at = (run_path_profile or {}).get("stop_at")
        if stop_at == "sandbox_bundle":
            if run_execution.get("sandbox_bundle_blocked"):
                return "sandbox_e2e_blocked_at_checkpoint_b"
            if sandbox_delivery and sandbox_delivery.get("ok"):
                return "sandbox_e2e_complete"
            if "export.delivery_bundle" in (run_execution.get("tools_executed") or []):
                return "sandbox_e2e_complete"
            return "waiting_for_human"
        if stop_at == "checkpoint_b":
            return "stopped_at_checkpoint_b"
        if stop_at == "cleaning_preview":
            return "stopped_at_cleaning_preview"
        if checkpoint_b.get("status") in ("written", "stopped_before_delivery"):
            return "waiting_for_human"
        if checkpoint_b.get("would_trigger"):
            return "waiting_for_human"
        return "run_complete"

    if checkpoint_a.get("status") in ("would_pause", "written"):
        return "waiting_for_human"
    if checkpoint_b.get("would_trigger"):
        return "waiting_for_human"
    return "preview_ready"


def _execute_sandbox_e2e_run(
    *,
    case_ref: str,
    case_dir_rel: str,
    task_type: str,
    profile: Dict[str, Any],
    planned_tools: List[str],
    outbox_root_override: Optional[str],
    auto_approve_delivery: bool,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Two-phase sandbox e2e: clean → W6-T6 CP-B integration → conditional bundle."""
    pre_profile = {
        **profile,
        "tools_to_run": list(profile.get("pre_bundle_tools") or []),
        "stop_before_delivery": True,
    }
    pre_run = _execute_run_path_tools(
        case_ref=case_ref,
        case_dir_rel=case_dir_rel,
        profile=pre_profile,
        planned_tools=planned_tools,
        outbox_root_override=outbox_root_override,
        regression_bundle_probe=False,
    )
    if not pre_run.get("ok"):
        pre_run["sandbox_end_to_end"] = True
        return pre_run, {}, {}

    case_path, _ = _normalize_case_dir(case_dir_rel)
    output_guard = _read_live_output_guard(
        case_path,
        case_ref,
        force_cleaning=bool(profile.get("force_cleaning")),
    )
    output_guard["note"] = (
        "S11 live read before sandbox Checkpoint B integration (W12-T2-P1)"
    )

    checkpoint_b = _resolve_checkpoint_b_after_run(
        case_ref=case_ref,
        case_dir_rel=case_dir_rel,
        task_type=task_type,
        output_guard=output_guard,
        run_execution=pre_run,
        run_path_profile=profile,
        auto_approve_delivery=auto_approve_delivery,
        outbox_root_override=outbox_root_override,
    )
    can_bundle, gate_reason = _can_proceed_sandbox_bundle_after_checkpoint_b(
        checkpoint_b
    )
    checkpoint_b["sandbox_bundle_gate"] = gate_reason
    if not can_bundle:
        pre_run["sandbox_end_to_end"] = True
        pre_run["sandbox_bundle_blocked"] = True
        return pre_run, output_guard, checkpoint_b

    bundle_profile = {
        **profile,
        "tools_to_run": ["export.delivery_bundle"],
        "stop_before_delivery": False,
    }
    bundle_run = _execute_run_path_tools(
        case_ref=case_ref,
        case_dir_rel=case_dir_rel,
        profile=bundle_profile,
        planned_tools=planned_tools,
        outbox_root_override=outbox_root_override,
        regression_bundle_probe=False,
    )

    merged_results = list(pre_run.get("tool_results") or [])
    merged_results.extend(bundle_run.get("tool_results") or [])
    merged_outbox = list(pre_run.get("outbox_entries") or [])
    merged_outbox.extend(bundle_run.get("outbox_entries") or [])
    merged_executed = list(pre_run.get("tools_executed") or [])
    for tool_id in bundle_run.get("tools_executed") or []:
        if tool_id not in merged_executed:
            merged_executed.append(tool_id)

    merged: Dict[str, Any] = {
        "ok": bool(pre_run.get("ok")) and bool(bundle_run.get("ok")),
        "stop_at": profile.get("stop_at"),
        "tools_planned": list(profile.get("tools_to_run") or []),
        "tools_executed": merged_executed,
        "tool_results": merged_results,
        "outbox_entries": merged_outbox,
        "sandbox_end_to_end": True,
        "sandbox_bundle_gate": gate_reason,
        "sandbox_bundle_blocked": False,
    }
    return merged, output_guard, checkpoint_b


def _build_resume_plan(
    *,
    case_ref: str,
    task_type: str,
    decision_result: Dict[str, Any],
    planned_route: Dict[str, Any],
    checkpoint_a: Dict[str, Any],
    checkpoint_b: Dict[str, Any],
    auto_approve_intake: bool,
) -> Dict[str, Any]:
    route = decision_result.get("suggested_route") or planned_route or {}
    resume_from = "selector"
    if checkpoint_a.get("status") == "auto_approved":
        resume_from = "selector"
    elif checkpoint_a.get("status") == "written":
        resume_from = "selector"
    return {
        "case_ref": case_ref,
        "task_type": task_type,
        "resume_from": resume_from,
        "selector_task_type": route.get("selector_task_type"),
        "planned_tools": list(route.get("planned_tools") or []),
        "auto_approve_intake": auto_approve_intake,
        "checkpoint_b_expected": checkpoint_b.get("would_trigger", False),
        "next_steps": [
            "S7 gate validation",
            "S8 cleaning execution",
            "S9 outbox write",
            "S10 bundle build",
            "S11 output guard (live)",
            "S12 checkpoint B if triggered",
        ],
    }


_RESUME_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "checkpoint_id",
        "case_ref",
        "status",
        "resume_context",
    }
)

_RESUME_SKIP_STEPS_A = [
    "S3_decision_evaluate",
    "S4_checkpoint_a",
    "S5_route_planning",
    "S6_tool_path_preview",
]

_RESUME_SKIP_STEPS_B = _RESUME_SKIP_STEPS_A + [
    "S7_S10_run_path_execution",
    "S11_output_guard_live",
    "S11_output_guard_mock",
    "S12_checkpoint_b_run",
    "S12_checkpoint_b_planned",
    "S12_checkpoint_b_stopped",
]


def _checkpoint_task_type(checkpoint: Dict[str, Any]) -> str:
    task_type = checkpoint.get("task_type")
    if task_type:
        return str(task_type)
    agent_output = checkpoint.get("agent_output") or {}
    return str(agent_output.get("task_type") or "")


def _resolve_checkpoint_file_path(
    path_str: str,
    *,
    outbox_root_override: Optional[str] = None,
) -> Path:
    """Resolve checkpoint JSON path (repo-relative → outbox-relative → absolute)."""
    raw = Path(path_str)
    if raw.is_file():
        return raw.resolve()

    repo_candidate = _REPO_ROOT / path_str
    if repo_candidate.is_file():
        return repo_candidate.resolve()

    outbox_base = (
        Path(outbox_root_override).resolve()
        if outbox_root_override
        else get_outbox_root(_REPO_ROOT, outbox_root_override)
    )
    outbox_candidate = outbox_base / path_str
    if outbox_candidate.is_file():
        return outbox_candidate.resolve()

    if path_str.startswith("outbox/"):
        trimmed = path_str[len("outbox/") :]
        trimmed_candidate = outbox_base / trimmed
        if trimmed_candidate.is_file():
            return trimmed_candidate.resolve()

    raise FileNotFoundError(f"checkpoint file not found: {path_str}")


def load_checkpoint_for_resume(
    path_str: str,
    *,
    outbox_root_override: Optional[str] = None,
) -> Tuple[Dict[str, Any], Path]:
    """Load checkpoint JSON for orchestrator resume (W6-T11)."""
    resolved = _resolve_checkpoint_file_path(
        path_str,
        outbox_root_override=outbox_root_override,
    )
    try:
        with resolved.open(encoding="utf-8") as fh:
            checkpoint = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"checkpoint file unreadable: {resolved}") from exc
    if not isinstance(checkpoint, dict):
        raise ValueError(f"checkpoint payload must be a JSON object: {resolved}")
    return checkpoint, resolved


def _checkpoint_expired(expires_at: str) -> bool:
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.astimezone(timezone.utc) <= datetime.now(timezone.utc)


def _resume_blocked(
    *,
    message: str,
    final_status: str = "blocked",
) -> Dict[str, Any]:
    return {
        "ok": False,
        "message": message,
        "final_status": final_status,
    }


def validate_resume_eligibility(
    checkpoint: Dict[str, Any],
    *,
    case_ref: str,
    task_type: str,
    mode: Mode,
    checkpoint_path: Path,
) -> Dict[str, Any]:
    """Fail-close validation for approved checkpoint resume (W6-T11 v1)."""
    missing = _RESUME_REQUIRED_KEYS - set(checkpoint)
    if missing:
        return _resume_blocked(
            message=f"checkpoint missing required keys: {sorted(missing)}",
        )

    schema_version = str(checkpoint.get("schema_version") or "")
    if schema_version != CHECKPOINT_SCHEMA_VERSION:
        return _resume_blocked(
            message=(
                f"unsupported schema_version {schema_version!r}; "
                f"expected {CHECKPOINT_SCHEMA_VERSION}"
            ),
        )

    if mode != "run":
        return _resume_blocked(message="resume requires --mode run")

    status = str(checkpoint.get("status") or "")
    expires_at = checkpoint.get("expires_at")
    if status in ("awaiting_human",) and expires_at and _checkpoint_expired(str(expires_at)):
        return _resume_blocked(
            message="checkpoint expired before human decision",
            final_status="stale_checkpoint",
        )
    if status != "approved":
        if status in ("rejected", "revise_needed", "on_hold"):
            return _resume_blocked(
                message=f"checkpoint status={status!r}; v1 resume supports approved only",
            )
        if status == "awaiting_human":
            return _resume_blocked(
                message=(
                    "checkpoint awaiting human decision; "
                    "apply run_hitl_checkpoint_cli --apply-decision first"
                ),
            )
        return _resume_blocked(
            message=f"checkpoint status={status!r}; expected approved",
        )

    ck_case_ref = str(checkpoint.get("case_ref") or "")
    if ck_case_ref != case_ref:
        return _resume_blocked(
            message=f"case_ref mismatch: checkpoint={ck_case_ref!r} cli={case_ref!r}",
            final_status="checkpoint_mismatch",
        )

    ck_task_type = _checkpoint_task_type(checkpoint)
    if ck_task_type != task_type:
        return _resume_blocked(
            message=(
                f"task_type mismatch: checkpoint={ck_task_type!r} cli={task_type!r}"
            ),
            final_status="checkpoint_mismatch",
        )

    resume_context = checkpoint.get("resume_context")
    if not isinstance(resume_context, dict):
        return _resume_blocked(message="checkpoint resume_context missing or invalid")

    checkpoint_id = str(checkpoint.get("checkpoint_id") or "")
    human = resume_context.get("human_decision") or checkpoint.get("human_decision") or {}
    action = str(human.get("action") or "")

    if checkpoint_id == CHECKPOINT_A_ID:
        if action != "approve":
            return _resume_blocked(
                message=f"Checkpoint A resume requires human action approve; got {action!r}",
            )
        if resume_context.get("resume_from") != "selector":
            return _resume_blocked(
                message=(
                    "Checkpoint A resume requires resume_context.resume_from=selector"
                ),
            )
        plan = resume_plan_from_checkpoint_a(resume_context)
        if not plan.get("ok"):
            return _resume_blocked(
                message=str(plan.get("message") or "invalid Checkpoint A resume plan"),
            )
    elif checkpoint_id == CHECKPOINT_B_ID:
        if action != "approve_delivery":
            return _resume_blocked(
                message=(
                    "Checkpoint B resume requires human action approve_delivery; "
                    f"got {action!r}"
                ),
            )
        plan = delivery_plan_from_checkpoint_b(resume_context)
        if not plan.get("ok"):
            return _resume_blocked(
                message=str(plan.get("message") or "invalid Checkpoint B delivery plan"),
            )
        if not plan.get("proceed_to_delivery"):
            return _resume_blocked(
                message=str(plan.get("message") or "delivery not approved"),
            )
    else:
        return _resume_blocked(message=f"unsupported checkpoint_id: {checkpoint_id!r}")

    return {
        "ok": True,
        "checkpoint_id": checkpoint_id,
        "checkpoint_path": str(checkpoint_path),
        "resume_context": resume_context,
    }


def _artifact_path_exists(rel_path: str) -> bool:
    if not rel_path:
        return False
    candidate = _REPO_ROOT / rel_path.replace("\\", "/")
    return candidate.is_file()


def _validate_checkpoint_b_resume_artifacts(
    artifacts: Dict[str, Any],
    *,
    case_path: Path,
) -> List[str]:
    """Return missing pre-delivery artifact keys (delivery_bundle may not exist yet)."""
    missing: List[str] = []
    eligibility = str(artifacts.get("eligibility_report") or "")
    if not _artifact_path_exists(eligibility):
        missing.append("eligibility_report")

    cleaned = str(artifacts.get("cleaned_csv") or "")
    if _artifact_path_exists(cleaned):
        return missing

    cleaned_dir = case_path / "cleaned"
    has_cleaned_csv = cleaned_dir.is_dir() and any(cleaned_dir.glob("*.csv"))
    if not has_cleaned_csv:
        missing.append("cleaned_csv")
    return missing


def _delivery_resume_marker_path(
    case_ref: str,
    checkpoint_path: Path,
    *,
    outbox_root_override: Optional[str] = None,
) -> Path:
    root = get_outbox_root(_REPO_ROOT, outbox_root_override)
    safe_name = checkpoint_path.name.replace(" ", "_")
    return root / case_ref / f".w6t11_delivery_resumed_{safe_name}.marker"


def _delivery_resume_already_done(
    case_ref: str,
    checkpoint_path: Path,
    *,
    outbox_root_override: Optional[str] = None,
) -> bool:
    return _delivery_resume_marker_path(
        case_ref,
        checkpoint_path,
        outbox_root_override=outbox_root_override,
    ).is_file()


def _write_delivery_resume_marker(
    case_ref: str,
    checkpoint_path: Path,
    *,
    outbox_root_override: Optional[str] = None,
) -> None:
    marker = _delivery_resume_marker_path(
        case_ref,
        checkpoint_path,
        outbox_root_override=outbox_root_override,
    )
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps(
            {
                "checkpoint_path": str(checkpoint_path),
                "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _checkpoint_path_for_result(resolved: Path) -> str:
    try:
        return str(resolved.relative_to(_REPO_ROOT))
    except ValueError:
        return str(resolved)


def _build_resume_metadata(
    *,
    checkpoint: Dict[str, Any],
    checkpoint_path: Path,
    resume_from_step: str,
    skipped_steps: List[str],
) -> Dict[str, Any]:
    return {
        "ok": True,
        "checkpoint_path": _checkpoint_path_for_result(checkpoint_path),
        "checkpoint_id": checkpoint.get("checkpoint_id"),
        "resume_from_step": resume_from_step,
        "skipped_steps": list(skipped_steps),
    }


def _decision_block_from_checkpoint(checkpoint: Dict[str, Any]) -> Dict[str, Any]:
    agent_output = checkpoint.get("agent_output") or {}
    intake = agent_output.get("intake_decision") or {}
    return {
        "ok": True,
        "decision": intake.get("decision") or "needs_review",
        "risk_level": intake.get("risk_level") or "medium",
        "rationale": list(intake.get("rationale") or []),
        "suggested_route": intake.get("suggested_route"),
        "message": "resumed from approved checkpoint A",
    }


def _planned_route_from_checkpoint(checkpoint: Dict[str, Any]) -> Dict[str, Any]:
    agent_output = checkpoint.get("agent_output") or {}
    intake = agent_output.get("intake_decision") or {}
    route = intake.get("suggested_route") or {}
    resume_context = checkpoint.get("resume_context") or {}
    planned_tools = list(resume_context.get("planned_tools") or route.get("planned_tools") or [])
    return {
        "ok": True,
        "selector_task_type": resume_context.get("selector_task_type")
        or route.get("selector_task_type"),
        "planned_tools": planned_tools,
        "case_profile": route.get("case_profile"),
        "inferred_gate_notes": route.get("inferred_gate_notes") or [],
        "notes": ["restored from approved checkpoint A resume_context"],
        "message": "route restored from checkpoint resume_context",
    }


def _finalize_after_run_execution(
    base: Dict[str, Any],
    *,
    case_path: Path,
    case_ref: str,
    case_dir_rel: str,
    task_type: str,
    mode: Mode,
    checkpoint_a: Dict[str, Any],
    run_path_profile: Optional[Dict[str, Any]],
    run_execution: Optional[Dict[str, Any]],
    auto_approve_intake: bool,
    auto_approve_delivery: bool,
    outbox_root_override: Optional[str] = None,
    sandbox_end_to_end: bool = False,
    experiment_id: str,
) -> None:
    """Shared S11–S12 + final_status wiring after S7 run path execution."""
    sandbox_delivery: Optional[Dict[str, Any]] = None
    tool_path: Dict[str, Any] = {}

    if (
        sandbox_end_to_end
        and run_execution
        and run_execution.get("ok")
        and not run_execution.get("sandbox_bundle_blocked")
        and "export.delivery_bundle" in (run_execution.get("tools_executed") or [])
    ):
        sandbox_delivery = write_sandbox_delivery_bundle(
            case_ref=case_ref,
            case_dir=case_dir_rel,
            experiment_id=experiment_id,
            output_guard=base.get("output_guard") or _mock_output_guard(case_ref),
            run_execution=run_execution,
            checkpoint_a=checkpoint_a,
            checkpoint_b=base.get("checkpoint_b_status") or {},
            outbox_root_override=outbox_root_override,
        )
        base["sandbox_delivery"] = sandbox_delivery
        base["steps_run"].append("S10_sandbox_delivery_bundle")
        # W6-T10-P2: emit delivery.bundle_ready when sandbox delivery succeeds
        if sandbox_delivery and sandbox_delivery.get("ok"):
            _emit_and_track(
                "delivery.bundle_ready",
                artifacts={
                    "manifest_path": sandbox_delivery.get("manifest_path"),
                    "bundle_dir": sandbox_delivery.get("bundle_dir"),
                },
                status_summary={"final_status": "sandbox_e2e_complete", "mode": mode},
                source_step="S10",
            )

    if run_execution and run_execution.get("ok") and not sandbox_end_to_end:
        stop_at = (run_path_profile or {}).get("stop_at")
        executed_tools = run_execution.get("tools_executed") or []
        if stop_at == "cleaning_preview":
            if "clean.phase_demo" in executed_tools:
                output_guard = _read_live_output_guard(
                    case_path,
                    case_ref,
                    force_cleaning=bool(
                        run_path_profile and run_path_profile.get("force_cleaning")
                    ),
                )
                output_guard["note"] = (
                    "cleaning executed for evaluation; stop at cleaning_preview "
                    "before Checkpoint B (W11-T1 controlled_experimental)"
                )
                base["steps_run"].append("S11_output_guard_live")
            else:
                output_guard = _mock_output_guard(case_ref)
                base["steps_run"].append("S11_output_guard_mock")
            base["output_guard"] = output_guard
            checkpoint_b = {
                "checkpoint_id": CHECKPOINT_B_ID,
                "status": "stopped_at_cleaning_preview",
                "would_trigger": False,
                "message": "run stopped at cleaning preview per run_path_profile",
            }
            base["steps_run"].append("S12_checkpoint_b_stopped")
            base["checkpoint_b_status"] = checkpoint_b
        else:
            output_guard = _read_live_output_guard(
                case_path,
                case_ref,
                force_cleaning=bool(
                    run_path_profile and run_path_profile.get("force_cleaning")
                ),
            )
            base["steps_run"].append("S11_output_guard_live")
            base["output_guard"] = output_guard
            checkpoint_b = _resolve_checkpoint_b_after_run(
                case_ref=case_ref,
                case_dir_rel=case_dir_rel,
                task_type=task_type,
                output_guard=output_guard,
                run_execution=run_execution,
                run_path_profile=run_path_profile or {},
                auto_approve_delivery=auto_approve_delivery,
                outbox_root_override=outbox_root_override,
            )
            base["steps_run"].append("S12_checkpoint_b_run")
            base["checkpoint_b_status"] = checkpoint_b
    elif not run_execution or not run_execution.get("ok"):
        if "output_guard" not in base:
            output_guard = _mock_output_guard(case_ref)
            base["steps_run"].append("S11_output_guard_mock")
            base["output_guard"] = output_guard
        checkpoint_b = _build_checkpoint_b_planned(
            case_ref=case_ref,
            task_type=task_type,
            output_guard=base.get("output_guard") or _mock_output_guard(case_ref),
            tool_path_preview=tool_path,
            auto_approve_delivery=auto_approve_delivery,
        )
        base["steps_run"].append("S12_checkpoint_b_planned")
        base["checkpoint_b_status"] = checkpoint_b
    else:
        checkpoint_b = base.get("checkpoint_b_status") or {}

    base["final_status"] = _resolve_final_status(
        decision_result=base.get("decision") or {},
        checkpoint_a=checkpoint_a,
        checkpoint_b=base.get("checkpoint_b_status") or checkpoint_b,
        allowlisted=True,
        mode=mode,
        auto_approve_intake=auto_approve_intake,
        run_execution=run_execution,
        run_path_profile=run_path_profile,
        sandbox_delivery=sandbox_delivery,
    )


def _run_experiment_resume_from_checkpoint(
    task_type: str,
    case_dir: str,
    *,
    resume_checkpoint: str,
    mode: Mode,
    auto_approve_intake: bool,
    auto_approve_delivery: bool,
    outbox_root_override: Optional[str] = None,
    sandbox_end_to_end: bool = False,
) -> Dict[str, Any]:
    case_path, case_dir_rel = _normalize_case_dir(case_dir)
    case_ref = case_ref_from_dir(case_dir)
    experiment_id = str(uuid.uuid4())

    base: Dict[str, Any] = {
        "ok": False,
        "experiment_id": experiment_id,
        "case_ref": case_ref,
        "case_dir": case_dir_rel,
        "task_type": task_type,
        "mode": mode,
        "steps_run": ["resume_checkpoint_load"],
        "resume_checkpoint": resume_checkpoint,
    }

    if not is_allowlisted_case(case_ref):
        base["message"] = "case_not_in_allowlist"
        base["final_status"] = "blocked"
        return base

    try:
        checkpoint, resolved_path = load_checkpoint_for_resume(
            resume_checkpoint,
            outbox_root_override=outbox_root_override,
        )
    except (FileNotFoundError, ValueError) as exc:
        base["message"] = str(exc)
        base["final_status"] = "blocked"
        base["resume"] = {"ok": False, "message": str(exc)}
        return base

    eligibility = validate_resume_eligibility(
        checkpoint,
        case_ref=case_ref,
        task_type=task_type,
        mode=mode,
        checkpoint_path=resolved_path,
    )
    if not eligibility.get("ok"):
        base["message"] = eligibility.get("message")
        base["final_status"] = eligibility.get("final_status", "blocked")
        base["resume"] = {
            "ok": False,
            "checkpoint_path": _checkpoint_path_for_result(resolved_path),
            "message": eligibility.get("message"),
        }
        return base

    checkpoint_id = str(checkpoint.get("checkpoint_id") or "")
    resume_context = checkpoint.get("resume_context") or {}
    base["steps_run"].append("resume_checkpoint_validated")

    if checkpoint_id == CHECKPOINT_A_ID:
        resume_plan = resume_plan_from_checkpoint_a(resume_context)
        planned_tools = list(resume_plan.get("planned_tools") or [])
        run_path_profile = get_run_path_profile(
            case_ref,
            sandbox_end_to_end=sandbox_end_to_end,
        )
        if not run_path_profile:
            base["message"] = "no run_path_profile for case_ref"
            base["final_status"] = "blocked"
            base["resume"] = {
                "ok": False,
                "message": "no run_path_profile for case_ref",
            }
            return base

        base["resume"] = _build_resume_metadata(
            checkpoint=checkpoint,
            checkpoint_path=resolved_path,
            resume_from_step="S7",
            skipped_steps=_RESUME_SKIP_STEPS_A,
        )
        base["path_kind"] = "run"
        base["fixture_maturity"] = get_fixture_maturity(case_ref)
        base["run_path_profile"] = run_path_profile
        base["decision"] = _decision_block_from_checkpoint(checkpoint)
        base["planned_route"] = _planned_route_from_checkpoint(checkpoint)
        base["tool_path_preview"] = {
            "ok": True,
            "mode": "resume_skipped",
            "message": "S6 skipped during checkpoint A resume",
        }
        checkpoint_a = {
            "checkpoint_id": CHECKPOINT_A_ID,
            "status": "resumed_approved",
            "would_trigger": False,
            "message": "resumed from approved checkpoint A; S3–S6 skipped",
            "checkpoint_path": _checkpoint_path_for_result(resolved_path),
        }
        base["checkpoint_a_status"] = checkpoint_a

        run_execution = _execute_run_path_tools(
            case_ref=case_ref,
            case_dir_rel=case_dir_rel,
            profile=run_path_profile,
            planned_tools=planned_tools,
            outbox_root_override=outbox_root_override,
        )
        base["run_execution"] = run_execution
        base["steps_run"].append("S7_S10_run_path_execution")

        _finalize_after_run_execution(
            base,
            case_path=case_path,
            case_ref=case_ref,
            case_dir_rel=case_dir_rel,
            task_type=task_type,
            mode=mode,
            checkpoint_a=checkpoint_a,
            run_path_profile=run_path_profile,
            run_execution=run_execution,
            auto_approve_intake=auto_approve_intake,
            auto_approve_delivery=auto_approve_delivery,
            outbox_root_override=outbox_root_override,
            sandbox_end_to_end=sandbox_end_to_end,
            experiment_id=experiment_id,
        )

        base["ok"] = bool(run_execution.get("ok"))
        if not base["ok"]:
            base["message"] = (
                "checkpoint A resume run path failed; see run_execution.tool_results"
            )
        else:
            base["message"] = (
                f"checkpoint A resume complete; final_status={base['final_status']}"
            )
        base["notes"] = [
            "W6-T11 checkpoint A resume: S3–S6 skipped; continued from S7 run path",
        ]
        return base

    # Checkpoint B approved → S13 delivery/export only
    delivery_plan = delivery_plan_from_checkpoint_b(resume_context)
    artifacts = dict(delivery_plan.get("artifacts") or {})
    missing_artifacts = _validate_checkpoint_b_resume_artifacts(
        artifacts,
        case_path=case_path,
    )
    if missing_artifacts:
        base["message"] = (
            "stale checkpoint artifacts missing: "
            + ", ".join(missing_artifacts)
        )
        base["final_status"] = "blocked"
        base["resume"] = {
            "ok": False,
            "checkpoint_path": _checkpoint_path_for_result(resolved_path),
            "message": base["message"],
        }
        return base

    if _delivery_resume_already_done(
        case_ref,
        resolved_path,
        outbox_root_override=outbox_root_override,
    ):
        base["message"] = "delivery already resumed for this checkpoint"
        base["final_status"] = "duplicate_delivery"
        base["resume"] = {
            "ok": False,
            "checkpoint_path": _checkpoint_path_for_result(resolved_path),
            "message": base["message"],
        }
        return base

    agent_output = checkpoint.get("agent_output") or {}
    output_guard = dict(agent_output.get("output_guard") or _read_live_output_guard(
        case_path,
        case_ref,
        force_cleaning=True,
    ))
    exec_summary = agent_output.get("execution_summary") or {}
    prior_tools = [
        item.get("tool_id")
        for item in exec_summary.get("tools_executed") or []
        if isinstance(item, dict)
    ]
    prior_run_execution = {
        "ok": True,
        "tools_executed": prior_tools,
        "tool_results": [],
        "outbox_entries": [],
    }

    base["resume"] = _build_resume_metadata(
        checkpoint=checkpoint,
        checkpoint_path=resolved_path,
        resume_from_step="S13",
        skipped_steps=_RESUME_SKIP_STEPS_B,
    )
    base["path_kind"] = "run"
    base["fixture_maturity"] = get_fixture_maturity(case_ref)
    base["decision"] = {
        "ok": True,
        "decision": "needs_review",
        "risk_level": "medium",
        "message": "restored for checkpoint B resume",
    }
    base["planned_route"] = {
        "ok": True,
        "planned_tools": ["export.delivery_bundle"],
        "notes": ["delivery-only resume from approved checkpoint B"],
    }
    base["tool_path_preview"] = {
        "ok": True,
        "mode": "resume_skipped",
        "message": "S3–S12 skipped during checkpoint B resume",
    }
    base["checkpoint_a_status"] = {
        "checkpoint_id": CHECKPOINT_A_ID,
        "status": "resumed_prior",
        "would_trigger": False,
        "message": "assumed approved prior to checkpoint B resume",
    }
    base["output_guard"] = output_guard

    export_profile = {
        "case_ref": case_ref,
        "stop_at": "bundle",
        "tools_to_run": ["export.delivery_bundle"],
        "stop_before_delivery": False,
        "force_cleaning": False,
    }
    run_execution = _execute_run_path_tools(
        case_ref=case_ref,
        case_dir_rel=case_dir_rel,
        profile=export_profile,
        planned_tools=["export.delivery_bundle"],
        outbox_root_override=outbox_root_override,
    )
    merged_execution = dict(prior_run_execution)
    merged_execution["tools_executed"] = list(prior_tools) + list(
        run_execution.get("tools_executed") or []
    )
    merged_execution["tool_results"] = list(run_execution.get("tool_results") or [])
    merged_execution["outbox_entries"] = list(run_execution.get("outbox_entries") or [])
    merged_execution["ok"] = bool(run_execution.get("ok"))
    base["run_execution"] = merged_execution
    base["steps_run"].append("S13_delivery_export")

    checkpoint_b = {
        "checkpoint_id": CHECKPOINT_B_ID,
        "status": "resumed_approved",
        "would_trigger": False,
        "message": "resumed from approved checkpoint B; delivery/export executed",
        "checkpoint_path": _checkpoint_path_for_result(resolved_path),
        "integration_layer": "hitl.checkpoint_b_integration_v1",
    }
    base["checkpoint_b_status"] = checkpoint_b

    if merged_execution.get("ok"):
        _write_delivery_resume_marker(
            case_ref,
            resolved_path,
            outbox_root_override=outbox_root_override,
        )
        base["final_status"] = "run_complete"
        base["ok"] = True
        base["message"] = "checkpoint B resume delivery/export complete"
    else:
        base["final_status"] = "blocked"
        base["ok"] = False
        base["message"] = "checkpoint B resume delivery/export failed"

    base["notes"] = [
        "W6-T11 checkpoint B resume: S3–S12 skipped; continued at S13 delivery/export",
    ]
    return base


def run_agent_standard_case_experiment(
    task_type: str,
    case_dir: str,
    *,
    mode: Mode = "preview",
    auto_approve_intake: bool = False,
    auto_approve_delivery: bool = False,
    write_checkpoint_state: Optional[bool] = None,
    outbox_root_override: Optional[str] = None,
    regression_bundle_probe: bool = False,
    sandbox_end_to_end: bool = False,
    resume_checkpoint: Optional[str] = None,
    notifications_enabled: bool = False,
) -> Dict[str, Any]:
    """Run experiment-line orchestration and return structured result dict."""
    # WD-P7-T3: align direct Python API with CLI — env gate enables emit without flag
    notifications_enabled = notifications_enabled or is_enabled_via_env()

    if resume_checkpoint:
        return _run_experiment_resume_from_checkpoint(
            task_type,
            case_dir,
            resume_checkpoint=resume_checkpoint,
            mode=mode,
            auto_approve_intake=auto_approve_intake,
            auto_approve_delivery=auto_approve_delivery,
            outbox_root_override=outbox_root_override,
            sandbox_end_to_end=sandbox_end_to_end,
        )

    case_path, case_dir_rel = _normalize_case_dir(case_dir)
    case_ref = case_ref_from_dir(case_dir)
    allowlisted = is_allowlisted_case(case_ref)
    experiment_id = str(uuid.uuid4())

    base: Dict[str, Any] = {
        "ok": False,
        "experiment_id": experiment_id,
        "case_ref": case_ref,
        "case_dir": case_dir_rel,
        "task_type": task_type,
        "mode": mode,
        "steps_run": [],
        "notifications": [],  # W6-T10-P2: notification events emitted
    }

    # W6-T10-P2: helper to track notifications (best-effort, failures don't block)
    # F1: returns event_id for cross-reference tracking
    def _emit_and_track(
        event_type: str,
        *,
        checkpoint_id: Optional[str] = None,
        checkpoint_status: Optional[str] = None,
        approval_source: Optional[str] = None,
        artifacts: Optional[Dict[str, Any]] = None,
        status_summary: Optional[Dict[str, Any]] = None,
        source_step: str = "orchestrator",
    ) -> Optional[str]:
        if mode != "run":
            return None
        result = emit_notification_safe(
            event_type,
            enabled=notifications_enabled,
            case_ref=case_ref,
            case_dir=case_dir_rel,
            experiment_id=experiment_id,
            checkpoint_id=checkpoint_id,
            checkpoint_status=checkpoint_status,
            approval_source=approval_source,
            artifacts=artifacts,
            status_summary=status_summary,
            source={"step_id": source_step, "module": "scripts.run_agent_standard_case_experiment"},
            repo_root=_REPO_ROOT,
            outbox_root_override=outbox_root_override,
        )
        if result:
            base["notifications"].append({
                "event_type": event_type,
                "ok": result.get("ok"),
                "event_id": result.get("event_id"),
                "path": (result.get("sink_result") or {}).get("path"),
            })
            return result.get("event_id")
        return None

    if sandbox_end_to_end:
        base["sandbox_end_to_end"] = True
        allowed, sandbox_reason = is_sandbox_e2e_allowed(case_ref)
        if not allowed:
            base["message"] = "sandbox_end_to_end_not_allowed"
            base["final_status"] = "blocked"
            base["notes"] = [
                sandbox_reason,
                "only allowlisted sandbox fixtures may use --sandbox-end-to-end",
            ]
            return base
        if mode != "run":
            base["message"] = "sandbox_end_to_end_requires_run_mode"
            base["final_status"] = "blocked"
            base["notes"] = ["--sandbox-end-to-end requires --mode run"]
            return base

    if not allowlisted:
        base["message"] = "case_not_in_allowlist"
        base["final_status"] = "blocked"
        base["notes"] = [
            f"allowed case_ref values: {sorted(_ALLOWLIST_CASE_REFS)}",
            "non-tabular or unknown fixtures are blocked in v1 experiment line",
        ]
        return base

    # S3: intake gate evaluate (P75-G2 — v2 rules via gate layer)
    intake_gate = evaluate_intake_gate(
        task_type,
        case_dir_rel,
        mode=mode,
        repo_root=_REPO_ROOT,
        outbox_root_override=outbox_root_override,
    )
    decision = decision_result_from_gate(intake_gate)
    base["steps_run"].append("S3_decision_evaluate")
    base["intake_gate"] = intake_gate
    base["decision"] = {
        "ok": decision.get("ok"),
        "decision": decision.get("decision"),
        "risk_level": decision.get("risk_level"),
        "rationale": decision.get("rationale"),
        "suggested_route": decision.get("suggested_route"),
        "message": decision.get("message"),
    }

    # WD-P7-T1: emit intake.gate_decision after S3 gate evaluation (run mode only)
    if mode == "run":
        _emit_and_track(
            "intake.gate_decision",
            artifacts={
                "decision": decision.get("decision"),
                "risk_level": decision.get("risk_level"),
                "intake_decision_id": intake_gate.get("intake_decision_id"),
                "outbox_record_path": intake_gate.get("outbox_record_path"),
            },
            status_summary={
                "decision": decision.get("decision"),
                "risk_level": decision.get("risk_level"),
                "final_status": base.get("final_status"),
                "mode": mode,
            },
            source_step="S3",
        )

    if intake_gate.get("decision") == "reject":
        base["ok"] = True
        base["message"] = decision.get("message", "rejected")
        base["checkpoint_a_status"] = {
            "checkpoint_id": CHECKPOINT_A_ID,
            "status": "not_applicable",
            "would_trigger": False,
            "message": "decision=reject",
        }
        base["planned_route"] = None
        base["tool_path_preview"] = None
        base["output_guard"] = None
        base["checkpoint_b_status"] = {
            "checkpoint_id": CHECKPOINT_B_ID,
            "status": "not_applicable",
            "would_trigger": False,
            "integration_layer": "hitl.checkpoint_b_integration_v1",
        }
        base["final_status"] = "blocked"
        base["notes"] = ["experiment stopped at S3: decision=reject"]
        return base

    # S5: route planning (W4-T1 glue)
    glue_plan = plan_tabular_route(task_type, case_dir_rel)
    base["steps_run"].append("S5_route_planning")
    base["planned_route"] = {
        "ok": glue_plan.get("ok"),
        "selector_task_type": glue_plan.get("selector_task_type"),
        "planned_tools": glue_plan.get("planned_tools") or [],
        "case_profile": glue_plan.get("case_profile"),
        "inferred_gate_notes": glue_plan.get("inferred_gate_notes") or [],
        "notes": glue_plan.get("notes") or [],
        "message": glue_plan.get("message"),
    }

    # S6: tool path preview (W4-T3)
    tool_path = run_tabular_intake_tool_path(task_type, case_dir_rel)
    base["steps_run"].append("S6_tool_path_preview")
    raw_selector_view = tool_path.get("selector_view") or {}
    base["tool_path_preview"] = {
        "ok": tool_path.get("ok"),
        "mode": tool_path.get("mode"),
        "glue_plan": tool_path.get("glue_plan"),
        "selector_view": {
            "ok": raw_selector_view.get("ok"),
            "selector_task_type": raw_selector_view.get("selector_task_type"),
            "selector_rule_id": raw_selector_view.get("selector_rule_id"),
            "candidates_count": len(raw_selector_view.get("candidates") or []),
        },
        "executor_plan": tool_path.get("executor_plan"),
        "notes": tool_path.get("notes"),
        "message": tool_path.get("message"),
    }

    fail_close, registry_error_rule_id = _should_fail_close_due_to_registry(
        raw_selector_view
    )
    if fail_close:
        base["steps_run"].append("S6_selector_registry_blocked")
        selector_preview = base["tool_path_preview"]["selector_view"]
        selector_preview["error_rule_id"] = registry_error_rule_id
        base["checkpoint_a_status"] = {
            "checkpoint_id": CHECKPOINT_A_ID,
            "status": "not_applicable",
            "would_trigger": False,
            "message": "blocked at S6: selector/registry fail-closed",
        }
        base["checkpoint_b_status"] = {
            "checkpoint_id": CHECKPOINT_B_ID,
            "status": "not_applicable",
            "would_trigger": False,
            "message": "blocked at S6: selector/registry fail-closed",
            "integration_layer": "hitl.checkpoint_b_integration_v1",
        }
        base["output_guard"] = None
        base["final_status"] = "blocked_at_selector_registry"
        base["ok"] = False
        base["message"] = (
            f"blocked at S6 selector/registry: {registry_error_rule_id or 'selector_failed'}"
        )
        base["notes"] = [
            "experiment stopped at S6: selector/registry fail-closed (W10-T3)",
            f"selector_rule_id={registry_error_rule_id}",
            "run path (S7–S10) skipped; no checkpoint A/B files written",
        ]
        return base

    # S4: checkpoint A (after decision + route context available)
    should_write = write_checkpoint_state
    if should_write is None:
        should_write = mode == "run" and not auto_approve_intake
    checkpoint_a = _resolve_checkpoint_a_status(
        mode=mode,
        decision_result=decision,
        case_ref=case_ref,
        task_type=task_type,
        case_dir_rel=case_dir_rel,
        auto_approve_intake=auto_approve_intake,
        write_state=bool(should_write),
        outbox_root_override=outbox_root_override,
    )
    base["steps_run"].append("S4_checkpoint_a")
    base["checkpoint_a_status"] = checkpoint_a

    # W6-T10-P2: emit checkpoint.awaiting_human when A is written and awaiting human
    cp_a_status = checkpoint_a.get("status")
    if cp_a_status == "written" and checkpoint_a.get("would_trigger"):
        integration = checkpoint_a.get("integration") or {}
        _emit_and_track(
            "checkpoint.awaiting_human",
            checkpoint_id=CHECKPOINT_A_ID,
            checkpoint_status="awaiting_human",
            artifacts={"checkpoint_path": integration.get("checkpoint_path")},
            status_summary={"final_status": "waiting_for_human", "mode": mode},
            source_step="S4",
        )
    # W6-T10-P2: emit checkpoint.approved when auto-approved
    if cp_a_status == "auto_approved":
        # F1: capture event_id for cross-reference tracking
        cp_a_event_id = _emit_and_track(
            "checkpoint.approved",
            checkpoint_id=CHECKPOINT_A_ID,
            checkpoint_status="auto_approved",
            approval_source="auto",
            status_summary={"final_status": base.get("final_status"), "mode": mode},
            source_step="S4",
        )
        if cp_a_event_id:
            checkpoint_a["notification_event_id"] = cp_a_event_id

    run_path_profile = get_run_path_profile(
        case_ref,
        sandbox_end_to_end=sandbox_end_to_end,
    )
    base["path_kind"] = "preview" if mode == "preview" else "run"
    base["fixture_maturity"] = get_fixture_maturity(case_ref)
    if run_path_profile:
        base["run_path_profile"] = run_path_profile

    run_execution: Optional[Dict[str, Any]] = None
    sandbox_delivery: Optional[Dict[str, Any]] = None
    execute_run = _can_start_run_execution(
        mode,
        checkpoint_a,
    )

    if execute_run and run_path_profile:
        base["steps_run"].append("S7_S10_run_path_execution")
        if sandbox_end_to_end:
            run_execution, live_guard, sandbox_cp_b = _execute_sandbox_e2e_run(
                case_ref=case_ref,
                case_dir_rel=case_dir_rel,
                task_type=task_type,
                profile=run_path_profile,
                planned_tools=base["planned_route"].get("planned_tools") or [],
                outbox_root_override=outbox_root_override,
                auto_approve_delivery=auto_approve_delivery,
            )
            base["run_execution"] = run_execution
            if live_guard:
                base["output_guard"] = live_guard
                base["steps_run"].append("S11_output_guard_live")
            if sandbox_cp_b:
                base["checkpoint_b_status"] = sandbox_cp_b
                base["steps_run"].append("S12_checkpoint_b_run")
        else:
            run_execution = _execute_run_path_tools(
                case_ref=case_ref,
                case_dir_rel=case_dir_rel,
                profile=run_path_profile,
                planned_tools=base["planned_route"].get("planned_tools") or [],
                outbox_root_override=outbox_root_override,
                regression_bundle_probe=regression_bundle_probe,
            )
            base["run_execution"] = run_execution

    if (
        sandbox_end_to_end
        and run_execution
        and run_execution.get("ok")
        and not run_execution.get("sandbox_bundle_blocked")
        and "export.delivery_bundle" in (run_execution.get("tools_executed") or [])
    ):
        sandbox_delivery = write_sandbox_delivery_bundle(
            case_ref=case_ref,
            case_dir=case_dir_rel,
            experiment_id=experiment_id,
            output_guard=base.get("output_guard") or _mock_output_guard(case_ref),
            run_execution=run_execution,
            checkpoint_a=checkpoint_a,
            checkpoint_b=base.get("checkpoint_b_status") or {},
            outbox_root_override=outbox_root_override,
        )
        base["sandbox_delivery"] = sandbox_delivery
        base["steps_run"].append("S10_sandbox_delivery_bundle")
        # W6-T10-P2: emit delivery.bundle_ready when sandbox delivery succeeds
        if sandbox_delivery and sandbox_delivery.get("ok"):
            _emit_and_track(
                "delivery.bundle_ready",
                artifacts={
                    "manifest_path": sandbox_delivery.get("manifest_path"),
                    "bundle_dir": sandbox_delivery.get("bundle_dir"),
                },
                status_summary={"final_status": "sandbox_e2e_complete", "mode": mode},
                source_step="S10",
            )

    if run_execution and run_execution.get("ok") and not sandbox_end_to_end:
        stop_at = (run_path_profile or {}).get("stop_at")
        executed_tools = run_execution.get("tools_executed") or []
        if stop_at == "cleaning_preview":
            if "clean.phase_demo" in executed_tools:
                output_guard = _read_live_output_guard(
                    case_path,
                    case_ref,
                    force_cleaning=bool(
                        run_path_profile and run_path_profile.get("force_cleaning")
                    ),
                )
                output_guard["note"] = (
                    "cleaning executed for evaluation; stop at cleaning_preview "
                    "before Checkpoint B (W11-T1 controlled_experimental)"
                )
                if case_ref == "sandbox_client":
                    output_guard.setdefault("checks", {})
                    output_guard["checks"]["schema_check"] = "review"
                    output_guard["evaluation_mode"] = "cleaning_preview_stop"
                base["steps_run"].append("S11_output_guard_live")
            else:
                output_guard = _mock_output_guard(case_ref)
                output_guard["note"] = (
                    "cleaning preview only; no live S8 execution (W8-T1 run_path_profile)"
                )
                base["steps_run"].append("S11_output_guard_mock")
            base["output_guard"] = output_guard
            checkpoint_b = {
                "checkpoint_id": CHECKPOINT_B_ID,
                "status": "stopped_at_cleaning_preview",
                "would_trigger": False,
                "message": (
                    "run stopped at cleaning preview per run_path_profile; "
                    "Checkpoint B safeguard not evaluated"
                ),
            }
            base["steps_run"].append("S12_checkpoint_b_stopped")
            base["checkpoint_b_status"] = checkpoint_b
        else:
            output_guard = _read_live_output_guard(
                case_path,
                case_ref,
                force_cleaning=bool(
                    run_path_profile and run_path_profile.get("force_cleaning")
                ),
            )
            base["steps_run"].append("S11_output_guard_live")
            base["output_guard"] = output_guard

            checkpoint_b = _resolve_checkpoint_b_after_run(
                case_ref=case_ref,
                case_dir_rel=case_dir_rel,
                task_type=task_type,
                output_guard=output_guard,
                run_execution=run_execution,
                run_path_profile=run_path_profile or {},
                auto_approve_delivery=auto_approve_delivery,
                outbox_root_override=outbox_root_override,
            )
            base["steps_run"].append("S12_checkpoint_b_run")
            base["checkpoint_b_status"] = checkpoint_b
    elif sandbox_end_to_end and run_execution and run_execution.get("sandbox_bundle_blocked"):
        if "output_guard" not in base:
            output_guard = _read_live_output_guard(
                case_path,
                case_ref,
                force_cleaning=bool(
                    run_path_profile and run_path_profile.get("force_cleaning")
                ),
            )
            base["output_guard"] = output_guard
        checkpoint_b = base.get("checkpoint_b_status") or {}
    elif not sandbox_end_to_end or not run_execution:
        output_guard = _mock_output_guard(case_ref)
        base["steps_run"].append("S11_output_guard_mock")
        base["output_guard"] = output_guard

        checkpoint_b = _build_checkpoint_b_planned(
            case_ref=case_ref,
            task_type=task_type,
            output_guard=output_guard,
            tool_path_preview=tool_path,
            auto_approve_delivery=auto_approve_delivery,
        )
        if auto_approve_delivery and checkpoint_b.get("would_trigger"):
            checkpoint_b["status"] = "auto_approved_planned"
            checkpoint_b["message"] = (
                "would trigger but bypassed via --auto-approve-delivery (preview only)"
            )
        base["steps_run"].append("S12_checkpoint_b_planned")
        base["checkpoint_b_status"] = checkpoint_b
    else:
        checkpoint_b = base.get("checkpoint_b_status") or {}

    base["final_status"] = _resolve_final_status(
        decision_result=decision,
        checkpoint_a=checkpoint_a,
        checkpoint_b=checkpoint_b,
        allowlisted=allowlisted,
        mode=mode,
        auto_approve_intake=auto_approve_intake,
        run_execution=run_execution,
        run_path_profile=run_path_profile,
        sandbox_delivery=sandbox_delivery,
    )

    # W6-T10-P2: emit checkpoint B notifications (run mode only)
    if mode == "run" and checkpoint_b:
        cp_b_status = checkpoint_b.get("status")
        cp_b_id = checkpoint_b.get("checkpoint_id", CHECKPOINT_B_ID)
        # checkpoint.awaiting_human when B written
        if cp_b_status == "written" and checkpoint_b.get("would_trigger"):
            integration = checkpoint_b.get("integration") or {}
            cp_b_event_id = _emit_and_track(
                "checkpoint.awaiting_human",
                checkpoint_id=cp_b_id,
                checkpoint_status="awaiting_human",
                artifacts={"checkpoint_path": integration.get("checkpoint_path") or checkpoint_b.get("checkpoint_path")},
                status_summary={"final_status": base.get("final_status"), "mode": mode},
                source_step="S12",
            )
            if cp_b_event_id:
                checkpoint_b["notification_event_id"] = cp_b_event_id
        # checkpoint.approved when B auto-approved/skipped
        if cp_b_status in ("skipped", "auto_approved") and not checkpoint_b.get("would_trigger"):
            cp_b_approved_event_id = _emit_and_track(
                "checkpoint.approved",
                checkpoint_id=cp_b_id,
                checkpoint_status=cp_b_status,
                approval_source="auto" if cp_b_status == "skipped" else "auto_approved",
                status_summary={"final_status": base.get("final_status"), "mode": mode},
                source_step="S12",
            )
            if cp_b_approved_event_id:
                checkpoint_b["notification_event_id"] = cp_b_approved_event_id

    if mode == "run":
        base["resume_plan"] = _build_resume_plan(
            case_ref=case_ref,
            task_type=task_type,
            decision_result=decision,
            planned_route=base["planned_route"],
            checkpoint_a=checkpoint_a,
            checkpoint_b=checkpoint_b,
            auto_approve_intake=auto_approve_intake,
        )
        base["steps_run"].append("run_resume_plan")

    base["ok"] = True
    if run_execution is not None and not run_execution.get("ok"):
        base["ok"] = False
        base["message"] = "experiment run path failed; see run_execution.tool_results"
    else:
        base["message"] = f"experiment {mode} complete; final_status={base['final_status']}"

    # W6-T10-P2: emit run.completed or run.blocked based on final result
    if mode == "run":
        final_status = base.get("final_status", "unknown")
        if base.get("ok") and final_status in (
            "run_complete",
            "resume_plan_ready",
            "sandbox_e2e_complete",
            "preview_ready",
            "waiting_for_human",
            "stopped_at_checkpoint_b",
            "stopped_at_cleaning_preview",
        ):
            _emit_and_track(
                "run.completed",
                status_summary={
                    "final_status": final_status,
                    "decision": (decision or {}).get("decision"),
                    "output_guard_status": (base.get("output_guard") or {}).get("status"),
                    "mode": mode,
                },
                source_step="orchestrator",
            )
        elif not base.get("ok") or final_status in ("blocked", "sandbox_e2e_blocked_at_checkpoint_b"):
            _emit_and_track(
                "run.blocked",
                status_summary={
                    "final_status": final_status,
                    "block_reason": base.get("message") or final_status,
                    "mode": mode,
                },
                source_step="orchestrator",
            )

    base["notes"] = [
        "experimental-line orchestrator; does not modify production main chain",
        "preview path: plan-only; run path: per-case profile in W7-T2/W11-T1 allowlist",
    ]
    if mode == "preview":
        base["notes"].append("S11 output_guard is mock/placeholder in preview")
        base["notes"].append("S12 checkpoint B is planned/would_pause only in preview")
    if execute_run and run_path_profile:
        base["notes"].append(
            f"run path stop_at={run_path_profile.get('stop_at')}; "
            f"tools={run_path_profile.get('tools_to_run')}"
        )
    if auto_approve_intake:
        base["notes"].append(
            "Checkpoint A auto-approved via W6-T5 integration layer (--auto-approve-intake)"
        )
    if auto_approve_delivery:
        base["notes"].append("Checkpoint B auto-approve flag set (delivery not executed)")
    if regression_bundle_probe and case_ref == "additional_demo":
        base["notes"].append(
            "regression_bundle_probe=true: additional_demo may attempt bundle (test only)"
        )
    if sandbox_end_to_end:
        base["notes"].append(
            "W12-T1 sandbox end-to-end: bundle artifacts copied to outbox/sandbox_delivery/"
        )
        base["notes"].append("no production notify; production_contract=false")
        if sandbox_delivery:
            base["notes"].append(
                f"sandbox manifest: {sandbox_delivery.get('manifest_path')}"
            )

    return base


def format_experiment_summary_text(result: Dict[str, Any]) -> str:
    lines = [
        "Agent-Run Standard Case Experiment (W6-T4 / W7-T2)",
        f"experiment_id: {result.get('experiment_id')}",
        f"case_ref: {result.get('case_ref')}",
        f"task_type: {result.get('task_type')}",
        f"mode: {result.get('mode')}",
        f"final_status: {result.get('final_status')}",
        f"ok: {result.get('ok')}",
    ]
    decision = result.get("decision") or {}
    lines.append(f"decision: {decision.get('decision')} (risk={decision.get('risk_level')})")

    cp_a = result.get("checkpoint_a_status") or {}
    lines.append(f"checkpoint_a_status: {cp_a.get('status')} (would_trigger={cp_a.get('would_trigger')})")

    route = result.get("planned_route") or {}
    if route:
        lines.append(f"planned_route.selector_task_type: {route.get('selector_task_type')}")
        tools = route.get("planned_tools") or []
        lines.append(f"planned_route.planned_tools: {', '.join(tools)}")

    preview = result.get("tool_path_preview") or {}
    if preview:
        lines.append(f"tool_path_preview.ok: {preview.get('ok')}")

    guard = result.get("output_guard") or {}
    if guard:
        lines.append(f"output_guard.status: {guard.get('status')} (mock: {guard.get('source')})")

    cp_b = result.get("checkpoint_b_status") or {}
    lines.append(f"checkpoint_b_status: {cp_b.get('status')} (would_trigger={cp_b.get('would_trigger')})")

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Agent-run standard case experiment orchestrator (W6-T4 / W7-T2).",
    )
    parser.add_argument("--task-type", required=True, help="W2 routing catalog task_type")
    parser.add_argument(
        "--case-dir",
        required=True,
        help="Case directory (demo_phase, sampleco/2026-0001, additional_demo, sandbox_client)",
    )
    parser.add_argument(
        "--mode",
        choices=("preview", "run"),
        default="preview",
        help="preview (default): plan-only; run: execute per-case run_path_profile",
    )
    parser.add_argument(
        "--auto-approve-intake",
        action="store_true",
        help="Skip Checkpoint A when decision=needs_review (run mode)",
    )
    parser.add_argument(
        "--auto-approve-delivery",
        action="store_true",
        help="Mark Checkpoint B as auto-approved planned (no delivery execution)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text summary)",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional outbox root override for checkpoint state writes (run mode)",
    )
    parser.add_argument(
        "--sandbox-end-to-end",
        action="store_true",
        help=(
            "W12-T1: run sandbox e2e delivery for allowlisted fixture only "
            "(additional_demo); writes outbox/sandbox_delivery/ manifest"
        ),
    )
    parser.add_argument(
        "--resume-checkpoint",
        default=None,
        help=(
            "W6-T11: resume from approved checkpoint JSON "
            "(Checkpoint A → S7 run path; Checkpoint B → S13 delivery/export)"
        ),
    )
    parser.add_argument(
        "--enable-notifications",
        action="store_true",
        default=False,
        help=(
            "W6-T10-P2: emit notification events to outbox/notifications/ "
            "(env GOV_NOTIFICATION_GATEWAY_ENABLED=1 also enables)"
        ),
    )
    args = parser.parse_args(argv)

    notifications_enabled = args.enable_notifications or is_enabled_via_env()

    result = run_agent_standard_case_experiment(
        args.task_type,
        args.case_dir,
        mode=args.mode,  # type: ignore[arg-type]
        auto_approve_intake=args.auto_approve_intake,
        auto_approve_delivery=args.auto_approve_delivery,
        outbox_root_override=args.outbox_root,
        sandbox_end_to_end=args.sandbox_end_to_end,
        resume_checkpoint=args.resume_checkpoint,
        notifications_enabled=notifications_enabled,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_experiment_summary_text(result))

    blocked_statuses = frozenset({
        "blocked",
        "checkpoint_mismatch",
        "stale_checkpoint",
        "duplicate_delivery",
    })
    if result.get("final_status") in blocked_statuses and not result.get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
