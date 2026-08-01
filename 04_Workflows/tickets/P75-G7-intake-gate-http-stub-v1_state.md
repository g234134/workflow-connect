# TICKET STATE · P75-G7-intake-gate-http-stub-v1 · P7.5 Intake Gate 本地 HTTP stub

> Full-Phase · P7.5 · **build** · L-local HTTP stub · 2026-07-13  
> Wave 2（全線到100 · 後端衝 ~90% · 無 UI）  
> 匯總：`W-PROG-full-line-to-100-wave-plan-2026-07-13`

---

## FRAME

- Goal: 落地 **本地 loopback HTTP stub** `POST /api/intake/gate`，包裝既有 `evaluate_intake_gate`；預設 `preview`；供 Wave 2→90% 後端入口；≠ prod app_api · ≠ UI · ≠ Phase closure。
- Scope:
  - MUST：`docs/p75-intake-gate-http-stub-v1.md`
  - MUST：`shared/schemas/intake_gate_http_request_v1.json`
  - MUST：`routing/intake_gate_http_stub_v1.py` — handle + loopback server
  - MUST：`scripts/run_intake_gate_http_stub_v1.py` — `--once`／`--serve`
  - MUST：`tests/test_intake_gate_http_stub_v1.py`
  - MAY：INDEX／upstream entry 一句；計劃／W-PROG／Progress 末尾 append
- NonScope:
  - 不改暗部 `app_api` · 不開 Web UI · 不寫 Dashboard 數字格
  - 不改 gate layer 決策邏輯本體（僅 HTTP 包裝）
  - 不暴露非 loopback host
- AllowedPaths:
  - `docs/p75-intake-gate-http-stub-v1.md`
  - `docs/p75-upstream-entry-index-v1.md`（MAY 一行）
  - `shared/schemas/intake_gate_http_request_v1.json`
  - `routing/intake_gate_http_stub_v1.py`
  - `scripts/run_intake_gate_http_stub_v1.py`
  - `tests/test_intake_gate_http_stub_v1.py`
  - `04_Workflows/tickets/P75-G7-intake-gate-http-stub-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md`（末尾／Wave 2 表 append）
  - `04_Workflows/tickets/W-PROG-full-line-to-100-wave-plan-2026-07-13_state.md`（末尾 append）
- BlockedPaths:
  - `core/**` · 暗部根 · `.github/workflows/**` · Dashboard 數字格
  - 治理母本 · 憲法 §7 類型 · 他人 core
- Dependencies:
  - P75-G2/G3/G4（gate layer + CLI）· 計劃 §2.1 →90% HTTP
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：契約 doc 含 request／response／non_claims（≠ prod／UI）
  - AC-2：`handle_gate_request` 回穩定 dict（`ok`／`http`／`gate`）
  - AC-3：預設 mode=preview；host 僅 loopback
  - AC-4：`python -m unittest tests.test_intake_gate_http_stub_v1 -v` PASS
  - AC-5：CLI `--once` JSON 可跑；`ok` 鍵存在
  - AC-6：loopback `POST /api/intake/gate` + `GET /health` 可驗

### Wave Master 擴展

- phase_targets: [P7.5]
- baseline_pct: "07-13 Dashboard · P7.5=46%"
- proposed_delta_pct: "P7.5 +2"
- evidence_gate: L-local
- impact_size: small
- apply_phase_pct: false
- phase_delta_lifecycle: verified
- non_claims:
  - ≠ prod app_api · ≠ UI · ≠ Phase closure · ≠ 暗部根 · ≠ 擅自大漲 Dashboard %

---

## STATE

- overall_status: done
- current_owner: none
- next_action: 無 · accepted；Δ 待 W-PROG 匯總 authorize
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
  - AC-6: pass

---

## B_REPORT

- changed_files:
  - docs/p75-intake-gate-http-stub-v1.md
  - shared/schemas/intake_gate_http_request_v1.json
  - routing/intake_gate_http_stub_v1.py
  - scripts/run_intake_gate_http_stub_v1.py
  - tests/test_intake_gate_http_stub_v1.py
  - docs/p75-upstream-entry-index-v1.md（一行）
  - 04_Workflows/WORKFLOW_INDEX.md（一句）
  - 04_Workflows/tickets/P75-G7-intake-gate-http-stub-v1_state.md
- verification: |
    python -m unittest tests.test_intake_gate_http_stub_v1 -v → 8 OK
    python scripts/run_intake_gate_http_stub_v1.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview → ok=true
- behavior_notes: loopback-only；預設 preview；run 可寫 outbox override；notify 僅 run+enable_notifications
- deferred_items: 暗部 app_api 正式路由 · Wave 4 UI · prod expose

### Phase 影響

- **影響 Phase**：P7.5
- **proposed_delta**：+2
- **實際上調**：否（apply_phase_pct=false）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: AC 全過；禁區未觸；無 UI；無 Dashboard 寫入；DarkOps 未碰。
- risk_level: low
- suggestions: 下一 Wave 2 可選 P8.9 敘事／metrics 閉環或 P8.6–8.8 runtime 薄增量；P2 --execute 仍 blocked

### Phase 影響

- apply_phase_pct=false · 未越權

---

## D_REPORT

- docs_updates: HTTP stub contract · INDEX · upstream entry · plan Wave 2 · Progress
- progress_entry: 本輪 Progress 條
- followup_suggestions: Wave 2 下一張見計劃；Wave 3 煙霧待 G7+既有 CLI 串線穩定後再談

### Phase 影響

- **實際上調**：否

## Phase Δ estimate (auto · heuristic n/a)

- phase_delta_lifecycle: estimated
- source: explicit
- heuristic: false
- heuristic_version: n/a
- heuristic_status: n/a
- impact_size: small
- evidence_gate: L-local
- baseline_pct: 07-13 Dashboard · P7.5=46%
- proposed_delta_pct: "P7.5 +2"
- rationale: parsed proposed_delta_pct='P7.5 +2'
- note: explicit FRAME delta preferred over heuristic
- non_claims: ≠ Dashboard write · ≠ Phase closure · 干活≠漲%

## Phase Δ verify

- phase_delta_lifecycle: verified
- proposed_delta_pct: "P7.5 +2"
- checks: {"checks_ok_flag": true, "review_ok_marker": true, "lifecycle_was": "estimated", "has_deltas": true}
- write_candidate: true（仍須 apply_phase_pct=true + 已授權寫入 + --authorize）
- non_claims: ≠ auto Dashboard write · verified ≠ applied
