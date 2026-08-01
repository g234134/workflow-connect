"""W4-GUARD G2–G4 opt-in escalation (FP-G1-T3 / W4-GUARD-01).

Default: observation-only sidecar. Does **not** change gate/E2E exit unless
explicit flags enable escalation / strict-guards.

G2 — schema ambiguity (phase_like + multi_row_export + schema_ambiguous)
G3 — low accepted_ratio; block_delivery when G2 ∧ ratio < block threshold
G4 — pass_with_warnings + G3 signal → fail E2E only under --strict-guards
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

GUARD_ESCALATION_VERSION = "w4-guard-escalation-v1"
DEFAULT_RATIO_WARN = 0.5
DEFAULT_RATIO_BLOCK = 0.1
_SCHEMA_AMBIGUOUS_NOTES = frozenset({"multi_row_export", "schema_ambiguous"})


def _schema_notes(eligibility_raw: Optional[Mapping[str, Any]]) -> list[str]:
    if not eligibility_raw:
        return []
    dimensions = eligibility_raw.get("dimensions") or {}
    schema = dimensions.get("schema") or {}
    notes = schema.get("notes") or []
    return [str(n) for n in notes]


def _ratio_from_guard(output_guard: Optional[Mapping[str, Any]]) -> Optional[float]:
    if not output_guard:
        return None
    raw = output_guard.get("ratio")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def evaluate_guard_escalation(
    *,
    eligibility_raw: Optional[Mapping[str, Any]] = None,
    output_guard: Optional[Mapping[str, Any]] = None,
    qa_status: Optional[str] = None,
    enable_g2: bool = False,
    enable_g3: bool = False,
    enable_g4: bool = False,
    strict_guards: bool = False,
    ratio_warn_threshold: float = DEFAULT_RATIO_WARN,
    ratio_block_threshold: float = DEFAULT_RATIO_BLOCK,
) -> dict[str, Any]:
    """Evaluate G2–G4 signals and optional apply recommendations.

    Returns a stable dict. With all enable_* / strict_guards False (default),
    ``applied`` is empty and ``e2e_fail`` is False — production-safe.
    """
    notes = _schema_notes(eligibility_raw)
    note_set = set(notes)
    g2_signal = (
        "phase_like" in note_set
        and "multi_row_export" in note_set
        and "schema_ambiguous" in note_set
    )
    ratio = _ratio_from_guard(output_guard)
    guard_status = str((output_guard or {}).get("status") or "")
    g3_warn_signal = (
        ratio is not None and ratio < ratio_warn_threshold
    ) or guard_status == "warning"
    g3_block_signal = g2_signal and ratio is not None and ratio < ratio_block_threshold
    qa = str(qa_status or "").strip().lower()
    g4_signal = qa == "pass_with_warnings" and (g3_warn_signal or g3_block_signal)

    signals = {
        "g2_schema_ambiguous": g2_signal,
        "g3_ratio_warning": g3_warn_signal,
        "g3_block_delivery": g3_block_signal,
        "g4_strict_candidate": g4_signal,
    }

    recommendations: dict[str, Any] = {
        "gate_eligibility": None,
        "delivery": None,
        "e2e": None,
    }
    applied: dict[str, Any] = {}
    reasons: list[str] = []

    if g2_signal:
        reasons.append("g2:phase_like+multi_row_export+schema_ambiguous")
        recommendations["gate_eligibility"] = "review_needed"
        if enable_g2:
            applied["gate_eligibility"] = "review_needed"

    if g3_warn_signal:
        reasons.append(f"g3:ratio_below_warn<{ratio_warn_threshold}")
        recommendations["delivery"] = recommendations["delivery"] or "manual_review"
    if g3_block_signal:
        reasons.append(f"g3:g2_and_ratio_below_block<{ratio_block_threshold}")
        recommendations["delivery"] = "block_delivery"
        if enable_g3:
            applied["delivery"] = "block_delivery"
    elif g3_warn_signal and enable_g3 and not applied.get("delivery"):
        applied["delivery"] = "manual_review"

    e2e_fail = False
    if g4_signal:
        reasons.append("g4:pass_with_warnings+g3_signal")
        recommendations["e2e"] = "fail_under_strict_guards"
        if enable_g4 or strict_guards:
            e2e_fail = bool(strict_guards)
            if e2e_fail:
                applied["e2e"] = "fail"
                applied["strict_guards"] = True

    return {
        "ok": True,
        "guard_escalation_version": GUARD_ESCALATION_VERSION,
        "signals": signals,
        "ratio": ratio,
        "ratio_warn_threshold": ratio_warn_threshold,
        "ratio_block_threshold": ratio_block_threshold,
        "qa_status": qa or None,
        "schema_notes": notes,
        "flags": {
            "enable_g2": bool(enable_g2),
            "enable_g3": bool(enable_g3),
            "enable_g4": bool(enable_g4),
            "strict_guards": bool(strict_guards),
        },
        "recommendations": recommendations,
        "applied": applied,
        "e2e_fail": e2e_fail,
        "reasons": reasons,
        "message": (
            "strict_guards_fail"
            if e2e_fail
            else (
                "escalation_applied"
                if applied
                else "observation_only_default_safe"
            )
        ),
    }


def attach_guard_escalation(
    result: MutableMapping[str, Any],
    escalation: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach escalation sidecar to an E2E/result dict; optionally fail overall."""
    result["guard_escalation"] = dict(escalation)
    if escalation.get("e2e_fail"):
        result["ok"] = False
        result["message"] = (
            f"strict_guards: {escalation.get('message') or 'g4_fail'}"
        )
    return dict(result)
