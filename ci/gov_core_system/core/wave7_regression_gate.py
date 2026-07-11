"""
Wave 6/7 integration regression gate (INT-REGRESSION-GATE v0.1).

Aggregates Tier-A / Tier-B unittest modules; returns structured ``dict`` result.
Does not implement business rules — only test orchestration and failure diagnostics.
"""

from __future__ import annotations

import re
import traceback
import unittest
from typing import Any

# --- Tier-A: minimum gate (Wave 6 modules + Wave 7 assembly + Wave 8 core contracts) ---
TIER_A_MODULES: tuple[str, ...] = (
    "tests.test_envelope_v2",
    "tests.test_wave6_manifest_writer",
    "tests.test_wave6_qa_manifest_m1",
    "tests.test_wave6_e2e_smoke",
    "tests.test_wave6_intake_gate",
    "tests.test_wave7_runner_env_bootstrap",
    "tests.test_wave7_runner_entry_job_input",
    "tests.test_wave7_artifact_storage",
    "tests.test_wave7_orch_pipeline_wire",
    "tests.test_wave7_report_summary_producer",
    "tests.test_wave7_orch_job_lifecycle",
    # Wave 8 Tier-A: M2 core contracts (sampling design, execution, M1+M2 merge semantics)
    "tests.test_wave8_m2_sampling_design",
    "tests.test_wave8_m2_execution_engine",
    "tests.test_wave8_m2_report_integration",
)

# --- Tier-B: heavier scenarios (Wave 8 orchestrator + Markdown rendering) ---
TIER_B_MODULES: tuple[str, ...] = (
    # Wave 8 Tier-B: orchestrator integration and MD rendering (heavier I/O & combinatorial)
    "tests.test_wave8_m2_orch_integration",
    "tests.test_wave8_report_md_renderer",
    "tests.test_wave8_report_md_orch_integration",
    # Planned (see WAVE7_INT_REGRESSION_GATE_v0.1.md §6):
    # - tests.test_wave7_regression_tier_b_job_rerun
    # - tests.test_wave7_regression_tier_b_io_jitter_matrix
    # - tests.test_wave7_regression_tier_b_large_manifest_batch
)

_VALID_TIERS = frozenset({"A", "B", "ALL"})

_STAGE_RE = re.compile(r"""['"]stage['"]\s*:\s*['"]([^'"]+)['"]""")
_JOB_ID_RE = re.compile(r"""['"]job_id['"]\s*:\s*['"]([^'"]+)['"]""")
_CHECK_ID_RE = re.compile(r"""['"]check_id['"]\s*:\s*['"]([^'"]+)['"]""")


def resolve_tier_modules(tier: str) -> tuple[str, ...]:
    """Resolve unittest module names for ``tier`` (A | B | ALL)."""
    key = (tier or "").strip().upper()
    if key not in _VALID_TIERS:
        raise ValueError(f"invalid tier {tier!r}; expected one of A, B, ALL")
    if key == "A":
        return TIER_A_MODULES
    if key == "B":
        return TIER_B_MODULES
    # ALL: A then B extras (deduped, order preserved)
    seen: set[str] = set()
    out: list[str] = []
    for name in (*TIER_A_MODULES, *TIER_B_MODULES):
        if name not in seen:
            seen.add(name)
            out.append(name)
    return tuple(out)


def extract_failure_diagnostics(text: str) -> dict[str, str | None]:
    """Best-effort parse of stage / job_id / first QA check_id from failure output."""
    stage = None
    job_id = None
    first_check = None
    if text:
        m_stage = _STAGE_RE.search(text)
        if m_stage:
            stage = m_stage.group(1)
        m_job = _JOB_ID_RE.search(text)
        if m_job:
            job_id = m_job.group(1)
        m_check = _CHECK_ID_RE.search(text)
        if m_check:
            first_check = m_check.group(1)
    return {
        "stage": stage,
        "job_id": job_id,
        "first_qa_check_id": first_check,
    }


class _GateTestResult(unittest.TestResult):
    """Capture per-failure diagnostics for structured gate output."""

    def __init__(self) -> None:
        super().__init__()
        self.failure_records: list[dict[str, Any]] = []

    def _record(self, test: unittest.TestCase, err: tuple[Any, Any, Any], *, kind: str) -> None:
        super().addFailure(test, err) if kind == "failure" else super().addError(test, err)
        tb_text = "".join(traceback.format_exception(*err))
        err_msg = err[1]
        msg = str(err_msg) if err_msg is not None else ""
        combined = f"{msg}\n{tb_text}"
        diag = extract_failure_diagnostics(combined)
        self.failure_records.append(
            {
                "test_id": test.id(),
                "kind": kind,
                "message": msg.splitlines()[0] if msg else kind,
                **diag,
            }
        )

    def addFailure(self, test: unittest.TestCase, err: tuple[Any, Any, Any]) -> None:
        self._record(test, err, kind="failure")

    def addError(self, test: unittest.TestCase, err: tuple[Any, Any, Any]) -> None:
        self._record(test, err, kind="error")


def _load_suite(module_names: tuple[str, ...]) -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    errors: list[str] = []
    for mod_name in module_names:
        try:
            suite.addTests(loader.loadTestsFromName(mod_name))
        except Exception as exc:  # noqa: BLE001 — surface import/load failures
            errors.append(f"{mod_name}: {exc}")
    if errors:
        raise RuntimeError("failed to load regression modules: " + "; ".join(errors))
    return suite


def run_regression_gate(
    *,
    tier: str = "A",
    verbosity: int = 1,
) -> dict[str, Any]:
    """
    Run Wave 6/7 regression gate for ``tier`` (A | B | ALL).

    Returns ``{ok, suite, tier, modules, passed, failed, errors, failed_tests, ...}``.
    """
    tier_key = (tier or "A").strip().upper()
    modules = resolve_tier_modules(tier_key)
    if not modules:
        return {
            "ok": True,
            "suite": tier_key,
            "tier": tier_key,
            "modules": [],
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "tests_run": 0,
            "failed_tests": [],
            "tier_b_pending": True,
            "message": "Tier-B modules not registered yet; see WAVE7_INT_REGRESSION_GATE_v0.1.md §6",
        }

    suite = _load_suite(modules)
    if suite.countTestCases() == 0:
        raise RuntimeError("no test cases loaded for requested tier")

    if verbosity >= 2:
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        failed_tests = []
        for test, trace in result.failures:
            failed_tests.append(
                {
                    "test_id": test.id(),
                    "kind": "failure",
                    "message": trace.splitlines()[-1] if trace else "failure",
                    **extract_failure_diagnostics(trace),
                }
            )
        for test, trace in result.errors:
            failed_tests.append(
                {
                    "test_id": test.id(),
                    "kind": "error",
                    "message": trace.splitlines()[-1] if trace else "error",
                    **extract_failure_diagnostics(trace),
                }
            )
    else:
        result = _GateTestResult()
        suite.run(result)
        failed_tests = list(result.failure_records)

    ok = not (result.failures or result.errors)
    return {
        "ok": ok,
        "suite": tier_key,
        "tier": tier_key,
        "modules": list(modules),
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "tests_run": result.testsRun,
        "failed_tests": failed_tests,
    }


def format_first_failure_line(result: dict[str, Any]) -> str | None:
    """Human-readable first-failure diagnostic line for CLI stderr."""
    records = result.get("failed_tests") or []
    if not records:
        return None
    first = records[0]
    parts = [
        f"test={first.get('test_id')}",
        f"stage={first.get('stage') or '-'}",
        f"job_id={first.get('job_id') or '-'}",
        f"first_qa_check_id={first.get('first_qa_check_id') or '-'}",
    ]
    return "INT-REGRESSION-GATE first failure: " + " ".join(parts)


__all__ = [
    "TIER_A_MODULES",
    "TIER_B_MODULES",
    "extract_failure_diagnostics",
    "format_first_failure_line",
    "resolve_tier_modules",
    "run_regression_gate",
]
