"""Controlled delivery / notify experiment v1 (W7-T3).

Reads existing delivery_signoff and bundle artifacts for internal sandbox cases,
generates simulated client-facing summary text, and writes a notify payload to
outbox/ only. Does not call real notification gateways or production delivery.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from tools.tabular_outbox_writer import format_run_timestamp, outbox_root
from tools.tabular_tool_executor import resolve_case_ref

EXPERIMENT_VERSION = "v1"
SCHEMA_VERSION = "controlled_notify_experiment_v1"

ALLOWLIST_CASE_REFS = frozenset({"demo_phase", "sampleco/2026-0001"})
INTERNAL_SENSITIVITY_VALUES = frozenset({"internal"})

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return repo_root.resolve() if repo_root is not None else _REPO_ROOT


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _load_intake(case_dir: Path) -> dict[str, Any]:
    for name in ("intake.json", "intake_record.json"):
        data = _load_json(case_dir / name)
        if data is not None:
            return data
    return {}


def _normalize_case_dir(
    case_dir: Union[str, Path],
    repo_root: Optional[Path] = None,
) -> Path:
    root = _repo_root(repo_root)
    path = Path(case_dir)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _case_dir_rel(case_path: Path, root: Path, case_ref: str) -> str:
    try:
        return case_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return case_ref


def is_experiment_case_allowed(
    case_ref: str,
    intake: Optional[dict[str, Any]] = None,
) -> tuple[bool, str]:
    """Return (allowed, reason). Restricted to internal sandbox allowlist."""
    ref = str(case_ref or "").replace("\\", "/").strip("/")
    if ref not in ALLOWLIST_CASE_REFS:
        return False, f"case_ref not in experiment allowlist: {ref!r}"

    intake = intake or {}
    sensitivity = str(intake.get("sensitivity") or "").strip().lower()
    if sensitivity and sensitivity not in INTERNAL_SENSITIVITY_VALUES:
        return False, f"sensitivity must be internal for notify experiment (got {sensitivity!r})"

    client_ref = str(intake.get("client_ref") or "").strip().lower()
    if client_ref.startswith("acme") or client_ref.endswith("-prod"):
        return False, "client_ref indicates non-sandbox fixture"

    return True, "allowed"


def _parse_signoff_fields(signoff_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in signoff_text.splitlines():
        match = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line.strip())
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip().strip("_")
        if key in {"field", "-------"}:
            continue
        fields[key] = value
    return fields


def load_delivery_context(
    case_dir: Union[str, Path],
    *,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Load signoff, report, eligibility, and bundle artifact paths from case_dir."""
    root = _repo_root(repo_root)
    case_path = _normalize_case_dir(case_dir, root)
    case_ref = resolve_case_ref(case_path)
    case_dir_rel = _case_dir_rel(case_path, root, case_ref)

    if not case_path.is_dir():
        return {
            "ok": False,
            "message": f"case directory not found: {case_dir_rel}",
            "case_ref": case_ref,
            "case_dir": case_dir_rel,
        }

    intake = _load_intake(case_path)
    allowed, allow_reason = is_experiment_case_allowed(case_ref, intake)
    if not allowed:
        return {
            "ok": False,
            "message": allow_reason,
            "blocked": True,
            "case_ref": case_ref,
            "case_dir": case_dir_rel,
        }

    signoff_path = case_path / "delivery_signoff.md"
    report_path = case_path / "reports" / "report.json"
    eligibility_path = case_path / "reports" / "eligibility_result.json"
    report_md_path = case_path / "reports" / "report.md"
    cleaning_stats_path = case_path / "reports" / "cleaning_stats.json"

    missing: list[str] = []
    if not signoff_path.is_file():
        missing.append("delivery_signoff.md")
    if not report_path.is_file():
        missing.append("reports/report.json")

    if missing:
        return {
            "ok": False,
            "message": "missing required delivery inputs",
            "case_ref": case_ref,
            "case_dir": case_dir_rel,
            "missing": missing,
        }

    report = _load_json(report_path) or {}
    eligibility = _load_json(eligibility_path) or {}
    signoff_text = signoff_path.read_text(encoding="utf-8")
    signoff_fields = _parse_signoff_fields(signoff_text)

    cleaned_csvs = sorted(
        p.relative_to(case_path).as_posix()
        for p in (case_path / "cleaned").glob("*.csv")
        if p.is_file()
    )

    bundle_artifacts: list[str] = []
    for rel in (
        "delivery_signoff.md",
        "reports/report.json",
        "reports/report.md",
        "reports/eligibility_result.json",
        "reports/cleaning_stats.json",
    ):
        if (case_path / rel).is_file():
            bundle_artifacts.append(rel)
    bundle_artifacts.extend(cleaned_csvs)

    summary_block = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    output_guard = report.get("output_guard") if isinstance(report.get("output_guard"), dict) else {}

    return {
        "ok": True,
        "message": "delivery context loaded",
        "case_ref": case_ref,
        "case_dir": case_dir_rel,
        "intake": intake,
        "signoff_path": signoff_path.relative_to(case_path).as_posix(),
        "signoff_fields": signoff_fields,
        "report": report,
        "eligibility": eligibility,
        "bundle_artifacts": bundle_artifacts,
        "delivery_sources": {
            "signoff": "delivery_signoff.md",
            "report": "reports/report.json",
            "eligibility": "reports/eligibility_result.json"
            if eligibility_path.is_file()
            else None,
            "report_md": "reports/report.md" if report_md_path.is_file() else None,
            "cleaning_stats": "reports/cleaning_stats.json"
            if cleaning_stats_path.is_file()
            else None,
        },
        "metrics": {
            "case_id": str(intake.get("case_id") or signoff_fields.get("case_id") or case_ref),
            "client_ref": str(intake.get("client_ref") or signoff_fields.get("client_ref") or "unknown"),
            "product_sku": str(
                intake.get("product_sku")
                or summary_block.get("sku")
                or signoff_fields.get("product_sku")
                or "CLEAN-BASIC"
            ),
            "job_id": str(summary_block.get("job_id") or signoff_fields.get("job_id") or case_ref),
            "qa_status": str(
                summary_block.get("qa_status")
                or (report.get("issues_summary") or {}).get("qa_status")
                or eligibility.get("status")
                or "unknown"
            ),
            "accepted_rows": summary_block.get("accepted_rows"),
            "rejected_rows": summary_block.get("rejected_rows"),
            "total_rows": summary_block.get("total_rows"),
            "output_guard_status": output_guard.get("status"),
        },
    }


def generate_client_summary(context: dict[str, Any]) -> str:
    """Build plain-text client-facing delivery summary (simulated only)."""
    metrics = context.get("metrics") or {}
    case_id = metrics.get("case_id", "unknown")
    client_ref = metrics.get("client_ref", "unknown")
    sku = metrics.get("product_sku", "CLEAN-BASIC")
    job_id = metrics.get("job_id", case_id)
    qa_status = metrics.get("qa_status", "unknown")
    accepted = metrics.get("accepted_rows")
    rejected = metrics.get("rejected_rows")
    total = metrics.get("total_rows")
    guard_status = metrics.get("output_guard_status")

    lines = [
        f"Subject: Tabular cleaning delivery ready — {case_id}",
        "",
        f"Dear {client_ref} team,",
        "",
        f"Your cleaning job `{job_id}` ({sku}) has completed internal QA review.",
    ]

    if total is not None and accepted is not None:
        tail = f" Accepted {accepted} of {total} rows"
        if rejected is not None:
            tail += f" ({rejected} rejected)"
        lines.append(tail + ".")
    else:
        lines.append("Row-level metrics are available in the attached bundle report.")

    lines.extend(
        [
            f"QA status: {qa_status}.",
        ]
    )
    if guard_status:
        lines.append(f"Output guard: {guard_status}.")

    next_steps = (context.get("report") or {}).get("next_steps") or {}
    customer_steps = next_steps.get("for_customer")
    if isinstance(customer_steps, list) and customer_steps:
        lines.append("")
        lines.append("Suggested follow-up:")
        for item in customer_steps[:3]:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "This message was generated by the controlled notify experiment (sandbox only).",
            "No external email or chat notification was sent.",
            "",
            f"Bundle artifacts: {', '.join(context.get('bundle_artifacts') or [])}",
        ]
    )
    return "\n".join(lines)


def build_notify_experiment_record(
    context: dict[str, Any],
    *,
    client_summary_text: str,
    dry_run: bool,
    generated_at: Optional[str] = None,
) -> dict[str, Any]:
    """Assemble outbox notify_experiment JSON payload."""
    metrics = context.get("metrics") or {}
    case_ref = str(context.get("case_ref") or "")
    case_dir = str(context.get("case_dir") or "")
    subject_line = client_summary_text.splitlines()[0]
    if subject_line.lower().startswith("subject:"):
        subject_line = subject_line.split(":", 1)[1].strip()

    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_version": EXPERIMENT_VERSION,
        "case_ref": case_ref,
        "case_dir": case_dir,
        "generated_at": generated_at or _utc_now_iso(),
        "dry_run": bool(dry_run),
        "simulated": True,
        "external_dispatch": False,
        "notify_channel": "experiment_log",
        "delivery_sources": context.get("delivery_sources") or {},
        "bundle_artifacts": context.get("bundle_artifacts") or [],
        "metrics": metrics,
        "client_summary_text": client_summary_text,
        "notify_payload": {
            "subject": subject_line,
            "body_text": client_summary_text,
            "recipient_hint": f"{metrics.get('client_ref', 'unknown')} (simulated only)",
            "channel": "experiment_log",
            "external_dispatch": False,
        },
    }


def run_controlled_notify_experiment(
    case_dir: Union[str, Path],
    *,
    dry_run: bool = True,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> dict[str, Any]:
    """Load bundle/signoff, generate summary, optionally write outbox notify JSON."""
    context = load_delivery_context(case_dir, repo_root=repo_root)
    if not context.get("ok"):
        return {
            "ok": False,
            "message": str(context.get("message") or "failed to load delivery context"),
            "blocked": bool(context.get("blocked")),
            "case_ref": context.get("case_ref"),
            "case_dir": context.get("case_dir"),
            "missing": context.get("missing"),
        }

    client_summary_text = generate_client_summary(context)
    record = build_notify_experiment_record(
        context,
        client_summary_text=client_summary_text,
        dry_run=dry_run,
    )

    outbox_path: str | None = None
    if not dry_run:
        root = _repo_root(repo_root)
        ob_root = outbox_root(root, outbox_root_override)
        case_ref = str(context["case_ref"])
        ts = format_run_timestamp()
        filename = f"notify_experiment_{ts}.json"
        target = ob_root / case_ref / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            outbox_path = target.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            outbox_path = target.as_posix()

    return {
        "ok": True,
        "message": "notify experiment completed (simulated only)"
        if dry_run
        else "notify experiment payload written to outbox",
        "dry_run": dry_run,
        "simulated": True,
        "external_dispatch": False,
        "case_ref": context.get("case_ref"),
        "case_dir": context.get("case_dir"),
        "client_summary_text": client_summary_text,
        "notify_payload": record.get("notify_payload"),
        "outbox_path": outbox_path,
        "record": record,
    }
