# TICKET STATE · W3-SMOKE-g7-gate-notify-mp-chain-v1

> Full-Phase · Wave 3 · 整合煙霧前置／最小煙霧包 · L-local  
> 匯總：`W-PROG-full-line-to-100-wave-plan-2026-07-13`  
> Runbook：`docs/wave3-smoke-g7-gate-notify-mp-chain-v1.md`

---

## FRAME

- Goal: 交付可重跑串線驗證：**G7 HTTP stub → gate layer 對齊 → run+notify → G6 alert sink → MP-SMOKE**；證明 Wave 3 煙霧就緒（無 UI）。
- Scope:
  - MUST：`docs/wave3-smoke-g7-gate-notify-mp-chain-v1.md`（命令／預期 ok／non_claims）
  - MUST：`delivery/wave3_smoke_chain_v1.py` · `scripts/run_wave3_smoke_chain_v1.py`
  - MUST：`tests/test_wave3_smoke_chain_v1.py` + 實際跑通證據
  - MUST：計劃／W-PROG／Progress 末尾 append；標明 Wave 3 GO 建議
  - MAY：INDEX 一句索引
- NonScope:
  - 不開 Web UI · 不改暗部根 · 不 authorize Dashboard 數字格 · 不 git commit
  - 不重寫 MP-SMOKE／gate 決策本體 · 不做 P8.6–8.8 大改（留給下輪）
  - 不自動開 Wave 4 UI（仍等用戶照片／凍結）
- AllowedPaths:
  - `docs/wave3-smoke-g7-gate-notify-mp-chain-v1.md`
  - `delivery/wave3_smoke_chain_v1.py`
  - `scripts/run_wave3_smoke_chain_v1.py`
  - `tests/test_wave3_smoke_chain_v1.py`
  - `04_Workflows/tickets/W3-SMOKE-g7-gate-notify-mp-chain-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md`（末尾 append）
  - `04_Workflows/tickets/W-PROG-full-line-to-100-wave-plan-2026-07-13_state.md`（末尾 append）
- BlockedPaths:
  - 憲法 §7 類型 · 暗部根 · 治理母本全文 · Dashboard 數字格 · `.github/workflows/**` · UI 實作
- Dependencies:
  - P75-G6 · P75-G7 · gate CLI／notify · MP-SMOKE v1（均已落地）
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：runbook 含五步、命令、預期 `ok`、non_claims
  - AC-2：`python -m unittest tests.test_wave3_smoke_chain_v1 -v` PASS
  - AC-3：CLI 全串 `ok=true` · `failed_steps=[]`
  - AC-4：G7 decision 與 gate layer preview 對齊
  - AC-5：Progress／計劃／W-PROG 末尾有證據；標 Wave 3 GO 建議（UI 仍等）
  - AC-6：`apply_phase_pct=false`；未寫 Dashboard %

### Wave Master 擴展

- phase_targets: [P7.5]
- baseline_pct: "07-13 Dashboard · P7.5=46%"
- proposed_delta_pct: "P7.5 +1"
- evidence_gate: L-local
- impact_size: small
- apply_phase_pct: false
- phase_delta_lifecycle: verified
- non_claims:
  - ≠ prod／required CI · ≠ UI · ≠ Phase closure · ≠ Dashboard authorize · ≠ DarkOps

---

## STATE

- overall_status: done
- current_owner: none
- next_action: 無 · accepted；Wave 4 UI 等用戶；Δ 待 W-PROG authorize
- last_updated: 2026-07-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- ac_status:
  - AC-1: pass
  - AC-2: pass
  - AC-3: pass
  - AC-4: pass
  - AC-5: pass
  - AC-6: pass
- wave3_go: smoke_go
- wave4_ui: hold_for_user_assets

---

## B_REPORT

- changed_files:
  - docs/wave3-smoke-g7-gate-notify-mp-chain-v1.md
  - delivery/wave3_smoke_chain_v1.py
  - scripts/run_wave3_smoke_chain_v1.py
  - tests/test_wave3_smoke_chain_v1.py
  - 04_Workflows/tickets/W3-SMOKE-g7-gate-notify-mp-chain-v1_state.md
  - 04_Workflows/WORKFLOW_INDEX.md（一句）
  - 04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md（清單 #9 + Append）
  - 04_Workflows/tickets/W-PROG-full-line-to-100-wave-plan-2026-07-13_state.md（Append）
  - 04_Workflows/00_Agent_Work_Progress.md（append）
- verification: |
    python -m unittest tests.test_wave3_smoke_chain_v1 -v → 2 OK
    python scripts/run_wave3_smoke_chain_v1.py --case-ref demo_phase --outbox-root outbox/_wave3_smoke_tmp --format json
    → ok=true · failed_steps=[] · 五步皆 ok（含 mp_smoke）
    python 04_Workflows/_phase_pct_apply.py estimate --ticket-id W3-SMOKE-g7-gate-notify-mp-chain-v1 --write-back --pretty
    → P7.5 +1 · dry_run · 未 apply Dashboard
- behavior_notes: 未發現配線斷裂；僅新增串線編排，未改 gate／MP 本體；same_chat O/B/C/D
- deferred_items: P8.6–8.8 薄增量 · Wave 4 UI · P2 execute · Dashboard authorize

### Phase 影響

- **影響 Phase**：P7.5
- **proposed_delta**：+1
- **實際上調**：否（apply_phase_pct=false）

## Phase Δ estimate (auto · heuristic n/a)

- phase_delta_lifecycle: estimated
- source: explicit
- heuristic: false
- heuristic_version: n/a
- heuristic_status: n/a
- impact_size: small
- evidence_gate: L-local
- baseline_pct: 07-13 Dashboard · P7.5=46%
- proposed_delta_pct: "P7.5 +1"
- rationale: parsed proposed_delta_pct='P7.5 +1'
- note: explicit FRAME delta preferred over heuristic
- non_claims: ≠ Dashboard write · ≠ Phase closure · 干活≠漲%

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無（串線綠；無配線斷裂需修）
- checks_summary: AC 全過；禁區未觸；無 UI；無 Dashboard 寫入；DarkOps 未碰；Wave3 煙霧 GO 與 Wave4 UI hold 分欄清楚。
- risk_level: low
- suggestions: 下一可選 P8.6–8.8；UI 等用戶資產後再開 Wave 4

### Phase 影響

- apply_phase_pct=false · 未越權

---

## D_REPORT

- docs_updates: wave3 smoke runbook · INDEX · 計劃 Append · W-PROG Append · Progress 戰報
- progress_entry: 本輪 Progress 條
- followup_suggestions: Wave 4 UI 等凍結；P2 仍 blocked；% 匯總留 W-PROG

### Phase 影響

- **實際上調**：否

## Phase Δ verify

- phase_delta_lifecycle: verified
- proposed_delta_pct: "P7.5 +1"
- checks: {"checks_ok_flag": true, "review_ok_marker": true, "lifecycle_was": "estimated", "has_deltas": true}
- write_candidate: true（仍須 apply_phase_pct=true + 已授權寫入 + --authorize）
- non_claims: ≠ auto Dashboard write · verified ≠ applied
