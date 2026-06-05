"""

Monitoring subagent executor v0.2 (Sprint 4 · O-2a).

Consumes C-1 routing signals (``metadata.subagent_route``, ``_subagent_target_agent_id``)

and runs a read-only monitoring service adapter when routed to monitoring, with safe

fallback to the v0.1 in-process stub. Does not start LangGraph workers or HQ

``task_routing``.

"""

from __future__ import annotations

import importlib
import importlib.util

import re

import sys

from pathlib import Path

from typing import Any, Callable, Mapping

from subagents.context_routing import MONITORING_AGENT_ID

_MONITORING_GRAPH_MODULE: Any | None = None


def _load_monitoring_graph_module() -> Any:
    """Import repo-root ``core/monitoring_graph`` without conflicting with dark ``core``."""
    global _MONITORING_GRAPH_MODULE
    if _MONITORING_GRAPH_MODULE is not None:
        return _MONITORING_GRAPH_MODULE
    graph_path = _repo_root() / "core" / "monitoring_graph.py"
    if not graph_path.is_file():
        raise ImportError("core/monitoring_graph.py not found at repo root")
    spec = importlib.util.spec_from_file_location("tang_monitoring_graph", graph_path)
    if spec is None or spec.loader is None:
        raise ImportError("failed to load monitoring_graph spec")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _MONITORING_GRAPH_MODULE = mod
    return mod


def is_monitoring_graph_enabled(*, explicit: bool | None = None) -> bool:
    return _load_monitoring_graph_module().is_monitoring_graph_enabled(explicit=explicit)


def run_monitoring_graph(graph_input: Mapping[str, Any]) -> dict[str, Any]:
    return _load_monitoring_graph_module().run_monitoring_graph(graph_input)


def extract_monitoring_graph_public_summary(
    graph_result: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    return _load_monitoring_graph_module().extract_monitoring_graph_public_summary(graph_result)


ENV_MONITORING_GRAPH_ENABLED = "GOV_MONITORING_GRAPH_ENABLED"

EXECUTOR_VERSION = "v0.1-stub"

EXECUTOR_ADAPTER_ID = "monitoring-service-adapter"

FALLBACK_STUB = EXECUTOR_VERSION

MONITORING_SUBAGENT_ID = "monitoring-subagent"

_MONITORING_ROUTE_IDS = frozenset(

    {

        MONITORING_AGENT_ID,

        MONITORING_SUBAGENT_ID,

        "monitoring",

    }

)

_DASHBOARD_SUMMARY_RE = re.compile(

    r"(?:dashboard[-_\s]?summary|/monitoring/dashboard[-_\s]?summary)",

    re.I,

)

_OVERVIEW_RE = re.compile(r"(?:/monitoring/overview\b|\boverview\b)", re.I)

_COST_TREND_RE = re.compile(r"(?:cost[-_\s]?trend|/monitoring/cost[-_\s]?trend)", re.I)

_ERROR_TREND_RE = re.compile(r"(?:error[-_\s]?trend|/monitoring/error[-_\s]?trend)", re.I)

_LATENCY_TREND_RE = re.compile(

    r"(?:latency[-_\s]?trend|/monitoring/latency[-_\s]?trend)", re.I

)

_DLQ_RE = re.compile(r"(?:\bdlq\b|/monitoring/dlq)", re.I)

_ALERTS_RE = re.compile(r"(?:\balerts?\b|/monitoring/alerts)", re.I)

# In-process audit log for v0.1 stub (tests may clear via ``reset_monitoring_task_log``).

_monitoring_task_log: list[dict[str, Any]] = []

def reset_monitoring_task_log() -> None:

    """Clear in-memory monitoring task log (test helper)."""

    _monitoring_task_log.clear()

def get_monitoring_task_log() -> list[dict[str, Any]]:

    """Return a shallow copy of the in-memory monitoring task log."""

    return list(_monitoring_task_log)

def _repo_root() -> Path:

    return Path(__file__).resolve().parents[1]

def _gov_core_system_root() -> Path:

    return _repo_root() / "01_Environments" / "python_venvs" / "gov_core_system"

def _purge_non_gov_core_modules() -> None:

    """Drop cached ``core`` tree when it was loaded from repo-root, not dark cabin."""

    core_mod = sys.modules.get("core")

    if core_mod is None:

        return

    core_file = str(getattr(core_mod, "__file__", "") or "").replace("\\", "/")

    if "gov_core_system" in core_file:

        return

    for key in list(sys.modules):

        if key == "core" or key.startswith("core."):

            del sys.modules[key]

def _load_monitoring_service_module() -> Any:

    """

    Import dark-cabin ``core.monitoring_service`` (read-only query layer).

    Inserts gov_core_system on ``sys.path`` when needed; does not write PG or run ingest.

    """

    gov_root = _gov_core_system_root()

    if not gov_root.is_dir():

        raise ImportError("gov_core_system root not found")

    gov_s = str(gov_root)

    if gov_s not in sys.path:

        sys.path.insert(0, gov_s)

    _purge_non_gov_core_modules()

    return importlib.import_module("core.monitoring_service")

def _task_text(task_input: Mapping[str, Any]) -> str:

    parts: list[str] = []

    for key in ("goal", "query", "task_type", "domain", "description"):

        val = task_input.get(key)

        if val is not None and str(val).strip():

            parts.append(str(val))

    return " ".join(parts).lower()

def _int_param(task_input: Mapping[str, Any], *keys: str, default: int) -> int:

    for key in keys:

        raw = task_input.get(key)

        if raw is None:

            continue

        try:

            return max(1, int(raw))

        except (TypeError, ValueError):

            continue

    return default

def resolve_monitoring_service_query(

    task_input: Mapping[str, Any] | None,

) -> tuple[str, dict[str, Any]]:

    """

    Map task_input text/params to a monitoring_service read function name + kwargs.

    Aligns with ``monitoring_api`` routes (overview, dashboard-summary, trends, dlq, alerts).

    """

    ti = dict(task_input) if isinstance(task_input, Mapping) else {}

    text = _task_text(ti)

    if _DASHBOARD_SUMMARY_RE.search(text):

        return "get_dashboard_summary", {

            "hours": _int_param(ti, "hours", "monitoring_hours", default=24),

            "cost_days": _int_param(ti, "cost_days", "monitoring_cost_days", default=7),

            "error_days": _int_param(ti, "error_days", default=1),

            "alert_limit": _int_param(ti, "alert_limit", default=15),

            "dlq_limit": _int_param(ti, "dlq_limit", default=10),

        }

    if _COST_TREND_RE.search(text):

        return "get_cost_trend", {

            "days": _int_param(ti, "days", "cost_days", default=7),

        }

    if _ERROR_TREND_RE.search(text):

        return "get_error_trend", {

            "hours": _int_param(ti, "hours", "monitoring_hours", default=24),

        }

    if _LATENCY_TREND_RE.search(text):

        cohort = str(ti.get("cohort") or "ask").strip() or "ask"

        return "get_latency_trend", {

            "hours": _int_param(ti, "hours", "monitoring_hours", default=24),

            "cohort": cohort,

            "bucket_minutes": _int_param(ti, "bucket_minutes", default=15),

        }

    if _DLQ_RE.search(text):

        return "get_dlq_snapshot", {

            "limit": _int_param(ti, "dlq_limit", "limit", default=10),

        }

    if _ALERTS_RE.search(text):

        return "get_alerts", {

            "limit": _int_param(ti, "alert_limit", "limit", default=15),

        }

    if _OVERVIEW_RE.search(text):

        return "get_overview", {}

    explicit = str(ti.get("monitoring_query") or ti.get("service_query") or "").strip()
    if explicit == "get_dashboard_summary":
        return explicit, {
            "hours": _int_param(ti, "hours", "monitoring_hours", default=24),
            "cost_days": _int_param(ti, "cost_days", "monitoring_cost_days", default=7),
            "error_days": _int_param(ti, "error_days", default=1),
            "alert_limit": _int_param(ti, "alert_limit", default=15),
            "dlq_limit": _int_param(ti, "dlq_limit", default=10),
        }
    if explicit == "get_cost_trend":
        return explicit, {"days": _int_param(ti, "days", "cost_days", default=7)}
    if explicit == "get_error_trend":
        return explicit, {"hours": _int_param(ti, "hours", "monitoring_hours", default=24)}
    if explicit == "get_latency_trend":
        return explicit, {
            "hours": _int_param(ti, "hours", "monitoring_hours", default=24),
            "cohort": str(ti.get("cohort") or "ask").strip() or "ask",
            "bucket_minutes": _int_param(ti, "bucket_minutes", default=15),
        }
    if explicit == "get_dlq_snapshot":
        return explicit, {"limit": _int_param(ti, "dlq_limit", "limit", default=10)}
    if explicit == "get_alerts":
        return explicit, {"limit": _int_param(ti, "alert_limit", "limit", default=15)}
    if explicit == "get_overview":
        return explicit, {}

    return "get_overview", {}

def _summarize_service_payload(query: str, payload: Mapping[str, Any]) -> dict[str, Any]:

    """Compact, stable summary for executor dict (avoid large series in LangGraph init)."""

    if query == "get_overview":

        kpis = payload.get("kpis") if isinstance(payload.get("kpis"), Mapping) else {}

        return {

            "date": payload.get("date"),

            "task_count": kpis.get("task_count"),

            "success_rate": kpis.get("success_rate"),

            "p95_latency_ms": kpis.get("p95_latency_ms"),

            "dlq_backlog": kpis.get("dlq_backlog"),

            "total_cost_usd": kpis.get("total_cost_usd"),

        }

    if query == "get_dashboard_summary":

        meta = payload.get("meta") if isinstance(payload.get("meta"), Mapping) else {}

        sh = (

            payload.get("system_health")

            if isinstance(payload.get("system_health"), Mapping)

            else {}

        )

        return {

            "tier": meta.get("tier"),

            "task_count": sh.get("task_count"),

            "success_rate": sh.get("success_rate"),

            "p95_latency_ms": sh.get("p95_latency_ms"),

            "dlq_backlog": sh.get("dlq_backlog"),

            "total_cost_usd": sh.get("total_cost_usd"),

        }

    if query == "get_cost_trend":

        series = payload.get("series")

        n = len(series) if isinstance(series, list) else 0

        return {"days": payload.get("days"), "series_points": n}

    if query in ("get_error_trend", "get_latency_trend"):

        series = payload.get("series")

        n = len(series) if isinstance(series, list) else 0

        return {"hours": payload.get("hours"), "series_points": n}

    if query == "get_dlq_snapshot":

        return {"total": payload.get("total"), "limit": payload.get("limit")}

    if query == "get_alerts":

        items = payload.get("items")

        n = len(items) if isinstance(items, list) else 0

        return {"alert_count": n}

    return {"ok": payload.get("ok")}

_READ_ONLY_SERVICE_QUERIES: frozenset[str] = frozenset(

    {

        "get_overview",

        "get_dashboard_summary",

        "get_cost_trend",

        "get_error_trend",

        "get_latency_trend",

        "get_dlq_snapshot",

        "get_alerts",

    }

)

def _invoke_monitoring_service_adapter(

    task_input: Mapping[str, Any] | None,

) -> dict[str, Any]:

    """

    Call monitoring_service read API; never ingest, scheduler, or alert evaluation writes.

    """

    ti = dict(task_input) if isinstance(task_input, Mapping) else {}

    query, kwargs = resolve_monitoring_service_query(ti)

    if query not in _READ_ONLY_SERVICE_QUERIES:

        return {"ok": False, "message": f"unsupported monitoring query: {query}"}

    try:

        svc = _load_monitoring_service_module()

    except Exception as exc:

        return {"ok": False, "message": f"monitoring service import failed: {exc}"}

    fn: Callable[..., dict[str, Any]] | None = getattr(svc, query, None)

    if not callable(fn):

        return {"ok": False, "message": f"monitoring service missing callable: {query}"}

    try:

        payload = fn(**kwargs)

    except Exception as exc:

        return {"ok": False, "message": f"monitoring service call failed: {exc}"}

    if not isinstance(payload, Mapping):

        return {"ok": False, "message": "monitoring service returned non-dict"}

    if payload.get("ok") is not True:

        return {

            "ok": False,

            "message": str(payload.get("message") or "monitoring service query failed"),

            "service_query": query,

        }

    return {

        "ok": True,

        "service_query": query,

        "service_kwargs": kwargs,

        "service_summary": _summarize_service_payload(query, payload),

    }

def _task_input_from_context(context_entry_output: Mapping[str, Any] | None) -> dict[str, Any]:

    if not isinstance(context_entry_output, Mapping):

        return {}

    working = context_entry_output.get("working_context")

    if isinstance(working, dict):

        ti = working.get("task_input")

        if isinstance(ti, dict):

            return dict(ti)

    ti_top = context_entry_output.get("task_input")

    return dict(ti_top) if isinstance(ti_top, dict) else {}

def resolve_subagent_routing(

    *,

    init: Mapping[str, Any] | None = None,

    context_entry_output: Mapping[str, Any] | None = None,

) -> dict[str, Any]:

    """

    Resolve routing dict from LangGraph init keys and/or H-line context metadata.

    Prefers ``init["_subagent_route"]``, then ``metadata.subagent_route`` on context output.

    """

    if isinstance(init, Mapping):

        route = init.get("_subagent_route")

        if isinstance(route, dict) and route:

            return dict(route)

        target = init.get("_subagent_target_agent_id")

        if isinstance(target, str) and target.strip():

            return {"target_agent_id": target.strip()}

    if isinstance(context_entry_output, Mapping):

        meta = context_entry_output.get("metadata")

        if isinstance(meta, dict):

            route = meta.get("subagent_route")

            if isinstance(route, dict) and route:

                return dict(route)

    return {}

def routing_subagent_id(routing: Mapping[str, Any] | None) -> str | None:

    """Normalized subagent id from routing decision (``subagent_id`` or ``target_agent_id``)."""

    if not isinstance(routing, Mapping):

        return None

    for key in ("subagent_id", "target_agent_id"):

        raw = routing.get(key)

        if isinstance(raw, str) and raw.strip():

            return raw.strip()

    return None

def is_monitoring_routing(routing: Mapping[str, Any] | None) -> bool:

    """True when C-1 (or explicit) routing selects the monitoring subagent."""

    sid = routing_subagent_id(routing)

    return sid in _MONITORING_ROUTE_IDS if sid else False

def _run_monitoring_stub(

    task_input: Mapping[str, Any],

    *,

    route: Mapping[str, Any],

    adapter_message: str | None = None,

) -> dict[str, Any]:

    """v0.1 in-process stub (audit log + stable executor markers)."""

    task_id = str(task_input.get("task_id") or task_input.get("work_order_id") or "").strip() or None

    entry = {

        "task_id": task_id,

        "subagent_id": routing_subagent_id(route) or MONITORING_SUBAGENT_ID,

        "executor": EXECUTOR_VERSION,

        "fallback": FALLBACK_STUB,

        "message": "monitoring stub executed",

        "task_type": task_input.get("task_type"),

        "goal": (str(task_input.get("goal") or task_input.get("query") or ""))[:200] or None,

        "adapter_skip_reason": adapter_message,

    }

    _monitoring_task_log.append(entry)

    out: dict[str, Any] = {

        "ok": True,

        "monitoring": True,

        "executed": True,

        "executor": EXECUTOR_VERSION,

        "fallback": FALLBACK_STUB,

        "message": entry["message"],

        "task_id": task_id,

        "subagent_id": entry["subagent_id"],

        "routing_rule_id": route.get("rule_id"),

    }

    if adapter_message:

        out["adapter_error"] = adapter_message

    return out

def _run_monitoring_graph_if_enabled(
    *,
    task_input: Mapping[str, Any],
    route: Mapping[str, Any],
    adapter: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    Optional M-2 glue: run monitoring graph when env flag is on and adapter succeeded.

    Graph errors are swallowed into ``{"ok": false, "reason": ...}``; never raises.
    """
    if not is_monitoring_graph_enabled():
        return None

    task_id = str(task_input.get("task_id") or task_input.get("work_order_id") or "").strip() or None
    summary = adapter.get("service_summary")
    try:
        return run_monitoring_graph(
            {
                "task_id": task_id,
                "service_summary": summary if isinstance(summary, Mapping) else {},
                "subagent_route": dict(route),
                "service_query": adapter.get("service_query"),
            }
        )
    except Exception as exc:
        return {"ok": False, "reason": f"monitoring graph error: {exc}"}


def _run_monitoring_service_adapter_result(

    task_input: Mapping[str, Any],

    *,

    route: Mapping[str, Any],

    adapter: Mapping[str, Any],

) -> dict[str, Any]:

    task_id = str(task_input.get("task_id") or task_input.get("work_order_id") or "").strip() or None

    query = str(adapter.get("service_query") or "")

    summary = adapter.get("service_summary")

    entry = {

        "task_id": task_id,

        "subagent_id": routing_subagent_id(route) or MONITORING_SUBAGENT_ID,

        "executor": EXECUTOR_ADAPTER_ID,

        "service_query": query,

        "message": f"monitoring service read: {query}",

        "task_type": task_input.get("task_type"),

    }

    _monitoring_task_log.append(entry)

    out: dict[str, Any] = {

        "ok": True,

        "monitoring": True,

        "executed": True,

        "executor": EXECUTOR_ADAPTER_ID,

        "message": entry["message"],

        "task_id": task_id,

        "subagent_id": entry["subagent_id"],

        "routing_rule_id": route.get("rule_id"),

        "service_query": query,

        "service_summary": summary if isinstance(summary, Mapping) else {},

    }

    graph_result = _run_monitoring_graph_if_enabled(
        task_input=task_input,
        route=route,
        adapter=adapter,
    )
    if graph_result is not None:
        out["_monitoring_graph_result"] = graph_result

    return out

def run_monitoring_subagent(

    task_input: Mapping[str, Any] | None,

    context_entry_output: Mapping[str, Any] | None,

    *,

    routing: Mapping[str, Any] | None = None,

) -> dict[str, Any]:

    """

    Execute monitoring subagent: read-only service adapter first, stub fallback on failure.

    Records one in-memory log entry and returns a structured result dict.

    """

    ti = dict(task_input) if isinstance(task_input, Mapping) else _task_input_from_context(

        context_entry_output

    )

    route = dict(routing) if isinstance(routing, Mapping) else {}

    adapter = _invoke_monitoring_service_adapter(ti)

    if adapter.get("ok") is True:

        return _run_monitoring_service_adapter_result(ti, route=route, adapter=adapter)

    adapter_message = str(adapter.get("message") or "monitoring service unavailable")

    return _run_monitoring_stub(ti, route=route, adapter_message=adapter_message)

def maybe_run_monitoring_executor(

    task_input: Mapping[str, Any] | None,

    context_entry_output: Mapping[str, Any] | None,

    *,

    init: Mapping[str, Any] | None = None,

) -> dict[str, Any]:

    """

    Run monitoring executor only when routing targets monitoring; otherwise noop.

    Safe to call on every ask init enrichment — non-monitoring routes are no-ops.

    """

    route = resolve_subagent_routing(init=init, context_entry_output=context_entry_output)

    if not is_monitoring_routing(route):

        return {

            "ok": True,

            "monitoring": False,

            "executed": False,

            "noop": True,

            "executor": None,

            "message": "subagent executor skipped (not monitoring route)",

        }

    ti = task_input if isinstance(task_input, Mapping) else _task_input_from_context(

        context_entry_output

    )

    return run_monitoring_subagent(ti, context_entry_output, routing=route)

def extract_monitoring_graph_summary_from_init(
    init: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Public ibridge summary from init/final ``_monitoring_graph_result`` (M-3)."""
    raw = init.get("_monitoring_graph_result")
    if not isinstance(raw, dict):
        executor = init.get("_monitoring_executor_result")
        if isinstance(executor, dict):
            raw = executor.get("_monitoring_graph_result")
    return extract_monitoring_graph_public_summary(raw if isinstance(raw, Mapping) else None)


def extract_monitoring_summary_from_init(init: Mapping[str, Any]) -> dict[str, Any]:
    """
    Compact monitoring executor summary for ibridge / API payloads.

    Reads ``_monitoring_executor_result`` from LangGraph init or final state without
    re-running the executor.
    """
    result = init.get("_monitoring_executor_result")
    if not isinstance(result, dict):
        return {"executed": False, "monitoring": False, "executor": None}
    summary: dict[str, Any] = {
        "executed": bool(result.get("executed")),
        "monitoring": bool(result.get("monitoring")),
        "executor": result.get("executor"),
        "fallback": result.get("fallback"),
        "noop": result.get("noop"),
        "message": result.get("message"),
        "service_query": result.get("service_query"),
    }
    svc_summary = result.get("service_summary")
    if isinstance(svc_summary, Mapping) and svc_summary:
        summary["service_summary"] = dict(svc_summary)
    return summary


def attach_executor_result_to_init(

    init: Mapping[str, Any],

    *,

    context_built: Mapping[str, Any] | None = None,

) -> dict[str, Any]:

    """

    Attach ``_monitoring_executor_result`` to LangGraph initial state when routed.

    Does not alter RAG selector or graph edges.

    """

    out = dict(init)

    payload = out.get("_context_entry_payload")

    ctx = context_built if context_built is not None else payload

    ti = _task_input_from_context(ctx if isinstance(ctx, Mapping) else None)

    result = maybe_run_monitoring_executor(ti, ctx if isinstance(ctx, Mapping) else None, init=out)

    out["_monitoring_executor_result"] = result

    graph_raw = result.get("_monitoring_graph_result") if isinstance(result, dict) else None
    if isinstance(graph_raw, dict):
        out["_monitoring_graph_result"] = graph_raw

    return out

