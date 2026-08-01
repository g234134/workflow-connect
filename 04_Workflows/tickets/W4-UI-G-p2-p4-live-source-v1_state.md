# TICKET STATE · W4-UI-G-p2-p4-live-source-v1 · P2–P4 live 換源薄補

> Wave 4.5 UI · build · 上游 W4-UI-F `accepted`（gaps：P2–P4 mock-only）  
> 宿主：`ui/command_center/` · 共用 F 票 `loadPageData`／`?source=`

---

## FRAME

- Goal: 將 P2／P3／P4 沿用 F 票 fetch 契約換成 live 投影；fixture + unittest；五頁 live 齊。
- Scope:
  - MUST：p2／p3／p4.html 改 `loadPageData`；`live/p2|p3|p4_*.json`；projector 擴 PAGE_MAP
  - MUST：unittest + runbook；Progress 末尾；`apply_phase_pct=false`
  - MUST：non_claims 對齊 F（≠ prod／Grafana／Round-2／Phase%）
- NonScope:
  - Operator prod · Grafana · PG soak · DarkOps · Round-2 GO · 代填 H1–H5
  - 改 `.env`／war_status（Wave6 另票）
- AllowedPaths:
  - `ui/command_center/p2.html`／`p3.html`／`p4.html`
  - `ui/command_center/live/p2_skills_resources_v1.json`／`p3_dark_loop_v1.json`／`p4_command_desk_v1.json`
  - `scripts/project_command_center_live_v1.py`
  - `docs/wave4-ui-g-p2-p4-live-source-runbook-v1.md`
  - `tests/test_w4_ui_g_p2_p4_live_source_v1.py`
  - `04_Workflows/tickets/W4-UI-G-p2-p4-live-source-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
  - `04_Workflows/command_queue/QUEUE.yaml`
- BlockedPaths: 憲法 §7 類型；暗部根；無授權 Dashboard／war_status
- Dependencies: W4-UI-F accepted
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：P2–P4 `?source=mock` 與靜態殼一致
  - AC-2：`?source=live` 載入 live 投影；失敗 fallback
  - AC-3：`python -m unittest tests.test_w4_ui_g_p2_p4_live_source_v1 -v` PASS；A–F 仍綠
  - AC-4：runbook + `apply_phase_pct=false`
  - AC-5：未宣稱 Operator prod／Round-2／Phase%／Grafana

### Wave Master 擴展

- wave_id: W4
- group_id: UI
- lifecycle_phase: E
- phase_targets: [P2, P3, P4, P8.9]
- apply_phase_pct: false
- non_claims:
  - ≠ Grafana
  - ≠ PG soak
  - ≠ DarkOps
  - ≠ Operator prod
  - ≠ Phase% authorize
  - ≠ Round-2 GO
- ticket_class: build
- evidence_tier: L-local

---

## STATE

- overall_status: accepted
- lifecycle_phase: E
- current_owner: scribe
- next_action: Wave6 Phase%／war_status（若授權）；Human H2–H5 追催並行
- last_updated: 2026-07-28 · implementer/reviewer/scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- gaps_summary: live＝CLI 投影 fixture ≠ 常駐 HTTP Operator API

---

## B_REPORT

- changed_files:
  - `ui/command_center/p2.html`／`p3.html`／`p4.html`
  - `ui/command_center/live/p2_skills_resources_v1.json`／`p3_dark_loop_v1.json`／`p4_command_desk_v1.json`
  - `scripts/project_command_center_live_v1.py`（PAGE_MAP +p2/p3/p4）
  - `docs/wave4-ui-g-p2-p4-live-source-runbook-v1.md`
  - `tests/test_w4_ui_g_p2_p4_live_source_v1.py`
  - 本 STATE／QUEUE／Progress
- verification: 見 Reviewer 命令
- apply_phase_pct: false
- non_claims: 見 FRAME

---

## C_REPORT

- verdict: accepted
- ac_coverage: AC-1…AC-5（本地 unittest＋fixture）
- gaps: ≠ Operator prod HTTP
- risk: 低（預設 mock；只讀投影）
- reviewer_date: 2026-07-28

---

## Work Report

- §1 變更：見 B_REPORT
- §2 skeleton：無
- §3 placeholder：無
- §4 驗證：unittest G + A–G 回歸
- §5 阻塞：無（本票）
- §6 下一步：Wave6 授權收口；Human H2 Infra
- §7 override：無
