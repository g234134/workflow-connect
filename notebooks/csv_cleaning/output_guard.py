"""Output row-ratio guard (Wave 4B · W-MVP-W4B-GUARD-RATIO).

Sidecar observation: cleaned output rows vs intake rows. Does not alter
cleaning logic, qa_status, or bundle/E2E exit codes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GUARD_VERSION = "output-guard-v0.1"
DEFAULT_RATIO_THRESHOLD = 0.5

_SCHEMA_FLAG_NOTES = frozenset({"multi_row_export", "schema_ambiguous"})


def _extract_row_counts(report: dict[str, Any]) -> tuple[int | None, int | None]:
    cleaning = report.get("cleaning_stats") or {}
    stats = report.get("stats") or {}
    row_counts = cleaning.get("row_counts") or stats.get("row_counts") or {}
    input_rows = row_counts.get("intake")
    output_rows = row_counts.get("ok", row_counts.get("accepted"))
    if input_rows is not None:
        input_rows = int(input_rows)
    if output_rows is not None:
        output_rows = int(output_rows)
    return input_rows, output_rows


def _schema_flags_from_eligibility(eligibility_raw: dict[str, Any] | None) -> list[str]:
    if not eligibility_raw:
        return []
    dimensions = eligibility_raw.get("dimensions") or {}
    schema = dimensions.get("schema") or {}
    notes = schema.get("notes") or []
    return [str(n) for n in notes if str(n) in _SCHEMA_FLAG_NOTES]


def compute_output_guard(
    report: dict[str, Any],
    *,
    eligibility_raw: dict[str, Any] | None = None,
    threshold: float = DEFAULT_RATIO_THRESHOLD,
) -> dict[str, Any]:
    """Compute output_guard sidecar from report row_counts and optional gate JSON."""
    input_rows, output_rows = _extract_row_counts(report)
    notes: list[str] = []

    if input_rows is None or output_rows is None:
        return {
            "guard_version": GUARD_VERSION,
            "ratio": None,
            "input_rows": input_rows,
            "output_rows": output_rows,
            "threshold": threshold,
            "status": "unknown",
            "notes": ["row_counts_missing"],
        }

    if input_rows <= 0:
        return {
            "guard_version": GUARD_VERSION,
            "ratio": None,
            "input_rows": input_rows,
            "output_rows": output_rows,
            "threshold": threshold,
            "status": "unknown",
            "notes": ["input_rows_zero_or_negative"],
        }

    ratio = round(output_rows / input_rows, 4)
    status = "ok" if ratio >= threshold else "warning"

    if status == "warning":
        notes.append(
            f"output_rows ({output_rows}) / input_rows ({input_rows}) = {ratio} "
            f"below MVP threshold {threshold}; manual review recommended"
        )

    schema_flags = _schema_flags_from_eligibility(eligibility_raw)
    if schema_flags:
        notes.append(
            "schema probe flagged ambiguous export pattern; see schema_flags"
        )

    guard: dict[str, Any] = {
        "guard_version": GUARD_VERSION,
        "ratio": ratio,
        "input_rows": input_rows,
        "output_rows": output_rows,
        "threshold": threshold,
        "status": status,
        "notes": notes,
    }
    if schema_flags:
        guard["schema_flags"] = schema_flags
    return guard


def apply_output_guard_to_report(
    case_dir: Path,
    report: dict[str, Any],
    *,
    eligibility_raw: dict[str, Any] | None = None,
    threshold: float = DEFAULT_RATIO_THRESHOLD,
    write: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Attach output_guard to report dict and optionally persist report.json."""
    if eligibility_raw is None:
        from case_eligibility import check_case_eligibility

        eligibility_raw = check_case_eligibility(case_dir)

    guard = compute_output_guard(
        report, eligibility_raw=eligibility_raw, threshold=threshold
    )
    report["output_guard"] = guard

    if write:
        report_path = case_dir / "reports" / "report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return report, guard
