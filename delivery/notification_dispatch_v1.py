"""Downstream notification dispatch v1 (P8.9-T3).

Pluggable local handler registry for workflow notification events.
Post-emit dispatch is fail-open; errors never block gateway emit.
"""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

from delivery.feedback_ingest_v1 import record_downstream_ack

DISPATCH_SCHEMA_VERSION = "notification_dispatch_v1"
HANDLERS_CONFIG_REL = Path("routing") / "notification_handlers_v1.yaml"

HandlerCallable = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]

_logger = logging.getLogger(__name__)


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    return Path(__file__).resolve().parents[1]


def is_dispatch_enabled_via_env() -> bool:
    """True when GOV_NOTIFICATION_DISPATCH_ENABLED=1|true|yes."""
    val = os.getenv("GOV_NOTIFICATION_DISPATCH_ENABLED", "").strip().lower()
    return val in ("1", "true", "yes")


def is_controlled_notify_on_dispatch_enabled() -> bool:
    """True when GOV_CONTROLLED_NOTIFY_ON_DISPATCH=1|true|yes."""
    val = os.getenv("GOV_CONTROLLED_NOTIFY_ON_DISPATCH", "").strip().lower()
    return val in ("1", "true", "yes")


def is_webhook_dispatch_enabled() -> bool:
    """True when GOV_NOTIFICATION_WEBHOOK_ENABLED=1|true|yes."""
    val = os.getenv("GOV_NOTIFICATION_WEBHOOK_ENABLED", "").strip().lower()
    return val in ("1", "true", "yes")


def _resolve_entrypoint(entrypoint: str) -> HandlerCallable:
    if ":" not in entrypoint:
        raise ValueError(f"invalid entrypoint (expected module:callable): {entrypoint!r}")
    module_name, attr_name = entrypoint.split(":", 1)
    module = importlib.import_module(module_name)
    fn = getattr(module, attr_name)
    if not callable(fn):
        raise TypeError(f"entrypoint not callable: {entrypoint!r}")
    return fn


@dataclass
class HandlerRegistry:
    """Maps handler_id + event_types to local Python callables."""

    handlers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _event_index: Dict[str, List[str]] = field(default_factory=dict)

    def register_handler(
        self,
        handler_id: str,
        event_types: List[str],
        handler: HandlerCallable,
        *,
        description: str = "",
        enabled_when: Optional[str] = None,
    ) -> None:
        self.handlers[handler_id] = {
            "handler_id": handler_id,
            "event_types": list(event_types),
            "handler": handler,
            "description": description,
            "enabled_when": enabled_when,
        }
        for event_type in event_types:
            self._event_index.setdefault(event_type, []).append(handler_id)

    def find_handlers(self, event_type: str) -> List[Tuple[str, HandlerCallable]]:
        handler_ids = self._event_index.get(event_type, [])
        out: List[Tuple[str, HandlerCallable]] = []
        for handler_id in handler_ids:
            spec = self.handlers.get(handler_id)
            if not spec:
                continue
            if not self._handler_enabled(spec):
                continue
            out.append((handler_id, spec["handler"]))
        return out

    def _handler_enabled(self, spec: Dict[str, Any]) -> bool:
        gate = spec.get("enabled_when")
        if gate == "controlled_notify_on_dispatch":
            return is_controlled_notify_on_dispatch_enabled()
        if gate == "webhook_dispatch":
            return is_webhook_dispatch_enabled()
        return True

    def list_handlers(self) -> List[Dict[str, Any]]:
        return [
            {
                "handler_id": spec["handler_id"],
                "event_types": spec["event_types"],
                "description": spec.get("description", ""),
                "enabled_when": spec.get("enabled_when"),
                "enabled": self._handler_enabled(spec),
            }
            for spec in self.handlers.values()
        ]


def load_handler_registry_from_yaml(
    config_path: Path,
    *,
    repo_root: Optional[Path] = None,
) -> HandlerRegistry:
    """Load handler registry from YAML config."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"handler config not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("handler config must be a mapping")

    registry = HandlerRegistry()
    for item in data.get("handlers") or []:
        if not isinstance(item, dict):
            continue
        handler_id = str(item.get("handler_id", "")).strip()
        entrypoint = str(item.get("entrypoint", "")).strip()
        event_types = item.get("event_types") or []
        if not handler_id or not entrypoint or not event_types:
            continue
        handler = _resolve_entrypoint(entrypoint)
        registry.register_handler(
            handler_id,
            [str(et) for et in event_types],
            handler,
            description=str(item.get("description") or ""),
            enabled_when=item.get("enabled_when"),
        )
    return registry


def load_default_handler_registry(*, repo_root: Optional[Path] = None) -> HandlerRegistry:
    """Load handlers YAML from repo; falls back to package root when override lacks config."""
    root = _repo_root(repo_root)
    config_path = root / HANDLERS_CONFIG_REL
    if not config_path.is_file():
        root = Path(__file__).resolve().parents[1]
        config_path = root / HANDLERS_CONFIG_REL
    return load_handler_registry_from_yaml(config_path, repo_root=root)


def _build_dispatch_context(
    notification_event: Dict[str, Any],
    *,
    handler_id: str,
    repo_root: Optional[Path],
    outbox_root_override: Optional[str],
) -> Dict[str, Any]:
    event_id = str(notification_event.get("event_id", ""))

    def _record_ack(status: str, message: str | None = None) -> dict:
        return record_downstream_ack(
            event_id,
            handler_id,
            status,
            message=message,
            case_ref=str(notification_event.get("case_ref") or "") or None,
            repo_root=repo_root,
            outbox_root_override=outbox_root_override,
        )

    return {
        "handler_id": handler_id,
        "repo_root": _repo_root(repo_root),
        "outbox_root_override": outbox_root_override,
        "record_ack": _record_ack,
    }


def dispatch_event(
    notification_event: Dict[str, Any],
    *,
    handler_registry: Optional[HandlerRegistry] = None,
    feedback_ingest: Any = None,
    repo_root: Path | None = None,
    outbox_root_override: str | None = None,
) -> dict:
    """Best-effort dispatch to registered local handlers (fail-open, never raises)."""
    event_type = str(notification_event.get("event_type", ""))
    event_id = notification_event.get("event_id")

    try:
        if handler_registry is not None:
            registry = handler_registry
        else:
            root = _repo_root(repo_root)
            registry = load_default_handler_registry(repo_root=root)
        handlers = registry.find_handlers(event_type)
        if not handlers:
            return {
                "ok": True,
                "schema_version": DISPATCH_SCHEMA_VERSION,
                "event_id": event_id,
                "event_type": event_type,
                "message": f"no handlers registered for event_type={event_type!r}",
                "handlers_invoked": [],
                "handler_results": [],
                "noop": True,
            }

        handler_results: List[Dict[str, Any]] = []
        handlers_invoked: List[str] = []

        for handler_id, handler_fn in handlers:
            handlers_invoked.append(handler_id)
            context = _build_dispatch_context(
                notification_event,
                handler_id=handler_id,
                repo_root=repo_root,
                outbox_root_override=outbox_root_override,
            )
            if feedback_ingest is not None and hasattr(feedback_ingest, "record_downstream_ack"):
                context["feedback_ingest"] = feedback_ingest

            try:
                result = handler_fn(notification_event, context)
                if not isinstance(result, dict):
                    result = {"ok": False, "message": "handler returned non-dict"}
            except Exception as exc:
                _logger.debug("dispatch handler %s failed: %s", handler_id, exc)
                ack = context["record_ack"]("failed", message=str(exc))
                handler_results.append(
                    {
                        "handler_id": handler_id,
                        "ok": False,
                        "message": str(exc),
                        "ack": ack,
                    }
                )
                continue

            if result.get("ok"):
                ack = result.get("ack")
                if not isinstance(ack, dict):
                    ack = context["record_ack"]("received", message=result.get("message"))
            else:
                ack = result.get("ack")
                if not isinstance(ack, dict):
                    ack = context["record_ack"](
                        "failed",
                        message=str(result.get("message") or "handler returned ok=false"),
                    )

            handler_results.append(
                {
                    "handler_id": handler_id,
                    "ok": bool(result.get("ok")),
                    "message": result.get("message"),
                    "ack": ack,
                    "detail": {k: v for k, v in result.items() if k not in {"ok", "message", "ack"}},
                }
            )

        all_ok = all(r.get("ok") for r in handler_results) if handler_results else True
        return {
            "ok": all_ok,
            "schema_version": DISPATCH_SCHEMA_VERSION,
            "event_id": event_id,
            "event_type": event_type,
            "message": f"dispatched to {len(handlers_invoked)} handler(s)",
            "handlers_invoked": handlers_invoked,
            "handler_results": handler_results,
            "noop": False,
        }
    except Exception as exc:
        return {
            "ok": False,
            "schema_version": DISPATCH_SCHEMA_VERSION,
            "event_id": event_id,
            "event_type": event_type,
            "message": f"dispatch error (fail-open): {exc}",
            "handlers_invoked": [],
            "handler_results": [],
            "fail_open": True,
        }


def handle_bundle_ready_log(
    notification_event: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Local log handler for delivery.bundle_ready; records downstream ack."""
    case_ref = notification_event.get("case_ref")
    event_id = notification_event.get("event_id")
    _logger.info(
        "dispatch bundle_ready: event_id=%s case_ref=%s handler=%s",
        event_id,
        case_ref,
        context.get("handler_id"),
    )
    ack = context["record_ack"]("received", message="bundle_ready local log handler ok")
    return {
        "ok": True,
        "message": "bundle_ready logged locally",
        "ack": ack,
        "logged": True,
    }


def handle_controlled_notify_bundle_ready(
    notification_event: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Invoke W7-T3 controlled notify experiment when dispatch gate is on."""
    from delivery.controlled_notify_experiment_v1 import run_controlled_notify_experiment

    case_dir = notification_event.get("case_dir") or f"cases/{notification_event.get('case_ref', '')}"
    result = run_controlled_notify_experiment(
        case_dir,
        dry_run=False,
        repo_root=context.get("repo_root"),
        outbox_root_override=context.get("outbox_root_override"),
    )
    if result.get("ok"):
        ack = context["record_ack"](
            "received",
            message=str(result.get("message") or "controlled notify completed"),
        )
        return {
            "ok": True,
            "message": result.get("message"),
            "ack": ack,
            "notify_outbox_path": result.get("outbox_path"),
        }

    ack = context["record_ack"](
        "failed",
        message=str(result.get("message") or "controlled notify failed"),
    )
    return {
        "ok": False,
        "message": result.get("message"),
        "ack": ack,
        "blocked": bool(result.get("blocked")),
        "missing": result.get("missing"),
    }


def handle_run_terminal_log(
    notification_event: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Log handler for run.completed / run.blocked terminal events."""
    event_type = notification_event.get("event_type")
    _logger.info(
        "dispatch terminal: event_type=%s event_id=%s handler=%s",
        event_type,
        notification_event.get("event_id"),
        context.get("handler_id"),
    )
    ack = context["record_ack"]("received", message=f"{event_type} local log handler ok")
    return {
        "ok": True,
        "message": f"{event_type} logged locally",
        "ack": ack,
        "logged": True,
    }


def handle_webhook_dispatch(
    notification_event: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Webhook sink handler for notification dispatch (WD-P7-T2).
    
    Dispatches to external HTTP endpoint when:
    - GOV_NOTIFICATION_WEBHOOK_ENABLED=1|true|yes
    - case_ref matches GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST glob patterns
    - Target URL is sandbox-safe (localhost/127.0.0.1 only in v1)
    
    Fail-open: webhook failures never change dispatch_event "ok".
    """
    # Import here to avoid circular dependency issues
    from delivery.notification_webhook_adapter_v1 import send_webhook_notification

    event_id = notification_event.get("event_id")
    case_ref = notification_event.get("case_ref", "")
    record_ack = context.get("record_ack")

    result = send_webhook_notification(
        notification_event,
        case_ref=case_ref,
    )

    # Record downstream ack
    if callable(record_ack):
        webhook_result = result.get("webhook_result", {})
        if result.get("ok") and webhook_result.get("dispatched"):
            ack = record_ack("received", message=result.get("message"))
        elif result.get("ok"):
            # Dry-run / skipped is still "received" from dispatch perspective
            ack = record_ack("received", message=result.get("message"))
        else:
            ack = record_ack("failed", message=result.get("message"))
        result["ack"] = ack

    _logger.debug(
        "webhook dispatch: event_id=%s case_ref=%s dispatched=%s",
        event_id,
        case_ref,
        result.get("webhook_result", {}).get("dispatched", False),
    )
    return result
