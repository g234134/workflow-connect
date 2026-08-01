# TICKET STATE · W-PROG-phase-pct-auto-estimate-v1 · 自動估 Δ

> Governance／W-PROG tooling · **implementer** · 2026-07-13  
> **性質**：補「自動估 proposed_delta」+ 對齊「先估 → 後驗 → 再寫」；本輪 **不**寫 Dashboard 數字格。

---

## FRAME

- Goal: 開工可預估本票對 Phase 的 `proposed_delta`；驗收通過後才允許升格為 apply 候選；寫入仍走既有授權閘門。
- Scope:
  - MUST：擴充 `04_Workflows/_phase_pct_apply.py`（`estimate`／`verify`／lifecycle 閘門）
  - MUST：協議 `docs/phase-progress-impact-protocol-v1.md` §8–§9
  - MUST：unittest + self-test；WORKFLOW_INDEX G1 一句；Progress 末尾
- NonScope: **不**改 Dashboard 現況 % · **不**升 war_status · 不冒充權重表定稿
- AllowedPaths:
  - `04_Workflows/_phase_pct_apply.py`
  - `tests/test_phase_pct_apply_v1.py`
  - `docs/phase-progress-impact-protocol-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（G1 一句）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
  - `04_Workflows/tickets/W-PROG-phase-pct-auto-estimate-v1_state.md`
- phase_targets: [P4, P10]
- baseline_pct: "07-13 W-PROG-B SSOT"
- proposed_delta_pct: "0（工具票 · heuristic micro）"
- evidence_gate: L-local
- impact_size: micro
- phase_delta_lifecycle: estimated
- apply_phase_pct: false

---

## STATE

- **overall_status**: `done`
- lifecycle_phase: B→O
- last_updated: 2026-07-13
- **授權標記**：本票 **未**授權寫入 Dashboard %（僅交付 estimate／verify 節奏）

---

## Phase 影響

- **影響 Phase**：P4／P10（編排／自動化閉環治理工具）
- **baseline**：07-13 W-PROG-B
- **proposed_delta**：+0（工具票 · impact_size=micro）
- **實際上調**：否（`apply_phase_pct: false`）
- **non_claims**：≠ 自動 uplift · ≠ 權重表定稿 · ≠ Phase closure · ≠ war_status

---

## Phase Δ estimate (auto · heuristic v0.1)

- phase_delta_lifecycle: estimated
- source: explicit
- heuristic: false
- impact_size: micro
- proposed_delta_pct: "0（工具票 · heuristic micro）"
- note: 本票為 runner 擴充；Δ=0；權重表待尚書省定稿
- non_claims: ≠ Dashboard write · ≠ Phase closure · 干活≠漲%

---

## Verification

```powershell
python .\04_Workflows\_phase_pct_apply.py self-test --pretty
python -m unittest tests.test_phase_pct_apply_v1 -v
```

期望：`ok: true` · estimate／refuse_apply_before_verify／verify 步驟綠 · unittest OK。

---

## 2026-07-13 · 尚書省裁決 · heuristic v0.1 定稿

- **裁決**：用戶回覆「可以.確定」→ **採納並定稿**目前 Phase% 自動估 Δ **heuristic v0.1** 權重表  
- **狀態**：`heuristic_status=approved`／定稿（**不再**標「待尚書省定稿」／placeholder）  
- **表**：micro=0 · small=+1 · medium=+2 · large=+5 · xl=+8  
- **evidence_gate 封頂**：blocked→0 · L-local→2 · CI-advisory→5 · GA-remote→8  
- **優先**：explicit `proposed_delta_pct`；否則走此表  
- **實際上調 Dashboard %**：否（本輪僅制度定稿 · `apply_phase_pct: false`）  
- **non_claims**：≠ 自動 uplift · ≠ Phase closure · ≠ war_status · 干活≠漲%  

