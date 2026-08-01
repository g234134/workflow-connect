# Delivery Approval One-Click CLI v1

> **Ticket**: W8-T3 · delivery-approval-one-click-cli-v1  
> **Date**: 2026-06-10  
> **Status**: Tool-layer CLI (HITL preview + confirm)  
> **Scope**: Integrates signoff review, Checkpoint B decision, optional controlled notify experiment

---

## 1. Purpose

Provide Human operators a **single CLI** for S13 Delivery Approval that:

1. Shows a consolidated review: `delivery_signoff`, `output_guard.status`, row metrics
2. Records Checkpoint B human decision → `resume_context` + `delivery_plan`
3. Optionally invokes W7-T3 controlled notify experiment (dry-run or outbox write)

**NonScope**

- No external email / Slack / Telegram dispatch (`external_dispatch` remains `false`)
- No changes to `controlled_notify_experiment_v1` behavior
- No main-chain delivery resume or `cases/index.json` mutation

**Governance alignment**

- HITL: default **preview**; `--confirm` required to persist decision
- R4: human still approves after reading signoff + guard summary
- R6: notify experiment remains simulated; optional and approve-only

---

## 2. Module API

| Module | Role |
|--------|------|
| `delivery/delivery_approval_cli_v1.py` | Core logic: review summary, decision, optional notify |
| `scripts/run_delivery_approval_cli.py` | CLI entry point |
| `hitl/checkpoints_v1.py` | `record_human_decision` persistence |
| `hitl/checkpoint_b_integration_v1.py` | `delivery_plan_from_checkpoint_b` |
| `delivery/controlled_notify_experiment_v1.py` | Optional simulated notify (unchanged) |

| Function | Description |
|----------|-------------|
| `build_approval_review_summary(case_dir)` | Load signoff + output_guard + metrics |
| `normalize_cli_action(action)` | Map `approve` → `approve_delivery` |
| `run_delivery_approval(...)` | End-to-end flow; returns stable `dict` |

---

## 3. CLI Usage

### 3.1 Preview (no write)

```bash
python scripts/run_delivery_approval_cli.py \
  --case-dir cases/demo_phase \
  --checkpoint-id B-delivery-confirmation \
  --action approve \
  --notes "Reviewing before confirm"
```

### 3.2 Confirm approve_delivery

Requires a **pending** Checkpoint B under `outbox/demo_phase/`:

```bash
# Seed checkpoint B (if not already present) via experiment line or:
python -c "
from hitl.checkpoint_b_integration_v1 import maybe_create_checkpoint_b
maybe_create_checkpoint_b(
    'cases/demo_phase',
    {'tools_executed': [], 'outbox_runs': []},
    {'status': 'warning', 'input_rows': 7, 'output_rows': 5, 'ratio': 0.286},
    {'signoff': 'delivery_signoff.md'},
)
"

python scripts/run_delivery_approval_cli.py \
  --case-dir cases/demo_phase \
  --action approve \
  --notes "LGTM" \
  --confirm \
  --format json
```

### 3.3 Request changes / hold

```bash
python scripts/run_delivery_approval_cli.py \
  --case-dir cases/demo_phase \
  --action request_changes \
  --revise-target cleaning \
  --notes "Re-clean null handling" \
  --confirm

python scripts/run_delivery_approval_cli.py \
  --case-dir cases/demo_phase \
  --action hold \
  --notes "Await client sign-off" \
  --confirm
```

### 3.4 Optional notify experiment (approve only)

```bash
# Dry-run notify summary (default when --with-notify-experiment)
python scripts/run_delivery_approval_cli.py \
  --case-dir cases/demo_phase \
  --action approve --confirm \
  --with-notify-experiment

# Write outbox notify_experiment JSON
python scripts/run_delivery_approval_cli.py \
  --case-dir cases/demo_phase \
  --action approve --confirm \
  --with-notify-experiment --no-notify-dry-run
```

---

## 4. CLI Flags

| Flag | Default | Behavior |
|------|---------|----------|
| `--case-dir` | (required) | Case directory under `cases/` |
| `--checkpoint-id` | `B-delivery-confirmation` | Checkpoint B id |
| `--action` | (required) | `approve` \| `request_changes` \| `hold` |
| `--notes` | `""` | Operator comment on `human_decision` |
| `--confirm` | off | Persist decision; without it, preview only |
| `--revise-target` | `cleaning` | For `request_changes`: `cleaning` or `bundle` |
| `--with-notify-experiment` | off | Call W7-T3 after approve |
| `--notify-dry-run` / `--no-notify-dry-run` | dry-run true | Outbox write when notify enabled |
| `--format` | `text` | `text` or `json` |

---

## 5. Human Actions → resume_context

| CLI `--action` | Internal action | `resume_from` | `update_case_status` |
|----------------|-----------------|---------------|----------------------|
| `approve` | `approve_delivery` | `delivery` | `delivered` |
| `request_changes` | `request_changes` | `cleaning` or `bundle` | `changes_requested` |
| `hold` | `hold` | `null` | `on_hold` |

---

## 6. Sample resume_context (approve)

```json
{
  "checkpoint_id": "B-delivery-confirmation",
  "case_ref": "demo_phase",
  "original_decision": {
    "output_guard_status": "warning",
    "qa_status": "pass_with_warnings"
  },
  "human_decision": {
    "action": "approve_delivery",
    "operator_id": "operator_cli",
    "comment": "LGTM",
    "timestamp": "2026-06-10T12:00:00Z"
  },
  "resume_from": "delivery",
  "artifacts": {
    "signoff": "delivery_signoff.md"
  }
}
```

---

## 7. Verification

```bash
python -m unittest tests.test_delivery_approval_cli_v1 -v
python scripts/run_delivery_approval_cli.py --case-dir cases/demo_phase --action approve
```

---

## 8. Cross References

| File | Purpose |
|------|---------|
| `docs/checkpoint-b-integration-v1.md` | Checkpoint B integration |
| `docs/controlled-delivery-notify-experiment-v1.md` | W7-T3 notify experiment |
| `docs/agent-standard-line-governance-view-v2.md` | S13 decision flow (v2) |
| `docs/agent-run-experiment-eval-guide-v1.md` | Eval / replay §4.5–4.6 |
| `scripts/run_hitl_checkpoint_cli.py` | Lower-level checkpoint admin CLI |

---

*W8-T3 · delivery approval one-click CLI · HITL confirm required · 2026-06-10*
