# TICKET STATE · W6-T6 · integrate-checkpoint-b-delivery-gate

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal: 將 W5-T2 Delivery Confirmation 落成 Agent-run 實驗線可消費的 Checkpoint B 整合層（output_guard → checkpoint → delivery_plan）。
- Scope:
  - 新增 `hitl/checkpoint_b_integration_v1.py`（`build_checkpoint_b_payload` / `maybe_create_checkpoint_b` / `delivery_plan_from_checkpoint_b`）
  - 新增 `tests/test_checkpoint_b_integration_v1.py`
  - 新增 `docs/checkpoint-b-integration-v1.md`
  - 更新 `WORKFLOW_INDEX` 與 `WAVE_PROGRESS_DASHBOARD` Wave 6 索引
- NonScope:
  - 不接真實 client notify
  - 不改主鏈 delivery 流程（`build_case_delivery_bundle.py`、notification gateway）
  - 不寫入 `cases/index.json`
  - 不自動 resume 主鏈
- AllowedPaths:
  - `hitl/checkpoint_b_integration_v1.py`
  - `tests/test_checkpoint_b_integration_v1.py`
  - `docs/checkpoint-b-integration-v1.md`
  - `04_Workflows/tickets/W6-T6-integrate-checkpoint-b-delivery-gate_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- BlockedPaths:
  - 暗部 `core/`、`.env`、`runtime/checkpoints/**`
  - `scripts/build_case_delivery_bundle.py`、`app/local_ui.py`、notification 模組
- Dependencies:
  - W5-T2 design: `docs/hitl-checkpoints-v1.md`
  - W5-T2B impl: `hitl/checkpoints_v1.py`
  - W6-T3 design: `docs/agent-run-standard-case-experiment-v1.md`
- AcceptanceCriteria:
  - AC-1: 三個公開函式存在且回傳穩定 `dict`
  - AC-2: `ok + auto_approve=True` 跳過 checkpoint；`warning` 建立 checkpoint B
  - AC-3: `approve_delivery` / `request_changes` / `hold` 三種 delivery_plan 完整
  - AC-4: 寫入路徑僅限 `outbox/`
  - AC-5: unittest 全綠
  - AC-6: 未改真實 delivery / notify 流程

---

## STATE

- overall_status: reviewer accepted · scribe done
- current_owner: scribe
- next_action: 後續整合票（orchestrator ↔ W6-T5/W6-T6 接線）
- last_updated: 2026-06-10 · reviewer + scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `hitl/checkpoint_b_integration_v1.py`（新建）
  - `tests/test_checkpoint_b_integration_v1.py`（新建）
  - `docs/checkpoint-b-integration-v1.md`（新建）
  - `04_Workflows/tickets/W6-T6-integrate-checkpoint-b-delivery-gate_state.md`（新建）
  - `04_Workflows/WORKFLOW_INDEX.md`（追加 W6-T6）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 6 追加 W6-T6）
- artifacts:
  - `docs/checkpoint-b-integration-v1.md`
- verification:
  - `python -m unittest tests.test_checkpoint_b_integration_v1 -v`
- behavior_notes:
  - v1 觸發：`warning`/`blocked` → 建 checkpoint；`ok`+`auto_approve` → 跳過；`error` → 終止不建 checkpoint
  - `delivery_plan.notify_client` 恆為 `false`（NonScope）
  - `request_changes` 支援 `revise_target=cleaning|bundle`
- deferred_items:
  - 實驗線 `scripts/run_agent_standard_case_experiment.py` 接線（另票；W6-T6 整合層已就緒）
  - Checkpoint A 對稱整合層 → **W6-T5 done**

---

## Acceptance Criteria（Reviewer 檢查）

| AC | 描述 | Reviewer |
|----|------|----------|
| AC-1 | 三個公開函式存在且回傳穩定 `dict` | ✅ |
| AC-2 | `ok`+`auto_approve=True` 跳過；`warning` 建立 checkpoint B | ✅ |
| AC-3 | `approve_delivery` / `request_changes` / `hold` 三種 delivery_plan 完整 | ✅ |
| AC-4 | 寫入路徑僅限 `outbox/` | ✅ evil outbox 拒絕 |
| AC-5 | unittest 全綠 | ✅ 10/10 OK（2026-06-10） |
| AC-6 | 未改真實 delivery / notify 流程 | ✅ `notify_client` 恆 false |

---

## C_REPORT（Reviewer · outbox-root fix batch · 2026-06-16）

- **conclusion**: `accepted_with_gaps`
- **blocking_issues**: None
- **checks_summary**:
  - 已對照 `hitl/checkpoint_b_integration_v1.py` L346–358：三層 fallback 與 W6-T5 對稱，與 B_REPORT 敘述一致
  - 已對照 `tests/test_checkpoint_b_integration_v1.py`：`test_custom_outbox_root_outside_repo_writes_checkpoint_b` 驗證 repo 外 custom outbox 無 `ValueError`、checkpoint B 寫入正確
  - `python -m unittest tests.test_checkpoint_b_integration_v1 -v` → **11/11 OK**
  - `python -m unittest tests.test_agent_standard_case_experiment -v` → **24/24 OK**
  - 原 AC-1–AC-6 未 regression；BlockedPaths 未觸及
- **risk_level**: low
- **suggestions**:
  - 與 W6-T5 同步：在 `docs/checkpoint-b-integration-v1.md` 補 `checkpoint_path` 三層 fallback 語義
  - W6-T10 orchestrator 可直接傳 external `outbox_root_override`，redirect workaround 可選保留或後續移除
  - orchestrator S12 改呼叫 `maybe_create_checkpoint_b`；觸發規則與 T4 mock 對齊仍留另票

---

## D_REPORT

- docs_updates:
  - `docs/checkpoint-b-integration-v1.md` §8 cross-ref 更新
  - 新增 `docs/agent-standard-line-v1-summary.md`
- **progress_entry**: W6-T6 Checkpoint B 整合層：`accepted_with_gaps` · outbox-root 三層 fallback 與 W6-T5 對稱（11/11 OK；orchestrator 24/24 OK）；gap=path 語義文件化 · orchestrator redirect 可選。

---

## B_REPORT · W6-T6-fix-outbox-root-override-relative-path-v1 (2026-06-16)

### Root Cause

同 W6-T5 對稱問題：`checkpoint_b_integration_v1.py` L346-348 使用 `dest.relative_to(repo_root)` 計算 `checkpoint_path`。當 `outbox_root_override` 位於 repo 外部時拋出 `ValueError`。

### 修正內容

- `hitl/checkpoint_b_integration_v1.py` `maybe_create_checkpoint_b()`:
  - 採用與 W6-T5 相同的三層 fallback 策略
  - 優先嘗試 repo_root 相對路徑（向後相容）
  - 其次嘗試 outbox_root 相對路徑
  - 最終回退到絕對路徑

### 測試新增

- `tests/test_checkpoint_b_integration_v1.py` 新增 `test_custom_outbox_root_outside_repo_writes_checkpoint_b`
  - 驗證 external outbox 情境下 checkpoint B 正確寫入
  - 驗證無 `ValueError`

### 驗證

```bash
python -m unittest tests.test_checkpoint_b_integration_v1 -v
# 11/11 OK (原有 10 項 + 新增 1 項)

python -m unittest tests.test_agent_standard_case_experiment -v
# 24/24 OK (含 orchestrator 整合測試)
```

### 與 W6-T5 修正的一致性

兩個整合層現使用相同的 `checkpoint_path` 計算策略：
- `relative_to(repo_root)` → `relative_to(outbox_root)` → `absolute_path`
- 確保 external sandbox outbox 情境下 orchestrator 無需 redirect workaround

---

*W6-T6 · integrate-checkpoint-b-delivery-gate · implementer done · 2026-06-10*
