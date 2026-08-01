"""Gov notification webhook HMAC receiver reference (WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1).

Minimal verify_gov_webhook aligned with docs/outbox-and-feedback-layer-contract-v1.md §4.6.5.2
and sender canonicalization in notification_webhook_adapter_v1.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, MutableMapping, Optional, Tuple

DEFAULT_SIGNATURE_HEADER = "X-Gov-Signature-256"
DEFAULT_TIMESTAMP_HEADER = "X-Gov-Timestamp"
DEFAULT_EVENT_ID_HEADER = "X-Gov-Event-Id"
DEFAULT_TIMESTAMP_WINDOW_SEC = 300


@dataclass
class VerifyGovWebhookResult:
    ok: bool
    status_code: int
    reason: str
    idempotent: bool = False
    event_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "status_code": self.status_code,
            "reason": self.reason,
            "idempotent": self.idempotent,
            "event_id": self.event_id,
        }


@dataclass
class ReplayCache:
    """In-memory seen-set for event_id idempotency (non-prod reference only)."""

    max_seen_window_sec: int = 86400
    _seen: MutableMapping[str, float] = field(default_factory=dict)

    def contains(self, event_id: str, *, now: float) -> bool:
        self._prune(now)
        return event_id in self._seen

    def store(self, event_id: str, *, now: float) -> None:
        self._prune(now)
        self._seen[event_id] = now + float(self.max_seen_window_sec)

    def _prune(self, now: float) -> None:
        expired = [key for key, expiry in self._seen.items() if expiry <= now]
        for key in expired:
            del self._seen[key]


def build_hmac_signed_message(timestamp: str, event_id: str, body_bytes: bytes) -> bytes:
    body_text = body_bytes.decode("utf-8")
    return f"{timestamp}.{event_id}.{body_text}".encode("utf-8")


def compute_hmac_sha256_hex(secret: str, message: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def sign_gov_webhook_headers(
    body_bytes: bytes,
    *,
    shared_secret: str,
    event_id: str,
    timestamp: Optional[int] = None,
    signature_header: str = DEFAULT_SIGNATURE_HEADER,
    timestamp_header: str = DEFAULT_TIMESTAMP_HEADER,
    event_id_header: str = DEFAULT_EVENT_ID_HEADER,
) -> Dict[str, str]:
    ts = str(timestamp if timestamp is not None else int(time.time()))
    message = build_hmac_signed_message(ts, event_id, body_bytes)
    digest_hex = compute_hmac_sha256_hex(shared_secret, message)
    return {
        signature_header: f"sha256={digest_hex}",
        timestamp_header: ts,
        event_id_header: event_id,
    }


def _normalize_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    return {str(k).lower(): str(v) for k, v in headers.items()}


def _constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def verify_gov_webhook(
    *,
    body_bytes: bytes,
    headers: Mapping[str, str],
    shared_secret: str,
    timestamp_window_sec: int = DEFAULT_TIMESTAMP_WINDOW_SEC,
    replay_cache: Optional[ReplayCache] = None,
    now_ts: Optional[int] = None,
    signature_header: str = DEFAULT_SIGNATURE_HEADER,
    timestamp_header: str = DEFAULT_TIMESTAMP_HEADER,
    event_id_header: str = DEFAULT_EVENT_ID_HEADER,
) -> VerifyGovWebhookResult:
    normalized = _normalize_headers(headers)
    sig_header = normalized.get(signature_header.lower(), "").strip()
    timestamp_raw = normalized.get(timestamp_header.lower(), "").strip()
    event_id_h = normalized.get(event_id_header.lower(), "").strip()

    if not sig_header or not timestamp_raw or not event_id_h:
        return VerifyGovWebhookResult(
            ok=False,
            status_code=401,
            reason="missing_signature_headers",
        )

    try:
        timestamp = int(timestamp_raw)
    except ValueError:
        return VerifyGovWebhookResult(
            ok=False,
            status_code=401,
            reason="invalid_timestamp_format",
        )

    now = now_ts if now_ts is not None else int(time.time())
    if abs(now - timestamp) > timestamp_window_sec:
        return VerifyGovWebhookResult(
            ok=False,
            status_code=401,
            reason="timestamp_out_of_window",
        )

    try:
        body_json = json.loads(body_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return VerifyGovWebhookResult(
            ok=False,
            status_code=400,
            reason="invalid_json_body",
        )

    event_id_b = str(body_json.get("event_id", "")).strip()
    if not event_id_b:
        return VerifyGovWebhookResult(
            ok=False,
            status_code=400,
            reason="missing_event_id_in_body",
        )
    if event_id_h != event_id_b:
        return VerifyGovWebhookResult(
            ok=False,
            status_code=400,
            reason="event_id_mismatch",
            event_id=event_id_b,
        )

    message = build_hmac_signed_message(str(timestamp), event_id_b, body_bytes)
    expected = f"sha256={compute_hmac_sha256_hex(shared_secret, message)}"
    if not _constant_time_equals(sig_header, expected):
        return VerifyGovWebhookResult(
            ok=False,
            status_code=401,
            reason="invalid_signature",
            event_id=event_id_b,
        )

    if replay_cache is not None:
        now_float = float(now)
        if replay_cache.contains(event_id_b, now=now_float):
            return VerifyGovWebhookResult(
                ok=True,
                status_code=200,
                reason="replay_idempotent_accept",
                idempotent=True,
                event_id=event_id_b,
            )
        replay_cache.store(event_id_b, now=now_float)

    return VerifyGovWebhookResult(
        ok=True,
        status_code=200,
        reason="accepted",
        idempotent=False,
        event_id=event_id_b,
    )
