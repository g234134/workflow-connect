# Phase 2 Knowledge Indexing Contract — v1

> **版本**：v1.0（Wave A · WA-T1）  
> **更新**：2026-06-10  
> **角色**：Phase 2 收录与分类 **唯一权威 SSOT**  
> **关系**：技术实现见 `docs/knowledge-layer.md`；本档定义「什么算被知识层收录」、双 pipeline 边界、metadata／命名／Wave／Phase 标注，以及新 spec 登记流程。

---

## §1 收录定义（What Counts as Indexed）

知识层对任一 artifact 的收录状态为 **三态之一**。Agent 不得自行发明第四态。

| 状态 | 定义 | 可检索性 | 典型证据 |
|------|------|----------|----------|
| **`indexed`** | 已写入 PostgreSQL 元数据 **且** Qdrant 向量 collection，可通过 smoke retrieve 交叉验证 | PG + Qdrant 可语义检索 | `document_chunks` / `repo_chunks` smoke；`ingest_verify` / `repo_index_agent` 输出 `ok: true` |
| **`catalogued`** | 已在 `04_Workflows/WORKFLOW_INDEX.md` 和／或 `docs/index.md` 登记为 human／Agent 导航入口，**未**向量化 | 仅路径／索引可发现；**不可**假设 PG+Qdrant 命中 | 新 spec／runbook 票交付；W3-B pilot 状态 JSON（experimental） |
| **`excluded`** | 明确禁止纳入主知识层检索或未经授权的 ingest 目标 | 不得作为 ask 主路或 repo tool 的默认检索源 | 见 §1.1 |

**默认假设（Wave B/C Agent）**

- 文档 RAG 主路 → `document_chunks`（`indexed` 文档 pipeline）
- 程式码语义检索 → `repo_chunks`（`indexed` codebase pipeline）
- 新交付的 governance spec → 至少 **`catalogued`**；是否升格 `indexed` 须走 §6 登记 + 专票 ingest
- W3-B repo index 试点 → **`catalogued` / experimental**；**禁止**假设全 repo 已 `indexed`

### §1.1 禁收录类型（`excluded` · 引用憲法 §7）

> **分流**：下表仅列**类型**；具体路径见 `04_Workflows/INSTANCE_ANCHOR_TANG.md` §4。完整类型表见 `04_Workflows/HARNESS_CONSTITUTION.md` §7.1。

| 类型 | 说明 | 知识层处理 |
|------|------|------------|
| **Z-ENV** | 环境密钥类 | **excluded** — 禁止 ingest；验证仅 `_smoke_test_keys.py` `[OK]`/`[FAILED]` |
| **Z-VENV-TREE** | 暗部 venv 套件树 | **excluded** — 不得 chunk／embed |
| **Z-RUNTIME-CP** | 执行态 checkpoint | **excluded** — 未授权不得写入索引 |
| **Z-ORCH-DESTRUCT** / **Z-DARK-OPS** / **Z-HQ-LIQUIDATION** | 破坏性／清算类脚本 | **excluded** |
| **Z-HQ-ENV-EDIT** | 擅自改根 `.env` 等 | **excluded** |
| **GraphRAG job 输出** | `graphrag_jobs` / `graphrag_grag1` | **excluded from primary retrieval** — 保留表结构；不得驱动 ask selector（见 `knowledge-layer.md` §1.1） |
| **agentmemory（PG+AGE）** | 独立 Docker schema | **excluded from Gov Core 主知识层** |
| **CrewAI/LangChain Knowledge** | 第三方 venv 套件 | **excluded**（憲法／`AGENTS.md` 红线） |
| **secrets / credentials** | 任何含密钥原文的文件 | **excluded** |

---

## §2 双 Pipeline 边界（document_chunks / repo_chunks）

| 维度 | Document pipeline | Codebase pipeline |
|------|-------------------|-------------------|
| **Collection** | `document_chunks` | `repo_chunks` |
| **PG 主表** | `documents` · `agent_runs` · `graphrag_jobs`（ingest 作业列） | `repo_index_jobs` · `repo_index_manifest` |
| **内容** | `.md` / `.txt` / `.markdown` UTF-8 文件 | `.py` 源码（manifest 扫描） |
| **Chunk 参数** | 320 / 48（冻结） | 320 / 48（冻结） |
| **Embedding** | `text-embedding-3-small`（1536 dim） | 同上 |
| **Ask 主路** | ✅ `perform_retrieve_query` | ❌ 不经 ask 主路 |
| **Tool 路径** | RAG smoke / answer | `repo_retrieve_v1` · `repo_tool_dispatch` |
| **与 `documents` 表** | 写入 | **不**写入 |
| **Sidecar** | — | 可选 `graph.v0.json`（**不**取代 Qdrant） |

**明确 excluded / 非主方案**

| 组件 | 状态 | 说明 |
|------|------|------|
| `graphrag_jobs` | catalogued skeleton | 实验队列；**非** primary retrieval |
| `_indexing_and_audit.py` → `metadata_index.json` | catalogued legacy | C2 户籍化索引；**≠** Qdrant `document_chunks` |
| `Master_Map.json` → `_build_elite_index.py` | catalogued tooling | 精英索引构建；**≠** 全 repo `repo_chunks` |
| W3-B pilot（`workflow_v2/20_pilot/W3-B/`） | catalogued / experimental | 案卷 KB 回填试点；scope 有限 |

**Phase 2 非目标（本 contract 不宣称）**

- 全库实时 repo index
- 新增 Qdrant collection
- GraphRAG / agentmemory 升格为主知识层

---

## §3 Metadata Schema v0.1

> **权威对齐**：字段语义与 PG／Qdrant payload 映射以 `docs/knowledge-layer.md` §3 为实现母本。  
> **冲突处理**：若 `knowledge-layer.md` §3.2「建议扩展」段落与本 contract 必填表冲突，**以本 contract 为准**；建议扩展字段（`doc_type`／`project`／`tags`／`source_path_rel` 写入 ingest）仍为 **draft**，待专票改 `data_pipeline`，不得宣称为已验收 ingest 行为。

### §3.1 Canonical 字段（逻辑名 · 必填语义）

| 字段 | 型别 | 说明 | document_chunks | repo_chunks |
|------|------|------|-----------------|-------------|
| `doc_id` | UUID string | 文件：`documents.id`；代码：`(job_id, repo_rel_path)` 确定性 UUID | ✅ | ✅ |
| `doc_type` | enum | `document` \| `code` \| `corpus` | 建议 `meta`／payload | payload `language` 辅助 |
| `source` | string | 人类可读来源：档名或 `repo_rel_path` | `doc_key` | `repo_rel_path` |
| `project` | string | 专案逻辑名（如 `gov_core`） | `meta.project` | job scope |
| `version` | int | 文件 ingest 递增 | `version` | `manifest_version` 辅助 |
| `chunk_id` | string | Qdrant point id（UUID5） | ✅ | ✅ |
| `chunk_index` | int | 0-based chunk 序号 | ✅ | ✅ |
| `created_at` | ISO-8601 UTC | 创建时间 | PG `documents.created_at` | manifest `indexed_at` |
| `updated_at` | ISO-8601 UTC | 更新时间 | PG | job `updated_at` |
| `tags` | string[] | 治理／过滤标签 | `meta.tags` + payload 同步 | 可选 scope tags |
| `content_sha256` | string | 全文／文件 hash | ✅ payload | ✅ payload |
| `agent_run_id` | UUID | ingest 执行关联 | ✅ payload | job 级 meta |

### §3.2 现行 payload 键（已落地 · 摘录）

**`document_chunks`**（见 `knowledge-layer.md` §3.2）：`document_id` · `doc_key` · `chunk_index` · `text` · `version` · `content_sha256` · `agent_run_id`

**`repo_chunks`**（见 `knowledge-layer.md` §3.3）：`repo_rel_path` · `path` · `job_id` · `job_type` · `chunk_index` · `text` · `content_sha256` · `language` · `manifest_version`

### §3.3 Spec front-matter 与 ingest metadata 关系

§5 front-matter 字段（`phase_tag` 等）用于 **catalogued** 登记与将来 ingest 标注；写入 Qdrant 前须映射到 §3.1 canonical 字段，映射规则见 §5.2。

---

## §4 命名与路径规则

| 规则 | 说明 |
|------|------|
| **路径权威** | 逻辑名见 `Master_Map.json` · `gov_paths`；**禁止**硬编码磁盘绝对路径 |
| **Contract 文件** | `docs/phase2-knowledge-indexing-contract-v1.md`（本档） |
| **实现文档** | `docs/knowledge-layer.md` |
| **Spec 命名** | `docs/<topic>-<role>-v<N>.md`（如 `intake-routing-catalog-v1.md`） |
| **Ticket state** | `04_Workflows/tickets/<TICKET-ID>_<slug>_state.md` |
| **Collection 名** | 仅 `document_chunks` · `repo_chunks`（Phase 2 冻结） |
| **doc_key 模式** | `ingest_batch/<hash>/<stem>`（document pipeline） |
| **repo job_type** | `repo_index_v1` |
| **W3-B 状态 JSON** | `workflow_v2/20_pilot/W3-B/index_status_<CASE>.json` |

---

## §5 Wave / Phase 标注规则

### §5.1 命名空间（禁止混淆）

| 名称 | 含义 | 示例 |
|------|------|------|
| **Phase（企业化）** | `00_master_plan.md` Phase 1–6 能力域 | P2 = 知识层／Indexing |
| **Wave（Tabular MVP）** | `docs/WAVE_PROGRESS_DASHBOARD.md` W1–W12 | W3-TL = Tabular 工具层 |
| **Wave A（波段 A）** | `docs/WAVE_A_EXECUTION_PLAN.md` 高完成度收尾 | P2 contract = WA-T1 |

**禁止**：将 Tabular `cases/demo_phase/raw/Phase.csv` 或 Wave 编号当作企业化 Phase 完成度 SSOT。

### §5.2 新 Spec 必填 front-matter（YAML 或表格列）

每份新 spec／runbook／governance 文档在 **catalogued** 登记时须含以下字段（YAML front-matter 或 Markdown 表格等价列）：

| 字段 | 必填 | 允许值 | 说明 |
|------|------|--------|------|
| `phase_tag` | ✅ | `P1` … `P6` | 企业化 Phase |
| `wave_tag` | ✅ | `W1` … `W12` · `WA` · `none` | Tabular MVP Wave；纯 Phase 文档可 `none` |
| `content_class` | ✅ | `governance` \| `spec` \| `runbook` \| `skill` \| `experiment` | 内容类别 |
| `index_tier` | ✅ | `A` \| `B` \| `draft` | A=主 SSOT；B=辅助；draft=未冻结 |

**样例 YAML front-matter**

```yaml
---
phase_tag: P2
wave_tag: WA
content_class: spec
index_tier: A
title: phase2-knowledge-indexing-contract-v1
---
```

**样例 Markdown 表格行（WORKFLOW_INDEX 登记用）**

| phase_tag | wave_tag | content_class | index_tier | path |
|-----------|----------|---------------|------------|------|
| P2 | WA | spec | A | `docs/phase2-knowledge-indexing-contract-v1.md` |

### §5.3 index_tier 与收录三态映射

| index_tier | 默认 catalogued | 升格 indexed 条件 |
|------------|-----------------|-------------------|
| **A** | ✅ 必须 WORKFLOW_INDEX | 专票 ingest + smoke 证据 |
| **B** | ✅ docs/index 可选 | 按需 ingest |
| **draft** | catalogued only | 不得宣称为 indexed |

---

## §6 登记流程（WORKFLOW_INDEX / docs/index / ticket state）

### §6.1 优先级（防双轨漂移）

1. **Ticket 交付物** → **必须**写入 `04_Workflows/WORKFLOW_INDEX.md`（含票号、spec 路径、验证命令、state 链接）
2. **`docs/index.md`** → 仅 human 导航；PR checklist 对照 WORKFLOW_INDEX，**以 WORKFLOW_INDEX 为准**
3. **`ticket state`** → `04_Workflows/tickets/<ID>_state.md` 记录 FRAME／B_REPORT／验证

### §6.2 新 Spec 登记 checklist

| 步骤 | 动作 | 目标 |
|------|------|------|
| 1 | 撰写 spec + §5 front-matter | `docs/<name>-v1.md` |
| 2 | 追加 WORKFLOW_INDEX 条目 | §Phase 2 或对应 Wave 小节 |
| 3 | 可选追加 docs/index 导航行 | 架构／计划段 |
| 4 | 创建／更新 ticket state | `04_Workflows/tickets/` |
| 5 | 若需向量检索 | 另开 ingest 票 → `indexed` + smoke |

### §6.3 何时更新哪一份索引

| 场景 | WORKFLOW_INDEX | docs/index | ingest |
|------|----------------|------------|--------|
| 新 governance spec 票交付 | ✅ 必须 | 推荐 | 否（默认 catalogued） |
| Runbook smoke 路径变更 | ✅ 必须 | 可选 | 若文档内容变更且需 RAG → 专票 |
| 实验 pilot（W3-B） | ✅ 标 experimental | 否 | catalogued only |
| Phase 2 实现细节变更 | 交叉引用 | 更新 knowledge-layer 链接 | 不改本 contract 除非收录规则变 |

### §6.4 Future ingest observability（本票不实现）

未来 ingest job 应携带 `run_id` 并关联 `agent_runs.id`（见 `knowledge-layer.md` §4 与 `agent_run_id` payload）。本票仅 codify 契约，不修改 `core/data_pipeline.py`。

> **脚注（P2-INDEX-OBS-FOOTNOTE-v1）**：叙述边界与 Wave B `index_cases` 分栏见 `docs/phase2-index-obs-footnote-v1.md`（关闭 gap-audit **GAP-OBS-INDEX** 的文档可导航缺口；**≠** 已接线 `agent_runs`）。

---

## §7 验收命令

### §7.1 最小工作示例（本地可跑 · 无需 live PG/Qdrant）

```powershell
# 1) Contract 结构与引用校验（≥8 断言）
python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v

# 2) 文档引用存在性（_indexing_and_audit.py 无 argparse --help；勿在无 env 时直接跑全脚本）
python 04_Workflows/_indexing_and_audit.py --help
# ↑ 预期：无 --help 选项；以文件存在为准：
python -c "from pathlib import Path; assert Path('04_Workflows/_indexing_and_audit.py').is_file()"
```

```powershell
# 3) 可选：对照 knowledge-layer 实现入口（需暗部 venv + live DB）
# python 04_Workflows/_smoke_test_keys.py
# 见 docs/knowledge-layer.md §6
```

### §7.2 Contract 自检清单

| # | 检查项 | 证据 |
|---|--------|------|
| 1 | §1 三态定义完整 | 本档 §1 表 |
| 2 | §2 双 pipeline 边界 | `knowledge-layer.md` §2 一致 |
| 3 | §3 metadata 与 knowledge-layer §3 零冲突或 contract 优先 | §3 冲突处理段 |
| 4 | §5 Phase vs Wave 区分 | §5.1 表 |
| 5 | WORKFLOW_INDEX 含 WA-T1 | `04_Workflows/WORKFLOW_INDEX.md` §Phase 2 |
| 6 | unittest 全绿 | §7.1 命令 1 |

---

## 相关文档

| 文档 | 角色 |
|------|------|
| `docs/knowledge-layer.md` | 双 pipeline **实现**与 CLI 入口 |
| `docs/WAVE_A_EXECUTION_PLAN.md` | 波段 A Phase 完成度 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Tabular MVP Wave 进度 |
| `workflow_v2/20_pilot/W3-B/W3-B_index_pipeline_runbook.md` | Repo index 试点 runbook |
| `04_Workflows/tickets/WA-T1-phase2-knowledge-indexing-contract-v1_state.md` | 本票 state |

---

*PHASE2-KNOWLEDGE-INDEXING-CONTRACT-v1 · Wave A · WA-T1 · 2026-06-10*
