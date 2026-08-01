# TICKET STATE · W4-UI-E-p2-skills-resources-v1 · Wave4-E P2 技能與資源

> Wave 4 UI · build · 上游 `W4-UI-D` accepted_with_gaps  
> 視覺 SSOT：`docs/ui-templates/unified_P2.png` · 凍結：`docs/wave4-ui-visual-freeze-v1.md`

---

## FRAME

- Goal: 交付 P2「技能管理與資源治理」靜態殼，對齊 `unified_P2.png` 資訊架構（六部技能卡 · 技能↔模組表 · 本機/雲比例 · API／Token · 金鑰庫僅遮罩）；mock JSON；宿主延續 `ui/command_center/`；Wave4 五頁靜態殼收口。
- Scope:
  - MUST：`ui/command_center/p2.html` + mock + 共用 shell CSS／JS 擴充
  - MUST：sidebar 導覽 P1／P2／P3／P4／P5 全部可互點；settings 極簡 stub
  - MUST：mock 頂層 `ok`／`demo`／`read_only`；金鑰僅遮罩（禁止明文）
  - MUST：unittest `tests/test_w4_ui_e_p2_skills_resources_v1.py`；A+B+C+D+E 全綠（期望 40/40）
  - MUST：runbook；freeze 標 A–E 靜態殼完成；Progress／plan／W-PROG／INDEX 末尾 append；`apply_phase_pct=false`
  - MAY：index 五頁入口；A–D runbook 交叉一句
- NonScope:
  - 真 API／Grafana／PG soak／暗部 dashboard 大改／DarkOps／金鑰明文
  - Dashboard Phase% authorize
  - 像素完美重畫五頁／commit／push
- AllowedPaths:
  - `ui/command_center/**`
  - `docs/wave4-ui-e-p2-skills-resources-runbook-v1.md`
  - `docs/wave4-ui-a-static-shell-runbook-v1.md`（MAY 交叉）
  - `docs/wave4-ui-b-p5-swimlane-runbook-v1.md`（MAY 交叉）
  - `docs/wave4-ui-c-p4-command-desk-runbook-v1.md`（MAY 交叉）
  - `docs/wave4-ui-d-p3-dark-loop-runbook-v1.md`（MAY 交叉）
  - `docs/wave4-ui-visual-freeze-v1.md`（狀態句）
  - `tests/test_w4_ui_e_p2_skills_resources_v1.py`
  - `tests/test_w4_ui_b_p5_swimlane_v1.py`（導覽：P2 啟用）
  - `tests/test_w4_ui_c_p4_command_desk_v1.py`（導覽：P2 啟用）
  - `tests/test_w4_ui_d_p3_dark_loop_v1.py`（導覽：P2 啟用）
  - `04_Workflows/tickets/W4-UI-E-p2-skills-resources-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md`（末尾 append）
  - `04_Workflows/tickets/W-PROG-full-line-to-100-wave-plan-2026-07-13_state.md`（末尾）
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
- BlockedPaths:
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 暗部根／Grafana／`docs/WAVE_PROGRESS_DASHBOARD.md` 數字格
  - `.github/workflows/**`
- Dependencies:
  - `W4-UI-D-p3-dark-execution-loop-v1`（accepted_with_gaps）
  - `W4-UI-C`／`W4-UI-B`／`W4-UI-A`（accepted_with_gaps）
  - `W4-UI-FREEZE-unified-p1-p5-v1`
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：可開 P2；六部技能卡／映射表／本機雲／API·Token／金鑰庫存在，對照 `unified_P2.png` IA（允許像素差）
  - AC-2：mock `ok` + `demo` + `read_only`；技能卡 ≥6；映射列 ≥1；金鑰列僅遮罩；無明文
  - AC-3：`python -m unittest tests.test_w4_ui_e_p2_skills_resources_v1 -v` PASS
  - AC-4：sidebar P1／P2／P3／P4／P5 可互點；settings stub 可點
  - AC-5：A+B+C+D+E 合計 40/40；runbook；Progress append；`apply_phase_pct=false`
  - AC-6：未宣稱 live API／Grafana／DarkOps／Phase% authorize／Operator 全量 prod

### Wave Master 擴展

- wave_id: W4
- group_id: null
- lifecycle_phase: E
- phase_targets: [P2, P7.5, P8.9]
- estimated_cycles: 1
- mvp_allowed: true
- apply_phase_pct: false
- non_claims:
  - ≠ live API／prod／Grafana／PG soak
  - ≠ 金鑰原文
  - ≠ DarkOps／暗部 core
  - ≠ Dashboard Phase% authorize
  - ≠ Operator UI 全量交付／Round-2 GO
  - ≠ 像素完美重畫五頁
- ticket_class: build
- evidence_tier: L-local
- parallel_ok: false

---

## STATE

- overall_status: accepted_with_gaps
- lifecycle_phase: E
- current_owner: scribe
- next_action: 真 API 掛載另票；像素完美可續薄補；≠ Operator 全量 prod
- last_updated: 2026-07-28 · implementer/reviewer/scribe
- ops_checklist: 無
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- gaps_summary: 甜甜圈／sparkline 為 CSS 殼非原圖插畫；雙層 sidebar 未像素還原；雲端分項條與間距允許差

---

## B_REPORT

- changed_files:
  - `ui/command_center/p2.html`
  - `ui/command_center/settings.html`（stub）
  - `ui/command_center/mock/p2_skills_resources_v1.json`
  - `ui/command_center/css/shell.css`（P2）
  - `ui/command_center/js/shell.js`（renderP2／renderNavOnly）
  - `ui/command_center/index.html`（五頁入口）
  - `ui/command_center/mock/p1_overview_v1.json`／p5／p4／p3（nav P2＋settings）
  - `docs/wave4-ui-e-p2-skills-resources-runbook-v1.md`
  - `docs/wave4-ui-a/b/c/d` runbook（交叉）
  - `docs/wave4-ui-visual-freeze-v1.md`（A–E 完成）
  - `tests/test_w4_ui_e_p2_skills_resources_v1.py`
  - `tests/test_w4_ui_b/c/d_*.py`（P2 導覽斷言）
  - Progress／plan／W-PROG／INDEX（末尾）
- artifacts:
  - 宿主：`ui/command_center/p2.html`
  - mock：`ui/command_center/mock/p2_skills_resources_v1.json`
  - runbook：`docs/wave4-ui-e-p2-skills-resources-runbook-v1.md`
  - 視覺 SSOT：`docs/ui-templates/unified_P2.png`
- verification:
  - `python -m unittest tests.test_w4_ui_e_p2_skills_resources_v1 -v` → PASS（8）
  - A+B+C+D+E：`python -m unittest tests.test_w4_ui_a_static_shell_v1 tests.test_w4_ui_b_p5_swimlane_v1 tests.test_w4_ui_c_p4_command_desk_v1 tests.test_w4_ui_d_p3_dark_loop_v1 tests.test_w4_ui_e_p2_skills_resources_v1 -v` → **40/40 OK**
  - 開啟：repo 根 `python -m http.server 8765` → `/ui/command_center/p2.html`
- behavior_notes:
  - IA 對齊 PNG：六部技能卡 · 技能↔模組表 · 本機/雲 · API／Token · 金鑰庫遮罩
  - sidebar P1–P5 可互點；settings stub
  - mock `demo`/`read_only`；金鑰僅遮罩；未改暗部根／.env／Dashboard %
- deferred_items: 真 API 掛載；Grafana；像素完美大重寫
- gaps: CSS 甜甜圈／sparkline 非原圖級；雙層 sidebar 未還原；像素間距差

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues: 無
- checks_summary: AC-1–6 過；unittest E＋A＋B＋C＋D 回歸 40/40 綠；殘差＝視覺像素／插畫級圖表／雙層 sidebar
- risk_level: low
- suggestions: 真 API 掛載另票；勿當 live SLO／金鑰真相源；勿 Phase% authorize

---

## D_REPORT

- docs_updates: E runbook；A／B／C／D runbook 交叉；freeze A–E 完成句；plan／Progress／W-PROG／INDEX 末尾
- progress_entry: 2026-07-28 · W4-UI-E P2 靜態殼 · accepted_with_gaps · 五頁收口
- followup_suggestions: 真 API 掛載另票 · ≠ Operator 全量 prod
