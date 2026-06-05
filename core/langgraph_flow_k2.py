"""
K-2: LangGraph orchestration upgrade on K-1 (Planner → Executor → Reviewer).

Adds explicit handoff nodes, executor error/retry branches, J-line skills on the
executor path, and P+ eval_gate metadata. Coexists with ``langgraph_flow_k1``;
does not modify ``/api/ask`` or gov_core ask_pipeline.

Graph (high level)
------------------

::

    START → prepare_context
         → planner
         → [route] handoff_planner | success_end | fail_end
         → handoff_planner          # orchestration handoff edge (metadata)
         → executor_prefetch        # J-line metrics-aware retrieve skill
         → executor
         → [route] handoff_executor | executor_retry | reviewer_fallback | fail_end
         → handoff_executor
         → reviewer
         → [route] success_end | executor | fail_end
         → finalize_eval            # P+ evaluate_task_record on M-line record
         → success_end | fail_end
         → END

Node responsibilities
---------------------
- **prepare_context**: H-line ``build_rooted_context`` (mode ``k2_pipeline``).
- **planner / executor / reviewer**: M-line agents + O/P retry spans (executor may simulate retry).
- **handoff_planner / handoff_executor**: explicit handoff edges; enrich ``eval_metadata``;
  agents still increment ``handoff_count`` on ``need_handoff``.
- **executor_prefetch**: J-line ``run_skill_retrieve`` (mock Qdrant).
- **executor_retry**: orchestration retry loop back to prefetch (increments ``executor_attempts``).
- **reviewer_fallback**: degraded path when executor fails but policy allows review.
- **finalize_eval**: P+ ``evaluate_task_record`` → ``eval_metadata`` for downstream gates.

Ask mainline merge (not wired this round)
-----------------------------------------
See ``ASK_MERGE_INTERFACE`` and module TODOs. Inputs/outputs must align with
``build_rooted_context(..., mode="ask_pipeline")`` and ask response envelope.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict, cast

from agents.base_agent import (
    ROLE_EXECUTOR,
    ROLE_PLANNER,
    ROLE_REVIEWER,
    route_by_status,
)
from core.context_entry import build_rooted_context
from core.langgraph_flow_k1 import (
    K1State,
    _AGENT_BY_ROLE,
    _agent_context_from_state,
    _make_agent_node,
    _run_agent_with_observability,
    fail_end_node,
    success_end_node,
)
from metrics.metrics_collector import MetricsCollector, get_collector
from observability.eval_gate import evaluate_task_record
from observability.logging_adapter import (
    agent_run_trace,
    log_event,
    reset_active_trace,
)
from skills.example_skill_retrieve import run_skill_retrieve

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover
    StateGraph = None  # type: ignore[misc, assignment]
    START = END = None  # type: ignore[misc, assignment]


# --- Ask merge contract (design only; no runtime wiring) --------------------

ASK_MERGE_INTERFACE: dict[str, Any] = {
    "status": "shadow_ready",
    "entry": {
        "required_input_keys": ("task_id", "goal", "query"),
        "context_builder": "core.context_entry.build_rooted_context",
        "context_mode": "ask_pipeline",
        "adapter": "core.k2_ask_shadow.map_task_input_for_k2",
        "notes": "K-2 uses k2_pipeline mode until merge; swap at single adapter node.",
    },
    "exit": {
        "required_output_keys": ("ok", "message", "result", "status"),
        "metrics_record": "metrics.MetricsCollector.get_task → record",
        "eval_screen": "observability.eval_gate.evaluate_task_record",
        "merge_hook": "core.k2_ask_shadow.k2_result_to_ask_response_envelope",
        "envelope_wrapper": "core.k2_ask_shadow.ask_response_envelope",
    },
    "shadow": {
        "runner": "core.k2_ask_shadow.run_shadow_pair",
        "compare_fields": (
            "ok",
            "status",
            "message_preview",
            "answer_preview",
            "retry_count",
            "handoff_count",
            "error_type",
            "context_entry_mode",
            "has_eval_metadata",
            "executed_node_count",
        ),
        "tests": "tests/test_k2_ask_shadow.py",
        "notes": "dev/test only; does not enable K-2 on /api/ask",
    },
    "why_not_hardwired_yet": [
        "ask_pipeline regression suite not extended for LangGraph branch",
        "K-1/K-2 stub agents differ from production LLM tool routing",
        "dual context modes (k2_pipeline vs ask_pipeline) need Governance alignment",
        "Telegram/API listener stability: single orchestration owner per process",
    ],
    "merge_hook_todo": "Gate on shadow diff baseline; then swap finalize_eval → ask envelope adapter",
}


class K2State(K1State, total=False):
    skill_results: dict[str, Any]
    eval_metadata: dict[str, Any]
    max_executor_retries: int
    allow_reviewer_fallback: bool
    recovery_route: str | None
    simulate_skill_failure: bool


K2RouteAfterPlanner = Literal["handoff_planner", "success_end", "fail_end"]
K2RouteAfterExecutor = Literal[
    "handoff_executor", "executor_retry", "reviewer_fallback", "fail_end"
]
K2RouteAfterReviewer = Literal["finalize_eval", "executor", "fail_end"]
K2RouteAfterFinalize = Literal["success_end", "fail_end"]

_ROLE_TO_HANDOFF_NODE: dict[str, K2RouteAfterPlanner | K2RouteAfterExecutor] = {
    ROLE_EXECUTOR: "handoff_planner",
    ROLE_REVIEWER: "handoff_executor",
}

_RETRYABLE_ERROR_TYPES = frozenset({"timeout", "tool_error"})


def _append_handoff_edge_metadata(
    state: K2State,
    *,
    from_role: str,
    to_role: str,
    via: str,
) -> dict[str, Any]:
    meta = dict(state.get("eval_metadata") or {})
    edges = list(meta.get("handoff_edges") or [])
    edges.append(
        {
            "from": from_role,
            "to": to_role,
            "via": via,
            "task_id": state.get("task_id"),
        }
    )
    meta["handoff_edges"] = edges
    return meta


def prepare_context_k2_node(state: K2State) -> dict[str, Any]:
    """H-line context entry with ``k2_pipeline`` mode label."""
    task_input = dict(state.get("task_input") or {})
    if not task_input.get("task_id"):
        task_input["task_id"] = state.get("task_id") or ""
    if not task_input.get("goal"):
        task_input["goal"] = state.get("goal") or ""

    built = build_rooted_context(task_input, mode="k2_pipeline")
    log_event(
        "build_context_done",
        {"ok": built.get("ok"), "message": built.get("message"), "entry": "k2_pipeline"},
        as_step=True,
    )

    token_usage = built.get("token_usage") if isinstance(built.get("token_usage"), dict) else {}
    tid = str(task_input.get("task_id") or state.get("task_id") or "")
    if token_usage and tid:
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
            metadata={"source": "context_entry", "entry_mode": "k2_pipeline"},
        )

    return {
        "task_id": task_input.get("task_id"),
        "goal": task_input.get("goal"),
        "task_input": task_input,
        "context_payload": built,
        "max_executor_retries": int(state.get("max_executor_retries") or 2),
        "allow_reviewer_fallback": bool(state.get("allow_reviewer_fallback", True)),
    }


def handoff_planner_node(state: K2State) -> dict[str, Any]:
    """Explicit orchestration edge: planner → executor (metadata; count from agent)."""
    target = state.get("next_agent") or ROLE_EXECUTOR
    log_event(
        "k2_handoff_edge",
        {"from": ROLE_PLANNER, "to": target, "edge": "planner_to_executor"},
    )
    meta = _append_handoff_edge_metadata(
        state, from_role=ROLE_PLANNER, to_role=str(target), via="handoff_planner_node"
    )
    return {"eval_metadata": meta, "recovery_route": "handoff_planner"}


def handoff_executor_node(state: K2State) -> dict[str, Any]:
    """Explicit orchestration edge: executor → reviewer."""
    target = state.get("next_agent") or ROLE_REVIEWER
    log_event(
        "k2_handoff_edge",
        {"from": ROLE_EXECUTOR, "to": target, "edge": "executor_to_reviewer"},
    )
    meta = _append_handoff_edge_metadata(
        state, from_role=ROLE_EXECUTOR, to_role=str(target), via="handoff_executor_node"
    )
    return {"eval_metadata": meta, "recovery_route": "handoff_executor"}


def executor_prefetch_node(state: K2State) -> dict[str, Any]:
    """J-line: metrics-aware mock retrieve before executor agent."""
    tid = str(state.get("task_id") or "")
    goal = str(state.get("goal") or "")
    simulate_fail = bool(state.get("simulate_skill_failure"))

    skill_out = run_skill_retrieve(
        tid,
        query=goal,
        top_k=3,
        simulate_first_failure=simulate_fail,
    )

    prior_skills = dict(state.get("skill_results") or {})
    prior_skills["retrieve"] = skill_out

    patch: dict[str, Any] = {"skill_results": prior_skills}
    if not skill_out.get("ok"):
        patch["last_status"] = "fail"
        patch["error_type"] = skill_out.get("error_type") or "tool_error"
        patch["agent_output"] = {
            "ok": False,
            "message": (skill_out.get("metadata") or {}).get("message", "skill retrieve failed"),
            "result": {},
            "status": "fail",
            "next_agent": None,
            "notes": {"error_type": skill_out.get("error_type"), "source": "executor_prefetch"},
        }
    else:
        hits = (skill_out.get("result") or {}).get("hits") if isinstance(skill_out.get("result"), dict) else []
        log_event(
            "k2_skill_prefetch_ok",
            {"hit_count": len(hits) if isinstance(hits, list) else 0, "skill": "retrieve"},
        )
    return patch


def executor_retry_node(state: K2State) -> dict[str, Any]:
    """Orchestration retry: bump attempts and loop to prefetch."""
    attempts = int(state.get("executor_attempts") or 0) + 1
    log_event(
        "k2_executor_retry",
        {"attempt": attempts, "error_type": state.get("error_type")},
    )
    meta = dict(state.get("eval_metadata") or {})
    retries = list(meta.get("executor_retries") or [])
    retries.append({"attempt": attempts, "error_type": state.get("error_type")})
    meta["executor_retries"] = retries
    return {
        "executor_attempts": attempts,
        "error_type": None,
        "recovery_route": "executor_retry",
        "eval_metadata": meta,
        "agent_output": {},
        "last_status": "",
    }


def reviewer_fallback_node(state: K2State) -> dict[str, Any]:
    """When executor exhausts retries, optionally still run reviewer (degraded)."""
    log_event("k2_reviewer_fallback", {"reason": state.get("error_type")})
    meta = dict(state.get("eval_metadata") or {})
    meta["reviewer_fallback"] = True
    meta["executor_error_type"] = state.get("error_type")
    agent = _AGENT_BY_ROLE[ROLE_REVIEWER]
    patch = _run_agent_with_observability(
        agent,
        state,
        span_name="reviewer_fallback",
        trace_ctx=None,
        collector=get_collector(),
    )
    patch["eval_metadata"] = meta
    patch["recovery_route"] = "reviewer_fallback"
    return patch


def finalize_eval_node(state: K2State) -> dict[str, Any]:
    """P+: attach eval_gate screening to state for export / ask merge."""
    tid = str(state.get("task_id") or "")
    col = get_collector()
    task = col.get_task(tid)
    record = task.get("record") if task.get("ok") else {}
    if not isinstance(record, dict):
        record = {}

    eval_out = evaluate_task_record(record)
    meta = dict(state.get("eval_metadata") or {})
    meta["eval_gate"] = eval_out
    meta["metrics_snapshot"] = {
        "retry_count": record.get("retry_count"),
        "handoff_count": record.get("handoff_count"),
        "success": record.get("success"),
        "trace_score": (record.get("trace_completeness") or {}).get("score"),
    }

    log_event(
        "k2_eval_gate",
        {"pass": eval_out.get("pass"), "tags": eval_out.get("tags")},
    )
    return {"eval_metadata": meta}


def _route_after_planner(state: K2State) -> K2RouteAfterPlanner:
    decision = route_by_status(state)
    if decision == "handoff":
        target = state.get("next_agent") or (state.get("agent_output") or {}).get("next_agent")
        if _ROLE_TO_HANDOFF_NODE.get(str(target or "")) == "handoff_planner":
            return "handoff_planner"
        return "fail_end"
    if decision == "success":
        return "success_end"
    return "fail_end"


def _route_after_executor(state: K2State) -> K2RouteAfterExecutor:
    out = state.get("agent_output") or {}
    status = out.get("status")
    if status == "need_handoff":
        target = state.get("next_agent") or out.get("next_agent")
        if str(target or "") == ROLE_REVIEWER:
            return "handoff_executor"
        return "fail_end"
    if status == "success":
        return "handoff_executor"

    err = str(state.get("error_type") or "")
    attempts = int(state.get("executor_attempts") or 0)
    max_retries = int(state.get("max_executor_retries") or 2)
    if err in _RETRYABLE_ERROR_TYPES and attempts < max_retries:
        return "executor_retry"
    if state.get("allow_reviewer_fallback", True):
        return "reviewer_fallback"
    return "fail_end"


def _route_after_reviewer(state: K2State) -> K2RouteAfterReviewer:
    decision = route_by_status(state)
    if decision == "success":
        return "finalize_eval"
    if decision == "handoff":
        target = state.get("next_agent") or (state.get("agent_output") or {}).get("next_agent")
        if str(target or "") == ROLE_EXECUTOR:
            return "executor"
        return "fail_end"
    return "fail_end"


def _route_after_finalize(state: K2State) -> K2RouteAfterFinalize:
    out = state.get("agent_output") or {}
    if out.get("status") == "success" or state.get("last_status") == "success":
        return "success_end"
    fr = state.get("final_result") or {}
    if fr.get("ok"):
        return "success_end"
    if out.get("status") == "fail" or state.get("last_status") == "fail":
        return "fail_end"
    return "success_end"


def _route_after_prefetch(state: K2State) -> Literal["executor", "fail_end"]:
    out = state.get("agent_output") or {}
    if out.get("status") == "fail":
        return "fail_end"
    return "executor"


def build_k2_graph() -> Any:
    if StateGraph is None:
        raise ImportError("langgraph is required for K-2 flow; install langgraph package")

    g = StateGraph(K2State)
    g.add_node("prepare_context", prepare_context_k2_node)
    g.add_node("planner", _make_agent_node(ROLE_PLANNER, span_name="planner"))
    g.add_node("handoff_planner", handoff_planner_node)
    g.add_node("executor_prefetch", executor_prefetch_node)
    g.add_node("executor", _make_agent_node(ROLE_EXECUTOR, span_name="executor", simulate_retry=True))
    g.add_node("handoff_executor", handoff_executor_node)
    g.add_node("executor_retry", executor_retry_node)
    g.add_node("reviewer_fallback", reviewer_fallback_node)
    g.add_node("reviewer", _make_agent_node(ROLE_REVIEWER, span_name="reviewer"))
    g.add_node("finalize_eval", finalize_eval_node)
    g.add_node("success_end", success_end_node)
    g.add_node("fail_end", fail_end_node)

    g.add_edge(START, "prepare_context")
    g.add_edge("prepare_context", "planner")
    g.add_conditional_edges(
        "planner",
        _route_after_planner,
        {
            "handoff_planner": "handoff_planner",
            "success_end": "success_end",
            "fail_end": "fail_end",
        },
    )
    g.add_edge("handoff_planner", "executor_prefetch")
    g.add_conditional_edges(
        "executor_prefetch",
        _route_after_prefetch,
        {"executor": "executor", "fail_end": "fail_end"},
    )
    g.add_conditional_edges(
        "executor",
        _route_after_executor,
        {
            "handoff_executor": "handoff_executor",
            "executor_retry": "executor_retry",
            "reviewer_fallback": "reviewer_fallback",
            "fail_end": "fail_end",
        },
    )
    g.add_edge("executor_retry", "executor_prefetch")
    g.add_edge("handoff_executor", "reviewer")
    g.add_conditional_edges(
        "reviewer",
        _route_after_reviewer,
        {
            "finalize_eval": "finalize_eval",
            "executor": "executor_prefetch",
            "fail_end": "fail_end",
        },
    )
    g.add_edge("reviewer_fallback", "finalize_eval")
    g.add_conditional_edges(
        "finalize_eval",
        _route_after_finalize,
        {"success_end": "success_end", "fail_end": "fail_end"},
    )
    g.add_edge("success_end", END)
    g.add_edge("fail_end", END)
    return g.compile()


_COMPILED_K2: Any | None = None


def _compiled_k2() -> Any:
    global _COMPILED_K2
    if _COMPILED_K2 is None:
        _COMPILED_K2 = build_k2_graph()
    return _COMPILED_K2


def initial_k2_state(
    *,
    task_id: str = "k2-demo-001",
    goal: str = "K-2 LangGraph orchestration smoke",
    task_input: dict[str, Any] | None = None,
    simulate_skill_failure: bool = False,
    allow_reviewer_fallback: bool = True,
    max_executor_retries: int = 2,
) -> K2State:
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
        "skill_results": {},
        "eval_metadata": {},
        "max_executor_retries": max_executor_retries,
        "allow_reviewer_fallback": allow_reviewer_fallback,
        "recovery_route": None,
        "simulate_skill_failure": simulate_skill_failure,
    }


def run_k2_flow(
    *,
    task_id: str = "k2-demo-001",
    goal: str = "K-2 LangGraph orchestration smoke",
    task_input: dict[str, Any] | None = None,
    collector: MetricsCollector | None = None,
    simulate_skill_failure: bool = False,
    allow_reviewer_fallback: bool = True,
) -> dict[str, Any]:
    """
    Invoke the K-2 graph once inside ``agent_run_trace``.

    Returns ``{ok, message, state, record, eval_metadata}``.
    """
    col = collector or get_collector()
    reset_active_trace()
    init = initial_k2_state(
        task_id=task_id,
        goal=goal,
        task_input=task_input,
        simulate_skill_failure=simulate_skill_failure,
        allow_reviewer_fallback=allow_reviewer_fallback,
    )
    graph = _compiled_k2()
    final_state: K2State = {}

    with agent_run_trace("langgraph_k2", task_id=task_id, collector=col) as trace_ctx:
        log_event("k2_graph_invoke_start", {"task_id": task_id}, trace_ctx=trace_ctx)
        final_state = cast(K2State, graph.invoke(init))
        log_event(
            "k2_graph_invoke_end",
            {"last_status": final_state.get("last_status")},
            trace_ctx=trace_ctx,
        )

    task = col.get_task(task_id)
    record = task.get("record") if task.get("ok") else {}
    fr = final_state.get("final_result") or {}
    eval_meta = final_state.get("eval_metadata") or {}
    ok = bool(fr.get("ok")) and bool(record.get("success"))

    return {
        "ok": ok,
        "message": fr.get("message", "K2 flow finished"),
        "state": final_state,
        "record": record,
        "eval_metadata": eval_meta,
        "trace_completeness": (record.get("trace_completeness") or {}),
    }


def main() -> None:
    out = run_k2_flow()
    rec = out.get("record") or {}
    ev = out.get("eval_metadata") or {}
    print(
        {
            "ok": out.get("ok"),
            "success": rec.get("success"),
            "retry_count": rec.get("retry_count"),
            "handoff_count": rec.get("handoff_count"),
            "eval_pass": (ev.get("eval_gate") or {}).get("pass"),
            "handoff_edges": len(ev.get("handoff_edges") or []),
            "skill_ok": (out.get("state", {}).get("skill_results", {}).get("retrieve", {}).get("ok")),
        }
    )


if __name__ == "__main__":
    main()
