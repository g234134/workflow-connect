# Phase 6 — INT Tier-A Verification Report v1

> **Ticket**: WF-P6-INT-GATE · consolidated operator artifact  
> **SSOT contract**: `docs/phase6-int-regression-gate-contract-v1.md`  
> **Matrix entry**: `TS-INT-TIER-A` in `routing/toolchain_smoke_matrix_v1.yaml`  
> **Executed**: 2026-06-27 · gov_core_system venv available

---

## Executive summary

INT Tier-A regression gate was executed locally against Wave 6/7/8 assembly modules (14 `tests.test_*` bundles). **Verdict: PASS** — exit code `0`, `ok: true`, zero failures across 112 tests.

This gate is **local mandatory** for envelope / manifest / QA / orchestrator / runner changes. It is **not** wired into PR CI (`blocks_pr_ci: false` in toolchain matrix). PR green (core-agent-smoke + eval-gate) does **not** imply INT Tier-A green.

---

## Tier-A command (authoritative)

From repo root with **`gov_core_system`** venv activated:

```powershell
python 04_Workflows/_wave7_regression_gate.py --tier A --pretty
```

Pass criteria (contract §2.1):

1. Exit code = `0`
2. JSON: `"ok": true`, `"failed_tests": []`, `"tier": "A"`
3. stderr: no `INT-REGRESSION-GATE first failure:` line

---

## Captured JSON (2026-06-27 run)

```json
{
  "ok": true,
  "suite": "A",
  "tier": "A",
  "modules": [
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
    "tests.test_wave8_m2_sampling_design",
    "tests.test_wave8_m2_execution_engine",
    "tests.test_wave8_m2_report_integration"
  ],
  "passed": 112,
  "failed": 0,
  "errors": 0,
  "tests_run": 112,
  "failed_tests": []
}
```

### Key fields

| Field | Value | Meaning |
|-------|-------|---------|
| `ok` | `true` | Gate pass |
| `tier` / `suite` | `A` | Tier-A scope |
| `modules` | 14 entries | Matches contract §3 / `TIER_A_MODULES` |
| `passed` / `tests_run` | 112 / 112 | All tests executed |
| `failed` / `errors` | 0 / 0 | No regressions |
| `failed_tests` | `[]` | No failure diagnostics |

---

## Verdict

| Check | Result |
|-------|--------|
| venv available | **Yes** |
| Exit code | **0** |
| `ok` | **true** |
| Module count | **14** (Tier-A) |
| Failures | **0** |
| **Overall** | **PASS** |

---

## CI readiness

> **Design SSOT**: `docs/ci-design-p6-int-gate-v1.md` (WF-P6-INT-UPLIFT · design-only · **not live CI**)

### Current state

| Check | Status | Notes |
|-------|--------|-------|
| Local Tier-A mandatory | **Ready** | Contract §2 · matrix `TS-INT-TIER-A` · `gate_class: mandatory` · `blocks_pr_ci: false` |
| PR CI runs INT Tier-A | **No** | `core-agent-smoke.yml` + `eval-gate-ci.yml` do not invoke `_wave7_regression_gate.py` |
| Nightly INT scheduled | **No** | Eval shadow nightly exists; INT nightly is design-only (Track B) |
| PR optional INT job | **No** | Track A pseudo-config in ci-design doc; `continue-on-error: true` |
| Release checklist Tier-A | **Ready** | Manual operator path · contract §5 · `TS-MVP-MAINLINE` separate |

### Gaps (functional — post-uplift ticket scope)

1. **Workflow landing** — `.github/workflows/*` change blocked until 尚書省 approves `docs/ci-design-p6-int-gate-v1.md` (Step 2).
2. **Nightly INT CI** — Track B cron not scheduled.
3. **PR optional advisory** — Track A not wired into eval-gate or standalone workflow.
4. **CI venv strategy** — gov_core_system bootstrap in GHA runner needs infra decision (ci-design § venv).
5. **Phase% uplift** — 72% → 90%+ requires governance chat; this report is evidence only.

### Verification commands (re-run before CI landing)

```powershell
# Contract + matrix structure (no venv required)
python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v
python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v

# Live Tier-A (requires gov_core_system venv)
python 04_Workflows/_wave7_regression_gate.py --tier A --pretty
```

Expected: contract **24/24** · matrix **13/13** (or higher if Tier-B entry added) · Tier-A **`ok: true`** · exit **0**.

---

## Related artifacts

| Artifact | Path |
|----------|------|
| Gate contract | `docs/phase6-int-regression-gate-contract-v1.md` |
| CI design (design-only) | `docs/ci-design-p6-int-gate-v1.md` |
| Toolchain matrix | `routing/toolchain_smoke_matrix_v1.yaml` → `TS-INT-TIER-A` · `TS-INT-TIER-B` |
| CLI runner | `04_Workflows/_wave7_regression_gate.py` |
| Developer entry | `docs/testing.md` |

---

*WF-P6-INT-GATE verification · WF-P6-INT-UPLIFT CI readiness · no CI workflow change*
