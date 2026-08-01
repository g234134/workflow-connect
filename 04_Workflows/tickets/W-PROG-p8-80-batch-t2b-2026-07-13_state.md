# TICKET STATE · W-PROG-p8-80-batch-t2b-2026-07-13 · P8 衝 75–80% 刷新

> Governance／W-PROG · **scribe/ops** · same_chat · 2026-07-13  
> **已授權寫入**（尚書省本 session：P8 衝 80 · BATCH-MVP-03→04→P8-T2b→W-PROG）  
> 匯總票：`BATCH-MVP-03` · `BATCH-MVP-04` · `P8-T2b-batch-approve-resume-mvp-v1`

---

## FRAME

- Goal: 三票 L-local 驗收通過後，依票面 proposed Δ 合計寫入 Dashboard P8（目標區間 ~75–80 保守端）。
- Scope:
  - MUST：寫入 `docs/WAVE_PROGRESS_DASHBOARD.md`
  - MUST：Progress 末尾 append 戰報（開工前／收工後）
  - MUST：estimate → verify → apply --authorize
- NonScope:
  - 不改 core · 不做 P8-T3 webhook · 不改 war_status（除非另授權）
- AllowedPaths:
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/tickets/W-PROG-p8-80-batch-t2b-2026-07-13_state.md`
- BlockedPaths:
  - `core/**` · 暗部 · 憲法 §7 類型 · 非末尾改寫 Progress
- Dependencies:
  - 三票 overall_status=accepted + unittest 綠
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：P8 寫入後落在 ~75–80（本票取 +30 → 76%）
  - AC-2：其餘 Phase Δ=0
  - AC-3：Progress 末尾有對照表
  - AC-4：non_claims 齊

### Wave Master 擴展

- phase_targets: [P8]
- baseline_pct: "07-13 W-PROG-triple · P8=46%"
- proposed_delta_pct: "P8 +30"
- evidence_gate: L-local
- impact_size: xl
- apply_phase_pct: true
- phase_delta_lifecycle: verified
- non_claims:
  - ≠ Phase closure · ≠ P8-T3 webhook／DLQ · ≠ prod operator console · ≠ war_status 默認改寫
  - Δ 來源：MVP-03 +8 · MVP-04 +10 · T2b +12（票面提案合計；落點 76% ∈ 75–80）

---

## STATE

- overall_status: done
- current_owner: none
- next_action: 無 · Dashboard 已寫入 P8 46→76；Progress 已 append
- last_updated: 2026-07-13 · scribe／orchestrator 收口
- **授權標記**：**已授權寫入**（尚書省 session 指令 2026-07-13 · P8 衝 80 串行交付鏈）
- authorization: granted
- phase_delta_lifecycle: applied
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

### 匯總驗收證據

| 票 | Phase | proposed Δ | 命令 | 結果 |
|----|-------|------------|------|------|
| BATCH-MVP-03 | P8 | +8 | `python -m unittest tests.test_batch_prompt_and_runner -v` | 5 OK · accepted |
| BATCH-MVP-04 | P8 | +10 | `python -m unittest tests.test_batch_e2e_mock -v` + CLI mock | 3 OK · CLI ok · accepted |
| P8-T2b | P8 | +12 | `python -m unittest tests.test_operator_backlog_t2b_v1 tests.test_operator_backlog_v1 -v` | 9 OK · accepted |

---

## C_REPORT

- conclusion: accepted（待 apply 後標 done）
- checks_summary: 三票 unittest／CLI 全綠；Δ 取票面合計 +30（76% ∈ 75–80）
- risk_level: medium（單次 +30 需 --allow-large-delta；已授權）

---

## D_REPORT

- docs_updates: WAVE_PROGRESS_DASHBOARD（經 apply）
- progress_entry: 收工後 append
- followup_suggestions: P8-T3 webhook 另票；checkpoint preview 另票

## Phase Δ estimate (auto · heuristic n/a)

- phase_delta_lifecycle: estimated
- source: explicit
- heuristic: false
- heuristic_version: n/a
- heuristic_status: n/a
- impact_size: xl
- evidence_gate: L-local
- baseline_pct: 07-13 W-PROG-triple · P8=46%
- proposed_delta_pct: "P8 +30"
- rationale: parsed proposed_delta_pct='P8 +30'
- note: explicit FRAME delta preferred over heuristic
- non_claims: ≠ Dashboard write · ≠ Phase closure · 干活≠漲%

## Phase Δ verify

- phase_delta_lifecycle: verified
- proposed_delta_pct: "P8 +30"
- checks: {"checks_ok_flag": true, "review_ok_marker": true, "lifecycle_was": "estimated", "has_deltas": true}
- write_candidate: true（仍須 apply_phase_pct=true + 已授權寫入 + --authorize）
- non_claims: ≠ auto Dashboard write · verified ≠ applied
