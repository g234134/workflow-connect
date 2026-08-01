# TICKET STATE · W4-GUARD-01-T1-reviewer-close · T1 fixture guard Reviewer 收口

> **orchestrator arrange** · 2026-07-28  
> **父票**：`W4-GUARD-01`（`implementer_done_pending_closure` · T1 IMPL done · Reviewer pending）  
> **SSOT**：`04_Workflows/tickets/W4-GUARD-01_state.md` B_REPORT IMPL · `docs/agent-and-non-tabular-lines-readme-v2.md` §2.3  
> **≠** G2–G4 gate／bundle 升格 · **≠** Phase% · **≠** Round-2 · **≠** DarkOps

---

## FRAME

- Goal: Reviewer 審閱 W4-GUARD-01 **T1 only**（experimental fixture guard · `--include-extended-fixtures`），寫 C_REPORT；Scribe 關父票／本票（`accepted` 或 `accepted_with_gaps`）。
- Scope:
  - MUST：只讀父票 B_REPORT IMPL + `enforce_fixture_guard` 行為說明
  - MUST：可選複跑 `python -m unittest` 覆蓋 fixture guard／regression 相關測（以父票既有 17 tests 為準）
  - MUST：填本票／父票 `C_REPORT`（結論 · gaps · non_claims）
  - MUST：Scribe 更新父票 `overall_status`（T1 收口）· Progress 一句
- NonScope:
  - **禁止**實作／開啟 G2–G4 schema／ratio／strict-guards 升格（仍 `blocked_on_approval`）
  - **禁止**改 `case_eligibility.py`／`clean_phase_demo.py` gate exit 語義
  - Phase%／Dashboard authorize／war_status
  - Round-2／H2–H5／execute-v2 · DarkOps · L1／K-2
- AllowedPaths:
  - `04_Workflows/tickets/W4-GUARD-01-T1-reviewer-close_state.md`
  - `04_Workflows/tickets/W4-GUARD-01_state.md`（C_REPORT／STATE 收口欄）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（僅 Lane A 狀態句 · **禁止**改 Phase% 數字格）
  - `docs/agent-and-non-tabular-lines-readme-v2.md`（僅若 C_REPORT 要求一字澄清）
  - `scripts/run_agent_standard_case_regression.py`（只讀）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
- BlockedPaths:
  - `notebooks/csv_cleaning/clean_phase_demo.py`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% Gauge／completion 數字
  - `04_Workflows/Master_Map.json`
  - `.env`／憲法 §7
- Dependencies: 父票 T1 IMPL done；口令／plan「P進度下階段再編排」
- relay_mode: same_chat_ok
- AcceptanceCriteria:
  - C_REPORT 對 T1 給出 `accepted`／`accepted_with_gaps`／`needs_changes` 之一
  - 明示 G2–G4 **仍 deferred**／`blocked_on_approval`
  - tip#1 仍 `P6-nightly-continue`
  - 未改 Phase%／未宣稱 gate 升格已落地

### Wave Master 擴展

- wave_id: SIDELINE
- group_id: Tabular
- lifecycle_phase: C
- phase_targets: [P6]
- estimated_cycles: 1
- mvp_allowed: true
- ticket_class: reviewer
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

- **overall_status**: `done_with_gaps`
- **lifecycle_phase**: E
- **current_owner**: scribe
- **last_updated**: 2026-07-28T20:20+08:00
- **授權標記**：Reviewer C_REPORT `accepted_with_gaps` · Scribe 關票完成
- **next_action**: closed · G2–G4 須另票＋批文 · tip#1 仍 `P6-nightly-continue`

---

## C_REPORT

**verdict**: `accepted_with_gaps`  
**role**: Reviewer（QA-Reviewer · same_chat）  
**ts**: 2026-07-28T20:20+08:00  
**scope**: T1 fixture guard only（`enforce_fixture_guard` · `--include-extended-fixtures`）

### 結論

T1 **達標**：stable fixtures（`demo_phase`／`sampleco`）無需 flag；experimental（`additional_demo`／`sandbox_client`）須 `--include-extended-fixtures`。六條 guard unit tests **全綠**。G2–G4 **仍** `blocked_on_approval`／deferred · **非** blocking gap。

### 證據命令

```powershell
gh run list --workflow=p6-int-gate-nightly.yml --limit 3
# latest 仍 30346954725 · 無新 success · 未改 monitor／Phase%

python -m unittest tests.test_agent_standard_case_regression -v
# Ran 17 · 16 OK · 1 FAIL（見 gaps）
# Guard 六測全 PASS：
#   test_enforce_fixture_guard_blocks_experimental_without_flag
#   test_enforce_fixture_guard_allows_stable_fixture
#   test_enforce_fixture_guard_allows_experimental_with_flag
#   test_enforce_fixture_guard_blocks_by_maturity_label
#   test_default_regression_excludes_extended_fixtures_silently
#   test_guard_blocks_when_include_extended_fixtures_true_but_fixture_marked_experimental
```

對照父票 B_REPORT IMPL 與 `scripts/run_agent_standard_case_regression.py` `enforce_fixture_guard`：行為與文件一致。

### gaps（non-blocking · 明示）

| ID | 說明 | 處置 |
|----|------|------|
| G-suite | `test_run_all_allowed_extended_fixtures_experimental_run` FAIL：`sandbox_client` 在 `--include-extended-fixtures`＋`run-all-allowed` 下 `final_status=blocked`／`decision=needs_review`／`ok=false`，測期望 `stopped_at_cleaning_preview`；**`guard_sanity_ok=true`**（T1 guard 已放行） | **out of T1 scope** · 屬 experimental run-path／checkpoint 行為 · 另票（非本票） |
| G2–G4 | schema／ratio／strict-guards 升格 | **仍 deferred**／`blocked_on_approval` · 須另票＋尚書省批文 |

### non_claims

≠ G2–G4 升格落地 · ≠ Phase% apply／改 Gauge · ≠ Round-2 GO／UNLOCK／execute · ≠ DarkOps／L1／K-2 · ≠ 宣稱 17/17 全綠

---

## APPEND LOG

- 2026-07-28T20:00+08:00 · HQ-Coordinator arrange · post W4-MEM-02 · QUEUE READY · tip#1 未改 · **禁** G2–G4
- 2026-07-28T20:20+08:00 · Reviewer+Scribe · C_REPORT `accepted_with_gaps` · overall `done_with_gaps` · 父票 T1 收口 · QUEUE DONE_WITH_GAPS · tip#1/#2 未改
