# TICKET STATE · P75-G6-alert-sink-contract-v1 · P7.5 真 alert sink 契約（無 UI）

> Full-Phase · P7.5 · **build** · L-local sink · 2026-07-13  
> 延伸：`P75-G5-slo-alert-probe-v1`（probe `would_emit` → **實際本地 sink**）  
> 匯總：`W-PROG-full-line-to-100-wave-plan-2026-07-13`

---

## FRAME

- Goal: 落地 Intake Gate **真本地 alert sink 契約**（file JSONL + stub HTTP）+ schema + unittest；明確 ≠ UI · ≠ prod alert · ≠ Phase closure。
- Scope:
  - MUST：`docs/p75-alert-sink-contract-v1.md`
  - MUST：`shared/schemas/p75_alert_sink_event_v1.json`
  - MUST：`delivery/p75_alert_sink_v1.py` — file sink + stub HTTP recorder
  - MUST：`scripts/run_p75_alert_sink_v1.py` — CLI（可接 probe alerts）
  - MUST：`tests/test_p75_alert_sink_v1.py`
  - MAY：probe doc 交叉引用 G6（最小一句；不改 G5 行為預設）
- NonScope:
  - 不開 Web UI · 不接 PagerDuty／Slack 真送 · 不改 `routing/intake_gate_layer_v1.py`
  - 不改暗部 `alert_event_v1`／monitoring core · 不宣稱 P7.5 closure
  - 不寫 Dashboard 數字格
- AllowedPaths:
  - `docs/p75-alert-sink-contract-v1.md`
  - `docs/p75-intake-gate-slo-alert-probe-v1.md`（僅交叉引用一句）
  - `shared/schemas/p75_alert_sink_event_v1.json`
  - `delivery/p75_alert_sink_v1.py`
  - `scripts/run_p75_alert_sink_v1.py`
  - `tests/test_p75_alert_sink_v1.py`
  - `04_Workflows/tickets/P75-G6-alert-sink-contract-v1_state.md`
- BlockedPaths:
  - `core/**` · 暗部根 · `.github/workflows/**` · Dashboard 數字格
  - 治理母本 · 憲法 §7 類型 · 他人 core · FRAME 外路徑
- Dependencies:
  - P75-G5-slo-alert-probe-v1（done）
  - `docs/p75-intake-gate-slo-alert-probe-v1.md` · `docs/intake-gate-contract-v1.md`
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：契約 doc 含 schema 形狀 + non_claims（≠ UI · ≠ prod · ≠ closure）
  - AC-2：`emit_alerts` file 模式寫入 JSONL（或可覆寫路徑）並回穩定 dict
  - AC-3：stub_http 模式可記錄投遞（無外網；失敗可 `ok:false`+message）
  - AC-4：`python -m unittest tests.test_p75_alert_sink_v1 -v` PASS
  - AC-5：CLI `--format json` 可跑；無硬編本機絕對路徑
  - AC-6：可從 probe alerts[] 映射為 sink events（至少一條路徑）

### Wave Master 擴展

- phase_targets: [P7.5]
- baseline_pct: "07-13 Dashboard · P7.5=46%"
- proposed_delta_pct: "P7.5 +1"
- evidence_gate: L-local
- impact_size: small
- apply_phase_pct: false
phase_delta_lifecycle: verified
- non_claims:
  - ≠ UI · ≠ prod alert · ≠ Grafana · ≠ Phase closure · ≠ 暗部 monitoring 接管

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
  - docs/p75-alert-sink-contract-v1.md
  - shared/schemas/p75_alert_sink_event_v1.json
  - delivery/p75_alert_sink_v1.py
  - scripts/run_p75_alert_sink_v1.py
  - tests/test_p75_alert_sink_v1.py
  - docs/p75-intake-gate-slo-alert-probe-v1.md（交叉引用）
- verification: |
    python -m unittest tests.test_p75_alert_sink_v1 -v → Ran 8 tests OK
    python scripts/run_p75_alert_sink_v1.py --from-probe --mode file --format json → ok=true emitted=0
    stub_http demo emit → ok=true emitted=1
    _phase_pct_apply estimate → P7.5 +1 dry_run write_back=false
- behavior_notes: file JSONL + in-process／loopback stub_http；probe→sink 映射；預設無外網。
- deferred_items: UI · prod PagerDuty／Slack · Grafana · Dashboard apply

### Phase 影響

- **影響 Phase**：P7.5
- **baseline**：46%
- **proposed_delta**：+1
- **實際上調**：否（apply_phase_pct=false）
- **non_claims**：≠ UI · ≠ prod · ≠ closure

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: 8 unittest OK；file／stub_http／force_fail／probe 映射；未改 gate layer；未寫 Dashboard；non_claims 齊。
- risk_level: low
- suggestions: Wave 1 下一張可接 P8.9 T4 sandbox 或 P5 metrics stub

### Phase 影響

- **影響 Phase**：P7.5 · proposed_delta +1 · apply_phase_pct=false 未越權

---

## D_REPORT

- docs_updates: p75-alert-sink-contract-v1.md · probe 交叉引用 · Progress／master_status 末尾
- progress_entry: 見 W-PROG-full-line-to-100 Progress 條
- followup_suggestions: UI→Wave 4；prod wiring 另票

### Phase 影響

- **實際上調**：否

## Phase Δ verify

- phase_delta_lifecycle: verified
- proposed_delta_pct: "P7.5 +1"
- checks: {"checks_ok_flag": true, "review_ok_marker": true, "lifecycle_was": "none", "has_deltas": true}
- write_candidate: true（仍須 apply_phase_pct=true + 已授權寫入 + --authorize）
- non_claims: ≠ auto Dashboard write · verified ≠ applied
