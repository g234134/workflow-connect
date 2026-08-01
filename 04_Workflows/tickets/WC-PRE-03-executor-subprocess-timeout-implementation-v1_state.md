# TICKET STATE · WC-PRE-03 · executor-subprocess-timeout-implementation-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

<!-- Orchestrator 填 -->

---

## STATE

- overall_status: accepted
- current_owner: orchestrator
- next_action: 無（可作 Wave C executor 依赖）
- last_updated: 2026-06-12 · reviewer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `tools/tabular_tool_executor.py`（`subprocess.run(..., timeout=600)` + `TimeoutExpired` handling）
  - `tests/test_tabular_tool_executor.py`（`test_subprocess_timeout_returns_failure_with_null_exit_code`）
  - `04_Workflows/tickets/WC-PRE-03-executor-subprocess-timeout-implementation-v1_state.md`（本檔 B_REPORT）
- artifacts: 無
- verification:
  - `python -m unittest tests.test_tabular_tool_executor tests.test_tool_executor_and_sandbox_contract_v1 -v` → **23/23 OK**
- behavior_notes:
  - 非 dry_run subprocess 路徑設 `timeout=600`；超時回傳 `ok=false`、`exit_code=null`、`message` 含 `subprocess_timeout`；仍寫 outbox 失敗紀錄。
  - dry_run 路徑不 spawn subprocess，行為不變。
  - 未改暗部 `core/tool_executor.py`、experiment orchestrator allowlist、`.github/workflows/*` 或 MVP mainline gate。
- deferred_items: 無

---

## C_REPORT

- conclusion: **accepted**
- blocking_issues: none
- checks_summary:
  - 抽检 `tools/tabular_tool_executor.py`：`_SUBPROCESS_TIMEOUT_SECONDS = 600`；非 dry_run subprocess 设 timeout；`TimeoutExpired` 回传 `ok=false` · `exit_code=null` · `message` 含 `subprocess_timeout`。
  - B_REPORT 验证 **23/23 OK**（`test_tabular_tool_executor` · `test_tool_executor_and_sandbox_contract_v1`）；dry_run 路径不 spawn subprocess，行为不变。
  - 未改暗部 `core/tool_executor.py`、experiment orchestrator allowlist、`.github/workflows/*` 或 MVP mainline gate。
  - FRAME 区仍为占位；B_REPORT 与代码抽检一致。
- risk_level: **low**
- suggestions:
  - Wave C 可引用 Tabular executor 非 dry_run subprocess 600s 超时语义与失败 outbox 写入。
  - 仍不得假设全 prod execute 默认开启或暗部 core executor 已同步 timeout。
  - WC-PRE-06/07 批文前不得将 executor timeout 升格为 PR required SLA。

---

## D_REPORT

<!-- Scribe 填 -->
