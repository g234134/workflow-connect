# Tool Executor and Sandbox Safety Contract v1

> **票號**：WB-T2 · `tool-executor-and-sandbox-safety-contract-v1`  
> **Phase**：8.8（Tool Executor · Sandbox 安全邊界）  
> **性质**：执行模式与 sandbox 边界 **SSOT**；**不**改 executor 实现、**不**扩大 allowlist。  
> **上位**：`tools/tabular_tool_catalog_v1.json`（WB-T1 / W3-TL-T1 `tool_id` 权威）· `docs/tabular-tool-selector-spec.md`（WB-T1 / W3-TL-T2）  
> **完成度锚点**：Phase 8.8 **58% → 82%**（本票 codify 后）

---

## §1 范围与分轨

### 1.1 本合同覆盖什么

| 在范围内 | 不在范围内 |
|----------|------------|
| 战车根 Tabular MVP `execute_tabular_tool` 四级 `execution_mode` 语义 | 修改 `tools/tabular_tool_executor.py` 执行逻辑 |
| Agent experiment orchestrator（`run_agent_standard_case_experiment.py`）与 sandbox e2e 的 **模式对照表** | 修改 `scripts/run_agent_standard_case_experiment.py` allowlist 行为 |
| Tabular outbox 写入条件（`outbox/<case_ref>/<run_id>.json`） | 暗部 `core/tool_executor.py`（Phase 8.8 编排轨） |
| Sandbox 安全边界（subprocess、cwd、`..` 逃逸） | Langfuse / DLQ / `orchestration_bridge_outbox` 写入 |
| PR CI 路径上 `execute` 仍为 optional / shadow（对齐 WA-T3 P3.5） | replay / re-execute from outbox · K8s / Celery job runner |

### 1.2 双轨声明（禁止混用）

| 轨道 | 模块 | 用途 |
|------|------|------|
| **战车根 Tabular MVP** | `tools/tabular_tool_executor.py` → `execute_tabular_tool` | W3-TL-T3；消费 `tabular_tool_catalog_v1.json`；写 Tabular outbox |
| **暗部 Phase 8.8 编排** | `core/tool_executor.py`（`gov_core_system`） | ask / orchestration Tool Layer；**禁止**从战车根测试或 CLI import |

**FORBID**：在 Tabular intake / agent experiment 路径 `import core.tool_executor` 或引用 `orchestration_bridge_outbox`。

`tool_id` 命名空间权威：**仅** `tools/tabular_tool_catalog_v1.json`（见 `docs/tabular-tool-catalog-v1.md`）；Selector 消费同一 JSON（`docs/tabular-tool-selector-spec.md`）。

### 1.3 权威位阶

```
尚書省批文 ＞ HARNESS_CONSTITUTION.md ＞ 本 contract ＞ tabular-tool-outbox-spec.md 操作细节 ＞ brief/notes
```

---

## §2 四级 `execution_mode` 与 case allowlist

### 2.1 模式枚举（冻结）

| `execution_mode` | 含义 | 典型入口 | subprocess | Tabular outbox 落盘 |
|------------------|------|----------|------------|---------------------|
| `dry_run` | Executor 层计划：构建 argv + 预期 artifacts，**不** spawn | `execute_tabular_tool(..., dry_run=True)` | 否 | 否 |
| `plan_only` | 路由链计划：glue → Selector → executor plan dict，**不**调 executor subprocess | `run_tabular_intake_tool_path.py`（默认） | 否 | 否 |
| `execute` | 真跑 catalog 工具 CLI；写 case artifacts + outbox | `execute_tabular_tool(..., dry_run=False)` · agent `mode=run`（非 sandbox flag） | 是 | 是 |
| `sandbox_end_to_end` | 实验线真跑到 bundle + **仅** sandbox 交付目录；无 production notify | `run_agent_standard_case_experiment.py --sandbox-end-to-end` | 是 | 是（+ `outbox/sandbox_delivery/`） |

**决策表（防混淆）**

| 调用方意图 | 应选模式 | 误用后果 |
|------------|----------|----------|
| PR / release checklist 预演 | `plan_only` 或 `dry_run` | 误开 `execute` → 污染 case / outbox |
| 本地单步验收某 `tool_id` | `execute`（allowlisted case） | 对 experimental fixture 误 `execute` without sandbox → 可能写 production case tree |
| W12-T1 受控 sandbox 交付实验 | `sandbox_end_to_end`（**仅** `additional_demo`） | 对 `demo_phase` 开 flag → `sandbox_end_to_end_not_allowed` |

### 2.2 Case allowlist 矩阵

实验 orchestrator 权威常数：`scripts/run_agent_standard_case_experiment.py` → `_ALLOWLIST_CASE_REFS`  
Sandbox e2e 权威常数：`delivery/sandbox_delivery_bundle_v1.py` → `SANDBOX_E2E_ALLOWLIST`

| `case_ref` | experiment allowlist | `dry_run` / `plan_only` | `execute`（agent run） | `sandbox_end_to_end` | `fixture_maturity` |
|------------|---------------------|-------------------------|------------------------|----------------------|-------------------|
| `demo_phase` | ✅ | ✅ | ✅（stable 主链锚点） | ❌ blocked | `stable` |
| `sampleco/2026-0001` | ✅ | ✅ | ✅（stable 主链锚点） | ❌ blocked | `stable` |
| `additional_demo` | ✅ | ✅ | ✅（controlled experimental） | ✅ **唯一** sandbox e2e | `controlled_experimental` |
| `sandbox_client` | ✅ | ✅ | ✅（preview 线） | ❌ blocked | `controlled_experimental` |

| 模式 | `demo_phase` | `sampleco/2026-0001` | `additional_demo` | `sandbox_client` |
|------|--------------|----------------------|-------------------|------------------|
| `dry_run` | ✅ | ✅ | ✅ | ✅ |
| `plan_only` | ✅ | ✅ | ✅ | ✅ |
| `execute` | ✅ | ✅ | ✅ | ✅ |
| `sandbox_end_to_end` | ❌ | ❌ | ✅ | ❌ |

非 allowlist `case_ref`：orchestrator 返回 `final_status=blocked`，`message=case_ref_not_allowlisted`。

---

## §3 `execute_tabular_tool` 回传契约

实现：`tools/tabular_tool_executor.py`  
Catalog 校验：每个 `tool_id` 必须存在于 `tabular_tool_catalog_v1.json` 且 `enabled=true`。

### 3.1 必填键（contract 层）

```python
{
    "ok": bool,
    "message": str,
    "tool_id": str,           # catalog tool_id，如 validate.eligibility
    "execution_mode": str,    # dry_run | execute（本函数仅产出这两级；见 §2.1 全表）
    "side_effects": list,     # 见 §3.2
}
```

### 3.2 `side_effects[]` 条目

每项为字符串枚举，表示本次调用已发生或**将发生**的副作用类别：

| `side_effects` 值 | `dry_run` | `execute` |
|-------------------|-----------|-------------|
| `subprocess_spawn` | — | ✅ |
| `outbox_run_record` | — | ✅ |
| `outbox_events_append` | — | ✅ |
| `case_artifact_write` | — | ✅（工具成功时） |
| `planned_command_only` | ✅ | — |

**映射（现实现 → contract）**

- `dry_run=True` → `execution_mode="dry_run"`，`side_effects=["planned_command_only"]`
- `dry_run=False` → `execution_mode="execute"`，`side_effects` 含 subprocess + outbox 项（失败 run 仍写 outbox 记录）

### 3.3 稳定扩展键（实现已返回；contract 推荐保留）

| 键 | 说明 |
|----|------|
| `case_ref` | outbox 目录 slug |
| `run_id` | 与 outbox 文件名 join |
| `schema_version` | `tabular_outbox_v1`（WB-T3 对齐） |
| `exit_code` | subprocess 退出码；dry_run 为 `0`（计划） |
| `artifacts` | 预期或观测产物指针 |
| `outbox_path` |  prospective 或实际 `outbox/<case_ref>/<run_id>.json` |
| `dry_run` | **遗留布尔**；与 `execution_mode` 并存；新消费方优先读 `execution_mode` |

### 3.4 明确不做

- **不**写 Langfuse / `task_runs`
- **不**写 DLQ / `structured_errors` patch
- **不**写 Phase 8.8 `orchestration_bridge_outbox`

---

## §4 Tabular outbox 写入条件

权威 schema：`docs/tabular-tool-outbox-spec.md` · `schema_version=tabular_outbox_v1`

| `execution_mode` | 写 `outbox/<case_ref>/<run_id>.json` | 写 `outbox/events.jsonl` |
|------------------|--------------------------------------|--------------------------|
| `dry_run` | **否** | **否** |
| `plan_only` | **否** | **否** |
| `execute` | **是**（含失败 run） | **是** |
| `sandbox_end_to_end` | **是**（每步 executor 调用） | **是** |

`sandbox_end_to_end` 额外写入：`outbox/sandbox_delivery/<case_ref>/`（manifest + artifact 复本）；见 `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md`。

**Observability 索引**：outbox 记录应含或可 join `execution_mode`（WB-T4 聚合 `executor_duration_ms` / `executor_exit_code` 为可选字段）。

---

## §5 Sandbox 安全边界

### 5.1 Subprocess

| 规则 | 要求 |
|------|------|
| 超时 | 单次 catalog CLI **建议** `timeout=600s`（10 min）；超时 → `ok=false`，`exit_code=null`，`message` 含 `subprocess_timeout` |
| 工作目录 | `cwd` **必须**为 repo 根（`gov_paths` / catalog 相对路径解析）；**禁止** caller 任意指定 repo 外 cwd |
| 命令来源 | argv **仅**来自 catalog `cli_invocation` 模板 + 文档化 `extra_args`；禁止拼接未审计 shell |

> **现实现注记**：`tools/tabular_tool_executor.py` 当前 `subprocess.run` 未设 `timeout`；本合同为安全 SSOT，超时行为由 follow-up 票实现，**本票不改代码**。

### 5.2 路径与 `..` 逃逸

| 规则 | 要求 |
|------|------|
| `case_dir` 解析 | `resolve_case_dir` 必须 `.resolve()` 后落在 repo `cases/` 子树内 |
| `..` 段 | `case_ref` / `case_dir` 含 `..` 或解析后逃逸 `cases/` → `ok=false`，`message=case_dir_out_of_bounds` |
| outbox 根 | 测试与实验 **必须**用 `extra_args["outbox_root"]` 或 `--outbox-root` 指向 tmp；禁止污染 repo `outbox/` |

### 5.3 Sandbox 交付隔离

- `sandbox_end_to_end`：**永不**触发 production notify（`notify_triggered=false`）
- `production_contract=false` on sandbox manifest
- `sandbox_client`：**禁止** `--sandbox-end-to-end`（allowlist 锁）

---

## §6 Observability 与 join 规则

| 维度 | 规则 |
|------|------|
| **logs** | outbox JSON 含 `tool_id`、`execution_mode`（或 `dry_run` 映射）、`exit_code`、`message` |
| **metrics**（WB-T4 可选） | `executor_duration_ms`、`executor_exit_code` 写入 outbox 可选字段 |
| **traces** | `run_id` + `case_ref` join `outbox/<case_ref>/<run_id>.json`；`fixture_maturity` **仅** agent line 字段，tabular executor 标 `N/A` |

---

## §7 最小示例（可复制）

### 7.1 `plan_only` — intake tool path 预演

```bash
python scripts/run_tabular_intake_tool_path.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json
```

### 7.2 `dry_run` — 单工具 executor 计划

```bash
python -c "from tools.tabular_tool_executor import execute_tabular_tool; import json; print(json.dumps(execute_tabular_tool('demo_phase', 'validate.eligibility', dry_run=True), indent=2))"
```

### 7.3 `sandbox_end_to_end`（仅 `additional_demo`）

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/additional_demo \
  --mode run \
  --auto-approve-intake \
  --sandbox-end-to-end \
  --format json
```

---

## §8 PR CI 与 WA-T3 P3.5 对齐

`execute` 在 PR 合并路径仍为 **optional / shadow**，**非** mandatory gate。

| 路径 | `execute` / `--execute` | 分类 | 权威 |
|------|----------------------|------|------|
| PR `eval-gate` | **禁止**接入 `--execute` | optional 预演仅 `dry_run` / `plan_only` | `docs/phase3-5-cost-model-governance-contract-v1.md` · `OG-ROUTING-EVAL-DRYRUN` |
| PR CI | routing eval dry-run · tabular intake tool path（plan_only） | optional | W4-T4 |
| Release checklist | 人工可跑 `execute` / mainline regression | optional | `docs/tabular-mvp-release-checklist.md` |
| Nightly / shadow | agent lines / sandbox 实验 | shadow-only | W10-T1 · W12-T1 |

**双重声明**：本合同 §2 + P3.5 contract §2.3 — PR **不得**将 tabular `execute` 升格为 merge blocker。

---

## §9 验证命令

```bash
# 本票 contract 结构测试（≥10 断言）
python -m unittest tests.test_tool_executor_and_sandbox_contract_v1 -v

# 既有回归（本票 ForbiddenChanges：不得破坏）
python -m unittest tests.test_tabular_tool_executor tests.test_agent_standard_case_experiment tests.test_sandbox_delivery_bundle_v1 -v
```

---

## §10 交叉引用

| 文档 | 关系 |
|------|------|
| `docs/tabular-tool-catalog-v1.md` | `tool_id` SSOT（WB-T1 / W3-TL-T1） |
| `docs/tabular-tool-selector-spec.md` | Selector 契约（WB-T1 / W3-TL-T2） |
| `docs/tabular-tool-outbox-spec.md` | outbox schema · dry-run 不写盘 |
| `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md` | W12-T1 sandbox e2e |
| `docs/phase3-5-cost-model-governance-contract-v1.md` | PR gate 分类 |
| `docs/agent-run-standard-case-experiment-v1.md` | W6-T4/T8 orchestrator |

---

*WB-T2 · tool-executor-and-sandbox-safety-contract-v1 · Phase 8.8 · 2026-06-11*
