# P7 Resume-Loop G-1–G-5 Spec + Trace Contract (v1)

> **Ticket**: `W2-P7-matrix-G1-G5-resume-loop-v1`  
> **Wave**: Wave 2 · P7 · spec-only  
> **Authority**: behavior narrative aligns with `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §4 R-11–R-15 and `04_Workflows/reports/W6-standard-case-v2-closure-report.md`.

---

## Non-claims (read first)

**This document is a spec + trace contract only. It is NOT a runtime prod gate.**

- Does **not** claim G-1–G-5 gaps are closed or that dedicated orchestrator resume unittests exist.
- Does **not** claim resume-loop runs in staging or prod.
- Does **not** modify orchestrator, HITL, or notification runtime code.
- Does **not** substitute for MP-SMOKE gate steps 1–2 (P7.5 intake gate trace is separate).
- Machine-readable matrix: `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml`.

---

## 1. Scope

| In scope | Out of scope |
|----------|--------------|
| G-1–G-5 resume-loop **expected behavior** | G-6–G-13 (other matrix gaps) |
| Trigger conditions · blocked/terminal semantics | Staging POST · prod rollout |
| Trace field naming for observability | New orchestrator/resume runtime code |
| Cross-ref matrix R-11–R-15 · W-ORCH P7 lane | Dashboard · W-ORCH code changes |

**Orchestrator entry**: `scripts/run_agent_standard_case_experiment.py` with `--resume-checkpoint <path>` and `--mode run`.

**Validation function**: `validate_resume_eligibility()` in the same file.  
**Resume handler**: `_run_experiment_resume_from_checkpoint()`.

---

## 2. G-1–G-5 behavior matrix

### G-1 · stale_checkpoint (R-11)

| Field | Value |
|-------|-------|
| **Gap ID** | G-1 |
| **Matrix row** | R-11 |
| **Checkpoint** | A |
| **Trigger** | On-disk `status=awaiting_human` **and** `expires_at` is in the past; operator attempts `--resume-checkpoint` with `--mode run` **without** applying human decision |
| **Expected resume** | `ok=false`, `final_status=stale_checkpoint`; orchestrator **does not** enter S7/S13 |
| **Error / interrupt** | Message: `checkpoint expired before human decision`; no checkpoint mutation; no notification on resume attempt |
| **Trace fields** | `resume_eligibility=stale_checkpoint` |
| **Outbox artifact** | Logical path `outbox/checkpoints/<case_ref>/<checkpoint_id>.json` (existing file; not rewritten on failed resume) |
| **Related impl** | `validate_resume_eligibility()` when `status in ("awaiting_human",)` and `_checkpoint_expired(expires_at)` |
| **Unittest** | `planned impl` (no dedicated orchestrator test today) |

---

### G-2 · revise_needed resume blocked (R-12)

| Field | Value |
|-------|-------|
| **Gap ID** | G-2 |
| **Matrix row** | R-12 |
| **Checkpoint** | A |
| **Trigger** | Human applied `revise_plan` → on-disk `status=revise_needed`; operator attempts resume |
| **Expected resume** | `ok=false`, `final_status=blocked`; orchestrator **does not** resume |
| **Error / interrupt** | Message contains `checkpoint status='revise_needed'; v1 resume supports approved only` |
| **Trace fields** | `resume_eligibility=blocked`, `resume_blocked_reason=revise_needed` |
| **Outbox artifact** | Checkpoint JSON reflects `revise_needed`; no new resume marker |
| **Related impl** | `validate_resume_eligibility()` status branch for `revise_needed` |
| **Indirect coverage** | `test_human_decision_resume_plans` (subTest revise_plan), `test_resume_context_revise_plan_uses_gate` |
| **Unittest** | `planned impl` (orchestrator resume path) |

---

### G-3 · on_hold resume blocked (R-13)

| Field | Value |
|-------|-------|
| **Gap ID** | G-3 |
| **Matrix row** | R-13 |
| **Checkpoint** | B |
| **Trigger** | Human applied `hold` → on-disk `status=on_hold`; operator attempts resume |
| **Expected resume** | `ok=false`, `final_status=blocked`; orchestrator **does not** resume |
| **Error / interrupt** | Message contains `checkpoint status='on_hold'; v1 resume supports approved only` |
| **Trace fields** | `resume_eligibility=blocked`, `resume_blocked_reason=on_hold` |
| **CLI / integration boundary** | Hold path covered by delivery CLI and integration tests; **orchestrator resume** remains blocked in v1 |
| **Indirect coverage** | `test_delivery_plan_hold`, `test_hold_on_hold` |
| **Unittest** | `planned impl` (orchestrator resume path) |

---

### G-4 · missing checkpoint file (R-14)

| Field | Value |
|-------|-------|
| **Gap ID** | G-4 |
| **Matrix row** | R-14 |
| **Checkpoint** | Any |
| **Trigger** | `--resume-checkpoint` points to invalid or missing path |
| **Expected resume** | `ok=false`, `final_status=blocked`; load fails before eligibility validation |
| **Error / interrupt** | `FileNotFoundError` or `ValueError` from `load_checkpoint_for_resume`; `resume.ok=false` sub-object; **no** checkpoint artifact created |
| **Trace fields** | `checkpoint_load_error` (in message / `resume.message`), `resume_eligibility=blocked` |
| **Related impl** | `_run_experiment_resume_from_checkpoint()` try/except around `load_checkpoint_for_resume` |
| **Unittest** | `planned impl` |

---

### G-5 · non-allowlisted case resume (R-15)

| Field | Value |
|-------|-------|
| **Gap ID** | G-5 |
| **Matrix row** | R-15 |
| **Checkpoint** | A (approved) |
| **Trigger** | Checkpoint shows `status=approved` but CLI `case_ref` is **not** in W7-T2 allowlist |
| **Expected resume** | `ok=false`, `final_status=blocked`; **early block** before checkpoint load |
| **Error / interrupt** | `message=case_not_in_allowlist`; steps_run may only include `resume_checkpoint_load` |
| **Trace fields** | `case_allowlist_block=true`, `resume_eligibility=blocked` |
| **Related impl** | `is_allowlisted_case()` guard in `_run_experiment_resume_from_checkpoint()` |
| **Unittest** | `planned impl` |

---

## 3. Trace contract (resume vs gate)

### 3.1 Resume-loop trace fields (this spec)

| Field | When set | Semantics |
|-------|----------|-----------|
| `resume_eligibility` | Resume validation or early block | `stale_checkpoint` · `blocked` · (future) `approved` |
| `resume_blocked_reason` | Status-based block | `revise_needed` · `on_hold` · null when stale/load/allowlist |
| `checkpoint_path` | After resolve attempt | Logical outbox-relative path or unresolved |
| `checkpoint_load_error` | G-4 load failure | Error string from load layer |
| `case_allowlist_block` | G-5 | Boolean; true when allowlist rejects before load |
| `run.blocked` | Terminal blocked run | Notification event type when run ends blocked (reference only; not asserted by this spec) |

### 3.2 Gate trace SSOT (do not mix)

| SSOT | Status | Resume spec relationship |
|------|--------|--------------------------|
| `docs/p75-intake-gate-control-plane-trace-v1.md` (W1-P75-TRACE-UPSTREAM-v1) | **active** | Gate fields (`intake.gate_decision`, `gate_status`, `reason_codes`) apply to **MP-SMOKE steps 1–2** only |
| `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7.4 | active | MP-1/MP-2 **do not** cover G-1–G-5 |

**Rule**: Resume-loop observability rows MUST NOT reuse gate step 1–2 trace keys as proof of resume behavior.

### 3.3 Cross-references

| Artifact | Role |
|----------|------|
| `standard-case-hitl-resume-notify-matrix.md` §4 R-11–R-15 | Matrix rows |
| `standard-case-hitl-resume-notify-matrix.md` §9 G-1–G-5 | Gap registry + observability |
| `W6-standard-case-v2-closure-report.md` | Fail-close narrative |
| `W-ORCH-wave-next-control-plane-v1` P7 lane | Control-plane index (read-only) |
| `p7-resume-loop-g1-g5-matrix-v1.yaml` | Machine-readable contract |

---

## 4. Test matrix appendix (scenario rows)

| Row | Gap | Input state | Expected orchestrator conclusion | Observability | Verify |
|-----|-----|-------------|----------------------------------|---------------|--------|
| M-G1 | G-1 | CP-A `awaiting_human`, expired `expires_at`, `--mode run` | `stale_checkpoint`, no S7 | `resume_eligibility=stale_checkpoint` | `rg "G-1" docs/p7-resume-loop-g1-g5-spec-v1.md` |
| M-G2 | G-2 | CP-A `revise_needed` after `revise_plan` | `blocked`, no resume | `resume_blocked_reason=revise_needed` | `rg "G-2" docs/p7-resume-loop-g1-g5-spec-v1.md` |
| M-G3 | G-3 | CP-B `on_hold` after `hold` | `blocked`, no resume | `resume_blocked_reason=on_hold` | `rg "G-3" docs/p7-resume-loop-g1-g5-spec-v1.md` |
| M-G4 | G-4 | Missing `--resume-checkpoint` path | `blocked`, load error | `checkpoint_load_error` | `rg "G-4" docs/p7-resume-loop-g1-g5-spec-v1.md` |
| M-G5 | G-5 | Approved CP-A, non-allowlisted `case_ref` | `blocked`, early allowlist | `case_allowlist_block` | `rg "G-5" docs/p7-resume-loop-g1-g5-spec-v1.md` |

---

## 5. Verification commands

```bash
# Spec + matrix keyword presence
rg "G-1|G-2|G-3|G-4|G-5|stale_checkpoint|resume_eligibility|resume_blocked_reason" \
  docs/p7-resume-loop-g1-g5-spec-v1.md \
  04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md

# W1-T5 / W1-P75-TRACE cross-ref (gate trace SSOT — active)
rg "W1-P75-TRACE|p75-intake-gate-control-plane-trace" docs/p7-resume-loop-g1-g5-spec-v1.md

# Matrix schema structural verify (this ticket)
python scripts/verify_g_matrix.py

# Existing HITL regression (reference only — NOT G-1–G-5 closure evidence)
python -m unittest tests.test_hitl_checkpoints_v1 -v
```

---

## 6. References

| Artifact | Path |
|----------|------|
| YAML matrix | `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml` |
| Verify script | `scripts/verify_g_matrix.py` |
| Orchestrator | `scripts/run_agent_standard_case_experiment.py` |
| Closure report | `04_Workflows/reports/W6-standard-case-v2-closure-report.md` |
| Gate trace SSOT | `docs/p75-intake-gate-control-plane-trace-v1.md`（W1-P75-TRACE-UPSTREAM-v1 · **active**） |
| WORKFLOW_INDEX | §1.45 末「P7 resume-loop G-1–G-5」一句 |

## Changelog

| Date | Note |
|------|------|
| 2026-06-26 | Initial spec + YAML + matrix §9 · `done_with_gaps`（`pending_w1_t5`） |
| 2026-07-09 | AC-6 gap closed：gate SSOT **active**（W1-P75-TRACE done）· INDEX 一句 · STATE → `done`；G-* runtime unittest 仍 `planned impl`（AC-8） |
