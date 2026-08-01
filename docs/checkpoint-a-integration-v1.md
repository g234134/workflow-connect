# Checkpoint A Integration v1

> **Ticket**: W6-T5 · Integrate Checkpoint A — Intake Confirmation  
> **Implementation**: `hitl/checkpoint_a_integration_v1.py`  
> **Upstream**: W5-T1 `evaluate_intake_decision` · W5-T2B `hitl/checkpoints_v1.py`  
> **Date**: 2026-06-10  
> **Status**: integration layer — **not** wired to main chain, UI, or durable workflow

---

## 1. Purpose

Connect intake decision summaries (W5-T1B) with checkpoint state and resume context (W5-T2B) for **Checkpoint A: Intake Confirmation**.

This module answers:

1. When should Checkpoint A be created?
2. What payload is written to `outbox/<case_ref>/`?
3. After human `approve` / `reject` / `revise_plan`, what `resume_plan` should downstream callers use?

**NonScope (W6-T5)**

- No main-chain E2E / intake CLI wiring
- No Local UI
- No Temporal / durable workflow engine
- No `cases/index.json` mutation on reject

---

## 2. API

### 2.1 `build_checkpoint_a_payload(task_type, case_dir, decision_result) -> dict`

Builds a W5-T2B-compatible checkpoint state dict (not yet persisted).

Requires `decision_result["ok"] is True`.

Includes:

- `agent_output.intake_decision` — decision, risk_level, rationale, suggested_route
- `agent_output.case_summary` — from `intake.json` when present
- `agent_output.gate_preview` — from `reports/eligibility_result.json` or glue gate notes

### 2.2 `maybe_create_checkpoint_a(task_type, case_dir, decision_result, auto_approve=False) -> dict`

| Condition | `status` | Checkpoint file |
|-----------|----------|-------------------|
| `decision=reject` | `rejected_intake` | not created |
| `decision=auto_accept` + `auto_approve=True` | `approved_auto` | not created |
| `decision=needs_review` **or** `risk_level=medium/high` | `awaiting_human` | written under `outbox/` |
| `decision=auto_accept` + `risk_level=low` (no auto_approve) | `skipped` | not created |

Optional kwargs: `repo_root`, `outbox_root_override` (for tests).

### 2.3 `resume_plan_from_checkpoint_a(resume_context) -> dict`

Translates W5-T2B `resume_context` into an actionable plan:

| Human action | `resume_from` | `final_status` |
|--------------|---------------|----------------|
| `approve` | `selector` | `approved` |
| `revise_plan` | `gate` | `revise_needed` |
| `reject` | `null` | `rejected` |

When `resume_from=selector`, plan includes `selector_task_type` and `planned_tools`.

### 2.4 Helpers

- `should_trigger_checkpoint_a(decision_result) -> bool`
- `evaluate_and_maybe_checkpoint_a(...)` — runs W5-T1 then `maybe_create_checkpoint_a`
- `apply_human_decision_to_checkpoint_a(action, checkpoint, ...)` — builds resume_context + resume_plan without persisting (use W5-T2B CLI to persist)

---

## 3. Trigger rules (Checkpoint A)

Aligned with `docs/hitl-checkpoints-v1.md` §3.1 and W6-T5 ticket:

1. **`decision=needs_review`** → create checkpoint, `awaiting_human`
2. **`risk_level=medium` or `high`** (even if `auto_accept`) → create checkpoint
3. **`decision=reject`** → no checkpoint; return `rejected_intake`
4. **`decision=auto_accept` + `auto_approve=True`** → skip checkpoint; return `approved_auto` with resume plan
5. **`decision=auto_accept` + `risk_level=low`** → skip checkpoint; return `skipped`

---

## 4. Payload example

```json
{
  "schema_version": "hitl_checkpoint_v1",
  "checkpoint_id": "A-intake-confirmation",
  "case_ref": "demo_phase",
  "run_id": "2026-06-10T08-30-00Z_intake_confirm",
  "status": "awaiting_human",
  "created_at": "2026-06-10T08:30:00Z",
  "expires_at": "2026-06-10T08:35:00Z",
  "task_type": "tabular.cleaning.mvp",
  "agent_output": {
    "task_type": "tabular.cleaning.mvp",
    "intake_decision": {
      "decision": "needs_review",
      "risk_level": "medium",
      "rationale": ["task_type=tabular.cleaning.mvp", "..."],
      "suggested_route": {
        "selector_task_type": "e2e",
        "planned_tools": [
          "validate.eligibility",
          "clean.phase_demo",
          "export.delivery_bundle"
        ],
        "orchestration_tool_id": "orchestrate.e2e"
      }
    },
    "case_summary": {
      "client_ref": "internal-demo",
      "case_id": "demo_phase",
      "input_file": "raw/Phase.csv",
      "estimated_rows": 7
    },
    "gate_preview": {
      "eligibility": "review_needed",
      "exit_code": 2,
      "reason_code": "rows<100"
    }
  },
  "human_decision": null,
  "resume_context": null
}
```

---

## 5. Resume plan examples

### approve

```json
{
  "ok": true,
  "checkpoint_id": "A-intake-confirmation",
  "case_ref": "demo_phase",
  "human_action": "approve",
  "resume_from": "selector",
  "final_status": "approved",
  "selector_task_type": "e2e",
  "planned_tools": ["validate.eligibility", "clean.phase_demo", "export.delivery_bundle"],
  "message": "resume at selector with approved planned_tools"
}
```

### revise_plan

```json
{
  "ok": true,
  "resume_from": "gate",
  "final_status": "revise_needed",
  "message": "resume at gate for plan revision"
}
```

### reject

```json
{
  "ok": true,
  "resume_from": null,
  "final_status": "rejected",
  "message": "flow terminated; no resume"
}
```

---

## 6. Usage flow

```
evaluate_intake_decision (W5-T1)
        │
        ▼
maybe_create_checkpoint_a (W6-T5)
        │
        ├─ awaiting_human → outbox/checkpoint_A-*.json
        │       │
        │       ▼
        │   run_hitl_checkpoint_cli --apply-decision (W5-T2B)
        │       │
        │       ▼
        │   resume_context
        │       │
        │       ▼
        └─ resume_plan_from_checkpoint_a (W6-T5)
```

---

## 7. checkpoint_path Semantics (Three-Tier Fallback)

The `maybe_create_checkpoint_a()` function returns a `checkpoint_path` field when a checkpoint file is created. This path uses a **three-tier fallback strategy** to ensure compatibility across different deployment scenarios (repo-internal outbox, external sandbox outbox, or temporary directories).

### Tier 1: Repository-Relative Path (Preferred)

When the checkpoint file is written under `repo_root`:

```json
{
  "checkpoint_path": "outbox/demo_phase/checkpoint_A-2026-06-10T08-30-00Z.json"
}
```

- **Form**: Relative path from repository root
- **Use case**: Standard deployment where outbox is inside the repo
- **Consumer parsing**: Prepend `repo_root` to resolve full path

### Tier 2: Outbox-Relative Path

When the checkpoint file is written outside `repo_root` but under `outbox_root` (e.g., external sandbox or temp directories):

```json
{
  "checkpoint_path": "demo_phase/checkpoint_A-2026-06-10T08-30-00Z.json"
}
```

- **Form**: Relative path from `outbox_root` (case_ref as first segment)
- **Use case**: Custom `outbox_root_override` in test/sandbox environments
- **Consumer parsing**: Prepend `outbox_root` to resolve full path

### Tier 3: Absolute Path (Fallback)

When the checkpoint file is outside both `repo_root` and `outbox_root`:

```json
{
  "checkpoint_path": "/tmp/sandbox/outbox/demo_phase/checkpoint_A-2026-06-10T08-30-00Z.json"
}
```

- **Form**: Absolute filesystem path
- **Use case**: Exotic deployment scenarios or system temp directories
- **Consumer parsing**: Use path directly

### Consumer Resolution Rules

When consuming `checkpoint_path` from JSON or audit quickview:

1. **If you have `outbox_root`** (from config or runtime):
   - Check if path starts with case_ref segment → prepend `outbox_root`
2. **Otherwise**:
   - Check if path is absolute → use as-is
   - Else → prepend `repo_root` (default assumption)

### Implementation Reference

The three-tier logic is implemented in `hitl/checkpoint_a_integration_v1.py`:

```python
# Tier 1: try repo-relative (backward compatible)
try:
    return str(dest.relative_to(repo_root))
except ValueError:
    pass

# Tier 2: try outbox-relative (sandbox/external outbox)
try:
    return str(dest.relative_to(outbox_root))
except ValueError:
    pass

# Tier 3: fallback to absolute path
return str(dest)
```

---

## 8. Verification

```bash
python -m unittest tests.test_checkpoint_a_integration_v1 -v
```

---

## 9. Cross-references

| Document | Role |
|----------|------|
| `docs/agent-standard-line-v1-summary.md` | Agent Standard Line v1 收口總結（W6-T3/4/5/6） |
| `docs/agent-run-standard-case-orchestrator-v1.md` | W6-T4 orchestrator CLI（inline Checkpoint A；未直接 import 本模組） |
| `docs/checkpoint-b-integration-v1.md` | W6-T6 Checkpoint B 對稱整合層 |
| `docs/hitl-checkpoints-v1.md` | Checkpoint A design (W5-T2) |
| `docs/intake-decision-rules-v1.md` | Decision helper (W5-T1) |
| `docs/agent-run-standard-case-experiment-v1.md` | S4 Checkpoint A in 15-step line |
| `04_Workflows/tickets/W6-T5-integrate-checkpoint-a-intake-confirmation_state.md` | Ticket state |
| `04_Workflows/tickets/W6-T5-T6-docs-checkpoint-path-semantics-v1_state.md` | B4 verify-and-close · §7 pre-landed（docs-only · ≠ Phase%／runtime） |

---

*Checkpoint-A-Integration-v1 · W6-T5 · 2026-06-10*
