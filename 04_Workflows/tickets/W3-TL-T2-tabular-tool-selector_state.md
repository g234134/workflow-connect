# TICKET STATE · W3-TL-T2 · Tabular Tool Selector v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 · Tool Layer · **Tabular MVP**

---

## FRAME

- Title: Tabular Tool Selector v1（推薦候選 · 可審計規則）
- Goal: 提供純函式 `select_tabular_tools(...)`，依 case metadata / gate schema notes / `task_type` 輸出 1–2 個 `candidate_tools[]` 與可審計 `selector_rule_id`；**不**改動 E2E driver 行為。
- Scope:
  - 新建 `tools/tabular_tool_selector.py`（或等價路徑）— 核心 `select_tabular_tools(...) -> dict`
  - 新建 `docs/tabular-tool-selector-spec.md` — 輸入／輸出契約、規則表、fixture 範例
  - Spec 含 **「未來掛鉤點（non-goal in this ticket）」**：若 E2E 要接 Selector，建議 `TABULAR_SELECTOR_ENABLED=1` env + **另開票**
  - 輸入至少：`case_dir`、`intake.json` metadata、`gate` 維度 `dimensions.schema.notes`（如 `phase_like` / `multi_row_export` / `schema_ambiguous`）、`task_type` ∈ `{gate_only, clean, bundle, e2e}`
  - 輸出至少：`ok`, `message`, `selector_rule_id`, `candidate_tools[]`（每項含 `tool_id`, `reason`, `requires_force`, `human_review_required`）
  - 規則 v1 草案（Implementer 可細化但須可測）：
    - `phase_like` / Phase 四列 header → `clean.phase_demo`
    - `multi_row_export` / `schema_ambiguous` → 同上 + `human_review_required: true`
    - `task_type=gate_only` → `validate.eligibility`
    - 已有 cleaned 產物 + `task_type=bundle` → `export.delivery_bundle`
    - 缺 raw / intake → `ok: false` + 空 `candidate_tools`
  - 新建 `tests/test_tabular_tool_selector.py`（fixture：`demo_phase`、`sampleco/2026-0001`）
  - Selector 只 **讀** W3-TL-T1 catalog（JSON 或 loader）；不發明 catalog 外 `tool_id`
- NonScope:
  - **不**修改 `scripts/run_case_e2e_validation.py` 或接入 Selector（v1 僅推薦）
  - ML ranker、embedding 選工具
  - 改 `case_eligibility` / gate 規則本體
  - 接 ask RAG selector / `config/routing_policy.yaml`
  - Langfuse / `task_runs` / DLQ
  - rename / 觸碰 Phase 8.8 `W3-T1`–`W3-T4` draft 票
- AllowedPaths:
  - `tools/tabular_tool_selector.py`
  - `docs/tabular-tool-selector-spec.md`
  - `tests/test_tabular_tool_selector.py`
  - `04_Workflows/tickets/W3-TL-T2-tabular-tool-selector_state.md`
  - 唯讀引用：`tools/tabular_tool_catalog_v1.json`、`notebooks/csv_cleaning/case_eligibility.py`（讀 notes 語意）
- BlockedPaths:
  - `scripts/run_case_e2e_validation.py`（E2E driver — 本票 non-goal）
  - `HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`AGENTS.md`、`.cursor/rules/*`
  - `04_Workflows/tickets/W3-T1_state.md`–`W3-T4_state.md`
  - `core/tool_selector.py`（Phase 8.8 暗部軌）
- Dependencies:
  - **W3-TL-T1**（Tabular Tool Catalog JSON + `tool_id` 穩定）
  - `docs/mvp-standard-trace-path.md`（標準樣本 gate notes）
  - `cases/demo_phase`、`cases/sampleco/2026-0001` fixture
- Risks:
  - Selector 規則與 catalog `enabled: false` 不一致 → 選前校驗 catalog
  - `review_needed` case 未標 `requires_force` → demo_phase fixture 必測
- Observability:
  - logs: `selector_rule_id`、`candidate_tools` 長度
  - metrics: N/A
  - traces: N/A（本票不接 Langfuse）
- OutputArtifacts:
  - `tools/tabular_tool_selector.py`
  - `docs/tabular-tool-selector-spec.md`
  - `tests/test_tabular_tool_selector.py`
- AcceptanceCriteria:
  - **AC-1**：`select_tabular_tools` 回傳穩定 `dict`（含 `ok`, `message`, `selector_rule_id`, `candidate_tools[]`）
  - **AC-2**：`demo_phase` + `task_type=clean` → 候選含 `clean.phase_demo`，`requires_force: true`（gate `review_needed`）
  - **AC-3**：`sampleco/2026-0001` + `task_type=clean` → 候選含 `clean.phase_demo`，`human_review_required: true`（`schema_ambiguous` / ratio 風險）
  - **AC-4**：`task_type=gate_only` → 候選含 `validate.eligibility`，不含 clean/bundle
  - **AC-5**：缺 `intake.json` 或 raw → `ok: false`，`candidate_tools` 為空
  - **AC-6**：spec 含「未來掛鉤點」小節（`TABULAR_SELECTOR_ENABLED` + 另開票）
  - **AC-7**：`python -m unittest tests.test_tabular_tool_selector -v` 全綠
  - **AC-8（主鏈守護）**：`python scripts/run_mvp_mainline_regression.py -v` → 6/6 OK，exit 0
- VerificationCommands:
  - `python -m unittest tests.test_tabular_tool_selector -v`
    - 預期：全綠
  - `python scripts/run_mvp_mainline_regression.py -v`
    - 預期：6/6 OK，exit 0

---

## Minimal Read Set

| # | 路徑 | 用途 |
|---|------|------|
| 1 | `docs/governance-constitution-v1.md` §1、§3、§5 | 合約、dict 契約 |
| 2 | 本檔 FRAME + AllowedPaths | 硬邊界 |
| 3 | `04_Workflows/tickets/W3-TL-T1-tabular-tool-catalog_state.md` | 上游 catalog `tool_id` |
| 4 | `tools/tabular_tool_catalog_v1.json`（T1 交付後） | 候選池權威 |
| 5 | `docs/mvp-standard-trace-path.md` §3–§4 | gate notes、force 語意 |
| 6 | `notebooks/csv_cleaning/case_eligibility.py` | `dimensions.schema.notes` 枚舉 |
| 7 | `cases/demo_phase/intake.json`、`cases/sampleco/2026-0001/intake.json` | fixture |

---

## §2 skeleton / placeholder

| 項 | 狀態 | 說明 |
|----|------|------|
| `tools/tabular_tool_selector.py` | **[待實作]** | 純函式 selector |
| `docs/tabular-tool-selector-spec.md` | **[待實作]** | 含 future hook 小節 |
| E2E driver 接入 | **[placeholder · non-goal]** | 僅 spec 描述；實作另開票 |

> **分軌聲明（§2 / §8）**：本票僅涵蓋 tabular MVP 工具層（gate / clean / bundle / E2E）；與既有 Phase 8.8 `W3-T1`–`W3-T4` 編排 Tool Layer 分軌，票號前綴 `W3-TL-*` 僅用於 Tabular MVP。

---

## STATE

- overall_status: draft
- current_owner: orchestrator
- next_action: Assign to Implementer — **待 W3-TL-T1 catalog 就緒** 後實作 selector + spec + tests
- last_updated: 2026-06-10 · orchestrator (W3-COORD)
- status_by_role:
  - orchestrator: done
  - implementer: pending
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

> **Orchestrator 初版（2026-06-10）**：本票剛開票；Implementer 施工時更新下方欄位。

### 與 Phase 8.8 W3-T* 的邊界

- **本票（W3-TL-T2）**：Tabular MVP **推薦** selector；不寫入 `tool_decision_log` / Langfuse（留 Phase 8.8 `W3-T2`）。
- **既有 draft W3-T2**：暗部 `core/tool_selector.py` + `ToolSelectionRequest` — **不同輸入契約**；禁止混用或 rename。
- **E2E**：`run_case_e2e_validation.py` **不在本票 scope**；future hook 僅寫入 spec。

### Implementation Plan (initial)

- [ ] 讀 W3-TL-T1 catalog；實作 `select_tabular_tools`
- [ ] 規則表 S-TL-1…（對照 spec）+ fixture tests（demo_phase / sampleco）
- [ ] 撰寫 `docs/tabular-tool-selector-spec.md`（含 future hook：`TABULAR_SELECTOR_ENABLED=1`）
- [ ] `run_mvp_mainline_regression.py -v` 主鏈守護

### Files To Touch

- `tools/tabular_tool_selector.py`
- `docs/tabular-tool-selector-spec.md`
- `tests/test_tabular_tool_selector.py`

- changed_files: **[待實作]**
- artifacts: **[待實作]**
- verification: **[待實作]** — 須含 `tests.test_tabular_tool_selector` 與 `run_mvp_mainline_regression.py -v`
- behavior_notes: **[待實作]**
- deferred_items: Executor + Outbox → W3-TL-T3；E2E 接入 Selector → 未來票 + env flag

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**：`select_tabular_tools` 回傳穩定 `dict`（`ok`, `message`, `selector_rule_id`, `candidate_tools[]`）
  - **AC-2 ✅**：`demo_phase` + `task_type=clean` → 候選含 `clean.phase_demo`，`requires_force: true`
  - **AC-3 ✅**：`sampleco/2026-0001` + `clean` → 候選含 `clean.phase_demo`，`human_review_required: true`
  - **AC-4 ✅**：`gate_only` → 僅 `validate.eligibility`，不含 clean/bundle
  - **AC-5 ✅**：缺 intake / raw → `ok: false`，`candidate_tools` 為空
  - **AC-6 ✅**：`docs/tabular-tool-selector-spec.md` §4 含 future hook（`TABULAR_SELECTOR_ENABLED=1` + 另開票）
  - **AC-7 ✅**：`python -m unittest tests.test_tabular_tool_selector -v` → 9/9 OK
  - **AC-8 ✅**：Implementer 已跑 `python scripts/run_mvp_mainline_regression.py -v` → 6/6 OK，exit 0
- risk_level: low
- suggestions:
  - **G1**：v1 僅覆蓋 `demo_phase` / `sampleco/2026-0001` fixture；`gate_notes=None` 時靠硬編碼 fixture 推斷 — 新 case 須 caller 顯式傳 gate notes 或另開票接 live gate JSON
  - **G2**：clean 候選目前僅 `clean.phase_demo`（`demo_non_prod`）；正式 cleaner 上線須新 `tool_id` + Selector 規則（對齊 T1 G4–G5）
  - **G3**：Selector **只推薦**，未接入 E2E driver（FRAME non-goal；spec §4 已描述 env flag）
  - **G4**：與 Phase 8.8 暗部 `core/tool_selector.py` 輸入契約不同 — 禁止混用

---

## D_REPORT

- docs_updates:
  - **交付**：`tools/tabular_tool_selector.py`（`select_tabular_tools` 純函式）+ `docs/tabular-tool-selector-spec.md`（輸入／輸出契約、規則表 S-TL-1…、future hook）+ `tests/test_tabular_tool_selector.py`（9/9 OK）。
  - **用途**：依 `case_dir`、`intake.json`、`gate_notes`、`task_type` 輸出 1–2 個可審計 `candidate_tools[]`；**不**驅動 E2E、**不**寫 Langfuse / `tool_decision_log`（留 Phase 8.8 `W3-T2` draft）。
  - **何時必讀**：改 Selector 規則或新增 `task_type`；接 Executor（W3-TL-T3）或規劃 E2E 掛鉤票；評估 case 該用哪個 cleaner 時（須同讀 catalog `risk_notes`）。
  - **何時必跑**：改 selector 後 → `python -m unittest tests.test_tabular_tool_selector -v`；合併前建議 → `python scripts/run_mvp_mainline_regression.py -v`。
  - **分軌聲明**：本票為戰車根 Tabular MVP **推薦** selector（`W3-TL-*`）；與 Phase 8.8 `W3-T1`–`W3-T4` 編排 Tool Layer **分軌**，禁止 rename／混用 ID。
  - **non-blocking gaps（Reviewer G1–G3）**：fixture-only gate_notes 推斷；僅 `clean.phase_demo` 覆蓋；E2E 接入 deferred。
- progress_entry: |
    [W3-TL-T2] Tabular Tool Selector v1 · accepted_with_gaps · `select_tabular_tools` + spec + 9 tests OK；主鏈回歸 6/6（Implementer）。與 Phase 8.8 W3-T2 分軌。Gaps：fixture 覆蓋、demo cleaner only、E2E hook 未接。
- followup_suggestions:
  - W3-TL-T3 Executor 可消費 `candidate_tools[]` 或显式 `tool_id`
  - 新 case 類型：另開票擴 Selector 規則 + live gate notes 解析
  - E2E 接入：`TABULAR_SELECTOR_ENABLED=1` + 新票（spec §4）

---

## §8 注意事項

- **分軌**：本票僅涵蓋 tabular MVP 工具層；與 Phase 8.8 `W3-T1`–`W3-T4` 分軌；`W3-TL-*` 前綴僅 Tabular MVP。
- **v1 定位**：Selector **只推薦**，不驅動 E2E；掛鉤須 env flag + 新票。
- **主鏈守護**：合併前必跑 `run_mvp_mainline_regression.py -v`。
- **上游阻塞**：W3-TL-T1 catalog 未完成前，Implementer 可用盤點草案 `tool_id` 開發，Reviewer 關票前須對齊 T1 JSON。

---

## O_NOTES

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-10 | orchestrator (W3-COORD) | 開票 FRAME / Minimal Read Set / B_REPORT 初版 | 本檔 |
