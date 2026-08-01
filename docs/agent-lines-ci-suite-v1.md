# Agent Lines CI Suite v1

> **Ticket**: W10-T1 · integrate-agent-lines-into-ci-v1  
> **Implementation**: `scripts/run_agent_lines_ci_suite.py`  
> **Upstream**: `scripts/run_agent_standard_case_regression.py` (W6-T8) · `scripts/run_non_tabular_experiment_preview.py` (W9-T4)  
> **Date**: 2026-06-10  
> **Status**: optional CI helper — **does not** modify MVP mainline regression or Gov Core smoke paths

---

## 1. Purpose

Provide a **single CI entrypoint** for experimental agent lines so pipelines can optionally run safe-case previews on PR, manual workflow dispatch, or nightly jobs — without touching `scripts/run_mvp_mainline_regression.py` or main-chain E2E / UI tests.

| Line | Scope flag | Runner | Safe cases |
|------|------------|--------|------------|
| **Tabular Agent Standard Line** | `tabular` | `run_agent_standard_case_regression.py` | `demo_phase`, `sampleco/2026-0001` (+ optional C/D extended fixtures) |
| **Non-Tabular Experiment Preview** | `non_tabular` | `run_non_tabular_experiment_preview.py` | NT-A (`nt_docu_stub`), NT-B (`nt_log_stub`) |

Merged JSON summary is written to:

```text
outbox/agent_ci/<timestamp>_ci_summary.json
```

---

## 2. When to use

| Scenario | Recommended scope | Notes |
|----------|-------------------|-------|
| **PR manual / optional job** | `all` or `tabular` | Fast signal for agent-line regressions; does not gate mainline by default |
| **Nightly experimental track** | `all --include-extended-fixtures` | Adds `additional_demo` + `sandbox_client` run-path profiles |
| **Non-tabular only smoke** | `non_tabular` | Preview-only; no heavy tools or main-chain writes |
| **Mainline MVP regression** | *(not this helper)* | Continue using `scripts/run_mvp_mainline_regression.py` |

---

## 3. CLI usage

```bash
# Default: both lines, text summary, write CI summary JSON
python scripts/run_agent_lines_ci_suite.py

# Full JSON for Reviewer / SRE dashboards
python scripts/run_agent_lines_ci_suite.py --scope all --format json

# Tabular only (run-all-allowed + auto-approve-intake)
python scripts/run_agent_lines_ci_suite.py --scope tabular

# Non-tabular NT-A / NT-B preview only
python scripts/run_agent_lines_ci_suite.py --scope non_tabular --format json

# Include Wave 7 extended fixtures (C/D)
python scripts/run_agent_lines_ci_suite.py --scope tabular --include-extended-fixtures --format json
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scope` | `all` | `tabular` · `non_tabular` · `all` |
| `--format` | `text` | `text` summary or full `json` to stdout |
| `--include-extended-fixtures` | off | Tabular: also run `additional_demo`, `sandbox_client` |
| `--tabular-outbox-root` | `outbox/agent_experiment_regression/` | Tabular per-case artifacts |
| `--non-tabular-outbox-root` | `outbox/non_tabular_experiment/` | NT preview sandbox artifacts |
| `--ci-outbox-root` | `outbox/agent_ci/` | Merged CI summary root |
| `--no-ci-summary` | off | Skip writing merged summary JSON |

**Success**: exit code `0`; summary `ok: true`.  
**Failure**: exit code `1`; inspect `tabular.cases[]` / `non_tabular.fixtures[]` and per-line outbox artifacts.

---

## 4. CI summary JSON shape

| Key | Description |
|-----|-------------|
| `schema_version` | `agent_lines_ci_suite_v1` |
| `suite_id` | UUID for this CI run |
| `timestamp` | UTC stub used in artifact filename |
| `scope` | Requested scope |
| `scopes_run` | Lines actually executed |
| `ok` | Overall pass/fail |
| `tabular` | Regression summary when tabular scope ran (`null` otherwise) |
| `non_tabular` | NT-A/NT-B fixture summaries when non-tabular scope ran |
| `ci_summary_path` | Relative path to this summary file |
| `message` | Human-readable completion note |

Tabular scope uses **`run-all-allowed`** with **`--auto-approve-intake`** (wired internally). Non-tabular scope runs **preview-only** against documented stub fixtures under `cases/_experiment_samples/`.

### Tabular case fields (W12-T2)

Each `tabular.cases[]` entry includes `fixture_maturity` (`stable` / `controlled_experimental` / `experimental` / `unknown`). When regression artifacts omit the field, the CI helper resolves it via `get_fixture_maturity(case_ref)`.

`tabular.summary.by_fixture_maturity` aggregates pass/fail per tier for Reviewer triage.

Text summary example:

```text
tabular (run-all-allowed):
  ok: true
  passed: 2/2
  - demo_phase [stable] (run): final_status=... ok=True
  - sampleco/2026-0001 [stable] (run): final_status=... ok=True
  by_fixture_maturity:
    stable: passed=2/2
```

With `--include-extended-fixtures`, C/D cases appear as `[controlled_experimental]`.

---

## 5. Safety boundaries

**Does:**

- Invoke existing agent-line helpers only (no duplicated orchestration logic)
- Write artifacts under `outbox/agent_experiment_regression/`, `outbox/non_tabular_experiment/`, `outbox/agent_ci/`
- Support isolated outbox overrides for CI sandboxes

**Does not:**

- Import or call `run_mvp_mainline_regression.py`
- Modify main-chain E2E, Local UI, or Gov Core smoke runners
- Execute non-tabular heavy tools
- Auto-merge into production intake or Tabular outbox state

---

## 6. Verification

```bash
python -m unittest tests.test_agent_lines_ci_suite_v1 -v
python scripts/run_agent_lines_ci_suite.py --scope all --format json
```

**Related docs**: `docs/agent-standard-case-regression-v1.md` · `docs/non-tabular-orchestrator-preview-v1.md` · `docs/agent-standard-line-governance-view-v2.md`

---

## 7. Toolchain health dashboard (WB-T4)

CI summary JSON under `outbox/agent_ci/` is consumed read-only by:

```bash
python scripts/run_toolchain_health_dashboard.py --format json --dry-run
```

The dashboard **does not** invoke `run_agent_lines_ci_suite.py` unless `--no-dry-run` is passed. See `docs/toolchain-health-dashboard-v1.md` · Phase 6 optional smoke matrix in `docs/phase6-int-regression-gate-contract-v1.md` 附录 A.
