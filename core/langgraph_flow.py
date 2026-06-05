"""
Test-compatible shim for ask LangGraph mainline.

Provides ``run_ask_flow`` with selector → retrieve → answer routing so CI and
unit tests can run without the full ``gov_core_system`` graph. Replace when the
production ``langgraph_flow`` module is available.
"""

from __future__ import annotations

from typing import Any

from core.ask_direct_answer import perform_direct_answer
from core.ask_pipeline_ibridge_v0 import _import_build_rooted_context
from core.ask_rag_selector import decide_use_rag
from core.fallback import retrieve_stub_fallback, should_use_retrieve_stub
from core.infra_health import run_full_healthcheck
from core.rag_backend import rag_answer
import skills.skill_answer_for_ask as answer_skill_mod
import skills.skill_retrieve_for_ask as retrieve_skill_mod
from metrics.metrics_collector import get_collector
from observability.logging_adapter import agent_run_trace

_COMPILED_ASK: Any = None


def _perform_retrieve_query(query: str, top_k: int) -> dict[str, Any]:
    if should_use_retrieve_stub():
        return retrieve_stub_fallback(query, top_k)
    return {
        "ok": True,
        "message": "shim retrieve ok",
        "query": query,
        "top_k": top_k,
        "hits": [],
    }


def _build_context_payload(query: str) -> dict[str, Any] | None:
    build_rooted_context = _import_build_rooted_context()
    built = build_rooted_context({"query": query}, mode="ask_pipeline")
    if isinstance(built, dict) and built.get("ok"):
        return built
    return None


def run_ask_flow(
    query: str,
    *,
    top_k: int = 3,
    ibridge_v0: bool = False,
    thread_id: str | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    task_id = (thread_id or "ask-flow").strip() or "ask-flow"
    executed_nodes: list[str] = []
    collector = get_collector()

    with agent_run_trace("ask_pipeline", task_id=task_id) as trace_ctx:
        executed_nodes.append("health_node")
        health = run_full_healthcheck()
        if not health.get("ok"):
            return {
                "ok": False,
                "message": health.get("message") or "health check failed",
                "executed_nodes": executed_nodes,
            }

        context_payload = _build_context_payload(query)
        executed_nodes.append("selector_node")
        selector = decide_use_rag(query, context_payload=context_payload)

        answer_block: dict[str, Any] | None = None
        retrieve_result: dict[str, Any] | None = None
        retrieve_fallback = False

        if selector.get("use_rag"):
            executed_nodes.append("retrieve_node")

            def _retrieve_core() -> dict[str, Any]:
                return _perform_retrieve_query(query, top_k)

            retrieve_skill = retrieve_skill_mod.run_skill_retrieve_for_ask(
                task_id,
                core_fn=_retrieve_core,
                collector=collector,
                trace_ctx=trace_ctx,
            )
            retrieve_result = (
                retrieve_skill.get("result")
                if isinstance(retrieve_skill.get("result"), dict)
                else None
            )

            if retrieve_result and retrieve_result.get("ok"):
                def _answer_core() -> dict[str, Any]:
                    return rag_answer(query, top_k)

                executed_nodes.append("answer_node")
                skill_out = answer_skill_mod.run_skill_answer_for_ask(
                    task_id,
                    core_fn=_answer_core,
                    collector=collector,
                    trace_ctx=trace_ctx,
                )
                answer_block = skill_out.get("result") if isinstance(skill_out.get("result"), dict) else None
            else:
                retrieve_fallback = True
                executed_nodes.append("answer_node")

                def _fallback_core() -> dict[str, Any]:
                    return perform_direct_answer(
                        query,
                        retrieve_error=str(retrieve_result.get("message") or "retrieve failed"),
                        retrieve_error_type=str(retrieve_result.get("error_type") or "unknown"),
                    )

                skill_out = answer_skill_mod.run_skill_answer_for_ask(
                    task_id,
                    core_fn=_fallback_core,
                    collector=collector,
                    trace_ctx=trace_ctx,
                )
                answer_block = skill_out.get("result") if isinstance(skill_out.get("result"), dict) else None
        else:
            executed_nodes.append("answer_node")

            def _direct_core() -> dict[str, Any]:
                return perform_direct_answer(query)

            skill_out = answer_skill_mod.run_skill_answer_for_ask(
                task_id,
                core_fn=_direct_core,
                collector=collector,
                trace_ctx=trace_ctx,
            )
            answer_block = skill_out.get("result") if isinstance(skill_out.get("result"), dict) else None

        collector.end_task(task_id, success=True)
        record = collector.get_task(task_id).get("record") or {}

        selector_decision = {
            "use_rag": bool(selector.get("use_rag")),
            "skip_rag": bool(selector.get("skip_rag")),
            "selector_rule_id": selector.get("selector_rule_id"),
            "answer_mode": selector.get("answer_mode"),
            "retrieve_fallback": retrieve_fallback,
        }
        if retrieve_fallback and isinstance(answer_block, dict):
            selector_decision["retrieve_error_type"] = answer_block.get("retrieve_error_type")

        out: dict[str, Any] = {
            "ok": True,
            "message": "ok",
            "query": query,
            "top_k": top_k,
            "executed_nodes": executed_nodes,
            "ask_selector": selector,
            "answer": answer_block,
            "retrieve": retrieve_result,
            "_context_entry_payload": context_payload,
        }

        if ibridge_v0:
            out["ibridge_v0"] = {"selector_decision": selector_decision}
            out["ibridge_record"] = record

        return out
