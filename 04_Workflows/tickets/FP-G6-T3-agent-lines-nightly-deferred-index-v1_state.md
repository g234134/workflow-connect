# TICKET STATE · FP-G6-T3-agent-lines-nightly-deferred-index-v1 · agent-lines nightly deferred 索引

> Full-Phase G6 · P6 · **doc/spec · planning/deferred** · 无 human 前置施工（索引本身）  
> 对齐：`W-MASTER-full-phase-plan_state.md#G6` · `docs/agent-lines-ci-suite-v1.md` · INDEX §1.14  
> **注意**：票目标是 **deferred 索引**；**不**解阻 D-01…D-07（required／7d／prod default 等仍 human／批文）

---

## FRAME
<!-- Orchestrator 填：2026-07-10 冻结 · arrange · frame_ready -->

- Goal: 产出 **Agent Lines `run-all-allowed` + nightly CI deferred 索引**单页：诚实区分 Landed（optional）与 Deferred（批文／另票）；**本票不**升格 required CI、不改 workflows、不上调 Phase%。
- Scope:
  - MUST：新建 `docs/phase6-agent-lines-nightly-deferred-index-v1.md`，至少含：
    - `non_claims` 置顶（≠ required／≠ INT Tier-A／≠ Phase%／≠ P6 closure／≠ Round-2／prod default）
    - Landed 表（suite · run-all-allowed · optional PR · schedule nightly · dispatch · unittest）
    - Deferred 索引表（required 升格 · nightly→uplift · prod default · extended mandatory · NT 扩面 · PR block · Tier-A）
    - 与 T2 runbook／T4 spotcheck／`agent-lines-ci-suite-v1.md` 分界
    - 链 INDEX §1.14 或 `agent-lines-ci-suite-v1.md`
  - MUST：本票 B_REPORT + 可重跑 `rg` 验证
  - MAY：`WORKFLOW_INDEX.md` §1.14 一句交叉引用本 doc
  - MAY：`docs/index.md` 导航一行
- NonScope:
  - 改 `.github/workflows/**`（含 agent-lines-ci.yml）· required CI · branch protection（WC-PRE）
  - 执行／回填 P6 nightly 7d 监控表 · Phase% 上调
  - 解阻 FP-G6-T1／FP-G6-required-ci · 改 prod default run mode
  - 改 `core/**`／`scripts/**`／`tests/**` 行为
  - human-blocked 七线 · FP-G2-T5 · DarkOps · 金钥
- AllowedPaths:
  - `docs/phase6-agent-lines-nightly-deferred-index-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（仅 §1.14 一句 MAY）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G6-T3-agent-lines-nightly-deferred-index-v1_state.md`（B/C/D_REPORT）
- BlockedPaths:
  - `core/**` · `scripts/**` · `tests/**`（除唯读引用）
  - `.github/workflows/**` · Dashboard Phase% 数字格
  - 治理母本 · 暗部 · 宪法 §7 类型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票报告区）
- Dependencies:
  - 无硬阻塞施工；必读：`docs/agent-lines-ci-suite-v1.md` · INDEX §1.14 · full-phase G6 表 T3 行
  - 可选：`phase6-int-regression-gate-contract-v1.md`（TS-AGENT-LINES-CI optional）· T2／T4 docs
- AcceptanceCriteria:
  - AC-1：doc 含 Landed 表 + Deferred 索引表（至少各 3 行实质项）
  - AC-2：doc 链 `agent-lines-ci-suite-v1.md` 或 INDEX §1.14；含 `run-all-allowed` 与 nightly／schedule 诚实边界
  - AC-3：doc 含 `non_claims`（≠ required／≠ INT Tier-A／≠ Phase%／≠ P6 closure／≠ Round-2 GO）
  - AC-4：`rg "deferred|run-all-allowed|nightly|non_claims|agent-lines|required" docs/phase6-agent-lines-nightly-deferred-index-v1.md` 命中
  - AC-5：未改 `core/**` · `.github/workflows/**` · Phase%；未宣称 required／Tier-A 已挂
  - AC-6（MAY）：INDEX §1.14 或 `docs/index.md` 一句命中本 doc 路径

### Wave Master 扩展

- wave_id: null
- group_id: G6
- lifecycle_phase: B
- phase_targets: [P6]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W10-T1-integrate-agent-lines-into-ci-v1, FP-G6-T2-release-sanity-runbook-v1, FP-G6-T4-inspector-overclaim-spotcheck-v1]
  - downstream_waves: []
  - blocks_if_missing: []
- risks:
  - id: RSK-G6-T3-01
    description: 索引被误读为 nightly required 已挂或 deferred 项已解阻
    likelihood: M
    impact: H
    mitigation: non_claims 置顶 · Deferred 表明示 blocker · 分界节
    residual: accept
- observability:
  - verify_commands:
    - "rg \"deferred|run-all-allowed|nightly|non_claims|agent-lines|required\" docs/phase6-agent-lines-nightly-deferred-index-v1.md"
  - evidence_artifacts:
    - docs/phase6-agent-lines-nightly-deferred-index-v1.md
  - trace_fields: []
  - success_signals: [deferred 索引存在 · 无 workflows／Phase% 变更]
  - failure_signals: [改 workflows · 宣称 required CI／解阻 T1]
- non_claims:
  - deferred 索引 ≠ required CI／INT Tier-A 已挂
  - schedule nightly 存在 ≠ P6 closure／7d uplift／Round-2 GO
  - 本票 doc ≠ 授权改 workflows 或 prod default run mode
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- implementation_status: doc_delivered · reviewer_accepted · scribe_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无 · 票已关；QUEUE 仅剩 human-blocked／批文线；勿 execute T1／required-CI／W4／WC-PRE／P6-nightly／P7 Round-2
- last_updated: 2026-07-10 · D（scribe_closed · overall done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  arrange+execute 同轮（尚书省「把安排好的工作全部做完」）；G6 可 AI 施工票 T2/T4/T3 收齐。
  未碰 human-blocked／T1／required-CI／workflows／Phase%。
- reviewer_notes: >-
  AC-1..AC-6 PASS；conclusion=accepted；交棒 scribe。

---

## B_REPORT
<!-- Implementer 填 -->

- changed_files:
  - docs/phase6-agent-lines-nightly-deferred-index-v1.md（新建）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.14 MAY 一句）
  - docs/index.md（导航一行 + changelog）
  - 04_Workflows/tickets/FP-G6-T3-agent-lines-nightly-deferred-index-v1_state.md（B_REPORT）
  - 04_Workflows/command_queue/QUEUE.yaml · SESSION.md（编排写回）
- artifacts:
  - docs/phase6-agent-lines-nightly-deferred-index-v1.md — Landed + Deferred 索引；链 suite SSOT／INDEX §1.14
- verification:
  - cmd: `rg "deferred|run-all-allowed|nightly|non_claims|agent-lines|required" docs/phase6-agent-lines-nightly-deferred-index-v1.md`
  - result: ok · 命中 non_claims／Landed／Deferred／run-all-allowed／nightly／required 否定
  - cmd: `rg "phase6-agent-lines-nightly-deferred-index" 04_Workflows/WORKFLOW_INDEX.md docs/index.md`
  - result: ok · MAY 交叉引用命中
- behavior_notes: doc-only；不改 workflows／scripts／tests；不宣称解阻 deferred 项
- deferred_items: D-01…D-07 仍须批文／另票／human（见正文 Deferred 表）

---

## C_REPORT
<!-- Reviewer 填 -->

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
  AC-1 PASS：Landed（L-01…L-07）+ Deferred（D-01…D-07）齐全。
  AC-2 PASS：链 agent-lines-ci-suite-v1.md／INDEX §1.14；run-all-allowed + nightly 诚实边界。
  AC-3 PASS：non_claims 置顶。
  AC-4 PASS：rg 命中。
  AC-5 PASS：未改 core／workflows／Phase%；未宣称 required／Tier-A。
  AC-6 PASS：INDEX §1.14 + docs/index 交叉引用。
- risk_level: low
- suggestions: Reviewer 遇「nightly=required」句式可链本档 §3 + T4 spotcheck

---

## D_REPORT
<!-- Scribe 填 -->

- docs_updates:
  - docs/phase6-agent-lines-nightly-deferred-index-v1.md（本票正文）
  - docs/index.md 导航 + changelog
  - WORKFLOW_INDEX §1.14 一句
- progress_entry: |
  2026-07-10 · FP-G6-T3 done · agent-lines nightly deferred 索引 · Reviewer accepted · G6 AI 可施工票耗尽 · 仅剩 human-blocked
- followup_suggestions:
  - 勿 execute FP-G6-T1／FP-G6-required-ci／W4／WC-PRE／P6-nightly／P7 Round-2／FP-G2-T5
  - human 解阻后再排 required-CI／7d uplift
