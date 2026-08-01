# TICKET STATE · WB-T5 · audit-quickview-and-case-history-spec-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal: 把 W10-T3 `run_agent_audit_quickview.py` 升格為 `docs/audit-quickview-and-case-history-spec-v1.md` 正式 spec；定義 decision → route → CP-A → CP-B → delivery approval → outbox join 的 read-only 追溯契約；與 WB-T3 outbox 命名空間對齊。
- Scope:
  - 新增 `docs/audit-quickview-and-case-history-spec-v1.md`
  - 新增 `tests/test_audit_quickview_and_case_history_spec_v1.py`
  - `scripts/run_agent_audit_quickview.py` docstring / `--help` 對齊
  - 更新 `docs/agent-and-non-tabular-lines-readme-v2.md` §4 指針
  - 更新 `docs/WAVE_PROGRESS_DASHBOARD.md`
- NonScope:
  - 不建 Web UI / Grafana
  - 不實作全文搜尋或 PG 查詢
  - 不擴展 non-tabular heavy tool 執行紀錄
- AllowedPaths:
  - `docs/audit-quickview-and-case-history-spec-v1.md`
  - `scripts/run_agent_audit_quickview.py`（docstring / help only）
  - `tests/test_audit_quickview_and_case_history_spec_v1.py`
  - `tests/test_agent_audit_quickview_v1.py`
  - `docs/agent-and-non-tabular-lines-readme-v2.md`
  - `04_Workflows/tickets/WB-T5-audit-quickview-and-case-history-spec-v1_state.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- BlockedPaths:
  - audit CLI 聚合邏輯（除非 spec 缺口 — 本票未觸）
  - MVP 主鏈 / Gov core
  - outbox / checkpoint writers
  - `cases/index.json` 寫入邏輯
- Dependencies: W10-T3 · W6-T9 · W11-T4 README v2 · WB-T3 · WA-T4 · C1-P1
- AcceptanceCriteria:
  - [AC-1] spec §2 定義 --case-ref 輸入與輸出 dict 形狀（sections[] · timeline[] · gaps[]）
  - [AC-2] spec §3 列出資料來源優先序
  - [AC-3] spec §4 case history join 對齊 lookup_case_history / cases/index.json
  - [AC-4] contract test 全綠；既有 test_agent_audit_quickview_v1 不回歸
  - [AC-5] demo_phase --format json 符合 spec 形狀（wire + projection）
  - [AC-6] spec §5 investigation-only
  - [AC-7] Phase 5 audit spec 70%→82%；8.9 join 語意 40%→75%
  - [AC-8] WB-T3 namespace 交叉引用一致
  - [AC-9] WA-T4 Scribe / STATE 邊界
  - [AC-10] README v2 §4 spec 指針

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: 無（票面已收口；Toolchain Wave B closure complete）
- last_updated: 2026-06-11 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `docs/audit-quickview-and-case-history-spec-v1.md`（新增 SSOT）
  - `tests/test_audit_quickview_and_case_history_spec_v1.py`（contract unittest + §2.4 projection helper）
  - `scripts/run_agent_audit_quickview.py`（docstring / argparse description / help only）
  - `tests/test_agent_audit_quickview_v1.py`（補 `schema_version` 斷言）
  - `docs/agent-and-non-tabular-lines-readme-v2.md`（§4.3 改 spec 指針；附錄索引）
  - `docs/agent-lines-audit-quickview-v1.md`（WB-T5 SSOT 指針）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（WB-T5 條目 · Phase 進度）
  - `04_Workflows/tickets/WB-T5-audit-quickview-and-case-history-spec-v1_state.md`（本檔）
- artifacts:
  - `docs/audit-quickview-and-case-history-spec-v1.md`
- verification:
  - `python -m unittest tests.test_audit_quickview_and_case_history_spec_v1 -v` → **13/13 OK**
  - `python -m unittest tests.test_agent_audit_quickview_v1 -v` → **6/6 OK**
  - `python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json --repo-root <temp>` → exit 0；wire `schema_version=agent_audit_quickview_v1`；projection 含 sections/timeline/gaps
- behavior_notes:
  - CLI 聚合邏輯未改；investigation view（sections/timeline/gaps）由 spec §2.4 純函式投影，contract test 內實作 `project_audit_investigation_view`。
  - 資料來源優先序 codify 於 spec §3（與現行 `find_latest_run_artifact` 掃描目錄順序對齊；同 tier 依檔名 timestamp）。
  - `agent-lines-audit-quickview-v1.md` 降級附錄；避免 README §4 雙維護。
- deferred_items:
  - CLI 原生輸出 investigation view 欄位（非本票 scope；consumers 用 §2.4 投影）
  - WB-T4 可選 hook 消費 `audit_sections_found` / `audit_gaps_count`（spec 已預留）

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: **无**
- checks_summary:
  - **FRAME**：未被 Implementer 改动；investigation-only、read-only join 与 AC 一致。
  - **B_REPORT 证据**：`tests.test_audit_quickview_and_case_history_spec_v1` **13/13 OK**；`tests.test_agent_audit_quickview_v1` **6/6 OK**；spec §2–§5 结构完整（sections/timeline/gaps · 数据源优先序 · case history join · investigation-only）。
  - **AC 对照**：WB-T3 namespace 交叉引用；README v2 §4 指针；CLI 仅 docstring/help 变更；Dashboard P5 audit 70%→82%、P8.9 join 40%→75%。
  - **Rule 3 注记**：`docs/agent-lines-audit-quickview-v1.md` 指针更新**不在** AllowedPaths，但为 SSOT 降级附录、无逻辑变更 → **缺但可接受**（建议 Orchestrator 关票时记 scope 留痕或补 FRAME 指针路径）。
- risk_level: **low**
- suggestions:
  - **缺但可接受**：CLI 未原生输出 investigation view（§2.4 投影函数在 contract test 内；consumers 按 spec 投影）。
  - **缺但可接受**：`audit_sections_found` / `audit_gaps_count` dashboard hook 留 WB-T4 deferred。
  - 无 blocking；可交 Scribe。

---

## D_REPORT

- docs_updates:
  - Dashboard WB-T5 专节与 Toolchain 分栏状态列已对齐 `done · accepted_with_gaps`（WC-PRE-01）
  - `docs/agent-and-non-tabular-lines-readme-v2.md` §4 指针已交付（B_REPORT；scope 留痕见 C_REPORT）
- progress_entry: WB-T5 交付 audit quickview + case history join spec（investigation-only）；`tests.test_audit_quickview_and_case_history_spec_v1` 13/13 OK · `tests.test_agent_audit_quickview_v1` 6/6 OK。
- followup_suggestions:
  - **WC-PRE-04**：CLI 原生输出 investigation view（§2.4 投影函数现于 contract test）
  - **WB-T4 deferred**：audit dashboard hook 字段
