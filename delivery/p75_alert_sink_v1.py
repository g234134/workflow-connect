"""P7.5 local alert sink v1 (P75-G6) — file JSONL + stub HTTP.

Design SSOT: docs/p75-alert-sink-contract-v1.md
Schema: shared/schemas/p75_alert_sink_event_v1.json

Honest boundaries:
  - Local only; no PagerDuty/Slack/external prod send by default.
  - stub_http uses in-process recorder or optional loopback URL.
  - ≠ UI · ≠ Phase closure · ≠ dark-ops monitoring takeover.
"""

from __future__ import annotations

import json
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

SCHEMA_VERSION = "p75_alert_sink_event_v1"
DOC_REL = "docs/p75-alert-sink-contract-v1.md"
DEFAULT_SINK_REL = Path("outbox") / "p75_alert_sink" / "events.jsonl"
DEFAULT_SOURCE = "intake_slo_alert_probe_v1"

_REPO_ROOT = Path(__file__).resolve().parents[1]

# In-process stub recorder (tests / default stub_http without URL)
_STUB_INBOX: List[Dict[str, Any]] = []


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return (repo_root or _REPO_ROOT).resolve()


def resolve_sink_path(
    *,
    repo_root: Optional[Path] = None,
    sink_path_override: Optional[str] = None,
) -> Path:
    if sink_path_override:
        path = Path(sink_path_override)
        return path if path.is_absolute() else _repo_root(repo_root) / path
    return _repo_root(repo_root) / DEFAULT_SINK_REL


def clear_stub_inbox() -> None:
    """Test helper: reset in-process stub HTTP inbox."""
    _STUB_INBOX.clear()


def stub_inbox_snapshot() -> List[Dict[str, Any]]:
    return list(_STUB_INBOX)


def _normalize_severity(level: Any) -> str:
    raw = str(level or "warn").strip().lower()
    if raw in ("critical", "crit", "error"):
        return "critical"
    if raw in ("warning", "warn"):
        return "warn"
    return "warn"


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_sink_event(
    alert: Mapping[str, Any],
    *,
    source: str = DEFAULT_SOURCE,
    probe_snapshot: Optional[Mapping[str, Any]] = None,
    sink_meta: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build one p75_alert_sink_event_v1 dict (not yet delivered)."""
    code = str(alert.get("code") or "unknown")
    detail = str(alert.get("detail") or "")
    message = str(alert.get("message") or detail or code)
    event: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "source": source,
        "severity": _normalize_severity(alert.get("level") or alert.get("severity")),
        "code": code,
        "message": message,
        "detail": detail,
        "fired_at": _utc_now_iso(),
        "sink": {
            "mode": "file",
            "delivered": False,
            "path": None,
            "http_status": None,
            "target": None,
        },
    }
    if probe_snapshot is not None:
        event["probe_snapshot"] = dict(probe_snapshot)
    if sink_meta:
        event["sink"].update(dict(sink_meta))
    return event


def alerts_from_probe_result(probe_result: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Extract alerts[] from a P75-G5 probe result dict."""
    alerts = probe_result.get("alerts") or []
    if not isinstance(alerts, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in alerts:
        if isinstance(item, Mapping):
            out.append(dict(item))
    return out


def _deliver_file(
    event: Dict[str, Any],
    *,
    path: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    rel = None
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        rel = path.name
    event["sink"] = {
        "mode": "file",
        "delivered": True,
        "path": rel,
        "http_status": None,
        "target": None,
    }
    _append_jsonl(path, event)
    return event


def _deliver_stub_http(
    event: Dict[str, Any],
    *,
    stub_url: Optional[str] = None,
    force_fail: bool = False,
) -> Dict[str, Any]:
    if force_fail:
        event["sink"] = {
            "mode": "stub_http",
            "delivered": False,
            "path": None,
            "http_status": 500,
            "target": stub_url or "inprocess://stub",
        }
        return event

    if not stub_url:
        event["sink"] = {
            "mode": "stub_http",
            "delivered": True,
            "path": None,
            "http_status": 202,
            "target": "inprocess://stub",
        }
        _STUB_INBOX.append(json.loads(json.dumps(event, ensure_ascii=False)))
        return event

    payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        stub_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = int(getattr(resp, "status", 200) or 200)
        delivered = 200 <= status < 300
        event["sink"] = {
            "mode": "stub_http",
            "delivered": delivered,
            "path": None,
            "http_status": status,
            "target": stub_url,
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        event["sink"] = {
            "mode": "stub_http",
            "delivered": False,
            "path": None,
            "http_status": None,
            "target": stub_url,
        }
        event["metadata"] = {"error": str(exc)}
    return event


def emit_alerts(
    alerts: Sequence[Mapping[str, Any]],
    *,
    mode: str = "file",
    source: str = DEFAULT_SOURCE,
    probe_snapshot: Optional[Mapping[str, Any]] = None,
    sink_path_override: Optional[str] = None,
    stub_url: Optional[str] = None,
    force_fail: bool = False,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Emit alert list to local sink. Returns stable dict."""
    root = _repo_root(repo_root)
    mode_norm = (mode or "file").strip().lower()
    if mode_norm not in ("file", "stub_http"):
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "message": f"unsupported sink mode: {mode}",
            "sink_mode": mode,
            "emitted": 0,
            "events": [],
            "doc": DOC_REL,
        }

    if not alerts:
        return {
            "ok": True,
            "schema_version": SCHEMA_VERSION,
            "message": "no alerts to emit · ok",
            "sink_mode": mode_norm,
            "emitted": 0,
            "events": [],
            "doc": DOC_REL,
        }

    sink_path = resolve_sink_path(repo_root=root, sink_path_override=sink_path_override)
    events: List[Dict[str, Any]] = []
    failures = 0

    for alert in alerts:
        if not isinstance(alert, Mapping):
            continue
        event = build_sink_event(
            alert,
            source=source,
            probe_snapshot=probe_snapshot,
        )
        if mode_norm == "file":
            event = _deliver_file(event, path=sink_path, repo_root=root)
        else:
            event = _deliver_stub_http(
                event, stub_url=stub_url, force_fail=force_fail
            )
        if not event.get("sink", {}).get("delivered"):
            failures += 1
        events.append(event)

    ok = failures == 0 and len(events) > 0
    message = (
        f"sink mode={mode_norm} · emitted={len(events)} · failures={failures} · "
        f"≠ prod alert · ≠ UI"
    )
    result: Dict[str, Any] = {
        "ok": ok,
        "schema_version": SCHEMA_VERSION,
        "message": message,
        "sink_mode": mode_norm,
        "emitted": len(events),
        "events": events,
        "doc": DOC_REL,
    }
    if mode_norm == "file":
        try:
            result["sink_path"] = sink_path.relative_to(root).as_posix()
        except ValueError:
            result["sink_path"] = sink_path.name
    return result
