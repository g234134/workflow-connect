"""
Governance dry-run: parse local artefacts and compute ideal vs actual verdicts.

Self-contained minimal rules (approximation of eval_gate + rollout gate semantics).
Does not import observability.* to avoid coupling and keep this ticket add-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final, Iterable, Iterator, Literal

DISCLAIMER: Final[str] = (
    "⚠ DRY-RUN — 不影響任何 CI/pipeline 決策；本報表僅供人工驗證治理近似規則。"
)

IdealVerdict = Literal["allow", "warn", "deny", "unknown"]
ActualVerdict = Literal["allow", "warn", "fail", "unknown"]
DryrunRule = Literal[
    "gate_ok_score_high",
    "gate_ok_score_low",
    "gate_fail_deny",
    "gate_fail_needs_review",
    "edge_unknown",
]

INFRA_ERROR_TYPES: Final[frozenset[str]] = frozenset({"context_overflow", "timeout"})
HIGH_RETRY_THRESHOLD: Final[int] = 2
TRACE_LOW_DEFAULT: Final[float] = 0.8

EVAL_EXPORT_GLOBS: Final[tuple[str, ...]] = (
    "shadow_eval_results*.jsonl",
    "*eval_results*.jsonl",
    "*eval_export*.jsonl",
)
IBRIDGE_GLOBS: Final[tuple[str, ...]] = (
    "shadow_ibridge_records*.jsonl",
    "*ibridge_records*.jsonl",
)
GATE_STATE_GLOBS: Final[tuple[str, ...]] = (
    "shadow_state.json",
    "*gate*verdict*.json",
    "*gate_verdict*.json",
)


def discover_input_paths(input_path: Path) -> list[Path]:
    """Resolve explicit file or directory into artefact paths (eval export preferred)."""
    if input_path.is_file():
        return [input_path]

    found: list[Path] = []
    if not input_path.is_dir():
        return found

    for pattern in EVAL_EXPORT_GLOBS:
        found.extend(sorted(input_path.glob(pattern)))
    for pattern in IBRIDGE_GLOBS:
        for p in sorted(input_path.glob(pattern)):
            if p not in found:
                found.append(p)
    for pattern in GATE_STATE_GLOBS:
        for p in sorted(input_path.rglob(pattern)):
            if p.is_file() and p not in found:
                found.append(p)
    return found


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if isinstance(row, dict):
                yield row


def _normalize_export_row(row: dict[str, Any], *, source_file: str) -> dict[str, Any]:
    """Ensure eval_export-shaped dict for downstream rules."""
    if row.get("schema_version") == "eval_export/v1" or "gate_result" in row:
        out = dict(row)
        out["_source_file"] = source_file
        out["_record_kind"] = "eval_export"
        return out

    metrics = {
        "success": row.get("success"),
        "retry_count": row.get("retry_count", 0),
        "handoff_count": row.get("handoff_count", 0),
        "error_type": row.get("error_type"),
        "context_tokens_total": (row.get("context_token_usage") or {}).get("total_tokens", 0),
        "trace_completeness_score": (row.get("trace_completeness") or {}).get("score"),
    }
    gate_result, synthetic_tags, reasons = _synthetic_gate_from_metrics(metrics, row)
    original_tags = list(row.get("tags") or [])
    synthetic_tag_list = list(synthetic_tags or [])
    final_tags = sorted(set(original_tags) | set(synthetic_tag_list))
    return {
        "schema_version": "dryrun/ibridge-derived",
        "task_id": row.get("task_id"),
        "trace_id": row.get("trace_id"),
        "gate_result": gate_result,
        "tags": final_tags,
        "_synthetic_tags": synthetic_tag_list,
        "reasons": reasons,
        "metrics": metrics,
        "_source_file": source_file,
        "_record_kind": "ibridge",
    }


def _synthetic_gate_from_metrics(
    metrics: dict[str, Any],
    row: dict[str, Any],
) -> tuple[str, list[str], list[str]]:
    """Minimal eval_gate-like pass/needs_review (not identical to observability.eval_gate)."""
    tags: list[str] = []
    reasons: list[str] = []
    retry = int(metrics.get("retry_count") or 0)
    handoff = int(metrics.get("handoff_count") or 0)
    error_type = metrics.get("error_type")
    score = metrics.get("trace_completeness_score")

    if retry >= HIGH_RETRY_THRESHOLD:
        tags.append("high_retry")
        reasons.append(f"retry_count={retry} >= {HIGH_RETRY_THRESHOLD}")
    if handoff >= 3:
        tags.append("many_handoffs")
        reasons.append(f"handoff_count={handoff} >= 3")
    if error_type in INFRA_ERROR_TYPES:
        tags.append("infra_risk")
        reasons.append(f"error_type={error_type}")
    if score is not None and float(score) < TRACE_LOW_DEFAULT:
        tags.append("observability_gap")
        reasons.append(f"trace_completeness_score={score} < {TRACE_LOW_DEFAULT}")

    gate_result = "pass" if not tags else "needs_review"
    if metrics.get("success") is False and "infra_risk" not in tags:
        tags.append("infra_risk")
        reasons.append("success=false")
    return gate_result, tags, reasons


def load_records_from_paths(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """
    Load per-task records; dedupe by task_id (eval_export wins over ibridge).

    Returns (records, optional_aggregate_gate_state).
    """
    by_task: dict[str, dict[str, Any]] = {}
    aggregate_gate: dict[str, Any] | None = None

    for path in paths:
        if not path.exists():
            continue
        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            for row in _iter_jsonl(path):
                normalized = _normalize_export_row(row, source_file=path.name)
                task_id = normalized.get("task_id")
                if not task_id:
                    continue
                existing = by_task.get(str(task_id))
                if existing is None or existing.get("_record_kind") != "eval_export":
                    if normalized.get("_record_kind") == "eval_export" or existing is None:
                        by_task[str(task_id)] = normalized
        elif suffix == ".json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and (
                "ok" in payload or "verdict" in payload or "eval_message" in payload
            ):
                aggregate_gate = {
                    "source_file": path.name,
                    "ok": payload.get("ok"),
                    "verdict": payload.get("verdict"),
                    "eval_message": payload.get("eval_message"),
                    "phase": payload.get("phase"),
                }

    return list(by_task.values()), aggregate_gate


def _trace_score(record: dict[str, Any]) -> float | None:
    metrics = record.get("metrics") or {}
    raw = metrics.get("trace_completeness_score")
    if raw is not None:
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None
    tc = record.get("trace_completeness")
    if isinstance(tc, dict) and tc.get("score") is not None:
        try:
            return float(tc["score"])
        except (TypeError, ValueError):
            return None
    return None


def map_actual_verdict(record: dict[str, Any]) -> ActualVerdict:
    """Map artefact fields to rollout-style actual verdict bucket."""
    explicit = record.get("verdict") or record.get("actual_verdict")
    if isinstance(explicit, str) and explicit.strip():
        v = explicit.strip().lower()
        if v in ("allow", "pass", "approve"):
            return "allow"
        if v in ("deny", "fail", "rejected", "blocked"):
            return "fail"
        if v in ("warn", "needs_review", "require-human-override", "review"):
            return "warn"
        if v == "unknown":
            return "unknown"

    metrics = record.get("metrics") or {}
    success = metrics.get("success")
    if success is False:
        return "fail"

    gate_result = (record.get("gate_result") or "").lower()
    if gate_result == "needs_review":
        return "warn"
    if gate_result == "pass":
        return "allow"
    return "unknown"


def compute_ideal_verdict(
    record: dict[str, Any],
    *,
    min_score: float = 0.875,
) -> tuple[IdealVerdict, DryrunRule]:
    """
    Simplified governance buckets (W5-A-RUNTIME-01-DRYRUN plan §4.1 approximation).
    """
    task_id = record.get("task_id")
    if not task_id:
        return "unknown", "edge_unknown"

    metrics = record.get("metrics") or {}
    tags = list(record.get("tags") or [])
    gate_result = (record.get("gate_result") or "").lower()
    success = metrics.get("success")
    error_type = metrics.get("error_type")
    score = _trace_score(record)

    if success is False or "infra_risk" in tags or error_type in INFRA_ERROR_TYPES:
        return "deny", "gate_fail_deny"

    if gate_result == "needs_review" or tags:
        return "warn", "gate_fail_needs_review"

    if gate_result == "pass":
        if score is None:
            return "unknown", "edge_unknown"
        if score >= min_score:
            return "allow", "gate_ok_score_high"
        return "warn", "gate_ok_score_low"

    return "unknown", "edge_unknown"


def verdicts_match(actual: ActualVerdict, ideal: IdealVerdict) -> bool:
    if actual == ideal:
        return True
    if actual == "fail" and ideal == "deny":
        return True
    return False


def build_comparison_rows(
    records: Iterable[dict[str, Any]],
    *,
    min_score: float = 0.875,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        actual = map_actual_verdict(record)
        verdict_record = record
        if "_synthetic_tags" in record:
            verdict_record = {**record, "tags": record.get("_synthetic_tags") or []}
        ideal, rule = compute_ideal_verdict(verdict_record, min_score=min_score)
        metrics = record.get("metrics") or {}
        rows.append(
            {
                "task_id": record.get("task_id"),
                "trace_id": record.get("trace_id"),
                "actual_verdict": actual,
                "ideal_verdict": ideal,
                "verdict_match": verdicts_match(actual, ideal),
                "dryrun_rule": rule,
                "gate_result": record.get("gate_result"),
                "tags": record.get("tags") or [],
                "metrics": {
                    "success": metrics.get("success"),
                    "retry_count": metrics.get("retry_count"),
                    "handoff_count": metrics.get("handoff_count"),
                    "error_type": metrics.get("error_type"),
                    "trace_completeness_score": metrics.get("trace_completeness_score"),
                },
                "source_file": record.get("_source_file"),
            }
        )
    rows.sort(key=lambda r: str(r.get("task_id") or ""))
    return rows
