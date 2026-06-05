# Wave 3 战役总结 — 回答侧 skill 化 + selector 收敛

> **封存日**：2026-05-24  
> **角色**：Chat C（收口与治理封存）  
> **范围**：文档 / run_queue / master_plan；**无 .py 变更**

---

## Summary（尚书省存档）

### 本轮完成

- **J-answer-skill-wire（Chat A）**：`langgraph_flow.answer_node` 统一经 `ask_skills_wire.run_answer_via_skill` → `skill_answer_for_ask`；answer 与 retrieve metrics 对称（`call_site`、`external_call_count`、`retry_count`、span `execute`）。
- **J-selector-context-governance（Chat B）**：`ask_rag_selector.decide_use_rag`（ASK-R1–R6）+ `selector_node` 图路由；S1 KB→RAG、S2 问候 skip retrieve、S3 retrieve 失败→`direct_fallback`；`ibridge_v0.selector_decision` 可审计。
- **K-2 合流治理（Chat A/B/C）**：行为画像 + `merge_ask_and_k2` adapter + `k2_deployment_governance`（Phase 0–4 rollout、指标、回退）；prod 仍 Phase 0（ask-only）；`K2-ask-shadow-merge` done，`K2-rollout-governance` planned。
- **Chat C 封存**：`90_run_queue.md` 对齐；`00_master_plan.md` §4.7–§4.8；合同 §9–§10 / context §8 / eval_pipeline §6.5 对齐。

### 验证证据

| 类型 | 命令 / 产物 |
|------|-------------|
| Answer skill 单元 | `python -m unittest tests.test_skills_ask_wire.py -v` |
| Selector + 流程 S1–S3 | `python -m unittest tests.test_ask_selector_and_answer.py -v` |
| Ask skills E2E | 暗部 `tests.test_ask_skills_wire_e2e` |
| Trace / ibridge | S3 断言 `ibridge_record.selector_decision.retrieve_fallback`、`answer.retrieve_error_type` |
| M-line metrics | S2/S3 断言 `record.external_call_count >= 1`（answer 步仍计数） |

### 对下一轮的影响

- **P+-eval-ci-wire**：export 批次已可含 answer 步 `external_call_count` 与 selector 标签；CI 阈值需用真实 dev/staging export 重算（见 `eval_stats_report.md`）。
- **K2-ask-shadow-merge**：ask 主线 retrieve/answer/selector 已稳定；K-2 shadow 可对照同一 metrics 字段。
- **H-historical-migrate**：**done（2026-05-25）** — 預設 ask 已走 H 線；selector S1–S3 回歸全綠。
- **遗留**：K-2 图内 agent 仍为 stub；prod K-2 rollout 见 `k2_deployment_governance.md`。

### 能力层叙事（一句话）

从「只有 retrieve skill 的 metrics-aware」升级为 **问 + 检索 + 答** 三段在同一治理骨架（H context → J skills → selector 路由 → P+ eval export）下可观测、可回归、可封存。

---

## 关联索引

- 任务队列：`_workflow_upgrade/90_run_queue.md`（Wave 3 Done + K2-rollout-governance planned）
- 总蓝图：`00_master_plan.md` §4.7–§4.8
- K-2：`docs/k2_behavior_profile.md` · `docs/k2_merge_strategy.md` · `docs/k2_deployment_governance.md`
- 合同：`skills/skills_contract.md` §9–§10；`context/context_entry_contract.md` §8
- Eval：`observability/eval_pipeline.md` §6.5
