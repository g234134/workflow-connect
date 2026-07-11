"""
Workflow node classification for retry / interrupt / side-effect handling (Package D).

Maps production LangGraph nodes (``core.langgraph_flow``) and minimal orchestration nodes
(``Departments/01_Orchestration/workflow/graph``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class NodeKind(str, Enum):
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"
    HUMAN_CONFIRM = "human_confirm"
    SIDE_EFFECT = "side_effect"


@dataclass(frozen=True)
class NodePolicy:
    node_id: str
    kinds: frozenset[NodeKind]
    default_retryable: bool
    notes: str = ""

    def has(self, kind: NodeKind) -> bool:
        return kind in self.kinds

    def is_retryable_by_policy(self) -> bool:
        if NodeKind.NON_RETRYABLE in self.kinds:
            return False
        if NodeKind.RETRYABLE in self.kinds:
            return True
        return self.default_retryable


# Production graph (langgraph_flow.py)
_PRODUCTION_NODES: tuple[NodePolicy, ...] = (
    NodePolicy(
        "health_node",
        frozenset({NodeKind.RETRYABLE}),
        True,
        "Infra probes; transient network/DB blips may recover.",
    ),
    NodePolicy(
        "ingest_node",
        frozenset({NodeKind.SIDE_EFFECT, NodeKind.NON_RETRYABLE}),
        False,
        "Writes vectors/docs — retry risks duplicates until idempotency key wired.",
    ),
    NodePolicy(
        "verify_node",
        frozenset({NodeKind.RETRYABLE}),
        True,
        "Read/validate only.",
    ),
    NodePolicy(
        "retrieve_node",
        frozenset({NodeKind.RETRYABLE}),
        True,
        "Qdrant read; safe to retry.",
    ),
    NodePolicy(
        "answer_node",
        frozenset({NodeKind.SIDE_EFFECT, NodeKind.RETRYABLE}),
        True,
        "LLM call (cost) — retry only when error is retryable; budget hook (B).",
    ),
)

# Minimal orchestration graph (workflow/graph.py)
_MINIMAL_NODES: tuple[NodePolicy, ...] = (
    NodePolicy("start", frozenset({NodeKind.RETRYABLE}), True, "Logging only."),
    NodePolicy(
        "retrieve_context",
        frozenset({NodeKind.RETRYABLE}),
        True,
        "Mock brain read.",
    ),
    NodePolicy(
        "human_confirm",
        frozenset({NodeKind.HUMAN_CONFIRM, NodeKind.NON_RETRYABLE}),
        False,
        "Interrupt before decide; resume supplies human_approved payload.",
    ),
    NodePolicy(
        "decide",
        frozenset({NodeKind.SIDE_EFFECT}),
        False,
        "Writes JSON checkpoint mirror — idempotency via make_idempotency_key.",
    ),
    NodePolicy("finish", frozenset({NodeKind.RETRYABLE}), True, "Logging only."),
)

NODE_POLICIES: dict[str, NodePolicy] = {
    p.node_id: p for p in (*_PRODUCTION_NODES, *_MINIMAL_NODES)
}


def get_node_policy(node_id: str) -> NodePolicy | None:
    return NODE_POLICIES.get(node_id)


def default_retryable_for_node(node_id: str) -> bool:
    policy = get_node_policy(node_id)
    if policy is None:
        return False
    return policy.is_retryable_by_policy()


def requires_human_confirm(node_id: str) -> bool:
    policy = get_node_policy(node_id)
    return policy is not None and policy.has(NodeKind.HUMAN_CONFIRM)


def has_side_effects(node_id: str) -> bool:
    policy = get_node_policy(node_id)
    return policy is not None and policy.has(NodeKind.SIDE_EFFECT)


# Retryable exception types (network / timeout always retry regardless of node)
RETRYABLE_EXCEPTION_TYPES: tuple[type[BaseException], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def classify_nodes_report() -> list[dict[str, Any]]:
    """Serializable matrix for ops / deliverables."""
    rows: list[dict[str, Any]] = []
    for policy in NODE_POLICIES.values():
        rows.append(
            {
                "node_id": policy.node_id,
                "retryable": policy.is_retryable_by_policy(),
                "human_confirm": policy.has(NodeKind.HUMAN_CONFIRM),
                "side_effect": policy.has(NodeKind.SIDE_EFFECT),
                "notes": policy.notes,
            }
        )
    return sorted(rows, key=lambda r: r["node_id"])


def side_effect_hooks(node_id: str) -> dict[str, str]:
    """
    Integration hooks for Package B (budget) and idempotency — do not invoke budget here.

    TODO(B): call budget gate before answer_node / ingest_node LLM or embed spend.
    TODO(D): pass make_idempotency_key(run_id, node_id) into ingest/answer when keys land.
    """
    hooks: dict[str, str] = {}
    if not has_side_effects(node_id):
        return hooks
    hooks["budget_hook"] = "TODO(B): core.budget.check_before_side_effect(node_id, run_id)"
    hooks["idempotency_hook"] = "TODO(D): make_idempotency_key(run_id, node_id) before write"
    if node_id == "ingest_node":
        hooks["duplicate_guard"] = "TODO(D): dedupe ingest_batch on idempotency_key"
    if node_id == "answer_node":
        hooks["duplicate_guard"] = "TODO(D): dedupe rag_answer on idempotency_key"
    return hooks


def merge_retryable_from_node(
    exc: BaseException,
    *,
    node_id: str | None = None,
    structured: Mapping[str, Any] | None = None,
) -> bool:
    """Combine explicit structured flag with node policy default."""
    if structured and "retryable" in structured:
        return bool(structured["retryable"])
    if node_id:
        return default_retryable_for_node(node_id)
    return False
