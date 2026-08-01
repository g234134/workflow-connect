# TICKET STATE · preview-checkpoint-b-status-integration-layer-v1

> **旁線／P4** · W6-T10 C_REPORT 小缺口收口  
> **授權**：尚書省「全開」2026-07-28  
> **≠** Phase% · ≠ Round-2 · ≠ G2–G4（另票）· ≠ DarkOps

---

## FRAME

- Goal: preview（及早期退出）路徑 `checkpoint_b_status` 與 run／sandbox 對齊，含 `integration_layer: hitl.checkpoint_b_integration_v1`。
- Scope:
  - `_build_checkpoint_b_planned`（已有）核對
  - reject／registry-blocked 早期退出補欄位
  - 既有／補強 unittest
- NonScope: HITL 核心規則變更 · Phase% · Round-2
- AllowedPaths:
  - `scripts/run_agent_standard_case_experiment.py`
  - `tests/test_agent_standard_case_experiment.py`
  - `04_Workflows/tickets/preview-checkpoint-b-status-integration-layer-v1_state.md`
- AcceptanceCriteria:
  - AC-1：preview `checkpoint_b_status.integration_layer` 存在
  - AC-2：S3 reject／S6 registry-blocked 亦帶同欄位
  - AC-3：相關 unittest 綠

---

## STATE

- **overall_status**: `done`
- **current_owner**: closed
- **last_updated**: 2026-07-28T23:55+08:00 · Implementer（全開）
- **next_action**: closed · tip#1 仍 P6 WATCH
- **授權標記**: 尚書省「全開」

---

## B_REPORT

### 變更

| 檔 | 摘要 |
|----|------|
| `scripts/run_agent_standard_case_experiment.py` | S3 reject／S6 registry-blocked `checkpoint_b_status` 補 `integration_layer` |
| （既有）`_build_checkpoint_b_planned` | 已含欄位（W6-T10 gap fix） |

### 驗證

```text
python -m unittest tests.Test…test_checkpoint_b_preview_has_integration_layer_field -v → OK
```

### non_claims

≠ Phase% · ≠ Round-2 · ≠ 改 HITL 寫檔規則
