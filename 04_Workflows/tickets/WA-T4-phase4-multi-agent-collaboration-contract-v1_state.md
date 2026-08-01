# TICKET STATE · WA-T4 · Phase 4 Multi-Agent Collaboration Contract v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Phase 4（Multi-agent 协作）

---

## FRAME

- Title: WA-T4 · Phase 4 Multi-Agent Collaboration Contract v1
- Goal: 在 AGENTS.md + engineering-contract.mdc + W5-T0 三份 spec 之上，产出 Phase 4 级 multi-agent collaboration contract：四角色责任界线、标准工作流（拆票→实作→测试→回报）、routing 与交接约定，供 Wave B/C 直接引用。
- Scope:
  - 新建 `docs/phase4-multi-agent-collaboration-contract-v1.md`（§1–§8）
  - W5-T0 三 docs 文首 §0「上游 contract」指针
  - `.cursor/rules/multi_chat_roles.mdc` 文首单行指针
  - `04_Workflows/tickets/README.md` contract 与 ticket state 对齐说明
  - `04_Workflows/WORKFLOW_INDEX.md` · `docs/WAVE_PROGRESS_DASHBOARD.md` · `docs/WAVE_A_EXECUTION_PLAN.md`
  - 新建 `tests/test_phase4_multi_agent_contract_v1.py`（≥10 断言）
- NonScope:
  - **不**改 AGENTS.md · ENGINEERING_CONTRACT.md · HARNESS_CONSTITUTION.md 正文
  - **不**改任何既有 `*.py`（除新建 contract test）
  - **不**新增 agent 类型（Planner/Executor/Judge reserved）
  - **不**改 Cursor Subagents v0.1 派工三原则原文
  - **不**改 MVP 主链 / Gov core 脚本
  - **不**替换 W5-T0 三 docs；**不**改 ticket state 模板结构
- AllowedPaths:
  - `docs/phase4-multi-agent-collaboration-contract-v1.md`
  - `docs/multi-agent-collaboration-spec-v1.md`（§0 指针）
  - `docs/multi-agent-handoff-runbook-v1.md`（§0 指针）
  - `docs/multi-agent-replay-guide-v1.md`（§0 指针）
  - `.cursor/rules/multi_chat_roles.mdc`（文首一行）
  - `04_Workflows/tickets/README.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `docs/WAVE_A_EXECUTION_PLAN.md`
  - `tests/test_phase4_multi_agent_contract_v1.py`
  - `04_Workflows/tickets/WA-T4-phase4-multi-agent-collaboration-contract-v1_state.md`
- BlockedPaths:
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md`
  - 既有 `*.py`（除 `tests/test_phase4_multi_agent_contract_v1.py`）
  - `04_Workflows/tickets/_templates/*`
  - `core/*` · `scripts/run_mvp_mainline_regression.py` · `.github/workflows/*`
- Dependencies:
  - W5-T0 三 docs + state
  - `.cursor/rules/multi_chat_roles.mdc`
  - `04_Workflows/tickets/_templates/ticket_state.template.md`
  - 唯读：`AGENTS.md` · `.cursor/agents/DISPATCH_GUIDE.md`
- AcceptanceCriteria:
  - **AC-1**：contract 含 §1–§8
  - **AC-2**：§2 每角色含 may_do/must_not/inputs/outputs/done_when；与 mdc 零矛盾或标注 machine rule 优先
  - **AC-3**：§3 两条典型流程（单票四角色；O 并行 B/C + Scribe）
  - **AC-4**：§4 routing 含直派/governance-guard/stop_work（TEST-SUB-003）
  - **AC-5**：§5 冻结 FRAME/STATE/B/C/D 写入权限
  - **AC-6**：§7 W4-T2 replay 样板 + unittest 命令
  - **AC-7**：W5-T0 三 docs §0 指针
  - **AC-8**：test ≥10 断言
  - **AC-9**：Dashboard / WAVE_A_EXECUTION_PLAN WA-T4 done · Phase 4 75%→85%
  - **AC-10**：WORKFLOW_INDEX WA-T4 排在 W5-T0 之后并注明层级
- VerificationCommands:
  - `python -m unittest tests.test_phase4_multi_agent_contract_v1 -v`
  - 人工：打开 `04_Workflows/tickets/W4-T2-routing-eval-runner_state.md` 对照 contract §3

---

## STATE

- overall_status: in_progress
- current_owner: implementer
- next_action: Reviewer 对照 AC-1–AC-10 验收 contract 与 unittest
- last_updated: 2026-06-10 · implementer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `docs/phase4-multi-agent-collaboration-contract-v1.md`（新建）
  - `tests/test_phase4_multi_agent_contract_v1.py`（新建）
  - `docs/multi-agent-collaboration-spec-v1.md`（§0 指针）
  - `docs/multi-agent-handoff-runbook-v1.md`（§0 指针）
  - `docs/multi-agent-replay-guide-v1.md`（§0 指针）
  - `.cursor/rules/multi_chat_roles.mdc`（文首单行指针）
  - `04_Workflows/tickets/README.md`（contract 对齐表）
  - `04_Workflows/WORKFLOW_INDEX.md`（WA-T4 条目 + 层级）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Phase 4 75%→85%）
  - `docs/WAVE_A_EXECUTION_PLAN.md`（Phase 4 WA-T4 小节）
  - `04_Workflows/tickets/WA-T4-phase4-multi-agent-collaboration-contract-v1_state.md`
- artifacts: `docs/phase4-multi-agent-collaboration-contract-v1.md`
- verification:
  - `python -m unittest tests.test_phase4_multi_agent_contract_v1 -v` → **12/12 OK**
- behavior_notes:
  - contract 偏依赖假设+routing+关口，操作细节留在 W5-T0；与 mdc 冲突标注 **machine rule 优先**
  - §3 含 mermaid sequenceDiagram（流程 a）与 ASCII 并行图（流程 b）
  - §4 引用 TEST-SUB-003 stop_work 语义，未改 AGENTS 派工三原则原文
- deferred_items:
  - Reviewer AC 全项对照
  - Scribe Progress 末尾 append（可选）

---

## C_REPORT

- conclusion: **accepted**
- blocking_issues: 無
- checks_summary:
  - **AC-1 §1–§8 ✅**: `docs/phase4-multi-agent-collaboration-contract-v1.md` 含 §1–§8（grep 驗證）
  - **AC-2 四角色 ✅**: §2 表含 may_do/must_not/inputs/outputs/done_when；文首標 **machine rule 优先** 與 mdc 對齊
  - **AC-3 流程 ✅**: §3 含 sequenceDiagram + 並行 ASCII；`test_two_typical_flows_documented` 通過
  - **AC-4 routing ✅**: §4 含直派/governance-guard/stop_work（TEST-SUB-003）；`test_routing_decision_tree_paths` 通過
  - **AC-5 STATE 凍結 ✅**: §5 FRAME/STATE/B/C/D 寫入權限；`test_state_block_write_permissions_frozen` 通過
  - **AC-6 replay ✅**: §7 W4-T2 樣板 + unittest 命令；`test_replay_entry_w4_t2_reference` 通過
  - **AC-7 W5-T0 指针 ✅**: `test_w5_t0_docs_have_upstream_contract_pointer` 通過
  - **AC-8 unittest ✅**: `python -m unittest tests.test_phase4_multi_agent_contract_v1 -v` → **12/12 OK**
  - **AC-9/10 索引 ✅**: B_REPORT 已更新 WORKFLOW_INDEX · WAVE_PROGRESS_DASHBOARD · WAVE_A_EXECUTION_PLAN
  - **NonScope ✅**: AGENTS/合約/憲法正文未改；既有 `*.py` 未改（除新建 test）
- risk_level: low
- suggestions:
  - deferred：Scribe 可選 Progress 末尾 append Phase 4 contract 定稿條目（B_REPORT deferred_items）
  - deferred：Planner/Executor/Judge 仍 reserved — 未來角色擴展須另開 governance 票，不得 silent 增列

---

## D_REPORT

<!-- Scribe 填 -->
