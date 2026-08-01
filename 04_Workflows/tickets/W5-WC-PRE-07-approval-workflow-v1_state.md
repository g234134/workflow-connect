# TICKET STATE · W5-WC-PRE-07-approval-workflow-v1 · Mandatory Smoke CI Approval Workflow (doc-only)

> handoff 摘要檔 · Wave 5 · WC-PRE-07 human 批文流程 SSOT · **不接 prod runtime**

---

## FRAME

- Goal: 補齊 WC-PRE-07 mandatory smoke CI 設計稿 + human 批文 workflow（誰批 · 產物格式 · `wc_pre_approval_id` trace）；Reviewer 可驗收 **`design_ready`** · **不**宣稱 PR required 已開。
- Scope:
  - 新建 `docs/toolchain-smoke-mandatory-ci-runner-v1.md`
  - 新建 `docs/governance/WC_PRE_07_approval_template.md`
  - 新建 `docs/governance/wc_pre_07_approval_workflow_policy_v1.json`
  - 更新 `docs/WAVE_PROGRESS_DASHBOARD.md` Lane B WC-PRE-07 cross-ref（不改 Phase%）
  - 本 state 檔 B_REPORT / D_REPORT
- NonScope:
  - 新建/改 `.github/workflows/**`
  - `WC-IMPL-SMOKE-CI-L1` / `L2` 施工
  - P10 S15 notify / intake API runtime
  - 填寫 human 批文
- AllowedPaths:
  - `docs/toolchain-smoke-mandatory-ci-runner-v1.md`
  - `docs/governance/WC_PRE_07_approval_template.md`
  - `docs/governance/wc_pre_07_approval_workflow_policy_v1.json`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Lane B 行 only）
  - `04_Workflows/tickets/W5-WC-PRE-07-approval-workflow-v1_state.md`
- BlockedPaths:
  - `.github/workflows/*` · branch protection
  - `routing/toolchain_smoke_matrix_v1.yaml`（YAML 变更另票 CH-12）
  - `core/*` · venv · `.env`
- Dependencies:
  - `docs/governance/WC_PRE_06_07_rollout_plan.md` §7 D3/D5
  - `routing/toolchain_smoke_matrix_v1.yaml` · `scripts/run_toolchain_smoke_matrix.py`（只读）
  - W5-WC-PRE-06（治理叙事一致 · 可并行）
- AcceptanceCriteria:
  - AC-1: `toolchain-smoke-mandatory-ci-runner-v1.md` 含 tier 表 · workflow 挂载设计 · rollback
  - AC-2: approval template 含批准方 · L1/L2 证据 · `wc_pre_approval_id` · impl 票映射
  - AC-3: `approval_status` pending · Reviewer 可判 `design_ready`
  - AC-4: explicit：mandatory smoke CI ≠ P10 prod gap 闭合
  - AC-5: 与 rollout D5 一致 · 无 workflow diff

```yaml
wave_id: W5
lifecycle_phase: D
phase_targets: [P10, P10.5]
estimated_cycles: 1
mvp_allowed: true
human_only_prereqs:
  - owner: 尚書省
    deliverable: WC-PRE-07 L1/L2 approval + wc_pre_approval_id + WC-IMPL-SMOKE-CI-* 授权
observability:
  verify_commands:
    - 'test -f docs/toolchain-smoke-mandatory-ci-runner-v1.md'
    - 'rg "blocked_on_approval|design_ready|wc_pre_approval_id" docs/governance/WC_PRE_07_approval_template.md'
    - 'python -c "import json; p=json.load(open(\"docs/governance/wc_pre_07_approval_workflow_policy_v1.json\")); assert p[\"status\"]==\"design_only\"; assert p[\"approval_status\"][\"L1_optional_ci_advisory\"]==\"pending\""'
  evidence_artifacts:
    - docs/toolchain-smoke-mandatory-ci-runner-v1.md
    - docs/governance/WC_PRE_07_approval_template.md
    - docs/governance/wc_pre_07_approval_workflow_policy_v1.json
  trace_fields:
    - wc_pre_approval_id
    - approval_status.L1
    - approval_status.L2
    - mandatory_ci_scope
    - design_ready
  success_signals:
    - design_ready · pending_approval · blocked_on_approval
  failure_signals:
    - PR required 已开启 over-claim
    - P10 prod-ready 暗示
  future_dashboard:
    - Lane B WC-PRE-07 行 + smoke_ci_summary.json post-impl
    - MS-OPTIONAL-CI-GAP advisory 消費 mandatory_ci_scope
non_claims:
  - 此票僅設計/批文流程，不等於 governance 已啟用
  - 非 mandatory CI 已上线
  - 非 P10 runtime 交付
  - 不等於 prod selector 已啟用
```

---

## STATE

- overall_status: **done**
- implementation_status: **done**
- lifecycle_phase: **D**
- current_owner: **scribe**
- next_action: 票已收口 · **`blocked_on_approval`** · human 批文後開 `WC-IMPL-SMOKE-CI-L1`/`L2`
- last_updated: 2026-06-26 · scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- non_claims:
  - 此票僅設計/批文流程，不等於 governance 已啟用
  - 非 mandatory CI 已上线 · 非 PR required 已開
  - 不等於 prod selector 已啟用 · 非 P10 prod-ready

---

## B_REPORT

- changed_files:
  - `docs/toolchain-smoke-mandatory-ci-runner-v1.md`（新建 · design SSOT）
  - `docs/governance/WC_PRE_07_approval_template.md`（新建）
  - `docs/governance/wc_pre_07_approval_workflow_policy_v1.json`（新建）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Lane B WC-PRE-07 行 cross-ref）
  - `04_Workflows/tickets/W5-WC-PRE-07-approval-workflow-v1_state.md`（新建）
- artifacts:
  - Smoke CI design：L1 optional_ci advisory · L2 白名單 · eval-gate 挂载 · rollback
  - Approval workflow：RACI · Progress YAML · `wc_pre_approval_id` 格式
  - Policy JSON：`workflow_mount_design` · `trace_fields` · `non_claims`
- verification:
  - `test -f docs/toolchain-smoke-mandatory-ci-runner-v1.md` → **ok**（文件存在）
  - `rg "blocked_on_approval|design_ready|wc_pre_approval_id" docs/governance/WC_PRE_07_approval_template.md` → **ok**（§0 · §3 · §8 命中）
  - `python -c "import json; p=json.load(open('docs/governance/wc_pre_07_approval_workflow_policy_v1.json')); assert p['status']=='design_only'; assert p['approval_status']['L1_optional_ci_advisory']=='pending'"` → **ok**
  - 未執行任何實際批文（依任務約束）
  - `.github/workflows/` diff → **none**
- behavior_notes:
  - L2 白名單對齊 rollout D3：`TS-TOOLCHAIN-DASHBOARD-UNIT` + `TS-W3TL-UNIT`
  - Legacy `WC-PRE-07_state.md` 未改；Wave 5 SSOT 為本檔
- deferred_items:
  - Human 批文 · `WC-IMPL-SMOKE-CI-L1` / `L2`
  - Legacy ticket `04_Workflows/tickets/WC-PRE-07_state.md` 同步（Orchestrator 可選）

---

## C_REPORT

- **review_date**: 2026-06-26
- **verdict**: **`accepted`**
- **conclusion**: approval workflow **design_ready** · **`blocked_on_approval`** · mandatory smoke CI **design-only**。
- **checks_summary**:
  - AC-1: `toolchain-smoke-mandatory-ci-runner-v1.md` tier 表 · workflow 挂载设计 · rollback — ✅
  - AC-2: approval template（批准方 · L1/L2 证据 · `wc_pre_approval_id` · impl 票映射）— ✅
  - AC-3: `approval_status` pending · `design_ready` 可判 — ✅
  - AC-4: mandatory smoke CI ≠ P10 prod gap 闭合 — ✅
  - AC-5: 与 rollout D5 一致 · 无 workflow diff — ✅
- **blocking_issues**: 无
- **risk_level**: low
- **suggestions**: 尚書省填 template → `WC-IMPL-SMOKE-CI-L1`/`L2`；**非 PR required 已啟**

---

## D_REPORT

- docs_updates:
  - 已完成 smoke CI design spec · approval template · policy JSON · Dashboard cross-ref
  - Progress 末尾已 append W5-WC-PRE-07 收口條目（2026-06-26 · Scribe）
- progress_entry: |
    W5-WC-PRE-07（WC-PRE-07）mandatory smoke CI design + approval workflow · Reviewer **accepted** · **design_ready** · **`blocked_on_approval`**。**非** human 批文 · **非** workflow 施工 · **非 PR required 已啟** · **非** P10 prod 閉環。
- followup_suggestions:
  - 尚書省填 template → 開 `WC-IMPL-SMOKE-CI-L1` / `L2`
  - Orchestrator 可將 legacy `WC-PRE-07_state.md` overall_status 對齊 `design_ready`
- observability_trace_plan:
  - **Dashboard**：Lane B 行 `mandatory_ci_scope` · `blocked_on_approval`
  - **Progress**：`wc_pre_approval_id` append 為 human 批文 SSOT
  - **State 欄位**：`approval_status.L1/L2` · `mandatory_ci_scope` · `implementation_tickets`
  - **Post-impl CI**：`smoke_ci_summary.json` · `MS-OPTIONAL-CI-GAP` / `MS-CI-SMOKE-*` in governance snapshot
  - **Observer**（W5-T3）：扫描本票 + template pending · honest gap if no wc_pre_approval_id

---
