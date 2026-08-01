# Checkpoint B Integration v1 — Delivery Gate

> **Ticket**: W6-T6 · integrate-checkpoint-b-delivery-gate  
> **Date**: 2026-06-10  
> **Status**: Tool-layer implementation  
> **Scope**: Integration only; no client notify; no main-chain delivery resume

---

## 1. Purpose

Connect W5-T2 **Delivery Confirmation** (Checkpoint B) to the Agent-run standard case experiment line (W6-T3). Consumers receive structured `delivery_plan` dicts after `output_guard` evaluation without touching real delivery or notification flows.

**Upstream**

| Artifact | Role |
|----------|------|
| `docs/hitl-checkpoints-v1.md` §4 | Checkpoint B design |
| `hitl/checkpoints_v1.py` | File-based state / events / resume_context |
| `docs/agent-run-standard-case-experiment-v1.md` | S11–S13 experiment steps |

**Module**: `hitl/checkpoint_b_integration_v1.py`

---

## 2. Public API

| Function | Description |
|----------|-------------|
| `build_checkpoint_b_payload(case_dir, execution_summary, output_guard, artifacts)` | Build checkpoint JSON (not persisted) |
| `maybe_create_checkpoint_b(..., auto_approve=False)` | Apply v1 rules; optionally write under `outbox/<case_ref>/` |
| `delivery_plan_from_checkpoint_b(resume_context)` | Map post-decision `resume_context` → delivery plan |
| `delivery_plan_from_human_decision(checkpoint, human_decision)` | Helper wrapping `build_resume_context` + plan |
| `should_create_checkpoint_b(output_guard, auto_approve=False)` | Pure trigger predicate |

All functions return stable `dict` shapes with `ok` / `message` where applicable.

---

## 3. v1 Trigger Rules

| `output_guard.status` | `auto_approve` | Behavior |
|----------------------|----------------|----------|
| `warning` | any | **Create** Checkpoint B (`awaiting_human`) |
| `blocked` | any | **Create** Checkpoint B |
| `ok` | `True` | **Skip** checkpoint; `delivery_plan.action=auto_approve`, `resume_from=delivery` |
| `ok` | `False` | **Skip** checkpoint (`ok_no_human_gate`); no mandatory human gate for clean ok |
| `error` | any | **No checkpoint**; `ok=false`, flow terminates |

Writes are restricted to `outbox/` via `hitl/checkpoints_v1.write_checkpoint`.

---

## 4. Human Decisions → Delivery Plan

| Human action | `resume_from` | `proceed_to_delivery` | `update_case_status` |
|--------------|---------------|----------------------|----------------------|
| `approve_delivery` | `delivery` | `true` | `delivered` |
| `request_changes` | `cleaning` or `bundle` | `false` | `changes_requested` |
| `hold` | `null` | `false` | `on_hold` |

`request_changes` revise target resolution order:

1. `resume_context.revise_target` / `resume_target`
2. `human_decision.revise_target`
3. `resume_context.resume_from` if `cleaning` or `bundle`
4. Default: `cleaning`

**v1 NonScope**: `notify_client` is always `false`; no `cases/index.json` mutation in this module.

---

## 5. Payload Example (Checkpoint B)

```json
{
  "schema_version": "hitl_checkpoint_v1",
  "checkpoint_id": "B-delivery-confirmation",
  "case_ref": "demo_phase",
  "status": "awaiting_human",
  "created_at": "2026-06-10T08:31:30Z",
  "expires_at": "2026-06-10T08:36:30Z",
  "task_type": "tabular.cleaning.mvp",
  "checkpoint": {
    "id": "B-delivery-confirmation",
    "version": "v1",
    "triggered_at": "2026-06-10T08:31:30Z",
    "case_ref": "demo_phase",
    "task_type": "tabular.cleaning.mvp"
  },
  "agent_output": {
    "task_type": "tabular.cleaning.mvp",
    "execution_summary": {
      "tools_executed": [
        {"tool_id": "validate.eligibility", "ok": true, "exit_code": 2},
        {"tool_id": "clean.phase_demo", "ok": true, "forced": true},
        {"tool_id": "export.delivery_bundle", "ok": true}
      ],
      "outbox_runs": [
        "2026-06-10T08-30-15Z_eligibility",
        "2026-06-10T08-30-45Z_phase_demo",
        "2026-06-10T08-31-15Z_delivery_bundle"
      ]
    },
    "cleaning_results": {
      "input_rows": 7,
      "output_rows": 5,
      "removed_rows": 2,
      "removal_ratio": 0.286,
      "qa_status": "pass_with_warnings"
    },
    "artifacts": {
      "eligibility_report": "reports/eligibility_result.json",
      "cleaned_csv": "cleaned/Phase_cleaned.csv",
      "delivery_bundle": "reports/delivery_bundle.zip",
      "signoff": "delivery_signoff.md"
    },
    "output_guard": {
      "status": "warning",
      "checks": {"ratio_check": "warning", "schema_check": "ok"}
    },
    "delivery_draft": {
      "summary_text": "已清洗 7→5 rows；移除 2 行；output_guard.status=warning",
      "confidence_score": 0.6
    }
  },
  "human_decision": null,
  "resume_context": null
}
```

---

## 6. Consumer Usage (Experiment Line)

```python
from hitl.checkpoint_b_integration_v1 import (
    maybe_create_checkpoint_b,
    delivery_plan_from_checkpoint_b,
)
from hitl.checkpoints_v1 import record_human_decision, CHECKPOINT_B_ID

# After S11 output_guard
result = maybe_create_checkpoint_b(
    case_dir="cases/demo_phase",
    execution_summary=execution_summary,
    output_guard=output_guard,
    artifacts=artifacts,
    auto_approve=False,
)

if result["checkpoint_created"]:
    # Human reviews via scripts/run_hitl_checkpoint_cli.py
    resume_context = record_human_decision(
        CHECKPOINT_B_ID,
        "approve_delivery",
        notes="LGTM",
    )
    plan = delivery_plan_from_checkpoint_b(resume_context)
else:
    plan = result["delivery_plan"]
```

---

## 7. checkpoint_path Semantics (Three-Tier Fallback)

The `maybe_create_checkpoint_b()` function returns a `checkpoint_path` field when a checkpoint file is created. This path uses a **three-tier fallback strategy** identical to Checkpoint A (W6-T5) to ensure compatibility across different deployment scenarios.

### Tier 1: Repository-Relative Path (Preferred)

When the checkpoint file is written under `repo_root`:

```json
{
  "checkpoint_path": "outbox/demo_phase/checkpoint_B-2026-06-10T08-31-30Z.json"
}
```

- **Form**: Relative path from repository root
- **Use case**: Standard deployment where outbox is inside the repo
- **Consumer parsing**: Prepend `repo_root` to resolve full path

### Tier 2: Outbox-Relative Path

When the checkpoint file is written outside `repo_root` but under `outbox_root`:

```json
{
  "checkpoint_path": "demo_phase/checkpoint_B-2026-06-10T08-31-30Z.json"
}
```

- **Form**: Relative path from `outbox_root` (case_ref as first segment)
- **Use case**: Custom `outbox_root_override` in test/sandbox environments
- **Consumer parsing**: Prepend `outbox_root` to resolve full path

### Tier 3: Absolute Path (Fallback)

When the checkpoint file is outside both `repo_root` and `outbox_root`:

```json
{
  "checkpoint_path": "/tmp/sandbox/outbox/demo_phase/checkpoint_B-2026-06-10T08-31-30Z.json"
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

The three-tier logic in `hitl/checkpoint_b_integration_v1.py` mirrors W6-T5:

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

## 8. NonScope (W6-T6)

- No Slack / Email / Telegram approval
- No `cases/index.json` status updates
- No `scripts/build_case_delivery_bundle.py` or notification gateway changes
- No durable workflow engine
- Does not resume main chain automatically

---

## 9. Cross References

| File | Purpose |
|------|---------|
| `docs/agent-standard-line-v1-summary.md` | Agent Standard Line v1 收口總結（W6-T3/4/5/6） |
| `docs/agent-run-standard-case-orchestrator-v1.md` | W6-T4 orchestrator（S12 經 W12-T2 接 W6-T6 integration layer） |
| `docs/checkpoint-a-integration-v1.md` | W6-T5 Checkpoint A 對稱整合層 |
| `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md` | Sandbox e2e · S12 共用 `maybe_create_checkpoint_b`（W12-T2） |
| `docs/agent-run-standard-case-experiment-v1.md` | W6-T3 15-step design (S11–S13) |
| `hitl/checkpoints_v1.py` | Persistence + `record_human_decision` |
| `scripts/run_hitl_checkpoint_cli.py` | Human decision CLI |
| `tests/test_checkpoint_b_integration_v1.py` | Unit tests |
| `04_Workflows/tickets/W6-T6-integrate-checkpoint-b-delivery-gate_state.md` | Ticket state |
| `04_Workflows/tickets/W6-T5-T6-docs-checkpoint-path-semantics-v1_state.md` | B4 verify-and-close · §7 pre-landed（對齊 A · B 檔名 `checkpoint_B` · ≠ Phase%／runtime） |
| `04_Workflows/tickets/W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1_state.md` | Sandbox e2e 完整 CP-B 寫檔路徑 |

---

## 10. Sandbox consumer（W12-T2）

Orchestrator sandbox e2e（`--sandbox-end-to-end`）在 Phase-1 後呼叫：

1. `_resolve_checkpoint_b_after_run` → `maybe_create_checkpoint_b(...)`（本模組）
2. `_can_proceed_sandbox_bundle_after_checkpoint_b(checkpoint_b_status)` 決定是否寫 sandbox manifest

`checkpoint_b_status` 必含 `integration_layer: hitl.checkpoint_b_integration_v1`（preview／run／sandbox 對齊）。  
舊函式 `can_proceed_sandbox_bundle` 仍保留於 `delivery/sandbox_delivery_bundle_v1.py` 供舊 consumer；**orchestrator 主流程不再 import**。

*CHECKPOINT-B-INTEGRATION-v1 · W6-T6 · 2026-06-10*
