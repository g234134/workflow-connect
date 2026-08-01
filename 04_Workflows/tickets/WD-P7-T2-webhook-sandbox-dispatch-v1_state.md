# WD-P7-T2-webhook-sandbox-dispatch-v1 — Ticket State

## FRAME

**Goal**: 落地 P8.9-T4——將 `notification_webhook_adapter_v1.py` skeleton 註冊為 dispatch registry 的第二個 sink，在 sandbox allowlist 下可對 mock HTTP 進行 POST，預設仍為 dry-run / fail-open。

**Scope**:
- 在 `delivery/notification_dispatch_v1.py` 中註冊 webhook handler，形成「local file + webhook」雙 sink 設計
- 更新 `routing/notification_handlers_v1.yaml`，增加對應 webhook handler 設定
- 實作 `delivery/notification_webhook_adapter_v1.py` 最小版本：
  - 由 env `GOV_NOTIFICATION_WEBHOOK_ENABLED` 控制是否啟用
  - 支援 case allowlist（只對特定 case_ref 實際嘗試 POST，其餘 no-op）
  - sandbox：target URL 可以是測試/mock endpoint
- 新增 `tests/test_notification_webhook_dispatch_v1.py`：
  - 測試 env 關閉時，不會發 HTTP
  - env 開啟 + allowlist 命中時，mock server 收到 POST
  - webhook 失敗時 dispatch/主流程仍為 ok（fail-open）
- 在 outbox/feedback docs 裡補一小段 webhook sandbox 說明

**NonScope**:
- 不寫入 prod URL / secret
- 不實作 retry / DLQ / HMAC 簽名
- 不要求 CI 能打外網（可用本地 mock server）
- 不改 gateway emit 的事件 schema/jsonl 格式
- 不做 Slack/Email 真實通道

**AllowedPaths**:
- `delivery/notification_webhook_adapter_v1.py`
- `delivery/notification_dispatch_v1.py`
- `routing/notification_handlers_v1.yaml`
- `tests/test_notification_webhook_dispatch_v1.py`
- `docs/outbox-and-feedback-layer-contract-v1.md`（新增 webhook sandbox 小節）

**BlockedPaths**:
- `scripts/run_agent_standard_case_experiment.py`（P7-T1 範圍）
- `order_ledger/**`
- `.github/workflows/**`
- 暗部 `core/**`

**AcceptanceCriteria**:
- AC-1：預設（env 未開）行為與現網完全一致，不發任何 HTTP
- AC-2：sandbox flag + allowlist case 下，測試時 mock server 能收到至少一個 POST，事件內容與 dispatch 輸入一致
- AC-3：webhook 失敗時，主流程 / orchestrator `ok` 不變，錯誤被記錄為 notify 層訊息
- AC-4：新增 unittest 全綠，並在 B_REPORT 中附上 mock server 測試方式

---

## STATE

- **overall_status**: done
- **current_owner**: orchestrator
- **next_action**: 無（文書收口完成 · WD-WG-SCRIBE-REVIEW-closure-v1）
- **last_updated**: 2026-06-22 · scribe
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-20 關票
  - **Implementer (B)**: done — 2026-06-19
  - **Reviewer (C)**: done — 2026-06-20
  - **Scribe (D)**: done — 2026-06-22

---

## B_REPORT (Implementer)

### §1 變更檔案清單

| 檔案路徑 | 變更類型 | 說明 |
|----------|----------|------|
| `delivery/notification_webhook_adapter_v1.py` | 實作 | 完整實作 sandbox webhook adapter：env 控制、case allowlist、mock HTTP POST、fail-open |
| `delivery/notification_dispatch_v1.py` | 修改 | 新增 `is_webhook_dispatch_enabled()` gate 函式、`HandlerRegistry._handler_enabled()` 支援 `webhook_dispatch` gate、新增 `handle_webhook_dispatch()` handler |
| `routing/notification_handlers_v1.yaml` | 修改 | 新增 `webhook_dispatch_v1` handler 註冊，event_types 包含 `delivery.bundle_ready`, `checkpoint.approved`, `run.completed`，`enabled_when: webhook_dispatch` |
| `tests/test_notification_webhook_dispatch_v1.py` | 新增 | 12 個測試案例，覆蓋 AC-1/AC-2/AC-3，包含 MockWebhookServer 實作 |
| `docs/outbox-and-feedback-layer-contract-v1.md` | 修改 | 新增 §4.4 Webhook sandbox dispatch (WD-P7-T2 / P8.9-T4) 小節，含 env gates、sandbox safety、fail-open guarantee、mock server 範例 |

### §2 Skeleton / Placeholder

| 項目 | 狀態 | 說明 |
|------|------|------|
| Retry / DLQ | skeleton | `notification_webhook_adapter_v1.py` 保留註解標記為 future phase |
| HMAC signature | skeleton | `build_webhook_endpoint_config()` 保留 `secret_key` 欄位但未實作簽名 |
| Non-localhost URL 支援 | placeholder | sandbox v1 僅允許 localhost/127.0.0.1，prod URL 支援待授權 |
| Async HTTP client | skeleton | `HttpClientProtocol` 保留但未實作 async 版本 |

### §3 Placeholder（無）

本次實作無額外 placeholder 待補。

### §4 驗證證據

**命令與結果**：

```powershell
# 執行新增測試
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

**結果**：12/12 測試通過
- `test_is_webhook_enabled_returns_false_when_env_not_set` — AC-1
- `test_send_webhook_disabled_by_env` — AC-1
- `test_send_webhook_allowlist_skip` — AC-1
- `test_webhook_post_to_mock_server_success` — AC-2
- `test_webhook_failure_is_fail_open` — AC-3
- 其他 7 項細節測試（gate、YAML 載入、dispatch 整合）

```powershell
# 既有測試回歸
python -m unittest tests.test_notification_dispatch_v1 -v
```

**結果**：9/9 測試通過（無回歸）

### §5 阻塞

無阻塞。所有 AC 已滿足。

### §6 下一步

1. **Reviewer (C)** 審查 diff 與測試覆蓋率
2. **Scribe (D)** 整理 Progress 末尾條目
3. **Orchestrator (A)** 決定是否關票或轉下一張

### §7 Override / 特殊留痕

無 override。所有變更均在 `AllowedPaths` 範圍內，符合 `ENGINEERING_CONTRACT.md` Rule 3（最小觸及）與 Rule 8（邊界尊重）。

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-20
- **reviewer_role**: Wave-D Reviewer (C)
- **conclusion**: **accepted**
- **blocking_issues**: 無
- **verification_rerun**:
  - `python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **12/12 OK**
- **checks_summary**:
  - **Rule 3 (最小觸及) ✅**: 僅改 adapter / dispatch / YAML / 專用 tests / docs 小節；無無關重構
  - **Rule 6 (路徑權威) ✅**: URL 與 allowlist 全由 env 控制；sandbox 限定 localhost/127.0.0.1；無硬編 prod endpoint
  - **Rule 7 (skeleton 誠實標示) ✅**: B_REPORT 清楚標出 retry/DLQ/HMAC、non-localhost、async client 等 skeleton
  - **Rule 8 (邊界尊重) ✅**: 未改 orchestrator 主程式、暗部 core、CI 工作流
  - **Rule 11 (驗證後宣稱) ✅**: unittest 可重跑且全綠
  - **FRAME / AC-1 ✅**: 預設 env 未開 → dry_run、不發 HTTP
  - **FRAME / AC-2 ✅**: sandbox + allowlist → mock server 收到 POST、payload 一致
  - **FRAME / AC-3 ✅**: HTTP 500 / webhook 失敗 → fail-open、主鏈 ok 不變
  - **FRAME / AC-4 ✅**: unittest 全綠；B_REPORT 含 mock server 測試方式
  - **AllowedPaths ✅**: 變更均在預期路徑內
- **behavior_notes**:
  - YAML handler 與程式內 registry 連線合理
  - 預設不破壞現網行為；sandbox allowlist 護欄足夠
- **risk_level**: low
- **suggestions**:
  - 可選：docs 再一句話描述 HTTP 500 對 downstream 語意（現 fail-open 已合理）
  - 本輪 verdict 維持 **accepted**；無阻擋性問題

---

## D_REPORT (Scribe)

- **verdict_echo**: Reviewer **`accepted`**（2026-06-20）；sandbox webhook 雙 sink 交付完整，無 blocking。
- **closure_summary**: 落地 `notification_webhook_adapter_v1` + dispatch registry 接線；env 關閉時零 HTTP、allowlist 命中時 mock POST、fail-open 已測；`tests.test_notification_webhook_dispatch_v1` **12/12 OK**。Skeleton：retry/DLQ/HMAC/prod URL 仍 deferred。
- **progress_entry**: WD-P7-T2 webhook sandbox dispatch — **`accepted`**；webhook dispatch **12/12 OK**。
- **scribe_date**: 2026-06-22 · WD-WG-SCRIBE-REVIEW-closure-v1
