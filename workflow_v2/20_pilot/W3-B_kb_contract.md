# W3-B — 知识层 / Repo Indexing 总控契约（index-before-AI-READY）

> **票号**：**W3-B-ORCH**  
> **角色**：Wave 3 主线 B 编排骨架（制度 only；**不写** index job 代码、**不改** G7/G8 正文、**不**替换 RAG prod 主路径）  
> **权威**：`00_master_plan.md` §13.2 · `02_dependency_map.md` §8 · G7-2 §4 **IMP-AI-READY**（只读引用，不增删 entry 条文）  
> **下游施工**：`90_run_queue.md` → W3-B-KB-CONTRACT／INDEX-PIPELINE／GRAPHRAG-MIN／SELECTOR-HOOK  
> **暗部能力索引**（只读）：`core/repo_index_job.py`（`job_type=repo_index_v1`）· `SPEC_repo_tool_catalog_v1.md`（`repo_index_v1_job`）· Progress「Repo index QA」段落

---

## 1. 制度定位与硬边界

| 项 | 说明 |
|----|------|
| **Wave 3 最低完成** | **repo index** 成为 **`IMP-AI-READY` 前置**；案卷与 **ART-ENG-CTX** 可**查** index 状态（`ready`／`stale`／`missing`），不宣称全库实时一致 |
| **本档交付** | `index-before-AI-READY` 规则、最小字段集、block vs degrade、`_TEMPLATE_case` 扩展建议、四张子票施工摘要 |
| **out-of-scope**（§13.2） | 全库**实时增量**索引；多 **tenant KB** 产品化；**替换**现有 RAG 主路径或 ask selector 生产默认 |
| **G7/G8** | 本制度以 **案卷字段 + ENG-CTX 扩展 + pilot 说明** 落地；**不**修改 `10_workflow_states.md`／`20_entry_conditions.md`／`30_engineering.md` 正文语义。G7-2 **IMP-AI-READY** 的「最少 artifact」仍含 **ART-ENG-CTX**；本案卷 KB 字段为 **AI-READY 前的附加 gate**（W3-B-KB-CONTRACT 写入模板后成为 P0 可查证据） |

### 1.1 Wave 4 接入点（W4-B implementation v1）

Wave 4 的最小实装以“**案卷字段（P0）+ 状态 JSON 侧车（P2）+ ORCH precheck 脚本**”作为接线点：

- **案卷回填**：`workflow_v2/tools/wf_kb_index_sync.ps1`（`index_status_*.json` → `kb_index_*`）
- **ORCH/AI-READY 前置 gate**：`workflow_v2/tools/wf_kb_index_gate.ps1`（读取案卷 `kb_index_*`，输出 `allow / require-human-override / deny`）
- **主 case / 主 repo**：见 `workflow_v2/20_pilot/W3-B/W4-B_orch_integration.md`

---

## 2. index-before-AI-READY 制度

### 2.1 原则（一句话）

**在 artifact 标称进入 `IMP-AI-READY` 之前，导入 scope 须至少完成一次离线 repo index，且案卷（P0）与 ENG-CTX（P1）须能回答「有没有 index、针对哪份 scope、何时更新、是否过期」。**

### 2.2 哪些 IMP 流程需要 index

| IMP 态 | index 要求 | 类型 | 说明 |
|--------|------------|------|------|
| **`IMP-SCOPE-DRAFT`** | 无 | — | 范围未定时不要求 index |
| **`IMP-SPEC-CLARIFY`** | 建议 | **软** | 若 `in_scope` 已含代码库路径语义，可**并行**启动 index pipeline（不阻塞澄清关）；状态可记 `missing` |
| **`IMP-AI-READY`** | **必须** | **硬（entry gate）** | `kb_index_status` **不得**为 `missing`；`stale` 见 §2.4 |
| **`IMP-REVIEW-READY` 及之后** | 继承 | **硬（继承）** | 若 AI-READY 时曾为 `ready`，进入 REVIEW 前若 scope／基线 commit 变更导致 index 过期，按 **stale** 处理（§2.4），**不**允许静默退回 `missing` 而不留痕 |
| **`IMP-REWORK` → 回到 `IMP-AI-READY`** | 视 scope 变更 | **条件硬** | `rework` 若变更 `in_scope` 代码路径或 repo root／subtree，须 **re-index** 或显式登记 `kb_index_status=stale` + 重跑票号 |

**最低制度覆盖**（§13.2）：**至少 `IMP-AI-READY` entry 硬门禁**；其余上表为推荐对齐，由 W3-B-SELECTOR-HOOK 与 checker 清单引用。

### 2.3 状态枚举（案卷权威）

| `kb_index_status` | 含义 | 对 `IMP-AI-READY` |
|-------------------|------|-------------------|
| **`ready`** | 存在覆盖当前 **index scope** 的成功 index job；manifest／状态可查；未超过 staleness 阈值 | **允许** entry（须满足 G7-2 其余 entry） |
| **`stale`** | 曾有 index，但 scope 指纹、基线 ref 或时间已超过阈值（见 W3-B-INDEX-PIPELINE） | **degrade**（§2.4）；默认 **不** 单独 block，须留痕 |
| **`missing`** | 无覆盖 scope 的成功 job，或仅有失败／中断 job | **block** entry |

**禁止**将 queue `Status`、route `assignable`、RAG `hits` 数量直接写入 `kb_index_status`。

### 2.4 block vs degrade

| 情境 | 处置 | 留痕 |
|------|------|------|
| **`kb_index_status=missing`** 且拟进入 **`IMP-AI-READY`** | **Block**：不得更新 `imp_state` 至 `IMP-AI-READY`；施工票保持 `BLOCKED` 或案卷态内 blocker | 案卷 §2 `kb_index_blocker`；IMP 迁移日志 **不** 写 forward 至 AI-READY |
| **`kb_index_status=stale`** 且拟进入 **`IMP-AI-READY`** | **Degrade / warning**：允许 entry **仅当** 同时满足：(1) `kb_index_stale_ack=true`（PM 或 engineering 主责）；(2) `kb_index_stale_reason` 非空；(3) `kb_index_reindex_ticket` 已登记（可为 TODO 票号） | §3 迁移日志追加「带 stale ack 进入 AI-READY」行 |
| **`stale`** 且进入 **`IMP-REVIEW-READY`**（scope 已变） | **Warning + 建议 re-index**：不强制 block REVIEW，但 **ART-ENG-EVD** 须声明检索／工具链可能基于过期图 | WR §5 阻塞或 §3 placeholder |
| **shadow／canary（W3-A）** | **软**：宜在 run 记录中抄录案卷 `kb_index_status`；index **missing** 不自动 block shadow，但 checker **应** 标 `accepted_with_gaps` | `20_pilot/W3-A/shadow_run_*.md` |

### 2.5 index scope（逻辑）

单次导入 artifact 的 index scope **至少**包含：

| 字段 | 说明 |
|------|------|
| `kb_index_scope_kind` | `repo_subtree`（默认）／`path_glob_list`（试点扩展） |
| `kb_index_repo_root_ref` | 逻辑名：`repo_root`（战车主根）；**禁止**写死磁碟绝对路径 |
| `kb_index_subtree` | 如 `core`、`subagents`；与 **ART-PM-SCOPE** `in_scope` 对齐 |
| `kb_index_baseline_ref` | 可选：commit SHA、标签或「未钉基线」声明 |

**scope 变更** → 自动将 `ready` 降为 `stale`（由 W3-B-INDEX-PIPELINE 定义指纹规则；本档只声明制度）。

### 2.6 与 G7-2 IMP-AI-READY 的对齐（只读引用）

G7-2 要求 **ART-ENG-CTX** 等；**不**在 G7 正文新增「index」字句。实施方式：

1. **W3-B-KB-CONTRACT** 在 `_TEMPLATE_case` §2 增加 KB 表（P0）。  
2. **ART-ENG-CTX** 增加 **建议字段**（P1，见 §4.2）；checker 用 pilot 清单验证，而非修改 G8-3 正文。  
3. 进入 `IMP-AI-READY` 时，`entry_evidence_refs` **应** 包含 index 证据指针（如 `repo_index_job_id` 或 `20_pilot/W3-B/index_status_<CASE>.json` 逻辑名）。

---

## 3. 最小字段集（v0.1 · ORCH 冻结名）

> **版本**：`kb_index_schema_version: "0.1"`（建议写在案卷 front matter，与 `imp_state_schema_version` 并列）

### 3.1 案卷（P0 · `<CASE>_case.md`）

| 字段 | 必填 | 类型／取值 | 说明 |
|------|:----:|------------|------|
| **`kb_index_status`** | 自 `IMP-SPEC-CLARIFY` 起建议；**AI-READY 前必填** | `ready` \| `stale` \| `missing` | §2.3 |
| **`kb_index_source`** | AI-READY 前必填 | 如 `repo_index_v1` \| `manual_decl` \| `unknown` | 对齐暗部 `JOB_TYPE` 或人工声明 |
| **`kb_index_last_updated`** | AI-READY 前必填 | ISO-8601 UTC | 最后一次 **成功** index 完成时间；`missing` 时写 `—` |
| **`kb_index_job_id`** | `ready`／`stale` 时必填 | UUID 或 job 表主键 | 对接 `repo_index_job`；`missing` 时 `—` |
| **`kb_index_scope_kind`** | 建议 | 见 §2.5 | |
| **`kb_index_subtree`** | 建议 | string | 默认与 PM scope 一致 |
| **`kb_index_baseline_ref`** | 可选 | string | commit／tag／`unpinned` |
| **`kb_index_stale_ack`** | 仅 `stale`→AI-READY | boolean | §2.4 degrade 门禁 |
| **`kb_index_stale_reason`** | `stale_ack=true` 时必填 | string | |
| **`kb_index_reindex_ticket`** | `stale` 时建议 | 施工票 ID | |
| **`kb_index_blocker`** | `missing` 时必填 | string | 人类可读 blocker 摘要 |
| **`kb_index_evidence_refs`** | AI-READY 前必填 | path 语义列表 | 如 manifest 逻辑路径、`index_pipeline_notes` 节号；**不**贴 secret |

### 3.2 ART-ENG-CTX（P1 · 施工起手）

在 G8-3 §4.1 必填之外，**W3-B 试点**增加（由 ENG worker 写入 Context Brief／JSON 侧车）：

| 字段 | 必填 | 说明 |
|------|:----:|------|
| **`repo_index_job_id`** | 与案卷 `kb_index_job_id` **一致**（`ready`／`stale`） | 主引用；等价别名禁止另造 |
| **`kb_index_status`** | ✓ | 须与案卷 P0 **一致**；不一致 → checker `blocked` |
| **`kb_index_scope_digest`** | 建议 | scope 指纹（由 INDEX-PIPELINE 定义算法）；用于判 `stale` |
| **`kb_index_query_ref`** | 可选 | 指向只读状态 JSON／runbook 节，供 selector hook 读取 |

**禁止**在 ART-ENG-CTX 写 PG DSN、Qdrant URL、`.env` 键名。

### 3.3 结构化侧车（P2 · 可选）

| 载体 | 字段 | 说明 |
|------|------|------|
| `20_pilot/W3-B/index_status_<CASE>.json` | `job_id`、`status`、`file_count`、`finished_at`、`scope` | W3-B-INDEX-PIPELINE 产出；**逻辑路径**，实例路径由 `Master_Map.json` 解析 |
| IMP 迁移日志 §3 | `kb_index_status_at_transition` | 每次 **进入** `IMP-AI-READY` 时追加一列（KB-CONTRACT 模板施工） |

---

## 4. `_TEMPLATE_case` 扩展建议（仅建议 · 由 W3-B-KB-CONTRACT 施工）

> **禁止**本票直接修改 `_TEMPLATE_case/_TEMPLATE_case.md`（留给 **W3-B-KB-CONTRACT**）。

### 4.1 建议插入位置

| 位置 | 建议 |
|------|------|
| **§2 当前 IMP 状态表** | 在 `imp_state_updated_by_ticket` 行之后增加 **「KB / Repo Index（`kb_index_current`）」** 子表（约 8–10 行），字段见 §3.1 |
| **§3 IMP 迁移日志** | 表头增加可选列：`kb_index_status_at_transition`；进入 `IMP-AI-READY` 的行 **必须**填写 |
| **§1 任务描述** 或 **§5 前新增 §4bis** | **「Index scope 声明」**：`kb_index_scope_kind`、`kb_index_subtree`、`kb_index_baseline_ref`；与 PM `in_scope` 交叉引用 |
| **§5 案卷文件索引** | 增加一行：`20_pilot/W3-B/index_status_<CASE>.json`（若存在）→ ART 类型 `ART-ENG-EVD` 辅助 |

### 4.2 命名与 `imp_state` 并列规则

- KB 字段前缀统一 **`kb_index_*`**；**不**使用 `index_status` 无前缀别名（避免与 K-2／monitoring 索引混淆）。  
- `imp_state` 与 `kb_index_status` **独立**：禁止用 `ready` 代替 `IMP-AI-READY`。  
- 复制模板时 front matter 增加：`kb_index_schema_version: "0.1"`。

### 4.3 W3-B 试点案卷

- 建议复制 `_TEMPLATE_case` → `20_pilot/W3-B_case/`（**W3-B-KB-CONTRACT** 施工），作为 Wave 3 B 线 **golden case**。

---

## 5. W3-B 子票施工摘要

### 5.1 W3-B-KB-CONTRACT

| 项 | 内容 |
|----|------|
| **目标** | 将 §3 字段写入 **`_TEMPLATE_case`** 与 **`W3-B_case`**；更新 `W2-2_imp_state_schema.md` **交叉引用**（可选 §「KB 并行字段」）；产出 `20_pilot/W3-B/kb_index_contract.md`（字段 normative 正文，可自本档精简迁移） |
| **依赖** | W3-B-ORCH（本档）、W2-2-IMP-FIELD |
| **产出** | 模板 diff、试点案卷、checker grep 清单草案 |
| **禁区** | 不改 G7/G8 正文；不写 index Python；不宣称 CI enforcement |
| **DoD** | 新案卷复制模板即含 KB 表；`IMP-AI-READY` pilot 清单含「三字段齐全」 |

### 5.2 W3-B-INDEX-PIPELINE

| 项 | 内容 |
|----|------|
| **目标** | **文档／Runbook only**：定义「导入 scope → 触发 `repo_index_v1` job → 写入状态 JSON → 更新案卷 KB 字段」的对接点；对齐 `repo_index_agent` CLI、`SPEC_repo_tool_catalog_v1` 的 `repo_index_v1_job` |
| **依赖** | W3-B-KB-CONTRACT |
| **产出** | `20_pilot/W3-B/index_pipeline_notes.md`；`index_status_*.json` **形状**示例（无 secret）；staleness 阈值表 |
| **禁区** | **不写**新 job 代码；不做全库实时增量；不替换 document_chunks ingest |
| **DoD** | 人工可按 runbook 对单一 subtree 跑通一次 offline index 并填齐案卷三字段（证据在 Progress／案卷，非本票执行） |

### 5.3 W3-B-GRAPHRAG-MIN（可选）

| 项 | 内容 |
|----|------|
| **目标** | 单一 scope 的 **GraphRAG 最小 job** + smoke 验收说明（`graph.v0.json` 已备路径）；依赖 index manifest |
| **依赖** | W3-B-INDEX-PIPELINE |
| **产出** | `20_pilot/W3-B/graphrag_min_probe.md` |
| **禁区** | **不阻塞** §13.4 Wave 3 DoD；不启动无 runbook 的大型 GraphRAG；产品化 → Wave 4 |
| **DoD** | 探针文档含：前置 index job_id、期望 `ok` 语义、失败时 **不** 回退 `kb_index_status` 为 `missing` 的规则 |

### 5.4 W3-B-SELECTOR-HOOK

| 项 | 内容 |
|----|------|
| **目标** | 工具选择层 **规则 only**：当 `runtime_context.kb_index_status`（或 ENG-CTX 镜像）为 `missing` 时 **block** `repo_*` retrieve／graph 类工具；`stale` 时 **degrade**（降优先级或强制 `cost_class=high` 审计） |
| **依赖** | W3-B-INDEX-PIPELINE |
| **产出** | `20_pilot/W3-B/selector_hook_spec.md`；映射 `repo_tool_preconditions` 的 `job_status` bucket 建议键 |
| **禁区** | **不改** production `repo_tool_selector`／ask selector；不接 ask pipeline 默认路径 |
| **DoD** | 规格含决策表 + 结构化 `decision_log` 示例行；与 `SPEC_tool_layer_vnext_draft.md` §2.1.2 对齐声明 |

---

## 6. 依赖链与软依赖（复述）

```
W3-B-ORCH (本档)
  → W3-B-KB-CONTRACT
    → W3-B-INDEX-PIPELINE
      → W3-B-SELECTOR-HOOK
      → W3-B-GRAPHRAG-MIN (可选，并行)
```

- **W3-A**：`W3-B-INDEX-PIPELINE` **宜先于或并行** `W3-A-SHADOW-PILOT`（`02` §8.3 R10）。  
- **W2-2**：`imp_state` P0 与 KB P0 **同案卷**，由 KB-CONTRACT 统一模板。

---

## 7. 风险与 TODO

| ID | 项 | 严重度 | 处理票 |
|----|-----|--------|--------|
| R-B1 | PG／Qdrant 不可达时 index job 失败（Progress 已记录） | 高 | INDEX-PIPELINE runbook 须写「基础设施 blocker vs missing」区分 |
| R-B2 | G7 正文未写 index，checker 可能漏检 | 中 | W3-B-KB-CONTRACT + W2-2-QA-CHECKLIST 增补 grep |
| R-B3 | `stale` 阈值未定义导致争议 | 中 | INDEX-PIPELINE 冻结阈值或「默认 7 日 + scope 变更即 stale」 |
| R-B4 | 与 K-2 shadow 指标混淆 | 低 | 案卷／shadow 记录分栏 `kb_index_*` vs `k2_*` |
| T-B1 | 机读 CI 校验 KB 字段 | 低 | Wave 4+；本波仅人工／helper |
| T-B2 | `manual_decl` 滥用绕过 index | 中 | 须 PM + engineering 双签 `kb_index_stale_ack` 等效流程 |

---

## 8. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W3-B-ORCH 初稿：`index-before-AI-READY`、字段集、子票摘要、模板建议 |
