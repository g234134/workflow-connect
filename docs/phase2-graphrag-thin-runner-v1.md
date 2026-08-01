# Phase 2 GraphRAG Thin Runner v1

> **Ticket**: `P2-GRAPHRAG-THIN-RUNNER-v1`  
> **Date**: 2026-07-15 · near-100 Wave B 薄刀（∥ sandbox 裁決）  
> **Goal**: 對齊 T4 狀態機的**本地 fixture** MVP 轉移模擬（≠ 生產 GraphRAG）

---

## What it does

| 步驟 | 行為 |
|------|------|
| load fixture | 讀 `tests/fixtures/graphrag_jobs_thin_v1/plan.json` |
| MVP 轉移 | 每 job：`queued` → `running` → `succeeded`｜`failed` |
| fail 路徑 | fixture `simulate: fail` → `status=failed` + `error_code` |
| 結構化回傳 | `ok` · `schema_version` · `jobs[]` · `summary` · `non_claims` |

**不做**：PG／`graphrag_jobs` migration、cron、改 `core/graphrag_backend.py`、ask／selector 消費、Phase% apply。

---

## Re-run commands

```powershell
python scripts/run_p2_graphrag_thin_runner_v1.py --format text
python scripts/run_p2_graphrag_thin_runner_v1.py --pretty
python scripts/run_p2_graphrag_thin_runner_v1.py --write
python -m unittest tests.test_p2_graphrag_thin_runner_v1 -v
```

**Expected**：`ok: True` · `schema_version=p2_graphrag_thin_runner_v1` · `primary_retrieval=false` · 至少一 succeeded + 一 failed（fixture）· unittest 全綠。

---

## Upstream

| 層 | 路徑 |
|----|------|
| 狀態機設計 | `docs/phase2-graphrag-jobs-state-machine-v1.md`（FP-G2-T4） |
| Gap | `docs/phase2-index-contract-gap-audit-v1.md` **GAP-GRAPH** |
| Contract | `docs/phase2-knowledge-indexing-contract-v1.md` §1.1（excluded from primary retrieval） |
| 計劃 | `04_Workflows/plans/multi-phase-near-100-p1-p6-execution-plan.md` §P2 #4 |

---

## non_claims

- ≠ GraphRAG primary retrieval／ask selector 消費  
- ≠ 生產 `graphrag_jobs` DB migration／cron／live batch  
- ≠ P2 sandbox Wave B 正式 GO／RAG E2E MVP  
- ≠ mandatory CI／Dashboard Phase% apply（`apply_phase_pct=false`）  

---

## Phase% proposal (not applied)

| Field | Value |
|-------|-------|
| phase_targets | P2 |
| baseline_pct | 66 |
| proposed_delta_pct | +1～+3 |
| apply_phase_pct | **false** |
| evidence_gate | L-local |

---

*P2-GRAPHRAG-THIN-RUNNER-v1 · 2026-07-15*
