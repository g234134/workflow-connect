# WH-P85-bridge-ci-hardening-v1 — Ticket State

> handoff 摘要檔；P8.5 **bridge Smoke A CI advisory hardening**（doc／workflow 文案對齊）票。  
> 上游：`WH-P85-bridge-run-record-jsonl-v1`（`done_with_gaps` · 本機 **17/17**；CI job 顯示名仍可能寫 14/14）。

---

## FRAME

### Goal

將 advisory `bridge-smoke.yml` Smoke A 顯示名／文案／EXPECTED 敘事從 **14/14** 對齊至 **17/17**（與 `EXPECTED_TEST_COUNT`／runbook 一致）；可選 path-filter 審查與遠端 Smoke A 重跑證據；**仍 advisory**。

### 核心 checklist

- [ ] 更新 `.github/workflows/bridge-smoke.yml` Smoke A job `name`／註解／warning／echo：**14/14 → 17/17**。
- [ ] 對照 path-filter：是否需納入 `orchestration_bridge_run_record.py`（或等價路徑）以免漏跑。
- [ ] （可選）遠端 Smoke A `workflow_dispatch` 重跑 · Progress／B_REPORT 留 `run_id`。
- [ ] （可選）補 OSError／寫入失敗 fail-open 專測（Reviewer gap；非阻塞）。
- [ ] runbook／INDEX 若仍寫 14/14 顯示名處，改為 17/17 或註「CI 對齊後」。

### Non-goals

- ❌ 不升格 required CI／branch protection。
- ❌ 不引入 Playwright · 不改 bridge 核心語意。
- ❌ 不實作 DOM file-backed（→ `WH-P85-bridge-fixture-dom-port-v1`）。
- ❌ 不合併 Phase 8.7e／8.8 outbox。

### AllowedPaths

- `.github/workflows/bridge-smoke.yml`（顯示名／註解／warning 文案 · path-filter）
- `docs/phase8_5-bridge-smoke-runbook-v1.md`（CI 顯示名 cross-ref · 裁決）
- `tests/test_minimal_orchestration_bridge.py`（**僅**可選 fail-open 專測；非本票必做）
- `04_Workflows/tickets/WH-P85-bridge-ci-hardening-v1_state.md`

### BlockedPaths

- bridge 核心邏輯大改、`GOV_BRIDGE_RUN_RECORD_*` 語意變更（除非修 CI 誤導所需之極小註解）
- 憲法／合約／`.env`／venv／DarkOps 禁區類型（見憲法 §7）

### Acceptance Criteria

- **AC-1**：Smoke A CI job 顯示名／主要 echo／warning 文案為 **17/17**（或等價「Ran N tests」與 EXPECTED 一致）。
- **AC-2**：path-filter 審查結論已記（改或明示不改 + 理由）。
- **AC-3**：仍標 **advisory** · ≠ required CI · ≠ Phase closure。

### Dependencies

- 上游：`WH-P85-bridge-run-record-jsonl-v1`（`done_with_gaps` · 本機 17/17）
- 並行：`WH-P85-bridge-fixture-dom-port-v1`（`frame_ready` · 不互阻）

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: none
- **next_action**: closed · gaps 僅註記（遠端 GA／OSError 專測 deferred · **不**另開票）· parallel `WH-P85-bridge-fixture-dom-port-v1` 不動 · **不**回 Implementer
- **last_updated**: 2026-07-13 · Orchestrator 收口 `done_with_gaps`
- **wave**: Wave-P8.5 · wave-H+2 · bridge CI advisory
- **status_by_role**:
  - **Orchestrator (O)**: done — 2026-07-13 開票；2026-07-13 收口 `done_with_gaps` · current_owner=none
  - **Implementer (B)**: done — 2026-07-13 CI 14→17 + path-filter；交 Reviewer
  - **Reviewer (C)**: done — 2026-07-13 `accept_with_gaps`（本機 17/17 · AC-1～3 過；遠端 GA／OSError deferred）
  - **Scribe (D)**: done — 2026-07-13 D_REPORT + Progress 末尾摘要
- **notes**:
  - 源自 Reviewer gaps：CI `bridge-smoke.yml` 仍 14/14 · 遠端 Smoke A 未重跑 · 可選 OSError 專測
  - **不**阻 fixture-dom 並行；**不**回 run-record Implementer
  - ≠ Phase closure · ≠ required CI · ≠ Playwright
  - 2026-07-13 Implementer：本地 CI 文案已 17/17；遠端 `workflow_dispatch`／OSError 專測仍 deferred（非阻塞）
  - 2026-07-13 Reviewer：AC-1～AC-3 本地證據通過；gaps 不阻交棒 Scribe
  - 2026-07-13 Scribe：敘事收口（CI advisory 14→17 · path-filter +run_record · 仍 continue-on-error）；交棒 Orchestrator
  - 2026-07-13 Orchestrator：`accept_with_gaps` → `done_with_gaps`；gaps 註記不另開；QUEUE READY→archive

---

## B_REPORT (Implementer)

- **status**: done_pending_review
- **purpose**: advisory CI 顯示名／path-filter 對齊 17/17。
- **verification**:
  - `cd` gov_core_system → `python -m unittest tests.test_minimal_orchestration_bridge -v` → **Ran 17 tests · OK**（`EXPECTED_TEST_COUNT=17` · discovered=17）
  - workflow text dry-check：`bridge-smoke.yml` 無 `14/14`；job name／warning／echo／dispatch description 均 **17/17**；path-filter 含 `core/orchestration_bridge_run_record.py`
- **files_changed**:
  - `.github/workflows/bridge-smoke.yml` — Smoke A 顯示名／註解／warning／echo／scenario description **14/14→17/17**；PR path-filter **新增** `orchestration_bridge_run_record.py`
  - `docs/phase8_5-bridge-smoke-runbook-v1.md` — Triggers 註記含 run_record；Historical note 改為「CI 已對齊 17/17（本票）」
- **path_filter_decision**: **改** — 納入 `01_Environments/python_venvs/gov_core_system/core/orchestration_bridge_run_record.py`，避免僅改 run-record 模組時 PR 漏跑 Smoke A（與 17 測中 3 條 run-record 測對齊）。
- **deferred**:
  - 遠端 Smoke A `workflow_dispatch` 重跑（無 GA `run_id`）
  - 可選 OSError／寫入失敗 fail-open 專測（Reviewer gap；非本票必做）
- **advisory_note**: 仍 `continue-on-error: true` · ≠ required CI · ≠ Phase closure
- **next**: Reviewer 對照 AC-1～AC-3；Scribe 待 C 通過後收 Progress 摘要

---

## C_REPORT (Reviewer)

- **verdict**: `accept_with_gaps`
- **reviewed_at**: 2026-07-13
- **ac_check**:
  - **AC-1**: PASS — `bridge-smoke.yml` job name／header／dispatch description／warning／echo 均為 **17/17**；dry-check **無**殘留 `14/14`
  - **AC-2**: PASS — path-filter **已改**納入 `core/orchestration_bridge_run_record.py`（B_REPORT 理由成立）
  - **AC-3**: PASS — 四 job 皆 `continue-on-error: true`；workflow 標題仍 `(advisory)`；≠ required CI · ≠ Phase closure
- **evidence**:
  - `python -m unittest tests.test_minimal_orchestration_bridge -v`（cwd=`gov_core_system`）→ **Ran 17 tests in 0.031s · OK**
  - workflow dry-check：`Select-String` 無 `14/14`；path-filter 含 `orchestration_bridge_run_record.py`
  - runbook spot-check：Triggers 含 run_record；Historical note 標本票已對齊 17/17；Smoke A 表列 17/17
- **scope_check**: within AllowedPaths（workflow · runbook · STATE）；未觸 bridge 核心語意／憲法禁區
- **gaps** (non-blocking):
  - 遠端 Smoke A `workflow_dispatch` 未跑 · 無 GA `run_id`
  - 可選 OSError／寫入失敗 fail-open 專測仍 deferred
- **risks**: 無阻交付風險；遠端 CI 文案僅能本機 dry-check 佐證
- **follow_up**: 可選另票補遠端 run_id／OSError 專測；不回 Implementer
- **next**: Scribe 收 Progress／交叉引用摘要；`current_owner=scribe`

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-07-13
- **status**: done
- **verdict_echo**: `accept_with_gaps`（Reviewer 2026-07-13；本機 unittest **17/17 OK**）
- **narrative**:
  - 本票將 advisory `bridge-smoke.yml` Smoke A **顯示名／文案／EXPECTED 敘事**自 **14/14 對齊至 17/17**（與 `EXPECTED_TEST_COUNT`／runbook 一致）。
  - **path-filter 已改**：納入 `core/orchestration_bridge_run_record.py`，避免僅改 run-record 模組時 PR 漏跑 Smoke A。
  - **仍 advisory**：四 job 皆 `continue-on-error: true`；workflow 標題仍 `(advisory)`；≠ required CI · ≠ branch protection · ≠ Phase closure。
  - runbook Triggers／Historical note 已註「CI 已對齊 17/17（本票）」。
- **gaps** (non-blocking · Reviewer):
  - 遠端 Smoke A `workflow_dispatch` 未跑 · 無 GA `run_id`
  - 可選 OSError／寫入失敗 fail-open 專測仍 deferred
- **progress_entry**: `04_Workflows/00_Agent_Work_Progress.md` 末尾 · 2026-07-13 Scribe 條
- **upstream_closed**: `WH-P85-bridge-run-record-jsonl-v1` → `done_with_gaps`
- **parallel**: `WH-P85-bridge-fixture-dom-port-v1`（不互阻）
- **unlocks**:
  - 敘事可寫「Smoke A CI advisory 顯示名 **17/17** · path-filter 含 run_record」
  - Orchestrator 可標 `done_with_gaps` 收口；遠端 GA／OSError 可選另票
- **non_claims**: ≠ Phase % uplift · ≠ Phase closure · ≠ required CI · ≠ Playwright · ≠ 回 Implementer · 無 git commit

---

## APPEND — Implementer 戰報（2026-07-13）

- **ticket**: `WH-P85-bridge-ci-hardening-v1`
- **role**: Implementer (B)
- **result**: 施工完成，待 Reviewer（**不**自稱可交付）
- **summary**: advisory `bridge-smoke.yml` Smoke A 顯示名／文案 **14/14→17/17**；path-filter 納入 `orchestration_bridge_run_record.py`；runbook Historical note／Triggers 對齊。本機 Smoke A **17/17 OK**。遠端 GA 重跑與 OSError 專測 deferred。
- **handoff**: `overall_status=review` · `current_owner=reviewer`

---

## APPEND — Reviewer 戰報（2026-07-13）

- **ticket**: `WH-P85-bridge-ci-hardening-v1`
- **role**: Reviewer (C)
- **verdict**: `accept_with_gaps`
- **summary**: 重跑 Smoke A **17/17 OK**；workflow 無殘留 `14/14`；path-filter 含 `orchestration_bridge_run_record.py`；仍 advisory。AC-1～AC-3 通過。Gaps：遠端 GA 未跑、OSError 專測 deferred（非阻塞）。
- **handoff**: `overall_status=scribe` · `current_owner=scribe` · next=Scribe Progress 收口

---

## APPEND — Scribe 戰報（2026-07-13）

- **ticket**: `WH-P85-bridge-ci-hardening-v1`
- **role**: Scribe (D)
- **verdict_echo**: `accept_with_gaps`
- **summary**: D_REPORT + Progress 末尾摘要已落盤。敘事：CI advisory 文案 **14→17**；path-filter **+run_record**；仍 `continue-on-error`。Gaps：遠端 GA 未跑、OSError 專測 deferred。
- **handoff**: `overall_status=accept_with_gaps` · `current_owner=orchestrator` · next=Orchestrator 收口（`done_with_gaps`）

---

## APPEND — Orchestrator 收口（2026-07-13）

- **ticket**: `WH-P85-bridge-ci-hardening-v1`
- **role**: Orchestrator (O)
- **overall_status**: `accept_with_gaps` → **`done_with_gaps`**（專案慣用閉合；≠ 新詞）
- **current_owner**: **none**
- **roles**: O／B／C／D 皆 **done**；verdict 維持 Reviewer `accept_with_gaps`
- **gaps**（註記 · **不**另開票）:
  - 遠端 Smoke A `workflow_dispatch` 未跑 · 無 GA `run_id`
  - 可選 OSError／寫入失敗 fail-open 專測 deferred（成本／必要性不足 · 預設不開）
- **parallel**：`WH-P85-bridge-fixture-dom-port-v1` **不動**（並行另一條）
- **non_actions**：不回 Implementer · 不改 core／tests／workflow 實體 · 不 git commit
- **QUEUE**：活躍 READY 移除 → `QUEUE.archive.yaml` `DONE_WITH_GAPS`；session note 更新
