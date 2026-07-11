"""Notification webhook adapter v1 — sandbox dispatch implementation (WD-P7-T2).

Minimal webhook sink for notification dispatch registry.
- Controlled by env GOV_NOTIFICATION_WEBHOOK_ENABLED
- Case allowlist: only specific case_ref patterns trigger actual POST
- Sandbox mode: target URL can be mock/test endpoint (http://localhost, etc.)
- Fail-open: webhook failures never block main dispatch flow
- Dry-run by default when env is not set or allowlist not matched

Optional retry (WH-P7-NOTIF-RETRY-SANDBOX-v1):
- Env-driven retry loop; default max_attempts=0 (single POST, unchanged behavior)
- Sandbox localhost only; no DLQ

Optional HMAC sender (WH-P7-NOTIF-HMAC-impl-v1):
- Env-gated HMAC-SHA256 signing; default off (sandbox unchanged)
- Headers: X-Gov-Signature-256, X-Gov-Timestamp, X-Gov-Event-Id
- Fail-open: signing errors disable signature, still POST unsigned

Tier / URL allowlist gate (WH-P7-NOTIF-PROD-URL-impl-v1):
- Env GOV_NOTIFICATION_WEBHOOK_TIER (default sandbox)
- Env GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST for staging/prod only
- Sandbox: localhost-only unchanged; allowlist ignored
- Staging/prod: https + allowlist match required; fail-open at dispatch layer

Tier HMAC mandatory gate (WH-P7-NOTIF-HMAC-prod-impl-v1):
- Staging/prod: HMAC_ENABLED + secret + event_id + signing must succeed
- Failure: no POST; blocked_by_hmac_tier_policy + blocked_rule
- Sandbox: gate skipped; fail-open unsigned unchanged

Optional DLQ audit log (WH-P7-NOTIF-DLQ-impl-v1):
- Env-gated append to events.jsonl on final webhook failure
- Default off; fail-open on DLQ write errors

Non-scope (P8.9-T4):
- No receiver verify-sign contract (future phase)
- No production URL / secrets in repo
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)

WEBHOOK_SCHEMA_VERSION = "webhook_adapter_v1"
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_RETRY_MAX_ATTEMPTS = 0
DEFAULT_RETRY_BASE_DELAY_MS = 100
DEFAULT_RETRY_MAX_DELAY_MS = 2000

# Tier defaults when env unset (WH-P7-NOTIF-RETRY-prod-impl-v1)
TIER_RETRY_DEFAULTS: Dict[str, Dict[str, int]] = {
    "sandbox": {
        "max_attempts": 0,
        "base_delay_ms": 100,
        "max_delay_ms": 2000,
    },
    "staging": {
        "max_attempts": 3,
        "base_delay_ms": 500,
        "max_delay_ms": 8000,
    },
    "prod": {
        "max_attempts": 5,
        "base_delay_ms": 1000,
        "max_delay_ms": 30000,
    },
}

ENV_RETRY_MAX_ATTEMPTS = "GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS"
ENV_RETRY_BASE_DELAY_MS = "GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS"
ENV_RETRY_MAX_DELAY_MS = "GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS"

ENV_HMAC_ENABLED = "GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"
ENV_HMAC_SECRET = "GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"
ENV_HMAC_HEADER = "GOV_NOTIFICATION_WEBHOOK_HMAC_HEADER"
ENV_HMAC_TIMESTAMP_HEADER = "GOV_NOTIFICATION_WEBHOOK_TIMESTAMP_HEADER"
ENV_HMAC_EVENT_ID_HEADER = "GOV_NOTIFICATION_WEBHOOK_EVENT_ID_HEADER"

ENV_TIER = "GOV_NOTIFICATION_WEBHOOK_TIER"
ENV_URL_ALLOWLIST = "GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST"
DEFAULT_TIER = "sandbox"
VALID_TIERS = frozenset({"sandbox", "staging", "prod"})

DEFAULT_HMAC_HEADER = "X-Gov-Signature-256"
DEFAULT_HMAC_TIMESTAMP_HEADER = "X-Gov-Timestamp"
DEFAULT_HMAC_EVENT_ID_HEADER = "X-Gov-Event-Id"

ENV_DLQ_ENABLED = "GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"
ENV_DLQ_PATH = "GOV_NOTIFICATION_WEBHOOK_DLQ_PATH"
ENV_DLQ_TIER = "GOV_NOTIFICATION_WEBHOOK_DLQ_TIER"

DEFAULT_DLQ_PATH = "outbox/notification_dlq/events.jsonl"
DEFAULT_DLQ_TIER = "sandbox"
DLQ_SCHEMA_ID = "notification_webhook_dlq_v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_webhook_enabled_via_env() -> bool:
    """True when GOV_NOTIFICATION_WEBHOOK_ENABLED=1|true|yes."""
    val = os.getenv("GOV_NOTIFICATION_WEBHOOK_ENABLED", "").strip().lower()
    return val in ("1", "true", "yes")


def _get_allowlist_patterns() -> List[str]:
    """Read case allowlist from env GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST.
    
    Format: comma-separated glob patterns, e.g.:
      GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST="demo_*,test_*"
    Empty means no cases allowed (dry-run mode for all).
    """
    raw = os.getenv("GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST", "").strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _case_ref_matches_allowlist(case_ref: str, patterns: List[str]) -> bool:
    """Check if case_ref matches any glob pattern in allowlist."""
    if not patterns:
        return False
    # Convert glob to regex: * -> .*, ? -> ., escape other special chars
    for pattern in patterns:
        regex = "^" + re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".") + "$"
        if re.match(regex, case_ref):
            return True
    return False


def _get_webhook_endpoint_config() -> Dict[str, Any]:
    """Read webhook endpoint config from env.
    
    GOV_NOTIFICATION_WEBHOOK_URL: Target URL (default: empty -> dry-run)
    GOV_NOTIFICATION_WEBHOOK_TIMEOUT: Timeout in seconds (default: 10)
    
    Returns endpoint config dict or empty dict to indicate dry-run.
    """
    url = os.getenv("GOV_NOTIFICATION_WEBHOOK_URL", "").strip()
    if not url:
        return {}
    
    timeout_str = os.getenv("GOV_NOTIFICATION_WEBHOOK_TIMEOUT", "10").strip()
    try:
        timeout = int(timeout_str)
        if timeout <= 0:
            timeout = DEFAULT_TIMEOUT_SECONDS
    except ValueError:
        timeout = DEFAULT_TIMEOUT_SECONDS
    
    return {
        "url": url,
        "timeout": timeout,
    }


def _parse_non_negative_int_env(
    env_name: str,
    default: int,
    *,
    invalid_fallback: int = 0,
) -> int:
    """Parse a non-negative integer env var; log one warning on parse failure."""
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
        if value < 0:
            _logger.warning(
                "Invalid %s=%r (negative); using fallback %s",
                env_name,
                raw,
                invalid_fallback,
            )
            return invalid_fallback
        return value
    except ValueError:
        _logger.warning(
            "Invalid %s=%r (not an integer); using fallback %s",
            env_name,
            raw,
            invalid_fallback,
        )
        return invalid_fallback


def _is_truthy_env_flag(env_name: str) -> bool:
    """True when env is 1|true|yes (case-insensitive)."""
    val = os.getenv(env_name, "").strip().lower()
    return val in ("1", "true", "yes")


def _get_hmac_config() -> Dict[str, str]:
    """Read HMAC header names and secret from env (safe defaults)."""
    return {
        "signature_header": os.getenv(ENV_HMAC_HEADER, DEFAULT_HMAC_HEADER).strip()
        or DEFAULT_HMAC_HEADER,
        "timestamp_header": os.getenv(
            ENV_HMAC_TIMESTAMP_HEADER, DEFAULT_HMAC_TIMESTAMP_HEADER
        ).strip()
        or DEFAULT_HMAC_TIMESTAMP_HEADER,
        "event_id_header": os.getenv(
            ENV_HMAC_EVENT_ID_HEADER, DEFAULT_HMAC_EVENT_ID_HEADER
        ).strip()
        or DEFAULT_HMAC_EVENT_ID_HEADER,
        "secret": os.getenv(ENV_HMAC_SECRET, "").strip(),
    }


def _should_apply_hmac_signature() -> bool:
    """True when HMAC_ENABLED=1 and secret is non-empty."""
    if not _is_truthy_env_flag(ENV_HMAC_ENABLED):
        return False
    secret = os.getenv(ENV_HMAC_SECRET, "").strip()
    if not secret:
        _logger.warning(
            "%s=1 but %s is empty; HMAC signing disabled (fail-open)",
            ENV_HMAC_ENABLED,
            ENV_HMAC_SECRET,
        )
        return False
    return True


def _build_hmac_signed_message(
    timestamp: str,
    event_id: str,
    body_bytes: bytes,
) -> bytes:
    """Canonical signed string: {timestamp}.{event_id}.{raw_body_utf8}."""
    body_text = body_bytes.decode("utf-8")
    return f"{timestamp}.{event_id}.{body_text}".encode("utf-8")


def _compute_hmac_sha256_hex(secret: str, message: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _apply_hmac_headers(
    headers: Dict[str, str],
    *,
    event_id: Optional[str],
    body_bytes: bytes,
) -> None:
    """Attach HMAC headers when env gate passes; fail-open on errors."""
    if not _should_apply_hmac_signature():
        return

    try:
        config = _get_hmac_config()
        secret = config["secret"]
        if not secret:
            _logger.warning(
                "HMAC signing skipped: %s is empty (fail-open)",
                ENV_HMAC_SECRET,
            )
            return

        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        resolved_event_id = event_id or ""
        message = _build_hmac_signed_message(timestamp, resolved_event_id, body_bytes)
        digest_hex = _compute_hmac_sha256_hex(secret, message)

        headers[config["timestamp_header"]] = timestamp
        if resolved_event_id:
            headers[config["event_id_header"]] = resolved_event_id
        headers[config["signature_header"]] = f"sha256={digest_hex}"
    except Exception as exc:
        _logger.warning(
            "HMAC signing failed (fail-open, sending unsigned): %s",
            exc,
        )


def _get_dlq_path() -> str:
    """Resolve DLQ jsonl path from env (§4.6.4)."""
    path = os.getenv(ENV_DLQ_PATH, DEFAULT_DLQ_PATH).strip()
    return path or DEFAULT_DLQ_PATH


def _get_dlq_tier() -> str:
    """Resolve endpoint tier for DLQ records; sandbox default."""
    tier = os.getenv(ENV_DLQ_TIER, "").strip().lower()
    if tier in ("sandbox", "staging", "prod"):
        return tier
    return DEFAULT_DLQ_TIER


def _redact_endpoint_url(url: str) -> str:
    """Strip query string from URL to avoid persisting secret query params."""
    if "?" not in url:
        return url
    base, _query = url.split("?", 1)
    return f"{base}?<redacted>"


def _sanitize_webhook_result_for_dlq(webhook_result: Dict[str, Any]) -> Dict[str, Any]:
    """Embed webhook_result snapshot with response_body truncated per §4.6.4.2."""
    snapshot = dict(webhook_result)
    body = snapshot.get("response_body")
    if isinstance(body, str) and len(body) > 512:
        snapshot["response_body"] = body[:512] + "..."
    return snapshot


def _build_dlq_record(
    *,
    event: Dict[str, Any],
    event_id: Optional[str],
    event_type: str,
    case_ref: str,
    endpoint_url: str,
    webhook_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Build one DLQ jsonl record per §4.6.4.2."""
    sanitized_result = _sanitize_webhook_result_for_dlq(webhook_result)
    failure_ts = webhook_result.get("timestamp") or _utc_now_iso()
    resolved_event_id = event_id or event.get("event_id") or ""

    payload_digest: Optional[str] = None
    try:
        payload_bytes = json.dumps(event, ensure_ascii=False, sort_keys=True).encode("utf-8")
        payload_digest = hashlib.sha256(payload_bytes).hexdigest()
    except Exception:
        payload_digest = None

    return {
        "schema_id": DLQ_SCHEMA_ID,
        "timestamp": failure_ts,
        "dlq_written_at": _utc_now_iso(),
        "tier": _get_dlq_tier(),
        "event_id": resolved_event_id,
        "event_type": event_type,
        "case_ref": case_ref or None,
        "endpoint": _redact_endpoint_url(endpoint_url),
        "http_status": webhook_result.get("http_status"),
        "attempt_count": webhook_result.get("attempt_count", 1),
        "retry_exhausted": bool(webhook_result.get("retry_exhausted")),
        "last_error": webhook_result.get("last_error") or webhook_result.get("error"),
        "request_headers": {},
        "payload_digest": payload_digest,
        "webhook_result": sanitized_result,
        "source_notification_path": None,
    }


def _append_dlq_record(record: Dict[str, Any]) -> None:
    """Append one JSON line to DLQ jsonl; raises on I/O failure."""
    dlq_path = _get_dlq_path()
    parent = os.path.dirname(dlq_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with open(dlq_path, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _maybe_append_dlq_record(
    *,
    event: Dict[str, Any],
    event_id: Optional[str],
    event_type: str,
    case_ref: str,
    endpoint_url: str,
    webhook_result: Dict[str, Any],
) -> None:
    """Write DLQ on final webhook failure when env gate is on; always fail-open."""
    if not _is_truthy_env_flag(ENV_DLQ_ENABLED):
        return
    try:
        record = _build_dlq_record(
            event=event,
            event_id=event_id,
            event_type=event_type,
            case_ref=case_ref,
            endpoint_url=endpoint_url,
            webhook_result=webhook_result,
        )
        _append_dlq_record(record)
    except Exception as exc:
        _logger.warning(
            "DLQ append failed (fail-open): path=%s error=%s",
            _get_dlq_path(),
            exc,
        )


def _get_tier_retry_defaults(tier: str) -> Dict[str, int]:
    """Return tier-specific retry defaults when env is unset."""
    return dict(TIER_RETRY_DEFAULTS.get(tier, TIER_RETRY_DEFAULTS["sandbox"]))


def _get_retry_config(*, tier: Optional[str] = None) -> Dict[str, int]:
    """Read retry policy from env with tier-aware defaults when env unset."""
    resolved_tier = tier if tier is not None else _get_webhook_tier()
    tier_defaults = _get_tier_retry_defaults(resolved_tier)
    return {
        "max_attempts": _parse_non_negative_int_env(
            ENV_RETRY_MAX_ATTEMPTS,
            tier_defaults["max_attempts"],
            invalid_fallback=0,
        ),
        "base_delay_ms": _parse_non_negative_int_env(
            ENV_RETRY_BASE_DELAY_MS,
            tier_defaults["base_delay_ms"],
            invalid_fallback=tier_defaults["base_delay_ms"],
        ),
        "max_delay_ms": _parse_non_negative_int_env(
            ENV_RETRY_MAX_DELAY_MS,
            tier_defaults["max_delay_ms"],
            invalid_fallback=tier_defaults["max_delay_ms"],
        ),
    }


def _check_tier_retry_readiness(
    tier: str,
    retry_config: Dict[str, int],
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate staging/prod mandatory retry + DLQ before POST.

    HMAC readiness is enforced by ``_check_hmac_tier_policy`` (runs earlier).
    Returns (ready, blocked_reason, blocked_rule).
    Sandbox tier is always ready (no mandatory gate).
    """
    if tier not in ("staging", "prod"):
        return True, None, None

    max_attempts = retry_config.get("max_attempts", 0)
    if max_attempts < 1:
        return False, "blocked_by_tier_retry_policy", "retry_policy_violation"

    if not _is_truthy_env_flag(ENV_DLQ_ENABLED):
        return False, "blocked_by_tier_retry_policy", "dlq_policy_violation"

    return True, None, None


def _is_http_success(result: Dict[str, Any]) -> bool:
    status = result.get("http_status")
    return (
        status is not None
        and 200 <= status < 300
        and result.get("error") is None
    )


def _is_retriable_http_result(result: Dict[str, Any]) -> bool:
    """Retriable: connection/timeout errors, 408, 429, 5xx. Non-retriable: other 4xx."""
    if result.get("timeout"):
        return True
    status = result.get("http_status")
    if status is None:
        return True
    if status in (408, 429):
        return True
    if status >= 500:
        return True
    return False


def _compute_retry_delay_ms(
    failed_attempt_index: int,
    *,
    base_delay_ms: int,
    max_delay_ms: int,
) -> int:
    """Exponential-ish backoff after failed attempt N (1-based), clamped to max_delay_ms."""
    if failed_attempt_index <= 0:
        return base_delay_ms
    delay = base_delay_ms * (2 ** (failed_attempt_index - 1))
    return min(delay, max_delay_ms)


def _send_http_post_with_retry(
    url: str,
    payload: Dict[str, Any],
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    retry_config: Optional[Dict[str, int]] = None,
) -> Tuple[Dict[str, Any], int, bool]:
    """POST with optional retry loop.

    Returns (last_result, attempt_count, retry_exhausted).
    When max_attempts <= 0: single POST (legacy behavior).
    When max_attempts >= 1: up to max_attempts tries with backoff between retriable failures.
    """
    if retry_config is None:
        retry_config = _get_retry_config()

    max_attempts = retry_config.get("max_attempts", DEFAULT_RETRY_MAX_ATTEMPTS)
    base_delay_ms = retry_config.get("base_delay_ms", DEFAULT_RETRY_BASE_DELAY_MS)
    max_delay_ms = retry_config.get("max_delay_ms", DEFAULT_RETRY_MAX_DELAY_MS)

    total_attempts = 1 if max_attempts <= 0 else max_attempts
    last_result: Dict[str, Any] = {}

    for attempt in range(1, total_attempts + 1):
        last_result = _send_http_post(url, payload, timeout=timeout)
        if _is_http_success(last_result):
            return last_result, attempt, False
        if max_attempts <= 0:
            break
        if not _is_retriable_http_result(last_result):
            break
        if attempt >= total_attempts:
            break
        delay_ms = _compute_retry_delay_ms(
            attempt,
            base_delay_ms=base_delay_ms,
            max_delay_ms=max_delay_ms,
        )
        _logger.info(
            "Webhook POST retry scheduled: attempt=%s/%s delay_ms=%s",
            attempt,
            total_attempts,
            delay_ms,
        )
        time.sleep(delay_ms / 1000.0)

    retry_exhausted = (
        max_attempts >= 1
        and not _is_http_success(last_result)
        and attempt >= total_attempts
        and _is_retriable_http_result(last_result)
    )
    return last_result, attempt, retry_exhausted


def _get_webhook_tier() -> str:
    """Read webhook tier from env; unset or invalid values default to sandbox."""
    raw = os.getenv(ENV_TIER, "").strip().lower()
    if not raw:
        return DEFAULT_TIER
    if raw in VALID_TIERS:
        return raw
    _logger.warning(
        "Invalid %s=%r; defaulting to sandbox",
        ENV_TIER,
        raw,
    )
    return DEFAULT_TIER


def _parse_allowlist_entry(entry: str) -> Optional[Dict[str, Any]]:
    """Parse one allowlist entry: host, host:port, or host/path-prefix."""
    entry = entry.strip()
    if not entry:
        return None

    path_prefix: Optional[str] = None
    host_part = entry
    if "/" in entry:
        host_part, path_rest = entry.split("/", 1)
        path_prefix = "/" + path_rest if path_rest else "/"

    port: Optional[int] = None
    host_pattern = host_part.strip()
    if ":" in host_part:
        host_pattern, port_str = host_part.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            return None
        host_pattern = host_pattern.strip()

    if not host_pattern:
        return None

    return {
        "host_pattern": host_pattern.lower(),
        "port": port,
        "path_prefix": path_prefix,
    }


def _get_url_allowlist_entries() -> Tuple[List[Dict[str, Any]], bool]:
    """Return parsed allowlist entries; False when unset or any entry invalid."""
    raw = os.getenv(ENV_URL_ALLOWLIST, "").strip()
    if not raw:
        return [], False

    entries: List[Dict[str, Any]] = []
    for part in raw.split(","):
        parsed = _parse_allowlist_entry(part)
        if parsed is None:
            _logger.warning(
                "Invalid %s entry %r; allowlist parse failed",
                ENV_URL_ALLOWLIST,
                part.strip(),
            )
            return [], False
        entries.append(parsed)
    return entries, True


def _parse_webhook_url(url: str) -> Optional[Dict[str, Any]]:
    """Extract scheme, host, port, path from a webhook URL."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        host = parsed.hostname
        if not host:
            return None
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "https" else 80
        path = parsed.path or "/"
        return {
            "scheme": parsed.scheme,
            "host": host.lower(),
            "port": port,
            "path": path,
        }
    except Exception:
        return None


def _is_bare_ip(host: str) -> bool:
    """True when host is a literal IP address (staging/prod forbid bare IP)."""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _host_matches_pattern(host: str, pattern: str) -> bool:
    """Match literal hostname or *.suffix subdomain glob."""
    host = host.lower()
    pattern = pattern.lower()
    if pattern.startswith("*."):
        suffix = pattern[2:]
        return host == suffix or host.endswith("." + suffix)
    return host == pattern


def _path_matches_prefix(url_path: str, path_prefix: Optional[str]) -> bool:
    """Match URL path against optional allowlist path prefix or glob."""
    if not path_prefix:
        return True

    prefix = path_prefix
    if prefix.endswith("/*"):
        base = prefix[:-2]
        return url_path == base or url_path.startswith(base + "/")
    if prefix.endswith("*"):
        return url_path.startswith(prefix[:-1])
    return url_path == prefix or url_path.startswith(prefix + "/")


def _url_matches_allowlist_entry(
    components: Dict[str, Any],
    entry: Dict[str, Any],
) -> bool:
    """True when URL components match one parsed allowlist entry."""
    if not _host_matches_pattern(components["host"], entry["host_pattern"]):
        return False
    if entry["port"] is not None and components["port"] != entry["port"]:
        return False
    if not _path_matches_prefix(components["path"], entry.get("path_prefix")):
        return False
    return True


def _check_hmac_tier_policy(
    tier: str,
    event_id: Optional[str],
    body_bytes: bytes,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate HMAC readiness for staging/prod before POST.

    Sandbox tier skips this gate (fail-open unsigned unchanged).
    Staging/prod require HMAC_ENABLED, non-empty secret, non-empty event_id,
    and successful signing dry-run.

    Returns (allowed, blocked_reason, blocked_rule).
    """
    if tier == DEFAULT_TIER:
        return True, None, None

    if not _is_truthy_env_flag(ENV_HMAC_ENABLED):
        _logger.warning(
            "HMAC tier gate blocked: tier=%s rule=hmac_disabled",
            tier,
        )
        return False, "blocked_by_hmac_tier_policy", "hmac_disabled"

    secret = os.getenv(ENV_HMAC_SECRET, "").strip()
    if not secret:
        _logger.warning(
            "HMAC tier gate blocked: tier=%s rule=hmac_secret_missing",
            tier,
        )
        return False, "blocked_by_hmac_tier_policy", "hmac_secret_missing"

    resolved_event_id = str(event_id).strip() if event_id is not None else ""
    if not resolved_event_id:
        _logger.warning(
            "HMAC tier gate blocked: tier=%s rule=hmac_event_id_missing",
            tier,
        )
        return False, "blocked_by_hmac_tier_policy", "hmac_event_id_missing"

    try:
        config = _get_hmac_config()
        sign_secret = config["secret"]
        if not sign_secret:
            return False, "blocked_by_hmac_tier_policy", "hmac_secret_missing"
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        message = _build_hmac_signed_message(timestamp, resolved_event_id, body_bytes)
        digest_hex = _compute_hmac_sha256_hex(sign_secret, message)
        if not digest_hex:
            raise ValueError("empty HMAC digest")
    except Exception as exc:
        _logger.warning(
            "HMAC tier gate blocked: tier=%s rule=hmac_signing_failed error=%s",
            tier,
            exc,
        )
        return False, "blocked_by_hmac_tier_policy", "hmac_signing_failed"

    return True, None, None


def _check_url_tier_policy(
    url: str,
    tier: str,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate URL against tier policy.

    Returns (allowed, blocked_reason, blocked_rule).
    """
    components = _parse_webhook_url(url)
    if components is None:
        return False, "blocked_by_url_tier_policy", "invalid_url"

    if tier == DEFAULT_TIER:
        if _is_safe_sandbox_url(url):
            return True, None, None
        return False, "blocked_by_url_tier_policy", "sandbox_localhost_only"

    if components["scheme"] != "https":
        return False, "blocked_by_url_tier_policy", "https_required"

    if _is_bare_ip(components["host"]):
        return False, "blocked_by_url_tier_policy", "bare_ip_forbidden"

    entries, parse_ok = _get_url_allowlist_entries()
    if not parse_ok or not entries:
        _logger.warning(
            "URL tier gate blocked: %s unset or invalid for tier=%s",
            ENV_URL_ALLOWLIST,
            tier,
        )
        return False, "blocked_by_url_tier_policy", "url_allowlist_missing"

    for entry in entries:
        if _url_matches_allowlist_entry(components, entry):
            return True, None, None

    _logger.warning(
        "URL tier gate blocked: host/path not in allowlist for tier=%s",
        tier,
    )
    return False, "blocked_by_url_tier_policy", "url_allowlist_mismatch"


def _is_safe_sandbox_url(url: str) -> bool:
    """Validate URL is safe for sandbox testing.
    
    Allowed:
    - localhost (any port)
    - 127.0.0.1 (any port)
    - http:// or https:// schemes only
    
    Blocked:
    - Non-http schemes (ftp, file, etc.)
    - Private IP ranges (future: could expand for prod guard)
    """
    if not url:
        return False
    
    # Must start with http:// or https://
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    
    # Extract host part
    try:
        # Simple URL parsing (sufficient for sandbox)
        if "://" in url:
            scheme, rest = url.split("://", 1)
            host_part = rest.split("/")[0]
            # Remove port if present
            if ":" in host_part:
                host = host_part.split(":")[0]
            else:
                host = host_part
        else:
            return False
    except Exception:
        return False
    
    # Allow localhost and 127.0.0.1 (sandbox only)
    allowed_hosts = {"localhost", "127.0.0.1", "127.0.0.1"}
    return host in allowed_hosts


def _send_http_post(
    url: str,
    payload: Dict[str, Any],
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """Send HTTP POST to webhook endpoint (synchronous, blocking).
    
    Returns result dict with http_status, response_body, error info.
    This is a simple urllib-based implementation for sandbox use.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Sent-At": _utc_now_iso(),
        "X-Webhook-Version": WEBHOOK_SCHEMA_VERSION,
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    _apply_hmac_headers(
        headers,
        event_id=payload.get("event_id"),
        body_bytes=data,
    )

    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            try:
                body = resp.read().decode("utf-8")
            except Exception:
                body = ""
            return {
                "http_status": status,
                "response_body": body,
                "error": None,
                "timeout": False,
            }
    except urllib.error.HTTPError as e:
        # HTTP error (4xx, 5xx) - still a valid HTTP response
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        return {
            "http_status": e.code,
            "response_body": body,
            "error": f"HTTP {e.code}: {e.reason}",
            "timeout": False,
        }
    except urllib.error.URLError as e:
        # Connection error, etc.
        return {
            "http_status": None,
            "response_body": None,
            "error": f"URL error: {e.reason}",
            "timeout": False,
        }
    except TimeoutError:
        return {
            "http_status": None,
            "response_body": None,
            "error": "Request timeout",
            "timeout": True,
        }
    except Exception as e:
        return {
            "http_status": None,
            "response_body": None,
            "error": f"Exception: {e}",
            "timeout": False,
        }


def send_webhook_notification(
    event: Dict[str, Any],
    endpoint_config: Optional[Dict[str, Any]] = None,
    *,
    case_ref: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Send notification via webhook with sandbox controls.
    
    This is the primary entry point used by notification_dispatch_v1.
    
    Args:
        event: The notification event envelope
        endpoint_config: Optional override config. If None, reads from env.
        case_ref: Optional case_ref (read from event if not provided)
        dry_run: If True, log only without HTTP call (overrides env)
    
    Returns:
        Dict with standardized result shape:
        {
            "ok": bool,
            "message": str,
            "event_id": str | None,
            "webhook_result": {
                "dispatched": bool,
                "dry_run": bool,
                "endpoint_url": str | None,
                "http_status": int | None,
                "response_body": str | None,
                "error": str | None,
                "timestamp": str,
                "case_allowed": bool,
            }
        }
    """
    event_id = event.get("event_id")
    event_type = event.get("event_type", "unknown")
    resolved_case_ref = case_ref or event.get("case_ref", "")
    
    # Check if webhook is enabled
    if not is_webhook_enabled_via_env():
        return {
            "ok": True,
            "message": f"Webhook disabled (GOV_NOTIFICATION_WEBHOOK_ENABLED not set): {event_type}",
            "event_id": event_id,
            "webhook_result": {
                "dispatched": False,
                "dry_run": True,
                "endpoint_url": None,
                "http_status": None,
                "response_body": None,
                "error": None,
                "timestamp": _utc_now_iso(),
                "case_allowed": False,
            },
        }
    
    # Check allowlist
    allowlist = _get_allowlist_patterns()
    case_allowed = _case_ref_matches_allowlist(resolved_case_ref, allowlist)
    
    if not case_allowed:
        # Allowlist not matched: dry-run mode
        return {
            "ok": True,
            "message": f"Webhook allowlist skip for case_ref={resolved_case_ref}: {event_type}",
            "event_id": event_id,
            "webhook_result": {
                "dispatched": False,
                "dry_run": True,
                "endpoint_url": None,
                "http_status": None,
                "response_body": None,
                "error": None,
                "timestamp": _utc_now_iso(),
                "case_allowed": False,
            },
        }
    
    # Get endpoint config
    if endpoint_config is None:
        endpoint_config = _get_webhook_endpoint_config()
    
    url = endpoint_config.get("url", "")
    if not url:
        # No URL configured: dry-run
        return {
            "ok": True,
            "message": f"Webhook URL not configured: {event_type}",
            "event_id": event_id,
            "webhook_result": {
                "dispatched": False,
                "dry_run": True,
                "endpoint_url": None,
                "http_status": None,
                "response_body": None,
                "error": None,
                "timestamp": _utc_now_iso(),
                "case_allowed": True,
            },
        }
    
    tier = _get_webhook_tier()
    url_allowed, blocked_reason, blocked_rule = _check_url_tier_policy(url, tier)
    if not url_allowed:
        error_msg = f"{blocked_reason}: {blocked_rule}"
        _logger.warning(
            "Webhook URL rejected by tier policy: tier=%s rule=%s url=%s",
            tier,
            blocked_rule,
            url,
        )
        return {
            "ok": True,
            "message": f"Webhook URL rejected (tier policy): {event_type}",
            "event_id": event_id,
            "webhook_result": {
                "dispatched": False,
                "dry_run": True,
                "endpoint_url": url,
                "http_status": None,
                "response_body": None,
                "error": error_msg,
                "blocked_reason": blocked_reason,
                "blocked_rule": blocked_rule,
                "tier": tier,
                "timestamp": _utc_now_iso(),
                "case_allowed": True,
            },
        }

    body_bytes = json.dumps(event, ensure_ascii=False).encode("utf-8")
    hmac_allowed, hmac_blocked_reason, hmac_blocked_rule = _check_hmac_tier_policy(
        tier,
        event_id,
        body_bytes,
    )
    if not hmac_allowed:
        error_msg = f"{hmac_blocked_reason}: {hmac_blocked_rule}"
        _logger.warning(
            "Webhook HMAC rejected by tier policy: tier=%s rule=%s event_id=%s",
            tier,
            hmac_blocked_rule,
            event_id,
        )
        return {
            "ok": True,
            "message": f"Webhook HMAC rejected (tier policy): {event_type}",
            "event_id": event_id,
            "webhook_result": {
                "dispatched": False,
                "dry_run": True,
                "endpoint_url": url,
                "http_status": None,
                "response_body": None,
                "error": error_msg,
                "blocked_reason": hmac_blocked_reason,
                "blocked_rule": hmac_blocked_rule,
                "tier": tier,
                "timestamp": _utc_now_iso(),
                "case_allowed": True,
            },
        }
    
    # Check explicit dry_run override
    if dry_run:
        return {
            "ok": True,
            "message": f"Webhook dry_run=True (explicit): {event_type}",
            "event_id": event_id,
            "webhook_result": {
                "dispatched": False,
                "dry_run": True,
                "endpoint_url": url,
                "http_status": None,
                "response_body": None,
                "error": None,
                "timestamp": _utc_now_iso(),
                "case_allowed": True,
            },
        }
    
    retry_config = _get_retry_config(tier=tier)
    retry_ready, retry_blocked_reason, retry_blocked_rule = _check_tier_retry_readiness(
        tier,
        retry_config,
    )
    if not retry_ready:
        error_msg = f"{retry_blocked_reason}: {retry_blocked_rule}"
        _logger.warning(
            "Webhook tier retry readiness blocked: tier=%s rule=%s url=%s",
            tier,
            retry_blocked_rule,
            url,
        )
        return {
            "ok": True,
            "message": f"Webhook POST blocked (tier retry policy): {event_type}",
            "event_id": event_id,
            "webhook_result": {
                "dispatched": False,
                "dry_run": True,
                "endpoint_url": url,
                "http_status": None,
                "response_body": None,
                "error": error_msg,
                "blocked_reason": retry_blocked_reason,
                "blocked_rule": retry_blocked_rule,
                "tier": tier,
                "timestamp": _utc_now_iso(),
                "case_allowed": True,
            },
        }

    timeout = endpoint_config.get("timeout", DEFAULT_TIMEOUT_SECONDS)
    _logger.info(
        "Sending webhook POST: event_id=%s event_type=%s case_ref=%s url=%s tier=%s",
        event_id, event_type, resolved_case_ref, url, tier,
    )

    result, attempt_count, retry_exhausted = _send_http_post_with_retry(
        url,
        event,
        timeout=timeout,
        retry_config=retry_config,
    )

    http_status = result.get("http_status")
    error = result.get("error")
    dispatched = _is_http_success(result)

    webhook_result_base: Dict[str, Any] = {
        "dispatched": dispatched,
        "dry_run": False,
        "endpoint_url": url,
        "http_status": http_status,
        "response_body": result.get("response_body"),
        "error": error,
        "last_error": error,
        "timestamp": _utc_now_iso(),
        "case_allowed": True,
        "attempt_count": attempt_count,
        "retry_exhausted": retry_exhausted,
    }

    # Fail-open: return ok=True even if HTTP failed
    # Main dispatch flow should not be blocked by webhook failure
    if not dispatched:
        _logger.warning(
            "Webhook POST failed (fail-open): event_id=%s error=%s attempts=%s retry_exhausted=%s",
            event_id,
            error,
            attempt_count,
            retry_exhausted,
        )
        _maybe_append_dlq_record(
            event=event,
            event_id=event_id,
            event_type=event_type,
            case_ref=resolved_case_ref,
            endpoint_url=url,
            webhook_result=webhook_result_base,
        )
        return {
            "ok": True,  # Fail-open: main flow continues
            "message": f"Webhook POST failed (fail-open): {error}",
            "event_id": event_id,
            "webhook_result": webhook_result_base,
        }

    _logger.info(
        "Webhook POST succeeded: event_id=%s http_status=%s attempts=%s",
        event_id,
        http_status,
        attempt_count,
    )
    return {
        "ok": True,
        "message": f"Webhook POST succeeded: HTTP {http_status}",
        "event_id": event_id,
        "webhook_result": webhook_result_base,
    }


# Dispatch handler entry point for notification_dispatch_v1 registry
def handle_webhook_dispatch(
    notification_event: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Handler for notification_dispatch_v1 registry.
    
    Signature matches dispatch handler contract:
    - Input: notification_event (dict), context (dict)
    - Output: dict with ok, message, ack
    
    Uses context["record_ack"] to record downstream ack.
    """
    event_id = notification_event.get("event_id")
    event_type = notification_event.get("event_type", "unknown")
    case_ref = notification_event.get("case_ref", "")
    handler_id = context.get("handler_id", "webhook_dispatch_v1")
    record_ack = context.get("record_ack")
    
    # Call webhook adapter
    result = send_webhook_notification(
        notification_event,
        case_ref=case_ref,
    )
    
    # Record downstream ack if available
    if callable(record_ack):
        if result.get("ok"):
            ack = record_ack(
                "received",
                message=result.get("message"),
            )
        else:
            ack = record_ack(
                "failed",
                message=result.get("message"),
            )
        result["ack"] = ack
    
    return result
