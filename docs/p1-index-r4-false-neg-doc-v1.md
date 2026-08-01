# P1 INDEX R4 假陰性輕修 v1

> **Ticket**: `P1-INDEX-R4-FALSE-NEG-DOC-v1`  
> **Date**: 2026-07-15 · near-100 無批文薄刀  
> **Upstream**: `P1-GOV-RESIDUAL-CHECKOFF-v1` R4（原 `explicit defer`）  
> **Phase%**: proposed P1 +1～+2 · `apply_phase_pct=false`（≠ 本票寫 Dashboard）

---

## Purpose

消除 `04_Workflows/WORKFLOW_INDEX.md` 對**已存在** runbook／thin 入口的**假陰性**敘事（INDEX 暗示「尚未就緒／尚無入口」，但檔案已落地），並把 P1 checkoff R4 收為 **done**。

**non_claims**：≠ 正式 GraphRAG Job Smoke runbook 已立 · ≠ DarkOps 解禁 · ≠ Phase% uplift · ≠ INDEX 全文重排 · ≠ 真 PG／prod。

---

## False-negative inventory（本票範圍）

| ID | 假陰性敘事（修前） | 實際已存在 | 修法 |
|----|-------------------|------------|------|
| FN-1 | §2.1「待完成 RAG_Smoke_Test v0.1 穩定後，另立 runbook」 | §1.2 · `04_Workflows/runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md` | §2.1 改為「RAG 已落地；指向 §1.2」 |
| FN-2 | §2 標題／§2.1 易讀成「GraphRAG 全無入口」 | `docs/phase2-graphrag-thin-runner-v1.md` + CLI（`P2-GRAPHRAG-THIN-RUNNER-v1`） | §2.1 標 thin 入口；仍誠實標「正式 smoke runbook 預留」 |
| FN-3 | checkoff R4 長期 `explicit defer` | 本票 doc + INDEX 輕修 | R4 Verdict → **done** |

**非假陰性（保留）**：§2.2 DarkOps Minimal Task — DarkOps Blocked 為真；本票**不**改為可跑。

---

## INDEX 變更摘要（AllowedPaths）

- `WORKFLOW_INDEX.md` §2 標題／導語：區分「無正式專用 smoke」vs「上游依賴不存在」。
- §2.1：去掉「待 RAG v0.1」假陰性；交叉引用 §1.2 + GraphRAG thin runner。
- 既有 GraphRAG 狀態機索引句：加一行 thin runner 交叉引用（最小）。

---

## Re-run commands

```powershell
python -m unittest tests.test_p1_index_r4_false_neg_doc_v1 -v
```

**Expected**：unittest 全綠；INDEX §2.1 含 `RAG_SMOKE_TEST_RUNBOOK` 與 `phase2-graphrag-thin-runner-v1`；checkoff R4 = done。

---

## Phase% proposal (not applied)

| Field | Value |
|-------|-------|
| phase_targets | P1 |
| baseline_pct | 90 |
| proposed_delta_pct | +1 ～ +2 |
| apply_phase_pct | **false** |

---

*P1-INDEX-R4-FALSE-NEG-DOC-v1 · doc-only · 2026-07-15*
