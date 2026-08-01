"""Tabular output_guard warning policy (v1).

Profile-aware rules for CP-B auto-skip, delivery_ready, and internal-use
classification. Authoritative prose: docs/tabular-cleaning-automation-manifest-v1.md §1.12.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]

GUARD_STATUSES = frozenset({"ok", "warning", "error", "unknown"})
PROFILE_KEYS = frozenset({"demo_phase", "sampleco", "generic_low_risk_case", "unknown"})

# profile × guard_status → policy fields
# delivery_ready_allowed: may become true when CP-B + e2e also pass
# cp_b_auto_skip_allowed: driver may auto-approve CP-B without human
# internal_use_allowed: artifacts usable for internal/demo after CP-B manual approve
# partial_ready: chain may complete but external delivery_ready stays false
WARNING_GUARD_POLICY: dict[str, dict[str, dict[str, Any]]] = {
    "demo_phase": {
        "ok": {
            "delivery_ready_allowed": True,
            "cp_b_auto_skip_allowed": True,
            "internal_use_allowed": True,
            "partial_ready": False,
            "usage_tier": "regression_anchor",
        },
        "warning": {
            "delivery_ready_allowed": False,
            "cp_b_auto_skip_allowed": False,
            "internal_use_allowed": True,
            "partial_ready": True,
            "usage_tier": "internal_only",
        },
        "error": {
            "delivery_ready_allowed": False,
            "cp_b_auto_skip_allowed": False,
            "internal_use_allowed": False,
            "partial_ready": False,
            "usage_tier": "blocked",
        },
    },
    "sampleco": {
        "ok": {
            "delivery_ready_allowed": True,
            "cp_b_auto_skip_allowed": True,
            "internal_use_allowed": True,
            "partial_ready": False,
            "usage_tier": "allowlist_regression",
        },
        "warning": {
            "delivery_ready_allowed": False,
            "cp_b_auto_skip_allowed": False,
            "internal_use_allowed": True,
            "partial_ready": True,
            "usage_tier": "internal_only",
        },
        "error": {
            "delivery_ready_allowed": False,
            "cp_b_auto_skip_allowed": False,
            "internal_use_allowed": False,
            "partial_ready": False,
            "usage_tier": "blocked",
        },
    },
    "generic_low_risk_case": {
        "ok": {
            "delivery_ready_allowed": True,
            "cp_b_auto_skip_allowed": True,
            "internal_use_allowed": True,
            "partial_ready": False,
            "usage_tier": "low_risk_auto",
        },
        "warning": {
            "delivery_ready_allowed": False,
            "cp_b_auto_skip_allowed": False,
            "internal_use_allowed": True,
            "partial_ready": True,
            "usage_tier": "internal_only",
        },
        "error": {
            "delivery_ready_allowed": False,
            "cp_b_auto_skip_allowed": False,
            "internal_use_allowed": False,
            "partial_ready": False,
            "usage_tier": "blocked",
        },
    },
    "unknown": {
        "ok": {
            "delivery_ready_allowed": False,
            "cp_b_auto_skip_allowed": False,
            "internal_use_allowed": False,
            "partial_ready": False,
            "usage_tier": "fail_closed",
        },
        "warning": {
            "delivery_ready_allowed": False,
            "cp_b_auto_skip_allowed": False,
            "internal_use_allowed": False,
            "partial_ready": False,
            "usage_tier": "fail_closed",
        },
        "error": {
            "delivery_ready_allowed": False,
            "cp_b_auto_skip_allowed": False,
            "internal_use_allowed": False,
            "partial_ready": False,
            "usage_tier": "fail_closed",
        },
    },
}

# Fill unknown guard status rows with fail-closed defaults for each profile
for profile_key, by_status in WARNING_GUARD_POLICY.items():
    for status in GUARD_STATUSES:
        if status not in by_status:
            by_status[status] = dict(by_status.get("error") or by_status["warning"])


def repo_root() -> Path:
    return _REPO_ROOT


def _rel_case_path(case_dir: Path, root: Path | None = None) -> str:
    base = root or _REPO_ROOT
    try:
        return case_dir.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return case_dir.name


def resolve_warning_guard_profile(case_dir: Path, *, repo_root: Path | None = None) -> str:
    """Map case directory to warning-guard profile key."""
    rel = _rel_case_path(case_dir, repo_root)
    if rel.startswith("cases/"):
        rel = rel[len("cases/") :]
    parts = rel.split("/")
    top = parts[0] if parts else case_dir.name

    if top == "demo_phase" or case_dir.name == "demo_phase":
        return "demo_phase"
    if top == "sampleco":
        return "sampleco"

    intake_path = case_dir / "intake.json"
    if intake_path.is_file():
        try:
            data = json.loads(intake_path.read_text(encoding="utf-8"))
            client_ref = str(data.get("client_ref", "")).strip().lower()
            case_id = str(data.get("case_id", "")).strip().lower()
            if client_ref == "internal-demo" or case_id == "demo_phase":
                return "demo_phase"
            if client_ref == "sampleco":
                return "sampleco"
        except (OSError, json.JSONDecodeError):
            pass

    if top in {"demo_phase", "sampleco"}:
        return top

    return "generic_low_risk_case"


def _normalize_guard_status(status: str | None) -> str:
    token = str(status or "unknown").strip().lower()
    return token if token in GUARD_STATUSES else "unknown"


def evaluate_guard_policy(profile: str, guard_status: str | None) -> dict[str, Any]:
    """Return policy dict for profile + output_guard.status."""
    profile_key = profile if profile in PROFILE_KEYS else "unknown"
    status_key = _normalize_guard_status(guard_status)
    policy = dict(WARNING_GUARD_POLICY[profile_key][status_key])
    policy.update(
        {
            "profile": profile_key,
            "guard_status": status_key,
        }
    )
    return policy


def load_output_guard_status(case_dir: Path) -> tuple[str, dict[str, Any] | None]:
    """Read output_guard.status from report.json."""
    report_path = case_dir / "reports" / "report.json"
    if not report_path.is_file():
        return "unknown", None
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "unknown", None
    if not isinstance(report, dict):
        return "unknown", None
    guard = report.get("output_guard")
    if not isinstance(guard, dict):
        return "unknown", None
    return _normalize_guard_status(guard.get("status")), guard


def evaluate_case_guard_policy(case_dir: Path) -> dict[str, Any]:
    """Profile + guard status + policy for one case directory."""
    profile = resolve_warning_guard_profile(case_dir)
    guard_status, guard = load_output_guard_status(case_dir)
    policy = evaluate_guard_policy(profile, guard_status)
    return {
        "ok": True,
        "profile": profile,
        "guard_status": guard_status,
        "output_guard": guard,
        "policy": policy,
    }


def compute_delivery_ready_from_policy(
    *,
    cp_b_approved: bool,
    e2e_pass: bool,
    policy: dict[str, Any],
) -> bool:
    """Apply warning-guard policy on top of CP-B and e2e gates."""
    if not cp_b_approved or not e2e_pass:
        return False
    return bool(policy.get("delivery_ready_allowed"))


def should_auto_skip_checkpoint_b(
    *,
    policy: dict[str, Any],
    qa_status: str | None,
    removal_ratio: float | None,
    force: bool = False,
) -> bool:
    """Whether CP-B may auto-approve per warning-guard policy."""
    if force:
        return True
    if not policy.get("cp_b_auto_skip_allowed"):
        return False
    if str(qa_status or "").strip().lower() != "pass":
        return False
    return (removal_ratio or 0) <= 0.3
