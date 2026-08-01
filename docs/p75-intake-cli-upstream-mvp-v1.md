# P7.5 Intake CLI Upstream MVP v1

> **Ticket**: `W1-P75-INTAKE-CLI-MVP-v1` · **Wave 1** · P7.5 upstream  
> **Scope**: canonical case-create → P75 gate CLI path + minimal `--run-p75-gate` wiring  
> **Not**: Local UI · dispatch · notify transport · E2E delivery · prod intake API

## Purpose

Close the narrative gap between **Wave 3 intake CLI** (`new_cleaning_case.py`) and **P75-G2 gate CLI** (`run_intake_gate_cli.py`) so human intake and MP-SMOKE step 1 share the same upstream commands.

## Canonical upstream commands (≥3 steps)

### 1. Create case + intake draft

```bash
python scripts/new_cleaning_case.py \
  --client-ref acme \
  --product-sku CLEAN-BASIC \
  --source-file cases/demo_phase/raw/Phase.csv \
  --encoding utf-8-sig
```

### 2. Run P75 gate preview on new case (MVP flag)

```bash
python scripts/new_cleaning_case.py \
  --client-ref acme \
  --product-sku CLEAN-BASIC \
  --source-file cases/demo_phase/raw/Phase.csv \
  --encoding utf-8-sig \
  --run-p75-gate
```

Prints summary `gate_status` (= gate `decision`) and `reason_codes` to stdout. Uses **preview** mode — **no** outbox write · **no** `eligibility_result.json`.

### 3. Full P75 gate CLI (existing case · run + optional notify)

```bash
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/acme/<YYYY-NNNN> \
  --mode preview --explain

python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run --enable-notifications --format json
```

Optional flags: `--policy-path` · `--include-extended-fixtures` · `--outbox-root`.

## Boundary table

| Entry | Tool | Gate layer | Outbox | Notify | Use when |
|-------|------|------------|--------|--------|----------|
| P2 eligibility | `new_cleaning_case.py --run-gate` | `check_case_eligibility` (Wave 3) | No | No | Legacy P2 review path · W-MVP-W3 demos |
| P75 upstream MVP | `new_cleaning_case.py --run-p75-gate` | `evaluate_intake_gate` preview | No | No | New case → P75 decision snapshot |
| P75 full CLI | `run_intake_gate_cli.py` | `evaluate_intake_gate` preview/run | run mode only | run + flag/env | MP-SMOKE step 1–2 equivalent · integrators |

**Do not** conflate `--run-gate` (P2 `eligibility`) with `--run-p75-gate` (P75 `decision` / `reason_codes` / policy trace fields).

## W-MVP-W3 boundary

| Concern | W-MVP-W3 (`W-MVP-W3-INTAKE-CLI`) | This ticket |
|---------|-----------------------------------|-------------|
| Case directory bootstrap | **Yes** — template copy + `intake.json` | Consumes same CLI |
| P2 `--run-gate` | **Yes** — `check_case_eligibility` | Unchanged |
| P75 gate layer | Out of W3 scope | **Yes** — `--run-p75-gate` + doc |
| E2E / dispatch / bundle | Out of W3 scope | Still out of scope |

## Trace fields (upstream)

| Field | `--run-p75-gate` stdout | Full gate CLI |
|-------|-------------------------|---------------|
| `gate_status` | summary line (= `decision`) | `decision:` text or json |
| `reason_codes` | summary + JSON block | json / `--explain` |
| `p75_policy_decision` | JSON when policy evaluated | gate result json |
| `deny_reason` | JSON when policy deny | gate result json |
| `intake.gate_decision` | **Not emitted** (preview only) | run + `--enable-notifications` |

Full trace chain: `docs/p75-intake-gate-control-plane-trace-v1.md`.

## Verify commands

```bash
python scripts/new_cleaning_case.py --help
python -m unittest tests.test_new_cleaning_case -v
rg "run_intake_gate_cli|new_cleaning_case|run-p75-gate" docs/p75-intake-cli-upstream-mvp-v1.md
```

## Non-claims

- Upstream MVP **≠** E2E delivery **≠** W4 dispatch **≠** prod intake API.
- `--run-p75-gate` preview **≠** durable outbox record **≠** notify transport.
- Does not replace Local UI (`W-MVP-W5-LOCAL-UI`).

## Cross-references

- `04_Workflows/tickets/W-MVP-W3-INTAKE-CLI_state.md`
- `04_Workflows/tickets/P75-G2-intake-gate-layer-and-outbox-record-v1_state.md`
- `docs/tabular-intake-tool-path-v1.md`
- `docs/p75-intake-gate-control-plane-trace-v1.md` (downstream trace SSOT)
- `docs/p75-policy-deny-path-mvp-v1.md` (deny trace fields)
- `docs/p75-upstream-entry-index-v1.md` (P7.5 upstream entry index · `W1-P75-UPSTREAM-ENTRY-INDEX-v1`)
