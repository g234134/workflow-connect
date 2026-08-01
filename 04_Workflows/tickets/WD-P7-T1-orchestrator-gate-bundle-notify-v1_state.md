# WD-P7-T1-orchestrator-gate-bundle-notify-v1 — Ticket State

> FRAME / STATE / B_REPORT 待 Orchestrator / Implementer 回填；本檔 C_REPORT 由 Wave-D Reviewer (C) 於 2026-06-20 交付。

---

## STATE

- **overall_status**: done_with_gaps
- **current_owner**: orchestrator
- **next_action**: 無（文書收口完成 · WD-WG-SCRIBE-REVIEW-closure-v1）
- **last_updated**: 2026-06-22 · scribe
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-20 收口裁決
  - **Implementer (B)**: done
  - **Reviewer (C)**: done — 2026-06-20
  - **Scribe (D)**: done — 2026-06-22
- **gap_summary**:
  - env-only gate 測試證據薄（僅 assert run ok，未 assert outbox/notification 寫入）
  - B_REPORT 待 Implementer/Scribe 補寫
  - **Wave-E footnote（2026-06-20）**：Wave-D 當時 env-only gate 與 orchestrator→dispatch 全鏈 smoke gap，已由 **WD-P7-T3** 補齊（`tests.test_orchestrator_dispatch_full_smoke_v1` **5/5 OK** + env-only assert outbox／notification jsonl）；上列兩項保留 Wave-D 審查當下語境。
- **orchestrator_decisions**:
  - **gate 事件語義**：`intake.gate_decision` 涵蓋 accept 與 reject；downstream 以 `type`/`field` 區分，本輪不拆票
- **b_report_note**: B_REPORT 待 Implementer/Scribe 補寫

---

## B_REPORT (Implementer)

### backfill_meta

| 欄位 | 值 |
|------|-----|
| **written_date** | 2026-06-20 |
| **author_role** | Wave-D Implementer (B) · WD-DOC-BREPORT-backfill-v1 |
| **source_refs** | 本票 C_REPORT (2026-06-20) · `00_Agent_Work_Progress.md` Wave-D 收口條目 · `scripts/run_agent_standard_case_experiment.py` · `tests/test_orchestrator_notifications.py` |
| **note** | verification 為**引用** Reviewer 2026-06-20 重跑結果；本 backfill 輪未重新執行 unittest |

### §1 變更檔案清單

| 檔案路徑 | 變更類型 | 說明 |
|----------|----------|------|
| `scripts/run_agent_standard_case_experiment.py` | 修改 | S3 gate 後 emit `intake.gate_decision`（run mode；payload 含 `decision` / `risk_level` / `intake_decision_id` 等）；S10 sandbox delivery 成功時 emit `delivery.bundle_ready`；經 `emit_notification_safe` fail-open 包裝 |
| `tests/test_orchestrator_notifications.py` | 新增 | 7 個 unittest，覆蓋 flag on/off、fail-open、bundle_ready sandbox、env gate、CLI 優先 |

### §2 Skeleton / Placeholder

| 項目 | 狀態 | 說明 |
|------|------|------|
| orchestrator→dispatch 全鏈 smoke | skeleton | 本票僅驗證 orchestrator emit 至 outbox/notification 層；未接 webhook / dispatch handler 端到端 |
| env-only gate 斷言 | placeholder | `test_env_gate_enables_notifications` 僅 assert run `ok`，未 assert outbox/jsonl 實際寫入（見 known_gaps） |

### §3 Placeholder（無）

本次實作無額外 placeholder 待補（除 §2 所列 deferred）。

### §4 驗證證據

> **來源**：Wave-D Reviewer (C) · 2026-06-20 重跑；**非**本 backfill 輪現場執行。

**命令與結果**：

```powershell
# cwd: 戰車根
python -m unittest tests.test_orchestrator_notifications -v
```

**結果**：**7/7 OK**

- `test_enable_notifications_emits_intake_gate_decision` — CLI flag 開啟時 emit `intake.gate_decision`
- `test_enable_notifications_emits_delivery_bundle_ready_sandbox` — sandbox bundle 路徑 emit `delivery.bundle_ready`
- `test_disable_notifications_no_events_emitted` — 預設/關閉時不 emit
- `test_notification_failure_does_not_block_orchestrator` — fail-open；orchestrator `ok` 不變
- `test_notification_events_tracked_in_result` — result 內追蹤 notification 摘要
- `test_env_gate_enables_notifications` — env gate 路徑（證據偏薄，見 §behavior_notes）
- `test_cli_flag_overrides_env_disable` — CLI flag 獨立啟用並 assert 有寫出

### §5 阻塞

無 blocking。Reviewer 結論：**accepted_with_gaps**。

### §6 behavior_notes

- **fail-open**：`emit_notification_safe` 捕獲例外，不讓 orchestrator 主流程 `ok` 變 false；unittest 已覆蓋。
- **gate 開關**：預設關閉；僅 `--enable-notifications` CLI flag 或 env gate 開啟時 emit。
- **`intake.gate_decision` 語義（Orchestrator 裁決）**：accept **與** reject 均會 emit；downstream 須依 payload 欄位（`decision` / `risk_level` 等）區分，**不可**僅依事件名稱假設「僅 accepted」；本輪不拆票。
- **env-only gap**：僅開 env、不給 CLI flag 時，測試僅 assert run `ok`，未 assert notification jsonl/outbox 實際寫入；證據偏弱但**非**本輪修復項。

### §7 known_gaps / deferred_items

| Gap | 現狀 | 後續 |
|-----|------|------|
| 正式 B_REPORT 缺失 | 本段 backfill 補齊 | — |
| env-only gate 測試證據薄 | `test_env_gate_enables_notifications` 未 assert 寫入 | 建議強化 assert outbox/notification jsonl；非 Wave-D 阻擋 |
| orchestrator→dispatch 全鏈 smoke | 未覆蓋 | 可選後續票「P7-T3 orchestrator→dispatch 全鏈 smoke」 |
| reject case 亦 emit | 已裁決為預期行為 | downstream 讀 payload，不另開票 |

> **Wave-E footnote（2026-06-20）**：上表 env-only gate 證據薄與全鏈 smoke「未覆蓋」為 Wave-D 當下狀態；**WD-P7-T3** 已交付 env-only 接線 assert + 全鏈 smoke **5/5 OK**（回歸 **7/7** · **12/12** 無退化）。本 parent 票 STATE verdict 不變。

### §8 下一步

1. **Scribe (D)** 填 D_REPORT 並末尾追加 Progress。
2. **Wave-E（可選）** 強化 env-only gate unittest。
3. **Wave-E（可選）** P7-T3 全鏈 smoke。

### §9 Override / 特殊留痕

無 override。變更集中於 orchestrator script + 專用 tests；未動 gateway core、webhook adapter、暗部 `core/**`、CI。

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-20
- **reviewer_role**: Wave-D Reviewer (C)
- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無
- **verification_rerun**:
  - `python -m unittest tests.test_orchestrator_notifications -v` → **7/7 OK**
- **checks_summary**:
  - **Rule 3 (最小觸及) ✅**: 變更集中在 `run_agent_standard_case_experiment.py` 的 S3 gate / S10 bundle hook 與 `tests/test_orchestrator_notifications.py`；未見無關重構
  - **Rule 6 (路徑權威) ✅**: 使用相對於 script 的 repo root；outbox 走既有 override；無硬編絕對磁碟路徑
  - **Rule 7 (skeleton 誠實標示) ❌**: repo 無本票正式 B_REPORT；邊界僅能從測試 docstring 推斷
  - **Rule 8 (邊界尊重) ✅**: 未動暗部 core / CI / 治理母本；通知仍經既有 gateway
  - **Rule 11 (驗證後宣稱) ✅**: `tests.test_orchestrator_notifications` 7/7 全過；含 fail-open、flag off、bundle_ready sandbox
  - **FRAME / Scope ✅**: 核心交付（gate/bundle 路徑 emit `intake.gate_decision` / `delivery.bundle_ready`；flag/環境關閉時不 emit；失敗 fail-open）與 Wave-D 設計一致
  - **FRAME / Scope ⚠️**: `intake.gate_decision` 對 reject case 也會 emit；若原設計僅 cover accepted，需 Orchestrator 明確定義
  - **AllowedPaths ✅**: diff 僅在 orchestrator + tests；符合「不動 gateway core、不動 webhook」意圖
- **behavior_notes**:
  - **fail-open**: `emit_notification_safe` 捕獲例外、不讓 orchestrator `ok` 變 false；測試覆蓋
  - **gate 開關**: 預設關閉；僅 CLI flag 或 env gate 打開才 emit
  - **env-only gap**: 只開 env、不給 CLI flag 時，測試僅 assert run `ok`，未 assert 實際事件寫出；證據偏弱
- **test_coverage**:
  - happy / disable / fail-open 均有
  - env gate 行為較薄
- **b_report_gap**: 票 `_state.md` / 正式 B_REPORT 於審查時不存在
- **risk_level**: low
- **suggestions**:
  - 補本票 B_REPORT（含 changed_files、verification）
  - 強化 `test_env_gate_enables_notifications`：env-only 情境 assert outbox/notification jsonl 寫入
  - 可選後續票「P7-T3 orchestrator→dispatch 全鏈 smoke」；不阻擋本輪 accepted_with_gaps

---

## D_REPORT (Scribe)

- **verdict_echo**: Reviewer **`accepted_with_gaps`**（2026-06-20）；Wave-E **WD-P7-T3** 已補 env-only gate assert 與 orchestrator→dispatch 全鏈 smoke。
- **closure_summary**: 交付 orchestrator 路徑 emit `intake.gate_decision` / `delivery.bundle_ready`（fail-open）；`tests.test_orchestrator_notifications` **7/7 OK**。已知 gap：`intake.gate_decision` accept/reject 共用 event_type（Wave-D 裁決不拆票）；Wave-D env-only 證據薄已由 P7-T3 接線補強。
- **progress_entry**: WD-P7-T1 orchestrator gate/bundle notify — **`accepted_with_gaps`**；notifications **7/7 OK**。
- **scribe_date**: 2026-06-22 · WD-WG-SCRIBE-REVIEW-closure-v1
