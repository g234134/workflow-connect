# Agent-Run Standard Case Orchestrator v1

> **Ticket**: W6-T4 · Agent-run Standard Case Orchestrator  
> **Implementation**: `scripts/run_agent_standard_case_experiment.py`  
> **Design upstream**: `docs/agent-run-standard-case-experiment-v1.md` (W6-T3)  
> **Date**: 2026-06-10  
> **Status**: experimental-line orchestrator — **does not** change production main-chain defaults

---

## 1. Purpose

Provide a **single CLI entry** for the Tabular MVP **Agent-run standard case experiment line**, limited to:

- `cases/demo_phase`
- `cases/sampleco/2026-0001`

The orchestrator chains existing helpers without modifying main-chain E2E, Local UI, or Gov routing.

---

## 2. Wired components

| Step | Component | Module / CLI |
|------|-----------|--------------|
| S3 Decision Evaluate | W5-T1 / W5-T1B | `routing/intake_decision_rules_v1.py` |
| S4 Checkpoint A | W6-T5 | `hitl/checkpoint_a_integration_v1.py` |
| S5 Route Planning | W4-T1 | `routing/intake_to_tabular_glue.py::plan_tabular_route` |
| S6 Tool Path Preview | W4-T3-A | `scripts/run_tabular_intake_tool_path.py` |
| S11 Output Guard | mock/placeholder | profile-based summary in orchestrator |
| S12 Checkpoint B | W6-T6 | `hitl/checkpoint_b_integration_v1.py` (run) / planned preview |

### Checkpoint integration (W6-T10)

As of **W6-T10**, the experiment-line orchestrator routes S4 (Checkpoint A) and S12 (Checkpoint B) through the W6-T5 / W6-T6 integration layers instead of inline payload builders. S4 calls `hitl/checkpoint_a_integration_v1.py` (`should_trigger_checkpoint_a` for trigger semantics; `maybe_create_checkpoint_a` for run-mode writes). S12 run path calls `hitl/checkpoint_b_integration_v1.py` (`should_create_checkpoint_b` + `maybe_create_checkpoint_b`). Preview mode never writes outbox files: S4 reports `would_pause` / `would_trigger` only; S12 reports `planned` status with trigger semantics delegated to the integration layer. Run mode writes when the integration layer decides a human gate is required — Checkpoint A on `decision=needs_review` (unless skipped), Checkpoint B when live `output_guard.status` is `warning` or `blocked`.

Two orchestrator-layer workarounds remain until follow-up integration-layer tickets land (details in `W6-T10` B/C_REPORT): (1) **`--auto-approve-intake`** — the orchestrator bypasses the W6-T5 write call before `maybe_create_checkpoint_a`, because the integration layer does not yet skip file creation for `needs_review` + `auto_approve=True`; status is `auto_approved` with a `resume_plan` emitted. (2) **`--outbox-root` override** — when tests or sandbox layouts use a non-default outbox root, the orchestrator passes `repo_root=Path(outbox_root).parent` so `checkpoint_path` relative paths resolve; the integration layers still assume outbox lives under repo root unless this workaround is applied.

Status objects include `integration_layer` (`hitl.checkpoint_a_integration_v1` / `hitl.checkpoint_b_integration_v1`) on run paths for observability. Payload and resume contracts remain authoritative in `docs/checkpoint-a-integration-v1.md` and `docs/checkpoint-b-integration-v1.md`.

### Notification gateway (W6-T10 · S15 · design)

**Status**: design only (2026-06-16); **not wired** in orchestrator until **W6-T10-P2-stub-notification-gateway-v1**.

When enabled (`--enable-notifications`, run mode only), the experiment line will emit best-effort workflow events via `delivery/notification_gateway_v1.py` (P2):

| Event | Trigger (run mode) |
|-------|-------------------|
| `checkpoint.awaiting_human` | Checkpoint A/B file written |
| `checkpoint.approved` | Checkpoint A/B auto-approved / skipped |
| `delivery.bundle_ready` | Sandbox delivery bundle written (S10) |
| `run.completed` | `final_status` ∈ `{run_complete, resume_plan_ready}` |
| `run.blocked` | Reject / blocked / failed gate |

Default sink: `outbox/notifications/<case_ref>/*.json` + append `outbox/notification_events.jsonl`. Notify failure must **not** fail the orchestrator run. Distinct from W7-T3 **content** notify (`controlled_notify_experiment_v1` → client summary). Design authority: `04_Workflows/tickets/W6-T10-client-notification-gateway-v1_state.md`.

---

## 3. CLI usage

```bash
# Preview (default) — plan-only, no checkpoint file writes
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview \
  --format json

# Partial run — auto-approve intake, emit resume plan (no delivery execution)
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --auto-approve-intake \
  --format json
```

### Parameters

| Flag | Required | Description |
|------|----------|-------------|
| `--task-type` | yes | W2 routing catalog task_type (`tabular.*` family) |
| `--case-dir` | yes | Case directory (allowlist fixtures only) |
| `--mode` | no | `preview` (default) or `run` |
| `--auto-approve-intake` | no | Skip Checkpoint A when `needs_review` |
| `--auto-approve-delivery` | no | Mark Checkpoint B as auto-approved planned (no delivery) |
| `--format` | no | `text` (default) or `json` |
| `--outbox-root` | no | Override outbox root for checkpoint state writes (run mode) |

---

## 4. Output JSON shape

```json
{
  "ok": true,
  "experiment_id": "<uuid>",
  "case_ref": "demo_phase",
  "case_dir": "cases/demo_phase",
  "task_type": "tabular.cleaning.mvp",
  "mode": "preview",
  "decision": { "decision": "needs_review", "risk_level": "medium", ... },
  "checkpoint_a_status": {
    "checkpoint_id": "A-intake-confirmation",
    "status": "would_pause",
    "would_trigger": true
  },
  "planned_route": {
    "selector_task_type": "e2e",
    "planned_tools": ["validate.eligibility", "clean.phase_demo", "export.delivery_bundle"]
  },
  "tool_path_preview": { "ok": true, "mode": "dry_run_preview", ... },
  "output_guard": {
    "status": "ok",
    "note": "S11 mock/placeholder — not read from bundle build in v1 experiment line",
    "source": "mock_profile_demo_phase"
  },
  "checkpoint_b_status": {
    "checkpoint_id": "B-delivery-confirmation",
    "status": "planned",
    "would_trigger": false
  },
  "final_status": "waiting_for_human",
  "steps_run": ["S3_decision_evaluate", "S5_route_planning", ...]
}
```

### `final_status` values

| Value | Meaning |
|-------|---------|
| `preview_ready` | Preview completed; no human gate expected |
| `waiting_for_human` | Checkpoint A and/or B would pause |
| `blocked` | `decision=reject` or non-allowlist case |
| `resume_plan_ready` | Run mode with resume plan emitted |

---

## 5. Checkpoint state writes

| Mode | Checkpoint A write |
|------|-------------------|
| `preview` | **No** — status `would_pause` only |
| `run` + `needs_review` | **Yes** — `outbox/<case_ref>/checkpoint_A-intake-confirmation_<ts>.json` |
| `run` + `--auto-approve-intake` | **No** — status `auto_approved` |

Checkpoint B in **run** mode writes via W6-T6 when `output_guard.status` is `warning` or `blocked`. Preview remains **planned / would_pause** (no file write).

Storage follows W5-T2B via integration layers: `hitl/checkpoint_a_integration_v1.py` / `hitl/checkpoint_b_integration_v1.py` → `hitl/checkpoints_v1.py::write_checkpoint`.

---

## 6. NonScope

- Does not invoke cleaning, executor, or mainline regression
- Does not modify `scripts/new_cleaning_case.py`, `app/local_ui.py`, glue, selector, executor
- Does not wire Gov routing / `_route_task.py`
- S11 output guard is **mock/placeholder** until bundle-read integration ticket
- S8–S10, S13–S15 not executed in v1 orchestrator

---

## 7. Verification

```bash
python -m unittest tests.test_agent_standard_case_experiment -v
```

---

## 8. Resume loop (planned · W6-T11)

> **Status**: design only (P1 · 2026-06-16). Not implemented in runtime until **W6-T11-P2**.

Today, run mode stops at Checkpoint A/B with `final_status=waiting_for_human`. Human decisions are recorded via `scripts/run_hitl_checkpoint_cli.py --apply-decision`, which updates the checkpoint JSON (`status=approved`, `resume_context`) but **does not** resume the experiment line.

**Planned v1 UX** (explicit path — recommended):

```bash
# After human approve on checkpoint file:
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --resume-checkpoint outbox/demo_phase/checkpoint_A-intake-confirmation_<ts>.json \
  --format json
```

| Checkpoint | Human action | Resume entry | Skip |
|------------|--------------|--------------|------|
| A (`A-intake-confirmation`) | `approve` | **S7** run path (cleaning / gate) | S3–S6, no new CP-A write |
| B (`B-delivery-confirmation`) | `approve_delivery` | **S13** delivery / export | S3–S12 |

**v1 scope**: approved resume only. `rejected`, `revise_plan`, `request_changes`, `hold`, stale/mismatched checkpoints → fail-close (`ok=false`).

**Consumer contract**: read `schema_version`, `checkpoint_id`, `case_ref`, `task_type`, `status`, `human_decision`, `resume_context`; derive plan via `resume_plan_from_checkpoint_a` / `delivery_plan_from_checkpoint_b`.

Design authority: `04_Workflows/tickets/W6-T11-checkpoint-resume-orchestrator-loop-v1_state.md`.

---

## 9. Cross-references

- **Line summary (Reviewer handoff)**: `docs/agent-standard-line-v1-summary.md`
- W6-T3 design: `docs/agent-run-standard-case-experiment-v1.md`
- W6-T5 Checkpoint A integration: `docs/checkpoint-a-integration-v1.md`
- W6-T6 Checkpoint B integration: `docs/checkpoint-b-integration-v1.md`
- W5-T1 decision: `docs/intake-decision-rules-v1.md`
- W5-T2 HITL design: `docs/hitl-checkpoints-v1.md`
- W4-T3 tool path: `docs/tabular-intake-tool-path-v1.md`
- Ticket state: `04_Workflows/tickets/W6-T4-agent-run-standard-case-orchestrator-v1_state.md`
- W6-T11 resume loop design: `04_Workflows/tickets/W6-T11-checkpoint-resume-orchestrator-loop-v1_state.md`

---

*AGENT-RUN-STANDARD-CASE-ORCHESTRATOR-v1 · W6-T4 · 2026-06-10*
