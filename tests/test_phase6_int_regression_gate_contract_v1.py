"""Structure / drift checks for phase6-int-regression-gate-contract-v1 (WA-T6).

Doc-only + optional CLI --help smoke; no live Groq/Postgres required.
Tier-A module list is validated against gov_core core/wave7_regression_gate.py when present.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "phase6-int-regression-gate-contract-v1.md"
_WAVE7_GATE_DOC = _REPO_ROOT / "04_Workflows" / "WAVE7_INT_REGRESSION_GATE_v0.1.md"
_TESTING_MD = _REPO_ROOT / "docs" / "testing.md"
_WORKFLOW_INDEX = _REPO_ROOT / "04_Workflows" / "WORKFLOW_INDEX.md"
_GATE_CLI = _REPO_ROOT / "04_Workflows" / "_wave7_regression_gate.py"
_TICKET_STATE = (
    _REPO_ROOT
    / "04_Workflows"
    / "tickets"
    / "WA-T6-phase6-int-regression-gate-runbook-and-ci-integration-v1_state.md"
)
_MATRIX_YAML = _REPO_ROOT / "routing" / "toolchain_smoke_matrix_v1.yaml"
_VERIFICATION_REPORT = (
    _REPO_ROOT / "docs" / "phase6-int-regression-verification-report-v1.md"
)
_MATRIX_TEST = "tests.test_phase6_toolchain_smoke_matrix_v1"
_GOV_CORE_GATE = (
    _REPO_ROOT
    / "01_Environments"
    / "python_venvs"
    / "gov_core_system"
    / "core"
    / "wave7_regression_gate.py"
)

_REQUIRED_SECTIONS = (
    "## §1 Gate 层级总览",
    "## §2 「过 INT gate」定义",
    "## §3 Tier-A 清单与不变量",
    "## §4 Tier-B / ALL / pending 语义",
    "## §5 与 smoke / eval / agent-lines 关系矩阵",
    "## §6 CI 集成指南",
    "## §7 失败诊断",
    "## §8 验证命令",
)

_TOOLCHAIN_SMOKE_COMMANDS = (
    "python scripts/run_toolchain_health_dashboard.py --format json --dry-run --no-write",
    "python -m unittest tests.test_toolchain_health_dashboard_v1 -v",
    "python scripts/run_agent_lines_ci_suite.py",
    "python scripts/analyze_agent_lines_metrics.py",
    "python -m observability.wf_status_summary --help",
)

_AUTHORITATIVE_CMD = "python 04_Workflows/_wave7_regression_gate.py --tier A"

_MATRIX_ROWS = (
    "INT Tier-A",
    "core-agent-smoke PR",
    "eval-gate-ci",
    "agent-lines-ci-suite",
    "mvp-mainline-regression",
    "routing-eval dry-run",
)

_JSON_SHAPE_KEYS = (
    '"ok"',
    '"suite"',
    '"tier"',
    '"modules"',
    '"passed"',
    '"failed"',
    '"tests_run"',
    '"failed_tests"',
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing required file: {path.relative_to(_REPO_ROOT)}")
    return path.read_text(encoding="utf-8")


def _load_tier_modules_from_code() -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    if not _GOV_CORE_GATE.is_file():
        return None
    spec = importlib.util.spec_from_file_location("wave7_regression_gate", _GOV_CORE_GATE)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tier_a = getattr(mod, "TIER_A_MODULES", None)
    tier_b = getattr(mod, "TIER_B_MODULES", None)
    if not isinstance(tier_a, tuple) or not isinstance(tier_b, tuple):
        return None
    return tier_a, tier_b


def _extract_contract_tier_a_modules(text: str) -> list[str]:
    section = text.split("## §3 Tier-A 清单与不变量", 1)
    if len(section) < 2:
        return []
    body = section[1].split("## §4", 1)[0]
    return re.findall(r"`(tests\.test_[^`]+)`", body)


class TestPhase6IntRegressionGateContractV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = _read(_CONTRACT)
        cls.wave7_doc = _read(_WAVE7_GATE_DOC)
        cls.testing_md = _read(_TESTING_MD)
        cls.workflow_index = _read(_WORKFLOW_INDEX)
        cls.code_tiers = _load_tier_modules_from_code()

    def test_contract_file_exists(self) -> None:
        self.assertTrue(_CONTRACT.is_file())

    def test_all_required_section_headings_present(self) -> None:
        missing = [h for h in _REQUIRED_SECTIONS if h not in self.contract]
        self.assertEqual(missing, [], f"missing section headings: {missing}")

    def test_authoritative_pass_command_documented(self) -> None:
        self.assertIn(_AUTHORITATIVE_CMD, self.contract)
        self.assertIn("stdout 末行 JSON", self.contract)
        self.assertIn('"ok": true', self.contract)
        self.assertTrue(
            "exit code 0" in self.contract.lower() or "exit code** = `0`" in self.contract.lower(),
            "contract must document exit code 0 pass criterion",
        )

    def test_first_failure_stderr_pattern_documented(self) -> None:
        self.assertIn("INT-REGRESSION-GATE first failure:", self.contract)
        self.assertIn("stage", self.contract)
        self.assertIn("job_id", self.contract)
        self.assertIn("first_qa_check_id", self.contract)

    def test_tier_b_pending_semantics_documented(self) -> None:
        self.assertIn("tier_b_pending", self.contract)
        self.assertIn('"ok": true', self.contract)
        self.assertRegex(
            self.contract,
            r"禁止.*Wave B.*Tier-B",
        )

    def test_relationship_matrix_has_six_rows(self) -> None:
        matrix_section = self.contract.split("## §5", 1)[1].split("## §6", 1)[0]
        for row in _MATRIX_ROWS:
            with self.subTest(row=row):
                self.assertIn(row, matrix_section)
        self.assertIn("when_required", matrix_section)
        self.assertIn("blocks_merge", matrix_section)

    def test_ci_section_states_pr_green_not_int_green(self) -> None:
        self.assertRegex(self.contract, r"≠|不.*等于|不等于")
        section6 = self.contract.split("## §6 CI 集成指南", 1)[1].split("## §7", 1)[0]
        self.assertIn("core-agent-smoke", section6)
        self.assertIn("eval-gate-ci", section6)

    def test_json_shape_keys_in_contract(self) -> None:
        for key in _JSON_SHAPE_KEYS:
            with self.subTest(key=key):
                self.assertIn(key, self.contract)

    def test_unittest_module_named_in_contract_section_8(self) -> None:
        self.assertIn("tests.test_phase6_int_regression_gate_contract_v1", self.contract)

    def test_wave7_doc_points_to_phase6_contract(self) -> None:
        self.assertIn("phase6-int-regression-gate-contract-v1", self.wave7_doc)

    def test_testing_md_cross_refs_contract(self) -> None:
        self.assertIn("phase6-int-regression-gate-contract-v1", self.testing_md)
        self.assertIn("phase6-int-regression-verification-report-v1", self.testing_md)

    def test_workflow_index_links_contract(self) -> None:
        self.assertIn("WA-T6", self.workflow_index)
        self.assertIn("phase6-int-regression-gate-contract-v1", self.workflow_index)

    def test_ticket_state_file_exists(self) -> None:
        self.assertTrue(_TICKET_STATE.is_file())

    def test_gate_cli_exists(self) -> None:
        self.assertTrue(_GATE_CLI.is_file())

    def test_tier_a_modules_match_code_when_available(self) -> None:
        if self.code_tiers is None:
            self.skipTest("gov_core wave7_regression_gate.py not available")
        tier_a_code, _ = self.code_tiers
        contract_modules = _extract_contract_tier_a_modules(self.contract)
        self.assertEqual(
            contract_modules,
            list(tier_a_code),
            "contract §3 Tier-A table must match TIER_A_MODULES in code",
        )

    def test_tier_a_modules_match_wave7_doc_table(self) -> None:
        if self.code_tiers is None:
            self.skipTest("gov_core wave7_regression_gate.py not available")
        tier_a_code, _ = self.code_tiers
        section5 = self.wave7_doc.split("## 5. Tier-A 测试清单", 1)
        if len(section5) < 2:
            self.fail("WAVE7 doc missing Tier-A section")
        body = section5[1].split("### 4.1 Tier-A", 1)[0]
        summary_modules = []
        for line in body.splitlines():
            m = re.match(r"\|\s*`(tests\.test_[^`]+)`\s*\|", line)
            if m:
                summary_modules.append(m.group(1))
        self.assertEqual(
            len(summary_modules),
            len(tier_a_code),
            "WAVE7 §5 summary table row count must match TIER_A_MODULES",
        )
        self.assertEqual(
            summary_modules,
            list(tier_a_code),
            "WAVE7 §5 module list must match code TIER_A_MODULES",
        )

    def test_appendix_toolchain_smoke_matrix_present(self) -> None:
        appendix = self.contract.split("## 附录 A", 1)
        self.assertGreaterEqual(len(appendix), 2, "missing appendix A section")
        body = appendix[1]
        self.assertIn("Tool-chain smoke matrix", body)
        self.assertIn("routing/toolchain_smoke_matrix_v1.yaml", body)
        self.assertIn("toolchain_smoke_matrix_v1", body)
        self.assertIn("optional", body.lower())
        self.assertIn("blocks_mainline", body)
        for cmd in _TOOLCHAIN_SMOKE_COMMANDS:
            with self.subTest(cmd=cmd):
                self.assertIn(cmd, body)
        self.assertIn("eval-gate-ci.yml", body)
        self.assertIn("release_only", body)
        self.assertIn("TS-AGENT-LINES-CI", body)
        self.assertIn("TS-INT-TIER-A", body)
        self.assertIn("local_mandatory", body)

    def test_toolchain_smoke_matrix_yaml_exists(self) -> None:
        self.assertTrue(_MATRIX_YAML.is_file(), "WB-T7 YAML SSOT must exist")

    def test_contract_section_8_references_matrix_unittest(self) -> None:
        section8 = self.contract.split("## §8 验证命令", 1)[1]
        self.assertIn(_MATRIX_TEST, section8)

    def test_contract_section_8_references_verification_report(self) -> None:
        section8 = self.contract.split("## §8 验证命令", 1)[1]
        self.assertIn("phase6-int-regression-verification-report-v1", section8)

    def test_verification_report_file_exists(self) -> None:
        self.assertTrue(_VERIFICATION_REPORT.is_file())

    def test_verification_report_documents_tier_a_command_and_verdict(self) -> None:
        if not _VERIFICATION_REPORT.is_file():
            self.skipTest("verification report not yet created")
        text = _VERIFICATION_REPORT.read_text(encoding="utf-8")
        self.assertIn(_AUTHORITATIVE_CMD, text)
        self.assertIn('"ok": true', text)
        self.assertIn("TS-INT-TIER-A", text)
        self.assertIn("PASS", text)


class TestPhase6ContractVerificationCommand(unittest.TestCase):
    def test_documented_unittest_command_runs(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.test_phase6_int_regression_gate_contract_v1.TestPhase6IntRegressionGateContractV1",
                "-v",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"unittest failed:\nstdout={proc.stdout}\nstderr={proc.stderr}",
        )


class TestPhase6GateCliHelp(unittest.TestCase):
    def test_wave7_regression_gate_help_invokable(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_GATE_CLI), "--help"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("--tier", proc.stdout)
        self.assertIn("--pretty", proc.stdout)


if __name__ == "__main__":
    unittest.main()
