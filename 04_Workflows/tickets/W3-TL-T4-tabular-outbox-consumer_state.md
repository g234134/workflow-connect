# TICKET STATE · W3-TL-T4 · Tabular Outbox Consumer / Debug / History Join

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 · Tool Layer · **Tabular MVP**

---

## FRAME

- Title: Tabular Outbox Consumer / Debug / History Join
- Goal: 提供 read-only outbox consumer 層與 CLI，讓開發者／Agent 可列出、過濾、讀取 tabular MVP outbox run，並與 `cases/index.json` / `lookup_case_history` join；**不**接 Phase 8.8 replay。
- Scope:
  - 新建 `tools/tabular_outbox_consumer.py` — `list_outbox_runs` / `get_outbox_run` / `join_with_case_history`
  - 新建 `tools/inspect_tabular_outbox.py` — debug CLI（`--case-ref`, `--tool-id`, `--join-history`, `--json`）
  - 新建 `docs/tabular-outbox-consumer-spec.md`
  - 新建 `tests/test_tabular_outbox_consumer.py` + `tests/fixtures/outbox/` 樣例
  - 新建本 state 檔
- NonScope:
  - Phase 8.8 `orchestration_bridge_outbox` / Langfuse / DLQ / replay pipeline
  - 修改 W3-TL-T1/T2/T3 實作檔或 state 檔
  - MVP 主鏈腳本、E2E driver、`run_mvp_mainline_regression.py`
  - Local UI、CI merge gate hook
  - 寫入或 mutate `outbox/`（consumer 唯讀）
- AllowedPaths:
  - `tools/tabular_outbox_consumer.py`
  - `tools/inspect_tabular_outbox.py`
  - `docs/tabular-outbox-consumer-spec.md`
  - `tests/test_tabular_outbox_consumer.py`
  - `tests/fixtures/outbox/**`
  - `04_Workflows/tickets/W3-TL-T4-tabular-outbox-consumer_state.md`
- BlockedPaths:
  - `tools/tabular_tool_executor.py`、`tools/tabular_outbox_writer.py`（唯讀）
  - `outbox/**` 既有樣例（唯讀；repo 根 outbox gitignored）
  - `scripts/lookup_case_history.py`、`scripts/build_cases_index.py`、`cases/index.json`（唯讀）
  - `HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`AGENTS.md`、`.cursor/rules/*`
  - `04_Workflows/tickets/W3-TL-T1*`–`W3-TL-T3*` state 檔
  - Phase 8.8 outbox / replay / orchestration 檔案
  - MVP 主鏈 gate / clean / bundle / E2E 腳本
- Dependencies:
  - **W3-TL-T3**（outbox schema `tabular_outbox_v1`）
  - **Wave 4A** `scripts/cases_index_lib.py`（lookup view）
  - `cases/index.json`（case registry SSOT）
- Risks:
  - repo 根 `outbox/` gitignored → 測試用 fixture + `outbox_root_override`
  - 與 Phase 8.8 outbox 混用 → spec §1 / §5 分軌聲明
- Observability:
  - logs: N/A（CLI stdout）
  - metrics: N/A
  - traces: N/A
- OutputArtifacts:
  - `tools/tabular_outbox_consumer.py`
  - `tools/inspect_tabular_outbox.py`
  - `docs/tabular-outbox-consumer-spec.md`
  - `tests/test_tabular_outbox_consumer.py`
  - `tests/fixtures/outbox/**`
- AcceptanceCriteria:
  - **AC-1**：API 能在 fixture outbox 樣例上正常運作，返回結構穩定（summary / full record / join dict）
  - **AC-2**：CLI 能列出特定 case 的 run 並可依 `tool_id` 過濾；`--json` 輸出可 parse
  - **AC-3**：`join_with_case_history` 將 outbox run 與 `cases/index.json` / `lookup_case_history` 對齊（含 `last_by_tool_id`）
  - **AC-4**：未修改 Wave 1/2 實作檔與 Phase 8.8 outbox 系統
  - **AC-5**：`python -m unittest tests.test_tabular_outbox_consumer -v` 全綠
- VerificationCommands:
  - `python -m unittest tests.test_tabular_outbox_consumer -v`
    - 預期：全綠

---

## Minimal Read Set

| # | 路徑 | 用途 |
|---|------|------|
| 1 | `docs/governance-constitution-v1.md` §1、§3、§5 | dict 契約、禁硬編路徑 |
| 2 | 本檔 FRAME + AllowedPaths | 硬邊界 |
| 3 | `docs/tabular-tool-outbox-spec.md` | outbox schema SSOT |
| 4 | `tools/tabular_outbox_writer.py` | path / validate 對齊（唯讀） |
| 5 | `scripts/cases_index_lib.py` | lookup join |
| 6 | `cases/index.json` | case registry |
| 7 | `04_Workflows/tickets/W3-TL-T3-tabular-tool-executor-outbox_state.md` | 前置票（唯讀） |

---

## §2 skeleton / placeholder

| 項 | 狀態 | 說明 |
|----|------|------|
| `tools/tabular_outbox_consumer.py` | **done** | list / get / join API |
| `tools/inspect_tabular_outbox.py` | **done** | debug CLI |
| `docs/tabular-outbox-consumer-spec.md` | **done** | consumer spec |
| `tests/test_tabular_outbox_consumer.py` | **done** | unit tests |
| replay pipeline | **[placeholder · Phase 8.8]** | re-execute non-goal |
| `events.jsonl` streaming consumer | **[deferred]** | v1 report reads file optionally |
| Local UI replay report | **done (CLI+HTML/MD)** | `scripts/build_tabular_outbox_replay_report.py` |

> **分軌聲明**：本票僅讀 tabular MVP `outbox/`；與 Phase 8.8 orchestration outbox **不同 schema／路徑**。

---

## STATE

- overall_status: done · Reviewer `accepted_with_gaps`
- current_owner: scribe
- next_action: 合併前可選跑 `python scripts/run_mvp_mainline_regression.py -v`（本票未改主鏈）；可選 follow-up：Local UI 或 `events.jsonl` consumer
- last_updated: 2026-06-10 · reviewer + scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done · `accepted_with_gaps`
  - scribe: done

---

## B_REPORT

### Implementation summary

- **Consumer API** (`tools/tabular_outbox_consumer.py`):
  - `list_outbox_runs(case_ref?, tool_id?, started_after?, started_before?)` → summaries, newest first
  - `get_outbox_run(case_ref, run_id)` → `{ok, record?}` or `{ok: false, message}`
  - `join_with_case_history(case_ref)` → case index subset + lookup history + chronological runs + `last_by_tool_id`
- **CLI** (`tools/inspect_tabular_outbox.py`): `--case-ref`, `--tool-id`, `--run-id`, `--join-history`, `--json`, `--outbox-root`
- **Fixtures**: `tests/fixtures/outbox/demo_phase/` (2 runs), `sampleco/2026-0001/` (1 run)
- **Spec**: `docs/tabular-outbox-consumer-spec.md`

### changed_files

- `tools/tabular_outbox_consumer.py` (new)
- `tools/inspect_tabular_outbox.py` (new)
- `docs/tabular-outbox-consumer-spec.md` (new)
- `tests/test_tabular_outbox_consumer.py` (new)
- `tests/fixtures/outbox/demo_phase/*.json` (new)
- `tests/fixtures/outbox/sampleco/2026-0001/*.json` (new)
- `04_Workflows/tickets/W3-TL-T4-tabular-outbox-consumer_state.md` (new)

### verification

- `python -m unittest tests.test_tabular_outbox_consumer -v` → **14/14 OK**

### behavior_notes

- Error paths return `{ok: false, message: ...}` — no exceptions for missing run/case
- Join uses `client_ref` from index entry to call `lookup_cases()` (Wave 4A view)
- Repo root `outbox/` remains gitignored; devs with local runs can inspect without `--outbox-root`

### deferred_items

- Replay / re-execute → Phase 8.8 or future ticket
- `events.jsonl` tail consumer
- Local UI integration

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- risk_level: low
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**：`list_outbox_runs` 回傳 9 欄 summary list；`get_outbox_run` 回傳 `{ok, record?}` 並驗證 `tabular_outbox_v1`；`join_with_case_history` 回傳 spec §2.3 完整 join dict — 與 `docs/tabular-outbox-consumer-spec.md` 一致。
  - **AC-2 ✅**：`inspect_tabular_outbox.py` 支援 `--case-ref`／`--tool-id`／`--json`／`--outbox-root`／`--join-history`；CLI list／join JSON 路徑有 unittest；API 層 `tool_id`／時間窗過濾已測。
  - **AC-3 ✅**：join 以 `case_dir` 對齊 `cases/index.json`，經 `client_ref` 呼叫 `lookup_cases()`，回傳 `case`／`history`／chronological `runs`／`last_by_tool_id`；`demo_phase` 與 `sampleco/2026-0001` fixture 皆通過。
  - **AC-4 ✅**：B_REPORT `changed_files` 僅含 T4 新建物；未觸 `tabular_tool_executor`／`tabular_outbox_writer`／T1–T3 state、主鏈腳本、Phase 8.8 outbox、憲法／合約／AGENTS（本票範圍內）。
  - **AC-5 ✅**：`python -m unittest tests.test_tabular_outbox_consumer -v` → **14/14 OK**（Reviewer 複跑確認）。
- gaps:
  - **G1**：CLI 層未單獨 unittest 覆蓋 `--tool-id`／`--run-id` 過濾與 table 模式輸出（API 與 `--json` list／join 已測）。
  - **G2**：`events.jsonl` streaming consumer 與 replay 已於 spec §5 標 defer；建議未來票補 Phase 8.8 交叉引用編號。
  - **G3**：WORKFLOW_INDEX／Dashboard 原仍寫 T4 not_started — Scribe 本回合已更新索引。

---

## D_REPORT

- deliverables:
  - **Consumer API** — `tools/tabular_outbox_consumer.py`：`list_outbox_runs`／`get_outbox_run`／`join_with_case_history`（read-only）
  - **Debug CLI** — `tools/inspect_tabular_outbox.py`：case／tool／run 查詢、history join、`--json`／`--outbox-root`
  - **Spec** — `docs/tabular-outbox-consumer-spec.md`：API／CLI／SSOT 關係與分軌聲明
  - **Tests + fixtures** — `tests/test_tabular_outbox_consumer.py`（14 tests）；`tests/fixtures/outbox/demo_phase/`（2 runs）、`sampleco/2026-0001/`（1 run）
- purpose: Tabular MVP **read-only outbox 檢視層**，供開發者／Agent 列出、過濾、讀取 per-run JSON 並與 case registry／lookup history join；**不**覆蓋 Phase 8.8 orchestration outbox。
- boundaries:
  - 唯讀 `outbox/`；不 spawn 工具、不 mutate outbox
  - 不實作 replay／re-execute、不接 Langfuse、不改 MVP 主鏈或 T1–T3 實作
- docs_updates: `docs/tabular-outbox-consumer-spec.md`；`04_Workflows/WORKFLOW_INDEX.md` §1.5；`docs/WAVE_PROGRESS_DASHBOARD.md` Wave 3-TL → 4/4 done
- progress_entry: |
    [W3-TL-T4] Tabular Outbox Consumer · Reviewer `accepted_with_gaps`；交付 consumer API + inspect CLI + spec + fixtures + 14 tests；Wave 3-TL **4/4 done**。
- non_blocking_gaps: G1 CLI 過濾路徑測試可選補強；G2 `events.jsonl` incremental reader／replay 留 Phase 8.8 或未來票；G3 Local UI 展示（W-MVP-W5）可選。
- followup_suggestions:
  - Optional: expose consumer in Local UI (W-MVP-W5)
  - Optional: `events.jsonl` incremental reader + Phase 8.8 cross-ref ticket

---

## E_REPORT · T4 follow-up (Local UI / replay closure · 2026-06-13)

### Mini design

- SSOT: `docs/tabular-outbox-replay-report-v1.md`
- **Replay** = read-only timeline reconstruction from outbox JSON (+ optional `events.jsonl` appendix)
- MVP = CLI + MD/HTML static report; **not** web app / auth / re-execute

### Implementation summary

- **Report CLI** — `scripts/build_tabular_outbox_replay_report.py`:
  - `collect_replay_report_data` / `build_tabular_outbox_replay_report`
  - `--case-ref` (optional all) · `--outbox-root` · `--format md|html|both` · `--json` · `--stdout`
  - Default output: `outbox/reports/replay_<slug>_<UTC>.{md,html}`
- **Tests** — `tests/test_build_tabular_outbox_replay_report.py` (8 tests)
- **Docs** — consumer spec §5/§6 + Dashboard Wave 3-TL verification block updated

### changed_files (follow-up)

- `docs/tabular-outbox-replay-report-v1.md` (new)
- `scripts/build_tabular_outbox_replay_report.py` (new)
- `tests/test_build_tabular_outbox_replay_report.py` (new)
- `docs/tabular-outbox-consumer-spec.md` (updated)
- `docs/WAVE_PROGRESS_DASHBOARD.md` (updated)
- `04_Workflows/tickets/W3-TL-T4-tabular-outbox-consumer_state.md` (this section)

### verification (follow-up)

- `python -m unittest tests.test_build_tabular_outbox_replay_report -v` → **8/8 OK**
- `python -m unittest tests.test_tabular_outbox_consumer -v` → **14/14 OK** (regression)

### deferred (unchanged)

- Re-execute replay → Phase 8.8
- `app/local_ui.py` integration → W-MVP-W5 optional
- Live `events.jsonl` tail consumer

---

## §8 注意事項

- **分軌**：tabular `outbox/` ≠ Phase 8.8 orchestration outbox
- **唯讀**：consumer 不寫 outbox、不 spawn 工具
- **測試**：使用 `outbox_root_override` 或 fixture 樹，避免污染 repo outbox

---

## O_NOTES

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-10 | orchestrator + implementer | 開票 + 實作 consumer / CLI / spec / tests | 本檔 |
