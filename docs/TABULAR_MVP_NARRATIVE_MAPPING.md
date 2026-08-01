# Tabular MVP Narrative Mapping — Supporting Rails vs Primary Product

> **Role**: Tabular MVP Noise Reduction Scribe · doc-only  
> **Date**: 2026-06-27  
> **Status**: v1 · **非** prod gate · **非** closure 宣称 · **不**改 Batch 1 治理裁決  
> **Landing SSOT**: `docs/TABULAR_MVP_SSOT.md`  
> **Governance guardrail**: Progress 末尾「2026-06-27 Governance Decisions — Batch 1」之 `non_claims` / `hard_no` / `defer_items` **仍有效**

**Narrative anchor**

> This repo's core product path is **tabular data cleaning and delivery automation**; governance / CI / GA lines are **supporting rails**, not the primary product outcome.

**Closure target (product value)**

> Current repo closure target for product value is tabular cleaning delivery readiness; governance/GA/CI lines remain supporting rails and should not block straightforward low-risk cleaning use cases unless explicitly required by policy.

---

## 1. Why this document exists

Repo 内并存多条 Phase / Wave / CI / GA 叙事线。若不标注角色，读者容易把 **GA-remote 待跑**、**WC-PRE 批文 pending**、**P7 Round-2 blocked** 等 **治理/supporting** 议题误读为「表格清洗主链未完成」或「不能交付 cleaning case」。

本档 **不删除、不推翻** 既有治理记录（含 Batch 1 YAML）；仅补 **产品主叙事 vs supporting rails** 的对照，供 planning / Progress / ticket 引用。

**Primary product outcome（当前）**

- 可重跑的 tabular cleaning 主链：`intake → gate → clean → bundle → deliver`
- 锚案：`cases/demo_phase/` · `cases/sampleco/2026-0001`
- 验收入口：`python scripts/run_case_e2e_validation.py` · `python scripts/run_mvp_mainline_regression.py`

**Not primary product outcome**

- Phase 全线收口、GA-remote 首跑回填、required CI 升格、prod provider flip、K-2 prod、Monitoring Graph L1/L2 等业务 **邻接/治理** 能力

---

## 2. Master mapping table

| 项目 / ID 或类别 | 当前角色 | 为何不是 Tabular MVP 主線 | 对主线的依赖 |
|------------------|----------|---------------------------|--------------|
| **Tabular cleaning main chain**（S1–S15 · `demo_phase` / `sampleco`） | **primary** | 即 repo 当前产品价值收口目标 | —（自身即主链） |
| **GA-remote observation**（`GOV-GA-P85-S2-01` · `GOV-GA-P9-PAY-01` · `GOV-GA-P7-ADV-01`） | **supporting**（governance · observation-only） | 远端 **单次观测** 与 merge gate / prod-ready **正交**；Batch 1 授权 **≠** 执行完成 | **无** — cleaning case 本地 E2E 不依赖 GA run_url |
| **CI-advisory landing**（yml on main · advisory job 绿） | **supporting** | Workflow 版控就位 **≠** GA-remote pass **≠** tabular 交付物 | **无** — 主链回归走 local runner |
| **WC-PRE-06/07**（toolchain health · mandatory smoke **设计**） | **deferred** | L1/L2 批文 pending · `design_ready` **≠** live gate · Batch 1 **defer** | **弱/可选** — tabular 主链可不跑 toolchain smoke matrix 完成交付 |
| **Required CI 升格**（G8 · branch protection · WC-PRE L2） | **deferred** | Batch 1 `hard_no` / `required_ci_execution_status: pending` | **无** — PR 已有 eval-gate + core-agent-smoke；tabular case 交付 **不** 绑定 WC-PRE 升格 |
| **P7 Round-2 execute**（`WH-P7-NOTIF-staging-integration-execute-v2` · `GOV-P7-R2-EXEC`） | **deferred**（blocked） | Staging 集成 **五顶 + POST 执行** 属通知/编排邻接线 · Batch 1 未裁定 | **无** — tabular intake/notify 实验线 **不** 阻塞 `run_case_e2e_validation` |
| **P7 prod flip / prod rollout bootstrap** | **future** | Prod 通知/编排 **非** cleaning 交付物 · 须 Batch 2+ 独立裁決 | **无** |
| **P9 payment sandbox smoke**（`GOV-GA-P9-PAY-01`） | **supporting**（sandbox · advisory） | Sandbox payment **≠** prod provider/ledger · **≠** merge gate | **无** — order ledger 路径为 **可选** 接案方式，非标准 cleaning 交付必要条件 |
| **P9 prod provider / prod ledger** | **future**（blocked · Batch 1 excludes） | 商业支付 prod 接線属 Phase 9 扩张 · `GOV-CI-P9-SANDBOX` hard_no 升格 | **无** — `PRODUCT_TABULAR_CLEANING` 不预设直写客户 DB 或 prod 支付 |
| **Monitoring Graph**（H 线 · L0/L1/L2） | **supporting**（adjacent · observability） | Ask API 侧车 · MVP CLI **当前不写入** Graph（见 `mvp-standard-trace-path.md` L2） | **无** — L0 可开可关，**不**参与 gate/clean/bundle 决策 |
| **K-2 LangGraph merge / prod rollout**（`GOV-GATE-K2-PROD` hard_no） | **future** | Ask 编排深化 · prod shadow/canary **非** tabular 清洗产出 | **无** |
| **Agent-lines CI / metrics / audit**（W10–W11 · `agent-lines-ci.yml`） | **supporting** | Agent 标准线 **观测与离线路径** · Wave 10 文档明示 **不影响主链运行** | **弱** — 可辅助 regression 认知；**非** case 交付判准 |
| **Orchestrator registry prod gates / Wave-G INT** | **supporting**（governance） | 控制面/registry **prod 门控** 属平台治理 · INT Tier-A **local mandatory · 不进 PR CI** | **无** — tabular demo case **不** 依赖 registry prod flip |
| **Phase full-line closure**（`GOV-PHASE-CLOSURE-FULL: NO`） | **deferred**（governance narrative） | 全线 Phase% 收口 **≠** tabular cleaning delivery readiness | **无** — 产品价值收口可独立于 Phase closure |
| **RAG / ask H 线 / Gov Core smoke** | **supporting**（adjacent platform） | 问答/RAG **非** 表格清洗交付物 | **无** |
| **Phase 8.x 商业编排 / order ledger / operator backlog HTTP** | **supporting**（commercial adjacent） | 订单/运营可见性 **邻接** tabular 接案 · **非** cleaning 核心产出 | **弱/可选** — 可走 `new_cleaning_case` 人工路径，不依赖 P8 HTTP |
| **P7 resume-loop MVP**（`GOV-RESUME-MVP-FULL` defer） | **supporting**（experimental） | HITL resume 编排 **实验** · 不升 prod resume gate | **弱** — 主链 E2E 今日 script 驱动；HITL 为设计/preview |
| **Non-tabular / shadow lines** | **deferred**（design / sandbox） | PDF/OCR/非表格 **shadow** · 明确 **非** Tabular MVP 首步 | **无** — 路由 catalog 将 non-tabular 与 tabular 分轨 |

---

## 3. Category narratives（保守敘事 · 可引用）

### 3.1 GA-remote · CI-advisory · evidence tiers

**角色**：supporting rails · governance observation

P7/P8.5/P9 的 GitHub Actions workflow 与 `GA-remote` 证据 tier 服务于 **远端观测与 Progress 物证回填**，Batch 1 已 **授权 observation-only** 三条 run，但 **Ops dispatch 仍 pending**、**无 run_url 不得宣称 GA pass**。

这些线 **不是** 当前 Tabular MVP 的 primary product outcome，也 **不应** 作为「能否交付一个 tabular cleaning case」的唯一判准。本地 `run_mvp_mainline_regression.py` / `run_case_e2e_validation.py` 才是主链就绪的 direct evidence。

**SSOT**：`docs/ga-remote-closure-checklist-v1.md` · `docs/p8_p89_evidence_index_v1.md` · `docs/evidence-tier-contract-v1.md`

### 3.2 WC-PRE · required CI · toolchain smoke

**角色**：deferred governance · design-ready · pending approval

WC-PRE-06（health gate）与 WC-PRE-07（mandatory smoke CI）是 **toolchain 治理升格提案**，Batch 1 对 L1 裁定 **defer**，required CI **blocked**，`hard_no` 禁止 AI 写成已 live。

Toolchain smoke / health dashboard **失败不阻断** Tabular MVP 主链（`blocks_mainline=false`）。升格 required CI 须尚书省批文 **独立于** tabular case 交付。

**SSOT**：`docs/required-ci-and-wc-pre-checklist-v1.md` · `docs/toolchain-observability-governance-upgrade-v1.md`

### 3.3 P7 Round-2 · staging execute · prod rollout

**角色**：deferred · blocked（Batch 1 excludes Round-2 execute）

P7 通知/staging 集成 Round-2（五顶 + S1–S4 POST + 48h 观测）属于 **平台通知邻接线**，票链 `execute-v2` **blocked**，**≠ prod flip**，**≠ required CI**。

Tabular cleaning 主链可在 **无** Round-2 GO 的情况下完成 gate → clean → bundle；notify 实验（S15）为 **experimental**，非 v1 交付必要条件。

**SSOT**：Progress Batch 1 `GOV-P7-R2-EXEC` · `04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md`

### 3.4 P9 payment · sandbox vs prod provider

**角色**：supporting（sandbox）/ future（prod provider blocked）

P9 payment sandbox smoke 验证 **sandbox adapter** 与 fixture 路径，Batch 1 GA 授权 **sandbox-only**；**prod provider / prod ledger 仍 blocked**（Batch 1 excludes）。

Payment **不** 是 tabular 清洗交付物的组成部分；order ledger 为 **可选** 接案编排，标准 Product Spec 以 **交付档案** 为主。

**SSOT**：`docs/internal/P9_payment_sandbox_CI_runbook.md` · `04_Workflows/order_ledger/`（邻接模块）

### 3.5 Monitoring Graph · K-2 · registry prod gates

**角色**：supporting（H 线 observability / ask 编排）/ future（prod gates hard_no）

Monitoring Graph **L0 only** 为 ask 侧 observability sidecar；**禁止** L1/L2 参与 selector/SLO（`GOV-GATE-MON-L2` hard_no）。K-2 prod rollout 同理（`GOV-GATE-K2-PROD` hard_no）。

Registry / orchestrator prod 门控属 **控制面治理**，与 `clean_phase_demo.py` → `build_case_delivery_bundle.py` **无直接依赖**。

**SSOT**：`AGENTS.md` Monitoring Graph 节 · `docs/k2_deployment_governance.md` · `docs/mvp-standard-trace-path.md` §L2

### 3.6 Agent-lines · Wave 10–12 · Phase 8.x commercial

**角色**：supporting · experimental adjacent

Agent-lines CI/metrics/audit（W10–W11）强化 **Agent 标准线** 可观测与离线路径；文档明确 **不阻塞主链**。Phase 8.x operator backlog / 商业交付 HTTP 为 **运营邻接**，非 C2-P1 Product Spec 核心交付包。

**SSOT**：`docs/agent-and-non-tabular-lines-readme-v2.md` · `docs/WAVE_PROGRESS_DASHBOARD.md`（治理视图 **≠** 产品 SSOT）

### 3.7 Phase closure · Dashboard Phase%

**角色**：deferred governance narrative

`GOV-PHASE-CLOSURE-FULL: NO` — Phase 全线收口 **尚未宣告**；Dashboard Phase% 为 **治理进度视图**，**不是** tabular cleaning delivery readiness 的 SSOT。

Batch 1 YES **≠** Phase% 上调 **≠** full closure。

**SSOT**：`docs/phase-closure-governance-playbook-v1.md` · `docs/WAVE_PROGRESS_DASHBOARD.md`（**未改** · 仅 cross-ref）

---

## 4. What *does* block tabular product delivery（诚实边界）

以下 **可以** 阻塞 **特定** tabular case 或 **主链回归**，但 **与 GA/WC-PRE/Round-2 正交**：

| 阻塞类 | 示例 | 与 supporting rails 关系 |
|--------|------|--------------------------|
| Case 级 gate | `rejected` · 缺 raw/schema | 主链业务规则 · **非** GA-remote |
| 主链 regression 红 | `run_mvp_mainline_regression.py` fail | release checklist **mandatory** · **非** WC-PRE-07 live |
| 政策显式要求 | 尚書省批文绑定某 CI | policy exception · 非默认 |

**Default rule**：低风险的 straightforward cleaning use case（有 schema、可解析 CSV、规模在 v1 基线内）**不应** 因 GA-remote pending、WC-PRE defer、Round-2 blocked 而被 **默认** 判为不可交付。

---

## 5. Quick cross-reference index

| 主题 | 文档 |
|------|------|
| 产品主链 SSOT | `docs/TABULAR_MVP_SSOT.md` |
| L1 trace / L2 adjacent | `docs/mvp-standard-trace-path.md` |
| GA-remote Ops | `docs/ga-remote-closure-checklist-v1.md` |
| Required CI / WC-PRE | `docs/required-ci-and-wc-pre-checklist-v1.md` |
| Phase closure governance | `docs/phase-closure-governance-playbook-v1.md` |
| Batch 1 裁決 YAML | `04_Workflows/00_Agent_Work_Progress.md` 末尾 |
| Smoke / regression contract | `docs/smoke-and-regression-contract-v1.md` |

---

## 6. Version & non-claims

| 项 | 状态 |
|----|------|
| 本档 | v1 · 2026-06-27 · Tabular MVP Noise Reduction Scribe |
| Batch 1 governance | **未改動** · 仅补叙事 mapping |
| Workflow yml / CI / Dashboard | **未改動** |
| Prod-ready / Phase closure | **未宣称** |

---

*Tabular MVP Narrative Mapping v1 · supporting rails ≠ primary product outcome · doc-only*
