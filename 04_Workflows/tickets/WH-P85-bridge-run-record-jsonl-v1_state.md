# WH-P85-bridge-run-record-jsonl-v1 — Ticket State

> handoff 摘要檔；P8.5 **bridge run record jsonl 側車** execution/impl 票。  
> 目的：opt-in 將每次 `run_minimal_orchestration_bridge()` 結構化結果 append 至 repo-relative jsonl run record（可稽核）；bridge 首個 **非純 in-memory** 能力。

---

## FRAME

### Goal

在維持 bridge 核心 `ok` fail-open 語意下，新增 file-backed run record 側車；DOM 仍 in-memory stub，run record 為 optional 持久化。

### 核心 checklist

- [x] 定義 `schema_id=orchestration_bridge_run_v1` 最小欄位（`run_id` · `flow` · `browser.status` · `intake.decision` · timestamp）。
- [x] 新增 env gate `GOV_BRIDGE_RUN_RECORD_ENABLED`（default **0**）；path 預設 `outbox/orchestration_bridge/runs.jsonl`。
- [x] 在 bridge 核心路徑 append 1 行；fail-open（寫入失敗不阻 bridge `ok`）。
- [x] 擴充 unittest：enabled/disabled · append 1 行 · 欄位形狀穩定（既有 14 不退化 · 現 **17/17**）。
- [x] 更新 runbook §Smoke A 註腳：in-memory DOM **仍 stub**，run record 為 **file-backed 側車**。
- [ ] Smoke A CI advisory 遠端重跑（本機 **17/17** 已綠；CI job 顯示名仍可能寫 14/14 · 另票 hardening）。

### Non-goals

- ❌ 不取代 bridge in-memory DOM stub（→ fixture-dom-port 票）。
- ❌ 不引入 Playwright · 不升格 required CI。
- ❌ 不合併 Phase 8.8 orchestration_bridge_outbox（§2.2 分軌）。

### AllowedPaths

- bridge 核心模組（路徑見 `Master_Map.json` · `minimal_orchestration_bridge`）
- `tests/test_minimal_orchestration_bridge.py`（或等價）
- `docs/phase8_5-bridge-smoke-runbook-v1.md`（註腳 cross-ref · Orchestrator 裁決）
- `04_Workflows/tickets/WH-P85-bridge-run-record-jsonl-v1_state.md`

### Acceptance Criteria

- **AC-1**：default off · enabled 時 append 1 行 · schema 穩定。
- **AC-2**：`tests.test_minimal_orchestration_bridge` **14/14 OK**。（**Orchestrator 註記 2026-07-13**：歷史開票數字；實作／runbook／Reviewer 證據已對齊 **17/17** · `EXPECTED_TEST_COUNT=17`；CI 顯示名 14→17 交 `WH-P85-bridge-ci-hardening-v1`）
- **AC-3**：runbook 註腳誠實：DOM stub · run record optional file-backed。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: none
- **next_action**: closed · follow-up `WH-P85-bridge-ci-hardening-v1`（frame_ready）· parallel `WH-P85-bridge-fixture-dom-port-v1` · **不**回 Implementer
- **last_updated**: 2026-07-13 · Orchestrator 收口
- **wave**: Wave-P8.5 · wave-H+2 · bridge non-stub
- **status_by_role**:
  - **Orchestrator (O)**: done — 2026-06-23 開票；2026-07-13 收口 `done_with_gaps` + 開 CI-hardening FRAME
  - **Implementer (B)**: done — run record 側車 + 17/17
  - **Reviewer (C)**: done — `accept_with_gaps` · 2026-07-13
  - **Scribe (D)**: done — D_REPORT + Progress append · 2026-07-13
- **notes**:
  - 本機 `python -m unittest tests.test_minimal_orchestration_bridge -v` → **17/17 OK**（Reviewer 重跑）
  - DOM 仍 in-memory stub；與 **`WH-P85-bridge-fixture-dom-port-v1`** 仍可並行（已存在 · 未重開）
  - gaps 移交：`WH-P85-bridge-ci-hardening-v1`（CI 14→17 顯示名／path-filter／遠端 Smoke A 可選）
  - ≠ Phase closure · ≠ required CI · ≠ Playwright

---

## B_REPORT (Implementer)

- **status**: done
- **purpose**: opt-in bridge run jsonl 持久化側車；fail-open；既有路徑不退化。
- **core_checklist_summary**: schema · env gate · append · unittest · runbook 註腳 · 本機 Smoke A 17/17
- **verification**: `python -m unittest tests.test_minimal_orchestration_bridge -v` → **Ran 17 tests · OK**
- **changed_paths**:
  - `01_Environments/python_venvs/gov_core_system/core/orchestration_bridge_run_record.py`（新建）
  - `01_Environments/python_venvs/gov_core_system/core/minimal_orchestration_bridge.py`（掛 `record_bridge_run`）
  - `01_Environments/python_venvs/gov_core_system/tests/test_minimal_orchestration_bridge.py`（+3 · EXPECTED=17）
  - `docs/phase8_5-bridge-smoke-runbook-v1.md`（Smoke A 17/17 · Non-goals 註腳）
- **gaps**: CI job 顯示名／path-filter 未改（不在本票 AllowedPaths）· 遠端 Smoke A GA 未重跑

---

## C_REPORT (Reviewer)

- **verdict**: `accept_with_gaps`
- **reviewed_at**: 2026-07-13
- **reviewer**: Multi-Chat C / checker-reviewer
- **core**: opt-in `GOV_BRIDGE_RUN_RECORD_ENABLED`（default 0）側車；`schema_id=orchestration_bridge_run_v1`；fail-open；與 8.7e outbox 分軌；DOM 仍 in-memory stub。
- **verification_rerun**: `python -m unittest tests.test_minimal_orchestration_bridge -v` → **Ran 17 tests · OK**
- **scope_ok**: true（AllowedPaths 內）
- **dod**:
  - context_source: true
  - incremental_honest: true
  - debugging_evidence: true
  - no_forbidden_zone: true
- **gaps**:
  1. CI `bridge-smoke.yml` job 顯示名／文案仍 **14/14**（另票 `WH-P85-bridge-ci-hardening-v1`）
  2. 遠端 Smoke A GA 未重跑
  3. DOM file-backed 非本票（`WH-P85-bridge-fixture-dom-port-v1`）
  4. FRAME **AC-2** 仍寫 14/14（checklist／runbook／EXPECTED=17 已對齊；FRAME 凍結由 Orchestrator 修或註記）
  5. 無專測 OSError fail-open 路徑（實作有 try/except；可選 hardening）
  6. Progress append 交 Scribe（本輪完成）
- **risks**: CI 顯示名與實際 17/17 不一致，易誤判；非功能回歸風險。
- **next**: Scribe（D）— Progress／敘事；Orchestrator 可開 CI-hardening；**不**回 Implementer。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-07-13
- **status**: done
- **verdict_echo**: `accept_with_gaps`（Reviewer 2026-07-13；本機 unittest **17/17 OK**）
- **narrative**:
  - 本票交付 **opt-in** bridge run-record JSONL 側車：`GOV_BRIDGE_RUN_RECORD_ENABLED` default **off**；啟用時 append `schema_id=orchestration_bridge_run_v1` 一行至 repo-relative jsonl。
  - **fail-open**：寫入失敗不阻 bridge 核心 `ok`。
  - 與 Phase **8.7e** orchestration_bridge_outbox **分軌**；本票不合併 outbox 路徑。
  - **DOM 仍 in-memory stub**；file-backed DOM 屬 `WH-P85-bridge-fixture-dom-port-v1`，非本票 scope。
  - Reviewer gaps：CI 顯示名仍 14/14、遠端 Smoke A 未重跑、FRAME AC-2 仍寫 14/14、OSError fail-open 無專測（可選）。
- **progress_entry**: `04_Workflows/00_Agent_Work_Progress.md` 末尾 · 2026-07-13 Scribe 條
- **unlocks**:
  - 敘事可寫「DOM in-memory · run record file-backed optional」（非 Phase closure）
  - Orchestrator 可開／推進 `WH-P85-bridge-ci-hardening-v1`；fixture-dom 並行
- **parallel**: `WH-P85-bridge-fixture-dom-port-v1`
- **non_claims**: ≠ Phase % uplift · ≠ Phase closure · ≠ required CI · ≠ Playwright · ≠ 回 Implementer

---
## Reviewer append · 2026-07-13
- C_REPORT verdict: **accept_with_gaps**
- evidence: unittest **17/17 OK**（Reviewer 重跑）
- next_owner: **scribe**
- next_action: D_REPORT + Progress 末尾摘要；CI 14→17 顯示名另票

---
## Scribe append · 2026-07-13
- D_REPORT + Progress 末尾摘要已落盤
- overall_status: **accept_with_gaps**
- next_owner: **orchestrator**
- next_action: 可開 CI-hardening；fixture-dom 並行；**不**回 Implementer

---
## Orchestrator append · 2026-07-13 · 收口
- **overall_status**: `accept_with_gaps` → **`done_with_gaps`**（專案慣用閉合；≠ `closed_accept_with_gaps` 新詞）
- **current_owner**: **none**
- **roles**: O／B／C／D 皆 **done**；verdict 維持 Reviewer `accept_with_gaps`；gaps 已記並移交
- **FRAME AC-2**：註記歷史 14/14 已由 17/17 證據 supersede（見 STATE／AcceptanceCriteria 註）
- **follow-up 開票**：`WH-P85-bridge-ci-hardening-v1` → `frame_ready`（CI 顯示名 14→17 · path-filter · 可選遠端 Smoke A）
- **parallel**：`WH-P85-bridge-fixture-dom-port-v1` 已存在（`frame_ready`）· **未重開**
- **non_actions**：不回 Implementer 修本票核心 · 不改 core／tests · 不 git commit
- **QUEUE**：session note + archive `DONE_WITH_GAPS` + hardening 入活躍 queue（`READY` · 非 `priority_next`）
