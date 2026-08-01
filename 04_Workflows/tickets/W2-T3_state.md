# TICKET STATE · W2-T3 · Cursor Subagents Dispatch 回歸包（TEST-SUB 系列擴充）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 2 - Multi-agent & Testing

---

## FRAME

- Title: Cursor Subagents Dispatch 回歸包（TEST-SUB 系列擴充）
- Goal: governance-guard → implementation-worker → checker-reviewer 三情境（allow / needs_changes / stop_work）可一鍵複驗。
- Scope:
  - 新增 tests/test_dispatch_guide_scenarios.py 或 04_Workflows/_dispatch_regression.py
  - 文檔 .cursor/agents/DISPATCH_GUIDE.md 補回歸命令一節
  - frozen scenario 斷言，不修改 subagent 行為
- NonScope:
  - 不新開 Subagent 類型
  - 不改 AGENTS.md Monitoring Graph L0–L2 制度
  - 不做 e2e IDE 自動化
- AllowedPaths:
  - tests/test_dispatch_guide_scenarios.py
  - 04_Workflows/_dispatch_regression.py
  - .cursor/agents/DISPATCH_GUIDE.md
- BlockedPaths:
  - AGENTS.md
  - .cursor/agents/*.md（除 DISPATCH_GUIDE 小節）
  - core/*
- Dependencies:
  - .cursor/agents/DISPATCH_GUIDE.md
  - AGENTS.md Cursor Subagents 驗收紀錄
  - W2-T1（可選並行）
- Risks:
  - DISPATCH_GUIDE 與 guard 規則漂移 → 測試讀 guide 內嵌期望值
  - 過度擴張到制度檔 → guard 應 stop_work
- Observability:
  - logs: 每 scenario guard_verdict
  - metrics: N/A
  - traces: N/A
- OutputArtifacts:
  - tests/test_dispatch_guide_scenarios.py 或 _dispatch_regression.py
  - 更新 DISPATCH_GUIDE.md
  - 回歸輸出 JSON 樣本
- AcceptanceCriteria:
  - 回歸 runner exit 0；輸出三情境 verdict 與 allowed_worker
  - 與 TEST-SUB-001/002/003 結論一致
  - stop_work 情境 allowed_worker=none
- VerificationCommands:
  - `python -m unittest tests.test_dispatch_guide_scenarios -v`
    - 預期：3/3 scenario 全綠
  - `python 04_Workflows/_dispatch_regression.py`
    - 預期：exit 0；三情境 verdict 正確

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

- [ ] 實作三情境 frozen 回歸測試
- [ ] 對照 TEST-SUB-001/002/003 期望值
- [ ] DISPATCH_GUIDE.md 補回歸命令

### Files To Touch

- tests/test_dispatch_guide_scenarios.py
- .cursor/agents/DISPATCH_GUIDE.md

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

- 回歸納入 docs/testing.md release checklist（可選）

### Rollout / Ops Notes

- 回歸納入 docs/testing.md release checklist（可選）

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
