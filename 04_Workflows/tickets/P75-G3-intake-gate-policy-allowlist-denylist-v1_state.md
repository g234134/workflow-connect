# P75-G3 — Intake Gate policy SSOT (allowlist / denylist)



| Field | Value |

|-------|-------|

| **Status** | `implemented` |

| **Owner** | Implementer |

| **Depends** | P75-G1 (reason_codes enum), P75-G2 (layer merge hook) |



## changed_files



### Added

- `routing/intake_gate_policy_v1.yaml`

- `shared/schemas/intake_gate_policy_v1.json`

- `routing/intake_gate_policy_loader_v1.py`

- `routing/intake_gate_policy_evaluator_v1.py`

- `routing/intake_gate_policy_bridge_v1.py`

- `routing/intake_gate_policy_types_v1.py`

- `docs/intake-gate-policy-v1.md`

- `tests/test_intake_gate_policy_loader_v1.py`

- `tests/test_intake_gate_policy_evaluator_v1.py`

- `tests/test_intake_gate_policy_bridge_v1.py`

- `tests/test_intake_gate_policy_integration_v1.py`

- `tests/golden/intake_gate_policy/demo_phase.json`

- `tests/golden/intake_gate_policy/sampleco.json`

- `tests/golden/intake_gate_policy/deny_phi.json`

- `tests/golden/intake_gate_policy/deny_web_scraping.json`

- `tests/golden/intake_gate_policy/deny_audio_video.json`

- `tests/golden/intake_gate_policy/deny_scale_exceeds.json`



### Modified

- `routing/intake_gate_layer_v1.py` — G3 policy load/eval/bridge merge + `merge_policy_with_v2()`

- `scripts/run_intake_gate_cli.py` — `--explain`, `--policy-path`, `--include-extended-fixtures`



## Delivered



- Policy SSOT YAML + JSON Schema loader with deny `reason_code` allowlist

- Evaluator (hits only) + bridge → `gate_checks` / `reason_codes` (G1 enum subset)

- Layer merge: policy deny escalates v2 `accept`; never downgrades v2 `reject` / `review_needed`

- CLI explain mode + extended-fixture flag aligned with W4-GUARD-01

- Golden decision snapshots for demo fixtures and four PM-D3 deny cases



## Golden fixtures



| File | Scenario |

|------|----------|

| `tests/golden/intake_gate_policy/demo_phase.json` | Tier A allowlist + v2 `review_needed` |

| `tests/golden/intake_gate_policy/sampleco.json` | Tier B allowlist + v2 `review_needed` |

| `tests/golden/intake_gate_policy/deny_phi.json` | PM-D3 PHI deny → `reject` |

| `tests/golden/intake_gate_policy/deny_web_scraping.json` | PM-D3 web_scraping deny → `reject` |

| `tests/golden/intake_gate_policy/deny_audio_video.json` | PM-D3 audio_video deny → `reject` |

| `tests/golden/intake_gate_policy/deny_scale_exceeds.json` | PM-D3 scale_exceeds deny → `reject` |



Integration test `test_golden_demo_phase_snapshot` asserts against `demo_phase.json`; deny/sampleco goldens are SSOT references for drift review and future snapshot tests.



## verification



```bash

python -m unittest \

  tests.test_intake_gate_policy_loader_v1 \

  tests.test_intake_gate_policy_evaluator_v1 \

  tests.test_intake_gate_policy_bridge_v1 \

  tests.test_intake_gate_policy_integration_v1 \

  tests.test_intake_decision_rules_v2 \

  tests.test_intake_gate_layer_v1 \

  -v

# Ran 48 tests — OK (2026-06-19 convergence pass)

```



## Drift prevention



- **Loader schema**: `load_intake_gate_policy(validate_schema=True)` validates against `shared/schemas/intake_gate_policy_v1.json`; deny `reason_code` must be in loader allowlist (`policy_deny_*` ×4).

- **G1 enum gate**: `bridge_policy_eval()` filters hits through `g1_reason_codes()`; `test_bridge_reason_codes_subset_of_g1_enum` asserts no novel codes.

- **Golden snapshots**: `tests/golden/intake_gate_policy/*.json` capture canonical `decision`, `reason_codes`, `gate_checks`, `policy_version` for key fixtures.

- **Cross-engine regression**: v2 suite (`test_intake_decision_rules_v2`) runs in the same unittest invocation as policy + layer tests (48 total).

- **Integration guard**: `test_layer_merge_deny_overrides_v2_accept` proves PHI deny rejects when v2 would `auto_accept`.



## Notes



- Policy evaluator does **not** set canonical `decision`; layer merges with v2 and applies deny override.

- `intake_decision_rules_v2.py` core unchanged per ticket boundary.

- G4 notify should consume merged `reason_codes` + `outbox_record_path` from gate result / outbox record.



## next



- P75-G4: `intake.gate_decision` notify event via notification gateway

- **linked_in_dashboard**: `docs/WAVE_PROGRESS_DASHBOARD.md` §Phase 7.5 + P8.9 能力摘要（2026-06-19 Scribe 收錄）

