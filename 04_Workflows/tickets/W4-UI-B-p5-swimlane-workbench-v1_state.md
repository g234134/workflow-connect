# TICKET STATE · W4-UI-B-p5-swimlane-workbench-v1 · Wave4-B P5 泳道作業台

> Wave 4 UI · build · 上游 `W4-UI-A` accepted_with_gaps  
> 視覺 SSOT：`docs/ui-templates/unified_P5.png` · 凍結：`docs/wave4-ui-visual-freeze-v1.md`

---

## FRAME

- Goal: 交付 P5「多任務 Agent 協作作業台」靜態殼，對齊 `unified_P5.png` 資訊架構（KPI · 泳道 · 右側業務／運維摘要 · 底部技能／工具／模型／API）；mock JSON；宿主延續 `ui/command_center/`。
- Scope:
  - MUST：`ui/command_center/p5.html` + mock + 共用 shell CSS／JS 擴充
  - MUST：sidebar 導覽 P1↔P5 可點；P2／P3／P4／設定仍 deferred
  - MUST：mock 頂層 `ok`／`demo`／`read_only`；可含任務／泳道／operator 摘要；金鑰僅遮罩
  - MUST：unittest `tests/test_w4_ui_b_p5_swimlane_v1.py`
  - MUST：runbook（新建或擴充 A runbook）註明 http.server 開啟路徑
  - MAY：A.1 視覺薄補併註 B_REPORT
- NonScope:
  - 真 API／Grafana／暗部 dashboard 大改／DarkOps／金鑰明文
  - Wave4-C–E 全做；Dashboard Phase% authorize
  - 像素完美大重寫
- AllowedPaths:
  - `ui/command_center/**`
  - `docs/wave4-ui-b-p5-swimlane-runbook-v1.md`
  - `docs/wave4-ui-a-static-shell-runbook-v1.md`（MAY 交叉引用）
  - `tests/test_w4_ui_b_p5_swimlane_v1.py`
  - `04_Workflows/tickets/W4-UI-B-p5-swimlane-workbench-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md`（末尾 append）
  - `04_Workflows/tickets/W-PROG-full-line-to-100-wave-plan-2026-07-13_state.md`（末尾）
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.md`（MAY A3）
- BlockedPaths:
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 暗部根／Grafana／`docs/WAVE_PROGRESS_DASHBOARD.md` 數字格
  - `.github/workflows/**`
- Dependencies:
  - `W4-UI-A-static-shell-align-p1-v1`（accepted_with_gaps）
  - `W4-UI-FREEZE-unified-p1-p5-v1`
  - `docs/p89-operator-fields-projection-v1.md`（mock 鍵參考）
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：可開 P5；KPI／泳道／右側摘要／底部四區存在，對照 `unified_P5.png` 資訊架構一致（允許像素差）
  - AC-2：mock `ok` + `demo` + `read_only`；泳道任務列 ≥1；金鑰無明文
  - AC-3：`python -m unittest tests.test_w4_ui_b_p5_swimlane_v1 -v` PASS
  - AC-4：sidebar P1↔P5 可點；其他 deferred
  - AC-5：runbook 有 http.server 路徑；Progress append；`apply_phase_pct=false`
  - AC-6：未宣稱 Wave4-C–E／live API／Grafana／DarkOps／Phase% authorize

### Wave Master 擴展

- wave_id: W4
- group_id: null
- lifecycle_phase: B
- phase_targets: [P5, P7.5, P8.9]
- estimated_cycles: 1
- mvp_allowed: true
- non_claims:
  - ≠ Wave4-C–E 完成
  - ≠ live API／prod／Grafana
  - ≠ 金鑰原文
  - ≠ DarkOps／暗部 core
  - ≠ Dashboard Phase% authorize
  - ≠ Operator UI 全量交付
- ticket_class: build
- evidence_tier: L-local
- parallel_ok: false

---

## STATE

- overall_status: accepted_with_gaps
- lifecycle_phase: B
- current_owner: scribe
- next_action: Wave4-C（P4）或真 API 掛載另票；像素完美可續 A.1
- last_updated: 2026-07-27 · implementer/reviewer/scribe
- ops_checklist: 無
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- gaps_summary: 泳道非原圖插畫級；KPI／底部微圖示為 CSS；像素間距允許差

---

## B_REPORT

- changed_files:
  - `ui/command_center/p5.html`
  - `ui/command_center/mock/p5_swimlane_v1.json`
  - `ui/command_center/css/shell.css`（P5＋A.1）
  - `ui/command_center/js/shell.js`（renderP5＋A.1）
  - `ui/command_center/index.html`
  - `ui/command_center/p1.html`（avatar／header）
  - `ui/command_center/mock/p1_overview_v1.json`（nav P5 連結＋KPI icon）
  - `docs/wave4-ui-b-p5-swimlane-runbook-v1.md`
  - `docs/wave4-ui-a-static-shell-runbook-v1.md`（交叉開啟路徑）
  - `tests/test_w4_ui_b_p5_swimlane_v1.py`
  - `04_Workflows/tickets/W4-UI-B-p5-swimlane-workbench-v1_state.md`
  - Progress／plan／W-PROG／INDEX／wave5 checklist（末尾）
- artifacts:
  - 宿主：`ui/command_center/p5.html`
  - mock：`ui/command_center/mock/p5_swimlane_v1.json`
  - runbook：`docs/wave4-ui-b-p5-swimlane-runbook-v1.md`
  - 視覺 SSOT：`docs/ui-templates/unified_P5.png`
- verification:
  - `python -m unittest tests.test_w4_ui_b_p5_swimlane_v1 -v` → PASS
  - `python -m unittest tests.test_w4_ui_a_static_shell_v1 -v` → PASS（回歸）
  - 開啟：repo 根 `python -m http.server 8765` → `/ui/command_center/p5.html`
- behavior_notes:
  - IA 對齊 PNG：7 KPI、7 階段×4 任務泳道、右側商務／運維、底部技能／工具／模型／API
  - sidebar P1↔P5 可點；P2／P3／P4 deferred
  - A.1 併本輪：token／KPI icon／flow 狀態點／status chip／avatar（≠ 像素完美）
  - mock `demo`/`read_only`；金鑰僅遮罩；P8.9 subset sidecar
- deferred_items: Wave4-C–E；真 API；Grafana；像素完美大重寫
- a1_visual_polish: done（薄補；仍允許像素差）

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues: 無
- checks_summary: AC-1–6 過；unittest B＋A 回歸綠；殘差＝視覺像素／插畫級
- risk_level: low
- suggestions: Wave4-C（P4）；勿當 live SLO

---

## D_REPORT

- docs_updates: B runbook；A runbook 交叉；plan／Progress／W-PROG／INDEX／wave5 A3 末尾
- progress_entry: 2026-07-27 · W4-UI-B P5 靜態殼＋A.1 · accepted_with_gaps
- followup_suggestions: Wave4-C（P4 拓撲）；真 API 掛載另票
