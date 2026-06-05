"""Subagent routing helpers (Sprint 1 · C-1) and executors (Sprint 2 · O-1)."""

from subagents.context_routing import (
    DEFAULT_AGENT_ID,
    MONITORING_AGENT_ID,
    ROUTING_VERSION,
    attach_subagent_route_to_context,
    build_route_decision,
    route_task_by_context,
)
from subagents.monitoring_executor import (
    EXECUTOR_ADAPTER_ID,
    EXECUTOR_VERSION,
    FALLBACK_STUB,
    MONITORING_SUBAGENT_ID,
    attach_executor_result_to_init,
    extract_monitoring_graph_summary_from_init,
    extract_monitoring_summary_from_init,
    get_monitoring_task_log,
    is_monitoring_routing,
    maybe_run_monitoring_executor,
    reset_monitoring_task_log,
    resolve_subagent_routing,
    run_monitoring_subagent,
    routing_subagent_id,
)

__all__ = [
    "DEFAULT_AGENT_ID",
    "EXECUTOR_ADAPTER_ID",
    "EXECUTOR_VERSION",
    "FALLBACK_STUB",
    "MONITORING_AGENT_ID",
    "MONITORING_SUBAGENT_ID",
    "ROUTING_VERSION",
    "attach_executor_result_to_init",
    "extract_monitoring_graph_summary_from_init",
    "extract_monitoring_summary_from_init",
    "attach_subagent_route_to_context",
    "build_route_decision",
    "get_monitoring_task_log",
    "is_monitoring_routing",
    "maybe_run_monitoring_executor",
    "reset_monitoring_task_log",
    "resolve_subagent_routing",
    "route_task_by_context",
    "run_monitoring_subagent",
    "routing_subagent_id",
]
