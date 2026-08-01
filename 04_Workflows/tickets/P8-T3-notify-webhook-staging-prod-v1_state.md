# TICKET STATE · P8-T3-notify-webhook-staging-prod-v1

> handoff 摘要檔。補齊 P8→100 缺口：**真 sandbox／staging／prod webhook** 路徑（經 P7 adapter）。

---

## FRAME

**Goal:**
- 在 P8-T3 mock 之上，提供可對 sandbox／staging／prod 註冊／dispatch 的真實 webhook 路徑（真 HTTP；env gates；不印金鑰）。

**Scope:**
- `delivery/p8_notify_webhook_v1.py`（wrap P7 `send_webhook_notification`）
- CLI readiness／dispatch／list-dlq
- unittest（sandbox 真 localhost HTTP；staging mocked POST；prod allowlist miss）
- docs

**NonScope:**
- ≠ SLA／exactly-once（計畫 §5 → Phase 9）
- ≠ 在 repo 寫死 prod URL／secret
- ≠ 改 P7 adapter 預設行為
- ≠ 取代 mock 探針模組

**AllowedPaths:**
- `delivery/p8_notify_webhook_v1.py`
- `scripts/run_p8_notify_webhook_v1.py`
- `tests/test_p8_notify_webhook_v1.py`
- `docs/phase-8-notify-webhook-v1.md`
- `docs/phase-8-notify-webhook-mock-v1.md`（僅末尾 cross-ref）
- `04_Workflows/tickets/P8-T3-notify-webhook-staging-prod-v1_state.md`

**BlockedPaths:**
- `.env` 原文 · venv · `core/**` · 暗部 · 改 `notification_webhook_adapter_v1.py` 商務邏輯（本票只消費）

**AcceptanceCriteria:**
1. sandbox：真 HTTP POST 收到 `delivery.bundle_ready`
2. staging：allowlist+HMAC 路徑可 dispatch（測試可 mock HTTP transport）
3. prod：allowlist miss 阻擋 POST
4. readiness CLI 僅回 boolean gates，不印 secret
5. unittest 全綠

---

## STATE

- **overall_status:** accepted
- **current_owner:** scribe
- **next_action:** W-PROG uplift
- **last_updated:** 2026-07-13 · same_chat
- **status_by_role:**
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `delivery/p8_notify_webhook_v1.py` (new)
  - `scripts/run_p8_notify_webhook_v1.py` (new)
  - `tests/test_p8_notify_webhook_v1.py` (new)
  - `docs/phase-8-notify-webhook-v1.md` (new)
- verification: |
    ```powershell
    python -m unittest tests.test_p8_notify_webhook_v1 -v
    # → 5 tests OK
    python scripts/run_p8_notify_webhook_v1.py readiness --tier staging
    ```
- deferred_items: SLA／exactly-once；遠端 staging endpoint 實機註冊（須運維 env）
- **proposed_delta**：P8 +4
- **non_claims**：≠ SLA · ≠ repo 內 prod URL · ≠ Phase closure alone

---

## C_REPORT

- conclusion: accepted
- checks_summary: AC-1～5 通過；sandbox 真 HTTP；staging／prod 走 P7 tier 政策；mock 模組未破壞
- risk_level: medium（staging／prod 依賴運維 env；本票交付可呼叫路徑＋閘門）
