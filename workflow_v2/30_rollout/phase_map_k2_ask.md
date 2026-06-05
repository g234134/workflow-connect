# Phase Map — K-2 × ask（shadow / canary 观察点）

> **票号**：W3-A-ORCH  
> **用途**：文本级节点映射；**非** runtime 配置  
> **合流语义**：邻接 `docs/k2_merge_strategy.md`（只读）

---

## 1. 关键节点一览

| 节点 ID | 名称 | 路径／模块（逻辑） | 输入 | 输出 | Fallback |
|---------|------|---------------------|------|------|----------|
| **N-ENTRY** | Ask 入口 | `app_api` `/api/ask` 或 ask pipeline | HTTP / `task_input` | ask 图 state | 4xx/5xx 标准错误 |
| **N-CTX** | Context 组装 | `core/context_entry.build_rooted_context` | `task_input`, `mode` | `root_context` 包 | deny metadata（A-3） |
| **N-SEL** | Selector + RAG | ask selector → retrieve | context | retrieval hits | skip-RAG / greeting 路径 |
| **N-ANS** | Answer | `perform_direct_answer` / skill 路径 | hits + context | **ask 主答案** text + metadata | retry（P 线） |
| **N-K2** | K-2 图 | `run_k2_flow` / `build_k2_graph` | 与 ask 同构或复制 `task_input` | K-2 envelope + tags | K-2 `ok:false` |
| **N-MERGE** | 合流 | `merge_ask_and_k2` | ask + K-2 结果 | merged envelope；`primary_source` | 双 ok → **ask**；`infra_risk` → ask 内容 + `ok=False` |
| **N-SPOOL** | Shadow 写入 | `k2_prod_shadow_worker_cli` → spool | merge 侧车 | JSONL spool 行 | 丢 spool **不**改 user 响应 |
| **N-EXPORT** | Eval 导出 | nightly export · `eval_ci_check` | spool / records | 指标报告 | CI fail 信号 |

---

## 2. Phase 1 — Shadow 观察点

| 观察点 | 节点 | 记录什么 | 案卷字段建议 |
|--------|------|----------|--------------|
| **O-S1** | N-ENTRY → N-ANS | ask 延迟 p50/p99；`ok` | `shadow_run_*.md` §latency |
| **O-S2** | N-K2 → N-MERGE | K-2 异步完成率；`infra_risk` 计数 | `execution_evidence.metrics_ref` |
| **O-S3** | N-MERGE | `primary_source=ask`；`merge_safe` / `unacceptable` | 对照 ask 主答案 diff 索引 |
| **O-S4** | N-SPOOL → N-EXPORT | 每日 spool 行数；`eval_ci_check` exit | 命令 + exit 语义（**无** secret） |
| **O-S5** | N-CTX（可选） | `ibridge_v0` / monitoring L0 键存在性 | **仅** observability；**NBT** 不可作 release 依据 |

**连续窗口**：≥7 日每日 O-S4；O-S3 无 `unacceptable` 回归（邻接 playbook §6）。

---

## 3. Phase 2 — Internal canary 观察点

| 观察点 | 节点 | 记录什么 | 案卷字段建议 |
|--------|------|----------|--------------|
| **O-C1** | cohort 路由 | internal allowlist 逻辑名；比例 5–10% | `canary_env.md` + **ART-REL-DEC** `target_audience_or_env` |
| **O-C2** | N-MERGE | cohort 内 `primary_source=k2` 次数 | `execution_evidence.canary_requests` |
| **O-C3** | N-ANS vs N-MERGE | 答案差异抽样；P0 反馈 | **ART-REL-EXEC** + 产品签字索引 |
| **O-C4** | N-EXPORT | canary 窗 `eval_ci_check` vs shadow 基线 | 不退步证明（命令索引） |
| **O-C5** | 回退演练 | 触发 ask-only 或降比例 | **ART-REL-DEC** `rollback_strategy_draft` 实测勾 |

---

## 4. 节点 × Phase 矩阵

| 节点 | P1 Shadow | P2 Canary |
|------|-----------|-----------|
| N-ENTRY | 必观测 | 必观测 |
| N-ANS | **用户可见主权** | cohort 外主权 |
| N-K2 | 异步必跑 | cohort 内可主答案 |
| N-MERGE | 仅 internal | cohort 影响 user |
| N-SPOOL | 必写 | 继续写（对比基线） |
| N-EXPORT | 每日 | 每日 + 窗末汇总 |

---

## 5. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W3-A-ORCH 初版 |
