# Tabular Mainline E2E Verification Checklist v1

> **Role**: Repeatable end-to-end verification for the Tabular cleaning **main chain** (control plane → unified driver → HITL → delivery approve).  
> **Status**: v1 · 2026-06-27 · **非** prod gate  
> **Authority**: `docs/TABULAR_MVP_SSOT.md` · `docs/C2-P2_RUNBOOK.md` · `docs/tabular-demo_phase-regression-v1.md`  
> **Report**: `docs/tabular-mainline-e2e-verification-report-v1.md`

---

## 1. Scope

| In scope | Out of scope |
|----------|--------------|
| Control plane (`automation_state.json` + `manage_tabular_automation_state.py`) | OCR / PDF tables |
| Unified driver (`run_tabular_automation.py` + `automation_run_log.json`) | Governance / CI / GA rails |
| HITL CP-A / CP-B + `run_hitl_checkpoint_cli.py` | `--force` bypass paths (internal demo only) |
| Delivery approve (`approve_tabular_delivery.py` + signoff + `cases/index.json`) | Prod closure claims |
| Allowlist cases: `demo_phase` · `sampleco/2026-0001` | Non-allowlist cases without explicit override |

**Driver step order (canonical):**  
`intake` → `eligibility` → `checkpoint_a` → `cleaning` → `report` → `bundle` → `e2e` → `checkpoint_b`

---

## 2. Prerequisites

- Repo root with `cases/demo_phase/` and `cases/sampleco/2026-0001/` fixtures present.
- Python 3.x on PATH; no venv required for CLI smoke (uses repo `scripts/`).
- Operator id for audit (e.g. `e2e_verifier`).

**One-command regression anchor (demo_phase only):**

```bash
python scripts/run_demo_phase_regression_smoke.py --json
```

This checklist adds **manual step-by-step** verification for both allowlist cases.

---

## 3. Case A — `demo_phase` (`phase_demo_v1`)

### 3.1 Flow

```text
start (control plane, --restart)
  → run_tabular_automation (no --force)
  → pause at CP-A
  → approve-a + resume-after-checkpoint
  → clean → report → bundle → e2e
  → CP-B (auto-skip when output_guard=ok)
  → approve_tabular_delivery --approve
```

### 3.2 Commands

```bash
python scripts/manage_tabular_automation_state.py start \
  --case-dir cases/demo_phase --requested-by <operator> --restart --json

python scripts/run_tabular_automation.py --case-id demo_phase --json

python scripts/run_hitl_checkpoint_cli.py approve-a --case-id demo_phase \
  --operator-id <operator> --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint \
  --case-id demo_phase --operator-id <operator> --json

# CP-B: auto-skip expected (output_guard.status=ok); no approve-b required

python scripts/approve_tabular_delivery.py --case-id demo_phase \
  --approve --by <operator> --json
```

### 3.3 Pass criteria

| Check | Expected |
|-------|----------|
| Gate | `eligibility=review_needed` (rows&lt;100); driver continues without `--force` after CP-A |
| Cleaning | 7 → 5 rows · `cleaning_profile_id=phase_demo_v1` |
| `qa_status` | `pass_with_warnings` |
| `output_guard.status` | `ok` (ratio ≥ 0.5) |
| CP-A | `checkpoint_a_status=approved` · outbox checkpoint written |
| CP-B | `checkpoint_b_status=not_required` or run-log `checkpoint_b` `completed` with `skip_reason=ok_no_human_gate` |
| `automation_status` | `completed` |
| `overall_ok` | `true` — run-log `e2e` step `completed` |
| `delivery_ready` | `true` after `--approve` |
| Artifacts | `cleaned/*_cleaned.csv` · `reports/report.json` · `delivery_signoff.md` |
| Index / signoff | Updated; no error flags in readiness gaps |

---

## 4. Case B — `sampleco/2026-0001` (`sampleco_order_profile`)

### 4.1 Flow

Same as Case A, but **CP-B HITL is required** when `output_guard.status=warning`.

```text
start → driver (no --force) → CP-A → approve-a → resume
  → clean (115→8) → bundle → e2e → CP-B pause
  → approve-b → resume-after-checkpoint
  → approve_tabular_delivery --approve
```

### 4.2 Commands

```bash
python scripts/manage_tabular_automation_state.py start \
  --case-dir cases/sampleco/2026-0001 --requested-by <operator> --restart --json

python scripts/run_tabular_automation.py --case-dir cases/sampleco/2026-0001 --json

python scripts/run_hitl_checkpoint_cli.py approve-a \
  --case-dir cases/sampleco/2026-0001 --operator-id <operator> --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint \
  --case-dir cases/sampleco/2026-0001 --operator-id <operator> --json

python scripts/run_hitl_checkpoint_cli.py approve-b \
  --case-dir cases/sampleco/2026-0001 --operator-id <operator> --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint \
  --case-dir cases/sampleco/2026-0001 --operator-id <operator> --json

python scripts/approve_tabular_delivery.py --case-id 2026-0001 \
  --approve --by <operator> --json
```

### 4.3 Pass criteria (profile-aligned)

| Check | Expected |
|-------|----------|
| Gate | `eligibility=accepted` (no `--force` on clean) |
| Cleaning | 115 → 8 rows · `cleaning_profile_id=sampleco_order_profile` |
| `qa_status` | `pass_with_warnings` |
| `output_guard.status` | `warning` (ratio 0.0696 &lt; 0.5) |
| CP-A | `approved` · outbox under `outbox/sampleco/2026-0001/` |
| CP-B | `checkpoint_b_status=approved` · outbox `B-delivery-confirmation` written |
| `automation_status` | `completed` · `current_step=approved_for_delivery` |
| `overall_ok` | `true` — e2e step `completed` |
| `delivery_ready` | **`false`** (by design: output_guard warning blocks ready gate) |
| `delivery_approval_status` | `approved` recorded · signoff + index updated |
| Known limits | `multi_row_export` · `phase_dedup_semantics_unstable` · low accepted ratio |

> **Note**: For sampleco, **`delivery_ready=false` is expected** even after human CP-B approve. The chain is still considered E2E-pass when automation completes and profile metrics match `docs/tabular-cleaning-profiles-v1.md` §3.4.

---

## 5. Artifacts to inspect

| Artifact | Path pattern |
|----------|--------------|
| Control state | `cases/<case>/automation_state.json` |
| Run log | `cases/<case>/reports/automation_run_log.json` |
| Delivery approval | `cases/<case>/delivery_approval.json` |
| Outbox checkpoints | `outbox/<case_ref>/checkpoint_*.json` |
| Signoff | `cases/<case>/delivery_signoff.md` |
| Case index | `cases/index.json` |

---

## 6. When to re-run

Re-run this checklist after changes to:

- `scripts/tabular_automation_state_lib.py` · `manage_tabular_automation_state.py`
- `scripts/tabular_automation_driver_lib.py` · `run_tabular_automation.py`
- `scripts/tabular_hitl_resume_lib.py` · `run_hitl_checkpoint_cli.py`
- `scripts/tabular_delivery_approval_lib.py` · `approve_tabular_delivery.py`
- `hitl/checkpoint_*` · allowlist fixtures under `cases/`

Also run `python scripts/run_demo_phase_regression_smoke.py --json` on every main-chain change.

---

## 7. Related docs

| Doc | Purpose |
|-----|---------|
| `docs/tabular-mainline-e2e-verification-report-v1.md` | Latest executed report |
| `docs/tabular-mainline-progress-update-2026-06-27.md` | Latest mainline progress snapshot |
| `docs/tabular-mainline-progress-template.md` | Reusable template for future progress updates |
| `docs/tabular-demo_phase-regression-v1.md` | demo_phase one-command regression |
| `docs/tabular-cleaning-profiles-v1.md` | Profile expected outcomes |
| `docs/tabular-hitl-resume-flow-v1.md` | CP-A/B resume semantics |
| `docs/tabular-mainline-progress-template.md` | Progress update skeleton (copy for new dated snapshots) |
| `docs/mvp-mainline-regression.md` | Gate→clean→bundle (no HITL) regression |

---

*Tabular mainline E2E verification v1 · regression baseline for Batch 2+ planning*
