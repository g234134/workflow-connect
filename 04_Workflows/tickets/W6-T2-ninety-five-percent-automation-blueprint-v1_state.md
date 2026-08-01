# TICKET STATE · W6-T2 · ninety-five-percent-automation-blueprint-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME
<!-- Orchestrator 填：票的邊界與驗收標準；開票時寫，施工前凍結 -->

- Goal: 基於 Wave 1–5 已完成產物，設計「從接案 → 清洗 → 交付」的 95% 自動化藍圖，標明 auto / HITL / human-only 以及當前缺口
- Scope:
  - 唯讀閱讀 Wave 1–5 相關產物文件（15+ 份 spec）
  - 設計 15 步驟全流程（S1–S15）from intake to closeout
  - 標記每步驟：現在狀態（auto / partial / human / planned）vs 目標狀態
  - 定義 2 個關鍵 HITL checkpoint（Checkpoint A / Checkpoint B）
  - 產出 10 項缺口清單（Gap G1–G10）對應後續票
  - 規劃 Wave 6/7 票順序（W6-T3 至 W6-T12）
- NonScope:
  - 不實作任何程式碼、不修改既有 CLI 或模組
  - 不建立新的 runner 或 test case
  - 不接線 glue / selector / executor（純設計）
  - 不涉及 Gov ask / DarkOps / GraphRAG / K-2 等路徑
- AllowedPaths:
  - `docs/ninety-five-percent-automation-blueprint-v1.md`（新建）
  - `04_Workflows/tickets/W6-T2-ninety-five-percent-automation-blueprint-v1_state.md`（本檔）
- BlockedPaths:
  - `scripts/*`（不修改）
  - `tools/*`（不修改）
  - `routing/*`（不修改）
  - `app/*`（不修改）
  - `.cursor/rules/*`（不修改）
  - `AGENTS.md` / `ENGINEERING_CONTRACT.md` / `HARNESS_CONSTITUTION.md`（不修改）
- Dependencies:
  - Wave 1–5 產物已交付（見藍圖 §8 對照索引）
  - 無阻塞項
- AcceptanceCriteria:
  - AC-1: `docs/ninety-five-percent-automation-blueprint-v1.md` 存在且包含 §1–§9 所有必要章節
  - AC-2: 藍圖明確標示 15 步驟流程，每步驟有「現在狀態」與「目標狀態」對照
  - AC-3: 定義 auto / HITL / human-only 分類標準與占比目標（95%）
  - AC-4: 缺口清單 G1–G10 對應可落地的後續票（W6-T3 至 W6-T12）
  - AC-5: Checkpoint A/B 設計符合 `docs/hitl-checkpoints-v1.md` §3–§4 規範
  - AC-6: 本 state 檔 FRAME / STATE / D_REPORT 填寫完整

---

## STATE
<!-- Orchestrator 維護：當前進度與下一棒；每次角色交棒後更新 -->

- overall_status: done
- current_owner: orchestrator
- next_action: 關票，藍圖交付完成
- last_updated: 2026-06-10 · O (Orchestrator)
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT
<!-- Implementer 填：施工結果；只寫本區塊，不改 FRAME / STATE -->

- changed_files:
  - `docs/ninety-five-percent-automation-blueprint-v1.md`（新建，完整藍圖文檔）
  - `04_Workflows/tickets/W6-T2-ninety-five-percent-automation-blueprint-v1_state.md`（本檔新建）
- artifacts:
  - 藍圖文檔：15 步驟流程設計（§3）
  - 狀態轉換矩陣：現在 vs 目標（§4）
  - Checkpoint A/B 設計細節（§5）
  - 缺口清單 G1–G10（§6）
  - Wave 6/7 票順序與依賴圖（§7）
- verification:
  - 命令: `python -c "import os; assert os.path.exists('docs/ninety-five-percent-automation-blueprint-v1.md')"`
  - 結果: exit 0，檔案存在
  - 命令: `python -c "import os; assert os.path.exists('04_Workflows/tickets/W6-T2-ninety-five-percent-automation-blueprint-v1_state.md')"`
  - 結果: exit 0，檔案存在
  - 藍圖字數檢查: ~4500 字，包含所有 §1–§9 章節
- behavior_notes:
  - 純設計票，無程式碼變更
  - 藍圖對照 15+ 份既有文檔，確保不與 Wave 1–5 產物衝突
  - HITL checkpoint 設計延續 W5-T2 設計規範，無 redefinition
- deferred_items:
  - 缺口實作：由後續票 W6-T3 至 W6-T12 承接
  - Resume Framework：G10 定義於藍圖，實作延後至 W6-T12

---

## C_REPORT
<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- conclusion: accepted
- blocking_issues: 無
- checks_summary:
  - AC-1: ✅ 藍圖文件存在，章節完整 §1–§9
  - AC-2: ✅ 15 步驟 S1–S15 明確定義，每步驟有「現在狀態」與「目標狀態」對照表
  - AC-3: ✅ auto / HITL / human-only 定義於 §1.1，占比目標 95% 明確
  - AC-4: ✅ G1–G10 缺口清單對應 W6-T3 至 W6-T12 後續票
  - AC-5: ✅ Checkpoint A/B 設計符合 `hitl-checkpoints-v1.md` 規範，見 §5
  - AC-6: ✅ 本 state 檔填寫完整
- risk_level: low
- suggestions:
  - G1: 建議 W6-T3 設計時考慮 intake 檔案大小限制（避免大檔記憶體問題）
  - G4: Decision v2 profile expansion 建議先分析 `cases/index.json` 歷史數據
  - G8: Notification gateway 可考慮重用既有 Telegram listener 基礎建設

---

## D_REPORT
<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->

- docs_updates:
  - 新建: `docs/ninety-five-percent-automation-blueprint-v1.md` — Wave 6/7 自動化藍圖主文件
  - 交叉引用: `docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 6 應新增本藍圖連結
  - 交叉引用: `04_Workflows/WORKFLOW_INDEX.md` §1.8 可新增「95% 自動化藍圖」條目
- progress_entry:
  ```
  2026-06-10 — W6-T2 ninety-five-percent-automation-blueprint-v1 設計完成。
  交付 15 步驟 auto/HITL/human 狀態轉換設計、Checkpoint A/B 規格、10 項缺口清單（G1–G10）。
  後續票順序 W6-T3→T12 已定義，Wave 6/7 實作基礎就緒。
  ```
- followup_suggestions:
  - 開票 W6-T3 (Intake API Gateway) — P0 優先，為所有後續票基礎
  - 開票 W6-T4 (Decision Rules v2) — P0 優先，解除 allowlist 限制
  - 開票 W6-T5/W6-T8 (Checkpoint A/B) — P0，HITL 核心
  - 同步更新 `docs/WAVE_PROGRESS_DASHBOARD.md` 新增 Wave 6 區段
  - 建議 Orchestrator 排定 Wave 6 kickoff 會議確認票優先序與資源

---

*W6-T2 · ninety-five-percent-automation-blueprint-v1 · done · 2026-06-10*
