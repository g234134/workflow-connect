# TICKET STATE · W4-UI-F-command-center-live-api-mount-v1 · Wave4.5 真 API／CLI 只讀掛載

> Wave 4.5 UI · build · 上游 Wave4 A–E 靜態殼 `accepted_with_gaps`（40/40）  
> 宿主：`ui/command_center/` · 契約：`docs/p89-operator-fields-projection-v1.md` · gate／metrics 計劃 §2.1–§2.3

---

## FRAME

- Goal: 在既有五頁靜態殼上增加 **mock | live** 資料源開關；優先掛 **P5 泳道 + P1 KPI** 的本地只讀 live 投影（CLI／fixture）；live 失敗 fallback mock；≠ Operator prod 全量。
- Scope:
  - MUST：共用 fetch 層（query／預設 mock）；`live/` 投影 JSON + projector CLI
  - MUST：P1／P5 頁換源；其餘頁可沿用 mock 但共用開關 API
  - MUST：unittest 既有 40 綠 + live-path 契約測（fixture；不依真 PG）
  - MUST：runbook（開啟方式／開關／non_claims）；Progress 末尾；`apply_phase_pct=false`
  - MAY：P2–P4 同契約換源（若一票內可完成）
- NonScope:
  - Grafana · PG soak · DarkOps 解禁 · 金鑰明文 · Operator prod · Phase% authorize · Round-2 GO
  - 改暗部根／`.env`／war_status 升檔（須另授權）
- AllowedPaths:
  - `ui/command_center/**`
  - `scripts/project_command_center_live_v1.py`
  - `docs/wave4-ui-f-live-api-mount-runbook-v1.md`
  - `docs/wave4-ui-visual-freeze-v1.md`（MAY 一句）
  - `tests/test_w4_ui_f_live_api_mount_v1.py`
  - `04_Workflows/tickets/W4-UI-F-command-center-live-api-mount-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/command_queue/QUEUE.yaml`（本票狀態）
- BlockedPaths:
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 暗部根／Grafana／`docs/WAVE_PROGRESS_DASHBOARD.md` 數字格（無 authorize）
  - `Master_Map.json` war_status（無尚書省授權）
- Dependencies:
  - W4-UI-A…E `accepted_with_gaps`
  - `docs/p89-operator-fields-projection-v1.md` · `scripts/inspect_p89_operator_fields_v1.py`
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：`?source=mock`（預設）行為與既有靜態殼一致
  - AC-2：`?source=live` 載入 live 投影（`demo=false`／`data_source=live_projection`）；失敗 fallback mock
  - AC-3：P1 KPI + P8.9 operator_fields；P5 泳道 + KPI 換源可渲染
  - AC-4：`python -m unittest tests.test_w4_ui_f_live_api_mount_v1 -v` PASS；A–E 仍 40/40
  - AC-5：runbook + Progress；`apply_phase_pct=false`
  - AC-6：未宣稱 Grafana／PG soak／DarkOps／Phase%／Operator prod／Round-2 GO

### Wave Master 擴展

- wave_id: W4
- group_id: UI
- lifecycle_phase: E
- phase_targets: [P5, P1, P7.5, P8.9]
- estimated_cycles: 1
- mvp_allowed: true
- apply_phase_pct: false
- non_claims:
  - ≠ Grafana
  - ≠ PG soak
  - ≠ DarkOps 解禁
  - ≠ 金鑰明文
  - ≠ Operator prod
  - ≠ Phase% authorize
  - ≠ Round-2 GO
- ticket_class: build
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: accepted
- lifecycle_phase: E
- current_owner: scribe
- next_action: Wave5 human 催辦並行；Wave6 統一回歸＋Phase%／war_status **待尚書省授權**；P2–P4 live 換源可薄補
- last_updated: 2026-07-28 · implementer/reviewer/scribe
- ops_checklist: 無
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- gaps_summary: 已由 W4-UI-G 補 P2–P4 live；live＝CLI 投影 fixture ≠ 常駐 HTTP Operator API

---

## B_REPORT

- changed_files:
  - `ui/command_center/js/shell.js`（resolveDataSource／loadPageData／banner）
  - `ui/command_center/p1.html`／`p5.html`（換源）
  - `ui/command_center/live/p1_overview_v1.json`／`p5_swimlane_v1.json`
  - `scripts/project_command_center_live_v1.py`
  - `docs/wave4-ui-f-live-api-mount-runbook-v1.md`
  - `tests/test_w4_ui_f_live_api_mount_v1.py`
  - Progress／QUEUE／本 STATE
- artifacts:
  - runbook：`docs/wave4-ui-f-live-api-mount-runbook-v1.md`
  - projector：`scripts/project_command_center_live_v1.py --write`
- verification:
  - `python -m unittest tests.test_w4_ui_f_live_api_mount_v1 -v` → PASS（8）
  - A–F：`…a…b…c…d…e…f…` → **48/48 OK**
- behavior_notes:
  - 預設 mock；`?source=live` 讀 live／失敗 fallback
  - P8.9 五鍵 overlay 自 `project_operator_fields`
- apply_phase_pct: false
- non_claims: 見 FRAME

---

## C_REPORT

- verdict: accepted
- ac_coverage: AC-1…AC-6 滿足（本地 unittest＋fixture；無真 PG）
- gaps: P2–P4 live 未掛；≠ Operator prod HTTP
- risk: 低（預設 mock；只讀投影）
- reviewer_date: 2026-07-28

---

## Work Report

- §1 變更檔案：見 B_REPORT
- §2 skeleton：無（live 為真實投影 fixture）
- §3 placeholder：P2–P4 live 換源未做（明示 gaps）
- §4 驗證：48/48 OK；`apply_phase_pct=false`
- §5 阻塞：無（Phase%／war_status 留 Wave6＋授權）
- §6 下一步：Human H1–H5 催辦；Wave6 defer／授權後 apply
- §7 override：無
