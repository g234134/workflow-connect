# P9 Prod Provider / Ledger Gap Index v1

> **Ticket**: `FP-G9-T3-p9-prod-ledger-gap-index-v1` · Full-Phase G9 · P9 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **對齊**：Dashboard P9 · `WH-P9-PROD-real-provider-v1` · sandbox smoke 敘事

---

## non_claims（置頂）

| 本索引 **不是** | 說明 |
|-----------------|------|
| ≠ **prod provider**／registry flip | **禁止**本票觸發 |
| ≠ sandbox PAID = 真金流 | sandbox mock only |
| ≠ GA-remote 首跑已完成 | 排程 2026-07-11 · run_url 仍 pending |
| ≠ INT Tier-A／required CI | advisory ≠ gate |

---

## 1. Landed（sandbox／本地）

| ID | 能力 | 邊界 |
|----|------|------|
| L-01 | Sandbox DRAFT→PENDING_PAYMENT→PAID | mock adapter · unittest／e2e 本地 |
| L-02 | `p9-payment-sandbox-smoke.yml` landing | **CI-advisory** · 首跑 URL pending |
| L-03 | Order ledger **sandbox** 路徑 | ≠ prod ledger |

---

## 2. Deferred／Blocked（prod）

| Gap ID | 項 | 解阻 | 票／指針 |
|--------|-----|------|----------|
| D-01 | Real payment provider | 尚書省 + Security + 合約 | `WH-P9-PROD-real-provider-v1` **blocked** |
| D-02 | Prod order ledger 閉環 | provider + env（禁本票碰 .env） | P9 prod 系列 |
| D-03 | INT／required CI 升格 | WC-PRE／治理批文 | human_ops H5 |
| D-04 | GA-remote 首跑 run_url | 2026-07-11 human dispatch | H1 |

---

## 3. Verification

```bash
rg "prod|ledger|sandbox|non_claims|blocked|provider" docs/p9-prod-ledger-gap-index-v1.md
```
