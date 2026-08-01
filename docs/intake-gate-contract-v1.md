# Intake Gate Contract v1

> **Ticket**: P75-G1 / P75-G2  
> **Status**: Contract SSOT + G2 implementation appendix  
> **Canonical schema**: `tests/fixtures/intake_gate/intake_gate_result_v1.json` (G1 → `shared/schemas/` when frozen)

## Canonical three-state vocabulary

| `decision` | Meaning |
|------------|---------|
| `accept` | Rules allow intake; proceed on standard case line |
| `review_needed` | Manual confirmation required (maps v1/v2 `needs_review`, Phase 7.5 `defer`) |
| `reject` | Rules deny intake; no Checkpoint A |

## Producer

`routing/intake_gate_layer_v1.evaluate_intake_gate()` is the **only** canonical producer.

## Appendix A — G2 implementation (P75-G2)

### API

```python
evaluate_intake_gate(
    task_type: str,
    case_dir: str,
    *,
    mode: "preview" | "run" = "preview",
    policy_path: str | None = None,  # reserved for G3
    use_v1_fallback: bool = True,
    repo_root: Path | None = None,
    outbox_root_override: str | None = None,
) -> dict  # intake_gate_result_v1
```

### CLI

```bash
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview --format json
```

### Outbox (run mode only)

| Artifact | Path |
|----------|------|
| Durable record | `outbox/<case_ref>/intake_gate_decision_<compact_ts>_<id_suffix>.json` |
| Event index | `outbox/intake_gate_events.jsonl` |

Preview mode: `outbox_record_path` is `null`; no files written.

### Example (demo_phase preview)

```json
{
  "ok": true,
  "schema_version": "intake_gate_result_v1",
  "decision": "review_needed",
  "decision_internal": "needs_review",
  "case_ref": "demo_phase",
  "risk_level": "medium",
  "reason_codes": ["manual_review_required", "allowlist_fixture"],
  "checkpoint_a": {
    "would_trigger": true,
    "trigger_reason": "decision_review_needed"
  },
  "outbox_record_path": null,
  "mode": "preview"
}
```

### Orchestrator S3 wiring

`scripts/run_agent_standard_case_experiment.py` S3 calls `evaluate_intake_gate` and sets:

- `result["intake_gate"]` — full gate result  
- `result["decision"]` — legacy block with **internal** values (`needs_review`, etc.) for backward compatibility  
- S4 CP-A uses `decision_result_from_gate()` adapter; CP-A trigger rules unchanged

### Checkpoint A — three-state gate vs trigger rules

Gate layer speaks **canonical** three-state vocabulary (`accept` / `review_needed` / `reject`).
Checkpoint A integration (`hitl/checkpoint_a_integration_v1.py`) still evaluates **internal**
decision values (`auto_accept` / `needs_review` / `reject`) via `should_trigger_checkpoint_a()`.
**G2 does not change CP-A trigger logic** — only how orchestrator feeds it.

| Gate `decision` | CP-A after adapter | `should_trigger_checkpoint_a` | `maybe_create_checkpoint_a` outcome |
|-----------------|-------------------|-------------------------------|-------------------------------------|
| `reject` | `decision=reject` | `False` | `status=rejected_intake`; no checkpoint file |
| `review_needed` | `decision=needs_review` | `True` | `status=awaiting_human` (unless `auto_approve=True`) |
| `accept` + `risk_level=low` | `decision=auto_accept` | `False` | `status=skipped` |
| `accept` + `risk_level=medium\|high` | `decision=auto_accept` | `True` (risk override) | `status=awaiting_human` |

Gate result also carries a **preview** block (`checkpoint_a.would_trigger` / `trigger_reason`) from
`compute_checkpoint_a_preview()` — informational only; CP-A creation still uses the adapter path below.

### Adapter: `decision_internal` → CP-A

Orchestrator S4 calls `routing/intake_gate_mapping_v1.decision_result_from_gate(gate_result)` before
CP-A helpers. The adapter:

1. Maps canonical → internal: `review_needed` → `needs_review`, `accept` → `auto_accept`, `reject` → `reject`.
2. Copies `risk_level`, `suggested_route`, `glue_plan`, and builds `rationale` from `gate_checks` / `reason_codes`.
3. Attaches `_intake_gate` (canonical snapshot) for `build_checkpoint_a_payload()` to embed under
   `agent_output.intake_gate` without altering legacy `agent_output.intake_decision` (internal values).

```python
gate = evaluate_intake_gate(task_type, case_dir, mode="preview")
adapted = decision_result_from_gate(gate)  # decision=needs_review, _intake_gate={decision: review_needed, ...}
maybe_create_checkpoint_a(task_type, case_dir, adapted)
```

Direct CLI / experiment flow: `run_agent_standard_case_experiment.py` S3 → gate, S4 → adapter → CP-A.

### Checkpoint A payload extension

When gate adapter is used, checkpoint JSON includes:

```json
"agent_output": {
  "intake_decision": {
    "decision": "needs_review",
    "risk_level": "medium",
    "rationale": ["G-RISK-02: risk_level=medium; ..."]
  },
  "intake_gate": {
    "intake_decision_id": "igd_...",
    "decision": "review_needed",
    "decision_internal": "needs_review",
    "reason_codes": [],
    "gate_checks": []
  }
}
```
