# TICKET STATE · W4-T2 · CLEAN 接單執行鏈（Intake → CleanJob → Orchestrator）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 4 - Commercialization

---

## FRAME

- Title: CLEAN 接單執行鏈（Intake → CleanJob → Orchestrator）
- Goal: CLEAN-BASIC SKU 從 intake JSON 到 Wave7 orchestrator 執行，產出 delivery 目錄與 run summary。
- Scope:
  - 收口 wave8_clean_intake_mapper → _wave8_submit_clean_job.py 最小路徑
  - 對齊 WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md BASIC 契約
  - 執行後寫 run_summary JSON
  - preview CLI 升級為可選 --submit（dev-only 閘門）
- NonScope:
  - ENRICH SKU 全功能
  - 自動計費
  - OCR/PDF
- AllowedPaths:
  - 04_Workflows/_wave8_submit_clean_job.py
  - 04_Workflows/_wave8_preview_clean_job_mapping.py
  - 04_Workflows/wave8_clean_intake_mapper.py
  - delivery/**
- BlockedPaths:
  - AGENTS.md
  - core/*（非 mapper 範圍）
- Dependencies:
  - W4-T1 gate accept
  - Wave 6/7/8 既有模組
  - 04_Workflows/_wave8_preview_clean_job_mapping.py
- Risks:
  - 輸入 CSV 編碼錯誤 → QA M1 攔截 NEED-HUMAN
  - mapper 與 orchestrator SKU 不一致 → intake 校驗攔截
- Observability:
  - logs: 每 stage S1–S5 狀態
  - metrics: clean_job_duration_ms
  - traces: job_id = work_order_id 對齊 metadata
- OutputArtifacts:
  - 更新 submit/preview runners
  - 樣本 delivery/ 目錄
  - run_summary fixture
- AcceptanceCriteria:
  - intake_basic_sample.json 端到端 exit 0
  - 產出 delivery/<job_id>/ 含 report + manifest
  - run_summary.ok == true 且含 stage_timeline[]
  - Wave7 Tier-A 仍綠（W2-T4）
- VerificationCommands:
  - `python 04_Workflows/_wave8_submit_clean_job.py ...`
    - 預期：exit 0；delivery 產出
  - `python 04_Workflows/_wave7_regression_gate.py --tier A`
    - 預期：仍 exit 0

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

- [ ] 收口 intake → mapper → submit 路徑
- [ ] 對齊 BASIC SKU 契約
- [ ] run_summary JSON 輸出
- [ ] preview --submit dev 閘門

### Files To Touch

- 04_Workflows/_wave8_submit_clean_job.py
- 04_Workflows/wave8_clean_intake_mapper.py
- 04_Workflows/_wave8_preview_clean_job_mapping.py

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

- dev-only --submit；delivery 目錄樣本保留

### Rollout / Ops Notes

- dev-only --submit；delivery 目錄樣本保留

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
