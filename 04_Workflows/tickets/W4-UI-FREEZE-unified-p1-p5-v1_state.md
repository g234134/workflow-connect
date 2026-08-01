# TICKET STATE · W4-UI-FREEZE-unified-p1-p5-v1 · Wave 4 UI visual freeze

> 凍結紀錄票 · scribe/ops · 解 HOLD · **≠** 施工實作（實作見 `W4-UI-A-static-shell-align-p1-v1`）

---

## FRAME

- Goal: 正式記錄用戶／尚書省確認：`unified_P1–P5.png` 為 Wave 4 視覺凍結稿，並固定頁優先序。
- Scope:
  - MUST：寫入凍結 SSOT `docs/wave4-ui-visual-freeze-v1.md`
  - MUST：Progress／全線計劃／Wave5 A3 末尾 append（HOLD → frozen）
  - MUST：開下游施工票 `W4-UI-A-static-shell-align-p1-v1`（FRAME）
  - MUST：記錄是／否與是否改頁優先序
- NonScope:
  - 不實作 HTML／React／暗部 dashboard
  - 不改 `.env`／金鑰／暗部根／runtime checkpoints
  - 不 `apply` Dashboard Phase%
  - 不編輯 Cursor plan 檔本身
- AllowedPaths:
  - `docs/wave4-ui-visual-freeze-v1.md`
  - `04_Workflows/tickets/W4-UI-FREEZE-unified-p1-p5-v1_state.md`
  - `04_Workflows/tickets/W4-UI-A-static-shell-align-p1-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md`（末尾 append）
  - `04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.md`（末尾 append + A3 狀態）
  - `04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.yaml`（A3 狀態）
  - `04_Workflows/tickets/W-PROG-full-line-to-100-wave-plan-2026-07-13_state.md`（末尾 append）
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句索引）
- BlockedPaths:
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 暗部根程式 · Grafana · Dashboard 數字格 authorize
- Dependencies:
  - 資產已存在：`docs/ui-templates/unified_P1.png`–`unified_P5.png`
  - 上游 HOLD：`W3-SMOKE`／全線計劃 Wave 4／Wave5 A3
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：凍結文檔載明 **是**＋頁序 **P1→P5…**（未改序）
  - AC-2：下游 `W4-UI-A` 票 FRAME 齊全（靜態殼→mock→宿主）
  - AC-3：Progress／計劃／A3 留痕 HOLD 解除
  - AC-4：未觸禁區；未宣稱 UI 已交付

### Wave Master 擴展

- wave_id: W4
- group_id: null
- lifecycle_phase: O
- phase_targets: [P7.5, P8, P8.9, P5]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: [視覺凍結確認（本票完成）]
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W3-SMOKE-g7-gate-notify-mp-chain-v1, WAVE5-human-staging-checklist-v1]
  - downstream_waves: [W4]
  - blocks_if_missing: [unified_P1–P5.png assets]
- risks:
  - id: freeze_without_explicit_chat_yes
    description: 確認來自 plan todo 指派完成而非口頭「是」
    likelihood: low
    impact: low
    mitigation: 本票與 Progress 明文記錄裁決與依據
    residual: 尚書省可一票覆寫頁序
- observability:
  - verify_commands:
    - `Test-Path docs/ui-templates/unified_P1.png, docs/ui-templates/unified_P5.png`
    - `rg "視覺 SSOT|凍結？" docs/wave4-ui-visual-freeze-v1.md`
  - evidence_artifacts:
    - `docs/wave4-ui-visual-freeze-v1.md`
    - `04_Workflows/tickets/W4-UI-A-static-shell-align-p1-v1_state.md`
  - trace_fields: []
  - success_signals: [freeze doc exists, W4-UI-A frame_ready, Progress append]
  - failure_signals: [assets missing, ticket missing]
- non_claims:
  - ≠ Operator UI 已上線
  - ≠ 金鑰原文可展示
  - ≠ DarkOps 解禁
  - ≠ Dashboard Phase% authorize
  - ≠ prod／required CI
- ticket_class: scribe/ops
- evidence_tier: n/a
- parallel_ok: false

---

## STATE

- overall_status: done
- lifecycle_phase: O
- current_owner: none
- next_action: Implementer 接 `W4-UI-A-static-shell-align-p1-v1`（另輪／同輪均可）
- last_updated: 2026-07-27 · orchestrator
- ops_checklist: 無
- status_by_role:
  - orchestrator: done
  - implementer: n/a
  - reviewer: n/a
  - scribe: done

### Freeze answers（await-freeze-confirm）

| 問 | 答 |
|----|----|
| `unified_P1–P5.png` 為 Wave 4 視覺凍結？ | **是** |
| 是否改頁優先序？ | **否**（維持 P1→P5→P4→P3→P2） |

---

## B_REPORT

- changed_files:
  - docs/wave4-ui-visual-freeze-v1.md
  - 04_Workflows/tickets/W4-UI-FREEZE-unified-p1-p5-v1_state.md
  - 04_Workflows/tickets/W4-UI-A-static-shell-align-p1-v1_state.md
  - （見本輪 Progress 變更清單）
- artifacts: freeze SSOT + Wave4-A FRAME
- verification: 資產 `unified_P1–P5.png` 存在於 `docs/ui-templates/`；凍結文檔含是／頁序
- behavior_notes: 僅解 HOLD 與開票；未改 page*.html 視覺
- deferred_items: Wave4-B–E 另開

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: 凍結答案齊；下游票 AllowedPaths／紅線清楚；未觸 §7
- risk_level: low
- suggestions: 施工時對照 PNG 像素級對齊 checklist 另附於 Wave4-A

---

## D_REPORT

- docs_updates: freeze SSOT · 全線計劃 Append · Wave5 A3 · INDEX 一句
- progress_entry: Wave 4 UI 視覺凍結＋開 Wave4-A
- followup_suggestions: 開工 Wave4-A 實作（靜態殼對齊 P1）
