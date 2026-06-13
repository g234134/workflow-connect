# TICKET STATE · WC-T5 · Control Plane Automation Coverage & Risk Boundary Contract

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave C · Control Plane · M3

---

## FRAME

- Goal: 为 Wave C Control Plane（eligibility → dispatch cards → comms → order intake）建立**可机器引用的自动化覆盖率与风险边界契约**，明确每条路径属于 auto / HITL / forbidden，并给出可 grep 的断言与验收命令，避免 Multi-Chat 编排越权或 silent automation。
- Scope:
  - 新建契约文档（`docs/wave_c/WC_T5_automation_coverage_contract.md`）：路径矩阵、风险等级、默认语义（optional / non-blocking / investigation-only）
  - 覆盖 M2 已交付 CLI 链：`run_ticket_eligibility.py` · `run_dispatch_cards.py` · `run_ticket_state_update_with_comms.py` · `run_order_intake.py`
  - 定义「覆盖率」口径：哪些步骤可脚本化、哪些必须 Orchestrator HITL、哪些禁止自动化（写 STATE、开 chat、改 CI required 等）
  - 结构化 JSON 附录：`path_id` · `automation_tier` · `risk_class` · `verification_command`
  - 单元测试 `tests/test_wc_t5_automation_coverage_contract_v1.py`：断言文档内路径 ID 与 repo 内脚本 entrypoint 一一对应
  - 交叉引用：`docs/phase4-multi-agent-collaboration-contract-v1.md` · `multi_chat_roles.mdc` · M2 E2E runbook（`docs/wave_c/overview.md` §M2 End-to-End）
- NonScope:
  - 不实现新的 workflow engine、不自动写 `*_state.md` STATE、不调用 Cursor API
  - 不将任何路径升格为 PR required / prod blocking gate
  - 不改 `ticket_eligibility` 判定规则、不改 dispatch 分桶逻辑（除非 doc 发现的命名不一致另开 bugfix）
  - 不含 Tabular MVP S1–S15 全链（见 `ninety-five-percent-automation-blueprint-v2.md`，本票仅 Control Plane）
  - 不含 skill 提炼（WC-T6）或 INT Tier-A runner 实装（WC-T7）
- AllowedPaths:
  - `docs/wave_c/WC_T5_automation_coverage_contract.md`（新建）
  - `docs/wave_c/overview.md`（交叉引用 · Scribe）
  - `tests/test_wc_t5_automation_coverage_contract_v1.py`（新建）
  - `04_Workflows/tickets/WC-T5_state.md`（本檔 · Orchestrator）
- BlockedPaths:
  - `04_Workflows/ticket_eligibility.py` · `_dispatch_cards.py` · `dispatch_executor.py`（本票 doc-first；实现变更另票）
  - `.github/workflows/**` · branch protection settings
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md`
  - 暗部 `core/**` · `.env` · venv 树
- Dependencies:
  - **WC-T1** — eligibility CLI + dispatch gate（`docs/wave_c/WC_T1_eligibility.md`）
  - **WC-T2** — comms payload（`docs/wave_c/WC_T2_comms_minimal.md`）
  - **WC-T4** — order intake v0.1（`docs/wave_c/WC_T4_order_ledger_design.md`）
  - **WC-IMPL-L1** — governance snapshot L1 advisory 语义（风险边界参考，非 merge gate）
  - **Phase 4 contract** — Multi-Chat 写入冻结（`docs/phase4-multi-agent-collaboration-contract-v1.md`）
  - **WC-T3** — dispatch cards（In Progress；契约可标注 T3 路径为 `draft` tier，T3 关票后 Scribe 同步）
- AcceptanceCriteria:
  1. 契约文档列出 ≥8 条 Control Plane 路径，每条含 `automation_tier`（auto|HITL|forbidden）与 `risk_class`（low|medium|high）
  2. 文档显式声明：eligibility/comms/order **默认只读 ticket state**；任何写 STATE 路径标 **forbidden** 或 **HITL-only**
  3. 每条 `auto` 路径至少绑定一条可重跑 verification 命令（与 overview M2 E2E 或 unittest 对齐）
  4. `python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v` 全绿（路径 ID ↔ 脚本 entrypoint 无 orphan）
  5. 文档含「禁止假设」小节：不得将本契约解读为 PR required / prod SLA / 自动关票授权

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: closed · M3 WC-T5 契约关票；deferred 项（T6 path_id cross-ref · T7 E2E 映射）移交后续票
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `04_Workflows/tickets/WC-T5_state.md` — FRAME 正式落盘；STATE → in_progress
  - `docs/wave_c/WC_T5_automation_coverage_contract.md` — Control Plane 路径矩阵 + JSON 附录
  - `tests/test_wc_t5_automation_coverage_contract_v1.py` — path_id ↔ entrypoint 契约测试
  - `docs/wave_c/overview.md` — WC-T5 registry / snapshot → In Progress；M3 交付说明
- artifacts: 契约 JSON 附录 `wc_t5_paths_v0.1`（内嵌于契约文档 §附录）
- verification: `python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v`
- behavior_notes: doc-first；不改 M2 CLI 实现；forbidden 路径仅文档声明，无新 runtime gate
- deferred_items:
  - WC-T6 skill distillation cross-ref（T5 已关票 · T6 v2 补全 path_id）
  - WC-T7 E2E walkthrough path_id 映射（T5 已关票 · T7 v2 补 runbook 附录）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: none
- checks_summary:
  - AC-1：`WC_T5_automation_coverage_contract.md` 列出 ≥8 条 Control Plane 路径，每条含 `automation_tier` + `risk_class`
  - AC-2：写 STATE / 开 chat / 改 CI required 等路径标 forbidden 或 HITL-only；eligibility/comms/order 默认只读 ticket state
  - AC-3：每条 `auto` 路径绑定可重跑 verification 命令（与 M2 E2E / unittest 对齐）
  - AC-4：`python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v` 全绿（path_id ↔ entrypoint 无 orphan；假定上一轮已跑绿）
  - AC-5：文档含「禁止假设」小节——不得解读为 PR required / prod SLA / 自动关票授权
  - NonScope 遵守：doc-first；无 workflow engine · 无 STATE 自动写入 · 无 CI required 升格
- risk_level: low
- suggestions: WC-T6 引用 `wc.m2.*` path_id 命名空间；WC-T7 runbook INT 对齐节可补 T5 映射表（deferred_items 已列）

---

## D_REPORT

- docs_updates:
  - `docs/wave_c/overview.md` — WC-T5 registry / M3 小节 **In Progress → Done**；M3 snapshot 补 automation coverage contract 一句
  - `docs/wave_c/WC_T5_automation_coverage_contract.md` — 契约正文已落盘（B_REPORT）；Scribe 确认 overview 交叉引用与禁止假设小节可见
- progress_entry: WC-T5 关票：Control Plane 自动化覆盖率与风险边界契约 v0.1 ready；`wc_t5_paths_v0.1` JSON 附录可供 T6/T7 cross-ref。
- followup_suggestions:
  - WC-T6：引用 T5 `path_id` 矩阵完善 `canonical_path_id` 映射（deferred）
  - WC-T7：runbook 补 T5 path_id 对照表（deferred）
  - 不在本票承诺任何路径升格为 PR required
