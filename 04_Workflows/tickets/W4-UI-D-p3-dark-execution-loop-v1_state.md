# TICKET STATE · W4-UI-D-p3-dark-execution-loop-v1 · Wave4-D P3 暗部執行閉環

> Wave 4 UI · build · 上游 `W4-UI-C` accepted_with_gaps  
> 視覺 SSOT：`docs/ui-templates/unified_P3.png` · 凍結：`docs/wave4-ui-visual-freeze-v1.md`

---

## FRAME

- Goal: 交付 P3「暗部執行與交付閉環」靜態殼，對齊 `unified_P3.png` 資訊架構（七模組卡 · 六部→暗部→知識→交付回流圖 · 右側重試／告警／健康）；mock JSON；宿主延續 `ui/command_center/`。
- Scope:
  - MUST：`ui/command_center/p3.html` + mock + 共用 shell CSS／JS 擴充
  - MUST：sidebar 導覽 P1／P5／P4／P3 可互點；P2／設定仍 deferred
  - MUST：mock 頂層 `ok`／`demo`／`read_only`；金鑰僅遮罩
  - MUST：unittest `tests/test_w4_ui_d_p3_dark_loop_v1.py`
  - MUST：runbook 註明 http.server 開啟路徑
  - MAY：像素差記 B_REPORT gaps
- NonScope:
  - 真 API／Grafana／暗部 dashboard 大改／DarkOps／金鑰明文
  - Wave4-E；Dashboard Phase% authorize
  - 像素完美大重寫／原圖向量插畫
- AllowedPaths:
  - `ui/command_center/**`
  - `docs/wave4-ui-d-p3-dark-loop-runbook-v1.md`
  - `docs/wave4-ui-a-static-shell-runbook-v1.md`（MAY 交叉引用）
  - `docs/wave4-ui-b-p5-swimlane-runbook-v1.md`（MAY 交叉引用）
  - `docs/wave4-ui-c-p4-command-desk-runbook-v1.md`（MAY 交叉引用）
  - `docs/wave4-ui-visual-freeze-v1.md`（MAY 狀態句）
  - `tests/test_w4_ui_d_p3_dark_loop_v1.py`
  - `tests/test_w4_ui_b_p5_swimlane_v1.py`（導覽斷言：P3 啟用）
  - `tests/test_w4_ui_c_p4_command_desk_v1.py`（導覽斷言：P3 啟用）
  - `04_Workflows/tickets/W4-UI-D-p3-dark-execution-loop-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md`（末尾 append）
  - `04_Workflows/tickets/W-PROG-full-line-to-100-wave-plan-2026-07-13_state.md`（末尾）
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
- BlockedPaths:
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 暗部根／Grafana／`docs/WAVE_PROGRESS_DASHBOARD.md` 數字格
  - `.github/workflows/**`
- Dependencies:
  - `W4-UI-C-p4-provinces-command-desk-v1`（accepted_with_gaps）
  - `W4-UI-B-p5-swimlane-workbench-v1`（accepted_with_gaps）
  - `W4-UI-A-static-shell-align-p1-v1`（accepted_with_gaps）
  - `W4-UI-FREEZE-unified-p1-p5-v1`
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：可開 P3；七模組卡／回流圖／右側監控存在，對照 `unified_P3.png` IA（允許像素差）
  - AC-2：mock `ok` + `demo` + `read_only`；模組 ≥7；閉環階段 ≥4；右側監控 ≥1；金鑰無明文
  - AC-3：`python -m unittest tests.test_w4_ui_d_p3_dark_loop_v1 -v` PASS
  - AC-4：sidebar P1／P5／P4／P3 可互點；P2／settings deferred
  - AC-5：runbook 有 http.server 路徑；Progress append；`apply_phase_pct=false`
  - AC-6：未宣稱 Wave4-E／live API／Grafana／DarkOps／Phase% authorize

### Wave Master 擴展

- wave_id: W4
- group_id: null
- lifecycle_phase: D
- phase_targets: [P3, P7.5, P8.9]
- estimated_cycles: 1
- mvp_allowed: true
- apply_phase_pct: false
- non_claims:
  - ≠ Wave4-E 完成
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
- lifecycle_phase: D
- current_owner: scribe
- next_action: Wave4-E（P2 技能與資源）另票；真 API 掛載另票；像素完美可續薄補
- last_updated: 2026-07-28 · implementer/reviewer/scribe
- ops_checklist: 無
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- gaps_summary: 回流虛線非原圖插畫級；模組／監控卡為 CSS 殼；像素間距允許差；雙層 sidebar 未像素還原

---

## B_REPORT

- changed_files:
  - `ui/command_center/p3.html`
  - `ui/command_center/mock/p3_dark_loop_v1.json`
  - `ui/command_center/css/shell.css`（P3）
  - `ui/command_center/js/shell.js`（renderP3）
  - `ui/command_center/index.html`
  - `ui/command_center/mock/p1_overview_v1.json`（nav P3）
  - `ui/command_center/mock/p5_swimlane_v1.json`（nav P3）
  - `ui/command_center/mock/p4_command_desk_v1.json`（nav P3）
  - `docs/wave4-ui-d-p3-dark-loop-runbook-v1.md`
  - `docs/wave4-ui-a-static-shell-runbook-v1.md`／B／C runbook（交叉）
  - `docs/wave4-ui-visual-freeze-v1.md`（Wave4-D 狀態句）
  - `tests/test_w4_ui_d_p3_dark_loop_v1.py`
  - `tests/test_w4_ui_b_p5_swimlane_v1.py`／`tests/test_w4_ui_c_p4_command_desk_v1.py`（P3 導覽斷言）
  - Progress／plan／W-PROG／INDEX（末尾）
- artifacts:
  - 宿主：`ui/command_center/p3.html`
  - mock：`ui/command_center/mock/p3_dark_loop_v1.json`
  - runbook：`docs/wave4-ui-d-p3-dark-loop-runbook-v1.md`
  - 視覺 SSOT：`docs/ui-templates/unified_P3.png`
- verification:
  - `python -m unittest tests.test_w4_ui_d_p3_dark_loop_v1 -v` → PASS（8）
  - A+B+C+D：`python -m unittest tests.test_w4_ui_a_static_shell_v1 tests.test_w4_ui_b_p5_swimlane_v1 tests.test_w4_ui_c_p4_command_desk_v1 tests.test_w4_ui_d_p3_dark_loop_v1 -v` → **32/32 OK**
  - 開啟：repo 根 `python -m http.server 8765` → `/ui/command_center/p3.html`
- behavior_notes:
  - IA 對齊 PNG：七模組卡 · 六部→暗部→知識→交付 · 回流標籤 · 右側健康／失敗／重試／告警／venv
  - sidebar P1／P5／P4／P3 可互點；P2／settings deferred
  - mock `demo`/`read_only`；金鑰僅遮罩；產品文案可寫「暗部」；未改暗部根
- deferred_items: Wave4-E；真 API；Grafana；像素完美大重寫
- gaps: 回流虛線／插畫級非原圖；雙層 sidebar 未還原；像素間距差

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues: 無
- checks_summary: AC-1–6 過；unittest D＋A＋B＋C 回歸 32/32 綠；殘差＝視覺像素／插畫級回流／雙層 sidebar
- risk_level: low
- suggestions: Wave4-E（P2）；勿當 live SLO／暗部執行真相源

---

## D_REPORT

- docs_updates: D runbook；A／B／C runbook 交叉；freeze 狀態句；plan／Progress／W-PROG／INDEX 末尾
- progress_entry: 2026-07-28 · W4-UI-D P3 靜態殼 · accepted_with_gaps
- followup_suggestions: Wave4-E（P2 技能與資源）；真 API 掛載另票
