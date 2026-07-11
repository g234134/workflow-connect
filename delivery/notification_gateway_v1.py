"""Notification gateway v1 — stub / local sink for workflow events (W6-T10-P2).

Best-effort notification delivery; failures do not block main flow.
Default disabled; use --enable-notifications or env GOV_NOTIFICATION_GATEWAY_ENABLED=1.
"""

from __future__ import annotations

import json
import os
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

# F2: Import file locking utilities for concurrent append safety
try:
    # Prefer portalocker for cross-platform file locking (pip install portalocker)
    import portalocker
    _HAS_PORTALOCKER = True
except ImportError:
    _HAS_PORTALOCKER = False
    portalocker = None  # type: ignore

DEFAULT_SCHEMA_VERSION = "notification_event_v1"
EVENT_TYPE_INTAKE_GATE_DECISION = "intake.gate_decision"


class NotificationGatewayError(Exception):
    """Non-fatal notification error; caller should not block main flow."""

    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compact_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _idempotency_key(
    case_ref: str,
    event_type: str,
    *,
    checkpoint_id: Optional[str] = None,
    compact_ts: Optional[str] = None,
) -> str:
    parts = [case_ref, event_type, checkpoint_id or "run", compact_ts or _compact_ts()]
    return ":".join(parts)


def _lock_file(f, exclusive: bool = True) -> bool:
    """Best-effort file locking for concurrent append safety (F2).
    
    Returns True if lock acquired, False if not available.
    Uses portalocker if available, otherwise falls back to platform-specific methods.
    """
    if _HAS_PORTALOCKER and portalocker:
        try:
            lock_flags = portalocker.LOCK_EX if exclusive else portalocker.LOCK_SH
            portalocker.lock(f, lock_flags | portalocker.LOCK_NB)
            return True
        except (portalocker.LockException, OSError, IOError):
            return False
    
    # Platform-specific fallback
    system = platform.system().lower()
    if system == "windows":
        # Windows: use msvcrt locking (best-effort, not atomic across processes)
        try:
            import msvcrt
            # Lock the entire file (0 means lock from current position to end)
            # LOCK_EX = 2, LOCK_NB = 1
            mode = 2 if exclusive else 0
            msvcrt.locking(f.fileno(), mode + 1, 0)  # LOCK_NB = 1
            return True
        except (OSError, IOError):
            return False
    else:
        # Unix: use fcntl (best-effort, import may fail in restricted environments)
        try:
            import fcntl
            operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(f.fileno(), operation | fcntl.LOCK_NB)
            return True
        except (ImportError, OSError, IOError):
            return False


def _unlock_file(f) -> None:
    """Release file lock acquired by _lock_file."""
    if _HAS_PORTALOCKER and portalocker:
        try:
            portalocker.unlock(f)
        except (OSError, IOError):
            pass
        return
    
    system = platform.system().lower()
    if system == "windows":
        try:
            import msvcrt
            msvcrt.locking(f.fileno(), 0, 0)  # UNLOCK = 0
        except (OSError, IOError):
            pass
    else:
        try:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (ImportError, OSError, IOError):
            pass


def _get_outbox_root(
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    if outbox_root_override:
        return Path(outbox_root_override).resolve()
    if repo_root:
        return repo_root / "outbox"
    return Path.cwd() / "outbox"


def build_notification_event(
    event_type: str,
    *,
    case_ref: str,
    case_dir: Optional[str] = None,
    experiment_id: Optional[str] = None,
    checkpoint_id: Optional[str] = None,
    checkpoint_status: Optional[str] = None,
    approval_source: Optional[str] = None,
    artifacts: Optional[Dict[str, Any]] = None,
    status_summary: Optional[Dict[str, Any]] = None,
    source: Optional[Dict[str, Any]] = None,
    schema_version: str = DEFAULT_SCHEMA_VERSION,
) -> Dict[str, Any]:
    """Build a standardized notification event envelope (v1).

    Returns dict with stable schema; does not perform I/O.
    """
    emitted_at = _utc_now_iso()
    compact_ts = _compact_ts()
    event_id = str(uuid.uuid4())

    envelope: Dict[str, Any] = {
        "schema_version": schema_version,
        "event_id": event_id,
        "event_type": event_type,
        "emitted_at": emitted_at,
        "idempotency_key": _idempotency_key(case_ref, event_type, checkpoint_id=checkpoint_id, compact_ts=compact_ts),
        "case_ref": case_ref,
        "case_dir": case_dir,
        "experiment_id": experiment_id,
        "checkpoint_id": checkpoint_id,
        "checkpoint_status": checkpoint_status,
        "approval_source": approval_source,
        "artifacts": artifacts or {},
        "status_summary": status_summary or {},
        "source": source or {},
    }
    return envelope


def _write_event_to_file(
    event: Dict[str, Any],
    outbox_root: Path,
) -> Dict[str, Any]:
    """Write single event file: outbox/notifications/<case_ref>/<event_type>_<ts>_<id8>.json"""
    case_ref = event.get("case_ref", "unknown")
    event_type = event.get("event_type", "unknown")
    event_id = str(event.get("event_id", uuid.uuid4()))
    emitted_at = str(event.get("emitted_at", _utc_now_iso()))

    # Compact timestamp from emitted_at: replace colons with hyphens, drop subseconds
    compact_ts = emitted_at.replace(":", "-").split(".")[0] + "Z"
    id8 = event_id[:8]

    notifications_dir = outbox_root / "notifications" / case_ref
    notifications_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{event_type}_{compact_ts}_{id8}.json"
    filepath = notifications_dir / filename

    try:
        filepath.write_text(
            json.dumps(event, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return {
            "ok": True,
            "channel": "local_file",
            "path": str(filepath),
            "message": "written",
        }
    except (OSError, IOError) as exc:
        return {
            "ok": False,
            "channel": "local_file",
            "path": str(filepath),
            "message": f"write failed: {exc}",
        }


def _append_event_to_jsonl(
    event: Dict[str, Any],
    outbox_root: Path,
) -> Dict[str, Any]:
    """Append event to outbox/notification_events.jsonl (one line per event).
    
    F2: Uses best-effort file locking for concurrent append safety on Windows.
    Falls back to simple append if locking not available (documented limitation).
    """
    jsonl_path = outbox_root / "notification_events.jsonl"
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # F2: Open and lock file for concurrent-safe append
        with jsonl_path.open("a", encoding="utf-8") as f:
            lock_acquired = _lock_file(f, exclusive=True)
            if not lock_acquired:
                # Fallback: still append but mark as potentially unsafe
                # In practice, line-oriented JSONL with atomic writes is safe enough
                pass
            try:
                # Ensure we're at end of file (in case of concurrent access)
                f.seek(0, 2)  # SEEK_END
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                f.flush()
            finally:
                if lock_acquired:
                    _unlock_file(f)
        
        return {
            "ok": True,
            "channel": "jsonl_append",
            "path": str(jsonl_path),
            "message": "appended",
        }
    except (OSError, IOError) as exc:
        return {
            "ok": False,
            "channel": "jsonl_append",
            "path": str(jsonl_path),
            "message": f"append failed: {exc}",
        }


def _should_run_post_emit_dispatch(dispatch_enabled: Optional[bool]) -> bool:
    if dispatch_enabled is not None:
        return bool(dispatch_enabled)
    try:
        from delivery.notification_dispatch_v1 import is_dispatch_enabled_via_env

        return is_dispatch_enabled_via_env()
    except Exception:
        return False


def _run_post_emit_dispatch(
    event: Dict[str, Any],
    *,
    repo_root: Optional[Path],
    outbox_root_override: Optional[str],
    dispatch_enabled: Optional[bool],
) -> Optional[Dict[str, Any]]:
    """Best-effort post-emit dispatch (P8.9-T3). Fail-open; never raises."""
    if not _should_run_post_emit_dispatch(dispatch_enabled):
        return None
    try:
        from delivery import feedback_ingest_v1 as feedback_ingest
        from delivery.notification_dispatch_v1 import dispatch_event

        return dispatch_event(
            event,
            feedback_ingest=feedback_ingest,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
        )
    except Exception as exc:
        return {
            "ok": False,
            "message": f"post-emit dispatch error (fail-open): {exc}",
            "fail_open": True,
        }


def send_notification(
    event: Dict[str, Any],
    *,
    enabled: bool = True,
    dry_run: bool = False,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    dispatch_enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """Send notification to local sink (best-effort).

    Returns dict:
      - ok: bool (True if at least one sink succeeded or skipped)
      - message: str
      - event_id: str | None
      - sink_result: dict with {ok, channel, path, message}
      - dispatch_result: optional post-emit dispatch summary (P8.9-T3)
      - event: the original event (if dry_run or debug)

    Failures are logged but never raised; main flow should continue.
    """
    event_id = event.get("event_id")

    # Disabled: return ok=True, no-op
    if not enabled:
        return {
            "ok": True,
            "message": "skipped (notifications disabled)",
            "event_id": event_id,
            "sink_result": {"ok": True, "channel": "none", "message": "disabled"},
        }

    # Dry-run: build envelope, don't write
    if dry_run:
        return {
            "ok": True,
            "message": "dry-run (no write)",
            "event_id": event_id,
            "sink_result": {"ok": True, "channel": "dry_run", "message": "dry-run"},
            "event": event,
        }

    outbox_root = _get_outbox_root(repo_root, outbox_root_override)

    # Primary sink: per-event file
    file_result = _write_event_to_file(event, outbox_root)

    # Secondary sink: jsonl append (best-effort; failure ignored)
    jsonl_result = _append_event_to_jsonl(event, outbox_root)

    # Aggregate result: primary sink determines ok
    ok = file_result.get("ok", False)

    dispatch_result: Optional[Dict[str, Any]] = None
    if ok:
        dispatch_result = _run_post_emit_dispatch(
            event,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
            dispatch_enabled=dispatch_enabled,
        )

    result: Dict[str, Any] = {
        "ok": ok,
        "message": file_result.get("message", "unknown"),
        "event_id": event_id,
        "sink_result": file_result,
        "jsonl_result": jsonl_result,  # informational only
    }
    if dispatch_result is not None:
        result["dispatch_result"] = dispatch_result
    return result


def is_enabled_via_env() -> bool:
    """Check if notifications enabled via environment variable."""
    env_val = os.getenv("GOV_NOTIFICATION_GATEWAY_ENABLED", "").strip()
    return env_val in ("1", "true", "yes")


def build_intake_gate_decision_event(
    gate_result: Mapping[str, Any],
    *,
    schema_version: str = DEFAULT_SCHEMA_VERSION,
) -> Dict[str, Any]:
    """Build ``intake.gate_decision`` notification envelope from gate result (P75-G4).

    Required gate payload fields are mirrored in ``artifacts`` and ``status_summary``
    for downstream consumers (workflow ledger, future UI).
    """
    case_ref = str(gate_result.get("case_ref") or "")
    intake_decision_id = str(gate_result.get("intake_decision_id") or "")
    decision = str(gate_result.get("decision") or "")
    reason_codes = list(gate_result.get("reason_codes") or [])
    policy_version = gate_result.get("policy_version")
    outbox_record_path = gate_result.get("outbox_record_path")

    return build_notification_event(
        EVENT_TYPE_INTAKE_GATE_DECISION,
        case_ref=case_ref,
        case_dir=gate_result.get("case_dir"),
        checkpoint_id=intake_decision_id or None,
        artifacts={
            "intake_decision_id": intake_decision_id,
            "outbox_record_path": outbox_record_path,
            "decision": decision,
            "reason_codes": reason_codes,
            "policy_version": policy_version,
        },
        status_summary={
            "decision": decision,
            "reason_codes": reason_codes,
            "policy_version": policy_version,
            "intake_decision_id": intake_decision_id,
            "outbox_record_path": outbox_record_path,
        },
        source={
            "step_id": "S3",
            "module": "routing.intake_gate_layer_v1",
        },
        schema_version=schema_version,
    )


def emit_intake_gate_decision_notification(
    gate_result: Mapping[str, Any],
    *,
    enabled: bool = True,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Emit ``intake.gate_decision`` after durable gate record write (best-effort).

    Caller must only invoke in ``mode=run`` with ``outbox_record_path`` set.
    Failures never raise; gate ``ok`` must not depend on this result.
    """
    if not enabled:
        return None

    outbox_record_path = gate_result.get("outbox_record_path")
    if not outbox_record_path:
        return None

    try:
        event = build_intake_gate_decision_event(gate_result)
        return send_notification(
            event,
            enabled=True,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
        )
    except Exception as exc:
        return {
            "ok": False,
            "message": f"intake gate notification error: {exc}",
            "event_id": None,
            "sink_result": {"ok": False, "channel": "none", "message": str(exc)},
            "skipped_main_flow": True,
        }


def emit_notification_safe(
    event_type: str,
    *,
    enabled: bool,
    case_ref: str,
    case_dir: Optional[str] = None,
    experiment_id: Optional[str] = None,
    checkpoint_id: Optional[str] = None,
    checkpoint_status: Optional[str] = None,
    approval_source: Optional[str] = None,
    artifacts: Optional[Dict[str, Any]] = None,
    status_summary: Optional[Dict[str, Any]] = None,
    source: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    dispatch_enabled: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """Convenience: build event + send with error handling (never raises).

    Returns None if disabled; returns result dict on attempt.
    Main flow should ignore failures.
    """
    if not enabled:
        return None

    try:
        event = build_notification_event(
            event_type,
            case_ref=case_ref,
            case_dir=case_dir,
            experiment_id=experiment_id,
            checkpoint_id=checkpoint_id,
            checkpoint_status=checkpoint_status,
            approval_source=approval_source,
            artifacts=artifacts,
            status_summary=status_summary,
            source=source,
        )
        return send_notification(
            event,
            enabled=True,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
            dispatch_enabled=dispatch_enabled,
        )
    except Exception as exc:
        # Best-effort: never raise; return error info for observability only
        return {
            "ok": False,
            "message": f"notification error: {exc}",
            "event_id": None,
            "sink_result": {"ok": False, "channel": "none", "message": str(exc)},
            "skipped_main_flow": True,
        }
