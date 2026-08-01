# TICKET STATE · W4-T4 · C1 偵錯健檢服務 — 實戰交付包自動彙整

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 4 - Commercialization

---

## FRAME

- Title: C1 偵錯健檢服務 — 實戰交付包自動彙整
- Goal: 對內商業交付可一鍵產出 C1 Product Spec 標準包（eval + wf + triage）。
- Scope:
  - 實作 04_Workflows/_c1_diagnostic_bundle.py：串聯 Step 0–4
  - 輸入：ibridge JSONL + 可選 trace + 可選 index_status
  - 輸出：artifacts/diagnostic/<case_id>/ 目錄
  - 更新 Product Spec §3.1 對照表（若路徑變更）
- NonScope:
  - 對客自動報價
  - 修復客戶程式
  - prod selector 一鍵修復
- AllowedPaths:
  - 04_Workflows/_c1_diagnostic_bundle.py
  - docs/C1_DELIVERY_CHECKLIST.md
  - artifacts/diagnostic/**
- BlockedPaths:
  - core/*
  - AGENTS.md
- Dependencies:
  - C1-P1/C1-P2 文檔
  - W1-T3 CI 產物格式
  - B-F1/B-F3 catalog + routing
- Risks:
  - 樣本 N<10 時 stats 不穩定 → 報告標低信心
  - 客戶資料敏感 → 僅處理遮罩後 JSONL
- Observability:
  - logs: 每 tool 步驟 ok/duration_ms
  - metrics: diagnostic_bundle_needs_review_ratio
  - traces: bundle manifest 含 trace_ids[]
- OutputArtifacts:
  - _c1_diagnostic_bundle.py
  - artifacts/diagnostic/<case_id>/ 樣本
  - docs/C1_DELIVERY_CHECKLIST.md
- AcceptanceCriteria:
  - fixture case exit 0；產物 = Product Spec §3.1 標準包
  - 缺 trace 時降級並 degraded_scope 聲明
  - gov_tool_registry validate 與 bundle tool_id 一致
  - 1 個開發循環內人工可跑通
- VerificationCommands:
  - `python 04_Workflows/_c1_diagnostic_bundle.py ...`
    - 預期：exit 0；標準包齊全
  - `python -m skills.gov_tool_registry validate`
    - 預期：ok=True

---

## STATE

- overall_status: draft
- current_owner: orchestrator
- next_action: Assign to Implementer — 依 B_REPORT Implementation Plan 開工
- last_updated: 2026-06-07 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: pending
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

> **C 區（Orchestrator 預填）**：Implementer 施工時更新下方欄位，保留 Implementation Plan 歷史。

### Implementation Plan (initial)

- [ ] 實作 bundle runner 串聯 Gov tools
- [ ] Step 0–4 對齊 WAVE_C_EXECUTION_PLAN
- [ ] degraded_scope 降級邏輯
- [ ] C1_DELIVERY_CHECKLIST.md

### Files To Touch

- 04_Workflows/_c1_diagnostic_bundle.py
- docs/C1_DELIVERY_CHECKLIST.md
- artifacts/diagnostic/

- changed_files: <!-- Implementer 填 -->
- artifacts: <!-- Implementer 填 -->
- verification: <!-- Implementer 填：執行 VerificationCommands 結果 -->
- behavior_notes: <!-- Implementer 填 -->
- deferred_items: <!-- Implementer 填；無則「無」 -->

---

## C_REPORT

- conclusion: <!-- Reviewer 填：accepted | accepted_with_gaps | needs_changes | rejected -->
- blocking_issues: <!-- Reviewer 填；無則「無」 -->
- checks_summary: <!-- Reviewer 填：對照 FRAME 邊界與 AcceptanceCriteria -->
- risk_level: <!-- Reviewer 填：low | medium | high -->
- suggestions: <!-- Reviewer 填；無則「無」 -->

---

## D_REPORT

- docs_updates: <!-- Scribe 填 -->
- progress_entry: <!-- Scribe 填：建議寫入 Progress 末尾 1–3 句 -->
- followup_suggestions: <!-- Scribe 填；無則「無」 -->

---

## O_NOTES

> **O 區**：Orchestrator 維護 run log 與戰報連結；Observe / Operate 計畫。

### Observability Plan

- 僅內部交付；敏感資料遮罩

### Rollout / Ops Notes

- 僅內部交付；敏感資料遮罩

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
