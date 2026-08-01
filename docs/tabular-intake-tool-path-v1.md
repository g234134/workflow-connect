# Tabular Intake Tool Path v1

> **Ticket**: W4-T3-A · Intake · Tabular Tool Path（獨立 CLI · 預演）  
> **Implementation**: `scripts/run_tabular_intake_tool_path.py`  
> **Glue**: `routing/intake_to_tabular_glue.py` (W4-T1)  
> **Selector**: `tools/tabular_tool_selector.py` (W3-TL-T2)  
> **Catalog SSOT**: `tools/tabular_tool_catalog_v1.json` (W3-TL-T1)  
> **Date**: 2026-06-10

---

## 1. Purpose and scope

This spec defines an **independent CLI dry-run preview** for the Tabular MVP intake → tool path. It chains W4-T1 routing glue with W3-TL Selector recommendations and a **local** executor plan (planned commands and expected artifacts) without spawning subprocesses or writing outbox files.

**In scope (v1 · version A)**

- Tabular family `task_type` values: `tabular.cleaning.mvp`, `tabular.cleaning.regression`, `tabular.intake.new_case`
- Allowlist fixtures: `cases/demo_phase`, `cases/sampleco/2026-0001` (and any case with valid `intake.json`)
- Structured JSON output: `glue_plan`, `selector_view`, `executor_plan`

**Out of scope (v1 · version A)**

- Modifying `scripts/new_cleaning_case.py`, `app/local_ui.py`, or main-chain E2E drivers
- Invoking `execute_tabular_tool` or writing `outbox/` files
- Gov / HQ routing (`config/routing_policy.yaml`, `routing_policy_loader`)
- Version B single-step execute / outbox (deferred to W4-T3-B)

---

## 2. CLI interface

### 2.1 Command

```bash
python scripts/run_tabular_intake_tool_path.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase

python scripts/run_tabular_intake_tool_path.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --json
```

### 2.2 Parameters

| Flag | Required | Description |
|------|----------|-------------|
| `--task-type` | yes | W2 routing catalog `task_type` (must be `tabular.*` family) |
| `--case-dir` | yes | Repo-relative or absolute path to case directory |
| `--json` | no | Emit full result as JSON (default: human-readable table) |

### 2.3 Exit code semantics

| Scenario | Exit code | Notes |
|----------|-----------|-------|
| CLI completed (success or structured failure) | `0` | Caller inspects `ok` in JSON |
| Unexpected Python exception | non-zero | Standard traceback |

Structured failures (`ok: false`) use exit `0` so orchestrators can parse JSON without shell failure.

---

## 3. JSON schema

### 3.1 Top-level success shape

```json
{
  "ok": true,
  "message": "dry-run preview for tabular.cleaning.mvp",
  "task_type": "tabular.cleaning.mvp",
  "case_dir": "cases/demo_phase",
  "mode": "dry_run_preview",
  "glue_plan": { ... },
  "selector_view": { ... },
  "executor_plan": [ ... ],
  "notes": [ ... ]
}
```

### 3.2 `glue_plan` (source: W4-T1 `plan_tabular_route`)

| Field | Type | Description |
|-------|------|-------------|
| `selector_task_type` | string | W3-TL intent (`e2e`, `gate_only`, …) |
| `planned_tools` | string[] | Ordered tool_ids from W2 routing catalog |
| `case_profile` | string | Inferred fixture profile (`demo_phase`, `sampleco`, …) |
| `inferred_gate_notes` | string[] | Gate schema notes for Selector |
| `notes` | string[] | Glue audit notes |

### 3.3 `selector_view` (source: W3-TL `select_tabular_tools`)

| Field | Type | Description |
|-------|------|-------------|
| `selector_task_type` | string | Overall intent from glue |
| `ok` | bool | Overall selector success |
| `selector_rule_id` | string | Rule id from Selector |
| `candidates` | object[] | Overall `candidate_tools` |
| `per_step` | object[] | Per `planned_tools` step with step-level selector result |
| `notes` | string[] | Alignment / warning notes |

Each candidate object includes `tool_id`, `reason`, optional `requires_force`, `human_review_required`.

### 3.4 `executor_plan[]` (source: catalog + local plan builder; **not** Executor module)

| Field | Type | Description |
|-------|------|-------------|
| `tool_id` | string | Catalog tool id |
| `dry_run` | bool | Always `true` in v1-A |
| `planned_command` | string | argv string that would be executed |
| `expected_artifacts` | object[] | `{kind, path, logical_key?}` repo-relative pointers |
| `requires_force` | bool | Optional; from Selector candidate |
| `human_review_required` | bool | Optional; from Selector candidate |

### 3.5 Failure shapes

**Non-tabular family**

```json
{
  "ok": false,
  "message": "unsupported_family",
  "task_type": "gov.observability.eval",
  "case_dir": "cases/demo_phase",
  "mode": "dry_run_preview",
  "notes": ["supported families: tabular.* (...)"]
}
```

**Glue plan failure** (e.g. unknown tabular task_type not in glue allowlist)

```json
{
  "ok": false,
  "message": "unsupported_task_type",
  "glue_plan": { ... },
  "notes": [ ... ]
}
```

---

## 4. Relationship to existing flows

| Entry | Role | W4-T3-A relationship |
|-------|------|----------------------|
| `scripts/new_cleaning_case.py` | Manual intake CLI | **Unchanged**; preview does not create cases |
| `app/local_ui.py` | Local UI intake | **Unchanged**; future ticket may display preview JSON |
| `scripts/run_case_e2e_validation.py` | Single-case E2E | **Unchanged**; preview does not run E2E |
| `scripts/run_mvp_mainline_regression.py` | Mainline regression | **Unchanged**; guard test remains 6/6 |
| `scripts/run_routing_eval.py` | Routing eval dry-run | **Complementary**; eval cross-checks catalog/glue/policy; this CLI previews full tool path for one case |
| `routing/intake_to_tabular_glue.py` | Plan-only glue | **Consumed** as step 1 |
| `tools/tabular_tool_selector.py` | Tool recommendations | **Called read-only** as step 2 |
| `tools/tabular_tool_executor.py` | Subprocess + outbox | **Not invoked** in v1-A |

The preview CLI is for **operators and orchestrators** to audit the Tabular path before wiring into UI or version B execute.

**P7.5 intake upstream（鄰票）**：人類接案 `new_cleaning_case` → P75 gate 的 canonical 命令與 `--run-gate`／`--run-p75-gate` 邊界見 `docs/p75-intake-cli-upstream-mvp-v1.md`（`W1-P75-INTAKE-CLI-MVP-v1`）。本檔仍為 W4-T3-A tool-path preview SSOT，**不**取代該上游敘事。

---

## 5. Limits and future work

| Limit | Behavior |
|-------|----------|
| No subprocess | `planned_command` is informational only |
| No outbox | No `outbox/<case_ref>/*.json` or `events.jsonl` writes |
| No case mutation | Does not modify `cases/*/reports/*` or cleaned CSV |
| Gov routes | `unsupported_family`; use `run_routing_eval.py` for Gov cross-check |
| Regression route | `tabular.cleaning.regression` plans `orchestrate.mainline_regression` |

**Future (W4-T3-B and beyond)**

- Optional single-step `execute_tabular_tool(dry_run=False)` with outbox
- Local UI panel showing preview JSON
- CI smoke: preview CLI on demo_phase fixture

---

## 6. Verification

```bash
python -m unittest tests.test_tabular_intake_tool_path -v
python scripts/run_tabular_intake_tool_path.py \
  --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json
python scripts/run_mvp_mainline_regression.py -v
```

---

*TABULAR-INTAKE-TOOL-PATH-v1 · W4-T3-A · 2026-06-10*
