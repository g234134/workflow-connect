#!/usr/bin/env python3
"""
Wave 8 — Semi-automatic Skill Card draft generator (v0.1).

Reads a successful CLEAN run_summary.json and emits a skill_card_v0.1-style
draft JSON for human review. Does not write to skills/cards/ or modify registry.

Usage:
    python 04_Workflows/_wave8_generate_skill_card_draft.py \\
        --run-summary path/to/run_summary.json --pretty

    python 04_Workflows/_wave8_generate_skill_card_draft.py \\
        --run-summary path/to/run_summary.json --output draft.json --pretty

Exit codes:
    0 — draft generated
    1 — not eligible, I/O error, or invalid input
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "skill_card_v0.1"
HIGH_VOLUME_MIN_ROWS = 100_000
HIGH_VOLUME_MIN_FILES = 10

_NOT_ELIGIBLE_MSG = "not eligible for draft generation"

_COMPLEXITY_SIGNAL_PATTERNS = (
    re.compile(r"multi[-_]?source", re.I),
    re.compile(r"multi[-_]?stage", re.I),
    re.compile(r"nested[-_]?workflow", re.I),
    re.compile(r"cross[-_]?ref", re.I),
    re.compile(r"\bxref\b", re.I),
)


def load_run_summary(path: str | Path) -> dict[str, Any]:
    """Load and validate run_summary.json root object."""
    summary_path = Path(path)
    if not summary_path.is_file():
        raise FileNotFoundError(f"run summary not found: {summary_path}")

    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in run summary: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("run summary root must be a JSON object")
    return data


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def is_eligible_for_draft(summary: dict[str, Any]) -> tuple[bool, str]:
    """
    Only qa_status == pass with clear success signals qualifies for draft generation.
    """
    outcome = summary.get("outcome")
    if not isinstance(outcome, dict):
        return False, "missing outcome block"

    qa_status = outcome.get("qa_status")
    if not isinstance(qa_status, str) or qa_status.strip().lower() != "pass":
        return False, f"qa_status must be pass (got {qa_status!r})"

    overall_ok = outcome.get("overall_ok")
    if overall_ok is not True:
        return False, "overall_ok must be true"

    job_status = outcome.get("job_status")
    if isinstance(job_status, str) and job_status.strip().lower() != "done":
        return False, f"job_status must be done (got {job_status!r})"

    identity = summary.get("identity")
    if not isinstance(identity, dict):
        return False, "missing identity block"

    job_id = identity.get("job_id")
    product_sku = identity.get("product_sku")
    if not isinstance(job_id, str) or not job_id.strip():
        return False, "missing job_id"
    if not isinstance(product_sku, str) or not product_sku.strip():
        return False, "missing product_sku"

    return True, ""


def _input_volume_metrics(summary: dict[str, Any]) -> tuple[int | None, int | None]:
    volume = summary.get("input_volume")
    if not isinstance(volume, dict):
        return None, None
    return (
        _coerce_int(volume.get("row_count")),
        _coerce_int(volume.get("file_count")),
    )


def is_high_volume(summary: dict[str, Any]) -> bool:
    row_count, file_count = _input_volume_metrics(summary)
    if row_count is not None and row_count >= HIGH_VOLUME_MIN_ROWS:
        return True
    if file_count is not None and file_count >= HIGH_VOLUME_MIN_FILES:
        return True
    return False


def _json_blob_for_heuristics(summary: dict[str, Any]) -> str:
    try:
        return json.dumps(summary, ensure_ascii=False).lower()
    except (TypeError, ValueError):
        return str(summary).lower()


def _has_complexity_text_signals(blob: str) -> bool:
    return any(pat.search(blob) for pat in _COMPLEXITY_SIGNAL_PATTERNS)


def is_high_complexity(summary: dict[str, Any]) -> bool:
    """
    Heuristic: multi-source / multi-stage / nested workflow / cross-reference signals.
    Defaults to False when inconclusive.
    """
    blob = _json_blob_for_heuristics(summary)

    if _has_complexity_text_signals(blob):
        return True

    identity = summary.get("identity")
    if isinstance(identity, dict):
        order_id = identity.get("order_id")
        batch_tag = identity.get("batch_tag")
        if order_id and batch_tag:
            return True

    row_count, file_count = _input_volume_metrics(summary)
    if file_count is not None and file_count >= 3:
        if row_count is not None and row_count >= 10_000:
            return True

    runtime = summary.get("runtime_stats")
    if isinstance(runtime, dict):
        if _coerce_int(runtime.get("envelope_compute_count")) or 0 > 1:
            return True
        if _coerce_int(runtime.get("storage_retry_count")) or 0 > 1:
            return True
        if runtime.get("checkpoint_hit") is True:
            return True

    artifacts = summary.get("artifacts")
    if isinstance(artifacts, dict):
        deliverable_refs = artifacts.get("deliverable_refs")
        if isinstance(deliverable_refs, list) and len(deliverable_refs) > 1:
            return True

    qa_layers = summary.get("qa_layers")
    if isinstance(qa_layers, dict):
        m2 = qa_layers.get("m2_summary")
        if isinstance(m2, dict) and m2.get("status") == "completed":
            sample_size = _coerce_int(m2.get("sample_size"))
            if sample_size is not None and sample_size > 0:
                return True

    product_sku = ""
    if isinstance(identity, dict) and isinstance(identity.get("product_sku"), str):
        product_sku = identity["product_sku"].strip().upper()
    if product_sku == "CLEAN-ENRICH" and (file_count or 0) >= 2:
        return True

    return False


def build_input_profile_description(
    summary: dict[str, Any],
    *,
    high_volume: bool,
    high_complexity: bool,
) -> str:
    row_count, file_count = _input_volume_metrics(summary)
    parts: list[str] = []

    if file_count is not None and row_count is not None:
        parts.append(f"approximately {row_count:,} rows across {file_count} input file(s)")
    elif row_count is not None:
        parts.append(f"approximately {row_count:,} rows")
    elif file_count is not None:
        parts.append(f"{file_count} input file(s)")
    else:
        parts.append("input volume not fully recorded in run summary")

    identity = summary.get("identity")
    if isinstance(identity, dict):
        sku = identity.get("product_sku")
        if isinstance(sku, str) and sku.strip():
            parts.append(f"under product SKU {sku.strip()}")

    if high_volume:
        parts.append("classified as high-volume intake")
    if high_complexity:
        parts.append("shows multi-stage or cross-source complexity signals")

    return "; ".join(parts) + "."


def _draft_skill_id(product_sku: str, job_id: str) -> str:
    sku_slug = product_sku.strip().lower().replace("_", "-")
    job_slug = job_id.strip().lower().replace("_", "-")
    return f"draft-{sku_slug}-{job_slug}"


def _pre_processing_recommendations(
    *,
    product_sku: str,
    high_volume: bool,
    high_complexity: bool,
) -> list[str]:
    tips = [
        "Validate input encoding and column headers against the target CLEAN product matrix before transform.",
        "Confirm intake file_count and row_count estimates match manifest billing_units after S3 entry.",
    ]
    if high_volume:
        tips.append(
            "For high-volume runs, enable checkpoint-friendly batching and monitor storage_retry_count during finalize."
        )
    elif high_complexity or product_sku.strip().upper() == "CLEAN-ENRICH":
        tips.append(
            "Review enrichment and cross-source dependencies in a dry-run before committing full orchestration."
        )
    return tips[:3]


def _common_pitfalls(*, high_complexity: bool) -> list[str]:
    pitfalls = [
        "This card is an auto-generated draft from a single successful job — human review required before reuse.",
        "Do not treat template pre-processing steps as validated production policy without operator approval.",
    ]
    if high_complexity:
        pitfalls[1] = (
            "Multi-stage or cross-reference runs may need tool-chain adjustments not captured in this draft."
        )
    return pitfalls[:2]


def build_skill_card_draft(summary: dict[str, Any]) -> dict[str, Any]:
    """Build skill_card_v0.1 draft dict from an eligible run summary."""
    eligible, reason = is_eligible_for_draft(summary)
    if not eligible:
        raise ValueError(reason)

    identity = summary["identity"]
    job_id = str(identity["job_id"]).strip()
    product_sku = str(identity["product_sku"]).strip()

    high_volume = is_high_volume(summary)
    high_complexity = is_high_complexity(summary)

    outcome = summary.get("outcome")
    qa_status = "pass"
    if isinstance(outcome, dict) and isinstance(outcome.get("qa_status"), str):
        qa_status = outcome["qa_status"].strip()

    draft: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "card_meta": {
            "skill_id": _draft_skill_id(product_sku, job_id),
            "title": f"Draft skill for {product_sku}",
            "derived_from_job_id": job_id,
            "confidence_level": "low",
            "review_status": "draft",
        },
        "scope": {
            "product_sku_scope": product_sku,
        },
        "input_profile": {
            "description": build_input_profile_description(
                summary,
                high_volume=high_volume,
                high_complexity=high_complexity,
            ),
            "complexity_indicators": {
                "is_high_volume": high_volume,
                "is_high_complexity": high_complexity,
            },
        },
        "success_signals": {
            "qa_criteria": {
                "expected_qa_status": "pass",
                "observed_qa_status": qa_status,
            },
        },
        "recommended_actions": {
            "pre_processing": _pre_processing_recommendations(
                product_sku=product_sku,
                high_volume=high_volume,
                high_complexity=high_complexity,
            ),
        },
        "risk_notes": {
            "common_pitfalls": _common_pitfalls(high_complexity=high_complexity),
        },
        "evidence": {
            "sample_job_ids": [job_id],
            "historical_success_rate": 1.0,
            "notes": (
                "Auto-generated draft from one successful run_summary.json. "
                "Requires human review before promotion to skills/cards."
            ),
        },
    }

    runtime_stats = summary.get("runtime_stats")
    if isinstance(runtime_stats, dict) and runtime_stats:
        draft["source_snapshot"] = {
            "runtime_stats": runtime_stats,
            "input_volume": summary.get("input_volume"),
        }

    return draft


def generate_skill_card_draft(
    summary: dict[str, Any],
) -> tuple[bool, dict[str, Any] | None, str]:
    """
    Returns (ok, draft_or_none, message).
    """
    eligible, reason = is_eligible_for_draft(summary)
    if not eligible:
        return False, None, reason
    try:
        draft = build_skill_card_draft(summary)
    except ValueError as exc:
        return False, None, str(exc)
    return True, draft, ""


def _emit_json(
    draft: dict[str, Any],
    *,
    output_path: str | None,
    pretty: bool,
) -> None:
    indent = 2 if pretty else None
    payload = json.dumps(draft, indent=indent, ensure_ascii=False)
    print(payload)
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        text = payload + ("\n" if not pretty else "\n")
        out.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a skill_card_v0.1 draft JSON from a successful run_summary.json",
    )
    parser.add_argument(
        "--run-summary",
        required=True,
        help="Path to run_summary.json (must be qa_status=pass)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write draft JSON (also prints to stdout)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    args = parser.parse_args(argv)

    try:
        summary = load_run_summary(args.run_summary)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    ok, draft, reason = generate_skill_card_draft(summary)
    if not ok or draft is None:
        print(_NOT_ELIGIBLE_MSG, file=sys.stderr)
        if reason:
            print(f"[ERROR] {reason}", file=sys.stderr)
        return 1

    try:
        _emit_json(draft, output_path=args.output, pretty=args.pretty)
    except OSError as exc:
        print(f"[ERROR] failed to write output: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
