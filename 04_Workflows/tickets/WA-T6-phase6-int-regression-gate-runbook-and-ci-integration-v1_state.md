# TICKET STATE · WA-T6 · phase6-int-regression-gate-runbook-and-ci-integration-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal: 把 INT-REGRESSION-GATE、Tier-A/Tier-B、与 core-agent-smoke / eval-gate / W10 agent-lines CI 的关系收敛为 Phase 6 gate spec + runbook
- Scope: `docs/phase6-int-regression-gate-contract-v1.md`（SSOT）；cross-ref WAVE7 gate 附录、testing.md、WORKFLOW_INDEX、Dashboard、Execution Plan；contract unittest
- NonScope: 不改 `_wave7_regression_gate.py` 逻辑；不新增 production GHA workflow；不把 INT 硬塞进 eval-gate-ci；不扩 Tier-B；不宣称 nightly INT 已在 CI
- AllowedPaths: docs/phase6-int-regression-gate-contract-v1.md · tests/test_phase6_int_regression_gate_contract_v1.py · WAVE7_* cross-ref · testing.md · WORKFLOW_INDEX · WAVE_PROGRESS_DASHBOARD · WAVE_A_EXECUTION_PLAN · tabular-mvp-release-checklist · 本 state
- BlockedPaths: `_wave7_regression_gate.py` · `core/wave7_regression_gate.py` · `.github/workflows/*`（新增/硬改 INT gate）· MVP 主链 regression
- Dependencies: WAVE7_INT_REGRESSION_GATE_v0.1.md · _wave7_regression_gate.py · gov_core wave7_regression_gate.py · testing.md · core-agent-smoke.yml · eval-gate-ci.yml · W10-T1/T2/T3 docs
- AcceptanceCriteria: AC-1–AC-10（见 Orchestrator 票面）

---

## STATE

- overall_status: in_progress
- current_owner: implementer
- next_action: Reviewer 跑 contract unittest + 可选 `--tier A --pretty` 对照 modules
- last_updated: 2026-06-10 · implementer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `docs/phase6-int-regression-gate-contract-v1.md`（新建 · §1–§8 SSOT + runbook）
  - `tests/test_phase6_int_regression_gate_contract_v1.py`（新建）
  - `04_Workflows/tickets/WA-T6-phase6-int-regression-gate-runbook-and-ci-integration-v1_state.md`（新建）
  - `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md`（文首 Phase 6 contract 索引）
  - `docs/testing.md`（§1 · §3 · §5.1 对齐 contract）
  - `04_Workflows/WAVE7_RUNBOOK_CLI_AND_QA_v0.1.md`（§7 cross-ref）
  - `04_Workflows/WAVE7_CLEAN_RUNNER_ORCH_OVERVIEW_v0.1.md`（INT gate 指针）
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.25 WA-T6）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave A · WA-T6）
  - `docs/WAVE_A_EXECUTION_PLAN.md`（P6 72%→84%）
  - `docs/tabular-mvp-release-checklist.md`（INT Tier-A 推荐一行）
- artifacts: Phase 6 INT gate contract v1
- verification:
  - `python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v` → **18/18 OK**
  - `python 04_Workflows/_wave7_regression_gate.py --tier A --pretty` → **ok: true**, 112 tests, exit 0
- behavior_notes: contract = Phase 6 SSOT；WAVE7 gate doc = implementation 附录；Tier-A 14 模块与 code 对齐
- deferred_items: nightly INT gate CI workflow；Tier-B 预留场景实装

---

## C_REPORT

- conclusion: <!-- Reviewer 填 -->
- blocking_issues:
- checks_summary:
- risk_level:
- suggestions:

---

## D_REPORT

- docs_updates:
- progress_entry:
- followup_suggestions:
