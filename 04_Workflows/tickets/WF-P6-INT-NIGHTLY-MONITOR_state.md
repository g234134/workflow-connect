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
- next_action: **≥7/7 已滿** · uplift **91 applied** · tip#1 超額綠日盯梢 · Round-2 仍 DEFER · ≠ war_status
- last_updated: 2026-07-28 · next-p6-watch
- status_by_role:
  - orchestrator: done — WINDOW OPEN 裁決已記
  - implementer: done — DAY6–7 + 超額綠日已核（GHA success）· 07-28 盯梢再核 latest=07-27
  - reviewer: done — uplift 91 已 apply（cross-ref W-PROG）
  - scribe: done — 裁決包已交 · authorize 已跑 · 盯梢總覽已交

---

## B_REPORT

- changed_files:
  - `docs/p6-int-nightly-monitor-v1.md` — DAY6–7 + post-7 超額綠日 · **≥7/7**
  - `04_Workflows/tickets/WF-P6-INT-NIGHTLY-MONITOR_state.md` — 本段 append
- artifacts:
  - DAY7 run_id=`29568619424` · post-7 latest=`30258570894`（2026-07-27）
  - prior DAY5 sample：`p6-int-gate-nightly-29403223522`（`ok=true` · tier=A · 112/112）
- verification: |
    gh run list --workflow=p6-int-gate-nightly.yml --limit 15
- behavior_notes: 綠日鐘以 GHA workflow success 計；artifact JSON 抽樣核驗可另開 · ≠ Phase% uplift
- deferred_items: 尚書省 B2 再簽 83→91 · Dashboard authorize

### Append · 2026-07-28 · Wave5 sidecar 綠日回填

- **結論**：**7/7 滿窗** + 超額綠日至 07-27
- **non_claims**：≠ 83→91 已 uplift · ≠ Round-2 · ≠ 改 workflow

### Append · 2026-07-28 · Track B · P6 uplift 裁決包（83→91 待簽）

- **裁決包**：`docs/governance/p6_uplift_decision_pack_83_to_91_v1.md`
- **證據**：DAY7=`29568619424` · latest post-7=`30258570894` · Dashboard P6=**83%**
- **建議**：83→91（+8）· **待**尚書省簽署欄勾選
- **本輪**：**未**改 Dashboard % · **未**跑 `_phase_pct_apply` · `apply_phase_pct=false`
- **next_action**：尚書省簽裁決包 → 另開 W-PROG + authorize apply
- **non_claims**：≠ 已 uplift · ≠ Round-2 · ≠ required CI

### Append · 2026-07-28 · P6 uplift applied（cross-ref W-PROG）

- **W-PROG**：`W-PROG-p6-uplift-83-to-91-2026-07-28` · authorize apply **完成**
- **Dashboard P6**：**83 → 91**
- **裁決包**：§3 APPROVE · 口令 `DEFER + P6_SIGN`
- **next_action**：超額綠日可續收 · Round-2 仍 DEFER／armed-not-run
- **non_claims**：≠ Round-2 GO · ≠ H2–H5 解阻 · ≠ required CI · ≠ DarkOps · ≠ war_status 升檔

### Append · 2026-07-28 · next-p6-watch（超額綠日盯梢）

- **核對**：`gh run list --workflow=p6-int-gate-nightly.yml --limit 15`
- **latest**：UTC 2026-07-27 · `30258570894` · success · UTC 07-28 schedule 尚未出現
- **Dashboard P6**：91% · **不再**開 uplift 除非新裁決包
- **旁線**：Tabular 可選 · 須 `TABULAR_SIDELINE` · ≠ Phase% 假閉環
- **總覽**：`docs/governance/wave5_next_stage_post_defer_p6_v1.md`
- **non_claims**：≠ Round-2 GO · ≠ war_status 升檔 · ≠ 假 host

---

## C_REPORT

*(uplift 91 已 apply · 超額綠日持續觀測)*

---

## D_REPORT

- docs_updates:
  - `docs/p6-int-nightly-monitor-v1.md` — DAY1–7 GREEN · **≥7/7** + post-7 超額（2026-07-28）
- progress_entry: P6 綠日鐘 ≥7/7 · uplift 待再簽 · ≠ Round-2
- followup_suggestions: 尚書省 B2 再簽 83→91 · 超額綠日續收 · Round-2 仍 human-gated
