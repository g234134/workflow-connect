# TICKET STATE · P5-metrics-grafana-stub-v1 · P5 本地 Grafana/JSON 對照 stub（無 UI）

> Full-Phase · P5 · **build** · L-local stub · 2026-07-13  
> Wave 1 隊列 #3（T4 webhook sandbox 已由 WD-P7-T2／P8.9-T4 落地 → 本輪改次選）  
> 匯總：`W-PROG-full-line-to-100-wave-plan-2026-07-13`

---

## FRAME

- Goal: 落地 **本地 Grafana／JSON 對照 stub**——聚合既有 toolchain health + `/metrics` scrape 形狀 + alert_budget 敘事摘要，寫入穩定 JSON；供 Wave 4 Grafana／Operator 讀；明確 ≠ 真 Grafana · ≠ PG soak · ≠ UI · ≠ Phase closure。
- Scope:
  - MUST：`docs/p5-metrics-grafana-stub-contract-v1.md`
  - MUST：`shared/schemas/p5_metrics_grafana_stub_v1.json`
  - MUST：`observability/p5_metrics_grafana_stub_v1.py` — 只讀聚合 + 可選寫 artifact
  - MUST：`scripts/run_p5_metrics_grafana_stub_v1.py` — CLI `--format json`
  - MUST：`tests/test_p5_metrics_grafana_stub_v1.py`
  - MAY：`grafana-pg-soak-deferred-index-v1.md`／fleet operator doc 交叉引用一句；INDEX §1.5 一句
- NonScope:
  - 不部署 Grafana · 不跑 PG soak · 不開 Web UI · 不改暗部 monitoring core
  - 不改 `export_std_case_metrics_v1`／`metrics_http_endpoint_v1` 行為預設
  - 不寫 Dashboard 數字格（`apply_phase_pct=false`）
- AllowedPaths:
  - `docs/p5-metrics-grafana-stub-contract-v1.md`
  - `docs/grafana-pg-soak-deferred-index-v1.md`（僅交叉引用一句）
  - `docs/fleet-metrics-dashboard-operator-v1.md`（僅交叉引用一句）
  - `shared/schemas/p5_metrics_grafana_stub_v1.json`
  - `observability/p5_metrics_grafana_stub_v1.py`
  - `scripts/run_p5_metrics_grafana_stub_v1.py`
  - `tests/test_p5_metrics_grafana_stub_v1.py`
  - `04_Workflows/tickets/P5-metrics-grafana-stub-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md`（末尾 append）
  - `04_Workflows/tickets/W-PROG-full-line-to-100-wave-plan-2026-07-13_state.md`（末尾 append）
- BlockedPaths:
  - `core/**` · 暗部根 · `.github/workflows/**` · Dashboard 數字格
  - 治理母本 · 憲法 §7 類型 · 他人 core · FRAME 外路徑
- Dependencies:
  - WB-T4 toolchain health · MP-METRICS-HTTP · FP-G5-T1／T2（doc 已有）
  - 計劃：`full-line-to-100-wave-plan-2026-07-13.md` §2.3／§3
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：契約 doc 含 schema 形狀 + Wave 4 UI 必讀欄位 + non_claims
  - AC-2：`build_grafana_stub` 回穩定 dict，含 `health.ok` · `metrics.scrape_ok` · `alert_budget_summary`
  - AC-3：預設只讀；`--write` 寫入 repo-relative artifact（無硬編本機絕對路徑）
  - AC-4：`python -m unittest tests.test_p5_metrics_grafana_stub_v1 -v` PASS
  - AC-5：CLI `--format json` 可跑；`ok` 鍵存在
  - AC-6：不啟動 Grafana／不連 PG；失敗回 `ok:false`+`message`（不崩潰）

### Wave Master 擴展

- phase_targets: [P5]
- baseline_pct: "07-13 Dashboard · P5=70%"
- proposed_delta_pct: "P5 +2"
- evidence_gate: L-local
- impact_size: small
- apply_phase_pct: false
phase_delta_lifecycle: verified
- non_claims:
  - ≠ 真 Grafana 部署 · ≠ PG soak · ≠ UI · ≠ Phase closure · ≠ 暗部 monitoring 接管
  - ≠ 擅自大漲 Dashboard %

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
  - docs/p5-metrics-grafana-stub-contract-v1.md
  - shared/schemas/p5_metrics_grafana_stub_v1.json
  - observability/p5_metrics_grafana_stub_v1.py
  - scripts/run_p5_metrics_grafana_stub_v1.py
  - tests/test_p5_metrics_grafana_stub_v1.py
  - docs/grafana-pg-soak-deferred-index-v1.md（L-06 一句）
  - docs/fleet-metrics-dashboard-operator-v1.md（交叉引用一句）
  - 04_Workflows/WORKFLOW_INDEX.md（§1.5 一句）
  - 04_Workflows/tickets/P5-metrics-grafana-stub-v1_state.md
- verification: |
    python -m unittest tests.test_p5_metrics_grafana_stub_v1 -v
    # → 5 tests OK
    python scripts/run_p5_metrics_grafana_stub_v1.py --format json --case-ref demo_phase
    # → ok=true · health.ok · metrics.scrape_ok
- behavior_notes: 只讀聚合 toolchain health + metrics scrape；可選掃 P75 sink；`--write` 才落 artifact
- deferred_items: 真 Grafana／PG soak（FP-G5-T2 Deferred）· Wave 4 UI · Dashboard apply

### Phase 影響

- **影響 Phase**：P5
- **proposed_delta**：+2
- **實際上調**：否（apply_phase_pct=false）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: AC-1…AC-6 對齊；5 unittest OK；CLI ok；無 UI／DarkOps／Dashboard %；non_claims 齊。
- risk_level: low
- suggestions: Wave 1 其餘契約補洞或 Wave 2 後端；微票 Δ 待匯總 authorize

### Phase 影響

- apply_phase_pct=false · 未越權

---

## D_REPORT

- docs_updates: contract · schema · INDEX · grafana deferred L-06 · fleet operator 交叉引用 · plan append
- progress_entry: 本輪 Progress 條
- followup_suggestions: Wave 1 #4 契約補洞 · 或 Wave 2；P8.9 Dashboard 40% 敘事與 T1–T4 已落地對齊可另開 W-PROG

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
- baseline_pct: 07-13 Dashboard · P5=70%
- proposed_delta_pct: "P5 +2"
- rationale: parsed proposed_delta_pct='P5 +2'
- note: explicit FRAME delta preferred over heuristic
- non_claims: ≠ Dashboard write · ≠ Phase closure · 干活≠漲%

## Phase Δ verify

- phase_delta_lifecycle: verified
- proposed_delta_pct: "P5 +2"
- checks: {"checks_ok_flag": true, "review_ok_marker": true, "lifecycle_was": "estimated", "has_deltas": true}
- write_candidate: true（仍須 apply_phase_pct=true + 已授權寫入 + --authorize）
- non_claims: ≠ auto Dashboard write · verified ≠ applied
