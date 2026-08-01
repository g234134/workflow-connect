# TICKET STATE · W10-T3 · agent-lines-audit-quickview-cli-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- **Goal**: 為 Tabular Agent 標準線 + Non-tabular preview 提供只讀「審計快查 CLI」，一條命令聚合 decision / route / checkpoint / delivery approval。

- **Scope**:
  1. `scripts/run_agent_audit_quickview.py`（`--case-ref` · `--format text|json`）
  2. 讀取 `agent_experiment_regression` / `agent_ci` / `non_tabular_experiment` 最新 artifact
  3. 讀取 `outbox/<case_ref>/checkpoint_A|B` 狀態與人類決策
  4. `tests/test_agent_audit_quickview_v1.py`（最小 fake outbox）
  5. `docs/agent-lines-audit-quickview-v1.md`
  6. WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引

- **NonScope**:
  - ❌ 任何寫入或 state 更新
  - ❌ 外部系統連結
  - ❌ 改 Tabular / non-tabular orchestrator 主鏈

- **AllowedPaths**:
  - `scripts/run_agent_audit_quickview.py`
  - `tests/test_agent_audit_quickview_v1.py`
  - `docs/agent-lines-audit-quickview-v1.md`
  - `04_Workflows/tickets/W10-T3-agent-lines-audit-quickview-cli-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`

- **AcceptanceCriteria**:
  - [AC-1] CLI 支援 `--case-ref` + `--format text|json`
  - [AC-2] 聚合 decision / risk / planned_route / CP-A / CP-B / delivery_approval
  - [AC-3] 完全只讀（unittest 驗證檔案內容不變）
  - [AC-4] unittest 全綠
  - [AC-5] 文檔含 demo_phase text 範例

---

## STATE

- **overall_status**: implementer_done
- **current_owner**: implementer
- **next_action**: Reviewer 審查只讀邊界與輸出形狀
- **last_updated**: 2026-06-10 · Implementer
- **status_by_role**:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- **changed_files**:
  - `scripts/run_agent_audit_quickview.py`（新增只讀 audit quickview CLI）
  - `tests/test_agent_audit_quickview_v1.py`（新增）
  - `docs/agent-lines-audit-quickview-v1.md`（新增）
  - `04_Workflows/tickets/W10-T3-agent-lines-audit-quickview-cli-v1_state.md`（本檔）
  - `04_Workflows/WORKFLOW_INDEX.md`（W10-T3 條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（W10-T3 行）

- **verification**:
  - `python -m unittest tests.test_agent_audit_quickview_v1 -v` → **6 tests OK**
  - `python scripts/run_agent_audit_quickview.py --case-ref demo_phase` → **ok=True**；聚合 regression + CP-B delivery approval

- **behavior_notes**:
  - 只讀聚合；`sources_read` 列出實際讀取的 JSON 路徑
  - `agent_ci` 目錄預留支援（尚無產物時靜默跳過）
  - delivery_approval 優先取自 on-disk CP-B `human_decision`

---

## C_REPORT

- **conclusion**: **accepted**
- **blocking_issues**: 無
- **checks_summary**:
  - **AC-1 CLI ✅**: `--case-ref` + `--format text|json` 由 unittest 與 CLI smoke 驗證
  - **AC-2 聚合 ✅**: 2026-06-15 `python scripts/run_agent_audit_quickview.py --case-ref demo_phase` → `ok: True`；含 decision / planned_route / CP-A / CP-B / delivery_approval 區塊
  - **AC-3 只讀 ✅**: `test_read_only_collects_paths_without_writes` 驗證 outbox 內容不變
  - **AC-4 unittest ✅**: `python -m unittest tests.test_agent_audit_quickview_v1 -v` → **6/6 OK**
  - **AC-5 文檔 ✅**: `docs/agent-lines-audit-quickview-v1.md` 存在且 B_REPORT 已索引
  - **W12-T1 交叉 ✅**: quickview 已含 `sandbox_delivery` 區塊（spot-check `run_agent_audit_quickview.py` 模組引用）
- **risk_level**: low
- **suggestions**:
  - deferred：`agent_ci` 目錄尚無產物時靜默跳過屬預期；W10-T1 CI 常態跑後可再驗 `sources_read` 含 `agent_ci` 路徑
  - deferred：investigation view 深化留 WC-PRE-04 follow-up（本票為 v1 快查）

---

## D_REPORT

- **docs_updates**: pending
