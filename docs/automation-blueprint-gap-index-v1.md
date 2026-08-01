# Automation Blueprint v2 — Gap Index（G8-1–G8-10）v1

> **Ticket**: `FP-G10-T3-automation-blueprint-gap-index-v1` · Full-Phase G10 · P10 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **對齊**：`docs/ninety-five-percent-automation-blueprint-v2.md` §6 · W5-T4 checklist · Dashboard P10

---

## non_claims（置頂）

| 本索引 **不是** | 說明 |
|-----------------|------|
| ≠ S15 **prod** notify 閉環 | 仍 experimental／blocked on Round-2 |
| ≠ 平台 95% 已達標 | 實驗線 ≈86.7% ≠ 平台目標 |
| ≠ 重寫 blueprint 正文 | 僅缺口索引 |
| ≠ Phase closure | — |

---

## 1. G8-1–G8-10 現況索引

| Gap | 主題 | 藍圖建議票 | 誠實現況（2026-07） |
|-----|------|------------|---------------------|
| G8-1 | Decision Rules v2 | W8-T2 | 有票／部分落地；profile 擴面仍 gap |
| G8-2 | Run path 擴面 | W8-T1 | 擴展 fixture 有進展；非全量 E2E |
| G8-3 | Delivery automation | W8-T3 | HITL 輕量化未全自動 |
| G8-4 | Notification gateway | W8-T4／S15 | **simulated／sandbox**；prod blocked Round-2 |
| G8-5 | Non-tabular family | W9-* | shadow／preview 有；非 prod |
| G8-6 | Ledger experiment | W8-T5 | 實驗 closeout 未全接 |
| G8-7 | Resume CLI | W8-T6 | 設計／部分；非全路徑 |
| G8-8 | Intake API gateway | W8-T7 | S1 仍偏 human-only |
| G8-9 | Experiment CI 升格 | W8-T8 | optional／deferred · ≠ required |
| G8-10 | Executor retry+DLQ | W8-T9 | 韌性缺口 |

---

## 2. 與 P10／P10.5

- P10／P10.5 Dashboard % **遠低於** 95% 目標；本索引 **不**上調 %。  
- S15 prod 閉環見 QUEUE `FP-G10-S15-notify` **NOT_PLANNED**（blocked Round-2）。

---

## 3. Verification

```bash
rg "G8-1|G8-10|S15|non_claims|95%" docs/automation-blueprint-gap-index-v1.md
```
