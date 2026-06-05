"""
Phase 6 / P6 — core agent workflow smoke gate.

Aggregates unittest modules for PR-fast (ROOT) and optional dark-core (DARK) tiers.
Returns structured ``dict`` (``ok``, ``tier``, ``modules``, ``failed_tests``, …).
"""

from __future__ import annotations

import re
import subprocess
import sys
import traceback
import unittest
from pathlib import Path
from typing import Any, Callable

# --- Tier ROOT: repo-root agent workflows (no venv / no PG) ---
TIER_ROOT_MODULES: tuple[str, ...] = (
    "tests.test_context_entry",
    "tests.test_context_subagent_routing",
    "tests.test_monitoring_executor",
    "tests.test_langgraph_flow_k2",
    "tests.test_hq_task_routing_smoke",
    "tests.test_eval_gate",
    "tests.test_eval_ci_check",
)

# --- Tier DARK: gov_core_system unittest (subprocess; stable subset for CI) ---
TIER_DARK_MODULES: tuple[str, ...] = (
    "tests.test_minimal_orchestration_bridge_tool_flow",
    "tests.test_tool_executor.TestToolExecutor.test_empty_selected_tools",
    "tests.test_tool_executor.TestToolExecutor.test_invalid_selection_missing_decision_id",
    "tests.test_monitoring_api.MonitoringApiTests.test_healthz_lists_monitoring_routes",
    "tests.test_monitoring_api.MonitoringApiTests.test_dashboard_summary_example_validates",
)

# Full dark modules for local venv (``--tier DARK_FULL``)
TIER_DARK_FULL_MODULES: tuple[str, ...] = (
    "tests.test_tool_executor",
    "tests.test_minimal_orchestration_bridge_tool_flow",
    "tests.test_monitoring_api",
)

# --- Tier HQ: 04_Workflows routing policy (loaded via workflows path) ---
TIER_HQ_MODULE = "test_task_routing"

_VALID_TIERS = frozenset({"ROOT", "DARK", "DARK_FULL", "HQ", "PR", "ALL"})

_TEST_ID_RE = re.compile(r"^\s*test_id=(\S+)")


def resolve_tier_modules(tier: str) -> tuple[str, ...]:
    """Resolve unittest module names for ``tier`` (ROOT | DARK | HQ | PR | ALL)."""
    key = (tier or "PR").strip().upper()
    if key not in _VALID_TIERS:
        raise ValueError(
            f"invalid tier {tier!r}; expected one of ROOT, DARK, DARK_FULL, HQ, PR, ALL"
        )
    if key == "ROOT":
        return TIER_ROOT_MODULES
    if key == "DARK":
        return TIER_DARK_MODULES
    if key == "DARK_FULL":
        return TIER_DARK_FULL_MODULES
    if key == "HQ":
        return (TIER_HQ_MODULE,)
    if key == "PR":
        return TIER_ROOT_MODULES
    # ALL: ROOT + HQ + DARK (deduped)
    seen: set[str] = set()
    out: list[str] = []
    for name in (*TIER_ROOT_MODULES, TIER_HQ_MODULE, *TIER_DARK_MODULES):
        if name not in seen:
            seen.add(name)
            out.append(name)
    return tuple(out)


def ensure_repo_root_on_path(repo_root: Path | None = None) -> Path:
    """Insert repo root at sys.path[0] if missing."""
    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    return root


def ensure_workflows_on_path(workflows_dir: Path) -> None:
    """Insert ``04_Workflows`` and ``02_Agents_Core`` for HQ routing tests."""
    wf = workflows_dir.resolve()
    agents = wf.parent / "02_Agents_Core"
    for p in (str(agents), str(wf)):
        if p not in sys.path:
            sys.path.insert(0, p)


def ensure_gov_core_on_path(gov_core_root: Path) -> Path:
    """Insert gov_core_system venv root at sys.path[0]."""
    gov = gov_core_root.resolve()
    gov_s = str(gov)
    if gov_s not in sys.path:
        sys.path.insert(0, gov_s)
    return gov


def gov_core_root_from_master_map(workflows_dir: Path) -> Path:
    """Resolve gov_core_system path via Master_Map.json cabins entry."""
    import json

    mp_path = workflows_dir / "Master_Map.json"
    with mp_path.open(encoding="utf-8") as fh:
        master_map = json.load(fh)
    cabins = master_map.get("cabins") or {}
    entry = cabins.get("gov_core_system") if isinstance(cabins, dict) else None
    if not isinstance(entry, dict):
        raise RuntimeError("Master_Map.cabins.gov_core_system missing")
    venv_rel = entry.get("venv_dir")
    if not venv_rel:
        raise RuntimeError("Master_Map.cabins.gov_core_system.venv_dir missing")
    return (workflows_dir.parent / str(venv_rel).replace("\\", "/")).resolve()


class _GateTestResult(unittest.TestResult):
    """Collect structured failure records without verbose runner output."""

    def __init__(self) -> None:
        super().__init__()
        self.failure_records: list[dict[str, Any]] = []

    def addFailure(self, test: unittest.TestCase, err: Any) -> None:  # noqa: N802
        super().addFailure(test, err)
        self._record(test, "failure", err)

    def addError(self, test: unittest.TestCase, err: Any) -> None:  # noqa: N802
        super().addError(test, err)
        self._record(test, "error", err)

    def _record(self, test: unittest.TestCase, kind: str, err: Any) -> None:
        trace = "".join(traceback.format_exception(*err))
        self.failure_records.append(
            {
                "test_id": test.id(),
                "kind": kind,
                "message": trace.splitlines()[-1] if trace else kind,
            }
        )


def _resolve_gov_core_python(gov_core_root: Path) -> str:
    """Prefer venv interpreter under ``gov_core_system`` when present."""
    import os

    gov = gov_core_root.resolve()
    if os.name == "nt":
        candidate = gov / "Scripts" / "python.exe"
    else:
        candidate = gov / "bin" / "python"
    if candidate.is_file():
        return str(candidate)
    return sys.executable


def _run_dark_subprocess(
    gov_core_root: Path,
    modules: tuple[str, ...],
    *,
    verbosity: int,
    repo_root: Path,
) -> dict[str, Any]:
    """
    Run dark-tier unittest in an isolated subprocess (avoids repo ``tests`` package clash).
    """
    gov = gov_core_root.resolve()
    py = _resolve_gov_core_python(gov)
    cmd = [py, "-m", "unittest", *modules]
    if verbosity >= 1:
        cmd.append("-v")
    if verbosity >= 2:
        cmd.append("-v")

    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = os_pathsep_join_unique(str(gov), str(repo_root.resolve()))

    proc = subprocess.run(
        cmd,
        cwd=str(gov),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = stdout + stderr

    # Parse unittest summary line: "Ran N tests in Xs" / "FAILED (failures=1, errors=2)"
    tests_run = 0
    failed = 0
    errors = 0
    m_run = re.search(r"Ran (\d+) tests?", combined)
    if m_run:
        tests_run = int(m_run.group(1))
    m_fail = re.search(r"failures=(\d+)", combined)
    if m_fail:
        failed = int(m_fail.group(1))
    m_err = re.search(r"errors=(\d+)", combined)
    if m_err:
        errors = int(m_err.group(1))

    failed_tests: list[dict[str, Any]] = []
    for line in combined.splitlines():
        if line.startswith("FAIL:") or line.startswith("ERROR:"):
            failed_tests.append(
                {
                    "test_id": line.split(maxsplit=1)[1] if " " in line else line,
                    "kind": "failure" if line.startswith("FAIL:") else "error",
                    "message": line,
                }
            )

    passed = max(0, tests_run - failed - errors)
    ok = proc.returncode == 0
    return {
        "ok": ok,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "tests_run": tests_run,
        "failed_tests": failed_tests,
        "subprocess_returncode": proc.returncode,
        "subprocess_tail": combined[-4000:] if combined else "",
    }


def os_pathsep_join_unique(*parts: str) -> str:
    import os

    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        if part and part not in seen:
            seen.add(part)
            out.append(part)
    return os.pathsep.join(out)


def _load_suite(module_names: tuple[str, ...]) -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    errors: list[str] = []
    for mod_name in module_names:
        try:
            suite.addTests(loader.loadTestsFromName(mod_name))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{mod_name}: {exc}")
    if errors:
        raise RuntimeError("failed to load smoke modules: " + "; ".join(errors))
    return suite


def _run_suite_once(
    modules: tuple[str, ...],
    *,
    verbosity: int,
    path_setup: Callable[[], None] | None = None,
) -> tuple[unittest.TestResult, list[dict[str, Any]]]:
    """Run one module bundle after optional ``path_setup`` (may reorder ``sys.path``)."""
    if path_setup is not None:
        path_setup()

    suite = _load_suite(modules)
    if suite.countTestCases() == 0:
        raise RuntimeError("no test cases loaded for requested tier")

    if verbosity >= 2:
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        failed_tests: list[dict[str, Any]] = []
        for test, trace in result.failures:
            failed_tests.append(
                {
                    "test_id": test.id(),
                    "kind": "failure",
                    "message": trace.splitlines()[-1] if trace else "failure",
                }
            )
        for test, trace in result.errors:
            failed_tests.append(
                {
                    "test_id": test.id(),
                    "kind": "error",
                    "message": trace.splitlines()[-1] if trace else "error",
                }
            )
        return result, failed_tests

    result = _GateTestResult()
    suite.run(result)
    return result, list(result.failure_records)


def _partition_modules(tier_key: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return (root_modules, hq_modules, dark_modules) for ``tier_key``."""
    all_mods = resolve_tier_modules(tier_key)
    dark_set = frozenset((*TIER_DARK_MODULES, *TIER_DARK_FULL_MODULES))
    hq_set = frozenset({TIER_HQ_MODULE})
    root: list[str] = []
    hq: list[str] = []
    dark: list[str] = []
    for name in all_mods:
        if name in dark_set:
            dark.append(name)
        elif name in hq_set:
            hq.append(name)
        else:
            root.append(name)
    return tuple(root), tuple(hq), tuple(dark)


def run_agent_workflow_smoke(
    *,
    tier: str = "PR",
    verbosity: int = 1,
    repo_root: Path | None = None,
    workflows_dir: Path | None = None,
    gov_core_root: Path | None = None,
) -> dict[str, Any]:
    """
    Run agent workflow smoke for ``tier``.

    ``PR`` = ROOT only (GitHub PR fast path).
    ``ALL`` = ROOT + HQ + DARK (requires ``gov_core_root`` or Master_Map resolution).

    DARK modules run with **only** ``gov_core_system`` on ``sys.path`` front to avoid
    clashing with repo-root ``tests`` package.
    """
    tier_key = (tier or "PR").strip().upper()
    root_mods, hq_mods, dark_mods = _partition_modules(tier_key)

    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    wf = workflows_dir or (root / "04_Workflows")
    gov = None
    if dark_mods:
        gov = gov_core_root or gov_core_root_from_master_map(wf)

    if not (root_mods or hq_mods or dark_mods):
        return {
            "ok": True,
            "suite": "agent_workflow_smoke",
            "tier": tier_key,
            "modules": [],
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "tests_run": 0,
            "failed_tests": [],
            "message": "no modules for tier",
        }

    def _setup_root_hq() -> None:
        ensure_repo_root_on_path(root)
        if hq_mods:
            ensure_workflows_on_path(wf)

    combined_failed: list[dict[str, Any]] = []
    tests_run = 0
    passed = 0
    failed = 0
    errors = 0
    all_module_names: list[str] = []

    bundles: list[tuple[tuple[str, ...], Callable[[], None] | None]] = []
    if root_mods:
        bundles.append((root_mods, _setup_root_hq))
    if hq_mods:
        bundles.append((hq_mods, _setup_root_hq))

    for mods, setup in bundles:
        all_module_names.extend(mods)
        result, fail_records = _run_suite_once(mods, verbosity=verbosity, path_setup=setup)
        tests_run += result.testsRun
        failed += len(result.failures)
        errors += len(result.errors)
        passed += result.testsRun - len(result.failures) - len(result.errors)
        combined_failed.extend(fail_records)

    if dark_mods:
        assert gov is not None
        all_module_names.extend(dark_mods)
        dark_result = _run_dark_subprocess(
            gov,
            dark_mods,
            verbosity=verbosity,
            repo_root=root,
        )
        tests_run += int(dark_result.get("tests_run") or 0)
        failed += int(dark_result.get("failed") or 0)
        errors += int(dark_result.get("errors") or 0)
        passed += int(dark_result.get("passed") or 0)
        combined_failed.extend(dark_result.get("failed_tests") or [])

    ok = failed == 0 and errors == 0
    return {
        "ok": ok,
        "suite": "agent_workflow_smoke",
        "tier": tier_key,
        "modules": all_module_names,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "tests_run": tests_run,
        "failed_tests": combined_failed,
    }


def format_first_failure_line(result: dict[str, Any]) -> str | None:
    """Human-readable first-failure line for CLI stderr."""
    records = result.get("failed_tests") or []
    if not records:
        return None
    first = records[0]
    return (
        "AGENT-WORKFLOW-SMOKE first failure: "
        f"test={first.get('test_id')} kind={first.get('kind')} "
        f"msg={first.get('message')}"
    )


__all__ = [
    "TIER_ROOT_MODULES",
    "TIER_DARK_MODULES",
    "TIER_DARK_FULL_MODULES",
    "TIER_HQ_MODULE",
    "ensure_gov_core_on_path",
    "ensure_repo_root_on_path",
    "format_first_failure_line",
    "gov_core_root_from_master_map",
    "resolve_tier_modules",
    "run_agent_workflow_smoke",
]
