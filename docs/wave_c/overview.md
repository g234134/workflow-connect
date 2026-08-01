# Wave C 总览 — 进度跟踪与沟通索引

> **成文日期**：2026-06-13（**v0.3 · 2026-06-14** 多 lane 收口同步）  
> **角色**：Orchestrator / 文档工程师进度索引（doc-only）  
> **SSOT**：票级细节见 `04_Workflows/tickets/*_state.md`；Toolchain 能力边界见 `docs/wave-b-toolchain-readme-v1.md` §Wave C 可假设能力  
> **机器可读状态**：见文末 `WAVE_C_TICKET_REGISTRY` 注释块（脚本可 grep / 替换 `status=` 字段）  
> **多 lane 索引**：Lane B/C 收口表见 `docs/WAVE_PROGRESS_DASHBOARD.md` §多 Lane 本輪收口

---

## Wave C 目标

Wave C 在 Wave B Toolchain（WB-T1–T8）与 Observability 产品基线（C1 AI Workflow 健检、C2 表格清洗）之上，完成三条并行能力线：**（1）Toolchain 前置治理与本地 gaps 盘点**（WC-PRE / WC-C1），把 plan_only、executor timeout、audit investigation、smoke matrix 等已验收能力收敛为可引用的开发者入口；**（2）Control Plane 智能接单与工单协同**（WC-T 系列），在 `*_state.md` 票务 SSOT 上叠加 eligibility 判断、STATE 变更通讯、dispatch 指令卡与订单 intake 模型，缩短 Multi-Chat 开 chat 与 handoff 摩擦；**（3）治理升格与商业化闭环**（WC-PRE-06/07、C1-P3+、产品交付包），在尚書省批文门控下可选升格 toolchain health / smoke CI，并将 C1 健检 runbook 从人工 CLI 演进为可重复 pipeline 与标准战报。全程维持 **optional / non-blocking / investigation-only** 默认语义，**不得**假设 PR required gate 或 prod SLA 已开启。

---

## Wave C 與全局 Wave 的關係

> **定位**：Wave C 並非獨立存在，而是承接 Wave 1–5 Tabular MVP 主幹、銜接 Wave 6–8 實驗線、並為 Wave 9+ Non-Tabular 影子流奠基的「Control Plane 治理與商業化閉環」層。

| 階段 | Wave 範圍 | 核心主題 | 與 Wave C 的關係 |
|------|-----------|----------|------------------|
| **主幹打底** | Wave 1–5 | MVP 主鏈 / Routing / Tool Layer | Wave C **可引用** Wave 1–5 已交付能力（Tabular Catalog/Selector/Executor），但**不修改**其行為；Wave 2 routing catalog 為 WC-T 系列 task_type 路由提供參考 |
| **實驗線延伸** | Wave 6–8 | Skill Card / Agent Standard Line / Controlled Notify / Delivery Approval | Wave C **受益於** W6–W8 的實驗線基礎設施（orchestrator allowlist、checkpoint 機制、notify 模擬），但**不依賴**其為 production contract；WC-T6/T7 的 skill distillation / E2E runbook 可視為 W6–W8 實驗治理的 Control Plane 化 |
| **治理閉環** | **Wave C** | Toolchain 治理 / Control Plane 智能接單 / 商業化閉環 | **本檔主題**：WC-PRE 系列把 Wave B Toolchain 能力收斂為 gaps quickview / governance snapshot；WC-T 系列把 W5–W8 的 Agent 協作經驗轉化為可重複的 eligibility/dispatch/comms/order 管線 |
| **影子流未來** | Wave 9+ | Non-Tabular Shadow Flow | Wave C **預留接口**（WC-T1-INTEGRATION 的 `task_type` 判斷、WC-PRE-06/07 的 L2 升格機制）供 Wave 9+ Non-Tabular 使用，但**不阻塞**其開發；WC-T5 的 automation coverage contract 定義了「Tabular vs Non-Tabular」的分軌語義 |

### 分軌聲明（重要）

- **Tabular 主鏈（Wave 1–5）**：`demo_phase` / `sampleco` 為錨點案型，MVP regression 不變；Wave C **不改**其行為。
- **實驗線（Wave 6–8）**：`additional_demo` / `sandbox_client` 為 `experiment_line_only`，允許 breakage；Wave C **可選引用**其基礎設施（orchestrator、checkpoint），但保持 `plan_only` / `dry-run` / `non-blocking` 語義。
- **Non-Tabular 影子流（Wave 9+）**：獨立 family，獨立 YAML / selector / stub；Wave C **不負責**另開 Wave 9 票，但預留 `non_tabular.*` task_type 判斷與 L2 升格批文機制。

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

### M2 达成情况（2026-06-14）

| 状态 | 票号 | 交付物摘要 |
|------|------|------------|
| **已达成** | **WC-T1** | `ticket_eligibility` + CLI；dispatch cards eligibility gate（**WC-T1-INTEGRATION** · implementer done · Reviewer pending） |
| **已达成** | **WC-T2** | STATE 变更 comms payload + file-log sender + `run_ticket_state_update_with_comms.py` |
| **已达成** | **WC-T3** | Dispatch cards MVP（**W-next-DISPATCH-CARDS-MVP** · done · accepted） |
| **已达成** | **WC-T4** | Order/job intake v0.1 · `run_order_intake.py` · JSONL ledger |
| **已达成** | **WC-IMPL-L1** | Governance snapshot L1 advisory（MissingSignalRules · non-blocking exit 0） |
| **已达成** | **WC-SMOKE-M2-NIGHTLY** | `run_wave_c_nightly_smoke.sh` · overview §Nightly smoke（**optional** 本地晚间扫） |

**M2 主体**：已收口；M2 E2E 验收见 [`WC_T7_e2e_walkthrough_runbook.md`](WC_T7_e2e_walkthrough_runbook.md)（**目前最新版 v0.4** · Control Plane 链 · **≠** INT Tier-A）。除 manual HITL walkthrough 外，另有 **demo fixture execute** 模式（`--execute --use-hitl-fixtures` · WD-P9-T2）；fixture execute 仍是 **demo skeleton**，**不等于** production HITL gate。逐步 HITL / fixture / INT Tier-A/B 对齐矩阵见 [`WC_M2_INT_HITL_alignment_matrix_v1.md`](WC_M2_INT_HITL_alignment_matrix_v1.md)（`WH-P9-M2-INT-alignment-v1` · 设计 SSOT）。

> **2026-06-24 · WC-M3 sandbox payment 里程碑**：WC-DEMO-* · DRAFT→PAID（**25/25** tests · runner **`--include-payment`** 一鍵 walkthrough OK · runbook §4+ 完整）已交付；**non-claims**：非 prod 金流 · 非真 provider · 非 INT Tier-A · 非 required CI。prod provider / INT gate / payment CI 仍为后续工作 — 见 [`WC_M3_payment_closure_scope_v1.md`](WC_M3_payment_closure_scope_v1.md) §6。

### M3 范围（留给 T5–T7 + L2）

| 分轨 | 票号 | 主题 |
|------|------|------|
| Control Plane 契约 | **WC-T5** | 自动化覆盖率 / 风险边界契约 — **done · accepted** · `WC_T5_automation_coverage_contract.md` + `test_wc_t5_automation_coverage_contract_v1.py` |
| Control Plane 学习 | **WC-T6** | Skill distillation lite — **done · accepted_with_gaps (v2)** · reports fixture + `--reports-dir` UT + T5 `wc.m2.*` 映射 · [`WC-T6-T7-v2_state.md`](../../04_Workflows/tickets/WC-T6-T7-v2_state.md) |
| 集成与收口 | **WC-T7** | E2E walkthrough + INT gate 对齐 — **done · accepted_with_gaps (v2)** · runbook v0.4 + WC-M3 sandbox payment §4+ · [`WC-T6-T7-v2_state.md`](../../04_Workflows/tickets/WC-T6-T7-v2_state.md) |
| Sandbox payment（P9） | **WC-M3** | sandbox DRAFT→PAID · runner `--include-payment` · **done_with_gaps**（2026-06-24）· [`WC_M3_payment_closure_scope_v1.md`](WC_M3_payment_closure_scope_v1.md) · **≠ prod 金流** |
| 治理升格（批文门控） | **WC-PRE-06 L2** · **WC-PRE-07 L2** · **WC-IMPL-L2**（若另开） | PR required health/smoke gate；**须**尚書省 `approval_status=approved` |
| Observability 产品 | **C1-P3+** | C1 诊断 pipeline / 产品交付包（与 WC-T 分轨，不 merge 票号） |

> **註（Wave C · Tabular Cleaning · 2026-06-15）**：C2 第二產品線關鍵票 **C2-P2／C2-D1** 本輪 Reviewer 已 **`accepted_with_gaps`**（runbook + demo 錨點）；JSON Schema／prod pipeline／sidecar 等 **deferred**，留未來票，**非**本輪 scope。詳見 `docs/wave_c/overview.md` C2 索引表。

---

## Wave C · Tabular Cleaning 產品線（C2 索引 · 2026-06-15）

| 票號 | 類型 | 狀態 | 交付物 |
|------|------|------|--------|
| **C2-P1** | Product Spec | done · `accepted_with_gaps` | `docs/PRODUCT_TABULAR_CLEANING.md` |
| **C2-P2** | Execution Plan / Runbook | **Reviewer `accepted_with_gaps`** | `docs/C2-P2_RUNBOOK.md` · `run_tabular_cleaning_plan.py`（pseudo CLI） |
| **C2-D1** | Demo Case | **Reviewer `accepted_with_gaps`** | `cases/demo_phase/` · `clean_phase_demo.py` · 品質戰報樣例 |

> **deferred（非本輪完成）**：`report.json` JSON Schema + CI 回歸 · 異常 flag sidecar · production pipeline／自助入口 · C2-D2 第二 mock · demo CLI 與 eligibility gate 文檔對齊。

**票 state**：`04_Workflows/tickets/C2-P1_state.md` · `C2-P2_state.md` · `C2-D1_state.md`

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
| **WC-T3** | Dispatch cards：由 dispatch plan 自动生成 Multi-Chat `*.cursor.md` 指令卡 | Done | TBD |
| **WC-T4** | Order / job intake model：外部请求 → ticket/job 结构化记录与只读 intake CLI | Done | TBD |
| **WC-T5** | 自动化覆盖率 / 风险边界契约：Control Plane 路径 auto·HITL·forbidden 矩阵 + 可验证断言 | Done | TBD |
| **WC-T6** | Skill distillation / learning lite：从 dispatch·comms·STATE handoff 提炼可复用 skill 片段 | Done · accepted_with_gaps (v2) | TBD |
| **WC-T7** | E2E walkthrough 制度化 + INT gate 边界对齐（M2 链 × Tier-A 契约 cross-ref） | Done · accepted_with_gaps (v2) | TBD |
| **WC-SMOKE-M2-NIGHTLY** | 本地晚间 smoke 脚本收编（WC-DEMO-1 · artifacts/e2e） | Done | TBD |
| **WC-T1-INTEGRATION** | eligibility 接入 dispatch cards 首入口（`--eligibility-gate`） | In Progress · Reviewer pending | TBD |

**快速验证（M2/M3 已交付项）**

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

**WC-T5 快速验证**

```bash
python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v
```

> **注**：WC-T3 实现对应 `W-next-DISPATCH-CARDS-MVP`（`04_Workflows/_dispatch_cards.py`）；**已 Reviewer 关票**。WC-T1-INTEGRATION 实现 eligibility gate（implementer done · Reviewer pending）。WC-T4 v0.1 最小路径已实装；Outbox / REST / 支付等 deferred 见设计稿 §10。WC-T5 **accepted**；WC-T6/T7 **accepted_with_gaps (v2)** — gap closure 见 [`WC-T6-T7-v2_state.md`](../../04_Workflows/tickets/WC-T6-T7-v2_state.md)（reports fixture · T5 path_id 附录已补；NonScope deferred：写 live STATE（forbidden）· 生产 artifacts · LLM）。WD-P9-T2 已交付 `--use-hitl-fixtures` demo skeleton execute（**非** prod E2E · **非** merge gate）；Wave-G 已接 CI advisory job `p9-wc-m2-fixture-execute`（**non-blocking**）。

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
<!-- ticket:WC-T3 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T4 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T5 status=Done owner=TBD milestone=M3 -->
<!-- ticket:WC-T6 status=Done owner=TBD milestone=M3 -->
<!-- ticket:WC-T7 status=Done owner=TBD milestone=M3 -->
<!-- ticket:WC-SMOKE-M2-NIGHTLY status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T1-INTEGRATION status=In Progress owner=TBD milestone=M2 -->

---

## M2 End-to-End regression (manual · fixture execute · dry-run)

> **SSOT**：[`docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`](WC_T7_e2e_walkthrough_runbook.md)（WC-T7 · **目前最新版 v0.3**）

在**不改动实现代码**的前提下，走通 M2 最小链：**eligibility → dispatch 指令卡 → STATE 变更 comms → order intake**。建议 demo 票 `WC-DEMO-1`；产物写入 `artifacts/e2e/<ticket_id>/`。

**三种执行路径**（详见 runbook 档头「执行路径分工」）：

| 模式 | 命令要点 | 说明 |
|------|----------|------|
| Dry-run 编排骨架 | `--dry-run` | 仅打印步骤命令；不写业务档 |
| Manual HITL | `--execute` + 手工编辑 live STATE（runbook §3/§4） | M2/M3 真人验收主路径 |
| Demo fixture execute | `--execute --use-hitl-fixtures`（WD-P9-T2） | 无真人 HITL；从 fixture 复制快照至 `artifacts/e2e/`；**仍是 demo skeleton，不等于 production HITL gate** |

```bash
# Dry-run：仅打印步骤命令
python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run

# Demo fixture execute（demo-only · CI advisory · 非 prod · 非 merge gate）
# 默认至 DRAFT；加 --include-payment 可 sandbox 一鍵至 PAID（≠ prod 金流）
python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket WC-DEMO-1 \
  --artifacts-root artifacts/e2e \
  --execute \
  --use-hitl-fixtures \
  --json

# Sandbox payment 一鍵 walkthrough（2026-06-24 · WC-M3）
python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket WC-DEMO-1 \
  --artifacts-root artifacts/e2e \
  --execute \
  --use-hitl-fixtures \
  --include-payment \
  --json
```

**CI advisory（Wave-G）**：`.github/workflows/p9-wc-m2-fixture-execute.yml` job **`p9-wc-m2-fixture-execute`** 按上列命令跑 `WC-DEMO-1` demo fixture execute（默认附带 `tests.test_run_wc_m2_e2e_walkthrough` 11 tests）；`continue-on-error: true` · **demo skeleton · non-prod · non-blocking**；产物仅 `artifacts/e2e/WC-DEMO-1/`。

**CI advisory（P9 payment sandbox）**：`.github/workflows/p9-payment-sandbox-smoke.yml` job **P9 payment sandbox smoke (advisory)** 跑 `--include-payment` sandbox DRAFT→PAID；`continue-on-error: true` · **sandbox-only · ≠ INT／prod／required** · GA-remote PASS run_id=`29159159265` · 票 `WH-P9-CI-payment-sandbox-smoke-v1`。

**边界**：本链为 Control Plane **demo / 非 prod E2E**，用于 M2/M3 本地验收与 CI advisory 观测；**不等于** INT Tier-A（见 runbook 文末 §INT gate 对齐）。Fixture execute／payment sandbox smoke **均未**接入 PR required 或 merge gate。加 **`--include-payment`** 可 sandbox 一鍵至 **PAID**（2026-06-24 · WC-M3）；**仍 ≠ prod 金流** · **≠ INT Tier-A**。

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
> **性质**：2026-06-14 多 lane 收口 + **WC-T6-T7-v2** gap closure；非 merge gate。细节见各票 `*_state.md`。  
> **摘要**：M3 契约骨架 **implemented + tested**；T6/T7 v0.1 gaps 已由 **WC-T6-T7-v2** 关闭，仍为 **accepted_with_gaps (v2)**——仅余 NonScope deferred；**不是** full M3 done（无 PR required / INT Tier-A 升格）。

- **WC-T5**：**done · accepted** — 契约文档 + `wc_t5_paths_v0.1` JSON 附录 + 结构契约测试已齐。
- **WC-T6**：**done · accepted_with_gaps (v2)** — distill CLI + cards/comms/reports fixture + 10 UT OK；`cp.ticket_state.b_report` 映射已文档化；deferred（NonScope）：生产 `artifacts/**` 增量扫描 · LLM 摘要 · forbidden severity 联动。
- **WC-T7**：**done · accepted_with_gaps (v2)** — runbook **v0.3** + WC-T5 path_id 附录 + doc regression UT；WD-P9-T2 已补 `--use-hitl-fixtures` demo fixture execute（**demo skeleton · 非 prod E2E**）；Wave-G 已接 CI advisory job `p9-wc-m2-fixture-execute`（**non-blocking**）；deferred（NonScope）：写 live STATE（forbidden · 仅 manual HITL）· LLM · 升格为 required check（须批文）。
- **WC-T6-T7-v2**：**done · accepted_with_gaps** — 联合 gap closure 票；索引 [`04_Workflows/tickets/WC-T6-T7-v2_state.md`](../../04_Workflows/tickets/WC-T6-T7-v2_state.md)。
- **WC-T1-INTEGRATION**：**implementer done · Reviewer pending** — eligibility gate 已接入 dispatch cards；**非** M2 全关。

### Wave C M4 · Control Plane 自动化升格治理（CP-AUTO）

- **WC-GOV-EXEC-ARTIFACTS-LLM**：**FRAME · doc-only** — CP-AUTO L0→L3 分级契约 SSOT · 承接 WC-T6-T7-v2 deferred 四项；**不含脚本/CI 施工** → [`docs/governance/WC_GOV_EXEC_ARTIFACTS_LLM_governance_contract.md`](../governance/WC_GOV_EXEC_ARTIFACTS_LLM_governance_contract.md) · [`04_Workflows/tickets/WC-GOV-EXEC-ARTIFACTS-LLM_state.md`](../../04_Workflows/tickets/WC-GOV-EXEC-ARTIFACTS-LLM_state.md)

## Wave C Phase 2 · Lane B Governance（2026-06-14 快照）

> **诚实边界**：Phase 2 Governance **目前仅 L1 advisory 已落地**（implemented + tested + Reviewer accepted）。L2 selective mandatory 与 mandatory smoke CI **尚未升格**——相关票均为 FRAME / design draft · **blocked_on_approval**；**不得**假设 PR required 或 branch protection 已改。

| 票号 | 状态 | 交付 / 边界 |
|------|------|-------------|
| **WC-IMPL-L1** | **done · implemented · accepted** | L1 advisory · MissingSignalRules v1 · **CI 仍 non-blocking exit 0** |
| **WC-IMPL-L2** | **frame_frozen_pending_governance** | L2 hard assert **设计稿 only** · 未改 branch protection |
| **WC-IMPL-SMOKE-CI-L1** | **frame_ready · blocked_on_approval** | optional_ci smoke step 提案 · CH-32～34 |
| **WC-PRE-06** | **design_ready · pending_approval** | `toolchain-observability-governance-upgrade-v1.md` |
| **WC-PRE-07** | **design_draft · blocked_on_approval** | smoke mandatory CI 设计稿 · 无批文不得改 PR required |

**观察期**：L1 自 2026-06-13 起算（见 `WC-IMPL-L1` D_REPORT）；L2 升格须 G1–G8 + 尚書省 `approval_status.L2=approved`。

## Wave C Phase 1 completion (Control Plane M2 + Governance v0.1)
> **宣告日**：2026-06-14  
> **性质**：Wave C Control Plane Phase 1 里程碑宣告；票级 SSOT 仍以 `04_Workflows/tickets/*_state.md` 为准。

### 范围（本阶段已交付）
| 分轨 | 内容 | SSOT |
|------|------|------|
| **M2 主链** | eligibility · dispatch plan/cards · comms · order intake | `docs/wave_c/WC_T1_eligibility.md` · `WC_T2_comms_minimal.md` · `docs/control_plane_dispatch_executor.md` · `docs/wave_c/WC_T4_order_ledger_design.md` |
| **Governance L1** | snapshot advisory（MissingSignalRules v1 · non-blocking exit 0） | `docs/governance/WC_PRE_06_07_rollout_plan.md` §3.6 · `04_Workflows/tickets/WC-IMPL-L1_state.md` |
| **M3 契约骨架** | T5 覆盖率契约 · T6 skill distillation lite · T7 E2E runbook + runner | `docs/wave_c/WC_T5_automation_coverage_contract.md` · `docs/wave_c/WC_T6_skill_distillation_lite.md` · `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` |
| **运营工具** | 本地 nightly smoke（`WC-DEMO-1` · 隔离 `artifacts/e2e/`） | `scripts/run_wave_c_nightly_smoke.sh` · overview 本页 §Nightly smoke |

### 状态（宣告日快照）
- Phase 1 视为完成：**implemented + tested** 可重复验证（M2 主链 + L1 advisory + T5/T6/T7 骨架）。
- **不是 full done**：W4-MEM-01 / WC-T1-INTEGRATION 仍 **Reviewer pending**；T6/T7 **accepted_with_gaps (v2)**（v0.1 gaps 已关；NonScope deferred 保留）；L2 / guard 升格 **blocked_on_approval**。
- 关键实现票（T1/T2/T3/T4、WC-IMPL-L1、WC-T5/T6/T7、WC-SMOKE-M2-NIGHTLY）Reviewer 结论为 `accepted` 或 `accepted_with_gaps`，gaps 保留在各票 C_REPORT。
- L2 selective mandatory：WC-PRE-06/07 与 WC-IMPL-L2 FRAME 已冻结，处于 L1→L2 观察期；**未**改任何 PR required / mandatory CI。

### 本阶段不含
- L2 merge gate（OG-TOOLCHAIN-HEALTH PR required · smoke 白名单 mandatory CI）。
- INT Tier-A 验收（Control Plane E2E / nightly pass ≠ INT pass）。
- Observability 产品轨 C1-P3+（与 WC-T 分轨，票号不合并）。
- 自动写 live `*_state.md`（`--use-hitl-fixtures` 仅写 `artifacts/e2e/` demo ledger，**不**写 live STATE）、自动开 Cursor chat、无 HITL 关票。

### 下一步（Phase 2 · 本轮回档后）
- **必做**：WC-T1-INTEGRATION Reviewer 关票；WC-T6-T7-v2 已关票（path_id · reports fixture 已补）。
- **blocked_on_approval**：WC-PRE-06/07 L2 · WC-IMPL-L2 · WC-IMPL-SMOKE-CI-L1。
- 观察期内仅本地/nightly 验证，仍保持 optional / non-gating。
- Lane A（最小接案 MVP Wave 4）：W4-MEM-01 Reviewer · W4-GUARD-01-IMPL（批文后）— 见 `docs/WAVE_PROGRESS_DASHBOARD.md` 多 Lane 收口表。

### Wave C 运营期工作模式（Phase 1 宣告后）
> 生效自 2026-06-14  
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
| E2E walkthrough（demo fixture execute · 非 prod） | `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures --json` |
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
| WC-PRE / IMPL | 8 | 0 | 0 | 8 |
| WC-C1 | 1 | 0 | 0 | 1 |
| WC-T + SMOKE + INTEGRATION | 8 | 1 | 0 | 9 |
| **合计** | **17** | **1** | **0** | **18** |

> **进行中**：WC-T1-INTEGRATION（Reviewer pending）。**blocked_on_approval**（不计入待办实施）：WC-PRE-06 L2 · WC-IMPL-L2 · WC-IMPL-SMOKE-CI-L1。

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
| `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` | Control Plane M2 E2E + INT gate 对齐（WC-T7 · v0.3 · 含 `--use-hitl-fixtures`） |
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
<!-- ticket:WC-T3 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T4 status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T5 status=Done owner=TBD milestone=M3 -->
<!-- ticket:WC-T6 status=Done owner=TBD milestone=M3 -->
<!-- ticket:WC-T7 status=Done owner=TBD milestone=M3 -->
<!-- ticket:WC-SMOKE-M2-NIGHTLY status=Done owner=TBD milestone=M2 -->
<!-- ticket:WC-T1-INTEGRATION status=In Progress owner=TBD milestone=M2 -->

---

*Wave C Overview · v0.3 · 2026-06-14 · doc-only · 状态以 registry 与 `*_state.md` 交叉校验*
