# Tool Catalog Authority — Phase 8.8 SSOT

> **Status**: v1 wire contract · **non production-ready**  
> **SSOT path**: `shared/schemas/tool_catalog_v1.json`  
> **Loader**: `core/tool_catalog.py` → `load_catalog()`

This document declares the **single source of truth** for the Phase 8.8 orchestration Tool Layer catalog. Other catalogs are **separate tracks** and must not be merged into this JSON without an explicit governance ticket.

---

## 1. Four-track boundary

| Track | Authority path | Purpose | Relationship to Phase 8.8 |
|-------|----------------|---------|---------------------------|
| **Phase 8.8 Orchestration** | `shared/schemas/tool_catalog_v1.json` | Tool Selector / Executor binding for intake orchestration | **This SSOT** |
| **Tabular MVP** | `tools/tabular_tool_catalog_v1.json` | Tabular tool selector / executor sandbox | **Separate** — see `docs/tabular-tool-catalog-v1.md` |
| **Gov Tool Registry (B-F1)** | `skills/gov_cards/*.json` | HQ observability / KB ops cards | **Read-only mapping** — not merged into catalog JSON |
| **Wave 8 Skill SKU** | `skills/cards/`, `skills/drafts/` | Distilled skill cards (`skill-clean-*`) | **Separate** — see `docs/SKILL_CATALOG_OVERVIEW.md` |

**Rule**: `load_catalog()` loads **only** `shared/schemas/tool_catalog_v1.json`. Tabular selector, Gov cards loader, and Wave8 skill registry each consume their own artifacts.

---

## 2. Gov Registry ↔ Orchestration mapping

Gov cards (`skills/gov_cards/`) describe operational tools for HQ/dark workflows. Phase 8.8 catalog describes **orchestration-facing** tools for intake Tool Selector. The mapping below links Gov `tool_id` values to orchestration catalog entries where semantics overlap.

| Gov `tool_id` | Gov domain | Orchestration `tool_id` | Notes |
|---------------|------------|-------------------------|-------|
| `obs.eval.export` | observability | — | Gov-only; no orchestration binding in v1 |
| `obs.eval.ci_check` | observability | — | Gov-only eval gate |
| `obs.eval.stats` | observability | — | Gov-only metrics |
| `obs.eval.report` | observability | — | Gov-only reporting |
| `obs.eval.correlate` | observability | — | Gov-only correlation |
| `obs.trace.query` | observability | `rag.retrieve` | Trace/query ↔ retrieval sidecar (read-only) |
| `obs.wf.status_summary` | observability | — | Gov workflow status |
| `obs.eval.triage` | observability | — | Composite Gov card |
| `kb.index.bootstrap` | knowledge | `file.io` | Index bootstrap ↔ logical file I/O |
| `kb.index.rag_smoke` | knowledge | `llm.ask` | RAG smoke ↔ ask pipeline |
| `kb.index.selector_gate` | knowledge | `llm.ask` | Selector gate ↔ ask with gate metadata |
| `llm.*` (SPEC Tool Flow) | orchestration | `llm.ask` | Primary RAG/QA binding |
| `rag.*` (SPEC Tool Flow) | orchestration | `rag.retrieve` | Retrieve-only path |

**Coverage**: Tool Flow whitelist tools from `04_Workflows/SPEC_tool_catalog_and_selector_v1.md` §4 are represented in `tool_catalog_v1.json`. Gov cards remain authoritative for **ops** execution; this catalog is authoritative for **selector** decisions.

---

## 3. Catalog revision and validation

| Field | Rule |
|-------|------|
| `schema_version` | Must be `tool_catalog_v1` |
| `catalog_revision` | Semver or date string; bump on JSON change |
| `tools[].enabled` | `false` tools are loaded but must not be selected (selector layer, W3-T2+) |
| `tools[].tool_id` | Unique within catalog; duplicate → `load_catalog()` returns `ok: false` |

---

## 4. Related docs

- `04_Workflows/SPEC_tool_catalog_and_selector_v1.md` — catalog + selector contract
- `docs/tabular-tool-catalog-v1.md` — Tabular track (do not merge)
- `docs/SKILL_CATALOG_OVERVIEW.md` — Wave 8 skill cards (do not merge)
- `skills/gov_tool_registry.py` — Gov cards loader (read-only reference)

---

## 5. Deferred (out of scope for W3-T1)

- Dark venv second-copy catalog sync script
- Selector integration test for `enabled: false` interception
- MCP dynamic registration
- Wave8 `skill-clean-*` SKU merged into `tool_catalog_v1.json`
