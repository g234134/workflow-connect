# Standard-Case Pipeline Change — Quality Self-Assessment Checklist

> **Audience**: Implementer, Reviewer, Process Engineer  
> **Applies to**: Changes on the **agent standard-case experiment line** (`scripts/run_agent_standard_case_experiment.py`) and its HITL / resume / notify adjacency (`hitl/*`, `delivery/notification_gateway_v1.py`, delivery approval CLI).  
> **Derived from**: W6 checkpoint batch (T5, T6, T10 wiring, T10 gateway, T11) and W7 fixture extension patterns.  
> **Usage**: Copy into ticket B_REPORT or mark yes/no before Reviewer sign-off. **All items should be yes** unless explicitly deferred with ticket reference.

**Reference artifacts**

| Artifact | Path |
|----------|------|
| Closure report (W6 v2) | `04_Workflows/reports/W6-standard-case-v2-closure-report.md` |
| HITL / resume / notify test matrix | `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` |
| Checkpoint A integration | `hitl/checkpoint_a_integration_v1.py` · `docs/checkpoint-a-integration-v1.md` |
| Checkpoint B integration | `hitl/checkpoint_b_integration_v1.py` · `docs/checkpoint-b-integration-v1.md` |
| Orchestrator | `scripts/run_agent_standard_case_experiment.py` |
| Notification gateway | `delivery/notification_gateway_v1.py` |

---

## How to use

1. **Design** — complete before coding (or before merge if design-only ticket).
2. **Implementation** — self-check during PR / B_REPORT.
3. **Testing** — attach command output to ticket §4 verification.
4. **Docs** — Scribe / Implementer before `accepted` or `accepted_with_gaps`.

Mark each line: `[ ]` no · `[x]` yes · `[~]` deferred (cite follow-up ticket in notes).

---

## Design

| # | Check item | W6/W7 anchor |
|---|------------|--------------|
| D-1 | **Fail-close vs best-effort** is explicitly defined for every new surface (resume / eligibility = fail-close; notifications = best-effort; orchestrator `ok` unchanged on notify failure). | Closure report §Reliability and Safety |
| D-2 | Ticket **FRAME** lists Goal, Scope, **NonScope**, AllowedPaths, and BlockedPaths before implementation starts. | W6-T5/T6/T10/T11 FRAME |
| D-3 | **B_REPORT** (and **C_REPORT** if reviewed) records `changed_files`, verification commands, skeleton/placeholder, and blocked/next. | Engineering contract Work Report |
| D-4 | **Preview vs run** semantics are documented: preview → `would_pause` / `would_trigger`, no default outbox writes; run → durable checkpoint files; resume requires run mode. | W6-T10 wiring AC-4 · W6-T11 |
| D-5 | **SSOT placement** is decided: checkpoint trigger/payload/resume logic lives in **integration layers**; orchestrator only maps integration `dict` results (no duplicated inline builders). | W6-T10 orchestrator-checkpoint-wiring |
| D-6 | **HITL schema** remains compatible with W5-T2B (`schema_version=hitl_checkpoint_v1`) or documents a version bump + migration. | W6-T5 AC-1 · W6-T6 AC-1 |
| D-7 | **Resume v1 scope** is documented: approved-only (`approve` / `approve_delivery`); `revise_plan` / `request_changes` / `hold` / `reject` are fail-close entry points. | W6-T11 NonScope · closure report |
| D-8 | **Checkpoint persistence** is outbox-only; change does **not** mutate `cases/index.json` or production main-chain state. | W6-T5 AC-5 · W6-T6 AC-4 |
| D-9 | **`checkpoint_path` semantics** define three-tier fallback (repo-relative → outbox-relative → absolute) when outbox is outside repo root. | W6-T5/T6 outbox-root fix |
| D-10 | **Notification gateway** default is off; enablement via `--enable-notifications` and/or `GOV_NOTIFICATION_GATEWAY_ENABLED=1`; emits only in `mode=run` when enabled. | W6-T10 client-notification-gateway |
| D-11 | **Intentional v1 gaps** and known limitations are listed (not silently deferred): e.g. no webhook dispatch, no revise resume, duplicate notify idempotency, approved checkpoint expiry behavior. | Closure report §Known Limitations |
| D-12 | **Human decision contract** maps CLI actions to integration `resume_plan` / `delivery_plan` APIs (`approve` / `revise_plan` / `reject`; `approve_delivery` / `request_changes` / `hold`). | W6-T5 AC-4 · W6-T6 AC-3 · matrix §5 |

---

## Implementation

| # | Check item | W6/W7 anchor |
|---|------------|--------------|
| I-1 | Orchestrator checkpoint steps (S4 / S12) call **integration public APIs only** — no inline payload builders or dynamic import of checkpoint logic. | W6-T10 wiring scope |
| I-2 | **`hitl/checkpoints_v1.py`** core schema / `record_human_decision` contract is **not** changed without a separate authorized ticket. | W6-T10 BlockedPaths |
| I-3 | **`--auto-approve-intake`** / **`--auto-approve-delivery`** are delegated to integration layers; no orchestrator-only bypass that duplicates SSOT (`bypass_reason` anti-pattern removed). | W6-T10 SSOT cleanup |
| I-4 | **Preview mode** does not write checkpoint JSON to outbox by default; orchestrator surfaces `would_pause` / `would_trigger`. | W6-T10 AC-4 |
| I-5 | **Run mode** with HITL pause stops before downstream execution (`waiting_for_human` / `stopped_before_delivery`) without silently continuing S7/S13. | W6-T5 AC-2 · W6-T11 AC-4 |
| I-6 | **`--resume-checkpoint`** loads JSON, runs **`validate_resume_eligibility()`**, and fail-closes with explicit `message` + `final_status` on any invalid state. | W6-T11 AC-3 |
| I-7 | **Resume requires `--mode run`**; preview + resume is blocked. | W6-T11 P3 · matrix R-4 |
| I-8 | **Resume does not re-run** skipped steps (A: S3–S6; B: S7–S12) and does not rewrite pending checkpoint files. | W6-T11 AC-4 |
| I-9 | **Notifications** go through gateway **`emit_notification_safe()`** (or equivalent); exceptions never propagate to orchestrator main flow. | W6-T10 AC-3 |
| I-10 | **Notification sink failure** does not downgrade orchestrator `ok` or terminal `final_status`. | W6-T10 gateway design |
| I-11 | **Notifications** are suppressed in preview and when gateway is disabled (zero side effects by default). | matrix N-1 · N-4 |
| I-12 | Orchestrator result includes **`checkpoint_*_status.integration_layer`** (or equivalent) marking `hitl.checkpoint_*_integration_v1` provenance. | W6-T10 B_REPORT artifacts |
| I-13 | **Evil-path / boundary guard**: checkpoint writes rejected outside allowed outbox roots (no writes under `cases/` etc.). | W6-T5 AC-5 · integration evil-path tests |
| I-14 | **BlockedPaths** respected: no unauthorized edits to main-chain scripts, Local UI, production delivery bundle builder, dark `core/`, `.env`, `runtime/checkpoints/**`. | W6-T6 NonScope · W7-T1 BlockedPaths |
| I-15 | **Checkpoint B duplicate delivery** is guarded (outbox marker or documented idempotency) on second `--resume-checkpoint`. | W6-T11 P3 R3 · matrix R-9 |
| I-16 | **External outbox** (`--outbox-root` outside repo) passes through to integration; path fallback handled in integration layer (no fragile orchestrator redirect unless documented). | W6-T5/T6 outbox-root fix |
| I-17 | **Registry fail-close** at selector/S6 prevents checkpoint A/B file creation when registry blocks run path. | matrix X-1 · orchestrator tests |
| I-18 | **Fixture / allowlist extension** (W7-style) marks new cases as **experiment-line only** and does not widen production decision allowlist. | W7-T1 NonScope |

---

## Testing

| # | Check item | W6/W7 anchor |
|---|------------|--------------|
| T-1 | **`tests.test_checkpoint_a_integration_v1`** passes (payload, awaiting_human write, auto-approve skip, human actions, evil outbox, external outbox). | W6-T5 · 9 tests |
| T-2 | **`tests.test_checkpoint_b_integration_v1`** passes (trigger rules, delivery plans, evil outbox, external outbox). | W6-T6 · 11 tests |
| T-3 | **`tests.test_agent_standard_case_experiment`** passes (full orchestration regression including wiring changes). | W6-T10 AC-5 · 43+ tests |
| T-4 | **`tests.test_notification_gateway_v1`** passes if notify surface touched (schema, disabled, dry_run, sink failure, safe emit, human approve). | W6-T10 gateway · 23 tests |
| T-5 | **Forward CP-A**: `needs_review` run → checkpoint file written + `waiting_for_human`. | matrix A-F4 |
| T-6 | **Forward CP-A**: `--auto-approve-intake` → **no** checkpoint A file + `resume_plan` / `auto_approved`. | matrix A-F5/F6 |
| T-7 | **Forward CP-B**: output_guard `warning` → checkpoint B written via W6-T6 integration. | matrix B-F2/F8 |
| T-8 | **Forward CP-B**: `ok` + `--auto-approve-delivery` → checkpoint B skipped. | matrix B-F4/F9 |
| T-9 | **Preview**: no outbox checkpoint writes by default (`would_pause` / `would_trigger` only). | matrix A-F3 · W6-T10 AC-4 |
| T-10 | **Custom outbox outside repo**: checkpoint write succeeds without `ValueError` on `checkpoint_path`. | W6-T5/T6 external outbox tests |
| T-11 | **Resume happy path A**: approved CP-A → `--resume-checkpoint` → S7+ execution. | matrix R-1 |
| T-12 | **Resume happy path B**: approved CP-B + `approve_delivery` → S13 delivery / export. | matrix R-2 |
| T-13 | **Resume fail-close**: `awaiting_human` (no human decision yet) → `blocked`. | matrix R-3 |
| T-14 | **Resume fail-close**: preview mode + resume → `blocked`. | matrix R-4 |
| T-15 | **Resume fail-close**: `case_ref` or `task_type` mismatch → `checkpoint_mismatch`. | matrix R-5/R-6 |
| T-16 | **Resume fail-close**: `rejected` status, wrong human action, **duplicate B delivery**, **stale/missing delivery artifacts**. | matrix R-7/R-8/R-9/R-10 |
| T-17 | **Human decisions**: integration tests cover A (`approve`/`revise_plan`/`reject`) and B (`approve_delivery`/`request_changes`/`hold`) plans. | matrix §5 H-1–H-6 |
| T-18 | **Notifications disabled** (default): no notification files; orchestrator `ok` unchanged. | matrix N-1 |
| T-19 | **Notifications enabled + run**: per-event files + `notification_events.jsonl` append. | matrix N-3 |
| T-20 | **Notifications dry_run / sink failure / exception**: error dict or skip; **no raise**; main flow not downgraded. | matrix N-2 · N-9 · N-10 |
| T-21 | **Notifications preview + enabled flag**: still **no** orchestrator notification emit. | matrix N-4 |
| T-22 | **Human delivery CLI approve** (if touched): optional `checkpoint.approved` with `approval_source=human` when enabled. | matrix N-11 |
| T-23 | **Registry fail-close**: selector/registry block → no checkpoint A/B files. | matrix X-1 |
| T-24 | **Test matrix** updated (`standard-case-hitl-resume-notify-matrix.md`); **coverage gaps** explicitly listed for scenarios without dedicated unittest. | matrix §9 G-1–G-11 |
| T-25 | **Extended fixtures** (W7): preview/run tests added per new `case_ref` without regressing `demo_phase` / `sampleco` baselines. | W7-T1 tests |

---

## Docs

| # | Check item | W6/W7 anchor |
|---|------------|--------------|
| DOC-1 | Ticket **`*_state.md`** AC table updated; Reviewer column filled or `accepted_with_gaps` rationale recorded. | W6 ticket states |
| DOC-2 | **Closure report** created or updated for batch-level changes (behavior delta, reliability asymmetry, test inventory, limitations). | `W6-standard-case-v2-closure-report.md` |
| DOC-3 | **`standard-case-hitl-resume-notify-matrix.md`** reflects new scenarios, `final_status` vocabulary, and notification event types. | matrix §1–§8 |
| DOC-4 | **Integration docs** updated: `docs/checkpoint-a-integration-v1.md` / `docs/checkpoint-b-integration-v1.md` (path fallback, trigger rules, human actions). | W6-T5/T6 C_REPORT suggestions |
| DOC-5 | **Orchestrator doc** updated: `docs/agent-run-standard-case-orchestrator-v1.md` (checkpoint wiring, resume loop §9, CLI flags). | W6-T11 AC-6 follow-up |
| DOC-6 | **Operator UX** documented: same CLI for forward run and `--resume-checkpoint`; HITL via `run_hitl_checkpoint_cli --apply-decision`. | W6-T11 Goal |
| DOC-7 | **`WORKFLOW_INDEX`** / **`WAVE_PROGRESS_DASHBOARD`** entries added or updated for delivered tickets. | W6-T5/T6 deliverables |
| DOC-8 | **Follow-up tickets** filed for intentional gaps (webhook adapter, revise/hold resume, production `delivery.bundle_ready`, matrix gap cells). | closure report §Future Work |
| DOC-9 | **Experiment vs production** scope called out when adding fixtures, mocks, or allowlist entries (extended fixtures ≠ production contract). | W7-T1 scope |
| DOC-10 | **Onboarding / summary docs** touched if operator or eval workflow changes (`agent-standard-line-v1-summary.md`, eval guide, skill cards). | W7-T1 docs list |

---

## Verification command bundle (baseline)

Run after any standard-case pipeline change; attach exit summaries to ticket §4.

```bash
python -m unittest tests.test_checkpoint_a_integration_v1 -v
python -m unittest tests.test_checkpoint_b_integration_v1 -v
python -m unittest tests.test_notification_gateway_v1 -v
python -m unittest tests.test_agent_standard_case_experiment -v
```

Optional adjacency if HITL core or delivery CLI touched:

```bash
python -m unittest tests.test_hitl_checkpoints_v1 tests.test_delivery_approval_cli_v1 -v
```

---

## Section counts

| Section | Items |
|---------|------:|
| Design | 12 |
| Implementation | 18 |
| Testing | 25 |
| Docs | 10 |
| **Total** | **65** |

---

## Sign-off block (paste into ticket)

```yaml
standard_case_change_checklist:
  design: __ / 12
  implementation: __ / 18
  testing: __ / 25
  docs: __ / 10
  deferred_items: []
  verifier: 
  date: 
```

---

*Checklist v1 · 2026-06-16 · Process Engineer · sourced from W6 v2 closure report, HITL/resume/notify matrix, and W6/W7 ticket AC.*
