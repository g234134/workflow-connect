# Langfuse / PG Alignment — Deferred Index v1

> **Ticket**: `FP-G3-T3-langfuse-pg-alignment-deferred-index-v1` · Full-Phase G3 · P3 · **doc/spec · deferred** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **依賴**：FP-G3-T1 evidence tier SSOT（已對齊）  
> **對齊**：Dashboard P3「Langfuse/PG 对齐仍 deferred」· `docs/observability.md`

---

## non_claims（置頂）

| 本索引 **不是** | 說明 |
|-----------------|------|
| ≠ **真接** Langfuse／改暗部 observability | **禁止**本票施工 |
| ≠ gov-trace-v2 未完成 | 契約層 **已** 13/13；本檔只標對齊缺口 |
| ≠ 授權碰 Z-ENV／暗部根 | 憲法 §7 |
| ≠ Phase% 上調 | — |

---

## 1. Landed（誠實）

| ID | 能力 | 邊界 |
|----|------|------|
| L-01 | gov-trace-v2 schema + UT 13/13 | 戰車根契約層 |
| L-02 | logging_adapter／trace_middleware | 本地結構化日誌 |
| L-03 | Evidence tier／P75／P8.9 OBS contracts | doc SSOT · ≠ Langfuse |

---

## 2. Deferred

| Deferred ID | 項 | 解阻條件 | Owner |
|-------------|-----|----------|-------|
| D-01 | Langfuse trace body 全量對齊 | infra + 批文 + 另開 build 票 | Infra／暗部（未 blocked 時） |
| D-02 | PG 持久化 trace／查詢對齊 | DB 窗口 + 契約測試 | Data／Infra |
| D-03 | 生產預設導出 Langfuse | 產品／安全批文 | Governance |
| D-04 | 以 Langfuse 驅動 selector／SLO | **禁止**（Monitoring Graph 僅 L0） | — |

### 解阻檢查清單（未來票）

- [ ] 尚書省明示授權（含是否觸暗部）  
- [ ] 環境鍵僅經實例錨點 · **不**寫入可移植 doc  
- [ ] 驗收命令 + evidence_tier 標註  
- [ ] **不得**宣稱本 deferred 索引 = 已對齊

---

## 3. Verification

```bash
rg "Langfuse|deferred|non_claims|gov-trace|解阻" docs/langfuse-pg-alignment-deferred-index-v1.md
```

---

## 4. Related FRAME（planning only）

> **P3-LANGFUSE-PG-ALIGN-FRAME-v1**：欄位對照／MVP·stretch／解阻閘門見 `docs/p3-langfuse-pg-align-frame-v1.md`。  
> **≠** 對齊已完成 · **≠** 真接 Langfuse／真 PG（實作另票 `P3-LANGFUSE-PG-ALIGN-IMPL-v1` + 批文）。
