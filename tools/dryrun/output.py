"""Write per-record JSONL and markdown summary for dry-run reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.dryrun.core import DISCLAIMER


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_per_record_jsonl(rows: list[dict[str, Any]], output_dir: Path, stamp: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{stamp}_per_record.jsonl"
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def write_summary_markdown(
    rows: list[dict[str, Any]],
    output_dir: Path,
    stamp: str,
    *,
    input_paths: list[Path],
    min_score: float,
    aggregate_gate: dict[str, Any] | None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{stamp}_summary.md"

    total = len(rows)
    matches = sum(1 for r in rows if r.get("verdict_match"))
    match_ratio = (matches / total) if total else 0.0
    mismatches = [r for r in rows if not r.get("verdict_match")]

    rule_counts: dict[str, int] = {}
    for row in rows:
        rule = str(row.get("dryrun_rule") or "edge_unknown")
        rule_counts[rule] = rule_counts.get(rule, 0) + 1

    lines: list[str] = [
        f"# Dry-run summary — {stamp}",
        "",
        f"> {DISCLAIMER}",
        "",
        "## Inputs",
        "",
    ]
    if input_paths:
        for p in input_paths:
            lines.append(f"- `{p.as_posix()}`")
    else:
        lines.append("- _(none)_")
    lines.extend(
        [
            "",
            f"- **min_score** (gate_ok_score_high threshold): `{min_score}`",
            "",
            "## Totals",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total records | {total} |",
            f"| Verdict matches | {matches} |",
            f"| Match ratio | {match_ratio:.1%} |",
            f"| Mismatches | {len(mismatches)} |",
            "",
            "### Rule distribution",
            "",
            "| dryrun_rule | count |",
            "|-------------|-------|",
        ]
    )
    for rule in sorted(rule_counts):
        lines.append(f"| {rule} | {rule_counts[rule]} |")

    if aggregate_gate:
        lines.extend(
            [
                "",
                "### Aggregate gate artefact (read-only snapshot)",
                "",
                f"- source: `{aggregate_gate.get('source_file')}`",
                f"- ok: `{aggregate_gate.get('ok')}`",
                f"- verdict: `{aggregate_gate.get('verdict')}`",
                f"- eval_message: {aggregate_gate.get('eval_message') or '—'}",
            ]
        )

    lines.extend(
        [
            "",
            "## Mismatch list",
            "",
        ]
    )
    if not mismatches:
        lines.append("_No mismatches._")
    else:
        lines.append("| task_id | actual | ideal | dryrun_rule |")
        lines.append("|---------|--------|-------|-------------|")
        for row in mismatches:
            lines.append(
                f"| {row.get('task_id')} | {row.get('actual_verdict')} | "
                f"{row.get('ideal_verdict')} | {row.get('dryrun_rule')} |"
            )

    lines.extend(
        [
            "",
            "## Disclaimer",
            "",
            DISCLAIMER,
            "",
            "Governance rules here are an **approximation** of eval_gate + rollout gate semantics.",
            "They do not replace G10 rulebook or production CI thresholds.",
            "See ticket `W5-A-RUNTIME-01-DRYRUN` plan §4.2 for known deviations.",
            "",
        ]
    )

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def emit_reports(
    rows: list[dict[str, Any]],
    output_dir: Path,
    *,
    input_paths: list[Path],
    min_score: float,
    aggregate_gate: dict[str, Any] | None,
) -> tuple[Path, Path, str]:
    stamp = _utc_stamp()
    jsonl_path = write_per_record_jsonl(rows, output_dir, stamp)
    md_path = write_summary_markdown(
        rows,
        output_dir,
        stamp,
        input_paths=input_paths,
        min_score=min_score,
        aggregate_gate=aggregate_gate,
    )
    return jsonl_path, md_path, stamp
