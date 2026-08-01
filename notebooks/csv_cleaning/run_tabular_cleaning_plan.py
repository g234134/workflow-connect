#!/usr/bin/env python3
"""C2-P2 runbook step planner — lists stages and checklists only.

INTERNAL ONLY · NOT PROD PIPELINE · NON-SLA
Does not perform cleaning; see docs/C2-P2_RUNBOOK.md and clean_phase_demo.py for demo.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

STAGES: dict[str, dict[str, Any]] = {
    "intake": {
        "title": "Stage A · Intake",
        "spec_refs": ["C2-P1 §2.1–§2.4", "C2-P1 §5 Step 1"],
        "inputs": [
            "Raw CSV/Excel (e.g. cases/demo_phase/Phase.csv)",
            "Field schema notes, primary key, nullable fields",
            "Cleaning goals from customer",
        ],
        "outputs": ["intake_summary.md", "cleaning_rules_draft.md", "job_id"],
        "checklist": [
            "File parses as 2D table; not OCR/PDF",
            "Size within ~1M rows / 1 GB",
            "Primary key and dedup strategy agreed",
            "Nullable vs required fields documented",
            "Degraded scope declared if inputs incomplete",
        ],
        "signoff": "Lead + customer: rules matrix and scope (#1)",
    },
    "cleaning": {
        "title": "Stage B · Cleaning (Profiling + Cleaning)",
        "spec_refs": ["C2-P1 §1.1", "C2-P1 §5 Step 2–3"],
        "inputs": ["Signed cleaning_rules_draft.md", "Raw data file", "job_id"],
        "outputs": [
            "cleaning_stats.json (before/after)",
            "{case}_cleaned.csv",
            "cleaning_rules_applied (→ report.json)",
        ],
        "checklist": [
            "Profile: total_rows, missing_rate_by_field, duplicates, format, anomalies",
            "Apply missing / duplicate / anomaly / format rules per matrix",
            "Do not auto-guess missing fills without agreement",
            "Demo rerun: python notebooks/csv_cleaning/clean_phase_demo.py",
        ],
        "signoff": "Analyst → Lead: thresholds and edge cases (#2)",
    },
    "quality": {
        "title": "Stage C · Quality Report",
        "spec_refs": ["C2-P1 §3.1", "C2-P1 §5 Step 4–5"],
        "inputs": [
            "cleaning_stats.json",
            "{case}_cleaned.csv",
            "WAVE6_CLEAN_DELIVERABLE_TEMPLATES structure",
        ],
        "outputs": [
            "report.json (product_metrics + summary/stats/errors)",
            "report.md",
            "docs/CASE_REPORTS/{ticket}_*.md",
        ],
        "checklist": [
            "product_metrics align with C2-P1 §3.1 (see runbook Appendix A)",
            "qa_status reviewed; warnings documented",
            "errors.top_errors_sample de-identified",
            "meta.disclaimer includes non-SLA / manual review",
        ],
        "signoff": "Reviewer or Lead: qa_status and report consistency (#3)",
    },
    "delivery": {
        "title": "Stage D · Delivery",
        "spec_refs": ["C2-P1 §3.1–§3.2", "C2-P1 §5 Step 5"],
        "inputs": ["Full stage C package", "QC signoff #3"],
        "outputs": [
            "delivery/{job_id}/ bundle",
            "delivery_manifest.md",
            "delivery_signoff.md",
        ],
        "checklist": [
            "No absolute paths or secrets in deliverables",
            "PII redacted per agreement",
            "Customer informed: non-SLA, not fully automated",
            "Do not imply self-service pipeline exists",
        ],
        "signoff": "Lead: external delivery approval (#4)",
    },
}

STAGE_ORDER = ["intake", "cleaning", "quality", "delivery"]

DISCLAIMER = (
    "INTERNAL USE ONLY · NOT A PROD PIPELINE · NON-SLA · "
    "Manual signoffs required at each stage."
)


def emit_stage(name: str, *, case: str | None) -> dict[str, Any]:
    stage = STAGES[name]
    payload: dict[str, Any] = {
        "ok": True,
        "stage": name,
        "title": stage["title"],
        "disclaimer": DISCLAIMER,
        "spec_refs": stage["spec_refs"],
        "inputs": stage["inputs"],
        "outputs": stage["outputs"],
        "checklist": stage["checklist"],
        "signoff": stage["signoff"],
        "runbook": "docs/C2-P2_RUNBOOK.md",
    }
    if case == "demo_phase":
        payload["demo_anchor"] = {
            "case_dir": "cases/demo_phase",
            "intake": "cases/demo_phase/intake.json",
            "input": "cases/demo_phase/raw/Phase.csv",
            "output": "cases/demo_phase/cleaned/Phase_cleaned.csv",
            "report": "cases/demo_phase/reports/report.json",
            "script": "notebooks/csv_cleaning/clean_phase_demo.py",
            "expected_metrics": {
                "total_rows": 7,
                "accepted_rows": 5,
                "rejected_rows": 1,
                "duplicate_rows_found": 2,
                "duplicate_rows_removed": 1,
                "qa_status": "pass_with_warnings",
            },
        }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List C2-P2 runbook stages and checklists (no cleaning)."
    )
    parser.add_argument(
        "--stage",
        choices=["intake", "cleaning", "quality", "delivery", "all"],
        default="all",
        help="Which stage to print (default: all)",
    )
    parser.add_argument(
        "--case",
        default=None,
        help="Optional case anchor (e.g. demo_phase)",
    )
    args = parser.parse_args(argv)

    if args.stage == "all":
        result = {
            "ok": True,
            "disclaimer": DISCLAIMER,
            "runbook": "docs/C2-P2_RUNBOOK.md",
            "stages": [emit_stage(s, case=args.case) for s in STAGE_ORDER],
        }
    else:
        result = emit_stage(args.stage, case=args.case)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
