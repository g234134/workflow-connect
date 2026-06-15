# TICKET STATE · W8-T4 · non-tabular-shadow-flow-blueprint-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME
<!-- Orchestrator 填：票的邊界與驗收標準；開票時寫，施工前凍結 -->

- **Goal**: 設計一條「非 Tabular」家族的 shadow flow v1，僅為未來擴展用，不觸及現有 Tabular 主鏈，繼承現有 Agent 標準線的治理與 HITL 思路

- **Scope**:
  1. 定義「Non-Tabular」範圍（什麼是 non-tabular，與 Tabular 的關鍵差異）
  2. 設計 1-2 個未來目標案型示例（Document Processing、Log Analysis）
  3. 對照 S1–S15，標示哪些步驟沿用 Tabular、哪些需全新設計
  4. 定義決策與治理策略（沿用 Tabular 標準線的部分、Non-Tabular 特有風險）
  5. 列出 Skill / Module 需求（需新增的 Skill 卡、工具層模組）
  6. 建議 Wave 9 票列表（9 張票，含依賴圖）
  7. 更新 WORKFLOW_INDEX 與 WAVE_PROGRESS_DASHBOARD

- **NonScope**:
  - ❌ 不改任何 Tabular 主鏈程式碼（`scripts/run_mvp_mainline_regression.py` 等）
  - ❌ 不進 production 行為（無實際執行路徑、不新建 cases/ fixture）
  - ❌ 不修改 `routing/intake_decision_rules_v1.py`（保留 v1 allowlist）
  - ❌ 不實作任何 Non-Tabular 工具或執行器（僅設計層規格）

- **AllowedPaths**:
  - `docs/non-tabular-shadow-flow-blueprint-v1.md`
  - `04_Workflows/tickets/W8-T4-non-tabular-shadow-flow-blueprint-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（追加 W8-T4 條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（追加 Wave 8 行）

- **BlockedPaths**:
  - `scripts/*.py`（任何可執行腳本）
  - `tools/*.py`（工具層實作）
  - `routing/*.py`（路由規則擴展程式碼）
  - `cases/`（不新建 fixture 目錄）
  - `.github/workflows/`（不改 CI）

- **Dependencies**:
  - `docs/ninety-five-percent-automation-blueprint-v2.md`（Wave 8 缺口 G8-5 規劃）
  - `docs/agent-standard-line-v1-summary.md`（S1–S15 基準）
  - `docs/agent-standard-line-governance-view-v2.md`（治理模式）
  - `docs/skill-cards-v2.md`（Skill Card 模板）

- **AcceptanceCriteria**:
  - [AC-1] 藍圖文件包含 §1–§6 所有要求章節（目的、案型、S1-S15 對照、治理、Skill 需求、Wave 9 票）
  - [AC-2] S1-S15 對照表明確標示「沿用」vs「擴展」vs「新設計」
  - [AC-3] Wave 9 建議票至少 7 張，含依賴關係圖
  - [AC-4] WORKFLOW_INDEX §1.9+ 已更新 W8-T4 條目
  - [AC-5] WAVE_PROGRESS_DASHBOARD 已新增 Wave 8 行（W8-T4 狀態）

---

## STATE
<!-- Orchestrator 維護：當前進度與下一棒；每次角色交棒後更新 -->

- **overall_status**: accepted_with_gaps
- **current_owner**: orchestrator
- **next_action**: closed — 後續追蹤：Wave 9 實作票（W9-T1~T9 依 §6.2）、W9-T5/T6 real fixtures、heavy tool executor（本票 design-only）
- **last_updated**: 2026-06-15 · orchestrator
- **status_by_role**:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT
<!-- Implementer 填：施工結果；只寫本區塊，不改 FRAME / STATE -->

- **changed_files**:
  - `docs/non-tabular-shadow-flow-blueprint-v1.md`（新增藍圖文件，§1–§7 完整）
  - `04_Workflows/tickets/W8-T4-non-tabular-shadow-flow-blueprint-v1_state.md`（本檔，ticket state）
  - `04_Workflows/WORKFLOW_INDEX.md`（追加 §1.11 Non-Tabular Shadow Flow Design 條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 8 表追加 W8-T4 行，implementer done · Reviewer pending）

- **artifacts**:
  - Blueprint v1 文件（§1–§6 六章 + §7 附錄 A/B/C）
  - S1–S15 對照表（§3.1 總覽 + §3.2 詳細設計 + §3.3 架構圖）
  - 2 個概念案型（§2 Case Type A/B：Document Processing、Log Analysis）
  - 9 張 Wave 9 建議票（§6.2 明細 + §6.3 依賴圖 + §6.4 DoD）

- **verification**:
  - **[AC-1] §1–§6 章節格式**（標題為 `## §N …`，非 `## N`）→ ✅
    - §1 目的與範圍（1.1 Non-Tabular 定義、1.2 v1 Shadow 範圍、1.3 Tabular 關係圖）
    - §2 典型 Non-Tabular 案型（Case Type A Document、Case Type B Log Analysis）
    - §3 Shadow Flow 結構（§3.1 S1–S15 對照表、§3.2 步驟詳設、§3.3 架構圖）
    - §4 決策與治理（§4.1 沿用規則、§4.2 R-NT1~R-NT5、§4.3 Governance View 對照）
    - §5 Skill / Module 需求（§5.1 Skill NT-A/NT-B、§5.2 新模組、§5.3 繼承模組）
    - §6 Wave 9 建議票列表（§6.1 目標、§6.2 票明細、§6.3 依賴圖、§6.4 DoD）
  - **[AC-2] S1–S15 沿用 vs 擴展 vs 新設計** → ✅
    - §3.1「設計策略」欄：沿用設計×5、需擴展設計×1（S3）、需新設計×6（S5–S8/S10/S11）、沿用治理模式×3（S4/S12/S15）
    - §3.3 Legend：`(Same)` / `(Extended)` / `(New: *)` 與上表一致
  - **[AC-3] Wave 9 票 ≥7 張 + 依賴圖** → ✅（9 張：W9-T1~T9；§6.3 ASCII 依賴樹）
  - **[AC-4] WORKFLOW_INDEX W8-T4 條目** → ✅（§1.11 Non-Tabular Shadow Flow Design — Wave 8 擴展設計）
  - **[AC-5] WAVE_PROGRESS_DASHBOARD Wave 8 行** → ✅（W8-T4 列：implementer done · Reviewer pending）
  - **上游對齊**：`docs/ninety-five-percent-automation-blueprint-v2.md` §6 G8-5「Non-Tabular 支援」→ §6.1 明示承接 → ✅
  - **治理繼承**：§4.1 Checkpoint A/B、HITL、Outbox、Notify、Audit log → 明確沿用 Tabular ✅
  - **本輪驗證**：2026-06-15 · Implementer · 唯讀核對藍圖 + 更新本 B_REPORT；未改藍圖正文

- **behavior_notes**:
  - Shadow flow 明確定位為「設計層 only」（§1.2 Explicitly Out of Scope），無 production 行為
  - Non-Tabular 特有風險 R-NT1~R-NT5（§4.2）已識別並對應 safeguard
  - Skill Card NT-A / NT-B（§5.1）對齊 v2 模板欄位；maturity 標 **shadow design only**

- **deferred_items**（Wave 9 實作 — 本票 design-only，以下留待各 W9 票）:
  - **W9-T1** · `routing/intake_routing_catalog_v1.yaml` 擴 `non-tabular.*` family
  - **W9-T2** · `routing/intake_decision_rules_v2.py` non-tabular decision logic
  - **W9-T3** · `tools/non_tabular_tool_catalog_v1.json` + selector stub
  - **W9-T4** · `routing/intake_to_non_tabular_glue.py` route planner
  - **W9-T5** · `cases/docu-corp/` fixture（Document Type A）
  - **W9-T6** · `cases/log-analytics-co/` fixture（Log Type B）
  - **W9-T7** · `scripts/run_non_tabular_experiment.py` preview mode（dry-run only）
  - **W9-T8** · `docs/agent-standard-line-governance-view-nt-v1.md`
  - **W9-T9** · PR CI dry-run for non-tabular family
  - §6.4 Wave 9 DoD 九項 checklist → 全部待 Wave 9 施工後勾選

---

## C_REPORT
<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無
- **checks_summary**:
  - **AC-1 ✅**: §1–§6 完整（`## §N` 格式）；§7 附錄為加分項
  - **AC-2 ✅**: §3.1 S1–S15 沿用/擴展/新設計標示明確
  - **AC-3 ✅**: 9 張 W9-T1~T9 + §6.3 依賴圖
  - **AC-4 ✅**: WORKFLOW_INDEX §1.11 條目存在
  - **AC-5 ✅**: Dashboard Wave 8 行已索引
  - **design-only 邊界 ✅**: 無 scripts/routing/cases 變更；符合 NonScope
- **risk_level**: low
- **suggestions**: Wave 9 實作前須逐票開 FRAME；勿跳過 shadow-only 定位

---

## D_REPORT
<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->

- **docs_updates**: `docs/non-tabular-shadow-flow-blueprint-v1.md` 為 Wave 9 上游 SSOT；Dashboard 保守註解留 Step 5
- **progress_entry**: W8-T4 design-only → **accepted_with_gaps** — Non-Tabular shadow 藍圖 §1–§6 + 9 張 W9 建議票 · 無 production 行為
- **followup_suggestions**: 依 §6.2 順序開 W9-T1 routing catalog → W9-T4 glue preview

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-10 | implementer | 藍圖 v1 初稿 + 索引 |
| 2026-06-15 | scribe | W8-T4 Reviewer→Scribe 收口 · accepted_with_gaps |
| 2026-06-15 | orchestrator | STATE 關票 · overall_status accepted_with_gaps · Dashboard/Progress 收口 |
