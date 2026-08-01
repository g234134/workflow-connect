# WD-P7-T3-orchestrator-dispatch-full-smoke-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-E follow-up · 源自 Wave-D P7-T1 / P7-T2（orchestrator→dispatch 全鏈 smoke + env-only gate 強化）

---

## FRAME

- **summary**: 補上 Wave-D 仍缺的 **orchestrator → gateway emit → dispatch registry → webhook sandbox** 全鏈 smoke，並讓 **僅 env gate、不開 CLI flag** 時 notification 事件可被 assert（非僅 `result["ok"]`）。

- **goal**:
  - 新增全鏈 integration smoke test 模組：以 `run_agent_standard_case_experiment`（`mode=run`）觸發 `intake.gate_decision` / `delivery.bundle_ready`，經 dispatch registry 到 webhook sandbox mock server。
  - **強化 env-only gate**：只設 env（`GOV_NOTIFICATION_GATEWAY_ENABLED=1` 及 dispatch / webhook 所需 env），**不**傳 `--enable-notifications`；assert outbox / `notification_events.jsonl` / mock POST 收到事件。若 direct Python call 仍因 `notifications_enabled=False` 繞過 env，允許 **極小** 接線修正（函式內合併 `is_enabled_via_env()`，或改以 CLI subprocess 驗證）。
  - 覆蓋 **fail-open**：webhook POST 失敗時 orchestrator 主 `ok` 仍 true；dispatch 錯誤被記錄但不阻斷主流程。
  - 提供可重跑驗證命令（unittest 為主）；B_REPORT 記錄完整 env 矩陣與 mock server 設定。
  - 與 Wave-D P7-T1 / P7-T2 既有 **7+12** tests 互補，不重寫 gateway / webhook adapter 核心邏輯。

- **non_goals**:
  - 不改 notification event schema、jsonl 格式或 outbox 目錄結構（P8.9-T1 範圍）。
  - 不實作 retry / DLQ / HMAC / prod URL / 外網 CI 依賴。
  - 不動 Phase 8.5 bridge、Phase 9 WC M2、`docs/WAVE_PROGRESS_DASHBOARD.md` 百分比。
  - 不將本 smoke 升格為 branch protection required check（CI 接線若做，須 advisory + `continue-on-error: true`）。
  - 不拆分 `intake.gate_decision` accept/reject 為不同 event_type（維持 Wave-D Orchestrator 裁決）。

- **allowed_paths**:
  - `tests/test_orchestrator_dispatch_full_smoke_v1.py`（新增，建議名）
  - `tests/test_orchestrator_notifications.py`（env-only / 全鏈 helper 小改）
  - `tests/test_notification_webhook_dispatch_v1.py`（可抽取共用 MockWebhookServer fixture）
  - `scripts/run_agent_standard_case_experiment.py`（**極小**：僅 env-only 接線與測試預期不一致時修）
  - `delivery/notification_dispatch_v1.py` · `delivery/notification_gateway_v1.py`（**極小** fail-open / env 讀取對齊）
  - `routing/notification_handlers_v1.yaml`（smoke 所需 handler 註解或 allowlist 對齊）
  - `docs/outbox-and-feedback-layer-contract-v1.md`（§4.3–§4.4 補「全鏈 smoke env 矩陣」短段）
  - `04_Workflows/tickets/WD-P7-T3-orchestrator-dispatch-full-smoke-v1_state.md`
  - `.github/workflows/core-agent-smoke.yml` 或 `eval-gate-ci.yml`（**可選** advisory 一步）

- **blocked_paths**:
  - 暗部 `gov_core_system/core/**`
  - `order_ledger/**` · 正式 production delivery bundle 路徑
  - `.env` · secrets / prod webhook URL
  - `docs/WAVE_PROGRESS_DASHBOARD.md` · Phase 百分比
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
  - 非 P7/P8.9 notification 域之大規模重構

- **acceptance_criteria**:
  - **AC-1**：`python -m unittest tests.test_orchestrator_dispatch_full_smoke_v1 -v`（repo 根 cwd）全綠。
  - **AC-2**：env-only 情境（無 `--enable-notifications`、env gate 開）assert 至少一筆 `intake.gate_decision` 寫入 outbox `notifications/` 或 `notification_events.jsonl`。
  - **AC-3**：同情境下 dispatch 觸發 webhook sandbox；mock server 收到至少一筆 POST，payload 含預期 `event_type` / `case_ref`。
  - **AC-4**：webhook 故意失敗時 smoke 主路徑仍 `ok: true`（fail-open 有 assert）。
  - **AC-5**：所有 env / flag 關閉時行為與 Wave-D 基線一致（無 HTTP、無額外 emit）；回歸 `tests.test_orchestrator_notifications` **7/7** · `tests.test_notification_webhook_dispatch_v1` **12/12** 仍全綠。
  - **AC-6**：B_REPORT 列出 env 矩陣（gateway / `GOV_NOTIFICATION_DISPATCH_ENABLED` / webhook / allowlist）與 mock server 用法。
  - **AC-7**（可選）：若接 CI，step 標 advisory、localhost mock only、失敗不阻 merge。

---

## STATE

- **overall_status**: done_with_gaps
- **current_owner**: orchestrator
- **next_action**: 無（文書收口完成 · WD-WG-SCRIBE-REVIEW-closure-v1）
- **last_updated**: 2026-06-22 · scribe
- **notes**: Wave-E 新票；源自 Wave-D Reviewer / Orchestrator 2026-06-20 收口列之 P7 follow-up（全鏈 smoke + env-only gate 證據）
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-20 開票落盤
  - **Implementer (B)**: done — 2026-06-20 全鏈 smoke + env-only 接線
  - **Reviewer (C)**: done — 2026-06-22（文書回填 · 依 Wave-E 收口證據）
  - **Scribe (D)**: done — 2026-06-22

---

## B_REPORT (Implementer)

- **changed_files**:
  - `scripts/run_agent_standard_case_experiment.py` — env-only 接線（見下）
  - `tests/test_orchestrator_dispatch_full_smoke_v1.py` — 新增（5 tests）
  - `tests/test_orchestrator_notifications.py` — 強化 `test_env_gate_enables_notifications` + EnvGate helpers

- **env-only gate 方案**:
  - **極小接線修正**（非純測試層）：`run_agent_standard_case_experiment()` 入口合併 `notifications_enabled = notifications_enabled or is_enabled_via_env()`，與 CLI `main()` 行為對齊；direct Python API 與 subprocess CLI（不傳 `--enable-notifications`）均可 assert outbox/jsonl。
  - 理由：原 `_emit_and_track` 僅看 `notifications_enabled` 參數，env gate 在 CLI 已生效但 Python API 被繞過；Wave-D `test_env_gate_enables_notifications` 亦無 assert。

- **env 矩陣（全鏈 smoke）**:

  | 變數 | 用途 | smoke 值 |
  |------|------|----------|
  | `GOV_NOTIFICATION_GATEWAY_ENABLED` | gateway emit | `1` |
  | `GOV_NOTIFICATION_DISPATCH_ENABLED` | post-emit dispatch registry | `1`（webhook 鏈）/ `0`（subprocess intake-only） |
  | `GOV_NOTIFICATION_WEBHOOK_ENABLED` | webhook handler gate | `1` |
  | `GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST` | case glob | `demo_*,additional_*` |
  | `GOV_NOTIFICATION_WEBHOOK_URL` | mock server | `http://127.0.0.1:<port>/webhook` |

- **mock server**: `tests/test_orchestrator_dispatch_full_smoke_v1.py` 內建 `MockWebhookServer`（127.0.0.1 HTTPServer）；全鏈用 `additional_demo` + `--sandbox-end-to-end` 觸發 `delivery.bundle_ready` → YAML `webhook_dispatch_v1`。

- **驗證命令**（repo 根 cwd）:
  - `python -m unittest tests.test_orchestrator_dispatch_full_smoke_v1 -v` → **5/5 OK**
  - `python -m unittest tests.test_orchestrator_notifications -v` → **7/7 OK**
  - `python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **12/12 OK**

- **AC 自檢**: AC-1~5 滿足；AC-6 見上表；AC-7 CI 未接（可選）。

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-20（文書回填 · 依 Wave-E 收口與 Progress 驗證證據；本輪未追加重跑）
- **reviewer_role**: Wave-E Reviewer (C) · WD-WG-SCRIBE-REVIEW-closure-v1 文書回填
- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無 blocking；gaps 已記錄於 B_REPORT / D_REPORT / suggestions
- **verification_rerun**:
  - `python -m unittest tests.test_orchestrator_dispatch_full_smoke_v1 -v` → **5/5 OK**
  - `python -m unittest tests.test_orchestrator_notifications -v` → **7/7 OK**
  - `python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **12/12 OK**
- **checks_summary**:
  - **AC-1～AC-6 ✅**: 全鏈 smoke + env-only assert outbox/jsonl + mock webhook POST + fail-open；回歸無退化
  - **AC-7 ⚠️**: Wave-G 已接 `.github/workflows/p7-notification-smoke.yml` job **`p7-notification-smoke`**（advisory · `continue-on-error`）；仍非 prod required gate
  - **Rule 3/6/8 ✅**: 極小 env-only 接線；無硬編路徑；未越 BlockedPaths
- **risk_level**: low
- **suggestions**: retry/DLQ/HMAC/prod URL 另票；`intake.gate_decision` accept/reject 仍同 event_type（維持 Wave-D Orchestrator 裁決）

---

## D_REPORT (Scribe)

- **verdict_echo**: Reviewer **`accepted_with_gaps`** — AC-1～AC-6 滿足；全鏈 smoke（5 tests）+ env-only 接線與 Wave-D P7-T1 gap 互補；回歸 **7/7** · **12/12** 無退化。
- **closure_summary**: orchestrator→gateway→dispatch→webhook sandbox 全鏈 integration smoke；env-only gate 極小接線修正。Wave-G 已以 non-blocking advisory CI（`p7-notification-smoke`）部分覆蓋 AC-7，仍保留為非 prod required gate 的 gap。
- **gaps**: 無 retry/DLQ/HMAC/prod URL；`intake.gate_decision` accept/reject 仍同 event_type。
- **progress_entry**: WD-P7-T3 全鏈 smoke + env-only gate — **`accepted_with_gaps`**；dispatch full smoke **5/5** + 回歸 **7/7** · **12/12** OK。
- **scribe_date**: 2026-06-22 · WD-WG-SCRIBE-REVIEW-closure-v1
