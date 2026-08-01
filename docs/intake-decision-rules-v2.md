# Intake Decision Rules v2

> **Ticket**: W8-T2 · decision-rules-v2-profile-and-reject-reduction · **W9-T2** non-tabular helper  
> **Implementation**: `routing/intake_decision_rules_v2.py`  
> **Glue dependency**: `routing/intake_to_tabular_glue.py` (W4-T1) · non-tabular glue planned W9-T4  
> **Upstream**: `docs/intake-decision-rules-v1.md` · `docs/agent-standard-line-governance-view-v2.md` · `docs/non-tabular-shadow-flow-blueprint-v1.md`  
> **Date**: 2026-06-10  
> **Status**: decision helper only — **not** wired to main-chain intake or routing

---

## 1. Purpose and scope

v2 extends W5-T1 with **A/B/C/D fixture profile tiers**, **tiered risk signals**, and **fewer false-positive rejects** for experimental Tabular fixtures while keeping production allowlist (`demo_phase` / `sampleco`) behavior stable.

**In scope (v2 + W9-T2)**

- Tabular family `task_type` values (same as v1)
- Profile tiers **A** (demo_phase) · **B** (sampleco) · **C** (additional_demo) · **D** (sandbox_client)
- **Non-Tabular** family `non_tabular.*` with profile tiers **NT-A** (document extraction) · **NT-B** (log analysis)
- Signal classes: `low` / `medium` / `high`
- Explicit reject conditions (hard failures only)
- Non-Tabular conservative `needs_review` default (v1 helper); corrupt/unparseable intake → `reject`
- v1 fallback on internal errors (`use_v1_fallback=True`)

**Out of scope (v2 + W9-T2)**

- Modifying main-chain CLIs, Local UI, Gov routing
- Changing W5-T1 production decision allowlist (`demo_phase` / `sampleco` only)
- Non-Tabular `auto_accept` (W9-T2 conservative; HITL still required)
- Non-Tabular glue / tool execution (W9-T3/T4)
- LLM judge or intake state mutation

---

## 2. API

### 2.1 Function

```python
from routing.intake_decision_rules_v2 import evaluate_intake_decision_v2

result = evaluate_intake_decision_v2(
    "tabular.cleaning.mvp",
    "cases/sandbox_client",
    use_v1_fallback=True,
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `task_type` | yes | — | W2 routing catalog `task_type` |
| `case_dir` | yes | — | Repo-relative or absolute case path |
| `use_v1_fallback` | no | `True` | On v2 internal error, delegate to v1 and annotate `rules_version=v1_fallback` |

### 2.2 Success output shape (v2 additions)

```python
{
    "ok": True,
    "rules_version": "v2",
    "task_type": "tabular.cleaning.mvp",
    "case_dir": "cases/sandbox_client",
    "flow_family": "tabular",
    "fixture_profile": "sandbox_client",
    "fixture_profile_tier": "D",
    "profile_maturity": "experimental",
    "decision": "needs_review",
    "risk_level": "medium",
    "signals": {
        "low": [],
        "medium": ["experimental_fixture_profile"],
        "high": [],
    },
    "rationale": [
        "rules_version=v2",
        "fixture_profile_tier=D",
        "profile_maturity=experimental",
        "experimental_fixture",
        "medium_risk_signals=['experimental_fixture_profile']",
        ...
    ],
    "suggested_route": { ... },
    "glue_plan": { ... },
}
```

### 2.3 Non-Tabular family (W9-T2)

Supported `task_type` values (underscore family; hyphen alias `non-tabular.*` normalized):

- `non_tabular.document.extract` → profile **NT-A**
- `non_tabular.log.analyze` → profile **NT-B**
- `non_tabular.generic.transform` → profile `unknown`

```python
{
    "ok": True,
    "rules_version": "v2",
    "task_type": "non_tabular.document.extract",
    "case_dir": "cases/docu-corp/2026-0001",
    "flow_family": "non_tabular",
    "fixture_profile": "docu-corp",
    "fixture_profile_tier": "NT-A",
    "case_profile_tier": "NT-A",
    "profile_maturity": "shadow",
    "decision": "needs_review",
    "risk_level": "medium",
    "signals": {
        "low": [],
        "medium": [
            "non_tabular_shadow_v1",
            "conservative_review",
            "document_extraction_profile"
        ],
        "high": []
    },
    "suggested_route": {
        "selector_task_type": "non_tabular.document.extract",
        "planned_tools": [],
        "shadow_only": true
    },
    "shadow_flow_hook": {
        "eligible": true,
        "implemented_by": "W9-T2-non-tabular-decision-rules-v1",
        "glue_planner": "W9-T4-non-tabular-glue-layer-v1"
    }
}
```

### 2.4 Other families reject (shadow-flow hook)

Non-`tabular.*` / non-`non_tabular.*` families (e.g. `gov.*`) remain **reject**:

```python
{
    "ok": True,
    "rules_version": "v2",
    "decision": "reject",
    "flow_family": "non_tabular",
    "message": "non_tabular_family",
    "shadow_flow_hook": {
        "eligible": False,
        "future_ticket": "W8-T5-non-tabular-intake-shadow",
    },
}
```

---

## 3. Fixture profile detection (A/B/C/D)

| Tier | Profile ID | Source case | Maturity | Decision allowlist | Cleaning decision |
|------|------------|-------------|----------|-------------------|-------------------|
| **A** | `demo_phase` | `cases/demo_phase` | stable | yes | `needs_review` (medium signals) |
| **B** | `sampleco` | `cases/sampleco/2026-0001` | stable | yes | `needs_review` (schema / human review) |
| **C** | `additional_demo` | `cases/additional_demo` | experimental | no | `needs_review` (conservative) |
| **D** | `sandbox_client` | `cases/sandbox_client` | experimental | no | `needs_review` (conservative) |
| unknown | other | — | unknown | no | `needs_review` (not reject) |

Detection uses W4-T1 glue `case_profile` plus v2 tier map. Experimental profiles (C/D) are **recognized** — v2 emits `experimental_fixture_profile` instead of v1's `unknown_fixture_profile`.

`tabular.intake.new_case` on any recognized profile → `auto_accept` when glue ok (intake request, not cleaning execution).

---

## 3.1 Non-Tabular fixture profile detection (NT-A / NT-B)

| Tier | Profile / case hint | `task_type` | Maturity | Cleaning decision (W9-T2 v1) |
|------|---------------------|-------------|----------|------------------------------|
| **NT-A** | `docu-corp` · `content_type` document/mixed | `non_tabular.document.extract` | shadow | `needs_review` / medium |
| **NT-B** | `log-analytics-co` · `content_type` logs · `schema_hint=semi-structured` | `non_tabular.log.analyze` | shadow | `needs_review` / medium |
| unknown | `non_tabular.generic.transform` or unrecognized hints | — | unknown | `needs_review` / medium |

Profile resolution order:

1. `task_type` suffix (document.extract → NT-A; log.analyze → NT-B)
2. `case_dir` path segment (`docu-corp`, `log-analytics-co`)
3. `intake.json` fields (`content_type`, `schema_hint`)

**Reject (R-NT1)** — only hard format failures:

- `intake.json` present but JSON invalid / empty → `intake_unparseable` / high
- `intake.json` marks corrupt or inaccessible content (`_corrupt`, `format_status=corrupt`, `content_accessible=false`) → `content_corrupt_or_unreadable` / high
- Missing `case_dir` directory → `case_dir_not_found` / high

**Not reject in W9-T2 v1**: valid non_tabular intake with recognized or unknown profile → conservative `needs_review`.

---

## 4. Signal classification

### 4.1 Low risk (informational)

Does **not** alone force `needs_review` on stable allowlist fixtures:

- `phase_like`
- `phase_demo`
- `review_needed`
- `multi_row_export`

### 4.2 Medium risk (HITL / review path)

Forces `needs_review` on cleaning tasks (except experimental tier which is always `needs_review`):

- `schema_ambiguous`
- `human_review_required`
- `manual_review_required`
- `experimental_fixture_profile` (C/D recognized profiles)
- `unknown_fixture_profile` (truly unknown profiles)

### 4.3 High risk (reject triggers)

Only hard failures — **not** profile tier alone:

- `non_tabular_family` (non-tabular, non-`non_tabular.*` families only)
- `unsupported_task_type` (Tabular only)
- `case_dir_not_found`
- `glue_plan_failed` (Tabular only)
- `intake_unparseable` (Non-Tabular: invalid `intake.json`)
- `content_corrupt_or_unreadable` (Non-Tabular: R-NT1)

---

## 5. Reject conditions (explicit)

| # | Condition | `decision` | `message` |
|---|-----------|------------|-----------|
| R1 | `task_type` not `tabular.*` and not `non_tabular.*` | `reject` | `non_tabular_family` |
| R2 | Tabular but not in supported set | `reject` | `unsupported_task_type` |
| R3 | Cleaning task + missing `case_dir` | `reject` | `case_dir_not_found` |
| R4 | W4-T1 glue `ok: false` | `reject` | `glue_plan_failed` |
| R5 | Non-Tabular + invalid `intake.json` | `reject` | `intake_unparseable` |
| R6 | Non-Tabular + corrupt/inaccessible content (R-NT1) | `reject` | `content_corrupt_or_unreadable` |

**Not reject in v2** (v1 improvement):

- Experimental fixture (C/D) with valid glue → `needs_review`
- Unknown fixture profile with valid glue → `needs_review`
- Medium risk signals alone → `needs_review`

---

## 6. v1 vs v2 behavior summary

| Fixture | v1 cleaning | v2 cleaning | v2 delta |
|---------|-------------|-------------|----------|
| A: demo_phase | `needs_review` | `needs_review` | + tier A · tiered signals |
| B: sampleco | `needs_review` | `needs_review` | + tier B · tiered signals |
| C: additional_demo | `needs_review` + `unknown_fixture_profile` | `needs_review` + `experimental_fixture_profile` | recognized tier C |
| D: sandbox_client | `needs_review` + `unknown_fixture_profile` | `needs_review` + `experimental_fixture_profile` | recognized tier D |
| non-tabular `non_tabular.*` | `reject` | `needs_review` (NT-A/NT-B) | W9-T2 conservative helper |
| gov / other families | `reject` | `reject` | unchanged |

---

## 7. CLI demo

```bash
# v2 module CLI
python routing/intake_decision_rules_v2.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/sandbox_client \
  --json

# Agent demo CLI (opt-in v2; Tabular + non_tabular.*)
python scripts/run_agent_intake_decision_demo.py \
  --task-type non_tabular.document.extract \
  --case-dir cases/docu-corp/2026-0001 \
  --use-v2 \
  --format json
```

Default Agent demo remains **v1** (`--use-v2` opt-in).

---

## 8. Verification

```bash
python -m unittest tests.test_intake_decision_rules_v2 -v
python -m unittest tests.test_intake_decision_rules_v1 tests.test_agent_intake_decision_demo -v
```

---

## 9. Cross-references

- v1 spec: `docs/intake-decision-rules-v1.md`
- Non-Tabular blueprint: `docs/non-tabular-shadow-flow-blueprint-v1.md` §2 / §5 (NT-A / NT-B)
- Governance v2: `docs/agent-standard-line-governance-view-v2.md` §2.2 · R-NT1–R-NT5 (blueprint §4.2)
- Skill cards: `docs/skill-cards-v2.md` (Card A–D; NT-A/NT-B in blueprint §5.1)
- Wave 9: `docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 9
