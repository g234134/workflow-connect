"""Typed structures for Intake Gate policy evaluation (P75-G3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

PolicySuggestedAction = Literal["accept", "reject", "review_needed", "none"]


@dataclass(frozen=True)
class PolicyHit:
    """Single policy rule evaluation outcome (not canonical gate decision)."""

    rule_id: str
    passed: bool
    detail: str
    reason_code: Optional[str] = None
    suggested_action: PolicySuggestedAction = "none"
    hit_kind: str = "policy"

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "rule_id": self.rule_id,
            "passed": self.passed,
            "detail": self.detail,
            "hit_kind": self.hit_kind,
            "suggested_action": self.suggested_action,
        }
        if self.reason_code is not None:
            payload["reason_code"] = self.reason_code
        return payload


@dataclass
class PolicyEvalResult:
    """Evaluator output: resolved profile context + ordered policy hits."""

    ok: bool
    policy_version: str
    profile_id: str = ""
    profile_tier: str = "unknown"
    profile_maturity: str = "unknown"
    hits: List[PolicyHit] = field(default_factory=list)
    message: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "policy_version": self.policy_version,
            "profile_id": self.profile_id,
            "profile_tier": self.profile_tier,
            "profile_maturity": self.profile_maturity,
            "hits": [hit.to_dict() for hit in self.hits],
            "message": self.message,
            "error": self.error,
        }
