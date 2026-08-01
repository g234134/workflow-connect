# TICKET STATE · P75-G5-slo-alert-probe-v1 · Intake Gate SLO／alert 探針

> Full-Phase · P7.5 · **build** · L-local probe · 2026-07-13  
> 對齊：Dashboard P7.5「UI / SLO / alert 未做」缺口最小增量

---

## FRAME

- Goal: 落地 Intake Gate **最小可驗收** SLO／alert 探針（本地 fixture · dry-run dict · 不發外網）。
- Scope:
  - MUST：`docs/p75-intake-gate-slo-alert-probe-v1.md`
  - MUST：`scripts/run_intake_slo_alert_probe_v1.py` — 穩定 dict（ok／slo／alerts／would_emit）
  - MUST：`tests/fixtures/intake_slo_probe_sample_v1.json` + `tests/test_intake_slo_alert_probe_v1.py`
- NonScope:
  - 不改 `routing/intake_gate_layer_v1.py` · 不接 PagerDuty／Slack 真送 · 不做 UI · 不宣稱 P7.5 closure
  - 不做 P7 Round-2 · WC-PRE
- AllowedPaths:
  - `docs/p75-intake-gate-slo-alert-probe-v1.md`
  - `scripts/run_intake_slo_alert_probe_v1.py`
  - `tests/fixtures/intake_slo_probe_sample_v1.json`
  - `tests/test_intake_slo_alert_probe_v1.py`
  - `04_Workflows/tickets/P75-G5-slo-alert-probe-v1_state.md`
- BlockedPaths:
  - `core/**` · 暗部 · `.github/workflows/**` · Dashboard 數字格（本票）
  - 治理母本 · 憲法 §7 類型 · 他人 core
- Dependencies:
  - P75-G2/G3/G4／P75-REG（已落地；本票不重開 gate）
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：CLI `--format json` → 穩定 dict 含 `ok`／`slo`／`alerts`
  - AC-2：`--emit-alert` 僅 `would_emit`；不寫外部 sink
  - AC-3：`python -m unittest tests.test_intake_slo_alert_probe_v1 -v` PASS
  - AC-4：doc 含 non_claims（≠ prod alert／Grafana）
  - AC-5：無硬編本機絕對路徑

### Wave Master 擴展

- phase_targets: [P7.5]
- baseline_pct: "07-13 W-PROG-B · P7.5=45%"
- proposed_delta_pct: "P7.5 +1"
- evidence_gate: L-local
- impact_size: small
- apply_phase_pct: false
- non_claims:
  - ≠ prod alert · ≠ Grafana · ≠ gate logic change · ≠ Phase closure

---

## STATE

- overall_status: done
- current_owner: none
- next_action: 無 · 已 accepted；P7.5 Δ 由 W-PROG-triple-batch 匯總
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
  - docs/p75-intake-gate-slo-alert-probe-v1.md
  - scripts/run_intake_slo_alert_probe_v1.py
  - tests/fixtures/intake_slo_probe_sample_v1.json
  - tests/test_intake_slo_alert_probe_v1.py
- verification: |
    python -m unittest tests.test_intake_slo_alert_probe_v1 -v → Ran 7 tests OK
    python scripts/run_intake_slo_alert_probe_v1.py --format json → ok=true
- behavior_notes: latency/error_rate 閾值探針；critical → ok=false；無外送。
- deferred_items: 真 alert sink／Grafana → 另票

### Phase 影響

- **影響 Phase**：P7.5
- **baseline**：07-13 W-PROG-B · 45%
- **proposed_delta**：+1
- **實際上調**：待 W-PROG-triple-batch-2026-07-13
- **non_claims**：≠ prod alert

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: 7 unittest OK；CLI ok；未改 gate layer；未寫 Dashboard。
- risk_level: low
- suggestions: 後續可接 metrics HTTP 對照（另票）

### Phase 影響

- **影響 Phase**：P7.5 · proposed_delta +1 · apply_phase_pct=false 未越權

---

## D_REPORT

- docs_updates: p75-intake-gate-slo-alert-probe-v1.md
- progress_entry: 見 W-PROG-triple-batch Progress 條
- followup_suggestions: UI／真 alert 另開

### Phase 影響

- **實際上調**：見 W-PROG 匯總
