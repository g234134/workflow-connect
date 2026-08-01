# Tabular Tool Selector Spec v1

> **Upstream contract（跨轨 SSOT）**：`docs/tool-catalog-and-selector-contract-v1.md` — Tabular selector 输入/输出、`plan_only`、trace 串接以 contract §4 为准；本档为 **实现附录**（规则表与 fixture 示例）。  
> **Ticket**: W3-TL-T2 · Tabular Tool Selector  
> **Catalog SSOT**: `tools/tabular_tool_catalog_v1.json` (W3-TL-T1)  
> **Implementation**: `tools/tabular_tool_selector.py`  
> **Date**: 2026-06-10

---

## 1. Purpose and scope

This spec defines the **recommendation-only** selector for the Tabular MVP tool layer. The selector reads case metadata (`intake.json`), optional gate schema notes (`dimensions.schema.notes`), and a `task_type` intent, then returns 1–2 auditable `candidate_tools[]` entries.

**In scope (v1)**

- Standard fixtures: `cases/demo_phase`, `cases/sampleco/2026-0001`
- Task intents: `gate_only`, `clean`, `bundle`, `e2e`
- Tool IDs from `tabular_tool_catalog_v1.json` only

**Out of scope (v1)**

- Invoking tools or changing E2E driver behavior
- ML rankers, embeddings, ask RAG selector, `config/routing_policy.yaml`
- Parsing raw CSV content (metadata and gate notes only)

---

## 2. Input and output contract

### 2.1 Function signature

```python
def select_tabular_tools(
    case_dir: str,
    task_type: str,  # "gate_only" | "clean" | "bundle" | "e2e"
    intake: dict | None = None,
    gate_notes: list[str] | None = None,
) -> dict:
    ...
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `case_dir` | yes | Path to case directory (e.g. `cases/demo_phase`) |
| `task_type` | yes | Selection intent |
| `intake` | no | Parsed `intake.json`; loaded from `case_dir/intake.json` when omitted |
| `gate_notes` | conditional | Gate `dimensions.schema.notes` (e.g. `phase_like`, `multi_row_export`). Required non-empty for `clean` / `e2e` when caller supplies the parameter; inferred for known fixtures when omitted |

### 2.2 Output shape

```python
{
    "ok": True,
    "message": "using phase_demo cleaner with force",
    "selector_rule_id": "phase_demo.clean.force",
    "candidate_tools": [
        {
            "tool_id": "clean.phase_demo",
            "reason": "phase_like schema with review_needed gate",
            "requires_force": True,
            "human_review_required": False
        }
    ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ok` | bool | Whether a recommendation (or valid gate-only path) was produced |
| `message` | str | Human-readable summary |
| `selector_rule_id` | str | Auditable rule identifier |
| `candidate_tools` | list | 0–2 candidates; empty when `ok=false` |

Each candidate must include: `tool_id`, `reason`, `requires_force`, `human_review_required`.

Before returning candidates, the selector validates each `tool_id` against the catalog (exists and `enabled=true`).

### 2.4 Approved registry consumption (W10-T2)

Read-only integration with `skills/approved_registry.json`. Env gate: `TABULAR_APPROVED_REGISTRY_ENABLED` (default **off**).

**When env is unset or `0`** — no registry load; success output is semantically and key-set identical to pre-W10-T2 (no top-level `approved_registry` sidecar).

**When env is `1`** — after catalog `enabled` validation and before returning success, load the registry and resolve an approved `tool_id` set:

| Mapping step | Rule |
|--------------|------|
| 1. Eligibility | Skip rows with `selector_eligible: false` |
| 2. Preferred | Use non-empty `tool_ids: ["clean.phase_demo", ...]` on the registry row (explicit bind; no W5-T1 promote change required) |
| 3. Fallback | Static `_SKILL_ID_TO_TOOL_IDS` in `tabular_tool_selector.py` (e.g. `draft-clean-basic-job-001` → `clean.phase_demo`; `skill-tabular-validate-eligibility` → `validate.eligibility`; `skill-tabular-export-delivery` → `export.delivery_bundle`) |

**When registry is missing, empty, malformed, or has no resolvable `tool_id` mappings** — graceful **degrade-open**: `ok=true`, `candidate_tools` unchanged, top-level `approved_registry.degraded=true` plus a human-readable `message` (and optional `approved_tool_count`). Candidates are **not** blocked.

**When registry loads with resolvable approvals** — keep only candidates whose `tool_id` is in the approved set; attach `approval_status=approved` on each kept candidate; top-level `approved_registry` sidecar records `enabled`, `degraded=false`, and summary fields.

**When all candidates are filtered out** — `ok=false`, `selector_rule_id=error.registry_not_approved`, empty `candidate_tools`.

Catalog `enabled=false` checks still run **before** registry filtering (W3-TL-T2 unchanged). v1 uses **drop** (not `approval_status=blocked` sidecar) for unapproved tools.

**Fail-closed policy** (opt-in via `TABULAR_APPROVED_REGISTRY_STRICT=1`):
- When strict mode is enabled alongside `TABULAR_APPROVED_REGISTRY_ENABLED=1`, the selector treats any registry load/malformation/emptiness as a **blocking error** rather than graceful degrade.
- Error result: `ok=false`, `selector_rule_id=error.registry_fail_closed`, empty `candidate_tools[]`.
- Strict mode is **default off**; prod remains on degrade-open policy unless explicitly enabled.

### 2.3 Fixture examples

**demo_phase + clean**

```python
select_tabular_tools(
    "cases/demo_phase",
    "clean",
    gate_notes=["phase_like", "phase_demo"],
)
# → clean.phase_demo, requires_force=True, human_review_required=False
```

**sampleco/2026-0001 + clean**

```python
select_tabular_tools(
    "cases/sampleco/2026-0001",
    "clean",
    gate_notes=["phase_like", "multi_row_export", "schema_ambiguous"],
)
# → clean.phase_demo, requires_force=False, human_review_required=True
```

---

## 3. Rule table

| `selector_rule_id` | Conditions | `candidate_tools` | Flags |
|--------------------|------------|-------------------|-------|
| `gate_only.eligibility` | `task_type=gate_only`; intake + raw present | `validate.eligibility` | — |
| `phase_demo.clean.force` | `task_type` ∈ `{clean, e2e}`; notes contain `phase_like` / `phase_demo`; no `multi_row_export` / `schema_ambiguous`; demo_phase / review_needed profile | `clean.phase_demo` | `requires_force=true` |
| `sampleco.clean.review` | `task_type` ∈ `{clean, e2e}`; notes contain `multi_row_export` or `schema_ambiguous` | `clean.phase_demo` | `human_review_required=true` |
| `phase_demo.clean` | `task_type` ∈ `{clean, e2e}`; `phase_like` without force/review signals | `clean.phase_demo` | both flags false |
| `bundle.delivery` | `task_type=bundle`; `cleaned/*_cleaned.csv` exists | `export.delivery_bundle` | — |
| `error.missing_intake` | No `intake` arg and no `case_dir/intake.json` | (empty) | `ok=false` |
| `error.missing_raw` | `intake.data_file` path missing under `case_dir` | (empty) | `ok=false` |
| `error.missing_gate_notes` | `task_type` ∈ `{clean, e2e}`; caller passed empty `gate_notes` | (empty) | `ok=false` |
| `error.unknown_schema` | `task_type` ∈ `{clean, e2e}`; notes lack `phase_like` / `phase_demo` | (empty) | `ok=false` |
| `error.missing_cleaned` | `task_type=bundle`; no cleaned artifact | (empty) | `ok=false` |
| `error.invalid_task_type` | Unknown `task_type` | (empty) | `ok=false` |
| `error.catalog_tool_id` | Recommended `tool_id` not in catalog | (empty) | `ok=false` |
| `error.catalog_disabled` | Catalog entry exists but `enabled=false` | (empty) | `ok=false` |
| `error.registry_not_approved` | Registry filter enabled; no candidate `tool_id` in approved set | (empty) | `ok=false` |

### 3.1 Gate notes reference (from P2 eligibility)

| Note | Typical fixture | Selector effect |
|------|-----------------|-----------------|
| `phase_like` | Both standard samples | Enables `clean.phase_demo` candidate |
| `phase_demo` | `demo_phase` | Contributes to `requires_force=true` |
| `multi_row_export` | `sampleco/2026-0001` | `human_review_required=true` |
| `schema_ambiguous` | `sampleco/2026-0001` | `human_review_required=true` |

When `gate_notes` is omitted, v1 infers notes from known fixtures (`demo_phase`, `sampleco/2026-0001`) via `intake` metadata and `case_dir` path.

---

## 4. Future E2E hook (non-goal in W3-TL-T2)

The selector is **recommendation-only** in v1. Wiring into the E2E driver is explicitly deferred.

**Proposed future integration (not implemented)**

1. Environment flag: `TABULAR_SELECTOR_ENABLED=1`
2. `scripts/run_case_e2e_validation.py` (or successor) calls `select_tabular_tools` before each step
3. Selector output logged as sidecar JSON; executor (W3-TL-T3) may consume `candidate_tools[]`
4. Requires a **separate ticket**; default remains hard-coded E2E chain

**This ticket does not** modify `run_case_e2e_validation.py` or any regression driver.

---

## 5. Risks and limitations

| Risk | Mitigation |
|------|------------|
| Rules only cover `demo_phase` and `sampleco` patterns | Unknown schema → `ok=false` (`error.unknown_schema`) or use `gate_only` for eligibility-only |
| Catalog / selector drift | Validate `tool_id` against catalog before return |
| `review_needed` without `requires_force` | `demo_phase` fixture tested; `phase_demo` note triggers force |
| Empty `gate_notes` passed explicitly | `error.missing_gate_notes` for `clean` / `e2e` |
| No CSV parsing | Relies on upstream gate notes and intake metadata; wrong notes → wrong flags |

---

## 6. Verification

```bash
python -m unittest tests.test_tabular_tool_selector -v
python -m unittest tests.test_tabular_tool_selector_approved_registry_v1 -v
```

Mainline guard (merge gate, not modified by this ticket):

```bash
python scripts/run_mvp_mainline_regression.py -v
```
