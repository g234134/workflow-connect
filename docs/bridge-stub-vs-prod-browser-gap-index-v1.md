# Bridge Stub vs Prod Browser — Gap Index v1

> **Ticket**: `W4-P85-bridge-prod-gap-index-v1` · Wave 4／G8 · P8.5 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **對齊**：`docs/phase8_5-bridge-smoke-runbook-v1.md` · Dashboard P8.5 · W3-P8-BRG

---

## non_claims（置頂）

| 本索引 **不是** | 說明 |
|-----------------|------|
| ≠ Scenario2 **GA-remote** 已通過 | 不需本票 run_url；GA 仍 human H1 |
| ≠ **prod browser**／Computer Use 就緒 | bridge 仍 **in-memory stub** |
| ≠ required CI | `bridge-smoke.yml` = advisory |
| ≠ P8.5 Phase closure | — |

---

## 1. Landed

| ID | 能力 | tier |
|----|------|------|
| L-01 | Smoke A/B 本機 14/14 · 7/7 | L-local |
| L-02 | `bridge-smoke.yml` landing | CI-advisory |
| L-03 | Minimal orchestration bridge API（stub） | L-local · in-memory |

---

## 2. Gaps（stub → prod browser）

| Gap ID | 缺口 | 解阻 |
|--------|------|------|
| G-01 | 真 browser／Computer Use 執行器 | 另開 infra／產品票 · 非 stub |
| G-02 | Scenario2 遠端 GA run_url | human dispatch 2026-07-11 |
| G-03 | 非 in-memory 持久化／多實例 | 架構票 |
| G-04 | required CI／merge gate | WC-PRE／hard_no 維持 |

**閱讀規則**：有 L-01／L-02 **不得**寫「prod browser ready」。

---

## 3. Verification

```bash
rg "stub|prod browser|Scenario2|non_claims|in-memory" docs/bridge-stub-vs-prod-browser-gap-index-v1.md
```
