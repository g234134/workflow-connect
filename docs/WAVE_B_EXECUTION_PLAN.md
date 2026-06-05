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
| 3 | `WAVE-B-P1-TRACE-QUERY-CLI` | P1 | todo | gov-trace-v2 本地 JSONL 查询 CLI |
| 4 | `WAVE-B-P2-KB-SELECTOR-HOOK-MIN` | P2 | todo | `kb_index_status` 只读 selector 降级规则 |
| 5 | `WAVE-B-P2-EVAL-TRACE-CORRELATE` | P2 | todo | eval_export 与 trace 关联追查 |

**建议依赖**：#1 → #4；#3 → #5；#2 可与 #1/#3 并行。

---

## WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE（done · 2026-06-05）

### 交付摘要

- HQ 侧 bootstrap runner：`workflow_v2/kb/repo_index_bootstrap.py`
- 冻结 scope：`workflow_v2/kb/wave_b_gov_scope.json`
- 权威 manifest：`workflow_v2/20_pilot/W3-B/index_manifest_W2-1.json`（**非** `.sample.`）
- 状态侧车：`workflow_v2/20_pilot/W3-B/index_status_W2-1.json`（`file_count=188`，`chunk_count=1190`）
- manifest RAG smoke：`workflow_v2/kb/rag_index_smoke.py`
- 单测：`tests/test_kb_index_bootstrap.py`（9/9 OK）

### 可重跑命令

见 `workflow_v2/20_pilot/W3-B/W3-B_index_pipeline_runbook.md` 附录 A。

### Wave C 留项

- 暗部 `repo_index_v1` + PG/Qdrant 替换 HQ bootstrap runner
- 全库增量 index、多 case 动态 scope

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

*文件版本：v0.2 · 2026-06-05 · Wave B #2 done*
