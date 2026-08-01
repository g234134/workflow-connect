#!/usr/bin/env python3
"""Agent-run standard case experiment regression hook v1 (W6-T8 / W7-T2 / W8-T1 / W11-T1).

Lightweight one-command regression for demo_phase + sampleco experiment line.
Independent from MVP mainline regression (run_mvp_mainline_regression.py).

Usage:
    python scripts/run_agent_standard_case_regression.py
    python scripts/run_agent_standard_case_regression.py --format json
    python scripts/run_agent_standard_case_regression.py --run-mode run --auto-approve-intake
    python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --auto-approve-intake
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_EXPERIMENT_SCRIPT = _REPO_ROOT / "scripts" / "run_agent_standard_case_experiment.py"
_TASK_TYPE = "tabular.cleaning.mvp"

_DEFAULT_CASES: List[Dict[str, str]] = [
    {"case_dir": "cases/demo_phase", "case_ref": "demo_phase"},
    {"case_dir": "cases/sampleco/2026-0001", "case_ref": "sampleco/2026-0001"},
]

_EXTENDED_CASES: List[Dict[str, str]] = [
    {"case_dir": "cases/additional_demo", "case_ref": "additional_demo"},
    {"case_dir": "cases/sandbox_client", "case_ref": "sandbox_client"},
]

# W4-GUARD-01: Experimental fixture maturity labels for guard enforcement
_EXPERIMENTAL_CASE_REFS = frozenset({"additional_demo", "sandbox_client"})
_EXPERIMENTAL_MATURITY_LABELS = frozenset({"experimental", "controlled_experimental"})

RunMode = Literal["preview", "run", "run-all-allowed"]


def _load_experiment_runner():
    spec = importlib.util.spec_from_file_location(
        "run_agent_standard_case_experiment", _EXPERIMENT_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load experiment script: {_EXPERIMENT_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_experiment_mod = _load_experiment_runner()
run_agent_standard_case_experiment = _experiment_mod.run_agent_standard_case_experiment
get_run_path_profile = _experiment_mod.get_run_path_profile
get_fixture_maturity = _experiment_mod.get_fixture_maturity
is_experimental_fixture = _experiment_mod.is_experimental_fixture
is_controlled_experimental_fixture = _experiment_mod.is_controlled_experimental_fixture

# W11-T1: lightweight removal_ratio bounds for extended fixture sanity checks.
_REMOVAL_RATIO_BOUNDS: Dict[str, tuple[float, float]] = {
    "demo_phase": (0.0, 0.5),
    "sampleco/2026-0001": (0.0, 1.0),
    "additional_demo": (0.0, 0.6),
    "sandbox_client": (0.0, 0.6),
}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def enforce_fixture_guard(
    case_ref: str,
    maturity: str,
    *,
    include_extended_fixtures: bool,
    explicit_flags: Dict[str, bool],
) -> Dict[str, Any]:
    """W4-GUARD-01: Prevent experimental fixtures from silently entering mainline.

    Returns a guard result dict with ok=True if allowed, ok=False if blocked.
    Experimental fixtures (additional_demo, sandbox_client) require either:
      - --include-extended-fixtures flag (for regression), OR
      - maturity-appropriate explicit flag in explicit_flags
    """
    is_experimental = (
        case_ref in _EXPERIMENTAL_CASE_REFS
        or maturity in _EXPERIMENTAL_MATURITY_LABELS
    )
    if not is_experimental:
        return {
            "ok": True,
            "action": "allow",
            "reason": "stable_fixture",
            "case_ref": case_ref,
            "maturity": maturity,
        }

    # Experimental fixture detected
    if include_extended_fixtures:
        return {
            "ok": True,
            "action": "allow",
            "reason": "explicit_include_extended_fixtures",
            "case_ref": case_ref,
            "maturity": maturity,
        }

    # Check explicit maturity flag (e.g., --sandbox-end-to-end)
    if explicit_flags.get("sandbox_end_to_end") and case_ref == "additional_demo":
        return {
            "ok": True,
            "action": "allow",
            "reason": "explicit_sandbox_end_to_end",
            "case_ref": case_ref,
            "maturity": maturity,
        }

    # BLOCK: Experimental fixture without explicit flag
    return {
        "ok": False,
        "action": "block",
        "reason": "experimental_fixture_requires_explicit_flag",
        "case_ref": case_ref,
        "maturity": maturity,
        "required_flags": ["--include-extended-fixtures"],
        "message": (
            f"Guard blocked: case_ref='{case_ref}' maturity='{maturity}' "
            f"is experimental and requires explicit opt-in. "
            f"Use --include-extended-fixtures to enable."
        ),
    }


def case_ref_to_filename_slug(case_ref: str) -> str:
    """Sanitize case_ref for artifact filenames (e.g. sampleco/2026-0001 → sampleco_2026-0001)."""
    return case_ref.replace("/", "_").replace("\\", "_")


def default_regression_outbox_root(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / "outbox" / "agent_experiment_regression"


def regression_artifact_path(
    *,
    outbox_root: Path,
    timestamp: str,
    case_ref: str,
) -> Path:
    slug = case_ref_to_filename_slug(case_ref)
    return outbox_root / f"{timestamp}_{slug}.json"


def _resolve_case_mode(case_ref: str, run_mode: RunMode) -> RunMode:
    """Map regression run_mode to per-case orchestrator mode (W7-T2 / W8-T1 profiles)."""
    if run_mode == "run-all-allowed":
        if get_run_path_profile(case_ref):
            return "run"
        return "preview"
    if run_mode == "run" and case_ref == "demo_phase":
        return "run"
    return "preview"


def _check_guard_sanity(
    case_ref: Optional[str],
    experiment: Dict[str, Any],
) -> Dict[str, Any]:
    """Lightweight sanity check on output_guard.removal_ratio (W11-T1)."""
    guard = experiment.get("output_guard") or {}
    ratio = guard.get("removal_ratio")
    bounds = _REMOVAL_RATIO_BOUNDS.get(str(case_ref or ""))
    notes: List[str] = []
    ok = True
    if ratio is None:
        pass
    elif not isinstance(ratio, (int, float)):
        ok = False
        notes.append(f"removal_ratio not numeric: {ratio!r}")
    elif bounds is not None:
        lo, hi = bounds
        if ratio < lo or ratio > hi:
            ok = False
            notes.append(f"removal_ratio {ratio} outside [{lo}, {hi}]")
    return {
        "guard_sanity_ok": ok,
        "guard_sanity_notes": notes,
        "removal_ratio": ratio,
    }


def _extract_case_summary(experiment: Dict[str, Any]) -> Dict[str, Any]:
    cp_a = experiment.get("checkpoint_a_status") or {}
    cp_b = experiment.get("checkpoint_b_status") or {}
    case_ref = experiment.get("case_ref")
    mode = experiment.get("mode")
    profile = experiment.get("run_path_profile") or {}
    fixture_maturity = experiment.get("fixture_maturity") or (
        get_fixture_maturity(str(case_ref)) if case_ref else "unknown"
    )
    experimental_run = bool(
        mode == "run"
        and (
            profile.get("experimental")
            or (case_ref and is_experimental_fixture(str(case_ref)))
        )
    )
    controlled_experimental_run = bool(
        mode == "run"
        and (
            fixture_maturity == "controlled_experimental"
            or (case_ref and is_controlled_experimental_fixture(str(case_ref)))
        )
    )
    sanity = _check_guard_sanity(
        str(case_ref) if case_ref else None,
        experiment,
    )
    run_exec = experiment.get("run_execution") or {}
    return {
        "case_ref": case_ref,
        "case_dir": experiment.get("case_dir"),
        "mode": mode,
        "ok": experiment.get("ok"),
        "final_status": experiment.get("final_status"),
        "checkpoint_a_status": cp_a.get("status"),
        "checkpoint_b_status": cp_b.get("status"),
        "checkpoint_b_would_trigger": cp_b.get("would_trigger"),
        "decision": (experiment.get("decision") or {}).get("decision"),
        "experiment_id": experiment.get("experiment_id"),
        "experimental_run": experimental_run,
        "controlled_experimental_run": controlled_experimental_run,
        "fixture_maturity": fixture_maturity,
        "run_path_stop_at": profile.get("stop_at"),
        "removal_ratio": sanity.get("removal_ratio"),
        "guard_sanity_ok": sanity.get("guard_sanity_ok"),
        "guard_sanity_notes": sanity.get("guard_sanity_notes"),
        "regression_bundle_probe": bool(run_exec.get("regression_bundle_probe")),
    }


def write_regression_artifact(
    path: Path,
    *,
    experiment: Dict[str, Any],
    regression_meta: Dict[str, Any],
) -> Path:
    payload = {
        "schema_version": "agent_experiment_regression_v1",
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "regression_meta": regression_meta,
        "case_summary": _extract_case_summary(experiment),
        "experiment": experiment,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def run_agent_standard_case_regression(
    *,
    run_mode: RunMode = "preview",
    outbox_root: Optional[str] = None,
    auto_approve_intake: bool = False,
    timestamp: Optional[str] = None,
    include_extended_fixtures: bool = False,
) -> Dict[str, Any]:
    """Run experiment-line regression for allowlisted fixtures; write JSON artifacts."""
    ts = timestamp or _utc_timestamp()
    outbox = Path(outbox_root) if outbox_root else default_regression_outbox_root()
    regression_id = str(uuid.uuid4())

    case_specs = list(_DEFAULT_CASES)
    if include_extended_fixtures:
        case_specs.extend(_EXTENDED_CASES)

    checkpoint_scratch: Optional[Path] = None
    if run_mode in ("run", "run-all-allowed"):
        checkpoint_scratch = outbox / "_checkpoint_scratch" / ts
        checkpoint_scratch.mkdir(parents=True, exist_ok=True)

    cases_out: List[Dict[str, Any]] = []
    all_ok = True

    for spec in case_specs:
        case_ref = spec["case_ref"]
        case_dir = spec["case_dir"]
        mode = _resolve_case_mode(case_ref, run_mode)

        # W4-GUARD-01: Enforce fixture guard for experimental fixtures
        maturity = get_fixture_maturity(case_ref)
        guard_result = enforce_fixture_guard(
            case_ref,
            maturity,
            include_extended_fixtures=include_extended_fixtures,
            explicit_flags={},
        )
        if not guard_result["ok"]:
            # Guard blocked - record failure but continue for visibility
            summary = {
                "case_ref": case_ref,
                "case_dir": case_dir,
                "mode": mode,
                "ok": False,
                "final_status": "guard_blocked",
                "fixture_maturity": maturity,
                "guard_result": guard_result,
            }
            cases_out.append(summary)
            all_ok = False
            continue

        bundle_probe = (
            run_mode == "run-all-allowed"
            and include_extended_fixtures
            and case_ref == "additional_demo"
            and mode == "run"
        )
        experiment = run_agent_standard_case_experiment(
            _TASK_TYPE,
            case_dir,
            mode=mode,
            auto_approve_intake=auto_approve_intake if mode == "run" else False,
            outbox_root_override=str(checkpoint_scratch) if checkpoint_scratch else None,
            regression_bundle_probe=bundle_probe,
        )

        artifact = regression_artifact_path(
            outbox_root=outbox,
            timestamp=ts,
            case_ref=case_ref,
        )
        write_regression_artifact(
            artifact,
            experiment=experiment,
            regression_meta={
                "regression_id": regression_id,
                "timestamp": ts,
                "run_mode": run_mode,
                "requested_mode": mode,
            },
        )

        try:
            rel_artifact = artifact.relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            rel_artifact = artifact.as_posix()

        summary = _extract_case_summary(experiment)
        summary["artifact_path"] = rel_artifact
        cases_out.append(summary)

        if not experiment.get("ok"):
            all_ok = False
        if summary.get("guard_sanity_ok") is False:
            all_ok = False

    passed = sum(1 for c in cases_out if c.get("ok"))
    try:
        rel_outbox = outbox.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        rel_outbox = outbox.as_posix()
    return {
        "ok": all_ok,
        "regression_id": regression_id,
        "timestamp": ts,
        "run_mode": run_mode,
        "include_extended_fixtures": include_extended_fixtures,
        "task_type": _TASK_TYPE,
        "cases": cases_out,
        "summary": {
            "total": len(cases_out),
            "passed": passed,
            "failed": len(cases_out) - passed,
        },
        "outbox_root": rel_outbox,
        "message": "agent experiment regression complete"
        if all_ok
        else "agent experiment regression completed with failures",
    }


def format_regression_summary_text(result: Dict[str, Any]) -> str:
    lines = [
        "Agent-Run Standard Case Experiment Regression (W6-T8)",
        f"regression_id: {result.get('regression_id')}",
        f"timestamp: {result.get('timestamp')}",
        f"run_mode: {result.get('run_mode')}",
        f"ok: {result.get('ok')}",
        "",
        "case summaries:",
    ]
    for case in result.get("cases") or []:
        maturity = case.get("fixture_maturity") or "unknown"
        if case.get("controlled_experimental_run"):
            exp_tag = f" [{maturity} run]"
        elif case.get("experimental_run"):
            exp_tag = " [experimental run]"
        else:
            exp_tag = ""
        stop_at = case.get("run_path_stop_at")
        stop_note = f" stop_at={stop_at}" if stop_at else ""
        ratio = case.get("removal_ratio")
        ratio_note = f" removal_ratio={ratio}" if ratio is not None else ""
        sanity_note = ""
        if case.get("guard_sanity_ok") is False:
            sanity_note = f" guard_sanity=FAIL {case.get('guard_sanity_notes')}"
        lines.append(
            f"  - {case.get('case_ref')} ({case.get('mode')}){exp_tag}: "
            f"maturity={maturity} final_status={case.get('final_status')}{stop_note}"
            f"{ratio_note}{sanity_note} "
            f"checkpoint_a={case.get('checkpoint_a_status')} "
            f"checkpoint_b={case.get('checkpoint_b_status')}"
        )
        lines.append(f"    artifact: {case.get('artifact_path')}")
    sm = result.get("summary") or {}
    lines.append("")
    lines.append(f"passed: {sm.get('passed')}/{sm.get('total')}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Agent-run standard case experiment regression hook (W6-T8).",
    )
    parser.add_argument(
        "--run-mode",
        choices=("preview", "run", "run-all-allowed"),
        default="preview",
        help=(
            "preview (default): both cases preview; "
            "run: demo_phase run only; "
            "run-all-allowed: all fixtures with run_path_profile per W7-T2/W8-T1"
        ),
    )
    parser.add_argument(
        "--auto-approve-intake",
        action="store_true",
        help="When --run-mode run, auto-approve Checkpoint A for demo_phase",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Override regression artifact root (default: outbox/agent_experiment_regression)",
    )
    parser.add_argument(
        "--include-extended-fixtures",
        action="store_true",
        help=(
            "W4-GUARD-01: Explicitly allow experimental fixtures "
            "(additional_demo, sandbox_client) to run. "
            "Without this flag, experimental fixtures are GUARDED (blocked with error). "
            "Stable fixtures (demo_phase, sampleco) run normally without this flag."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text summary)",
    )
    args = parser.parse_args(argv)

    result = run_agent_standard_case_regression(
        run_mode=args.run_mode,  # type: ignore[arg-type]
        outbox_root=args.outbox_root,
        auto_approve_intake=args.auto_approve_intake,
        include_extended_fixtures=args.include_extended_fixtures,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_regression_summary_text(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
