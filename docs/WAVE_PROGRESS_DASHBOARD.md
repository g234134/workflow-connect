# Wave Progress Dashboard — Tabular MVP · Governance / Routing / Tool Layer

> **成文日期**：2026-06-10  
> **角色**：Orchestrator 進度索引（doc-only）  
> **SSOT**：本檔為 **Tabular MVP Wave 1–Wave 8** 完成度總覽；票級細節見 `04_Workflows/tickets/*_state.md`。

---

## Wave A · Phase Foundations

| 票号 | 状态 | Phase | 交付摘要 |
|------|------|-------|----------|
| **WA-T1-phase2-knowledge-indexing-contract-v1** | **done** · accepted_with_gaps | **P2 65%→82%** | 收录契约 SSOT → `docs/phase2-knowledge-indexing-contract-v1.md` · `python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v` |
| **WA-T6-phase6-int-regression-gate-runbook-and-ci-integration-v1** | **done** · accepted_with_gaps | **P6 72%→90%** | INT gate SSOT → `docs/phase6-int-regression-gate-contract-v1.md` · 附录 A tool-chain optional smoke matrix (WB-T4) · `python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v` |
| **WB-T7-phase6-toolchain-smoke-matrix-extension-v1** | **done** · **accepted** | **P6 84%→88%** | YAML SSOT → `routing/toolchain_smoke_matrix_v1.yaml` · P6 附录 A 引用 · `python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v` |

> **註（Wave A · 2026-06-12）**：上表状态列以各票 `*_state.md` `C_REPORT` 为准。**Wave B · Toolchain: done · accepted_with_gaps_deferred_to_WC-PRE**（WB-T1–T8 + WC-PRE-01～05 Reviewer 已关票）；详见下方「Wave B · Toolchain」分栏註脚。

**票 state**：`04_Workflows/tickets/WA-T1-phase2-knowledge-indexing-contract-v1_state.md` · `04_Workflows/tickets/WA-T6-phase6-int-regression-gate-runbook-and-ci-integration-v1_state.md` · `04_Workflows/tickets/WB-T7-phase6-toolchain-smoke-matrix-extension-v1_state.md`

---

## 命名空間（勿混淆）

| 名稱 | 含義 | 索引 |
|------|------|------|
| **本 Dashboard** | 治理收口 + MVP trace／回歸 + Intake／Routing／Eval + Tabular Tool Layer（`W3-TL-*`） | 本檔 |
| **Observability Wave B** | Phase 2/3 知识索引 · eval/trace · `WAVE-B-P*` | `docs/WAVE_B_EXECUTION_PLAN.md` |
| **Toolchain Wave B** | Phase 8.5–8.9 底層 contract · outbox · toolchain health · `WB-T*` | `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` · `docs/wave-b-toolchain-readme-v1.md` |
| **Tabular Tool Layer** | Tabular MVP 实现四件套 · `W3-TL-*` | `docs/tabular-tool-catalog-v1.md` 等 |
| Observability V2 Wave 1–3 | Monitoring／Structured Errors／Retry·DLQ（`gov_core_system`） | `docs/WAVE1-3_HISTORY_STATUS.md` |
| 最小接案 MVP Wave 1–4 | `cases/` 結構、gate、E2E、`new_cleaning_case.py` | `04_Workflows/00_Agent_Work_Progress.md` →「最小接案 MVP · Wave 1–4」 |

---

## Phase 完成度表（Toolchain + 跨轨 · SSOT）

> **口径**：本表为 **Phase% 唯一 SSOT**；readme / 执行计划 **仅引用**。`cases/demo_phase/raw/Phase.csv` 为 Tabular 输入 maturity 范例，**不是**本表数据源。  
> **结构 / 权责 / P5·P6 指标槽**：`docs/wave-progress-dashboard-skeleton-v1.md`（数字轨 vs 叙事轨 · **不重算 %**）。  
> **最近寫入（2026-07-13）**：W-PROG A/B · triple／P8 鏈 · wave013 · `P8 92→100`（via `_phase_pct_apply.py`）；數字以下方「当前」列／Gauge 為準。

| Phase | 基线（06-12） | 当前（07-13 · W-PROG-wave013） | 主要票 | 证据摘要 |
|-------|-------------|---------------------------|--------|----------|
| **P1** 治理層 | ~92% | **91%** | W1-T1B · WA-T3 | `governance-constitution-v1.md` · `ENGINEERING_CONTRACT.md` · 本轮无新票 |
| **P2** 知識層 / Index | 65%→82% | **68%** | WA-T1 · **C2-P2 Tabular** · **FP-G2-T6** | `phase2-knowledge-indexing-contract-v1.md` · Tabular 子域 C2-P2 · **index hook thin runtime**（fixture dry-run · ≠ prod ingest）· 全局 RAG job 仍 gap |
| **P3** 可觀測性 / Trace | Done | **82%** | WA-T3 · trace v2 · **C2-P2 Tabular** | `docs/observability.md` · gov-trace-v2 13/13 · **Tabular 子域**：automation run log + ops summary · Langfuse/PG 对齐仍 deferred |
| **P4** 多智能體協作 | 75%→85% | **78%** | WA-T4 · W5-T0 · **W5-T1 Multi-Chat** | `phase4-multi-agent-collaboration-contract-v1.md` · **07-13 W-PROG-B +2**：ticket commands／skill／`multi_chat_roles.mdc` 落地（編排層 · ≠ prod multi-agent runtime） |
| **P5** Dashboard / 离线健康度 | 70%→85% | **73%** | WB-T4 · **MP-METRICS-HTTP** · **P5-metrics stub** | toolchain health + **metrics HTTP** `GET /metrics` + Grafana/JSON 對照 stub；Grafana/PG soak 仍 placeholder · **W-PROG-wave013 +2** |
| **P6** 测试 / 回归 gate | 84%→88% | **91%** | WB-T7 · **WF-P6-INT-CI-LANDING** · **C2-P2 Tabular** | INT gate contract · Tier-A live 112/112 · **Track B nightly + Track A PR optional CI landed**（`p6-int-gate-nightly.yml` · `p6-int-gate-pr-optional.yml` · **非** PR mandatory）· 綠日鐘 **≥7/7 已滿**（DAY7=`29568619424`）· 裁決包 `docs/governance/p6_uplift_decision_pack_83_to_91_v1.md` · **83→91 待尚書省再簽**（≠ 自動 uplift） |
| **P7** 自動客戶溝通 | ~48%→52% | **30%** | **WD-P7-T*** · **WH-P7-NOTIF-*** · **WH-P7-PROD-*** | **Round-1 local slot validated**（run_id `20260623T165252Z` · S1–S4 GO · simulated governance_dual）；**H1 approved** `GOV-DUAL-APPROVAL-2026-07-13-01`（具名 2026-07-28 · war_status v2.63）；**Round-2 execute-v2 仍 `blocked`／armed-not-run**（H2–H5：Infra／Security／allowlist／receiver · 無 P-GO）；sandbox **~90%** · prod phase-1 adapter+unittest **ready**。**≠ Round-2 GO · ≠ prod-ready · ≠ 客戶 staging endpoint**；required CI **未落地** |
| **P7.5** Intake Gate | ~62%→75% | **51%** | **P75-G2/G3/G4 · P75-REG · P75-G5 · P75-G6/G7 · W3-SMOKE** | gate layer + policy + notify + E2E + SLO probe + **alert sink + HTTP gate stub + 煙霧串線**；UI／prod alert 未做 · **W-PROG-wave013 +3** |
| **P8** 商業化交付 / Operator | ~68%→78% | **100%** | **P8-T2 · P8-T2b · P8-T2c · P8-T3-mock · P8-API · MP-SMOKE** · **BATCH-MVP-02/03/04** | backlog + batch/resume + **checkpoint preview** · **notify mock／DLQ／replay**（≠ prod webhook · ≠ 真 Worker）· HTTP API · Tabular · batch mock E2E |
| **P8.5** Browser / Computer Use | 55%→72% | **20%** | **WD-P85-T*** · **WH-P85-*** | **Scenario1 / CI-LAND OK**；dom-port + CI 17→20 + run-record；**W-PROG-B +2**：Scenario2 **GA-remote recorded**（run `29157178993` · evidence SSOT complete）· ops-run **`done`**；bridge **≠ prod browser · ≠ required CI · ≠ Playwright** |
| **P8.6** Tool Catalog SSOT | 65%→85% | **66%** | WB-T1 · **P868 inspect** | `tool-catalog-and-selector-contract-v1.md` · runtime inspect catalog · **W-PROG-wave013 +1** |
| **P8.7** Selector 推荐契约 | 60%→85% | **61%** | WB-T1 · **P868 inspect** | 同上 §4 · selector `plan_only` inspect · **W-PROG-wave013 +1** |
| **P8.8** Executor / Sandbox | 58%→82% | **59%** | WB-T2 · **P868 inspect** | `tool-executor-and-sandbox-safety-contract-v1.md` · executor `dry_run` inspect · **W-PROG-wave013 +1** |
| **P8.9** Outbox / Feedback | 40%→72% | **41%** | **P8.9-T1/T2/T3 · P8.9-REG · MP-METRICS · WD-P7-T2 · P89-W2** | consumer + feedback ack + **dispatch registry** + metrics；**T4=WD-P7-T2 webhook sandbox landed**；operator fields 投影；**W-PROG-wave013 +1**；仍缺 staging／prod SLA · Wave 4 UI |
| **P9** 訂單 / 金流閉環 | ~55%→58% | **24%** | WC-T1–T7 · **WD-P9-T1/T2** · **WH-P9-M2-INT** · **WH-P9-CI-*** | sandbox happy-path + advisory CI landing + 本地 21/21；**W-PROG-B +2**：首跑 **RUN_URL recorded**（`29159159265` · evidence SSOT complete）；**≠ required · ≠ merge gate · ≠ prod／INT**；prod provider／ledger **仍 gap** |
| **P10** 95% 全自動化閉環 | ~45% | **37%** | W6–W8 · W7-T4 · **W5 Wave Master** · **C2-P2 Tabular** | 實驗線 auto ≈86.7% · Tabular near-auto；**W-PROG-B +2**：Wave Master templates／commands／INDEX §1.55／ticket schema relay（編排資產 · **≠** P10 runtime 95%／prod 閉環） |
| **P10.5** 學習 / Skill 蒸餾 | ~28% | **30%** | WC-T6 · W5-T1 registry | `distill_control_plane_skills_lite` skeleton · 无 prod 蒸馏闭环 |

### Phase Completion Gauge（2026-07-28 · W-PROG · `_phase_pct_apply`）

> **口径**：下列 `completion` 为 **全局 Phase%**（本表「当前」列）；**≠** Tabular 子域独立 Phase%。`cases/demo_phase/raw/Phase.csv` 为 Tabular 输入 maturity 范例，**不是**本表数据源。

| Phase | completion | prev | delta |
|-------|------------|------|-------|
| P1 治理層 | **91%** | 90% | **+1%** |
| P2 知識層 / Index | **68%** | 66% | **+2%** |
| P3 可觀測性 / Trace | **82%** | 82% | 0 |
| P3.5 成本 / 模型治理 | **55%** | 55% | 0 |
| P4 多智能體協作 | **78%** | 77% | **+1%** |
| P5 Dashboard / 离线健康度 | **73%** | 72% | **+1%** |
| P6 测试 / 回归 gate | **91%** | 83% | **+8%** |
| P7 自動客戶溝通 | **30%** | 30% | 0 |
| P7.5 Intake Gate | **51%** | 49% | **+2%** |
| P8 商業化交付 / Operator | **100%** | 92% | **+8%** |
| P8.5 Browser / Computer Use | **20%** | 18% | **+2%** |
| P8.6 Tool Catalog SSOT | **66%** | 65% | **+1%** |
| P8.7 Selector 推荐契约 | **61%** | 60% | **+1%** |
| P8.8 Executor / Sandbox | **59%** | 58% | **+1%** |
| P8.9 Outbox / Feedback | **41%** | 40% | **+1%** |
| P9 訂單 / 金流閉環 | **24%** | 22% | **+2%** |
| P10 95% 全自動化閉環 | **37%** | 35% | **+2%** |
| P10.5 學習 / Skill 蒸餾 | **30%** | 30% | 0 |

**单行索引（playbook / Progress 可引用）**：

- Phase 1: completion **91%** (prev 90%, delta **+1%**)
- Phase 2: completion **68%** (prev 66%, delta **+2%**)
- Phase 3: completion **82%** (prev 82%, delta 0)
- Phase 3.5: completion **55%** (prev 55%, delta 0)
- Phase 4: completion **78%** (prev 77%, delta **+1%**)
- Phase 5: completion **73%** (prev 72%, delta **+1%**)
- Phase 6: completion **91%** (prev 83%, delta **+8%**)
- Phase 7: completion **30%** (prev 30%, delta 0)
- Phase 7.5: completion **51%** (prev 49%, delta **+2%**)
- Phase 8: completion **100%** (prev 92%, delta **+8%**)
- Phase 8.5: completion **20%** (prev 18%, delta **+2%**)
- Phase 8.6: completion **66%** (prev 65%, delta **+1%**)
- Phase 8.7: completion **61%** (prev 60%, delta **+1%**)
- Phase 8.8: completion **59%** (prev 58%, delta **+1%**)
- Phase 8.9: completion **41%** (prev 40%, delta **+1%**)
- Phase 9: completion **24%** (prev 22%, delta **+2%**)
- Phase 10: completion **37%** (prev 35%, delta **+2%**)
- Phase 10.5: completion **30%** (prev 30%, delta 0)


### Phase 完成度进度条（2026-07-28 · W-PROG · `_phase_pct_apply` · 人读 Gauge）

> **bar**：20 格 · `█` = 已完成 · `░` = 未完成 · **≠** CI gate · **≠** Tabular 子域独立 Phase%

- Phase 1 治理層：上一版 90% → 目前版 91%（**+1**）  
  `██████████████████░░` **91%**
- Phase 2 知識層 / Index：上一版 66% → 目前版 68%（**+2**）  
  `██████████████░░░░░░` **68%**
- Phase 3 可觀測性 / Trace：上一版 82% → 目前版 82%（调整 0）  
  `████████████████░░░░` **82%**
- Phase 3.5 成本 / 模型治理：上一版 55% → 目前版 55%（调整 0）  
  `███████████░░░░░░░░░` **55%**
- Phase 4 多智能體協作：上一版 77% → 目前版 78%（**+1**）  
  `████████████████░░░░` **78%**
- Phase 5 Dashboard / 离线健康度：上一版 72% → 目前版 73%（**+1**）  
  `███████████████░░░░░` **73%**
- Phase 6 测试 / 回归 gate：上一版 83% → 目前版 91%（**+8**）  
  `██████████████████░░` **91%**
- Phase 7 自動客戶溝通：上一版 30% → 目前版 30%（调整 0）  
  `██████░░░░░░░░░░░░░░` **30%**
- Phase 7.5 Intake Gate：上一版 49% → 目前版 51%（**+2**）  
  `██████████░░░░░░░░░░` **51%**
- Phase 8 商業化交付 / Operator：上一版 92% → 目前版 100%（**+8**）  
  `████████████████████` **100%**
- Phase 8.5 Browser / Computer Use：上一版 18% → 目前版 20%（**+2**）  
  `████░░░░░░░░░░░░░░░░` **20%**
- Phase 8.6 Tool Catalog SSOT：上一版 65% → 目前版 66%（**+1**）  
  `█████████████░░░░░░░` **66%**
- Phase 8.7 Selector 推荐契约：上一版 60% → 目前版 61%（**+1**）  
  `████████████░░░░░░░░` **61%**
- Phase 8.8 Executor / Sandbox：上一版 58% → 目前版 59%（**+1**）  
  `████████████░░░░░░░░` **59%**
- Phase 8.9 Outbox / Feedback：上一版 40% → 目前版 41%（**+1**）  
  `████████░░░░░░░░░░░░` **41%**
- Phase 9 訂單 / 金流閉環：上一版 22% → 目前版 24%（**+2**）  
  `█████░░░░░░░░░░░░░░░` **24%**
- Phase 10 95% 全自動化閉環：上一版 35% → 目前版 37%（**+2**）  
  `███████░░░░░░░░░░░░░` **37%**
- Phase 10.5 學習 / Skill 蒸餾：上一版 30% → 目前版 30%（调整 0）  
  `██████░░░░░░░░░░░░░░` **30%**


---

## 總覽表

| Wave | 主題 | 狀態 | 關鍵票 | 主要 spec / SSOT |
|------|------|------|--------|------------------|
| **Wave 1** | MVP 主鏈與治理 | **done** | W1-T1B · W1-T2-mvp-trace-path · W1-T3B | `docs/governance-constitution-v1.md` · `docs/mvp-standard-trace-path.md` · `docs/mvp-mainline-regression.md` |
| **Wave 2** | Intake / Routing / Eval | **done** | W2-T1-intake-routing-catalog · W2-T2-routing-eval | `docs/intake-routing-catalog-v1.md` · `routing/intake_routing_catalog_v1.yaml` · `docs/routing-eval-guide-v1.md` · `routing/routing_eval_cases_v1.yaml` |
| **Wave 3-TL** | Tabular 工具層 | **4/4 done** | W3-TL-T1 · W3-TL-T2 · W3-TL-T3 · W3-TL-T4 | `docs/tabular-tool-catalog-v1.md` · `docs/tabular-tool-selector-spec.md` · `docs/tabular-tool-outbox-spec.md` · `docs/tabular-outbox-consumer-spec.md` · `tools/tabular_tool_catalog_v1.json` |
| **Wave 4** | Routing ↔ Tool Layer 銜接 | **4/4 done** | W4-T1 · W4-T2 · W4-T3-A · W4-T4-routing-ci-hooks | `docs/routing-tool-layer-glue-v1.md` · `docs/routing-eval-runner-v1.md` · `docs/tabular-intake-tool-path-v1.md` · `docs/tabular-mvp-release-checklist.md` · `.github/workflows/eval-gate-ci.yml`（W4-T4 dry-run step） |
| **Wave 5** | Multi-Agent Collaboration & Decision Helper | **W5-T0 done / W5-T1 implementer done / W5-T1B done** | W5-T0-multi-agent-collaboration-docs · W5-T1-intake-decision-rules-v1 · W5-T1B-intake-decision-agent-entry | `docs/multi-agent-collaboration-spec-v1.md` · `docs/intake-decision-rules-v1.md` · `routing/intake_decision_rules_v1.py` · `scripts/run_agent_intake_decision_demo.py` |
| **Phase 4** | Multi-Agent Collaboration **Contract** | **WA-T4 done · 75%→85%** | **WA-T4-phase4-multi-agent-collaboration-contract-v1** | **`docs/phase4-multi-agent-collaboration-contract-v1.md`** · `tests/test_phase4_multi_agent_contract_v1.py` |
| **Wave 6** | Skill Card & Agent Standard Line | **W6-T5/T6/T10 done · accepted_with_gaps** | W6-T1–T10 · W6-T3–T8 | docs/skill-cards-v1.md · docs/agent-run-standard-case-experiment-v1.md · **W6-T5/T6 整合層 checkpoint 行為修復完成**（outbox-root fallback · auto_approve skip）；gap=path 語義文件化 · orchestrator redirect 可選 |
| **Wave 7** | Run Path · Fixtures · Controlled Notify · v2 設計收斂 | **W7-T1–T3 implementer done / W7-T4 design done** | W7-T1 · W7-T2 · W7-T3 · **W7-T4** | `docs/ninety-five-percent-automation-blueprint-v2.md` · `docs/skill-cards-v2.md` · `docs/skill-map-v2.md` · `docs/agent-standard-line-governance-view-v2.md` · `delivery/controlled_notify_experiment_v1.py` |
| **Wave 8** | Experimental Fixture Run Paths · Delivery Approval CLI | **W8-T1 done · W8-T3 implementer done** | W8-T1 · **W8-T3** | `scripts/run_delivery_approval_cli.py` · `docs/delivery-approval-one-click-cli-v1.md` |
| **Wave 9** | Non-Tabular Shadow · Controlled Walkthrough | **W9-NT done · accepted** | W9-T2–T6 · **W9-NT** | NT fixtures + preview CLI · **README v2 §3.5 8 步 walkthrough**（docu-corp + log-analytics-co） |
| **Wave 10** | Agent Lines CI · Registry · Metrics | **W10-T2 registry done · accepted_with_gaps** | W10-T1 · **W10-T2-selector** · W10-T3/T4 | `run_agent_lines_ci_suite.py` · **registry fail-closed policy 已落地**（env gate 預設 off · strict opt-in） |

---

## Agent Lines v1 必做圈 — 進度快照（2026-06-16）

> **口径**：Tabular Standard Line v2 + Non-Tabular shadow v1 + CI/registry/guard 最小可交付子集；票級細節見各 `*_state.md` C/D_REPORT。

| 必做項 | 票 | Reviewer | 一句摘要 |
|--------|-----|----------|----------|
| Checkpoint A/B 整合層修復 | **W6-T5** · **W6-T6** | `accepted_with_gaps` | outbox-root 三層 fallback + `needs_review`+`auto_approve` skip 已入整合層；9/9 + 11/11 unittest · orchestrator 24/24 OK |
| Orchestrator ↔ 整合層接線 | **W6-T10** | `accepted_with_gaps` | S4/S12 改接 W6-T5/W6-T6；**deferred** 縮至 path 語義文件 · sandbox e2e CP-B · S15 notify |
| NT controlled walkthrough | **W9-NT** | **`accepted`** | 8 步命令鏈 · NT-A/B 雙 fixture · audit quickview · **README v2 §3.5** |
| Registry fail-closed policy | **W10-T2-selector** | `accepted_with_gaps` | Tabular selector 只讀消費 `approved_registry.json` · `TABULAR_APPROVED_REGISTRY_*` env gate **預設關** · strict fail-closed opt-in · 16/16 OK |
| Experimental fixture guard T1 | **W4-GUARD-01** | **accepted_with_gaps（T1）** · **G2–G4 opt-in DONE** | T1：`additional_demo`/`sandbox_client` 需 `--include-extended-fixtures`；G2–G4：`FP-G1-T3` opt-in · 預設 off · ≠ required CI（2026-07-28 全開） |

**後續工作（建議）**（來源：W6-T10 `C_REPORT` / `B_REPORT` · W6-T5/T6 `C_REPORT` suggestions）

| 建議票 | 說明 |
|--------|------|
| **W6-T10-cleanup-orchestrator-checkpoint-workarounds-v1** | 收斂 W6-T10 orchestrator workaround：移除 auto-approve bypass 與 outbox redirect；改為 `maybe_create_checkpoint_a/b(..., auto_approve=auto_approve_*)` 並直接傳 `outbox_root_override`；更新 `test_custom_outbox_root_*` docstring（W6-T5/W6-T6 整合層 fix 已 landed · C_REPORT 優先 follow-up；文件層 LEGACY 標註已完成，runtime 收斂留本票） |
| **W6-T10-cleanup-v2-remove-legacy-redirect** | 完整移除 Issue 2 LEGACY redirect（L487–502、L664–682）；直接傳 `outbox_root_override` 至整合層；更新測試使 external outbox 路徑與 caller 預期一致（B_REPORT · partial cleanup 後拆票） |
| **W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1**（**done**） | sandbox e2e 已接 `maybe_create_checkpoint_b`（W12-T2 · 2026-07-28 全開收口 · 舊敘事「僅 can_proceed」作廢） |
| **checkpoint_path 語義文件化**（W6-T5/T6 `C_REPORT` · **done**） | 票 `W6-T5-T6-docs-checkpoint-path-semantics-v1` **DONE** · A/B docs §7 三層 fallback + consumer 已落地（B4 verify-and-close · cross-ref） |
| **preview `checkpoint_b_status` 補 `integration_layer`**（**done**） | 票 `preview-checkpoint-b-status-integration-layer-v1` · preview／早期退出對齊 |

### Agent Lines v1 後續待排票池（建議優先序）

> **口徑**：僅收錄「後續工作（建議）」表與 W6-T10 / W6-T5 / W6-T6 / W12-T2 之 `C_REPORT`／`B_REPORT` 明確 suggestion／deferred；**不含**已 landed 的 W6-T5/T6 整合層 bugfix（auto-approve skip · outbox-root fallback）。

| 票名 | 類型 | 來源 | 建議優先級 | 一句摘要 |
|------|------|------|------------|----------|
| **W6-T10-cleanup-orchestrator-checkpoint-workarounds-v1** | cleanup | W6-T10 `C_REPORT` · 後續工作表 | **High** | 收斂 orchestrator 雙重 enforcement：移除 auto-approve bypass 與 outbox redirect，改 `maybe_create_checkpoint_a/b(..., auto_approve=*)` 並直接傳 `outbox_root_override`；更新 `test_custom_outbox_root_*` docstring（文件層 LEGACY 標註已完成，runtime 收斂留本票） |
| **W6-T10-cleanup-v2-remove-legacy-redirect** | cleanup | W6-T10 `B_REPORT` · 後續工作表 | **High** | 完整移除 Issue 2 LEGACY redirect（L487–502、L664–682）；直接傳 `outbox_root_override` 至整合層；更新測試使 external outbox 路徑與 caller 預期一致 |
| **W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1** | feature | W6-T10 `C_REPORT`／`B_REPORT` · 後續工作表 | **done** | 完整 `maybe_create_checkpoint_b` 寫檔路徑 · 2026-07-28 全開收口 |
| **checkpoint_path 語義文件化**（`W6-T5-T6-docs-checkpoint-path-semantics-v1`） | docs | W6-T5/T6 `C_REPORT` · 後續工作表 | **done** | A/B docs §7 三層 fallback + consumer 已落地 · B4 verify-and-close（≠ Phase%／runtime） |
| **preview `checkpoint_b_status` 補 `integration_layer`** | docs/code | W6-T10 `C_REPORT` 小缺口 | **done** | `preview-checkpoint-b-status-integration-layer-v1` · 早期退出亦補欄位 |
| **S8–S10 主鏈真實執行 · S15 notify gateway** | feature | W6-T10 `C_REPORT` deferred · FRAME NonScope | **Low** | 實驗線 S8–S10 真實執行與 S15 通知閘道；維持 deferred，不阻擋 Agent Lines v1 必做圈 |

**Agent Lines v1 故事位置**：Wave 6 完成 HITL 整合層與 orchestrator 接線（實驗線可 preview/run CP-A/B）；Wave 9 提供 Non-Tabular 一線 walkthrough；Wave 10 落地 registry 策略層（prod gate 仍 off）；Lane A **W4-GUARD-01 T1** 防止 extended fixture 默認混入 regression。

**驗證命令（本地 smoke）**

```bash
# Wave 1 主鏈回歸
python scripts/run_mvp_mainline_regression.py -v

# Wave 2 routing 文件一致性
python -m unittest tests.test_intake_routing_catalog tests.test_routing_eval_cases -v

# Wave 3-TL 工具層
python -m unittest tests.test_tabular_tool_catalog tests.test_tabular_tool_selector tests.test_tabular_tool_executor tests.test_tabular_outbox_consumer tests.test_build_tabular_outbox_replay_report -v

# Wave 3-TL T4 replay report (fixture smoke)
python scripts/build_tabular_outbox_replay_report.py --case-ref demo_phase --outbox-root tests/fixtures/outbox --stdout --format md

# Wave 4 routing → tabular glue（W4-T1）
python -m unittest tests.test_routing_tabular_glue -v

# Wave 4 routing eval runner dry-run（W4-T2）
python scripts/run_routing_eval.py --dry-run --format table
python -m unittest tests.test_routing_eval_runner -v

# Wave 4 tabular intake tool path preview（W4-T3-A）
python scripts/run_tabular_intake_tool_path.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json
python -m unittest tests.test_tabular_intake_tool_path -v

# Wave 5 intake decision rules（W5-T1）
python routing/intake_decision_rules_v1.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json
python -m unittest tests.test_intake_decision_rules_v1 -v

# Phase 4 multi-agent collaboration contract（WA-T4）
python -m unittest tests.test_phase4_multi_agent_contract_v1 -v

# Wave 5 Agent intake decision entry（W5-T1B）
python scripts/run_agent_intake_decision_demo.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --format json
python -m unittest tests.test_agent_intake_decision_demo -v

# Wave 7 experiment run path + extended fixtures（W7-T2 / W7-T1）
python -m unittest tests.test_agent_standard_case_experiment tests.test_agent_standard_case_regression -v
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --auto-approve-intake --format json
python scripts/run_agent_standard_case_regression.py --include-extended-fixtures --format json

# Wave 7 controlled notify experiment（W7-T3）
python scripts/run_controlled_delivery_notify_experiment.py --case-dir cases/demo_phase --format json
python -m unittest tests.test_controlled_delivery_notify_experiment_v1 -v

# Wave 8 experimental fixture run paths（W8-T1）
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --include-extended-fixtures --auto-approve-intake --format json
```

---

## Wave 1 — MVP 主鏈與治理 · **done**

**一句話**：治理收斂視圖就緒；tabular MVP 標準 trace spec 與一鍵主鏈回歸（`demo_phase` + `sampleco/2026-0001`）已交付。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W1-T1B** | done · Reviewer `accepted_with_gaps` | 治理／合約／禁區／票務 **收斂視圖** → `docs/governance-constitution-v1.md` |
| **W1-T2-mvp-trace-path** | done | L1 trace 對照 spec → `docs/mvp-standard-trace-path.md` |
| **W1-T3B-mvp-mainline-regression** | done · Scribe 收口 | 回歸 runner + 文檔 → `docs/mvp-mainline-regression.md` · `scripts/run_mvp_mainline_regression.py` · `tests/test_mvp_mainline.py`（6 tests） |

**票 state**：`04_Workflows/tickets/W1-T1B_governance_consolidation.md` · `W1-T2-mvp-trace-path_state.md` · `W1-T3B-mvp-mainline-regression_state.md`

---

## Wave 2 — Intake / Routing / Eval · **done**

**一句話**：跨 family routing catalog（規則索引）與 routing eval cases（事後對照卷）已交付；**不**實作 routing engine。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W2-T1-intake-routing-catalog** | done · Orchestrator accepted | 人讀 spec + 機器 YAML（10 條 `task_type`）→ `docs/intake-routing-catalog-v1.md` · `routing/intake_routing_catalog_v1.yaml` · `tests/test_intake_routing_catalog.py`（10/10） |
| **W2-T2-routing-eval** | done · Orchestrator accepted | Eval 指南 + cases 骨架 → `docs/routing-eval-guide-v1.md` · `routing/routing_eval_cases_v1.yaml` · `tests/test_routing_eval_cases.py`（8/8）；與 T1 合跑 18/18 |

**票 state**：`04_Workflows/tickets/W2-T1-intake-routing-catalog_state.md`（含 C/D_REPORT）  
**備註**：`W2-T2-routing-eval` **無獨立 state 檔**；與 `04_Workflows/tickets/W2-T2_state.md`（Multi-Chat 參照票）為**不同票號語境**。Progress 以 `W2-T2-routing-eval` 記錄。

> **註（Wave 2 · 2026-06-15 · 更新）**：Intake／Routing／Eval **主幹已打底**（W2-T1 done · W2-T2-routing-eval done）。**`W2-T2_state.md`（Multi-Chat B→C→D→O 參照票）Reviewer `accepted_with_gaps` · Orchestrator 已關票** — 子票 W2-REF-001 + `docs/testing.md` §9 + `tickets/README.md` walkthrough 已交付。**deferred**：子票 W2-REF-001 C/D 關票、state lint CI、history migration、routing eval 專用 state 檔。**不得**與 `W2-T2-routing-eval`（routing eval 主幹票）混淆。

---

## Wave 3-TL — Tabular 工具層 · **4/4 done**

**一句話**：Catalog → Selector → Executor + Outbox → **Consumer / Debug** 四件套已交付；T4 為 read-only outbox 檢視與 history join（**非** Phase 8.8 replay）。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W3-TL-T1** | done · `accepted_with_gaps` | Tabular 工具 SSOT（11 tools）→ `docs/tabular-tool-catalog-v1.md` · `tools/tabular_tool_catalog_v1.json` · `tests/test_tabular_tool_catalog.py`（10/10） |
| **W3-TL-T2** | done · `accepted_with_gaps` | 推薦 selector（不驅動 E2E）→ `docs/tabular-tool-selector-spec.md` · `tools/tabular_tool_selector.py` · `tests/test_tabular_tool_selector.py`（9/9） |
| **W3-TL-T3** | done · `accepted_with_gaps` | Executor + outbox → `docs/tabular-tool-outbox-spec.md` · `tools/tabular_tool_executor.py` · `tools/tabular_outbox_writer.py` · `tests/test_tabular_tool_executor.py`（6/6） |
| **W3-TL-T4** | done · `accepted_with_gaps` | Outbox consumer + debug CLI + history join + **replay report** → `docs/tabular-outbox-consumer-spec.md` · `docs/tabular-outbox-replay-report-v1.md` · `tools/tabular_outbox_consumer.py` · `tools/inspect_tabular_outbox.py` · `scripts/build_tabular_outbox_replay_report.py` · `tests/test_tabular_outbox_consumer.py`（14/14）· `tests/test_build_tabular_outbox_replay_report.py`；re-execute／Langfuse **out of scope** |

**票 state**：`04_Workflows/tickets/W3-TL-T1-tabular-tool-catalog_state.md` 等（C/D_REPORT 已填；`overall_status` 欄位可能仍為 `draft`，以本 Dashboard 與 D_REPORT 為準）。

**分軌**：`W3-TL-*` 僅 Tabular MVP；與 Phase 8.8 `W3-T1`–`W3-T4` 編排 Tool Layer **禁止** rename／合併。

> **註（Wave 3 · Phase 8.8 Tool Layer · 2026-06-15）**：**`W3-T1_state.md`（Tool Catalog v1 權威化 · Phase 8.8 編排層）Reviewer `accepted_with_gaps` · Orchestrator 已關票** — SSOT 四檔：`shared/schemas/tool_catalog_v1.json`、`core/tool_catalog.py`、`docs/TOOL_CATALOG_AUTHORITY.md`、`tests/test_tool_layer_schemas.py`（6/6 OK）。**deferred**：selector 消費 `enabled:false` 攔截整合、暗部 venv catalog sync、MCP 動態註冊、Wave8 SKU 合 schema。**分軌**：與上方 `W3-TL-*` Tabular MVP **禁止** rename／合併。

**合併前建議**：`python scripts/run_mvp_mainline_regression.py -v` → 6/6 OK（T1–T3 Reviewer G3／G1 留痕）。

---

## Wave 4 — Routing / Tool Layer Integration · **4/4 done**

**一句話**：W2 `task_type` → W3-TL **plan_only glue**（W4-T1）、**routing eval dry-run runner**（W4-T2）、**Tabular intake 路徑預演 CLI**（W4-T3-A）與 **PR CI dry-run + release checklist**（W4-T4）已交付；PR CI 不跑 `--execute` 或 mainline regression。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W4-T1-routing-to-tabular-glue** | done · Reviewer `accepted_with_gaps` | `plan_tabular_route` 純 mapping → `routing/intake_to_tabular_glue.py` · `docs/routing-tool-layer-glue-v1.md` · `tests/test_routing_tabular_glue.py`（9/9）；主鏈守護 6/6 |
| **W4-T2-routing-eval-runner** | done · Reviewer `accepted_with_gaps` | 消費 `routing_eval_cases_v1.yaml` dry-run 對照 → `scripts/run_routing_eval.py` · `docs/routing-eval-runner-v1.md` · `tests/test_routing_eval_runner.py`（12/12）；CLI **4/4 aligned**；主鏈守護 6/6 |
| **W4-T3-A-intake-tabular-tool-path** | done · Reviewer `accepted_with_gaps` | 獨立 CLI 路徑預演（glue → Selector → executor plan）→ `scripts/run_tabular_intake_tool_path.py` · `docs/tabular-intake-tool-path-v1.md` · `tests/test_tabular_intake_tool_path.py`（8/8）；dry-run only，不寫 outbox、不改 intake／UI／主鏈；G1–G4 見票 C_REPORT |
| **W4-T4-routing-ci-hooks** | implementer done · Reviewer pending | PR CI：`eval-gate-ci.yml` step `Routing eval dry-run (W4-T4)`（unittest + `--dry-run --format json`）；release checklist → `docs/tabular-mvp-release-checklist.md`；**無** `--execute`、**無** mainline regression in CI |

**票 state**：`04_Workflows/tickets/W4-T1-routing-to-tabular-glue_state.md` · `W4-T2-routing-eval-runner_state.md` · `W4-T3-intake-tabular-tool-path_state.md` · `W4-T4-routing-ci-hooks_state.md`

**備註**：W4-T4 — mainline / W3-TL 四件套僅 release checklist 人工項，未接入 PR CI。W4-T2 G1（接 CI）本票已解。其餘 G 項見各票 C_REPORT。

---

## Wave 5 — Multi-Agent Collaboration & Decision Helper · **W5-T0 done / W5-T1 implementer done**

**一句話**：Multi-Chat 四角色協作機制文檔化（W5-T0）；Tabular intake 接案決策規則 v1 已交付（W5-T1），消費 W4-T1 glue 輸出 `auto_accept` / `needs_review` / `reject`，**不**改主鏈 routing 或 intake CLI。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W5-T0-multi-agent-collaboration-docs** | **done** · Reviewer `accepted` | Multi-Chat 四角色協作文檔：\| `docs/multi-agent-collaboration-spec-v1.md`（角色規格/DoD/與合約對齊）\| `docs/multi-agent-handoff-runbook-v1.md`（票生命週期/拆合票/常見錯誤）\| `docs/multi-agent-replay-guide-v1.md`（W4-T2 範例/postmortem 三級深度）\| 純文檔、不改程式碼/測試/治理母本 |
| **W5-T1-intake-decision-rules-v1** | implementer done · Reviewer pending | `evaluate_intake_decision` → `routing/intake_decision_rules_v1.py` · `docs/intake-decision-rules-v1.md` · `tests/test_intake_decision_rules_v1.py`；allowlist demo_phase / sampleco；CLI demo 內建於模組 |
| **W5-T1B-intake-decision-agent-entry** | **done** | Agent/Orchestrator CLI → `scripts/run_agent_intake_decision_demo.py` · `tests/test_agent_intake_decision_demo.py`；`--format text\|json`；消費 W4-T1 glue + W5-T1 decision；plan-only，不改主鏈 |
| **W5-T2-hitl-checkpoints-v1** | design **done** | HITL Checkpoint A/B 設計 → `docs/hitl-checkpoints-v1.md` · `04_Workflows/tickets/W5-T2-hitl-checkpoints-v1_state.md`；design only |
| **W5-T2B-hitl-checkpoints-v1-impl** | implementer **done** | 檔案型 checkpoint state/events → `hitl/checkpoints_v1.py` · CLI `scripts/run_hitl_checkpoint_cli.py` · `tests/test_hitl_checkpoints_v1.py`；`--list` / `--review` / `--apply-decision`；產生 `resume_context`，不 resume 主鏈 |

**票 state**：
- W5-T0：`04_Workflows/tickets/W5-T0-multi-agent-collaboration-docs_state.md`
- W5-T1：`04_Workflows/tickets/W5-T1-intake-decision-rules-v1_state.md`
- W5-T2：`04_Workflows/tickets/W5-T2-hitl-checkpoints-v1_state.md`

> **註（Wave 5 · 2026-06-15 · 更新）**：W5-T0／W5-T1B **done**；`W5-T1-intake-decision-rules-v1`（intake decision rules 票）實作已交付（implementer done · Reviewer pending）。**`W5-T1_state.md`（Skill Card → approved registry 管道）Reviewer `accepted_with_gaps` · Orchestrator 已關票** — 交付 `skills/approved_registry.json` + CLI（`list-approved` / `promote-from-queue`）+ tests（6/6 + 6/6 OK）。**deferred**：selector 消費 registry、runbook 同步、`skills/cards/`↔registry 雙向 sync。**票號語境**：**非** `W5-T1-intake-decision-rules-v1`。

**決策摘要（v1）**

| Fixture | `tabular.cleaning.mvp` | `tabular.intake.new_case` |
|---------|------------------------|---------------------------|
| `demo_phase` | `needs_review`（`manual_review_required`） | `auto_accept` |
| `sampleco` | `needs_review`（`human_review_required` / `schema_ambiguous`） | `auto_accept` |

---

## Wave B · Toolchain（WB-T*）· 底層 Contract 收口

> **分轨（AC-3）**：本節 **Toolchain Wave B（WB-T*）** 与 **Observability Wave B（`WAVE-B-P*`）**、**Tabular `W3-TL-*`** 三轴并列；详见上方「命名空間」与 `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` §0。

**一句話**：**Wave B · Toolchain: done · accepted_with_gaps_deferred_to_WC-PRE** — WB-T1–T8 contract SSOT · audit spec · smoke matrix YAML · **WB-T6** readme/执行计划/Dashboard 索引 · **WB-T8** closure handoff（108/108 OK）；WC-PRE-01～05 impl/doc gap 已 Reviewer 关票（2026-06-12）。

| 票號 | 狀態 | Phase | 交付摘要 |
|------|------|-------|----------|
| **WB-T1-tool-catalog-and-selector-contract-v1** | **done** · accepted_with_gaps | P8.6 · P8.7 | `docs/tool-catalog-and-selector-contract-v1.md` · contract unittest |
| **WB-T2-tool-executor-and-sandbox-safety-contract-v1** | **done** · accepted_with_gaps | P8.8 | `docs/tool-executor-and-sandbox-safety-contract-v1.md` · 16 断言 |
| **WB-T3-outbox-and-feedback-layer-contract-v1** | **done** · accepted_with_gaps | P8.9 | `docs/outbox-and-feedback-layer-contract-v1.md` · `outbox_layer_v1.json` |
| **WB-T4-agent-lines-ci-and-metrics-dashboard-v1** | **done** · accepted_with_gaps | P5 · P6 | `run_toolchain_health_dashboard.py` · optional gate |
| **WB-T5-audit-quickview-and-case-history-spec-v1** | **done** · accepted_with_gaps | P5 audit · P8.9 join | `docs/audit-quickview-and-case-history-spec-v1.md` · investigation-only |
| **WB-T6-wave-b-bottom-layer-readme-and-phase-progress-alignment-v1** | **done** · accepted_with_gaps | P8.5 · 跨 P5/P6/P8 | `WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` · `wave-b-toolchain-readme-v1.md` · 本 Dashboard Phase 表 |
| **WB-T7-phase6-toolchain-smoke-matrix-extension-v1** | **done** · **accepted** | P6 | `routing/toolchain_smoke_matrix_v1.yaml` · P6 附录 A 引用 |
| **WB-T8-toolchain-wave-b-review-and-progress-closure-v1** | **done** · accepted_with_gaps | closure | Toolchain Wave B review-and-progress closure handoff · 批量验收 T1–T7 |

> **註（Toolchain Wave B · 2026-06-12）**：**Wave B · Toolchain: done · accepted_with_gaps_deferred_to_WC-PRE**。WC-PRE-01～05 已 Reviewer 关票（selector `plan_only` · executor timeout · audit investigation view · smoke runner）。WC-PRE-06/07 仍为治理/CI 提案（需批文）；**不得**假设 PROD gate / mandatory smoke CI 已开启。Phase% **仅**读本 Dashboard Phase 表（未改数字）。

**快速入口**：`docs/wave-b-toolchain-readme-v1.md` · **执行计划**：`docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md`

**WC-PRE-06 提案**：`docs/toolchain-observability-governance-upgrade-v1.md` — toolchain health L0→L1→L2 治理升格設計稿（doc-only · 不改 Phase%）

**驗證命令（汇总）**

```bash
python -m unittest tests.test_tool_catalog_and_selector_contract_v1 tests.test_tool_executor_and_sandbox_contract_v1 tests.test_outbox_and_feedback_layer_contract_v1 tests.test_toolchain_health_dashboard_v1 tests.test_audit_quickview_and_case_history_spec_v1 tests.test_phase6_toolchain_smoke_matrix_v1 -v
python scripts/run_toolchain_health_dashboard.py --format json --dry-run
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json
```

**票 state**：`04_Workflows/tickets/WB-T1-tool-catalog-and-selector-contract-v1_state.md` … `WB-T8-toolchain-wave-b-review-and-progress-closure-v1_state.md` · `WB-T6-wave-b-bottom-layer-readme-and-phase-progress-alignment-v1_state.md`

---

## Phase 4 — Multi-Agent Collaboration Contract · **75%**（WA-T4 done · 75%→85%）

**一句話**：在 W5-T0 三份 docs + `multi_chat_roles.mdc` 之上，升格 **Phase 4 contract SSOT**（四角色 contract 表、O→B→C→D 工作流、routing 决策树、STATE 写入冻结）；Wave B/C 可直接引用 contract 假设。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **WA-T4-phase4-multi-agent-collaboration-contract-v1** | **implementer done · Reviewer pending** | `docs/phase4-multi-agent-collaboration-contract-v1.md`（§1–§8）· `tests/test_phase4_multi_agent_contract_v1.py`（≥10 断言）· W5-T0 三 docs §0 指针 · `tickets/README.md` contract 对齐 · WORKFLOW_INDEX 层级说明 |

**文档层级**：contract（WA-T4）＞ `multi_chat_roles.mdc` ＞ W5-T0 spec ＞ handoff runbook ＞ replay guide

**驗證命令**

```bash
python -m unittest tests.test_phase4_multi_agent_contract_v1 -v
# 人工：打开 04_Workflows/tickets/W4-T2-routing-eval-runner_state.md 对照 contract §3 流程
```

**票 state**：`04_Workflows/tickets/WA-T4-phase4-multi-agent-collaboration-contract-v1_state.md`

---

## Wave 6 — Skill Card & Agent Standard Line · **W6-T5/T6/T10 done · accepted_with_gaps**

**一句話（Agent Lines v1）**：Wave 6 是 Tabular **Agent Standard Line** 的 HITL 與 orchestrator 主幹——**W6-T5/T6 整合層 checkpoint 行為已修復**（`accepted_with_gaps`：path 語義文件化 · orchestrator redirect 可選）；W6-T10 已接線 S4/S12；Skill Cards/Map 與 15 步實驗線設計供一線定位入口；sandbox e2e 與 S15 notify 仍 out of scope。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W6-T1-skill-card-and-skill-map-v1** | implementer done · Reviewer pending | Skill Cards（2 張）+ Skill Map（8 步驟）：\| `docs/skill-cards-v1.md` — Card A: demo_phase、Card B: sampleco/2026-0001（10 欄位模板）\| `docs/skill-map-v1.md` — intake → decision → glue → selector → executor → outbox → inspect → release 映射表 \| 純文檔、不改程式碼 |
| **W6-T2** | planned · not_started | 延伸 Skill Card（可選新案例，如 `acme/2026-0001` 或其他 schema 類型）|
| **W6-T3-agent-run-standard-case-experiment-v1** | **design · in_progress** | 15 步標準實驗線設計（S1 Intake → S15 Notify）：\| docs/agent-run-standard-case-experiment-v1.md — 完整流程規格、Checkpoint A/B 整合、驅動者分布 \| 限定 demo_phase / sampleco 案型、設計 only（無程式碼）、預留實作票（W6-T5 Checkpoint A, W6-T8 Checkpoint B 等）|
| **W6-T6-integrate-checkpoint-b-delivery-gate** | **done · `accepted_with_gaps`** | Checkpoint B 整合層：\| `hitl/checkpoint_b_integration_v1.py` — output_guard → checkpoint B → `delivery_plan` \| outbox-root 三層 fallback（2026-06-16）\| 11/11 unittest OK · **gap**：`checkpoint_path` 語義文件化 · orchestrator redirect 可選 |
|| **W6-T7-experiment-eval-and-replay-guide-v1** | **implementer done · Reviewer pending** | 實驗線驗收、replay、失敗分析完整指南：\| `docs/agent-run-experiment-eval-guide-v1.md` — §1-§6 完整（三級成功定義 Preview/Auto/Full HITL、五階段 replay Decision/CP-A/Route/CP-B/Delivery、六類失敗 F1-F6 診斷順序、G1-G7 升級條件）\| 純文檔、不改程式碼 |
| **W6-T5-integrate-checkpoint-a-intake-confirmation** | **done · `accepted_with_gaps`** | Checkpoint A 整合層：\| `maybe_create_checkpoint_a` — outbox-root fallback + `needs_review`+`auto_approve` skip（不寫檔）\| 9/9 unittest OK · orchestrator 24/24 OK · **gap**：path 語義 consumer 規則 · orchestrator `.temp_test_outbox_area` redirect 可選 |
| **W6-T4-agent-run-standard-case-orchestrator-v1** | **implementer done · Reviewer pending** | Agent-run 標準案實驗線 orchestrator CLI：\| `scripts/run_agent_standard_case_experiment.py` — preview/run 串接 W5-T1B + W4-T1 + W4-T3 + W5-T2B \| `docs/agent-run-standard-case-orchestrator-v1.md` · `tests/test_agent_standard_case_experiment.py` |
| **W6-T10-orchestrator-checkpoint-wiring-v1** | done · **`accepted_with_gaps`** | S4/S12 改接 W6-T5/W6-T6 整合層（移除 inline checkpoint 邏輯）· preview 不寫 outbox · run 依整合層觸發寫 A/B · 24/24 unittest OK · **deferred**（2026-06-16 縮減）：path 語義文件 · sandbox e2e CP-B 完整寫檔 · S15 notify |
| **W6-T8-agent-standard-case-experiment-regression-v1** | **implementer done · Reviewer pending** | 實驗線輕量回歸鉤子：\| `scripts/run_agent_standard_case_regression.py` — 一鍵 demo_phase + sampleco preview \| JSON 寫入 `outbox/agent_experiment_regression/` \| `docs/agent-standard-case-regression-v1.md` · `tests/test_agent_standard_case_regression.py` \| 不改 MVP mainline regression |
| **W6-T9-agent-standard-line-governance-view-v1** | **design done** | 治理觀點文檔：\| `docs/agent-standard-line-governance-view-v1.md` — 15 步決策權分佈（S1-S15 人類/Agent 權責） / 10 類 audit log 檔案清單 / R1-R5 風險 safeguard 分層 / 95%→100% 升級路徑治理原則 \| 純文檔、無程式碼變更 |
| **W7-T2-increase-agent-run-mode-coverage-v1** | done · `accepted_with_gaps` | Run 模式覆蓋擴大：\| `scripts/run_agent_standard_case_experiment.py` — per-case run_path_profile（demo_phase→bundle；sampleco→checkpoint_b）\| `scripts/run_agent_standard_case_regression.py` — `--run-mode run-all-allowed` \| `docs/agent-run-experiment-eval-guide-v1.md` §2.4 \| `tests/test_agent_standard_case_experiment.py` · `tests/test_agent_standard_case_regression.py`（31 tests OK） |

> **註（Wave 6 · 2026-06-16 · Agent Lines v1 必做圈）**：**W6-T5** / **W6-T6** Reviewer **`accepted_with_gaps`** — 整合層 outbox-root 三層 fallback + `needs_review`+`auto_approve` skip 已落地（9/9 + 11/11 OK；orchestrator 24/24 OK）。**gap**：`checkpoint_path` 語義文件化 · W6-T10 orchestrator redirect 可選保留。**W6-T10** deferred 自 outbox/auto_approve bugfix 縮減至 path 語義 · sandbox e2e CP-B · S15 notify。

**Skill Card 對照**

| 維度 | Card A: demo_phase | Card B: sampleco/2026-0001 |
|------|-------------------|---------------------------|
| **輸入行數** | 7 | 115 |
| **Gate Status** | `review_needed`（exit 2） | `accepted`（exit 0） |
| **Need Force** | 是 | 否 |
| **Selector Rule** | `phase_demo.clean.force` | `sampleco.clean.review` |
| **Human Review** | 否 | 是（schema_ambiguous）|
| **輸出行數** | 5 | 8 |
| **Output Guard** | `ok` | `warning`（比例）|

**票 state**：`04_Workflows/tickets/W6-T1-skill-card-and-skill-map-v1_state.md`

---

## Wave 7 — Run Path · Extended Fixtures · Controlled Notify · v2 Design Convergence

**一句話**：實驗線 **run path 真執行**（demo→bundle · sampleco→CP-B）；allowlist 擴至 4 fixture；S15 Controlled Notify 模擬；**W7-T4** 交付藍圖/Skill/治理 v2。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W7-T1-extend-agent-standard-line-more-fixtures-v1** | implementer done · Reviewer pending | `cases/additional_demo` · `cases/sandbox_client` · orchestrator allowlist + mock profiles · regression `--include-extended-fixtures` |
| **W7-T2-increase-agent-run-mode-coverage-v1** | done · `accepted_with_gaps` | `_RUN_PATH_PROFILES` · live S11 · CP-B 接 run · regression `--run-mode run-all-allowed` · 31 tests OK |
| **W7-T3-controlled-delivery-and-notify-experiment-v1** | implementer done · Reviewer pending | `delivery/controlled_notify_experiment_v1.py` · simulated only · demo/sampleco allowlist |
| **W7-T4-update-ninety-five-percent-blueprint-and-skills-wave7-v1** | **design done** | `docs/ninety-five-percent-automation-blueprint-v2.md` · `docs/skill-cards-v2.md` · `docs/skill-map-v2.md` · `docs/agent-standard-line-governance-view-v2.md` · Wave 8 缺口 G8-1–G8-10 |

**Wave 7 自動化實測**：(10 auto + 4 HITL×0.5) / 15 ≈ **86.7%**（95% 目標 → Wave 8）

**驗證命令**

```bash
python -m unittest tests.test_agent_standard_case_experiment tests.test_agent_standard_case_regression tests.test_controlled_delivery_notify_experiment_v1 -v
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --auto-approve-intake --format json
python scripts/run_agent_standard_case_regression.py --include-extended-fixtures --format json
python scripts/run_controlled_delivery_notify_experiment.py --case-dir cases/demo_phase --format json
```

**票 state**：`04_Workflows/tickets/W7-T1-extend-agent-standard-line-more-fixtures_state.md` · **`W7-T2-increase-agent-run-mode-coverage-v1_state.md`** · `W7-T3-controlled-delivery-and-notify-experiment-v1_state.md` · **`W7-T4-update-ninety-five-percent-blueprint-and-skills-wave7-v1_state.md`**

> **註（Wave 7 · 2026-06-15 · 更新）**：**`W7-T2-increase-agent-run-mode-coverage-v1` Reviewer `accepted_with_gaps` · Orchestrator 已關票** — `run_path_profile`（demo_phase→bundle · sampleco→CP-B）+ `--run-mode run-all-allowed` + `docs/agent-run-experiment-eval-guide-v1.md` §2.4 + 31 tests OK。**deferred**：CI nightly `run-all-allowed`（W10-T1 helper 排程）、production v2 default run mode（需批文）、extended fixtures run 覆蓋（W8-T1）。**不得**宣稱 Wave 7 全部完成；W7-T1/T3 等仍可有 `Reviewer pending` 狀態。

---

## Wave 8 — Experimental Fixture Run Paths · Delivery Approval · Decision v2

**一句話**：W7-T1 擴展 fixture 受控 run path（W8-T1）+ S13 一鍵交付確認 CLI（W8-T3）+ intake decision rules v2（W8-T2）+ **Non-Tabular Shadow Flow 設計（W8-T4）**；錨點案型 demo/sampleco 行為不變。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W8-T2-decision-rules-v2-profile-and-reject-reduction** | done · `accepted_with_gaps` | `evaluate_intake_decision_v2` · A/B/C/D profile tiers · C/D `experimental_fixture_profile` · non-Tabular shadow hook metadata · demo CLI `--use-v2` opt-in · 29 tests OK |
| **W8-T1-extend-run-path-profiles-for-experimental-fixtures-v1** | **implementer done · Reviewer pending** | additional_demo→CP-B（force clean）· sandbox→cleaning_preview（gate only）· regression `experimental_run` summary · skill-cards/skill-map v2.1 |
| **W8-T3-delivery-approval-one-click-cli-v1** | **implementer done · Reviewer pending** | `delivery/delivery_approval_cli_v1.py` · signoff/guard 摘要 · CP-B `--confirm` · 可選 controlled notify（simulated only） |
| **W8-T4-non-tabular-shadow-flow-blueprint-v1** | done · `accepted_with_gaps` | Non-Tabular Shadow Flow 藍圖 v1 · §1–§6 完整設計 · 2 案型示例 · S1–S15 對照表 · 9 張 Wave 9 建議票 · **design-only** |

**Run path 摘要**

| case_ref | stop_at | experimental |
|----------|---------|--------------|
| `demo_phase` | bundle | no |
| `sampleco/2026-0001` | checkpoint_b | no |
| `additional_demo` | checkpoint_b | **yes** |
| `sandbox_client` | cleaning_preview | **yes** |

**驗證命令**

```bash
python -m unittest tests.test_intake_decision_rules_v2 tests.test_agent_standard_case_experiment tests.test_agent_standard_case_regression tests.test_delivery_approval_cli_v1 -v
python scripts/run_agent_intake_decision_demo.py --task-type tabular.cleaning.mvp --case-dir cases/sandbox_client --use-v2 --format json
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --include-extended-fixtures --auto-approve-intake --format json
python scripts/run_delivery_approval_cli.py --case-dir cases/demo_phase --action approve
```

**票 state**：`04_Workflows/tickets/W8-T2-decision-rules-v2-profile-and-reject-reduction_state.md` · `04_Workflows/tickets/W8-T1-extend-run-path-profiles-for-experimental-fixtures-v1_state.md` · `W8-T3-delivery-approval-one-click-cli-v1_state.md` · **`W8-T4-non-tabular-shadow-flow-blueprint-v1_state.md`**

> **註（Wave 8 · 2026-06-15 · 更新）**：**W8-T2**（decision rules v2）與 **W8-T4**（Non-Tabular shadow blueprint）Reviewer **`accepted_with_gaps` · Orchestrator 已關票**。**W8-T2** — `routing/intake_decision_rules_v2.py` + A/B/C/D profile tiers + shadow hook metadata + demo `--use-v2` opt-in + 29 tests OK。**W8-T4** — `docs/non-tabular-shadow-flow-blueprint-v1.md` §1–§6 design-only + 9 張 Wave 9 建議票；無 production 行為。**deferred**：non-Tabular shadow pipeline 實作（W9 票）、demo CLI v2 預設升格、CI nightly。**不得**宣稱 Wave 8 全部完成；W8-T1/T3 等仍可有未完成 Reviewer 收口。

---

## Wave 9 — Non-Tabular Shadow Preview · **W9-NT walkthrough done**

**一句話（Agent Lines v1）**：Wave 9 把 Non-Tabular shadow 從 blueprint 推進到 **一線可複製 walkthrough**——fixtures（W9-T5/T6）+ preview CLI（W9-T4）+ **W9-NT 8 步命令鏈**（`accepted` · README v2 §3.5）；heavy execute / OCR 仍 deferred。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W9-NT-CONTROLLED-WALKTHROUGH-V1** | **done · `accepted`** | 8 步 walkthrough（unittest → preview → audit quickview）· NT-A `docu-corp` + NT-B `log-analytics-co` · **README v2 §3.5** · shadow-only · **deferred**：OCR / run mode / CP-A/B |
| **W9-T4-non-tabular-orchestrator-preview-v1** | done · `accepted_with_gaps` | `run_non_tabular_experiment_preview.py` · glue + selector stub · NT-A/NT-B preview · sandbox outbox · 11/11 tests OK · blocked for non-`non_tabular.*` |

**驗證命令**

```bash
python -m unittest tests.test_non_tabular_orchestrator_preview_v1 -v
python scripts/run_non_tabular_experiment_preview.py --task-type non_tabular.document.extract --case-dir cases/_experiment_samples/nt_docu_stub --format json
```

**票 state**：`04_Workflows/tickets/W9-NT-CONTROLLED-WALKTHROUGH-V1_state.md` · `04_Workflows/tickets/W9-T4-non-tabular-orchestrator-preview-v1_state.md`

---

## Wave 9 — Non-Tabular Shadow Implementation · **fixtures + decision + walkthrough**

**一句話（Agent Lines v1）**：承接 W8-T4 藍圖，Wave 9 逐步實作 non-tabular family；**W9-NT controlled walkthrough v1 已交付**（一線 8 步 · README v2 §3.5）；W9-T2/T3/T4/T5/T6 覆蓋 decision · selector stub · preview · 真實 fixtures。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W9-T1-non-tabular-routing-catalog-v1** | **implementer done · Reviewer pending** | Catalog spec + YAML skeleton：\| docs/non-tabular-routing-catalog-v1.md — NT-A/NT-B 案型規格、routing 欄位定義、與 Tabular 差異對照 \| routing/non_tabular_routing_catalog_v1.yaml — 3 entries (NT-A, NT-B, generic)，symbolic tool names \| **設計層 only**，無 executable glue |
| **W9-T2-non-tabular-decision-rules-v1** | done · `accepted_with_gaps` | `evaluate_intake_decision_v2` 支援 `non_tabular.*` · NT-A/NT-B profile · R-NT1 `reject` · Tabular regression 15/15 OK |
| **W9-T3-non-tabular-tool-catalog-and-selector-stub-v1** | done · `accepted_with_gaps` | `non_tabular_tool_catalog_v1.json`（NT-A ×2 + NT-B ×2）· `select_non_tabular_tools` stub · symbolic `planned_tools` only · 9/9 tests OK |
| **W9-T5-non-tabular-fixture-docu-corp-v1** | implementer done · Reviewer pending | NT-A fixture → `cases/docu-corp/2026-0001`（intake + `raw/documents/sample_brief.md`）· v2 decision NT-A / `needs_review` · `tests/test_non_tabular_fixture_docu_corp_v1.py`（4/4 OK） |
| **W9-T6-non-tabular-fixture-log-analytics-co-v1** | done · `accepted_with_gaps` | NT-B fixture → `cases/log-analytics-co/2026-0001`（intake + `raw/server_logs/app_server.log`）· v2 decision NT-B / `needs_review` · `tests/test_non_tabular_fixture_log_analytics_co_v1.py`（4/4 OK） |

**驗證命令**

```bash
python -m unittest tests.test_intake_decision_rules_v2 tests.test_non_tabular_tool_selector_v1 -v
python scripts/run_agent_intake_decision_demo.py --task-type non_tabular.document.extract --case-dir cases/docu-corp/2026-0001 --use-v2 --format json

# Wave 9 NT-A/NT-B fixtures（W9-T5 / W9-T6）
python -m unittest tests.test_non_tabular_fixture_docu_corp_v1 tests.test_non_tabular_fixture_log_analytics_co_v1 -v
python routing/intake_decision_rules_v2.py --task-type non-tabular.document.clean_and_annotate --case-dir cases/docu-corp/2026-0001 --json
python routing/intake_decision_rules_v2.py --task-type non_tabular.log.analyze --case-dir cases/log-analytics-co/2026-0001 --json
```

**票 state**：`04_Workflows/tickets/W9-T2-non-tabular-decision-rules-v1_state.md` · **`04_Workflows/tickets/W9-T3-non-tabular-tool-catalog-and-selector-stub-v1_state.md`** · **`04_Workflows/tickets/W9-T4-non-tabular-orchestrator-preview-v1_state.md`** · **`04_Workflows/tickets/W9-T5-non-tabular-fixture-docu-corp-v1_state.md`** · **`04_Workflows/tickets/W9-T6-non-tabular-fixture-log-analytics-co-v1_state.md`**

> **註（Wave 9 · 2026-06-16 · Agent Lines v1 必做圈）**：**W9-NT-CONTROLLED-WALKTHROUGH-V1** Reviewer **`accepted`** — 8 步命令鏈 · NT-A/B 雙 fixture · audit quickview `flow_family: non_tabular` · **README v2 §3.5**。**deferred**：OCR（W9-T7）· run mode（W12-T3）· CP-A/B（NT shadow 設計如此）。

---

## Wave 10 — Agent Lines CI Integration · **W10-T2 registry done**

**一句話（Agent Lines v1）**：Wave 10 把 Agent Lines 接入 **可選 CI / 離線觀測 / registry 治理**——W10-T1 CI suite 合併 Tabular+NT preview；**W10-T2-selector registry fail-closed policy 已落地**（env gate 預設 off · strict opt-in · prod gate 仍 off）；metrics/audit/readme 供一線運維入口。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W10-T1-integrate-agent-lines-into-ci-v1** | **implementer done · Reviewer pending** | `run_agent_lines_ci_suite.py` · `--scope tabular\|non_tabular\|all` · merged CI JSON · NT stub fixtures · mainline 未動 |

**驗證命令**

```bash
python -m unittest tests.test_agent_lines_ci_suite_v1 -v
python scripts/run_agent_lines_ci_suite.py --scope all --format json
```

**票 state**：`04_Workflows/tickets/W10-T1-integrate-agent-lines-into-ci-v1_state.md`

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W10-T2-selector-consumes-approved-registry-v1** | **done · `accepted_with_gaps`** | Tabular selector 只讀消費 `skills/approved_registry.json` · env `TABULAR_APPROVED_REGISTRY_ENABLED`（**預設關**）· `TABULAR_APPROVED_REGISTRY_STRICT` fail-closed **opt-in** · 16/16 unittest OK · **deferred**：degrade-open 策略 · 靜態 map 依賴 · non-tabular 未接 · **prod gate 預設仍 off** |

**驗證命令（W10-T2 · selector registry）**

```bash
python -m unittest tests.test_tabular_tool_selector_approved_registry_v1 tests.test_tabular_tool_selector -v
```

**票 state（W10-T2 · selector registry）**：`04_Workflows/tickets/W10-T2-selector-consumes-approved-registry-v1_state.md`

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W10-T2-agent-lines-metrics-and-monitoring-v1** | **implementer done · Reviewer pending** | `analyze_agent_lines_metrics.py` · 掃描 `agent_experiment_regression` / `agent_ci` / `non_tabular_experiment` · 輸出 `outbox/agent_metrics/metrics_summary.{json,csv}` · 離線 error rate / CP-A/B / duration |

**驗證命令（W10-T2）**

```bash
python -m unittest tests.test_analyze_agent_lines_metrics_v1 -v
python scripts/analyze_agent_lines_metrics.py
python scripts/analyze_agent_lines_metrics.py --format json
```

**票 state（W10-T2）**：`04_Workflows/tickets/W10-T2-agent-lines-metrics-and-monitoring-v1_state.md`

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W10-T3-agent-lines-audit-quickview-cli-v1** | **implementer done · Reviewer pending** | `run_agent_audit_quickview.py` · 只讀聚合 decision / route / CP-A/B / delivery approval · `agent_experiment_regression` + `agent_ci` + `non_tabular_experiment` + checkpoint JSON |

**驗證命令（W10-T3）**

```bash
python -m unittest tests.test_agent_audit_quickview_v1 -v
python scripts/run_agent_audit_quickview.py --case-ref demo_phase
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json
```

**票 state（W10-T3）**：`04_Workflows/tickets/W10-T3-agent-lines-audit-quickview-cli-v1_state.md`

|| 票號 | 狀態 | 交付摘要 |
||------|------|----------|
|| **W10-T4-agent-and-non-tabular-lines-readme-v1** | **implementer done · Reviewer pending** | `docs/agent-and-non-tabular-lines-readme-v1.md` · README 級總覽：§1 Overview、§2 Tabular v2 S1-S15、§3 Non-Tabular v1 Shadow、§4 CI/Metrics/Audit、§5 Governance/HITL、§6 Roadmap · 給未來合作者與新 Agent 的快速入口 |

**驗證命令（W10-T4）**

```bash
# 文件存在檢查
ls -la docs/agent-and-non-tabular-lines-readme-v1.md
ls -la 04_Workflows/tickets/W10-T4-agent-and-non-tabular-lines-readme-v1_state.md

# 章節完整性檢查
grep "^## §" docs/agent-and-non-tabular-lines-readme-v1.md | wc -l
# 預期輸出: 6
```

**票 state（W10-T4）**：`04_Workflows/tickets/W10-T4-agent-and-non-tabular-lines-readme-v1_state.md`

---

## Wave 11 — Controlled Experimental Fixtures · Non-Tabular Content Checks · Agent Lines Reporting

**一句話**：W11-T1 將 C/D fixture 升格為 `controlled_experimental` 受控準正式線；W11-T2 加入 shadow preview metadata-only 案型掃描；W11-T3 在 W10-T2 指標基礎上產出離線月度 Markdown 報表。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W11-T1-promote-experimental-tabular-fixtures-to-controlled-line-v1** | **implementer done · Reviewer pending** | C→CP-B+outbox · D→cleaning_preview+live guard · `fixture_maturity` · regression `bundle_probe` + `guard_sanity` · skill-cards/skill-map v2.1 |
| **W11-T2-non-tabular-lightweight-content-checks-v1** | **implementer done · Reviewer pending** | `non_tabular_lightweight_inspector_v1.py` · preview `content_summary` · stat/path metadata only · sandbox outbox |
| **W11-T3-agent-lines-monthly-metrics-report-v1** | **implementer done · Reviewer pending** | `generate_agent_lines_monthly_report.py` · 讀 `metrics_summary.json` / `runs[]` · 輸出 `outbox/agent_metrics/monthly_report_YYYY-MM.md` · error rate / CP-A/B / non-tabular preview |

**Run path 摘要（W11-T1）**

| case_ref | stop_at | maturity |
|----------|---------|----------|
| `demo_phase` | bundle | stable |
| `sampleco/2026-0001` | checkpoint_b | stable |
| `additional_demo` | checkpoint_b | **controlled_experimental** |
| `sandbox_client` | cleaning_preview | **controlled_experimental** |

**驗證命令（W11-T1）**

```bash
python -m unittest tests.test_agent_standard_case_experiment tests.test_agent_standard_case_regression -v
python scripts/run_agent_standard_case_regression.py \
  --run-mode run-all-allowed --include-extended-fixtures --auto-approve-intake --format json
```

**票 state（W11-T1）**：`04_Workflows/tickets/W11-T1-promote-experimental-tabular-fixtures-to-controlled-line-v1_state.md`

**驗證命令（W11-T2）**

```bash
python -m unittest tests.test_non_tabular_lightweight_inspector_v1 tests.test_non_tabular_orchestrator_preview_v1 -v
```

**票 state（W11-T2）**：`04_Workflows/tickets/W11-T2-non-tabular-lightweight-content-checks-v1_state.md`

**驗證命令（W11-T3）**

```bash
python -m unittest tests.test_generate_agent_lines_monthly_report_v1 -v
python scripts/analyze_agent_lines_metrics.py
python scripts/generate_agent_lines_monthly_report.py
python scripts/generate_agent_lines_monthly_report.py --month 2026-06
```

**票 state（W11-T3）**：`04_Workflows/tickets/W11-T3-agent-lines-monthly-metrics-report-v1_state.md`

|| 票號 | 狀態 | 交付摘要 |
||------|------|----------|
|| **W11-T4-agent-and-non-tabular-lines-readme-v2-wave10-aligned** | **implementer done · Reviewer pending** | `docs/agent-and-non-tabular-lines-readme-v2.md` · v2 更新：納入 W10-T1 CI Suite、W10-T2 Metrics、W10-T3 Audit 完整說明 · 新增「系統現狀一句話摘要」· 新增「典型開發者流程」· §6 Roadmap 結構化 · 保留 v1 |

**驗證命令（W11-T4）**

```bash
# 文件存在檢查
ls -la docs/agent-and-non-tabular-lines-readme-v2.md
ls -la 04_Workflows/tickets/W11-T4-agent-and-non-tabular-lines-readme-v2_state.md

# 章節完整性檢查
grep "^## §" docs/agent-and-non-tabular-lines-readme-v2.md | wc -l
# 預期輸出: 6

# Wave 10 內容覆蓋檢查
grep -c "W10-T1\|W10-T2\|W10-T3\|Wave 10" docs/agent-and-non-tabular-lines-readme-v2.md

# 「典型開發者流程」存在檢查
grep -c "典型開發者流程\|Typical Developer Flow" docs/agent-and-non-tabular-lines-readme-v2.md
```

**票 state（W11-T4）**：`04_Workflows/tickets/W11-T4-agent-and-non-tabular-lines-readme-v2_state.md`

---

## Wave 12 — Sandbox E2E Controlled Delivery · Fixture Maturity Metrics

**一句話**：W12-T1 為 `additional_demo` 新增 `--sandbox-end-to-end` 受控真實交付線（bundle → `outbox/sandbox_delivery/`）；不改 demo/sampleco 錨點。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W12-T1-tabular-controlled-end-to-end-delivery-sandbox-v1** | **implementer done · Reviewer pending** | `sandbox_delivery_bundle_v1` · orchestrator `end_to_end_sandbox` · audit `sandbox_delivery` 區塊 · allowlist=`additional_demo` only |
| **W12-T2-tabular-fixture-maturity-aware-metrics-and-ci-v1** | （見 WORKFLOW_INDEX §1.20b） | metrics / CI maturity tier |
| **W12-T4-wave1-to-wave12-architecture-retrospective-v1** | **implementer done · Reviewer pending** | 架構回顧文件：§1–§6 完整；Wave 1–12 演進紀錄 + 未來風險預警 |

**Sandbox e2e 摘要（W12-T1）**

| case_ref | 預設 stop_at | `--sandbox-end-to-end` |
|----------|--------------|------------------------|
| `demo_phase` | bundle | ❌ blocked |
| `sampleco/2026-0001` | checkpoint_b | ❌ blocked |
| `additional_demo` | checkpoint_b | ✅ `sandbox_bundle` → manifest |
| `sandbox_client` | cleaning_preview | ❌ blocked |

**驗證命令（W12-T1）**

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp --case-dir cases/additional_demo \
  --mode run --auto-approve-intake --sandbox-end-to-end --format json
python -m unittest tests.test_sandbox_delivery_bundle_v1 tests.test_agent_standard_case_experiment -v
```

**票 state（W12-T1）**：`04_Workflows/tickets/W12-T1-tabular-controlled-end-to-end-delivery-sandbox-v1_state.md`

**W12-T4 摘要（架構回顧）**

| 章節 | 核心內容 |
|------|----------|
| §1 | Wave 1–12 Timeline（12 Wave 一行摘要） |
| §2 | Tabular 演進：MVP → v1 → v2 → controlled E2E |
| §3 | Non-Tabular 演進：blueprint → shadow → metadata |
| §4 | Governance/HITL/Eval/CI/Metrics 演進 |
| §5 | 5 項核心設計原則 |
| §6 | 5 項未來風險與 Wave 13+ 建議 |

**驗證命令（W12-T4）**

```bash
# 文件存在與結構檢查
ls -la docs/wave1-to-wave12-architecture-retrospective-v1.md
grep "^## §" docs/wave1-to-wave12-architecture-retrospective-v1.md | wc -l
# 預期: 7

grep "^| W" docs/wave1-to-wave12-architecture-retrospective-v1.md | wc -l
# 預期: 12
```

**票 state（W12-T4）**：`04_Workflows/tickets/W12-T4-wave1-to-wave12-architecture-retrospective-v1_state.md`

---

## Wave 1–5 進度（2026-06-15 快照）

> **免責聲明**：以下進度表為 Wave 1–5 主要票務狀態快照，供快速查閱；詳細驗收條件與遺留 gaps 請見各票 `*_state.md` 之 C_REPORT。部分票仍為 `accepted_with_gaps` 或 `Reviewer pending`，**不得**視為「Wave 已全部完成」或「CI 已 blocking」。

| Wave | 主題 | 狀態 | 關鍵票 | Reviewer 結論 | 主要交付 |
|------|------|------|--------|---------------|----------|
| **Wave 1** | MVP 主鏈與治理 | **主幹 done** | W1-T1B · W1-T2 · W1-T3B | T1B: `accepted_with_gaps`；T2/T3B: `accepted` | 治理收斂視圖 · L1 trace · 主鏈回歸 runner |
| **Wave 2** | Intake / Routing / Eval | **主幹 done** | W2-T1 · W2-T2-routing-eval | `accepted` | routing catalog YAML · eval cases 骨架；**W2-T2 Multi-Chat 參照票 `accepted_with_gaps`** |
| **Wave 3-TL** | Tabular 工具層 | **4/4 done** | W3-TL-T1～T4 | `accepted_with_gaps` | Catalog/Selector/Executor/Consumer 四件套；**W3-T1 Tool Catalog SSOT `accepted_with_gaps`**（Phase 8.8 分軌） |
| **Wave 4** | Routing ↔ Tool Layer 銜接 | **4/4 done** | W4-T1～T4 | T1/T2/T3: `accepted_with_gaps`；T4: `Reviewer pending` | glue mapping · eval dry-run runner · intake path preview · CI hooks |
| **Wave 5** | Multi-Agent 協作與決策助手 | **T0/T1B done** | W5-T0 · W5-T1 · W5-T1B | T0/T1B: `accepted`；T1 intake rules: `Reviewer pending` | 四角色協作文檔 · intake decision rules · Agent CLI demo；**W5-T1 Skill Registry `accepted_with_gaps`** |

### 驗證命令索引（Wave 1–5 smoke）

```bash
# Wave 1 主鏈回歸
python scripts/run_mvp_mainline_regression.py -v

# Wave 2 routing 文件一致性
python -m unittest tests.test_intake_routing_catalog tests.test_routing_eval_cases -v

# Wave 3-TL 工具層
python -m unittest tests.test_tabular_tool_catalog tests.test_tabular_tool_selector tests.test_tabular_tool_executor -v

# Wave 4 routing glue & eval runner
python -m unittest tests.test_routing_tabular_glue tests.test_routing_eval_runner -v

# Wave 5 intake decision
python -m unittest tests.test_intake_decision_rules_v1 tests.test_agent_intake_decision_demo -v
```

---

## 多 Lane 本輪收口（2026-06-14 · doc-only 索引）

> **命名提醒**：Lane A「最小接案 MVP Wave 4」≠ 本檔 Tabular MVP **Wave 4** routing glue。Lane B = Wave C Phase 2 Governance；Lane C = Control Plane 商業化閉環；Lane D = Tabular **W3-TL-T4**。
>
> **收口語義（2026-06-14）**：各 lane 多數票為 **implemented + tested**（本輪 unittest smoke 全綠），但 **不是 full done**——部分仍 **Reviewer pending**、**blocked_on_approval** 或 **accepted_with_gaps**；**不得**將 design draft / FRAME 寫成 gate 已升格或 mandatory CI 已開。

### 分票收口表（實作 / 測試 / Review·Approval / 未完成）

| Lane | 票号 | 實作完成 | 測試狀態 | Reviewer or Approval | 尚未完成 |
|------|------|----------|----------|----------------------|----------|
| **A** | **W4-MEM-01** | **yes** — `cases_index_lib` enriched · lookup `--verbose` · spec v0.1 | **tested** — `test_lookup_case_history` + `test_build_cases_index` **10/10 OK**（2026-06-14 smoke） | **accepted_with_gaps**（Reviewer 已关 · 2026-06-14） | glob 自動登記 · `schema_fingerprint` deferred → **W4-MEM-02** |
| **A** | **W4-GUARD-01** | **yes** — **T1 IMPL done**（experimental fixture guard · regression entry） | **tested** — guard 6 tests + regression 17/17 OK | **Reviewer pending**（T1 guard 已 IMPL；G2–G4 升格仍 deferred） | G2–G4 schema/ratio 升格 · `--strict-guards` · CI 接入 |
| **B** | **WC-IMPL-L1** | **yes** — L1 advisory · MissingSignalRules v1 · artifact + log | **tested** — `test_toolchain_governance_snapshot_v1` **17/17 OK**；CLI **non-blocking exit 0** | **accepted**（Reviewer 已关） | L2 觀察期證據累積（非本票） |
| **B** | **WC-IMPL-L2** | **no** — **FRAME / design only** | **n/a** | **blocked_on_approval** · `frame_frozen_pending_governance` | G1–G8 + `approval_status.L2=approved` 後方可施工 |
| **B** | **WC-IMPL-SMOKE-CI-L1** | **no** — **FRAME / design only** | **n/a** | **blocked_on_approval** · `frame_ready` | optional_ci workflow 接線；**不得**假設 PR required 已開 |
| **B** | **WC-PRE-06** | **no** — design_ready | **n/a** | **pending_approval** | L2 health gate 升格提案 |
| **B** | **WC-PRE-07** | **no** — design_ready（W5 doc bundle） | **n/a** | **blocked_on_approval** | mandatory smoke CI 设计稿 `docs/toolchain-smoke-mandatory-ci-runner-v1.md` + `WC_PRE_07_approval_template.md`；无批文不得改 PR required · 见 W5-WC-PRE-07 |
| **C** | **WC-T1** · **WC-T2** · **WC-T3** · **WC-T4** · **WC-SMOKE-M2-NIGHTLY** | **yes** — M2 主链已落盘 | **tested** — eligibility / dispatch / comms / order / nightly 模块 UT 含于 Lane C smoke **62/62 OK** | **done**（T3 = `W-next-DISPATCH-CARDS-MVP` **accepted**） | — |
| **C** | **WC-T1-INTEGRATION** | **yes** — eligibility gate 接入 `_dispatch_cards.py` | **tested** — `test_dispatch_cards` + `test_ticket_eligibility` **21/21 OK**；含于 Lane C **62/62 OK** | **accepted_with_gaps**（Reviewer 2026-06-14；AC-6 doc 已由 Scribe 补） | 可选 UT：unresolved-dependency + gate=block；入口 B/C deferred |
| **C** | **WC-T5** | **yes** — 覆盖率契约 + JSON 附录 | **tested** — `test_wc_t5_automation_coverage_contract_v1` 含于 **62/62 OK** | **accepted** | T6/T7 全量 path_id 映射 deferred |
| **C** | **WC-T6** | **yes** — v0.1 骨架 · distill CLI + cards/comms fixture | **tested** — `test_distill_control_plane_skills_lite` **4/4 OK** | **accepted_with_gaps** | v2：reports fixture · `--reports-dir` UT · T5 全量 canonical 映射 |
| **C** | **WC-T7** | **yes** — runbook + runner dry-run + INT 对齐草稿 | **tested** — `test_run_wc_m2_e2e_walkthrough` 含于 **62/62 OK** | **accepted_with_gaps** | v2：runbook T5 path_id 附录 · `--execute` 全自动 STATE（forbidden · HITL） |
| **C** | E2E / nightly | **yes** — 脚本可跑 | **optional · non-gating** — `run_wave_c_nightly_smoke.sh` 本地晚间扫 | **n/a** | **≠ INT Tier-A**；不接 PR required |
| **D** | **W3-TL-T4** | **yes** — consumer · inspect CLI · replay report（2026-06-13 follow-up） | **tested** — consumer **14/14** + replay **8/8** = **22/22 OK**（2026-06-14 smoke） | **accepted_with_gaps**（Reviewer 已关；gaps 见 C_REPORT） | re-execute／Langfuse／`events.jsonl` tail／Local UI replay **out of scope** |

### Lane 摘要（一行）

| Lane | 主題 | 本輪狀態 |
|------|------|----------|
| **A** | 最小接案 MVP · 輕量記憶／護欄 | 記憶層 **accepted_with_gaps**（W4-MEM-01 已关）；**W4-GUARD-01 T1 guard IMPL done**（extended fixtures 需 `--include-extended-fixtures`） |
| **B** | Wave C Phase 2 Governance | **L1 advisory implemented + tested**；L2 / mandatory smoke CI **FRAME · blocked_on_approval** |
| **C** | Control Plane 商業化閉環 | M2 **done** · **WC-T1-INTEGRATION accepted_with_gaps** · M3 契约 **accepted / accepted_with_gaps** |
| **D** | Tabular W3-TL-T4 | **4/4 done** · replay follow-up 已落盘 · unittest 全綠 · 已知 gaps 不含 Local UI |

**Lane 驗證命令（本輪 smoke）**

```bash
# Lane A — case memory index
python scripts/build_cases_index.py --json
python scripts/lookup_case_history.py --client-ref sampleco --verbose
python -m unittest tests.test_lookup_case_history tests.test_build_cases_index -v

# Lane B — governance snapshot L1 advisory（non-blocking）
python scripts/generate_toolchain_governance_snapshot.py --ci-context eval-gate-pr --write --non-blocking
python -m unittest tests.test_toolchain_governance_snapshot_v1 -v

# Lane C — Control Plane M2/M3
python -m unittest tests.test_ticket_eligibility tests.test_dispatch_cards tests.test_ticket_comms tests.test_order_ledger tests.test_wc_t5_automation_coverage_contract_v1 tests.test_distill_control_plane_skills_lite tests.test_run_wc_m2_e2e_walkthrough -v
bash scripts/run_wave_c_nightly_smoke.sh

# Lane D — Tabular outbox consumer + replay report
python -m unittest tests.test_tabular_outbox_consumer tests.test_build_tabular_outbox_replay_report -v
python scripts/build_tabular_outbox_replay_report.py --case-ref demo_phase --outbox-root tests/fixtures/outbox --stdout --format md
```

**索引**：Lane A → `docs/wave4-lane-a-execution-plan-v0.1.md` · Lane B/C → `docs/wave_c/overview.md` · Lane D → 本檔 Wave 3-TL 分欄

---

## 最小接案 MVP · Wave 4（Lane A · ≠ Tabular Wave 4）

**一句話（Agent Lines v1）**：Lane A 護欄 **T1 已 IMPL**——extended fixtures 不得默認混入 regression；G2–G4 真樣本升格仍待批文。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W4-MEM-01** | **done** · Reviewer **`accepted_with_gaps`** | 只讀 case 記憶索引 enriched 字段 → `docs/case-history-lookup-spec-v0.1.md` · `cases/index.json` refresh · lookup `--verbose`；gaps → **W4-MEM-02** |
| **W4-GUARD-01** | **T1 IMPL done · Reviewer pending** | `enforce_fixture_guard()` @ `run_agent_standard_case_regression.py` — **`additional_demo`/`sandbox_client` 需顯式 `--include-extended-fixtures`**；stable 錨點不受影響 · 17 tests OK · README v2 §2.3 · **deferred**：G2–G4 schema/ratio 升格 · `--strict-guards` |

**票 state**：`04_Workflows/tickets/W4-MEM-01_state.md` · `04_Workflows/tickets/W4-GUARD-01_state.md`

---

## 下一步（僅索引，不開新實作票）

| 優先 | 項目 | 歸屬 | 類別 |
|------|------|------|------|
| **1** | ~~WC-T1-INTEGRATION Reviewer 關票~~ · AC-6 doc 已补 | Lane C | **已关票 · accepted_with_gaps** |
| **2** | ~~W4-MEM-01 Reviewer 關票~~ · ~~WC-T6-v2 / WC-T7-v2 gaps~~ | Lane A / C | **已关票** |
| **3** | approval 後才可動：WC-PRE-06/07 L2 · WC-IMPL-L2 · WC-IMPL-SMOKE-CI-L1 · **W4-GUARD-01 G2–G4 升格** | Lane B / A | **blocked_on_approval** |
| 可選 | W3-TL-T4 follow-up：`app/local_ui.py` 嵌入 replay report；`events.jsonl` streaming tail | Wave 3-TL | 可延後 |
| 可選 | W1-T1B-FOLLOWUP（§6.2 Q1–Q5） | Wave 1 | 可延後 |
| 可選 | routing eval 專用 state 檔（與 Multi-Chat W2-T2 區隔） | Wave 2 | 可延後 |
| 可選 | W4-T3-B 單步 execute；mainline regression nightly CI | Tabular Wave 4 | 可延後 |
| 可選 | W6-T2 — 延伸 Skill Card（新案例/schema 類型）| Wave 6 | 可延後 |
| 可延後 | W4-MEM-02 Scribe 收口 · demo walkthrough | Lane A | 可延後 |

---

> **WB-T2/T3/T4 明细**：已并入上方 **「Wave B · Toolchain（WB-T*）」** 总表；本节保留验证命令索引。

**WB-T2 验证**

```bash
python -m unittest tests.test_tool_executor_and_sandbox_contract_v1 -v
python scripts/run_tabular_intake_tool_path.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json
```

**WB-T3 验证**

```bash
python -m unittest tests.test_outbox_and_feedback_layer_contract_v1 -v
python -m tools.inspect_tabular_outbox --case-ref demo_phase --json --outbox-root tests/fixtures/outbox
```

**WB-T4 验证**

```bash
python -m unittest tests.test_toolchain_health_dashboard_v1 tests.test_phase6_int_regression_gate_contract_v1 -v
python scripts/run_toolchain_health_dashboard.py --format json --dry-run
```

**WB-T7 验证**

```bash
python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v
python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v
```

---

## Toolchain Wave B · WB-T5 — Audit Quickview & Case History Spec · **done · accepted_with_gaps**

**一句話**：W10-T3 audit CLI 升格正式 spec；定義 wire format + investigation view（sections/timeline/gaps）；對齊 WB-T3 outbox 命名空間與 Wave 4A case history join；**read-only · investigation-only**。

| 票號 | 狀態 | Phase | 交付摘要 |
|------|------|-------|----------|
| **WB-T5-audit-quickview-and-case-history-spec-v1** | **done** · accepted_with_gaps | **P5 audit 70%→82% · P8.9 join 40%→75%** | `docs/audit-quickview-and-case-history-spec-v1.md` · `tests/test_audit_quickview_and_case_history_spec_v1.py` · README v2 §4 指針 |

**Phase 5 Audit 觀測面**：**70% → 82%**（本票 codify；與 WB-T4 疊加後 dashboard 軸仍 **70%**）  
**Phase 8.9 case-history join 語意**：**40% → 75%**（audit spec §4 + WB-T3 §5 交叉引用）

**驗證命令**

```bash
python -m unittest tests.test_audit_quickview_and_case_history_spec_v1 -v
python -m unittest tests.test_agent_audit_quickview_v1 -v
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json
```

**票 state**：`04_Workflows/tickets/WB-T5-audit-quickview-and-case-history-spec-v1_state.md`

---

## Wave A — Phase 3.5 成本 / 模型 / 风险治理 · **WA-T3 done**

> **命名空間**：本節 **Wave A / P3.5** 與上文 Tabular MVP Wave 1–12 **不同軸**；亦與 `docs/WAVE_A_EXECUTION_PLAN.md` 之 **P3 Trace Done**、**P5 ≥85%** 並列但不混淆。

**一句話**：eval-gate CI、shadow nightly、K-2 治理、ENF shadow 的 gate 行为已收敛为 Phase 3.5 contract SSOT；Wave B/C 可读 §2 假设 PR 必过项与 shadow-only 项，**不会**误开 blocking canary。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **WA-T3-phase3-5-cost-model-governance-contract-v1** | **done · implementer** | `docs/phase3-5-cost-model-governance-contract-v1.md`（§1–§8）· `tests/test_phase3_5_governance_contract_v1.py` · k2/ENF/testing cross-ref |

**Phase 3.5 完成度**：**55% → 83%**（本票 codify 后）

**驗證命令**

```bash
python -m unittest tests.test_phase3_5_governance_contract_v1 tests.test_eval_gate -v
python 04_Workflows/_ops_cycle.py checklist --mode full
```

**票 state**：`04_Workflows/tickets/WA-T3-phase3-5-cost-model-governance-contract-v1_state.md`

---

## 交叉引用

- Toolchain Wave B 快速入口：`docs/wave-b-toolchain-readme-v1.md` · 执行计划：`docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md`
- Observability Wave B：`docs/WAVE_B_EXECUTION_PLAN.md`（**≠** Toolchain）
- 工作流索引：`04_Workflows/WORKFLOW_INDEX.md` §1.5 · §1.26  
- Phase 3.5 gate SSOT：`docs/phase3-5-cost-model-governance-contract-v1.md`  
- Wave C 入口（唯读）：`docs/WAVE_C_EXECUTION_PLAN.md`
- 全局戰報末尾：`04_Workflows/00_Agent_Work_Progress.md`（Wave Dashboard 條目）  
- Tabular 工具層單元驗證：WORKFLOW_INDEX §1.5 所列 unittest 三件套

---

*WAVE-PROGRESS-DASHBOARD · Tabular MVP + Toolchain Wave B + Multi-Lane 收口 · **Phase% SSOT 2026-07-13 · W-PROG-B**（P8.5 **20%** · P9 **24%** · P4 **77%** · P10 **37%** · prev=同日 W-PROG A · 見 Progress／`W-PROG-war-status-phase-refresh-2026-07-13_state.md`）*
