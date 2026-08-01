# TICKET STATE · FP-G6-T2-release-sanity-runbook-v1 · release-sanity runbook 單頁 SSOT

> Full-Phase G6 · P6 · **doc/spec** · 無 human 前置  
> 對齊：`W-MASTER-full-phase-plan_state.md#G6` · 契約層 `docs/smoke-and-regression-contract-v1.md`  
> INDEX runners：`04_Workflows/WORKFLOW_INDEX.md` §1.5（MP/MC/CI-SMOKE 段）

---

## FRAME
<!-- Orchestrator 填：2026-07-10 凍結 · arrange · frame_ready -->

- Goal: 產出 **MP-SMOKE + MC-SMOKE + CI-SMOKE** 發版前 **release-sanity runbook 單頁 SSOT**（建議命令順序、pass 判準、與既有契約／INDEX 交叉引用）；**本票不**升格 required CI、不改 workflows、不上調 Phase%。
- Scope:
  - MUST：新建 `docs/phase6-release-sanity-runbook-v1.md`，至少含：
    - 發版前建議順序（MP → MC → CI-SMOKE）與典型命令（對齊既有 scripts）
    - pass／fail 判準摘要（引用 CI-SMOKE 規則與 contract non_claims）
    - 與 `docs/smoke-and-regression-contract-v1.md`、INDEX §1.5、Dashboard §Multi-phase smoke 的位階說明（runbook = 操作單頁；contract = 契約 SSOT）
    - `non_claims`：L-local release sanity ≠ GitHub required · ≠ INT Tier-A · ≠ P6 closure · ≠ P7 Round-2 GO
  - MUST：本票 B_REPORT + 可重跑 `rg` 驗證
  - MAY：`WORKFLOW_INDEX.md` §1.5 一句交叉引用本 doc
  - MAY：`docs/index.md` 導航一行
- NonScope:
  - 改 `core/**`／`scripts/**`／`tests/**` 行為
  - `.github/workflows/**` · required CI · branch protection（WC-PRE）
  - INT Tier-A 重跑／nightly 7d 執行 · Phase% 上調
  - human-blocked 七線 · FP-G2-T5 · DarkOps · 金鑰
- AllowedPaths:
  - `docs/phase6-release-sanity-runbook-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（僅 §1.5 一句 MAY）
  - `docs/index.md`（MAY 一行）
  - `04_Workflows/tickets/FP-G6-T2-release-sanity-runbook-v1_state.md`（B_REPORT）
- BlockedPaths:
  - `core/**` · `scripts/**` · `tests/**`（除唯讀引用）
  - `.github/workflows/**` · Dashboard Phase% 數字格
  - 治理母本 · 暗部 · 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票 B_REPORT）
- Dependencies:
  - 無硬阻塞；必讀：`docs/smoke-and-regression-contract-v1.md` · INDEX §1.5 MP/MC/CI 段
  - 可選：`docs/P8_P89_ADVISORY_CI_INDEX.md`（local-only 標籤）· Dashboard §Multi-phase smoke
- AcceptanceCriteria:
  - AC-1：doc 含 MP／MC／CI-SMOKE 發版前建議順序 + 至少各一條典型命令
  - AC-2：doc 鏈 `smoke-and-regression-contract-v1.md` 與 INDEX §1.5（或等價 runner 索引）
  - AC-3：doc 含 pass 判準摘要 + `non_claims`（≠ required CI／≠ INT Tier-A／≠ Phase%／≠ Round-2 GO）
  - AC-4：`rg "MP-SMOKE|MC-SMOKE|CI-SMOKE|non_claims|release.sanity|smoke-and-regression" docs/phase6-release-sanity-runbook-v1.md` 命中
  - AC-5：未改 `core/**` · `.github/workflows/**` · Phase%
  - AC-6（MAY）：INDEX §1.5 一句命中本 doc 路徑

### Wave Master 擴展

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
  - upstream_tickets: [W2-P7-advisory-ci-ssot-index-v1, CI-SMOKE-multi-phase-smoke-and-metrics-hook-v1, MC-SMOKE-multi-case-smoke-runner-v1, MP-SMOKE-std-case-multi-phase-smoke-v1]
  - downstream_waves: [FP-G6-T4-inspector-overclaim-spotcheck-v1]
  - blocks_if_missing: []
- risks:
  - id: RSK-G6-T2-01
    description: runbook 被誤讀為 required CI／INT Tier-A 已掛
    likelihood: M
    impact: H
    mitigation: non_claims 置頂 · 僅 doc AllowedPaths
    residual: accept
- observability:
  - verify_commands:
    - "rg \"MP-SMOKE|MC-SMOKE|CI-SMOKE|non_claims\" docs/phase6-release-sanity-runbook-v1.md"
  - evidence_artifacts:
    - docs/phase6-release-sanity-runbook-v1.md
  - trace_fields: []
  - success_signals: [單頁 runbook 存在 · 無 workflows／Phase% 變更]
  - failure_signals: [改 workflows · 宣稱 required CI]
- non_claims:
  - runbook ≠ GitHub required workflow 已掛
  - runbook 綠路徑指引 ≠ INT Tier-A／P6 closure／P7 Round-2 GO
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- implementation_status: doc_delivered · reviewer_accepted · scribe_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无 · 票已关；下一刀建议 arrange FP-G6-T4（勿把 human-blocked W4／T1／required-CI 当可 execute）
- last_updated: 2026-07-10 · D（scribe_closed · overall done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  arrange-only；契約層已有 smoke-and-regression-contract-v1；本票補「發版前操作單頁」。
  未寫 doc 正文；未碰 human-blocked／T5／DarkOps／workflows／Phase%。
- reviewer_notes: >-
  AC-1..AC-6 PASS；conclusion=accepted；交棒 scribe。
  工作樹另有無關 core/**／.github/workflows/** 髒檔，不屬本票 B_REPORT，勿併入本票封存敘事。

---

## B_REPORT
<!-- Implementer 填 -->

- changed_files:
  - docs/phase6-release-sanity-runbook-v1.md（新建）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.5 MP-SMOKE 段 MAY 一句交叉引用）
  - docs/index.md（架構與治理表 MAY 導航一行）
  - 04_Workflows/tickets/FP-G6-T2-release-sanity-runbook-v1_state.md（B_REPORT + STATE 交棒）
- artifacts:
  - docs/phase6-release-sanity-runbook-v1.md — MP→MC→CI-SMOKE 操作單頁；non_claims 置頂；鏈 contract + INDEX §1.5
- verification:
  - cmd: `rg "MP-SMOKE|MC-SMOKE|CI-SMOKE|non_claims|smoke-and-regression" docs/phase6-release-sanity-runbook-v1.md`
  - result: 命中 non_claims 標題、MP/MC/CI-SMOKE 各節、smoke-and-regression-contract 鏈接（exit 0）
  - cmd: `rg "phase6-release-sanity-runbook-v1" 04_Workflows/WORKFLOW_INDEX.md docs/index.md`
  - result: INDEX §1.5 與 docs/index.md 均命中（AC-6 MAY）
  - AC 自檢: AC-1..AC-6 PASS（見 behavior_notes）；未改 core/** · scripts/** · tests/** · .github/workflows/** · Phase%
- behavior_notes:
  - 發版建議順序固定為 FRAME 要求之 MP → MC → CI-SMOKE；文內註明契約 §6「Fleet 優先」為互補敘事，不改命令路徑。
  - 典型命令均對齊 INDEX §1.5／contract（demo_phase · sampleco · run_ci_smoke_check_v1.py --format text）。
  - pass/fail 摘要引用 CI-SMOKE 三規則與 MC release 排除 phi_demo。
  - 位階：runbook=操作單頁 · contract=契約 SSOT · INDEX §1.5=runner 索引。
- deferred_items:
  - QUEUE.yaml／SESSION.md 狀態行（不在 FRAME AllowedPaths；請 Orchestrator／Scribe 可選 append）
  - 未執行實際 MP/MC/CI smoke runner（本票 doc-only；AC 僅要求 rg）
  - INT Tier-A／required CI／Phase%／P6 closure／Round-2 — 明確 non_claims，另票

---

## C_REPORT
<!-- Reviewer 填 · 2026-07-10 -->

- conclusion: accepted
- blocking_issues: []
- checks_summary:
  - AC-1: PASS — §2 固定 MP→MC→CI-SMOKE；§3.1–3.3 各至少一條典型命令（對齊 INDEX／contract）
  - AC-2: PASS — 鏈 `docs/smoke-and-regression-contract-v1.md` 與 INDEX §1.5；位階表屬實（runbook=操作單頁 · contract=契約 SSOT）
  - AC-3: PASS — §4 pass/fail 摘要含 CI-SMOKE 三規則 + MC 排除 phi_demo；`non_claims` 置頂且含 ≠ required CI／≠ INT Tier-A／≠ Phase%／≠ P6 closure／≠ Round-2 GO
  - AC-4: PASS — Reviewer 重跑 `rg "MP-SMOKE|MC-SMOKE|CI-SMOKE|non_claims|release.sanity|smoke-and-regression" docs/phase6-release-sanity-runbook-v1.md` 命中（exit 0）
  - AC-5: PASS — 本票 B_REPORT 變更僅 AllowedPaths；未改本票範圍內 `core/**`／`.github/workflows/**`／Phase%（工作樹另有無關髒檔，見 suggestions）
  - AC-6: PASS（MAY）— INDEX §1.5 MP-SMOKE 段一句 + `docs/index.md` 導航一行均命中本 doc 路徑；未越界改 §1.5 外 runner 行為敘事
- risk_level: low
- suggestions:
  - Scribe：Progress 末尾 append；可選 QUEUE／SESSION；`docs/index.md` 文末 changelog 可補一行 FP-G6-T2（非 blocking）
  - 封存敘事勿把工作樹內無關 `core/**`／`.github/workflows/**` 髒檔算入本票
  - 勿宣稱 required CI／INT Tier-A／P6 closure／Round-2 GO；本票未跑實際 smoke runner（doc-only · L-local）

---

## D_REPORT
<!-- Scribe 填 · 2026-07-10 -->

- docs_updates:
  - `docs/phase6-release-sanity-runbook-v1.md`（本票产物 · Implementer 已交 · 本轮未改正文）
  - `04_Workflows/WORKFLOW_INDEX.md` §1.5 一句交叉引用（已有 · 未改）
  - `docs/index.md` 导航一行（已有）+ 文末 changelog 一行（本轮 Scribe）
  - QUEUE／SESSION／Progress 末尾封存收口
- progress_entry: >-
  2026-07-10 · FP-G6-T2 done · release-sanity runbook 单页 SSOT · Reviewer accepted ·
  AC-1..AC-6 PASS · 未改 core／workflows／Phase% · 勿宣称 required CI／INT Tier-A／P6 closure／Round-2 GO
- followup_suggestions:
  - 下一刀：arrange `FP-G6-T4-inspector-overclaim-spotcheck-v1`（G6 doc-only · 无 human 前置）
  - 勿把 W4 human-blocked／FP-G6-T1（WC-PRE）／FP-G6-required-ci 当可 execute
  - 封存叙事勿并入工作树无关 core/**／.github/workflows/** 脏档
