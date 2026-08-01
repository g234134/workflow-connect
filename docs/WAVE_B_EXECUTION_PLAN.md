# Wave B Execution Plan

> **摘要日**：2026-06-05  
> **前提**：Wave A 治理层 + eval gate CI 已绿（含 `WAVE-B-P1-ASK-RAG-SELECTOR-CI-FIX`）  
> **主轴**：深化 Phase 2（知识层 / Codebase Indexing）与 Phase 3（可观测性 / Trace / eval 可视化）

---

## 批次一（P1 / 高优 P2）

| 顺序 | 票号 | 优先级 | 状态 | 说明 |
|------|------|--------|------|------|
| 1 | `WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE` | P1 | **done** | 治理关键 subtree 真实 index bootstrap + 案卷 sync/gate + manifest RAG smoke |
| 2 | `WAVE-B-P1-EVAL-GATE-REPORT-BOOTSTRAP` | P1 | **done** | eval_export → Markdown/JSON 报表 + CI artifact |
| 3 | `WAVE-B-P1-TRACE-QUERY-CLI` | P1 | **done** | gov-trace-v2 本地 JSONL 查询 CLI |
| 4 | `WAVE-B-P2-KB-SELECTOR-HOOK-MIN` | P2 | **done** | `core/kb_index_selector_hook.py` + test harness |
| 5 | `WAVE-B-P2-EVAL-TRACE-CORRELATE` | P2 | **done** | eval_export 与 trace 关联追查 |

**建议依赖**：#1 → #4；#3 → #5；#2 可与 #1/#3 并行。

---

## 批次二（P3 · 可观测汇总）

| 顺序 | 票号 | 优先级 | 状态 | 说明 |
|------|------|--------|------|------|
| 1 | `WAVE-B-P3-KB-INDEX-EVAL-OBSERVABILITY` | P3 | **TODO** | eval 导出 / 报表携带 `kb_index_status` |
| 2 | `WAVE-B-P3-WF-STATUS-SUMMARY-CLI` | P3 | **done** | Gate / Index / Trace 一页总览 CLI |
| 3 | `WAVE-B-P3-FLAGGED-TRIAGE-ENRICH` | P3 | **done** | needs_review triage 输出增强 |

**建议依赖**：票 3 硬依赖票 2；票 1 与票 2 可并行。

---

## WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE（done · 2026-06-05）

### 交付摘要

- HQ 侧 bootstrap runner：`workflow_v2/kb/repo_index_bootstrap.py`
- 冻结 scope：`workflow_v2/kb/wave_b_gov_scope.json`
- 权威 manifest：`workflow_v2/20_pilot/W3-B/index_manifest_W2-1.json`（**非** `.sample.`）
- 状态侧车：`workflow_v2/20_pilot/W3-B/index_status_W2-1.json`（`file_count=190`，`chunk_count=1204`）
- manifest RAG smoke：`workflow_v2/kb/rag_index_smoke.py`
- 单测：`tests/test_kb_index_bootstrap.py`（9/9 OK）

### 可重跑命令

见 `workflow_v2/20_pilot/W3-B/W3-B_index_pipeline_runbook.md` 附录 A。

### Wave C 留项

- 暗部 `repo_index_v1` + PG/Qdrant 替换 HQ bootstrap runner
- 全库增量 index、多 case 动态 scope

---

## WAVE-B-P2-KB-SELECTOR-HOOK-MIN（done · 2026-06-05）

### 交付摘要

- Hook 模块：`core/kb_index_selector_hook.py` → `decide_kb_index_tool_gate(kb_index_status, tool_name)`
- test harness：`core/ask_rag_selector.py` → `apply_kb_index_tool_gate_from_hints`（`selector_hints.kb_index_status`）
- 单测：`tests/test_kb_index_selector_hook.py`（13/13 OK）
- 契约：`workflow_v2/20_pilot/W3-B_kb_contract.md` §5.4.1–§5.4.2 truth table

### 可重跑命令

```bash
python -m unittest tests.test_kb_index_selector_hook -v
python -m unittest tests.test_ask_selector_and_answer tests.test_context_subagent_routing -v
```

### Wave C 留项

- `GOV_KB_INDEX_SELECTOR_HOOK_ENABLED=1` prod 默认与案卷／ENG-CTX runtime wiring
- `decision_log` 写入 gov-trace-v2

---

## WAVE-B-P1-EVAL-GATE-REPORT-BOOTSTRAP（done · 2026-06-05）

### 交付摘要

- 报表 CLI：`observability/eval_report.py` → `artifacts/eval/eval_report.latest.{md,json}`
- CI：`eval-gate-ci.yml` PR + nightly 上传 artifact（`eval-gate-report-pr` / `eval-gate-report-nightly`）
- 单测：`tests/test_eval_report.py`（4/4 OK）

### 可重跑命令

```bash
python -m observability.eval_report tests/fixtures/eval/eval_export_sample.jsonl --out-dir artifacts/eval
python -m unittest tests.test_eval_report tests.test_eval_stats -v
```

### Wave C 留项

- Grafana/HTML dashboard、Slack 通知、真实 nightly cohort 自动 threshold tighten

---

## WAVE-B-P1-TRACE-QUERY-CLI（done · 2026-06-05）

### 交付摘要

- CLI：`observability/trace_query.py` → `python -m observability.trace_query`
- 过滤器：`--trace-id` / `--task-id` / `--session-id` / `--event`；`--limit`；`--format json|text`
- 可重用 `query_traces()` dict：`{ ok, message, matches, events[], summary }`
- Fixture：`tests/fixtures/trace/sample_traces.jsonl`
- 单测：`tests/test_trace_query.py`（9/9 OK，含 trace/task/session 与零匹配）

### 可重跑命令

```bash
python -m observability.trace_query --help
python -m observability.trace_query --file tests/fixtures/trace/sample_traces.jsonl --trace-id trace-wb-fixture-001 --format json
python -m unittest tests.test_trace_query tests.test_trace_schema tests.test_logging_adapter tests.test_trace_middleware -v
```

### Wave C 留项

- PG + Langfuse unified query API

---

## WAVE-B-P2-EVAL-TRACE-CORRELATE（done · 2026-06-05）

### 交付摘要

- 关联 CLI：`observability/eval_trace_correlate.py`（eval_export + gov-trace-v2 join）
- Join 优先序：`trace_id` > `task_id` > `session_id`；默认仅 flagged 列（`needs_review` / `--fail-on-tags`）
- 复用 `trace_query.iter_trace_events` / `_build_summary`；`trace_completeness` 来自 gov-trace-v2 `trace_end`
- Fixture 扩充：`tests/fixtures/trace/sample_traces.jsonl`（`tr-3` / `t-infra` 对齐 eval sample）
- 单测：`tests/test_eval_trace_correlate.py`

### 可重跑命令

```bash
python -m observability.eval_trace_correlate \
  --eval tests/fixtures/eval/eval_export_sample.jsonl \
  --trace tests/fixtures/trace/sample_traces.jsonl \
  --format json

python -m unittest tests.test_eval_trace_correlate tests.test_trace_query -v
```

### Wave C 留项

- nightly correlate artifact、Langfuse deep link、Web UI

---

## WAVE-B-P3-WF-STATUS-SUMMARY-CLI（done · 2026-06-05）

### 交付摘要

- 汇总 CLI：`observability/wf_status_summary.py` → `artifacts/wf/wf_status_summary.latest.{md,json}`
- 组装既有 `eval_report` / `index_status` / `eval_trace_correlate`（只读；不改 gate 逻辑）
- 单测：`tests/test_wf_status_summary.py`（6/6 OK）

### 可重跑命令

```bash
python -m observability.wf_status_summary \
  --eval tests/fixtures/eval/eval_export_sample.jsonl \
  --index-status workflow_v2/20_pilot/W3-B/index_status_W2-1.json \
  --trace-jsonl tests/fixtures/trace/sample_traces.jsonl \
  --out-dir artifacts/wf

python -m unittest tests.test_wf_status_summary -v
```

### Wave C 留项

- 建议后续接入 CI artifact（本票未改 `.github/workflows/*`）
- 消费票 2 `index_context_breakdown` 扩展 Gate 区块

---

## WAVE-B-P3-KB-INDEX-EVAL-OBSERVABILITY（done · 2026-06-05）

### 交付摘要

- Exporter 侧车：`GOV_EVAL_EXPORT_KB_INDEX_STATUS`（默认 **0**）；`--case-index-map`；解析优先序 metadata → selector_hints → case map
- Schema：`eval_export_schema.json` 可选 `kb_index_status` / `kb_index_job_id`
- Report：`eval_report` → `index_context_breakdown` + Markdown **Index context** 小节
- Fixture：`eval_export_sample.jsonl`（1 列含 `kb_index_status=ready`）；`ibridge_records.jsonl` metadata；`case_index_map_W2-1.json`
- 单测：`tests/test_eval_exporter.py`（+6）、`tests/test_eval_report.py`（+3）

### 可重跑命令

```bash
GOV_EVAL_EXPORT_KB_INDEX_STATUS=1 \
  python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl \
  --case-index-map tests/fixtures/eval/case_index_map_W2-1.json \
  -o /tmp/eval_kb.jsonl

python -m observability.eval_report tests/fixtures/eval/eval_export_sample.jsonl --out-dir artifacts/eval

python -m unittest tests.test_eval_exporter tests.test_eval_report tests.test_eval_ci_check -v
```

### Wave C 留项

- 案卷／ENG-CTX runtime 自动 wiring；gov-trace-v2 JSONL 默认写档仍不含 kb_index（export 侧车 only）

---

## WAVE-B-P3-FLAGGED-TRIAGE-ENRICH（done · 2026-06-05）

### 交付摘要

- `eval_trace_correlate`：`--format triage-md`；JSON/JSONL 列含 `triage` 子物件；`--only-needs-review`（默认 true）
- `trace_query`：`summary.kb_index_status`（metadata/selector_hints）；`--format triage`
- Export 侧车：`attach_kb_index_to_trace_metadata` → `source_ref.kb_index_status` + `trace_metadata_sidecar`
- Fixture：`sample_traces.jsonl` tr-3 含 `metadata.kb_index_status`
- 单测：`tests/test_eval_trace_correlate.py`（+8）、`tests/test_trace_query.py`（+3）

### 可重跑命令

```bash
GOV_EVAL_EXPORT_KB_INDEX_STATUS=1 \
  python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl \
  --case-index-map tests/fixtures/eval/case_index_map_W2-1.json \
  -o /tmp/e.jsonl

python -m observability.eval_trace_correlate \
  --eval /tmp/e.jsonl \
  --trace tests/fixtures/trace/sample_traces.jsonl \
  --format triage-md

python -m observability.trace_query \
  --file tests/fixtures/trace/sample_traces.jsonl \
  --trace-id tr-3 \
  --format triage

python -m unittest tests.test_eval_trace_correlate tests.test_trace_query -v
```

---

## Wave B 小结

- **flagged triage enrich done**（`WAVE-B-P3-FLAGGED-TRIAGE-ENRICH`）：correlate triage-md + trace_query kb_index/triage format；观测 only。
- **kb index eval observability done**（`WAVE-B-P3-KB-INDEX-EVAL-OBSERVABILITY`）：eval export/report 可选携带 `kb_index_status` 分桶；观测 only，非 gate／非 prod selector。
- **repo index bootstrap done**（`WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE`）：治理关键 subtree 真实 index → sync → gate → manifest RAG smoke 全链已跑通；权威范本见 runbook 附录 A。
- **eval gate report bootstrap done**（`WAVE-B-P1-EVAL-GATE-REPORT-BOOTSTRAP`）：eval_export → Markdown/JSON 报表 + CI artifact。
- **trace query CLI done**（`WAVE-B-P1-TRACE-QUERY-CLI`）：gov-trace-v2 JSONL 本地只读追查；见 `docs/observability.md` §7。
- **eval–trace correlate done**（`WAVE-B-P2-EVAL-TRACE-CORRELATE`）：flagged eval 列一键追到 trace 摘要。
- **wf status summary done**（`WAVE-B-P3-WF-STATUS-SUMMARY-CLI`）：Gate / Index / Trace 一页总览；见 `docs/observability.md` §8。
- **待办**：Wave C 可视化与 nightly correlate artifact。

---

*文件版本：v0.8 · 2026-06-05 · Wave B P3 flagged triage enrich done*
