# TICKET STATE · B-F1 · Skill Catalog / Gov Tool Registry v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal:
  - 建立／核對 **11 個** Gov `tool_id` 卡面（格式 `<domain>.<action>.<target>`），提供 `python -m skills.gov_tool_registry list|validate` 可重跑驗收，產出 `docs/SKILL_CATALOG_OVERVIEW.md` 作為 `tool_id` 權威索引；明確標示 skeleton（`kb.index.selector_gate`）與 composite（`obs.eval.triage`）。
- Scope:
  - `skills/gov_tool_card_schema.json`（`gov_tool_card_v1`）
  - `skills/gov_cards/*.json`（僅 repo 內已存在之 Wave B 工具）
  - `skills/gov_tool_registry.py`（load／validate／list CLI）
  - `docs/SKILL_CATALOG_OVERVIEW.md`
  - `tests/test_gov_tool_registry.py`
- NonScope:
  - 不接 `ask_rag_selector`／prod gate／CI workflow
  - 不執行工具本體、不改 observability／KB CLI 行為
  - 不混用 Wave8 `skills/cards/skill-clean-*.json`
  - 不把 skeleton 標為 production-ready
  - 不建 routing policy（留 B-F3）
- AllowedPaths:
  - `skills/gov_tool_card_schema.json`
  - `skills/gov_cards/*.json`
  - `skills/gov_tool_registry.py`
  - `docs/SKILL_CATALOG_OVERVIEW.md`
  - `tests/test_gov_tool_registry.py`
- BlockedPaths:
  - `core/*`（含 `ask_rag_selector.py`、`routing_policy_loader.py`）
  - `config/routing_policy.yaml`
  - `observability/*.py`、`workflow_v2/kb/*.py`（唯讀引用驗證，不可改）
  - `.github/workflows/*`
  - `AGENTS.md`、`.cursor/rules/*`
  - `04_Workflows/00_Agent_Work_Progress.md`
- Dependencies:
  - Wave B P1–P3 已交付（eval／trace／index／triage CLI 模組已存在）
- AcceptanceCriteria:
  - `python -m skills.gov_tool_registry validate` → `ok=True`，`total=11`，`errors=0`
  - `python -m unittest tests.test_gov_tool_registry -v` → 全綠
  - Overview 列出 11 `tool_id`，每筆有 `module_path`／`entry_kind`／`verify_command` 摘要
  - `kb.index.selector_gate` 含 `skeleton: true`；brief 明示 Wave C prod 接線
  - `obs.eval.triage` 標 composite 並列出 depends_on
  - Reviewer `conclusion ∈ {accepted, accepted_with_gaps}`，無 catalog 捏造或誇大

---

## STATE

- overall_status: accepted_with_gaps
- current_owner: orchestrator
- next_action: closed
- last_updated: 2026-06-07 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `skills/gov_tool_card_schema.json`
  - `skills/gov_tool_registry.py`
  - `skills/gov_cards/obs_eval_export.json`
  - `skills/gov_cards/obs_eval_ci_check.json`
  - `skills/gov_cards/obs_eval_stats.json`
  - `skills/gov_cards/obs_eval_report.json`
  - `skills/gov_cards/obs_eval_correlate.json`
  - `skills/gov_cards/obs_trace_query.json`
  - `skills/gov_cards/obs_wf_status_summary.json`
  - `skills/gov_cards/kb_index_bootstrap.json`
  - `skills/gov_cards/kb_index_rag_smoke.json`
  - `skills/gov_cards/kb_index_selector_gate.json`
  - `skills/gov_cards/obs_eval_triage.json`
  - `docs/SKILL_CATALOG_OVERVIEW.md`
  - `tests/test_gov_tool_registry.py`
- artifacts:
  - Gov Tool Catalog v1：11 張 `gov_tool_card_v1` 卡、`gov_tool_registry` list/validate CLI、Overview 索引
- verification:
  - `python -m skills.gov_tool_registry validate` → `ok=True total=11 passed=11 failed=0`
  - `python -m unittest tests.test_gov_tool_registry -v` → **8/8 OK**
  - Wave B 抽樣回歸：`tests.test_eval_report`、`tests.test_trace_query`、`tests.test_eval_trace_correlate`、`tests.test_wf_status_summary`、`tests.test_kb_index_bootstrap` → **54/54 OK**（Implementer 回報）
- behavior_notes:
  - 本票為「核對＋補齊 Catalog 層」，未改 Wave B CLI 執行邏輯；`kb.index.selector_gate` 僅引用既有 `core/kb_index_selector_hook.py`（`skeleton: true`）；`obs.eval.triage` 為 composite（`depends_on`: correlate + trace.query）；主艙無 `jsonschema` 時 registry 走 `_manual_schema_errors` fallback
- deferred_items:
  - Catalog `validate` 接入 CI（`.github/workflows/*`）
  - ask／selector catalog binding（B-F3／Wave C）
  - `kb.index.selector_gate` prod flag wiring（`GOV_KB_INDEX_SELECTOR_HOOK_ENABLED`）
  - jsonschema fallback 可觀測性（`schema_validator` 欄位／警告）

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues:
  - 無
- checks_summary:
  - boundary: "交付物均落在 FRAME.AllowedPaths（`skills/gov_*`、`docs/SKILL_CATALOG_OVERVIEW.md`、`tests/test_gov_tool_registry.py`）；未修改 BlockedPaths（`core/*` 執行邏輯、`observability/*.py`、`workflow_v2/kb/*.py`、`config/routing_policy.yaml`、`.github/workflows/*`、`AGENTS.md`、`.cursor/rules/*`）。`kb.index.selector_gate` 的 `module_path` 指向 `core/kb_index_selector_hook.py` 為卡面引用既有模組，非改 core。Implementer 未先回寫本 state 檔；Reviewer 依 repo 交付物與 chat Work Report 還原 FRAME/STATE/B_REPORT 供審查。"
  - alignment: "11 張 `gov_tool_card_v1` 卡之 `tool_id` 集合與 `tests/test_gov_tool_registry._REQUIRED_TOOL_IDS`、Overview 索引表、`python -m skills.gov_tool_registry list` 輸出一致。各卡 `module_path`／`entrypoint` 對應 Wave B 真實模組（10 個 `.py` 檔案存在性已 spot-check；composite 無 module）。`kb.index.selector_gate`：`skeleton: true`、title `(reference)`、brief 明示「Prod selector wiring … Wave C only; not wired into ask selector」— 未冒充 prod gate。`obs.eval.triage`：`entry_kind=composite`、`module_path`/`entrypoint` null、`depends_on=[obs.eval.correlate, obs.trace.query]`，Overview §Composite 與卡面 brief 一致。對照 `docs/WAVE_B_EXECUTION_PLAN.md` 各票交付模組無捏造。"
  - verification: "本輪獨立重跑：`python -m skills.gov_tool_registry validate` → `ok=True total=11 passed=11 failed=0`；`python -m unittest tests.test_gov_tool_registry -v` → **8/8 OK**。與 B_REPORT 所述全綠一致。主艙 Python **未安裝** `jsonschema`（`ModuleNotFoundError`），validate 仍通過係走 `_manual_schema_errors` fallback — 屬已知非阻擋缺口（見 suggestions）。"
  - existing_behavior: "Registry 僅 load/validate/list，不執行工具、不接 ask/selector pipeline；Wave B CLI 行為未變。`kb.index.rag_smoke` 的 `verify_command` 指向 `tests.test_kb_index_bootstrap`（rag smoke 覆蓋在該測試模組內）— 可跑通但語意略混，建議 Overview 加註（非阻擋）。"
  - docs: "`docs/SKILL_CATALOG_OVERVIEW.md` 與 11 卡／registry 對齊：區隔 Wave8 CLEAN cards、列出 11 tool_id 表、標 skeleton/composite、明示 B-F1 out of scope（CI validate、ask binding）。交叉 `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` §3.3／§4.3：selector_gate prod 接線標 ❌ skeleton only；已交付能力（eval export/report、trace query、correlate、wf summary、kb bootstrap+smoke）與 catalog 一致，Product Spec 未誇大 tool 能力。"
- risk_level: low
- suggestions:
  - Wave C 小票：將 `python -m skills.gov_tool_registry validate` 接入 CI（gov venv 內執行，確保 `jsonschema` 路徑）；可選 `--strict` 或回傳 `schema_validator: jsonschema|manual` 避免 fallback 靜默降級。
  - 卡面語意：`kb.index.selector_gate` 的 `review_status: approved` 與 `skeleton: true` 略衝突，建議改 `draft` 或 brief 加「approved = 卡面定稿，非 prod 接線」。
  - `kb.index.rag_smoke` verify_command 於 Overview 註明「覆蓋在 `test_kb_index_bootstrap` 內」。
  - Orchestrator：更新 STATE 交棒至 Scribe；本票可標 `accepted_with_gaps` 收口，作為 B-F3／C1-P2 之 `tool_id` 權威來源。

---

## D_REPORT

- docs_updates:
  - **`docs/SKILL_CATALOG_OVERVIEW.md`（本票已交付）**
    - 文首標 B-F1、`gov_tool_card_v1` schema／registry CLI 權威；反向指向 Product Spec，並明示 **`tool_id` 權威仍以本檔與 `skills/gov_cards/` 為準**。
    - §Gov Catalog vs Wave8：區隔 `skills/gov_cards/` 與 `skills/cards/skill-clean-*`，禁止混用 schema／ID。
    - §Catalog index（11 tools）：每筆含 `flags`（—／**skeleton**／**composite**）、`module_path`、`entry_kind`、`verify_command` 摘要；`kb.index.selector_gate` brief 明示 Wave C prod 接線留項；`obs.eval.triage` 列 `depends_on`。
    - §Routing Policy ↔ Catalog（B-F3）：雙層 validate 命令、 skeleton／composite 路由規則、prod selector 接線留 Wave C。
    - §Downstream：B-F3／C1-P2 須引用 Gov `tool_id`；catalog validate CI 與 ask binding 標 out of scope。
  - **`docs/SKILL_CATALOG_OVERVIEW.md`（Reviewer 建議、可選輕修票）**
    - `kb.index.rag_smoke` 列加註：`verify_command` 指向 `tests.test_kb_index_bootstrap`（rag smoke 覆蓋在該模組內，非獨立測試檔名）。
    - `kb.index.selector_gate`：`review_status: approved` 與 `skeleton: true` 語意釐清（approved＝卡面定稿，≠ prod 接線；或改 `draft`）。
  - **`docs/WAVE_B_EXECUTION_PLAN.md`（可選交叉引用）**
    - B-Final 收口段補連結：`docs/SKILL_CATALOG_OVERVIEW.md` 為 Wave B 工具 **`tool_id` 權威索引**；routing policy 見 `docs/ROUTING_POLICY_GUIDE.md`。
  - **`docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md`（已對齊，無需本票改動）**
    - §4.3 能力邊界與 catalog 11 tool 一致；`kb.index.selector_gate` 標 skeleton／reference；§6 索引已列 `SKILL_CATALOG_OVERVIEW.md` 為 Gov `tool_id` 清單權威。
- progress_entry: |
    ## B-F1 · Skill Catalog / Gov Tool Registry v1

    **日期**：2026-06-07 · **票號**：B-F1 · **狀態**：accepted_with_gaps（Reviewer 無阻擋項）

    **交付**：Gov Tool Catalog v1 — `skills/gov_tool_card_schema.json`（`gov_tool_card_v1`）、11 張 `skills/gov_cards/*.json`（obs eval×6、trace、wf summary、kb index×3）、`skills/gov_tool_registry.py`（list／validate CLI）、`docs/SKILL_CATALOG_OVERVIEW.md`（`tool_id` 權威索引）、`tests/test_gov_tool_registry.py`。`kb.index.selector_gate` 標 **skeleton**（reference only）；`obs.eval.triage` 標 **composite**（`depends_on`: correlate + trace.query）。未改 Wave B CLI 執行邏輯。

    **驗收**：`python -m skills.gov_tool_registry validate` → `ok=True total=11 passed=11 failed=0`；`python -m unittest tests.test_gov_tool_registry -v` → **8/8 OK**。11 `tool_id` 與 Overview 索引表、`_REQUIRED_TOOL_IDS`、registry list 輸出一致；對照 `WAVE_B_EXECUTION_PLAN` 各票模組無捏造。

    **已知缺口（非阻擋）**：主艙未安裝 `jsonschema`，validate 走 `_manual_schema_errors` fallback（靜默降級風險）；`kb.index.selector_gate` 的 `review_status: approved` 與 `skeleton: true` 語意略衝；catalog `validate` 尚未接入 CI；`kb.index.rag_smoke` verify_command 語意略混（建議 Overview 加註）。

    **對下游**：B-F3 Routing Policy、C1-P2 戰報模板應引用本 catalog 之 Gov `tool_id`，非 Wave8 `skill_id` 或暱稱。

    **下一步**：Wave C 小票掛 CI validate（gov venv + jsonschema）；prod selector 接線（`GOV_KB_INDEX_SELECTOR_HOOK_ENABLED`）；可選輕修卡面 `review_status`／Overview 註記。
- followup_suggestions:
  - **Wave C · CI 掛 `gov_tool_registry validate`**：於 `.github/workflows/*` 或 eval-gate CI 加一步（gov venv 內執行）；確保 `jsonschema` 可用；可選 CLI 回傳 `schema_validator: jsonschema|manual` 或 `--strict`，避免 fallback 靜默降級。
  - **Wave C · prod selector 接線票**：將 `kb.index.selector_gate`（`core/kb_index_selector_hook.py`）接入 `ask_rag_selector`／prod gate（`GOV_KB_INDEX_SELECTOR_HOOK_ENABLED`）；須另開實作票，本 catalog 僅 reference。
  - **Catalog 語意輕修票（可併 CI 票）**：釐清 `kb.index.selector_gate` 的 `review_status` 與 `skeleton` 標籤一致性；於 Overview 為 `kb.index.rag_smoke` 加 verify_command 覆蓋說明。
