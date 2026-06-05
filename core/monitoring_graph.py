"""
Monitoring graph v0.2 (Sprint 5 · M-1 / A-line).

Read-only LangGraph workflow over executor ``service_summary``; does not call monitoring API,
Postgres, or LangGraph main ask graph. Optional glue via ``GOV_MONITORING_GRAPH_ENABLED``.
"""

import os
from typing import Any, Mapping, Optional, TypedDict

MONITORING_GRAPH_VERSION = "v0.2-langgraph-min"

ENV_MONITORING_GRAPH_ENABLED = "GOV_MONITORING_GRAPH_ENABLED"

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover — optional until langgraph installed
    StateGraph = None  # type: ignore[misc, assignment]
    START = END = None  # type: ignore[misc, assignment]


class MonitoringGraphState(TypedDict, total=False):
    task_id: Optional[str]
    service_summary: dict
    subagent_route: Optional[dict]
    service_query: Optional[str]
    ok: bool
    reason: Optional[str]
    analysis: dict
    recommendations: list
    nodes_executed: list


def is_monitoring_graph_enabled(*, explicit: bool | None = None) -> bool:
    """True when env ``GOV_MONITORING_GRAPH_ENABLED`` is 1/true/yes/on (default off)."""
    if explicit is not None:
        return bool(explicit)
    return os.environ.get(ENV_MONITORING_GRAPH_ENABLED, "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _append_node(state: dict, node_name: str) -> list:
    executed = list(state.get("nodes_executed") or [])
    executed.append(node_name)
    return executed


def _heuristic_recommendations(service_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []

    success_rate = service_summary.get("success_rate")
    if isinstance(success_rate, (int, float)) and success_rate < 0.95:
        recommendations.append(
            {
                "kind": "health",
                "severity": "warn",
                "message": "success_rate below 0.95",
            }
        )

    dlq_backlog = service_summary.get("dlq_backlog")
    if isinstance(dlq_backlog, (int, float)) and dlq_backlog > 0:
        recommendations.append(
            {
                "kind": "dlq",
                "severity": "info",
                "message": "dlq_backlog is non-zero",
            }
        )

    p95 = service_summary.get("p95_latency_ms")
    if isinstance(p95, (int, float)) and p95 > 5000:
        recommendations.append(
            {
                "kind": "latency",
                "severity": "warn",
                "message": "p95_latency_ms above 5000",
            }
        )

    return recommendations


def _heuristic_signals(service_summary: Mapping[str, Any]) -> dict[str, bool]:
    signals: dict[str, bool] = {}
    success_rate = service_summary.get("success_rate")
    if isinstance(success_rate, (int, float)):
        signals["low_success_rate"] = success_rate < 0.95
    dlq_backlog = service_summary.get("dlq_backlog")
    if isinstance(dlq_backlog, (int, float)):
        signals["dlq_nonzero"] = dlq_backlog > 0
    p95 = service_summary.get("p95_latency_ms")
    if isinstance(p95, (int, float)):
        signals["high_p95_latency"] = p95 > 5000
    return signals


def _node_summarize(state: dict) -> dict:
    service_summary = state.get("service_summary")
    if not isinstance(service_summary, Mapping) or not service_summary:
        return {
            "ok": False,
            "reason": "missing or empty service_summary",
            "analysis": {"graph_version": MONITORING_GRAPH_VERSION},
            "recommendations": [],
            "nodes_executed": _append_node(state, "summarize"),
        }

    route = state.get("subagent_route")
    rule_id = route.get("rule_id") if isinstance(route, Mapping) else None
    analysis: dict[str, Any] = {
        "graph_version": MONITORING_GRAPH_VERSION,
        "service_query": state.get("service_query"),
        "summary_keys": sorted(str(k) for k in service_summary.keys()),
        "routing_rule_id": rule_id,
    }
    if state.get("task_id"):
        analysis["task_id"] = state.get("task_id")

    return {
        "ok": True,
        "reason": None,
        "analysis": analysis,
        "recommendations": [],
        "nodes_executed": _append_node(state, "summarize"),
    }


def _route_after_summarize(state: dict) -> str:
    if state.get("ok") is False:
        return "finalize"
    return "analyze"


def _node_analyze(state: dict) -> dict:
    service_summary = state.get("service_summary") or {}
    analysis = dict(state.get("analysis") or {})
    signals = _heuristic_signals(service_summary)
    analysis["signals"] = signals
    analysis["signal_count"] = sum(1 for v in signals.values() if v)
    return {
        "analysis": analysis,
        "nodes_executed": _append_node(state, "analyze"),
    }


def _node_recommend(state: dict) -> dict:
    service_summary = state.get("service_summary") or {}
    recommendations = _heuristic_recommendations(service_summary)
    analysis = dict(state.get("analysis") or {})
    analysis["recommendation_count"] = len(recommendations)
    return {
        "recommendations": recommendations,
        "analysis": analysis,
        "nodes_executed": _append_node(state, "recommend"),
    }


def _node_finalize(state: dict) -> dict:
    analysis = dict(state.get("analysis") or {})
    executed = _append_node(state, "finalize")
    analysis["nodes_executed"] = executed
    if state.get("ok") is False:
        return {
            "analysis": analysis,
            "nodes_executed": executed,
        }
    return {
        "ok": True,
        "analysis": analysis,
        "recommendations": list(state.get("recommendations") or []),
        "nodes_executed": executed,
    }


def build_monitoring_graph() -> Any:
    """Compile read-only monitoring LangGraph (summarize → analyze → recommend → finalize)."""
    if StateGraph is None:
        raise RuntimeError("langgraph is not installed")

    g = StateGraph(MonitoringGraphState)
    g.add_node("summarize", _node_summarize)
    g.add_node("analyze", _node_analyze)
    g.add_node("recommend", _node_recommend)
    g.add_node("finalize", _node_finalize)

    g.add_edge(START, "summarize")
    g.add_conditional_edges(
        "summarize",
        _route_after_summarize,
        {"analyze": "analyze", "finalize": "finalize"},
    )
    g.add_edge("analyze", "recommend")
    g.add_edge("recommend", "finalize")
    g.add_edge("finalize", END)
    return g.compile()


_COMPILED_MONITORING_GRAPH: Any | None = None


def _compiled_monitoring_graph() -> Any:
    global _COMPILED_MONITORING_GRAPH
    if _COMPILED_MONITORING_GRAPH is None:
        _COMPILED_MONITORING_GRAPH = build_monitoring_graph()
    return _COMPILED_MONITORING_GRAPH


def _state_from_graph_input(graph_input: Mapping[str, Any]) -> dict:
    service_summary = graph_input.get("service_summary")
    route = graph_input.get("subagent_route")
    return {
        "task_id": graph_input.get("task_id"),
        "service_summary": dict(service_summary) if isinstance(service_summary, Mapping) else {},
        "subagent_route": dict(route) if isinstance(route, Mapping) else None,
        "service_query": graph_input.get("service_query"),
        "ok": True,
        "reason": None,
        "analysis": {},
        "recommendations": [],
        "nodes_executed": [],
    }


def _result_from_final_state(final: dict) -> dict:
    if final.get("ok") is False:
        reason = final.get("reason") or "monitoring graph failed"
        out: dict[str, Any] = {"ok": False, "reason": str(reason)}
        analysis = final.get("analysis")
        if isinstance(analysis, Mapping) and analysis:
            out["analysis"] = dict(analysis)
        return out

    analysis = final.get("analysis")
    recommendations = final.get("recommendations")
    return {
        "ok": True,
        "analysis": dict(analysis) if isinstance(analysis, Mapping) else {},
        "recommendations": list(recommendations) if isinstance(recommendations, list) else [],
    }


def _run_monitoring_graph_inline(graph_input: Mapping[str, Any]) -> dict[str, Any]:
    """In-process fallback when LangGraph is unavailable (same contract as compiled graph)."""
    init = _state_from_graph_input(graph_input)
    after_summarize = _node_summarize(init)
    merged = {**init, **after_summarize}
    if merged.get("ok") is False:
        final = _node_finalize(merged)
        return _result_from_final_state({**merged, **final})

    merged = {**merged, **_node_analyze(merged)}
    merged = {**merged, **_node_recommend(merged)}
    final = _node_finalize(merged)
    return _result_from_final_state({**merged, **final})


def run_monitoring_graph(graph_input: Mapping[str, Any]) -> dict[str, Any]:
    """
    Run monitoring graph (LangGraph when available, else inline node sequence).

    Expected ``graph_input`` keys (all optional except meaningful ``service_summary``):
      - ``task_id``
      - ``service_summary`` — compact dict from monitoring executor adapter
      - ``subagent_route`` — C-1 routing sidecar
      - ``service_query`` — resolved monitoring_service function name

    Returns:
      - ``{"ok": true, "analysis": {...}, "recommendations": [...]}``
      - ``{"ok": false, "reason": "..."}`` when input cannot be analyzed
    """
    init = _state_from_graph_input(graph_input)
    if StateGraph is None:
        return _run_monitoring_graph_inline(graph_input)

    final = _compiled_monitoring_graph().invoke(init)
    return _result_from_final_state(final)


def extract_monitoring_graph_public_summary(
    graph_result: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Compact summary for ``ibridge_v0.monitoring_graph`` (observability only)."""
    if not isinstance(graph_result, Mapping) or not graph_result:
        return None

    if graph_result.get("ok") is not True:
        reason = graph_result.get("reason") or graph_result.get("message") or "graph failed"
        return {"ok": False, "analysis_summary": None, "reason": str(reason)}

    analysis = graph_result.get("analysis")
    analysis_summary: dict[str, Any] | None = None
    if isinstance(analysis, Mapping):
        analysis_summary = {
            "graph_version": analysis.get("graph_version"),
            "service_query": analysis.get("service_query"),
            "routing_rule_id": analysis.get("routing_rule_id"),
            "summary_keys": list(analysis.get("summary_keys") or []),
        }
        nodes = analysis.get("nodes_executed")
        if isinstance(nodes, list) and nodes:
            analysis_summary["nodes_executed"] = list(nodes)

    recs = graph_result.get("recommendations")
    rec_count = len(recs) if isinstance(recs, list) else 0

    out: dict[str, Any] = {
        "ok": True,
        "analysis_summary": analysis_summary,
        "recommendation_count": rec_count,
    }
    if isinstance(recs, list) and recs:
        first = recs[0]
        if isinstance(first, Mapping):
            out["top_recommendation"] = {
                "kind": first.get("kind"),
                "severity": first.get("severity"),
                "message": first.get("message"),
            }
    return out
