# TICKET STATE · WB-T2 · tool-executor-and-sandbox-safety-contract-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal: 把 W3-TL-T3 executor、W6-T4/T8 experiment orchestrator、W12-T1 sandbox e2e 的执行模式收敛为 `docs/tool-executor-and-sandbox-safety-contract-v1.md`；定义 dry_run / plan_only / execute / sandbox_end_to_end 四级语义与 allowlist 矩阵。
- Scope:
  - 新增 contract SSOT + contract unittest（≥10 断言）
  - 更新 `docs/tabular-tool-outbox-spec.md` §0 指针
  - 更新 `docs/WAVE_PROGRESS_DASHBOARD.md` Phase 8.8 完成度 58%→82%
  - 更新 `04_Workflows/WORKFLOW_INDEX.md`
- NonScope:
  - 不改 `tools/tabular_tool_executor.py` / `scripts/run_agent_standard_case_experiment.py` allowlist / 暗部 `core/tool_executor.py`
  - 不实现 replay / 不扩大 sandbox allowlist / 不接外部 job runner
- AllowedPaths:
  - `docs/tool-executor-and-sandbox-safety-contract-v1.md`
  - `docs/tabular-tool-outbox-spec.md`
  - `tests/test_tool_executor_and_sandbox_contract_v1.py`
  - `04_Workflows/tickets/WB-T2-tool-executor-and-sandbox-safety-contract-v1_state.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
- BlockedPaths:
  - `tools/tabular_tool_executor.py`
  - `scripts/run_agent_standard_case_experiment.py`
  - `01_Environments/**/core/tool_executor.py`
  - `.github/workflows/*`（production gate 门槛）
- Dependencies: WB-T1（catalog/selector `tool_id` 权威 → 引用 W3-TL-T1/T2）· W3-TL-T3 · W6-T4/T8 · W12-T1 · WA-T3 P3.5 · WA-T6
- AcceptanceCriteria:
  - AC-1: contract §2 四级 execution_mode + allowlist 表
  - AC-2: contract §3 必填键 ok/message/tool_id/execution_mode/side_effects[]
  - AC-3: contract §4 outbox 仅 execute/sandbox_end_to_end
  - AC-4: tests.test_tool_executor_and_sandbox_contract_v1 全绿
  - AC-5: test_tabular_tool_executor · test_agent_standard_case_experiment · test_sandbox_delivery_bundle_v1 无回归
  - AC-6: contract §7 dry-run 命令可复制
  - AC-7: Dashboard Phase 8.8 58%→82%
  - AC-8: WA-T3 P3.5 execute optional/shadow
  - AC-9: contract §5 sandbox safety
  - AC-10: ticket state + B_REPORT 验证证据

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: 無（票面已收口；Toolchain Wave B closure complete）
- last_updated: 2026-06-11 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `docs/tool-executor-and-sandbox-safety-contract-v1.md`（新增）
  - `tests/test_tool_executor_and_sandbox_contract_v1.py`（新增）
  - `docs/tabular-tool-outbox-spec.md`（§0 指针 + sandbox 交叉引用）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Phase 8.8 58%→82%）
  - `04_Workflows/WORKFLOW_INDEX.md`（WB-T2 索引）
  - `04_Workflows/tickets/WB-T2-tool-executor-and-sandbox-safety-contract-v1_state.md`（本档）
- artifacts:
  - Phase 8.8 executor/sandbox safety contract SSOT
- verification:
  - `python -m unittest tests.test_tool_executor_and_sandbox_contract_v1 -v` → 16/16 OK
  - `python -m unittest tests.test_tabular_tool_executor tests.test_agent_standard_case_experiment tests.test_sandbox_delivery_bundle_v1 -v` → 无回归
- behavior_notes:
  - doc-only；ForbiddenChanges 遵守：未改 executor / orchestrator allowlist / 暗部 core
  - `tool_id` 权威引用 W3-TL-T1 JSON + WB-T1 依赖说明
  - contract §3 `execution_mode`/`side_effects` 为规范化契约；现实现仍返回 `dry_run` 布尔，映射表见 contract §3.2
- deferred_items:
  - subprocess `timeout=600s` 实装（contract §5.1 注记 follow-up）
  - WB-T4 outbox 可选 metrics 字段聚合

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: **无**（STATE 不一致为 Orchestrator 维护项，非交付 blocking）
- checks_summary:
  - **FRAME**：未被 Implementer 改动；四级 `execution_mode`、allowlist、outbox 写入条件、sandbox 边界与 AC 对齐。
  - **B_REPORT 证据**：`tests.test_tool_executor_and_sandbox_contract_v1` **16/16 OK**；回归 `test_tabular_tool_executor` + `test_agent_standard_case_experiment` + `test_sandbox_delivery_bundle_v1` **32/32 OK**。
  - **AC 对照**：§2 四级模式 + allowlist 表；§3 必填键；§4 outbox 仅 execute/sandbox_end_to_end；§5 sandbox safety；§7 可复制 dry-run 命令；Dashboard P8.8 58%→82%；doc-only，未改 executor / orchestrator allowlist / 暗部 core。
  - **Rule 5**：未触 BlockedPaths。
- risk_level: **low**
- suggestions:
  - **缺但可接受**：`execution_mode`/`side_effects` 为契约规范化；现实现仍用 `dry_run` 布尔（§3.2 映射表已说明）；subprocess `timeout=600s` 实装 follow-up。
  - **Orchestrator P1**：原 `overall_status: in_progress` 与同批 `review` 不一致 → 已对齐为 `accepted_with_gaps`。
  - 无 blocking；可交 Scribe。

---

## D_REPORT

- docs_updates:
  - Dashboard Toolchain 分栏 P8.8 状态列已对齐 `done · accepted_with_gaps`（WC-PRE-01）
  - `docs/tabular-tool-outbox-spec.md` §0 指针与 contract 交叉引用已交付（B_REPORT）
- progress_entry: WB-T2 交付 executor/sandbox safety contract SSOT（`tests.test_tool_executor_and_sandbox_contract_v1` 16/16 OK；回归 32/32 OK）；doc-only，未改 executor 实现。
- followup_suggestions:
  - **WC-PRE-03**：subprocess `timeout=600s` 实装（C_REPORT deferred）
  - 历史 STATE 不一致（in_progress vs implementer done）已于 2026-06-11 Orchestrator 对齐（WB-T8 closure）
