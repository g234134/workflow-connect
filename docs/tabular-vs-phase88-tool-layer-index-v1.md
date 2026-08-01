# Tabular W3-TL vs Phase 8.8 Tool Layer — 分軌索引 v1

> **Ticket**: `FP-G9-T4-tabular-vs-phase88-tool-layer-index-v1` · Full-Phase G9 · P8.8 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **對齊**：Dashboard Wave 3-TL 註脚 · `docs/TABULAR_MVP_SSOT.md` · `docs/TOOL_CATALOG_AUTHORITY.md`

---

## non_claims（置頂）

| 本索引 **不是** | 說明 |
|-----------------|------|
| ≠ 授權 rename／合併兩軌 | **禁止合併** |
| ≠ 重寫 catalog 正文 | 僅索引 |
| ≠ Phase 8.8／Tabular MVP closure | — |

---

## 1. 兩軌對照

| 軸 | 票前綴 | 定位 | 典型產物 |
|----|--------|------|----------|
| **Tabular MVP Tool Layer** | `W3-TL-T1`–`T4` | CSV 清洗案工具四件套 | `docs/tabular-tool-*.md` · `tools/tabular_*` |
| **Phase 8.8 編排 Tool Layer** | `W3-T1`–`T4`（編排） | 通用 tool catalog／編排權威 | `shared/schemas/tool_catalog_v1.json` · `core/tool_catalog.py` · `docs/TOOL_CATALOG_AUTHORITY.md` |

**規則**：文件、模組、票 ID **禁止**互相 rename 成同一命名空間；交叉引用必須標「分軌」。

---

## 2. 何時讀哪邊

| 任務 | 讀 |
|------|-----|
| Tabular cleaning／outbox／replay | W3-TL-* |
| 通用 catalog schema／enabled 旗標／MCP 註冊敘事 | Phase 8.8 W3-T* |
| Toolchain Wave B contract | `WB-T*`（第三軸 · 見 FP-G9-T1） |

---

## 3. Verification

```bash
rg "W3-TL|Phase 8.8|分軌|禁止合併|non_claims" docs/tabular-vs-phase88-tool-layer-index-v1.md
```
