# WH-P85-bridge-fixture-dom-port-v1 — Ticket State

> handoff 摘要檔；P8.5 **file-backed DOM fixture port** execution/impl 票。  
> 目的：`browser_runner` 支援從 fixture 檔載入初始 DOM snapshot（`DomAutomationPort` file-backed），取代全 inline 建樹；**不引入 Playwright**。

---

## FRAME

### Goal

第二個 non-stub 能力：plan/bridge request 可引用 repo-relative DOM fixture；未設則維持 InMemory 行為；HTTP Smoke B **7/7** 不退化。

### 核心 checklist

- [ ] 新增 `tests/fixtures/browser_dom/` HTML snapshot（≥1 happy · 1 negative）。
- [ ] Plan 或 bridge request 支援 `dom_fixture_ref`（repo-relative）；未設則維持 InMemory 行為。
- [ ] 實作 file load port；`run_plan` 結果 dict 形狀不變。
- [ ] 新增 unittest ≥3（load ok · missing fixture fail-closed · regression 既有 14/14）。
- [ ] 更新 P85-T1 fixture smoke 索引；runbook 補「fixture DOM vs in-memory」對照表。
- [ ] HTTP Smoke B **7/7** 回歸。

### Non-goals

- ❌ 不引入 Playwright / 真 browser CI。
- ❌ 不升格 Smoke C 為 CI job。
- ❌ 不改 advisory CI required 語意。

### AllowedPaths

- `browser_runner` / bridge 相關模組（見 `Master_Map.json`）
- `tests/fixtures/browser_dom/**`
- `tests/test_minimal_orchestration_bridge.py` · `tests/test_app_api_orchestration_bridge.py`
- `docs/phase8_5-bridge-smoke-runbook-v1.md`（對照表 · 裁決）
- `04_Workflows/tickets/WH-P85-bridge-fixture-dom-port-v1_state.md`

### Acceptance Criteria

- **AC-1**：`dom_fixture_ref` load ok · missing fail-closed · dict 形狀不變。
- **AC-2**：**14/14 + 7/7** 回歸綠。
- **AC-3**：runbook 對照表已更新。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: none
- **next_action**: closed · follow-up **`WH-P85-bridge-ci-hardening-v2`**（CI 顯示名 **17→20** · **新開** · **不**重開已 done 的 v1）· **不**回 Implementer
- **last_updated**: 2026-07-13 · Orchestrator 收口 `done_with_gaps`
- **wave**: Wave-P8.5 · wave-H+2 · bridge non-stub
- **status_by_role**:
  - **Orchestrator (O)**: done — 2026-06-23 開票；2026-07-13 收口 `done_with_gaps` · current_owner=none · 開 v2 FRAME
  - **Implementer (B)**: done — 2026-07-13 file-backed DOM port
  - **Reviewer (C)**: done — 2026-07-13 `accept_with_gaps`（本機 A 20/20 · B 7/7 · runner 14/14）
  - **Scribe (D)**: done — 2026-07-13 D_REPORT + Progress 末尾
- **notes**:
  - 上游 **`WD-P85-T1`** browser fixture smoke
  - 為未來 Playwright adapter 留 port 注入點
  - **≠** `orchestration_bridge_run_record`／8.7e outbox（分軌）
  - CI display 名仍 **17/17**；權威本機／runbook／`EXPECTED_TEST_COUNT` 已 **20** → 續票 **`WH-P85-bridge-ci-hardening-v2`**（**勿**重開 `…-v1`）
  - 2026-07-13 Orchestrator：`accept_with_gaps` → `done_with_gaps`；QUEUE 歸檔；開 v2 frame_ready／READY

---

## B_REPORT (Implementer)

- **status**: done — handoff to reviewer
- **purpose**: file-backed DOM fixture port；維持 InMemory fallback；Smoke A/B 回歸。
- **core_checklist_summary**: browser_dom fixtures · dom_fixture_ref · file load · ≥3 unittest · runbook 對照 · Smoke A **20/20** · B **7/7**
- **verification**:
  - `Scripts\python.exe -m unittest tests.test_minimal_orchestration_bridge -v` → **20/20 OK**（cwd=`gov_core_system`）
  - `Scripts\python.exe -m unittest tests.test_app_api_orchestration_bridge -v` → **7/7 OK**
  - `Scripts\python.exe -m unittest tests.test_browser_runner -v` → **14/14 OK**（回歸）
- **files_changed**:
  - `core/browser_runner.py` — `load_dom_fixture_html` · navigate 解析 `dom_fixture_ref`
  - `core/browser_actions.py` — step/plan `dom_fixture_ref`
  - `core/schemas/orchestration_bridge.py` — `BrowserBridgeSection.dom_fixture_ref`
  - `core/minimal_orchestration_bridge.py` — bridge → plan ref 合併
  - `tests/fixtures/browser_dom/**` — happy + negative HTML + README
  - `tests/test_minimal_orchestration_bridge.py` — +3 tests · `EXPECTED_TEST_COUNT=20`
  - `tests/fixtures/orchestration_bridge/README.md` — 索引交叉引用
  - `docs/phase8_5-bridge-smoke-runbook-v1.md` — Fixture DOM vs in-memory 對照表 · Smoke A=20
- **skeleton**: 無（Playwright adapter 仍為未來票；本票僅 file load + InMemory port）
- **placeholder**: 無
- **gaps / deferred**:
  - CI Actions display name 仍可能顯示 17/17（本票 **不改** `bridge-smoke.yml`）
  - `negative_sparse.html` 已落檔；本票負向驗收以 **missing ref fail-closed** 為準（未另開 sparse 互動失敗測）

---

## C_REPORT (Reviewer)

- **verdict**: `accept_with_gaps`
- **reviewed_at**: 2026-07-13
- **evidence**:
  - Smoke A `tests.test_minimal_orchestration_bridge` → **20/20 OK**
  - Smoke B `tests.test_app_api_orchestration_bridge` → **7/7 OK**
  - `tests.test_browser_runner` → **14/14 OK**
- **AC**:
  - AC-1 PASS — load ok · missing fail-closed · dict 形狀
  - AC-2 PASS — 20/20 + 7/7（+ runner 14/14 回歸）
  - AC-3 PASS — runbook Fixture DOM vs in-memory 對照表
- **scope_check**: within AllowedPaths；未引入 Playwright；≠ run-record／8.7e
- **gaps**:
  - CI `bridge-smoke.yml` 顯示名／文案仍 **17/17**；權威已 **20** — 建議另票 ci-hardening 跟顯示名
  - `negative_sparse.html` 無專測（非阻塞）
- **risks**: CI 顯示與本機 EXPECTED 不一致易誤判（advisory 非 required）
- **next**: owner → scribe；Progress 摘要；CI 17→20 另票

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-07-13
- **status**: done
- **verdict_echo**: `accept_with_gaps`（Reviewer 2026-07-13；Ask 模式由父 agent 代落盤 C_REPORT）
- **narrative**:
  - 本票交付 **file-backed** DOM fixture port：`dom_fixture_ref`（repo-relative）可載入 `tests/fixtures/browser_dom/**`；未設則維持 **InMemory**；inline 仍可用。
  - **fail-closed**：missing fixture → 失敗關閉；**不**引入 Playwright／真 browser CI。
  - 驗證：Smoke A **20/20** · Smoke B **7/7** · `tests.test_browser_runner` **14/14**。
  - runbook 已補「Fixture DOM vs in-memory」對照表；≠ run-record／8.7e outbox（分軌）。
  - **gap（非阻塞）**：CI `bridge-smoke.yml` 顯示名／文案仍 **17/17**；權威本機／runbook／`EXPECTED_TEST_COUNT` 已 **20** — 建議 Orchestrator 開／續 `WH-P85-bridge-ci-hardening` 對齊 **17→20**（本票**不**改 CI yml／core）。
  - `negative_sparse.html` 已落檔但無專測（Reviewer 標非阻塞）。
- **gaps** (non-blocking · Reviewer):
  - CI 顯示 **17 ≠ 20**（建議另票）
  - `negative_sparse.html` 無專測
- **progress_entry**: `04_Workflows/00_Agent_Work_Progress.md` 末尾 · 2026-07-13 Scribe 條
- **depends_on**: `WD-P85-T1` · bridge runner／Smoke B 基線
- **parallel**: `WH-P85-bridge-run-record-jsonl-v1`（已 done_with_gaps）· `WH-P85-bridge-ci-hardening-v1`（已 done_with_gaps · 當時對齊至 17）
- **unlocks**:
  - 敘事可寫「DOM file-backed · `dom_fixture_ref` · fail-closed · inline 仍可用」
  - Orchestrator 可標 `done_with_gaps`；CI **17→20** 顯示名另票／續 hardening
- **non_claims**: ≠ Phase % uplift · ≠ Phase closure · ≠ required CI · ≠ Playwright · ≠ 本票改 CI yml · 無 git commit

---

## APPEND — Implementer 戰報（2026-07-13）

- **角色**：Implementer (B)
- **結果**：施工完成，待 Reviewer（**不**宣稱可交付）
- **AC**：
  - AC-1 PASS — `dom_fixture_ref` load ok · missing fail-closed · `run_plan` dict 形狀不變
  - AC-2 PASS — Smoke A **20/20** · Smoke B **7/7**（FRAME 原文 14/14 為歷史基線；權威數見 runbook / `EXPECTED_TEST_COUNT`）
  - AC-3 PASS — runbook「Fixture DOM vs in-memory」對照表已寫
- **override**：無（未觸憲法 §7 禁區；未改 CI yml）
- **下一步**：Reviewer 唯讀驗收 → C_REPORT；Scribe 收 Progress／索引

---
## Reviewer append · 2026-07-13
- C_REPORT verdict: **accept_with_gaps**
- evidence: A20 / B7 / runner14 OK（Ask 模式由父 agent 代落盤）
- next_owner: **scribe**

---
## Scribe append · 2026-07-13
- D_REPORT + Progress 末尾摘要已落盤
- overall_status: **accept_with_gaps**
- current_owner: **orchestrator**
- next_action: 裁決收口（`done_with_gaps`）；建議開／續 `WH-P85-bridge-ci-hardening` 對齊 CI **17→20**；**不**回 Implementer · **不**本票改 CI／core · 無 git commit

---
## APPEND — Orchestrator 收口（2026-07-13）

- **ticket**: `WH-P85-bridge-fixture-dom-port-v1`
- **role**: Orchestrator (O)
- **overall_status**: `accept_with_gaps` → **`done_with_gaps`**（專案慣用閉合）
- **current_owner**: **none**
- **roles**: O／B／C／D 皆 **done**；verdict 維持 Reviewer `accept_with_gaps`
- **evidence**: Smoke A **20/20** · B **7/7** · runner **14/14**
- **gaps**（註記 · 另開續票）:
  - CI `bridge-smoke.yml` 顯示名／文案仍 **17/17**；權威已 **20** → **`WH-P85-bridge-ci-hardening-v2`**（**新開** · **不**重開已 `done_with_gaps` 的 v1）
  - `negative_sparse.html` 無專測（非阻塞 · 預設不開）
- **follow_up**: `WH-P85-bridge-ci-hardening-v2` · `frame_ready`／QUEUE **READY** · **不**入 `priority_next`
- **non_actions**：不回 Implementer · 不改 core／tests／workflow 實體 · 不 git commit
- **QUEUE**：本票 → `QUEUE.archive.yaml` `DONE_WITH_GAPS`（活躍 READY 無此列則僅歸檔）
