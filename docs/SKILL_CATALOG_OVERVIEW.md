# Skill Catalog Overview — Gov Tool Registry v1

> **Ticket**: B-F1 · Skill Catalog / Tool Registry v1  
> **Schema**: `gov_tool_card_v1` (`skills/gov_tool_card_schema.json`)  
> **Cards**: `skills/gov_cards/*.json`  
> **Registry**: `python -m skills.gov_tool_registry list|validate`  
> **Product Spec**（對外服務敘事）: `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` — **`tool_id` 權威仍以本檔與 `skills/gov_cards/` 為準**

---

## Gov Catalog vs Wave8 `skills/cards`

| Aspect | Gov Tool Catalog (this doc) | Wave8 CLEAN cards |
|--------|----------------------------|-------------------|
| **Directory** | `skills/gov_cards/` | `skills/cards/skill-clean-*.json` |
| **Schema** | `gov_tool_card_v1` | `skill_card_v0.1` (product SKU) |
| **ID format** | `<domain>.<action>.<target>` (e.g. `obs.eval.export`) | `skill-clean-*` product IDs |
| **Purpose** | Wave B observability / KB CLI registry for routing & ops | Customer-facing CLEAN product SKUs |

**Do not mix schemas or IDs.** B-F3 `routing_policy` and C1-P2 must reference **Gov `tool_id` values only** — not Wave8 `skill_id` aliases.

---

## Tool ID naming rule

Format: `<domain>.<action>.<target>`

- **domain**: `obs` | `kb` | `route` (route reserved for B-F3)
- **action**: lowercase verb (`export`, `report`, `query`, `correlate`, `bootstrap`, `smoke`, `gate`)
- **target**: lowercase noun (`eval`, `trace`, `triage`, `index`, `manifest`)
- Charset: `[a-z0-9._]` only; no spaces

---

## Catalog index (11 tools)

| tool_id | flags | brief | module_path | entry_kind | verify_command (summary) |
|---------|-------|-------|-------------|------------|--------------------------|
| `obs.eval.export` | — | ibridge → eval_gate JSONL export | `observability/eval_exporter.py` | python_cli | `unittest tests.test_eval_exporter` |
| `obs.eval.ci_check` | — | CI gate on needs_review ratio / fail-on-tags | `observability/eval_ci_check.py` | python_cli | `unittest tests.test_eval_ci_check` |
| `obs.eval.stats` | — | Tag distributions and threshold suggestions | `observability/eval_stats.py` | python_cli | `unittest tests.test_eval_stats` |
| `obs.eval.report` | — | Markdown + JSON eval gate report | `observability/eval_report.py` | python_cli | `unittest tests.test_eval_report` |
| `obs.eval.correlate` | — | Join flagged eval rows to gov-trace-v2 | `observability/eval_trace_correlate.py` | python_cli | `unittest tests.test_eval_trace_correlate` |
| `obs.trace.query` | — | Read-only gov-trace-v2 JSONL lookup | `observability/trace_query.py` | python_cli | `unittest tests.test_trace_query` |
| `obs.wf.status_summary` | — | One-page Gate / Index / Trace status | `observability/wf_status_summary.py` | python_cli | `unittest tests.test_wf_status_summary` |
| `kb.index.bootstrap` | — | HQ offline repo index bootstrap (gov scope) | `workflow_v2/kb/repo_index_bootstrap.py` | python_cli | `unittest tests.test_kb_index_bootstrap` |
| `kb.index.rag_smoke` | — | Manifest keyword smoke (no PG/Qdrant) | `workflow_v2/kb/rag_index_smoke.py` | python_cli | `unittest tests.test_kb_index_bootstrap`（覆蓋於此，見 test_kb_index_bootstrap 內 rag_smoke 用例） |
| `kb.index.selector_gate` | **skeleton** | Pure-function gate reference only; **Wave C prod 接線留項** — not wired into ask selector by this catalog | `core/kb_index_selector_hook.py` | python_module | `unittest tests.test_kb_index_selector_hook` |
| `obs.eval.triage` | **composite** | Orchestrates correlate + trace query for flagged rows; no standalone module | *(none)* | composite | `unittest tests.test_eval_trace_correlate tests.test_trace_query` |

**Flags legend**

| Flag | Meaning |
|------|---------|
| — | Delivered Wave B CLI/module; safe to reference in routes when policy enables |
| **skeleton** | Catalog reference only; **must not** appear in prod route steps until Wave C wiring |
| **composite** | No `module_path`; expand to underlying `depends_on` tools in route steps |

### Composite: `obs.eval.triage`

No standalone module (`module_path=null`, `entrypoint=null`). Depends on:

- `obs.eval.correlate` — `--format triage-md`
- `obs.trace.query` — `--format triage`

Do **not** treat composite as a runnable prod gate; routing policy should list the underlying tools.

---

## Registry commands

```bash
# List all tool IDs
python -m skills.gov_tool_registry list

# Validate schema + module existence + depends_on
python -m skills.gov_tool_registry validate
```

---

## Authority references

- Wave B execution plan: `docs/WAVE_B_EXECUTION_PLAN.md`
- Eval export contract: `observability/eval_export.md`
- Trace query: `docs/observability.md` §7
- WF status summary: `docs/observability.md` §8
- KB index bootstrap runbook: `workflow_v2/20_pilot/W3-B/W3-B_index_pipeline_runbook.md` appendix A
- Selector hook contract: `workflow_v2/20_pilot/W3-B_kb_contract.md` §5.4

---

## Downstream (B-F3 / C1-P2)

- **B-F3** `config/routing_policy.yaml` entries must use `tool_id` from this catalog.
- **C1-P2** battle-report / ops templates should reference `tool_id`, not ad-hoc nicknames.
- Catalog validate CI wiring and ask-pipeline binding are **out of scope** for B-F1 (Wave C / B-F3 follow-ups).

---

## Routing Policy ↔ Catalog (B-F3)

Routing Policy v1 (`config/routing_policy.yaml`) **does not define new tools**. It only maps existing Gov `tool_id` values into named `routes` with `enabled` / `review_required` metadata.

| Layer | Authority | Validate command |
|-------|-----------|------------------|
| Tool definitions | `skills/gov_cards/*.json` (this catalog) | `python -m skills.gov_tool_registry validate` |
| Route orchestration | `config/routing_policy.yaml` | `python -m core.routing_policy_loader validate` |

Rules:

- Every `tools[].tool_id` and `routes[].steps[].tool_id` **must** exist in this catalog.
- Skeleton tools (e.g. `kb.index.selector_gate`) may appear in `tools` with `enabled: false` but **must not** appear in route steps until Wave C wiring.
- Composite tools (e.g. `obs.eval.triage`) should be expanded to underlying catalog tools in route steps.
- **Prod selector 接線**：Routing Policy v1 **尚未**接入 `ask_rag_selector` 或 prod gate；policy 僅描述／驗證／解析 Wave B 編排，prod selector 接線留給 **Wave C 專票**。

See `docs/ROUTING_POLICY_GUIDE.md` for field semantics and Wave C follow-ups.
