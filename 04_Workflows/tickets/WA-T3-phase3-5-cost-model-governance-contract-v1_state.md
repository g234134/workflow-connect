# TICKET STATE · WA-T3 · phase3-5-cost-model-governance-contract-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- **Goal**: 把分散在 eval-gate CI、shadow pipeline、K-2 治理、ENF shadow、成本/风险条文中的 gate 行为，收敛为 Phase 3.5 governance contract SSOT（mandatory / optional / shadow-only）。
- **Scope**:
  - `docs/phase3-5-cost-model-governance-contract-v1.md`（新建）
  - `tests/test_phase3_5_governance_contract_v1.py`
  - 轻量 cross-ref：`docs/testing.md`、`docs/k2_deployment_governance.md`、`docs/k2_merge_strategy.md`、`docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md`、`docs/governance-constitution-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`、`docs/WAVE_PROGRESS_DASHBOARD.md`、`docs/WAVE_A_EXECUTION_PLAN.md`
- **NonScope**:
  - ❌ 不改 eval_ci_check 门槛、ENF blocking 旗标、production CI `if:` 条件
  - ❌ 不启用 K-2 Phase 2 canary 或 `GOV_ENF_BLOCKING_CANARY=1`
  - ❌ 不统一 daily_cost_summary vs task_runs
- **AcceptanceCriteria**: AC-1–AC-10（见票面）

---

## STATE

- **overall_status**: implementer_done
- **current_owner**: implementer
- **next_action**: Reviewer 对照 AC-1–AC-10 审 contract 与 unittest
- **last_updated**: 2026-06-10 · Implementer
- **phase35_completion**: 55% → **83%**（本票 codify 后预期）
- **status_by_role**:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- **changed_files**:
  - `docs/phase3-5-cost-model-governance-contract-v1.md`（新增 · SSOT）
  - `tests/test_phase3_5_governance_contract_v1.py`（新增）
  - `docs/testing.md`（§5 eval/shadow cross-ref）
  - `docs/k2_deployment_governance.md`（Phase 3.5 contract 索引段）
  - `docs/k2_merge_strategy.md`（contract cross-ref）
  - `docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md`（contract cross-ref）
  - `docs/governance-constitution-v1.md`（§3.4 指针行）
  - `04_Workflows/WORKFLOW_INDEX.md`（WA-T3 索引）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave A · WA-T3 done）
  - `docs/WAVE_A_EXECUTION_PLAN.md`（§0 P3.5 ~83%）
  - `04_Workflows/tickets/WA-T3-phase3-5-cost-model-governance-contract-v1_state.md`（本檔）

- **verification**:
  - `python -m unittest tests.test_phase3_5_governance_contract_v1 tests.test_eval_gate -v` → **17/17 OK**
  - `python 04_Workflows/_ops_cycle.py checklist --mode full` → **`ok: true`**（archive + wave1 readiness 全 pass）

- **behavior_notes**:
  - contract = gate 分类 SSOT；各 runbook = 操作细节
  - routing eval dry-run 在 eval-gate PR job 运行但分类为 **optional**（AC-5）
  - shadow nightly `continue-on-error` → `blocks_mainline=N`

---

## Work Report（简）

| 节 | 内容 |
|----|------|
| §1 变更 | 见 changed_files |
| §2 skeleton | 无 |
| §3 placeholder | 成本双数据源 follow-up 票号占位（§6.3） |
| §4 验证 | unittest 见 verification |
| §5 阻塞 | checklist 若失败记 blocked，不冒充 done |
| §6 下一步 | Reviewer AC 审查 |
| §7 override | 无 |
