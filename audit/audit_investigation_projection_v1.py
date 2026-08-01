"""Audit investigation view projection (WB-T5 spec §2.4 · WC-PRE-04).

Pure-function wire → investigation dict; read-only; no filesystem I/O.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _namespace_prefix_from_source_kind(source_kind: Optional[str]) -> str:
    mapping = {
        "agent_ci": "agent_ci",
        "agent_experiment_regression": "agent_experiment_regression",
        "non_tabular_experiment": "non_tabular_experiment",
    }
    return mapping.get(source_kind or "", "unknown")


def _fixture_maturity(wire: Dict[str, Any]) -> str:
    run = wire.get("latest_run") or {}
    source_kind = run.get("source_kind")
    if source_kind == "non_tabular_experiment":
        return "sandbox"
    sandbox = wire.get("sandbox_delivery") or {}
    if sandbox.get("found"):
        return "sandbox"
    if run.get("flow_family") == "non_tabular":
        return "sandbox"
    if run.get("mode") == "preview":
        return "experimental"
    case_ref = wire.get("case_ref") or ""
    if case_ref in ("demo_phase", "sampleco/2026-0001") and run.get("found"):
        return "stable"
    return "unknown"


def project_audit_investigation_view(
    wire: Dict[str, Any],
    *,
    case_history: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Deterministic wire → investigation projection per spec §2.4."""
    run = wire.get("latest_run") or {}
    source_kind = run.get("source_kind")
    ns = _namespace_prefix_from_source_kind(source_kind)
    maturity = _fixture_maturity(wire)
    artifact_path = run.get("artifact_path")

    def _section(
        section_id: str,
        step_ids: List[str],
        found: bool,
        summary: Dict[str, Any],
        source_paths: List[str],
        namespace_prefix: str,
    ) -> Dict[str, Any]:
        return {
            "section_id": section_id,
            "step_ids": step_ids,
            "found": found,
            "fixture_maturity": maturity,
            "namespace_prefix": namespace_prefix,
            "summary": summary,
            "source_paths": [p for p in source_paths if p],
        }

    sections: List[Dict[str, Any]] = [
        _section(
            "latest_run",
            ["S1", "S2"],
            bool(run.get("found")),
            {k: run.get(k) for k in ("found", "source_kind", "mode", "final_status", "task_type")},
            [artifact_path] if artifact_path else [],
            ns,
        ),
        _section(
            "decision",
            ["S3"],
            wire.get("decision", {}).get("decision") is not None,
            dict(wire.get("decision") or {}),
            [artifact_path] if artifact_path else [],
            ns,
        ),
        _section(
            "planned_route",
            ["S5", "S6"],
            bool((wire.get("planned_route") or {}).get("planned_tools"))
            or (wire.get("planned_route") or {}).get("selector_task_type") is not None,
            dict(wire.get("planned_route") or {}),
            [artifact_path] if artifact_path else [],
            ns,
        ),
    ]

    for cp_key, section_id, step_id in (
        ("checkpoint_a", "checkpoint_a", "S4"),
        ("checkpoint_b", "checkpoint_b", "S12"),
    ):
        cp = wire.get(cp_key) or {}
        cp_path = cp.get("checkpoint_path")
        sections.append(
            _section(
                section_id,
                [step_id],
                bool(cp.get("status") or cp.get("on_disk") or cp.get("would_trigger") is not None),
                dict(cp),
                [cp_path] if cp_path else [],
                f"outbox/{wire.get('case_ref')}/",
            )
        )

    delivery = wire.get("delivery_approval")
    sections.append(
        _section(
            "delivery_approval",
            ["S13"],
            delivery is not None,
            dict(delivery) if delivery else {},
            [
                (wire.get("checkpoint_b") or {}).get("checkpoint_path") or "",
            ],
            f"outbox/{wire.get('case_ref')}/",
        )
    )

    sandbox = wire.get("sandbox_delivery")
    if sandbox:
        sections.append(
            _section(
                "sandbox_delivery",
                ["S10", "S11"],
                bool(sandbox.get("found")),
                dict(sandbox),
                [sandbox.get("artifact_path") or ""],
                "sandbox_delivery",
            )
        )

    wf_notif = wire.get("workflow_notifications") or {}
    wf_events = wf_notif.get("events") or []
    wf_source_paths = [
        p for row in wf_events if (p := row.get("source_path") or row.get("ack_path"))
    ]
    wf_summary = {
        "count": wf_notif.get("count", len(wf_events)),
        "pending_ack_count": wf_notif.get("pending_ack_count", 0),
        "failed_ack_count": wf_notif.get("failed_ack_count", 0),
        "count_by_event_type": wf_notif.get("count_by_event_type") or {},
        "streams_read": wf_notif.get("streams_read") or [],
    }
    sections.append(
        _section(
            "workflow_notifications",
            ["S4", "S10", "S12", "S14"],
            bool(wf_notif.get("found") or wf_events),
            wf_summary,
            wf_source_paths,
            "outbox/notifications/",
        )
    )

    timeline: List[Dict[str, Any]] = []
    if run.get("found"):
        timeline.append(
            {
                "step_id": "S3",
                "event_kind": "agent_run",
                "timestamp": run.get("artifact_timestamp"),
                "source_path": artifact_path,
                "namespace_prefix": ns,
                "summary": f"latest run from {source_kind}",
            }
        )
    decision = wire.get("decision") or {}
    if decision.get("decision"):
        timeline.append(
            {
                "step_id": "S3",
                "event_kind": "decision",
                "timestamp": run.get("artifact_timestamp"),
                "source_path": artifact_path,
                "namespace_prefix": ns,
                "summary": f"decision={decision.get('decision')}",
            }
        )
    route = wire.get("planned_route") or {}
    if route.get("planned_tools") or route.get("selector_task_type"):
        timeline.append(
            {
                "step_id": "S5",
                "event_kind": "route_planned",
                "timestamp": run.get("artifact_timestamp"),
                "source_path": artifact_path,
                "namespace_prefix": ns,
                "summary": "planned route assembled",
            }
        )
    for cp_key, step_id, kind in (
        ("checkpoint_a", "S4", "checkpoint_a"),
        ("checkpoint_b", "S12", "checkpoint_b"),
    ):
        cp = wire.get(cp_key) or {}
        if cp.get("status") or cp.get("on_disk"):
            timeline.append(
                {
                    "step_id": step_id,
                    "event_kind": kind,
                    "timestamp": cp.get("checkpoint_timestamp"),
                    "source_path": cp.get("checkpoint_path"),
                    "namespace_prefix": f"outbox/{wire.get('case_ref')}/",
                    "summary": f"status={cp.get('status')}",
                }
            )
    if delivery:
        timeline.append(
            {
                "step_id": "S13",
                "event_kind": "delivery_approval",
                "timestamp": delivery.get("timestamp"),
                "source_path": (wire.get("checkpoint_b") or {}).get("checkpoint_path"),
                "namespace_prefix": f"outbox/{wire.get('case_ref')}/",
                "summary": f"action={delivery.get('action')}",
            }
        )
    for row in wf_events:
        if row.get("source_stream") != "notification":
            continue
        step_id = row.get("source_step") or "S14"
        tracking = row.get("tracking_status") or "recorded"
        timeline.append(
            {
                "step_id": step_id,
                "event_kind": "workflow_notification",
                "timestamp": row.get("emitted_at"),
                "source_path": row.get("source_path") or row.get("ack_path"),
                "namespace_prefix": "outbox/notifications/",
                "summary": (
                    f"{row.get('event_type')} tracking={tracking}"
                    + (f" error={row.get('last_error')}" if row.get("last_error") else "")
                ),
                "event_id": row.get("native_id"),
                "tracking_status": tracking,
            }
        )

    timeline.sort(key=lambda e: (e.get("timestamp") or "", e.get("step_id") or ""))

    gaps: List[Dict[str, Any]] = []
    if not run.get("found"):
        gaps.append(
            {
                "gap_id": "missing_run_artifact",
                "step_ids": ["S3", "S4", "S5", "S6"],
                "reason": "no agent-line run artifact matched case_ref",
                "severity": "warning",
            }
        )
    cp_a = wire.get("checkpoint_a") or {}
    if cp_a.get("would_trigger") and not cp_a.get("on_disk"):
        gaps.append(
            {
                "gap_id": "missing_checkpoint_a_on_disk",
                "step_ids": ["S4"],
                "reason": "checkpoint A would trigger but no on-disk JSON",
                "severity": "info",
            }
        )
    cp_b = wire.get("checkpoint_b") or {}
    if cp_b.get("would_trigger") and not cp_b.get("on_disk"):
        gaps.append(
            {
                "gap_id": "missing_checkpoint_b_on_disk",
                "step_ids": ["S12"],
                "reason": "checkpoint B would trigger but no on-disk JSON",
                "severity": "warning",
            }
        )
    if cp_b.get("status") in ("approved", "auto_approved") and not delivery:
        gaps.append(
            {
                "gap_id": "missing_delivery_approval",
                "step_ids": ["S13"],
                "reason": "checkpoint B approved path without delivery_approval block",
                "severity": "info",
            }
        )
    if case_history is not None and not case_history.get("ok"):
        gaps.append(
            {
                "gap_id": "case_not_in_index",
                "step_ids": ["S2"],
                "reason": "case_ref absent from cases/index.json",
                "severity": "info",
            }
        )

    for row in wf_events:
        if row.get("source_stream") != "notification":
            continue
        event_id = row.get("native_id")
        tracking = row.get("tracking_status")
        if tracking == "pending_ack":
            gaps.append(
                {
                    "gap_id": "missing_downstream_ack",
                    "step_ids": [row.get("source_step") or "S14"],
                    "reason": (
                        f"notification event {event_id} ({row.get('event_type')}) "
                        "has no downstream ack"
                    ),
                    "severity": "warning",
                    "event_id": event_id,
                }
            )
        elif tracking == "failed":
            gaps.append(
                {
                    "gap_id": "downstream_ack_failed",
                    "step_ids": [row.get("source_step") or "S14"],
                    "reason": (
                        f"downstream ack failed for event {event_id}: "
                        f"{row.get('last_error') or 'unknown error'}"
                    ),
                    "severity": "warning",
                    "event_id": event_id,
                }
            )

    audit_sections_found = sum(1 for s in sections if s.get("found"))
    view: Dict[str, Any] = {
        "ok": wire.get("ok", False),
        "read_only": True,
        "schema_version": "audit_investigation_view_v1",
        "case_ref": wire.get("case_ref"),
        "sections": sections,
        "timeline": timeline,
        "gaps": gaps,
        "audit_sections_found": audit_sections_found,
        "audit_gaps_count": len(gaps),
        "message": wire.get("message", ""),
    }
    if case_history is not None:
        view["case_history"] = case_history
    return view
