# Toolchain Runtime Gap Audit v1（WB-T1–T3）

> **Ticket**: `FP-G9-T1-toolchain-runtime-gap-audit-v1` · Full-Phase G9 · P8.6–P8.8 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **對齊**：`docs/wave-b-toolchain-readme-v1.md` · `docs/toolchain-local-gaps-quickview-v1.md` · Dashboard Wave B

---

## non_claims（置頂）

| 本審計 **不是** | 說明 |
|-----------------|------|
| ≠ selector／executor **prod flip** | contract 綠 ≠ 生產預設 |
| ≠ WC-PRE approved／required CI | gaps 追蹤 ≠ 批文 |
| ≠ 重做 WB-T1–T3 contract | DNR；本檔只標 **runtime gap** |
| ≠ Phase% 上調 | — |

---

## 1. Contract vs Runtime（摘要）

| 層 | Contract（已落地） | Runtime 現況 | Gap ID |
|----|------------------|--------------|--------|
| **WB-T1** Catalog+Selector | `tool-catalog-and-selector-contract-v1.md` + UT | plan_only／推薦；**不**驅動主鏈 E2E | GAP-T1-01 plan_only 預設 |
| **WB-T2** Executor+Sandbox | executor／sandbox safety contract + UT | subprocess timeout 契約；執行仍受控／optional | GAP-T2-01 timeout／sandbox 邊界需 WC-PRE 追蹤 |
| **WB-T3** Outbox+Feedback | outbox／feedback contract + UT | Tabular outbox 寫入可測；跨 Phase 消費不完整 | GAP-T3-01 consumer／feedback 全鏈 |
| **Local gaps CLI** | WC-C1-01 quickview | 本地聚合 **investigation-only** | GAP-LOC-01 ≠ CI gate |

---

## 2. Gap 索引（解阻條件）

| Gap ID | 描述 | 解阻 | 禁止宣稱 |
|--------|------|------|----------|
| GAP-T1-01 | Selector 仍 plan_only | WC-PRE／產品批文後另票 | 「selector 已 prod」 |
| GAP-T2-01 | Executor timeout／sandbox 契約 vs 真負載 | WC-PRE-03 + soak 另線 | 「executor 生產就緒」 |
| GAP-T3-01 | Outbox feedback 跨系統 ack | P8.9／另票 | 「feedback 全自動閉環」 |
| GAP-LOC-01 | local gaps quickview | 僅開發者工具 | 「CI required」 |

---

## 3. 驗證入口（只讀）

```bash
python -m unittest tests.test_tool_catalog_and_selector_contract_v1 tests.test_tool_executor_and_sandbox_contract_v1 tests.test_outbox_and_feedback_layer_contract_v1 -v
python scripts/run_toolchain_local_gaps_quickview.py --format json
```

（本票 **不要求** 重跑作為 AC 硬門；命令供後續 build 票引用。）

---

## 4. Verification（本票 AC）

```bash
rg "WB-T1|gap|plan_only|non_claims|runtime" docs/toolchain-runtime-gap-audit-v1.md
```
