# Wave 3 · G7 + gate + notify + alert sink + MP-SMOKE 串線煙霧包

> **票**：`W3-SMOKE-g7-gate-notify-mp-chain-v1`  
> **性質**：可重跑 **L-local** 串線驗證（整合煙霧前置／最小煙霧包）  
> **實作**：`delivery/wave3_smoke_chain_v1.py` · `scripts/run_wave3_smoke_chain_v1.py`  
> **計劃**：`04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md` Wave 3

---

## §0 non_claims

| 禁止宣稱 | 說明 |
|----------|------|
| ≠ prod / required GitHub CI | 僅本機／可選 local CI wrapper |
| ≠ Web UI／Operator 面 | UI 仍 Wave 4（等照片／凍結） |
| ≠ Dashboard Phase% authorize | 本票 `apply_phase_pct=false`；僅 estimate |
| ≠ DarkOps／暗部 `app_api` | 不改暗部根 |
| ≠ Phase closure | 煙霧綠 ≠ 全線 100% |
| ≠ 改 gate 決策本體 | 只配線既有 G7／CLI／notify／G6／MP-SMOKE |

---

## §1 串線步驟

| # | `step_id` | 做什麼 | 預期 |
|---|-----------|--------|------|
| 1 | `g7_http_preview` | G7 `handle_gate_request` · `mode=preview` | `ok=true` · HTTP 200 · gate.ok |
| 2 | `gate_layer_preview_parity` | 同案 `evaluate_intake_gate` preview 對齊 G7 `decision` | `g7_decision == layer_decision` |
| 3 | `g7_http_run_notify` | G7 `mode=run` + `enable_notifications` | outbox 記錄 + notify `ok` |
| 4 | `alert_sink_file` | G6 `emit_alerts` → 隔離 outbox JSONL | `emitted>=1` · delivered |
| 5 | `mp_smoke` | 呼叫既有 `run_multi_phase_smoke_v1` 七步 | `multi_phase_smoke.ok=true` |

頂層摘要：`schema_version=wave3_smoke_chain_v1` · `ok` · `steps[]` · `failed_steps` · `non_claims`。

---

## §2 命令（可重跑）

```powershell
# 全串（含 MP-SMOKE）
python scripts/run_wave3_smoke_chain_v1.py --case-ref demo_phase --format json

# 僅前四步（快測）
python scripts/run_wave3_smoke_chain_v1.py --case-ref demo_phase --skip-mp-smoke --format text

# unittest
python -m unittest tests.test_wave3_smoke_chain_v1 -v
```

**預期**：頂層 `ok=true` · `failed_steps=[]` · 五步皆 `ok`。

隔離 outbox（建議本機）：

```powershell
python scripts/run_wave3_smoke_chain_v1.py --case-ref demo_phase --outbox-root outbox/_wave3_smoke_tmp --format json
```

---

## §3 與既有 runner 關係

| 組件 | 關係 |
|------|------|
| G7 HTTP stub | 步驟 1／3 直接呼叫 |
| Gate CLI／layer | 步驟 2 對齊；CLI 仍可獨立跑 |
| Notify gateway | 經 G7 `enable_notifications` |
| G6 alert sink | 步驟 4 薄配線（gate 決策信號 → file sink） |
| MP-SMOKE | 步驟 5 複用七步；**不**重寫 MP 邏輯 |

---

## §4 Wave 3 GO 建議

| 條件 | 本輪 |
|------|------|
| 串線 CLI／unittest 綠 | **通過 → Wave 3 煙霧 GO** |
| Wave 4 UI | **仍等**用戶照片／欄位凍結；**不**因煙霧綠自動開 UI |
| P2 `--execute` | 仍 blocked（另票） |
| Dashboard % | 未 authorize |

---

## Changelog

| 日期 | 變更 |
|------|------|
| 2026-07-13 | 初版 · W3-SMOKE-g7-gate-notify-mp-chain-v1 |
