# Routing / Eval Guide v1

> **Ticket**: W2-T2 · Routing / Eval 测试与说明（Wave 2）  
> **Machine SSOT**: `routing/routing_eval_cases_v1.yaml`  
> **Catalog SSOT**: `routing/intake_routing_catalog_v1.yaml` · `docs/intake-routing-catalog-v1.md`  
> **Date**: 2026-06-10  
> **Status**: test skeleton / human checklist — **not** a routing engine

---

## 1. 目的

### 1.1 这份文档是什么

本档回答：**怎么检查「路由有没有走对」**，而不是「怎么实现路由」。

| 层 | 职责 | 本票是否实现 |
|----|------|--------------|
| **Routing engine** | 运行时决定走哪条 CLI / tool（如 `ask_rag_selector`、Tabular selector、HQ `_route_task`） | **否** — 不改现有 router / Agent |
| **Intake routing catalog**（W2-T1） | 规则索引：`task_type` → family + `tool_id` + entrypoint | 只读引用 |
| **Routing eval cases**（本票） | 可机器读的「期望行为」样例 + 人读检查清单 | **是** — 本票交付 |
| **Eval runner / LLM judge** | 自动比对 trace 与期望 | **否** — 仅描述未来挂钩点 |

新工程师读完应能：**写一个新的 routing 测试案例**，并知道该去哪里观察 Agent / CLI 是否真的按 catalog 建议执行。

### 1.2 假设读者与模型

- 日常执行环境：Composer 2.5 Fast 或同等 Cursor Agent。  
- Agent **不会**自动读本 YAML 做路由；人类或未来 runner 用 cases 做 **事后对照**。  
- 验收标准：cases 与 catalog **结构一致**（见 `tests/test_routing_eval_cases.py`）。

### 1.3 Out of scope（本票不做）

- 接入 GitHub Actions / CI pipeline  
- 完整 LLM-as-a-judge prompt  
- 修改 `skills/`、`core/*` router、Tabular Tool Layer 三件套  
- 合并四套 Catalog 命名空间（见 `intake-routing-catalog-v1.md` §4）

---

## 2. 测试单位：什么是「一个 routing 测试案例」

一个 **routing eval case** 描述：**给定某类任务，期望使用哪些 tool family / tool_id，以及去哪里验证**。

### 2.1 必填字段（YAML）

| 字段 | 含义 |
|------|------|
| `id` | 案例唯一 ID（snake_case） |
| `task_type` | 必须在 `intake_routing_catalog_v1.yaml` → `routes[].task_type` 中存在 |
| `input_summary` | 一句任务描述或 ticket 摘要（人读） |
| `expected_families` | 期望的 catalog family（通常 1 个，与 route 的 `preferred_tool_family` 对齐） |
| `expected_tool_ids` | 期望出现的 Gov / Tabular `tool_id`（须为 catalog 该 route 的 `tool_ids` 子集或等价编排） |

### 2.2 常用可选字段

| 字段 | 含义 |
|------|------|
| `input_context` | 结构化上下文（`case_dir`、`trigger`、`policy_route_id` 等） |
| `acceptable_orchestration_tool_ids` | 允许用一键编排代替逐步 tool（如 `orchestrate.e2e`） |
| `optional_tool_ids` | 允许出现但不强制（如 CI 额外的 `obs.eval.ci_check`） |
| `expected_entrypoint` | 应对照的脚本 / 模块路径 |
| `observation_points` | 人读检查清单：看哪条 CLI、哪份 spec、哪目录产物 |
| `eval_profile` | 未来 eval gate profile id（与 catalog 占位对齐） |

### 2.3 通过 / 失败的语义（人工或未来自动化）

**人工对照（v1 默认）**

1. 确认任务可映射到某个 `task_type`。  
2. 查 catalog route → 记下 `preferred_tool_family` 与 `tool_ids`。  
3. 执行或回放 Agent 会话 / CLI 日志。  
4. 检查是否调用了 **expected_entrypoint** 或等价 CLI，且 **未** 混用错误 family（例：Tabular 任务不应触发 `obs.eval.export`）。

**未来自动化（本票不实现）**

- 解析 Langfuse / gov-trace JSONL → 提取 `tool_id` 或 CLI 名 → 与 case YAML diff。  
- LLM judge 只评「是否遵循 catalog 叙事」，不替代结构测试。

---

## 3. 范例：关键 task_type 怎么写 case

以下 3 个范例与 `routing/routing_eval_cases_v1.yaml` 同步；展示 **input → expected → 观察点** 写法。

### 3.1 Tabular MVP · `tabular.cleaning.mvp`（demo_phase）

| 项 | 内容 |
|----|------|
| **Input** | 「对 `cases/demo_phase` 跑 7 行 Phase CSV 清洗 E2E」 |
| **Expected family** | `tabular_mvp` |
| **Expected tool_ids** | `validate.eligibility` → `clean.phase_demo` → `export.delivery_bundle`（或一步 `orchestrate.e2e`） |
| **Entrypoint** | `scripts/run_case_e2e_validation.py` |
| **观察点** | 是否执行 E2E CLI；`cases/demo_phase/reports/eligibility_result.json` 等是否更新；对照 `docs/mvp-standard-trace-path.md` §3.1 |
| **反例** | 任务却是 Tabular 清洗，却去跑 `observability/eval_exporter.py` |

### 3.2 Tabular MVP · `tabular.cleaning.mvp`（sampleco）

| 项 | 内容 |
|----|------|
| **Input** | 「近真实客户案 `cases/sampleco/2026-0001` 完整 gate → clean → bundle」 |
| **Expected** | 同上 family / tool_ids；`case_dir` 不同 |
| **观察点** | `docs/mvp-standard-trace-path.md` §3.2；产物在 `cases/sampleco/2026-0001/reports/` |

### 3.3 Gov / Eval · `gov.observability.eval`

| 项 | 内容 |
|----|------|
| **Input** | 「检查 ask pipeline 的 Langfuse ingest 与 eval gate 是否对齐」 |
| **Expected family** | `gov_registry` |
| **Expected tool_ids** | `obs.eval.export` · `obs.eval.report` · `obs.wf.status_summary` |
| **Policy** | `config/routing_policy.yaml` → `route_id: wave_b.eval_report` |
| **观察点** | Gov cards 在 `skills/gov_cards/`；CI 子集见 `docs/testing.md` §5；可选 `obs.eval.ci_check` |
| **反例** | 把 `clean.phase_demo` 写进 eval 任务；或使用 composite `obs.eval.triage` 作 prod 单步 |

### 3.4 附加范例 · `tabular.cleaning.regression`

| 项 | 内容 |
|----|------|
| **Input** | 「Reviewer 跑 MVP 主链回归（demo_phase + sampleco）」 |
| **Expected** | `orchestrate.mainline_regression`（链到 `orchestrate.e2e`） |
| **Entrypoint** | `scripts/run_mvp_mainline_regression.py` |
| **观察点** | `docs/mvp-mainline-regression.md` |

---

## 4. 与外部 eval 工具的关系（未来挂钩，本票不实现）

| 工具 / 机制 | 现状 | 未来如何消费 routing eval cases |
|-------------|------|----------------------------------|
| **Langfuse** | ask / workflow trace；MVP Tabular CLI **未** 预定义 span 名（见 `mvp-standard-trace-path.md` §2.2） | Runner 从 span metadata 提取 CLI 或 `tool_id` → 映射到 case `expected_tool_ids` |
| **gov-trace-v2 JSONL** | Wave B observability | `obs.eval.correlate` 类任务可对照 trace case |
| **`obs.eval.*` CI gate** | `eval-gate-ci.yml` + `tests.test_eval_gate` | case `gov_obs_eval_gate` 的 `eval_profile: eval_gate_v1` 占位 |
| **Langfuse / 自动化 eval SaaS** | 无本 repo 内 LLM judge | T3+ 票：prompt 评「是否读了正确 spec / 是否混 family」；**结构一致性仍靠 YAML unittest** |
| **Intake catalog loader** | `core/routing_policy_loader` 未读 intake catalog | 专票可增 `resolve-intake-route --task-type`；cases 作 golden file |

**原则**：外部 eval 评 **行为与质量**；routing eval cases 评 **是否走对 catalog 轨道**。二者互补，不互相替代。

---

## 5. 建议运行时机

| 时机 | 建议动作 |
|------|----------|
| 新增 / 修改 **skill** 或 **gov tool card** | 更新 catalog（若 task_type 变）→ 增改 case → 跑 `tests.test_routing_eval_cases` |
| 新增 **Tabular tool_id** | 同步 `tools/tabular_tool_catalog_v1.json` + intake catalog + 相关 case |
| 修改 **routing policy**（`config/routing_policy.yaml`） | 对照 `gov.observability.eval` / `kb.index.bootstrap` cases 的 `policy_route_id` |
| 改 **Agent 接战指令** 或 Multi-Chat 角色边界 | 人工 spot-check：Tabular 票是否仍指向 `mvp-standard-trace-path` |
| PR 合并前（本地） | `python -m unittest tests.test_routing_eval_cases tests.test_intake_routing_catalog -v` |
| **不**建议 | 本票 cases **未** 接入 CI；勿在未另开票时改 GitHub Actions |

---

## 6. 如何新增一个 case（步骤清单）

1. 在 `intake-routing-catalog-v1.md` §3 找到或新增 `task_type`。  
2. 确认 `routing/intake_routing_catalog_v1.yaml` 已有对应 `routes[]` 条目。  
3. 在 `routing/routing_eval_cases_v1.yaml` 追加 `cases[]` 项（`id` 唯一）。  
4. `expected_tool_ids` 必须是该 route 的 `tool_ids`（及文档允许的 `orchestration_tool_id` / `optional_tool_ids`）的子集。  
5. 写 2–4 条 `observation_points`（CLI、spec 路径、产物目录）。  
6. 跑结构测试：

```bash
python -m unittest tests.test_routing_eval_cases -v
```

---

## 7. 验证与相关文档

```bash
# W2-T2：cases ↔ catalog 一致性
python -m unittest tests.test_routing_eval_cases -v

# W2-T1：catalog 自身结构
python -m unittest tests.test_intake_routing_catalog -v
```

| 文档 / 文件 | 用途 |
|-------------|------|
| `routing/routing_eval_cases_v1.yaml` | 机器可读 cases |
| `routing/intake_routing_catalog_v1.yaml` | task_type 权威 |
| `docs/intake-routing-catalog-v1.md` | Catalog 人读 spec |
| `docs/SKILL_CATALOG_OVERVIEW.md` | Gov `tool_id` 索引 |
| `docs/mvp-standard-trace-path.md` | Tabular 标准 trace |
| `docs/mvp-mainline-regression.md` | 主链回归 |
| `04_Workflows/tickets/W2-T2_state.md` | 本票 FRAME / AC |

---

## 附录 A：routing engine vs eval case（一图读懂）

```text
  用户 / Ticket                    Agent / CLI 实际执行
       │                                    │
       ▼                                    ▼
  task_type 归类              ←──对照──   日志 / 产物 / trace
       │                                    │
       ▼                                    │
 intake_routing_catalog_v1.yaml             │
 (规则：应该走哪条 family)                   │
       │                                    │
       ▼                                    ▼
 routing_eval_cases_v1.yaml  ──期望──►  人工或未来 runner：通过？
 (本票：测试样例 + 观察点)
```

**记住**：中间没有自动 router 读本 YAML；本票只提供 **标准答案卷**，供人对照或后续自动化。
