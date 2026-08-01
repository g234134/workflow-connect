# Phase 6 — INT Gate CI Integration Design v1

> **Ticket**: WF-P6-INT-UPLIFT · design-only · **not live CI**  
> **SSOT contract**: `docs/phase6-int-regression-gate-contract-v1.md`  
> **Verification evidence**: `docs/phase6-int-regression-verification-report-v1.md`  
> **Matrix entries**: `TS-INT-TIER-A` · `TS-INT-TIER-B` in `routing/toolchain_smoke_matrix_v1.yaml`

---

## Executive summary

**Today (2026-06-27)**

| Aspect | Status |
|--------|--------|
| INT Tier-A CLI | **Available** — `python 04_Workflows/_wave7_regression_gate.py --tier A` |
| Local mandatory | **Yes** — envelope / manifest / QA / orchestrator / runner changes |
| Contract + unittest | **24/24** contract tests · **13/13** matrix tests |
| Live Tier-A run | **PASS** — 14 modules · 112 tests · exit 0 |
| PR CI (mandatory trio) | **Does not run** INT Tier-A |
| Nightly INT CI | **Not scheduled** |
| Release checklist | **Recommends** Tier-A (already in contract §5) |

**Bottom line**: INT gate is **locally mandatory and verified**; **CI is not wired**. This document specifies a three-track CI design for governance approval and a future workflow landing ticket. **No `.github/workflows/*` change is included in WF-P6-INT-UPLIFT.**

---

## Two-step governance model

| Step | Owner | Deliverable | Status |
|------|-------|-------------|--------|
| **Step 1** | WF-P6-INT-UPLIFT (this ticket) | CI design doc · verification report CI readiness · matrix semantics · cross-refs | **Done** (design + evidence) |
| **Step 2** | Future ticket (post 尚書省 approval) | Land pseudo-config below into `.github/workflows/*` | **Blocked** — requires governance sign-off |

**Phase% uplift (72% → 90%+)** is a **separate governance chat** decision. This ticket prepares technical artifacts only; it does **not** change global Phase% or `workflow_line_status` uplift fields (Scribe-owned).

---

## Existing CI context (read-only reference)

| Workflow | File | PR role | Runs INT Tier-A? |
|----------|------|---------|------------------|
| Core agent smoke | `.github/workflows/core-agent-smoke.yml` | **Required** — `_core_agent_smoke.py --tier PR` | **No** |
| Eval gate | `.github/workflows/eval-gate-ci.yml` | **Required** — eval unittest + routing dry-run | **No** |
| Eval shadow nightly | `eval-gate-ci.yml` → `eval-shadow-nightly` job | Scheduled UTC 06:00 | **No** |

**Key invariant (contract §5)**: `core-agent-smoke` green + `eval-gate-ci` green **≠** INT Tier-A green.

---

## Three-track CI design

### Track A — PR optional job (non-blocking)

| Field | Value |
|-------|-------|
| **Purpose** | Early signal on Wave 6/7/8 assembly regressions without blocking merge |
| **Trigger** | `pull_request` · `push` to default branch (same paths as eval-gate or path-filtered to `04_Workflows/**`, `gov_core_system/**`, envelope/manifest modules) |
| **Placement options** | (1) New job in `eval-gate-ci.yml` with `continue-on-error: true`; (2) Separate workflow `p6-int-gate-smoke.yml` |
| **venv / setup** | Checkout → Python 3.12 → **gov_core_system path bootstrap** via `_wave7_regression_gate.py` (inserts venv from `Master_Map.json`) **or** cached venv artifact (future infra ticket) |
| **Command** | `python 04_Workflows/_wave7_regression_gate.py --tier A --pretty` |
| **Pass criteria** | Exit `0` · JSON `"ok": true` · `"failed_tests": []` · `"tier": "A"` |
| **Merge impact** | **`continue-on-error: true`** — failure surfaces as annotation / artifact, **does not block PR** |
| **Est. runtime** | **~2–4 min** (112 tests @ 2026-06-27 baseline; matrix `estimated_seconds: 120`) |

**Pseudo YAML (design-only — not committed)**

```yaml
# Option A: additional job in eval-gate-ci.yml (non-blocking advisory)
int-tier-a-advisory:
  name: P6 INT Tier-A (advisory · non-blocking)
  if: github.event_name != 'schedule'
  runs-on: ubuntu-latest
  continue-on-error: true  # WA-T3 optional class; blocks_pr_ci=false
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - name: INT Tier-A regression (Wave 6/7/8)
      run: |
        set -euo pipefail
        python 04_Workflows/_wave7_regression_gate.py --tier A --pretty | tee int_tier_a_result.json
    - name: Upload INT gate JSON
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: p6-int-tier-a-advisory-${{ github.run_id }}
        path: int_tier_a_result.json
        if-no-files-found: warn
```

**Governance note**: Track A satisfies "PR visibility" without elevating INT to PR mandatory trio (forbidden by WA-T3 / contract appendix A).

---

### Track B — Nightly scheduled INT Tier-A

| Field | Value |
|-------|-------|
| **Purpose** | Continuous assembly regression on main; catch drift when developers skip local Tier-A |
| **Trigger** | `schedule` cron (recommended **UTC 07:00** — after eval shadow nightly at 06:00) · `workflow_dispatch` |
| **Placement options** | New workflow `p6-int-gate-nightly.yml` **or** new scheduled job in existing nightly-capable workflow |
| **venv / setup** | Same as Track A; nightly may use longer timeout (10–15 min) |
| **Command** | `python 04_Workflows/_wave7_regression_gate.py --tier A --pretty` |
| **Pass criteria** | Exit `0` · `"ok": true` · upload JSON artifact |
| **Failure handling** | `continue-on-error: false` for nightly job itself; notify via existing observability / Slack hook (out of scope — separate ticket) |
| **Est. runtime** | **~2–4 min** Tier-A only; **~5–7 min** if extended to `--tier ALL` (future option) |

**Pseudo YAML (design-only — not committed)**

```yaml
name: P6 INT gate nightly

on:
  schedule:
    - cron: "0 7 * * *"  # UTC daily, after eval-gate shadow
  workflow_dispatch:
    inputs:
      tier:
        description: INT tier (A, B, ALL)
        type: choice
        options: [A, B, ALL]
        default: A

jobs:
  int-regression-nightly:
    name: INT Tier-A nightly
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Wave 6/7/8 INT regression
        run: |
          TIER="${{ github.event_name == 'workflow_dispatch' && inputs.tier || 'A' }}"
          python 04_Workflows/_wave7_regression_gate.py --tier "${TIER}" --pretty \
            | tee "int_gate_nightly_${TIER}.json"
      - uses: actions/upload-artifact@v4
        with:
          name: p6-int-gate-nightly-${{ github.run_id }}
          path: int_gate_nightly_*.json
```

**Optional extension**: Add `TS-INT-TIER-B` (`--tier B`) as a second matrix step on weekly cron (Sunday) — heavier integration, still non-blocking for PR.

---

### Track C — Release checklist mandatory (existing)

| Field | Value |
|-------|-------|
| **Purpose** | Human gate before tag / demo / Tabular MVP release |
| **Trigger** | Manual — operator runs before release sign-off |
| **Commands** | Tier-A: `python 04_Workflows/_wave7_regression_gate.py --tier A --pretty` · Recommended ALL: `--tier ALL` · MVP mainline: `python scripts/run_mvp_mainline_regression.py -v` (`TS-MVP-MAINLINE`) |
| **Pass criteria** | Tier-A exit `0` · mainline 6/6 green (release contract) |
| **CI automation** | **None required** — checklist-driven; documented in `docs/tabular-mvp-release-checklist.md` and contract §5 |
| **Est. runtime** | Tier-A **~2–4 min** · ALL **~5–7 min** · MVP mainline **~90 s** |

Track C is **already in contract**; this design doc does not change release semantics.

---

## Track comparison matrix

| Track | Trigger | Blocks PR merge | Blocks release | CI status |
|-------|---------|-----------------|----------------|-----------|
| **A — PR optional** | PR / push | **No** | No | **Not wired** |
| **B — Nightly** | cron / dispatch | No | No | **Not wired** |
| **C — Release checklist** | Manual | No | **Yes** (operator) | **Process-only** (no GHA) |

---

## venv and environment requirements

INT Tier-A **must** import dark `core.wave7_*` and `gov_core_system/tests/*`.

1. **Local (today)**: Activate gov_core_system venv via `04_Workflows/Enter-Agency.ps1`; CLI auto-injects paths from `Master_Map.json`.
2. **CI (future)**: Options ranked by complexity:
   - **A1 (minimal)**: Rely on `_wave7_regression_gate.py` bootstrap + checkout-only (works if tests are self-contained with stubs).
   - **A2 (recommended)**: Pre-build venv cache keyed on `requirements-ci-minimal.txt` + dark test deps (mirrors `core-agent-smoke.yml` DARK tier pattern).
   - **A3 (full)**: Self-hosted runner with pre-provisioned gov_core_system venv (instance anchor — not in portable docs).

**Exit code 2** in CI = infrastructure failure (venv/map); do **not** treat as regression failure (contract §2.3).

---

## Uplift readiness (72% → 90%+)

| Criterion | Evidence | Gap |
|-----------|----------|-----|
| Contract SSOT v1 | `docs/phase6-int-regression-gate-contract-v1.md` | — |
| Executable CLI + live PASS | Verification report 2026-06-27 · 112/112 | — |
| Machine-readable matrix | `TS-INT-TIER-A` · `blocks_pr_ci: false` | — |
| CI design documented | **This doc** | Workflow landing (Step 2) |
| Nightly or PR optional CI live | — | **Governance + Step 2 ticket** |
| Phase% uplift | — | **尚書省 governance chat** |

**Recommended governance minimum for 90%+**: Approve **Track B (nightly)** *or* **Track A (PR optional)** — at least one automated path beyond local mandatory.

---

## Explicit non-claims

- **NOT** live CI — no workflow files changed in WF-P6-INT-UPLIFT.
- **NOT** PR mandatory INT Tier-A — `blocks_pr_ci: false` preserved.
- **NOT** nightly INT CI scheduled or running in production.
- **NOT** global Phase% uplift — governance-only.
- **NOT** a substitute for MVP mainline regression or eval-gate on PR.

---

## Related artifacts

| Document | Role |
|----------|------|
| `docs/phase6-int-regression-gate-contract-v1.md` | Tier semantics · pass definition · §8 verification |
| `docs/phase6-int-regression-verification-report-v1.md` | Executed Tier-A JSON · CI readiness |
| `routing/toolchain_smoke_matrix_v1.yaml` | `TS-INT-TIER-A` / `TS-INT-TIER-B` |
| `docs/testing.md` | Developer entry · pyramid |
| `.github/workflows/core-agent-smoke.yml` | PR smoke reference (read-only) |
| `.github/workflows/eval-gate-ci.yml` | Eval + nightly pattern reference (read-only) |
| `04_Workflows/WAVE7_RUNBOOK_CLI_AND_QA_v0.1.md` §7 | Legacy CI hook pseudo-code |

---

*WF-P6-INT-UPLIFT · design-only · Step 2 requires 尚書省 approval before workflow landing*
