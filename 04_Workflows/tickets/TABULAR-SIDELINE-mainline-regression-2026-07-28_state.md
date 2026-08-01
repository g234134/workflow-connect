# TICKET STATE · TABULAR-SIDELINE-mainline-regression-2026-07-28 · Tabular 主鏈雙案回歸旁線

> **scribe/ops + implementer** · same_chat · 2026-07-28  
> **授權**：尚書省口令 `TABULAR_SIDELINE`（與 `WAR_BUMP_v2.64` 同輪）  
> **SSOT**：`docs/TABULAR_MVP_SSOT.md` §5 · `docs/governance/wave5_next_stage_post_defer_p6_v1.md` §1  
> **≠** Phase%／war_status 改寫 · **≠** Round-2 GO · **≠** DarkOps · **≠** prod delivery

---

## FRAME

- Goal: 開產品旁線票並跑 Tabular 主鏈最小 regression（`demo_phase` + mainline 雙案），記錄綠／紅與缺口。
- Scope:
  - MUST：`python scripts/run_demo_phase_regression_smoke.py --json`
  - MUST：`python scripts/run_tabular_mainline_regression_smoke.py --json`
  - MUST：結果寫入本 STATE evidence · Progress 一句
- NonScope:
  - Phase%／Dashboard authorize
  - war_status（另口令已升 v2.64 · 本票不改）
  - Round-2／H2–H5／execute-v2
  - DarkOps · Monitoring L1／L2 · K-2 · required CI · 外部交付／SLA
- AllowedPaths:
  - `04_Workflows/tickets/TABULAR-SIDELINE-mainline-regression-2026-07-28_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
  - `scripts/run_demo_phase_regression_smoke.py`
  - `scripts/run_tabular_mainline_regression_smoke.py`
  - `cases/demo_phase/**`／`cases/sampleco/**`（僅 smoke 寫入產物）
  - 相關 tests／scripts 被 smoke 間接呼叫者
- BlockedPaths:
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（禁止本票改 Phase%）
  - `04_Workflows/Master_Map.json`（本票不改 war_status）
  - `.env`／憲法 §7 禁區類型
- Dependencies: 口令 `TABULAR_SIDELINE`；現有 Tabular MVP 主鏈腳本
- relay_mode: same_chat
- AcceptanceCriteria:
  - 兩條 smoke 有結構化結果（`ok`／exit）或明確失敗 `message`
  - tip#1 仍為 `P6-nightly-continue`（本票並行）
  - 未改 Phase%／未宣稱主線閉環

### Wave Master 擴展

- wave_id: SIDELINE
- group_id: Tabular
- lifecycle_phase: O
- phase_targets: [P6]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: []
  - downstream_waves: []
  - blocks_if_missing: []
- risks: smoke 可能寫 case 產物 · low · 隔離在 cases/** · 不影響 prod
- observability:
  - verify_commands:
    - `python scripts/run_demo_phase_regression_smoke.py --json`
    - `python scripts/run_tabular_mainline_regression_smoke.py --json`
  - evidence_artifacts: []
  - success_signals: [both smokes ok / exit 0]
  - failure_signals: [non-zero exit · missing script · import error]
- non_claims:
  - ≠ Phase% 假閉環
  - ≠ Round-2 GO／UNLOCK／execute
  - ≠ DarkOps／prod delivery／SLA／required CI
- ticket_class: implementer
- evidence_tier: L-local
- parallel_ok: true
- parallel_to: P6-nightly-continue

---

## STATE

- **overall_status**: `done`
- **lifecycle_phase**: E
- **current_owner**: closed
- **last_updated**: 2026-07-28T18:08+08:00
- **授權標記**：**已授權開票**（口令 `TABULAR_SIDELINE`）
- **next_action**: closed · 雙 smoke 綠 · ≠ Phase%／Round-2

---

## EVIDENCE（同輪填）

| 命令 | 結果 | 備註 |
|------|------|------|
| `run_demo_phase_regression_smoke.py --json` | `ok=true` · exit **0** | message=`demo_phase main-chain regression passed` |
| `run_tabular_mainline_regression_smoke.py --json` | `ok=true` · exit **0** | `passed=3`／`case_count=3` · message=`tabular mainline regression smoke passed` |

---

## APPEND LOG

- 2026-07-28T18:06+08:00 · 開票 · QUEUE READY · tip#1 未改派
- 2026-07-28T18:08+08:00 · 同輪雙 smoke 綠 · overall_status→done · ≠ Phase% 假閉環
