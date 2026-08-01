"""P8 Notify webhook v1 — real sandbox / staging / prod path via P7 adapter.

Wraps ``delivery.notification_webhook_adapter_v1.send_webhook_notification``
for ``delivery.bundle_ready`` events. Unlike the P8-T3 *mock* module, this
path can perform real HTTP when env gates pass.

Honest boundaries:
  - Secrets / URLs come from env (never printed).
  - Staging/prod require P7 tier policy (HTTPS + URL allowlist + HMAC + retry/DLQ).
  - ≠ Phase closure · ≠ SLA / exactly-once (plan §5 → Phase 9).
  - Does not mutate ``notification_webhook_adapter_v1`` production defaults.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from delivery.notification_webhook_adapter_v1 import (
    DEFAULT_DLQ_PATH,
    ENV_DLQ_PATH,
    send_webhook_notification,
)

SCHEMA_VERSION = "p8_notify_webhook_v1"
DEFAULT_EVENT_TYPE = "delivery.bundle_ready"
VALID_TIERS = frozenset({"sandbox", "staging", "prod"})

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return (repo_root or _REPO_ROOT).resolve()


def resolve_dlq_path(
    *,
    repo_root: Optional[Path] = None,
    dlq_path_override: Optional[str] = None,
) -> Path:
    if dlq_path_override:
        path = Path(dlq_path_override)
        return path if path.is_absolute() else _repo_root(repo_root) / path
    env_path = os.getenv(ENV_DLQ_PATH, "").strip()
    if env_path:
        path = Path(env_path)
        return path if path.is_absolute() else _repo_root(repo_root) / path
    return _repo_root(repo_root) / DEFAULT_DLQ_PATH


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def build_bundle_ready_event(
    *,
    case_ref: str,
    client_summary: Optional[str] = None,
    event_id: Optional[str] = None,
) -> Dict[str, Any]:
    eid = event_id or f"p8wh-{uuid.uuid4().hex[:12]}"
    summary = client_summary or ""
    return {
        "event_id": eid,
        "event_type": DEFAULT_EVENT_TYPE,
        "case_ref": case_ref,
        "schema_version": SCHEMA_VERSION,
        "created_at": _utc_now_iso(),
        "payload": {
            "client_summary": summary,
            "client_summary_preview": summary[:240],
        },
    }


def dispatch_bundle_ready(
    *,
    case_ref: str,
    client_summary: Optional[str] = None,
    tier: str = "sandbox",
    dry_run: bool = False,
    endpoint_url: Optional[str] = None,
    event_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatch ``delivery.bundle_ready`` via P7 webhook adapter (real HTTP path).

    Parameters
    ----------
    tier:
        ``sandbox`` | ``staging`` | ``prod``. Sets ``GOV_NOTIFICATION_WEBHOOK_TIER``
        for the duration of the call when not already aligned (restored after).
    endpoint_url:
        Optional override for this call only (passed as endpoint_config).
        Staging/prod still subject to P7 URL allowlist / HTTPS policy.
    """
    result: Dict[str, Any] = {
        "ok": False,
        "schema_version": SCHEMA_VERSION,
        "tier": tier,
        "event_type": DEFAULT_EVENT_TYPE,
        "case_ref": case_ref,
        "external_http": False,
        "delivered_at": None,
        "dry_run": dry_run,
        "message": "",
        "webhook_result": None,
        "event_id": None,
    }

    if tier not in VALID_TIERS:
        result["message"] = (
            f"fail-close: tier={tier!r} not in {sorted(VALID_TIERS)}; "
            "use mock module for local theater"
        )
        return result

    event = build_bundle_ready_event(
        case_ref=case_ref,
        client_summary=client_summary,
        event_id=event_id,
    )
    result["event_id"] = event["event_id"]

    previous_tier = os.environ.get("GOV_NOTIFICATION_WEBHOOK_TIER")
    os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = tier
    try:
        endpoint_config = None
        if endpoint_url:
            endpoint_config = {"url": endpoint_url, "timeout": 10}
        adapter = send_webhook_notification(
            event,
            endpoint_config=endpoint_config,
            case_ref=case_ref,
            dry_run=dry_run,
        )
    finally:
        if previous_tier is None:
            os.environ.pop("GOV_NOTIFICATION_WEBHOOK_TIER", None)
        else:
            os.environ["GOV_NOTIFICATION_WEBHOOK_TIER"] = previous_tier

    wr = adapter.get("webhook_result") or {}
    dispatched = bool(wr.get("dispatched"))
    external = dispatched and not bool(wr.get("dry_run"))

    result.update(
        {
            "ok": bool(adapter.get("ok")),
            "message": str(adapter.get("message") or ""),
            "webhook_result": wr,
            "external_http": external,
            "attempt_count": wr.get("attempt_count"),
            "retry_exhausted": wr.get("retry_exhausted"),
            "http_status": wr.get("http_status"),
            "blocked_reason": wr.get("blocked_reason"),
            "blocked_rule": wr.get("blocked_rule"),
        }
    )
    if dispatched and not wr.get("dry_run"):
        result["delivered_at"] = wr.get("timestamp") or _utc_now_iso()
    return result


def list_dlq(
    *,
    repo_root: Optional[Path] = None,
    dlq_path_override: Optional[str] = None,
    case_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """List P7 notification DLQ rows (shared path with adapter)."""
    dlq_path = resolve_dlq_path(
        repo_root=repo_root,
        dlq_path_override=dlq_path_override,
    )
    rows = _read_jsonl(dlq_path)
    if case_ref:
        rows = [r for r in rows if str(r.get("case_ref") or "") == case_ref]
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "dlq_path": str(dlq_path),
        "count": len(rows),
        "items": rows,
        "message": f"found {len(rows)} DLQ row(s)",
    }


def staging_prod_readiness_check(*, tier: str = "staging") -> Dict[str, Any]:
    """Read-only readiness probe for staging/prod (no secrets printed).

    Reports which env gates are set (booleans only), without values.
    """
    if tier not in ("staging", "prod"):
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "tier": tier,
            "message": "readiness check only for staging|prod",
        }

    def _set(name: str) -> bool:
        return bool(os.getenv(name, "").strip())

    gates = {
        "GOV_NOTIFICATION_WEBHOOK_ENABLED": _set("GOV_NOTIFICATION_WEBHOOK_ENABLED"),
        "GOV_NOTIFICATION_WEBHOOK_URL": _set("GOV_NOTIFICATION_WEBHOOK_URL"),
        "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST": _set(
            "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"
        ),
        "GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST": _set(
            "GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST"
        ),
        "GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED": _set(
            "GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"
        ),
        "GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET": _set(
            "GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"
        ),
        "GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED": _set(
            "GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"
        ),
    }
    missing = [k for k, v in gates.items() if not v]
    ready = len(missing) == 0
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "tier": tier,
        "ready": ready,
        "gates_present": gates,
        "missing_gates": missing,
        "external_http": False,
        "message": (
            "staging/prod env gates complete"
            if ready
            else f"missing {len(missing)} gate(s); set env then dispatch"
        ),
        "non_claims": [
            "≠ prints secret values",
            "≠ auto-enables prod",
            "≠ SLA / exactly-once",
        ],
    }
