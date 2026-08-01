# TICKET STATE · P8-T3-notify-webhook-mock-mvp-v1

> handoff 摘要檔。P8 Notify v1.5 **mock／契約／本地探針** MVP（≠ prod webhook）。

---

## FRAME

<!-- Orchestrator 填 · 2026-07-13 凍結 -->

**Goal:**
- 補齊計畫 P8-T3 的可驗收本地層：mock dispatch → retry 耗盡 → file DLQ → replay CLI（mock sink only）。

**Scope:**
- `delivery/p8_notify_webhook_mock_v1.py`：mock dispatch／DLQ append／list／replay（預設 fail-close 禁真 HTTP）
- `scripts/run_p8_notify_webhook_mock_v1.py`：CLI（dispatch／list-dlq／replay）
- `tests/test_p8_notify_webhook_mock_v1.py`
- `docs/phase-8-notify-webhook-mock-v1.md`（契約 + NonScope prod）
- 本票 state

**NonScope:**
- **不做**真 prod webhook／staging URL／破壞性維運
- 不改 P7 `notification_webhook_adapter_v1` 生產語意；不開 GOV_* prod env 預設
- 不做 Email／Slack／Telegram；不做 Exactly-once／SLA
- 不改 `core/**`、AGENTS、憲法、合約、`.cursor/rules`
- `apply_phase_pct: false`

**AllowedPaths:**
- `delivery/p8_notify_webhook_mock_v1.py`
- `scripts/run_p8_notify_webhook_mock_v1.py`
- `tests/test_p8_notify_webhook_mock_v1.py`
- `docs/phase-8-notify-webhook-mock-v1.md`
- `04_Workflows/tickets/P8-T3-notify-webhook-mock-mvp-v1_state.md`
- `04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md`（僅末尾 append mock MVP 註記）

**BlockedPaths:**
- `core/**` · `delivery/notification_webhook_adapter_v1.py`（本票不改 P7 adapter）
- `AGENTS.md` / 憲法 / 合約 / `.cursor/rules/**`
- `docs/WAVE_PROGRESS_DASHBOARD.md`
- `04_Workflows/project_status/master_status.md`

**Dependencies:**
- P8 plan §2.3 / §3 P8-T3；W7-T3 controlled notify（client summary 語意）
- P7 webhook／DLQ 為參考；本票獨立 mock 命名空間

**relay_mode:** same_chat

**AcceptanceCriteria:**
1. `dispatch` mock：`delivery.bundle_ready` → `ok=true` + `mode=mock` + `delivered_at`（模擬成功）或失敗後寫入 DLQ。
2. 強制失敗路徑：retry max 3 → `retry_exhausted=true` → DLQ jsonl 一筆；`external_http=false`。
3. `replay --dry-run` 回傳可重放摘要；`replay` mock 標記 `replayed_at` 且仍 `external_http=false`。
4. `mode=live`／真 HTTP → fail-close `ok=false`（本票禁止）。
5. `python -m unittest tests.test_p8_notify_webhook_mock_v1 -v` 全綠；docs 誠實標 skeleton／≠ prod。

**Phase 影響（FRAME）:**
```yaml
phase_targets: [P8]
baseline_pct: "07-13 W-PROG-p8-80 · P8=76%"
proposed_delta_pct: "+8"
evidence_gate: L-local
apply_phase_pct: false
```

---

## STATE

- **overall_status:** accepted
- **current_owner:** scribe
- **next_action:** scribe_via_wprog_batch
- **last_updated:** 2026-07-13 · same_chat O/B/C
- **status_by_role:**
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending
- **ac_status:**
  - AC-1: pass
  - AC-2: pass
  - AC-3: pass
  - AC-4: pass
  - AC-5: pass

---

## B_REPORT

- changed_files:
  - `delivery/p8_notify_webhook_mock_v1.py` (new)
  - `scripts/run_p8_notify_webhook_mock_v1.py` (new)
  - `tests/test_p8_notify_webhook_mock_v1.py` (new)
  - `docs/phase-8-notify-webhook-mock-v1.md` (new)
  - `04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md`（末尾 append）
  - `04_Workflows/tickets/P8-T3-notify-webhook-mock-mvp-v1_state.md`
- verification: |
    ```powershell
    python -m unittest tests.test_p8_notify_webhook_mock_v1 -v
    # → 4 tests OK
    python scripts/run_p8_notify_webhook_mock_v1.py dispatch --case-ref demo_phase --force-fail --dlq-path <tmp>
    # → ok=true · retry_exhausted · external_http=false
    ```
- behavior_notes: |
    - mock success 寫 delivered_at；force-fail → retry 3 → DLQ → replay
    - mode=live fail-close；skeleton／≠ prod
- deferred_items: 真 prod webhook／staging URL／SLA；接真 Worker

### Phase 影響

- **影響 Phase**：P8
- **baseline**：07-13 W-PROG-p8-80 · 76%
- **proposed_delta**：+8
- **實際上調**：待 W-PROG
- **non_claims**：≠ prod webhook · ≠ Phase closure · ≠ P7 adapter 替換

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    AC-1～5 通過；4 unittest OK；CLI force-fail→DLQ smoke OK；
    live fail-close；docs non_claims 齊；未改 notification_webhook_adapter_v1。
- risk_level: low
- suggestions: 誠實 100 仍卡真 Worker／真 webhook

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+8
- **實際上調**：待 W-PROG
- **non_claims**：≠ auto-uplift · ≠ prod

---

## D_REPORT

- docs_updates: `docs/phase-8-notify-webhook-mock-v1.md`；plan 末尾缺口註記
- progress_entry: 見 W-PROG 匯總
- followup_suggestions: 真 webhook／真 Worker 另票；勿把 mock 標 100

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+8
- **實際上調**：見 W-PROG
- **non_claims**：≠ Phase closure
