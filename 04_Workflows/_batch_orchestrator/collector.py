"""Aggregate mock ExecutionResult lists into BatchResult (BATCH-MVP-04)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from .runner_mock import ExecutionResult


@dataclass
class BatchResult:
    """Batch-level aggregation of per-subtask ExecutionResult rows."""

    batch_id: str
    summary: dict[str, int]
    subtask_results: list[dict[str, Any]] = field(default_factory=list)
    ok: bool = True
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _result_as_dict(item: ExecutionResult | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(item, ExecutionResult):
        return item.to_dict()
    if isinstance(item, Mapping):
        return dict(item)
    return {
        "subtask_id": "invalid",
        "ok": False,
        "status": "failed",
        "message": "result must be ExecutionResult or mapping",
        "error": "invalid result type",
    }


def _status_bucket(status: str, ok: bool) -> str:
    normalized = (status or "").strip().lower()
    if normalized in ("success", "failed", "blocked", "timeout"):
        return normalized
    return "success" if ok else "failed"


def collect_results(
    results: list[ExecutionResult] | Sequence[ExecutionResult | Mapping[str, Any]],
    *,
    batch_id: str | None = None,
) -> BatchResult:
    """Aggregate ExecutionResult rows into a BatchResult.

    BatchResult contains at least:
      batch_id, summary (total/success/failed/blocked/timeout), subtask_results
    """
    rows = [_result_as_dict(item) for item in (results or [])]
    summary = {
        "total": len(rows),
        "success": 0,
        "failed": 0,
        "blocked": 0,
        "timeout": 0,
    }
    for row in rows:
        bucket = _status_bucket(str(row.get("status") or ""), bool(row.get("ok")))
        row["status"] = bucket
        summary[bucket] = summary.get(bucket, 0) + 1

    resolved_id = (batch_id or "").strip() or "batch-mock"
    all_ok = summary["failed"] == 0 and summary["blocked"] == 0 and summary["timeout"] == 0
    message = (
        f"collected {summary['total']} result(s): "
        f"success={summary['success']} failed={summary['failed']} "
        f"blocked={summary['blocked']} timeout={summary['timeout']}"
    )
    return BatchResult(
        batch_id=resolved_id,
        summary=summary,
        subtask_results=rows,
        ok=all_ok and summary["total"] > 0,
        message=message,
    )
