# TICKET STATE · P8-T2c-checkpoint-preview-cli-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準。補齊 P8-T2 最後 deferred：checkpoint preview CLI。

---

## FRAME

<!-- Orchestrator 填 · 2026-07-13 凍結 -->

**Goal:**
- Operator 在核准前可預覽 checkpoint 內容（path 或 id），唯讀、結構化 `dict`。

**Scope:**
- `scripts/preview_checkpoint_v1.py`：`--checkpoint-path` / `--checkpoint-id`（可選 `--case-ref`）· `--format json|text`
- `tests/test_preview_checkpoint_v1.py`
- `docs/phase-8-operator-backlog-v1.md`（preview 節 + deferred 清除）
- 本票 state

**NonScope:**
- 不做 approve／reject／resume 突變
- 不做 Web UI；不做 P8-T3 webhook
- 不改 `hitl/checkpoints_v1.py` 契約語意（僅消費公開 API + 安全讀 path）
- 不改 `core/**`、AGENTS、憲法、合約、`.cursor/rules`
- `apply_phase_pct: false`（% 僅 W-PROG）

**AllowedPaths:**
- `scripts/preview_checkpoint_v1.py`
- `tests/test_preview_checkpoint_v1.py`
- `docs/phase-8-operator-backlog-v1.md`
- `04_Workflows/tickets/P8-T2c-checkpoint-preview-cli-v1_state.md`
- `04_Workflows/tickets/P8-T2-operator-pending-visibility-v1_state.md`（僅末尾 append deferred→delivered）

**BlockedPaths:**
- `core/**`
- `AGENTS.md` / `HARNESS_CONSTITUTION.md` / `ENGINEERING_CONTRACT.md` / `.cursor/rules/**`
- `docs/WAVE_PROGRESS_DASHBOARD.md`（本票不寫 %）
- `04_Workflows/project_status/master_status.md`

**Dependencies:**
- P8-T2 / P8-T2b（backlog + batch/resume）
- `hitl.checkpoints_v1.review_summary` / `get_checkpoint`

**relay_mode:** same_chat

**AcceptanceCriteria:**
1. `--checkpoint-path` 指向 outbox 下合法 checkpoint → `ok=true` + preview 含 checkpoint_id／case_ref／status／suggested_actions。
2. path 在 outbox 外 → `ok=false` fail-close。
3. `--checkpoint-id` 可解析既有 pending／resolved checkpoint；找不到 → `ok=false`。
4. `python -m unittest tests.test_preview_checkpoint_v1 -v` 全綠；`read_only=true`；無突變副作用。
5. docs 記載 preview CLI；P8-T2 deferred 註記已更新。

**Phase 影響（FRAME）:**
```yaml
phase_targets: [P8]
baseline_pct: "07-13 W-PROG-p8-80 · P8=76%"
proposed_delta_pct: "+8"
evidence_gate: L-local
apply_phase_pct: false
```

---

## STATE

- **overall_status:** accepted
- **current_owner:** scribe
- **next_action:** scribe_via_wprog_batch
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
  - AC-5: pass

---

## B_REPORT

- changed_files:
  - `scripts/preview_checkpoint_v1.py` (new)
  - `tests/test_preview_checkpoint_v1.py` (new)
  - `docs/phase-8-operator-backlog-v1.md`
  - `04_Workflows/tickets/P8-T2c-checkpoint-preview-cli-v1_state.md`
  - `04_Workflows/tickets/P8-T2-operator-pending-visibility-v1_state.md`（末尾 deferred→delivered）
- verification: |
    ```powershell
    python -m unittest tests.test_preview_checkpoint_v1 -v
    # → 5 tests OK
    ```
- behavior_notes: |
    - path／id 唯讀 preview；outbox 外 fail-close；mutated=false
    - 消費 `review_summary`／`get_checkpoint`；不改 checkpoint 檔
- deferred_items: 無（本票範圍內）

### Phase 影響

- **影響 Phase**：P8
- **baseline**：07-13 W-PROG-p8-80 · 76%
- **proposed_delta**：+8
- **實際上調**：待 W-PROG
- **non_claims**：≠ approve／resume 突變 · ≠ P8-T3 · ≠ Phase closure

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    AC-1～5 通過；5 unittest OK；read_only／mutated=false；
    outbox 外 fail-close；docs 已記載 preview；未改 hitl 契約。
- risk_level: low
- suggestions: 無

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+8
- **實際上調**：待 W-PROG
- **non_claims**：≠ auto-uplift

---

## D_REPORT

- docs_updates: `docs/phase-8-operator-backlog-v1.md` preview 節已寫
- progress_entry: 見 W-PROG 匯總
- followup_suggestions: 真 Worker／prod webhook 另票（誠實 100 缺口）

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+8
- **實際上調**：見 W-PROG
- **non_claims**：≠ Phase closure
