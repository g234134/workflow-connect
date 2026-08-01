# TICKET STATE · W4-REG-sandbox-client-runpath-suite-align-v1 · sandbox_client run-path suite 對齊

> **orchestrator arrange** · 2026-07-28  
> **觸發**：W4-GUARD-01-T1 C_REPORT gap（out of T1）  
> **SSOT**：`tests/test_agent_standard_case_regression.py` · `scripts/run_agent_standard_case_regression.py`  
> **≠** G2–G4 gate／bundle 升格 · **≠** Phase% · **≠** Round-2 · **≠** DarkOps

---

## FRAME

- Goal: 對齊 `sandbox_client` 在 `--include-extended-fixtures` + `run-all-allowed` 下的 suite 期望與真實 stop／blocked 語義，使 regression unittest 與 T1+W8 契約一致。
- Scope:
  - MUST：複現 FAIL `test_run_all_allowed_extended_fixtures_experimental_run`（現況：`final_status=blocked`／`decision=needs_review`；測期望 `stopped_at_cleaning_preview`；`guard_sanity_ok=true`）
  - MUST：最小改 `tests/test_agent_standard_case_regression.py`（更新斷言對齊契約，**或**確認 runtime 回歸後極小修 regression runner）
  - MUST：`python -m unittest tests.test_agent_standard_case_regression -v` 全綠（或明示剩餘 gaps）
  - MUST：Progress 一句 · 本票 B_REPORT／STATE
- NonScope:
  - **禁止** G2–G4 schema／ratio／strict-guards 升格（仍 `blocked_on_approval`）
  - **禁止**改 `case_eligibility.py`／`clean_phase_demo.py` gate exit 語義
  - Phase%／Dashboard Gauge 數字／war_status authorize
  - Round-2／H2–H5／execute-v2 · DarkOps · L1／K-2
  - 重開 W6-T10-cleanup
- AllowedPaths:
  - `04_Workflows/tickets/W4-REG-sandbox-client-runpath-suite-align-v1_state.md`
  - `tests/test_agent_standard_case_regression.py`
  - `scripts/run_agent_standard_case_regression.py`（僅若確認 runtime 回歸 · 極小 diff）
  - `docs/agent-and-non-tabular-lines-readme-v2.md`（僅一字澄清契約 · 可選）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
  - `04_Workflows/tickets/W4-GUARD-01_state.md`（僅 APPEND pointer · 可選）
- BlockedPaths:
  - `notebooks/csv_cleaning/clean_phase_demo.py`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% Gauge／completion 數字
  - `04_Workflows/Master_Map.json`
  - `.env`／憲法 §7
- Dependencies: W4-GUARD-01-T1 `accepted_with_gaps`；口令／plan「P進度下階段再編排（post Guard T1）」
- relay_mode: same_chat_ok
- AcceptanceCriteria:
  - 該 FAIL 測改為 PASS（或契約明示更新 + suite 全綠）
  - 明示 ≠ G2–G4 · ≠ Phase% apply
  - tip#1 仍 `P6-nightly-continue`

### Wave Master 擴展

- wave_id: SIDELINE
- group_id: Tabular
- lifecycle_phase: B
- phase_targets: [P6]
- estimated_cycles: 1
- mvp_allowed: true
- ticket_class: implementer
- evidence_tier: L-local
- parallel_ok: true
- parallel_to: P6-nightly-continue
- non_claims:
  - ≠ G2–G4 升格
  - ≠ Phase% 假閉環
  - ≠ Round-2 GO／UNLOCK／execute
  - ≠ DarkOps

---

## STATE

- **overall_status**: `done`
- **lifecycle_phase**: E
- **current_owner**: closed
- **last_updated**: 2026-07-28T21:15+08:00
- **授權標記**：plan execute B3 · Implementer 已對齊 suite · unittest 17/17
- **next_action**: closed · tip#1 仍 `P6-nightly-continue` · ≠ G2–G4／Phase%

---

## B_REPORT

ts: 2026-07-28T21:15+08:00  
author: Cursor（Implementer）  
auth: plan「執行 B3 · sandbox_client run-path suite 對齊」

### 變更

| 檔 | 摘要 |
|----|------|
| `tests/test_agent_standard_case_regression.py` | 對齊 `test_run_all_allowed_extended_fixtures_experimental_run`：sandbox 接受 `blocked`+`needs_review`+`ok=false`（`stop_at=cleaning_preview`∧`guard_sanity_ok`）；stable+additional_demo 仍須通過；overall `ok=false`＝controlled fail |
| `docs/agent-and-non-tabular-lines-readme-v2.md` | 一字契約註（controlled fail 語義） |
| runner | **未改**（非誤標 `stopped_at_*`；現況合法 controlled fail） |

### 驗證

- `python -m unittest tests.test_agent_standard_case_regression -v` → **17/17 OK**
- P6 輕核：latest **仍** `30346954725` · 無新 success · **未**改 monitor／Phase%

### skeleton／placeholder

- 無

### non_claims

≠ G2–G4 升格 · ≠ Phase% apply · ≠ Round-2 GO／UNLOCK／execute-v2 · ≠ DarkOps／L1／K-2

### 裁決建議

- `overall_status=done` · QUEUE READY→DONE · `default_next_mode=watch`

---

## C_REPORT

<!-- Reviewer 填 · same_chat 可略 · Implementer 自標 done -->

---

## APPEND LOG

- 2026-07-28T20:25+08:00 · HQ-Coordinator arrange · post Guard T1 · QUEUE READY · tip#1 未改 · **禁** G2–G4／Phase%
- 2026-07-28T21:15+08:00 · Implementer execute · suite 對齊 · 17/17 OK · overall_status=done · tip#1 未改 · ≠ G2–G4／Phase%
