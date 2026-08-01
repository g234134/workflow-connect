# Trace Canonical Schema Append Process v1

> **Ticket**: `FP-G3-T4-trace-canonical-schema-append-v1` · Full-Phase G3 · P3 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **對齊**：`docs/p75-intake-gate-control-plane-trace-v1.md` §Canonical · `docs/observability.md` · `docs/evidence-tier-contract-v1.md`

---

## non_claims（置頂）

| 本流程 **不是** | 說明 |
|-----------------|------|
| ≠ 授權改 `observability/trace_schema.py`／暗部 Langfuse | 本檔僅 **流程 doc** |
| ≠ 新欄位已落地 runtime | 流程齊 ≠ schema 已 merge |
| ≠ Phase closure／GA-remote | 見 evidence tier contract |
| ≠ 發明新 evidence_tier 名 | tier 仍僅 `L-local`／`CI-advisory`／`GA-remote`／`n/a` |

---

## 1. Purpose

任何 **新 trace 字段**（intake／gate／delivery／observer／ticket STATE）在被 CLI、B_REPORT、metrics 或 Reviewer 引用前，**必須**先增量寫入對應 **§Canonical schema**，並在 changelog 留一行。禁止 ad-hoc 欄位名。

---

## 2. Canonical 權威表（讀哪份）

| 域 | Canonical SSOT | 備註 |
|----|----------------|------|
| P7.5 upstream intake／gate | `docs/p75-intake-gate-control-plane-trace-v1.md` §Canonical | Wave 1 TRACE |
| P8／P8.9 delivery | `docs/p8_p89_delivery_observability_contract_v1.md` | W3-P89-OBS |
| gov-trace-v2 事件 | `docs/observability.md` + `observability/trace_schema_v2.json` | WA-T3；改碼另票 |
| Evidence **tier**（非 trace 字段） | `docs/evidence-tier-contract-v1.md` | FP-G3-T1 |

---

## 3. Append 流程（MUST）

1. **開票／FRAME**：寫明新字段名、類型、required 條件、消費方（CLI／observer／metrics）。
2. **先改 Canonical 表**：在對應 SSOT 增一行 + Changelog 日期行；**禁止**先在 runtime 發明再補 doc。
3. **交叉引用**：若跨域 join，在兩份 contract 各加一行 pointer（不複製全表）。
4. **Implementer**：B_REPORT 列字段名；verification 命令須能 `rg` 到 Canonical 表。
5. **Reviewer**：缺 Canonical 行 → **needs_changes**（硬門）。
6. **Scribe**：Progress 末尾可一句「schema append · field=`…`」；**不**改 Phase%。

### 禁止

- 在 Progress／Dashboard 用未登記字段宣稱「已觀測」
- 用 `L-GA-remote`／`prod` 當 tier（見 evidence-tier §6）
- 本流程票直接改 `.github/workflows/**` 或暗部

---

## 4. Mini checklist

- [ ] 新字段已在 Canonical 表 + changelog  
- [ ] 消費方僅引用表內名  
- [ ] Reviewer 可 `rg` 字段名於 SSOT  
- [ ] 未改 Phase%／workflows／core（除非另開 build 票）

---

## 5. Verification

```bash
rg "Canonical|append|ad-hoc|non_claims" docs/trace-canonical-schema-append-process-v1.md
```

期望命中：`non_claims`、Canonical、append、ad-hoc 禁止句。
