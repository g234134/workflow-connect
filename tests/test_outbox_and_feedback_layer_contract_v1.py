"""Contract tests for outbox-and-feedback-layer-contract-v1 (WB-T3).

Doc + schema index only; scans fixture outbox samples; no writer/consumer changes.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "outbox-and-feedback-layer-contract-v1.md"
_SCHEMA = _REPO_ROOT / "docs" / "schemas" / "outbox_layer_v1.json"
_TABULAR_OUTBOX_SPEC = _REPO_ROOT / "docs" / "tabular-tool-outbox-spec.md"
_TABULAR_CONSUMER_SPEC = _REPO_ROOT / "docs" / "tabular-outbox-consumer-spec.md"
_FIXTURES_ROOT = _REPO_ROOT / "tests" / "fixtures" / "outbox"
_CASES_INDEX = _REPO_ROOT / "cases" / "index.json"

_REQUIRED_SECTIONS = (
    "## §1 Purpose and scope",
    "## §2 Outbox namespace table",
    "## §3 Tabular list consumer output",
    "## §4 Feedback sub-object semantics",
    "## §5 `join_with_case_history` contract",
    "## §6 Legacy and degradation rules",
    "## §7 Observability conventions",
    "## §8 Implementation appendices",
    "## §9 Verification",
)

_NAMESPACE_PATHS = (
    "outbox/<case_ref>/",
    "outbox/agent_experiment_regression/",
    "outbox/agent_ci/",
    "outbox/non_tabular_experiment/",
    "outbox/sandbox_delivery/",
    "outbox/agent_metrics/",
)

_SCHEMA_IDS = (
    "tabular_outbox_v1",
    "agent_experiment_regression_v1",
    "agent_lines_ci_suite_v1",
    "non_tabular_experiment_preview_v1",
    "sandbox_delivery_bundle_v1",
    "agent_lines_metrics_v1",
)

_FEEDBACK_KINDS = (
    "hitl_checkpoint_a",
    "hitl_checkpoint_b",
    "delivery_approval",
    "controlled_notify_simulated",
    "downstream_ack",
)

_JOIN_CASE_FIELDS = (
    "case_dir",
    "client_ref",
    "case_id",
    "product_sku",
    "gate_status",
    "schema_headers",
    "known_limits",
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing required file: {path.relative_to(_REPO_ROOT)}")
    return path.read_text(encoding="utf-8")


class TestOutboxAndFeedbackLayerContractV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = _read(_CONTRACT)
        cls.schema = json.loads(_read(_SCHEMA))
        cls.tabular_spec = _read(_TABULAR_OUTBOX_SPEC)
        cls.consumer_spec = _read(_TABULAR_CONSUMER_SPEC)

    def test_contract_and_schema_files_exist(self) -> None:
        self.assertTrue(_CONTRACT.is_file())
        self.assertTrue(_SCHEMA.is_file())

    def test_required_section_headings_present(self) -> None:
        missing = [h for h in _REQUIRED_SECTIONS if h not in self.contract]
        self.assertEqual(missing, [], f"missing sections: {missing}")

    def test_namespace_table_lists_all_six_paths(self) -> None:
        section2 = self._section("## §2", "## §3")
        for path in _NAMESPACE_PATHS:
            with self.subTest(path=path):
                self.assertIn(path, section2)

    def test_each_namespace_has_schema_producer_consumer_retention(self) -> None:
        section2 = self._section("## §2", "## §3")
        for ns in self.schema["namespaces"]:
            with self.subTest(namespace_id=ns["namespace_id"]):
                self.assertIn(ns["path_pattern"], section2)
                self.assertIn(ns["schema_id"], section2)
                self.assertIn("Producer", section2)
                self.assertIn("Consumer", section2)
                self.assertIn("Retention", section2)

    def test_schema_index_namespace_count_and_schema_ids(self) -> None:
        namespaces = self.schema["namespaces"]
        self.assertEqual(len(namespaces), 6)
        index_ids = {n["schema_id"] for n in namespaces}
        for schema_id in _SCHEMA_IDS:
            self.assertIn(schema_id, index_ids)

    def test_feedback_semantics_defined(self) -> None:
        section4 = self._section("## §4", "## §5")
        for kind in _FEEDBACK_KINDS:
            with self.subTest(kind=kind):
                self.assertIn(kind, section4)
        self.assertIn("checkpoint json", section4.lower())
        self.assertIn("authority", section4.lower())

    def test_feedback_schemas_in_machine_index(self) -> None:
        kinds = {f["feedback_kind"] for f in self.schema["feedback_schemas"]}
        self.assertEqual(set(_FEEDBACK_KINDS), kinds)

    def test_downstream_ack_storage_documented(self) -> None:
        section4 = self._section("## §4", "## §5")
        self.assertIn("downstream_ack", section4)
        self.assertIn("outbox/feedback/", section4)
        self.assertIn("pending_ack", section4)
        ack_schema = next(
            f for f in self.schema["feedback_schemas"] if f["feedback_kind"] == "downstream_ack"
        )
        self.assertEqual(ack_schema["schema_id"], "downstream_ack_v1")

    def test_join_with_case_history_aligns_index_fields(self) -> None:
        section5 = self._section("## §5", "## §6")
        join_block = self.schema["join_with_case_history"]
        for field in _JOIN_CASE_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, section5)
                self.assertIn(field, join_block["case_fields"])
        self.assertIn("cases/index.json", section5)
        self.assertEqual(join_block["index_ssot"], "cases/index.json")

    def test_legacy_degradation_unknown_and_case_ref_lookup(self) -> None:
        section6 = self._section("## §6", "## §7")
        self.assertIn("unknown", section6)
        self.assertIn("case_ref", section6)
        deg = self.schema["legacy_degradation"]
        self.assertEqual(deg["missing_schema_version_schema_id"], "unknown")
        self.assertIn("case_ref", deg["lookup_keys"])

    def test_wa_t4_state_write_freeze_referenced(self) -> None:
        self.assertIn("phase4-multi-agent-collaboration-contract-v1.md", self.contract)
        self.assertIn("FRAME", self.contract)
        self.assertIn("STATE", self.contract)
        self.assertIn("Scribe", self.contract)

    def test_orchestration_bridge_merge_forbidden(self) -> None:
        self.assertIn("orchestration_bridge_outbox", self.contract)
        self.assertIn("Permanent separate track", self.contract)
        forbidden = self.schema["forbidden_merge_paths"]
        self.assertIn("orchestration_bridge_outbox", forbidden)
        self.assertTrue(self.schema["track_separation"]["merge_forbidden"])

    def test_tabular_specs_downgraded_to_appendix_pointers(self) -> None:
        for spec_path, spec_text in (
            (_TABULAR_OUTBOX_SPEC, self.tabular_spec),
            (_TABULAR_CONSUMER_SPEC, self.consumer_spec),
        ):
            with self.subTest(spec=spec_path.name):
                self.assertIn("outbox-and-feedback-layer-contract-v1.md", spec_text)
                self.assertIn("implementation appendix", spec_text.lower())

    def test_fixture_outbox_samples_validate_schema_id(self) -> None:
        samples = list(_FIXTURES_ROOT.rglob("*.json"))
        self.assertGreater(len(samples), 0, "expected fixture outbox JSON samples")
        for path in samples:
            with self.subTest(path=path.relative_to(_REPO_ROOT)):
                payload = json.loads(path.read_text(encoding="utf-8"))
                schema_version = payload.get("schema_version")
                if schema_version is None:
                    self.assertIn("unknown", self.contract)
                else:
                    self.assertEqual(schema_version, "tabular_outbox_v1")

    def test_inspect_tabular_outbox_minimum_example_matches_section3(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.inspect_tabular_outbox",
                "--case-ref",
                "demo_phase",
                "--json",
                "--outbox-root",
                "tests/fixtures/outbox",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload.get("ok"))
        self.assertEqual(payload.get("case_ref"), "demo_phase")
        self.assertIsNone(payload.get("tool_id"))
        self.assertIsInstance(payload.get("count"), int)
        runs = payload.get("runs")
        self.assertIsInstance(runs, list)
        self.assertEqual(payload["count"], len(runs))
        if runs:
            row = runs[0]
            for key in (
                "case_ref",
                "run_id",
                "tool_id",
                "started_at",
                "finished_at",
                "ok",
                "exit_code",
                "message",
                "outbox_path",
            ):
                self.assertIn(key, row)

    def test_join_with_case_history_live_against_fixtures(self) -> None:
        if str(_REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(_REPO_ROOT))
        from tools.tabular_outbox_consumer import join_with_case_history

        result = join_with_case_history(
            "demo_phase",
            outbox_root_override=str(_FIXTURES_ROOT),
        )
        self.assertTrue(result.get("ok"))
        case = result.get("case") or {}
        for field in _JOIN_CASE_FIELDS:
            if case:
                self.assertIn(field, case)
        self.assertGreaterEqual(result.get("run_count", 0), 1)

    def test_cases_index_has_demo_phase_for_join(self) -> None:
        index = json.loads(_CASES_INDEX.read_text(encoding="utf-8"))
        case_dirs = {c.get("case_dir") for c in index.get("cases", [])}
        self.assertIn("cases/demo_phase", case_dirs)

    def _section(self, start: str, end: str) -> str:
        pattern = re.escape(start) + r"(.*?)" + re.escape(end)
        match = re.search(pattern, self.contract, re.DOTALL)
        self.assertIsNotNone(match, f"section between {start} and {end}")
        return match.group(1)


if __name__ == "__main__":
    unittest.main()
