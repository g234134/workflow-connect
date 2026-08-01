# TICKET STATE · W2-T4 · Wave 7 Integration Regression Tier-A 納入 Release Checklist

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 2 - Multi-agent & Testing

---

## FRAME

- Title: Wave 7 Integration Regression Tier-A 納入 Release Checklist
- Goal: CLEAN orchestrator 關鍵模組在發版前有固定 Tier-A 回歸。
- Scope:
  - 將 04_Workflows/_wave7_regression_gate.py --tier A 納入 docs/testing.md release checklist
  - 修復 Tier-A 現有失敗項（若有）至 exit 0
  - 產出 artifacts/regression/wave7_tier_a.latest.json
  - 與 Phase 6 smoke 分工寫清（PR vs pre-release）
- NonScope:
  - 不全跑 Tier-B/C
  - 不改 Wave 6/7 業務規則
  - 不接商業化 intake（Wave 4）
- AllowedPaths:
  - docs/testing.md
  - 04_Workflows/_wave7_regression_gate.py
  - artifacts/regression/**
  - 最小修復（僅失敗模組）
- BlockedPaths:
  - AGENTS.md
  - 04_Workflows/00_Agent_Work_Progress.md
- Dependencies:
  - 04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md
  - W2-T1
- Risks:
  - staging 路徑依賴 temp cache → hermetic tmpdir
  - 與 gov_core Phase 6 成本硬化命名混淆 → 文檔加註
- Observability:
  - logs: 每模組 pass/fail
  - metrics: regression duration
  - traces: N/A
- OutputArtifacts:
  - 更新 docs/testing.md
  - artifacts/regression/wave7_tier_a.latest.json
  - 必要時最小修復 PR
- AcceptanceCriteria:
  - --tier A 本地 exit 0
  - JSON 含 modules_passed、modules_failed、duration_ms
  - docs/testing.md 明確 PR（W2-T1）vs Release（W2-T4）邊界
- VerificationCommands:
  - `python 04_Workflows/_wave7_regression_gate.py --tier A`
    - 預期：exit 0
  - `檢查 wave7_tier_a.latest.json`
    - 預期：結構化摘要完整

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

- [ ] 跑 Tier-A 確認 baseline
- [ ] 修復失敗模組（若有）
- [ ] 更新 testing.md release checklist
- [ ] 產出 JSON 摘要 artifact

### Files To Touch

- 04_Workflows/_wave7_regression_gate.py
- docs/testing.md
- artifacts/regression/

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

- pre-release 必跑 Tier-A；PR 僅 W2-T1 smoke

### Rollout / Ops Notes

- pre-release 必跑 Tier-A；PR 僅 W2-T1 smoke

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
