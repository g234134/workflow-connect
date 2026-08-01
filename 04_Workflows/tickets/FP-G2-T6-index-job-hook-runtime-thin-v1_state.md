# TICKET STATE · FP-G2-T6-index-job-hook-runtime-thin-v1 · Index hook thin runtime

> Full-Phase G2 · P2 · **build** · thin runtime on T1 skeleton · 2026-07-13  
> 上游：`FP-G2-T1-index-job-scheduler-hook-v1`

---

## FRAME

- Goal: 在 T1 dry-run skeleton 上加 **thin runtime**：本地 fixture · dry-run dict · fixture_digest · **非**生產 ingest。
- Scope:
  - MUST：`scripts/run_index_job_hook_runtime_thin_v1.py`
  - MUST：`tests/fixtures/index_job_hook_thin_v1/**` + `tests/test_index_job_hook_runtime_thin_v1.py`
  - MUST：`docs/phase2-index-job-hook-runtime-thin-v1.md`
- NonScope:
  - 不改 `core/**` · 不做 T5 corpus · 不部署 cron · 不宣稱 P2 closure
  - 不執行生產 ingest（`--execute` blocked）
- AllowedPaths:
  - `scripts/run_index_job_hook_runtime_thin_v1.py`
  - `tests/test_index_job_hook_runtime_thin_v1.py`
  - `tests/fixtures/index_job_hook_thin_v1/**`
  - `docs/phase2-index-job-hook-runtime-thin-v1.md`
  - `04_Workflows/tickets/FP-G2-T6-index-job-hook-runtime-thin-v1_state.md`
- BlockedPaths:
  - `core/**` · 暗部 · `.github/workflows/**` · Dashboard 數字格（本票）
  - T5 corpus 路徑 · 治理母本 · 憲法 §7
- Dependencies:
  - FP-G2-T1（skeleton CLI 已存在）
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：CLI dry-run JSON 含 `ok`／`planned_jobs`／`fixture_digest`／`writes_index=false`
  - AC-2：不寫 03_RAG_Database／不建 write probe
  - AC-3：`--execute` → ok=false · execute_blocked
  - AC-4：`python -m unittest tests.test_index_job_hook_runtime_thin_v1 -v` PASS
  - AC-5：doc non_claims 齊

### Wave Master 擴展

- phase_targets: [P2]
- baseline_pct: "07-13 W-PROG-B · P2=65%"
- proposed_delta_pct: "P2 +1"
- evidence_gate: L-local
- impact_size: small
- apply_phase_pct: false
- non_claims:
  - ≠ production ingest · ≠ cron · ≠ T5 corpus · ≠ P2 closure

---

## STATE

- overall_status: done
- current_owner: none
- next_action: 無 · 已 accepted；P2 Δ 由 W-PROG-triple-batch 匯總
- last_updated: 2026-07-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- ac_status:
  - AC-1: pass
  - AC-2: pass
  - AC-3: pass
  - AC-4: pass
  - AC-5: pass

---

## B_REPORT

- changed_files:
  - scripts/run_index_job_hook_runtime_thin_v1.py
  - tests/test_index_job_hook_runtime_thin_v1.py
  - tests/fixtures/index_job_hook_thin_v1/plan.json
  - tests/fixtures/index_job_hook_thin_v1/sample.txt
  - docs/phase2-index-job-hook-runtime-thin-v1.md
- verification: |
    python -m unittest tests.test_index_job_hook_runtime_thin_v1 -v → Ran 6 tests OK
    python scripts/run_index_job_hook_runtime_thin_v1.py --dry-run --format json → ok=true
- behavior_notes: 疊加 T1 skeleton metadata；fixture plan → planned_jobs；execute blocked。
- deferred_items: core ingest 配線另票

### Phase 影響

- **影響 Phase**：P2
- **baseline**：07-13 W-PROG-B · 65%
- **proposed_delta**：+1
- **實際上調**：待 W-PROG-triple-batch-2026-07-13
- **non_claims**：≠ production ingest

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: 6 unittest OK；writes_index 恒 false；未碰 core／T5。
- risk_level: low
- suggestions: 後續 execute 須另票 + infra 解阻

### Phase 影響

- **影響 Phase**：P2 · +1 · apply_phase_pct=false

---

## D_REPORT

- docs_updates: phase2-index-job-hook-runtime-thin-v1.md
- progress_entry: 見 W-PROG-triple-batch
- followup_suggestions: T5／core wiring 另開

### Phase 影響

- **實際上調**：見 W-PROG 匯總
