# P7.5 Policy Deny Path MVP v1

> **Ticket**: `W1-P75-POLICY-DENY-MVP-v1` · **Wave 1** · P7.5 upstream  
> **SSOT upstream**: `P75-G3` · `routing/intake_gate_policy_v1.yaml` · `routing/intake_gate_layer_v1.py`  
> **MVP scope**: doc + minimal trace fields — **not** full prod gate · **not** staging POST · **not** prod-ready

## Purpose

Document and minimally instrument the **policy deny** upstream chain so Reviewers can audit deny behavior without staging:

`intake_gate_policy_v1.yaml` → policy evaluator/bridge → layer merge → gate result trace → MC-SMOKE `phi_demo` probe → `intake.gate_decision` notify (when run + notifications enabled).

## Policy deny `reason_code` enum (PM-D3)

| `reason_code` | YAML `rule_id` | Match signal |
|---------------|----------------|--------------|
| `policy_deny_phi` | `POLICY-DENY-PHI` | `sensitivity=phi` or PHI intake flags |
| `policy_deny_web_scraping` | `POLICY-DENY-WEB-SCRAPING` | `provenance.source_type=web_scraping` |
| `policy_deny_audio_video` | `POLICY-DENY-AUDIO-VIDEO` | `structure=audio_video` |
| `policy_deny_scale_exceeds` | `POLICY-DENY-SCALE` | row/file/batch scale above YAML limits |

Authoritative mapping: `routing/intake_gate_policy_v1.yaml` `deny_rules` + `routing/intake_gate_policy_bridge_v1.py` `P75_POLICY_DENY_REASON_CODES`.

## Golden fixture ↔ deny对照表

| Golden file | Primary `reason_code` | Canonical `decision` | Intake pattern (summary) |
|-------------|----------------------|----------------------|--------------------------|
| `tests/golden/intake_gate_policy/deny_phi.json` | `policy_deny_phi` | `reject` | `sensitivity=phi` |
| `tests/golden/intake_gate_policy/deny_web_scraping.json` | `policy_deny_web_scraping` | `reject` | `provenance.source_type=web_scraping` |
| `tests/golden/intake_gate_policy/deny_audio_video.json` | `policy_deny_audio_video` | `reject` | `structure=audio_video` |
| `tests/golden/intake_gate_policy/deny_scale_exceeds.json` | `policy_deny_scale_exceeds` | `reject` | `scale.row_count` above limit |

Integration guard: `tests/test_intake_gate_policy_integration_v1.py` `test_golden_deny_fixtures_snapshot`.

## Layer merge rules (policy vs v2)

1. Policy evaluator emits **hits only**; canonical `decision` is merged in `intake_gate_layer_v1`.
2. **Deny escalates**: policy `reject` overrides v2 `auto_accept` (e.g. PHI case where v2 would accept).
3. **Never downgrades**: policy does not weaken v2 `reject` or `review_needed`.
4. Precedence: `reject` (deny / unsupported task) > `review_needed` (unknown client, experimental tier) > v2 base.

See also `docs/intake-gate-policy-v1.md` §Layer merge.

## `phi_demo` MC-SMOKE deny probe

| Field | Value |
|-------|-------|
| `case_ref` | `phi_demo` (ephemeral — **not** a persistent `cases/` fixture) |
| `task_type` | `tabular.intake.new_case` |
| `synthetic_setup` | `phi_deny` in `scripts/run_multi_case_smoke_v1.py` |
| Intake | Same pattern as PHI deny golden (`sensitivity=phi`, owned provenance) |
| Expected gate | `decision=reject`, `p75_policy_decision=policy_deny`, `deny_reason=policy_deny_phi` |
| Expected smoke | `ok=false`; typical `failed_steps`: `gate_run_notify`, `std_case_experiment` (fail-closed) |

**Release pass**: use `--cases demo_phase,sampleco` to exclude deny probe (see `MC-SMOKE` state · Dashboard §representative cases).

## Trace fields (deny path)

| Field | Where | Deny-path meaning |
|-------|-------|-------------------|
| `p75_policy_decision` | `intake_gate_result_v1` (gate layer) | `policy_deny` \| `policy_review` \| `policy_pass` |
| `deny_reason` | gate layer | Primary PM-D3 `reason_code` when `policy_deny`; else `null` |
| `reason_codes[]` | gate layer · notify payload | Includes `policy_deny_*` when matched |
| `gate_checks[]` | gate layer | `POLICY-DENY-*` entries with `passed=false` |
| `intake.gate_decision` | notification gateway / outbox jsonl | Event type when gate run + notifications enabled |
| `multi_case_smoke_run.cases[].failed_steps` | MC-SMOKE summary | Downstream fail-closed steps after gate reject |

Derivation (no external calls): `routing/intake_gate_policy_bridge_v1.py` → `derive_p75_policy_trace()`.

## Verify commands

```bash
# Unit / integration (deny golden + phi_demo trace)
python -m unittest tests.test_intake_gate_policy_integration_v1 -v
python -m unittest tests.test_intake_gate_policy_bridge_v1 -v

# MC-SMOKE deny probe (expect top-level ok=false)
python scripts/run_multi_case_smoke_v1.py --cases phi_demo --format json

# Doc grep sanity
rg "reason_code|phi_demo|policy deny" docs/p75-policy-deny-path-mvp-v1.md
```

## Non-claims

- MVP doc + trace fields **≠** full intake gate **≠** prod deny SLA **≠** staging POST verified.
- `phi_demo` is an ephemeral synthetic probe; do not treat as production case fixture.
- G-1–G-5 resume-loop **runtime** is out of scope (Wave 2).
- Does not change existing staging behavior or Phase% on Dashboard.

## Cross-references

- `04_Workflows/tickets/P75-G3-intake-gate-policy-allowlist-denylist-v1_state.md`
- `04_Workflows/tickets/MC-SMOKE-multi-case-smoke-runner-v1_state.md`
- `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7.6
- Downstream consumer: `W1-P75-TRACE-UPSTREAM-v1` → `docs/p75-intake-gate-control-plane-trace-v1.md`
- P7.5 upstream entry index: `docs/p75-upstream-entry-index-v1.md`（`W1-P75-UPSTREAM-ENTRY-INDEX-v1`）
