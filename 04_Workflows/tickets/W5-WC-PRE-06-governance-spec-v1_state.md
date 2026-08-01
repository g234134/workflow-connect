# TICKET STATE · W5-WC-PRE-06-governance-spec-v1 · P10 CI Governance Spec (doc-only)

> handoff 摘要檔 · Wave 5 · WC-PRE-06 governance 升格設計/批文層 · **不接 prod runtime**

---

## FRAME

- Goal: 將 toolchain health L0→L1→L2 CI governance 升格路徑對齊 Wave Master P10 敘事，交付 `design_ready` spec + 批文 template + minimal policy JSON；**不**實施 CI 變更。
- Scope:
  - 增量 `docs/toolchain-observability-governance-upgrade-v1.md` §12 Wave Master cross-ref
  - 新建 `docs/governance/WC_PRE_06_approval_template.md`
  - 新建 `docs/governance/wc_pre_06_governance_policy_v1.json`（minimal policy）
  - `docs/governance/WC_PRE_06_07_rollout_plan.md` §9 Wave 5 cross-ref（不改 D1–D5）
  - 本 state 檔 B_REPORT / D_REPORT
- NonScope:
  - 修改 `.github/workflows/*` · branch protection
  - 填寫 `approval_status=approved`
  - `WC-IMPL-L1` / `WC-IMPL-L2` 施工
  - 拉升 Dashboard Phase%
- AllowedPaths:
  - `docs/toolchain-observability-governance-upgrade-v1.md`
  - `docs/governance/WC_PRE_06_approval_template.md`
  - `docs/governance/wc_pre_06_governance_policy_v1.json`
  - `docs/governance/WC_PRE_06_07_rollout_plan.md`（§9 append only）
  - `04_Workflows/tickets/W5-WC-PRE-06-governance-spec-v1_state.md`
- BlockedPaths:
  - `.github/workflows/*`
  - `docs/phase3-5-cost-model-governance-contract-v1.md` 正文表
  - `core/*` · venv · `.env`
- Dependencies:
  - `docs/toolchain-observability-governance-upgrade-v1.md`（WC-PRE-06 母本）
  - `docs/governance/WC_PRE_06_07_rollout_plan.md`
  - `04_Workflows/tickets/W-MASTER-wave-plan_state.md` §Wave 5
- AcceptanceCriteria:
  - AC-1: spec 含 Wave Master + P10 non-runtime 邊界（§12）
  - AC-2: approval template 含批准方 · 證據形式 · L1/L2 門檻 · rollback 引用
  - AC-3: policy JSON 存在且 `approval_status` 均 pending
  - AC-4: verify_commands grep 通過 · 零 workflow diff
  - AC-5: non_claims 明示 governance 未啟用

```yaml
wave_id: W5
lifecycle_phase: D
phase_targets: [P10]
estimated_cycles: 1
mvp_allowed: true
human_only_prereqs:
  - owner: 尚書省/治理委員会
    deliverable: WC-PRE-06 L1/L2 approval_status signed + wc_pre_approval_id
observability:
  verify_commands:
    - 'rg "approval_status|design_ready|non-runtime" docs/toolchain-observability-governance-upgrade-v1.md docs/governance/WC_PRE_06_approval_template.md'
    - 'python -c "import json; p=json.load(open(\"docs/governance/wc_pre_06_governance_policy_v1.json\")); assert p[\"status\"]==\"design_only\"; assert p[\"approval_status\"][\"L1_pr_optional\"]==\"pending\""'
    - 'rg "pending" docs/governance/WC_PRE_06_approval_template.md'
  evidence_artifacts:
    - docs/toolchain-observability-governance-upgrade-v1.md
    - docs/governance/WC_PRE_06_approval_template.md
    - docs/governance/wc_pre_06_governance_policy_v1.json
  trace_fields:
    - wc_pre_approval_id
    - approval_status.L1
    - approval_status.L2
    - design_ready
    - mandatory_ci_scope  # WC-PRE-07 分軌 · 本票只讀引用
  success_signals:
    - Reviewer design_ready · approval pending
    - policy JSON schema_version present
  failure_signals:
    - 文档含 approved 已填值
    - 声称 PR required 已开启
  future_dashboard:
    - WAVE_PROGRESS_DASHBOARD.md Lane B WC-PRE-06 row 消费 approval_status.L1/L2
    - observe_wave_evidence_v1.py 扫描 wc_pre_approval_id in Progress append
non_claims:
  - 此票僅設計/批文流程，不等於 governance 已啟用
  - 不等於 prod selector 已啟用
  - 不等於 WC-PRE-06 已 human 批准
```

---

## STATE

- overall_status: **done**
- implementation_status: **done**
- lifecycle_phase: **D**
- current_owner: **scribe**
- next_action: 票已收口 · human 批文（`approval_status.*`）仍 pending · 尚書省填 template 後開 `WC-IMPL-L1`/`L2`
- last_updated: 2026-06-26 · scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- non_claims:
  - 此票僅設計/批文流程，不等於 governance 已啟用
  - 不等於 prod selector / Monitoring Graph L1/L2 已啟用
  - 不等於 branch protection 或 PR required 已變更

---

## B_REPORT

- changed_files:
  - `docs/toolchain-observability-governance-upgrade-v1.md`（新增 §12 Wave Master · P10 non-runtime）
  - `docs/governance/WC_PRE_06_approval_template.md`（新建）
  - `docs/governance/wc_pre_06_governance_policy_v1.json`（新建 · minimal policy）
  - `docs/governance/WC_PRE_06_07_rollout_plan.md`（§9 Wave 5 cross-ref append）
  - `04_Workflows/tickets/W5-WC-PRE-06-governance-spec-v1_state.md`（新建）
- artifacts:
  - Governance spec §12：可升格 gate 表 · 升格條件 G1–G6 · non-claims
  - Approval template：RACI · `wc_pre_approval_id` · Progress YAML 範例
  - Policy JSON：`levels` L0/L1/L2 · `escalation_gates` · `non_claims`
- verification:
  - `rg "approval_status|design_ready|non-runtime" docs/toolchain-observability-governance-upgrade-v1.md docs/governance/WC_PRE_06_approval_template.md` → **ok**（多處命中 §12 · template §5 pending）
  - `python -c "import json; p=json.load(open('docs/governance/wc_pre_06_governance_policy_v1.json')); assert p['status']=='design_only'; assert all(v=='pending' for k,v in p['approval_status'].items() if k.endswith('optional') or k.endswith('required') or k=='proposal_review')"` → **ok**
  - `rg "approved" docs/governance/WC_PRE_06_approval_template.md` → **ok**（僅「禁止 AI 填 approved」語境 · 無已填批准值）
  - `.github/workflows/` diff → **none**（未改 CI）
- behavior_notes:
  - Policy JSON 為 machine-readable 骨架；human 批文仍以 template + design doc §8 為準
  - L2 hard assert 對齊 rollout D2：不含 `aggregated_health_score`
- deferred_items:
  - Human 批文 · `WC-IMPL-L1` / `WC-IMPL-L2` 施工
  - P3.5 `OG-TOOLCHAIN-HEALTH` 正式增行（`WA-T3-AMEND-OG-TOOLCHAIN`）

---

## C_REPORT

- **review_date**: 2026-06-26
- **verdict**: **`accepted`**
- **conclusion**: governance **design_ready** · policy JSON 全 **pending** · **非 CI 啟用**。
- **checks_summary**:
  - AC-1: spec §12 Wave Master · P10 non-runtime 邊界 — ✅
  - AC-2: approval template（批准方 · 證據 · L1/L2 門檻 · rollback）— ✅
  - AC-3: policy JSON `status=design_only` · `approval_status.*` 均 pending — ✅
  - AC-4: verify_commands grep 通過 · 零 workflow diff — ✅
  - AC-5: non_claims 明示 governance 未啟用 — ✅
- **blocking_issues**: 無
- **risk_level**: low
- **suggestions**: human 批文 append `wc_pre_approval_id` 至 Progress 後另開 `WC-IMPL-L1`/`L2`；**不得**由 AI 填 `approval_status=approved`

---

## D_REPORT

- docs_updates:
  - 已完成 spec §12 · approval template · policy JSON · rollout §9
  - Progress 末尾已 append W5-WC-PRE-06 收口條目（2026-06-26 · Scribe）
- progress_entry: |
    W5-WC-PRE-06（WC-PRE-06）Wave 5 governance spec + approval template + policy JSON · Reviewer **accepted** · **design_ready**。**非** human 批准 · **非** CI 啟用 · policy JSON `approval_status.*` 全 pending。
- followup_suggestions:
  - Reviewer 驗收後 Orchestrator 更新 overall_status
  - 尚書省填 `WC_PRE_06_approval_template.md` → 另開 `WC-IMPL-L1` / `L2`
- observability_trace_plan:
  - **Dashboard**：Lane B WC-PRE-06 行讀 `approval_status.L1/L2` + `design_ready`
  - **Progress**：human 批文 append `wc_pre_approval_id` + scope
  - **Policy JSON**：implementation 前同步 `approval_status.*`
  - **Observer CLI**（W5-T3）：future 掃描本票 STATE + template pending 欄位
  - **CI signals**（post-impl）：`governance_snapshot.json` · `governance_advisory.log` · **非** 本票範圍

---
