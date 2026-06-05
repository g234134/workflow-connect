"""
K-1: minimal LangGraph e2e — Planner → Executor → Reviewer.

Wires context (N), agents/handoff (M), observability (O), reliability (P), metrics (Q).
Does not touch ``gov_core_system`` ask_pipeline / ``langgraph_flow``.
"""

from __future__ import annotations

import copy
from typing import Any, Literal, TypedDict, cast

from agents.base_agent import (
    ROLE_EXECUTOR,
    ROLE_PLANNER,
    ROLE_REVIEWER,
    BaseAgent,
    ExecutorAgent,
    PlannerAgent,
    ReviewerAgent,
    route_by_status,
)
from core.context_entry import build_rooted_context
from metrics.metrics_collector import MetricsCollector, get_collector
from observability.logging_adapter import (
    TraceContext,
    agent_run_trace,
    end_span,
    log_event,
    log_metric,
    reset_active_trace,
    start_span,
)
from reliability.retry_handler import ReliabilityError, run_with_retry

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover — optional until langgraph installed
    StateGraph = None  # type: ignore[misc, assignment]
    START = END = None  # type: ignore[misc, assignment]


class K1State(TypedDict, total=False):
    task_id: str
    goal: str
    task_input: dict[str, Any]
    context_payload: dict[str, Any]
    agent_output: dict[str, Any]
    handoff_chain: list[dict[str, Any]]
    last_status: str
    final_result: dict[str, Any]
    error_type: str | None
    next_agent: str | None
    executor_attempts: int


RouteLabel = Literal["executor", "reviewer", "success_end", "fail_end"]

_AGENT_BY_ROLE: dict[str, BaseAgent] = {
    ROLE_PLANNER: PlannerAgent(strict_handoff_edges=True),
    ROLE_EXECUTOR: ExecutorAgent(strict_handoff_edges=True),
    ROLE_REVIEWER: ReviewerAgent(strict_handoff_edges=True),
}

_ROLE_TO_NODE: dict[str, RouteLabel] = {
    ROLE_EXECUTOR: "executor",
    ROLE_REVIEWER: "reviewer",
}


def _route_after_agent(state: K1State) -> RouteLabel:
    """Map ``route_by_status`` + ``next_agent`` to graph node names."""
    decision = route_by_status(state)
    if decision == "handoff":
        target = state.get("next_agent") or (state.get("agent_output") or {}).get("next_agent")
        node = _ROLE_TO_NODE.get(str(target or ""))
        if node:
            return node
        return "fail_end"
    if decision == "success":
        return "success_end"
    return "fail_end"


def _agent_context_from_state(state: K1State) -> dict[str, Any]:
    payload = state.get("context_payload") or {}
    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    return {
        "root_context": result.get("root_context") or {},
        "working_context": result.get("working_context") or {},
        "long_term_memory": result.get("long_term_memory") or {},
        "assembled_text": result.get("assembled_text"),
        "metadata": payload.get("metadata") or {},
    }


def _run_agent_with_observability(
    agent: BaseAgent,
    state: K1State,
    *,
    span_name: str,
    trace_ctx: TraceContext | None,
    collector: MetricsCollector,
    attempt_box: dict[str, int] | None = None,
    simulate_retry: bool = False,
) -> dict[str, Any]:
    """Run one agent inside span + ``run_with_retry``; return graph state patch."""
    task_id = str(state.get("task_id") or "")
    agent_input = {
        "task_id": task_id,
        "goal": state.get("goal") or "",
        "context": _agent_context_from_state(state),
    }

    start_span(trace_ctx, span_name, agent=agent.role_id)
    log_event(
        f"{span_name}_start",
        {"role": agent.role_id},
        trace_ctx=trace_ctx,
    )

    def _core() -> dict[str, Any]:
        if simulate_retry and attempt_box is not None:
            attempt_box["n"] = attempt_box.get("n", 0) + 1
            if attempt_box["n"] == 1:
                collector.log_error(
                    task_id,
                    "tool_error",
                    "K1 controlled tool_error (first executor attempt)",
                    increment_retry=False,
                )
                raise ReliabilityError(
                    "K1 simulated executor fault (retry via timeout policy)",
                    error_type="timeout",
                )
        return agent.run(agent_input)

    retry_out = run_with_retry(
        _core,
        task_id=task_id or None,
        step_name=span_name,
        collector=collector,
    )

    end_span(trace_ctx, success=bool(retry_out.get("ok")), metadata={"retry_count": retry_out.get("retry_count")})

    if not retry_out.get("ok"):
        return {
            "agent_output": {
                "ok": False,
                "message": retry_out.get("message", "retry exhausted"),
                "result": {},
                "status": "fail",
                "next_agent": None,
                "notes": {"error_type": retry_out.get("error_type")},
            },
            "last_status": "fail",
            "error_type": retry_out.get("error_type"),
            "executor_attempts": attempt_box.get("n", 0) if attempt_box else state.get("executor_attempts", 0),
        }

    output = cast(dict[str, Any], retry_out.get("result") or {})
    prior = state.get("handoff_chain")
    prior_chain = list(prior) if isinstance(prior, list) else []
    patch = agent.to_graph_state_patch(output, prior_chain=prior_chain)

    if output.get("status") == "need_handoff":
        collector.record_handoff(task_id)
        log_event(
            "agent_handoff",
            {"from": agent.role_id, "to": output.get("next_agent")},
            trace_ctx=trace_ctx,
        )
        patch["next_agent"] = output.get("next_agent")

    if simulate_retry and attempt_box is not None:
        patch["executor_attempts"] = attempt_box.get("n", 0)

    return patch


def prepare_context_node(state: K1State) -> dict[str, Any]:
    """Entry: ``build_rooted_context`` (H-line) → ``context_payload`` + token metrics."""
    task_input = dict(state.get("task_input") or {})
    if not task_input.get("task_id"):
        task_input["task_id"] = state.get("task_id") or ""
    if not task_input.get("goal"):
        task_input["goal"] = state.get("goal") or ""

    built = build_rooted_context(task_input, mode="k1_pipeline")
    log_event(
        "build_context_done",
        {"ok": built.get("ok"), "message": built.get("message"), "entry": "context_entry"},
        as_step=True,
    )

    token_usage = built.get("token_usage") if isinstance(built.get("token_usage"), dict) else {}
    meta = built.get("metadata") if isinstance(built.get("metadata"), dict) else {}
    if token_usage:
        log_metric(
            "context_token_usage",
            int(token_usage.get("total_tokens") or token_usage.get("total") or 0),
        )
        tid = str(task_input.get("task_id") or state.get("task_id") or "")
        if tid:
            get_collector().log_step(
                tid,
                "build_context",
                token_delta={
                    "prompt_tokens": int(token_usage.get("prompt_tokens", 0)),
                    "completion_tokens": int(token_usage.get("completion_tokens", 0)),
                    "total_tokens": int(
                        token_usage.get("total_tokens") or token_usage.get("total") or 0
                    ),
                },
                metadata={"source": "context_entry", "entry_mode": "k1_pipeline"},
            )

    return {
        "task_id": task_input.get("task_id"),
        "goal": task_input.get("goal"),
        "task_input": task_input,
        "context_payload": built,
    }


def _make_agent_node(
    role: str,
    *,
    span_name: str,
    simulate_retry: bool = False,
) -> Any:
    agent = _AGENT_BY_ROLE[role]

    def node(state: K1State) -> dict[str, Any]:
        trace_ctx = None
        try:
            from observability.logging_adapter import get_active_trace

            trace_ctx = get_active_trace()
        except Exception:
            trace_ctx = None
        col = get_collector()
        attempt_box: dict[str, int] | None = {"n": int(state.get("executor_attempts") or 0)} if simulate_retry else None
        return _run_agent_with_observability(
            agent,
            state,
            span_name=span_name,
            trace_ctx=trace_ctx,
            collector=col,
            attempt_box=attempt_box,
            simulate_retry=simulate_retry,
        )

    return node


def success_end_node(state: K1State) -> dict[str, Any]:
    out = state.get("agent_output") or {}
    return {
        "final_result": {
            "ok": True,
            "message": out.get("message", "K1 flow completed"),
            "result": copy.deepcopy(out.get("result") or {}),
            "status": "success",
            "handoff_chain": list(state.get("handoff_chain") or []),
        },
        "last_status": "success",
        "error_type": None,
    }


def fail_end_node(state: K1State) -> dict[str, Any]:
    out = state.get("agent_output") or {}
    err = state.get("error_type") or (out.get("notes") or {}).get("error_type") if isinstance(out.get("notes"), dict) else None
    return {
        "final_result": {
            "ok": False,
            "message": out.get("message", "K1 flow failed"),
            "result": copy.deepcopy(out.get("result") or {}),
            "status": "fail",
            "error_type": err,
        },
        "last_status": "fail",
        "error_type": err,
    }


def build_k1_graph() -> Any:
    if StateGraph is None:
        raise ImportError("langgraph is required for K-1 flow; install langgraph package")

    g = StateGraph(K1State)
    g.add_node("prepare_context", prepare_context_node)
    g.add_node("planner", _make_agent_node(ROLE_PLANNER, span_name="planner"))
    g.add_node("executor", _make_agent_node(ROLE_EXECUTOR, span_name="executor", simulate_retry=True))
    g.add_node("reviewer", _make_agent_node(ROLE_REVIEWER, span_name="reviewer"))
    g.add_node("success_end", success_end_node)
    g.add_node("fail_end", fail_end_node)

    g.add_edge(START, "prepare_context")
    g.add_edge("prepare_context", "planner")
    g.add_conditional_edges("planner", _route_after_agent, {
        "executor": "executor",
        "reviewer": "reviewer",
        "success_end": "success_end",
        "fail_end": "fail_end",
    })
    g.add_conditional_edges("executor", _route_after_agent, {
        "executor": "executor",
        "reviewer": "reviewer",
        "success_end": "success_end",
        "fail_end": "fail_end",
    })
    g.add_conditional_edges("reviewer", _route_after_agent, {
        "executor": "executor",
        "reviewer": "reviewer",
        "success_end": "success_end",
        "fail_end": "fail_end",
    })
    g.add_edge("success_end", END)
    g.add_edge("fail_end", END)
    return g.compile()


_COMPILED_K1: Any | None = None


def _compiled_k1() -> Any:
    global _COMPILED_K1
    if _COMPILED_K1 is None:
        _COMPILED_K1 = build_k1_graph()
    return _COMPILED_K1


def initial_k1_state(
    *,
    task_id: str = "k1-demo-001",
    goal: str = "K-1 LangGraph e2e smoke",
    task_input: dict[str, Any] | None = None,
) -> K1State:
    ti = dict(task_input or {})
    ti.setdefault("task_id", task_id)
    ti.setdefault("goal", goal)
    ti.setdefault("query", goal)
    return {
        "task_id": task_id,
        "goal": goal,
        "task_input": ti,
        "context_payload": {},
        "agent_output": {},
        "handoff_chain": [],
        "last_status": "",
        "final_result": {},
        "error_type": None,
        "executor_attempts": 0,
    }


def run_k1_flow(
    *,
    task_id: str = "k1-demo-001",
    goal: str = "K-1 LangGraph e2e smoke",
    task_input: dict[str, Any] | None = None,
    collector: MetricsCollector | None = None,
) -> dict[str, Any]:
    """
    Invoke the K-1 graph once inside ``agent_run_trace``.

    Returns ``{ok, message, state, record}`` where ``record`` is the M-line task record.
    """
    col = collector or get_collector()
    reset_active_trace()
    init = initial_k1_state(task_id=task_id, goal=goal, task_input=task_input)
    graph = _compiled_k1()
    final_state: K1State = {}

    with agent_run_trace("langgraph_k1", task_id=task_id, collector=col) as trace_ctx:
        log_event("k1_graph_invoke_start", {"task_id": task_id}, trace_ctx=trace_ctx)
        final_state = cast(K1State, graph.invoke(init))
        log_event(
            "k1_graph_invoke_end",
            {"last_status": final_state.get("last_status")},
            trace_ctx=trace_ctx,
        )

    task = col.get_task(task_id)
    record = task.get("record") if task.get("ok") else {}
    fr = final_state.get("final_result") or {}
    ok = bool(fr.get("ok")) and bool(record.get("success"))

    return {
        "ok": ok,
        "message": fr.get("message", "K1 flow finished"),
        "state": final_state,
        "record": record,
        "trace_completeness": (record.get("trace_completeness") or {}),
    }


def main() -> None:
    """CLI smoke for K-1."""
    out = run_k1_flow()
    rec = out.get("record") or {}
    print(
        {
            "ok": out.get("ok"),
            "success": rec.get("success"),
            "retry_count": rec.get("retry_count"),
            "handoff_count": rec.get("handoff_count"),
            "context_token_usage": rec.get("context_token_usage"),
            "trace_score": (rec.get("trace_completeness") or {}).get("score"),
        }
    )


if __name__ == "__main__":
    main()
