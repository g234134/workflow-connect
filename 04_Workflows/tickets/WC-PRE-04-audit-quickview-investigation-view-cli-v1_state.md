# TICKET STATE · WC-PRE-04 · audit-quickview-investigation-view-cli-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

<!-- Orchestrator 填 -->

---

## STATE

- overall_status: accepted_with_gaps
- current_owner: orchestrator
- next_action: 無（investigation view 已可用；text formatter 留后续）
- last_updated: 2026-06-12 · reviewer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `audit/audit_investigation_projection_v1.py`（新建 · `project_audit_investigation_view` 從 contract test 抽出）
  - `audit/__init__.py`（新建）
  - `scripts/run_agent_audit_quickview.py`（`--view investigation` + wire→investigation 投影）
  - `tests/test_audit_quickview_and_case_history_spec_v1.py`（改 import 模組；移除內嵌投影函式）
  - `tests/test_agent_audit_quickview_v1.py`（investigation shape + CLI subprocess 測試）
  - `04_Workflows/tickets/WC-PRE-04-audit-quickview-investigation-view-cli-v1_state.md`（本檔 B_REPORT）
- artifacts:
  - `audit/audit_investigation_projection_v1.py`
- verification:
  - `python -m unittest tests.test_agent_audit_quickview_v1 tests.test_audit_quickview_and_case_history_spec_v1 -v` → **20/20 OK**
  - `python scripts/run_agent_audit_quickview.py --case-ref demo_phase --view investigation --format json` → exit 0；`schema_version=audit_investigation_view_v1`；含 `sections`/`timeline`/`gaps`
- behavior_notes:
  - 預設 `--view wire` 行為不變；`--view investigation` 輸出 spec §2.4 投影（investigation-only，read-only）。
  - wire 聚合邏輯未改；未建 Web UI / PG 查詢 / 全文搜尋。
  - 未改 outbox writers、MVP 主鏈或 Gov core。
- deferred_items:
  - CLI investigation text 格式仍輸出 JSON（非專用 human-readable formatter）

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: none
- checks_summary:
  - 抽检 `audit/audit_investigation_projection_v1.py` · `scripts/run_agent_audit_quickview.py`：`--view investigation` 接线至 `project_audit_investigation_view`；默认 `--view wire` 不变。
  - B_REPORT 验证 **20/20 OK** + CLI subprocess 抽检 exit 0；输出 `schema_version=audit_investigation_view_v1` 含 `sections`/`timeline`/`gaps`（investigation-only · read-only）。
  - 未改 outbox writers、MVP 主链或 Gov core；wire 聚合逻辑未动。
  - gap（非阻塞）：`deferred_items` 载明 investigation `--format text` 仍输出 JSON，无专用 human-readable formatter。
- risk_level: **low**
- suggestions:
  - Wave C 可引用 audit CLI `--view investigation` 与 WB-T5 spec §2.4 投影模块。
  - 不得假设全文搜索 / PG 查询 / Web UI 已交付。
  - 可选后续票补 investigation text formatter；WC-PRE-06 hooks 可索引本 CLI 产出。

---

## D_REPORT

<!-- Scribe 填 -->
