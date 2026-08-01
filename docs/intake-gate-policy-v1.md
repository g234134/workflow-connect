# Intake Gate Policy v1

> **Ticket**: P75-G3  
> **SSOT**: `routing/intake_gate_policy_v1.yaml`  
> **Schema**: `shared/schemas/intake_gate_policy_v1.json`

## Purpose

Externalize allowlist tiers and PM-approved deny rules so policy changes do not require edits to `intake_decision_rules_v2.py`. The policy evaluator emits **hits** only; canonical `decision` is merged in `intake_gate_layer_v1`.

## YAML structure

| Section | Role |
|---------|------|
| `policy_version` | Fixed `intake_gate_policy_v1` |
| `defaults` | PM-D2/D4/D6 default actions |
| `allowlist_tiers` | Fixture profiles A/B/C/D with optional `requires_extended_fixture_flag` |
| `supported_task_types` | Tabular and non-tabular task_type allow sets |
| `deny_rules` | PHI / web_scraping / audio_video / scale_exceeds with G1 `reason_code` |

## Loader

```python
load_intake_gate_policy(path=None, *, validate_schema=True) -> dict
# {"ok": bool, "policy": dict|None, "error": str|None}
```

Default path: `routing/intake_gate_policy_v1.yaml`.

## Evaluator

```python
evaluate_policy(
    policy,
    *,
    task_type: str,
    case_dir: str,
    intake: dict | None = None,
    flags: dict | None = None,
) -> PolicyEvalResult
```

`flags["include_extended_fixtures"]` aligns with W4-GUARD-01 extended fixture runs.

## Bridge

```python
bridge_policy_eval(eval_result) -> dict
# gate_checks[], reason_codes[], policy_version, profile_* 
```

Deny failures (`POLICY-DENY-*` with `passed=false`) map to G1 reason codes and can override v2 `accept` in the layer.

## Layer merge (G2 + G3)

`evaluate_intake_gate()`:

1. Loads policy (optional `policy_path`)
2. Runs v2 rules engine
3. Evaluates policy + bridge
4. Merges `gate_checks` / `reason_codes`
5. Applies policy override via `merge_policy_with_v2()`

### Relationship to G2 (rules engine vs policy)

| Layer | Responsibility |
|-------|----------------|
| **`intake_decision_rules_v2`** (G2) | Risk signals, glue plan, fixture tier hints, internal `decision` (`auto_accept` / `needs_review` / `reject`) |
| **Policy YAML + evaluator** (G3) | Allowlist tiers, supported `task_type` sets, PM deny rules, unknown-client default — emits **hits only** |
| **`intake_gate_layer_v1`** | Maps v2 → canonical three-state, merges policy hits, produces `intake_gate_result_v1` |

**Deny override strategy**: policy may **escalate** v2 `accept` → `review_needed` or `reject`, but never **downgrade** v2 `reject` or `review_needed`. Precedence: `reject` (deny / unsupported task / non-tabular without flag) > `review_needed` (unknown client, experimental tier without extended flag) > rules-engine base.

**Allowlist vs `review_needed` boundary**:

- Tier A/B on allowlist with supported task → policy adds `allowlist_fixture`; canonical decision still follows v2 (e.g. demo_phase → `review_needed` from `manual_review_required`).
- Unknown client (PM-D6) → policy suggests `review_needed` + `unknown_client_profile`; upgrades v2 `accept` only.
- Tier C/D without `--include-extended-fixtures` → `experimental_fixture` → `review_needed` (not deny).
- Deny rules (PM-D3) → always `reject` when matched, even if v2 returned `auto_accept`.

## CLI

```bash
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --explain \
  --include-extended-fixtures
```

`--explain` prints matched policy rules; no outbox write.

## PM defaults applied

| ID | Policy default |
|----|----------------|
| PM-D2 | unsupported `task_type` → `reject` + `unsupported_task_type` |
| PM-D3 | deny rules → `reject` + `policy_deny_*` |
| PM-D4 | non-tabular without extended flag → `reject` |
| PM-D6 | unknown client → `review_needed` + `unknown_client_profile` |
