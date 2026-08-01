# P75-G2 — Intake Gate layer + durable outbox record



> **Status**: implemented (G2) — closure pass complete  

> **Depends on**: P75-G1 contract (partial — doc + fixture schema in-repo)



## changed_files



### Added

- `routing/intake_gate_mapping_v1.py` — canonical mapping, gate_checks, CP-A adapter

- `routing/intake_gate_outbox_v1.py` — durable outbox record + events index

- `routing/intake_gate_layer_v1.py` — canonical producer `evaluate_intake_gate()`

- `scripts/run_intake_gate_cli.py` — standalone gate CLI

- `tests/test_intake_gate_layer_v1.py` — layer, mapping, outbox, orchestrator reject skip

- `tests/fixtures/intake_gate/intake_gate_result_v1.json` — G1 schema fixture (pre-promote)

- `docs/intake-gate-contract-v1.md` — contract SSOT + G2 appendix + CP-A adapter section



### Modified

- `scripts/run_agent_standard_case_experiment.py` — S3 → `evaluate_intake_gate`; S4 → `decision_result_from_gate` → CP-A

- `hitl/checkpoint_a_integration_v1.py` — embed `agent_output.intake_gate` from `_intake_gate` adapter block

- `tests/test_agent_standard_case_experiment.py` — gate layer assertions on experiment path

- `tests/test_checkpoint_a_integration_v1.py` — gate adapter payload + reject/review trigger tests

- `docs/outbox-and-feedback-layer-contract-v1.md` — intake gate outbox paths

- `04_Workflows/WORKFLOW_INDEX.md` — Intake Gate index entry



## verification



```bash

python scripts/run_intake_gate_cli.py \

  --task-type tabular.cleaning.mvp \

  --case-dir cases/demo_phase \

  --mode preview --format json



python -m unittest \

  tests.test_intake_gate_layer_v1 \

  tests.test_agent_standard_case_experiment \

  tests.test_checkpoint_a_integration_v1 \

  -v

```



Closure pass (2026-06-19): all above commands green; CP-A adapter tests cover reject skip + review_needed trigger.



## B_REPORT



Gate layer (`evaluate_intake_gate`) is the single canonical producer for three-state decisions (`accept` / `review_needed` / `reject`). Preview mode returns full `intake_gate_result_v1` without writing outbox; run mode persists `outbox/<case_ref>/intake_gate_decision_*.json` plus `outbox/intake_gate_events.jsonl`. Orchestrator S3/S4 wires gate → `decision_result_from_gate()` → existing CP-A trigger rules unchanged. Checkpoint payload gains `agent_output.intake_gate` (canonical snapshot) alongside legacy `intake_decision` (internal values).



## O_NOTES



**Known limits:** Policy YAML loader + deny merge already feed `gate_checks` / `reason_codes` in-repo (G3 track); no `intake.gate_decision` notify event yet (G4). Schema fixture lives under `tests/fixtures/` until G1 freeze. `checkpoint_a.would_trigger` on gate result is preview-only — CP-A creation uses adapter + `should_trigger_checkpoint_a`, not the preview block directly.



## next



- P75-G3: policy YAML loader + deny reason codes

- P75-G4: `intake.gate_decision` notify event

- Promote schema to `shared/schemas/intake_gate_result_v1.json` when G1 freezes

- **linked_in_dashboard**: `docs/WAVE_PROGRESS_DASHBOARD.md` §Phase 7.5 + P8.9 能力摘要（2026-06-19 Scribe 收錄）

