# Tabular Tri-Case HITL Matrix v1

> **Ticket**: TAB-S5-WS-A-T3 · WS-A  
> **Status**: v1 · spec-only · **非** prod gate · **非** closure 宣稱  
> **Machine-readable SSOT**: [`docs/tabular-tri-case-hitl-matrix-v1.yaml`](tabular-tri-case-hitl-matrix-v1.yaml)  
> **Drift verify**: `python scripts/verify_tabular_tri_case_hitl_matrix.py` · `tests/test_tabular_tri_case_hitl_matrix_v1.py`

**Authority chain**: `scripts/tabular_regression_smoke_lib.py` → `verify_case_regression()` · `scripts/run_tabular_mainline_regression_smoke.py` → `SMOKE_CASES` · HITL flow → `docs/tabular-hitl-resume-flow-v1.md` · guard policy → `scripts/tabular_warning_guard_lib.py`

---

## 1. Purpose

Freeze **smoke terminal states** for the three Tabular main-chain regression anchors after Gate 2 (`run_tabular_mainline_regression_smoke.py`) completes. WS-B / T5 / T4 / T1 queue behind this matrix.

**Non-goals (this doc)**:

| Non-goal | Notes |
|----------|-------|
| Prod gate / Phase% / closure | Batch 1 `hard_no` still applies |
| 7×24 no-HITL | v1 retains CP-A/B design |
| Prod notification | Internal notify hook remains placeholder |
| Driver / DLQ behavior change | T3 is document + contract drift only |

---

## 2. Regression gates (T3 cross-ref)

| Layer | Command | Scope |
|-------|---------|-------|
| **Gate 1** | `python scripts/run_demo_phase_regression_smoke.py --json` | Single-case HITL smoke anchor |
| **Gate 2** | `python scripts/run_tabular_mainline_regression_smoke.py --json` | Tri-case main-chain smoke |
| **Gate 3** | `python scripts/run_mvp_mainline_regression.py -v` | Gate→clean→bundle E2E (no control plane) |
| **Contract** | `python -m unittest tests.test_tabular_tri_case_hitl_matrix_v1 -v` | YAML / SMOKE_CASES drift (does **not** replace Gate 3) |

See also `docs/TABULAR_MVP_SSOT.md` §5 (Gate 1–2); Gate 3 + contract row added here for T3.

---

## 3. Main matrix — smoke terminal states only

Fields mirror [`tabular-tri-case-hitl-matrix-v1.yaml`](tabular-tri-case-hitl-matrix-v1.yaml) `entries.*`. Values must satisfy `verify_case_regression()` after Gate 2.

| case_id | case_dir | force_driver | expected_delivery_ready | cleaning_profile_id | gate_status | output_guard.status | checkpoint_a_status | checkpoint_b_status | current_step | automation_status | dlq_status |
|---------|----------|--------------|-------------------------|---------------------|-------------|---------------------|---------------------|---------------------|--------------|-------------------|------------|
| `demo_phase` | `cases/demo_phase` | `true` | `true` | `phase_demo_v1` | `review_needed` | `ok` | `approved` | `approved`¹ | `delivery` | `completed` | `none` |
| `2026-0001` | `cases/sampleco/2026-0001` | `false` | `false` | `sampleco_order_profile` | `accepted` | `warning` | `approved` | `approved` | `delivery` | `completed` | `none` |
| `generic-low-risk` | `cases/internal/generic-low-risk` | `false` | `true` | `generic_low_risk_profile` | `review_needed` | `ok` | `approved` | `approved` | `delivery` | `completed` | `none` |

¹ `verify_case_regression` also accepts `checkpoint_b_status=not_required` when CP-B auto-skips; see §5 appendix.

### verify_assertions (summary)

All three cases share the smoke-lib rule set (full strings in YAML):

- `automation_status=completed`
- `checkpoint_a_status ∈ {approved, not_required}`
- `checkpoint_b_status ∈ {approved, not_required}` (+ run-log `checkpoint_b` completed when `not_required`)
- `current_step ∈ {checkpoint_b, delivery, approved_for_delivery}`
- `expected_delivery_ready` per case (see table)
- `e2e` step `completed` in `reports/automation_run_log.json`
- Artifacts: `report.json`, `delivery_signoff.md`, `cleaned/*_cleaned.csv`

---

## 4. WS-B boundary (readonly)

| Field / concept | T3 stance | WS-B constraint |
|-----------------|-----------|-----------------|
| `dlq_status` · `dlq/` entries | Terminal `none` on tri-case smoke happy path | **Must not** rewrite stuck/DLQ semantics before matrix freeze; fleet aggregation display only |
| `stuck` · `pause_reason` intermediate states | Appendix narrative only | Dashboard/triage must align with §3 terminal states |
| Run-log `checkpoint_b.awaiting_hitl` vs `automation_state` | Known P2 — E2E report §6 | Document only; driver fix deferred to **T7** |

**References (do not copy implementation)**:

- `scripts/tabular_warning_guard_lib.py` — guard → `delivery_ready`
- `docs/tabular-cleaning-automation-manifest-v1.md` §1.9 — DLQ collect-only
- `docs/tabular-mainline-e2e-verification-report-v1.md` §6 — P2 items

---

## 5. Appendix — smoke path notes (non-contract)

Narrative only; **not** hard drift assertions in `verify_tabular_tri_case_hitl_matrix.py`.

### `demo_phase`

- `force_driver=true` in smoke registry bypasses CP-A pause.
- Without `--force`, driver pauses at CP-A (`review_needed` gate).
- CP-B may **auto-skip** → terminal `checkpoint_b_status=not_required` when `output_guard.status=ok`.
- Regression smoke may also end with `checkpoint_b_status=approved` after approve-b path; both pass verify.

### `2026-0001`

- `force_driver=false`; CP-A and CP-B both HITL in smoke.
- `output_guard.status=warning` → `expected_delivery_ready=false` by design (`partial_ready_internal_only`).

### `generic-low-risk`

- `force_driver=false`; gate `review_needed` (rows&lt;100).
- Terminal CP-A/B **both `approved`** per anchor `automation_state.json` after Gate 2 — **not** demo CP-B auto-skip narrative.

---

## 6. Known limits

| ID | Description | Disposition |
|----|-------------|-------------|
| `run_log_cp_b_awaiting_hitl_vs_state` | Run log may show CP-B awaiting HITL while state shows `approved` | Document only · T7 |
| `pause_intermediate_states` | `awaiting_checkpoint_a` etc. | Runtime smoke only; excluded from YAML main table |

---

## 7. Freeze statement

When `verify_tabular_tri_case_hitl_matrix.py` returns `ok: true` and Gates 1–3 pass, matrix semantics are **frozen** for:

- **WS-B** — stuck/DLQ fleet views (readonly fields in YAML `extensions.ws_b_boundary`)
- **T5 / T4 / T1** — queued until freeze confirmed

---

*TAB-S5-WS-A-T3 · Tabular tri-case HITL matrix · spec-only · 2026-07-01*
