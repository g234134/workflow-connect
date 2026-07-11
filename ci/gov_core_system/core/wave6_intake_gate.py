"""
Wave 6 intake gate — entry anti-pollution filter for DATA-CLEANING jobs.

Outputs intake decision + reasons only. Does not read filesystem, DB, or
produce manifest / envelope / QA artifacts. ``suggested_pipeline`` is a
routing hint only; billing truth remains manifest / job_record downstream.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError

from core.intake_decider import decide_intake_gate
from core.intake_phase6_5_mapping import attach_phase6_5_pre_state
from core.schemas.intake import GateCheckItem
from core.schemas.wave6_intake_gate import (
    SKU_TAG_ALIASES,
    SIZE_POLICY_ACK_TAGS,
    SUGGESTED_PIPELINE_HINT,
    VALID_PRODUCT_SKUS,
    IntakeGateFailure,
    IntakeGateRequest,
    IntakeGateResult,
    WAVE6_INTAKE_GATE_SCHEMA_VERSION,
    _ISO639_1_RE,
    _LLM_ASSIST_LEVELS,
    _RISK_SCAN_LEVELS,
)

_ABSOLUTE_PATH_RE = re.compile(
    r"(?:^[a-zA-Z]:[\\/])|(?:^/[a-zA-Z])|(?:\\\\)",
)
_SIZE_POLICY_TEXT_MARKERS = (
    "2097152",
    "2mib",
    "2 mib",
    "2mb",
    "2 mb",
    "2mi",
    "单档上限",
    "單檔上限",
    "size_policy",
)


def _normalize_tag(tag: str) -> str:
    return tag.strip().lower()


def _resolve_product_sku(req: IntakeGateRequest) -> tuple[str | None, str | None, list[GateCheckItem]]:
    """Return (effective_sku, tag_alias_sku, checks)."""
    checks: list[GateCheckItem] = []
    explicit = req.product_sku.strip()
    tag_skus: list[str] = []
    for raw in req.tags:
        mapped = SKU_TAG_ALIASES.get(_normalize_tag(raw))
        if mapped:
            tag_skus.append(mapped)

    tag_sku: str | None = None
    if tag_skus:
        unique = set(tag_skus)
        if len(unique) > 1:
            checks.append(
                GateCheckItem(
                    id="SKU-TAG-CONFLICT",
                    passed=False,
                    detail="sku_tag_conflict",
                )
            )
            return explicit or None, None, checks
        tag_sku = tag_skus[0]

    if explicit and tag_sku and explicit != tag_sku:
        checks.append(
            GateCheckItem(
                id="SKU-TAG-CONFLICT",
                passed=False,
                detail="sku_tag_conflict",
            )
        )
        return explicit, tag_sku, checks

    effective = explicit or tag_sku
    if effective:
        checks.append(
            GateCheckItem(
                id="SKU-PRESENT",
                passed=True,
                detail=f"product_sku={effective}",
            )
        )
    else:
        checks.append(
            GateCheckItem(
                id="SKU-PRESENT",
                passed=False,
                detail="missing_product_sku",
            )
        )
    return effective, tag_sku, checks


def _check_absolute_path(path_hint: str) -> GateCheckItem:
    if not path_hint:
        return GateCheckItem(
            id="ABS-PATH-BAN",
            passed=True,
            detail="inbound_path_hint empty (ok)",
        )
    if _ABSOLUTE_PATH_RE.search(path_hint):
        return GateCheckItem(
            id="ABS-PATH-BAN",
            passed=False,
            detail="absolute_path_forbidden",
        )
    return GateCheckItem(
        id="ABS-PATH-BAN",
        passed=True,
        detail="inbound_path_hint looks relative/logical",
    )


def _validate_enrichment_profile(profile: dict[str, Any] | None) -> GateCheckItem:
    if profile is None:
        return GateCheckItem(
            id="ENRICH-PROFILE",
            passed=False,
            detail="missing_enrichment_profile",
        )

    risk = profile.get("risk_scan_level")
    llm = profile.get("llm_assist")
    if risk not in _RISK_SCAN_LEVELS:
        return GateCheckItem(
            id="ENRICH-PROFILE",
            passed=False,
            detail="invalid_enrichment_profile:risk_scan_level",
        )
    if llm not in _LLM_ASSIST_LEVELS:
        return GateCheckItem(
            id="ENRICH-PROFILE",
            passed=False,
            detail="invalid_enrichment_profile:llm_assist",
        )

    lang = profile.get("language_hint")
    if lang is not None:
        lang_s = str(lang).strip()
        if lang_s and lang_s.lower() != "auto" and _ISO639_1_RE.fullmatch(lang_s) is None:
            return GateCheckItem(
                id="ENRICH-PROFILE",
                passed=False,
                detail="invalid_enrichment_profile:language_hint",
            )

    domain_tags = profile.get("domain_tags")
    if domain_tags is not None:
        if not isinstance(domain_tags, list):
            return GateCheckItem(
                id="ENRICH-PROFILE",
                passed=False,
                detail="invalid_enrichment_profile:domain_tags",
            )
        if len(domain_tags) > 8:
            return GateCheckItem(
                id="ENRICH-PROFILE",
                passed=False,
                detail="invalid_enrichment_profile:domain_tags_count",
            )
        for item in domain_tags:
            if len(str(item).strip()) > 32:
                return GateCheckItem(
                    id="ENRICH-PROFILE",
                    passed=False,
                    detail="invalid_enrichment_profile:domain_tag_length",
                )

    return GateCheckItem(
        id="ENRICH-PROFILE",
        passed=True,
        detail="enrichment_profile valid",
    )


def _check_basic_no_enrich(req: IntakeGateRequest) -> GateCheckItem:
    profile = req.enrichment_profile
    if profile is None:
        return GateCheckItem(
            id="BASIC-NO-ENRICH",
            passed=True,
            detail="no enrichment_profile on BASIC",
        )
    return GateCheckItem(
        id="BASIC-NO-ENRICH",
        passed=False,
        detail="basic_must_not_carry_enrichment_profile",
    )


def _check_batch_hint(batch_size_hint: int | None) -> GateCheckItem | None:
    if batch_size_hint is None:
        return None
    if batch_size_hint >= 1:
        return GateCheckItem(
            id="BATCH-HINT-POSITIVE",
            passed=True,
            detail=f"batch_size_hint={batch_size_hint}",
        )
    return GateCheckItem(
        id="BATCH-HINT-POSITIVE",
        passed=False,
        detail="invalid_batch_size_hint",
    )


def _size_policy_acknowledged(req: IntakeGateRequest) -> bool:
    for tag in req.tags:
        if _normalize_tag(tag) in {_normalize_tag(t) for t in SIZE_POLICY_ACK_TAGS}:
            return True
        if "size_policy" in _normalize_tag(tag) and "ack" in _normalize_tag(tag):
            return True
    hay = req.combined_text().lower()
    return any(marker in hay for marker in _SIZE_POLICY_TEXT_MARKERS)


def _check_size_policy(req: IntakeGateRequest) -> GateCheckItem:
    if _size_policy_acknowledged(req):
        return GateCheckItem(
            id="SIZE-POLICY-DECL",
            passed=True,
            detail="size_policy acknowledged",
        )
    return GateCheckItem(
        id="SIZE-POLICY-DECL",
        passed=False,
        detail="size_policy_not_acknowledged",
    )


def _check_sku_enum(product_sku: str | None) -> GateCheckItem | None:
    if not product_sku:
        return None
    if product_sku in VALID_PRODUCT_SKUS:
        return GateCheckItem(
            id="SKU-ENUM",
            passed=True,
            detail=f"product_sku={product_sku}",
        )
    return GateCheckItem(
        id="SKU-ENUM",
        passed=False,
        detail=f"invalid_product_sku:{product_sku}",
    )


def _enrich_requires_clarification(req: IntakeGateRequest) -> bool:
    if req.product_sku != "CLEAN-ENRICH":
        return False
    profile = req.enrichment_profile or {}
    llm = profile.get("llm_assist")
    domain_tags = profile.get("domain_tags") or []
    if llm == "off" and not domain_tags:
        return True
    return False


def _apply_wave6_phase65_mapping(result: dict[str, Any], req: IntakeGateRequest) -> dict[str, Any]:
    """R2 B.6: product_sku → order line SKU; pipeline → profile tags (not billing SKU)."""
    bundle = result.get("phase6_5_pre_state")
    if not isinstance(bundle, dict) or result.get("decision") != "accept":
        return result

    order = bundle.get("order")
    if isinstance(order, dict):
        mapping = dict(order.get("field_mapping") or {})
        mapping.pop("intake.suggested_pipeline", None)
        mapping.pop("intake.explicit_task_type", None)
        mapping.pop("intake.description", None)
        if req.product_sku:
            mapping["intake.product_sku"] = "order.line_items[0].sku"
        if req.batch_size_hint is not None and req.batch_size_hint > 0:
            mapping["intake.batch_size_hint"] = "order.line_items[0].quantity"
        order["field_mapping"] = mapping
        order["notes"] = (
            "Wave6: billing SKU from intake.product_sku; "
            "suggested_pipeline is routing hint only (tag pipeline:code_cleaning_pipeline_v2)"
        )

    profile = bundle.get("requirement_profile")
    if isinstance(profile, dict):
        mapping = dict(profile.get("field_mapping") or {})
        mapping["intake.suggested_pipeline"] = "requirement_profile.constraints.tags"
        profile["field_mapping"] = mapping

    return result


def _failure_from_validation(exc: ValidationError) -> IntakeGateFailure:
    issues = "; ".join(
        f"{'.'.join(str(x) for x in e.get('loc', ()))}: {e.get('msg', '')}"
        for e in exc.errors()
    )
    return IntakeGateFailure(
        decision="reject",
        work_category="unknown",
        confidence=0.0,
        message=f"reject: intake validation failed: {issues}",
        reasons=["request_shape_invalid"],
        gate_checks=[
            GateCheckItem(id="request_shape", passed=False, detail=issues),
        ],
    )


def run_intake_gate(request: IntakeGateRequest | dict[str, Any]) -> IntakeGateResult | IntakeGateFailure:
    """
    Evaluate whether a structured intake payload may enter Wave 6 data-cleaning.

    Returns accept / defer / reject with audit ``gate_checks`` and ``reasons``.
    """
    try:
        req = request if isinstance(request, IntakeGateRequest) else IntakeGateRequest.model_validate(request)
    except ValidationError as exc:
        return _failure_from_validation(exc)

    checks: list[GateCheckItem] = []
    reasons: list[str] = []
    defer_fields: list[str] = []

    path_check = _check_absolute_path(req.inbound_path_hint)
    checks.append(path_check)
    if not path_check.passed:
        reasons.append("absolute_path_forbidden")
        data = IntakeGateResult(
            decision="reject",
            work_category="unknown",
            confidence=0.95,
            message="reject: inbound_path_hint must not be an absolute disk path",
            gate_checks=checks,
            reasons=reasons,
        ).to_dict()
        data = attach_phase6_5_pre_state(
            data,
            req.to_phase75_request(),
            suggested_pipeline=None,
        )
        return IntakeGateResult.model_validate(_apply_wave6_phase65_mapping(data, req))

    base_out = decide_intake_gate(req.to_phase75_request())
    base_decision = base_out.get("decision", "reject")
    base_category = base_out.get("work_category", "unknown")
    pipeline_passed = base_decision == "accept" and base_category == "data_cleaning"
    checks.append(
        GateCheckItem(
            id="PIPELINE-ANCHOR",
            passed=pipeline_passed,
            detail=f"phase75_decision={base_decision};work_category={base_category}",
        )
    )

    product_sku, _tag_sku, sku_checks = _resolve_product_sku(req)
    checks.extend(sku_checks)

    for item in sku_checks:
        if item.id == "SKU-TAG-CONFLICT" and not item.passed:
            reasons.append("sku_tag_conflict")
            defer_fields.extend(["product_sku", "tags"])
            return _finalize(
                req,
                decision="defer",
                work_category="unknown",
                confidence=0.55,
                message="defer: resolve product_sku vs sku:* tag alias conflict",
                checks=checks,
                reasons=reasons,
                defer_fields=defer_fields,
                base_out=base_out,
            )

    enum_check = _check_sku_enum(product_sku)
    if enum_check is not None:
        checks.append(enum_check)
        if not enum_check.passed:
            reasons.append("invalid_product_sku")
            return _finalize(
                req,
                decision="reject",
                work_category="other" if not pipeline_passed else "data_cleaning",
                confidence=0.9,
                message=f"reject: {enum_check.detail}",
                checks=checks,
                reasons=reasons,
                defer_fields=defer_fields,
                base_out=base_out,
            )

    if product_sku and not pipeline_passed:
        reasons.append("sku_without_cleaning_intent")
        return _finalize(
            req,
            decision="reject",
            work_category="other",
            confidence=0.88,
            message="reject: product_sku present without data-cleaning intent",
            checks=checks,
            reasons=reasons,
            defer_fields=defer_fields,
            base_out=base_out,
        )

    if not pipeline_passed:
        if base_decision == "defer":
            reasons.append("pipeline_anchor_deferred")
            defer_fields.extend(["description", "tags", "explicit_task_type", "file_extension_hints"])
            return _finalize(
                req,
                decision="defer",
                work_category=base_category,
                confidence=float(base_out.get("confidence", 0.45)),
                message=str(base_out.get("message", "defer: clarify data-cleaning scope")),
                checks=checks,
                reasons=reasons,
                defer_fields=_unique(defer_fields),
                base_out=base_out,
            )
        reasons.append("not_data_cleaning")
        return _finalize(
            req,
            decision="reject",
            work_category=base_category,
            confidence=float(base_out.get("confidence", 0.85)),
            message=str(base_out.get("message", "reject: not classified as data-cleaning")),
            checks=checks,
            reasons=reasons,
            defer_fields=defer_fields,
            base_out=base_out,
        )

    batch_check = _check_batch_hint(req.batch_size_hint)
    if batch_check is not None:
        checks.append(batch_check)
        if not batch_check.passed:
            reasons.append("invalid_batch_size_hint")
            defer_fields.append("batch_size_hint")

    size_check = _check_size_policy(req)
    checks.append(size_check)
    if not size_check.passed:
        reasons.append("size_policy_not_acknowledged")
        defer_fields.append("size_policy_acknowledgement")

    if not product_sku:
        reasons.append("missing_product_sku")
        defer_fields.append("product_sku")

    if product_sku == "CLEAN-BASIC":
        basic_check = _check_basic_no_enrich(req)
        checks.append(basic_check)
        if not basic_check.passed:
            reasons.append("basic_must_not_carry_enrichment_profile")
            defer_fields.append("enrichment_profile")

    if product_sku == "CLEAN-ENRICH":
        enrich_check = _validate_enrichment_profile(req.enrichment_profile)
        checks.append(enrich_check)
        if not enrich_check.passed:
            reasons.append("invalid_enrichment_profile")
            defer_fields.append("enrichment_profile")
        elif _enrich_requires_clarification(req):
            checks.append(
                GateCheckItem(
                    id="ENRICH-LLM-OR-DOMAIN",
                    passed=False,
                    detail="enrich_requires_llm_or_domain",
                )
            )
            reasons.append("enrich_requires_llm_or_domain")
            defer_fields.extend(["enrichment_profile.llm_assist", "enrichment_profile.domain_tags"])

    defer_fields = _unique(defer_fields)
    if defer_fields:
        return _finalize(
            req,
            decision="defer",
            work_category="data_cleaning",
            confidence=0.62,
            message="defer: Wave 6 intake requires clarification before accept",
            checks=checks,
            reasons=reasons,
            defer_fields=defer_fields,
            base_out=base_out,
            product_sku=product_sku,
        )

    reasons.append("wave6_intake_accept")
    return _finalize(
        req,
        decision="accept",
        work_category="data_cleaning",
        confidence=min(0.98, float(base_out.get("confidence", 0.85)) + 0.05),
        message="accept: Wave 6 data-cleaning intake",
        checks=checks,
        reasons=reasons,
        defer_fields=[],
        base_out=base_out,
        product_sku=product_sku,
    )


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _finalize(
    req: IntakeGateRequest,
    *,
    decision: str,
    work_category: str,
    confidence: float,
    message: str,
    checks: list[GateCheckItem],
    reasons: list[str],
    defer_fields: list[str],
    base_out: dict[str, Any],
    product_sku: str | None = None,
) -> IntakeGateResult | IntakeGateFailure:
    suggested_task_type = base_out.get("suggested_task_type") if decision == "accept" else None
    suggested_pipeline = SUGGESTED_PIPELINE_HINT if decision == "accept" else None
    suggested_product_sku = product_sku if decision == "accept" else None

    payload: dict[str, Any] = {
        "ok": True,
        "decision": decision,
        "work_category": work_category,
        "confidence": confidence,
        "message": message,
        "suggested_task_type": suggested_task_type,
        "suggested_pipeline": suggested_pipeline,
        "suggested_product_sku": suggested_product_sku,
        "gate_checks": [c.model_dump(mode="json") for c in checks],
        "reasons": reasons,
        "defer_fields_needed": defer_fields,
        "schema_version": WAVE6_INTAKE_GATE_SCHEMA_VERSION,
    }
    payload = attach_phase6_5_pre_state(
        payload,
        req.to_phase75_request(),
        suggested_pipeline=suggested_pipeline,
    )
    payload = _apply_wave6_phase65_mapping(payload, req)

    if decision == "reject" and "request_shape_invalid" in reasons:
        return IntakeGateFailure.model_validate(payload)

    return IntakeGateResult.model_validate(payload)
