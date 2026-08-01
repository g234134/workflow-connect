# TICKET STATE · W1-T4 · KB Index Selector Gate 最小 Prod 接線（dev-only）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 1 - Governance & Observability

---

## FRAME

- Title: KB Index Selector Gate 最小 Prod 接線（dev-only）
- Goal: kb_index_status 可進入 selector 決策鏈與 gov-trace metadata，決策依據可審計（仍非 blocking gate）。
- Scope:
  - 實作 GOV_KB_INDEX_SELECTOR_HOOK_ENABLED=1 dev 路徑
  - 更新 skills/gov_cards/kb_index_selector_gate.json：skeleton → dev-ready（tier: dev_only）
  - 對齊 workflow_v2/20_pilot/W3-B_kb_contract.md §5.4 truth table 單測全綠
  - Runbook：docs/KB_INDEX_SELECTOR_DEV_RUNBOOK.md
- NonScope:
  - 不改 ask 主線預設（預設仍 bypass）
  - 不做 ML ranker
  - 不接 Wave8 CLEAN selector
- AllowedPaths:
  - core/kb_index_selector_hook.py
  - core/ask_rag_selector.py（接線點）
  - skills/gov_cards/kb_index_selector_gate.json
  - docs/KB_INDEX_SELECTOR_DEV_RUNBOOK.md
  - tests/test_kb_index_selector_hook.py
- BlockedPaths:
  - AGENTS.md
  - .cursor/rules/*
  - 04_Workflows/00_Agent_Work_Progress.md
- Dependencies:
  - core/kb_index_selector_hook.py（已存在）
  - core/ask_rag_selector.py
  - W1-T2（trace metadata 寫入；可並行）
- Risks:
  - index_status JSON 過期導致誤判 stale → 文檔要求 TTL
  - 與 K-2 merge 語意衝突 → 僅 advisory，不阻斷 answer
- Observability:
  - logs: selector_decision reason 字串
  - metrics: kb_index_gate 計數（ready/stale/missing）
  - traces: ibridge_v0.selector_decision + gov-trace metadata
- OutputArtifacts:
  - 更新 hook 接線 + gov_card
  - docs/KB_INDEX_SELECTOR_DEV_RUNBOOK.md
  - tests/test_kb_index_selector_hook.py 擴充
- AcceptanceCriteria:
  - flag ON 時 unittest 覆蓋 ready/stale/missing 三態；決策 log 含 kb_index_status、gate_reason
  - flag OFF 時行為與現基線 bit-identical
  - python -m skills.gov_tool_registry validate → errors=0
  - Reviewer 確認未宣稱 prod blocking
- VerificationCommands:
  - `python -m unittest tests.test_kb_index_selector_hook -v`
    - 預期：全綠；三態覆蓋
  - `GOV_KB_INDEX_SELECTOR_HOOK_ENABLED=0`
    - 預期：行為與基線一致
  - `python -m skills.gov_tool_registry validate`
    - 預期：ok=True errors=0

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

- [ ] 接線 apply_kb_index_tool_gate_from_hints 至 selector/trace
- [ ] 更新 gov_card skeleton → dev-ready
- [ ] 擴充 test_kb_index_selector_hook 三態
- [ ] 撰寫 KB_INDEX_SELECTOR_DEV_RUNBOOK.md

### Files To Touch

- core/kb_index_selector_hook.py
- core/ask_rag_selector.py
- skills/gov_cards/kb_index_selector_gate.json
- docs/KB_INDEX_SELECTOR_DEV_RUNBOOK.md
- tests/test_kb_index_selector_hook.py

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

- 預設 flag=0；dev 開啟需 runbook 記錄；回退 flag=0

### Rollout / Ops Notes

- 預設 flag=0；dev 開啟需 runbook 記錄；回退 flag=0

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
