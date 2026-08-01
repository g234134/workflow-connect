# TICKET STATE · W4-MEM-02 · Tabular 記憶索引增量（glob／schema_fingerprint）

> **orchestrator arrange** · 2026-07-28  
> **上游**：`W4-MEM-01`（`accepted_with_gaps` · deferred → 本票）  
> **SSOT**：`docs/TABULAR_MVP_SSOT.md` · `docs/case-history-lookup-spec-v0.1.md` · `docs/governance/wave5_next_stage_post_defer_p6_v1.md`  
> **≠** Phase%／war_status · **≠** Round-2 GO · **≠** DarkOps · **≠** gate exit 語義升格

---

## FRAME

- Goal: 補齊 W4-MEM-01 deferred：glob 自動登記 `cases/<client>/<id>/`、temp-dir index refresh UT、`schema_fingerprint` 欄位（單票單 scope）。
- Scope:
  - MUST：`scripts/cases_index_lib.py`／`build_cases_index.py` 支援 glob 發現 client 子案
  - MUST：index 條目可含 `schema_fingerprint`（與既有 `schema_notes`／headers 對齊 spec）
  - MUST：temp-dir index refresh 專項 unittest
  - MUST：更新 `docs/case-history-lookup-spec-v0.1.md` 欄位表
  - MUST：`python -m unittest tests.test_lookup_case_history tests.test_build_cases_index -v` 全綠
- NonScope:
  - Phase%／Dashboard authorize／war_status
  - Round-2／H2–H5／execute-v2
  - 改 gate／cleaning／bundle **exit 語義**（僅索引／lookup）
  - 向量 RAG／agent memory／prod SLA／required CI
  - DarkOps · Monitoring L1／L2 · K-2
- AllowedPaths:
  - `scripts/cases_index_lib.py` · `scripts/build_cases_index.py` · `scripts/lookup_case_history.py`
  - `cases/index.json`（refresh only）
  - `docs/case-history-lookup-spec-v0.1.md`
  - `tests/test_lookup_case_history.py` · `tests/test_build_cases_index.py`
  - `04_Workflows/tickets/W4-MEM-02-schema-fingerprint-index-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
- BlockedPaths:
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `04_Workflows/Master_Map.json`
  - `notebooks/csv_cleaning/clean_phase_demo.py`（本票不改清洗）
  - `.env`／憲法 §7 禁區類型
- Dependencies: `W4-MEM-01` accepted_with_gaps；旁線 `TABULAR-SIDELINE` 已綠（並行 · 非硬依賴）
- relay_mode: same_chat_ok
- AcceptanceCriteria:
  - glob 可登記至少一層 `cases/<client>/<id>/`（既有 demo_phase／sampleco 不回退）
  - index／lookup 暴露 `schema_fingerprint`（或缺省明確為 null + spec 註明）
  - temp-dir refresh UT 綠
  - tip#1 仍為 `P6-nightly-continue`
  - 未改 Phase%／未宣稱主線閉環

### Wave Master 擴展

- wave_id: SIDELINE
- group_id: Tabular
- lifecycle_phase: B
- phase_targets: [P2]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W4-MEM-01]
  - downstream_waves: []
  - blocks_if_missing: []
- risks: index refresh 寫 `cases/index.json` · low · 可回滾
- observability:
  - verify_commands:
    - `python scripts/build_cases_index.py --json`
    - `python -m unittest tests.test_lookup_case_history tests.test_build_cases_index -v`
  - evidence_artifacts: [cases/index.json]
  - success_signals: [unittest green · fingerprint field or documented null]
  - failure_signals: [regression on demo_phase/sampleco lookup]
- non_claims:
  - ≠ Phase% 假閉環
  - ≠ Round-2 GO／UNLOCK／execute
  - ≠ DarkOps／prod delivery／SLA／required CI
- ticket_class: implementer
- evidence_tier: L-local
- parallel_ok: true
- parallel_to: P6-nightly-continue

---

## STATE

- **overall_status**: `done`
- **lifecycle_phase**: E
- **current_owner**: closed
- **last_updated**: 2026-07-28T19:55+08:00
- **授權標記**：plan Execute W4-MEM-02 · Implementer 已施工
- **next_action**: closed · Reviewer 可選複核 · tip#1 仍 P6 · ≠ Phase%

---

## B_REPORT

### changed_files

- `scripts/cases_index_lib.py` — `discover_case_dirs` · `schema_fingerprint` · refresh／verbose lookup
- `scripts/build_cases_index.py` — discovered-count 訊息
- `tests/test_build_cases_index.py` — discover／fingerprint／temp-dir UT
- `tests/test_lookup_case_history.py` — verbose 含 fingerprint
- `docs/case-history-lookup-spec-v0.1.md` — W4-MEM-02 欄位與發現規則
- `cases/index.json` — refresh（10 entries）
- `04_Workflows/tickets/W4-MEM-02-schema-fingerprint-index-v1_state.md` — 本檔

### verification

```bash
gh run list --workflow=p6-int-gate-nightly.yml --limit 3
# latest still 30346954725 · no new success

python -m unittest tests.test_lookup_case_history tests.test_build_cases_index -v
# Ran 13 tests · OK

python scripts/build_cases_index.py --json
# ok · cases_written=10 · skipped=[]
```

### deferred_items

- 無（FRAME AC 已滿）
- 非本票：gate exit 護欄升格 · Phase% · Round-2

---

## APPEND LOG

- 2026-07-28T19:40+08:00 · HQ-Coordinator arrange · 承接 W4-MEM-01 deferred · QUEUE READY · tip#1 未改派 · ≠ Phase%
- 2026-07-28T19:55+08:00 · Implementer · glob+fingerprint+temp-dir UT · 13/13 OK · index 10 entries · overall_status→done · ≠ Phase%
