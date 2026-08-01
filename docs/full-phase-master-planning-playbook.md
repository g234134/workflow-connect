# Full-Phase Master Planning Playbook

> **编排 SSOT**：`04_Workflows/tickets/W-MASTER-full-phase-plan_state.md`  
> **8-Lane 索引**：`docs/full-phase-lane-map-v1.md`  
> **后段战术（P7+ planned tickets）**：`04_Workflows/tickets/W-MASTER-wave-plan_state.md` · `docs/wave-master-ticketing-playbook.md`  
> **Phase% SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md`（**2026-06-27** · **本 playbook 不重算**）  
> **角色边界**：`.cursor/rules/multi_chat_roles.mdc` · `docs/phase4-multi-agent-collaboration-contract-v1.md`

---

## 1. 本 Playbook 解决什么问题

**Full-Phase Master Orchestrator** 已将 Phase 1 → Phase 10.5 全部未完成工作收斂为 **10 个任务群组（G1–G10）**。本 playbook 告诉后续 **lane planner / implementer / reviewer / scribe** chat：

1. 如何 **读同一份 state** 而不各自发明任务盘。
2. 如何 **避免重做** 已落地能力（DNR 表）。
3. 如何 **写合规 ticket**（含 `group_id` · evidence tier · ticket class）。
4. 什么票 **可直接 build**，什么票 **blocked but still worth planning**。
5. **Reviewer 最后如何验收整盘**（Full-Phase Master Review）。

**本 playbook 不做**：功能施工 · Phase% 上调 · required CI 升格 · prod/staging 真执行 · closure 宣稱。

**產品主線敘事（與 Phase 編排正交）**：This repo's core product path is tabular data cleaning and delivery automation; governance / CI / GA lines are supporting rails, not the primary product outcome. 見 `docs/TABULAR_MVP_SSOT.md`。

---

## 2. 后续 Lane Chat 如何读同一份 State

### 2.1 共通开读顺序（所有 Lane Chat）

```
1. AGENTS.md §初始化校準（至少 1–4 步；Multi-Chat 加 multi_chat_roles）
2. .cursor/rules/engineering-contract.mdc（执行层）
3. docs/full-phase-master-planning-playbook.md（本档）
4. 04_Workflows/tickets/W-MASTER-full-phase-plan_state.md（全文 · G1–G10）
5. docs/full-phase-lane-map-v1.md（8-Lane 横向 · 与 10-Group 对照）
6. docs/WAVE_PROGRESS_DASHBOARD.md — 只读己 Group 覆盖的 Phase 列
7. 04_Workflows/tickets/README.md — ticket state 机制
8. （G7–G10 必加）W-MASTER-wave-plan_state.md — 只读己 Wave 区块
9. （G7–G10 涉 P7/P85/P9）W-ORCH-wave-next-control-plane-v1 + docs/wave-next-playbook.md
10. （G3/G6/G7/G8/G9）p75 trace · p8_p89 evidence index · matrix · inspector
11. （**人类 Phase 收口前**）本档 §15 三档 closure playbook — **不得**跳过直接改 Phase% 或 dispatch GA
```

### 2.2 Group → Lane → Wave 对照（开 chat 前确认）

| Group | 8-Lane | Wave Master 区块 | 典型 Chat 口令 |
|-------|--------|------------------|----------------|
| G1 | L1 | Wave 5 WC-PRE | `/wave-master-planner` 或 Full-Phase lane |
| G2 | L2 | — | Full-Phase lane · FP-G2-* |
| G3 | L3 | Wave 5 W5-T3 | Full-Phase + Wave 5 交叉 |
| G4 | L4 | Wave 5 W5-T1/T2/T5 | `/wave-master-planner` Wave 5 |
| G5 | L5 | Wave 4 closure | Scribe 重 O |
| G6 | L6 | Wave 2 advisory/matrix | `/wave-master-planner` Wave 2 |
| G7 | L7 | **Wave 1–2** | `/wave-master-planner` Wave 1 或 2 |
| G8 | L7 | **Wave 3–4** | `/wave-master-planner` Wave 3 或 4 |
| G9 | L7 | **Wave 3–4** + Toolchain | Wave 3/4 + FP-G9-* |
| G10 | L8 | **Wave 5** | `/wave-master-planner` Wave 5 |

### 2.3 起手口令模板

```text
角色：Full-Phase Lane Planner · Group G<N>
State SSOT：04_Workflows/tickets/W-MASTER-full-phase-plan_state.md §G<N>
Playbook：docs/full-phase-master-planning-playbook.md
Wave Master（若 G7+）：W-MASTER-wave-plan §Wave <N> — Planned Tickets
任务：只规划/执行 G<N> 票；不修改其他 Group；不调整 Phase%
```

### 2.4 写回规则（避免 state 分叉）

| 变更类型 | 写到哪里 | 禁止 |
|----------|----------|------|
| G1–G10 索引 / 新 FP-* 规划行 | `W-MASTER-full-phase-plan` 对应 §G* 表 | 在 chat 口述代替写档 |
| P7+ 执行票 FRAME 全文 | `W-MASTER-wave-plan` §Wave N | 在 full-phase state 重复 FRAME 全文 |
| 子票施工 REPORT | `04_Workflows/tickets/<id>_state.md` | 跳过 C_REPORT |
| Progress 战报 | `00_Agent_Work_Progress.md` **末尾** | 覆盖历史段 |
| Phase% | `WAVE_PROGRESS_DASHBOARD.md` | lane chat 擅自修改 |

---

## 3. 如何避免重做已有能力

### 3.1 三步自检（Implementer 开工前）

1. **查 DNR** — `W-MASTER-full-phase-plan` §Do Not Re-Build Registry + 各 G* 节「已落地能力」。
2. **查 Dashboard** — 该 Phase 列「证据摘要」是否已列同名能力。
3. **查子票 STATE** — 是否已有 `validated` / `done_with_gaps` / `accepted*` C_REPORT。

**任一步命中「已落地」→ 不得重开大工程**；仅允许 doc cross-ref · 单点 bugfix · cleanup 票（如 W6-T10）。

### 3.2 典型禁止重做清单

| 能力 | 正确做法 | 错误做法 |
|------|----------|----------|
| P75 gate layer + policy + notify | 开 UI/SLO/alert 缺口票 | 重写 gate orchestrator |
| MP-SMOKE 七步 | 加 `--enable-dispatch` 或 doc | 新建第二套 smoke orchestrator |
| W3-TL Tabular 四件套 | 分轨索引 | 与 Phase 8.8 tool layer 合并 rename |
| bridge L-local 14/14 | 开 GA-remote 证据票 | 宣称 prod browser 已就绪 |
| engineering-contract / AGENTS | 索引引用 | 在 lane 内重写禁區表 |

### 3.3 「只消费、不维护」资产

以下由 **Wave 5（G4）** SSOT；其他 Group **只引用**：

- `docs/wave-master-ticket-template-v1.md`
- `.cursor/commands/ticket-*.md` · `wave-master-*.md`
- `_templates/wave_master_frame_block.template.yaml`

---

## 4. Ticket 栏位规范

### 4.1 标准 FRAME（来自 template + Full-Phase 扩展）

| 栏位 | 要求 |
|------|------|
| **Goal** | 一句话 · 可验证 · 不含「提升 Phase%」 |
| **Scope / NonScope** | MUST / 明确不做 |
| **AllowedPaths / BlockedPaths** | repo 相对路径 · 宪章 §7 类型 |
| **group_id** | `G1`…`G10` · **Full-Phase 必填** |
| **wave_id** | `W1`…`W5` 或 `null`（Foundation 票） |
| **phase_targets** | 只列 Dashboard Phase 名 · **不写 %** |
| **ticket_class** | `build` · `doc/spec` · `scribe/ops` · `blocked/planning` |
| **evidence_tier** | `L-local` · `CI-advisory` · `GA-remote` · `n/a` |
| **parallel_ok** | `true`/`false` · 对照 §Parallelization Plan |
| **human/infra/security_only_prereqs** | 无则 `[]` · 不可留空却隐含 human 已做 |
| **non_claims** | 复制 global + 票专属 |

### 4.2 Wave Master 扩展（W1–W5 执行子票）

与 `docs/wave-master-ticketing-playbook.md` §3.2 **相同**；另加 `group_id` 指向 G7–G10。

### 4.3 dependencies_detail 合格标准

```yaml
dependencies_detail:
  upstream_tickets:
    - P75-G3-intake-gate-policy-allowlist-denylist-v1_state.md
  downstream_groups:
    - G7
  blocks_if_missing:
    - item: "governance_dual 真批文"
      owner: "human · 尚書省"
      if_missing: "defer W2-P7 staging execute 票"
```

**不合格**：「依赖 P7」无票号 · 「等 staging 好」无负责方 · `blocks_if_missing` 为空却 AC 要求 staging 完成。

### 4.4 observability 合格标准

Reviewer **不跑代码**也能判票是否完成：

```yaml
observability:
  verify_commands:
    - "python -m unittest tests.test_xxx -v"
  evidence_artifacts:
    - "outbox/verification/demo_phase/multi_phase_smoke_run.json"
  trace_fields:
    - run_id
    - ga_run.url          # 若涉 CI/GA
  success_signals:
    - "C_REPORT conclusion=accepted*"
  failure_signals:
    - "AC 要求 GA 但 run_url=pending"
```

---

## 5. 什么叫可直接 Build

票满足 **全部** 下列条件 → 可交 Implementer（`/ticket-implementer` 或 `/wave-master-implementer`）：

| # | 条件 |
|---|------|
| 1 | FRAME 冻结 · `lifecycle_phase: B` 已完成 |
| 2 | `ticket_class` 为 **`build`** 或 **`doc/spec`**（非 `blocked/planning`） |
| 3 | `human_only` / `infra_only` / `security_only` prereqs **已满足** 或 AC **不依赖** 其交付物 |
| 4 | `AllowedPaths` 明确 · 不触宪章 §7 未授权禁區 |
| 5 | `observability.verify_commands` 非空 |
| 6 | `non_claims` 含诚实边界（尤其 advisory / sandbox / stub） |
| 7 | 未命中 DNR「禁止重做」 |

**可直接 build 示例（本盘）**

- `W1-P75-POLICY-DENY-MVP-v1` — doc + 最小 probe · 无 human block
- `W6-T10-cleanup-orchestrator-checkpoint-workarounds-v1` — 整合层已 landed
- `FP-G3-T1-evidence-tier-ssot-v1` — doc-only
- `FP-G6-T2-release-sanity-runbook-v1` — doc-only

**不可直接 build 示例**

- `W2-P7-staging-unblock-*` 中带 **execute staging POST** 的 AC（五顶 human 未齐）
- `FP-G6-T1-required-ci-unblock-frame-v1`（WC-PRE-07 批文前）
- `W4-P85-scenario2-ga-evidence-v1`（无 GA dispatch）
- `FP-G10-T1-s15-notify-gateway-frame-v1` runtime 部分（L7 未解阻）

---

## 6. 什么叫 Blocked but Still Worth Planning

票 **当下不能施工**，但仍应保留 FRAME / 依赖 / observability，以免 lane 遗忘或 over-claim。

| 特征 | 说明 |
|------|------|
| `ticket_class: blocked/planning` | STATE 可标 `blocked` · AC 只含 planning 交付物 |
| AC 交付物 | checklist · runbook · 解阻条件 · URL 占位符模板 |
| `non_claims` | 必须写「blocked ≠ done」 |
| Reviewer | 验 **规划质量** · 不验 runtime 完成 |

**示例**

- `FP-G1-T3-guard-schema-ratio-escalation-frame-v1` — blocked_on_approval · 仍 worth 写 FRAME
- `FP-G3-T3-langfuse-pg-alignment-deferred-index-v1` — deferred 索引
- `FP-G10-T1-s15-notify-gateway-frame-v1` — 等 G7 Round-2 解阻
- `W4-P9-run-url-backfill-v1` — human dispatch 模板 + pending 占位

**禁止**：blocked 票 C_REPORT 写 `accepted` 且无 `accepted_with_gaps` + 明确 deferred。

---

## 7. Human / Infra / Security 标注规则

与 `W-MASTER-full-phase-plan` §Human/Infra/Security Dependency Rules **相同**。

| 类型 | AC 允许 | AC 禁止 |
|------|---------|---------|
| **human_only** | 「交付 run URL 模板」·「回填 run_id= pending」 | 「staging 集成已完成」 |
| **infra_only** | 「记录 slot 需求清单」 | 「endpoint 已 flip」 |
| **security_only** | 「POST 审查 checklist doc」 | 「Security 已 sign-off」无记录 |

**Scribe/ops 票**（`ticket_class: scribe/ops`）通常 **human 触发** 后才进入 O 阶段。

---

## 8. B/C/D/O 与 Multi-Chat 映射

| 阶段 | Multi-Chat 角色 | Full-Phase 备注 |
|------|-----------------|-----------------|
| **B** | Orchestrator | 规划阶段可只做 B · 无 B_REPORT verification |
| **C** | Implementer | `FP-*` build 票必须 B_REPORT |
| **D** | Reviewer | 对照 AC + non_claims + evidence_tier |
| **O** | Scribe + Orchestrator | Progress append · 见 §Output file map |

**命令 SSOT**：`.cursor/commands/README.md`

---

## 9. Phase >80% 与 Priority（lane 必守）

- **06-27 Dashboard 基准**：**无 Phase ≥80%** · 全盘按 **关键缺口** 排序。
- 若未来某 Phase 上调 ≥80%：**仅补 AC 列出的最后一档缺口** · 禁止架构重做。
- **Priority**：blocking → cross-wave glue → 80% 边界缺口 → observability/doc → deferred。

### 9.1 Phase Completion Gauge（2026-06-27 · 敘事 · SSOT = Dashboard）

> **prev** = 06-23 SSOT · **current** = 06-27 · **本節只索引** · 不重算 gate。

- Phase 1: completion **90%** (prev 92%, delta −2%)
- Phase 2: completion **65%** (prev 82%, delta −17%)
- Phase 3: completion **82%** (prev 95%, delta −13%)
- Phase 3.5: completion **55%** (prev 83%, delta −28%)
- Phase 4: completion **75%** (prev 85%, delta −10%)
- Phase 5: completion **70%** (prev 87%, delta −17%)
- Phase 6: completion **72%** (prev 90%, delta −18%)
- Phase 7: completion **30%** (prev 68%, delta −38%)
- Phase 7.5: completion **45%** (prev 81%, delta −36%)
- Phase 8: completion **45%** (prev 80%, delta −35%)
- Phase 8.5: completion **10%** (prev 83%, delta −73%)
- Phase 8.6: completion **65%** (prev 85%, delta −20%)
- Phase 8.7: completion **60%** (prev 85%, delta −25%)
- Phase 8.8: completion **58%** (prev 82%, delta −24%)
- Phase 8.9: completion **40%** (prev 81%, delta −41%)
- Phase 9: completion **20%** (prev 60%, delta −40%)
- Phase 10: completion **35%** (prev 48%, delta −13%)
- Phase 10.5: completion **30%** (prev 32%, delta −2%)

### 9.2 Tabular 子域 vs 全局 Phase%（C2-P2 · 2026-06-27）

**Phase 2/3/6/8/10 (Tabular low-risk cleaning subline): functionally complete for scope C2-P2.**

| 维度 | 说明 |
|------|------|
| **全局 Phase%** | 仍依 `docs/WAVE_PROGRESS_DASHBOARD.md` §Phase 完成度表「当前（06-27）」 |
| **Tabular 子域** | C2-P2 范围内已完工：**Tabular low-risk cleaning subline 在 Phase 2/3/6/8/10 已功能完備** |
| **非宣稱** | **≠** 全局 P2/P3/P6/P8/P10 上调 · **≠** prod gate · **≠** mandatory CI |

**Tabular C2-P2 子域能力（按 Phase）**

- **P2**：3 cleaning profiles（`phase_demo_v1` · `sampleco_order_profile` · `generic_low_risk_profile`）· case registry
- **P3**：automation run log · `tabular_ops_summary.py` · E2E verification report
- **P6**：`run_demo_phase_regression_smoke.py` · mainline E2E checklist · 三案 E2E（demo_phase · sampleco · generic-low-risk）
- **P8**：HITL CP-A/B resume · delivery approve · bundle · `delivery_ready`
- **P10**：control plane · unified driver · retry/DLQ（完整 state/run log/DLQ 档/测试）· warning guard 策略表

详见 `docs/TABULAR_MVP_SSOT.md` §10.1 · `docs/tabular-mainline-e2e-verification-v1.md` · `docs/WAVE_PROGRESS_DASHBOARD.md` §Tabular 主線子域完工。

---

## 10. Reviewer 如何验收整盘

### 10.1 触发条件

- 各 Group lane 完成己组 **FP-* 子票 FRAME** 或 **Wave Master Wave N 区块**更新
- 或 Full-Phase Master Orchestrator 宣告「Full-Phase Plan Review 截止」

### 10.2 Reviewer 只读范围

- `W-MASTER-full-phase-plan_state.md` 全文（G1–G10）
- `W-MASTER-wave-plan_state.md` Wave 1–5（G7–G10 交叉）
- 抽样 ≥3 张 `FP-*` 或 `W*-P*` 子票 FRAME
- `docs/WAVE_PROGRESS_DASHBOARD.md` 相关 Phase 列
- `docs/p8_p89_evidence_index_v1.md` · `wave-next-code-inspector-v1.md`（若涉 G7–G9）

### 10.3 Full-Phase Master Plan Review Checklist

| # | 检查项 | Blocking |
|---|--------|----------|
| 1 | G1–G10 每组 ≥3 tickets 或 explicit「仅 blocked/解阻」说明 | Y |
| 2 | 所有票含 `group_id` · `FP-*` 与 Wave 票无 hard conflict | Y |
| 3 | DNR 未违反 · 无重做已 validated 能力 | Y |
| 4 | `estimated_cycles` ≤2 或已拆票 | Y |
| 5 | human/infra/security prereqs 完整 · 无伪完成 AC | Y |
| 6 | observability 抽样合格（§4.4） | Y |
| 7 | **无 Phase% 上调** · **无 required CI 升格**（无批文） | Y |
| 8 | Parallelization plan 与共享 mutation surface 一致 | N |
| 9 | Output file map 与 actual 写档路径一致 | N |
| 10 | 与 `full-phase-lane-map-v1.md` 8-Lane 叙事一致 | N |

### 10.4 Verdict 与写入

Reviewer 写 `W-MASTER-full-phase-plan_state.md` → **C_REPORT**：

```markdown
## Full-Phase Master Plan Review Verdict

- **reviewer_date**: YYYY-MM-DD
- **verdict**: PLAN_READY | PLAN_WITH_GAPS | PLAN_REJECT
- **groups_reviewed**: G1–G10
- **summary**: （2–4 句）
- **blocking_issues**: 无 | （列项）
- **over_claims_found**: 无 | （列项）
- **per_group_notes**:
  - G1: …
  - …
- **next_action**: 开 Implementer lane chats | 退回 Planner 修订
```

Orchestrator 更新 STATE：`planning_status` · `reviewer_verdict` · `next_action`。

### 10.5 PLAN_REJECT 典型原因

- blocked 票 AC 要求 runtime 完成
- 双份维护 Wave Master Wave 1–5 于 full-phase state
- 缺少 `group_id` 或 evidence_tier
- 把 local smoke 标成 prod-ready
- 修改 Dashboard Phase%

---

## 11. Progress / Dashboard 协议（Scribe 重 O）

| 规则 | 说明 |
|------|------|
| Progress | **仅末尾 append** · 含 `group_id` · `evidence_tier` · blocked/next |
| Dashboard | **lane 不得改 Phase%** · 叙事更新须 Governance 授权 |
| master_status | Governance 独占 |
| GA/CI | `run_url` + `run_id` 回填或 `pending` |
| Ops cycle | `_ops_cycle.py validate-report` → `append-report`（可选） |

---

## 12. Output File Map（lane chat 应写哪些档）

| 产出 | 路径 | 角色 |
|------|------|------|
| Full-Phase state | `04_Workflows/tickets/W-MASTER-full-phase-plan_state.md` | Master Orch · append G* 表 |
| 本 playbook | `docs/full-phase-master-planning-playbook.md` | Master Orch · Reviewer 审修订 |
| 8-Lane map | `docs/full-phase-lane-map-v1.md` | G4 · 交叉引用 |
| Wave Master | `04_Workflows/tickets/W-MASTER-wave-plan_state.md` | Wave Planner · G7–G10 |
| 子票 | `04_Workflows/tickets/<id>_state.md` | O 开票 · B/C/D/O 填 REPORT |
| Progress | `04_Workflows/00_Agent_Work_Progress.md` | Scribe · 末尾 |
| P7.5 / evidence docs | `docs/p75-*` · `docs/p8_p89_evidence_index_v1.md` | G3/G7/G9 |
| Matrix / inspector | `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` · `review_checklists/wave-next-code-inspector-v1.md` | G6/G7 · Reviewer |

完整表见 `W-MASTER-full-phase-plan` §Output file map。

---

## 13. 与 Wave Master Playbook 的分工

| 维度 | Full-Phase（本档） | Wave Master |
|------|-------------------|-------------|
| 覆盖 | Phase 1–10.5 · G1–G10 | P7+ Wave 1–5 planned tickets |
| Chat 数 | 10 Group · 可映射 8 Lane | Chat 1–5 Wave Planner |
| 票前缀 | `FP-G*-*` + 引用 `W*-P*` | `W1–W5-*` |
| Review | Full-Phase Master Review | Master Plan Review（`WAVE_MASTER_PLAN_REVIEW_2026-06-26.md`） |

**规则**：G7–G10 执行 planning **以 Wave Master 正文为准**；本盘只索引 + 补 Foundation（G1–G6）与跨 Phase 票。

---

## 14. 相关索引

| 类型 | 路径 |
|------|------|
| Full-Phase state | `04_Workflows/tickets/W-MASTER-full-phase-plan_state.md` |
| 8-Lane map | `docs/full-phase-lane-map-v1.md` |
| Wave Master state | `04_Workflows/tickets/W-MASTER-wave-plan_state.md` |
| Wave Master playbook | `docs/wave-master-ticketing-playbook.md` |
| Master Plan Review | `docs/WAVE_MASTER_PLAN_REVIEW_2026-06-26.md` |
| Dashboard | `docs/WAVE_PROGRESS_DASHBOARD.md` |
| Commands | `.cursor/commands/README.md` |
| Multi-Chat skill | `.cursor/skills/multi-chat-ticket-workflow/SKILL.md` |

### 14.1 Phase 收口 · Human-only 配套（Groundwork Finisher B · 2026-06-26）

> **本 playbook 不做 closure 宣称**；下列三档为 **人类必须完成** 的收尾 checklist / 批文 playbook · AI 仅 doc/辅助。

| 文档 | 用途 |
|------|------|
| `docs/phase-closure-governance-playbook-v1.md` | Phase 收口裁決权 · 六维 evidence · AI/人类责任矩阵 |
| `docs/ga-remote-closure-checklist-v1.md` | P7/P8.5/P9/P8.9 GA-remote · run_url 回填 · ops RACI |
| `docs/required-ci-and-wc-pre-checklist-v1.md` | WC-PRE-06/07 批文 · required CI 升格 · wiring checklist |

**现状（doc 索引）**：GA-remote **全线 pending/blocked** · WC-PRE-06/07 **`approval_status.*` pending** · **不得**由 lane chat 或 AI 宣告 Phase 闭环。

**State 标记**：`W-MASTER-full-phase-plan_state.md` → `groundwork_governance_support: ready`（**只**表示三档 doc 就绪 · **不**改变 Phase% · **不**等于 GA/WC-PRE/required CI 已执行）。

---

## 15. 人类 Phase 收口 — 先查三档（Mandatory Lookup）

> **触发**：尚書省 / Governance / Ops 准备宣告 **某一 Phase / Wave / 全线**「收口」或上调 Phase% 前。  
> **本 playbook 不做 closure 宣称**；下列为 **人类-only** 查档顺序 · AI 仅可 doc/格式化 Progress。

### 15.1 查档顺序（固定 · 不可跳步）

```
1. docs/phase-closure-governance-playbook-v1.md
   → 谁有权宣告收口？六维 evidence 是否齐？AI 禁止项？
2. docs/ga-remote-closure-checklist-v1.md
   → 涉 GA-remote 的 Phase 是否有 run_url/run_id？Ops RACI 是否完成？
3. docs/required-ci-and-wc-pre-checklist-v1.md
   → WC-PRE-06/07 是否 human approved？required CI 升格是否独立授权？
4. docs/WAVE_PROGRESS_DASHBOARD.md（只读 · Governance 独占写入 Phase%）
5. 00_Agent_Work_Progress.md 末尾 append 留痕（Scribe · O 阶段）
```

### 15.2 三档文档速查

| 顺序 | 文档 | 何时必读 | 核心问题 |
|------|------|----------|----------|
| **1** | `docs/phase-closure-governance-playbook-v1.md` | **任何** Phase 收口裁決前 | 裁決权在谁？六维 evidence 缺哪维？ |
| **2** | `docs/ga-remote-closure-checklist-v1.md` | Phase 涉及 P7 / P8.5 / P9 / P8.9 远端证据 | 有无 GA `run_url`？advisory landing 是否误当 GA pass？ |
| **3** | `docs/required-ci-and-wc-pre-checklist-v1.md` | 拟升格 merge gate / mandatory CI / WC-PRE L2 | WC-PRE 批文是否 pending？eval-gate 绿是否误当 toolchain required？ |

### 15.3 常见误判（收口前必对照）

| 误判 | 正确依据 |
|------|----------|
| L-local N/N OK = Phase 可收口 | §15.1 步骤 1 · 六维 evidence 表 |
| advisory CI on `main` = required CI 就绪 | §15.1 步骤 3 · 三分表 |
| `groundwork_governance_support: ready` = Phase% 可上调 | **否** — 仅 doc 就绪 · 见 `W-MASTER-full-phase-plan` META |
| checklist doc 存在 = GA 已完成 | **否** — GA-remote **全线 pending** · 步骤 2 须 human dispatch |

### 15.4 AI / Lane Chat 边界

- **允许**：索引三档 · draft Progress · 回填 ticket STATE 中 `run_url=pending` 占位
- **禁止**：dispatch GA · 代签 WC-PRE · 改 workflow yml / branch protection · 写 Dashboard Phase% · 写 `closure_claimed: true`

**审计留痕**：Groundwork Governance Close-Out → `00_Agent_Work_Progress.md` 2026-06-27 段。

---

*full-phase-master-planning-playbook · v1 · 2026-06-27 · Full-Phase Master Orchestrator · doc-only · Phase% frozen*
