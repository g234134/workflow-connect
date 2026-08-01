# K-2 合流策略（dev/test · merge adapter）

> **战役**：K-2 合流治理 · Chat B（合流策略 + adapter）  
> **实现**：`core/k2_merge_adapter.py` → `merge_ask_and_k2`  
> **入口/出口 hook**：`core/k2_ask_shadow.py`（`ASK_MERGE_INTERFACE` exit）  
> **行为基线**：`docs/k2_behavior_profile.md`（Chat A）  
> **范围**：shadow / dev/test only；**未**改动 `/api/ask` 或生产路由。

---

## 1. 设计原则

### 1.1 单点切换

未来启用 K-2 部分流量时，仅在 **adapter 节点** 调用 `merge_ask_and_k2`（或治理批准的 K-2-only 变体），不在 ask 图内散落分支。

### 1.2 生产主权（Phase 0 · 当前）

| 维度 | 原则 |
|------|------|
| **回答内容** | **ask 为主**。双 ok 时用户可见 `answer` 取自 ask；K-2 答案仅写入 `k2_merge.k2_answer_preview` 供 shadow 对比。 |
| **严重 eval 回退** | K-2 `eval_gate.tags` 含 **`infra_risk`** 时：内容仍用 ask，但 **`ok=False`**，errors 追加 `k2_merge:severe_eval:infra_risk`（与 `eval_ci_check --fail-on-tags infra_risk` 对齐）。 |
| **非严重 eval** | `high_retry` / `retrieve_retry` / `context_heavy` 等：不改变 ask `ok`；`k2_merge.gate_result=needs_review`，并附带 `k2_eval_metadata`。 |
| **错误信号** | ask 失败路径优先暴露（保守）；K-2 单独 ok 不覆盖 ask 失败（`k2_recovered=True` 仅 metadata）。 |
| **infra 硬门禁** | K-2 `state.error_type ∈ {timeout, context_overflow}` 且 eval 打出 `infra_risk` → 合流 **fail** + **CI fail**，即便 ask 正常。 |

### 1.3 eval_metadata 透传

| 场景 | 是否写入 envelope `k2_eval_metadata` | 说明 |
|------|--------------------------------------|------|
| 双 ok | **是**（默认） | shadow 观测；P+ 批次可消费 |
| ask ok / K-2 fail | **否**（无 eval 时）或 **是**（K-2 部分产出 eval） | 失败侧 eval 仍保留若存在 |
| ask fail / K-2 ok | **是** | 标注 K-2 恢复信号 |
| 双 fail | **是** | 合流诊断 |
| `include_eval_in_envelope=False` | **否** | 仅内部日志；供未来生产 slim envelope |

`k2_merge` 块（含 `gate_result` / `ci_fail`）始终写入，标记 **dev_only**。

---

## 2. 场景决策表

| # | 场景 | ask | K-2 | 主答案来源 | `ok` | `k2_merge.gate_result` | CI fail | 备注 |
|---|------|-----|-----|------------|------|------------------------|---------|------|
| S1 | 双 ok · 无 eval 标签 | ok | ok | ask | True | pass | 否 | 默认 happy path |
| S2 | 双 ok · 非严重 eval | ok | ok | ask | True | needs_review | 否 | 如 `high_retry`, `retrieve_retry` |
| S3 | 双 ok · **infra_risk** | ok | ok | ask（回退） | **False** | **fail** | **是** | 内容 ask，整体 fail |
| S4 | ask ok · K-2 fail | ok | fail | ask | True | needs_review | 否 | K-2 失败不拖垮 ask |
| S5 | ask fail · K-2 ok | fail | ok | ask（保持失败） | False | needs_review | 否 | `k2_recovered=True`；待治理是否切换主源 |
| S6 | 双 fail | fail | fail | ask envelope | False | fail | 是 | errors 合并 K-2 error_type |
| S7 | 双 ok · 答案不一致 | ok | ok | ask | True | needs_review* | 否 | *有 eval 标签按 S2/S3；无标签 pass + preview 差异 |

### 2.1 与 Chat A 分类对齐

| Chat A 分类 | 合流处理 |
|-------------|----------|
| **expected**（answer_preview、eval_metadata、selector） | ask 主答案 + K-2 eval overlay |
| **uncertain**（handoff、retry、fallback） | `needs_review`；不自动改 ok |
| **unacceptable**（ok/status/error_type 硬回归） | S3/S5/S6 规则；`retrieve_timeout` 需 error_type 映射工单（未在本 adapter 自动修） |

---

## 3. 输出 schema

合流结果 **必须** 包含现行 ask 顶层键：`mode`, `query`, `top_k`, `ok`, `message`, `answer`, `errors`, `executed_nodes`（及 ask 原有 `retrieve` / `ibridge_v0` 等 pass-through 字段）。

附加字段（dev/test shadow）：

| 字段 | 说明 |
|------|------|
| `k2_eval_metadata` | K-2 P+ eval_gate 快照 |
| `k2_metrics_record` | retry / handoff / trace_completeness |
| `k2_merge` | 策略版本、primary_source、gate_result、decision、ci_fail、tags |

---

## 4. 启用门禁（治理 · 未决议）

以下条件为 **必要非充分**（见 `k2_behavior_profile.md` §6）：

1. Shadow 回归：`tests/test_k2_ask_shadow.py` + merge tests 全绿  
2. `merge_safe=True` 且 `classification.unacceptable=[]`（场景级）  
3. Selector 桥接工单（greeting skip-RAG）  
4. Answer adapter / LLM 对齐（stub vs RAG）  
5. 尚書省批准 partial traffic 与 `ASK_MERGE_INTERFACE.entry.context_mode` 切换  

**Rollout 审批、Phase 门控与回退**：见 `docs/k2_deployment_governance.md`（Chat C）。

---

## 5. 验证

```bash
python -m unittest tests.test_k2_merge_adapter tests.test_k2_ask_shadow -v
```

---

## 6. 相关文档

- `docs/k2_behavior_profile.md` — Chat A 行为画像  
- `docs/k2_ask_shadow_findings.md` — 早期 findings  
- `core/k2_merge_adapter.py` — 实现  
- `docs/k2_deployment_governance.md` — Chat C rollout 审批、Phase、指标与回退  
- `docs/phase3-5-cost-model-governance-contract-v1.md` — Phase 3.5 gate 分类 SSOT（shadow export · severe eval 与 nightly `infra_risk` 对齐；**不含** prod canary 授权）
