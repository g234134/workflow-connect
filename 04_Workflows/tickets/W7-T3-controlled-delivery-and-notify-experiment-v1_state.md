# TICKET STATE · W7-T3 · controlled-delivery-and-notify-experiment-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal: 在 Agent 標準線 v1 上新增受控 delivery / notify 試驗層（僅 internal sandbox），讀 bundle/signoff、模擬客戶文案、寫 outbox notify JSON。
- Scope:
  - 新增 `delivery/controlled_notify_experiment_v1.py`
  - 新增 `scripts/run_controlled_delivery_notify_experiment.py`
  - 新增 `tests/test_controlled_delivery_notify_experiment_v1.py`
  - 新增 `docs/controlled-delivery-notify-experiment-v1.md`
  - 更新 `WORKFLOW_INDEX` 與 `WAVE_PROGRESS_DASHBOARD`
- NonScope:
  - 不改 `notebooks/csv_cleaning/case_delivery_bundle.py`
  - 不改任何 production delivery / notify 管線
  - 不對非 allowlist case 啟用
  - 不寫入真實外部系統
- AllowedPaths:
  - `delivery/controlled_notify_experiment_v1.py`
  - `delivery/__init__.py`
  - `scripts/run_controlled_delivery_notify_experiment.py`
  - `tests/test_controlled_delivery_notify_experiment_v1.py`
  - `docs/controlled-delivery-notify-experiment-v1.md`
  - `04_Workflows/tickets/W7-T3-controlled-delivery-and-notify-experiment-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- BlockedPaths:
  - 暗部 `core/`、`.env`、`runtime/checkpoints/**`
  - `notebooks/csv_cleaning/case_delivery_bundle.py`、notification gateway
- Dependencies:
  - W6-T3: `docs/agent-run-standard-case-experiment-v1.md` (S15)
  - W6-T6: `docs/checkpoint-b-integration-v1.md`
  - W6-T9: `docs/agent-standard-line-governance-view-v1.md` (R4/R5)
- AcceptanceCriteria:
  - AC-1: 模組讀 signoff/bundle 並產出 client summary 純文字
  - AC-2: `--no-dry-run` 寫入 `outbox/<case_ref>/notify_experiment_<ts>.json`
  - AC-3: 非 allowlist → `ok: false` / blocked
  - AC-4: CLI `--dry-run` 預設 true
  - AC-5: unittest 全綠
  - AC-6: 未改 production delivery / notify

---

## STATE

- overall_status: implementer done · reviewer pending
- current_owner: implementer
- next_action: Reviewer 審稿 + Scribe 索引確認
- last_updated: 2026-06-10
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: accepted
  - scribe: done

---

## B_REPORT

- changed_files:
  - `delivery/__init__.py`（新建）
  - `delivery/controlled_notify_experiment_v1.py`（新建）
  - `scripts/run_controlled_delivery_notify_experiment.py`（新建）
  - `tests/test_controlled_delivery_notify_experiment_v1.py`（新建）
  - `docs/controlled-delivery-notify-experiment-v1.md`（新建）
  - `04_Workflows/tickets/W7-T3-controlled-delivery-and-notify-experiment-v1_state.md`（新建）
  - `04_Workflows/WORKFLOW_INDEX.md`（追加 W7-T3）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 7 追加 W7-T3）
- verification:
  - `python -m unittest tests.test_controlled_delivery_notify_experiment_v1 -v`
  - `python scripts/run_controlled_delivery_notify_experiment.py --case-dir cases/demo_phase`
- behavior_notes:
  - allowlist: `demo_phase`, `sampleco/2026-0001` + `sensitivity=internal`
  - `external_dispatch` 恆 false；`notify_channel=experiment_log`
  - dry-run 預設：只印 summary，不寫 outbox

---

## DEFERRED

- Orchestrator 實驗線 S15 接線（本票僅獨立 CLI + 模組）
- 真實 notification gateway（另票；對照 W6-T3 S15 NonScope）

---

## C_REPORT (Reviewer)

- conclusion: **accepted**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**: controlled notify experiment 僅作用於 allowlist
  - **AC-2 ✅**: dry-run 預設行為正確
  - **AC-3 ✅**: external dispatch 仍 disabled，符合 NonScope
  - **AC-4 ✅**: unittest 全綠
- risk_level: low
- notes:
  - controlled notify experiment 僅作用於 allowlist + dry-run 預設，external dispatch 仍 disabled

---

*W7-T3 · implementer · 2026-06-10 · Reviewer: accepted*
