#!/usr/bin/env python3
"""E2E validation driver: intake → gate → cleaning → bundle (Wave 3 · W-MVP-W3).

Runs the P1–P4 CLI chain for a single case_dir and prints a structured summary.
Does not modify gate rules, cleaning logic, or bundle structure.

Usage:
    python scripts/run_case_e2e_validation.py
    python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase
    python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_CASE_DIR = _REPO_ROOT / "cases" / "demo_phase"
_GATE_SCRIPT = _REPO_ROOT / "scripts" / "check_case_eligibility.py"
_CLEAN_SCRIPT = _REPO_ROOT / "notebooks" / "csv_cleaning" / "clean_phase_demo.py"
_BUNDLE_SCRIPT = _REPO_ROOT / "scripts" / "build_case_delivery_bundle.py"

if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
from w4_guard_escalation_v1 import (  # noqa: E402
    attach_guard_escalation,
    evaluate_guard_escalation,
)


def _rel_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(_REPO_ROOT.resolve()))
    except ValueError:
        return str(resolved)


def _run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout, proc.stderr


def _parse_json_output(text: str) -> dict:
    """Extract the first JSON object from subprocess stdout (may be multi-line)."""
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


def _check_case_structure(case_dir: Path) -> list[str]:
    missing: list[str] = []
    if not case_dir.is_dir():
        return ["case_dir"]
    for name in ("intake.json", "raw"):
        if not (case_dir / name).exists():
            missing.append(name)
    return missing


def run_case_e2e_validation(
    case_dir: Path,
    *,
    force_review: bool = True,
    enable_guard_escalation: bool = False,
    enable_g2: bool = False,
    enable_g3: bool = False,
    enable_g4: bool = False,
    strict_guards: bool = False,
) -> dict:
    """Execute gate → cleaning → bundle for one case directory."""
    case_dir = case_dir.resolve()
    case_label = _rel_path(case_dir)

    result: dict = {
        "ok": False,
        "case_dir": case_label,
        "eligibility": None,
        "steps": {},
        "artifacts": {},
        "message": "",
    }

    missing = _check_case_structure(case_dir)
    if missing:
        result["message"] = f"case structure incomplete: missing {', '.join(missing)}"
        result["steps"]["structure"] = {"ok": False, "missing": missing}
        return result

    result["steps"]["structure"] = {"ok": True}

    # Step 1 — gate (P2)
    gate_rc, gate_out, gate_err = _run_cmd(
        [
            sys.executable,
            str(_GATE_SCRIPT),
            "--case-dir",
            str(case_dir),
            "--json",
        ]
    )
    gate_data = _parse_json_output(gate_out)
    eligibility = gate_data.get("eligibility", "unknown")
    gate_ran = gate_data.get("ok") is True
    result["eligibility"] = eligibility
    result["steps"]["gate"] = {
        "ok": gate_ran,
        "exit_code": gate_rc,
        "eligibility": eligibility,
        "reason_code": gate_data.get("reason_code"),
    }

    if not gate_ran:
        result["message"] = "gate script failed or returned invalid JSON"
        if gate_err:
            result["steps"]["gate"]["stderr"] = gate_err[:500]
        return result

    if eligibility == "rejected":
        result["message"] = "gate rejected; cleaning and bundle skipped"
        return result

    # Step 2 — cleaning (P3)
    clean_cmd = [
        sys.executable,
        str(_CLEAN_SCRIPT),
        "--case-dir",
        str(case_dir),
        "--skip-eligibility",
    ]
    forced = False
    if eligibility == "review_needed":
        if not force_review:
            result["message"] = "review_needed without --force-review; cleaning skipped"
            result["steps"]["cleaning"] = {"ok": False, "skipped": True}
            return result
        clean_cmd.append("--force")
        forced = True

    clean_rc, clean_out, clean_err = _run_cmd(clean_cmd)
    clean_data = _parse_json_output(clean_out)
    clean_ok = clean_rc == 0 and clean_data.get("ok") is True
    result["steps"]["cleaning"] = {
        "ok": clean_ok,
        "exit_code": clean_rc,
        "forced": forced,
        "output_path": clean_data.get("output_path"),
        "report_json": clean_data.get("report_json"),
        "cleaning_profile_id": clean_data.get("cleaning_profile_id"),
    }
    if clean_data.get("cleaning_profile_id"):
        result["cleaning_profile_id"] = clean_data["cleaning_profile_id"]

    if not clean_ok:
        result["message"] = f"cleaning failed (exit {clean_rc})"
        if clean_err:
            result["steps"]["cleaning"]["stderr"] = clean_err[:500]
        return result

    # Step 3 — bundle (P4)
    bundle_rc, bundle_out, bundle_err = _run_cmd(
        [
            sys.executable,
            str(_BUNDLE_SCRIPT),
            "--case-dir",
            str(case_dir),
            "--json",
        ]
    )
    bundle_data = _parse_json_output(bundle_out)
    bundle_ok = bundle_rc == 0 and bundle_data.get("ok") is True
    result["steps"]["bundle"] = {
        "ok": bundle_ok,
        "exit_code": bundle_rc,
        "eligibility_status": bundle_data.get("eligibility_status"),
    }
    if bundle_data.get("artifacts"):
        result["artifacts"] = bundle_data["artifacts"]
    if bundle_data.get("output_guard"):
        result["output_guard"] = bundle_data["output_guard"]
    else:
        report_path = case_dir / "reports" / "report.json"
        if report_path.is_file():
            try:
                report_data = json.loads(report_path.read_text(encoding="utf-8"))
                if isinstance(report_data, dict) and report_data.get("output_guard"):
                    result["output_guard"] = report_data["output_guard"]
            except json.JSONDecodeError:
                pass

    if not bundle_ok:
        result["message"] = bundle_data.get("message") or f"bundle failed (exit {bundle_rc})"
        if bundle_err:
            result["steps"]["bundle"]["stderr"] = bundle_err[:500]
        return result

    result["ok"] = True
    result["message"] = "e2e validation passed"

    # W4-GUARD G2–G4: observation by default; apply only when flags set.
    qa_status = None
    report_path = case_dir / "reports" / "report.json"
    if report_path.is_file():
        try:
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
            if isinstance(report_data, dict):
                summary = report_data.get("summary") or {}
                qa_status = report_data.get("qa_status") or summary.get("qa_status")
        except json.JSONDecodeError:
            pass

    apply_g2 = enable_g2 or enable_guard_escalation
    apply_g3 = enable_g3 or enable_guard_escalation
    apply_g4 = enable_g4 or enable_guard_escalation or strict_guards
    escalation = evaluate_guard_escalation(
        eligibility_raw=gate_data,
        output_guard=result.get("output_guard"),
        qa_status=qa_status,
        enable_g2=apply_g2,
        enable_g3=apply_g3,
        enable_g4=apply_g4,
        strict_guards=strict_guards,
    )
    attach_guard_escalation(result, escalation)
    return result


def print_summary(result: dict) -> None:
    print("=== Case E2E Validation Summary ===")
    print(f"case_dir:     {result.get('case_dir')}")
    print(f"overall_ok:   {result.get('ok')}")
    print(f"eligibility:  {result.get('eligibility')}")
    if result.get("message"):
        print(f"message:      {result.get('message')}")

    steps = result.get("steps") or {}
    gate = steps.get("gate") or {}
    print(
        f"gate:         {'ok' if gate.get('ok') else 'FAIL'}"
        f" (eligibility={gate.get('eligibility')}, exit={gate.get('exit_code')})"
    )

    cleaning = steps.get("cleaning") or {}
    forced_suffix = " [forced]" if cleaning.get("forced") else ""
    profile_suffix = ""
    if cleaning.get("cleaning_profile_id"):
        profile_suffix = f" · profile={cleaning.get('cleaning_profile_id')}"
    print(f"cleaning:     {'ok' if cleaning.get('ok') else 'FAIL'}{forced_suffix}{profile_suffix}")

    if result.get("cleaning_profile_id"):
        print(f"profile_id:   {result.get('cleaning_profile_id')}")

    bundle = steps.get("bundle") or {}
    print(f"bundle:       {'ok' if bundle.get('ok') else 'FAIL'}")

    esc = result.get("guard_escalation") or {}
    if esc:
        print(
            f"guards:       {esc.get('message')} "
            f"(e2e_fail={esc.get('e2e_fail')} strict={((esc.get('flags') or {}).get('strict_guards'))})"
        )

    arts = result.get("artifacts") or {}
    for key in (
        "cleaned_csv",
        "report_json",
        "report_md",
        "eligibility_result_json",
        "delivery_signoff_md",
    ):
        val = arts.get(key)
        if val:
            print(f"  {key}: {val}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run intake→gate→clean→bundle e2e validation for a single case_dir."
    )
    parser.add_argument(
        "--case-dir",
        type=Path,
        default=_DEFAULT_CASE_DIR,
        help="Case directory (default: cases/demo_phase)",
    )
    parser.add_argument(
        "--force-review",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Continue cleaning when gate returns review_needed (default: true)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full structured result JSON after summary",
    )
    parser.add_argument(
        "--enable-guard-escalation",
        action="store_true",
        default=False,
        help="Opt-in: apply G2/G3 recommendations into guard_escalation.applied (default off)",
    )
    parser.add_argument(
        "--strict-guards",
        action="store_true",
        default=False,
        help="Opt-in G4: fail E2E when pass_with_warnings + G3 signal (default off; ≠ prod required)",
    )
    args = parser.parse_args(argv)

    result = run_case_e2e_validation(
        args.case_dir,
        force_review=args.force_review,
        enable_guard_escalation=args.enable_guard_escalation,
        strict_guards=args.strict_guards,
    )
    print_summary(result)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
