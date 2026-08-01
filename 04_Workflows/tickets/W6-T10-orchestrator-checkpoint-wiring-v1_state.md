# TICKET STATE · W6-T10 · orchestrator-checkpoint-wiring-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 6 · Agent Standard Line · Checkpoint 接線  
> **票號語境**：本票為 **orchestrator ↔ W6-T5/W6-T6 整合接線**；與藍圖中的 `W6-T10-client-notification-gateway`（S15 notify）**不同票**。

---

## FRAME

- **Title**: W6-T10 · orchestrator-checkpoint-wiring-v1
- **Wave / Motivation**: W6-T4 實驗線 orchestrator 目前 inline checkpoint A/B 邏輯；W6-T5（Checkpoint A）與 W6-T6（Checkpoint B）整合層已交付且 Reviewer accepted。本票將 `scripts/run_agent_standard_case_experiment.py` 改為呼叫 `evaluate_and_maybe_checkpoint_a` / `maybe_create_checkpoint_b`，消除重複、對齊 payload／resume_plan 契約。**不**改主鏈預設。

- **Goal**: Refactor 實驗線 orchestrator 的 S4/S12 checkpoint 路徑，改用 `hitl/checkpoint_a_integration_v1.py` 與 `hitl/checkpoint_b_integration_v1.py` 公開 API；維持既有 CLI 旗標語意（`--auto-approve-intake`、`--auto-approve-delivery`、run path profiles）；unittest 全綠。

- **Scope**:
  1. `scripts/run_agent_standard_case_experiment.py` — 移除／替換 inline `_resolve_checkpoint_a_*`、`_build_checkpoint_a_payload`、dynamic load checkpoint B 等重複邏輯
  2. `tests/test_agent_standard_case_experiment.py` — 更新／追加接線回歸（preview + run + auto-approve 路徑）
  3. `docs/agent-run-standard-case-orchestrator-v1.md` — 最小 cross-ref（§ checkpoint 整合層）
  4. 本票 `*_state.md` B_REPORT

- **NonScope / non_goals**:
  - ❌ 不改 `hitl/checkpoint_a_integration_v1.py` / `checkpoint_b_integration_v1.py` 核心契約（除非發現 blocking bug，須在 B_REPORT 標 deferred 並回報 Orchestrator）
  - ❌ 不改 `scripts/run_mvp_mainline_regression.py`、intake CLI、Local UI
  - ❌ 不實作 S15 client notification gateway
  - ❌ 不擴展 allowlist 至 non-tabular cases
  - ❌ 不接 S8–S10 真實執行（仍 deferred）

- **Minimal Read Set**:
  - `04_Workflows/tickets/W6-T4-agent-run-standard-case-orchestrator-v1_state.md`（C_REPORT gaps）
  - `04_Workflows/tickets/W6-T5-integrate-checkpoint-a-intake-confirmation_state.md`
  - `04_Workflows/tickets/W6-T6-integrate-checkpoint-b-delivery-gate_state.md`
  - `hitl/checkpoint_a_integration_v1.py` · `hitl/checkpoint_b_integration_v1.py`
  - `scripts/run_agent_standard_case_experiment.py`
  - `tests/test_agent_standard_case_experiment.py`

- **AllowedPaths**:
  - `scripts/run_agent_standard_case_experiment.py`
  - `tests/test_agent_standard_case_experiment.py`
  - `docs/agent-run-standard-case-orchestrator-v1.md`
  - `04_Workflows/tickets/W6-T10-orchestrator-checkpoint-wiring-v1_state.md`

- **BlockedPaths / non_scope_paths**:
  - `hitl/checkpoint_a_integration_v1.py` · `hitl/checkpoint_b_integration_v1.py`（預設不修改；bugfix 須 Orchestrator 授權）
  - `scripts/run_mvp_mainline_regression.py` · `scripts/new_cleaning_case.py` · `app/local_ui.py`
  - `routing/*` · `tools/tabular_tool_*`
  - `core/*` · `.github/workflows/*`
  - `04_Workflows/00_Agent_Work_Progress.md` · `docs/WAVE_PROGRESS_DASHBOARD.md`

- **Dependencies**:
  - **W6-T4** · orchestrator CLI baseline
  - **W6-T5** · `evaluate_and_maybe_checkpoint_a` / `maybe_create_checkpoint_a`
  - **W6-T6** · `maybe_create_checkpoint_b` / `delivery_plan_from_checkpoint_b`

- **AcceptanceCriteria**:
  - **AC-1**：run 模式 `needs_review` → 透過 W6-T5 整合層寫入 `outbox/<case_ref>/checkpoint_A-*.json`（行為與 W6-T4 既有測試語意一致或更嚴）
  - **AC-2**：`--auto-approve-intake` → 跳過 Checkpoint A 寫檔，產出 `resume_plan`（W6-T5 契約）
  - **AC-3**：run 模式 output_guard `warning` → 透過 W6-T6 `maybe_create_checkpoint_b` 建 B；`ok`+auto_approve 跳過
  - **AC-4**：preview 模式仍為 `would_pause` / `would_trigger`，不寫 outbox
  - **AC-5**：`tests.test_agent_standard_case_experiment` 全綠；AST／import 檢查未 import 禁改模組
  - **AC-6**：未修改 BlockedPaths 所列主鏈檔案

- **VerificationCommands**:
  - `python -m unittest tests.test_agent_standard_case_experiment -v`
  - （可選）`python scripts/run_agent_standard_case_experiment.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview --format json`
  - （可選）`python scripts/run_agent_standard_case_experiment.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode run --auto-approve-intake --format json`

---

## STATE

- **overall_status**: `accepted_with_gaps_pending_scribe`
- **current_owner**: `scribe`
- **next_action**: Scribe：根據 B_REPORT/C_REPORT 更新 Dashboard/Progress；Orchestrator：決定 follow-up 票
- **last_updated**: 2026-06-15 · orchestrator
- **status_by_role**:
  - orchestrator: `done`
  - implementer: `done`
  - reviewer: `done`
  - scribe: `pending`

---

## B_REPORT

- **changed_files**:
  - `scripts/run_agent_standard_case_experiment.py`
    - S4/S12 改接 W6-T5/W6-T6 公開 API；移除 inline payload/trigger 邏輯與 dynamic load checkpoint B
    - **Issue 1 fix (L632-636)**: `--auto-approve-intake` 時 orchestrator 層級 bypass，不呼叫 `maybe_create_checkpoint_a`，直接回傳 `status=auto_approved` + `bypass_reason`
    - **Issue 2 stable workaround (L647-655)**: `--outbox-root` 在 outbox 於 repo_root 外時，redirect 至 `.temp_test_outbox_area/outbox/`（repo-internal），避免整合層 `relative_to()` ValueError
  - `tests/test_agent_standard_case_experiment.py`
    - 新增 2 個 W6-T10 整合層接線測試（基線 22 項 → 總計 24 項）
    - **Issue 1 test**: `test_auto_approve_intake_does_not_write_checkpoint_a_file` — 驗證 `needs_review` + `auto_approve=True` 不寫檔（經整合層，非 orchestrator bypass）
    - **SSOT cleanup test**: `test_run_mode_auto_approve_intake_resume_plan_via_integration_layer` — 驗證 run mode 經 W6-T5 接線得 `auto_approved` + `resume_plan`，無 `bypass_reason`
    - **Issue 2 test**: `test_custom_outbox_root_with_workaround_writes_checkpoint` — 驗證 custom outbox 於 repo 外部時 redirect 至 repo-internal temp，checkpoint 成功寫入
    - **C_REPORT gap fix**: `test_checkpoint_b_preview_has_integration_layer_field` — 驗證 preview 模式 `checkpoint_b_status` 包含 `integration_layer` 欄位（W6-T10 C_REPORT 小缺口）
  - `docs/agent-run-standard-case-orchestrator-v1.md` — §2 元件表 + W6-T10 checkpoint 整合 cross-ref + Issue 1/2 行為註記

- **artifacts**:
  - orchestrator `checkpoint_a_status.integration_layer` / `checkpoint_b_status.integration_layer` 欄位標示 W6-T5/T6
  - Issue 1: `checkpoint_a_status.bypass_reason` = `"auto_approve_intake_true_skips_checkpoint_a_write"`

- **verification**:
  - `python -m unittest tests.test_agent_standard_case_experiment -v` → **25/25 OK** (22 基線 + 2 follow-up bugfix tests + 1 C_REPORT gap fix)
  - `test_auto_approve_intake_does_not_write_checkpoint_a_file`: `status=auto_approved`, outbox 無 checkpoint 檔案 ✅
  - `test_custom_outbox_root_with_workaround_writes_checkpoint`: `status=written`, repo-internal temp 有 checkpoint 檔案 ✅
  - `test_checkpoint_b_preview_has_integration_layer_field`: preview `checkpoint_b_status.integration_layer=hitl.checkpoint_b_integration_v1` ✅
  - preview CLI smoke: `demo_phase` → `checkpoint_a_status=would_pause`, `integration_layer=hitl.checkpoint_a_integration_v1`
  - run CLI smoke: `--auto-approve-intake` → `checkpoint_a_status=auto_approved`, `final_status=run_complete`

- **behavior_notes**:

  **Issue 1 (SSOT unified — W6-T10-cleanup-orchestrator-auto-approve-ssot-v1)**: `--auto-approve-intake` 時 orchestrator **不再**前置 bypass。路徑：CLI `auto_approve_intake` → `_resolve_checkpoint_a_status(..., delegate_auto_approve=auto_approve_intake and mode=="run")` → `maybe_create_checkpoint_a(..., auto_approve=delegate_auto_approve)` → 整合層回傳 `status=auto_approved`（不寫檔）→ orchestrator 映射 `checkpoint_a_status.integration.status` 與 `resume_plan`。行為 SSOT = 整合層 + `tests/test_checkpoint_a_integration_v1.py`；orchestrator tests 驗證接線繼承。

  **Issue 1 (legacy — superseded)**: ~~orchestrator 在呼叫 W6-T5 前 bypass（L632-636）~~ 已移除。

  **Issue 2 (FIXED via cleanup-v2)**: ~~當使用 `--outbox-root` 指定 repo_root 外部的路徑（如系統 temp dirs for tests）時，orchestrator 將之 redirect 至 repo 內部的 `.temp_test_outbox_area/outbox/`（L647-655）。~~ **已於 cleanup-v2 (2026-06-16) 移除**。orchestrator 現在直接將 `outbox_root_override` 傳遞給 W6-T5/W6-T6 整合層，由整合層的三層 fallback（repo-relative → outbox-relative → absolute）處理外部路徑。這是基於 W6-T5/T6 整合層已修復 `relative_to()` 對外部路徑的 ValueError 問題。orchestrator 的 redirect 程式碼與 LEGACY 註解已移除。測試已更新以驗證直接使用外部 outbox 路徑。

- **deferred_items**:
  - ✅ **Issue 1 FIXED (2026-06-16)**: `--auto-approve-intake=True` with `needs_review` now correctly skips checkpoint file write via orchestrator-level bypass at L632-636. Test: `test_auto_approve_intake_does_not_write_checkpoint_a_file`.
  - ✅ **Issue 2 FIXED via cleanup-v2 (2026-06-16)**: ~~`outbox_root_override` outside repo_root now redirects to `.temp_test_outbox_area/outbox/` under repo to avoid integration layer ValueError.~~ Legacy redirect removed; outbox_root now passed directly to integration layer which handles external paths via three-tier fallback.
  - ✅ **W6-T10-cleanup-orchestrator-checkpoint-workarounds-v1 (2026-06-16, partial)**: Documentation cleanup completed. Issue 2 workarounds marked as LEGACY in code comments (L487-502, L664-682) and test docstring. No runtime behavior change; 24/24 tests pass. Redirect remains for backward compatibility.
  - ✅ **W6-T10-cleanup-v2-remove-legacy-redirect (2026-06-16)**: Removed Issue 2 LEGACY outbox redirect in orchestrator; outbox_root/outbox_root_override now passed through directly to W6-T5/W6-T6 integration layer. External outbox semantics are owned by integration layer three-tier fallback. Updated custom outbox orchestrator tests to assert external outbox is used (no `.temp_test_outbox_area`). All 24 tests pass.
  - ✅ **W6-T10-cleanup-orchestrator-auto-approve-ssot-v1 (2026-06-16)**: Removed orchestrator-level auto-approve bypass (Issue 1 workaround at `_resolve_checkpoint_a_status`). Auto-approve skip semantics SSOT = W6-T5 `maybe_create_checkpoint_a(..., auto_approve=delegate_auto_approve)`; orchestrator only passes `--auto-approve-intake` flag and maps integration result (`status=auto_approved`, no `bypass_reason`). Removed `_can_start_run_execution` would_pause+auto_approve fallback. Tests: `test_run_mode_auto_approve_intake_resume_plan_via_integration_layer` + updated `test_auto_approve_intake_does_not_write_checkpoint_a_file`.
  - **W6-T5-fix-needs-review-auto-approve-skip-v1**（已 superseded by W6-T5 整合層 fix + 本票 SSOT cleanup）: ~~將 Issue 1 的 orchestrator-level bypass 邏輯下移至 W6-T5 整合層~~
  - ✅ **W6-T10-cleanup-v2-remove-legacy-redirect (COMPLETED 2026-06-16)**: 完整移除 Issue 2 的 orchestrator redirect，直接傳 `outbox_root_override` 至整合層，更新測試以使用外部路徑。整合層測試已確認 direct external outbox 行為穩定（`test_custom_outbox_root_outside_repo_writes_checkpoint[_b]` 皆綠）。
  - **W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1**: sandbox e2e 仍用 `can_proceed_sandbox_bundle` 閘門，非完整 `maybe_create_checkpoint_b` 寫檔路徑。
  - **S8–S10 主鏈真實執行、S15 notify gateway**: 仍 out of scope。

---

## C_REPORT

- **reviewer**: C 角色 · Reviewer 收口（2026-06-16）
- **conclusion**: `accepted_with_gaps`
- **blocking_issues**: None
- **checks_summary**:
  - **已讀**：本票 FRAME／B_REPORT；`W6-T4`／`W6-T5`／`W6-T6` state（含 2026-06-16 整合層 bugfix B/C_REPORT）；`scripts/run_agent_standard_case_experiment.py`（`_resolve_checkpoint_a_status` L647–689、`_resolve_checkpoint_b_after_run` L464–516）；`hitl/checkpoint_a_integration_v1.py`（L244–256 auto-approve skip、L276–290 outbox path fallback）；`hitl/checkpoint_b_integration_v1.py`（對稱 fallback）；`tests/test_agent_standard_case_experiment.py`；`tests/test_checkpoint_a_integration_v1.py`（9 項）；`tests/test_checkpoint_b_integration_v1.py`（11 項）；`docs/agent-run-standard-case-orchestrator-v1.md` §2
  - **FRAME AC 對照**：
    - **AC-1 ✅**：run + `needs_review` + 無 `--auto-approve-intake` → orchestrator 呼叫 `maybe_create_checkpoint_a`（`auto_approve=False`）；`test_run_mode_writes_checkpoint_a_when_needed` + `test_checkpoint_a_uses_w6_t5_integration_layer` 確認 `status=written`、`integration_layer=hitl.checkpoint_a_integration_v1`、outbox 有 checkpoint 檔
    - **AC-2 ✅**：`--auto-approve-intake` → orchestrator **前置 bypass**（L652–656）回傳 `status=auto_approved`、`bypass_reason`、不寫檔；run 模式 `_build_resume_plan` 產出 `resume_from=selector` + `planned_tools`；`test_run_mode_auto_approve_intake_resume_plan` + `test_auto_approve_intake_does_not_write_checkpoint_a_file` + B_REPORT CLI smoke 一致。**缺口**：orchestrator 未把 `auto_approve=True` 下傳整合層（L687 固定 `auto_approve=False`）；W6-T5 整合層已內建同等 skip（L244–256，`test_auto_approve_needs_review_skips_checkpoint_file`），形成**雙重 enforcement、SSOT 分裂**
    - **AC-3 ✅**：S12 run → `_resolve_checkpoint_b_after_run` 呼叫 `maybe_create_checkpoint_b` + `should_create_checkpoint_b`；sampleco live `warning` → `integration_layer=hitl.checkpoint_b_integration_v1`、`written|stopped_before_delivery`（`test_sampleco_run_writes_checkpoint_b_via_w6_t6_integration`）；`ok`+`--auto-approve-delivery` 跳過；preview 不寫檔
    - **AC-4 ✅**：preview / `write_state=False` → `would_pause` / `would_trigger`、不呼叫寫檔 API；`test_preview_does_not_write_checkpoint_state_by_default` + CLI preview smoke 一致
    - **AC-5 ✅**：`python -m unittest tests.test_agent_standard_case_experiment -v` → **24/24 OK**（Reviewer 實跑 2026-06-16）；`test_module_does_not_import_forbidden_modules` AST 通過；整合層 `tests.test_checkpoint_a_integration_v1` **9/9 OK**、`tests.test_checkpoint_b_integration_v1` **11/11 OK**
    - **AC-6 ✅**：W6-T10 變更限 AllowedPaths；本票未改 `hitl/*`（整合層 bugfix 屬 W6-T5/T6 另批，非本票 scope 違規）
  - **orchestrator ↔ 整合層分工（現況）**：
    - **已共同滿足 v1 DoD**：S4/S12 改 static import W6-T5/W6-T6 公開 API；移除 inline payload／dynamic load checkpoint B；`checkpoint_*_status.integration_layer` 標記正確；preview 觸發語意委託 `should_trigger_checkpoint_a` / `should_create_checkpoint_b`
    - **Issue 1（auto-approve）**：行為正確（不寫檔 + resume_plan）；**enforcement 仍在 orchestrator bypass**，整合層 capability 已就緒但未接線
    - **Issue 2（outbox_root）**：W6-T5/T6 已修 `checkpoint_path` 三層 fallback（repo-relative → outbox-relative → absolute）；orchestrator **仍保留** repo 外 outbox redirect 至 `.temp_test_outbox_area/outbox/`（L667–681，checkpoint B 同構 L487–501）。`test_custom_outbox_root_with_workaround_writes_checkpoint` 驗證 redirect 路徑；整合層 `test_custom_outbox_root_outside_repo_writes_checkpoint(_b)` 驗證 direct external outbox。**缺口**：redirect 現為冗餘 workaround，external outbox 實際寫入 repo-internal temp 而非 caller 指定路徑
  - **W6-T4 回歸**：allowlist、run path profiles、fixture maturity、sandbox e2e、regression_bundle_probe 等 22 項基線測試仍綠；行為變更限 checkpoint「inline → 整合層」及 preview B `would_trigger` 對齊
- **risk_level**: `low`（實驗線 allowlist + 24 項 orchestrator 測試 + 20 項整合層測試覆蓋；workaround 行為可預測且已文件化；不影響主鏈）
- **deferred_items**（供 Orchestrator 開 follow-up 票）:
  - **W6-T10-cleanup-orchestrator-checkpoint-workarounds-v1**：移除 orchestrator auto-approve bypass 與 outbox redirect；改為 `maybe_create_checkpoint_a/b(..., auto_approve=auto_approve_*)` 並直接傳 `outbox_root_override`；更新 `test_custom_outbox_root_*` docstring（仍描述已修復的 integration bug）
  - **W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1**：sandbox e2e 仍用 `can_proceed_sandbox_bundle` 閘門，非完整 `maybe_create_checkpoint_b` 寫檔路徑
  - **S8–S10 主鏈真實執行、S15 notify gateway**：FRAME NonScope，維持 deferred
  - **小缺口（非阻擋）**：preview `checkpoint_b_status` 未設 `integration_layer`（run path 有）；orchestrator L650–651 註解仍寫「整合層可能寫檔」與 W6-T5 L244–256 現況不符
- **suggestions**:
  - **SSOT 對齊**：後續 orchestrator 行為說明應以 W6-T5/W6-T6 整合層 + 各自 docs 為準；B_REPORT Issue 1/2 的「需另開 W6-T5-fix-* 票」敘述已過時（整合層 fix 已 landed），建議 Scribe/Orchestrator 更新 cross-ref 時註明
  - **優先 follow-up**：`W6-T10-cleanup-orchestrator-checkpoint-workarounds-v1` — 在整合層 fix 穩定後收掉雙重 enforcement 與 redirect，使 `--outbox-root` 語意與 caller 預期一致
  - **文檔／測試衛生**：`test_custom_outbox_root_with_workaround_writes_checkpoint` docstring 仍列 integration layer bug root cause（已修）；cleanup 票一併更正
  - **Orchestrator 建議**：本票 v1 DoD 已滿足，可標 `accepted_with_gaps` 並移交 Scribe；follow-up cleanup 票不阻擋本票收口

---

## D_REPORT

- **docs_updates**:
  - `docs/agent-run-standard-case-orchestrator-v1.md` — §2「Checkpoint integration (W6-T10)」：三段落說明 S4/S12 經 W6-T5/W6-T6 整合層接線、preview 不寫檔／run 依 `needs_review`/`warning|blocked` 寫檔、以及 `auto_approve` bypass 與 `outbox_root` Issue 2 workaround 行為（細節仍見本票 B/C_REPORT behavior_notes）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` — Wave 6 快照表（第 62 行）追加 checkpoint wiring 一句話；Wave 6 詳細段「一句話」補 sandbox/notify out of scope；新增 W6-T10 票列（`accepted_with_gaps` + Issue 1/2 摘要）
  - `04_Workflows/00_Agent_Work_Progress.md` — 文末「2026-06-15 · W6-T10 · orchestrator checkpoint wiring」：Wave 6 由 inline checkpoints 改為 via integration layer，並列四項 deferred
- **progress_entry**: W6-T10 done (`accepted_with_gaps`) — experiment-line orchestrator S4/S12 wired to W6-T5/T6 integration layer; Issue 1 auto-approve bypass & Issue 2 outbox redirect workarounds implemented with tests; integration-layer bugfixes + sandbox e2e + notify remain deferred.
- **followup_suggestions**:
  - **W6-T5-fix-needs-review-auto-approve-skip-v1** — `maybe_create_checkpoint_a` 應在 `decision=needs_review` 且 `auto_approve=True` 時跳過寫檔並回傳 skip/resume_plan，消除 orchestrator 前置 bypass
  - **W6-T5/W6-T6-fix-outbox-root-override-relative-path-v1** — `outbox_root_override` 時 `checkpoint_path` 不應依賴 `dest.relative_to(repo_root)`；支援獨立 outbox 根
  - **W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1** — sandbox e2e 改走完整 `maybe_create_checkpoint_b` 寫檔路徑，取代 `can_proceed_sandbox_bundle` 閘門 alone
  - **小缺口（非阻擋）** — preview `checkpoint_b_status` 補 `integration_layer` 觀測欄位一致性（文檔或後續小票）

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | orchestrator | 起票 FRAME 草稿；與 notify gateway W6-T10 分軌標註 |
| 2026-06-15 | implementer | S4/S12 接 W6-T5/T6 整合 API；unittest 22/22 OK；B_REPORT 填寫 |
| 2026-06-15 | orchestrator | reviewer accepted_with_gaps；等待 Scribe 更新 Wave 6 orchestrator 接線段落 |
| 2026-06-16 | implementer (B_REPORT) | W6-T10 follow-up bugfix 完成統整：Issue 1 (auto-approve 不寫檔) 與 Issue 2 (outbox_root workaround) 已驗證並寫入 B_REPORT。建議 Orchestrator 開立 **W6-T5-fix-needs-review-auto-approve-skip-v1** 與 **W6-T5/W6-T6-fix-outbox-root-override-relative-path-v1** 兩張整合層 bugfix 後續票。 |
| 2026-06-16 | implementer | Issue 2 stable workaround implemented: When custom outbox outside repo_root, redirect to `.temp_test_outbox_area/outbox/` to avoid integration layer ValueError. All 24 tests pass. True fix requires W6-T5/W6-T6 ticket for `dest.relative_to(repo_root)` dependency. |
| 2026-06-16 | implementer (cleanup) | W6-T10-cleanup-orchestrator-checkpoint-workarounds-v1 文件層 cleanup：將 Issue 2 redirect 標註為 LEGACY WORKAROUND（L487-502, L664-682）；更新 test docstring。無 runtime 行為變更，24/24 tests OK。建議後續拆 **W6-T10-cleanup-v2-remove-legacy-redirect** 進行完整移除。 |
| 2026-06-16 | implementer | W6-T10-cleanup-v2-remove-legacy-redirect 完成：移除 orchestrator Issue 2 LEGACY redirect block（Checkpoint A/B），直接傳遞 outbox_root_override 至整合層；更新測試 `test_custom_outbox_root_outside_repo_writes_checkpoint_via_orchestrator` 以驗證 external outbox 行為；24/24 tests OK。 |
| 2026-06-16 | implementer (B role) | **C_REPORT gap fix**: preview 路徑 `_build_checkpoint_b_planned` 補上 `integration_layer: "hitl.checkpoint_b_integration_v1"` 欄位，與 run 路徑一致；新增測試 `test_checkpoint_b_preview_has_integration_layer_field`；25/25 tests OK。 |
| 2026-06-16 | implementer (B role) | **auto-approve SSOT cleanup 完成**（W6-T10-cleanup-orchestrator-auto-approve-ssot-v1）：移除 orchestrator bypass；`auto_approve` 下傳 W6-T5 整合層；26/26 orchestrator tests + 9/9 integration tests OK。 |
