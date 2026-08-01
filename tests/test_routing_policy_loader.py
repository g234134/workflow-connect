"""Unit tests for Routing Policy v1 loader (B-F3)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.routing_policy_loader import (  # noqa: E402
    build_registry_context,
    get_default_wave_b_eval_route_tool_ids,
    get_route,
    load_routing_policy,
    resolve_route_tool_ids,
    validate_routing_policy,
)
from skills.gov_tool_registry import load_gov_tool_cards  # noqa: E402


def _minimal_valid_policy(**overrides: object) -> dict:
    policy = {
        "schema_version": "routing_policy_v1",
        "default_env": "dev",
        "tools": [
            {"tool_id": "obs.eval.export", "enabled": True, "review_required": False},
            {"tool_id": "obs.eval.report", "enabled": True, "review_required": False},
        ],
        "routes": [
            {
                "route_id": "wave_b.eval_report",
                "description": "test route",
                "env": "dev",
                "steps": [
                    {"kind": "tool", "tool_id": "obs.eval.export"},
                    {"kind": "tool", "tool_id": "obs.eval.report"},
                ],
            }
        ],
    }
    policy.update(overrides)
    return policy


class TestRoutingPolicyLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = build_registry_context(repo_root=_REPO_ROOT)

    def test_load_production_policy_validate_ok(self) -> None:
        policy = load_routing_policy(repo_root=_REPO_ROOT)
        result = validate_routing_policy(policy, registry=self.registry, repo_root=_REPO_ROOT)
        self.assertTrue(result["ok"], msg=json.dumps(result, indent=2))
        self.assertEqual(result["total_tools"], 6)
        self.assertEqual(result["total_routes"], 2)
        self.assertEqual(result["errors"], [])

    def test_get_route_and_resolve_wave_b_eval_report(self) -> None:
        policy = load_routing_policy(repo_root=_REPO_ROOT)
        route = get_route(policy, "wave_b.eval_report")
        self.assertIsNotNone(route)
        self.assertEqual(route["env"], "dev")

        resolved = resolve_route_tool_ids(policy, "wave_b.eval_report")
        self.assertTrue(resolved["ok"])
        self.assertEqual(
            resolved["tool_ids"],
            ["obs.eval.export", "obs.eval.report", "obs.wf.status_summary"],
        )

    def test_default_wave_b_eval_route_helper_uses_config(self) -> None:
        result = get_default_wave_b_eval_route_tool_ids(repo_root=_REPO_ROOT)
        self.assertTrue(result["ok"])
        self.assertEqual(result["route_id"], "wave_b.eval_report")
        self.assertEqual(
            result["tool_ids"],
            ["obs.eval.export", "obs.eval.report", "obs.wf.status_summary"],
        )

    def test_unknown_tool_id_in_tools_section_fails(self) -> None:
        policy = _minimal_valid_policy(
            tools=[{"tool_id": "obs.eval.not_real", "enabled": True, "review_required": False}]
        )
        result = validate_routing_policy(policy, registry=self.registry, repo_root=_REPO_ROOT)
        self.assertFalse(result["ok"])
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("tools.unknown_catalog", codes)

    def test_route_referencing_undeclared_tool_fails(self) -> None:
        policy = _minimal_valid_policy(
            routes=[
                {
                    "route_id": "wave_b.eval_report",
                    "description": "bad route",
                    "env": "dev",
                    "steps": [{"kind": "tool", "tool_id": "obs.wf.status_summary"}],
                }
            ]
        )
        result = validate_routing_policy(policy, registry=self.registry, repo_root=_REPO_ROOT)
        self.assertFalse(result["ok"])
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("routes.step.undeclared_tool", codes)

    def test_route_referencing_skeleton_tool_fails(self) -> None:
        policy = _minimal_valid_policy(
            tools=[
                {"tool_id": "obs.eval.export", "enabled": True, "review_required": False},
                {"tool_id": "kb.index.selector_gate", "enabled": True, "review_required": True},
            ],
            routes=[
                {
                    "route_id": "wave_b.kb_selector",
                    "description": "should fail",
                    "env": "dev",
                    "steps": [{"kind": "tool", "tool_id": "kb.index.selector_gate"}],
                }
            ],
        )
        result = validate_routing_policy(policy, registry=self.registry, repo_root=_REPO_ROOT)
        self.assertFalse(result["ok"])
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("routes.step.skeleton_tool", codes)

    def test_route_referencing_composite_tool_fails(self) -> None:
        policy = _minimal_valid_policy(
            tools=[
                {"tool_id": "obs.eval.export", "enabled": True, "review_required": False},
                {"tool_id": "obs.eval.triage", "enabled": True, "review_required": False},
            ],
            routes=[
                {
                    "route_id": "wave_b.triage",
                    "description": "composite in route",
                    "env": "dev",
                    "steps": [{"kind": "tool", "tool_id": "obs.eval.triage"}],
                }
            ],
        )
        result = validate_routing_policy(policy, registry=self.registry, repo_root=_REPO_ROOT)
        self.assertFalse(result["ok"])
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("routes.step.composite_tool", codes)

    def test_disabled_tool_in_tools_but_not_in_route_is_allowed(self) -> None:
        policy = load_routing_policy(repo_root=_REPO_ROOT)
        selector = next(t for t in policy["tools"] if t["tool_id"] == "kb.index.selector_gate")
        self.assertFalse(selector["enabled"])
        result = validate_routing_policy(policy, registry=self.registry, repo_root=_REPO_ROOT)
        self.assertTrue(result["ok"])

    def test_validate_with_fake_registry_cards(self) -> None:
        fake_cards = [
            {
                "tool_id": "obs.eval.export",
                "entry_kind": "python_cli",
                "skeleton": False,
            }
        ]
        policy = {
            "schema_version": "routing_policy_v1",
            "default_env": "dev",
            "tools": [{"tool_id": "obs.eval.export", "enabled": True, "review_required": False}],
            "routes": [
                {
                    "route_id": "wave_b.min",
                    "description": "min",
                    "env": "dev",
                    "steps": [{"kind": "tool", "tool_id": "obs.eval.export"}],
                }
            ],
        }
        result = validate_routing_policy(policy, registry=fake_cards)
        self.assertTrue(result["ok"])
        self.assertEqual(result["total_tools"], 1)
        self.assertEqual(result["total_routes"], 1)

    def test_production_catalog_has_expected_tool_ids(self) -> None:
        cards = load_gov_tool_cards(repo_root=_REPO_ROOT)
        tool_ids = {str(card["tool_id"]) for card in cards}
        self.assertIn("obs.eval.export", tool_ids)
        self.assertIn("kb.index.selector_gate", tool_ids)


if __name__ == "__main__":
    unittest.main()
