# Tabular `demo_phase` Regression Guard v1

> **Purpose**: Minimum regression anchor for the Tabular **main chain** (control plane + unified driver + HITL + delivery approve).  
> **Case**: `cases/demo_phase/` · **Authority**: `docs/C2-P2_RUNBOOK.md` · `docs/tabular-hitl-resume-flow-v1.md` · `docs/TABULAR_MVP_SSOT.md`

---

## 1. When to run

Re-run **`scripts/run_demo_phase_regression_smoke.py`** after **any** change touching:

| Area | Typical paths |
|------|----------------|
| Automation state / control plane | `scripts/tabular_automation_state_lib.py`, `scripts/manage_tabular_automation_state.py` |
| Unified driver | `scripts/tabular_automation_driver_lib.py`, `scripts/run_tabular_automation.py` |
| HITL resume | `scripts/tabular_hitl_resume_lib.py`, `scripts/run_hitl_checkpoint_cli.py`, `hitl/checkpoint_*` |
| Delivery approve | `scripts/tabular_delivery_approval_lib.py`, `scripts/approve_tabular_delivery.py` |
| Gate / clean / bundle (when wired into driver) | `scripts/check_case_eligibility.py`, `notebooks/csv_cleaning/clean_phase_demo.py`, `scripts/build_case_delivery_bundle.py` |
| `demo_phase` fixture | `cases/demo_phase/**` |

**Not a substitute for** `scripts/run_mvp_mainline_regression.py` (gate→clean→bundle E2E only, no HITL/control plane). Run **both** before Tabular main-chain releases.

---

## 2. Expected flow (full main chain)

```text
start (control plane)
  → gate (eligibility)
  → CP-A (HITL pause)
  → resume (after approve-a)
  → clean
  → stats (report)
  → bundle
  → e2e
  → CP-B (HITL pause)
  → resume (after approve-b)
  → delivery approve (Lead CLI)
```

Driver step order (canonical names):  
`intake` → `eligibility` → `checkpoint_a` → `cleaning` → `report` → `bundle` → `e2e` → `checkpoint_b`

Human decisions in regression smoke (automated by the CLI):

1. `approve-a` + `resume-after-checkpoint`
2. `approve-b` + `resume-after-checkpoint`
3. `approve_tabular_delivery --approve`

---

## 3. Key artifacts

| Artifact | Path | Role |
|----------|------|------|
| Control state | `cases/demo_phase/automation_state.json` | `automation_status`, checkpoint fields, `current_step` |
| Run log | `cases/demo_phase/reports/automation_run_log.json` | Per-step audit; **e2e** step must be `completed` |
| Delivery approval | `cases/demo_phase/delivery_approval.json` | `delivery_ready`, `delivery_approval_status` |
| Gate result | `cases/demo_phase/reports/eligibility_result.json` | `review_needed` expected for demo |
| Cleaned CSV | `cases/demo_phase/cleaned/*_cleaned.csv` | 7 → 5 rows (reference) |
| Reports | `cases/demo_phase/reports/report.json`, `report.md`, `cleaning_stats.json` | QA + output_guard |
| Signoff | `cases/demo_phase/delivery_signoff.md` | Updated on delivery approve |

---

## 4. Pass criteria (smoke output)

The regression CLI sets **`ok: true`** only when all of the following hold:

| Check | Expected |
|-------|----------|
| `automation_status` | `completed` |
| `current_step` | `checkpoint_b` · `delivery` · or `approved_for_delivery` (CP-B HITL path) |
| `overall_ok` | `true` — composite: `e2e` step `completed` in run log + CP-A approved |
| `delivery_ready` | `true` in `delivery_approval.json` after `--approve` |
| CP-B | `checkpoint_b_status=approved` (HITL path) **or** `not_required` with run-log `checkpoint_b` `completed` (auto-skip when guard ok) |
| Core artifacts | cleaned CSV, `report.json`, `delivery_signoff.md` present |

**Note on run log `ok`**: The top-level `automation_run_log.json` → `ok` may be `false` on the **last driver invocation** when that run paused at CP-B (`awaiting_hitl`). That is normal. The smoke **`overall_ok`** field is the regression gate, not the raw run-log flag.

---

## 5. How to run

### One command (recommended)

```bash
python scripts/run_demo_phase_regression_smoke.py --json
```

Human-readable summary:

```bash
python scripts/run_demo_phase_regression_smoke.py
```

Plan only (no subprocess mutations):

```bash
python scripts/run_demo_phase_regression_smoke.py --dry-run --json
```

**Success**: exit code `0`; JSON includes `"ok": true`.  
**Failure**: exit code `1`; JSON includes `"ok": false` and `failures[]`.

---

## 6. Manual reference (debug)

```bash
python scripts/manage_tabular_automation_state.py start \
  --case-dir cases/demo_phase --requested-by operator --restart --json

python scripts/run_tabular_automation.py --case-id demo_phase --json

python scripts/run_hitl_checkpoint_cli.py approve-a --case-id demo_phase --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint --case-id demo_phase --json

python scripts/run_hitl_checkpoint_cli.py approve-b --case-id demo_phase --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint --case-id demo_phase --json

python scripts/approve_tabular_delivery.py --case-id demo_phase --approve --by lead --json
```

Skip-HITL internal demo bypass ( **not** this regression): `--force` on `run_tabular_automation.py`.

---

## 7. First steps when smoke fails

1. Re-run with `--json` and read `failures` / `phases`.
2. Inspect `automation_state.json` → `last_error`, `pause_reason`, checkpoint statuses.
3. Inspect `reports/automation_run_log.json` → last failed / `awaiting_hitl` step.
4. Re-run a single step manually (see §6) from the first red step.
5. If fixture drift (row counts, guard thresholds), update `cases/demo_phase` reports **and** smoke assertions together.

---

## 8. Related docs / runners

| Doc / runner | Scope |
|--------------|--------|
| `scripts/run_mvp_mainline_regression.py` | Gate→clean→bundle E2E (`demo_phase` + `sampleco`) |
| `docs/mvp-mainline-regression.md` | MVP mainline regression guard |
| `docs/tabular-hitl-resume-flow-v1.md` | CP-A/B resume semantics |
| `docs/C2-P2_RUNBOOK.md` §3.3 | Automation mode runbook |
