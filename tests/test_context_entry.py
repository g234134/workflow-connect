"""Unit tests for H-line context entry contract."""

from __future__ import annotations

import re
import unittest
from unittest.mock import patch

from context import deny_rules
from core.context_entry import build_rooted_context


class TestGateRunner(unittest.TestCase):
    def test_manual_gate_selects_matching_rule_sets(self) -> None:
        marker = "GATERUNNER_PHASE_MARKER_R3B"
        content_only_pre = {
            "id": "gate_runner_content_pre_only",
            "gates": ["pre_injection"],
            "fields": ["task_input"],
            "pattern": re.escape(marker),
            "enabled": True,
        }
        action_only_pre = {
            "id": "gate_runner_action_pre_only",
            "gate": "pre_injection",
            "keys": ["_gate_runner_probe"],
            "enabled": True,
        }
        runner = deny_rules.GateRunner(
            content_rules=[content_only_pre],
            action_rules=[action_only_pre],
        )
        task_input = {"query": "x", "note": marker, "_gate_runner_probe": True}

        pre_hits = runner.run("pre_injection", {"task_input": task_input})
        self.assertIn("gate_runner_content_pre_only", pre_hits)
        self.assertIn("gate_runner_action_pre_only", pre_hits)

        post_hits = runner.run(
            "post_assembly",
            {
                "result": {
                    "root_context": {},
                    "working_context": {"note": marker},
                    "long_term_memory": {},
                    "assembled_text": "",
                },
                "metadata": {},
            },
        )
        self.assertNotIn("gate_runner_action_pre_only", post_hits)
        self.assertNotIn("gate_runner_content_pre_only", post_hits)

    def test_post_assembly_pipeline_appends_rag_hit_with_secrets(self) -> None:
        runner = deny_rules.GateRunner()
        hits = runner.run(
            "post_assembly",
            {
                "result": {
                    "root_context": {},
                    "working_context": {},
                    "long_term_memory": {},
                    "assembled_text": "password=leakedsecretvalue999",
                },
                "metadata": {},
            },
        )
        self.assertIn("env_secret_plaintext", hits)
        self.assertIn("rag_hit_with_secrets", hits)

    def test_registered_gates_includes_subtree_gate_v1(self) -> None:
        gates = deny_rules.registered_gates()
        self.assertIn("pre_injection", gates)
        self.assertIn("post_assembly", gates)
        self.assertIn("subtree", gates)


class TestDenyRulesTable(unittest.TestCase):
    def test_content_rule_table_extensible_and_disable(self) -> None:
        marker = "XYZZY_DENY_MARKER_R3A_TEST"
        dummy = {
            "id": "dummy_test_pattern",
            "phase": "pre_injection",
            "gates": ["pre_injection"],
            "fields": ["task_input"],
            "pattern": re.escape(marker),
            "enabled": True,
        }
        extended = list(deny_rules.CONTENT_RULE_TABLE) + [dummy]
        blob = f"payload {marker} end"
        self.assertIn(
            "dummy_test_pattern",
            deny_rules.scan_content_deny_types(blob, content_rules=extended),
        )
        disabled_table = list(deny_rules.CONTENT_RULE_TABLE) + [{**dummy, "enabled": False}]
        self.assertNotIn(
            "dummy_test_pattern",
            deny_rules.scan_content_deny_types(blob, content_rules=disabled_table),
        )

    def test_builtin_content_and_action_rule_ids(self) -> None:
        self.assertEqual(
            deny_rules.content_rule_ids(),
            [
                "env_secret_plaintext",
                "env_key_literal",
                "instance_absolute_path",
                "checkpoint_binary_blob",
                "full_constitution_mirror",
                "eval_sample_raw",
                "full_cli_trace",
            ],
        )
        self.assertEqual(
            deny_rules.action_rule_ids(),
            [
                "hand_assemble_three_layer_context",
                "hline_bypass_trim",
                "unauthorized_z_env_edit",
                "unauthorized_z_runtime_cp",
            ],
        )


class TestContextEntry(unittest.TestCase):
    def test_minimal_task_input_fills_ids_and_layers(self) -> None:
        out = build_rooted_context({"goal": "smoke"}, mode="k1_pipeline")
        self.assertTrue(out.get("ok"), out.get("message"))
        self.assertTrue(str(out.get("task_input", {}).get("task_id", "")).startswith("task-"))
        self.assertTrue(str(out.get("task_input", {}).get("work_order_id", "")).startswith("wo-"))
        self.assertIn("root_context", out)
        self.assertIn("subtree_context", out)
        self.assertIn("working_context", out)
        self.assertIn("long_term_memory", out)
        usage = out.get("token_usage") or {}
        self.assertIn("total_tokens", usage)
        self.assertEqual(int(usage.get("total_tokens", 0)), int(usage.get("total", 0)))
        self.assertGreater(int(usage.get("total_tokens", 0)), 0)
        meta = out.get("metadata") or {}
        self.assertEqual(meta.get("entry"), "context_entry")
        self.assertEqual(meta.get("source"), "k1_pipeline")

    def test_preserves_explicit_task_ids(self) -> None:
        out = build_rooted_context(
            {
                "task_id": "task-fixed-001",
                "work_order_id": "wo-fixed-001",
                "query": "hello",
            },
            mode="ask_pipeline",
        )
        ti = out.get("task_input") or {}
        self.assertEqual(ti.get("task_id"), "task-fixed-001")
        self.assertEqual(ti.get("work_order_id"), "wo-fixed-001")
        result = out.get("result") or {}
        self.assertEqual(result.get("root_context"), out.get("root_context"))
        self.assertEqual(result.get("working_context"), out.get("working_context"))

    def test_ask_pipeline_mode_contract(self) -> None:
        out = build_rooted_context({"query": "ask smoke"}, mode="ask_pipeline")
        self.assertTrue(out.get("ok"), out.get("message"))
        meta = out.get("metadata") or {}
        self.assertEqual(meta.get("entry"), "context_entry")
        self.assertEqual(meta.get("source"), "ask_pipeline")
        self.assertEqual(meta.get("entry_mode"), "ask_pipeline")
        ti = out.get("task_input") or {}
        self.assertTrue(str(ti.get("task_id", "")).startswith("task-"))
        self.assertTrue(str(ti.get("work_order_id", "")).startswith("wo-"))
        usage = out.get("token_usage") or {}
        self.assertGreater(int(usage.get("total_tokens", 0)), 0)

    def test_invalid_task_input_returns_contract_error(self) -> None:
        out = build_rooted_context("not-a-dict")  # type: ignore[arg-type]
        self.assertFalse(out.get("ok"))
        self.assertIn("dict", str(out.get("message", "")).lower())
        self.assertEqual((out.get("metadata") or {}).get("entry"), "context_entry")
        self.assertEqual(out.get("subtree_context"), [])

    def test_subtree_context_v01_default_mock_aligns_a2(self) -> None:
        out = build_rooted_context({"goal": "subtree smoke"}, mode="ask_pipeline")
        self.assertTrue(out.get("ok"), out.get("message"))
        subtrees = out.get("subtree_context")
        self.assertIsInstance(subtrees, list)
        self.assertGreaterEqual(len(subtrees), 1)
        first = subtrees[0]
        self.assertEqual(first.get("subtree_id"), "line.a.context-entry")
        self.assertEqual(first.get("mount_type"), "line")
        self.assertTrue(str(first.get("scope_label", "")).strip())
        self.assertTrue(first.get("active"))
        entry_refs = first.get("entry_refs")
        self.assertIsInstance(entry_refs, list)
        self.assertEqual(len(entry_refs), 3)
        self.assertIn(
            "workflow_upgrade/01_context-entry/A2_subtree_context_spec.md",
            entry_refs,
        )
        trim = (out.get("metadata") or {}).get("trim") or {}
        contract_trim = next(
            (
                t
                for t in trim.get("trims") or []
                if "context/context_entry_contract.md" in (t.get("trimmed_entries") or [])
            ),
            None,
        )
        self.assertIsNotNone(contract_trim)
        meta = out.get("metadata") or {}
        self.assertEqual(meta.get("subtree_context_version"), "v0.1")
        self.assertGreaterEqual(int(meta.get("subtree_active_count", 0)), 1)
        result = out.get("result") or {}
        self.assertEqual(result.get("subtree_context"), subtrees)

    def test_deny_pre_injection_env_secret_plaintext(self) -> None:
        out = build_rooted_context(
            {
                "query": "leaked",
                "attachments": "api_key=supersecretvalue123456789",
            },
            mode="ask_pipeline",
        )
        self.assertFalse(out.get("ok"))
        self.assertIn("denied", str(out.get("message", "")).lower())
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertTrue(deny.get("denied"))
        self.assertEqual(deny.get("gate"), "pre_injection")
        self.assertIn("env_secret_plaintext", deny.get("deny_types") or [])
        self.assertEqual(out.get("root_context"), {})
        self.assertEqual(out.get("subtree_context"), [])

    def test_deny_pre_injection_hand_assemble_three_layer(self) -> None:
        out = build_rooted_context(
            {
                "query": "bypass attempt",
                "root_context": {"version": "hand-rolled"},
            },
            mode="k1_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertEqual(deny.get("gate"), "pre_injection")
        self.assertIn("hand_assemble_three_layer_context", deny.get("deny_types") or [])

    def test_deny_pre_injection_checkpoint_binary_blob(self) -> None:
        out = build_rooted_context(
            {
                "query": "checkpoint leak",
                "note": "runtime/checkpoints/unauthorized/model.ckpt",
            },
            mode="ask_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertEqual(deny.get("gate"), "pre_injection")
        self.assertIn("checkpoint_binary_blob", deny.get("deny_types") or [])
        obs = deny.get("observability") or {}
        self.assertTrue(obs.get("enabled"))
        self.assertGreaterEqual(int(obs.get("deny_total_count", 0)), 1)
        self.assertEqual((obs.get("phase_hist") or {}).get("pre"), 1)

    def test_deny_pre_injection_full_constitution_mirror(self) -> None:
        out = build_rooted_context(
            {
                "query": "mirror attempt",
                "attachments": "FULL_CONSTITUTION_MIRROR",
            },
            mode="k1_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertIn("full_constitution_mirror", deny.get("deny_types") or [])
        hist = (deny.get("observability") or {}).get("deny_types_hist") or {}
        self.assertGreaterEqual(int(hist.get("full_constitution_mirror", 0)), 1)

    def test_deny_pre_injection_eval_sample_raw(self) -> None:
        out = build_rooted_context(
            {
                "query": "eval leak",
                "eval_sample_raw": {"task_id": "t-1", "verdict": "needs_review"},
            },
            mode="ask_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertIn("eval_sample_raw", deny.get("deny_types") or [])

    def test_happy_path_deny_observability_cleared(self) -> None:
        out = build_rooted_context({"goal": "smoke"}, mode="ask_pipeline")
        self.assertTrue(out.get("ok"), out.get("message"))
        obs = ((out.get("metadata") or {}).get("deny") or {}).get("observability") or {}
        self.assertTrue(obs.get("enabled"))
        self.assertEqual(obs.get("deny_total_count"), 0)
        self.assertEqual(obs.get("deny_types_hist"), {})
        self.assertEqual(obs.get("phase_hist"), {"pre": 0, "post": 0, "subtree": 0})

    @patch("core.context_entry.build_context")
    def test_deny_post_assembly_rag_hit_with_secrets(self, mock_build) -> None:
        mock_build.return_value = {
            "ok": True,
            "message": "context assembled",
            "result": {
                "root_context": {"version": "v0.1"},
                "working_context": {"goal": "safe query"},
                "long_term_memory": {
                    "semantic": {
                        "hits": [
                            {
                                "chunk_id": "c1",
                                "text": "rag hit with password=leakedfromrag99",
                                "score": 0.9,
                            }
                        ],
                    },
                    "structured": {"rows": []},
                },
                "assembled_text": "# assembled\npassword=leakedfromrag99",
            },
            "metadata": {"token_usage": {"root": 1, "working": 1, "memory": 1, "total": 3}},
        }
        out = build_rooted_context({"query": "safe query"}, mode="ask_pipeline")
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertEqual(deny.get("gate"), "post_assembly")
        self.assertIn("env_secret_plaintext", deny.get("deny_types") or [])
        self.assertIn("rag_hit_with_secrets", deny.get("deny_types") or [])

    def test_happy_path_records_deny_cleared_in_metadata(self) -> None:
        out = build_rooted_context({"goal": "smoke"}, mode="ask_pipeline")
        self.assertTrue(out.get("ok"), out.get("message"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertFalse(deny.get("denied"))
        self.assertEqual(deny.get("deny_types"), [])

    def test_subtree_trimming_caps_active_subtrees_by_priority(self) -> None:
        out = build_rooted_context(
            {
                "query": "multi subtree",
                "subtrees": [
                    {
                        "subtree_id": "line.low",
                        "active": True,
                        "subtree_priority": 1,
                        "entry_refs": ["a.md"],
                    },
                    {
                        "subtree_id": "line.high",
                        "active": True,
                        "subtree_priority": 100,
                        "entry_refs": ["b.md"],
                    },
                    {
                        "subtree_id": "line.mid",
                        "active": True,
                        "subtree_priority": 50,
                        "entry_refs": ["c.md"],
                    },
                ],
            },
            mode="ask_pipeline",
        )
        self.assertTrue(out.get("ok"), out.get("message"))
        by_id = {s["subtree_id"]: s for s in out.get("subtree_context") or []}
        self.assertTrue(by_id["line.high"]["active"])
        self.assertTrue(by_id["line.mid"]["active"])
        self.assertFalse(by_id["line.low"]["active"])
        trim = (out.get("metadata") or {}).get("trim") or {}
        self.assertEqual(trim.get("version"), "p0.5-v0.1")
        reasons = {t.get("subtree_id"): t.get("reason") for t in trim.get("trims") or []}
        self.assertEqual(reasons.get("line.low"), "active_subtree_cap")
        self.assertEqual((out.get("metadata") or {}).get("subtree_active_count"), 2)

    def test_subtree_trimming_caps_entry_refs_and_records_trim_metadata(self) -> None:
        refs = [f"workflow_upgrade/ref-{i}.md" for i in range(8)]
        out = build_rooted_context(
            {
                "subtrees": [
                    {
                        "subtree_id": "line.test.refs",
                        "active": True,
                        "entry_refs": refs,
                    }
                ]
            },
            mode="k1_pipeline",
        )
        node = (out.get("subtree_context") or [])[0]
        self.assertEqual(node.get("entry_refs"), refs[:3])
        trim = (out.get("metadata") or {}).get("trim") or {}
        entry_trim = next(
            (t for t in trim.get("trims") or [] if t.get("reason") == "entry_refs_cap"),
            None,
        )
        self.assertIsNotNone(entry_trim)
        self.assertEqual(entry_trim.get("subtree_id"), "line.test.refs")
        self.assertEqual(entry_trim.get("trimmed_entries"), refs[3:])

    def test_deny_response_has_no_subtree_trim_metadata(self) -> None:
        out = build_rooted_context(
            {
                "query": "leaked",
                "attachments": "api_key=supersecretvalue123456789",
            },
            mode="ask_pipeline",
        )
        self.assertFalse(out.get("ok"))
        meta = out.get("metadata") or {}
        self.assertTrue((meta.get("deny") or {}).get("denied"))
        self.assertNotIn("trim", meta)

    def test_happy_path_includes_trim_metadata(self) -> None:
        out = build_rooted_context({"goal": "smoke"}, mode="ask_pipeline")
        self.assertTrue(out.get("ok"), out.get("message"))
        trim = (out.get("metadata") or {}).get("trim") or {}
        self.assertEqual(trim.get("version"), "p0.5-v0.1")
        self.assertIn("trims", trim)
        self.assertIn("token_estimate", trim)
        default_refs = (out.get("subtree_context") or [])[0].get("entry_refs") or []
        self.assertLessEqual(len(default_refs), 3)

    def test_subtree_context_task_input_override(self) -> None:
        out = build_rooted_context(
            {
                "query": "dept scope",
                "subtree_id": "dept.data-agent",
                "subtree_mount_type": "dept",
                "subtree_scope_label": "暗部 Data agent 專線",
                "subtree_entry_refs": [
                    "context/context_model.md",
                    "context/memory_routing_rules.md",
                ],
            },
            mode="k1_pipeline",
        )
        subtrees = out.get("subtree_context") or []
        self.assertEqual(len(subtrees), 1)
        node = subtrees[0]
        self.assertEqual(node.get("subtree_id"), "dept.data-agent")
        self.assertEqual(node.get("mount_type"), "dept")
        self.assertEqual(node.get("scope_label"), "暗部 Data agent 專線")
        self.assertEqual(
            node.get("entry_refs"),
            [
                "context/context_model.md",
                "context/memory_routing_rules.md",
            ],
        )

    def test_nav_auto_v01_generates_navigation_map_without_task_input_nav(self) -> None:
        out = build_rooted_context({"goal": "nav auto smoke"}, mode="ask_pipeline")
        self.assertTrue(out.get("ok"), out.get("message"))
        meta = out.get("metadata") or {}
        result = out.get("result") or {}
        nav = meta.get("navigation_map")
        self.assertIsInstance(nav, dict)
        self.assertEqual(result.get("navigation_map"), nav)
        self.assertEqual(nav.get("version"), "nav-auto-v0.1")
        self.assertEqual(meta.get("navigation_map_version"), "v0.1")
        active_path = nav.get("active_path")
        self.assertIsInstance(active_path, list)
        self.assertGreaterEqual(len(active_path), 2)
        self.assertEqual(active_path[0], "root")
        self.assertIn("line.a.context-entry", active_path)
        nodes = nav.get("nodes") or {}
        self.assertIn("root", nodes)
        self.assertIn("line.a.context-entry", nodes)
        root_refs = nodes["root"].get("entry_refs") or []
        self.assertIn("AGENTS.md", root_refs)
        subtree_refs = nodes["line.a.context-entry"].get("entry_refs") or []
        trimmed_refs = (out.get("subtree_context") or [{}])[0].get("entry_refs") or []
        self.assertGreaterEqual(len(subtree_refs), len(trimmed_refs))
        self.assertIn("context/context_entry_contract.md", subtree_refs)
        self.assertIn(
            "workflow_upgrade/01_context-entry/A2_subtree_context_spec.md",
            subtree_refs,
        )
        link = nav.get("subtree_to_node") or {}
        self.assertEqual(link.get("line.a.context-entry"), "line.a.context-entry")

    def test_nav_auto_v01_subtree_override_links_custom_subtree(self) -> None:
        out = build_rooted_context(
            {
                "query": "dept nav",
                "subtree_id": "dept.data-agent",
                "subtree_mount_type": "dept",
                "subtree_entry_refs": ["context/context_model.md"],
            },
            mode="ask_pipeline",
        )
        nav = (out.get("metadata") or {}).get("navigation_map") or {}
        active_path = nav.get("active_path") or []
        self.assertIn("dept.data-agent", active_path)
        nodes = nav.get("nodes") or {}
        self.assertIn("dept.data-agent", nodes)
        self.assertEqual(nodes["dept.data-agent"].get("subtree_id"), "dept.data-agent")
        self.assertEqual(
            (nav.get("subtree_to_node") or {}).get("dept.data-agent"),
            "dept.data-agent",
        )

    def test_nav_auto_v01_user_partial_nav_fill_missing_only(self) -> None:
        user_refs = ["context/context_entry_contract.md"]
        out = build_rooted_context(
            {
                "goal": "partial nav",
                "navigation_map": {
                    "active_path": ["root"],
                    "nodes": {
                        "root": {
                            "entry_refs": user_refs,
                        }
                    },
                },
            },
            mode="ask_pipeline",
        )
        nav = (out.get("metadata") or {}).get("navigation_map") or {}
        self.assertEqual(nav.get("active_path"), ["root"])
        root_node = (nav.get("nodes") or {}).get("root") or {}
        self.assertEqual(root_node.get("entry_refs"), user_refs)
        self.assertEqual(root_node.get("type"), "root")
        self.assertTrue(str(root_node.get("scope_label") or "").strip())
        self.assertEqual(nav.get("nav_map_ref"), "workflow_upgrade/01_context-entry/40_navigation_map_template.md")

    @patch("core.context_entry._deny_gate_post_assembly", return_value=None)
    @patch("core.context_entry._deny_gate_pre_injection", return_value=None)
    def test_deny_subtree_gate_hits_forbidden_pattern_in_runbook_digest(
        self, _mock_pre, _mock_post
    ) -> None:
        out = build_rooted_context(
            {
                "query": "subtree deny smoke",
                "subtrees": [
                    {
                        "subtree_id": "line.test.deny",
                        "active": True,
                        "entry_refs": ["workflow_upgrade/ref-a.md"],
                        "runbook_digest": [
                            "runtime/checkpoints/unauthorized/model.ckpt",
                        ],
                    }
                ],
            },
            mode="ask_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertTrue(deny.get("denied"))
        self.assertEqual(deny.get("gate"), "subtree")
        self.assertEqual(deny.get("phase"), "P0.5")
        self.assertIn("checkpoint_binary_blob", deny.get("deny_types") or [])
        subtree_meta = deny.get("subtree") or {}
        self.assertIn("line.test.deny", subtree_meta.get("active_subtree_ids") or [])
        union = subtree_meta.get("deny_union") or {}
        self.assertIn("line.test.deny", union.get("active_subtree_ids") or [])

    @patch("core.context_entry._deny_gate_post_assembly", return_value=None)
    @patch("core.context_entry._deny_gate_pre_injection", return_value=None)
    def test_deny_subtree_gate_records_scope_constraints_union(
        self, _mock_pre, _mock_post
    ) -> None:
        out = build_rooted_context(
            {
                "query": "scope union",
                "subtrees": [
                    {
                        "subtree_id": "line.test.scope",
                        "active": True,
                        "entry_refs": ["workflow_upgrade/ref-b.md"],
                        "scope_constraints": {
                            "append_forbidden_content_types": ["full_cli_trace"],
                            "must_not_touch": ["core/"],
                        },
                        "runbook_digest": ['FULL_CLI_TRACE payload {"events": []}'],
                    }
                ],
            },
            mode="k1_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertEqual(deny.get("gate"), "subtree")
        self.assertIn("full_cli_trace", deny.get("deny_types") or [])
        union = (deny.get("subtree") or {}).get("deny_union") or {}
        self.assertIn("full_cli_trace", union.get("forbidden_content_types") or [])

    def test_deny_pre_injection_full_cli_trace(self) -> None:
        out = build_rooted_context(
            {
                "query": "trace leak",
                "attachments": 'FULL_CLI_TRACE {"trace_id": "t-1", "events": []}',
            },
            mode="ask_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertEqual(deny.get("gate"), "pre_injection")
        self.assertIn("full_cli_trace", deny.get("deny_types") or [])

    def test_deny_pre_injection_unauthorized_z_env_edit(self) -> None:
        out = build_rooted_context(
            {
                "query": "env edit attempt",
                "_z_env_edit": True,
            },
            mode="ask_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertIn("unauthorized_z_env_edit", deny.get("deny_types") or [])
        audit = deny.get("action_audit") or []
        self.assertTrue(any(a.get("z_type") == "Z-HQ-ENV-EDIT" for a in audit))
        self.assertTrue(any(a.get("skeleton") is True for a in audit))

    def test_deny_pre_injection_unauthorized_z_runtime_cp(self) -> None:
        out = build_rooted_context(
            {
                "query": "checkpoint write attempt",
                "z_runtime_checkpoint_write": {"path": "runtime/checkpoints/x"},
            },
            mode="k1_pipeline",
        )
        self.assertFalse(out.get("ok"))
        deny = (out.get("metadata") or {}).get("deny") or {}
        self.assertIn("unauthorized_z_runtime_cp", deny.get("deny_types") or [])
        audit = deny.get("action_audit") or []
        self.assertTrue(any(a.get("z_type") == "Z-RUNTIME-CP" for a in audit))

    def test_summarize_deny_policy_coverage(self) -> None:
        summary = deny_rules.summarize_deny_policy()
        self.assertTrue(summary.get("ok"))
        self.assertEqual(summary.get("rule_table_version"), deny_rules.RULE_TABLE_VERSION)
        content = summary.get("content") or {}
        action = summary.get("action") or {}
        self.assertEqual(content.get("coverage"), "7/7")
        self.assertEqual(action.get("coverage"), "3/8")
        self.assertIn("unauthorized_z_runtime_cp", action.get("implemented_ids") or [])
        self.assertIn("full_cli_trace", content.get("implemented_ids") or [])
        self.assertIn("unauthorized_z_env_edit", action.get("z_action_skeletons") or [])
        self.assertIn("subtree", summary.get("registered_gates") or [])


if __name__ == "__main__":
    unittest.main()
