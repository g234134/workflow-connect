# TICKET STATE · W10-T2 · selector-consumes-approved-registry-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 10 · Agent Lines / Skill Registry 整合  
> **票號語境**：本票為 **selector 消費 approved registry**；與既有 `W10-T2-agent-lines-metrics-and-monitoring-v1`（metrics 離線工具）**不同票**，禁止 rename／合併。

---

## FRAME

- **Title**: W10-T2 · selector-consumes-approved-registry-v1
- **Wave / Motivation**: 承接 W5-T1（Skill Card → `skills/approved_registry.json`）與 W3-T1 deferred（selector 應尊重 `enabled`/approval 邊界），讓 Tabular selector **只讀**消費 approved registry，未批准 skill／draft 不得進入候選工具鏈。**不**改 prod 主鏈預設、不強制 CI gate。

- **Goal**: 擴展 `tools/tabular_tool_selector.py`（primary consumer）以載入 `skills/approved_registry.json`，在推薦流程中過濾或標記未批准項；補 spec 片段與 unittest；維持既有 catalog `enabled:false` 行為不回歸。

- **Scope**:
  1. `tools/tabular_tool_selector.py` — 新增 approved-registry 只讀載入與候選過濾／metadata sidecar
  2. `tests/test_tabular_tool_selector_approved_registry_v1.py`（或等價擴充既有 selector tests）
  3. `docs/tabular-tool-selector-spec.md` — 追加 § approved registry 消費規則（最小段落）
  4. 本票 `*_state.md` B_REPORT

- **NonScope / non_goals**:
  - ❌ 不改 `skills/approved_registry.json` 寫入路徑／promote CLI（W5-T1 已交付）
  - ❌ 不改 `non_tabular_tool_selector_v1.py`（另票）
  - ❌ 不接 prod INT gate / blocking delivery
  - ❌ 不合併 Gov Tool Catalog / Phase 8.8 `core/tool_catalog.py`
  - ❌ 不更新 CI workflows

- **Minimal Read Set**:
  - `04_Workflows/tickets/W5-T1_state.md`（approved registry schema）
  - `skills/approved_registry.json`
  - `tools/tabular_tool_selector.py` · `docs/tabular-tool-selector-spec.md`
  - `docs/TOOL_CATALOG_AUTHORITY.md`（四軌分軌）
  - `tests/test_skill_registry.py` · `tests/test_tabular_tool_selector.py`

- **AllowedPaths**:
  - `tools/tabular_tool_selector.py`
  - `tests/test_tabular_tool_selector_approved_registry_v1.py`
  - `docs/tabular-tool-selector-spec.md`
  - `04_Workflows/tickets/W10-T2-selector-consumes-approved-registry-v1_state.md`

- **BlockedPaths / non_scope_paths**:
  - `skills/approved_registry.json`（**唯讀**；Implementer 不寫入）
  - `04_Workflows/_wave8_skill_card_review_queue.py`
  - `tools/non_tabular_tool_selector_v1.py`
  - `core/*` · `scripts/run_mvp_mainline_regression.py`
  - `.github/workflows/*`
  - `04_Workflows/00_Agent_Work_Progress.md` · `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `W10-T2-agent-lines-metrics-and-monitoring-v1_state.md`（不同票）

- **Dependencies**:
  - **W5-T1** · `skills/approved_registry.json` + promote 管道
  - **W3-TL-T2** · tabular selector baseline
  - **W3-T1** · catalog 權威／`enabled:false` 語意（對齊不衝突）

- **AcceptanceCriteria**:
  - **AC-1**：selector 可選／預設安全載入 `approved_registry.json`；缺失或空 registry → graceful degrade（`ok: true` + 明確 message），不崩潰
  - **AC-2**：未在 `approved[]` 的 skill／tool 映射不進最終 `recommended_tools`（或標記 `approval_status=blocked` sidecar）
  - **AC-3**：既有 `enabled:false` catalog 工具仍被攔截（不回歸 W3-TL-T2 行為）
  - **AC-4**：unittest 覆蓋：空 registry、含 1 筆 approved、未批准 draft 隔離
  - **AC-5**：`tests.test_tabular_tool_selector` 既有用例仍全綠

- **VerificationCommands**:
  - `python -m unittest tests.test_tabular_tool_selector_approved_registry_v1 -v`
  - `python -m unittest tests.test_tabular_tool_selector -v`
  - （可選）`python -m unittest tests.test_skill_registry -v`

---

## STATE

- **overall_status**: `accepted_with_gaps_pending_scribe`
- **current_owner**: `scribe`
- **next_action**: Scribe：根據 B_REPORT/C_REPORT 更新 Dashboard/Progress；Orchestrator：決定 follow-up 票
- **last_updated**: 2026-06-15 · orchestrator
- **status_by_role**:
  - orchestrator: `done`
  - implementer: `done`
  - reviewer: `done`
  - scribe: `done`

---

## B_REPORT

- **changed_files**:
  - `tools/tabular_tool_selector.py` — read-only `_load_approved_registry`、`_apply_approved_registry`；env gate `TABULAR_APPROVED_REGISTRY_ENABLED` + `TABULAR_APPROVED_REGISTRY_STRICT` (fail-closed)
  - `tests/test_tabular_tool_selector_approved_registry_v1.py`（新建 · 11 tests：原 7 + fail-closed 4）
  - `docs/tabular-tool-selector-spec.md` — §2.4 approved registry 消費規則 + `error.registry_not_approved` + fail-closed policy
- **artifacts**:
  - Optional registry filter layer on tabular selector success path
  - Candidate enrichment: `approval_status=approved` when filter active and tool passes
  - Top-level sidecar: `approved_registry` (`enabled`, `degraded`, `message`, optional `approved_tool_count`)
- **verification**:
  - `python -m unittest tests.test_tabular_tool_selector_approved_registry_v1 -v` → **11 tests OK**（原 7 + fail-closed 4）
  - `python -m unittest tests.test_tabular_tool_selector -v` → **9 tests OK**（無回歸）
- **behavior_notes**:
  - **預設關閉**（env 未設）：行為與 W3-TL-T2 一致，不載入 registry、不新增 top-level 鍵
  - **啟用**（`TABULAR_APPROVED_REGISTRY_ENABLED=1`）：catalog `enabled` 校驗後再過濾 approved `tool_id`
  - **映射假設（v1）**：
    1. **首選**：registry row 含 `tool_ids: ["clean.phase_demo", ...]`（explicit bind，不需改 W5-T1 promote 寫入邏輯）
    2. **Fallback**：靜態 `_SKILL_ID_TO_TOOL_IDS`（`draft-clean-basic-job-001`→`clean.phase_demo`；`skill-tabular-validate-eligibility`→`validate.eligibility`；`skill-tabular-export-delivery`→`export.delivery_bundle`）
    3. `selector_eligible: false` 列忽略；無可解析 mapping 時 degrade（不攔截候選）
  - **Graceful degrade（預設）**：registry 缺失／空／malformed／無可解析 tool_id → `ok=true` + `approved_registry.degraded=true` + message 附於 `message`
  - **Fail-closed 策略（opt-in）**：`TABULAR_APPROVED_REGISTRY_ENABLED=1` + `TABULAR_APPROVED_REGISTRY_STRICT=1` 時，registry 缺失／malformed／空／缺 approved key → `ok=false` + `selector_rule_id=error.registry_fail_closed` + 空 candidates
  - **攔截**：registry 已載入且候選 `tool_id` 全數未批准 → `error.registry_not_approved`
- **deferred_items**:
  - promote-from-queue 自動寫入 `tool_ids`（需 W5-T1 follow-up 或 registry schema 擴充票）
  - 從 `source_card_path` 讀 card 的 `applicable_scenarios` 動態推導 tool_id（本票僅靜態 map + optional `tool_ids`）
  - non-tabular selector 消費 registry（另票）
  - prod / E2E / CI 預設啟用 registry filter（prod 預設仍為 env=off + strict=off）
  - `approval_status=blocked` sidecar 模式（本票採 drop + error，未保留 blocked 候選列）
  - governance 決定：strict fail-closed 是否納入 prod 預設（現僅實作策略，未開 gate）

---

## C_REPORT

- **conclusion**: `accepted_with_gaps` — AC-1～AC-5 均達成；映射優先序與 W5-T1 deferred 語意一致；預設關閉無回歸。策略層保留：degrade-open（空／不可解析 mapping 時候選不變）、drop 非 sidecar blocked、W5-T1 promote 尚未寫 `tool_ids` 依賴靜態 map。
- **blocking_issues**: 無
- **checks_summary**: |
    **已讀**：本票 FRAME／B_REPORT；`W5-T1_state.md`（registry schema + deferred selector 消費）；`skills/approved_registry.json`（空樣本）；`tools/tabular_tool_selector.py`；`tests/test_tabular_tool_selector_approved_registry_v1.py`；`tests/test_tabular_tool_selector.py`；`docs/tabular-tool-selector-spec.md` §2.4 + rule table。

    **映射優先序（程式 ↔ B_REPORT）** ✅  
    `_resolve_approved_tool_ids`：`selector_eligible=false` 跳過 → 非空 `tool_ids[]` 採用 → 否則 `_SKILL_ID_TO_TOOL_IDS[skill_id]`。與 W5-T1 不矛盾：registry 以 skill 為 SSOT 列；promote 目前只寫 `skill_id`/`selector_eligible`（無 `tool_ids`），本票以 optional `tool_ids` + 靜態 map 補綁，符合 W5-T1「selector 消費 deferred」邊界。

    **AC 對照**  
    - **AC-1** ✅ — 預設 env 未設不載入（`test_disabled_env_matches_baseline_shape`）；啟用時空 registry／malformed → `ok=true` + `approved_registry.degraded=true` + 候選不變；缺失檔案走同 degrade 路徑（`_load_approved_registry` L100–105，未單測但邏輯同類）。  
    - **AC-2** ✅ — 未批准 `tool_id` 自 `candidate_tools` 移除；全數被濾 → `error.registry_not_approved`（`test_unapproved_tool_blocked`）。採 drop 非 `approval_status=blocked` sidecar，FRAME 允許「或」。  
    - **AC-3** ✅ — catalog `enabled` 校驗仍在 `_success` 內、registry 過濾之前；baseline 9 tests 全綠，無回歸。  
    - **AC-4** ✅ — 7 tests 覆蓋：空 registry、單筆 approved（`tool_ids`）、未批准攔截、malformed、靜態 map、預設關閉、`selector_eligible=false`。  
    - **AC-5** ✅ — Reviewer 重跑 `tests.test_tabular_tool_selector` 9/9 OK；`tests.test_tabular_tool_selector_approved_registry_v1` 7/7 OK。

    **Verification（Reviewer 實跑）**  
    `python -m unittest tests.test_tabular_tool_selector_approved_registry_v1 tests.test_tabular_tool_selector -v` → **16 tests OK**
- **risk_level**: `low`（預設關閉、graceful degrade 不 crash）；啟用 env 且 registry 有 approved 列但 skill 不在靜態 map、亦無 `tool_ids` 時會 degrade-open — 若未來 prod 啟用需知悉（見 suggestions）
- **suggestions**: |
    1. **Follow-up 測試**：補 `registry 檔案缺失` 與 `TABULAR_APPROVED_REGISTRY_ENABLED=1` + catalog `enabled=false` 組合各一 case，釘死 AC-1／AC-3 邊界（非本輪阻塞）。  
    2. **W5-T1 銜接**：promote-from-queue 寫入 `tool_ids`（或從 `applicable_scenarios` 推導），減少對 `_SKILL_ID_TO_TOOL_IDS` 硬編碼依賴（B_REPORT 已 deferred）。  
    3. **策略選項**：若 prod 啟用 registry filter，評估「空 registry / 全不可解析 mapping」應 degrade-open 還是 fail-closed；現行與 B_REPORT 一致為 open。  
    4. **可觀測性**：啟用且非 degraded 時，被 drop 的 `tool_id` 可選 sidecar `filtered_out[]` 或 debug log，方便審計（本票 drop 模式已滿 AC-2）。  
    5. **Spec 小修（Scribe）**：§2.4 現排在 §2.3 前，編號順序可後續調整；「byte-identical」表述可改為「語意與鍵集合與 pre-W10-T2 一致」以對齊測試粒度。

---

## D_REPORT

- **docs_updates**:
  - `docs/tabular-tool-selector-spec.md` — §2.4 改寫：env 未設／設為 1 行為、映射優先序表（`tool_ids` > 靜態 map > `selector_eligible`）、degrade-open vs `error.registry_not_approved`、drop 非 blocked sidecar、prod policy TBD
  - `docs/WAVE_PROGRESS_DASHBOARD.md` — Wave 10 一句話追加 registry 摘要；新增 W10-T2-selector-consumes 票列與驗證命令
  - `04_Workflows/00_Agent_Work_Progress.md` — Wave 10 W10-T2 現狀與 deferred 段落（含管理者 opt-in 摘要）
- **progress_entry**: W10-T2 selector registry：`accepted_with_gaps` · fail-closed policy 已落地（`TABULAR_APPROVED_REGISTRY_STRICT` opt-in · env 預設關 · 16/16 OK）；prod gate 預設仍 off；degrade-open · 靜態 map · non-tabular 未接 deferred。
- **followup_suggestions**:
  - **W5-T1 銜接**：promote-from-queue 寫入 `tool_ids`（或從 `applicable_scenarios` 推導），減少 `_SKILL_ID_TO_TOOL_IDS` 硬編碼依賴
  - **Prod 策略**：評估空 registry／全不可解析 mapping 應 degrade-open 還是 fail-closed（現行 open）
  - **可觀測性**：啟用且非 degraded 時，被 drop 的 `tool_id` 可選 sidecar `filtered_out[]` 或 debug log
  - **Follow-up 測試**：registry 檔案缺失、`TABULAR_APPROVED_REGISTRY_ENABLED=1` + catalog `enabled=false` 組合各一 case
  - **Non-tabular**：`non_tabular_tool_selector_v1.py` 消費 registry（另票）
  - **Spec 編號**：§2.4 現排在 §2.3 前，可後續調整順序

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | orchestrator | 起票 FRAME 草稿；與 metrics 票 W10-T2 分軌標註 |
| 2026-06-15 | implementer | 實作 tabular selector approved-registry read-only 消費層；7+9 unittest OK；B_REPORT 填寫 |
| 2026-06-15 | scribe | §2.4 spec、Dashboard/Progress 摘要、D_REPORT 填寫 |
| 2026-06-15 | orchestrator | reviewer accepted_with_gaps；等待 Scribe 更新 selector/registry 整合說明 |
| 2026-06-15 | implementer | fail-closed policy follow-up：新增 `TABULAR_APPROVED_REGISTRY_STRICT` env gate；`_load_approved_registry` strict 模式；4 個 fail-closed 測試；spec 更新；11+9 tests OK
