# K-2 行为画像与 shadow 回归基线

> **战役**：K-2 合流治理 · Chat A（行为画像）  
> **范围**：dev/test shadow only；**未**改动 `/api/ask` 或 `run_k2_flow` 主逻辑。  
> **Runner**：`core/k2_ask_shadow.py` · **Tests**：`tests/test_k2_ask_shadow.py`

---

## 1. Shadow 场景 → 测试映射

| 场景 | 测试名 | 查询 / 条件 | 目的 |
|------|--------|-------------|------|
| 简单 happy path（RAG 知识型） | `test_shadow_simple_happy` | `explain ask_pipeline retrieve flow` | 双管线均成功；selector 走 RAG |
| 问候 / selector skip | `test_shadow_greeting_selector_skip` | `你好` | ask 跳过 retrieve；K-2 仍 prefetch |
| 明显 RAG + KB context | `test_shadow_rag_with_kb_context` | `document_chunks pipeline 如何運作？` + mock H-line KB | ASK-R4；retrieve + answer |
| 检索 timeout / fallback | `test_shadow_retrieve_timeout_fallback` | 知识型 query + `ibridge_v0=True` + mock retrieve fail | ask 直答 fallback；K-2 skill retry |
| I-bridge v0 对齐 | `test_shadow_ibridge_v0_hline_alignment` | 知识型 query + `ibridge_v0=True` | H 线 / I 线字段可比 |
| K-2 skill retry | `test_shadow_k2_skill_retry_still_succeeds` | 任意 query + `simulate_skill_failure=True` | J 线 retry + eval_metadata |
| 摘要 / profile helper | `test_shadow_summaries_printable` | 探针 query | `compare_shadow_profiles` 可打印 |
| Profile 分层单元 | `test_compare_shadow_profiles_layers` | 合成 summary | 分层 diff 分类 |

---

## 2. `compare_shadow_profiles` 字段与输出

### 2.1 对比字段（四层）

| 层 | 字段 | 说明 |
|----|------|------|
| **功能** | `ok`, `status`, `answer_preview` | 成败与答案粗粒度；另算 `answer_similarity` ∈ [0,1] |
| **编排** | `handoff_count`, `executed_node_count`, `retry_count` | M 线 record vs ask `executed_nodes` |
| **策略** | `selector_use_rag`, `selector_rule_id`, `retrieve_fallback` | ask selector；K-2 无 selector（`K2-N/A`） |
| **观测** | `has_eval_metadata`, `error_type`, `tags`, `context_entry_mode` | eval_gate / ibridge vs K-2 P+ |

完整字段列表见 `SHADOW_COMPARE_FIELDS`；分层见 `SHADOW_PROFILE_LAYERS`（`core/k2_ask_shadow.py`）。

### 2.2 输出结构（摘要）

```python
{
    "ok": bool,                    # 全字段字面相等
    "case_name": str,
    "answer_similarity": float,    # SequenceMatcher 粗粒度
    "functional_ok": bool,           # ok 对齐 或 (双 ok + similarity ≥ 阈值)
    "merge_safe": bool,              # 无 unacceptable + ok 一致
    "layers": {
        "<layer>": {"match": bool, "mismatched": {...}, "fields": [...]}
    },
    "classification": {
        "expected": [...],           # 预期差异（如 eval_metadata、answer 来源）
        "uncertain": [...],          # 需治理（handoff/retry/fallback）
        "unacceptable": [...],       # 硬门禁（ok/status/error_type 回归）
    },
    "matched_fields", "mismatched", "ask_summary", "k2_summary", "report"
}
```

### 2.3 差异分类常量

| 集合 | 字段 | 治理含义 |
|------|------|----------|
| `INVARIANT_DIFF_FIELDS` | `ok`, `status`, `error_type` | **必须**与 ask 一致才可 merge |
| `EXPECTED_DIFF_FIELDS` | `answer_preview`, `context_entry_mode`, `has_eval_metadata`, selector 等 | 已知架构差；merge hook 适配 |
| `UNCERTAIN_DIFF_FIELDS` | `handoff_count`, `retry_count`, `retrieve_fallback` | Chat B 定阈值 / 策略 |

---

## 3. 分场景行为摘要

### 3.1 `simple_happy` — 知识型 RAG

| | ask 主线 | K-2 |
|---|----------|-----|
| **ok** | True | True |
| **selector** | `use_rag=True`, ASK-R5 | 无 selector（始终 prefetch retrieve skill） |
| **answer** | `rag:{query}`（RAG mock） | `agent succeeded`（stub agent） |
| **nodes / handoff** | 4 nodes（health→selector→retrieve→answer） | agent graph；`executed_node_count=0` |
| **eval** | 无 | `has_eval_metadata=True`, tags 含 `infra_risk` |
| **context** | H-line（无 ibridge 时 entry_mode 未暴露） | `k2_pipeline` |

**主要差异**：答案来源不同（预期）；K-2 多 eval_gate（预期）。`answer_similarity≈0.34`。`merge_safe=True`。

### 3.2 `greeting_skip` — 无 RAG

| | ask 主线 | K-2 |
|---|----------|-----|
| **selector** | ASK-R2, skip retrieve | 仍跑 `executor_prefetch` retrieve skill |
| **nodes** | selector + answer（无 retrieve_node） | planner→prefetch→executor→reviewer |
| **answer** | `direct:你好` | `agent succeeded` |

**主要差异**：**策略层结构性差异** — ask 可 skip RAG，K-2 当前无等价 selector。属 **不确定 / 需治理**：是否在 merge 前为 K-2 引入 ask selector 或 adapter 层。

### 3.3 `rag_kb_context` — KB + 知识问题

| | ask 主线 | K-2 |
|---|----------|-----|
| **selector** | ASK-R4（KB context） | 无 |
| **retrieve** | retrieve_node 执行 | prefetch skill mock hits |
| **ok** | True | True |

**主要差异**：与 simple_happy 类似；验证 KB 信号下 ask 走 RAG 而 K-2 行为不变（始终 prefetch）。

### 3.4 `retrieve_timeout` — 检索失败

| | ask 主线 | K-2 |
|---|----------|-----|
| **retrieve** | fail `error_type=timeout` | skill retry（`retry_count≥1`） |
| **fallback** | direct answer + `retrieve_fallback=True` | 仍 `ok=True`（agent 成功） |
| **error_type** | 经 answer/ibridge 暴露 timeout | K-2 summary 常为 `None` |

**主要差异**：ask 明确标记 fallback + timeout；K-2 通过 retry 消化失败仍成功。**不可接受初判**：`error_type` 未对齐（ask 有 timeout tag，K-2 无）— merge 时需映射 skill failure → ask `retrieve_error_type`。

### 3.5 `ibridge_v0` — I 线对齐

| | ask 主线 | K-2 |
|---|----------|-----|
| **ibridge_v0** | `context_payload_ok`, `selector_decision`, `ibridge_record` | N/A |
| **context_entry_mode** | `ask_pipeline` | `k2_pipeline` |
| **handoff / retry** | ibridge_record 计数 | M-line record（常更高） |

**主要差异**：I-bridge 仅 ask 侧；K-2 用独立 trace。H 线 mode 不同为预期；ibridge 字段需在 merge envelope 中补齐或标注。

### 3.6 `k2_skill_retry` — J 线 retry

| | ask 主线 | K-2 |
|---|----------|-----|
| **retry** | ask 路径 retry=0 | skill `retry_count≥1`, record 可能 +1 |
| **eval** | 无 | `eval_gate` tags: `high_retry`, `infra_risk`, `retrieve_retry` |
| **ok** | True | True |

**主要差异**：K-2 更细粒度暴露 retry 与 eval 标签（**可引入的新能力**）；ask 同 query 无 retry 信号。

---

## 4. 不可变 vs 可变边界

### 4.1 必须保持与 ask 一致（硬门禁）

- 顶层 **`ok`** / HTTP 语义等价 **status**
- 失败路径 **`error_type`** 不可被吞（`retrieve_timeout` 已暴露 gap）
- 用户可见 **失败 message** 不应静默降级为 success（当前 mock 下均 ok=True，需 live 回归再验）

### 4.2 允许差异但需治理

- **`handoff_count` / `retry_count`**：K-2 agent 图 vs ask 扁平节点
- **`retrieve_fallback`**：ask selector+direct answer vs K-2 reviewer_fallback
- **`answer_preview`**：不同 producer；用 `answer_similarity` 阈值而非字节相等
- **selector 决策**：K-2 无 ASK-R* 规则；merge 前需 adapter 或共享 selector

### 4.3 可由 K-2 引入的新能力

- **`eval_metadata` / `eval_gate`**（pass, tags, handoff_edges）
- **M-line `trace_completeness`** 与 skill 级 retry 明细
- **`k2_metrics_record`** overlay（见 merge hook draft）

---

## 5. K-2 vs ask — 初判要点

### K-2 相对 ask 的优点

1. **P+ eval_gate**：每次 run 产出 `eval_metadata`（pass/tags），便于合流前质检。
2. **显式 handoff 边**：`handoff_edges` 记录 planner→executor→reviewer，编排可审计。
3. **J 线 skill retry**：retrieve timeout 可配置 retry，失败模式更可观测（`retrieve_retry` tag）。
4. **统一 agent trace**：`agent_run_trace("langgraph_k2")` 包裹全图，M 线 record 更完整。
5. **Reviewer fallback 路径**：executor 失败时仍可 degraded 完成（ask 靠 direct answer fallback）。

### 最需要担心的差异

1. **无 ask RAG selector**：问候语等 skip-RAG 场景 K-2 仍 prefetch，策略不对齐。
2. **答案来源不同**：stub agent vs RAG/direct answer — merge 前必须定 adapter 或 LLM 对齐。
3. **`error_type` / fallback 语义**：timeout 场景 ask 标记 fallback，K-2 可能 retry 后 ok=True 且无 error_type。
4. **`executed_node_count` 不可比**：观测/dashboard 需双轨指标或归一化映射。
5. **context mode**：`k2_pipeline` vs `ask_pipeline` — Governance 尚未签 `ASK_MERGE_INTERFACE.entry.context_mode` 切换。

---

## 6. Chat B 合流策略输入（建议）

1. **Shadow 门禁**：`merge_safe=True` 且 `classification.unacceptable=[]` 为必要非充分条件；`retrieve_timeout` 类场景需先修 error_type 映射。
2. **Selector 桥接**：在 K-2 `prepare_context` 后插入 ask selector 或 task_input `selector_hints` 透传，消除 greeting 误 retrieve。
3. **Answer adapter**：`k2_result_to_ask_response_envelope` 应优先取 RAG/direct 结果而非 agent stub summary（待 LLM 对齐工单）。
4. **阈值**：建议 `answer_similarity ≥ 0.25` 为 mock 基线；live 回归另定。
5. **Gradual merge**：先 overlay `k2_eval_metadata` on ask response（`ask_response_envelope`），再切换 orchestration owner。

---

## 7. 验证命令

```bash
python -m unittest tests.test_k2_ask_shadow -v
```

关键结果：全部 tests OK；每场景打印 `=== shadow: <case> ===` 报告含 `answer_similarity` / `merge_safe` / 三层 classification。

---

## 8. 相关文档

- 上一轮 findings：`docs/k2_ask_shadow_findings.md`
- Merge 接口草稿：`ASK_MERGE_INTERFACE` in `core/langgraph_flow_k2.py`
- Ask selector 规约：`skills/skills_contract.md` §10
