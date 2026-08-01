# Dual Control-Plane Narrative Alignment v1

> **Ticket**: `FP-G4-T1-dual-cp-narrative-alignment-v1` · Full-Phase G4 · P4 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **對齊**：W5-T5 playbook index · `docs/wave-master-ticketing-playbook.md` · `docs/full-phase-lane-map-v1.md`

---

## non_claims（置頂）

| 本對齊 **不是** | 說明 |
|-----------------|------|
| ≠ 合併／重寫三份 Master 正文結構 | 只讀敘事對齊 |
| ≠ P10 runtime 已排期 | 規劃 CP ≠ 執行完成 |
| ≠ 取代 W5-T5 INDEX §1.55 | 本檔補 **雙 CP 分工**；索引仍 W5-T5 |
| ≠ Phase closure／Round-2 GO | — |

---

## 1. 三份 CP 角色

| 檔案 | 角色 | 何時開 chat |
|------|------|-------------|
| `04_Workflows/tickets/W-MASTER-full-phase-plan_state.md` | **Full-Phase 10 組（G1–G10）** 盤點 · 缺口 · FP-* 票索引 | 跨 Phase／補最後缺口／開 FP-* |
| `04_Workflows/tickets/W-MASTER-wave-plan_state.md` | **Wave 1–5 執行規劃**（P7／P8.5／P9 戰術波次） | 依 Wave 開 Implementer |
| `04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md` | **Wave-next 戰術線**（P7／P8.5／P9 子票 STATE 對賬） | 子票衝突／GA／staging 敘事 |

**操作索引**：`04_Workflows/command_queue/QUEUE.yaml`（READY／PLANNED／BLOCKED · human_ops_sequence）。

---

## 2. 衝突裁決（誠實）

| 衝突類型 | 裁決 |
|----------|------|
| Wave 子票 `overall_status` vs Dashboard 敘事 | **以子票 STATE + C_REPORT** 為準；Dashboard 僅敘事 |
| Full-phase G* 表 vs Wave Master 同 ID | **同 ID 不重開**；QUEUE `superseded_by`／DONE 併入 |
| W-ORCH vs W-MASTER-wave-plan | 戰術細節以 **W-ORCH／子票**；波次清單以 **wave-plan** |
| Phase% | **僅** `docs/WAVE_PROGRESS_DASHBOARD.md` SSOT 日期格；本票 **不改 %** |

---

## 3. 接戰 traversal（給新 chat）

1. `QUEUE.yaml` `priority_next`／`human_ops_sequence`  
2. 若 FP-* → 讀 full-phase 對應 G* 節 + 本票 STATE  
3. 若 W1–W5 → 讀 wave-plan 對應 Wave 節  
4. 若涉 P7／P8.5／P9 GA／staging → 加讀 W-ORCH + `docs/ga-remote-closure-checklist-v1.md`  
5. Playbook 入口：`docs/wave-master-ticketing-playbook.md` · INDEX §1.55（W5-T5）

---

## 4. Verification

```bash
rg "W-MASTER-full-phase|W-ORCH|wave-plan|non_claims|QUEUE" docs/dual-cp-narrative-alignment-v1.md
```
