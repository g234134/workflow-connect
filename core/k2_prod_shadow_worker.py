"""
K-2 Phase 1 prod shadow worker (repo-root entry).

Runs ask snapshot + K-2 flow + merge in an isolated process (subprocess from
``gov_core_system`` ``/api/ask`` hook). Appends one JSONL line to the shadow spool.

Not wired to ``/api/ask`` directly — invoked via ``core.k2_prod_shadow_worker_cli``.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ENV_K2_SHADOW_SPOOL = "K2_SHADOW_SPOOL_FILENAME"
DEFAULT_SPOOL_FILENAME = "k2_shadow_spool.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_shadow_spool_path(*, repo_root: Path | None = None) -> Path:
    """Shadow spool under ``artifacts/eval`` (or ``IBRIDGE_EXPORT_ROOT``)."""
    from observability.ibridge_exporter import resolve_artifact_dir

    name = os.environ.get(ENV_K2_SHADOW_SPOOL, "").strip() or DEFAULT_SPOOL_FILENAME
    artifact_dir = resolve_artifact_dir(repo_root=repo_root)
    return artifact_dir / name


def _build_spool_line(
    *,
    ask_snapshot: Mapping[str, Any],
    query: str,
    top_k: int,
    thread_id: str | None,
    session_id: str | None,
    k2_out: Mapping[str, Any],
    merged: Mapping[str, Any],
    comparison: Mapping[str, Any],
) -> dict[str, Any]:
    k2_record = k2_out.get("record") if isinstance(k2_out.get("record"), dict) else {}
    task_id = str(k2_out.get("task_id") or k2_record.get("task_id") or f"prod-shadow-{uuid.uuid4().hex[:12]}")
    trace_id = str(k2_record.get("trace_id") or uuid.uuid4().hex)
    end_time = k2_record.get("end_time") or k2_record.get("timestamp") or _utc_now_iso()

    line: dict[str, Any] = {
        "schema": "k2_prod_shadow/v1",
        "task_id": task_id,
        "trace_id": trace_id,
        "end_time": end_time,
        "timestamp": end_time,
        "case_name": f"prod-{task_id}",
        "query": query,
        "top_k": top_k,
        "thread_id": thread_id,
        "session_id": session_id,
        "primary_source": "ask",
        "ask_summary": comparison.get("ask_summary"),
        "k2_summary": comparison.get("k2_summary"),
        "merge_safe": comparison.get("merge_safe"),
        "classification": comparison.get("classification"),
        "k2_merge": merged.get("k2_merge"),
    }
    kmr = merged.get("k2_metrics_record")
    if isinstance(kmr, dict):
        line["k2_metrics_record"] = dict(kmr)
    elif k2_record:
        line["k2_metrics_record"] = dict(k2_record)
    return line


def append_shadow_spool_line(line: dict[str, Any], *, spool_path: Path | None = None) -> dict[str, Any]:
    """Append one JSON object line to the shadow spool (creates parent dirs)."""
    path = spool_path or resolve_shadow_spool_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(line, ensure_ascii=False, default=str)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(payload + "\n")
    return {"ok": True, "message": "spool line appended", "spool_path": str(path)}


def execute_prod_shadow_from_ask(
    ask_snapshot: Mapping[str, Any],
    *,
    query: str,
    top_k: int,
    thread_id: str | None = None,
    session_id: str | None = None,
    spool_path: Path | None = None,
) -> dict[str, Any]:
    """
    Run K-2 + merge against a frozen ask snapshot; append spool line.

    Intended for subprocess isolation — normal repo-root ``core`` imports apply.
    """
    from core.k2_ask_shadow import (
        build_shadow_task_input,
        compare_shadow_profiles,
        map_task_input_for_k2,
        summarize_ask_output,
        summarize_k2_output,
    )
    from core.k2_merge_adapter import merge_ask_and_k2
    from core.langgraph_flow_k2 import run_k2_flow

    base_id = f"prod-shadow-{uuid.uuid4().hex[:10]}"
    task_input = build_shadow_task_input(
        task_id=f"{base_id}-shared",
        query=query,
        top_k=top_k,
        thread_id=thread_id,
        session_id=session_id,
    )
    k2_ti = map_task_input_for_k2(task_input, default_goal=query)
    k2_task_id = f"{base_id}-k2"

    k2_out = run_k2_flow(
        task_id=k2_task_id,
        goal=query,
        task_input=k2_ti,
    )
    merged = merge_ask_and_k2(
        ask_snapshot,
        k2_out,
        query=query,
        top_k=top_k,
        include_eval_in_envelope=True,
    )
    ask_summary = summarize_ask_output(ask_snapshot)
    k2_summary = summarize_k2_output(k2_out)
    comparison = compare_shadow_profiles(
        ask_summary,
        k2_summary,
        case_name=f"prod-{k2_task_id}",
    )

    line = _build_spool_line(
        ask_snapshot=ask_snapshot,
        query=query,
        top_k=top_k,
        thread_id=thread_id,
        session_id=session_id,
        k2_out={**k2_out, "task_id": k2_task_id},
        merged=merged,
        comparison=comparison,
    )
    spool_result = append_shadow_spool_line(line, spool_path=spool_path)

    return {
        "ok": True,
        "message": "prod shadow worker completed",
        "merge_safe": comparison.get("merge_safe"),
        "classification": comparison.get("classification"),
        "k2_ok": k2_out.get("ok"),
        "ask_ok": ask_snapshot.get("ok"),
        "primary_source": "ask",
        "spool": spool_result,
    }
