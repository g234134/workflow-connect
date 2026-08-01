# Intake Decision Rules v1

> **Ticket**: W5-T1 · Intake Decision Rules  
> **Implementation**: `routing/intake_decision_rules_v1.py`  
> **Glue dependency**: `routing/intake_to_tabular_glue.py` (W4-T1)  
> **Date**: 2026-06-10  
> **Status**: decision helper only — **not** wired to main-chain intake or routing

---

## 1. Purpose and scope

This spec defines a **pure decision helper** that evaluates whether a Tabular MVP intake case should be **auto-accepted**, sent for **human review**, or **rejected**, based on W4-T1 glue plans and fixture metadata.

**In scope (v1)**

- Tabular family `task_type` values: `tabular.cleaning.mvp`, `tabular.cleaning.regression`, `tabular.intake.new_case`
- Structured output: `decision`, `risk_level`, `rationale`, `suggested_route`
- Allowlist fixtures: `demo_phase`, `sampleco` (via glue `case_profile`)

**Out of scope (v1)**

- Modifying `scripts/new_cleaning_case.py`, `app/local_ui.py`, or main-chain E2E drivers
- Gov / HQ routing (`config/routing_policy.yaml`, `_route_task.py`)
- LLM judge, payment, or production intake state mutation
- Wiring into main-chain routing (helper only)

---

## 2. API

### 2.1 Function

```python
from routing.intake_decision_rules_v1 import evaluate_intake_decision

result = evaluate_intake_decision("tabular.cleaning.mvp", "cases/demo_phase")
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `task_type` | yes | W2 routing catalog `task_type` (Tabular family only in v1) |
| `case_dir` | yes | Repo-relative or absolute path to case directory |

### 2.2 Success output shape

```python
{
    "ok": True,
    "task_type": "tabular.cleaning.mvp",
    "case_dir": "cases/demo_phase",
    "decision": "needs_review",  # auto_accept | needs_review | reject
    "risk_level": "medium",      # low | medium | high
    "rationale": [
        "task_type=tabular.cleaning.mvp",
        "decision=needs_review",
        "risk_level=medium",
        "case_profile=demo_phase",
        "allowlist_fixture",
        "risk_signals=['manual_review_required', 'review_needed']",
        "glue_plan_ok: planned 3 tool(s) for tabular.cleaning.mvp",
    ],
    "suggested_route": {
        "selector_task_type": "e2e",
        "planned_tools": [
            "validate.eligibility",
            "clean.phase_demo",
            "export.delivery_bundle",
        ],
        "orchestration_tool_id": "orchestrate.e2e",
    },
    "message": "decision=needs_review risk=medium",
    "glue_plan": { ... },  # audit subset from W4-T1
}
```

### 2.3 Reject output shape

Reject decisions still return `ok: True` (structured decision, not a Python exception). `suggested_route` is `null`.

```python
{
    "ok": True,
    "decision": "reject",
    "risk_level": "high",
    "message": "non_tabular_family",  # or unsupported_task_type / case_dir_not_found / glue_plan_failed
    "suggested_route": None,
    "rationale": [...],
}
```

---

## 3. Rule table (v1)

| Condition | `decision` | `risk_level` |
|-----------|------------|--------------|
| `task_type` not `tabular.*` | `reject` | `high` |
| `task_type` not in supported Tabular set | `reject` | `high` |
| `case_dir` missing (cleaning tasks) | `reject` | `high` |
| W4-T1 glue `ok: false` | `reject` | `high` |
| `tabular.intake.new_case` + glue ok | `auto_accept` | `low` |
| Allowlist fixture + glue ok + no medium signals | `auto_accept` | `low` |
| Tabular family + medium risk signals in glue notes / gate notes | `needs_review` | `medium` |
| Non-allowlist fixture + glue ok | `needs_review` | `medium` |

### 3.1 Medium risk signals

Detected from glue `notes[]`, `inferred_gate_notes[]`, and `cases/index.json` profile hints:

- `schema_ambiguous`
- `human_review_required`
- `manual_review_required`
- `review_needed`
- `unknown_fixture_profile` (non-allowlist case)

### 3.2 Allowlist fixtures

| Profile | Typical case_dir | v1 cleaning decision | Notes |
|---------|------------------|----------------------|-------|
| `demo_phase` | `cases/demo_phase` | `needs_review` for `tabular.cleaning.mvp` | `manual_review_required` per `cases/index.json` |
| `sampleco` | `cases/sampleco/2026-0001` | `needs_review` | `human_review_required`, `schema_ambiguous` in glue gate notes |

`tabular.intake.new_case` on allowlist fixtures → `auto_accept` (intake request, not cleaning execution).

---

## 4. Relationship to glue / selector

1. **W4-T1 glue** (`plan_tabular_route`) supplies `selector_task_type` and `planned_tools`.
2. **Decision rules** layer classifies accept/review/reject from glue audit notes and fixture profile.
3. **Future tickets** may optionally call this helper before intake CLI or Local UI — **not in W5-T1**.

---

## 5. CLI demo

```bash
python routing/intake_decision_rules_v1.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --json

python routing/intake_decision_rules_v1.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/sampleco/2026-0001 \
  --json
```

---

## 6. Verification

```bash
python -m unittest tests.test_intake_decision_rules_v1 -v
```

---

## 7. Cross-references

- W2 routing catalog: `docs/intake-routing-catalog-v1.md`
- W4-T1 glue: `docs/routing-tool-layer-glue-v1.md`
- W4-T3-A intake tool path: `docs/tabular-intake-tool-path-v1.md`
- Wave dashboard: `docs/WAVE_PROGRESS_DASHBOARD.md` § Wave 5
