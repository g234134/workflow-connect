"""
Phase 7.5 → Phase 6.5 pre-state alignment for intake gate decisions.

Maps ``accept`` / ``defer`` / ``reject`` to lead / requirement_profile / order
statuses and field paths defined in ``phase6_5_entities_v1.json``.
"""

from __future__ import annotations

from typing import Any, Literal

from core.contracts.phase6_5_data_contract import (
    CONTRACT_TIER,
    EventType,
    LeadStatus,
    OrderStatus,
    RequirementProfileStatus,
)
from core.schemas.intake import GateDecisionLiteral, IntakeGateRequest
from shared.naming import PHASE6_5_ENTITIES_SCHEMA_VERSION, PHASE6_5_EVENTS_SCHEMA_VERSION

GateDecision = GateDecisionLiteral


def _hint(
    *,
    entity_type: Literal["lead", "requirement_profile", "order"],
    pre_status: str,
    next_status: str | None,
    next_event_type: str | None,
    field_mapping: dict[str, str],
    notes: str = "",
) -> dict[str, Any]:
    return {
        "entity_type": entity_type,
        "pre_status": pre_status,
        "next_status": next_status,
        "next_event_type": next_event_type,
        "field_mapping": field_mapping,
        "notes": notes,
    }


def _lead_mapping(req: IntakeGateRequest) -> dict[str, str]:
    out = {
        "intake.source_channel": "lead.source",
        "intake.description": "lead.contact_ref",
    }
    if req.tags:
        out["intake.tags"] = "lead.source"
    return out


def _profile_mapping(req: IntakeGateRequest) -> dict[str, str]:
    out = {
        "intake.description": "requirement_profile.summary",
        "intake.tags": "requirement_profile.constraints.tags",
    }
    if req.inbound_path_hint:
        out["intake.inbound_path_hint"] = "requirement_profile.constraints.tags"
    if req.file_extension_hints:
        out["intake.file_extension_hints"] = "requirement_profile.constraints.tags"
    return out


def _order_mapping(req: IntakeGateRequest, *, pipeline_sku: str | None) -> dict[str, str]:
    out: dict[str, str] = {
        "intake.explicit_task_type": "order.line_items[0].sku",
        "intake.suggested_pipeline": "order.line_items[0].sku",
        "intake.description": "order.line_items[0].sku",
    }
    if pipeline_sku:
        out["intake.suggested_pipeline"] = "order.line_items[0].sku"
    if req.batch_size_hint is not None and req.batch_size_hint > 0:
        out["intake.batch_size_hint"] = "order.line_items[0].quantity"
    return out


def build_phase6_5_pre_state(
    decision: GateDecision,
    req: IntakeGateRequest,
    *,
    suggested_pipeline: str | None = None,
) -> dict[str, Any]:
    """
    Build Phase 6.5 entity pre-state bundle for an intake gate decision.

    ``pre_status`` = expected entity status before downstream writes.
    ``next_status`` / ``next_event_type`` = promotion target after gate passes.
    """
    pipeline = suggested_pipeline or "code_cleaning_pipeline_v2"

    if decision == "accept":
        return {
            "contract_tier": CONTRACT_TIER,
            "entities_schema_version": PHASE6_5_ENTITIES_SCHEMA_VERSION,
            "events_schema_version": PHASE6_5_EVENTS_SCHEMA_VERSION,
            "decision": decision,
            "lead": _hint(
                entity_type="lead",
                pre_status=LeadStatus.DRAFT.value,
                next_status=LeadStatus.QUALIFIED.value,
                next_event_type=EventType.LEAD_QUALIFIED.value,
                field_mapping=_lead_mapping(req),
                notes="Gate accept: promote lead draft→qualified before factory/dark.data routing",
            ),
            "requirement_profile": _hint(
                entity_type="requirement_profile",
                pre_status=RequirementProfileStatus.DRAFT.value,
                next_status=RequirementProfileStatus.ACTIVE.value,
                next_event_type=EventType.REQUIREMENT_PROFILE_CREATED.value,
                field_mapping=_profile_mapping(req),
                notes="Materialize active profile from intake summary/constraints",
            ),
            "order": _hint(
                entity_type="order",
                pre_status=OrderStatus.DRAFT.value,
                next_status=OrderStatus.DRAFT.value,
                next_event_type=None,
                field_mapping=_order_mapping(req, pipeline_sku=pipeline),
                notes="Order remains draft until explicit order.placed (downstream wave)",
            ),
            "authority": _authority_block(),
        }

    if decision == "defer":
        return {
            "contract_tier": CONTRACT_TIER,
            "entities_schema_version": PHASE6_5_ENTITIES_SCHEMA_VERSION,
            "events_schema_version": PHASE6_5_EVENTS_SCHEMA_VERSION,
            "decision": decision,
            "lead": _hint(
                entity_type="lead",
                pre_status=LeadStatus.DRAFT.value,
                next_status=LeadStatus.DRAFT.value,
                next_event_type=EventType.LEAD_CREATED.value,
                field_mapping=_lead_mapping(req),
                notes="Hold in draft; emit lead.created only after clarification",
            ),
            "requirement_profile": None,
            "order": None,
            "authority": _authority_block(),
        }

    # reject (includes validation failures)
    return {
        "contract_tier": CONTRACT_TIER,
        "entities_schema_version": PHASE6_5_ENTITIES_SCHEMA_VERSION,
        "events_schema_version": PHASE6_5_EVENTS_SCHEMA_VERSION,
        "decision": decision,
        "lead": _hint(
            entity_type="lead",
            pre_status=LeadStatus.DRAFT.value,
            next_status=LeadStatus.ARCHIVED.value,
            next_event_type=EventType.LEAD_ARCHIVED.value,
            field_mapping=_lead_mapping(req),
            notes="Gate reject: archive lead without opening cleaning pipeline",
        ),
        "requirement_profile": _hint(
            entity_type="requirement_profile",
            pre_status=RequirementProfileStatus.DRAFT.value,
            next_status=RequirementProfileStatus.CLOSED.value,
            next_event_type=None,
            field_mapping=_profile_mapping(req),
            notes="Profile not activated; closed without order placement",
        ),
        "order": _hint(
            entity_type="order",
            pre_status=OrderStatus.DRAFT.value,
            next_status=OrderStatus.CANCELLED.value,
            next_event_type=EventType.ORDER_CANCELLED.value,
            field_mapping=_order_mapping(req, pipeline_sku=None),
            notes="Cancel draft order path; no order.placed",
        ),
        "authority": _authority_block(),
    }


def _authority_block() -> dict[str, str]:
    return {
        "entities_json": "shared/schemas/phase6_5_entities_v1.json",
        "events_json": "shared/schemas/phase6_5_events_v1.json",
        "python_contract": "core.contracts.phase6_5_data_contract",
    }


def attach_phase6_5_pre_state(
    result: dict[str, Any],
    req: IntakeGateRequest,
    *,
    suggested_pipeline: str | None = None,
) -> dict[str, Any]:
    """Attach ``phase6_5_pre_state`` to an intake gate result dict."""
    decision = result.get("decision")
    if decision not in ("accept", "defer", "reject"):
        decision = "reject"
    pipeline = suggested_pipeline or result.get("suggested_pipeline")
    result["phase6_5_pre_state"] = build_phase6_5_pre_state(
        decision,  # type: ignore[arg-type]
        req,
        suggested_pipeline=pipeline,
    )
    return result
