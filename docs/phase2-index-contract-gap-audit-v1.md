# Phase 2 Index Contract Gap Audit — v1

> **版本**：v1.0（Full-Phase G2 · FP-G2-T2）  
> **日期**：2026-07-10  
> **角色**：WA-T1 收录契约 vs 当前能力的 **只读 gap 审计**（≠ 修复清单已完成）  
> **Contract SSOT**：`docs/phase2-knowledge-indexing-contract-v1.md`  
> **票**：`04_Workflows/tickets/FP-G2-T2-phase2-index-contract-gap-audit-v1_state.md`

---

## §0 non_claims（必读）

| 禁止宣称 | 说明 |
|----------|------|
| 本审计 **≠** 已修复下列 gap | 仅列期望／实际／建议票 |
| 本审计 **≠** P2 closure／Phase% 上调 | Dashboard P2 仍以既有 SSOT 为准 |
| 本审计 **≠** 新 index job／cron 已落地 | 见 GAP-SCHED → `FP-G2-T1` |
| 本审计 **≠** GraphRAG／E2E 问答已验收 | 见 GAP-E2E／GAP-GRAPH → T3／T4 |
| Tabular C2-P2 子域完工 **≠** 全局知识层 index 排程就绪 | Dashboard 已分栏 |

---

## §1 对照范围

| 来源 | 用途 |
|------|------|
| `docs/phase2-knowledge-indexing-contract-v1.md` | 期望：三态 · 双 pipeline · 登记流程 · 非目标 |
| `docs/knowledge-layer.md` | 实际：ingest／repo_index／CLI 入口叙述 |
| `docs/observability.md`（index_cases／kb_index_status） | 实际：eval／pilot 侧车观测 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` P2 行 | 实际：完成度叙事（65% · 无新 index job） |
| `docs/full-phase-lane-map-v1.md` L2 | 缺口：规模化排程 · E2E／GraphRAG |
| `python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v` | Contract 结构回归（本票须仍绿） |

---

## §2 Gap 表

| ID | 期望（contract／lane-map） | 实际 | 优先级 | 建议票 | Verify／artifact |
|----|---------------------------|------|--------|--------|------------------|
| **GAP-SCHED** | 规模化 index job／排程能力可演进（lane-map L2 Ready-to-build：单票 hook） | Dashboard／Progress：**本轮无新 index job**；无 `scripts/run_index_job_hook_v1.py` | **P0** | `FP-G2-T1-index-job-scheduler-hook-v1` | `rg "run_index_job_hook" scripts/` → 预期 0（T1 前）；T1 后 dry-run CLI |
| **GAP-HOOK-DOC** | 触发模型与解阻条件可文档化 | 仅 contract §6.4「Future ingest observability」占位；无 hook 设计 doc | **P0** | `FP-G2-T1`（doc 段） | `rg "index-job-hook\|index job hook" docs/phase2*` |
| **GAP-META-DRAFT** | metadata 建议扩展字段（`doc_type`／`tags` 等）可升格 ingest | contract §3：**draft**；明示待专票改 `data_pipeline`，不得宣称已验收 | **P1** | 另开 ingest metadata 票（非本 sprint 必做） | contract §3「冲突处理／draft」段 |
| **GAP-OBS-INDEX** | ingest job 携带 `run_id`↔`agent_runs`（contract §6.4） | §6.4 **真接线仍不实现**；observability `index_cases` 主要服务 W3-B／eval sidecar，非全库排程 SSOT | **P1** | **脚注已交付**：`P2-INDEX-OBS-FOOTNOTE-v1` → `docs/phase2-index-obs-footnote-v1.md`（≠ 接线）；真接线另票 | `rg "phase2-index-obs-footnote-v1\|GAP-OBS-INDEX" docs/phase2-index-obs-footnote-v1.md` · contract unittest |
| **GAP-E2E** | E2E 问答／LLM synthesis 为知识层 stretch（lane-map critical gaps） | 无 `phase2-rag-e2e-answer-frame`；rag smoke ≠ E2E 问答验收 | **P2** | `FP-G2-T3-rag-e2e-answer-frame-v1`（串行本审计） | `rg "rag-e2e-answer-frame" docs/` → 预期 0（T3 前） |
| **GAP-GRAPH** | GraphRAG **excluded from primary retrieval**；状态机可规划 | `graphrag_jobs`／backend 为 skeleton；无状态机设计 doc | **P2** | `FP-G2-T4-graphrag-jobs-state-machine-v1` | contract §1.1 GraphRAG 行 · `docs/knowledge-layer.md` GraphRAG 行 |
| **GAP-CORPUS** | 非种子 corpus 扩展须独立 verify（防破 INV） | smoke_corpus 种子路径存在；无扩展 FRAME／PM 策略 | **P2** | `FP-G2-T5-smoke-corpus-expansion-v1`（blocked on T1+PM） | lane-map／LANE-A T5；勿无 FRAME 扩档 |
| **GAP-PILOT** | W3-B repo index = catalogued／experimental | 试点 runbook／`index_status` 样例存在；**禁止**假设全 repo `indexed` | **P3**（叙事） | 维持 non-claim；勿并入主路 | contract §1 W3-B 段 · `workflow_v2/20_pilot/W3-B/` |
| **GAP-LEGACY** | `_indexing_and_audit.py` → `metadata_index.json` = catalogued legacy ≠ Qdrant | 脚本存在；与 `document_chunks` 分轨已在 contract／INDEX 写明 | **P3**（已标注） | 无需新票；防混淆即可 | INDEX §1.24 Legacy 行 · unittest 含脚本存在断言 |

---

## §3 与 Observability Wave B 命名空间

| 命名空间 | 含义 | 勿与本审计混淆 |
|----------|------|----------------|
| WA-T1／FP-G2 | Gov 知识层收录契约与 index job 缺口 | — |
| Wave B `index_cases`／`kb_index_status` | eval／pilot 侧车就绪度 | **≠** 全库规模化 index 排程已完成 |
| Tabular C2-P2 | 清洗子域完工 | **≠** P2 全局 index job |

---

## §4 建议消费顺序

```text
FP-G2-T2（本票 · done）
    ├─∥─► FP-G2-T1（hook skeleton · 下一张 execute）
    ├─∥─► FP-G2-T4（graphrag 状态机 doc · 非 P0）
    └─串行► FP-G2-T3（E2E FRAME · 读本 gap 表）
              FP-G2-T5（corpus · 串行 T1 + PM）
```

---

## §5 回归验证

```powershell
python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v
# 预期：OK（≥8 断言；当前 13）

rg "GAP-|non_claims" docs/phase2-index-contract-gap-audit-v1.md
rg "phase2-index-contract-gap-audit" 04_Workflows/WORKFLOW_INDEX.md
```

---

## 相关文档

| 文档 | 角色 |
|------|------|
| `docs/phase2-knowledge-indexing-contract-v1.md` | 期望 SSOT |
| `docs/knowledge-layer.md` | 实现叙述 |
| `docs/full-phase-lane-map-v1.md` | L2 缺口 |
| `04_Workflows/tickets/FP-G2-index-job_state.md` | G2 母票 arrange |
| `04_Workflows/tickets/FP-G2-T1-index-job-scheduler-hook-v1_state.md` | 下一张 build |

---

*PHASE2-INDEX-CONTRACT-GAP-AUDIT-v1 · FP-G2-T2 · 2026-07-10*
