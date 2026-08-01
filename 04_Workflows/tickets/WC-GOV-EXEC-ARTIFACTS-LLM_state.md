# TICKET STATE · WC-GOV-EXEC-ARTIFACTS-LLM · Control Plane 自动化升格治理契约（FRAME）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave C · Control Plane · Lane C · **M4 Governance**（doc-only · FRAME 冻结）  
> 父上下文：**WC-T6-T7-v2**（`accepted_with_gaps` · NonScope deferred 为本票输入）· **WC-T5**（`wc.m2.*` automation_tier SSOT）  
> 索引：`docs/WAVE_PROGRESS_DASHBOARD.md` §多 Lane 本輪收口 · `docs/wave_c/overview.md` §M3 self-check

---

## FRAME

- Goal: 为 WC-T6-T7-v2 遗留的四类 deferred 行为（`--execute` 写 live STATE · 生产 `artifacts/**` 扫描 / `--json-out` 落盘 · LLM distillation / 自动写 `.cursor/skills` · Control Plane E2E 升格 PR required / mandatory CI / INT Tier-A）建立**分级治理契约（CP-AUTO L0→L3）**与升格门槛，明确「在何种守门下可从 forbidden 过渡为 allowlisted optional」，以及**本票完成后仍保持 forbidden** 的硬边界；**本票仅交付治理 FRAME + SSOT 文档，不含任何脚本或 CI 施工**。
- Scope:
  - **治理 SSOT（本票主交付）**
    - 新建 `docs/governance/WC_GOV_EXEC_ARTIFACTS_LLM_governance_contract.md`（建议名；Scribe 可微调），定义 **CP-AUTO L0 / L1 / L2 / L3** 四级语义、升格门槛、观察期、rollback、审计留痕位点
    - 维护本 state 檔 FRAME/STATE；Orchestrator 冻结后供后续实施票（`WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L1` 等）引用
  - **纳入场景（契约层定义，非本票开启）**
    | 行为域 | L1 允许场景（契约草案） | L2 允许场景（须批文 + 观察期） |
    |--------|-------------------------|--------------------------------|
    | `--execute` 写 STATE | 仅 **demo 票**（`WC-DEMO-1` 等 allowlist）· 仅 **sandbox artifacts root**（`artifacts/e2e/**`）· 默认仍 dry-run；L1 仅允许写 **B_REPORT 草稿区** 至 **隔离副本**（非 live `04_Workflows/tickets/*_state.md`） | allowlisted demo 票 + Orchestrator **一次性批准 token**；可写 **FRAME 禁止区以外的 STATE 字段**（`status_by_role` · `next_action`）；**仍禁止**改 FRAME / C_REPORT / D_REPORT |
    | `artifacts/**` 扫描 | 仅 `artifacts/e2e/**` · `tests/fixtures/skill_distillation/**` · `artifacts/control_plane/`（只读 · 增量索引 manifest） | 扩展至 `artifacts/control_plane/**` 生产样例 + dedup；**仍禁止**扫 `order_ledger` 生产队列 · 暗部 outbox · 含 PII 路径 |
    | `--json-out` 落盘 | 仅 sandbox 路径（`artifacts/e2e/` · `artifacts/control_plane/skill_distillation.sandbox.json`）；保留期 ≤14 日 · 不得进 git tracked 默认路径 | allowlisted 路径 + retention 策略文档化；**仍禁止**落盘至 repo 根或 `04_Workflows/tickets/` |
    | LLM / skills | **L0–L2 均禁止** LLM 调用与自动写 `.cursor/skills`；L1 仅允许 **本地启发式**（延续 WC-T6 v0.1） | L2 允许 **advisory-only** LLM 摘要至 stdout / sandbox JSON（人工审阅闸门）；**仍禁止**无人值守写 skills 或 rules |
    | CI / gate 升格 | **L0–L2 均禁止** PR required · mandatory CI · INT Tier-A 绑定 | L3 **独立子契约**（见 NonScope）；须尚書省 `approval_status.CP_AUTO_L3=approved` |
  - **与现有票关系**
    | 票号 | 关系 |
    |------|------|
    | **WC-T6 / WC-T7 / WC-T6-T7-v2** | 本票 **承接** v2 NonScope deferred 四项；**不修改** v2 已验收交付；v2 C_REPORT gaps 在本票 FRAME 获批后才有升格路径 |
    | **WC-T5** | `wc.m2.state.write_ticket` · `wc.m2.chat.open_cursor` 在 L0–L2 **保持 forbidden**；本票仅提案 L2 下 **子集字段** 的 `automation_tier` 修正案（doc-only），**须** `WA-T5-AMEND-*` 或 WC-T5 v0.2 独立票才改 JSON 附录 |
    | **WC-PRE-06 / WC-PRE-07 / WC-IMPL-L2** | **分轨**：toolchain health / smoke mandatory CI；**不得**与本票 CP-AUTO L3 混票或捆绑升格 |
    | **WC-IMPL-SMOKE-CI-L1** | Wave C nightly smoke 仍为 optional；本票 L3 若提案 Control Plane E2E 进 CI，**须**独立挂载点与 rollback，不占用 toolchain smoke 白名单 |
    | **W5-T2 / WA-T4** | HITL checkpoint 与四角色 STATE 写入冻结为本票 **硬约束**；L2 `--execute` 不得绕过 Reviewer / Scribe 关口 |
  - **Joint（Orchestrator / Scribe 收口）**
    - FRAME 冻结后更新 `docs/wave_c/overview.md` M4 治理行（一句 · 链至本票）
    - Progress **末尾** append 治理契约索引（Scribe · D_REPORT）
- NonScope / Forbidden:
  - **本票禁止任何实作**：不改 `scripts/*` · `tests/*` · `.github/workflows/**` · branch protection · live `*_state.md`
  - **L0–L2 恒 forbidden（本票 FRAME 完成后仍禁止，除非 L3 子票 + 批文）**
    - runner `--execute` **全自动**写 live `04_Workflows/tickets/*_state.md`（含 FRAME / STATE / C_REPORT / D_REPORT）
    - 对 **prod 队列表**（非 demo allowlist）的任何自动 STATE 变更
    - `wc.m2.chat.open_cursor` 及任何 Cursor API 自动开 chat
    - 无人值守 LLM 调用 · embedding · 外部 API；自动 PR 写 `.cursor/skills` 或 `.cursor/rules/**`
    - 扫描暗部路径 · `order_ledger` 生产账本 · 含凭证/PII 的 artifacts
    - 将 Control Plane E2E / nightly pass **等同** INT Tier-A pass
    - 将 CP-AUTO 升格与 **WC-PRE-06/07 L2** 或 **P3.5 mandatory trio** 捆绑为单票施工
  - **L3（PR required / mandatory CI / INT Tier-A）**
    - 本票 FRAME **可定义** L3 门槛与 rollback 草案；**禁止**在本票直接改 workflow required 或 INT gate 表
    - L3 启用须：`approval_status.CP_AUTO_L3=approved` + 独立实施票（`WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L3` 或 `WA-T6-AMEND-CP-E2E-CI`）+ rollback 演练留痕
  - 推翻 WC-T6 v0.1 本地只读启发式底线（无网络 · 无写回）作为 **L0 默认**
- AllowedPaths:
  - **Orchestrator / Scribe（本票）**
    - `docs/governance/WC_GOV_EXEC_ARTIFACTS_LLM_governance_contract.md`（新建 · SSOT）
    - `04_Workflows/tickets/WC-GOV-EXEC-ARTIFACTS-LLM_state.md`（本檔）
    - `docs/wave_c/overview.md`（仅 M4 治理索引行 · 一句 cross-ref）
    - `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append** · Scribe）
  - **只读引用（不得在本票修改正文）**
    - `docs/wave_c/WC_T5_automation_coverage_contract.md`
    - `docs/wave_c/WC_T6_skill_distillation_lite.md`
    - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`
    - `docs/governance/WC_PRE_06_07_rollout_plan.md`
    - `docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md`（分轨对照）
    - `docs/phase4-multi-agent-collaboration-contract-v1.md`
    - `.cursor/rules/multi_chat_roles.mdc`（角色边界引用）
- BlockedPaths:
  - `scripts/run_wc_m2_e2e_walkthrough.py` · `scripts/distill_control_plane_skills_lite.py` · 一切 `scripts/*` 与 `tests/*`（**实施票**范围）
  - `.github/workflows/**` · branch protection / GitHub Environments
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md` · `.cursor/rules/**`（须 governance-guard 另票）
  - `core/**` · 暗部 `01_Environments/**` · `.env`
  - `04_Workflows/ticket_eligibility.py` · `_dispatch_cards.py` · `dispatch_executor.py` · `order_ledger/**`
  - live `04_Workflows/tickets/*_state.md`（本票 state 除外）
  - `.cursor/skills/**`（任何自动写入）
- Dependencies:
  - **WC-T6-T7-v2** — done · `accepted_with_gaps`；deferred 枚举为本票输入（**必完成**）
  - **WC-T5** — `docs/wave_c/WC_T5_automation_coverage_contract.md` · `wc_t5_paths_v0.1`（path_id / automation_tier SSOT）
  - **WC-T6 / WC-T7** v0.1+v2 — distill CLI · E2E runbook · nightly smoke 语义（**必引用**）
  - **WC-T1-INTEGRATION** — eligibility gate 已接入；**建议** Reviewer 关票后再开 CP-AUTO L1 实施票（非本票阻塞）
  - **W4-MEM-01** — case history；**建议** Reviewer 关票（非本票阻塞）
  - **WA-T4** — Phase 4 四角色 STATE 写入冻结（**硬约束**）
  - **W5-T2 / W5-T2B** — HITL checkpoint A/B 契约（`--execute` 不得绕过）
  - **WC-PRE-06/07 · WC-IMPL-L2** — toolchain L2 分轨；本票 **不得**依赖其批文作为 CP-AUTO L1/L2 前置
  - **尚書省批文** — CP-AUTO L2 观察期启动 · CP-AUTO L3 任何 CI/INT 升格（**本票 FRAME 不替代批文**）
- AcceptanceCriteria:
  - **AC-GOV-1（分级契约）**: `WC_GOV_EXEC_ARTIFACTS_LLM_governance_contract.md` 存在且定义 **CP-AUTO L0 / L1 / L2 / L3**；每级含：允许行为 · 禁止行为 · 环境边界（sandbox / demo only）· 默认语义（optional / non-blocking）
  - **AC-GOV-2（deferred 映射表）**: 契约含 **Deferred → Tier** 对照表，覆盖四项输入；每项标明「本票 FRAME 完成后」状态：`仍 forbidden` | `L1 下 allowlisted optional` | `L2 下 allowlisted + HITL-reduced` | `L3 提案 only`
  - **AC-GOV-3（allowlist & 审计）**: L1/L2 各有 **ticket allowlist**（至少含 `WC-DEMO-1`）· **artifacts root allowlist** · **审计 log 最低字段**（`run_id` · `path_id` · `tier` · `operator` · `rollback_ref` · `ok`）
  - **AC-GOV-4（rollback）**: 契约含 **L1→L0** · **L2→L1** rollback playbook（文档级）；含「误写 live STATE」应急步骤（HITL 手工恢复 · Progress 留痕）
  - **AC-GOV-5（升格门槛）**: L1→L2 · L2→L3 各 ≥3 条可验证门槛（例：demo E2E dry-run 连续 N 次 ok · 零 P0 mis-write · 观察期天数）；**不得**写成已满足
  - **AC-GOV-6（分轨声明）**: 契约 **三处** 声明：Control Plane E2E / nightly **≠** INT Tier-A；CP-AUTO L3 **≠** WC-PRE-06/07 toolchain L2；`wc.m2.state.write_ticket` 在 L0–L2 不全量升格
  - **AC-GOV-7（WC-T5 修正案）**: 契约含 **doc-only** 提案：L2 下哪些 STATE 字段可标 `HITL-reduced`（非 `auto`）；**不**直接改 `wc_t5_paths_v0.1` JSON
  - **AC-GOV-8（FRAME 冻结）**: Reviewer 确认本票 NonScope 含「无脚本/CI 施工」；`overall_status` 达 `frame_frozen` 或 `design_ready` 后方可开 `*-IMPL-L1` 实施票
  - **AC-GOV-9（索引收口）**: `docs/wave_c/overview.md` 有 M4 一行指向本票；Progress 末尾有 Scribe 摘要（D_REPORT）
- **需审批／批文**:
  - **本票 FRAME**：**否**（doc-only · non-gating · 定义升格路径）
  - **CP-AUTO L2 观察期启动**：**是**（`approval_status.CP_AUTO_L2=approved`）
  - **CP-AUTO L3（PR required / INT Tier-A）**：**是**（`approval_status.CP_AUTO_L3=approved` · 独立实施票）

### Deferred 过渡一览（本票 FRAME 获批后的治理结论）

> **读表须知**：下表为 **治理契约目标态**；非宣称 L1/L2 已开启。实施须另开 `*-IMPL-*` 票。

| Deferred 项（来源：WC-T6-T7-v2 NonScope） | FRAME 完成后：可过渡为「守门下允许」 | FRAME 完成后：仍 forbidden |
|--------------------------------------------|--------------------------------------|---------------------------|
| runner `--execute` 全自动写 live `*_state.md` | **L1**：仅 demo 票 + sandbox 副本写 B_REPORT 草稿（非 live path）· optional nightly · 审计 log · rollback | live `04_Workflows/tickets/*_state.md` 全自动写 FRAME/STATE/C/D；prod 队列表；无 token 的 L2 写 STATE |
| 生产 `artifacts/**` 增量扫描 | **L1**：`artifacts/e2e/**` + fixtures 只读索引 · **L2**（批文后）：`artifacts/control_plane/**` + dedup manifest | 暗部 outbox · order_ledger 生产 · 含 PII/凭证路径；无 retention 的落盘 |
| `--json-out` 落盘样本 | **L1**：sandbox 路径（`artifacts/e2e/` · `*.sandbox.json`）· 保留期 ≤14 日 | git tracked 默认路径 · `04_Workflows/tickets/` · 无审计的落盘 |
| LLM distillation / 自动写 `.cursor/skills` | **无**（L0–L2 保持 WC-T6 本地启发式）；**L2 批文后**仅 advisory stdout/JSON · 人工审阅闸门 | 无人值守 LLM/embedding/外部 API；自动 PR 写 `.cursor/skills` 或 `.cursor/rules/**` |
| 升格 PR required / mandatory CI / INT Tier-A | **L3 提案 only**（门槛 + rollback 草案 · 独立实施票） | 本票或 L1/L2 实施票 **不得**改 `.github/workflows` required · 不得宣稱 E2E pass = INT Tier-A |

---

## STATE

- overall_status: frame_frozen
- current_owner: orchestrator
- next_action: Orchestrator 确认 FRAME 冻结；可开 `WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L1`（须 Reviewer 关本票 C_REPORT）
- last_updated: 2026-06-14 · scribe + reviewer
- status_by_role:
  - orchestrator: pending
  - implementer: n/a
  - reviewer: done
  - scribe: done

---

## B_REPORT

<!-- pending -->

---

## C_REPORT

- conclusion: **frame_ready**
- verdict: frame_ready
- risk_level: low
- blocking_issues: 無
- checks_summary: |
  **AC-GOV-1（分级契约）**: ✓ `docs/governance/WC_GOV_EXEC_ARTIFACTS_LLM_governance_contract.md` 定义 CP-AUTO L0/L1/L2/L3；每级含允许/禁止/守门/环境边界；默认 optional · non-blocking。
  **AC-GOV-2（deferred 映射表）**: ✓ §3 对照表覆盖 WC-T6-T7-v2 五项 deferred（含 CI/INT 升格）；状态标签与 FRAME 一致。
  **AC-GOV-3（allowlist & 审计）**: ✓ §4 ticket/artifacts allowlist + 审计 log 六必填字段（`run_id` · `path_id` · `tier` · `operator` · `rollback_ref` · `ok`）。
  **AC-GOV-4（rollback）**: ✓ §5.3 L1→L0 · L2→L1 playbook + 误写 live STATE 应急步骤。
  **AC-GOV-5（升格门槛）**: ✓ §5.1 L1→L2 · §5.2 L2→L3 各 ≥4 条可验证门槛；已标注「不得解读为已满足」。
  **AC-GOV-6（分轨声明）**: ✓ §6 三处声明：E2E/nightly ≠ INT Tier-A；CP-AUTO L3 ≠ WC-PRE-06/07 L2；write_ticket L0–L2 不全量升格。
  **AC-GOV-7（WC-T5 修正案）**: ✓ §7 doc-only 提案 HITL-reduced 子集字段；未改 `wc_t5_paths_v0.1` JSON。
  **AC-GOV-8（FRAME 冻结）**: ✓ §1.4 明示「本票不做任何实作」；NonScope 与合約文一致；`overall_status=frame_frozen`。
  **AC-GOV-9（索引收口）**: ✓ `docs/wave_c/overview.md` M4 一行已链至本契约；Progress 末尾 Scribe 摘要见 D_REPORT。
  **WC-T5 forbidden 对齐**: ✓ `wc.m2.state.write_ticket` · `wc.m2.chat.open_cursor` L0–L2 保持 forbidden；与 `WC_T5_automation_coverage_contract.md` §4 无冲突。
  **工程合約对齐**: ✓ doc-only 票；未触 AGENTS Subagents 派工禁改制度档；STATE 写入红線（FRAME/C/D 禁止自动写）已写入 §2.3 · §5.3 应急。
- ContractMismatch: 無
- MissingConstraints: 無 blocking；建议 IMPL-L1 票 FRAME 引用 §4.1 扩展 demo 票列表流程（非本票阻塞）
- Ambiguities: L2「一次性批准 token」格式留待 IMPL-L2 票定义（本 FRAME 已标注 token_ref 审计字段，可接受 deferred）
- GovernanceConcerns: CP-AUTO L3 与 toolchain L2 分轨已三处声明；升格不得捆绑 PRE-06/07 — 已覆盖
- frame_frozen: **是** — FRAME 可冻结；**可开后续 IMPL 票**：`WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L1`（L1 · 无批文）；L2/L3 须对应批文
- reviewed_by: reviewer（同 Scribe 轮治理设计）
- reviewed_at: 2026-06-14

---

## D_REPORT

- docs_updates:
  - `docs/governance/WC_GOV_EXEC_ARTIFACTS_LLM_governance_contract.md` — 新建 CP-AUTO L0→L3 治理 SSOT（§1–10）
  - `docs/wave_c/overview.md` — M4 治理行（一句 · 链至本契约与本票 state）
  - `04_Workflows/tickets/WC-GOV-EXEC-ARTIFACTS-LLM_state.md` — STATE · C_REPORT · D_REPORT 收口
- progress_entry: WC-GOV-EXEC-ARTIFACTS-LLM Scribe+Reviewer：CP-AUTO 分级契约 FRAME 落盘；Reviewer **frame_ready** · risk **low**；承接 WC-T6-T7-v2 deferred 四项；**本票无脚本/CI 施工**。
- followup_suggestions:
  - Orchestrator 确认 `overall_status=frame_frozen` 后开 `WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L1`
  - L2 观察期须 `approval_status.CP_AUTO_L2=approved`；L3 须 `CP_AUTO_L3=approved` + 独立子票
  - WC-T5 JSON 修正案走 `WA-T5-AMEND-*`，不随 L1 实施票捆绑
