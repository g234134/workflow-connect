# Routing → Tabular Tool Layer Glue v1

> **Ticket**: W4-T1 · Routing → Tabular Tool Layer Glue  
> **Implementation**: `routing/intake_to_tabular_glue.py`  
> **Routing SSOT**: `routing/intake_routing_catalog_v1.yaml` (W2-T1)  
> **Tabular SSOT**: `tools/tabular_tool_catalog_v1.json` (W3-TL-T1)  
> **Date**: 2026-06-10

---

## 1. Purpose and scope

This spec defines a **pure mapping glue** between Wave 2 intake routing catalog `task_type` values and Wave 3-TL Tabular tool layer plans.

**In scope (v1)**

- Tabular MVP family routes only: `tabular.cleaning.mvp`, `tabular.cleaning.regression`, `tabular.intake.new_case`
- Output: auditable **plan dict** with `selector_task_type` and `planned_tools[]`
- Case fixture hints from read-only `intake.json` and `cases/index.json` (`demo_phase`, `sampleco/2026-0001`)

**Out of scope (v1)**

- Gov / HQ / ask routing (`config/routing_policy.yaml`, `_route_task.py`, H-line context)
- General routing engine, eval pipeline, or catalog namespace merge
- Invoking `select_tabular_tools`, Executor, or E2E drivers
- Changing main-chain CLI behavior

---

## 2. Input and output

### 2.1 Function signature

```python
def plan_tabular_route(task_type: str, case_dir: str) -> dict:
    ...
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `task_type` | yes | W2 routing catalog `routes[].task_type` (Tabular family only in v1) |
| `case_dir` | yes | Repo-relative or absolute path to a case directory |

Environment:

| Variable | Default | Meaning |
|----------|---------|---------|
| `TABULAR_ROUTING_GLUE_ENABLED` | `0` | Feature flag; **off by default**. This ticket does not wire glue into main-chain CLIs. |

### 2.2 Success output shape

```python
{
    "ok": True,
    "message": "planned 3 tool(s) for tabular.cleaning.mvp",
    "task_type": "tabular.cleaning.mvp",
    "case_dir": "cases/demo_phase",
    "case_profile": "demo_phase",
    "selector_task_type": "e2e",
    "planned_tools": [
        "validate.eligibility",
        "clean.phase_demo",
        "export.delivery_bundle",
    ],
    "routing_catalog_tool_ids": [...],  # same as W2 route tool_ids
    "orchestration_tool_id": "orchestrate.e2e",  # when present on route
    "inferred_gate_notes": ["phase_like", "phase_demo"],
    "glue_enabled": False,
    "notes": [...],
}
```

### 2.3 Failure output shape

```python
{
    "ok": False,
    "message": "unsupported_task_type",
    "task_type": "gov.observability.eval",
    "case_dir": "cases/demo_phase",
    "glue_enabled": False,
    "notes": ["supported: ['tabular.cleaning.mvp', ...]"],
}
```

Other failure messages: `route_not_found_in_routing_catalog`, catalog validation errors, `planned_tools empty`.

---

## 3. Rule table

| `task_type` | `selector_task_type` | `planned_tools` (from W2 route) | Case notes (v1 fixtures) |
|-------------|----------------------|----------------------------------|--------------------------|
| `tabular.cleaning.mvp` | `e2e` | `validate.eligibility` → `clean.phase_demo` → `export.delivery_bundle` | **demo_phase**: `--force` on clean; `manual_review_required` from index. **sampleco**: `human_review_required`; `multi_row_export` / `schema_ambiguous` in inferred notes |
| `tabular.cleaning.regression` | `e2e` | `orchestrate.mainline_regression` | Wraps `orchestrate.e2e` over demo_phase + sampleco fixtures |
| `tabular.intake.new_case` | `gate_only` | `intake.new_case` | No case_dir intake required for plan; profile notes optional |

**Orchestration alternative (documented, not in `planned_tools`)**

| Route | `orchestration_tool_id` |
|-------|-------------------------|
| `tabular.cleaning.mvp` | `orchestrate.e2e` |

---

## 4. Relationship to Selector / Executor

This glue produces a **pre-plan** only:

1. **W2 routing catalog** supplies authoritative `tool_ids` for the business `task_type`.
2. **Glue** maps that route to W3-TL `selector_task_type` and validates tools against `tabular_tool_catalog_v1.json`.
3. **Future tickets (T3/T4)** may optionally call `select_tabular_tools(case_dir, selector_task_type, ...)` per step or pass `planned_tools` to Executor outbox — **not in W4-T1**.

### Selector alignment (AC-2)

| `planned_tools` step | Suggested `select_tabular_tools` intent |
|----------------------|----------------------------------------|
| `validate.eligibility` | `task_type=gate_only` |
| `clean.phase_demo` | `task_type=clean` or `e2e` (with inferred gate notes) |
| `export.delivery_bundle` | `task_type=bundle` |
| Full E2E plan | `selector_task_type=e2e` on glue output |

Glue does **not** call Selector; alignment is by documented mapping and unittest static checks.

---

## 5. Limits and future work

| Limit | Behavior |
|-------|----------|
| Unknown `task_type` | `ok: false`, `message: unsupported_task_type` |
| Unknown case fixture | Plan still built from routing catalog; profile notes warn limited inference |
| Feature flag off (default) | Main-chain CLIs unchanged; `run_mvp_mainline_regression.py -v` remains 6/6 |
| Gov / ask routes | Out of scope; use W2 catalog docs + Gov routing separately |

**Future (deferred)**

- Wire `TABULAR_ROUTING_GLUE_ENABLED=1` into Local UI or E2E driver (separate ticket)
- Expand case profile detection beyond demo_phase / sampleco
- Optional replay: plan → Selector → Executor outbox chain

---

## 6. Verification

```bash
python -m unittest tests.test_routing_tabular_glue -v
python scripts/run_mvp_mainline_regression.py -v   # main-chain guard (6/6)
```

---

*ROUTING-TOOL-LAYER-GLUE-v1 · W4-T1 · 2026-06-10*
