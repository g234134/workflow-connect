"""Unit tests for scripts/generate_toolchain_governance_snapshot.py (WC-IMPL-L1)."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SNAPSHOT_CLI = _REPO_ROOT / "scripts" / "generate_toolchain_governance_snapshot.py"


def _load_snapshot_module():
    spec = importlib.util.spec_from_file_location(
        "generate_toolchain_governance_snapshot", _SNAPSHOT_CLI
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["generate_toolchain_governance_snapshot_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def _base_payload(**overrides) -> dict:
    payload = {
        "ci_context": "none",
        "smoke_matrix": {"loaded_ok": True, "load_message": "ok"},
        "coverage": {"smoke_entries_total": 14},
        "toolchain_health_embed": {
            "ok": True,
            "sections_populated": 5,
            "degraded_sections": [],
        },
        "components": [
            {"smoke_id": "TS-ROUTING-EVAL-UNIT", "tier": "optional_ci", "last_result": "not_observed"},
            {"smoke_id": "TS-ROUTING-EVAL-DRYRUN", "tier": "optional_ci", "last_result": "not_observed"},
        ],
        "output_paths": {"json": "output/toolchain/governance_snapshot.json"},
    }
    payload.update(overrides)
    return payload


def _codes(result: dict) -> set[str]:
    return {item["code"] for item in result.get("advisory_findings", [])}


class TestToolchainGovernanceSnapshotV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _SNAPSHOT_CLI.is_file():
            raise unittest.SkipTest(f"missing script: {_SNAPSHOT_CLI}")
        cls.mod = _load_snapshot_module()

    def test_build_snapshot_schema(self) -> None:
        payload = self.mod.build_toolchain_governance_snapshot(repo_root=_REPO_ROOT)
        self.assertEqual(payload["schema_version"], "toolchain_governance_snapshot_v1")
        self.assertTrue(payload["non_blocking"])
        self.assertEqual(payload["gate_class"], "optional")
        self.assertFalse(payload["blocks_mainline"])
        self.assertIn("coverage", payload)
        self.assertIn("components", payload)
        self.assertIn("toolchain_health_embed", payload)
        self.assertIn("advisory_level", payload)
        self.assertIn("advisory_findings", payload)
        self.assertIn("advisory_summary", payload)
        self.assertGreater(payload["coverage"]["smoke_entries_total"], 0)

    def test_ci_context_marks_observed_smokes_passed(self) -> None:
        payload = self.mod.build_toolchain_governance_snapshot(
            repo_root=_REPO_ROOT,
            ci_context="eval-gate-pr",
        )
        by_id = {row["smoke_id"]: row for row in payload["components"]}
        self.assertEqual(by_id["TS-ROUTING-EVAL-DRYRUN"]["last_result"], "passed")
        self.assertEqual(by_id["TS-ROUTING-EVAL-UNIT"]["last_result"], "passed")
        self.assertEqual(by_id["TS-MVP-MAINLINE"]["last_result"], "not_observed")
        self.assertNotIn("MS-CI-SMOKE-MISSING", _codes(payload))

    def test_external_core_agent_smoke_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "smoke_ci_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "ok": False,
                        "smoke_result": {
                            "ok": False,
                            "message": "1 failed",
                            "failed_tests": [
                                {"test_id": "tests.test_foo.TestBar.test_x", "message": "assert False"}
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            payload = self.mod.build_toolchain_governance_snapshot(
                repo_root=_REPO_ROOT,
                ci_context="core-agent-smoke-pr",
                smoke_results_json=summary_path,
            )
            by_id = {row["smoke_id"]: row for row in payload["components"]}
            row = by_id["TS-CORE-AGENT-SMOKE-PR"]
            self.assertEqual(row["last_result"], "failed")
            self.assertIn("assert False", row["error_summary"])
            self.assertTrue(payload["recent_errors"])
            self.assertIn("MS-CI-SMOKE-FAILED", _codes(payload))

    def test_write_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "routing").mkdir(parents=True)
            matrix_src = _REPO_ROOT / "routing" / "toolchain_smoke_matrix_v1.yaml"
            if matrix_src.is_file():
                (root / "routing" / "toolchain_smoke_matrix_v1.yaml").write_text(
                    matrix_src.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            payload = self.mod.build_toolchain_governance_snapshot(repo_root=root)
            out_dir = root / "output" / "toolchain"
            paths = self.mod.write_toolchain_governance_snapshot_artifacts(
                payload,
                repo_root=root,
                output_dir=out_dir,
            )
            self.assertTrue((root / paths["json"]).is_file())
            self.assertTrue((root / paths["markdown"]).is_file())
            self.assertTrue((root / paths["advisory_log"]).is_file())
            written = json.loads((root / paths["json"]).read_text(encoding="utf-8"))
            self.assertEqual(written["schema_version"], "toolchain_governance_snapshot_v1")
            self.assertIn("advisory_level", written)
            md_text = (root / paths["markdown"]).read_text(encoding="utf-8")
            self.assertIn("## Advisory (L1 · non-blocking)", md_text)
            log_text = (root / paths["advisory_log"]).read_text(encoding="utf-8")
            self.assertIn("=== L1 governance advisory", log_text)
            self.assertIn("advisory_level=", log_text)

    def test_main_non_blocking_exit_zero_on_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "routing").mkdir(parents=True)
            code = self.mod.main(
                [
                    "--repo-root",
                    str(root),
                    "--non-blocking",
                    "--format",
                    "json",
                    "--no-write",
                ]
            )
            self.assertEqual(code, 0)

    def test_advisory_level_aggregation(self) -> None:
        warn_only = self.mod.evaluate_governance_advisory(
            _base_payload(
                toolchain_health_embed={
                    "ok": True,
                    "sections_populated": 5,
                    "degraded_sections": ["agent_ci"],
                }
            )
        )
        self.assertEqual(warn_only["advisory_level"], "warn")

        critical = self.mod.evaluate_governance_advisory(
            _base_payload(smoke_matrix={"loaded_ok": False, "load_message": "missing"})
        )
        self.assertEqual(critical["advisory_level"], "critical")

        clean = self.mod.evaluate_governance_advisory(
            _base_payload(
                ci_context="eval-gate-pr",
                components=[
                    {"smoke_id": "TS-ROUTING-EVAL-UNIT", "tier": "optional_ci", "last_result": "passed"},
                    {"smoke_id": "TS-ROUTING-EVAL-DRYRUN", "tier": "optional_ci", "last_result": "passed"},
                ],
            )
        )
        self.assertEqual(clean["advisory_level"], "none")

    def test_ms_matrix_load_trigger_and_no_trigger(self) -> None:
        triggered = self.mod.evaluate_governance_advisory(
            _base_payload(smoke_matrix={"loaded_ok": False, "load_message": "bad yaml"})
        )
        self.assertIn("MS-MATRIX-LOAD", _codes(triggered))
        finding = next(f for f in triggered["advisory_findings"] if f["code"] == "MS-MATRIX-LOAD")
        self.assertEqual(finding["severity"], "critical")
        self.assertIn("remedial_action", finding)

        not_triggered = self.mod.evaluate_governance_advisory(_base_payload())
        self.assertNotIn("MS-MATRIX-LOAD", _codes(not_triggered))

    def test_ms_matrix_empty_trigger_and_no_trigger(self) -> None:
        triggered = self.mod.evaluate_governance_advisory(
            _base_payload(coverage={"smoke_entries_total": 0})
        )
        self.assertIn("MS-MATRIX-EMPTY", _codes(triggered))

        not_triggered = self.mod.evaluate_governance_advisory(_base_payload())
        self.assertNotIn("MS-MATRIX-EMPTY", _codes(not_triggered))

    def test_ms_health_assembly_trigger_and_no_trigger(self) -> None:
        triggered = self.mod.evaluate_governance_advisory(
            _base_payload(
                toolchain_health_embed={
                    "ok": False,
                    "sections_populated": 5,
                    "degraded_sections": [],
                    "message": "assembly failed",
                }
            )
        )
        self.assertIn("MS-HEALTH-ASSEMBLY", _codes(triggered))

        not_triggered = self.mod.evaluate_governance_advisory(_base_payload())
        self.assertNotIn("MS-HEALTH-ASSEMBLY", _codes(not_triggered))

    def test_ms_health_sections_trigger_and_no_trigger(self) -> None:
        triggered = self.mod.evaluate_governance_advisory(
            _base_payload(
                toolchain_health_embed={
                    "ok": True,
                    "sections_populated": 2,
                    "degraded_sections": [],
                }
            )
        )
        self.assertIn("MS-HEALTH-SECTIONS", _codes(triggered))

        not_triggered = self.mod.evaluate_governance_advisory(_base_payload())
        self.assertNotIn("MS-HEALTH-SECTIONS", _codes(not_triggered))

    def test_ms_ci_smoke_missing_trigger_and_no_trigger(self) -> None:
        triggered = self.mod.evaluate_governance_advisory(
            _base_payload(ci_context="core-agent-smoke-pr"),
            external_smoke_ids=set(),
        )
        self.assertIn("MS-CI-SMOKE-MISSING", _codes(triggered))

        not_triggered = self.mod.evaluate_governance_advisory(
            _base_payload(ci_context="core-agent-smoke-pr"),
            external_smoke_ids={"TS-CORE-AGENT-SMOKE-PR"},
        )
        self.assertNotIn("MS-CI-SMOKE-MISSING", _codes(not_triggered))

    def test_ms_ci_smoke_failed_trigger_and_no_trigger(self) -> None:
        triggered = self.mod.evaluate_governance_advisory(
            _base_payload(
                ci_context="eval-gate-pr",
                components=[
                    {"smoke_id": "TS-ROUTING-EVAL-UNIT", "tier": "optional_ci", "last_result": "failed"},
                    {"smoke_id": "TS-ROUTING-EVAL-DRYRUN", "tier": "optional_ci", "last_result": "passed"},
                ],
            )
        )
        self.assertIn("MS-CI-SMOKE-FAILED", _codes(triggered))

        not_triggered = self.mod.evaluate_governance_advisory(
            _base_payload(
                ci_context="eval-gate-pr",
                components=[
                    {"smoke_id": "TS-ROUTING-EVAL-UNIT", "tier": "optional_ci", "last_result": "passed"},
                    {"smoke_id": "TS-ROUTING-EVAL-DRYRUN", "tier": "optional_ci", "last_result": "passed"},
                ],
            )
        )
        self.assertNotIn("MS-CI-SMOKE-FAILED", _codes(not_triggered))

    def test_ms_optional_ci_gap_trigger_and_no_trigger(self) -> None:
        triggered = self.mod.evaluate_governance_advisory(_base_payload(ci_context="none"))
        self.assertIn("MS-OPTIONAL-CI-GAP", _codes(triggered))
        finding = next(f for f in triggered["advisory_findings"] if f["code"] == "MS-OPTIONAL-CI-GAP")
        self.assertEqual(finding["severity"], "warn")

        not_triggered = self.mod.evaluate_governance_advisory(
            _base_payload(
                ci_context="eval-gate-pr",
                components=[
                    {"smoke_id": "TS-ROUTING-EVAL-UNIT", "tier": "optional_ci", "last_result": "passed"},
                    {"smoke_id": "TS-ROUTING-EVAL-DRYRUN", "tier": "optional_ci", "last_result": "passed"},
                ],
            )
        )
        self.assertNotIn("MS-OPTIONAL-CI-GAP", _codes(not_triggered))

    def test_ms_health_degraded_trigger_and_no_trigger(self) -> None:
        triggered = self.mod.evaluate_governance_advisory(
            _base_payload(
                toolchain_health_embed={
                    "ok": True,
                    "sections_populated": 5,
                    "degraded_sections": ["metrics_summary"],
                }
            )
        )
        self.assertIn("MS-HEALTH-DEGRADED", _codes(triggered))

        not_triggered = self.mod.evaluate_governance_advisory(_base_payload())
        self.assertNotIn("MS-HEALTH-DEGRADED", _codes(not_triggered))

    def test_ms_snapshot_artifact_trigger_and_no_trigger(self) -> None:
        triggered = self.mod.evaluate_governance_advisory(
            _base_payload(output_paths={}),
            write_attempted=True,
        )
        self.assertIn("MS-SNAPSHOT-ARTIFACT", _codes(triggered))

        not_triggered = self.mod.evaluate_governance_advisory(
            _base_payload(),
            write_attempted=True,
        )
        self.assertNotIn("MS-SNAPSHOT-ARTIFACT", _codes(not_triggered))

    def test_print_ci_summary_emits_github_warning_for_critical(self) -> None:
        payload = _base_payload(
            smoke_matrix={"loaded_ok": False, "load_message": "missing"},
            coverage={"smoke_entries_total": 0},
        )
        self.mod.attach_governance_advisory(payload)
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.mod.print_ci_log_summary(payload)
        output = buf.getvalue()
        self.assertIn("=== L1 governance advisory", output)
        self.assertIn("::warning title=MS-MATRIX-LOAD::", output)

    def test_main_non_blocking_exit_zero_with_critical_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "routing").mkdir(parents=True)
            code = self.mod.main(
                [
                    "--repo-root",
                    str(root),
                    "--ci-context",
                    "core-agent-smoke-pr",
                    "--non-blocking",
                    "--print-ci-summary",
                    "--no-write",
                ]
            )
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
