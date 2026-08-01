# TICKET STATE · W11-T2 · non-tabular-lightweight-content-checks-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- **Goal**: 在 Non-Tabular shadow preview 流程引入 metadata-only 輕量內容檢查（檔案枚舉、大小/數量、擴展名分布、檔名 pattern hints），不讀取檔案內容、不執行 OCR / log parser。

- **Scope**:
  1. `tools/non_tabular_lightweight_inspector_v1.py` → `inspect_non_tabular_case_dir()`
  2. `scripts/run_non_tabular_experiment_preview.py` 整合 `content_summary`（S4_lite）
  3. 更新 `docs/non-tabular-orchestrator-preview-v1.md`
  4. unittest：`tests/test_non_tabular_lightweight_inspector_v1.py` · 擴充 orchestrator preview 測試
  5. WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引

- **NonScope**:
  - ❌ heavy tools（OCR、全文 parser）
  - ❌ 讀取檔案實際內容
  - ❌ Tabular 主 outbox / 主鏈改動

- **AllowedPaths**:
  - `tools/non_tabular_lightweight_inspector_v1.py`
  - `scripts/run_non_tabular_experiment_preview.py`
  - `docs/non-tabular-orchestrator-preview-v1.md`
  - `tests/test_non_tabular_lightweight_inspector_v1.py`
  - `tests/test_non_tabular_orchestrator_preview_v1.py`
  - `04_Workflows/tickets/W11-T2-non-tabular-lightweight-content-checks-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`

- **AcceptanceCriteria**:
  - [AC-1] `inspect_non_tabular_case_dir` 回傳 file_count / total_size / extension_distribution
  - [AC-2] preview orchestrator 輸出含 `content_summary`；sandbox outbox 同步寫入
  - [AC-3] 僅 stat/path metadata；unittest 驗證不呼叫 `open()` 讀內容
  - [AC-4] NT-A / NT-B fake fixture 測試全綠
  - [AC-5] 文檔與索引更新

---

## STATE

- **overall_status**: implementer_done
- **current_owner**: implementer
- **next_action**: Reviewer 審查 inspector 與 preview 整合
- **last_updated**: 2026-06-10 · Implementer
- **status_by_role**:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- **changed_files**:
  - `tools/non_tabular_lightweight_inspector_v1.py`（新增）
  - `scripts/run_non_tabular_experiment_preview.py`（S4_lite + outbox `content_summary`）
  - `docs/non-tabular-orchestrator-preview-v1.md`（§3.2 content_summary）
  - `tests/test_non_tabular_lightweight_inspector_v1.py`（新增）
  - `tests/test_non_tabular_orchestrator_preview_v1.py`（擴充）
  - `04_Workflows/tickets/W11-T2-non-tabular-lightweight-content-checks-v1_state.md`（本檔）
  - `04_Workflows/WORKFLOW_INDEX.md`（W11-T2 條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（W11-T2 行）

- **verification**:
  - `python -m unittest tests.test_non_tabular_lightweight_inspector_v1 tests.test_non_tabular_orchestrator_preview_v1 -v`

- **behavior_notes**:
  - `metadata_only=true` · `inspection_method=stat_only`
  - preview outbox 仍僅寫 `outbox/non_tabular_experiment/`

---

## C_REPORT

- **conclusion**: **accepted**
- **blocking_issues**: 無
- **checks_summary**:
  - **AC-1 inspector ✅**: `inspect_non_tabular_case_dir` 回傳 file_count / total_size / extension_distribution（unittest 覆蓋）
  - **AC-2 preview 整合 ✅**: `run_non_tabular_experiment_preview.py` 輸出含 `content_summary`；outbox 同步寫入
  - **AC-3 metadata-only ✅**: `test_does_not_read_file_contents` 驗證不呼叫 `open()` 讀內容 · `metadata_only=true`
  - **AC-4 NT fixtures ✅**: `python -m unittest tests.test_non_tabular_lightweight_inspector_v1 tests.test_non_tabular_orchestrator_preview_v1 -v` → **17/17 OK**
  - **AC-5 文檔/索引 ✅**: B_REPORT changed_files 含 preview doc 與 WORKFLOW_INDEX/Dashboard
  - **NonScope ✅**: 未觸 Tabular 主 outbox；heavy tools 未引入
- **risk_level**: low
- **suggestions**:
  - deferred：NT-B metadata extraction 仍受 allowlist/flag 限制（preview tests 已覆蓋 skip 路徑）；真實 heavy parser 留 W12-T3 follow-up
  - deferred：W10-T1 CI `non_tabular` scope 可選擇性展示 `content_summary` 欄位於 merged summary（非 blocking）

---

## D_REPORT

- **docs_updates**: pending
