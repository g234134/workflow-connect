# Tabular HITL Resume Flow v1

> **Ticket scope**: Tabular unified driver CP-A / CP-B resume integration  
> **Related**: `docs/hitl-checkpoints-v1.md` · `docs/tabular-cleaning-automation-manifest-v1.md` · `docs/C2-P2_RUNBOOK.md`

---

## 1. Goal

When `run_tabular_automation.py` hits **CP-A** or **CP-B**, the case pauses safely. After a human records **approve** / **reject**, the operator runs **resume-after-checkpoint** to continue from the correct driver step—without re-running completed stages.

---

## 2. State fields (`automation_state.json`)

| Field | Values | Meaning |
|-------|--------|---------|
| `checkpoint_a_status` | `not_required` · `pending` · `approved` · `rejected` | CP-A lifecycle |
| `checkpoint_b_status` | same | CP-B lifecycle |
| `checkpoint_a_decided_by` | string \| null | Operator id for CP-A |
| `checkpoint_b_decided_by` | string \| null | Operator id for CP-B |
| `checkpoint_a_decided_at` | ISO-8601 \| null | CP-A decision time |
| `checkpoint_b_decided_at` | ISO-8601 \| null | CP-B decision time |
| `checkpoint_resume_step` | driver step \| null | Next step after approval |

**Pause semantics** (with control plane):

| Situation | `automation_status` | `pause_reason` |
|-----------|---------------------|----------------|
| Waiting on CP-A | `paused` | `awaiting_checkpoint_a` |
| Waiting on CP-B | `paused` | `awaiting_checkpoint_b` |
| CP approved, ready to resume | `paused` | `checkpoint_a_approved_awaiting_resume` (or `_b_`) |
| CP-B approved for delivery | `completed` | `null` · `current_step=approved_for_delivery` |

---

## 3. Resume step mapping

| Checkpoint | Human action | `checkpoint_resume_step` | Driver behavior |
|------------|--------------|--------------------------|-----------------|
| **CP-A** | `approve` | `cleaning` | Continue R3 clean → report → bundle → e2e → CP-B |
| **CP-A** | `reject` | `null` | `automation_status=stopped`; manual restart only |
| **CP-A** | `revise_plan` | `eligibility` | Re-run gate (not auto-wired in v1 CLI; use outbox `--apply-decision revise_plan` + manual driver) |
| **CP-B** | `approve_delivery` | `approved_for_delivery` | Mark completed; no further driver steps |
| **CP-B** | `reject-b` → `hold` | `null` | Stays paused; operator must release or revise manually |
| **CP-B** | `request_changes` | `cleaning` | Re-run from cleaning (outbox action; v1 CLI maps reject-b to hold only) |

---

## 4. CLI commands

Tabular resume commands (first positional arg):

```bash
# After driver stops at CP-A
python scripts/run_hitl_checkpoint_cli.py approve-a \
  --case-id demo_phase --operator-id operator --notes "LGTM" --json

python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint \
  --case-id demo_phase --operator-id operator --json

# Reject paths
python scripts/run_hitl_checkpoint_cli.py reject-a --case-id demo_phase --json
python scripts/run_hitl_checkpoint_cli.py reject-b --case-id demo_phase --json

# Plan resume without executing driver
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint \
  --case-id demo_phase --dry-run --json
```

Legacy outbox-only commands unchanged:

```bash
python scripts/run_hitl_checkpoint_cli.py --list
python scripts/run_hitl_checkpoint_cli.py --review --checkpoint-id A-intake-confirmation
python scripts/run_hitl_checkpoint_cli.py --apply-decision approve \
  --checkpoint-id A-intake-confirmation
```

---

## 5. Example: `demo_phase` full HITL path

`demo_phase` intake decision is `needs_review` (medium risk). **Without** `--force`, CP-A is written and the driver pauses.

```bash
# 1. Start control plane
python scripts/manage_tabular_automation_state.py start \
  --case-dir cases/demo_phase --requested-by operator --json

# 2. Run driver (no --force → CP-A triggers)
python scripts/run_tabular_automation.py --case-id demo_phase --json
# → automation_status=paused, pause_reason=awaiting_checkpoint_a
# → checkpoint_a_status=pending, requires_hitl_checkpoint=true

# 3. Review (optional)
python scripts/run_hitl_checkpoint_cli.py --review \
  --checkpoint-id A-intake-confirmation

# 4. Approve + resume
python scripts/run_hitl_checkpoint_cli.py approve-a \
  --case-id demo_phase --operator-id operator --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint \
  --case-id demo_phase --json
# → continues from cleaning; may stop again at CP-B

# 5. After CP-B pending
python scripts/run_hitl_checkpoint_cli.py approve-b \
  --case-id demo_phase --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint \
  --case-id demo_phase --json
# → automation_status=completed, current_step=approved_for_delivery
```

**Skip HITL (internal demo only)**:

```bash
python scripts/run_tabular_automation.py --case-id demo_phase --force --json
```

---

## 6. State flow (ASCII)

```
running ──► checkpoint_a step ──► [trigger] ──► paused / awaiting_checkpoint_a
                                                      │
                         approve-a ◄──────────────────┘
                              │
                              ▼
              checkpoint_a_status=approved, checkpoint_resume_step=cleaning
                              │
              resume-after-checkpoint
                              │
                              ▼
         running ──► cleaning ──► … ──► checkpoint_b ──► paused / awaiting_checkpoint_b
                                                              │
                         approve-b ◄──────────────────────────┘
                              │
                              ▼
              completed / approved_for_delivery
```

---

## 7. NonScope (v1)

| Scenario | v1 behavior |
|----------|-------------|
| `revise_plan` after CP-A | Outbox records decision; **no** auto replan—operator edits case or restarts |
| `request_changes` after CP-B | Not exposed as CLI alias; use outbox `--apply-decision request_changes` + manual `--start-from cleaning` |
| Reject after human edited artifacts | Operator must reconcile files vs checkpoint snapshot manually |
| Multi-pending checkpoints same case | Uses latest pending outbox file per checkpoint id |
| External notify (Slack/Telegram) | Not wired |
| Timeout auto-approve | Not unified with driver |

---

## 8. Cross references

| Artifact | Role |
|----------|------|
| `scripts/tabular_hitl_resume_lib.py` | State + outbox + driver glue |
| `scripts/tabular_automation_driver_lib.py` | Pause at CP-A/B |
| `scripts/run_hitl_checkpoint_cli.py` | Operator CLI |
| `hitl/checkpoints_v1.py` | Outbox checkpoint schema |
