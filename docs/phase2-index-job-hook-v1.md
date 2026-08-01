# Phase 2 Index Job Hook — v1（skeleton）

> **版本**：v1.0（Full-Phase G2 · FP-G2-T1）  
> **日期**：2026-07-10  
> **角色**：规模化 index job **触发 hook 设计** + **dry-run skeleton CLI**（≠ 生产 cron 已部署）  
> **票**：`04_Workflows/tickets/FP-G2-T1-index-job-scheduler-hook-v1_state.md`  
> **上游**：WA-T1 `docs/phase2-knowledge-indexing-contract-v1.md` · FP-G2-T2 `docs/phase2-index-contract-gap-audit-v1.md`（GAP-SCHED／GAP-HOOK-DOC）

---

## §0 non_claims（必读）

| 禁止宣称 | 说明 |
|----------|------|
| skeleton CLI **≠** 生产 index job 已排程 | 无 cron／scheduler 部署；默认 dry-run |
| dry-run `planned_jobs` **≠** 已执行 ingest | 仅计划预览；不写 PG／Qdrant／seed corpus |
| 本票 **≠** P2 65%→closure · ≠ GraphRAG 主路 | 见 gap-audit GAP-GRAPH／GAP-E2E |
| 本票 **≠** 重写 `core/repo_index_job`／`data_pipeline` | BlockedPaths 禁 `core/**` |
| 本票 **≠** smoke_corpus 扩档 | 见 T5（串行本票 + PM） |

---

## §1 目标与边界

### Goal（MVP）

补「规模化排程」缺口的 **最小可验收增量**：

1. 文档化触发模型、解阻条件（infra／PM）、与 WA-T1／gap-audit 交叉引用  
2. 提供 `scripts/run_index_job_hook_v1.py`：**默认 `--dry-run`**，回传稳定 `dict`（`ok`／`message`／`planned_jobs`）  
3. unittest ≥3：dry-run、不触发写入、dict 形状

### NonScope（stretch／另票）

| 项 | 归属 |
|----|------|
| 生产 cron／K8s CronJob／云调度部署 | infra 票 |
| 全库 re-ingest · 改 seed INV | 禁止本票；T5+PM |
| GraphRAG 全量 · E2E LLM synthesis | T4／T3 |
| `run_id`↔`agent_runs` 真接线 | contract §6.4 未来 obs 票 |

---

## §2 触发模型（设计）

```text
[operator / future scheduler]
        │
        ▼
 run_index_job_hook_v1.py
   · 默认 dry-run / plan-only
   · 输出 planned_jobs[]（逻辑名 · pipeline · mode）
        │
        ├── dry-run：仅 dict 预览（本票交付）
        └── execute（本票不实现）：须另开票 + 解阻后接 core ingest
```

| 字段（planned_job） | 含义 | MVP |
|---------------------|------|-----|
| `job_id` | 逻辑作业名（如 `document_chunks.plan`） | ✅ |
| `pipeline` | `document_chunks` \| `repo_chunks` | ✅ |
| `mode` | 恒为 `plan_only`（本票） | ✅ |
| `writes_index` | 是否写生产 index；本票恒 `false` | ✅ |
| `notes` | 人读说明 | ✅ |

**触发源（设计 · 未接线）**

| 源 | 本票状态 |
|----|----------|
| CLI 手动 dry-run | ✅ skeleton |
| 未来 cron／scheduler | ❌ 未部署（infra） |
| CI workflow | ❌ BlockedPaths；勿本票加 workflow |

---

## §3 解阻条件（infra／PM）

在宣称「规模化 index job 已落地」前，须同时满足：

| 角色 | 条件 | 本票 |
|------|------|------|
| **Infra** | 生产 cron／调度槽位、密钥与 runner 舱位就绪；回填 runbook | **未交付** |
| **PM／尚书省** | 确认 corpus／verify 策略（尤其 T5 扩档防破 INV） | **未交付** |
| **工程** | 另开票将 hook 接到 `core` ingest（本票禁改 core） | **未交付** |

未解阻前：仅允许 dry-run／plan-only；**禁止**把本 skeleton 标为 complete／生产就绪。

---

## §4 MVP vs stretch

| 层级 | 内容 | 状态 |
|------|------|------|
| **MVP（本票）** | 本 doc · dry-run CLI · unittest · INDEX §1.24 一句 | 本票交付 |
| **Stretch** | execute 模式 · 真写 index · cron · obs `run_id` 接线 · corpus 扩 | 另票 |

---

## §5 交叉引用

| 文档／票 | 关系 |
|----------|------|
| `docs/phase2-knowledge-indexing-contract-v1.md` | 三态／双 pipeline SSOT；§6.4 Future ingest observability |
| `docs/phase2-index-contract-gap-audit-v1.md` | GAP-SCHED／GAP-HOOK-DOC → 本票 |
| `docs/knowledge-layer.md` | 实现叙述（ingest／retrieve）；本票不改其行为 |
| `04_Workflows/tickets/FP-G2-index-job_state.md` | G2 母票 |
| `FP-G2-T5-smoke-corpus-expansion-v1` | 下游（串行本票 + PM） |

---

## §6 CLI 与验收

```powershell
python scripts/run_index_job_hook_v1.py --dry-run --format json
# 预期：ok=true · mode=dry_run · planned_jobs 非空 · writes_index=false

python -m unittest tests.test_index_job_hook_v1 -v
# 预期：≥3 tests OK
```

**路径惯例**：相对 repo root／`Master_Map.json`；**禁止**硬编本机绝对路径。

---

## §7 Observability 脚注

本 skeleton 可在 `message`／job `notes` 中提示未来应携带 `run_id`（contract §6.4）。**本票不实现** `agent_runs` 写入，亦不改 observability Wave B `index_cases` 命名空间语义。

> 完整命名空间对照／non_claims：`docs/phase2-index-obs-footnote-v1.md`（票 `P2-INDEX-OBS-FOOTNOTE-v1` · **GAP-OBS-INDEX** 脚注；≠ 真接线）。

---

*PHASE2-INDEX-JOB-HOOK-v1 · FP-G2-T1 · 2026-07-10 · skeleton*
