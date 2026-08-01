# Lane A Full-Phase Plan — Governance · Index · Trace · Multi-Agent CP

> **角色**：Lane A Planner · Governance / Index / Trace / Multi-Agent Control Plane  
> **Authority**：`04_Workflows/tickets/W-MASTER-full-phase-plan_state.md` §G1–G4  
> **Playbook**：`docs/full-phase-master-planning-playbook.md`  
> **Phase% SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md` · **2026-06-26**（**本檔不重算**）  
> **Wave Master 交叉**：P7+ 执行票正文见 `W-MASTER-wave-plan_state.md` · 本档 **只规划 Lane A 四组** · **禁止双份维护 Wave 1–5 FRAME 全文**

---

## META

| 欄位 | 值 |
|------|-----|
| **Lane** | L1 + L2 + L3 + L4（8-Lane 映射见 `docs/full-phase-lane-map-v1.md`） |
| **Groups** | G1 治理 · G2 知识/Index · G3 Trace/Obs · G4 Multi-Agent CP |
| **Covered Phases** | P1 · P2 · P3 · P3.5 · P4 · Wave 5 CP 资产 |
| **planning_status** | `frame_ready` |
| **phase_percent_modified** | **false** |
| **closure_claimed** | **false** |
| **last_updated** | 2026-06-26 |

### 已读清单（Lane A Planner）

- `W-MASTER-full-phase-plan_state.md` · `docs/full-phase-master-planning-playbook.md`
- `.cursor/rules/engineering-contract.mdc` · `AGENTS.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md` · `docs/observability.md`
- `docs/p75-intake-gate-control-plane-trace-v1.md` · `docs/p8_p89_evidence_index_v1.md`
- `docs/wave-master-ticket-template-v1.md` · `04_Workflows/review_checklists/wave-next-code-inspector-v1.md`

### 状态依据

Dashboard **2026-06-26**：P1 **90%** · P2 **65%** · P3 **82%** · P3.5 **55%** · P4 **75%**。Lane A 按 **关键缺口** 排序；P1/P3 接近 80% 边界时 **只补 SSOT/批文/contract 最后一档**，不重做 W1-T1B · gov-trace-v2 13/13 · WA-T4 · W5-T0 等已落地能力。

---

## Group 1 — 治理与规则层（Phase 1 + P3.5）

**Phase 姿态**：P1 **90%** 补最后缺口 · P3.5 **55%** 中度缺口（批文边界 + cross-ref）

### DNR（不可重做）

| ID | 已落地 | 证据 |
|----|--------|------|
| DNR-G1-01 | 治理收敛 · ENGINEERING_CONTRACT · engineering-contract.mdc | W1-T1B · `docs/governance-constitution-v1.md` |
| DNR-G1-02 | P3.5 cost/model governance contract | WA-T3 · `docs/phase3-5-cost-model-governance-contract-v1.md` |
| DNR-G1-03 | WC-IMPL-L1 advisory snapshot | `tests/test_toolchain_governance_snapshot_v1` |

---

### A-G1-T1 — governance_dual 解阻 FRAME

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G1-T1-governance-dual-unblock-frame-v1` |
| **Title** | P7 Round-2 governance_dual 五顶要件 checklist FRAME |
| **Goal** | 产出 **doc-only** 解阻 FRAME：列出 governance_dual 真批文、Infra staging slot、Security 外部 POST、allowlist、receiver 五顶前置的 **负责方 · 交付物 · 关票条件**，供 Wave 2 消费；**不负责**取得真批文。 |
| **Scope** | 新建 `docs/governance-dual-unblock-checklist-v1.md`；交叉引用 `W-MASTER-wave-plan` Wave 2 staging 票 · Dashboard P7 Round-2 叙事 · `WH-REV-*` 不可说表 |
| **Non-Goals** | 真批文 · staging POST execute · prod endpoint flip · Phase% 上调 · 修改 `.github/workflows` required |
| **Acceptance Criteria** | AC-1：checklist 含五顶前置，每项有 owner（human/infra/security）· 交付物 · blocked 时 defer 规则；AC-2：每项链到 Wave 2 票 ID 或 `blocked/planning` 占位；AC-3：`non_claims` 表明确「FRAME ≠ Round-2 GO」；AC-4：Reviewer 只读可判 planning 质量 |
| **Dependencies** | 无硬上游；下游：`W2-P7-staging-unblock-*` · G7 Wave 2 |
| **Observability** | `rg "governance_dual|五顶" docs/governance-dual-unblock-checklist-v1.md`；无 runtime verify；`evidence_tier: n/a` |
| **Risks / Edge Cases** | 将 checklist 误标为「批文已齐」→ AC-3 non_claims 必填；与 Wave 2 双份维护 → 本票只 FRAME，执行 SSOT 在 wave-plan |
| **Output Artifact** | `docs/governance-dual-unblock-checklist-v1.md` · 可选 `04_Workflows/tickets/A-G1-T1-governance-dual-unblock-frame-v1_state.md` |
| **B/C/D/O Landing Plan** | **B** Orchestrator 冻结 FRAME → **C** Implementer doc diff only → **D** Reviewer 对照 AC + inspector §3.4 → **O** Scribe Progress 末尾 append（`group_id: G1` · `evidence_tier: n/a`） |
| **Parallelization Note** | ∥ `A-G1-T2` · `A-G1-T4` · G2/G3 doc 票（无共享 mutation surface） |

```yaml
group_id: G1
wave_id: null
ticket_class: doc/spec
human_only_prereqs: []
lifecycle_phase: B
parallel_ok: true
```

---

### A-G1-T2 — WC-PRE-06/07 批文追踪 SSOT

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G1-T2-wc-pre-06-07-approval-tracker-v1` |
| **Title** | WC-PRE-06/07 批文状态机 SSOT（design_ready → approved） |
| **Goal** | 建立 **human-only 关票** 可追踪的批文 SSOT：WC-PRE-06（toolchain observability L0→L1）与 WC-PRE-07（mandatory smoke CI）从 `design_ready` / `pending_approval` 到 `approved` 的状态机、模板字段、解阻后下游票清单。 |
| **Scope** | 新建或 extend `docs/wc-pre-06-07-approval-tracker-v1.md`；引用 `docs/toolchain-observability-governance-upgrade-v1.md` · `docs/toolchain-smoke-mandatory-ci-runner-v1.md` · `WC_PRE_07_approval_template.md` |
| **Non-Goals** | 修改 branch protection · 升格 PR required · 假设批文已获 · 施工 WC-IMPL-L2 |
| **Acceptance Criteria** | AC-1：两票状态枚举 + 转换条件（仅 human 可关 `approved`）；AC-2：`blocks_if_missing` 列出 G6 required CI · W4-GUARD G2–G4 · WC-IMPL-L2；AC-3：关票交付物 = 批文 ID / sign-off 记录位置占位符；AC-4：STATE 标 `blocked` 直至 human 回填 |
| **Dependencies** | 上游：WC-PRE-06/07 design_ready 资产；下游：`A-G1-T3` · `A-G6-T1`（G6 索引，非 Lane A 施工） |
| **Observability** | Doc keyword sanity；`evidence_tier: n/a`；success = Reviewer `accepted*` on planning doc |
| **Risks / Edge Cases** | AI 代填「已批准」→ AC-4 + human_only 标注；与 Wave 5 W5-WC-PRE-06/07 重复 → 本票为 **tracker SSOT**，Wave 5 票为 design bundle |
| **Output Artifact** | `docs/wc-pre-06-07-approval-tracker-v1.md` |
| **B/C/D/O Landing Plan** | **B** FRAME → **C** doc → **D** Reviewer → **O** Scribe append；**关票 O 阶段 = human-only** |
| **Parallelization Note** | ∥ `A-G1-T1` · `A-G1-T5`；**串行** `A-G1-T3`（需批文或 PM 裁定后升格 FRAME 有效） |

```yaml
group_id: G1
ticket_class: doc/spec
human_only_prereqs: ["尚書省 WC-PRE-06/07 批文 sign-off"]
lifecycle_phase: B
parallel_ok: true
```

---

### A-G1-T3 — W4-GUARD G2–G4 升格 FRAME

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G1-T3-guard-schema-ratio-escalation-frame-v1` |
| **Title** | W4-GUARD-01 G2–G4 schema/ratio 升格 FRAME（blocked_on_approval） |
| **Goal** | 在 **W4-GUARD-01 T1 已 IMPL** 前提下，为 G2–G4（schema 真样本 · ratio guard · `--strict-guards` · CI 接入）产出 blocked FRAME + 解阻条件，避免无批文升格 regression。 |
| **Scope** | `docs/w4-guard-g2-g4-escalation-frame-v1.md`；引用 Dashboard Lane A W4-GUARD-01 · `run_agent_standard_case_regression.py` guard 行为 |
| **Non-Goals** | 无批文施工 G2–G4 · 重写 T1 guard · 默认开启 strict · 改 Dashboard Phase% |
| **Acceptance Criteria** | AC-1：G2/G3/G4 分项 AC + 依赖 WC-PRE 或 PM 批文；AC-2：STATE=`blocked/planning`；AC-3：明确 T1 已 landed 证据（17 tests OK）；AC-4：升格后 verify_commands 占位（unittest + regression） |
| **Dependencies** | **blocked_on** `A-G1-T2` 批文或 PM 显式 waive；上游：W4-GUARD-01 T1 |
| **Observability** | `python -m unittest tests.test_agent_standard_case_regression -v`（T1 基线）；FRAME doc review |
| **Risks / Edge Cases** | 与 extended fixtures 默认行为冲突 → FRAME 须保留 `--include-extended-fixtures` 语义 |
| **Output Artifact** | `docs/w4-guard-g2-g4-escalation-frame-v1.md` |
| **B/C/D/O Landing Plan** | **B only**（blocked）→ 批文后 **C** 才可开 implementer 子票 |
| **Parallelization Note** | 与 G1 其他票 **可并行写 FRAME**；**施工串行** 批文 |

```yaml
group_id: G1
ticket_class: blocked/planning
human_only_prereqs: ["WC-PRE 或 PM 批文"]
parallel_ok: true  # planning doc only
```

---

### A-G1-T4 — P3.5 eval-gate / K-2 / ENF shadow 交叉索引

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G1-T4-eval-gate-k2-enf-crossref-index-v1` |
| **Title** | Phase 3.5 eval-gate · K-2 · ENF shadow 诚实交叉索引 |
| **Goal** | 防止 lane chat **误开 blocking canary / required eval gate**：将 WA-T3 contract · `eval-gate-ci.yml` · K-2 playbook · ENF shadow 的 **blocking vs advisory** 边界收成单页 SSOT 索引。 |
| **Scope** | `docs/phase3-5-gate-crossref-index-v1.md`；引用 `docs/phase3-5-cost-model-governance-contract-v1.md` · `docs/k2_deployment_governance.md` · `docs/observability.md` §9 |
| **Non-Goals** | 改 eval 阈值 · 开 prod K-2 主答案 · 升格 CI required |
| **Acceptance Criteria** | AC-1：表格列 gate 名 · blocking? · evidence · non-claim；AC-2：链到 `tests/test_phase3_5_governance_contract_v1`；AC-3：engineering-contract REF-9.7 交叉引用 |
| **Dependencies** | DNR-G1-02 WA-T3 done |
| **Observability** | `python -m unittest tests.test_phase3_5_governance_contract_v1 tests.test_eval_gate -v` |
| **Risks / Edge Cases** | Dashboard 06-26 写 P3.5 55% 与 WA-T3 codify 83% 叙事并存 → 索引只引用 Dashboard Phase 名 **不写 %** |
| **Output Artifact** | `docs/phase3-5-gate-crossref-index-v1.md` |
| **B/C/D/O Landing Plan** | **B→C doc→D→O** |
| **Parallelization Note** | ∥ `A-G1-T1` · `A-G3-T1`（不同路径） |

```yaml
group_id: G1
ticket_class: doc/spec
parallel_ok: true
```

---

### A-G1-T5 — Progress / Dashboard 写入边界协议

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G1-T5-constitution-progress-append-protocol-v1` |
| **Title** | Progress · Dashboard · master_status 写入边界 doc（Governance 独占字段） |
| **Goal** | 为 Multi-Chat Scribe / lane chat 提供 **append-only** 与 **Governance 独占** 字段的 SSOT，含 `evidence_tier` · `run_url` · `group_id` 模板，减少 over-claim 与 Phase% 误改。 |
| **Scope** | `docs/progress-dashboard-append-protocol-v1.md`；引用 `OPS_CYCLE.md` · `full-phase-master-planning-playbook.md` §11 · 宪章 §6.2–§6.3 |
| **Non-Goals** | 修改 Dashboard Phase% 数字 · 写 master_status 正文 · 替代 `_ops_cycle.py` |
| **Acceptance Criteria** | AC-1：谁可写 Progress/Dashboard/master_status 表；AC-2：Progress 末尾条目模板（含 evidence_tier · blocked/next）；AC-3：lane chat **禁止** 改 Phase% 的 enforcement 句；AC-4：链 inspector checklist |
| **Dependencies** | `A-G3-T1` evidence tier 名（可并行，完成后 cross-ref） |
| **Observability** | Doc review；可选 `_ops_cycle.py validate-report --dry-run` 示例 |
| **Risks / Edge Cases** | 与 Scribe 实际习惯冲突 → 模板标 **recommended** 非 mandatory code |
| **Output Artifact** | `docs/progress-dashboard-append-protocol-v1.md` |
| **B/C/D/O Landing Plan** | **B→C doc→D→O** · Scribe 重 O |
| **Parallelization Note** | ∥ `A-G1-T2` · `A-G5-T3`（L5，索引引用）；∥ G2/G3 doc 带 |

```yaml
group_id: G1
ticket_class: doc/spec
parallel_ok: true
```

---

### Group 1 — 为什么这组要先 / 可并行

**要先**：L1 批文与 non-claim 边界是 L4/L6/L7 的 **硬依赖**（`full-phase-lane-map-v1.md` §4）；P7 Round-2 与 required CI 均 blocked_on governance_dual / WC-PRE。**可并行**：G1 五票均为 doc/spec 或 blocked planning，无代码 mutation；`A-G1-T1/T2/T4/T5` 可同时开 chat；`A-G1-T3` 施工 blocked 但 FRAME 可与 T2 并行起草。

---

## Group 2 — 知识与索引层（Phase 2）

**Phase 姿态**：P2 **65%** 中度缺口 · **本轮无新 index job**（Dashboard 06-26）

### DNR（不可重做）

| ID | 已落地 | 证据 |
|----|--------|------|
| DNR-G2-01 | Phase1 ingest_verify · INV1–INV4 | Progress D2/D3 |
| DNR-G2-02 | R1/R2 retrieve + Postgres cross-check | rag smoke |
| DNR-G2-03 | WA-T1 knowledge indexing contract | `docs/phase2-knowledge-indexing-contract-v1.md` |

---

### A-G2-T1 — index job 触发 hook 设计 + skeleton CLI

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G2-T1-index-job-scheduler-hook-v1` |
| **Title** | Index job 触发 hook 设计 + skeleton CLI（不破坏 seed INV） |
| **Goal** | 补 **规模化排程** 缺口：设计 index job 触发 hook + skeleton CLI（dry-run / plan-only），**不**破坏既有 ingest_verify seed 与 INV 约束。 |
| **Scope** | 设计 doc + `scripts/run_index_job_hook_v1.py` skeleton（或等价）；引用 WA-T1 contract · `Master_Map.json` runners |
| **Non-Goals** | 生产 cron 部署 · 重写 ingest pipeline · GraphRAG 全量 · 宣称 P2 closure |
| **Acceptance Criteria** | AC-1：CLI 返回稳定 `dict`（`ok` · `message` · `planned_jobs[]`）；AC-2：默认 dry-run · 不写生产 index；AC-3：unittest ≥3 断言 skeleton 行为；AC-4：doc 列解阻条件（infra/PM） |
| **Dependencies** | DNR-G2-03 WA-T1；可选 `A-G2-T2` gap 清单 |
| **Observability** | `python scripts/run_index_job_hook_v1.py --dry-run --format json`；`python -m unittest tests.test_index_job_hook_v1 -v` |
| **Risks / Edge Cases** | skeleton 被标 complete → AC 分 MVP vs stretch；路径硬编码 → Rule 6 gov_paths |
| **Output Artifact** | 设计 doc · skeleton script · test module |
| **B/C/D/O Landing Plan** | **B→C build→D verify→O** Progress append · `evidence_tier: L-local` |
| **Parallelization Note** | ∥ `A-G2-T2`；**串行** `A-G2-T5`（依赖 index 策略） |

```yaml
group_id: G2
ticket_class: build
mvp_allowed: true
parallel_ok: true
```

---

### A-G2-T2 — WA-T1 contract vs 实际 ingest gap 审计

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G2-T2-phase2-index-contract-gap-audit-v1` |
| **Title** | Phase 2 WA-T1 contract vs 实际 ingest 能力 gap 审计 |
| **Goal** | 产出 **schema 漂移 / SSOT 缺口** 清单：WA-T1 契约字段 vs 当前 ingest_verify · index_status · eval-gate index_cases 实际能力。 |
| **Scope** | `docs/phase2-index-contract-gap-audit-v1.md`；只读对照 contract test · observability §9 index_cases |
| **Non-Goals** | 修复所有 gap · 新 mandatory index job · Phase% 上调 |
| **Acceptance Criteria** | AC-1：gap 表（字段 · 期望 · 实际 · 优先级 · 建议票）；AC-2：每条 gap 有 verify 命令或 artifact 引用；AC-3：`non_claims` 审计 ≠ 已修复 |
| **Dependencies** | DNR-G2-03 |
| **Observability** | `python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v` |
| **Risks / Edge Cases** | 与 Observability Wave B WAVE-B-P* 混淆 → 命名空间表 |
| **Output Artifact** | `docs/phase2-index-contract-gap-audit-v1.md` |
| **B/C/D/O Landing Plan** | **B→C doc→D→O** |
| **Parallelization Note** | ∥ `A-G2-T1` · `A-G2-T4` |

```yaml
group_id: G2
ticket_class: doc/spec
parallel_ok: true
```

---

### A-G2-T3 — RAG E2E 问答 FRAME

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G2-T3-rag-e2e-answer-frame-v1` |
| **Title** | RAG E2E 问答 FRAME（LLM synthesis · planning only） |
| **Goal** | 为 **E2E 问答 / GraphRAG** 大缺口建 honest FRAME：范围 · AC · 依赖 P2 index job · 非本 sprint 施工。 |
| **Scope** | `docs/phase2-rag-e2e-answer-frame-v1.md` |
| **Non-Goals** | LLM synthesis 实现 · prod RAG selector 改线 · 宣称 demo 问答已验收 |
| **Acceptance Criteria** | AC-1：FRAME 含 MVP vs stretch；AC-2：**串行**依赖 `A-G2-T2` gap 清单引用；AC-3：`ticket_class: blocked/planning` 或 doc-only planning |
| **Dependencies** | `A-G2-T2` |
| **Observability** | Doc review only · 引用现有 rag smoke 命令作 baseline |
| **Risks / Edge Cases** | 与 K-2 主答案混淆 → non_claims 分轨 |
| **Output Artifact** | `docs/phase2-rag-e2e-answer-frame-v1.md` |
| **B/C/D/O Landing Plan** | **B only**（planning） |
| **Parallelization Note** | 串行 `A-G2-T2` 后；与 G1/G3 doc **可并行** |

```yaml
group_id: G2
ticket_class: blocked/planning
parallel_ok: false  # after T2
```

---

### A-G2-T4 — graphrag_jobs 状态机设计

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G2-T4-graphrag-jobs-state-machine-v1` |
| **Title** | graphrag_jobs 状态机设计 doc（blocked but worth planning） |
| **Goal** | Document **graphrag_jobs** 状态机（queued/running/succeeded/failed）与 observability 挂钩点，供未来 index job 票消费。 |
| **Scope** | `docs/phase2-graphrag-jobs-state-machine-v1.md` |
| **Non-Goals** | DB migration · 生产 GraphRAG 跑批 |
| **Acceptance Criteria** | AC-1：状态转移图 + 字段表；AC-2：链 WA-T1 · observability index_cases；AC-3：blocked 标注 |
| **Dependencies** | 无硬阻塞；可选 `A-G2-T2` |
| **Observability** | Doc review |
| **Risks / Edge Cases** | 过早施工 → 明确 defer 至 index hook 解阻后 |
| **Output Artifact** | `docs/phase2-graphrag-jobs-state-machine-v1.md` |
| **B/C/D/O Landing Plan** | **B→C doc** |
| **Parallelization Note** | ∥ `A-G2-T1/T2` |

```yaml
group_id: G2
ticket_class: doc/spec
parallel_ok: true
```

---

### A-G2-T5 — smoke_corpus 扩展 FRAME

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G2-T5-smoke-corpus-expansion-v1` |
| **Title** | smoke_corpus 扩展 FRAME（blocked on verify 策略） |
| **Goal** | 规划 **非种子** corpus 扩展的 verify 策略与 FRAME，避免破坏 ingest seed INV。 |
| **Scope** | `docs/phase2-smoke-corpus-expansion-frame-v1.md` |
| **Non-Goals** | 实际扩展 corpus 文件 · 无 PM 策略施工 |
| **Acceptance Criteria** | AC-1：PM 裁定项清单；AC-2：独立 verify 需求；AC-3：**blocked** 直至 `A-G2-T1` 策略 + PM sign-off |
| **Dependencies** | `A-G2-T1` · PM 策略 |
| **Observability** | n/a until unblocked |
| **Risks / Edge Cases** | 与 eval fixture 路径冲突 → 引用 tests/fixtures 惯例 |
| **Output Artifact** | FRAME doc |
| **B/C/D/O Landing Plan** | **B only** |
| **Parallelization Note** | 串行 `A-G2-T1` |

```yaml
group_id: G2
ticket_class: blocked/planning
human_only_prereqs: ["PM verify 策略裁定"]
parallel_ok: false
```

---

### Group 2 — 为什么这组要先 / 可并行

**要先**：L7 商业流依赖 L2 index 就绪（lane-map §4），但 **65% 中度缺口** 不要求阻塞 G1/G3 doc。**可并行**：`A-G2-T1/T2/T4` 可同时；`A-G2-T3/T5` 串行 gap/策略。与 G1/G3 **Foundation doc 带** 并行无 mutation 冲突。

---

## Group 3 — 可观测与 Trace 层（Phase 3 + trace 轴）

**Phase 姿态**：P3 **82%** 补最后缺口 · Langfuse/PG 对齐 **deferred**

### DNR（不可重做）

| ID | 已落地 | 证据 |
|----|--------|------|
| DNR-G3-01 | gov-trace-v2 13/13 · observability.md | Dashboard P3 |
| DNR-G3-02 | P75 trace SSOT | `docs/p75-intake-gate-control-plane-trace-v1.md` |
| DNR-G3-03 | P7 advisory CI 索引 | `docs/P7_ADVISORY_CI_INDEX.md` |

---

### A-G3-T1 — 证据 tier 统一 SSOT

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G3-T1-evidence-tier-ssot-v1` |
| **Title** | L-local / CI-advisory / GA-remote / prod 证据 tier 统一 SSOT |
| **Goal** | 将 `p8_p89_evidence_index_v1.md` · P7 索引 · Full-Phase playbook 的 tier 命名 **收敛为 Lane 级 SSOT**，供 Reviewer / Scribe / W5-T3 observer 只读消费。 |
| **Scope** | Extend `docs/p8_p89_evidence_index_v1.md` §1 或新建 `docs/evidence-tier-ssot-v1.md`（二选一，避免双 SSOT）；含 `evidence_tier` · `evidence_kind` YAML 模板 |
| **Non-Goals** | 宣称 GA-remote 已存在 · 改 Phase% · 替代 inspector checklist |
| **Acceptance Criteria** | AC-1：四 tier 定义 + 禁止表述表；AC-2：P3 trace 票 B_REPORT 字段对齐；AC-3：链 `wave-next-code-inspector-v1.md` · `A-G1-T5`；AC-4：无 run URL 时 honest pending 模板 |
| **Dependencies** | DNR-G3-02 · 现有 p8_p89 index |
| **Observability** | Doc + `rg evidence_tier docs/` sanity |
| **Risks / Edge Cases** | 与 P7 专线索引重复 → 主 SSOT + P7 cross-ref |
| **Output Artifact** | Tier SSOT doc（单权威路径） |
| **B/C/D/O Landing Plan** | **B→C doc→D→O** |
| **Parallelization Note** | ∥ `A-G3-T2/T4` · G1 `A-G1-T5`（完成后互链） |

```yaml
group_id: G3
ticket_class: doc/spec
parallel_ok: true
```

---

### A-G3-T2 — P8/P8.9 delivery observability contract

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G3-T2-p89-delivery-observability-contract-v1` |
| **Title** | P8/P8.9 delivery observability contract doc |
| **Goal** | 补 **W3-P89-OBS 待建** 缺口：delivery 阶段 trace 字段 · MP-SMOKE 步 3–7 · metrics · verification bundle 的 observability contract（doc-only）。 |
| **Scope** | `docs/p8_p89_delivery_observability_contract_v1.md`；引用 p75 upstream SSOT · outbox contract · MP-SMOKE artifacts |
| **Non-Goals** | HTTP webhook T4 · prod SLA · 新 mandatory trace 字段无 schema 流程 |
| **Acceptance Criteria** | AC-1：字段表 + 场景矩阵（P8 operator · P8.9 consumer）；AC-2：新字段须走 `A-G3-T4` 流程；AC-3：链 `A-G3-T1` tier；AC-4：unittest 引用只读（MP-SMOKE export） |
| **Dependencies** | DNR-G3-02 · `A-G3-T1`（可并行起草） |
| **Observability** | `python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json`；`python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json` |
| **Risks / Edge Cases** | 与 p8_p89 evidence index 重复 → 分工：index=tier，contract=字段 |
| **Output Artifact** | `docs/p8_p89_delivery_observability_contract_v1.md` |
| **B/C/D/O Landing Plan** | **B→C doc→D→O** |
| **Parallelization Note** | ∥ `A-G3-T1/T4` |

```yaml
group_id: G3
ticket_class: doc/spec
parallel_ok: true
```

---

### A-G3-T3 — Langfuse/PG 对齐 deferred 索引

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G3-T3-langfuse-pg-alignment-deferred-index-v1` |
| **Title** | Langfuse/PG 对齐 deferred 项索引 + 解阻条件 |
| **Goal** | 诚实索引 Dashboard「Langfuse/PG 对齐 deferred」：列 W1-T2 ingest soak · Wave C unified query · 解阻条件，**不开**新 soak 施工（除非另票）。 |
| **Scope** | `docs/phase3-langfuse-pg-deferred-index-v1.md`；引用 `observability.md` §4.2.1 · §7 · `WAVE_B_EXECUTION_PLAN.md` Wave C 留项 |
| **Non-Goals** | 宣称 PG/Langfuse 已统一 · prod soak · OpenTelemetry |
| **Acceptance Criteria** | AC-1：deferred 项表 + owner + 解阻条件；AC-2：现有 13/13 trace unittest 为 baseline 引用；AC-3：`blocked but worth planning` |
| **Dependencies** | DNR-G3-01 |
| **Observability** | `python -m unittest tests.test_trace_schema tests.test_logging_adapter -v` |
| **Risks / Edge Cases** | 与 P5 live soak 混淆 → 交叉引用 WAVE-A-P5 |
| **Output Artifact** | deferred index doc |
| **B/C/D/O Landing Plan** | **B→C doc** |
| **Parallelization Note** | ∥ G3 其他 doc 票 |

```yaml
group_id: G3
ticket_class: blocked/planning
parallel_ok: true
```

---

### A-G3-T4 — trace canonical schema 增量流程

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G3-T4-trace-canonical-schema-append-v1` |
| **Title** | 新 trace 字段必须增 §Canonical schema 流程 doc |
| **Goal** | 制度化 **p75-intake-gate** 与 **gov-trace-v2** 的字段增量流程，防止 Wave 3/5/observer ad-hoc 字段。 |
| **Scope** | `docs/trace-canonical-schema-append-protocol-v1.md`；引用 `p75-intake-gate-control-plane-trace-v1.md` §治理规则 · `observability/trace_schema_v2.json` |
| **Non-Goals** | 批量新增字段 · 改 gov-trace-v2 13/13 baseline |
| **Acceptance Criteria** | AC-1：PR/checklist 步骤（doc row + changelog + consumer 更新）；AC-2：示例走 `intake_decision_id` 已有字段；AC-3：Reviewer 可判合规 |
| **Dependencies** | DNR-G3-02 |
| **Observability** | Doc review · `rg "Canonical trace schema" docs/` |
| **Risks / Edge Cases** | 流程过重 → MVP = doc-only gate，code lint defer |
| **Output Artifact** | append protocol doc |
| **B/C/D/O Landing Plan** | **B→C doc→D→O** |
| **Parallelization Note** | ∥ `A-G3-T1/T2` · **下游** `W5-T3` observer 须消费 |

```yaml
group_id: G3
ticket_class: doc/spec
parallel_ok: true
```

---

### A-G3-T5 — P75 upstream ↔ gov-trace-v2 crosswalk

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G3-T5-p75-gov-trace-crosswalk-v1` |
| **Title** | P7.5 upstream trace ↔ gov-trace-v2 crosswalk（glue doc） |
| **Goal** | 补 **trace contract 缺口**：映射 p75 §Canonical 字段与 gov-trace-v2 / MP-SMOKE artifact 键，供 W5-T3 observer 只读 join。 |
| **Scope** | `docs/p75-gov-trace-crosswalk-v1.md`；只读对照，不改 runtime |
| **Non-Goals** | 合并两套 schema 为单一 JSON schema · G-1–G-5 runtime |
| **Acceptance Criteria** | AC-1：crosswalk 表（p75 字段 · gov-trace 字段 · join key · 场景）；AC-2：链 `A-G3-T4`；AC-3：W5-T3 索引引用（不重复 FRAME 全文） |
| **Dependencies** | DNR-G3-02 · `A-G3-T4`（可并行） |
| **Observability** | MP-SMOKE + gate CLI spot-check（p75 doc §Verify commands） |
| **Risks / Edge Cases** | `run_id` 缺失 → 诚实写 alias 规则（p75 doc 已有） |
| **Output Artifact** | crosswalk doc |
| **B/C/D/O Landing Plan** | **B→C doc→D→O** |
| **Parallelization Note** | ∥ `A-G3-T2` · Wave 5 **`W5-T3`** 施工可并行（只读消费） |

```yaml
group_id: G3
wave_id: W5  # consumer cross-ref only
ticket_class: doc/spec
parallel_ok: true
```

> **Wave 5 去重**：`W5-T3-evidence-observer-v1` **build** 正文见 `W-MASTER-wave-plan_state.md` §Wave 5；Lane A 只索引 + 提供 trace_fields SSOT（T4/T5）。

---

### Group 3 — 为什么这组要先 / 可并行

**要先**：L3 是 L7 的 **硬依赖**（禁止 ad-hoc trace）；P3 **82%** 仅补 tier/contract/deferred 文档，不重做 trace v2。**可并行**：G3 五票全 doc/spec；与 G1/G2 Foundation 带并行；`W5-T3` build 可与 G3 doc 并行（不同 paths）。

---

## Group 4 — 多智能体协作控制面（Phase 4 + Wave 5）

**Phase 姿态**：P4 **75%** 中度缺口 · Wave 5 = Master CP SSOT

### DNR（不可重做）

| ID | 已落地 | 证据 |
|----|--------|------|
| DNR-G4-01 | Multi-Chat 四角色 · phase4 contract | WA-T4 · multi_chat_roles.mdc |
| DNR-G4-02 | `.cursor/commands` MVP · wave-master schema | W5-T1 · W5-T2 |
| DNR-G4-03 | dispatch cards · WC-T1-INTEGRATION | `tests/test_dispatch_cards` |

---

### A-G4-T1 — 双 CP 叙事对齐

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G4-T1-dual-cp-narrative-alignment-v1` |
| **Title** | W-MASTER-full-phase vs wave-plan vs W-ORCH 叙事对齐 doc |
| **Goal** | 消除 **双 CP 叙事漂移**：明确 Full-Phase 10-Group · Wave Master W1–5 · Wave-next 战术 CP 的权威位阶与写回规则。 |
| **Scope** | `docs/dual-control-plane-narrative-v1.md`；更新 `full-phase-lane-map-v1.md` 交叉引用（append 一节，非重写） |
| **Non-Goals** | 合并三份 state 为单文件 · 改 Wave 1–5 正文 |
| **Acceptance Criteria** | AC-1：位阶表 + output file map；AC-2：禁止双份维护列表；AC-3：Multi-Chat 起手口令模板 |
| **Dependencies** | W-MASTER-full-phase · W-MASTER-wave-plan 已 frame_ready |
| **Observability** | Doc review · playbook §13 一致性 |
| **Risks / Edge Cases** | 与 orchestrator chat 口述冲突 → SSOT 位阶句 |
| **Output Artifact** | narrative alignment doc |
| **B/C/D/O Landing Plan** | **B→C doc→D→O** |
| **Parallelization Note** | ∥ `A-G4-T4/T5/T6` · `W5-T5` |

```yaml
group_id: G4
ticket_class: doc/spec
parallel_ok: true
```

---

### A-G4-T2 — W6-T10 orchestrator checkpoint cleanup

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G4-T2-w6-t10-orchestrator-cleanup-v1` |
| **Title** | W6-T10 orchestrator checkpoint workaround runtime 收敛 |
| **Goal** | 收敛 W6-T10 **deferred**：移除 orchestrator auto-approve bypass / outbox redirect，改接 `maybe_create_checkpoint_a/b(..., auto_approve=*)` 与直接 `outbox_root_override`（W6-T5/T6 已 landed）。 |
| **Scope** | `scripts/run_agent_standard_case_experiment.py` · 相关 tests · docstring 更新 |
| **Non-Goals** | 重写整合层 · S15 notify · sandbox e2e CP-B 完整路径 |
| **Acceptance Criteria** | AC-1：24/24+ orchestrator unittest 绿；AC-2：无 LEGACY redirect 路径（或显式 LEGACY 标且 AC 列 removal）；AC-3：C_REPORT `accepted*` |
| **Dependencies** | W6-T5/T6 done · DNR-G4-03 不冲突 |
| **Observability** | `python -m unittest tests.test_agent_standard_case_experiment -v` |
| **Risks / Edge Cases** | 破坏 custom outbox 测试 → 更新 `test_custom_outbox_root_*` |
| **Output Artifact** | code diff · ticket STATE |
| **B/C/D/O Landing Plan** | **B→C build→D→O** |
| **Parallelization Note** | ∥ G4 doc 票 · ∥ `A-G4-T3`（不同模块） |

```yaml
group_id: G4
ticket_class: build
parallel_ok: true
```

---

### A-G4-T3 — dispatch eligibility 可选 UT

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G4-T3-dispatch-eligibility-ut-v1` |
| **Title** | dispatch eligibility 可选 UT（unresolved-dependency · gate=block） |
| **Goal** | 补 WC-T1-INTEGRATION **accepted_with_gaps**：unresolved-dependency + gate=block 的 optional UT，不扩 dispatch 产品面。 |
| **Scope** | `tests/test_dispatch_cards.py` 或 sibling · 最小增量 |
| **Non-Goals** | 新 dispatch product 行为 · 改 eligibility 主逻辑 |
| **Acceptance Criteria** | AC-1：≥2 新 UT 覆盖 gap 场景；AC-2：既有 21/21 不回归；AC-3：AC-6 doc 交叉引用 |
| **Dependencies** | WC-T1-INTEGRATION accepted_with_gaps |
| **Observability** | `python -m unittest tests.test_dispatch_cards tests.test_ticket_eligibility -v` |
| **Risks / Edge Cases** |  scope 膨胀 → Rule 3 最小增量 |
| **Output Artifact** | test diff |
| **B/C/D/O Landing Plan** | **B→C→D→O** |
| **Parallelization Note** | ∥ `A-G4-T2` |

```yaml
group_id: G4
ticket_class: build
parallel_ok: true
```

---

### A-G4-T4 — Multi-Chat commands SSOT 索引（消费 W5-T1）

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G4-T4-multi-chat-commands-ssot-index-v1` |
| **Title** | Multi-Chat `.cursor/commands` SSOT 索引与维护边界（Wave 5 W5-T1） |
| **Goal** | Lane A **只索引不双份维护** W5-T1：commands 路径 · 角色映射 · 与 `multi_chat_roles.mdc` 对齐表。 |
| **Scope** | Append `docs/wave-master-ticket-template-v1.md` 或 `04_Workflows/tickets/README.md` · 引用 `.cursor/commands/*.md` |
| **Non-Goals** | 重写 commands · Wave 1 维护 schema |
| **Acceptance Criteria** | AC-1：commands 清单 + owner=Wave 5；AC-2：Lane chat 消费规则；AC-3：若 W5-T1 未 delivery 标 `TBD: W5-T1` |
| **Dependencies** | **W5-T1-multi-chat-commands-v1**（Wave 5 SSOT） |
| **Observability** | `ls .cursor/commands/` · README 链接检查 |
| **Risks / Edge Cases** | 与 ticket-implementer 重复 → 单一索引点 |
| **Output Artifact** | index section in README or docs |
| **B/C/D/O Landing Plan** | **B→C doc**（维护票在 Wave 5） |
| **Parallelization Note** | ∥ `A-G4-T5/T6` |

```yaml
group_id: G4
wave_id: W5
ticket_class: doc/spec
parallel_ok: true
```

---

### A-G4-T5 — Wave Master ticket schema SSOT 索引（消费 W5-T2）

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G4-T5-wave-master-schema-ssot-index-v1` |
| **Title** | Wave Master ticket schema / FRAME 扩展 SSOT 索引（Wave 5 W5-T2） |
| **Goal** | 确保 Lane A / Full-Phase FP-* 票 **group_id** · observability 栏与 W5-T2 template 对齐；Lane 只消费。 |
| **Scope** | 交叉引用 `docs/wave-master-ticket-template-v1.md` · `_templates/ticket_state.template.md` · 本档 ticket YAML 块 |
| **Non-Goals** | 新建第二 template 主版本 |
| **Acceptance Criteria** | AC-1：FP-* 与 W*-P* 字段对照表；AC-2：Full-Phase 必填 `group_id` enforcement 句 |
| **Dependencies** | W5-T2 |
| **Observability** | Template file existence · playbook §4 一致性 |
| **Risks / Edge Cases** | schema 漂移 → 建议 W5-T4 reviewer checklist |
| **Output Artifact** | index / cross-ref doc section |
| **B/C/D/O Landing Plan** | **B→C doc** |
| **Parallelization Note** | ∥ `A-G4-T4/T6` |

```yaml
group_id: G4
wave_id: W5
ticket_class: doc/spec
parallel_ok: true
```

---

### A-G4-T6 — cross-wave playbook 索引（对齐 W5-T5）

| 栏位 | 内容 |
|------|------|
| **Ticket ID** | `A-G4-T6-cross-wave-playbook-index-v1` |
| **Title** | Lane / playbook / evidence 索引 rollup（对齐 W5-T5） |
| **Goal** | 为 Lane A chat 提供 **单页入口**：playbook · state · inspector · evidence index · commands 的 rollup（**不**重复 Wave 1–5 FRAME）。 |
| **Scope** | Extend `04_Workflows/WORKFLOW_INDEX.md` 新节或 `docs/full-phase-lane-map-v1.md` §9；链 W5-T5 deliverable |
| **Non-Goals** | 重写 WORKFLOW_INDEX 全文 |
| **Acceptance Criteria** | AC-1：Lane A 开读顺序 10 步内；AC-2：链本档四组 ticket 表；AC-3：与 `A-G4-T1` 位阶一致 |
| **Dependencies** | `A-G4-T1`（可并行起草）· W5-T5 |
| **Observability** | Link check · Reviewer spot-check |
| **Risks / Edge Cases** | 索引腐烂 → owner=Wave 5 + Lane A append 规则 |
| **Output Artifact** | WORKFLOW_INDEX section or lane-map §9 |
| **B/C/D/O Landing Plan** | **B→C doc→D→O** |
| **Parallelization Note** | ∥ G4 其他 doc · Wave 5 W5-T5 **共交付或分工**（避免双份 rollup） |

```yaml
group_id: G4
wave_id: W5
ticket_class: doc/spec
parallel_ok: true
```

> **Wave 5 施工票索引（Lane A 不重复 FRAME）**

| Wave 5 ID | 职责 | Lane A 关系 |
|-----------|------|-------------|
| **W5-T1** | commands SSOT | `A-G4-T4` 只索引 |
| **W5-T2** | schema SSOT | `A-G4-T5` 只索引 |
| **W5-T3** | evidence observer build | `A-G3-T4/T5` 提供 trace_fields |
| **W5-T4** | Master Plan Review checklist | G6/Reviewer 消费 |
| **W5-T5** | playbook rollup | 与 `A-G4-T6` 对齐分工 |

---

### Group 4 — 为什么这组要先 / 可并行

**要先**：L4 CP schema 是 Wave 1 **只消费不维护** 的前置（DNR-07）；P4 **75%** 优先 W6-T10 cleanup + dispatch UT，不重做 Multi-Chat。**可并行**：G4 三 doc 票与 G1/G3 doc 带并行；`A-G4-T2/T3` build 与 doc 票并行（不同 paths）；Wave 5 W5-T1/T2/T3 由 Chat 5 施工，Lane A 用 T4/T5/T6 **索引对齐** 避免双份维护。

---

## Lane A 并行化总览

| 并行带 | Tickets | 条件 |
|--------|---------|------|
| **Foundation doc** | G1 T1/T2/T4/T5 · G2 T1/T2/T4 · G3 全组 · G4 T1/T4/T5/T6 | 无共享 mutation |
| **Build** | G2-T1 · G4-T2/T3 · Wave5 W5-T3 | AllowedPaths 不重叠 |
| **Blocked planning** | G1-T3 · G2-T3/T5 · G3-T3 | 仅 FRAME/checklist |
| **Human gate** | G1-T2 关票 · G1-T3 施工 | 尚書省批文 |

### 禁止并行（Lane A 须知）

| Surface | 规则 |
|---------|------|
| `run_agent_standard_case_experiment.py` | `A-G4-T2` 单 owner |
| `.cursor/commands/*` schema | Wave 5 W5-T1 单 owner · Lane A 只索引 |
| Dashboard Phase% | **禁止任何 Lane A 票修改** |
| `delivery/notification_gateway_v1.py` | 非 Lane A 范围 · G7 owner |

---

## Non-Claims（Lane A 全局）

| 禁止宣称 | 正确表述 |
|----------|----------|
| 本 plan 完成 = Phase closure | doc-only · Phase% 不变 |
| G1 FRAME = governance_dual 已解阻 | checklist / tracker only |
| G2 skeleton = index job 生产就绪 | dry-run / planning |
| G3 doc = Langfuse/PG 已对齐 | deferred 索引 |
| G4 索引 = W5-T1/T2 已 delivery | 以 W5 STATE 为准 · TBD 诚实标 |
| L-local = GA-remote | `A-G3-T1` tier SSOT |

---

## Cross-References

| 类型 | 路径 |
|------|------|
| Full-Phase Master | `04_Workflows/tickets/W-MASTER-full-phase-plan_state.md` |
| Playbook | `docs/full-phase-master-planning-playbook.md` |
| 8-Lane map | `docs/full-phase-lane-map-v1.md` |
| Wave Master | `04_Workflows/tickets/W-MASTER-wave-plan_state.md` |
| Dashboard SSOT | `docs/WAVE_PROGRESS_DASHBOARD.md` |
| Inspector | `04_Workflows/review_checklists/wave-next-code-inspector-v1.md` |
| P75 trace | `docs/p75-intake-gate-control-plane-trace-v1.md` |
| Evidence index | `docs/p8_p89_evidence_index_v1.md` |

---

## STATE

```yaml
overall_status: frame_ready
planning_status: frame_ready
lane: A
groups_defined: G1-G4
tickets_defined: 21  # G1×5 + G2×5 + G3×5 + G4×6
phase_percent_modified: false
closure_claimed: false
next_action: "Full-Phase Master Review · 各 A-G*-T* 开 _state.md FRAME · Wave 5 施工 W5-T1/T2/T3"
last_updated: 2026-06-26
```

---

*LANE-A-full-phase-plan · Lane A Planner · 2026-06-26 · doc-only · Phase% frozen at Dashboard 06-26*
