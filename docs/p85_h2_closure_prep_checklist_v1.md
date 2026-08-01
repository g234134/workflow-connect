# P8.5 H2 Closure Prep Checklist v1

> **票**：`W4-P85-H2-CLOSURE-PREP-v1`  
> **用途**：Browser／bridge wave-H2 **收口前置**清單 · **≠** 宣稱 prod browser  
> **權威 closure**：`WH-P85-wave-H2-closure-scribe-v1`（已 DONE_WITH_GAPS · GA `29157178993`）

---

## 1. 何時用本清單

| 情境 | 動作 |
|------|------|
| 新一輪 Scenario GA 後要寫 Progress rollup | 複製票 STATE 內 **Closure Rollup Template** |
| 審計「是否誤稱 prod browser」 | 對照下方 non_claims |
| bridge 仍 stub | 列 optional follow-up，**勿**標 wave 全閉 |

---

## 2. 必核證據（Hard）

1. `gh run`／Actions：**scenario=scenario2** · completed · run_id + URL  
2. Progress **末尾**有對應條目（不改歷史段）  
3. entry／closure STATE 狀態與 gaps 一致  
4. EVD index（若專案要求）已 `recorded`

---

## 3. non_claims（必須寫進 rollup）

- ≠ Phase closure／Phase% apply  
- ≠ required CI／branch protection  
- ≠ **prod browser ready**  
- ≠ Round-2 GO／UNLOCK／execute-v2  
- ≠ DarkOps

---

## 4. Optional follow-ups（非 blocking）

- Bridge CI hardening  
- Smoke C manual matrix  
- 第二負例 fixture  
- bridge 持久化（另開票）

---


> **2026-07-29 · A2**：optional gaps 收成可驗收票 `W4-P85-OPTIONAL-BRIDGE-SMOKE-C-v1` · checklist `docs/p85_optional_bridge_smoke_c_checklist_v1.md`（≠ required CI／prod browser）。
## 5. Cross-ref

- `04_Workflows/tickets/W4-P85-H2-CLOSURE-PREP-v1_state.md`
- `docs/phase8_5-bridge-smoke-runbook-v1.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md`（敘事 only · 不改數字）
