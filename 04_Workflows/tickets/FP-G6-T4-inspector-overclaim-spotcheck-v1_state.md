# TICKET STATE · FP-G6-T4-inspector-overclaim-spotcheck-v1 · inspector over-claim 抽样对照清单

> Full-Phase G6 · P6 · **doc/spec** · 无 human 前置  
> 对齐：`W-MASTER-full-phase-plan_state.md#G6` · inspector SSOT `review_checklists/wave-next-code-inspector-v1.md`

---

## FRAME
<!-- Orchestrator 填：2026-07-10 冻结 · arrange · frame_ready -->

- Goal: 产出 **wave-next inspector 抽样对照清单**（Reviewer 用）：在既有 `wave-next-code-inspector-v1.md` 之上，提供 over-claim 快速抽样表与迷你 verdict；**本票不**升格 required CI、不改 workflows、不上调 Phase%。
- Scope:
  - MUST：新建 `docs/phase6-inspector-overclaim-spotcheck-v1.md`，至少含：
    - 与三份 checklist 分界（wave-next / master-plan / cross-rollup）
    - 抽样对照表（证据位阶 + over-claim 硬拦截 + human-blocked 诚实）
    - 常见 over-claim 句式 → 诚实改写
    - 迷你 Verdict 模板（映射 inspector OK/Partial/Blocked/Reject-over-claim）
    - `non_claims`：抽样清单 ≠ 替代 inspector 全文 · ≠ required CI · ≠ INT Tier-A · ≠ P6 closure · ≠ Round-2 GO
  - MUST：本票 B_REPORT + 可重跑 `rg` 验证
  - MAY：`WORKFLOW_INDEX.md` Reviewer 收口段一句交叉引用本 doc
  - MAY：`docs/index.md` 导航一行
- NonScope:
  - 改写 / 取代 `wave-next-code-inspector-v1.md` 正文权威
  - 改 `core/**`／`scripts/**`／`tests/**` 行为
  - `.github/workflows/**` · required CI · branch protection（WC-PRE）
  - INT Tier-A／nightly 7d 执行 · Phase% 上调
  - human-blocked 七线 · FP-G2-T5 · DarkOps · 金钥
- AllowedPaths:
  - `docs/phase6-inspector-overclaim-spotcheck-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（仅 Reviewer 收口相关一句 MAY）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G6-T4-inspector-overclaim-spotcheck-v1_state.md`（B/C/D_REPORT）
- BlockedPaths:
  - `core/**` · `scripts/**` · `tests/**`（除唯读引用）
  - `.github/workflows/**` · Dashboard Phase% 数字格
  - 治理母本 · 暗部 · 宪法 §7 类型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票报告区）
  - 覆盖改写 `wave-next-code-inspector-v1.md` 为「被本档取代」
- Dependencies:
  - 无硬阻塞；必读：`04_Workflows/review_checklists/wave-next-code-inspector-v1.md`
  - 可选：`wave-cross-rollup-inspector-v1.md` · `docs/phase6-release-sanity-runbook-v1.md`（T2 DONE）
- AcceptanceCriteria:
  - AC-1：doc 含与 inspector SSOT 的分界说明 + 抽样对照表（证据／over-claim／blocked）
  - AC-2：doc 链 `wave-next-code-inspector-v1.md` 路径
  - AC-3：doc 含迷你 Verdict 模板 + `non_claims`（≠ 替代 inspector／≠ required CI／≠ INT Tier-A／≠ Phase%／≠ Round-2 GO）
  - AC-4：`rg "over.?claim|spotcheck|wave-next-code-inspector|non_claims|Reject-over-claim" docs/phase6-inspector-overclaim-spotcheck-v1.md` 命中
  - AC-5：未改 `core/**` · `.github/workflows/**` · Phase% · 未宣称取代 inspector SSOT
  - AC-6（MAY）：INDEX 或 `docs/index.md` 一句命中本 doc 路径

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
  - upstream_tickets: [FP-G6-T2-release-sanity-runbook-v1, W5-T4-wave-plan-reviewer-checklist-v1]
  - downstream_waves: [FP-G6-T3-agent-lines-nightly-deferred-index-v1]
  - blocks_if_missing: []
- risks:
  - id: RSK-G6-T4-01
    description: 抽样清单被误读为取代 inspector 全文或 required CI 已挂
    likelihood: M
    impact: H
    mitigation: non_claims 置顶 · 分界表明示 SSOT
    residual: accept
- observability:
  - verify_commands:
    - "rg \"over.?claim|spotcheck|wave-next-code-inspector|non_claims\" docs/phase6-inspector-overclaim-spotcheck-v1.md"
  - evidence_artifacts:
    - docs/phase6-inspector-overclaim-spotcheck-v1.md
  - trace_fields: []
  - success_signals: [抽样清单存在 · 链 inspector · 无 workflows／Phase% 变更]
  - failure_signals: [宣称取代 inspector · 改 workflows]
- non_claims:
  - 抽样清单 ≠ 替代 wave-next-code-inspector 全文
  - 抽样绿 ≠ required CI／INT Tier-A／P6 closure／Round-2 GO
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- implementation_status: doc_delivered · reviewer_accepted · scribe_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无 · 票已关；下一刀建议 arrange FP-G6-T3（deferred nightly 索引 · planning）；勿把 T1／required-CI／W4 human-blocked 当可 execute
- last_updated: 2026-07-10 · D（scribe_closed · overall done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  arrange+execute 同轮（尚书省「安排工作完成」）；inspector SSOT 已存在；本票补抽样加速层。
  未碰 human-blocked／T5／DarkOps／workflows／Phase%。
- reviewer_notes: >-
  AC-1..AC-6 PASS；conclusion=accepted；交棒 scribe。

---

## B_REPORT
<!-- Implementer 填 -->

- changed_files:
  - docs/phase6-inspector-overclaim-spotcheck-v1.md（新建）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.55 Reviewer 收口 MAY 一句）
  - docs/index.md（架构与治理表 MAY 导航一行 + changelog）
  - 04_Workflows/tickets/FP-G6-T4-inspector-overclaim-spotcheck-v1_state.md（B_REPORT）
  - 04_Workflows/command_queue/QUEUE.yaml · SESSION.md（编排写回）
- artifacts:
  - docs/phase6-inspector-overclaim-spotcheck-v1.md — 抽样对照 + over-claim 拦截 + 迷你 verdict；链 inspector SSOT
- verification:
  - cmd: `rg "over.?claim|spotcheck|wave-next-code-inspector|non_claims|Reject-over-claim" docs/phase6-inspector-overclaim-spotcheck-v1.md`
  - result: ok · 命中 non_claims／分界／抽样表／Reject-over-claim／inspector 路径
  - cmd: `rg "phase6-inspector-overclaim-spotcheck" 04_Workflows/WORKFLOW_INDEX.md docs/index.md`
  - result: ok · MAY 交叉引用命中
- behavior_notes: doc-only；不改 inspector 正文；不改 runner／CI
- deferred_items: FP-G6-T3 deferred nightly 索引 · FP-G6-T1／required-CI（批文）

---

## C_REPORT
<!-- Reviewer 填 -->

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
  AC-1 PASS：分界 + 抽样表（S/O/blocked）齐全。
  AC-2 PASS：链 wave-next-code-inspector-v1.md。
  AC-3 PASS：迷你 Verdict + non_claims 置顶。
  AC-4 PASS：rg 命中。
  AC-5 PASS：未改 core／workflows／Phase%；未宣称取代 SSOT。
  AC-6 PASS：INDEX + docs/index 交叉引用。
- risk_level: low
- suggestions: 后续 Reviewer chat 可把本档 §5 模板默认贴进 C_REPORT 首段

---

## D_REPORT
<!-- Scribe 填 -->

- docs_updates:
  - docs/phase6-inspector-overclaim-spotcheck-v1.md（本票正文）
  - docs/index.md 导航 + changelog
  - WORKFLOW_INDEX §1.55 一句
- progress_entry: |
  2026-07-10 · FP-G6-T4 done · inspector over-claim spotcheck 抽样清单 · Reviewer accepted · 下一 arrange FP-G6-T3
- followup_suggestions:
  - arrange `FP-G6-T3-agent-lines-nightly-deferred-index-v1`（planning／deferred 索引）
  - 勿 execute FP-G6-T1／FP-G6-required-ci／W4 human-blocked
