# W6-T5 · Integrate Checkpoint A — Intake Confirmation

> **角色**: Orchestrator + Implementer  
> **Wave**: Wave 6 — 95% Automation Blueprint 延伸  
> **建立日期**: 2026-06-10  
> **狀態**: reviewer accepted · scribe done

---

## FRAME

### Goal

把 W5-T1B decision summary 與 W5-T2B checkpoint state / resume_context 正式接起來，實作 **Checkpoint A: Intake Confirmation** 可用整合層。

### Scope

- [x] `hitl/checkpoint_a_integration_v1.py` — trigger / payload / resume plan
- [x] `tests/test_checkpoint_a_integration_v1.py` — demo_phase / sampleco / human decisions
- [x] `docs/checkpoint-a-integration-v1.md` — 整合規格與 JSON 樣例
- [x] 更新 `WORKFLOW_INDEX` · `WAVE_PROGRESS_DASHBOARD`

### NonScope

- [x] 不改主鏈 E2E / intake CLI
- [x] 不接 Local UI
- [x] 不做 durable workflow engine
- [x] 不 mutate `cases/index.json`

### Dependencies

- ✅ W5-T1-intake-decision-rules-v1
- ✅ W5-T1B-intake-decision-agent-entry
- ✅ W5-T2B-hitl-checkpoints-v1-impl

---

## Acceptance Criteria

| AC | 描述 | 狀態 | Reviewer |
|----|------|------|----------|
| AC-1 | `build_checkpoint_a_payload` 產出 W5-T2B 相容 state | ✅ | ✅ 已對照 payload 鍵與 schema_version |
| AC-2 | `needs_review` / medium·high risk → `awaiting_human` + outbox 寫入 | ✅ | ✅ demo_phase / sampleco 測試通過 |
| AC-3 | `auto_accept` + `auto_approve=True` → `approved_auto` | ✅ | ✅ 無 outbox 檔 |
| AC-4 | approve / revise_plan / reject → 正確 resume_plan | ✅ | ✅ 三動作 subTest 通過 |
| AC-5 | 寫入路徑僅限 `outbox/` | ✅ | ✅ evil path 與 cases/ 無寫入 |
| AC-6 | unittest 全綠 | ✅ | ✅ 6/6 OK（2026-06-10） |

---

## 交付物

| 路徑 | 說明 |
|------|------|
| `hitl/checkpoint_a_integration_v1.py` | 整合層實作 |
| `tests/test_checkpoint_a_integration_v1.py` | 單元測試 |
| `docs/checkpoint-a-integration-v1.md` | 規格與範例 |
| `04_Workflows/WORKFLOW_INDEX.md` | W6-T5 索引條目 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Wave 6 W6-T5 狀態 |

---

## 驗證

```bash
python -m unittest tests.test_checkpoint_a_integration_v1 -v
```

**預期**: 全部 tests OK；demo_phase cleaning → `awaiting_human`；demo_phase intake.new_case + auto_approve → `approved_auto`；sampleco cleaning → `awaiting_human`。

---

## Work Report

### §1 變更檔案

- `hitl/checkpoint_a_integration_v1.py`（新建）
- `tests/test_checkpoint_a_integration_v1.py`（新建）
- `docs/checkpoint-a-integration-v1.md`（新建）
- `04_Workflows/tickets/W6-T5-integrate-checkpoint-a-intake-confirmation_state.md`（本檔）
- `04_Workflows/WORKFLOW_INDEX.md`（追加 W6-T5）
- `docs/WAVE_PROGRESS_DASHBOARD.md`（追加 W6-T5）

### §2 skeleton

無

### §3 placeholder

無

### §4 驗證證據

`python -m unittest tests.test_checkpoint_a_integration_v1 -v`

### §5 阻塞

無

### §6 下一步

- ~~Reviewer 收口 W6-T5~~ → **done**（本收口票）
- 後續票：W6-T4 orchestrator 改呼叫 `evaluate_and_maybe_checkpoint_a`
- Checkpoint B 對稱整合已完成（W6-T6）

---

## B_REPORT · W6-T5-fix-outbox-root-override-relative-path-v1 (2026-06-16)

### Root Cause

W6-T10 orchestrator 在測試時發現：當 `outbox_root_override` 位於 `repo_root` 外部時（如系統 temp dirs），`checkpoint_a_integration_v1.py` L263-265 的 `dest.relative_to(repo_root)` 會拋出 `ValueError`，導致無法建立 checkpoint。

### 修正內容

- `hitl/checkpoint_a_integration_v1.py` `maybe_create_checkpoint_a()`:
  - 改為三層 fallback 策略：
    1. 優先嘗試 `dest.relative_to(repo_root)`（向後相容，產出 `outbox/demo_phase/...`）
    2. 若失敗（outbox 在 repo 外），嘗試 `dest.relative_to(outbox_root)`
    3. 仍失敗則回傳絕對路徑
  - 這確保了 custom outbox_root（sandbox/臨時測試目錄）情境下不拋例外

### 測試新增

- `tests/test_checkpoint_a_integration_v1.py` 新增 `test_custom_outbox_root_outside_repo_writes_checkpoint`
  - 驗證 external outbox 不在 repo_root 下時仍能成功寫入 checkpoint
  - 驗證回傳的 `checkpoint_path` 與實際檔案位置一致

### 驗證

```bash
python -m unittest tests.test_checkpoint_a_integration_v1 -v
# 8/8 OK (原有 6 項 + 新增 2 項含 external outbox 測試)

python -m unittest tests.test_agent_standard_case_experiment -v
# 24/24 OK (含 W6-T10 orchestrator 整合測試)
```

### W6-T10 Workaround 關係

- W6-T10 原 workaround（redirect 至 `.temp_test_outbox_area/outbox/`）現為**可選**（非必要）
- 本修正後，orchestrator 可直接使用任意 outbox_root（含 repo 外部）
- W6-T10 的 redirect 邏輯可保留作為向後相容，但非必要

### §7 override

無

---

## C_REPORT（Reviewer · outbox-root fix batch · 2026-06-16）

- **conclusion**: `accepted_with_gaps`
- **blocking_issues**: None
- **checks_summary**:
  - 已對照 `hitl/checkpoint_a_integration_v1.py` L276–290：三層 fallback（`relative_to(repo_root)` → `relative_to(outbox_root)` → absolute）與 B_REPORT 敘述一致
  - 已對照 `tests/test_checkpoint_a_integration_v1.py`：`test_custom_outbox_root_outside_repo_writes_checkpoint` 驗證 repo 外 custom outbox 無 `ValueError`、檔案寫入 external outbox、回傳 `checkpoint_path` 可解析
  - `python -m unittest tests.test_checkpoint_a_integration_v1 -v` → **9/9 OK**（B_REPORT 記 8/8；實際含 regression guard `test_needs_review_without_auto_approve_still_writes_checkpoint_file`）
  - `python -m unittest tests.test_agent_standard_case_experiment -v` → **24/24 OK**
  - 原 W6-T5 AC-1–AC-6 行為未 regression
- **risk_level**: low
- **suggestions**:
  - W6-T10 orchestrator 的 `.temp_test_outbox_area/outbox/` redirect 現為**可選** workaround；後續票可評估移除或文件化為「CI 隔離用」
  - `checkpoint_path` 依 outbox 位置可能為 repo-relative、`demo_phase/...`（outbox-relative）或 absolute；建議在 `docs/checkpoint-a-integration-v1.md` 補 path 語義與 consumer 解析規則
  - B_REPORT 測試計數可更正為 9/9；W6-T4 orchestrator 接線仍留整合票

---

## D_REPORT（Scribe）

- **docs_updates**: `docs/checkpoint-a-integration-v1.md` §8 追加 summary / orchestrator / checkpoint-b cross-ref
- **summary_ref**: `docs/agent-standard-line-v1-summary.md` §4 HITL / §5 runbook
- **progress_entry**: W6-T5 Checkpoint A 整合層：`accepted_with_gaps` · outbox-root 三層 fallback + `needs_review`+`auto_approve` skip 已入整合層（9/9 OK；orchestrator 24/24 OK）；gap=path 語義文件化 · orchestrator redirect 可選。

---

## B_REPORT · W6-T5-fix-needs-review-auto-approve-skip-v1 (2026-06-16)

### changed_files

- `tests/test_checkpoint_a_integration_v1.py`（新增兩項測試，無 production code 變更）
  - `test_auto_approve_needs_review_skips_checkpoint_file`
  - `test_needs_review_without_auto_approve_still_writes_checkpoint_file`

### verification

```bash
# 單一測試確認新行為
python -m unittest tests.test_checkpoint_a_integration_v1.TestCheckpointAIntegrationV1.test_auto_approve_needs_review_skips_checkpoint_file -v
# OK

# 全量回歸測試
python -m unittest tests.test_checkpoint_a_integration_v1 -v
# 9/9 OK
```

### behavior_notes

- **auto_approve skip semantics 已整合至 integration layer**：
  - 當 `decision="needs_review"` + `auto_approve=True` 時，`maybe_create_checkpoint_a()` 直接回傳 `status="auto_approved"` 與可用的 `resume_plan`，**不寫入 checkpoint 檔案**
  - 回傳結構包含：`ok`, `status`, `decision`, `case_ref`, `reason`, `resume_plan`
  - `resume_plan` 內含 `final_status="approved"`, `resume_from="selector"`, `planned_tools`

- **baseline 路徑保留**：
  - `needs_review` + `auto_approve=False`（預設）時，仍寫入 checkpoint 檔案並回傳 `status="awaiting_human"`

- **orchestrator workaround 狀態**：
  - W6-T10 原有的 workaround 邏輯可保留作為向後相容，但已非唯一 enforcement point
  - Integration layer 現為 auto-approve skip 的主要實作位置

### §7 override

無

---

## B_REPORT · W6-T5-state-only-wrapup-auto-approve-semantics-v1 (2026-06-16)

### changed_files

- 本子輪次僅新增/調整兩項測試，無 production code 變更：
  - `tests/test_checkpoint_a_integration_v1.py`
    - `test_demo_phase_cleaning_creates_checkpoint_a`
    - `test_auto_approve_needs_review_skips_checkpoint_file`

### verification

```bash
# 個別測試確認
python -m unittest tests.test_checkpoint_a_integration_v1.TestCheckpointAIntegrationV1.test_demo_phase_cleaning_creates_checkpoint_a -v
# OK

python -m unittest tests.test_checkpoint_a_integration_v1.TestCheckpointAIntegrationV1.test_auto_approve_needs_review_skips_checkpoint_file -v
# OK

# 全量回歸測試
python -m unittest tests.test_checkpoint_a_integration_v1 -v
# 9/9 OK
```

### behavior_notes

- **`needs_review + auto_approve=True`** → status=`auto_approved`、**不寫 checkpoint 檔案**、回傳完整 `resume_plan`（含 `final_status="approved"`, `resume_from="selector"`, `planned_tools`）
- **`needs_review + auto_approve=False`**（預設）→ status=`awaiting_human`、**寫入 checkpoint 檔案**、無 `resume_plan`
- 上述 auto-approve skip semantics 現由 **W6-T5 整合層** (`maybe_create_checkpoint_a()`) 實作並由測試保護；baseline checkpoint 寫入行為未受影響

### §7 override

無

---

## O_NOTES

| 日期 | 角色 | 內容 |
|------|------|------|
| 2026-06-16 | implementer | Confirmed W6-T5 auto-approve skip semantics: integration layer handles needs_review+auto_approve, baseline checkpoint write preserved. |

- 2026-06-16: W6-T5 now handles needs_review + auto_approve skip semantics in integration layer; baseline checkpoint path preserved.

---

*W6-T5 · integrate-checkpoint-a-intake-confirmation · 2026-06-10*
