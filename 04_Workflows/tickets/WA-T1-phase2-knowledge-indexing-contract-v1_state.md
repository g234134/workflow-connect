# TICKET STATE · WA-T1 · phase2-knowledge-indexing-contract-v1

> handoff 摘要档；跨 chat 交棒以本档为准。  
> Wave：**Wave A · Phase Foundations（P2 知识层 / Indexing）**

---

## FRAME

- Goal: 产出 Phase 2 唯一权威 contract，定义收录三态、双 pipeline 边界、metadata／命名／Wave／Phase 标注，以及登记流程。
- Scope:
  - 新建 `docs/phase2-knowledge-indexing-contract-v1.md`
  - 新建 `tests/test_phase2_knowledge_indexing_contract_v1.py`
  - 追加 `docs/knowledge-layer.md` cross-ref（不重写 §1–§3）
  - 更新 `docs/index.md` · `WORKFLOW_INDEX.md` · `WAVE_PROGRESS_DASHBOARD.md` · `WAVE_A_EXECUTION_PLAN.md`
- NonScope:
  - 不改 `core/data_pipeline.py` · ingest 写入逻辑
  - 不扩面全 repo index · 不新增 Qdrant collection
  - 不改 production CI workflow
- AllowedPaths: 见票面 AllowedPaths
- BlockedPaths: 见票面 ForbiddenChanges
- Dependencies: `docs/knowledge-layer.md` · `04_Workflows/_indexing_and_audit.py` · W3-B pilot
- AcceptanceCriteria: AC-1 … AC-10（票面）

---

## STATE

- overall_status: review
- current_owner: implementer
- next_action: Reviewer 对照 AC-1–AC-10 与 knowledge-layer §3 metadata
- last_updated: 2026-06-10 · implementer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `docs/phase2-knowledge-indexing-contract-v1.md`（新建 · SSOT）
  - `tests/test_phase2_knowledge_indexing_contract_v1.py`（新建）
  - `docs/knowledge-layer.md`（文首 cross-ref）
  - `docs/index.md`（Phase 2 contract 导航行）
  - `04_Workflows/WORKFLOW_INDEX.md`（§Phase 2 / WA-T1 条目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave A · Phase Foundations 行）
  - `docs/WAVE_A_EXECUTION_PLAN.md`（P2 ~82% + evidence）
  - `04_Workflows/tickets/WA-T1-phase2-knowledge-indexing-contract-v1_state.md`（本档）
- artifacts: contract §1–§7 · front-matter YAML 样例 · unittest ≥12 断言
- verification:
  - `python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v` → exit 0
  - `04_Workflows/_indexing_and_audit.py` 存在性已测（脚本无 argparse `--help`；contract §7 已注明）
- behavior_notes:
  - contract = 收录规则 SSOT；knowledge-layer = 技术实现
  - knowledge-layer §3.2 建议扩展字段标为 draft；contract §3 明示「contract 优先」
  - W3-B pilot 标 catalogued/experimental；禁止假设全 repo indexed
- deferred_items:
  - `doc_type`/`project`/`tags` 写入 ingest（专票改 data_pipeline）
  - future ingest run_id / agent_runs.id 接线（§6.4 引用 only）

---

## C_REPORT

- conclusion: <!-- Reviewer 填 -->
- blocking_issues: <!-- Reviewer 填 -->
- checks_summary: <!-- Reviewer 填 -->
- risk_level: <!-- Reviewer 填 -->
- suggestions: <!-- Reviewer 填 -->

---

## D_REPORT

- docs_updates: <!-- Scribe 填 -->
- progress_entry: <!-- Scribe 填 -->
- followup_suggestions: <!-- Scribe 填 -->
