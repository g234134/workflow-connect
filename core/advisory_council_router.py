"""
Multi-Advisory Council Router.

Routes tasks to the appropriate advisory council(s) based on task type,
then merges results back to the Orchestrator.

Usage:
    from core.advisory_council_router import AdvisoryCouncilRouter

    router = AdvisoryCouncilRouter()
    result = router.route_task(task_type="prompt_design", payload={...})

Council lifecycle:
    1. Orchestrator calls route_task() with task_type + payload
    2. Router dispatches to the matching council (LC/LG/MCP/OBS/TOOL/MOD)
    3. Council executes its domain-specific logic
    4. Results flow back through Observability (OBS) for tracing
    5. Merged result returned to Orchestrator
"""

from __future__ import annotations

from typing import Any, Literal

# ── Council identifiers ────────────────────────────────────────────────────

COUNCIL_LC = "langchain"       # prompts, tools, agents, memory
COUNCIL_LG = "langgraph"       # graph, state, nodes, edges
COUNCIL_MCP = "mcp"           # external tool integration, protocol
COUNCIL_OBS = "observability"  # tracing, eval, metrics, shadow
COUNCIL_TOOL = "tool"         # terminal, chrome, db, file
COUNCIL_MOD = "model"         # LLM selection, routing, cost optimization

COUNCIL_LABELS: dict[str, str] = {
    COUNCIL_LC: "LangChain 智囊團",
    COUNCIL_LG: "LangGraph 智囊團",
    COUNCIL_MCP: "MCP 智囊團",
    COUNCIL_OBS: "Observability 智囊團",
    COUNCIL_TOOL: "Tool 智囊團",
    COUNCIL_MOD: "Model 智囊團",
}

# ── Task type → council mapping ────────────────────────────────────────────

# fmt: off
TASK_TYPE_TO_COUNCIL: dict[str, list[str]] = {
    # LangChain domain
    "prompt_design":        [COUNCIL_LC],
    "tool_definition":      [COUNCIL_LC, COUNCIL_MCP],
    "agent_config":         [COUNCIL_LC],
    "memory_setup":         [COUNCIL_LC],
    "output_parsing":       [COUNCIL_LC],

    # LangGraph domain
    "workflow_design":      [COUNCIL_LG],
    "state_machine":        [COUNCIL_LG],
    "graph_optimization":   [COUNCIL_LG],
    "routing_logic":        [COUNCIL_LG],

    # MCP domain
    "external_integration": [COUNCIL_MCP],
    "protocol_selection":   [COUNCIL_MCP],
    "server_discovery":     [COUNCIL_MCP],

    # Observability domain
    "tracing_setup":        [COUNCIL_OBS],
    "evaluation":           [COUNCIL_OBS],
    "slo_tracking":         [COUNCIL_OBS],
    "shadow_testing":       [COUNCIL_OBS],

    # Tool domain
    "terminal_automation":  [COUNCIL_TOOL],
    "browser_automation":   [COUNCIL_TOOL],
    "database_operation":   [COUNCIL_TOOL],
    "file_management":      [COUNCIL_TOOL],

    # Model domain
    "model_selection":      [COUNCIL_MOD],
    "cost_optimization":    [COUNCIL_MOD],
    "local_deployment":     [COUNCIL_MOD],

    # Cross-domain
    "end_to_end_pipeline":  [COUNCIL_LC, COUNCIL_LG, COUNCIL_TOOL, COUNCIL_OBS],
    "experiment":           [COUNCIL_MOD, COUNCIL_OBS],
}
# fmt: on

# ── Router class ───────────────────────────────────────────────────────────

TaskType = Literal[
    "prompt_design",
    "tool_definition",
    "agent_config",
    "memory_setup",
    "output_parsing",
    "workflow_design",
    "state_machine",
    "graph_optimization",
    "routing_logic",
    "external_integration",
    "protocol_selection",
    "server_discovery",
    "tracing_setup",
    "evaluation",
    "slo_tracking",
    "shadow_testing",
    "terminal_automation",
    "browser_automation",
    "database_operation",
    "file_management",
    "model_selection",
    "cost_optimization",
    "local_deployment",
    "end_to_end_pipeline",
    "experiment",
    "unknown",
]


class AdvisoryCouncilRouter:
    """Routes tasks to the correct advisory council(s)."""

    def __init__(self, enable_tracing: bool = True) -> None:
        self.enable_tracing = enable_tracing
        self._routing_log: list[dict[str, Any]] = []

    def resolve_councils(self, task_type: str) -> list[str]:
        """Return the council(s) responsible for a given task type."""
        return TASK_TYPE_TO_COUNCIL.get(task_type, [COUNCIL_LC, COUNCIL_OBS])

    def route_task(
        self,
        task_type: TaskType | str,
        payload: dict[str, Any],
        *,
        caller: str = "orchestrator",
    ) -> dict[str, Any]:
        """
        Route a task to the appropriate advisory council(s).

        Args:
            task_type: Type of task to route.
            payload: Task input data.
            caller: Who is calling the router (default: orchestrator).

        Returns:
            dict with keys:
                - task_type: str
                - councils: list[str]
                - council_labels: list[str]
                - results: dict[str, Any] by council
                - merged: dict[str, Any] (merged results)
                - error: str | None
        """
        councils = self.resolve_councils(task_type)
        labels = [COUNCIL_LABELS.get(c, c) for c in councils]

        # Build routing record
        record: dict[str, Any] = {
            "task_type": task_type,
            "councils": councils,
            "council_labels": labels,
            "caller": caller,
            "payload_keys": list(payload.keys()),
        }

        # Execute each council (stub — real impl connects to existing agents)
        results: dict[str, Any] = {}
        errors: list[str] = []
        for council in councils:
            try:
                result = self._execute_council(council, payload)
                results[council] = result
            except Exception as exc:
                errors.append(f"{council}: {exc}")
                results[council] = {"status": "error", "error": str(exc)}

        # Merge results
        merged = self._merge_results(results)

        record["results"] = results
        record["merged"] = merged
        record["error"] = "; ".join(errors) if errors else None
        self._routing_log.append(record)

        return {
            "task_type": task_type,
            "councils": councils,
            "council_labels": labels,
            "results": results,
            "merged": merged,
            "error": record["error"],
        }

    def get_routing_log(self) -> list[dict[str, Any]]:
        """Return the full routing history for this session."""
        return list(self._routing_log)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _execute_council(
        self, council: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a single council's logic.

        Stub — real implementation should dispatch to existing agents:
            - COUNCIL_TOOL → core.infra_health, core.data_pipeline
            - COUNCIL_LC   → core.coding_agent_router
            - COUNCIL_OBS  → core.monitoring_graph, observability.*
            - COUNCIL_LG   → core.langgraph_flow_k1, core.langgraph_flow_k2
            - COUNCIL_MOD  → agent routing logic
            - COUNCIL_MCP  → MCP registry integration
        """
        _ = payload  # consumed by real impl
        if council == COUNCIL_TOOL:
            return {
                "council": council,
                "status": "dispatched",
                "handler": "core.infra_health | core.data_pipeline",
            }
        if council == COUNCIL_LC:
            return {
                "council": council,
                "status": "dispatched",
                "handler": "core.coding_agent_router",
            }
        if council == COUNCIL_LG:
            return {
                "council": council,
                "status": "dispatched",
                "handler": "core.langgraph_flow_k2",
            }
        if council == COUNCIL_OBS:
            return {
                "council": council,
                "status": "dispatched",
                "handler": "core.monitoring_graph",
            }
        if council == COUNCIL_MCP:
            return {
                "council": council,
                "status": "dispatched",
                "handler": "mcp._registry",
            }
        if council == COUNCIL_MOD:
            return {
                "council": council,
                "status": "dispatched",
                "handler": "core.coding_agent_router (model routing)",
            }
        return {
            "council": council,
            "status": "unknown_council",
            "handler": None,
        }

    @staticmethod
    def _merge_results(results: dict[str, Any]) -> dict[str, Any]:
        """Merge multiple council results into a single dict."""
        merged: dict[str, Any] = {
            "statuses": {},
            "total_councils": len(results),
            "successful": 0,
            "failed": 0,
        }
        for council, result in results.items():
            merged["statuses"][council] = result.get("status", "unknown")
            if result.get("status") == "error":
                merged["failed"] += 1
            else:
                merged["successful"] += 1
        merged["all_ok"] = merged["failed"] == 0
        return merged
