# TICKET STATE · W-PROG-phase-pct-apply-runner-v1 · Phase% apply CLI

> Governance／W-PROG tooling · **implementer** · 2026-07-13  
> **性質**：補齊「完成時可更新對應 P 趴數」的 **apply runner**（非本輪寫入 Dashboard 數字）。

---

## FRAME

- Goal: 提供可重跑 CLI，讀／提案／授權後寫入 `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% SSOT。
- Scope:
  - MUST：`04_Workflows/_phase_pct_apply.py`（read／plan／from-ticket／apply／self-test）
  - MUST：協議索引 `docs/phase-progress-impact-protocol-v1.md` §8
  - MUST：`Master_Map.json` runners 別名 · WORKFLOW_INDEX G1 一句 · unittest
  - MUST：Progress 末尾 append
- NonScope: 本輪 **不**改 Dashboard 現況數字 · **不**升 war_status · 不改憲法／合約全文
- AllowedPaths:
  - `04_Workflows/_phase_pct_apply.py`
  - `tests/test_phase_pct_apply_v1.py`
  - `docs/phase-progress-impact-protocol-v1.md`
  - `04_Workflows/Master_Map.json`（runners only）
  - `04_Workflows/WORKFLOW_INDEX.md`（G1 一句）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
  - `04_Workflows/tickets/W-PROG-phase-pct-apply-runner-v1_state.md`
- phase_targets: [P4, P10]
- baseline_pct: "07-13 W-PROG-B SSOT"
- proposed_delta_pct: "0（本票交付 runner · 不寫數字格）"
- evidence_gate: L-local
- apply_phase_pct: false

---

## STATE

- **overall_status**: `done`
- lifecycle_phase: B→O
- last_updated: 2026-07-13
- **授權標記**：本票 **未**授權寫入 Dashboard %（僅交付工具）

---

## Phase 影響

- **影響 Phase**：P4／P10（編排／自動化閉環治理工具）
- **baseline**：07-13 W-PROG-B
- **proposed_delta**：+0（工具票）
- **實際上調**：否（`apply_phase_pct: false`）
- **non_claims**：≠ 自動對普通票 uplift · ≠ Phase closure · ≠ war_status 升版

---

## Verification

```powershell
python .\04_Workflows\_phase_pct_apply.py self-test --pretty
python -m unittest tests.test_phase_pct_apply_v1 -v
```

期望：`ok: true` · 5 tests OK。
