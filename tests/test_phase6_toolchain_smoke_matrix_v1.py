"""Schema and drift checks for routing/toolchain_smoke_matrix_v1.yaml (WB-T7).

Validates YAML structure, WA-T3 gate_class alignment, and command target existence.
Does NOT execute smoke commands via subprocess (AC-4).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MATRIX_PATH = _REPO_ROOT / "routing" / "toolchain_smoke_matrix_v1.yaml"
_P35_CONTRACT = _REPO_ROOT / "docs" / "phase3-5-cost-model-governance-contract-v1.md"
_DASHBOARD_DOC = _REPO_ROOT / "docs" / "toolchain-health-dashboard-v1.md"

_REQUIRED_TOP = frozenset(
    {
        "schema_version",
        "matrix_revision",
        "description",
        "entries",
    }
)
_REQUIRED_ENTRY_FIELDS = frozenset(
    {
        "smoke_id",
        "command",
        "tier",
        "gate_class",
        "blocks_mainline",
    }
)
_GATE_CLASSES = frozenset({"mandatory", "optional", "shadow"})
_TIERS = frozenset({"local_mandatory", "local_recommended", "optional_ci", "release_only"})

# Local-mandatory INT Tier-A — only entry allowed gate_class=mandatory (not PR CI).
_INT_TIER_A_SMOKE_ID = "TS-INT-TIER-A"

# WB-T4 dashboard / Phase 6 appendix A commands — YAML must contain each (AC-7).
_WB_T4_DASHBOARD_COMMANDS = (
    "python scripts/run_toolchain_health_dashboard.py --format json --dry-run --no-write",
    "python -m unittest tests.test_toolchain_health_dashboard_v1 -v",
    "python scripts/run_agent_lines_ci_suite.py --scope all --format json --no-ci-summary",
    "python scripts/analyze_agent_lines_metrics.py --format json --no-write",
    "python scripts/generate_agent_lines_monthly_report.py --no-write --format json",
    "python -m observability.wf_status_summary --help",
)

# AC-1 minimum coverage smoke_ids
_AC1_REQUIRED_SMOKE_IDS = frozenset(
    {
        "TS-W3TL-UNIT",
        "TS-ROUTING-EVAL-DRYRUN",
        "TS-AGENT-LINES-CI",
        "TS-AGENT-LINES-METRICS",
        "TS-AGENT-LINES-AUDIT",
        "TS-TOOLCHAIN-DASHBOARD-DRYRUN",
        "TS-MVP-MAINLINE",
        "TS-INT-TIER-A",
    }
)


def _load_matrix() -> dict:
    text = _MATRIX_PATH.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ImportError:
        raise unittest.SkipTest("pyyaml not installed; skip YAML parse test")
    if not isinstance(data, dict):
        raise AssertionError("matrix root must be a mapping")
    return data


def _command_targets_exist(command: str) -> tuple[bool, str]:
    """Resolve primary script/module path from a smoke command string."""
    command = command.strip()
    script_match = re.search(r"python\s+scripts/([\w./_-]+\.py)", command)
    if script_match:
        path = _REPO_ROOT / "scripts" / Path(script_match.group(1)).name
        if script_match.group(1) != Path(script_match.group(1)).name:
            path = _REPO_ROOT / script_match.group(1)
        if path.is_file():
            return True, str(path.relative_to(_REPO_ROOT))
        return False, f"missing script: {path.relative_to(_REPO_ROOT)}"

    workflow_match = re.search(r"python\s+04_Workflows/([\w./_-]+\.py)", command)
    if workflow_match:
        path = _REPO_ROOT / "04_Workflows" / Path(workflow_match.group(1)).name
        if workflow_match.group(1) != Path(workflow_match.group(1)).name:
            path = _REPO_ROOT / workflow_match.group(1)
        if path.is_file():
            return True, str(path.relative_to(_REPO_ROOT))
        return False, f"missing workflow script: {path.relative_to(_REPO_ROOT)}"

    module_match = re.search(r"python\s+-m\s+([\w.]+)", command)
    if module_match:
        module = module_match.group(1)
        if module.startswith("unittest"):
            test_modules = re.findall(r"tests\.test_[\w]+", command)
            if not test_modules:
                return False, "unittest command missing tests.test_* modules"
            for mod in test_modules:
                rel = mod.replace(".", "/") + ".py"
                path = _REPO_ROOT / rel
                if not path.is_file():
                    return False, f"missing test module file: {rel}"
            return True, test_modules[0]

        parts = module.split(".")
        path = _REPO_ROOT / "/".join(parts[:-1]) / f"{parts[-1]}.py"
        if path.is_file():
            return True, str(path.relative_to(_REPO_ROOT))
        return False, f"missing module file: {path.relative_to(_REPO_ROOT)}"

    return False, f"unrecognized command pattern: {command[:80]}"


class TestToolchainSmokeMatrixV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _MATRIX_PATH.is_file():
            raise unittest.SkipTest(f"missing matrix: {_MATRIX_PATH}")
        cls.matrix = _load_matrix()
        cls.entries = cls.matrix["entries"]

    def test_matrix_file_exists(self) -> None:
        self.assertTrue(_MATRIX_PATH.is_file())

    def test_top_level_schema(self) -> None:
        missing = _REQUIRED_TOP - set(self.matrix)
        self.assertFalse(missing, msg=f"missing top-level keys: {sorted(missing)}")
        self.assertEqual(self.matrix["schema_version"], "toolchain_smoke_matrix_v1")
        self.assertIsInstance(self.entries, list)
        self.assertGreaterEqual(len(self.entries), 10)

    def test_smoke_ids_unique(self) -> None:
        ids = [e["smoke_id"] for e in self.entries]
        self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate smoke_id: {ids}")

    def test_each_entry_has_required_fields(self) -> None:
        for entry in self.entries:
            with self.subTest(smoke_id=entry.get("smoke_id")):
                missing = _REQUIRED_ENTRY_FIELDS - set(entry)
                self.assertFalse(missing, msg=f"missing fields: {sorted(missing)}")
                self.assertIn(entry["gate_class"], _GATE_CLASSES)
                self.assertIn(entry["tier"], _TIERS)
                self.assertIsInstance(entry["blocks_mainline"], bool)
                self.assertIsInstance(entry["command"], str)
                self.assertTrue(entry["command"].strip())

    def test_ac1_required_smoke_ids_present(self) -> None:
        present = {e["smoke_id"] for e in self.entries}
        missing = _AC1_REQUIRED_SMOKE_IDS - present
        self.assertFalse(missing, msg=f"AC-1 missing smoke_ids: {sorted(missing)}")

    def test_mvp_mainline_is_release_only(self) -> None:
        by_id = {e["smoke_id"]: e for e in self.entries}
        mainline = by_id["TS-MVP-MAINLINE"]
        self.assertEqual(mainline["tier"], "release_only")
        self.assertIn("run_mvp_mainline_regression.py", mainline["command"])

    def test_agent_lines_ci_is_optional_gate_class(self) -> None:
        """AC-8: agent lines CI must not be PR mandatory."""
        agent_entries = [
            e
            for e in self.entries
            if "AGENT-LINES-CI" in e["smoke_id"] or "run_agent_lines_ci_suite" in e["command"]
        ]
        self.assertGreaterEqual(len(agent_entries), 1)
        for entry in agent_entries:
            with self.subTest(smoke_id=entry["smoke_id"]):
                self.assertEqual(entry["gate_class"], "optional")
                self.assertFalse(entry["blocks_mainline"])

    def test_no_toolchain_entry_is_pr_mandatory(self) -> None:
        """Tool-chain matrix entries must not claim PR mandatory gate_class."""
        for entry in self.entries:
            with self.subTest(smoke_id=entry["smoke_id"]):
                if entry["gate_class"] != "mandatory":
                    continue
                if entry["smoke_id"] == _INT_TIER_A_SMOKE_ID:
                    self.assertEqual(entry["tier"], "local_mandatory")
                    self.assertFalse(entry.get("blocks_pr_ci", True))
                    self.assertFalse(entry["blocks_mainline"])
                    continue
                self.fail(
                    f"{entry['smoke_id']} has gate_class=mandatory; "
                    "only TS-INT-TIER-A may be local mandatory (blocks_pr_ci=false)"
                )

    def test_int_tier_a_matrix_entry_semantics(self) -> None:
        by_id = {e["smoke_id"]: e for e in self.entries}
        entry = by_id[_INT_TIER_A_SMOKE_ID]
        self.assertEqual(entry["tier"], "local_mandatory")
        self.assertEqual(entry["gate_class"], "mandatory")
        self.assertFalse(entry["blocks_pr_ci"])
        self.assertIn("_wave7_regression_gate.py", entry["command"])
        self.assertIn("--tier A", entry["command"])

    def test_wa_t3_optional_gate_ids_referenced_when_present(self) -> None:
        p35 = _P35_CONTRACT.read_text(encoding="utf-8")
        for entry in self.entries:
            gate_id = entry.get("wa_t3_gate_id")
            if not gate_id:
                continue
            with self.subTest(smoke_id=entry["smoke_id"], gate_id=gate_id):
                self.assertIn(gate_id, p35)
                self.assertIn("| optional |", p35.split(gate_id, 1)[1][:120])

    def test_wb_t4_dashboard_commands_in_matrix(self) -> None:
        """AC-7: YAML SSOT must cover WB-T4 dashboard verification commands."""
        all_commands = "\n".join(e["command"] for e in self.entries)
        for cmd in _WB_T4_DASHBOARD_COMMANDS:
            with self.subTest(cmd=cmd):
                self.assertIn(cmd, all_commands)

    def test_command_targets_exist(self) -> None:
        for entry in self.entries:
            ok, detail = _command_targets_exist(entry["command"])
            with self.subTest(smoke_id=entry["smoke_id"], detail=detail):
                self.assertTrue(ok, msg=detail)

    def test_dashboard_doc_points_to_matrix_ssot(self) -> None:
        if not _DASHBOARD_DOC.is_file():
            self.skipTest("toolchain-health-dashboard-v1.md missing")
        text = _DASHBOARD_DOC.read_text(encoding="utf-8")
        self.assertIn("phase6-int-regression-gate-contract-v1", text)


if __name__ == "__main__":
    unittest.main()
