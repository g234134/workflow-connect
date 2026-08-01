# W-MASTER-full-phase-plan — Full-Phase Master Control Plane State

> **handoff 摘要檔** · Full-Phase Master Orchestrator 總調度 · **doc-only · 非功能施工票**。  
> **目的**：將 Phase 1 → Phase 10.5 **全部未完成工作**收斂成 **10 個大任務群組**、每組 **3–6 張可執行 tickets**，供 Multi-Chat 並行消費；**不做 closure 宣稱** · **不改 Dashboard Phase%**。  
> **Phase% SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md` §Phase 完成度表 · **2026-06-26**（本票不重算）。  
> **後段战术线（P7+ planned tickets）**：`04_Workflows/tickets/W-MASTER-wave-plan_state.md` · **must 交叉讀，禁止雙份維護 Wave 1–5 正文**。  
> **Lane 索引**：`docs/full-phase-lane-map-v1.md`（8-Lane 橫向視圖 · 本票為 10-Group 縱向任務盤）。

---

## META

| 欄位 | 值 |
|------|-----|
| **Phase** | Global · Full-Phase 1–10.5 planning |
| **Lane** | Master control plane · Multi-Chat 編排 |
| **Owner** | Full-Phase Master Orchestrator |
| **Ticket type** | orchestration · frame · non-functional |
| **Playbook SSOT** | `docs/full-phase-master-planning-playbook.md` |
| **Wave Master 子盤** | `W-MASTER-wave-plan_state.md`（Wave 1–5 · P7+ 已規劃票） |
| **Wave-next 战术** | `W-ORCH-wave-next-control-plane-v1_state.md` |
| **Multi-Chat 角色** | `.cursor/rules/multi_chat_roles.mdc` · `docs/phase4-multi-agent-collaboration-contract-v1.md` |
| **planning_status** | `frame_ready` |
| **reviewer_verdict** | `pending`（待 Full-Phase Master Review） |
| **last_updated** | 2026-06-27 |
| **groundwork_governance_support** | **`ready`**（2026-06-27 · Groundwork Governance Closer） |

> **`groundwork_governance_support: ready` 语义**：Phase 收口 / GA-remote / required CI 三档 human-only playbook 已就绪（见 §Groundwork Governance Support）。**不**改变 `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% · **不**等于 GA/WC-PRE/required CI 已执行 · **不**等于 closure 已宣告。

---

## Groundwork Governance Support

> **Close-Out**：2026-06-27 · Groundwork Governance Closer · doc-only · 审计留痕见 `00_Agent_Work_Progress.md`「Groundwork Governance Close-Out」

| 栏位 | 值 |
|------|-----|
| **groundwork_governance_support** | **`ready`** |
| **execution_status** | GA-remote **pending/blocked** · WC-PRE-06/07 **pending** · required CI 升格 **pending/blocked** |
| **affects_phase_percent** | **`false`** — Dashboard SSOT 不变 |
| **closure_claimed** | **`false`** |

**三档 SSOT（人类 Phase 收口前先查）**

| 文档 | 用途 |
|------|------|
| `docs/phase-closure-governance-playbook-v1.md` | 裁決权 · 六维 evidence · AI/人类边界 |
| `docs/ga-remote-closure-checklist-v1.md` | GA-remote dispatch · run_url 回填 · ops RACI |
| `docs/required-ci-and-wc-pre-checklist-v1.md` | WC-PRE-06/07 批文 · required CI wiring |

**Playbook 索引**：`docs/full-phase-master-planning-playbook.md` §14.1 · §15

---

## Objective

建立 **全 Phase 總任務盤（Full-Phase Master CP）**，使後續 lane / wave chat 能在**統一邊界**下：

1. 覆蓋 **Phase 1–10.5** 全部域（非僅 P7+ path report）。
2. 將工作收斂為 **10 個大任務群組（G1–G10）**，每組 **3–6 張 tickets**。
3. 標記 **並行 vs 串行**、**已落地（不可重做）**、**關鍵缺口**、**human/infra/security-only**、**doc/spec-only**、**可直接 B/C/D/O 施工**。
4. 與既有 **W-MASTER-wave-plan**（Wave 1–5）**對齊不重複**：P7+ 執行票以 Wave Master 為準；本票補 **Phase 1–6 + 跨 Phase 編排** 與 **全盤索引**。
5. **禁止** closure 宣稱 · **禁止** 單方面修改 Dashboard Phase%。

**成功判準（本票）**：本 state + playbook 就緒；G1–G10 每組 ≥3 tickets；Parallelization plan 與 DNR 表凍結；lane chat 可依 §Output file map 寫入下游檔案。

---

## Current Baseline by Phase

> **權威**：`docs/WAVE_PROGRESS_DASHBOARD.md` · **2026-06-26** · 06-23→06-26 為**保守重估**（見 `00_Agent_Work_Progress.md` 2026-06-26 條）。**本表只引用，不重算。**

| Phase | **当前 %** | 姿態 | 關鍵已落地（摘要） | 關鍵缺口（blocking / 優先） |
|-------|-----------|------|-------------------|------------------------------|
| **P1** 治理層 | **90%** | 补最后缺口 | W1-T1B · ENGINEERING_CONTRACT · `.cursor/rules` · AGENTS | WC-PRE-06/07 批文 · W4-GUARD G2–G4 升格 |
| **P2** 知識層 / Index | **65%** | 中度缺口 | Phase1 ingest_verify · WA-T1 contract · RAG smoke | 规模化 index job · E2E 问答 · GraphRAG |
| **P3** 可觀測性 / Trace | **82%** | 补最后缺口 | gov-trace-v2 13/13 · `docs/observability.md` | Langfuse/PG 对齐 deferred · GA-remote evidence |
| **P3.5** 成本 / 模型治理 | **55%** | 中度缺口 | WA-T3 contract · eval-gate CI · K-2/ENF shadow | WC-IMPL-L2 blocked · mandatory CI 未开 |
| **P4** 多智能體協作 | **75%** | 中度缺口 | W5-T0 · WA-T4 contract · multi_chat_roles · commands MVP | W6-T10 cleanup · notify transport defer |
| **P5** Dashboard / 离线健康度 | **70%** | 中度缺口 | WB-T4 health · MP-METRICS HTTP · audit spec | Grafana/PG soak placeholder · P85 closure blocked |
| **P6** 测试 / 回归 gate | **72%** | 中度缺口 | INT gate contract · toolchain smoke matrix · MP/MC/CI-SMOKE local | required CI 未落地 · G-1–G-5 runtime · GA-remote pending |
| **P7** 自動客戶溝通 | **30%** | **大缺口** | Round-1 local GO · sandbox ~90% 子线 · advisory CI landing | Round-2 **五顶 blocked** · prod phase-1 ~54% · required CI 未落地 |
| **P7.5** Intake Gate | **45%** | **大缺口** | P75-G2/G3/G4 · P75-REG E2E · gate CLI | UI/SLO/alert · matrix G-1–G-5 runtime · policy deny MVP 票 |
| **P8** 商業化交付 | **45%** | **大缺口** | P8-T2 backlog · P8-API HTTP · MP-SMOKE 接線 | batch approve · resume-latest · webhook deferred |
| **P8.5** Browser / CU | **10%** | **大缺口** | L-local 14/14·7/7 · bridge-smoke.yml landing | Scenario2 GA 未跑 · in-memory stub · closure-scribe blocked |
| **P8.6** Tool Catalog | **65%** | 中度缺口 | WB-T1 · W3-T1 SSOT · tabular catalog | selector 消费 enabled:false · dark venv sync deferred |
| **P8.7** Selector | **60%** | 中度缺口 | WB-T1 contract · tabular selector | registry 生产默认 off · non-tabular 未接 |
| **P8.8** Executor / Sandbox | **58%** | 中度缺口 | WB-T2 contract · tabular executor | WC-PRE executor timeout · replay 非 Phase 8.8 |
| **P8.9** Outbox / Feedback | **40%** | **大缺口** | T1/T2/T3 · REG bundle · dispatch registry · metrics | HTTP webhook T4 · INT/real provider |
| **P9** 訂單 / 金流 | **20%** | **大缺口** | WC M2 landing · local 21/21 · e2e PAID sandbox | 首跑 run URL 未回填 · prod provider/ledger |
| **P10** 95% 自動化 | **35%** | **大缺口** | 15 步 ~86.7% · blueprint v2 · experiment orchestrator | S15 notify · intake API prod · prod 閉環 |
| **P10.5** 學習 / 蒸餾 | **30%** | **大缺口** | WC-T6 skeleton · W5-T1 registry · distill CLI | prod 蒸馏闭环 · T5/T7 v2 全量 mapping |

---

## Ten Task Groups — Phase Mapping

| Group | 名稱 | Covered Phases | 主 Lane（8-Lane） | 与 Wave Master 关系 |
|-------|------|----------------|-------------------|---------------------|
| **G1** | Governance · Approval · Model Gate | P1 · P3.5 · 跨 Phase 批文 | L1 | Wave 5：WC-PRE-06/07 |
| **G2** | Knowledge · Index · RAG Corpus | P2 | L2 | — |
| **G3** | Trace · Observability · Evidence Tier | P3 · P3.5 trace 轴 | L3 | Wave 5：W5-T3 observer |
| **G4** | Multi-Agent · Control Plane · Dispatch | P4 | L4 | Wave 5：W5-T1/T2/T5 · Wave 1–5 CP |
| **G5** | Dashboard · Metrics · Progress Closure | P5 | L5 | Wave 4：closure-scribe |
| **G6** | Test · Smoke · Regression · CI Gate | P6 | L6 | Wave 2：advisory CI · matrix |
| **G7** | Customer Comms · Intake Gate | P7 · P7.5 | L7 | **Wave 1–2** planned tickets |
| **G8** | Commercial Delivery · Browser / CU | P8 · P8.5 | L7 | **Wave 3–4** planned tickets |
| **G9** | Toolchain · Outbox · Feedback · Payment | P8.6–P8.9 · P9 | L7 | **Wave 3–4** + Toolchain WB-T* |
| **G10** | Full Automation · Skill Distillation | P10 · P10.5 | L8 | **Wave 5** P10 编排资产 |

---

## G1 — Governance · Approval · Model Gate

**Phase**：P1 (90%) · P3.5 (55%)  
**姿態**：补最后缺口（P1）+ 中度缺口（P3.5 批文边界）

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G1-01 | 治理收斂視圖 · ENGINEERING_CONTRACT · engineering-contract.mdc | `docs/governance-constitution-v1.md` · W1-T1B |
| DNR-G1-02 | P3.5 cost/model governance contract | `docs/phase3-5-cost-model-governance-contract-v1.md` · WA-T3 |
| DNR-G1-03 | WC-IMPL-L1 advisory snapshot（non-blocking） | `tests/test_toolchain_governance_snapshot_v1` |

### 關鍵缺口

- WC-PRE-06/07 **尚書省批文**前不得 L2 mandatory CI / branch protection
- governance_dual **真批文**（P7 Round-2 硬依赖）
- W4-GUARD G2–G4 schema/ratio 升格（approval 后）

### Tickets（G1 · 3–6）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **FP-G1-T1-governance-dual-unblock-frame-v1** | governance_dual 解阻 FRAME（五顶要件 checklist · 不负责真批文） | doc/spec | ∥ G1-T2 | 无 | **B→C doc** |
| **FP-G1-T2-wc-pre-06-07-approval-tracker-v1** | WC-PRE-06/07 批文追踪 SSOT（design_ready → approved 状态机） | doc/spec | ∥ G1-T1 | 无 | **B→C doc** · **human-only** 关票 |
| **FP-G1-T3-guard-schema-ratio-escalation-frame-v1** | W4-GUARD G2–G4 升格 FRAME（blocked_on_approval） | doc/spec | 串行 G1-T2 批文后 | WC-PRE 或 PM 批文 | **blocked** until approval |
| **FP-G1-T4-eval-gate-k2-enf-crossref-index-v1** | P3.5 eval-gate / K-2 / ENF shadow 交叉索引（防误开 blocking canary） | doc/spec | ∥ G1-T1 | 无 | **B→C doc** |
| **FP-G1-T5-constitution-progress-append-protocol-v1** | Progress/Dashboard 写入边界 doc（Governance 独占字段） | doc/spec | ∥ G1-T2 | 无 | **B→C doc** · Scribe 重 O |

---

## G2 — Knowledge · Index · RAG Corpus

**Phase**：P2 (65%)  
**姿態**：中度缺口

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G2-01 | Phase1 ingest_verify · AGENTS.md ingest · INV1–INV4 | `00_Agent_Work_Progress.md` D2/D3 |
| DNR-G2-02 | R1/R2 retrieve + Postgres cross-check | rag_query_agent smoke |
| DNR-G2-03 | WA-T1 knowledge indexing contract | `docs/phase2-knowledge-indexing-contract-v1.md` |

### 關鍵缺口

- **本轮无新 index job**（Dashboard 06-26）· 缺规模化排程
- E2E 问答 / GraphRAG / 监控评测

### Tickets（G2 · 3–6）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **FP-G2-T1-index-job-scheduler-hook-v1** | index job 触发 hook 设计 + skeleton CLI（不破坏 seed INV） | build | ∥ G2-T2 | 无 | **B→C→D** |
| **FP-G2-T2-phase2-index-contract-gap-audit-v1** | WA-T1 contract vs 实际 ingest 能力 gap 审计 doc | doc/spec | ∥ G2-T1 | 无 | **B→C doc** |
| **FP-G2-T3-rag-e2e-answer-frame-v1** | RAG E2E 问答 FRAME（LLM synthesis · 非本 sprint 施工） | doc/spec | 串行 G2-T2 | G2-T2 gap 清单 | **B only** · planning |
| **FP-G2-T4-graphrag-jobs-state-machine-v1** | graphrag_jobs 状态机设计 doc | doc/spec | ∥ G2-T3 | 无 | **blocked but worth planning** |
| **FP-G2-T5-smoke-corpus-expansion-v1** | smoke_corpus 扩展 FRAME（非种子 · 独立 verify 需求） | doc/spec | 串行 G2-T1 | PM 策略 | **blocked** on verify 策略 |

---

## G3 — Trace · Observability · Evidence Tier

**Phase**：P3 (82%) · P3.5 trace 轴  
**姿態**：补最后缺口

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G3-01 | gov-trace-v2 13/13 · observability.md | Dashboard P3 |
| DNR-G3-02 | p75 trace SSOT · p8_p89 evidence index | `docs/p75-intake-gate-control-plane-trace-v1.md` |
| DNR-G3-03 | P7 advisory CI 诚实索引 | `docs/P7_ADVISORY_CI_INDEX.md` · W2-P7-advisory-ci-ssot-index-v1 |

### 關鍵缺口

- Langfuse/PG 对齐 **deferred**
- P8/P8.9 delivery observability contract（W3-P89-OBS 待建）
- GA-remote run URL 证据 tier

### Tickets（G3 · 3–6）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **FP-G3-T1-evidence-tier-ssot-v1** | L-local / CI-advisory / GA-remote 证据 tier 统一 SSOT | doc/spec | ∥ G3-T2 | 无 | **B→C doc** · → `docs/evidence-tier-contract-v1.md` |
| **FP-G3-T2-p89-delivery-observability-contract-v1** | P8/P8.9 delivery observability contract doc | doc/spec | ∥ G3-T1 | 无 | **B→C doc** |
| **FP-G3-T3-langfuse-pg-alignment-deferred-index-v1** | Langfuse/PG 对齐 deferred 项索引 + 解阻条件 | doc/spec | 串行 G3-T1 | 无 | **blocked but worth planning** |
| **W5-T3-evidence-observer-v1** | evidence observer CLI（消费 trace 栏位） | build | ∥ G3-T1 | W5-T2 schema | **Wave 5 · B→C→D** |
| **FP-G3-T4-trace-canonical-schema-append-v1** | 新 trace 字段必须增 §Canonical schema 流程 doc | doc/spec | ∥ G3-T2 | 无 | **B→C doc** |

> **去重**：`W5-T3` 正文见 `W-MASTER-wave-plan` Wave 5；本组只索引。

---

## G4 — Multi-Agent · Control Plane · Dispatch

**Phase**：P4 (75%)  
**姿態**：中度缺口

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G4-01 | Multi-Chat 四角色 · phase4 contract | WA-T4 · multi_chat_roles.mdc |
| DNR-G4-02 | `.cursor/commands` MVP · wave-master schema | W5-T1 · W5-T2 |
| DNR-G4-03 | dispatch cards · WC-T1-INTEGRATION | `tests/test_dispatch_cards` |

### 關鍵缺口

- W6-T10 orchestrator cleanup（runtime redirect）
- W-MASTER vs W-ORCH 双 CP 叙事对齐
- notify transport 执行票（Master Plan 外 defer）

### Tickets（G4 · 3–6）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **W5-T1-multi-chat-commands-v1** | Multi-Chat commands SSOT | build | ∥ W5-T2 | 无 | **Wave 5 · done/维护** |
| **W5-T2-wave-master-ticket-template-v1** | ticket schema 模板 SSOT | build | ∥ W5-T1 | 无 | **Wave 5 · done/维护** |
| **W6-T10-cleanup-orchestrator-checkpoint-workarounds-v1** | orchestrator checkpoint cleanup | build | 串行 W6-T5/T6 | 整合层已 landed | **B→C→D** |
| **FP-G4-T1-dual-cp-narrative-alignment-v1** | W-MASTER-full-phase vs wave-plan vs W-ORCH 叙事对齐 doc | doc/spec | ∥ W5-T5 | 无 | **B→C doc** |
| **W5-T5-cross-wave-playbook-index-v1** | lane/playbook 索引 | doc/spec | ∥ G4-T1 | 无 | **Wave 5 · B→C doc** |
| **FP-G4-T2-dispatch-cards-eligibility-ut-v1** | dispatch eligibility 可选 UT（unresolved-dependency） | build | ∥ W6-T10 | WC-T1-INTEGRATION | **B→C→D** |

---

## G5 — Dashboard · Metrics · Progress Closure

**Phase**：P5 (70%)  
**姿態**：中度缺口

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G5-01 | toolchain health dashboard · audit quickview spec | WB-T4 · WB-T5 |
| DNR-G5-02 | MP-METRICS HTTP GET /metrics | `scripts/metrics_http_endpoint_v1.py` |
| DNR-G5-03 | `_ops_cycle.py` · Progress append 制度 | OPS_CYCLE.md |

### 關鍵缺口

- Grafana/PG soak placeholder
- P8.5 closure-scribe **blocked**（无 GA URL）
- fleet 聚合运维视图

### Tickets（G5 · 3–6）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **FP-G5-T1-fleet-metrics-dashboard-doc-v1** | MC-METRICS fleet 视图 operator doc | doc/spec | ∥ G5-T2 | 无 | **B→C doc** |
| **FP-G5-T2-grafana-pg-soak-placeholder-index-v1** | Grafana/PG soak deferred 索引 + infra 解阻条件 | doc/spec | ∥ G5-T1 | **infra-only** | **blocked but worth planning** |
| **WH-P85-wave-H2-closure-scribe-v1** | P8.5 closure rollup | scribe | 串行 GA URL | **human** Scenario2 GA | **blocked** · Scribe O |
| **FP-G5-T3-progress-append-template-v1** | lane chat Progress 末尾模板（含 evidence_tier） | doc/spec | ∥ G5-T1 | 无 | **B→C doc** · Scribe 重 O |
| **FP-G5-T4-audit-quickview-fleet-extension-v1** | audit quickview 多 case 聚合 FRAME | doc/spec | 串行 G5-T1 | WB-T5 | **B only** |

---

## G6 — Test · Smoke · Regression · CI Gate

**Phase**：P6 (72%)  
**姿態**：中度缺口

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G6-01 | INT gate contract · toolchain smoke matrix | WB-T7 · phase6 contract |
| DNR-G6-02 | MP/MC-SMOKE · CI-SMOKE local | Dashboard §Multi-phase smoke |
| DNR-G6-03 | MVP mainline 6/6 · Agent Lines CI suite | W1-T3B · W10-T1 |

### 關鍵缺口

- required CI **未落地**（WC-PRE-07 blocked）
- G-1–G-5 resume-loop **runtime**
- P7/P85/P9 advisory **GA-remote pending**

### Tickets（G6 · 3–6）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **W2-P7-matrix-G1-G5-resume-loop-v1** | matrix G-1–G-5 resume-loop spec/trace contract | doc/spec | ∥ G6-T2 | W1-P75-TRACE | **Wave 2 · B→C doc** |
| **W2-P7-advisory-ci-ssot-index-v1** | P7 advisory CI 诚实索引 | doc/spec | ∥ G6-T2 | 无 | **Wave 2 · B→C doc** |
| **FP-G6-T1-required-ci-unblock-frame-v1** | WC-PRE-07 mandatory CI FRAME（blocked_on_approval） | doc/spec | 串行 G1-T2 | 尚書省批文 | **blocked** |
| **FP-G6-T2-release-sanity-runbook-v1** | MP+MC+CI-SMOKE release 前 runbook 单页 SSOT | doc/spec | ∥ W2 票 | 无 | **B→C doc** |
| **FP-G6-T3-agent-lines-nightly-deferred-index-v1** | run-all-allowed nightly CI deferred 索引 | doc/spec | ∥ G6-T2 | 无 | **blocked but worth planning** |
| **FP-G6-T4-inspector-overclaim-spotcheck-v1** | wave-next inspector 抽样对照清单（Reviewer 用） | doc/spec | ∥ G6-T2 | inspector checklist | **B→C doc** |

---

## G7 — Customer Comms · Intake Gate

**Phase**：P7 (30%) · P7.5 (45%)  
**姿態**：**大缺口** · **Wave Master Wave 1–2 为主战场**

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G7-01 | P75-G2/G3/G4 + P75-REG E2E | gate layer · policy · notify · regression |
| DNR-G7-02 | P7 Round-1 local slot GO（S1–S4） | run_id `20260623T165252Z` |
| DNR-G7-03 | MP-SMOKE 七步 · intake.gate_decision notify | Dashboard §MP-SMOKE |

### 關鍵缺口

- P7 Round-2 **五顶 blocked**（governance_dual · Infra · Security · allowlist · receiver）
- UI / SLO / alert · matrix G-1–G-5 runtime

### Tickets（G7 · 引用 Wave Master + 本盘补票）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **W1-P75-POLICY-DENY-MVP-v1** | policy deny doc + phi_demo 探针 | build/doc | ∥ W1 其他 | P75-G3 | **Wave 1 · B→C→D** |
| **W1-P75-INTAKE-CLI-MVP-v1** | intake CLI upstream doc + 最小接線 | build/doc | ∥ W1 其他 | P75-G2 | **Wave 1 · B→C→D** |
| **W1-P75-TRACE-UPSTREAM-v1** | gate→outbox→smoke trace 契约 | doc/spec | ∥ W1 其他 | 无 | **Wave 1 · B→C doc** |
| **W1-P75-UPSTREAM-ENTRY-INDEX-v1** | P7.5 上游入口索引 | doc/spec | ∥ W1 其他 | 无 | **Wave 1 · B→C doc** |
| **W2-P7-staging-unblock-T1..T5** | Round-2 五顶解阻 spec（**非 execute**） | doc/spec | 串行 human 前置 | **human/infra/security** | **Wave 2 · blocked planning** |
| **W2-P7-matrix-G1-G5-resume-loop-v1** | matrix spec-only | doc/spec | ∥ W2 staging | W1-P75-TRACE | **Wave 2 · B→C doc** |

> **执行 SSOT**：Wave 1–2 票 FRAME 全文见 `W-MASTER-wave-plan_state.md` §Wave 1–2。

---

## G8 — Commercial Delivery · Browser / Computer Use

**Phase**：P8 (45%) · P8.5 (10%)  
**姿態**：**大缺口** · **Wave Master Wave 3–4**

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G8-01 | P8-T2 backlog · P8-API HTTP read-only | operator backlog |
| DNR-G8-02 | P8.5 L-local bridge smoke 14/14·7/7 | bridge-smoke.yml landing |
| DNR-G8-03 | delivery approval CLI · sandbox bundle | W8-T3 · W12-T1 |

### 關鍵缺口

- batch approve · resume-latest · webhook deferred（P8）
- Scenario2 GA · in-memory stub · closure-scribe blocked（P8.5）

### Tickets（G8 · 引用 Wave Master Wave 3–4）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **W3-P8-operator-batch-resume-frame-v1** | batch approve / resume-latest FRAME | doc/spec | ∥ W3 其他 | PM 裁定 | **Wave 3 · blocked planning** |
| **W3-P8-P89-advisory-ci-ssot-v1** | P8/P8.9 advisory CI 索引 | doc/spec | ∥ W3 其他 | 无 | **Wave 3 · B→C doc** |
| **W3-P89-verification-bundle-extend-v1** | P8.9 verification bundle 回归扩展 | build | 串行 P8.9-T3 | T3 landed | **Wave 3 · B→C→D** |
| **W4-P85-scenario2-ga-evidence-v1** | Scenario2 GA 证据链票 | scribe/ops | 串行 human dispatch | **human-only** GA | **Wave 4 · blocked** |
| **W4-P85-bridge-prod-gap-index-v1** | bridge stub vs prod browser 差距索引 | doc/spec | ∥ W4 GA | 无 | **Wave 4 · B→C doc** |
| **W4-P9-run-url-backfill-v1** | P9 CI 首跑 run URL 回填 | scribe/ops | ∥ W4-P85 | **human** workflow_dispatch | **Wave 4 · blocked** |

> **执行 SSOT**：Wave 3–4 票见 `W-MASTER-wave-plan_state.md` §Wave 3–4。

---

## G9 — Toolchain · Outbox · Feedback · Payment

**Phase**：P8.6 (65%) · P8.7 (60%) · P8.8 (58%) · P8.9 (40%) · P9 (20%)  
**姿態**：**大缺口**（contract 在 · runtime/prod 远）

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G9-01 | WB-T1–T3 toolchain contracts | tool catalog · executor · outbox |
| DNR-G9-02 | P8.9 T1/T2/T3 · dispatch registry · REG bundle | P8.9 tickets |
| DNR-G9-03 | P9 sandbox 21/21 · e2e PAID · WC M2 | payment sandbox smoke |
| DNR-G9-04 | W3-TL 四件套（Tabular MVP · 分轨） | Dashboard Wave 3-TL |

### 關鍵缺口

- HTTP webhook T4 · INT/real provider（P8.9）
- prod provider / ledger（P9）
- selector 生产 registry · dark venv sync（P8.6–8.8）

### Tickets（G9 · 3–6）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **FP-G9-T1-toolchain-runtime-gap-audit-v1** | WB-T1–T3 contract vs runtime gap 审计 | doc/spec | ∥ G9-T2 | 无 | **B→C doc** |
| **FP-G9-T2-p89-webhook-t4-frame-v1** | P8.9-T4 HTTP webhook FRAME（post-80% stretch） | doc/spec | 串行 PM | PM-D7 类裁定 | **blocked but worth planning** |
| **FP-G9-T3-p9-prod-ledger-gap-index-v1** | P9 prod provider/ledger gap 索引 | doc/spec | ∥ G9-T1 | 无 | **B→C doc** |
| **W4-P9-payment-sandbox-ci-run-v1** | P9 advisory CI 首跑证据 | scribe/ops | ∥ W4 run URL | **human** dispatch | **Wave 4 · blocked** |
| **FP-G9-T4-tabular-vs-phase88-tool-layer-index-v1** | W3-TL vs Phase 8.8 分轨禁止合并索引 | doc/spec | ∥ G9-T1 | 无 | **B→C doc** |
| **FP-G9-T5-wc-pre-selector-executor-runtime-v1** | WC-PRE selector plan_only · executor timeout 落地跟踪 | build | 串行 G9-T1 | WC-PRE closed | **B→C→D** |

---

## G10 — Full Automation · Skill Distillation

**Phase**：P10 (35%) · P10.5 (30%)  
**姿態**：**大缺口** · **Wave Master Wave 5 编排 + runtime defer**

### 已落地能力（不可重做）

| ID | 能力 | 证据索引 |
|----|------|----------|
| DNR-G10-01 | 15 步实验线 ~86.7% · orchestrator · checkpoints | W6/W7/W8 |
| DNR-G10-02 | blueprint v2 · skill-cards v2 | W7-T4 |
| DNR-G10-03 | distill_control_plane_skills_lite skeleton | WC-T6 |

### 關鍵缺口

- S15 notify gateway · intake API prod · prod 闭环
- prod 蒸馏闭环 · WC-T6/T7 v2 全量 mapping

### Tickets（G10 · 引用 Wave 5 + 本盘）

| Ticket ID | 目的 | 类型 | 并行 | 前置 | B/C/D/O |
|-----------|------|------|------|------|---------|
| **W5-T4-master-plan-review-checklist-v1** | Master Plan Review checklist 落盘 | doc/spec | ∥ W5 其他 | 无 | **Wave 5 · B→C doc** |
| **W5-WC-PRE-06-governance-spec-v1** | toolchain observability L0→L1 设计 | doc/spec | ∥ W5-WC-PRE-07 | 无 | **Wave 5 · doc-only** |
| **W5-WC-PRE-07-approval-workflow-v1** | mandatory CI 批文 workflow | doc/spec | ∥ W5-WC-PRE-06 | 无 | **Wave 5 · human-only 关票** |
| **FP-G10-T1-s15-notify-gateway-frame-v1** | S15 notify gateway FRAME（blocked on L7） | doc/spec | 串行 G7 解阻 | P7 Round-2 | **blocked but worth planning** |
| **FP-G10-T2-wc-t6-t7-v2-mapping-frame-v1** | WC-T6/T7 v2 全量 path_id mapping FRAME | doc/spec | ∥ G10-T1 | WC-T5/T6 | **B only** |
| **FP-G10-T3-automation-blueprint-gap-index-v1** | blueprint v2 G8-1–G8-10 缺口索引 | doc/spec | ∥ W5-T4 | W7-T4 | **B→C doc** |

---

## Shared Ticket Schema

> 基於 `04_Workflows/tickets/_templates/ticket_state.template.md` + Wave Master 扩展（`docs/wave-master-ticket-template-v1.md`）。**Full-Phase 子票 must 追加 `group_id` 栏。**

### FRAME 必填（标准 + Full-Phase 扩展）

```yaml
Goal: ""
Scope: []
NonScope: []
AllowedPaths: []
BlockedPaths: []
Dependencies: []
AcceptanceCriteria: []

# --- Wave Master 扩展（W1–W5 执行子票必填）---
wave_id: W1|W2|W3|W4|W5|null   # P7+ 执行票；Foundation 票可 null
group_id: G1|G2|...|G10         # Full-Phase 群组（必填）
lifecycle_phase: B|C|D|O
phase_targets: []               # 只列 Dashboard Phase 名；不写 %
estimated_cycles: 1|2
mvp_allowed: true|false
human_only_prereqs: []
infra_only_prereqs: []
security_only_prereqs: []
dependencies_detail:
  upstream_tickets: []
  downstream_groups: []         # G1–G10
  blocks_if_missing: []
risks: []
observability:
  verify_commands: []
  evidence_artifacts: []
  trace_fields: []
  success_signals: []
  failure_signals: []
non_claims: []
ticket_class: build|doc/spec|scribe/ops|blocked/planning
evidence_tier: L-local|CI-advisory|GA-remote|n/a
parallel_ok: true|false
```

> **evidence_tier 权威**：`docs/evidence-tier-contract-v1.md` · `docs/p8_p89_evidence_index_v1.md` §1。**禁止** `L-GA-remote` · `prod` 作为 tier 值。

### Ticket class 定义

| Class | 含义 | 可直接 B/C/D/O |
|-------|------|----------------|
| **build** | 代码/配置/测试增量 | **是**（FRAME 冻结后） |
| **doc/spec** | 文档/契约/索引/FRAME | **是**（C=doc diff） |
| **scribe/ops** | Progress/closure · GA 回填 | **O 重** · 常 **human-only** |
| **blocked/planning** | 值得规划但 AC 诚实 blocked | **B only** · 不得标 done |

---

## Parallelization Plan

### 全局硬依赖（必须串行）

```
G1 批文/解阻 FRAME ──► G6 required CI FRAME ──► G6 mandatory CI 施工（批文后）
G7 P75 上游（Wave 1）──► G7 P7 staging 解阻（Wave 2 · human 后）
G7/G8/G9 human 解阻 ──► G10 S15 notify / prod 闭环 runtime
G2 index 策略 ──► G2 smoke corpus 扩展
```

### 可并行带（Multi-Chat 建议分配）

| 并行带 | Groups | 条件 |
|--------|--------|------|
| **带 A · Foundation doc** | G1 · G2 · G3 · G4 · G5 · G6 的 doc/spec 票 | 无共享 mutation surface |
| **带 B · Wave Master 执行规划** | G7 Wave 1–2 · G8 Wave 3–4 · G9 Wave 4 · G10 Wave 5 | 各 chat 只写己 Wave 区块 |
| **带 C · Toolchain audit** | G9 FP-G9-T1/T4 · G4 W6-T10 cleanup | 不同模块 |
| **带 D · Scribe/closure** | G5 WH-P85-closure · G8/G9 run URL 回填 | **human 触发后** |

### 禁止并行（共享 mutation surface）

| Surface | 协调规则 |
|---------|----------|
| `delivery/notification_gateway_v1.py` | 单票 owner · G7 notify 先于 G9 dispatch hook |
| `scripts/run_agent_standard_case_experiment.py` S3 | G7 P75-G2 owner · G9 仅 post-emit |
| `.github/workflows/*` required 升格 | **G1 批文前禁止** · G6 单票 owner |
| Dashboard Phase% | **禁止任何 lane 并行修改** |

---

## Non-Claims

> 本 Master CP 及下游 lane chat **禁止**下列宣稱。权威：`docs/p8_p89_evidence_index_v1.md` · `wave-next-code-inspector-v1.md` · Dashboard §Wave-next 敘事。

| 禁止宣稱 | 正确表述 |
|----------|----------|
| 本计划完成 = 任何 Phase closure | doc-only 规划 · Phase% 不变 |
| L-local unittest = GA-remote / prod-ready | `evidence_tier: L-local` |
| CI yml landing = GA pass | landing + **pending GA-remote** |
| advisory CI 绿 = merge gate | `continue-on-error` · non-required |
| MP-SMOKE 七步绿 = P7 staging 完成 | Round-2 still **blocked** |
| bridge 14/14 = prod browser | in-memory stub · Scenario2 blocked |
| P9 21/21 = prod 金流 | sandbox · prod provider gap |
| PLAN_READY = P10 runtime 已排期 | G10 runtime 票 mostly **blocked/planning** |
| Wave 1–5 planned = 全部可立即施工 | 大量 **human-only / blocked** 票 |

---

## Human / Infra / Security Dependency Rules

| 类型 | 必须写清 | 缺失时 |
|------|----------|--------|
| **human_only** | 负责方 · 控制台动作 · 交付物（批文 ID / run URL / sign-off） | STATE=`blocked` · AC 不得写「已完成」 |
| **infra_only** | 逻辑环境名 · slot/endpoint/DNS · flip 授权 | defer execute 票 · 可开 planning/doc 票 |
| **security_only** | 审查类型 · sign-off 记录位置 | P7 Round-2 不得进入 execute |

### 全局 human-blocked 清单（不可包装成 AI 已完成）

1. **P7 Round-2** — governance_dual 批文 · Infra staging slot · Security 外部 POST · allowlist · receiver
2. **P8.5 Scenario2 GA** — Actions `scenario=scenario2` dispatch + run URL
3. **P9 / P85 CI 首跑** — push + `workflow_dispatch` + run URL 回填
4. **WC-PRE-06/07 · WC-IMPL-L2** — 尚書省批文前不得改 required CI / branch protection
5. **master_status 里程碑** — Governance 独占 · worker 不得 append

---

## B/C/D/O Enforcement

> 与 `W-MASTER-wave-plan` §B/C/D/O Enforcement Rule **相同**；Full-Phase 追加 **group_id** 追踪。

| 阶段 | 产出 | Multi-Chat | 关卡 |
|------|------|------------|------|
| **B** Build spec | FRAME 冻结 · AC · paths · 扩展栏 | Orchestrator | 无 FRAME 不得进 C |
| **C** Code/Config | diff · **B_REPORT** | Implementer | AllowedPaths 外禁止 |
| **D** Debug/Verify | **C_REPORT** | Reviewer | `needs_changes` → 回 C |
| **O** Observe/Trace | **D_REPORT** · Progress 末尾 | Scribe + Orchestrator | 无 C=`accepted*` 不得 O 关票 |

**Full-Phase 追加规则**

- 规划票（`ticket_class: doc/spec` · lifecycle B）**跳过** B_REPORT verification；执行阶段不得跳过 C_REPORT。
- `FP-*` 与 `W*-P*` 票必须互链 `dependencies_detail`，避免双份施工。
- Scribe **只 append** Progress · 不改 Dashboard Phase%。

---

## Phase >80% Rule

| 条件 | 允许 | 禁止 |
|------|------|------|
| Phase **≥80%** 且无 blocking gap | doc 索引 · cross-ref · Progress 叙事 | 重开大工程 · 架构重做 · 新 mandatory CI |
| Phase **≥80%** 且有明确 AC 缺口 | **单票** 只补该 AC · MVP 可 | 连带重写已 accepted 模块 |
| Phase **<80%**（本盘多数 Phase） | 依 Priority heuristic 开票 | 单票包打整 Phase |
| **06-26 基准无 Phase ≥80%** | 全盘按 **关键缺口** 排序 · 不触发「>80% 仅补最后一档」简化 | 沿用 06-23 偏高 % 做规划 |

**判定 SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md` 该 Phase 列 + 对应 `*_state.md` C_REPORT。

**Priority heuristic**（同 Wave Master）：blocking → cross-wave glue → 80% 边界关键缺口 → observability/doc → deferred。

---

## Progress / Dashboard / Reviewer Protocol

### Dashboard

- **唯一 Phase% SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md`（2026-06-26）
- lane chat / ticket / Progress **不得**自行修改 Phase% 数字
- 上调 Phase% 仅尚書省 / 授权 Governance **append** Progress + Dashboard 同步

### Progress

- **仅末尾 append**：`04_Workflows/00_Agent_Work_Progress.md`
- 每条须含：`ticket_id` · `group_id` · 命令摘要 · 关键 `ok`/计数 · `evidence_tier` · blocked/next
- GA/CI 首跑必须 `run_url` + `run_id` 已回填或标 `pending`
- 可选：`_ops_cycle.py validate-report` → `append-report`

### Reviewer

1. **只读施工** — 不改 yml required · 不跑 prod/staging 真执行 · 不调 Phase%
2. **SSOT 位阶** — 子票 STATE ＞ 本票 ＞ `W-MASTER-wave-plan` ＞ chat 口述
3. **Evidence tier** — 无 run URL 不得 GA-remote verdict
4. **Full-Phase Master Review** — 对照 `docs/full-phase-master-planning-playbook.md` §6 checklist
5. **Verdict** — `PLAN_READY` | `PLAN_WITH_GAPS` | `PLAN_REJECT` → 写入本票 C_REPORT

---

## Output File Map

> 后续各 lane chat **应写入**的档案（按角色 · 禁止写错 ownership）。

| 产出类型 | 路径 | 负责角色 | 备注 |
|----------|------|----------|------|
| Full-Phase Master state | `04_Workflows/tickets/W-MASTER-full-phase-plan_state.md` | Master Orchestrator | 本票 · G1–G10 索引更新 append |
| Full-Phase playbook | `docs/full-phase-master-planning-playbook.md` | Master Orchestrator | 制度修订须 Reviewer |
| 8-Lane 索引 | `docs/full-phase-lane-map-v1.md` | Master Orchestrator / G4 | 与 10-Group 交叉引用 |
| Wave Master state | `04_Workflows/tickets/W-MASTER-wave-plan_state.md` | Wave Master Orch | **P7+ planned tickets 唯一正文** |
| Wave-next 战术 | `04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md` | Wave-next Orch | P7/P85/P9 并行 lane |
| 子票 STATE | `04_Workflows/tickets/<TICKET-ID>_state.md` | Orchestrator 开 · I/R/S 填 REPORT | 复制 template |
| Progress 末尾 | `04_Workflows/00_Agent_Work_Progress.md` | Scribe | **仅 append** |
| Dashboard | `docs/WAVE_PROGRESS_DASHBOARD.md` | Governance 授权 | **本计划不修改** |
| master_status | `04_Workflows/project_status/master_status.md` | Governance 独占 | worker 禁止 |
| P7.5 trace | `docs/p75-intake-gate-control-plane-trace-v1.md` | G7 / Wave 1 | W1-P75-TRACE 消费 |
| Evidence index | `docs/p8_p89_evidence_index_v1.md` | G3 / G8 / G9 | tier 对照 |
| Advisory CI 索引 | `docs/P7_ADVISORY_CI_INDEX.md` | G6 / G7 | W2-P7-advisory |
| Matrix | `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` | G6 / G7 | G-1–G-5 |
| Inspector | `04_Workflows/review_checklists/wave-next-code-inspector-v1.md` | Reviewer | over-claim 拦截 |
| Commands | `.cursor/commands/*.md` | G4 / Wave 5 | W5-T1 SSOT |
| **Schema template** | `docs/ticket-schema-master-v1.md` · `docs/wave-master-ticket-template-v1.md` | G4 / Wave 5 | W5-T2 SSOT |
| Evidence tier contract | `docs/evidence-tier-contract-v1.md` | G3 | tier 对照 |

---

## Do Not Re-Build Registry（全局摘要）

> 完整 10 组内 DNR 见各 G* 节 · 与 `full-phase-lane-map-v1.md` §5 对齐。

| ID | 已落地 | 禁止 | 允许 |
|----|--------|------|------|
| DNR-01 | W1–W4 Tabular MVP 主链 6/6 | 重写 routing engine | 单点 bugfix 票 |
| DNR-02 | W3-TL 四件套 + W4 glue | 合并 Tabular/Phase8.8 | 分轨索引 |
| DNR-03 | P75-G2/G3/G4 + P75-REG | 重开 gate layer | UI/SLO/alert 缺口票 |
| DNR-04 | MP/MC/CI-SMOKE CLI | 新 orchestrator 取代七步 | 增量 flag |
| DNR-05 | W6-T5/T6 checkpoint 整合层 | inline checkpoint 重写 | W6-T10 cleanup |
| DNR-06 | W10-T2 registry fail-closed（env off） | prod gate 默认开 | strict opt-in 文档 |
| DNR-07 | Master CP schema/commands（W5-T1/T2） | Wave 双份维护 | Wave 1 只消费 |
| DNR-08 | P8.5 L-local 14/14·7/7 | prod browser / required CI | GA-remote 证据票 |
| DNR-09 | P9 sandbox 21/21 + e2e PAID | prod provider/ledger | 首跑 URL 票 |
| DNR-10 | 憲法/合約/AGENTS | 规则档重定义禁區表 | 索引/append |

---

## Cross-References

| 类型 | 路径 |
|------|------|
| Playbook | `docs/full-phase-master-planning-playbook.md` |
| 8-Lane map | `docs/full-phase-lane-map-v1.md` |
| Wave Master | `04_Workflows/tickets/W-MASTER-wave-plan_state.md` |
| Wave Master playbook | `docs/wave-master-ticketing-playbook.md` |
| Master Plan Review | `docs/WAVE_MASTER_PLAN_REVIEW_2026-06-26.md` |
| Dashboard SSOT | `docs/WAVE_PROGRESS_DASHBOARD.md` |
| Phase closure playbook | `docs/phase-closure-governance-playbook-v1.md` |
| GA-remote checklist | `docs/ga-remote-closure-checklist-v1.md` |
| Required CI / WC-PRE checklist | `docs/required-ci-and-wc-pre-checklist-v1.md` |
| 80% 整合计划 | `04_Workflows/plans/multi-phase-80-percent-execution-plan.md` |
| WORKFLOW_INDEX | `04_Workflows/WORKFLOW_INDEX.md` |

---

## STATE

```yaml
overall_status: frame_ready
planning_status: frame_ready
reviewer_verdict: pending
lifecycle_phase: B
current_owner: full-phase-master-orchestrator
next_action: "Lane planners 依 G1–G10 开 FP-* 子票 FRAME；P7+ 执行消费 W-MASTER-wave-plan Wave 1–5"
last_updated: 2026-06-26
groups_defined: G1-G10
tickets_indexed: 52  # 含 Wave Master 引用票 + FP-* 新规划票
phase_percent_modified: false
closure_claimed: false
groundwork_governance_support: ready  # doc-only · does NOT affect Phase% · GA/WC-PRE/required CI still pending
groundwork_governance_close_out: 2026-06-27
```

---

*W-MASTER-full-phase-plan · Full-Phase Master Orchestrator · 2026-06-27 · doc-only · Phase% frozen at Dashboard 06-26*
