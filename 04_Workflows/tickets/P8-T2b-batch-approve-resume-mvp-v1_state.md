# TICKET STATE · P8-T2b-batch-approve-resume-mvp-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準。補齊 P8-T2 deferred：`--batch-approve` + `--resume-latest-approved`。

---

## FRAME

<!-- Orchestrator 填 · 2026-07-13 凍結 -->

**Goal:**
- 補齊 Operator backlog deferred：同 `task_type` 批次核准，以及 resume-latest 路徑解析（多個 approved 時 fail-close）。

**Scope:**
- `scripts/list_operator_backlog_v1.py`：`--batch-approve`、`--resume-latest-approved`、`--task-type`、`--dry-run`
- `tests/test_operator_backlog_t2b_v1.py`
- `docs/phase-8-operator-backlog-v1.md`（T2b 旗標說明）
- 本票 state

**NonScope:**
- 不做 checkpoint preview CLI
- 不做 P8-T3 真 webhook／DLQ
- 不做 Web UI；不自動執行完整 standard-case orchestrator resume（僅路徑解析 + hint）
- 不改 `core/**`、AGENTS、憲法、合約、`.cursor/rules`
- `apply_phase_pct: false`（% 僅 W-PROG）

**AllowedPaths:**
- `scripts/list_operator_backlog_v1.py`
- `tests/test_operator_backlog_t2b_v1.py`
- `docs/phase-8-operator-backlog-v1.md`
- `04_Workflows/tickets/P8-T2b-batch-approve-resume-mvp-v1_state.md`
- `04_Workflows/tickets/P8-T2-operator-pending-visibility-v1_state.md`（僅末尾 append deferred→delivered 註記）

**BlockedPaths:**
- `core/**`
- `AGENTS.md` / `HARNESS_CONSTITUTION.md` / `ENGINEERING_CONTRACT.md` / `.cursor/rules/**`
- `docs/WAVE_PROGRESS_DASHBOARD.md`（本票不寫 %）
- `04_Workflows/project_status/master_status.md`

**Dependencies:**
- P8-T2 operator backlog v1（已 implemented）
- `hitl.checkpoints_v1`（list_pending / build_resume_context / append event）

**AcceptanceCriteria:**
1. `--batch-approve --task-type <T>` 僅核准同 task_type 的 awaiting_human CP-A；缺 task_type → fail。
2. `--resume-latest-approved`：0 → fail；1 → 回傳 selected path；>1 且無 `--case-ref` → fail-close + options。
3. `python -m unittest tests.test_operator_backlog_t2b_v1 -v` 全綠；既有 `tests.test_operator_backlog_v1` 不回歸。
4. docs 已記載 T2b 旗標；`executed_resume=false` 誠實口徑。

**Phase 影響（FRAME）:**
```yaml
phase_targets: [P8]
baseline_pct: "07-13 W-PROG-triple · P8=46%"
proposed_delta_pct: "+12"
evidence_gate: L-local
apply_phase_pct: false
```

---

## STATE

- **overall_status:** accepted
- **current_owner:** scribe
- **next_action:** scribe_progress_via_wprog_batch
- **last_updated:** 2026-07-13 · same_chat O/B/C
- **status_by_role:**
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending
- **ac_status:**
  - AC-1: pass
  - AC-2: pass
  - AC-3: pass
  - AC-4: pass

---

## B_REPORT

- changed_files:
  - `scripts/list_operator_backlog_v1.py`
  - `tests/test_operator_backlog_t2b_v1.py` (new)
  - `docs/phase-8-operator-backlog-v1.md`
  - `04_Workflows/tickets/P8-T2b-batch-approve-resume-mvp-v1_state.md` (new)
- verification: |
    ```powershell
    python -m unittest tests.test_operator_backlog_t2b_v1 tests.test_operator_backlog_v1 -v
    ```
- behavior_notes: |
    - batch-approve：case-scoped 寫入 approved + checkpoint event；跳過異 task_type
    - resume-latest：路徑解析 only；多個 approved → fail_close + options
- deferred_items: checkpoint preview CLI；自動執行 full resume orchestrator

### Phase 影響

- **影響 Phase**：P8
- **baseline**：07-13 W-PROG-triple · 46%
- **proposed_delta**：+12
- **實際上調**：待 W-PROG
- **non_claims**：≠ preview CLI · ≠ P8-T3 webhook · ≠ Phase closure · ≠ 自動跑 full resume

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: AC-1～4 對照通過；T2b + v1 unittest 全綠；未寫 Dashboard %。
- risk_level: low
- suggestions: W-PROG 匯總 03/04/T2b 後保守端寫入 P8 %

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+12
- **實際上調**：待 W-PROG
- **non_claims**：≠ auto-uplift

---

## D_REPORT

- docs_updates: `docs/phase-8-operator-backlog-v1.md` T2b 旗標
- progress_entry: 見 Progress 末尾 · W-PROG 匯總
- followup_suggestions: checkpoint preview 另票；P8-T3 webhook 另票

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+12
- **實際上調**：見 W-PROG
- **non_claims**：≠ Phase closure
