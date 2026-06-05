"""
D3 multi-agent contract stub.

Contract docs: agents/agent_contract.md, handoff_spec.md, agent_role_map.md
LangGraph: use invoke_node(state) or to_graph_state_patch(output).
"""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Any, Final, Literal, TypedDict

# --- Contract enums / types -------------------------------------------------

AgentStatusValue = Literal["success", "fail", "need_handoff"]

VALID_STATUSES: Final[frozenset[str]] = frozenset({"success", "fail", "need_handoff"})

ROLE_PLANNER: Final[str] = "planner_agent"
ROLE_EXECUTOR: Final[str] = "executor_agent"
ROLE_REVIEWER: Final[str] = "reviewer_agent"

KNOWN_ROLES: Final[frozenset[str]] = frozenset(
    {ROLE_PLANNER, ROLE_EXECUTOR, ROLE_REVIEWER}
)

# Default handoff edges (see handoff_spec.md §4)
ALLOWED_HANDOFF_EDGES: Final[frozenset[tuple[str, str]]] = frozenset(
    {
        (ROLE_PLANNER, ROLE_EXECUTOR),
        (ROLE_EXECUTOR, ROLE_REVIEWER),
        (ROLE_EXECUTOR, ROLE_PLANNER),
        (ROLE_REVIEWER, ROLE_EXECUTOR),
    }
)


class AgentInput(TypedDict, total=False):
    task_id: str
    goal: str
    context: dict[str, Any]


class AgentOutput(TypedDict, total=False):
    result: Any
    status: AgentStatusValue
    next_agent: str | None
    notes: str | list[Any] | dict[str, Any]
    ok: bool
    message: str


class ValidationReport(TypedDict):
    ok: bool
    message: str
    errors: list[str]


def validate_input(agent_input: dict[str, Any]) -> ValidationReport:
    """Validate AgentInput before run."""
    errors: list[str] = []
    for key in ("task_id", "goal", "context"):
        if key not in agent_input:
            errors.append(f"missing required input key: {key}")
    if "context" in agent_input and not isinstance(agent_input.get("context"), dict):
        errors.append("context must be an object")
    if errors:
        return {"ok": False, "message": "invalid agent input", "errors": errors}
    return {"ok": True, "message": "input valid", "errors": []}


def validate_output(output: dict[str, Any]) -> ValidationReport:
    """
    Validate AgentOutput contract (agent_contract.md §4).

    Returns ok=False with errors list when invalid.
    """
    errors: list[str] = []
    for key in ("result", "status", "notes"):
        if key not in output:
            errors.append(f"missing required output key: {key}")

    status = output.get("status")
    if status not in VALID_STATUSES:
        errors.append(f"status must be one of {sorted(VALID_STATUSES)}")
    else:
        next_agent = output.get("next_agent")
        if status == "need_handoff":
            if not next_agent or not isinstance(next_agent, str):
                errors.append("need_handoff requires non-empty next_agent")
            elif next_agent not in KNOWN_ROLES:
                errors.append(f"unknown next_agent role: {next_agent}")
        elif next_agent not in (None, ""):
            errors.append("next_agent must be null when status is not need_handoff")

    if "result" in output and output["result"] is None:
        errors.append("result must not be None (use {} if empty)")

    if errors:
        return {"ok": False, "message": "invalid agent output", "errors": errors}
    return {"ok": True, "message": "output valid", "errors": []}


def apply_envelope(output: dict[str, Any], *, default_message: str = "") -> dict[str, Any]:
    """Attach repo-standard ok/message fields (ENGINEERING_CONTRACT appendix B)."""
    out = copy.deepcopy(output)
    status = out.get("status")
    out["ok"] = status == "success"
    if not out.get("message"):
        if status == "need_handoff":
            out["message"] = f"handoff to {out.get('next_agent')}"
        elif status == "fail":
            out["message"] = default_message or "agent failed"
        else:
            out["message"] = default_message or "agent succeeded"
    return out


class BaseAgent(ABC):
    """
    Abstract agent with structured dict I/O.

    Subclasses implement _execute(input) -> AgentOutput (without envelope).
    """

    role_id: str = "base_agent"

    def __init__(self, *, strict_handoff_edges: bool = True) -> None:
        self.strict_handoff_edges = strict_handoff_edges

    def validate_output(self, output: dict[str, Any]) -> ValidationReport:
        report = validate_output(output)
        if not report["ok"]:
            return report
        if self.strict_handoff_edges and output.get("status") == "need_handoff":
            target = output.get("next_agent")
            edge = (self.role_id, target)
            if edge not in ALLOWED_HANDOFF_EDGES:
                return {
                    "ok": False,
                    "message": "handoff edge not allowed",
                    "errors": [f"edge ({self.role_id} -> {target}) not in ALLOWED_HANDOFF_EDGES"],
                }
        return report

    @abstractmethod
    def _execute(self, agent_input: dict[str, Any]) -> dict[str, Any]:
        """Subclass: return contract output without ok/message envelope."""

    def run(self, agent_input: dict[str, Any]) -> dict[str, Any]:
        """
        Run agent with validated input and structured output.

        On validation failure returns ok=False dict (no exception).
        """
        in_report = validate_input(agent_input)
        if not in_report["ok"]:
            return {
                "ok": False,
                "message": in_report["message"],
                "result": {},
                "status": "fail",
                "next_agent": None,
                "notes": {"validation_errors": in_report["errors"]},
            }

        try:
            raw = self._execute(agent_input)
        except Exception as exc:  # noqa: BLE001 — contract layer must not crash orchestrator
            return apply_envelope(
                {
                    "result": {},
                    "status": "fail",
                    "next_agent": None,
                    "notes": {"error": type(exc).__name__, "detail": str(exc)},
                },
                default_message="execution error",
            )

        out_report = self.validate_output(raw)
        if not out_report["ok"]:
            return apply_envelope(
                {
                    "result": raw.get("result", {}),
                    "status": "fail",
                    "next_agent": None,
                    "notes": {"validation_errors": out_report["errors"]},
                },
                default_message="output validation failed",
            )

        return apply_envelope(raw)

    # --- LangGraph adapters -------------------------------------------------

    @staticmethod
    def from_graph_state(state: dict[str, Any]) -> dict[str, Any]:
        """Extract AgentInput from LangGraph state."""
        if "agent_input" in state:
            return dict(state["agent_input"])
        return {
            "task_id": state.get("task_id", ""),
            "goal": state.get("goal", ""),
            "context": dict(state.get("context") or {}),
        }

    @staticmethod
    def to_graph_state_patch(
        output: dict[str, Any],
        *,
        prior_chain: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Build state patch for LangGraph.

        Sets agent_output and appends to handoff_chain when status is need_handoff.
        """
        chain = list(prior_chain or [])
        chain.append(copy.deepcopy(output))
        patch: dict[str, Any] = {
            "agent_output": output,
            "handoff_chain": chain,
            "last_status": output.get("status"),
        }
        if output.get("status") == "need_handoff":
            patch["next_agent"] = output.get("next_agent")
        return patch

    def invoke_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """LangGraph node callable: state -> partial state update."""
        agent_input = self.from_graph_state(state)
        output = self.run(agent_input)
        prior = state.get("handoff_chain")
        if isinstance(prior, list):
            prior_chain = prior
        else:
            prior_chain = []
        patch = self.to_graph_state_patch(output, prior_chain=prior_chain)
        if output.get("status") == "need_handoff" and output.get("ok") is False:
            self._record_handoff_metric(agent_input.get("task_id", ""))
        return patch

    @staticmethod
    def _record_handoff_metric(task_id: str) -> None:
        """Optional D3 metric; no-op if metrics package unavailable."""
        if not task_id:
            return
        try:
            from metrics.metrics_collector import MetricsCollector

            MetricsCollector().record_handoff(task_id)
        except Exception:
            pass

    def build_handoff_input(
        self,
        *,
        task_id: str,
        goal: str,
        prior_outputs: list[dict[str, Any]],
        handoff_payload: dict[str, Any],
        target_agent: str,
        artifacts: dict[str, Any] | None = None,
        constraints: list[str] | None = None,
    ) -> dict[str, Any]:
        """Construct downstream AgentInput per handoff_spec.md §3."""
        handoff_index = sum(
            1 for o in prior_outputs if o.get("status") == "need_handoff"
        )
        ctx: dict[str, Any] = {
            "prior_outputs": prior_outputs,
            "handoff_payload": handoff_payload,
            "metadata": {
                "handoff_index": handoff_index,
                "source_agent": self.role_id,
                "target_agent": target_agent,
            },
        }
        if artifacts:
            ctx["artifacts"] = artifacts
        if constraints:
            ctx["constraints"] = constraints
        return {"task_id": task_id, "goal": goal, "context": ctx}


# --- Skeleton implementations -----------------------------------------------


class PlannerAgent(BaseAgent):
    role_id = ROLE_PLANNER

    def _execute(self, agent_input: dict[str, Any]) -> dict[str, Any]:
        return {
            "result": {
                "plan_id": "stub-plan",
                "steps": [{"id": "1", "action": "stub", "acceptance": "stub"}],
                "frozen": True,
            },
            "status": "need_handoff",
            "next_agent": ROLE_EXECUTOR,
            "notes": {
                "reason": "plan frozen (stub)",
                "downstream_goal_hint": "execute plan steps",
                "open_questions": [],
            },
        }


class ExecutorAgent(BaseAgent):
    role_id = ROLE_EXECUTOR

    def _execute(self, agent_input: dict[str, Any]) -> dict[str, Any]:
        return {
            "result": {
                "executed_steps": ["1"],
                "artifacts": {},
                "partial": False,
            },
            "status": "need_handoff",
            "next_agent": ROLE_REVIEWER,
            "notes": {"reason": "execution complete (stub)", "blocker": None},
        }


class ReviewerAgent(BaseAgent):
    role_id = ROLE_REVIEWER

    def _execute(self, agent_input: dict[str, Any]) -> dict[str, Any]:
        return {
            "result": {
                "verdict": "accept",
                "checks": [],
                "evidence_refs": [],
            },
            "status": "success",
            "next_agent": None,
            "notes": {"reason": "stub accept"},
        }


def route_by_status(state: dict[str, Any]) -> str:
    """
    LangGraph conditional edge helper.

    Returns: 'success' | 'fail' | 'handoff'
    """
    out = state.get("agent_output") or {}
    status = out.get("status")
    if status == "success":
        return "success"
    if status == "need_handoff":
        return "handoff"
    return "fail"
