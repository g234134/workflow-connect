# WC-T6 / WC-T7 v2 — Path_id Mapping FRAME v1

> **Ticket**: `FP-G10-T2-wc-t6-t7-v2-mapping-frame-v1` · Full-Phase G10 · P10.5 · **doc/spec · planning FRAME** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **對齊**：`docs/wave_c/WC_T5_automation_coverage_contract.md` · `WC_T6_skill_distillation_lite.md` · `WC-T6-T7-v2_state.md`

---

## non_claims（置頂）

| 本 FRAME **不是** | 說明 |
|-------------------|------|
| ≠ 改 `distill_control_plane_skills_lite` **runtime** | **planning only** |
| ≠ LLM distillation／生產 artifacts 掃描 | deferred |
| ≠ 授權 `--execute` 寫 live STATE | 禁止 |
| ≠ P10.5 closure | — |

---

## 1. Goal（可驗收規劃）

凍結 **全量 path_id 映射表** 範圍：`cp.*` ↔ `wc.m2.*`（含 forbidden／HITL），作為後續 build 票輸入；本票 **只交付 FRAME／映射索引**，不改 distill CLI。

---

## 2. Mapping 範圍（MUST 列入後續實作）

| 來源 | 目標 | 備註 |
|------|------|------|
| WC-T5 cards／comms／order／loop | `wc.m2.*` | SSOT：WC_T5 contract |
| distill `PATH_ID_MAPPING` | 同上 | v2 已部分擴展；全量對賬另票 |
| `cp.ticket_state.b_report` | fallback／forbidden 语境 | 無 T5 等價時標明 |
| forbidden：`wc.m2.state.write_ticket` 等 | 不可 auto | runbook 附錄 |

---

## 3. NonScope（本票）

- 不改 `scripts/distill_control_plane_skills_lite.py`  
- 不新增 production reports 掃描  
- 不開 Round-2／S15 prod

---

## 4. 後續票建議

| 建議 ID | 類型 | 依賴 |
|---------|------|------|
| （另開）WC-T6-T7-v2-mapping-impl | build | 本 FRAME accepted |
| FP-G10-T1 S15 notify FRAME | doc | Round-2 解阻後 |

---

## 5. Verification

```bash
rg "path_id|wc.m2|distill|planning|non_claims" docs/wc-t6-t7-v2-mapping-frame-v1.md
```
