# TICKET STATE · WF-P6-INT-NIGHTLY-MONITOR · P6 INT Gate Nightly Stability Monitor (83→91 uplift)

> **Orchestrator line ticket** · Phase 3 · 监控 nightly Track B 连续 7 日绿 · 为 final Phase uplift 83→91 提供 evidence  
> **Upstream**: `WF-P6-INT-CI-LANDING` merge · governance_decision_p6_int_gate_2026-06-27  
> **handoff 摘要檔**；跨 chat 交棒以本档 FRAME 为准

---

## FRAME

### Goal

监控 `.github/workflows/p6-int-gate-nightly.yml` 连续 **7 日**成功运行（无 gating failure），汇总 artifact evidence 供治理 chat 执行 Phase uplift **83→91**。

### Scope

- 从 GitHub Actions artifacts / run history 收集 nightly JSON（`artifacts/p6-int-gate/nightly.json` 或 upload artifact `p6-int-gate-nightly-*`）
- 新建 `docs/p6-int-nightly-monitor-v1.md`（或等价 YAML 摘要）记录 7 日绿证据
- `04_Workflows/workflow_line_status_2026-06-27.yaml` — 可追加 `nightly_monitor_*` 字段（**不改 Phase%**）

### NonScope

- **不**修改 `.github/workflows/p6-int-gate-nightly.yml` / `p6-int-gate-pr-optional.yml`
- **不**改 `docs/WAVE_PROGRESS_DASHBOARD.md` Phase%（83→91 留治理 chat）
- **不**在未满 7 日绿时宣称 final uplift 就绪

### allowed_paths

| Path | 操作 |
|------|------|
| `docs/p6-int-nightly-monitor-v1.md` | **新建** evidence 汇总 |
| `04_Workflows/workflow_line_status_2026-06-27.yaml` | `nightly_monitor_*` 字段 only |
| `04_Workflows/00_Agent_Work_Progress.md` | 末尾 append |
| `04_Workflows/tickets/WF-P6-INT-NIGHTLY-MONITOR_state.md` | B/C/D_REPORT |

### blocked_paths

- `.github/workflows/*`
- `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 数字
- Batch 1 治理 YAML
- 任意 Phase% uplift 在本票自动执行

### AcceptanceCriteria

- **AC-1**: 连续 7 个 UTC 日 nightly run 均为 success（或 documented infra skip 不计入）
- **AC-2**: 每日 artifact 可查 · JSON `ok: true` · `tier: A`
- **AC-3**: `docs/p6-int-nightly-monitor-v1.md` 含日期表 · run_id · verdict
- **AC-4**: 治理 chat 可引用 monitor doc 执行 83→91 uplift

### final_uplift_conditions (governance_ref)

来自 **governance_decision_p6_int_gate_2026-06-27**：

- nightly 7 日连续绿
- 首跑 artifact 可查
- 移除 `functional_gaps` 中 `nightly_int_gate_ci_not_scheduled`

---

## STATE

- overall_status: in_progress
- lifecycle_phase: A
- current_owner: human-ops
- next_action: 綠日鐘 · DAY1 GREEN (29159219832) · **DAY2 GREEN** (29186698130) · **2/7** · 續收 DAY3–7 · 滿 7/7 後尚書省再裁 83→91
- last_updated: 2026-07-12 · Scribe 回填 DAY2 schedule GREEN
- status_by_role:
  - orchestrator: done — WINDOW OPEN 裁決已記
  - implementer: done — core 可見性已修 · 二次 PASS
  - reviewer: pending — 滿 7/7 後驗
  - scribe: done — monitor 表 DAY2 GREEN · **2/7** · ≠ uplift

---

## B_REPORT

*(待 nightly 7 日窗口完成后回填)*

---

## C_REPORT

*(待 Reviewer 回填)*

---

## D_REPORT

- docs_updates:
  - `docs/p6-int-nightly-monitor-v1.md` — DAY0 RED 不計 · DAY1 GREEN `29159219832` · DAY2 GREEN `29186698130` · **2/7**
  - `docs/ga-remote-closure-checklist-v1.md` — P6／P9／P7 二次結果
- progress_entry: P6 綠日鐘 DAY2 · 2/7 · ≠ uplift
- followup_suggestions: 續收 nightly 綠日 · 勿自動 uplift · Round-2 仍 DEFER ≥07-18