# TICKET STATE · WF-P6-INT-CI-LANDING · P6 INT Gate CI Workflow Landing

> **Orchestrator line ticket** · P6 专项目 · Track B (nightly mandatory) + Track A (PR optional advisory)  
> **Upstream SSOT**: `docs/ci-design-p6-int-gate-v1.md` · governance_decision_p6_int_gate_2026-06-27  
> **handoff 摘要檔**；跨 Task 子 agent 以本檔 FRAME 為準

---

## FRAME

### Goal

根据 `docs/ci-design-p6-int-gate-v1.md` 与 **governance_decision_p6_int_gate_2026-06-27** 治理裁决，落地 P6 INT regression gate 的 GitHub Actions CI：

- **Track B (mandatory)** — nightly scheduled INT Tier-A · UTC 07:00 · artifact JSON · job 失败即红
- **Track A (recommended)** — PR optional advisory · `continue-on-error: true` · **不** blocks PR merge · **不** 升格 `blocks_pr_ci: true`

本票 merge 后 Phase% **仍为 72%**；interim uplift **72→83** 由治理 chat 在 merge 证据就绪后单独执行。

### Scope

- 新建 `.github/workflows/p6-int-gate-nightly.yml`（Track B）
- 新建 `.github/workflows/p6-int-gate-pr-optional.yml`（Track A · 独立 workflow · 等价于 eval-gate 增 job 方案）
- `04_Workflows/workflow_line_status_2026-06-27.yaml` — 仅新增 `ci_landing_done` / `ci_tracks_landed` 等标记（**不改** `current_phase_pct` / Phase%）
- `04_Workflows/00_Agent_Work_Progress.md` — Scribe 末尾追加本票战报
- 本票 STATE 回填 B/C/D_REPORT

### NonScope

- **不**修改 `docs/ci-design-p6-int-gate-v1.md` 设计正文（仅 cross-ref）
- **不**改 Batch 1 治理 YAML
- **不**改 `docs/WAVE_PROGRESS_DASHBOARD.md` Phase%（72→83→91 留治理 chat）
- **不**将 INT Tier-A 升格为 PR mandatory / branch protection required
- **不**改 `_wave7_regression_gate.py` / dark `core/wave7_regression_gate.py`
- **不**扩 scope 到 Tabular / P8.9 / 其他 Phase 线条

### allowed_paths

| Path | 操作 |
|------|------|
| `.github/workflows/p6-int-gate-nightly.yml` | **新建** Track B |
| `.github/workflows/p6-int-gate-pr-optional.yml` | **新建** Track A |
| `docs/ci-design-p6-int-gate-v1.md` | cross-ref only（本 batch 预期零 diff） |
| `04_Workflows/workflow_line_status_2026-06-27.yaml` | 新增 `ci_landing_*` 字段 · **不改 Phase%** |
| `04_Workflows/00_Agent_Work_Progress.md` | 末尾 append only |
| `04_Workflows/tickets/WF-P6-INT-CI-LANDING_state.md` | B/C/D_REPORT |

### blocked_paths

- 除上述 workflow 外之 `.github/workflows/*` 修改（eval-gate / core-agent-smoke 等）
- `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 数字
- Batch 1 治理 YAML（`routing/*governance*.yaml` · `docs/governance/` 已定稿档）
- `_wave7_regression_gate.py` · `01_Environments/python_venvs/gov_core_system/core/wave7_regression_gate.py`
- 其他 Phase 的 workflow_line_status 行或 global Phase% uplift

### governance_decision_ref

**governance_decision_p6_int_gate_2026-06-27**（尚書省裁决 · 2026-06-27）：

| 项 | 裁决 |
|----|------|
| Track B nightly | **mandatory 落地** |
| Track A PR optional | **建议同票落地** |
| PR mandatory INT | **禁止** · `blocks_pr_ci: false` 维持 |
| phase_uplift_policy | current **72** → interim **83**（CI merge 后）→ final **91**（nightly 7 日稳定） |

### AcceptanceCriteria

- **AC-1**: Track B nightly workflow 存在 · `on.schedule.cron` = `"0 7 * * *"` (UTC) · `workflow_dispatch` 可用
- **AC-2**: Track B job 跑 `python 04_Workflows/_wave7_regression_gate.py --tier A --pretty` · 产出 artifact JSON · exit code 反映 gate 结果
- **AC-3**: Track A PR optional job 存在 · `continue-on-error: true` · 不 blocks PR merge
- **AC-4**: CI 落地票完成后 YAML P6 行有 `ci_landing_done: true` · `ci_tracks_landed: [track_b_nightly, track_a_pr_optional]` · Phase% 仍为 72
- **AC-5**: 新增 workflow 至少一次 dry run / 语法验证（`gh workflow run` 或本地 YAML + gate 命令验证）

### Wave Master 扩展

- wave_id: null
- group_id: G6
- lifecycle_phase: B→C→D
- phase_targets: P6
- ticket_class: ci-land
- evidence_tier: L-ci
- parallel_ok: true（Worker A/B 可并行）
- non_claims:
  - no_pr_mandatory_tier_a
  - no_global_phase_pct_uplift_in_this_ticket
  - no_batch1_governance_yaml_change

---

## STATE

- overall_status: done_with_gaps
- lifecycle_phase: D
- current_owner: orchestrator
- next_action: merge 至 main → workflow_dispatch nightly 首跑 → WF-P6-INT-NIGHTLY-MONITOR 7 日窗口 → 治理 83→91
- last_updated: 2026-06-27 · scribe
- status_by_role:
  - orchestrator: done — FRAME opened
  - implementer: done — Track A/B workflows landed
  - reviewer: done — accepted_with_gaps
  - scribe: done — YAML + Progress append

---

## B_REPORT

**Implementer A (Track B nightly)**: implementation-worker · 2026-06-27  
**Implementer B (Track A PR optional)**: implementation-worker · 2026-06-27  
**Status**: 施工完成 · checker-reviewer 已签

### Changed files

| Path | Summary |
|------|---------|
| `.github/workflows/p6-int-gate-nightly.yml` | **Created** — Track B · cron `0 7 * * *` UTC · workflow_dispatch tier input · artifact `artifacts/p6-int-gate/nightly.json` · exit code = gate result |
| `.github/workflows/p6-int-gate-pr-optional.yml` | **Created** — Track A · path-filtered PR/push · `continue-on-error: true` · advisory artifact |

### Verification suggestions

```powershell
# Local (pre-push)
python -c "import yaml; yaml.safe_load(open('.github/workflows/p6-int-gate-nightly.yml',encoding='utf-8')); yaml.safe_load(open('.github/workflows/p6-int-gate-pr-optional.yml',encoding='utf-8'))"
python 04_Workflows/_wave7_regression_gate.py --tier A --pretty

# Post-merge (requires gh auth)
gh workflow run "P6 INT gate nightly" --field tier=A
gh workflow run "P6 INT gate PR optional (advisory)"
```

---

## C_REPORT

**Reviewer**: checker-reviewer · 2026-06-27  
**Verdict**: `accepted_with_gaps`

| AC | Result | Evidence |
|----|--------|----------|
| AC-1 | **PASS** | `p6-int-gate-nightly.yml` · `schedule.cron: "0 7 * * *"` · `workflow_dispatch` with tier input |
| AC-2 | **PASS** | Job runs `_wave7_regression_gate.py --tier A --pretty` · tees to `artifacts/p6-int-gate/nightly.json` · uploads artifact · exit propagates gate code |
| AC-3 | **PASS** | `p6-int-gate-pr-optional.yml` job has `continue-on-error: true` · no branch-protection coupling · `blocks_pr_ci: false` preserved |
| AC-4 | **PASS** | YAML `ci_landing_done: true` · `ci_tracks_landed: [track_b_nightly, track_a_pr_optional]` · `current_phase_pct: 72` unchanged |
| AC-5 | **PASS with gap** | Local YAML parse OK · local Tier-A gate exit 0 · **`gh workflow run` not executed** (gh CLI absent on worker host) — recommend post-merge dispatch |

**Non-claims verified**: no eval-gate / core-agent-smoke edits · no Dashboard Phase% change · no PR mandatory elevation.

---

## D_REPORT

**Scribe**: 2026-06-27

- Updated `04_Workflows/workflow_line_status_2026-06-27.yaml` P6 row: `ci_landing_done: true`, `ci_tracks_landed`, `ci_workflows`, `phase_uplift_policy`, removed landed gaps (`nightly_int_gate_ci_not_scheduled`, `ci_workflow_landing_pending`, `governance_ci_design_approval_pending`)
- Appended Progress entry `2026-06-27 · WF-P6-INT-CI-LANDING`
- Opened downstream ticket `WF-P6-INT-NIGHTLY-MONITOR_state.md` for Phase 3 (83→91)
