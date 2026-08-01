# Routing Eval Runner v1

> **Ticket**: W4-T2 · Routing Eval Runner（consume `routing_eval_cases`）  
> **Runner**: `scripts/run_routing_eval.py`  
> **Cases SSOT**: `routing/routing_eval_cases_v1.yaml`  
> **Date**: 2026-06-10  
> **Status**: local manual runner — **not** a routing engine; **not** wired to CI

---

## 1. 目的

本 runner 把 **W2-T2 routing eval cases** 自动化对照到现有只读 SSOT：

| 输入 | 对照目标 |
|------|----------|
| `routing_eval_cases_v1.yaml` 每个 case | `intake_routing_catalog_v1.yaml` route |
| Tabular family case | W4-T1 `plan_tabular_route` + `tabular_tool_catalog_v1.json` |
| Gov family case | `config/routing_policy.yaml`（经 `core.routing_policy_loader` 只读 resolve） |

**不是** routing engine：不调用 Selector / Executor / HQ `_route_task`、不改任何 router 或 policy。

v1 重点：**plan / 对照** — 确认 `expected_families`、`expected_tool_ids`、`expected_entrypoint` 与 catalog / glue / policy 一致。不做 LLM 判分、不读 Langfuse。

---

## 2. 输入与输出

### 2.1 输入：eval cases YAML

消费 `routing/routing_eval_cases_v1.yaml`（schema `routing_eval_cases_v1`）。runner 读取字段：

| 字段 | 用途 |
|------|------|
| `id` | case 唯一 ID；`--case-id` 过滤 |
| `task_type` | 在 intake catalog `routes[]` 查找 route |
| `expected_families` | 与 route `preferred_tool_family` 对齐检查 |
| `expected_tool_ids` | 必须被 planned / policy 步骤 **覆盖**（planned ⊇ expected） |
| `expected_entrypoint` | 与 catalog route `entrypoint` 精确比对 |
| `input_context.case_dir` | Tabular glue `plan_tabular_route` 输入 |
| `input_context.policy_route_id` | Gov policy `resolve_route_tool_ids` 输入 |
| `acceptable_orchestration_tool_ids` | 允许编排 tool 代替逐步 tool（如 `orchestrate.e2e`） |
| `optional_tool_ids` | Gov case 可选 tool，缺失不判 fail |

`case_dir` 缺省时，runner 使用内置 mapping（如 `tabular_mainline_regression` → `cases/demo_phase`）。

### 2.2 CLI

```bash
# 默认：--dry-run（plan/对照），JSON 输出
python scripts/run_routing_eval.py

python scripts/run_routing_eval.py --dry-run --format table

python scripts/run_routing_eval.py --case-id tabular_demo_phase_clean --format json

# 可选 smoke（仅 allowlist case）
python scripts/run_routing_eval.py --execute --case-id tabular_mainline_regression
```

| 旗标 | 默认 | 说明 |
|------|------|------|
| `--dry-run` / `--no-dry-run` | `--dry-run` | 只做对照，不 subprocess |
| `--execute` | off | 对 allowlist case 跑 `run_mvp_mainline_regression.py -v` |
| `--case-id` | all | 单 case 过滤 |
| `--format` | `json` | `json` 或 `table` |
| `--cases-path` | cases YAML | 覆盖路径（测试用） |
| `--catalog-path` | catalog YAML | 覆盖路径（测试用） |

`--execute` 隐含对该 case 关闭 dry-run 的 subprocess 部分；其余 case 仍只读对照。

### 2.3 输出 JSON 结构

顶层：

```json
{
  "ok": true,
  "message": "4/4 case(s) aligned",
  "schema_version": "routing_eval_cases_v1",
  "catalog_ref": "routing/intake_routing_catalog_v1.yaml",
  "dry_run": true,
  "execute": false,
  "cases_run": 4,
  "cases_ok": 4,
  "results": [ /* per-case */ ]
}
```

每个 case（`results[]`）：

| 字段 | 说明 |
|------|------|
| `id` | case id |
| `ok` | 本 case 是否通过 |
| `task_type` | 来自 case |
| `family` | catalog `preferred_tool_family` |
| `expected_tool_ids` | 来自 case |
| `planned_tools` | glue plan 或 policy resolve 的 tool 列表 |
| `mismatched_tools` | expected 中未被 planned 覆盖的 id |
| `expected_entrypoint` / `catalog_entrypoint` / `entrypoint_match` | entrypoint 对照 |
| `notes` | 审计说明（profile、policy、execute smoke 等） |
| `message` | 人类可读摘要 |
| `execute` | 仅 `--execute` 时存在 smoke 结果 |

---

## 3. Case 类型

### 3.1 Tabular family（`tabular_mvp`）

适用 `task_type`：`tabular.cleaning.mvp`、`tabular.cleaning.regression` 等 catalog family 为 `tabular_mvp` 的 route。

检查步骤：

1. `task_type` 存在于 intake catalog。  
2. `plan_tabular_route(task_type, case_dir)`（W4-T1 glue）成功。  
3. `planned_tools` ⊇ `expected_tool_ids`。  
4. 每个 `planned_tools` 存在于 `tabular_tool_catalog_v1.json` 且 `enabled: true`。  
5. `expected_entrypoint` 与 catalog `entrypoint` 一致。  
6. 若逐步 tool 未覆盖但 `acceptable_orchestration_tool_ids` 含 glue 的 `orchestration_tool_id`，记 note 且可不判 fail（v1 仍以逐步覆盖为主）。

### 3.2 Gov family（`gov_registry`）

适用 `task_type`：`gov.observability.eval` 等。

检查步骤：

1. 从 case / catalog 取得 `policy_route_id`（如 `wave_b.eval_report`）。  
2. 只读 `load_routing_policy` + `resolve_route_tool_ids`。  
3. policy `tool_ids` ⊇ case `expected_tool_ids`（`optional_tool_ids` 缺失不计 fail）。  
4. **不**执行任何 Gov tool / eval exporter。

### 3.3 其他 family

v1 回退为 catalog route `tool_ids` 与 `expected_tool_ids` 子集检查；当前 cases 文件未使用此路径。

---

## 4. 与其他 Wave 的关系

```text
W1  trace / regression docs
         │
W2-T1  intake_routing_catalog_v1.yaml ──┐
W2-T2  routing_eval_cases_v1.yaml ──────┼──► run_routing_eval.py (本 runner)
         │                               │
W3-TL  tabular_tool_catalog_v1.json ◄───┤ (Tabular tool_id 校验)
         │                               │
W4-T1  plan_tabular_route (glue) ◄──────┘
         │
B-F3   routing_policy_loader (Gov 只读 resolve)
```

| Wave | 本 runner 如何消费 |
|------|-------------------|
| W1 | cases 引用 `mvp-standard-trace-path` / `mvp-mainline-regression` entrypoint |
| W2-T1 | route 查找、`tool_ids` / `entrypoint` SSOT |
| W2-T2 | cases YAML 为输入全集 |
| W3-TL | Tabular catalog 校验 `planned_tools` |
| W4-T1 | Tabular plan 来源 |
| B-F3 | Gov policy resolve（**只读**，不改 `config/routing_policy.yaml`） |

---

## 5. 限制与未来工作

| 限制（v1） | 未来票 |
|------------|--------|
| 不做 LLM-as-judge | T3+ eval gate 挂钩 |
| 不读 Langfuse / gov-trace JSONL | runner 解析 trace metadata |
| 不接 GitHub Actions | 专票接 CI + `eval_profile` |
| `--execute` 仅 `tabular_mainline_regression` | 扩展 E2E smoke allowlist |
| 不改 `routing_eval_cases_v1.yaml` 结构 | 若增字段须向后兼容并更新本文 §2 |

**向后兼容**：若未来 cases YAML 增字段，runner 应忽略未知键；必填键行为与 `tests/test_routing_eval_cases.py` 一致。

---

## 6. 验证

```bash
# W4-T2 runner 单测
python -m unittest tests.test_routing_eval_runner -v

# W2 cases ↔ catalog 结构（既有，勿改）
python -m unittest tests.test_routing_eval_cases -v

# 本地 dry-run 全案
python scripts/run_routing_eval.py --dry-run --format table

# 主链守护（确认未动禁改 runner）
python scripts/run_mvp_mainline_regression.py -v
```

| 文档 | 用途 |
|------|------|
| `docs/routing-eval-guide-v1.md` | cases 人读说明 |
| `docs/routing-tool-layer-glue-v1.md` | glue plan 语义 |
| `04_Workflows/tickets/W4-T2-routing-eval-runner_state.md` | 本票 AC / 战报 |
