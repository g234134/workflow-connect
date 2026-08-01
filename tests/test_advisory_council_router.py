"""Tests for advisory council router."""

from core.advisory_council_router import (
    AdvisoryCouncilRouter,
    COUNCIL_LABELS,
    COUNCIL_LC,
    COUNCIL_LG,
    COUNCIL_MCP,
    COUNCIL_MOD,
    COUNCIL_OBS,
    COUNCIL_TOOL,
    TASK_TYPE_TO_COUNCIL,
)


def test_resolve_single_council():
    router = AdvisoryCouncilRouter()
    assert router.resolve_councils("prompt_design") == [COUNCIL_LC]
    assert router.resolve_councils("workflow_design") == [COUNCIL_LG]
    assert router.resolve_councils("tracing_setup") == [COUNCIL_OBS]
    assert router.resolve_councils("terminal_automation") == [COUNCIL_TOOL]
    assert router.resolve_councils("model_selection") == [COUNCIL_MOD]
    assert router.resolve_councils("server_discovery") == [COUNCIL_MCP]


def test_resolve_multi_council():
    router = AdvisoryCouncilRouter()
    councils = router.resolve_councils("end_to_end_pipeline")
    assert COUNCIL_LC in councils
    assert COUNCIL_LG in councils
    assert COUNCIL_TOOL in councils
    assert COUNCIL_OBS in councils


def test_resolve_unknown_falls_back():
    router = AdvisoryCouncilRouter()
    councils = router.resolve_councils("totally_unknown_type")
    assert COUNCIL_LC in councils
    assert COUNCIL_OBS in councils


def test_route_task_returns_structure():
    router = AdvisoryCouncilRouter()
    result = router.route_task("prompt_design", {"task_id": "T1"})
    assert result["task_type"] == "prompt_design"
    assert isinstance(result["councils"], list)
    assert isinstance(result["results"], dict)
    assert isinstance(result["merged"], dict)
    assert result["merged"]["all_ok"] is True


def test_route_task_unknown_type():
    router = AdvisoryCouncilRouter()
    result = router.route_task("unknown", {})
    assert result["task_type"] == "unknown"
    assert result["merged"]["all_ok"] is True


def test_routing_log_accumulates():
    router = AdvisoryCouncilRouter()
    router.route_task("prompt_design", {})
    router.route_task("workflow_design", {})
    log = router.get_routing_log()
    assert len(log) == 2
    assert log[0]["task_type"] == "prompt_design"
    assert log[1]["task_type"] == "workflow_design"


def test_all_task_types_mapped():
    """Every defined task type must map to at least one council."""
    for task_type, councils in TASK_TYPE_TO_COUNCIL.items():
        assert len(councils) >= 1, f"{task_type} has no council"


def test_all_councils_have_labels():
    for council_id in [
        COUNCIL_LC,
        COUNCIL_LG,
        COUNCIL_MCP,
        COUNCIL_OBS,
        COUNCIL_TOOL,
        COUNCIL_MOD,
    ]:
        assert council_id in COUNCIL_LABELS, f"{council_id} missing label"
