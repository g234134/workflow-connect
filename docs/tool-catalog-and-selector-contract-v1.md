# Tool Catalog and Selector Contract — v1

> **版本**：v1.0（Toolchain Wave B · WB-T1）  
> **更新**：2026-06-11  
> **角色**：Tabular / Non-Tabular **Catalog + Selector** 跨轨 **唯一权威 SSOT**  
> **关系**：Tabular 实现附录见 `docs/tabular-tool-catalog-v1.md` · `docs/tabular-tool-selector-spec.md`；Non-Tabular routing 见 `docs/non-tabular-routing-catalog-v1.md`；Multi-Chat 施工边界见 `docs/phase4-multi-agent-collaboration-contract-v1.md` §3。

---

## §1 适用范围

### 1.1 何时启用

| 场景 | 是否适用本 contract |
|------|---------------------|
| Wave B/C 引用 `tool_id`、catalog JSON、selector 输出形状 | **是** — 以本档为 SSOT |
| W3-TL-T1/T2 Tabular catalog/selector 实现细节 | **部分** — 本档定跨轨边界；字段细则见 Tabular 附录 |
| W9-T3 Non-Tabular selector stub | **部分** — 本档定 NT catalog + `planned_tools[]` 形状 |
| Gov Registry（`obs.*` / `kb.*`）或 Phase 8.8（`llm.*`）编排 | **引用 §2 分轨表** — **禁止**写入 Tabular/NT JSON |
| prod selector 接 prod gate / E2E 驱动 | **否** — 见 §6 Wave C 假设 |

### 1.2 文档层级

```
本 contract（SSOT 跨轨边界 + 命名 + selector 形状）
    ↑
Tabular 附录：tabular-tool-catalog-v1.md · tabular-tool-selector-spec.md
Non-Tabular 附录：non-tabular-routing-catalog-v1.md（routing YAML 不改本票）
    ↑
机器 SSOT：tools/tabular_tool_catalog_v1.json · tools/non_tabular_tool_catalog_v1.json
```

**双维护禁止**：旧 spec 仅保留「实现附录」与指针；新增跨轨规则 **只** 写入本 contract。

### 1.3 默认假设（Wave B/C Agent）

- Selector 输出 **`plan_only: true`**（推荐／计划层；**不是** gate 结果、**不是** delivery 批准）
- Tabular `tool_id` 仅来自 `tools/tabular_tool_catalog_v1.json`
- Non-Tabular `tool_id` 仅来自 `tools/non_tabular_tool_catalog_v1.json`
- Gov Registry / Phase 8.8 工具 **不得** 出现在上述两份 JSON
- KB selector hook（`kb.index.*`）属 Gov Registry 轨；与 Tabular/NT selector **分轨**，见 `docs/phase2-knowledge-indexing-contract-v1.md` §1

---

## §2 四轨对照表

四套 Catalog **禁止** 合并 JSON 或共用 `tool_id` 命名空间。

| 轨 | `governed_by` | SSOT 文档 / 位置 | `tool_id` 格式 | 与本 contract 关系 |
|----|---------------|------------------|----------------|---------------------|
| **Tabular MVP** | `tabular_mvp` | 本档 §2 + `tools/tabular_tool_catalog_v1.json` · `docs/tabular-tool-catalog-v1.md` | `<category>.<name>`（如 `intake.new_case`、`validate.eligibility`） | **本票 Tabular 权威**；W3-TL-T2 Selector 消费 |
| **Non-Tabular shadow** | `non_tabular_shadow` | `tools/non_tabular_tool_catalog_v1.json` · `docs/non-tabular-routing-catalog-v1.md` | snake_case 符号名（如 `text_extractor`、`log_parser`） | **本票 NT 权威**；W9-T3 stub；`symbolic_only: true` |
| **Gov Registry** | `gov_registry` | `docs/SKILL_CATALOG_OVERVIEW.md` · `skills/gov_cards/*.json` | `obs.*` · `kb.*` · `route.*` | **分轨**；不入 Tabular/NT JSON |
| **Phase 8.8 暗部编排** | `phase_8.8_spec` | `04_Workflows/SPEC_tool_catalog_and_selector_v1.md`（draft）· W3-T1–T4 state | `llm.*` 等 | **分轨**；暗部 orchestration；与本票 rename/合并 **禁止** |

### 2.1 `governed_by` 字段语义

| 值 | 含义 | Selector 是否消费 |
|----|------|-------------------|
| `tabular_mvp` | Tabular case 主链工具层 | `select_tabular_tools` |
| `non_tabular_shadow` | NT-A/NT-B 符号工具 stub | `select_non_tabular_tools` |
| `gov_registry` | Wave B 可观测 / KB CLI 登记 | routing policy / ask 侧车（**非**本票 selector） |
| `phase_8.8_spec` | 暗部 LLM / outbox 编排 draft | 未来 Phase 8.8 专票；**禁止** WB-T1 合入 Tabular JSON |

**Product skill cards**（`skill-clean-*`）为第五分轨（`governed_by: product_sku`），同样 **禁止** 写入 Tabular/NT JSON。

---

## §3 tool_id 命名规则

### 3.1 Tabular MVP（`governed_by: tabular_mvp`）

- **格式**：`<category>.<name>`，小写；`category` 为已知动词域前缀。
- **允许 category 前缀**（unittest 校验）：`intake` · `validate` · `clean` · `export` · `orchestrate` · `index` · `lookup` · `plan` · `ui`
- **禁止前缀**（不得出现在 `tabular_tool_catalog_v1.json`）：`obs.` · `kb.` · `llm.` · `skill-clean` · `nt.` · `non_tabular.`
- **禁止** 使用 Non-Tabular catalog 已登记的 `tool_id`（如 `text_extractor`）

### 3.2 Non-Tabular shadow（`governed_by: non_tabular_shadow`）

- **格式**：snake_case 符号名；**不** 使用 `tabular.*` 或 Tabular category 前缀。
- **v1 登记 ID**：`text_extractor` · `doc_classifier` · `log_parser` · `anomaly_summarizer`
- **禁止前缀**：`obs.` · `kb.` · `llm.` · `intake.` · `validate.` · `clean.` · `export.` · `orchestrate.`
- **禁止** 与 Tabular catalog 中任一 `tool_id` 相同

### 3.3 Gov Registry / Phase 8.8（仅交叉引用）

| 轨 | 前缀示例 | SSOT |
|----|----------|------|
| Gov Registry | `obs.eval.report` · `kb.index.bootstrap` | `skills/gov_cards/` |
| Phase 8.8 | `llm.ask.route` · `llm.outbox.replay` | 暗部 draft spec |

### 3.4 碰撞处理

- Tabular 与 Non-Tabular **全局唯一**：两 JSON 的 `tool_id` 集合交集必须为空。
- 若 routing catalog 使用符号名（如 `extract.text_content`），W9-T3 通过 `_SYMBOLIC_TO_CATALOG_TOOL` 映射到 NT catalog `tool_id`；**contract 权威 ID** 以 NT JSON 为准。

---

## §4 Selector 输入 / 输出 dict 形状

> **全局**：所有 selector 返回 **`plan_only: true`**（文档语义；实现可在调用方侧标注）。下游 **不得** 将 selector 输出当作 INT gate / delivery gate / prod blocking 结果。

### 4.1 Tabular — `select_tabular_tools`

**实现**：`tools/tabular_tool_selector.py` · 附录 `docs/tabular-tool-selector-spec.md`

**输入**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `case_dir` | str | 是 | Case 目录路径 |
| `task_type` | str | 是 | `gate_only` \| `clean` \| `bundle` \| `e2e` |
| `intake` | dict \| None | 否 | 解析后的 `intake.json` |
| `gate_notes` | list[str] \| None | 条件 | P2 gate `dimensions.schema.notes`；`clean`/`e2e` 时若显式传参则须非空 |

**输出（必填键）**

```python
{
    "ok": bool,
    "message": str,
    "selector_rule_id": str,
    "candidate_tools": list,  # 0–2 项；ok=false 时 []
    "plan_only": True,          # contract 语义；Wave C 接 prod 前须显式消费
}
```

**`candidate_tools[]` 每项必填键**

| 键 | 类型 | 说明 |
|----|------|------|
| `tool_id` | str | 须存在于 Tabular catalog 且 `enabled=true` |
| `reason` | str | 可审计说明 |
| `requires_force` | bool | 清洗是否需 `--force` |
| `human_review_required` | bool | 是否建议人工复核 |

**Observability（文档字段，本票不写 logger）**

| 字段 | 来源 | 用途 |
|------|------|------|
| `decision_reason` | 实现侧 `message` + `selector_rule_id` | 日志 / sidecar JSON |
| `catalog_tool_count` | Tabular JSON `tools` 长度 | WB-T4 dashboard 消费 |
| `selector_candidate_count` | `len(candidate_tools)` | WB-T4 dashboard 消费 |

### 4.2 Non-Tabular — `select_non_tabular_tools`

**实现**：`tools/non_tabular_tool_selector_v1.py` · stub only

**输入**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_type` | str | 是 | `non_tabular.*` 或 `non-tabular.*` |
| `case_profile` | str | 是 | 案型描述符 |
| `max_tools` | int | 否 | 默认 3 |

**输出（必填键）**

```python
{
    "ok": bool,
    "message": str,
    "selector_rule_id": str,
    "flow_family": "non_tabular",
    "profile_tier": str | None,  # "NT-A" | "NT-B" | None when error
    "planned_tools": list,         # ok=false 时 []
    "plan_only": True,
}
```

**`planned_tools[]` 每项必填键**

| 键 | 类型 | 说明 |
|----|------|------|
| `tool_id` | str | 须存在于 NT catalog |
| `reason` | str | 映射来源说明 |
| `input_kind` | str | `document` \| `log` |
| `output_kind` | str | catalog 声明 |
| `maturity` | str | 默认 `experimental` |
| `symbolic_only` | bool | v1 固定 `true` |

### 4.3 Trace 串接规则

跨步骤 trace **建议**携带（Wave C executor / dashboard 消费）：

```text
case_ref + task_type + selector_rule_id
```

| 轨 | `case_ref` 示例 | `task_type` 示例 |
|----|-----------------|------------------|
| Tabular | `cases/demo_phase` | `clean` · `e2e` |
| Non-Tabular | `docu-corp` | `non_tabular.document.extract` |
| Routing glue | 同上 | `tabular.cleaning.mvp`（routing 层；glue 再调 Tabular selector） |

**禁止**：用 `selector_rule_id` 单独作为 merge gate 或 delivery 批准依据。

---

## §5 与 Wave A P4 角色边界交叉引用

Multi-Chat 施工须对齐 `docs/phase4-multi-agent-collaboration-contract-v1.md` §3（O → B → C → D）：

| 角色 | 与本 contract 关系 |
|------|-------------------|
| **Orchestrator** | 冻结 FRAME.AllowedPaths；WB-T1 禁止 Implementer 改 selector 实现 |
| **Implementer** | **仅**改本票 AllowedPaths；**不得**改 `tabular_tool_selector.py` / `select_non_tabular_tools` 行为 |
| **Reviewer** | 对照 §2 四轨表 + §3 命名 + unittest AC；**不可绕过** |
| **Scribe** | 更新 Dashboard / WORKFLOW_INDEX 指针；不重写 contract 正文 |

**Implementer 边界（WB-T1 明示）**

- Allowed：本 contract、附录 §0 指针、contract unittest、ticket state B_REPORT
- Blocked：selector 实现、CI/gate、MVP 主链、Gov/Phase 8.8 JSON 合并

---

## §6 Wave C 假设（显式非目标）

Wave C 及后续票 **可假设**：

1. 可读 `candidate_tools[]` / `planned_tools[]` 作为 executor 计划输入
2. `plan_only: true` 可在 sidecar / outbox metadata 中显式标注
3. `catalog_tool_count` / `selector_candidate_count` 可由 dashboard 只读聚合
4. Trace 键 `case_ref + task_type + selector_rule_id` 可写入 outbox event

Wave C **不得假设**（除非另票交付）：

1. Selector 已接 prod INT gate 或 blocking delivery gate
2. Tabular E2E driver 默认调用 selector（仍须 `TABULAR_SELECTOR_ENABLED` 或等价 flag 专票）
3. Non-Tabular stub 已接 heavy processor 或外部 API
4. Gov Registry / Phase 8.8 工具已并入 Tabular JSON
5. `selector_candidate_count` 参与 SLO / canary 裁决（见 `docs/phase3-5-cost-model-governance-contract-v1.md`）

---

## §7 验证入口

```bash
# WB-T1 contract unittest（≥12 断言）
python -m unittest tests.test_tool_catalog_and_selector_contract_v1 -v

# 既有 catalog/selector 不回歸
python -m unittest tests.test_tabular_tool_catalog tests.test_tabular_tool_selector tests.test_non_tabular_tool_selector_v1 -v
```

**票 state**：`04_Workflows/tickets/WB-T1-tool-catalog-and-selector-contract-v1_state.md`

---

*TOOL-CATALOG-SELECTOR-CONTRACT-v1 · Toolchain Wave B · WB-T1 · 2026-06-11*
