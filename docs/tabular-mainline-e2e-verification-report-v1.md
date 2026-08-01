# Tabular Mainline E2E Verification Report v1

> **Date**: 2026-06-27  
> **Verifier role**: Tabular Mainline E2E Verifier  
> **Checklist**: `docs/tabular-mainline-e2e-verification-v1.md`  
> **Operator**: `e2e_verifier`

---

## 1. Executive summary

The Tabular cleaning main chain was executed end-to-end on both low-risk allowlist cases using the control plane CLI, unified driver, HITL checkpoint CLIs, and delivery approve CLI.

| Verdict | Detail |
|---------|--------|
| **Main line status** | **`tabular_mainline_e2e_ready: true_with_known_limits`** |
| **Anchor case (`demo_phase`)** | Full pass — automation completed, `delivery_ready=true` |
| **Second case (`sampleco/2026-0001`)** | Chain pass — profile metrics match; `delivery_ready=false` by design (`output_guard.warning`) |
| **Fix applied during verification** | Unified driver CP-B now writes outbox state (`write_state=True`) and uses consistent `case_ref` (`sampleco/2026-0001`) so `approve-b` CLI works |

---

## 2. Cases and profiles

| Case dir | Profile | Gate | Cleaning outcome |
|----------|---------|------|------------------|
| `cases/demo_phase` | `phase_demo_v1` | `review_needed` | 7 → 5 rows · ratio 0.7143 · guard `ok` |
| `cases/sampleco/2026-0001` | `sampleco_order_profile` | `accepted` | 115 → 8 rows · ratio 0.0696 · guard `warning` |
| `cases/internal/generic-low-risk` | `generic_low_risk_profile` | `review_needed` | 7 → 5 rows · ratio ≈ 0.7143 · guard `ok` |

---

## 3. `demo_phase` — step results

| Step | Result | Notes |
|------|--------|-------|
| Control plane `start --restart` | **PASS** | `automation_status=running` |
| Driver → CP-A (no `--force`) | **PASS** | Paused at `checkpoint_a` · `awaiting_hitl` |
| `approve-a` | **PASS** | Outbox: `outbox/demo_phase/checkpoint_A-*.json` |
| `resume-after-checkpoint` | **PASS** | Ran clean → report → bundle → e2e |
| Cleaning / stats | **PASS** | `phase_demo_v1` · 7→5 · `pass_with_warnings` |
| Bundle + e2e | **PASS** | `e2e` step `completed` · `output_guard.status=ok` |
| CP-B | **PASS (auto-skip)** | `checkpoint_b_status=not_required` · `skip_reason=ok_no_human_gate` |
| `approve_tabular_delivery --approve` | **PASS** | `delivery_ready=true` · signoff + index updated |
| **Final state** | **PASS** | `automation_status=completed` · `overall_ok=true` · `delivery_ready=true` |

**Cross-check:** `python scripts/run_demo_phase_regression_smoke.py --json` → exit 0 · `"ok": true`.

---

## 4. `sampleco/2026-0001` — step results

| Step | Result | Notes |
|------|--------|-------|
| Control plane `start --restart` | **PASS** | |
| Driver → CP-A | **PASS** | Paused · risk signals: `multi_row_export`, `schema_ambiguous` |
| `approve-a` + resume | **PASS** | Gate `accepted`; clean without `--force` |
| Cleaning / stats | **PASS** | 115→8 matches profile §3.4 |
| Bundle + e2e | **PASS** | `e2e` completed · guard `warning` as expected |
| CP-B pause | **PASS** | Human gate triggered on `output_guard.warning` |
| `approve-b` + resume | **PASS** | After driver fix; `checkpoint_b_status=approved` · `current_step=approved_for_delivery` |
| `approve_tabular_delivery --approve` | **PASS (partial gate)** | `delivery_approval_status=approved` · **`delivery_ready=false`** (guard warning) |
| **Final state** | **PASS (profile-aligned)** | `automation_status=completed` · e2e OK · known low accepted ratio |

### 4.1 Profile alignment

| Metric | Expected (profile doc) | Observed |
|--------|--------------------------|----------|
| Input rows | 115 | 115 |
| Output rows | 8 | 8 |
| `qa_status` | `pass_with_warnings` | `pass_with_warnings` |
| Gate | `accepted` | `accepted` |
| CP-B HITL | Required on warning guard | Triggered and approved |
| `delivery_ready` | Not claimed for marginal quality | `false` (correct) |

---

## 5. `generic-low-risk` — generic profile case (2026-06-27)

| Step | Result | Notes |
|------|--------|-------|
| E2E validation | **PASS** | `run_case_e2e_validation.py --case-dir cases/internal/generic-low-risk` |
| Profile | **PASS** | `cleaning_profile_id=generic_low_risk_profile` |
| Cleaning | **PASS** | 7 → 5 rows · dedup by `order_id` · numeric range flags |
| Gate | **PASS** | `review_needed` (rows&lt;100) · forced clean in E2E |
| `output_guard` | **PASS** | `ok` (ratio ≥ 0.5) |

**Purpose**: Validates schema-driven generic profile path (`clean.generic` runner) for future low-risk cases without Phase-specific columns.

---

## 6. Issues found and disposition

| Issue | Severity | Disposition |
|-------|----------|-------------|
| CP-B used `write_state=False` in unified driver → `approve-b` could not find outbox checkpoint | **P1 (fixed)** | Changed to `write_state=True` in `tabular_automation_driver_lib._step_checkpoint_b` |
| CP-B `case_ref` was client slug (`sampleco`) vs nested path (`sampleco/2026-0001`) | **P1 (fixed)** | Use `case_ref_from_case_dir()` for execution summary |
| After `approve-b`, run log still shows `checkpoint_b.awaiting_hitl`; delivery readiness does not read `automation_state.checkpoint_b_status` | **P2 (follow-up)** | Document only; does not block automation completion |
| `delivery_ready=false` on sampleco despite human approve | **By design** | `output_guard.warning` blocks ready gate per `tabular_delivery_approval_lib` |

---

## 7. Conclusion

**The Tabular main line is usable** for low-risk allowlist cases: intake → gate → HITL → clean → bundle → e2e → delivery approve can be repeated with documented CLIs.

- **`demo_phase`**: Suitable as regression anchor and full delivery-ready path.
- **`sampleco/2026-0001`**: Validates near-real export semantics, CP-B human gate, and marginal-quality guardrails; not suitable as a “delivery_ready=true” exemplar until profile / dedup rules improve.

- **`generic-low-risk`**: Validates `generic_low_risk_profile` for simple key+numeric tables; suitable template for new internal cases.

---

## 8. Recommended follow-up (Batch 2+)

1. Sync run-log `checkpoint_b` step status after `approve-b`, or teach `evaluate_delivery_readiness` to honor `automation_state.checkpoint_b_status=approved`.
2. Add `scripts/run_sampleco_mainline_regression_smoke.py` (or generalize smoke runner for both allowlist cases).
3. Extend unit tests for driver CP-B outbox write + nested `case_ref` resolution.
4. Product decision: whether human CP-B approve on `output_guard.warning` should ever set `delivery_ready=true` (override gate) vs remain fail-closed.

---

## 9. Verification commands (evidence)

```bash
# demo_phase manual E2E (2026-06-27)
python scripts/manage_tabular_automation_state.py start --case-dir cases/demo_phase --requested-by e2e_verifier --restart --json
python scripts/run_tabular_automation.py --case-id demo_phase --json
python scripts/run_hitl_checkpoint_cli.py approve-a --case-id demo_phase --operator-id e2e_verifier --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint --case-id demo_phase --operator-id e2e_verifier --json
python scripts/approve_tabular_delivery.py --case-id demo_phase --approve --by e2e_verifier --json

# sampleco manual E2E (2026-06-27)
python scripts/manage_tabular_automation_state.py start --case-dir cases/sampleco/2026-0001 --requested-by e2e_verifier --restart --json
python scripts/run_tabular_automation.py --case-dir cases/sampleco/2026-0001 --json
python scripts/run_hitl_checkpoint_cli.py approve-a --case-dir cases/sampleco/2026-0001 --operator-id e2e_verifier --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint --case-dir cases/sampleco/2026-0001 --operator-id e2e_verifier --json
python scripts/run_hitl_checkpoint_cli.py approve-b --case-dir cases/sampleco/2026-0001 --operator-id e2e_verifier --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint --case-dir cases/sampleco/2026-0001 --operator-id e2e_verifier --json
python scripts/approve_tabular_delivery.py --case-id 2026-0001 --approve --by e2e_verifier --json

# generic profile case (2026-06-27)
python scripts/run_case_e2e_validation.py --case-dir cases/internal/generic-low-risk --json

# Regression cross-check
python scripts/run_demo_phase_regression_smoke.py --json
python -m unittest tests.test_tabular_automation_driver tests.test_tabular_hitl_resume tests.test_approve_tabular_delivery -q
python -m unittest tests.test_tabular_automation_retry_dlq -q
```

---

## 9. Retry & DLQ verification summary

Unit tests (`tests/test_tabular_automation_retry_dlq.py`) validate driver retry/DLQ wiring without touching production cases.

| Scenario | Expected behavior | Result |
|----------|-------------------|--------|
| **Transient I/O** (`resource temporarily unavailable`) | 4 attempts (1 initial + 3 retries) · backoff mocked · `retry_count=3` · `dlq_status=queued` | **PASS** |
| **Transient then success** (fail once, succeed on 2nd) | `attempt=2` · no DLQ · `dlq_status=none` | **PASS** |
| **Persistent schema/report** (`missing report artifacts`) | 0 retries · immediate DLQ · `failure_class=immediate_dlq` | **PASS** |
| **Classification lib** | `is_transient_error` · `classify_step_failure` · `enqueue_dlq` index + entry | **PASS** |

**Run log step fields verified**: `attempt` · `error_if_any` · `dlq_if_any` · `retry_attempts[]` · state mirror (`retry_count` · `last_error_at` · `dlq_status`).

**DLQ location**: `cases/<case>/dlq/dlq.json` (index) + `cases/<case>/dlq/<entry_id>.json` (detail). Collect-only — no auto re-run.

**Evidence command**:

```bash
python -m unittest tests.test_tabular_automation_retry_dlq -v
```

---

*Report v1 · Tabular mainline E2E verification · 2026-06-27*
