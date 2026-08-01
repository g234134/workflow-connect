# TICKET STATE · W12-T3 · non-tabular-first-real-processing-step-sandbox-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- **Goal**: 在 Non-Tabular shadow preview + W11-T2 lightweight inspector 之上，為 NT-A docu-corp fixture 新增極小步真實 processing（sandbox metadata 抽取），僅 allowlist + flag 啟用。

- **Scope**:
  1. `tools/document_metadata_extractor_v1.py` → `extract_document_metadata()`
  2. `scripts/run_non_tabular_experiment_preview.py` → `preview+meta` mode / `--with-metadata-extraction`
  3. `processing_summary` 掛載於 preview JSON 與 sandbox outbox
  4. unittest：extractor + orchestrator gating
  5. 更新 `docs/non-tabular-orchestrator-preview-v1.md`

- **NonScope**:
  - ❌ 任意 case_dir 啟用（須 allowlist + flag）
  - ❌ OCR / 全文解析
  - ❌ Tabular / production outbox / notify

- **AllowedPaths**:
  - `tools/document_metadata_extractor_v1.py`
  - `scripts/run_non_tabular_experiment_preview.py`
  - `docs/non-tabular-orchestrator-preview-v1.md`
  - `tests/test_document_metadata_extractor_v1.py`
  - `tests/test_non_tabular_orchestrator_preview_v1.py`
  - `04_Workflows/tickets/W12-T3-non-tabular-first-real-processing-step-sandbox-v1_state.md`

- **AcceptanceCriteria**:
  - [AC-1] `document_metadata_extractor_v1` 抽取 size / mime / page_count / encoding（metadata only）
  - [AC-2] orchestrator 僅在 NT-A + allowlist + flag 時執行 S7
  - [AC-3] `processing_summary` 寫入 preview 與 `outbox/non_tabular_experiment/`
  - [AC-4] 無 flag / 非 allowlist 時不執行；unittest 全綠
  - [AC-5] 文檔與 state 更新

---

## STATE

- **overall_status**: implementer_done
- **current_owner**: implementer
- **next_action**: Reviewer 審查 allowlist gate 與 sandbox 邊界
- **last_updated**: 2026-06-10 · Implementer
- **status_by_role**:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- **changed_files**:
  - `tools/document_metadata_extractor_v1.py`（新增）
  - `scripts/run_non_tabular_experiment_preview.py`（S7 + CLI flags）
  - `docs/non-tabular-orchestrator-preview-v1.md`（§3.4 processing_summary）
  - `tests/test_document_metadata_extractor_v1.py`（新增）
  - `tests/test_non_tabular_orchestrator_preview_v1.py`（W12-T3 測試）
  - `04_Workflows/tickets/W12-T3-non-tabular-first-real-processing-step-sandbox-v1_state.md`（本檔）

- **verification**:
  - `python -m unittest tests.test_document_metadata_extractor_v1 tests.test_non_tabular_orchestrator_preview_v1 -v`

- **behavior_notes**:
  - allowlist: `cases/_experiment_samples/nt_docu_stub` 或 path 含 `nt_docu_stub` + intake `client_ref=docu-corp`
  - mode: `preview+meta` via `--with-metadata-extraction` or `--mode preview+meta`
  - 僅寫 `outbox/non_tabular_experiment/`；未觸 production outbox / notify

---

## C_REPORT

- **conclusion**: pending

---

## D_REPORT

- **docs_updates**: pending
