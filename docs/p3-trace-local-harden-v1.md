# P3 Trace Local Harden v1

> **Ticket**: `P3-TRACE-LOCAL-HARDEN-v1`  
> **Date**: 2026-07-15 · Wave A／near-100 P3 薄刀  
> **Goal**: 本地 gov-trace-v2 JSONL **契約一致性 hardening** + `trace_query` smoke（≠ prod Langfuse）

---

## What it does

| Check | 行為 |
|-------|------|
| `schema_fixture` | 逐行 `validate_trace_event`（必填鍵 + `gov-trace-v2`） |
| `query_by_trace_id` | `query_traces(..., trace_id=trace-wb-fixture-001)` → matches ≥ 3 |
| `query_by_task_id` | `query_traces(..., task_id=task-wb-002)` → 含 `trace_end` |

**不做**：Langfuse API、PG `task_runs` 對齊、改暗部 observability、mandatory CI、Phase% apply。

---

## Re-run commands

```powershell
python scripts/run_p3_trace_local_harden_v1.py --format text
python scripts/run_p3_trace_local_harden_v1.py --pretty
python scripts/run_p3_trace_local_harden_v1.py --write
python -m unittest tests.test_p3_trace_local_harden_v1 -v
```

**Expected**：`ok: True` · 三 checks pass · `schema_version=p3_trace_local_harden_v1` · unittest 全綠。

預設檔：`tests/fixtures/trace/sample_traces.jsonl`（相對戰車根；可 `--file` 覆蓋）。

---

## Upstream

| 層 | 路徑 |
|----|------|
| Schema | `observability/trace_schema.py` · `validate_trace_event` |
| Query CLI | `observability/trace_query.py`（WAVE-B-P1-TRACE-QUERY-CLI） |
| Fixture | `tests/fixtures/trace/sample_traces.jsonl` |
| Obs baseline | `docs/observability.md` |
| Deferred Langfuse／PG | `docs/langfuse-pg-alignment-deferred-index-v1.md`（≠ 本票） |

---

## non_claims

- ≠ prod Langfuse upgrade／真接 Langfuse  
- ≠ Langfuse↔PG alignment complete  
- ≠ mandatory CI／Dashboard Phase% apply（`apply_phase_pct=false`）  
- ≠ rewrite live `runtime/checkpoints` 或暗部 core  

---

## Phase% proposal (not applied)

| Field | Value |
|-------|-------|
| phase_targets | P3 |
| baseline_pct | 82 |
| proposed_delta_pct | +1 ～ +3 |
| apply_phase_pct | **false** |

---

*P3-TRACE-LOCAL-HARDEN-v1 · local fixture harden only*
