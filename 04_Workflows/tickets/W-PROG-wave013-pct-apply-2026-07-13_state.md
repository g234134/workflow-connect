# TICKET STATE · W-PROG-wave013-pct-apply-2026-07-13 · Wave0–3 驗收後 Phase% 匯總寫入

> Governance／W-PROG · **scribe/ops** · same_chat · 2026-07-13  
> **已授權寫入**（尚書省本 session：執行 Orchestrator「把剛剛做事相關 P 的趴數進展更新」）  
> 匯總源票：`P75-G6` · `P75-G7` · `W3-SMOKE` · `P5-metrics` · `P89-W2` · `P868`（`WAVE5` Δ=+0 **跳過**）

---

## FRAME

- Goal: 對 Wave 0–3 已 accepted／verified 且有 `proposed_delta` 的票，保守加總後一次寫入 Dashboard Phase%。
- Scope:
  - MUST：各源票 `verify --checks-ok --write-back` 後，本票 `apply --authorize`
  - MUST：寫入 `docs/WAVE_PROGRESS_DASHBOARD.md`（当前列 + Gauge + 單行索引 + 進度條）
  - MUST：Progress／計劃／本 STATE 末尾留痕
- NonScope:
  - 不改 core／源票實作 · 不碰 DarkOps／.env · **不**因本票宣稱 Round-2 GO／Phase closure
  - WAVE5 `P7 +0` 不寫入
- AllowedPaths:
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md`（末尾 Append）
  - `04_Workflows/tickets/W-PROG-wave013-pct-apply-2026-07-13_state.md`
  - 源票 `*_state.md`（僅 lifecycle verify write-back）
- BlockedPaths:
  - `core/**` · 暗部 · `.github/workflows/**` · 憲法 §7 類型
  - 非末尾改寫 Progress／Conditions
- Dependencies:
  - 源票 C_REPORT accepted + `_phase_pct_apply verify` → `verified`
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：下列 Δ 寫入 Dashboard（見 proposed_delta_pct）
  - AC-2：WAVE5 未動 P7%
  - AC-3：Progress 有舊→新對照表
  - AC-4：non_claims 齊

### Wave Master 擴展

- phase_targets: [P7.5, P5, P8.9, P8.6, P8.7, P8.8]
- baseline_pct: "07-13 Dashboard · P7.5=46 · P5=70 · P8.9=40 · P8.6=65 · P8.7=60 · P8.8=58"
- proposed_delta_pct: "P5 +2 · P7.5 +3 · P8.6 +1 · P8.7 +1 · P8.8 +1 · P8.9 +1"
- evidence_gate: L-local
- impact_size: medium
- apply_phase_pct: true
- phase_delta_lifecycle: verified
- non_claims:
  - ≠ Phase closure · ≠ P7 Round-2 GO · ≠ prod alert／staging POST · ≠ WAVE5 解阻 · ≠ DarkOps

### 保守加總說明（勿灌水）

| Phase | 源票 proposed（raw） | W-PROG 寫入 Δ | 理由 |
|-------|----------------------|---------------|------|
| **P7.5** | G6 +1 · G7 +2 · SMOKE +1＝**+4** | **+3** | SMOKE 為 G7 鏈驗證，與 G7 證據重疊 → 減 1（保守） |
| **P5** | metrics stub +2 | **+2** | 單票 accepted · 照提案 |
| **P8.9** | P89-W2 +1 | **+1** | 照提案 |
| **P8.6** | P868 +1 | **+1** | 照提案 |
| **P8.7** | P868 +1 | **+1** | 照提案 |
| **P8.8** | P868 +1 | **+1** | 照提案 |
| **P7** | WAVE5 +0 | **跳過** | 文件 only · 不解阻 |

---

## STATE

- overall_status: in_progress
- current_owner: orchestrator
- next_action: verify → apply --authorize → Progress append
- last_updated: 2026-07-13 · 執行 Orchestrator（same_chat）
- **授權標記**：**已授權寫入**（尚書省 session 指令 2026-07-13 · 更新相關 P 趴數）
- authorization: granted
- status_by_role:
  - orchestrator: in_progress
  - implementer: pending
  - reviewer: pending
  - scribe: pending

### 匯總驗收證據（源票）

| 票 | Phase | proposed Δ | verify | C_REPORT |
|----|-------|------------|--------|----------|
| P75-G6-alert-sink-contract-v1 | P7.5 | +1 | verified | accepted |
| P75-G7-intake-gate-http-stub-v1 | P7.5 | +2 | verified | accepted |
| W3-SMOKE-g7-gate-notify-mp-chain-v1 | P7.5 | +1（W-PROG 不另疊） | verified | accepted |
| P5-metrics-grafana-stub-v1 | P5 | +2 | verified | accepted |
| P89-W2-narrative-t4-obs-projection-v1 | P8.9 | +1 | verified | accepted |
| P868-W2-runtime-inspect-catalog-selector-executor-v1 | P8.6/7/8 | 各 +1 | verified | accepted |
| WAVE5-human-staging-checklist-v1 | P7 | +0 | — | accepted · **skip** |

## Phase Δ estimate (auto · heuristic n/a)

- phase_delta_lifecycle: estimated
- source: explicit
- heuristic: false
- heuristic_version: n/a
- heuristic_status: n/a
- impact_size: medium
- evidence_gate: L-local
- baseline_pct: 07-13 Dashboard · P7.5=46 · P5=70 · P8.9=40 · P8.6=65 · P8.7=60 · P8.8=58
- proposed_delta_pct: "P5 +2 · P7.5 +3 · P8.6 +1 · P8.7 +1 · P8.8 +1 · P8.9 +1"
- rationale: parsed proposed_delta_pct='P7.5 +3 · P5 +2 · P8.9 +1 · P8.6 +1 · P8.7 +1 · P8.8 +1'
- note: explicit FRAME delta preferred over heuristic
- non_claims: ≠ Dashboard write · ≠ Phase closure · 干活≠漲%

## Phase Δ verify

- phase_delta_lifecycle: verified
- proposed_delta_pct: "P5 +2 · P7.5 +3 · P8.6 +1 · P8.7 +1 · P8.8 +1 · P8.9 +1"
- checks: {"checks_ok_flag": true, "review_ok_marker": true, "lifecycle_was": "estimated", "has_deltas": true}
- write_candidate: true（仍須 apply_phase_pct=true + 已授權寫入 + --authorize）
- non_claims: ≠ auto Dashboard write · verified ≠ applied

---

## STATE（收口）

- overall_status: done
- current_owner: none
- next_action: 無 · Dashboard 已寫入；H1 另票推進
- last_updated: 2026-07-13 · apply --authorize 完成
- phase_delta_lifecycle: applied
- authorization: granted
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

### 寫入結果（apply）

| Phase | 舊% | 新% | Δ | 依據票 |
|-------|-----|-----|---|--------|
| P7.5 | 46 | 49 | +3 | P75-G6/+1 · P75-G7/+2 · W3-SMOKE 驗證不另疊 |
| P5 | 70 | 72 | +2 | P5-metrics-grafana-stub-v1 |
| P8.9 | 40 | 41 | +1 | P89-W2-narrative-t4-obs-projection-v1 |
| P8.6 | 65 | 66 | +1 | P868-W2-runtime-inspect |
| P8.7 | 60 | 61 | +1 | 同上 |
| P8.8 | 58 | 59 | +1 | 同上 |
| P7 | 30 | 30 | 0 | WAVE5 skip |

命令：

```powershell
python .\04_Workflows\_phase_pct_apply.py apply --ticket-id W-PROG-wave013-pct-apply-2026-07-13 --authorize --label "2026-07-13 · W-PROG-wave013" --pretty
# → applied 6 phase delta(s)
```

---

## REVIEWER_NOTE · 2026-07-15 · Wave A Reviewer（C）

- 檔內前段 STATE `in_progress` 已被下方 **STATE（收口）`done`／`phase_delta_lifecycle: applied`** 取代；**勿**再當成待 apply 票重開。
- 本輪 Wave A Reviewer 重跑 `python 04_Workflows/_phase_pct_apply.py read` → average_pct=**57.89**（與 07-13 表一致）；**未**再跑 `apply --authorize`。
- Wave A 新票（P1／P4／P5）proposed Δ **不得**借本票灌水；另開 W-PROG 匯總後再裁。
