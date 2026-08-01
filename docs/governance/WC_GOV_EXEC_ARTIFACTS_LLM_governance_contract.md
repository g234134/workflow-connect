# WC-GOV-EXEC-ARTIFACTS-LLM · Control Plane 自动化升格治理契约（CP-AUTO）

> **票号**：WC-GOV-EXEC-ARTIFACTS-LLM  
> **版本**：v0.1 · FRAME · 2026-06-14  
> **性质**：**doc-only · 治理 SSOT** — 定义升格路径与硬边界；**不含任何脚本、CI、branch protection 或 live STATE 施工**  
> **票 state SSOT**：`04_Workflows/tickets/WC-GOV-EXEC-ARTIFACTS-LLM_state.md`  
> **父输入**：WC-T6-T7-v2 NonScope deferred 四项 · WC-T5 `wc.m2.*` automation_tier SSOT

---

## 1. 简介

### 1.1 目的

为 WC-T6-T7-v2 遗留的四类 deferred 行为建立**分级治理契约（CP-AUTO L0→L3）**：

1. runner `--execute` 写 live `*_state.md`
2. 生产 `artifacts/**` 增量扫描 / `--json-out` 落盘
3. LLM distillation / 自动写 `.cursor/skills`
4. Control Plane E2E 升格 PR required / mandatory CI / INT Tier-A

本契约回答：**在何种守门下可从 `forbidden` 过渡为 allowlisted optional**，以及 **FRAME 冻结后仍恒 forbidden 的硬边界**。

### 1.2 与 WC-T6-T7-v2 的关系

| 项 | 关系 |
|----|------|
| **WC-T6-T7-v2** | 已 `accepted_with_gaps`；v0.1 gaps 已关；NonScope deferred 为本契约**唯一输入枚举** |
| **本契约** | **承接** deferred 四项的升格路径定义；**不修改** v2 已验收交付（scripts / tests / runbook 正文） |
| **升格生效** | 须另开 `WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L*` 实施票；本 FRAME **不开启**任何自动化行为 |

### 1.3 与 WC-T5 的关系

| 项 | 关系 |
|----|------|
| **WC-T5 SSOT** | `docs/wave_c/WC_T5_automation_coverage_contract.md` · 附录 `wc_t5_paths_v0.1` |
| **L0–L2 默认** | `wc.m2.state.write_ticket` · `wc.m2.chat.open_cursor` **保持 `forbidden`**（与 WC-T5 一致） |
| **L2 修正案（doc-only）** | 本契约 §7 提案 L2 下 **子集 STATE 字段** 可标 `HITL-reduced`；**不**直接改 JSON 附录 |
| **JSON 变更** | 须 `WA-T5-AMEND-*` 或 WC-T5 v0.2 独立票 + Reviewer 关票 |

### 1.4 本票边界声明（必读）

> **本票（WC-GOV-EXEC-ARTIFACTS-LLM）不做任何实作。**

禁止在本票内修改：

- `scripts/*` · `tests/*` · `.github/workflows/**`
- branch protection / GitHub Environments
- live `04_Workflows/tickets/*_state.md`（本票 state 除外）
- `wc_t5_paths_v0.1` JSON 附录

本契约仅为 **治理 FRAME + SSOT 文档**；任何行为变更须独立实施票 + 对应批文。

---

## 2. CP-AUTO 等级说明（L0 / L1 / L2 / L3）

> **默认语义（L0–L2）**：optional · non-blocking · investigation-only · sandbox/demo only  
> **L3**：独立子契约；须尚書省 `approval_status.CP_AUTO_L3=approved`

### 2.1 L0 · Baseline（当前默认）

| 维度 | 定义 |
|------|------|
| **定位** | WC-T6 v0.1 本地只读启发式底线：**无网络 · 无写回 · 无 LLM** |
| **允许** | 现有 dry-run CLI；fixtures / cards / comms / reports 只读扫描；stdout 输出 |
| **禁止** | 任何 `--execute` 写 STATE；生产 artifacts 扫描；`--json-out` 落盘至非 sandbox；LLM / embedding / 外部 API；自动写 `.cursor/skills` 或 `.cursor/rules/**`；PR required / mandatory CI / INT Tier-A 绑定 |
| **守门** | WC-T5 `forbidden` 路径有效；W5-T2 / WA-T4 四角色 STATE 写入冻结；HITL checkpoint A/B 不可绕过 |
| **环境** | 本地 dev · fixtures · `tests/fixtures/**` |

### 2.2 L1 · Allowlisted Optional（sandbox · demo only）

| 维度 | 定义 |
|------|------|
| **定位** | 在 **demo 票 + sandbox artifacts root** 下，允许 **optional · non-blocking** 的隔离副本写入与只读索引 |
| **允许** | 见 §4 allowlist；`--execute` 仅写 **B_REPORT 草稿** 至 **隔离副本**（非 live `*_state.md`）；`artifacts/e2e/**` · fixtures 只读索引；sandbox `--json-out`（保留期 ≤14 日） |
| **禁止** | 写 live `04_Workflows/tickets/*_state.md`（含 FRAME / STATE / C_REPORT / D_REPORT）；prod 队列表 STATE 变更；`wc.m2.chat.open_cursor`；任何 LLM / 外部 API；扫暗部 · order_ledger 生产 · PII/凭证路径；PR required / mandatory CI / INT Tier-A |
| **守门** | ticket allowlist（至少 `WC-DEMO-1`）；artifacts root allowlist；审计 log 最低字段（§4.3）；默认仍 dry-run；nightly optional |
| **环境** | `artifacts/e2e/**` · `tests/fixtures/skill_distillation/**` · demo 票 only |

### 2.3 L2 · HITL-Reduced（批文 + 观察期）

| 维度 | 定义 |
|------|------|
| **定位** | 尚書省 `approval_status.CP_AUTO_L2=approved` 后，在 L1 基础上 **缩小 HITL 范围**（非全量 `auto`） |
| **允许** | allowlisted demo 票 + Orchestrator **一次性批准 token**；可写 FRAME 禁止区以外的 STATE 子集字段（`status_by_role` · `next_action`）；扩展 `artifacts/control_plane/**` 生产样例 + dedup manifest；advisory-only LLM 摘要至 stdout / sandbox JSON（**人工审阅闸门**） |
| **禁止** | 改 FRAME / C_REPORT / D_REPORT；无 token 的 L2 STATE 写入；无人值守 LLM / embedding / 外部 API；自动 PR 写 `.cursor/skills` 或 `.cursor/rules/**`；扫 order_ledger 生产 · 暗部 outbox · PII/凭证；`--json-out` 至 repo 根或 `04_Workflows/tickets/`；PR required / mandatory CI / INT Tier-A |
| **守门** | L2 批文 + 观察期（§5.1）；Reviewer / Scribe 关口不可 bypass（W5-T2 / WA-T4）；rollback playbook 就绪（§5.3） |
| **环境** | L1 sandbox + 文档化 retention 的 allowlisted 路径 |

### 2.4 L3 · CI / INT 升格（独立子契约）

| 维度 | 定义 |
|------|------|
| **定位** | Control Plane E2E / nightly **升格** PR required / mandatory CI / INT Tier-A 的**提案层**；与本票 L0–L2 **分轨** |
| **允许（提案 only）** | 定义升格门槛 · rollback 草案 · 独立挂载点设计；**不**在本 FRAME 或 L1/L2 实施票直接改 workflow |
| **禁止** | 本票 / L1/L2 实施票改 `.github/workflows/**` required；宣稱 E2E pass = INT Tier-A pass；与 WC-PRE-06/07 L2 或 P3.5 mandatory trio **捆绑为单票施工** |
| **守门** | 尚書省 `approval_status.CP_AUTO_L3=approved` + 独立实施票（`WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L3` 或 `WA-T6-AMEND-CP-E2E-CI`）+ rollback 演练留痕 |
| **环境** | CI / branch protection — **仅 L3 子票范围** |

### 2.5 等级对照速查

| 行为域 | L0 | L1 | L2 | L3 |
|--------|----|----|----|-----|
| `--execute` 写 STATE | 禁止 | 隔离副本 B_REPORT 草稿 only | token + 子集字段 | 子契约定义 |
| `artifacts/**` 扫描 | fixtures only | e2e + fixtures 只读索引 | + control_plane/** dedup | 子契约定义 |
| `--json-out` | 禁止落盘 | sandbox ≤14 日 | allowlisted + retention 文档化 | 子契约定义 |
| LLM / skills | 禁止 | 本地启发式 only | advisory stdout/JSON + 人工闸门 | 仍禁止无人值守写 skills |
| CI / INT gate | 禁止 | 禁止 | 禁止 | 提案 + 独立子票 |

---

## 3. Deferred 映射表（WC-T6-T7-v2 NonScope → CP-AUTO）

> **读表须知**：下表为 **治理契约目标态**；**非宣称 L1/L2 已开启**。实施须另开 `*-IMPL-*` 票 + 对应批文。

| Deferred 项（来源：WC-T6-T7-v2 NonScope） | FRAME 完成后：可过渡为「守门下允许」 | FRAME 完成后：仍 forbidden |
|--------------------------------------------|--------------------------------------|---------------------------|
| runner `--execute` 全自动写 live `*_state.md` | **L1**：demo 票 + sandbox 副本写 B_REPORT 草稿 · optional nightly · 审计 log · rollback | live `04_Workflows/tickets/*_state.md` 全自动写 FRAME/STATE/C/D；prod 队列表；无 token 的 L2 STATE 写入 |
| 生产 `artifacts/**` 增量扫描 | **L1**：`artifacts/e2e/**` + fixtures 只读索引 · **L2**（批文后）：`artifacts/control_plane/**` + dedup manifest | 暗部 outbox · order_ledger 生产 · 含 PII/凭证路径；无 retention 的落盘 |
| `--json-out` 落盘样本 | **L1**：sandbox 路径（`artifacts/e2e/` · `*.sandbox.json`）· 保留期 ≤14 日 | git tracked 默认路径 · `04_Workflows/tickets/` · 无审计的落盘 |
| LLM distillation / 自动写 `.cursor/skills` | **无 L1 路径**（L0–L2 保持 WC-T6 本地启发式）；**L2 批文后**仅 advisory stdout/JSON · 人工审阅闸门 | 无人值守 LLM/embedding/外部 API；自动 PR 写 `.cursor/skills` 或 `.cursor/rules/**` |
| 升格 PR required / mandatory CI / INT Tier-A | **L3 提案 only**（门槛 + rollback 草案 · 独立实施票） | 本票或 L1/L2 实施票 **不得**改 `.github/workflows` required · 不得宣稱 E2E pass = INT Tier-A |

### 3.1 映射状态枚举（AC-GOV-2）

| 状态标签 | 含义 |
|----------|------|
| `仍 forbidden` | FRAME 完成后默认；L3 子票 + 批文前不可改 |
| `L1 下 allowlisted optional` | 须 `*-IMPL-L1` 票 + demo/sandbox allowlist |
| `L2 下 allowlisted + HITL-reduced` | 须 `approval_status.CP_AUTO_L2=approved` + `*-IMPL-L2` 票 |
| `L3 提案 only` | 本 FRAME 可定义门槛；实施须 L3 子票 |

---

## 4. Allowlist 与审计

### 4.1 Ticket Allowlist

| 级别 | 票号 allowlist | 说明 |
|------|----------------|------|
| **L1** | `WC-DEMO-1`（**最低要求**） | 可扩展至 Orchestrator 文档化 demo 票列表；**不得**含 prod 队列表票 |
| **L2** | L1 列表 + Orchestrator **一次性批准 token** 绑定的单票 | token 过期即回退 L1 语义 |

**恒 forbidden 票类**：非 demo allowlist 的 prod 队列表；任何须 Reviewer 关票的 live 生产票（除非 L3 子契约另定义且批文）。

### 4.2 Artifacts Root Allowlist

| 级别 | 路径 | 模式 |
|------|------|------|
| **L1** | `artifacts/e2e/**` | 读写（B_REPORT 隔离副本 · `--json-out`） |
| **L1** | `tests/fixtures/skill_distillation/**` | 只读索引 |
| **L1** | `artifacts/control_plane/` | 只读 · 增量索引 manifest |
| **L1** | `artifacts/control_plane/skill_distillation.sandbox.json` | sandbox JSON 落盘 |
| **L2** | `artifacts/control_plane/**` | 扩展生产样例 + dedup manifest |
| **恒 forbidden** | 暗部 outbox · `order_ledger/**` 生产队列 · 含 PII/凭证路径 · repo 根 · `04_Workflows/tickets/` |

### 4.3 审计 Log 最低字段

L1 / L2 任何 allowlisted 自动化运行 **必须**产出结构化审计记录（JSONL 或等价 artifact）：

| 字段 | 必填 | 说明 |
|------|------|------|
| `run_id` | 是 | 单次运行 UUID 或 ISO 时间戳复合 id |
| `path_id` | 是 | WC-T5 `wc.m2.*` 或 CP 扩展 id |
| `tier` | 是 | `CP-AUTO-L0` … `L3` |
| `operator` | 是 | 人工操作者或 HITL 批准人标识 |
| `rollback_ref` | 是 | 对应 rollback playbook 版本 / ticket id |
| `ok` | 是 | `true` / `false` |
| `ticket_id` | L1+ 推荐 | allowlisted 票号 |
| `artifacts_root` | L1+ 推荐 | 实际写入根路径 |
| `approval_token_ref` | L2 必填 | 一次性 token 引用（非 secret 原文） |

**禁止**：审计 log 含 secret / token 原文 / PII；须符合 AGENTS §红线与憲法 §7.3。

---

## 5. 升格与 Rollback

> **诚实边界**：下列门槛为 **可验证条件草案**；**不得**解读为已满足或已开启观察期。

### 5.1 L1 → L2 升格门槛（须 ≥3 条 + 批文）

| # | 门槛 | 验证方式 |
|---|------|----------|
| G-L2-1 | demo E2E dry-run **连续 N≥7 次** `ok: true`（`WC-DEMO-1` · nightly 或手工） | `[WC-SMOKE]` / walkthrough artifact 留痕 |
| G-L2-2 | L1 观察期内 **零 P0 mis-write**（无误写 live STATE / FRAME / C/D） | Progress + 审计 log 抽查 |
| G-L2-3 | rollback playbook **文档演练** 1 次留痕（Scribe D_REPORT） | 演练记录 |
| G-L2-4 | WC-T1-INTEGRATION · W4-MEM-01 **Reviewer 关票**（建议非阻塞） | 票 state `accepted` |
| **批文** | 尚書省 `approval_status.CP_AUTO_L2=approved` | 独立字段 · 非 WC-PRE-06 L2 批文 |

### 5.2 L2 → L3 升格门槛（须 ≥3 条 + 批文）

| # | 门槛 | 验证方式 |
|---|------|----------|
| G-L3-1 | L2 观察期 **≥14 日** · 零 P0 · advisory LLM（若启用）100% 人工审阅 | 审计 log + Reviewer 抽查 |
| G-L3-2 | Control Plane E2E **≠ INT Tier-A** 三处声明已在 runbook / 本契约对齐 | doc regression |
| G-L3-3 | rollback 演练 **≥2 次**（含 CI required 降级路径） | D_REPORT |
| G-L3-4 | 独立挂载点设计评审（**不**占用 toolchain smoke 白名单） | `WC-IMPL-SMOKE-CI-L1` 分轨对照 |
| **批文** | 尚書省 `approval_status.CP_AUTO_L3=approved` | 独立实施票 |

### 5.3 Rollback Playbook（文档级）

#### L1 → L0

1. 停用 L1 `--execute` flag / nightly 中的写副本步骤（实施票 revert 或 env 开关 off）。
2. 删除或归档 `artifacts/e2e/**` 下 L1 隔离副本（保留审计 log）。
3. Progress **末尾 append** rollback 事件：`tier=L0` · `run_id` · `operator` · `reason`。

#### L2 → L1

1. 吊销所有未消费 L2 **一次性批准 token**。
2. 恢复 WC-T5 `wc.m2.state.write_ticket` = `forbidden` 全量语义（若曾 doc-amend 标 HITL-reduced，回退修正案）。
3. 停用 L2 扩展 artifacts 扫描与 advisory LLM 路径。
4. 审计 log 标记 `tier=CP-AUTO-L1` · `rollback_ref=§5.3-L2-to-L1`。

#### 应急：误写 live STATE

1. **立即停止** runner；不得继续 `--execute`。
2. Orchestrator **HITL 手工恢复** live `*_state.md`（git checkout 或备份还原）；**禁止**脚本自动回滚 FRAME / C_REPORT / D_REPORT。
3. Scribe 在 Progress **末尾 append** P0 事件；Reviewer 开 incident 复查票。
4. 强制回退至 **L0** 直至 L2 观察期重新满足 §5.1。

---

## 6. 分轨声明（三处 · AC-GOV-6）

### 6.1 Control Plane E2E / nightly ≠ INT Tier-A

- `run_wc_m2_e2e_walkthrough.py` · `run_wave_c_nightly_smoke.sh` 的 pass **不等于** INT Tier-A pass。
- Control Plane 链验收见 `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`；INT 验收见 `docs/phase6-int-regression-gate-contract-v1.md`。
- CP-AUTO L3 若提案 E2E 进 CI，须 **独立 gate_id** · 不替换 `OG-WAVE7-REGRESSION-A`。

### 6.2 CP-AUTO L3 ≠ WC-PRE-06/07 Toolchain L2

| 轴 | CP-AUTO L3 | WC-PRE-06/07 L2 |
|----|------------|-----------------|
| 对象 | Control Plane E2E / nightly CI 升格 | Toolchain health / smoke matrix mandatory CI |
| 批文 | `approval_status.CP_AUTO_L3` | `approval_status.L2`（toolchain） |
| 实施票 | `WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L3` | `WC-IMPL-L2` · `WC-PRE-06/07` |
| **禁止** | 混票或捆绑升格 | 同上 |

CP-AUTO L1/L2 **不得**依赖 toolchain L2 批文作为前置。

### 6.3 `wc.m2.state.write_ticket` 在 L0–L2 不全量升格

- WC-T5 path_id `wc.m2.state.write_ticket` · `wc.m2.chat.open_cursor` 在 L0–L2 **保持 `forbidden`**（全路径级）。
- L2 仅允许 **doc-only 修正案** 标注子集字段（`status_by_role` · `next_action`）为 `HITL-reduced` — **非** `auto` · **非** 全量 write_ticket 升格。
- 推翻 WC-T6 v0.1 **无网络 · 无写回** 底线作为 L0 默认 — **禁止**。

---

## 7. WC-T5 修正案提案（doc-only · AC-GOV-7）

> **不**直接修改 `wc_t5_paths_v0.1` JSON；生效须 `WA-T5-AMEND-*` 或 WC-T5 v0.2 票。

| path_id / 字段域 | L0–L1 | L2 提案 | 说明 |
|------------------|-------|---------|------|
| `wc.m2.state.write_ticket`（全路径） | `forbidden` | `forbidden`（不变） | 全量自动写 live STATE 仍禁止 |
| STATE 子集 · `status_by_role` | HITL-only | **`HITL-reduced`** | 允许 token 门控下的有限自动更新；仍须 Reviewer 可见 |
| STATE 子集 · `next_action` | HITL-only | **`HITL-reduced`** | 同上 |
| FRAME / C_REPORT / D_REPORT | HITL-only | **HITL-only**（不变） | L2 仍禁止自动写入 |
| `wc.m2.chat.open_cursor` | `forbidden` | `forbidden`（不变） | Multi-Chat 仍人工开 chat |

---

## 8. 依赖与批文

### 8.1 依赖（只读引用）

| 依赖 | 状态 | 本票关系 |
|------|------|----------|
| WC-T6-T7-v2 | done · `accepted_with_gaps` | deferred 输入 **必完成** |
| WC-T5 | done · `accepted` | automation_tier SSOT |
| WC-T6 / WC-T7 v0.1+v2 | done | distill CLI · E2E runbook 语义 |
| WC-T1-INTEGRATION | Reviewer pending | L2 升格 **建议** 前置；非本票阻塞 |
| W4-MEM-01 | Reviewer pending | 同上 |
| WA-T4 · W5-T2 / W5-T2B | 制度 SSOT | HITL / 四角色 STATE 冻结 **硬约束** |
| WC-PRE-06/07 · WC-IMPL-L2 | blocked_on_approval | **分轨**；非 CP-AUTO L1/L2 前置 |

### 8.2 批文矩阵

| 动作 | 须尚書省批文 | 实施票 |
|------|--------------|--------|
| **本票 FRAME 冻结** | **否**（doc-only · non-gating） | WC-GOV-EXEC-ARTIFACTS-LLM |
| **CP-AUTO L1 开启** | **否**（建议 Reviewer 关 FRAME 后） | `WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L1` |
| **CP-AUTO L2 观察期启动** | **是** · `approval_status.CP_AUTO_L2=approved` | `WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L2` |
| **CP-AUTO L3（PR / CI / INT）** | **是** · `approval_status.CP_AUTO_L3=approved` | `WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L3` 或 `WA-T6-AMEND-CP-E2E-CI` |
| **WC-T5 JSON 附录变更** | **是**（修正案流程） | `WA-T5-AMEND-*` / WC-T5 v0.2 |

---

## 9. 交叉引用

| 文档 | 用途 |
|------|------|
| `04_Workflows/tickets/WC-GOV-EXEC-ARTIFACTS-LLM_state.md` | 本票 FRAME / STATE / C_REPORT |
| `04_Workflows/tickets/WC-T6-T7-v2_state.md` | deferred 来源 · v2 验收 |
| `docs/wave_c/WC_T5_automation_coverage_contract.md` | `wc.m2.*` forbidden 矩阵 |
| `docs/wave_c/WC_T6_skill_distillation_lite.md` | L0 本地启发式 SSOT |
| `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` | E2E · INT 分离声明 |
| `docs/wave_c/overview.md` §M3 self-check · M4 | Wave C 进度索引 |
| `docs/governance/WC_PRE_06_07_rollout_plan.md` | toolchain L2 分轨 |
| `docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md` | toolchain L2 设计对照 |
| `docs/phase4-multi-agent-collaboration-contract-v1.md` | 四角色 STATE 写入冻结 |
| `.cursor/rules/multi_chat_roles.mdc` | Multi-Chat 角色边界 |

---

## 10. 验收索引（契约级 · 非施工）

本 FRAME 文档自身验收（AC-GOV-1～9）由 Reviewer 对照 `WC-GOV-EXEC-ARTIFACTS-LLM_state.md` AcceptanceCriteria 关票；**不包含** runner 执行。

```bash
# 仅验证 WC-T5 基线未被本票误改（父契约仍绿）
python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v
```

---

*WC-GOV-EXEC-ARTIFACTS-LLM Governance Contract · v0.1 FRAME · doc-only · 2026-06-14*
