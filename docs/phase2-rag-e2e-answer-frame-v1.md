# Phase 2 RAG E2E Answer FRAME — v1（planning only）

> **版本**：v1.0（Full-Phase G2 · FP-G2-T3）  
> **日期**：2026-07-10  
> **角色**：RAG E2E 问答／LLM synthesis **诚实 planning FRAME**（≠ 已验收 demo 问答）  
> **票**：`04_Workflows/tickets/FP-G2-T3-rag-e2e-answer-frame-v1_state.md`  
> **上游**：FP-G2-T2 `docs/phase2-index-contract-gap-audit-v1.md`（**GAP-E2E**）· WA-T1 contract · LANE-A `A-G2-T3`  
> **ticket_class**：`doc/spec · planning`（本票无 runtime 变更）

---

## §0 non_claims（必读）

| 禁止宣称 | 说明 |
|----------|------|
| 本 FRAME／doc **≠** RAG E2E 问答已落地或已验收 | 仅规划边界；无新 E2E 套件、无本票跑通合成答案 |
| 本票 **≠** P2 closure · ≠ Phase% 上调 | Dashboard P2 仍以既有 SSOT 为准 |
| 本票 **≠** K-2 prod 主答案 · ≠ partial rollout | 见 `docs/k2_deployment_governance.md`；本票仅分轨 non_claim |
| 本票 **≠** GraphRAG 主路 · ≠ 改 ask／RAG selector | GraphRAG → T4；selector／LLM 实作另票 |
| baseline rag smoke **引用** **≠** 本票新跑通 E2E | 下列命令仅作现状锚点，本票不扩跑未定义套件 |

---

## §1 Goal 与 ticket_class

### Goal

为知识层 **E2E 问答／LLM synthesis** 大缺口产出可审查的 planning FRAME：明确 **MVP vs stretch**、串行依赖（T2 **GAP-E2E** + index 就绪叙事）、验收边界、解阻条件与后续实作票占位。

### ticket_class

| 字段 | 值 |
|------|-----|
| `ticket_class` | **doc/spec · planning** |
| `evidence_tier` | L-local（doc + `rg`） |
| 本票交付 | 本文档（+ 可选 INDEX／docs/index 一句） |
| 本票**不**交付 | runtime、selector、LLM、CI workflow、未定义 E2E 跑批 |

---

## §2 MVP vs stretch

### MVP — 何谓「可验收 E2E 问答」（规划定义 · 非本票已达成）

后续**实作票**在宣称「E2E 问答可验收」前，须同时满足（本 FRAME 仅定义，不执行）：

| # | 条件 | 说明 |
|---|------|------|
| M1 | **Retrieve 基线绿** | 既有 document／repo retrieve smoke（见 §4）在约定环境可重跑且 `ok` |
| M2 | **Index 就绪叙事诚实** | 依赖 T1 hook／infra 解阻后的 index 能力；不得把 dry-run skeleton 当成生产 cron |
| M3 | **合成路径有界** | 明确「retrieve →（可选）LLM synthesis → 结构化答案 dict」的契约；**不**默许改写 prod selector 决策 |
| M4 | **验收命令可重跑** | 专票定义 runner／unittest；禁止口头「demo 过了」冒充 AC |
| M5 | **non_claims 仍成立** | 通过 ≠ P2 closure ≠ K-2 主答案升格 |

**本票 MVP 交付**（仅此）：本 FRAME doc 本身（MVP/stretch 分栏 · GAP-E2E 引用 · baseline 引用 · 解阻 · non_claims）。

### Stretch — 明确不做／另轨

| 项 | 归属 | 本票 |
|----|------|------|
| GraphRAG 生产跑批／状态机落地 | **GAP-GRAPH** → `FP-G2-T4` | ❌ |
| smoke_corpus 扩档 | **GAP-CORPUS** → `FP-G2-T5`（PM） | ❌ |
| K-2 prod 主答案／canary／扩面 | `docs/k2_deployment_governance.md` | ❌ |
| 改 `core/**` ask／RAG selector／LangGraph 新图 | 后续 runtime 票 | ❌ |
| 未定义「全库 E2E 套件」冒充验收 | 禁止 | ❌ |
| LLM synthesis 生产接线 | 建议票占位 §6 | ❌（本票） |

---

## §3 串行依赖与 gap 边界

### 硬依赖（已满足）

| 上游 | 产物 | 本 FRAME 用法 |
|------|------|----------------|
| **FP-G2-T2**（done） | `docs/phase2-index-contract-gap-audit-v1.md` | 引用 **GAP-E2E** 为开本票依据 |
| **WA-T1** | `docs/phase2-knowledge-indexing-contract-v1.md` | 三态／双 pipeline；E2E 为 stretch 叙事 |

### GAP 表交叉引用（T2）

| Gap ID | 与本票关系 |
|--------|------------|
| **GAP-E2E** | **本票主缺口**：lane-map critical；「无 `phase2-rag-e2e-answer-frame`；rag smoke ≠ E2E 问答验收」→ 本 doc 关闭「无 FRAME」文档缺口，**不**关闭「无 runtime E2E」能力缺口 |
| **GAP-SCHED**／**GAP-HOOK-DOC** | Index 排程／hook → `FP-G2-T1`（done · skeleton）；E2E 实作前须诚实对待「index 就绪」 |
| **GAP-GRAPH** | GraphRAG **excluded from primary retrieval**；状态机 → **T4**（可并行 doc，非本票范围） |
| **GAP-CORPUS** | corpus 扩 → **T5**（blocked on PM）；本票不扩档 |

### 与 T1 index 就绪叙事

- T1 交付：`docs/phase2-index-job-hook-v1.md` + dry-run CLI（`writes_index=false`）。  
- **解阻前**：不得宣称规模化 index 已落地，因而也不得宣称「依赖生产 index 的 E2E」已可跑。  
- 本 FRAME 将「index hook／infra 解阻」列为 E2E **实作票**前置（§5），非本票 AC。

---

## §4 Baseline（仅引用 · 本票不扩跑）

> 下列为**现状锚点**（knowledge-layer／catalog／contract）。本票 **不**要求执行、**不**新增 E2E 套件、**不**把 smoke 结果写入本票验收证据。

| 层级 | 逻辑名／入口（引用） | 语义 |
|------|----------------------|------|
| 文件 RAG smoke runbook | `04_Workflows/runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md` | 文件 RAG smoke |
| Manifest keyword smoke | tool `kb.index.rag_smoke` · `workflow_v2/kb/rag_index_smoke.py` | 无 PG／Qdrant 的 keyword smoke |
| Ask 主路 retrieve | `core/retrieve_core.perform_retrieve_query` → `document_chunks` | retrieve ≠ LLM synthesis 验收 |
| 文件交叉验证工具 | `document_chunks_smoke_retrieve_and_verify` | R1/R2 字段 |
| 程式码检索 | `repo_chunks_smoke_retrieve_and_verify`／`repo_retrieve_v1` | repo pipeline |
| Contract 结构回归 | `python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v` | 收录契约；非 E2E 问答 |
| 实现叙述 | `docs/knowledge-layer.md` §6 CLI 速查 | ingest／retrieve 入口 |

**判定**：baseline 绿 **仅**证明 retrieve／契约层；**不能**单独证明「E2E 问答／LLM synthesis」已验收。

---

## §5 解阻条件（后续实作票）

在宣称「E2E 问答 runtime 可验收」前，建议同时满足：

| 角色 | 条件 | 本票 |
|------|------|------|
| **工程** | 另开票实现有界 synthesis／答案 dict；禁无 FRAME 改 selector | **未交付** |
| **Infra** | 若依赖 live PG／Qdrant／密钥舱位：runner 与 runbook 回填 | **未交付**（若需） |
| **Index** | T1 execute 模式／生产调度解阻（见 hook doc §3）或等价 index 就绪证据 | **未交付** |
| **PM／尚书省** | 若触及 corpus 扩或 K-2 流量：独立批文（T5／K-2 playbook） | **未交付**；本票不碰 |

未解阻前：仅允许本 FRAME 与既有 smoke **引用**；**禁止**把本 doc 标为 E2E 已验收。

---

## §6 建议后续票（占位 ID）

| 建议 ID（占位） | 目的 | 相对本 FRAME |
|-----------------|------|----------------|
| `FP-G2-T3b-rag-e2e-answer-runtime-v1`（建议） | 最小可重跑 E2E／synthesis skeleton（仍须新 FRAME） | 关闭 GAP-E2E **能力**侧 |
| `FP-G2-T4-graphrag-jobs-state-machine-v1` | GraphRAG 状态机 doc | **GAP-GRAPH**；∥ 本票 doc |
| `FP-G2-T5-smoke-corpus-expansion-v1` | corpus 扩 FRAME | **GAP-CORPUS**；blocked on PM |
| （K-2 专票） | shadow／canary／主答案 | **禁止**与本 FRAME 合并 |

---

## §7 交叉引用

| 文档／票 | 关系 |
|----------|------|
| `docs/phase2-index-contract-gap-audit-v1.md` | **GAP-E2E** 开票依据 |
| `docs/phase2-knowledge-indexing-contract-v1.md` | 收录三态；GraphRAG excluded |
| `docs/phase2-index-job-hook-v1.md` | index 就绪／skeleton 边界 |
| `docs/knowledge-layer.md` | retrieve／CLI 实现叙述 |
| `docs/k2_deployment_governance.md` | K-2 流量分轨（仅边界） |
| `04_Workflows/tickets/FP-G2-index-job_state.md` | G2 母票 |
| LANE-A `A-G2-T3` | 同目标别名／规划源 |

---

## §8 本票验收（doc／rg）

```powershell
rg "phase2-rag-e2e-answer-frame|MVP|stretch|GAP-E2E|non_claims" docs/phase2-rag-e2e-answer-frame-v1.md
# 预期：命中 MVP/stretch、GAP-E2E、non_claims、文件名锚点

# MAY
rg "phase2-rag-e2e-answer-frame" 04_Workflows/WORKFLOW_INDEX.md
```

**成功信号**：FRAME doc 存在 · MVP/stretch 分栏 · 引用 GAP-E2E · 无 `core/**` 变更。  
**失败信号**：改 selector／core · 宣称 E2E 已验收 · 跑未定义 E2E 套件冒充 AC。
