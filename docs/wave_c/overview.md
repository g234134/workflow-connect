# Wave C 总览 — 进度跟踪与沟通索引

> **成文日期**：2026-06-13  
> **角色**：Orchestrator / 文档工程师进度索引（doc-only）  
> **SSOT**：票级细节见 `04_Workflows/tickets/*_state.md`；Toolchain 能力边界见 `docs/wave-b-toolchain-readme-v1.md` §Wave C 可假设能力  
> **机器可读状态**：见文末 `WAVE_C_TICKET_REGISTRY` 注释块（脚本可 grep / 替换 `status=` 字段）

---

## Wave C 目标

Wave C 在 Wave B Toolchain（WB-T1–T8）与 Observability 产品基线（C1 AI Workflow 健检、C2 表格清洗）之上，完成三条并行能力线：**（1）Toolchain 前置治理与本地 gaps 盘点**（WC-PRE / WC-C1），把 plan_only、executor timeout、audit investigation、smoke matrix 等已验收能力收敛为可引用的开发者入口；**（2）Control Plane 智能接单与工单协同**（WC-T 系列），在 `*_state.md` 票务 SSOT 上叠加 eligibility 判断、STATE 变更通讯、dispatch 指令卡与订单 intake 模型，缩短 Multi-Chat 开 chat 与 handoff 摩擦；**（3）治理升格与商业化闭环**（WC-PRE-06/07、C1-P3+、产品交付包），在尚書省批文门控下可选升格 toolchain health / smoke CI，并将 C1 健检 runbook 从人工 CLI 演进为可重复 pipeline 与标准战报。全程维持 **optional / non-blocking / investigation-only** 默认语义，**不得**假设 PR required gate 或 prod SLA 已开启。

---

## 命名空间（勿混淆）

| 名称 | 含义 | 索引 |
|------|------|------|
| **Wave C · Toolchain** | WC-PRE / WC-C1 / toolchain gaps & governance | 本档 · `docs/toolchain-local-gaps-quickview-v1.md` |
| **Wave C · Control Plane** | WC-T* 智能接单 / 通讯 / dispatch 卡 | `docs/control_plane_dispatch_executor.md` · `docs/wave_c/WC_T*.md` |
| **Wave C · Observability 产品** | C1 AI Workflow 健检 · C2 表格清洗 | `docs/WAVE_C_EXECUTION_PLAN.md` · `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` |
| **Toolchain Wave B** | WB-T* 底层 contract（Wave C 可引用） | `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` |

---

## 里程碑

| 里程碑 | 主题 | 包含票 | 完成信号 |
|--------|------|--------|----------|
| **M1** | 基础治理与工具 | WC-PRE-01～05 · WC-C1-01 · WC-PRE-06 L0 | PRE-01～05 Reviewer 关票；gaps quickview CLI 可用；governance snapshot 非阻塞 CI 落地 |
| **M2** | 智能接单与订单 | WC-T1～T4 · WC-IMPL-L1 · dispatch_executor 栈 | eligibility / comms / dispatch cards / order intake 可本地跑通；Multi-Chat handoff 可脚本化；governance snapshot L1 advisory 落地 |
| **M3** | 治理升格与 Wave C 收口 | WC-PRE-06/07 L2 批文后 · WC-T5～T7 · C1-P3+ | 自动化覆盖率契约；skill distillation lite；E2E walkthrough + INT gate 对齐；可选 L2 health/smoke gate |

### M2 达成情况（2026-06-13）

| 状态 | 票号 | 交付物摘要 |
|------|------|------------|
| **已达成** | **WC-T1** | `ticket_eligibility` + CLI；dispatch cards eligibility gate（WC-T1-INTEGRATION） |
| **已达成** | **WC-T2** | STATE 变更 comms payload + file-log sender + `run_ticket_state_update_with_comms.py` |
| **已达成** | **WC-T4** | Order/job intake v0.1 · `run_order_intake.py` · JSONL ledger |
| **已达成** | **WC-IMPL-L1** | Governance snapshot L1 advisory（MissingSignalRules · non-blocking exit 0） |
| **进行中** | **WC-T3** | Dispatch cards MVP（`W-next-DISPATCH-CARDS-MVP` · 待 Reviewer 关票） |

**M2 尾项**：WC-T3 关票后 M2 主体可宣告收口；M2 E2E 验收见 [`WC_T7_e2e_walkthrough_runbook.md`](WC_T7_e2e_walkthrough_runbook.md)（Control Plane 链 · **≠** INT Tier-A）。

### M3 范围（留给 T5–T7 + L2）

| 分轨 | 票号 | 主题 |
|------|------|------|
| Control Plane 契约 | **WC-T5** | 自动化覆盖率 / 风险边界契约（哪些路径 auto vs HITL vs forbidden）；**T5 交付**：`WC_T5_automation_coverage_contract.md` + `test_wc_t5_automation_coverage_contract_v1.py` |
| Control Plane 学习 | **WC-T6** | Skill distillation / learning lite（从 ticket handoff 提炼可复用 skill 片段）— **v0.1 骨架进行中**（`distill_control_plane_skills_lite.py` + fixture unittest） |
| 集成与收口 | **WC-T7** | E2E walkthrough 制度化 + INT gate 边界对齐 → [`WC_T7_e2e_walkthrough_runbook.md`](WC_T7_e2e_walkthrough_runbook.md) |
| 治理升格（批文门控） | **WC-PRE-06 L2** · **WC-PRE-07 L2** · **WC-IMPL-L2**（若另开） | PR required health/smoke gate；**须**尚書省 `approval_status=approved` |
| Observability 产品 | **C1-P3+** | C1 诊断 pipeline / 产品交付包（与 WC-T 分轨，不 merge 票号） |

---

## 票清单

> **状态枚举**：`TODO` · `In Progress` · `Done`（与 `overall_status` 解耦，供本总览人类阅读；脚本以 registry 为准）

### WC-PRE — Wave B 前置清理与 impl gap

| 票号 | 简短描述 | 状态 | 负责人 |
|------|----------|------|--------|
| **WC-PRE-01** | Wave B 文档/票务 hygiene：D_REPORT 补齐、Dashboard/执行计划/索引对齐 | Done | TBD |
| **WC-PRE-02** | Selector 回传 dict 显式 `plan_only: True`（Tabular + Non-Tabular） | Done | TBD |
| **WC-PRE-03** | Executor subprocess `timeout=600s` 实装与契约断言 | Done | TBD |
| **WC-PRE-04** | Audit quickview 原生 investigation view CLI（`--view investigation`） | Done | TBD |
| **WC-PRE-05** | Smoke matrix YAML 本地 runtime runner（dry-run / list / execute） | Done | TBD |
| **WC-PRE-06** | Toolchain observability 治理升格设计（L0→L1→L2 · `OG-TOOLCHAIN-HEALTH` 提案） | In Progress | TBD |
| **WC-PRE-07** | P6 smoke matrix CI 独立设计稿 + ticket state（rollout §7 D5=YES · design draft 已冻结 · 无批文不得改 workflow required） | Done | TBD |
| **WC-IMPL-L1** | Governance snapshot L1 advisory enforcement（最弱约束 · 不改 pass/fail · implemented） | Done | TBD |

**快速验证（PRE 已交付项）**

```bash
python -m unittest tests.test_tabular_tool_selector tests.test_tool_executor_and_sandbox_contract_v1 -v
python scripts/run_toolchain_smoke_matrix.py --list --dry-run --format json
python scripts/generate_toolchain_governance_snapshot.py --write
```

**票 state**：`04_Workflows/tickets/WC-PRE-0*_state.md` · `WC-PRE-07_state.md` · `WC-IMPL-L1_state.md` · 索引：`04_Workflows/tickets/README.md` §Wave C PRE

---

### WC-C1 — Toolchain 核心开发者入口

| 票号 | 简短描述 | 状态 | 负责人 |
|------|----------|------|--------|
| **WC-C1-01** | Toolchain local gaps quickview：只读聚合 selector/executor/audit/smoke/health（local · optional · non-gating） | Done | TBD |

**快速验证**

```bash
python scripts/run_toolchain_local_gaps_quickview.py --format json
python -m unittest tests.test_toolchain_local_gaps_quickview_v1 -v
```

**文档**：`docs/toolchain-local-gaps-quickview-v1.md`  
**票 state**：`04_Workflows/tickets/WC-C1-01-toolchain-local-gaps-quickview-v1_state.md`

---

### WC-T — Control Plane 智能接单与协同

| 票号 | 简短描述 | 状态 | 负责人 |
|------|----------|------|--------|
| **WC-T1** | Ticket eligibility：基于 `*_state.md` 判断 implementer/reviewer/scribe 是否可接单 | Done | TBD |
| **WC-T2** | Minimal ticket comms：STATE 变更时生成结构化通讯 payload + file-log sender | Done | TBD |
| **WC-T3** | Dispatch cards：由 dispatch plan 自动生成 Multi-Chat `*.cursor.md` 指令卡 | In Progress | TBD |
| **WC-T4** | Order / job intake model：外部请求 → ticket/job 结构化记录与只读 intake CLI | Done | TBD |
| **WC-T5** | 自动化覆盖率 / 风险边界契约：Control Plane 路径 auto·HITL·forbidden 矩阵 + 可验证断言 | In Progress | TBD |
| **WC-T6** | Skill distillation / learning lite：从 dispatch·comms·STATE handoff 提炼可复用 skill 片段 | In Progress | TBD |
| **WC-T7** | E2E walkthrough 制度化 + INT gate 边界对齐（M2 链 × Tier-A 契约 cross-ref） | In Progress | TBD |

**快速验证（T1/T2/T4 已交付 · T3 代码已存在待关票）**

```bash
python scripts/run_ticket_eligibility.py --ticket W1-T2 --requested-role reviewer --format json
python -m unittest tests.test_ticket_eligibility tests.test_ticket_comms tests.test_ticket_state_update_cli -v
python scripts/run_ticket_state_update_with_comms.py \
  --before tests/fixtures/ticket_comms/wc_t2_before_state.md \
  --after tests/fixtures/ticket_comms/wc_t2_after_state.md
python scripts/run_dispatch_executor.py --json-out artifacts/control_plane/dispatch_plan.latest.json
python scripts/run_dispatch_cards.py --limit 3 --pretty
python -m unittest tests.test_dispatch_cards -v
python scripts/run_order_intake.py create --ticket WC-T4-INT --amount-minor 10000 --currency TWD \
  --ticket-path tests/fixtures/order_ledger/WC-T4-INT_state.md --dry-run
python -m unittest tests.test_order_ledger tests.test_order_ledger_integration -v
python scripts/distill_control_plane_skills_lite.py \
  --cards-dir tests/fixtures/skill_distillation/cards \
  --comms-jsonl tests/fixtures/skill_distillation/comms/one_comms.jsonl --pretty
python -m unittest tests.test_distill_control_plane_skills_lite -v
```

**文档**：`docs/wave_c/WC_T1_eligibility.md` · `docs/wave_c/WC_T2_comms_minimal.md` · `docs/wave_c/WC_T4_order_ledger_design.md` · `docs/wave_c/WC_T5_automation_coverage_contract.md` · `docs/wave_c/WC_T6_skill_distillation_lite.md` · `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` · `docs/control_plane_dispatch_executor.md`

**WC-T5 快速验证（In Progress）**

```bash
python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v
```

> **注**：WC-T3 实现对应 `W-next-DISPATCH-CARDS-MVP`（`04_Workflows/_dispatch_cards.py`）；票 state 仍为 `draft`，本总览标 **In Progress** 直至 Reviewer 关票。WC-T4 v0.1 最小路径已实装（真实 ticket state → order/ledger）；Outbox / REST / 支付等 deferred 见设计稿 §10。WC-T5 契约文档 + coverage 测试已落盘；WC-T7 runbook v0.1 + 可选 runner `scripts/run_wc_m2_e2e_walkthrough.py` 已落盘（`04_Workflows/tickets/WC-T7_state.md`）。

---

## Wave C status snapshot (auto-friendly)

> **用途**：脚本 / dashboard 可 grep 本节或文末 `WAVE_C_TICKET_REGISTRY`（格式一致）；更新时**两处同步**或只改 registry 后复制到本节。  
> **格式**：`<!-- ticket:<id> status=<Status> owner=<Owner> milestone=<Mx> -->`  
> **状态枚举**：`TODO` · `In Progress` · `Done`

<!-- ticket:WC-PRE-01 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-02 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-03 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-04 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-05 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-06 status=In Progress owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-07 status=Done owner=TBD milestone=M3 -->
<!-- ticket:WC-IMPL-L1 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-C1-01 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-T1 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T2 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T3 status=In Progress owner=TBD milestone=M2 -->
<!-- ticket:WC-T4 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T5 status=In Progress owner=TBD milestone=M3 -->
<!-- ticket:WC-T6 status=In Progress owner=TBD milestone=M3 -->
<!-- ticket:WC-T7 status=In Progress owner=TBD milestone=M3 -->

---

## M2 End-to-End regression (manual)

> **SSOT**：[`docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`](WC_T7_e2e_walkthrough_runbook.md)（WC-T7 · v0.1）

在**不改动实现代码**的前提下，手工（或半自动）走通 M2 最小链：**eligibility → dispatch 指令卡 → STATE 变更 comms → order intake**。建议 demo 票 `WC-DEMO-1`；产物写入 `artifacts/e2e/<ticket_id>/`。

```bash
# 可选 runner：仅打印步骤命令
python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run
```

**边界**：本链为 Control Plane E2E，用于 M2/M3 验收；**不等于** INT Tier-A（见 runbook 文末 §INT gate 对齐）。

---

## Nightly smoke (Wave C M2)

> **用途**：本地晚间约 20 分钟快速扫 Control Plane M2 链（eligibility → dispatch → comms → order → governance snapshot → distillation → unittest）。**非 CI gate**；仅写 demo 票 `WC-DEMO-1` 与隔离产物目录。

- Demo ticket: `WC-DEMO-1`
- Artifacts root: `artifacts/e2e/WC-DEMO-1/`
- Script: `scripts/run_wave_c_nightly_smoke.sh`
- Runbook SSOT: [`docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`](WC_T7_e2e_walkthrough_runbook.md)
- Suggested command:

```bash
bash scripts/run_wave_c_nightly_smoke.sh
```

**前置**：在 repo 根执行；先激活 Python 环境（`PYTHON` 或 venv，见脚本头注释）。日志标记 `[WC-SMOKE]` 便于 grep。

---

## Wave C M3 self-check (T5/T6/T7)
> **性质**：2026-06-13 M3 自检快照（实现 vs FRAME）；非 merge gate。细节见各票 `*_state.md` 与 FRAME 契约。

- **WC-T5**：契约文档 + 14 路径 JSON 附录 + 结构契约测试已齐，AC 主体满足；待补 T6 `cp.*`↔`wc.m2.*` 映射、verification 真跑 smoke、Reviewer 关票。
- **WC-T6**：distill CLI + fixture + unittest 已绿，设计稿示例完备；待补 state B_REPORT、reports fixture/`--reports-dir` 测试、与 T5 正式 path_id 对齐。
- **WC-T7**：runbook + INT 对齐 + runner 骨架已落盘，overview M2 已收口；待补 `WC-DEMO-1` 模板票、runner unittest、dry-run 零写盘与 T5 path_id 映射。

## Wave C Phase 1 completion (Control Plane M2 + Governance v0.1)
> **宣告日**：2026-06-XX（宣告时替换为实际日期）  
> **性质**：Wave C Control Plane Phase 1 里程碑宣告；票级 SSOT 仍以 `04_Workflows/tickets/*_state.md` 为准。

### 范围（本阶段已交付）
| 分轨 | 内容 | SSOT |
|------|------|------|
| **M2 主链** | eligibility · dispatch plan/cards · comms · order intake | `docs/wave_c/WC_T1_eligibility.md` · `WC_T2_comms_minimal.md` · `docs/control_plane_dispatch_executor.md` · `docs/wave_c/WC_T4_order_ledger_design.md` |
| **Governance L1** | snapshot advisory（MissingSignalRules v1 · non-blocking exit 0） | `docs/governance/WC_PRE_06_07_rollout_plan.md` §3.6 · `04_Workflows/tickets/WC-IMPL-L1_state.md` |
| **M3 契约骨架** | T5 覆盖率契约 · T6 skill distillation lite · T7 E2E runbook + runner | `docs/wave_c/WC_T5_automation_coverage_contract.md` · `docs/wave_c/WC_T6_skill_distillation_lite.md` · `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` |
| **运营工具** | 本地 nightly smoke（`WC-DEMO-1` · 隔离 `artifacts/e2e/`） | `scripts/run_wave_c_nightly_smoke.sh` · overview 本页 §Nightly smoke |

### 状态（宣告日快照）
- Phase 1 视为完成：Control Plane M2 主链 + governance snapshot L1 advisory + T5/T6/T7 文档与脚本骨架已可重复验证。
- 关键实现票（T1/T2/T3/T4、WC-IMPL-L1、WC-T5/T6/T7、WC-SMOKE-M2-NIGHTLY）由 Reviewer 评为 `accepted` 或 `accepted_with_gaps`，gaps 保留在各票 C_REPORT。
- L2 selective mandatory：WC-PRE-06/07 与 WC-IMPL-L2 FRAME 已冻结，处于 L1→L2 观察期；未改任何 PR required / mandatory CI。

### 本阶段不含
- L2 merge gate（OG-TOOLCHAIN-HEALTH PR required · smoke 白名单 mandatory CI）。
- INT Tier-A 验收（Control Plane E2E / nightly pass ≠ INT pass）。
- Observability 产品轨 C1-P3+（与 WC-T 分轨，票号不合并）。
- 自动写 live `*_state.md`、自动开 Cursor chat、无 HITL 关票。

### 下一步（Phase 2 起点）
- 按各票 C_REPORT 补完 gaps（T5↔T6 path_id 映射、T6 reports fixture、T7 runner unittest 等）。
- 观察期内仅本地/nightly 验证，仍保持 optional / non-gating。
- L2 升格通过 WC-PRE-06/07 rollout + 尚書省批文，Observability 继续走 C1-P3+ 票。
- Scribe 在 Progress 末尾追加 Phase 1 snapshot，并保持本页 registry 与票状态同步。

### Wave C 运营期工作模式（Phase 1 宣告后草案）
> 生效自 2026-06-XX（宣告时替换为实际日期）  
> 默认语义：本地 optional · non-blocking · investigation-only；E2E / nightly 不接 PR required。

#### 频率
| 节奏 | 动作 | 产出 |
|------|------|------|
| 每票 | eligibility → dispatch plan → Multi-Chat B/C/D | `*_state.md` B/C/D REPORT |
| 每周 | 扫 overview registry + 进行中票 `next_action` | registry 与 Progress 中 Wave C 行 |
| 按需 | 跑 governance snapshot / gaps quickview | snapshot JSON/Markdown 报告 |
| 本地晚间（可选） | `run_wave_c_nightly_smoke.sh` | `artifacts/e2e/WC-DEMO-1/` + `[WC-SMOKE]` 日志摘要 |
| 升格前 | G1–G8 证据盘点 | `WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md` §4 对照周报 |

#### 入口（SSOT）
| 用途 | 命令 |
|------|------|
| 晚间 smoke | `bash scripts/run_wave_c_nightly_smoke.sh` |
| E2E walkthrough（dry-run） | `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run` |
| Control Plane 模块回归 | `python -m unittest tests.test_ticket_eligibility tests.test_dispatch_cards tests.test_ticket_comms tests.test_order_ledger tests.test_wc_t5_automation_coverage_contract_v1 tests.test_distill_control_plane_skills_lite tests.test_run_wc_m2_e2e_walkthrough -v` |
| Governance snapshot | `python scripts/generate_toolchain_governance_snapshot.py --ci-context eval-gate-pr --write --non-blocking` |
| Toolchain gaps | `python scripts/run_toolchain_local_gaps_quickview.py --format json` |

#### 开票规则
| 场景 | 动作 |
|------|------|
| nightly smoke 出现 blocking error | 按模块开 `WC-T*` / `WC-PRE-*` 修复票，附 `[WC-SMOKE]` 片段 |
| smoke WARN 可接受 | Progress 记一行，留月度治理 review 汇总 |
| 治理设计/框架变更 | 更新 PRE/IMPL 设计稿 + `*_state.md` FRAME，不直接改 workflow |
| 提议 L2 升格 | 先收 G1–G8 + rollback 演练 + 尚書省批文，再开执行票 |

#### 角色分工（简表）
| 角色 | 运营期职责 |
|------|------------|
| Orchestrator | 排期 smoke，汇总 WARN，决定是否开票，维护 registry |
| Implementer | 修复票施工，保证 UT/runner 绿，遵守 AllowedPaths/BlockedPaths |
| Reviewer | 定期抽查 smoke 产物和 snapshot，关票并维护 `accepted_with_gaps` 诚实性 |
| Scribe | Progress 和 overview 同步，归档 L1/L2 观察期证据 |

---

## 进度摘要

| 分轨 | 已完成 | 进行中 | 待办 | 合计 |
|------|--------|--------|------|------|
| WC-PRE / IMPL | 7 | 1 | 0 | 8 |
| WC-C1 | 1 | 0 | 0 | 1 |
| WC-T | 3 | 2 | 2 | 7 |
| **合计** | **11** | **3** | **2** | **16** |

---

## 关键边界（开票前必读）

- **可安全引用**：Wave B + WC-PRE-02～05 + WC-C1-01 gaps quickview；WC-T1 eligibility · WC-T2 comms（只读、不写 STATE）。
- **禁止假设**：`OG-TOOLCHAIN-HEALTH` PR required；smoke matrix mandatory CI；selector prod blocking gate；dashboard SLA 字段。
- **批文门控**：WC-PRE-06/07 改 CI required 或 P3.5 gate 表须尚書省 `approval_status=approved`（见 `docs/toolchain-observability-governance-upgrade-v1.md` §8）。
- **分轨**：Observability 产品（C1/C2）与 Toolchain（WC-PRE/C1）与 Control Plane（WC-T）**禁止** rename 或合并票号。

---

## 交叉引用

| 文档 | 用途 |
|------|------|
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Tabular MVP + Toolchain Wave B Phase% SSOT |
| `docs/WAVE_C_EXECUTION_PLAN.md` | C1 AI Workflow 健检对内 runbook |
| `docs/governance/WC_PRE_06_07_rollout_plan.md` | PRE-06/07 升格路径与 CH-* 检查清单 |
| `docs/governance/WC_PRE_06_07_snapshot.md` | L0 non-blocking governance snapshot 用法 |
| `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` | Control Plane M2 E2E + INT gate 对齐（WC-T7） |
| `04_Workflows/tickets/README.md` | 票 state 路径索引 |
| `04_Workflows/00_Agent_Work_Progress.md` | 全局战报末尾 Wave C 条目 |

---

## WAVE_C_TICKET_REGISTRY

<!--
  机器可读票册 — 脚本更新约定：
  - 每行格式：ticket:<ID> status=<TODO|In Progress|Done> owner=<name|TBD> milestone=<M1|M2|M3>
  - 仅修改 status= 与 owner= 字段；勿删 ticket: 行
  - 示例：python scripts/update_wave_c_overview.py --ticket WC-T1 --status Done --owner alice
-->

<!-- ticket:WC-PRE-01 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-02 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-03 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-04 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-05 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-06 status=In Progress owner=TBD milestone=M1 -->
<!-- ticket:WC-PRE-07 status=Done owner=TBD milestone=M3 -->
<!-- ticket:WC-IMPL-L1 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-C1-01 status=Done owner=TBD milestone=M1 -->
<!-- ticket:WC-T1 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T2 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T3 status=In Progress owner=TBD milestone=M2 -->
<!-- ticket:WC-T4 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T5 status=In Progress owner=TBD milestone=M3 -->
<!-- ticket:WC-T6 status=In Progress owner=TBD milestone=M3 -->
<!-- ticket:WC-T7 status=In Progress owner=TBD milestone=M3 -->

---

*Wave C Overview · v0.2 · 2026-06-13 · doc-only · 状态以 registry 与 `*_state.md` 交叉校验*
