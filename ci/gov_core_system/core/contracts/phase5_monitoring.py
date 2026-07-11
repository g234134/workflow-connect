"""
Phase 5 shared contracts — **dev/staging v1 · NOT production-ready**.

Authority for:
- documentation tier wording
- alert severity enum
- cross-agent import boundaries (see ``output/phase5_parallel_coordination.md``)
"""

from __future__ import annotations

from enum import Enum
from typing import Final, Literal

# --- Documentation tier (all Phase 5 docs MUST include CONTRACT_DOC_TIER_LINE) ---

CONTRACT_TIER: Final[str] = "dev_staging_v1"
CONTRACT_DOC_TIER_LINE: Final[str] = (
    "**Tier**: dev/staging v1 · **NOT production-ready**"
)
PRODUCTION_READY: Final[bool] = False


def is_production_ready() -> bool:
    return False


# --- Alert severity (DB ``alert_events.severity`` + API + notifier) ---


class AlertSeverity(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"


ALERT_SEVERITIES: Final[tuple[str, ...]] = tuple(s.value for s in AlertSeverity)

AlertSeverityLiteral = Literal["warning", "critical"]
