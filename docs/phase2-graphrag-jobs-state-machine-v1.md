# Phase 2 graphrag_jobs 状态机设计 — v1

> **版本**：v1.0（Full-Phase G2 · FP-G2-T4）  
> **日期**：2026-07-10  
> **角色**：**设计 doc only** — `graphrag_jobs` 作业状态机与 observability 挂钩点（≠ 生产 GraphRAG 已落地／已验收）  
> **票**：`04_Workflows/tickets/FP-G2-T4-graphrag-jobs-state-machine-v1_state.md`  
> **上游**：WA-T1 `docs/phase2-knowledge-indexing-contract-v1.md` · FP-G2-T2 `docs/phase2-index-contract-gap-audit-v1.md`（**GAP-GRAPH**） · `docs/knowledge-layer.md` §1.1

---

## §0 non_claims（必读）

| 禁止宣称 | 说明 |
|----------|------|
| 本设计 doc **≠** GraphRAG 主路／已验收 | WA-T1：`graphrag_jobs`／`graphrag_grag1` **excluded from primary retrieval** |
| 本票 **≠** DB migration／生产跑批 | NonScope；无 schema 变更、无 cron、无全量 GraphRAG job |
| 本票 **≠** P2 closure · ≠ Phase% 上调 | Dashboard／Progress 既有 SSOT 不变 |
| 本票 **≠** 改 `core/**`／selector／ask 主路 | BlockedPaths；不得用 GraphRAG 结果驱动 ask |
| Wave B `index_cases`／`kb_index_status` **≠** `graphrag_jobs` 生产 SSOT | 见 §4；obs 侧车 ≠ 本状态机已接线 |

---

## §1 目标与边界

### Goal

为未来 index／GraphRAG 专票提供可消费的 **`graphrag_jobs` 状态机设计**：

1. 状态转移图（或等价表）+ 建议字段表  
2. 链 WA-T1 contract · gap-audit **GAP-GRAPH** · knowledge-layer GraphRAG 边界  
3. observability 挂钩点（与 `index_cases` 命名空间边界写清）  
4. **blocked／defer** 标注：生产跑批待 index hook／infra 解阻

### NonScope

| 项 | 归属 |
|----|------|
| DB migration · 改 `graphrag_jobs` 表结构 | 另开 infra／data 票 |
| 生产 GraphRAG 全量跑批 · cron | infra + 解阻后专票 |
| E2E LLM synthesis | `FP-G2-T3` |
| smoke_corpus 扩档 | `FP-G2-T5`（human-blocked on PM） |
| 改 `core/graphrag_backend.py`／selector | 禁止本票 |

---

## §2 状态机（设计）

> **语义**：下列状态为 **设计契约**，供未来 runtime／migration 票对齐。  
> 现况：`graphrag_jobs` 为 **catalogued skeleton**（knowledge-layer §1.1）；本票不宣称表内已强制执行下列转移。

### 2.1 状态集合

| 状态 | 含义 | 终态？ |
|------|------|--------|
| `queued` | 作业已登记、等待执行器拾取 | 否 |
| `running` | 执行器已认领、正在处理 | 否 |
| `succeeded` | 作业成功完成（产物可观测；**仍非** primary retrieval） | 是 |
| `failed` | 作业失败（可带 `error_code`／`message`） | 是（可经 `retry` 回 `queued`） |
| `cancelled`（可选） | 人工／策略取消 | 是 |
| `deferred`（可选） | 显式推迟（缺 infra／依赖未解阻） | 否（解阻后 → `queued`） |

**MVP 必含**：`queued` · `running` · `succeeded` · `failed`。  
`cancelled`／`deferred` 为 stretch，便于与 index hook 解阻叙事对齐。

### 2.2 状态转移图

```text
                    ┌─────────────┐
         enqueue    │   queued    │◄──── retry（策略允许）
       ────────────►│             │◄──── resume（自 deferred）
                    └──────┬──────┘
                           │ claim / start
                           ▼
                    ┌─────────────┐
                    │   running   │
                    └──────┬──────┘
              ┌────────────┼────────────┐
              │ success    │ failure    │ cancel（可选）
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌────────────┐
        │succeeded │ │  failed  │ │ cancelled  │
        └──────────┘ └────┬─────┘ └────────────┘
                          │
                          │（可选 retry）
                          └──► queued

  [blocked path · 设计]
  缺 infra／index hook 未解阻 → deferred（或不入队）
  deferred ──解阻──► queued
```

### 2.3 转移表（等价）

| From | Event | To | 守卫／备注 |
|------|-------|-----|------------|
| — | `enqueue` | `queued` | 须有 `job_id`／`job_type`；本票不实现写入 |
| `queued` | `claim`／`start` | `running` | 单执行器认领；防双跑（未来锁） |
| `running` | `complete_ok` | `succeeded` | 写 `finished_at`；**不**升格为 ask 主路 |
| `running` | `complete_err` | `failed` | 写 `error_code`／`message` |
| `running` | `cancel`（可选） | `cancelled` | 人工／策略 |
| `failed` | `retry`（可选） | `queued` | 须策略允许；计 `attempt` |
| —／`queued` | `defer`（可选） | `deferred` | **blocked**：缺 index hook／infra |
| `deferred` | `unblock` | `queued` | 解阻后入队 |

**禁止转移（设计硬约束）**

- `succeeded` → 任意「驱动 ask selector」语义（违反 WA-T1 excluded）  
- 本票范围内任何状态 → 宣称「GraphRAG 已验收」

---

## §3 建议字段表

> 字段名为 **设计建议**，对齐 knowledge-layer／contract 叙述；**≠** 已 migration 的权威 DDL。  
> 冲突时以未来 data 票 + WA-T1 修订为准。

| 字段 | 类型（建议） | 必填（MVP） | 说明 |
|------|--------------|-------------|------|
| `job_id` | text／uuid | ✅ | 作业主键 |
| `job_type` | text | ✅ | 如 `graphrag`／历史 `ingest` 列用途（见 knowledge-layer §3.4） |
| `status` | enum | ✅ | `queued`／`running`／`succeeded`／`failed`（+ 可选） |
| `attempt` | int | ✅ | 重试计数；默认 0 |
| `created_at` | timestamptz | ✅ | 入队时间 |
| `started_at` | timestamptz | 运行后 | `running` 起填 |
| `finished_at` | timestamptz | 终态 | `succeeded`／`failed`／`cancelled` |
| `error_code` | text | failed 时 | 稳定机器码 |
| `message` | text | 建议 | 人读说明；对齐合约 `ok`／`message` 习惯 |
| `run_id` | text | 建议 | 未来关联 `agent_runs`（contract §6.4；**本票不接线**） |
| `payload_ref` | text／json | 可选 | 输入／产物逻辑引用（非密钥） |
| `skeleton` | bool | 建议 | `true` = 实验／未升格主路 |

**与 document ingest 列的边界**：knowledge-layer 记载文件 pipeline 可能写入 `job_type=ingest` 至同表。本状态机文档的 **GraphRAG 语义**仅适用于 `job_type` 标明图任务（或未来专列）的行；**不得**把 ingest 行误标为 GraphRAG 主路验收。

---

## §4 Observability 挂钩点

### 4.1 命名空间边界（必读）

| 命名空间 | 用途 | 与本状态机 |
|----------|------|------------|
| Wave B `index_cases`／`kb_index_status` | eval／pilot 侧车就绪度（`docs/observability.md` §9） | **≠** `graphrag_jobs` 生产作业 SSOT |
| WA-T1／FP-G2 index hook | document／repo 规模化排程（T1 skeleton） | 解阻前置；**不**等于 GraphRAG 已跑 |
| 本设计 `graphrag_jobs.status` | 图任务作业列（未来） | 设计 only；未接线 |

### 4.2 建议挂钩（未来票 · 本票不实现）

| 挂钩点 | 建议 | 本票 |
|--------|------|------|
| job 生命周期事件 | 状态变更时写结构化 log／trace（含 `job_id`／`status`） | ❌ defer |
| `run_id` ↔ `agent_runs` | 对齐 contract §6.4 Future ingest observability | ❌ defer |
| wf／eval 摘要 | **勿**把 `kb_index_status` 误读为 GraphRAG `succeeded` | 文档约束 ✅ |
| Dashboard Phase% | **禁止**本票上调；成功信号仅「状态机 doc 存在」 | ✅ |

---

## §5 blocked／defer 标注

| 项 | 状态 | 解阻条件 | 下游 |
|----|------|----------|------|
| 生产 GraphRAG 跑批 | **blocked** | index hook 可执行路径 + infra 调度 + 专票授权 | 未来 GraphRAG runtime 票 |
| DB migration（强制 status enum） | **defer** | data／infra 票 + 与现有 `ingest` 行共存策略 | 非本票 |
| ask／selector 消费 GraphRAG | **blocked（制度）** | WA-T1 修订 + runbook 门檻 + 尚书省批文 | 禁止本票暗示 |
| E2E 问答验收 | **out of scope** | — | `FP-G2-T3` |
| smoke_corpus 扩档 | **out of scope** | PM verify | `FP-G2-T5` |

**GAP-GRAPH（gap-audit）摘要**：GraphRAG **excluded from primary retrieval**；`graphrag_jobs`／backend 为 skeleton；本票补齐 **状态机设计 doc**，不修复 runtime gap。

---

## §6 交叉引用

| 文档／票 | 关系 |
|----------|------|
| `docs/phase2-knowledge-indexing-contract-v1.md` §1.1／§2 | WA-T1：GraphRAG excluded；`graphrag_jobs` catalogued skeleton |
| `docs/phase2-index-contract-gap-audit-v1.md` **GAP-GRAPH** | 本票关闭「无状态机设计 doc」缺口（≠ 关闭 GraphRAG 能力缺口） |
| `docs/knowledge-layer.md` §1.1／§3.4／§8 | 实现叙述；禁止 `graphrag_grag1` 驱动 ask |
| `docs/phase2-index-job-hook-v1.md` | T1 skeleton；生产跑批解阻前置之一 |
| `docs/observability.md` §9 `index_cases` | 侧车观测边界 |
| `FP-G2-T3`／`FP-G2-T5` | 并行／串行邻票；本票不碰 |
| `P2-GRAPHRAG-THIN-RUNNER-v1` | 本地 fixture thin runner（`docs/phase2-graphrag-thin-runner-v1.md`）· ≠ 生产跑批 |

---

## §7 验收命令（本票）

```text
rg "graphrag_jobs|queued|running|succeeded|failed|non_claims|GAP-GRAPH" docs/phase2-graphrag-jobs-state-machine-v1.md
```

预期：上述关键词均命中；无 `core/**`／migration／workflow 变更。
