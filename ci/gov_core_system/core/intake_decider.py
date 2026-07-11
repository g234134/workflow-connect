"""
Phase 7.5 — intake / gate for data-cleaning work orders (MVP).

Pure logic: no DB, no env secrets, no HQ ``task_routing`` import.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError

from core.intake_phase6_5_mapping import attach_phase6_5_pre_state
from core.schemas.intake import (
    INTAKE_GATE_SCHEMA_VERSION,
    GateCheckItem,
    IntakeGateFailure,
    IntakeGateRequest,
    IntakeGateResult,
)

# Aligned with 04_Workflows/task_routing_table.json (chariot.factory, dark.data).
DATA_CLEANING_TASK_TYPES = frozenset({"chariot.factory", "dark.data"})
SUGGESTED_PIPELINE = "code_cleaning_pipeline_v2"

DATA_CLEANING_KEYWORDS: tuple[str, ...] = (
    "清洗",
    "碼源",
    "code cleaning",
    "code_cleaning",
    "cleaner",
    "raw_inbound",
    "cleaned_full",
    "format_error",
    "inbound",
    "wave",
    "factory",
    "指紋",
    "registry",
    "envelope",
    "pipeline_meta",
    "code_cleaning_pipeline_v2",
    "throttle",
    "quarantine",
)

OUT_OF_SCOPE_KEYWORDS: tuple[str, ...] = (
    "rag query",
    "rag ",
    " graphrag",
    "graphrag",
    "ingest_verify",
    "ingest verify",
    "document_chunks",
    "master_status",
    "handoff",
    "dlq retry",
    "monitoring dashboard",
    "phase5 probe",
    "cost experiment",
    "langfuse only",
)

GENERIC_FILE_KEYWORDS: tuple[str, ...] = (
    "處理檔案",
    "處理文件",
    "幫我處理",
    "一些檔案",
    "一些文件",
    "process files",
    "handle files",
)

_CODE_EXTENSIONS = frozenset(
    {
        ".py",
        ".pyi",
        ".js",
        ".ts",
        ".php",
        ".rs",
        ".go",
        ".java",
        ".md",
        ".json",
        ".html",
        ".css",
        ".svg",
        ".h",
        ".c",
        ".cpp",
    }
)

_ABSOLUTE_PATH_RE = re.compile(
    r"(?:^[a-zA-Z]:[\\/])|(?:^/[a-zA-Z])|(?:\\\\)",
)


def _normalize(text: str) -> str:
    return text.strip().lower()


def _keyword_score(text: str, keywords: tuple[str, ...]) -> int:
    hay = _normalize(text)
    score = 0
    for kw in keywords:
        token = _normalize(kw)
        if not token:
            continue
        if token in hay:
            score += 2
        elif re.search(re.escape(token), hay):
            score += 1
    return score


def _has_code_extension_hints(hints: list[str]) -> bool:
    for raw in hints:
        ext = raw.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = f".{ext}"
        if ext in _CODE_EXTENSIONS:
            return True
    return False


def _check_absolute_path_hint(path_hint: str) -> GateCheckItem:
    if not path_hint:
        return GateCheckItem(
            id="no_absolute_path",
            passed=True,
            detail="inbound_path_hint empty (ok)",
        )
    if _ABSOLUTE_PATH_RE.search(path_hint):
        return GateCheckItem(
            id="no_absolute_path",
            passed=False,
            detail="inbound_path_hint must be logical/relative, not a disk absolute path",
        )
    return GateCheckItem(
        id="no_absolute_path",
        passed=True,
        detail="inbound_path_hint looks relative/logical",
    )


def _finalize(req: IntakeGateRequest, result: IntakeGateResult | IntakeGateFailure) -> dict[str, Any]:
    data = result.to_dict()
    return attach_phase6_5_pre_state(
        data,
        req,
        suggested_pipeline=data.get("suggested_pipeline"),
    )


def _suggest_task_type(clean_score: int, text: str) -> str:
    hay = _normalize(text)
    if "pipeline_meta" in hay or "ingest" in hay or "data_pipeline" in hay:
        return "dark.data"
    return "chariot.factory"


def decide_intake_gate(payload: dict[str, Any] | IntakeGateRequest) -> dict[str, Any]:
    """
    Evaluate whether an inbound work order should enter the data-cleaning pipeline.

    Returns a stable ``dict`` with ``ok``, ``decision``, ``work_category``, etc.
    """
    try:
        req = payload if isinstance(payload, IntakeGateRequest) else IntakeGateRequest.model_validate(payload)
    except ValidationError as exc:
        issues = "; ".join(
            f"{'.'.join(str(x) for x in e.get('loc', ()))}: {e.get('msg', '')}"
            for e in exc.errors()
        )
        stub = IntakeGateRequest(description="[validation_failed]")
        return _finalize(
            stub,
            IntakeGateFailure(
                message=f"intake validation failed: {issues}",
                reasons=["request_shape_invalid"],
                gate_checks=[
                    GateCheckItem(id="request_shape", passed=False, detail=issues),
                ],
            ),
        )

    text = req.combined_text()
    checks: list[GateCheckItem] = []
    reasons: list[str] = []

    checks.append(_check_absolute_path_hint(req.inbound_path_hint))
    if not checks[-1].passed:
        reasons.append("absolute_path_forbidden")
        return _finalize(
            req,
            IntakeGateResult(
                decision="reject",
                work_category="unknown",
                confidence=0.95,
                message="reject: inbound_path_hint must not be an absolute disk path",
                gate_checks=checks,
                reasons=reasons,
            ),
        )

    explicit = _normalize(req.explicit_task_type)
    if explicit in DATA_CLEANING_TASK_TYPES:
        checks.append(
            GateCheckItem(
                id="explicit_task_type",
                passed=True,
                detail=f"explicit_task_type={req.explicit_task_type}",
            )
        )
        reasons.append("explicit_data_cleaning_route")
        stt = req.explicit_task_type.strip()
        return _finalize(
            req,
            IntakeGateResult(
                decision="accept",
                work_category="data_cleaning",
                confidence=0.98,
                message=f"accept: explicit route {stt}",
                suggested_task_type=stt,
                suggested_pipeline=SUGGESTED_PIPELINE,
                gate_checks=checks,
                reasons=reasons,
            ),
        )

    if explicit and explicit not in DATA_CLEANING_TASK_TYPES:
        checks.append(
            GateCheckItem(
                id="explicit_task_type",
                passed=False,
                detail=f"task_type {req.explicit_task_type!r} is outside data-cleaning MVP",
            )
        )
        reasons.append("explicit_task_out_of_scope")
        return _finalize(
            req,
            IntakeGateResult(
                decision="reject",
                work_category="other",
                confidence=0.9,
                message=f"reject: {req.explicit_task_type!r} is not a data-cleaning route in MVP",
                gate_checks=checks,
                reasons=reasons,
            ),
        )

    clean_score = _keyword_score(text, DATA_CLEANING_KEYWORDS)
    scope_score = _keyword_score(text, OUT_OF_SCOPE_KEYWORDS)
    generic_score = _keyword_score(text, GENERIC_FILE_KEYWORDS)

    checks.append(
        GateCheckItem(
            id="data_cleaning_keywords",
            passed=clean_score >= 2,
            detail=f"score={clean_score}",
        )
    )
    checks.append(
        GateCheckItem(
            id="out_of_scope_keywords",
            passed=scope_score == 0,
            detail=f"score={scope_score}",
        )
    )

    has_ext = _has_code_extension_hints(req.file_extension_hints)
    if has_ext:
        checks.append(GateCheckItem(id="code_extensions", passed=True, detail="code-like extensions present"))
        clean_score += 1
        reasons.append("code_extension_hints")

    if req.inbound_path_hint and "inbound" in _normalize(req.inbound_path_hint):
        clean_score += 1
        reasons.append("inbound_path_hint")

    if req.batch_size_hint is not None and req.batch_size_hint > 0:
        checks.append(
            GateCheckItem(
                id="batch_size_hint",
                passed=True,
                detail=f"batch_size_hint={req.batch_size_hint}",
            )
        )
        clean_score += 1

    pipeline_anchor = SUGGESTED_PIPELINE in _normalize(text) or "pipeline_meta" in _normalize(text)
    if pipeline_anchor:
        reasons.append("pipeline_anchor")
        clean_score += 3

    if scope_score >= 2 and clean_score < scope_score:
        reasons.append("strong_out_of_scope_signal")
        return _finalize(
            req,
            IntakeGateResult(
                decision="reject",
                work_category="other",
                confidence=min(0.95, 0.55 + 0.1 * scope_score),
                message="reject: request matches non-data-cleaning work (MVP scope)",
                gate_checks=checks,
                reasons=reasons,
            ),
        )

    if clean_score >= 4 or (clean_score >= 2 and scope_score == 0 and pipeline_anchor):
        reasons.append("data_cleaning_signals_sufficient")
        stt = _suggest_task_type(clean_score, text)
        conf = min(0.92, 0.5 + 0.08 * clean_score)
        return _finalize(
            req,
            IntakeGateResult(
                decision="accept",
                work_category="data_cleaning",
                confidence=conf,
                message="accept: data-cleaning work order",
                suggested_task_type=stt,
                suggested_pipeline=SUGGESTED_PIPELINE,
                gate_checks=checks,
                reasons=reasons,
            ),
        )

    if generic_score >= 1 and clean_score < 2:
        reasons.append("ambiguous_generic_file_request")
        return _finalize(
            req,
            IntakeGateResult(
                decision="defer",
                work_category="unknown",
                confidence=0.45,
                message="defer: clarify data-cleaning scope (source, extensions, pipeline)",
                gate_checks=checks,
                reasons=reasons,
            ),
        )

    if clean_score >= 1 and scope_score <= 1:
        reasons.append("weak_data_cleaning_signal")
        return _finalize(
            req,
            IntakeGateResult(
                decision="defer",
                work_category="unknown",
                confidence=0.5,
                message="defer: possible data-cleaning work; need stronger signals",
                gate_checks=checks,
                reasons=reasons,
            ),
        )

    if scope_score >= 1:
        reasons.append("non_cleaning_dominant")
        return _finalize(
            req,
            IntakeGateResult(
                decision="reject",
                work_category="other",
                confidence=0.75,
                message="reject: not classified as data-cleaning for MVP",
                gate_checks=checks,
                reasons=reasons,
            ),
        )

    reasons.append("insufficient_signal")
    return _finalize(
        req,
        IntakeGateResult(
            decision="defer",
            work_category="unknown",
            confidence=0.35,
            message="defer: insufficient intake signal",
            gate_checks=checks,
            reasons=reasons,
        ),
    )


def parse_and_decide(raw: dict[str, Any]) -> dict[str, Any]:
    """Alias for orchestrators: validate + gate in one call."""
    out = decide_intake_gate(raw)
    out.setdefault("schema_version", INTAKE_GATE_SCHEMA_VERSION)
    return out
