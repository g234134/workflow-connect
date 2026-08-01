# WH-P85-bridge-ci-hardening-v2 — Ticket State

> handoff 摘要檔；P8.5 **bridge Smoke A CI advisory hardening v2**（顯示名／文案 **17→20**）票。  
> 上游：`WH-P85-bridge-fixture-dom-port-v1`（`done_with_gaps` · 本機／`EXPECTED_TEST_COUNT`／runbook 權威 **20**）。  
> **≠** 重開 `WH-P85-bridge-ci-hardening-v1`（該票已 `done_with_gaps` · 對齊至 **17**）。

---

## FRAME

### Goal

將 advisory `bridge-smoke.yml` Smoke A 顯示名／文案／EXPECTED 敘事從 **17/17** 對齊至 **20/20**（與 fixture-dom 後 `EXPECTED_TEST_COUNT`／runbook 一致）；審查 path-filter 是否需納入 `tests/fixtures/browser_dom/**`（或等價）；**仍 advisory**。

### 核心 checklist

- [ ] 更新 `.github/workflows/bridge-smoke.yml` Smoke A job `name`／註解／warning／echo／dispatch description：**17/17 → 20/20**。
- [ ] 對照 path-filter：是否需納入 `tests/fixtures/browser_dom/**`（或等價路徑）以免僅改 DOM fixture 時漏跑 Smoke A；記「改或明示不改 + 理由」。
- [ ] runbook 若仍寫 CI 顯示名 **17/17** 處，改為 **20/20** 或註「CI 對齊後（本票）」。
- [ ] （可選）遠端 Smoke A `workflow_dispatch` 重跑 · Progress／B_REPORT 留 `run_id`（非阻塞）。

### Non-goals

- ❌ 不升格 required CI／branch protection。
- ❌ 不引入 Playwright · 不改 bridge／DOM port 核心語意。
- ❌ 不重開／改寫已收口的 `WH-P85-bridge-ci-hardening-v1`。
- ❌ 不合併 Phase 8.7e／8.8 outbox · 不改 `EXPECTED_TEST_COUNT` 測試本體（權威已 20）。

### AllowedPaths

- `.github/workflows/bridge-smoke.yml`（顯示名／註解／warning／echo／dispatch 文案 · path-filter）
- `docs/phase8_5-bridge-smoke-runbook-v1.md`（CI 顯示名 cross-ref · Historical／Triggers 裁決）
- `04_Workflows/tickets/WH-P85-bridge-ci-hardening-v2_state.md`

### BlockedPaths

- `core/*`、`tests/*`（含改測／改 EXPECTED 本體；本票僅 CI／runbook 顯示對齊）
- 憲法／合約／`.env`／venv／DarkOps 禁區類型（見憲法 §7）
- 重開或覆寫 `WH-P85-bridge-ci-hardening-v1_state.md` 為 in_progress

### Acceptance Criteria

- **AC-1**：Smoke A CI job 顯示名／主要 echo／warning／dispatch 文案為 **20/20**（或等價「Ran N tests」與 EXPECTED 一致）；workflow 無殘留誤導性 **17/17**（Smoke A 語境）。
- **AC-2**：path-filter 審查結論已記（改或明示不改 + 理由；建議關注 `tests/fixtures/browser_dom/**`）。
- **AC-3**：仍標 **advisory** · ≠ required CI · ≠ Phase closure。

### Dependencies

- 上游：`WH-P85-bridge-fixture-dom-port-v1`（`done_with_gaps` · 本機 A **20/20**）
- 前代（已收口 · **勿重開**）：`WH-P85-bridge-ci-hardening-v1`（`done_with_gaps` · 對齊至 17）

### relay_mode

`same_chat`（doc／workflow 文案對齊 · 估計 1 循環）

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: none
- **next_action**: closed · gaps 僅註記（遠端 GA `run_id` deferred · **不**另開票）· **不**回 Implementer
- **last_updated**: 2026-07-13 · Orchestrator 收口 `done_with_gaps`
- **wave**: Wave-P8.5 · wave-H+2 · bridge CI advisory
- **status_by_role**:
  - **Orchestrator (O)**: done — 2026-07-13 開票 FRAME · QUEUE READY；2026-07-13 收口 `done_with_gaps` · current_owner=none
  - **Implementer (B)**: done — 2026-07-13 對齊 17→20 + path-filter；交 C
  - **Reviewer (C)**: done — 2026-07-13 `accepted_with_gaps` · AC-1～AC-3 本機／檔案綠
  - **Scribe (D)**: done — 2026-07-13 D_REPORT + Progress 末尾
- **notes**:
  - 源自 fixture-dom Reviewer gap：CI 仍 **17** · 權威已 **20**
  - **新開 v2**；v1 gaps（遠端 GA／OSError）仍 deferred · 本票可不重做
  - ≠ Phase closure · ≠ required CI · ≠ Playwright · **不**入 `priority_next`（慣例 human 維持）
  - C 驗收：Smoke A **20/20** 文案齊 · path-filter 含 `browser_dom/**` · 仍 advisory；遠端 `workflow_dispatch` 可選 deferred
  - 2026-07-13 Scribe：敘事收口（CI／runbook 顯示名 **17→20** · path-filter **+browser_dom** · 仍 advisory）；交棒 Orchestrator
  - 2026-07-13 Orchestrator：`accepted_with_gaps` → `done_with_gaps`；遠端 GA 僅註記不另開；QUEUE READY→archive

---

## B_REPORT (Implementer)

### 任務／角色／日期
- **ticket**: `WH-P85-bridge-ci-hardening-v2`
- **role**: Implementer (B)
- **date**: 2026-07-13
- **verdict**: 施工完成，待 checker／Reviewer（**不**自稱可交付）

### §1 變更檔案
- `.github/workflows/bridge-smoke.yml` — Smoke A 註解／dispatch／job `name`／warning／echo：**17/17 → 20/20**；path-filter **新增** `tests/fixtures/browser_dom/**`
- `docs/phase8_5-bridge-smoke-runbook-v1.md` — CI 顯示名 cross-ref **20/20**；Triggers 註 browser_dom；Historical note 改為 v2 已對齊
- `04_Workflows/tickets/WH-P85-bridge-ci-hardening-v2_state.md` — STATE → `review` · B_REPORT

### §2 skeleton
- 無

### §3 placeholder
- 無（遠端 `workflow_dispatch` 重跑可選 · 未執行 · 非阻塞）

### §4 驗證證據
- `python -m unittest tests.test_minimal_orchestration_bridge -v`（cwd: `gov_core_system`）→ **Ran 20 tests · OK**
- dry-check：`.github/workflows/bridge-smoke.yml` **無**殘留 Smoke A **17/17**；runbook 無「CI 仍寫 17/17」誤導句（Historical 僅保留歷史敘事）

### §5 阻塞
- 無

### §6 下一步
- 交 Reviewer（C）對照 AC-1～AC-3
- （可選）遠端 Smoke A `workflow_dispatch` 留 `run_id`（deferred／non-blocking）

### §7 override／留痕
- 無憲法／合約 override
- path-filter **已改**：納入 `01_Environments/python_venvs/gov_core_system/tests/fixtures/browser_dom/**` — 理由：fixture-dom 後僅改 DOM fixture 也應觸發 Smoke A advisory
- **仍 advisory**（`continue-on-error: true`）· ≠ required CI · ≠ Phase closure
- 未改 v1 票檔 · 未改 `core/*`／`tests/*` 邏輯 · 未 git commit

### path-filter 審查結論（AC-2）
- **改**：新增 `tests/fixtures/browser_dom/**` 於 `pull_request.paths`
- **理由**：上游 fixture-dom 權威依賴該目錄；僅改 HTML fixture 時若未列入 path-filter 會漏跑 Smoke A

### gaps / deferred
- 遠端 GA Scenario 1 重跑 `run_id`（可選 · 非本票阻塞）
- v1 deferred（遠端 GA／OSError）**不**重做

---

## APPEND — Implementer B_REPORT（2026-07-13）

- **ticket**: `WH-P85-bridge-ci-hardening-v2`
- **role**: Implementer (B)
- **action**: CI／runbook 顯示名 **17→20** + path-filter 納入 `browser_dom/**`
- **verify**: unittest **20 OK** · workflow 無殘留 Smoke A **17/17**
- **handoff**: STATE=`review` · owner=`reviewer`

---

## C_REPORT (Reviewer)

### 任務／角色／日期
- **ticket**: `WH-P85-bridge-ci-hardening-v2`
- **role**: Reviewer (C)
- **date**: 2026-07-13
- **conclusion**: `accepted_with_gaps`
- **risk_level**: low

### checks_summary（對照 FRAME AC）
- **AC-1** ✅：`.github/workflows/bridge-smoke.yml` Smoke A job `name`／註解／dispatch description／warning／echo 均為 **20/20**；workflow 全文 **無**殘留 `17`／`17/17`（Smoke A 語境）。runbook 現行表／Scenario／Triggers 為 **20/20**；Historical note 僅保留歷史 **17/17** 敘事並明示 v2 已對齊（非誤導現行 CI）。
- **AC-2** ✅：path-filter **已改** — `pull_request.paths` 含 `01_Environments/python_venvs/gov_core_system/tests/fixtures/browser_dom/**`；理由與 B_REPORT 一致（僅改 DOM fixture 亦應觸發 Smoke A）。
- **AC-3** ✅：workflow／runbook 仍標 **advisory**；`continue-on-error: true`；≠ required CI · ≠ Phase closure。
- **邊界**：變更落在 AllowedPaths；未改 `core/*`／`tests/*` 邏輯；未重開 v1 票檔（Rule 3／8）。
- **Rule 11**：B_REPORT 驗證可重跑；C 本輪重跑通過。

### 驗證證據（C 重跑）
- `python -m unittest tests.test_minimal_orchestration_bridge -v`（cwd: `gov_core_system`）→ **Ran 20 tests in 0.056s · OK**
- dry-check：`bridge-smoke.yml` 無 `17`；`browser_dom/**` 在 path-filter；runbook Triggers 含 `tests/fixtures/browser_dom/**`

### blocking_issues
- 無

### gaps / deferred（非阻塞）
- 遠端 Smoke A `workflow_dispatch`／GA `run_id`（FRAME 可選 · 未執行）— **不**阻擋 scribe／關票
- v1 deferred（遠端 GA／OSError）**不**重做

### suggestions
- Scribe：Progress 末尾註「CI／runbook 顯示名 17→20 + path-filter browser_dom · 仍 advisory · 遠端 GA deferred」
- 無必須改 workflow／runbook 實體（本輪僅 STATE）

### §7 override／留痕
- 無憲法／合約 override
- 依尚書省本輪指令：C 寫入 C_REPORT **並**更新 STATE handoff → scribe（`accepted_with_gaps`）

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-07-13
- **status**: done
- **verdict_echo**: `accepted_with_gaps`（Reviewer 2026-07-13；本機 unittest **20/20 OK**）
- **narrative**:
  - 本票將 advisory `bridge-smoke.yml` Smoke A **顯示名／文案／EXPECTED 敘事**自 **17/17 對齊至 20/20**（與 fixture-dom 後 `EXPECTED_TEST_COUNT`／runbook 權威一致）。
  - **path-filter 已改**：納入 `tests/fixtures/browser_dom/**`（repo 相對路徑見 workflow），避免僅改 DOM fixture 時 PR 漏跑 Smoke A。
  - **仍 advisory**：`continue-on-error: true`；≠ required CI · ≠ branch protection · ≠ Phase closure。
  - runbook 現行表／Triggers／Historical note 已對齊「CI 顯示名 **20/20**（本票 v2）」；Historical 僅保留歷史 **17/17** 敘事。
- **gaps** (non-blocking · Reviewer):
  - 遠端 Smoke A `workflow_dispatch` 未跑 · 無 GA `run_id`（FRAME 可選 · deferred）
  - v1 deferred（遠端 GA／OSError）**不**重做
- **progress_entry**: `04_Workflows/00_Agent_Work_Progress.md` 末尾 · 2026-07-13 Scribe 條
- **upstream_closed**: `WH-P85-bridge-fixture-dom-port-v1` → `done_with_gaps`
- **predecessor_closed**: `WH-P85-bridge-ci-hardening-v1` → `done_with_gaps`（對齊至 17 · **勿重開**）
- **unlocks**:
  - 敘事可寫「Smoke A CI advisory 顯示名 **20/20** · path-filter 含 `browser_dom/**`」
  - Orchestrator 可標 `done_with_gaps` 收口；遠端 GA 僅註記
- **non_claims**: ≠ Phase % uplift · ≠ Phase closure · ≠ required CI · ≠ Playwright · ≠ 回 Implementer · 無 git commit · 無新開票

---

## APPEND — Orchestrator 開票（2026-07-13）

- **ticket**: `WH-P85-bridge-ci-hardening-v2`
- **role**: Orchestrator (O)
- **action**: 新開 FRAME（**不**重開 v1）
- **scope**: 僅 `.github/workflows/bridge-smoke.yml` + runbook 顯示名／文案 **17→20**；path-filter 審查註記
- **QUEUE**: **READY** · **不**改 `priority_next`
- **upstream_closed**: `WH-P85-bridge-fixture-dom-port-v1` → `done_with_gaps`

---

## APPEND — Reviewer C_REPORT（2026-07-13）

- **ticket**: `WH-P85-bridge-ci-hardening-v2`
- **role**: Reviewer (C)
- **conclusion**: `accepted_with_gaps`
- **verify**: unittest **20 OK** · workflow 無殘留 Smoke A **17/17** · path-filter 含 `browser_dom/**` · 仍 advisory
- **gaps**: 遠端 GA `run_id` deferred（非阻塞）
- **handoff**: STATE=`scribe` · owner=`scribe` · 未改 workflow／runbook 實體 · 未 git commit

---

## APPEND — Scribe 戰報（2026-07-13）

- **ticket**: `WH-P85-bridge-ci-hardening-v2`
- **role**: Scribe (D)
- **verdict_echo**: `accepted_with_gaps`
- **summary**: D_REPORT + Progress 末尾摘要已落盤。敘事：CI／runbook 顯示名 **17→20**；path-filter **+browser_dom**；仍 advisory。Gaps：遠端 GA deferred（非阻塞 · 不另開票）。
- **handoff**: `overall_status=accepted_with_gaps` · `current_owner=orchestrator` · next=Orchestrator 收口（`done_with_gaps`）

---

## APPEND — Orchestrator 收口（2026-07-13）

- **ticket**: `WH-P85-bridge-ci-hardening-v2`
- **role**: Orchestrator (O)
- **overall_status**: `accepted_with_gaps` → **`done_with_gaps`**（專案慣用閉合；≠ 新詞）
- **current_owner**: **none**
- **roles**: O／B／C／D 皆 **done**；verdict 維持 Reviewer `accepted_with_gaps`
- **gaps**（註記 · **不**另開票）:
  - 遠端 Smoke A `workflow_dispatch` 未跑 · 無 GA `run_id`
  - v1 deferred（遠端 GA／OSError）**不**重做
- **non_actions**：不回 Implementer · 不改 core／tests／workflow 實體 · 不 git commit · 不開無謂新票
- **QUEUE**：活躍 READY 移除 → `QUEUE.archive.yaml` `DONE_WITH_GAPS`；session note 更新
