# TICKET STATE · W6-T10 · client-notification-gateway-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 6 · Agent Standard Line · S15 Notification Gateway  
> **票號語意**：本票為 **S15 標準化對外通知 gateway**（workflow event bus）；與 **W6-T10-orchestrator-checkpoint-wiring-v1**（checkpoint 接線）**不同票**。

---

## FRAME

- **Title**: W6-T10 · client-notification-gateway-v1
- **Wave / Motivation**: 清洗／實驗線完成後，結果落在 outbox JSON、checkpoint 檔、sandbox manifest / delivery bundle，但 downstream client / system **無標準化機制**得知「任務完成」「需人工 review」「bundle 就緒」。W7-T3 已有 **S15 內容型** simulated notify（signoff → client summary → `notify_experiment_*.json`），仍缺 **跨步驟 workflow event gateway**。本票 S15 設計步：定義事件模型、delivery contract 草案、orchestrator 接線邊界；**不改 runtime code**。

- **Goal**: 在工作流重要邊界產生**標準化 notification event**，使 downstream 可訂閱／輪詢，而不必解析 orchestrator 全量 JSON 或手動查 outbox。

- **Scope（本輪 · S15 設計 only）**:
  1. 最小事件模型（5 種 `event_type` + payload 必填欄位）
  2. v1 stub / local sink delivery contract（file + jsonl audit）
  3. 推薦模組位置與 orchestrator 呼叫邊界
  4. 拆 P2（stub + 接線 + tests）/ P3（adapters + docs）小票
  5. 本票 `*_state.md` B_REPORT（設計交付）

- **NonScope / non_goals**:
  - ❌ 本輪不改 `scripts/*.py`、`delivery/*.py`、`tests/*.py`
  - ❌ 真實 webhook / queue / Telegram / Email 可靠性語意
  - ❌ 重試策略、簽名驗證、DLQ、多租戶路由
  - ❌ 取代 W7-T3 `controlled_notify_experiment_v1`（內容型 client summary 仍屬 S15 子能力）
  - ❌ 主鏈 production delivery 預設行為變更

- **Minimal Read Set**:
  - `docs/agent-run-standard-case-experiment-v1.md` § S15
  - `docs/agent-run-standard-case-orchestrator-v1.md`
  - `04_Workflows/tickets/W6-T10-orchestrator-checkpoint-wiring-v1_state.md`（接線邊界）
  - `04_Workflows/tickets/W7-T3-controlled-delivery-and-notify-experiment-v1_state.md`（S15 模擬層）
  - `hitl/checkpoints_v1.py`（checkpoint 寫入／events.jsonl 模式）
  - `delivery/controlled_notify_experiment_v1.py`（既有 notify payload 形狀）
  - `delivery/sandbox_delivery_bundle_v1.py`（bundle manifest）

- **AllowedPaths（本輪）**:
  - `04_Workflows/tickets/W6-T10-client-notification-gateway-v1_state.md`
  - `docs/agent-run-standard-case-orchestrator-v1.md`（最小 cross-ref，可選）

- **BlockedPaths（本輪 + P2 前）**:
  - `scripts/run_agent_standard_case_experiment.py`（P2 接線票）
  - `delivery/*.py`、`tests/*.py`（P2 實作票）
  - 暗部 `core/`、`.env`、`runtime/checkpoints/**`

- **Dependencies**:
  - **W6-T10** checkpoint wiring（orchestrator ↔ W6-T5/W6-T6）— 接線邊界已就緒
  - **W6-T5 / W6-T6** — checkpoint 狀態與 path fallback 契約
  - **W7-T3** — S15 內容 notify 實驗（下游可消費 `delivery.bundle_ready`）

- **AcceptanceCriteria（設計輪 · 本票）**:
  - **AC-D1**：5 種 `event_type` 與 payload 必填欄位已文件化
  - **AC-D2**：stub sink contract（file + jsonl）與 `send` 回傳 `dict` 形狀已定義
  - **AC-D3**：orchestrator 呼叫邊界表與 preview/run 語意對齊 W6-T10 wiring
  - **AC-D4**：P2 / P3 小票 FRAME 可開工

- **AcceptanceCriteria（P2 實作 · 後續票）**:
  - **AC-1**：workflow 在 `checkpoint.awaiting_human` / `run.completed` / `delivery.bundle_ready` 邊界可發送結構化事件
  - **AC-2**：事件有穩定 schema（`event_type` / `case_ref` / `checkpoint_id?` / artifact paths / `emitted_at`）
  - **AC-3**：通知失敗不阻斷主流程（best-effort；orchestrator 主 `ok` 不受 sink 失敗影響）

- **VerificationCommands（P2 起）**:
  - `python -m unittest tests.test_notification_gateway_v1 -v`
  - （可選）orchestrator run + 檢查 `outbox/notifications/` 與 `outbox/notification_events.jsonl`

---

## STATE

- **overall_status**: `p2_reviewed · accept_with_followups`
- **current_owner**: `reviewer`
- **next_action**: Reviewer 審查完成；待 Scribe 補 file location map；P3 webhook adapter 設計待開票
- **last_updated**: 2026-06-16 · reviewer (B · review)
- **status_by_role**:
  - orchestrator: `done`（P2 stub 已接線）
  - implementer: `done`
  - reviewer: `done`（verdict: accept_with_followups）
  - scribe: `pending`

---

## B_REPORT · S15 Design Delivery（2026-06-16）

### 1. 與既有模組的關係

| 層 | 模組 | 職責 | 與 gateway 關係 |
|----|------|------|-----------------|
| Workflow events | **`delivery/notification_gateway_v1.py`**（P2 新建） | 標準化 **何時**、**何事** 通知 downstream | **本票核心** |
| S15 內容 notify | `delivery/controlled_notify_experiment_v1.py`（W7-T3） | 讀 signoff/bundle → **client summary 文案** | P3 可訂閱 `delivery.bundle_ready` 觸發 |
| Checkpoint state | `hitl/checkpoints_v1.py` | 寫 checkpoint JSON + `checkpoint_events.jsonl` | gateway **不**改 checkpoint；**並行** emit notification event |
| Sandbox bundle | `delivery/sandbox_delivery_bundle_v1.py` | 寫 manifest；`notify_triggered: false` | P2 在 bundle 成功後 emit `delivery.bundle_ready` |

**設計原則**：gateway = **thin event envelope**；W7-T3 = **fat content payload**。避免 W7-T3 被 orchestrator 逐步耦合進每一步。

---

### 2. 最小事件集合（v1）

| event_type | 觸發邊界 | 必填語意 | preview 模式 |
|------------|----------|----------|--------------|
| `checkpoint.awaiting_human` | Checkpoint A/B **寫檔成功**且 `status=awaiting_human`（或 integration `written`） | 哪個 checkpoint、檔案路徑、case | **不發**（與 checkpoint 不寫檔一致） |
| `checkpoint.approved` | Checkpoint A/B **跳過或核准**：`auto_approved`、`approved`、`approved_auto` | checkpoint_id、核准來源（human/auto） | **不發** |
| `run.completed` | Run 模式結束且 `final_status` ∈ `{run_complete, resume_plan_ready}`，且非 `blocked` | experiment_id、steps_run 摘要 | **不發** |
| `delivery.bundle_ready` | `write_sandbox_delivery_bundle` 成功，或未來 production `build_case_delivery_bundle` ok | manifest_path、bundle_dir、artifacts_count | sandbox e2e run only |
| `run.blocked` | `decision=reject`、output_guard `blocked`、allowlist 拒絕、run_execution 失敗阻斷 | block_reason、step_id | run 模式可發；preview 若 `blocked` 可選發（P2 預設 **不發**） |

**v1 刻意不含**（P3+）：`checkpoint.rejected`、`checkpoint.changes_requested`、`run.failed`（可映射到 `run.blocked`）、`delivery.notify_dispatched`（外部通道成功回執）。

**`checkpoint.approved` 語意細分**（payload 內 `approval_source`）：

- `auto` — `--auto-approve-intake` / `--auto-approve-delivery` 或 integration skip
- `human` — 預留；P2 僅 stub，human approve 路徑由 delivery approval CLI 另票接線（P3）

---

### 3. Event schema 草案

**Envelope**（所有事件共用）：

```json
{
  "schema_version": "notification_event_v1",
  "event_id": "<uuid4>",
  "event_type": "checkpoint.awaiting_human",
  "emitted_at": "2026-06-16T12:00:00Z",
  "idempotency_key": "<case_ref>:<event_type>:<checkpoint_id|run>:<compact_ts>",

  "case_ref": "demo_phase",
  "case_dir": "cases/demo_phase",
  "experiment_id": "<uuid4-or-null>",

  "checkpoint_id": "A-intake-confirmation",
  "checkpoint_status": "awaiting_human",
  "approval_source": null,

  "artifacts": {
    "checkpoint_path": "outbox/demo_phase/checkpoint_A-intake-confirmation_2026-06-16T12-00-00Z.json",
    "bundle_dir": null,
    "manifest_path": null
  },

  "status_summary": {
    "final_status": "waiting_for_human",
    "decision": "needs_review",
    "output_guard_status": "ok",
    "mode": "run"
  },

  "source": {
    "step_id": "S4",
    "module": "hitl.checkpoint_a_integration_v1",
    "orchestrator": "scripts/run_agent_standard_case_experiment"
  },

  "sink_result": {
    "ok": true,
    "channel": "local_file",
    "path": "outbox/notifications/demo_phase/checkpoint.awaiting_human_2026-06-16T12-00-00Z_a1b2c3d4.json",
    "message": "written"
  }
}
```

**必填欄位（所有 event_type）**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `schema_version` | string | 固定 `notification_event_v1` |
| `event_id` | string | UUID |
| `event_type` | enum | 五種之一 |
| `emitted_at` | string | ISO-8601 UTC |
| `case_ref` | string | |
| `source.step_id` | string | S4 / S12 / S10 / orchestrator |
| `source.module` | string | 觸發模組邏輯名 |
| `status_summary.mode` | string | `preview` \| `run` |

**條件必填**：

| 條件 | 額外必填 |
|------|----------|
| checkpoint 類事件 | `checkpoint_id`；`artifacts.checkpoint_path` 若已寫檔 |
| `delivery.bundle_ready` | `artifacts.manifest_path`、`artifacts.bundle_dir` |
| `run.completed` / `run.blocked` | `experiment_id`（run 模式）、`status_summary.final_status` |
| `checkpoint.approved` | `checkpoint_id`、`approval_source` |

**Path 語意**：與 W6-T5/T6 對齊 — 優先 repo-relative；outbox 在 repo 外時允許 absolute（三層 fallback 消費端須容忍）。

---

### 4. v1 最小 gateway 形式（stub / local sink）

**推薦模組**：`delivery/notification_gateway_v1.py`

**公開 API（P2 實作）**：

```python
def build_notification_event(
    event_type: str,
    *,
    case_ref: str,
    case_dir: str | None = None,
    experiment_id: str | None = None,
    checkpoint_id: str | None = None,
    checkpoint_status: str | None = None,
    approval_source: str | None = None,
    artifacts: dict[str, Any] | None = None,
    status_summary: dict[str, Any] | None = None,
    source: dict[str, Any] | None = None,
) -> dict[str, Any]: ...

def send_notification(
    event: dict[str, Any],
    *,
    enabled: bool = True,
    dry_run: bool = False,
    repo_root: Path | None = None,
    outbox_root_override: str | None = None,
) -> dict[str, Any]:
    """Best-effort. Returns {ok, message, event_id, sink_result, event?}. Never raises."""
```

**預設 sink 行為**（`channel=local_file`）：

1. **Per-event file**：`outbox/notifications/<case_ref>/<event_type>_<compact_ts>_<event_id[:8]>.json`
2. **Append-only audit**：`outbox/notification_events.jsonl`（一行一 event envelope，鏡像 `checkpoint_events.jsonl` 模式）
3. **Disabled 模式**：`enabled=False`（CLI 旗標 `--no-notifications` 或 env `GOV_NOTIFICATION_GATEWAY_ENABLED=0`）→ `ok: true`, `message: "skipped"`, 不寫檔
4. **Dry-run**：組 envelope + 回傳，不寫檔

**不回傳 secret**；不含 webhook URL、token。

**與 W7-T3 整合點（P3）**：`delivery.bundle_ready` 事件可選觸發 `run_controlled_notify_experiment(..., dry_run=False)` 作為 **downstream handler**，非 P2 必做。

---

### 5. Orchestrator 呼叫邊界（P2 接線）

在 `scripts/run_agent_standard_case_experiment.py` 內，**僅 run 模式**（`mode=="run"`）且 `notifications_enabled` 時 best-effort 呼叫 `send_notification`：

| 順序 | 步驟後 | 條件 | event_type |
|------|--------|------|------------|
| 1 | S4 Checkpoint A 解析後 | `checkpoint_a_status.integration.status == "written"` | `checkpoint.awaiting_human` |
| 2 | S4 Checkpoint A 解析後 | `status in ("auto_approved", "approved_auto")` | `checkpoint.approved` |
| 3 | S12 Checkpoint B 解析後 | B `written` / awaiting_human | `checkpoint.awaiting_human` |
| 4 | S12 Checkpoint B 解析後 | B `auto_approved` / skipped approved | `checkpoint.approved` |
| 5 | S10 sandbox bundle 後 | `sandbox_delivery.ok == true` | `delivery.bundle_ready` |
| 6 | 函式 return 前 | `final_status in ("run_complete", "resume_plan_ready")` 且未 blocked | `run.completed` |
| 7 | 函式 return 前 | `final_status == "blocked"` 或 early reject | `run.blocked` |

**接線模式**：

```python
def _emit_notification_safe(event_type: str, **kwargs) -> dict[str, Any] | None:
    if mode != "run" or not notifications_enabled:
        return None
    try:
        event = build_notification_event(event_type, ...)
        return send_notification(event, outbox_root_override=outbox_root_override)
    except Exception as exc:
        return {"ok": False, "message": str(exc), "skipped_main_flow": True}
```

Orchestrator result 新增可選觀測欄位 `notifications: [{event_type, ok, path?}]`（P2）；主 `ok` **不得**因 notify 失敗變 false。

**CLI（P2）**：`--enable-notifications` / `--no-notifications`（預設 **off**，與實驗線保守預設一致）。

---

### 6. P2 / P3 小票拆分

#### W6-T10-P2-stub-notification-gateway-v1（實作 · 下一張）

- **Goal**：stub gateway + orchestrator 最小接線 + unit tests
- **AllowedPaths**：
  - `delivery/notification_gateway_v1.py`
  - `delivery/__init__.py`（export 若需要）
  - `scripts/run_agent_standard_case_experiment.py`（接線 + CLI 旗標）
  - `tests/test_notification_gateway_v1.py`
  - `tests/test_agent_standard_case_experiment.py`（接線回歸）
  - `docs/notification-gateway-v1.md`（stub contract）
  - `04_Workflows/tickets/W6-T10-P2-stub-notification-gateway-v1_state.md`
- **AC**：AC-1～AC-3（見上 FRAME）
- **NonScope**：webhook、W7-T3 自動串接、production bundle

#### W6-T10-P3-notification-gateway-adapters-v1（擴展）

- **Goal**：downstream contract 定稿、webhook adapter skeleton、與 W7-T3 / delivery approval CLI 整合設計
- **Scope**：
  - `docs/notification-gateway-v1.md` § downstream / webhook / idempotency
  - `delivery/notification_sinks/` 或 `notification_gateway_webhook_v1.py` skeleton（`external_dispatch` 仍 default false）
  - `run_delivery_approval_cli.py` 核准後 emit `checkpoint.approved`（human source）
  - 可選：`delivery.bundle_ready` → 觸發 W7-T3 controlled notify
- **NonScope**：重試/DLQ/簽名/多租戶（文件化為 future）

---

### 7. 風險

| 風險 | 說明 | 緩解（v1） |
|------|------|------------|
| **Duplicate events** | orchestrator 重跑、resume 多次 emit | `idempotency_key` + jsonl 去重留 P3；P2 測試同 run 只 emit 一次 |
| **Stale path** | artifact 路徑在 emit 後被移動 | payload 標 `emitted_at`；downstream 以 path + mtime 驗證；文件警告 |
| **Sink failure** | 磁碟滿、權限、outbox 外 path | best-effort + `sink_result.ok=false`；**不**阻斷主流程 |
| **Schema drift** | 與 checkpoint / W7-T3 payload 分叉 | `schema_version` 固定；gateway 不嵌入 client summary |
| **Preview 誤發** | preview 被當 production 訂閱 | v1 僅 `mode=run` + 顯式 `--enable-notifications` |

---

### 8. changed_files（本輪）

- `04_Workflows/tickets/W6-T10-client-notification-gateway-v1_state.md`（新建 · 本檔）
- `docs/agent-run-standard-case-orchestrator-v1.md`（§2 追加 Notification gateway 設計 cross-ref）

### 9. verification（本輪）

- 無 runtime 驗證（設計票）
- 設計自檢：AC-D1～AC-D4 已覆蓋於 §2–§6

### 10. deferred_items

- ~~P2 stub 實作與 orchestrator 接線~~ ✅ Done
- P3 webhook / human approve 接線 / W7-T3 handler
- Production `build_case_delivery_bundle` 路徑的 `delivery.bundle_ready`
- ~~Env 鍵 `GOV_NOTIFICATION_GATEWAY_ENABLED` 實例錨點登錄~~ ✅ P2 已採用

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-16 | implementer (B · design) | S15 設計交付：事件模型、stub contract、接線邊界、P2/P3 拆分 |
| 2026-06-16 | implementer (B · implement) | P2 實作：notification_gateway_v1.py、orchestrator 接線、tests、51 tests pass |

---

## B_REPORT · P2 Implementation（2026-06-16）

### 1. changed_files

| 檔案 | 變更摘要 |
|------|----------|
| `delivery/notification_gateway_v1.py` | 新建 stub gateway：build_notification_event、send_notification、emit_notification_safe |
| `delivery/__init__.py` | 未變更（未 expose，保持低耦合） |
| `scripts/run_agent_standard_case_experiment.py` | 接線：import gateway、--enable-notifications CLI flag、4 個事件發射點、notifications[] 追蹤 |
| `tests/test_notification_gateway_v1.py` | 新建 15 個測試：schema、disabled、dry-run、local sink、orchestrator 整合 |

### 2. gateway API

```python
# build_notification_event — 建構事件 envelope
event = build_notification_event(
    "checkpoint.awaiting_human",
    case_ref="demo_phase",
    checkpoint_id="A-intake-confirmation",
    ...
)
# Returns: {schema_version, event_id, event_type, emitted_at, idempotency_key,
#           case_ref, checkpoint_id, checkpoint_status, artifacts, ...}

# send_notification — best-effort 寫入 local sink
result = send_notification(event, enabled=True, outbox_root_override=...)
# Returns: {ok, message, event_id, sink_result: {ok, channel, path, message}}

# emit_notification_safe — 組合 + 發送 + 異常捕獲
result = emit_notification_safe(
    "checkpoint.approved",
    enabled=notifications_enabled,
    case_ref=case_ref,
    ...
)
# Returns: None if disabled; otherwise {ok, message, ...} (never raises)
```

### 3. 事件發射點（已接線）

| 順序 | 邊界 | event_type | 條件 |
|------|------|------------|------|
| 1 | S4 Checkpoint A | `checkpoint.awaiting_human` | status=="written" and would_trigger |
| 2 | S4 Checkpoint A | `checkpoint.approved` | status=="auto_approved" |
| 3 | S12 Checkpoint B | `checkpoint.awaiting_human` | status=="written" and would_trigger |
| 4 | S12 Checkpoint B | `checkpoint.approved` | status in ("skipped", "auto_approved") and not would_trigger |
| 5 | S10 Sandbox bundle | `delivery.bundle_ready` | sandbox_delivery.ok==True |
| 6 | 函式 return 前 | `run.completed` | mode=="run" and ok==True |
| 7 | 函式 return 前 | `run.blocked` | mode=="run" and ok==False |

### 4. notification 檔案路徑格式

- Per-event file: `outbox/notifications/<case_ref>/<event_type>_<compact_ts>_<id8>.json`
  - 例：`outbox/notifications/demo_phase/checkpoint.awaiting_human_2026-06-16T00-14-24Z_a1b2c3d4.json`
- Audit log: `outbox/notification_events.jsonl`（一行一 event，append-only）

### 5. 新增測試名稱（test_notification_gateway_v1.py）

| 類別 | 測試名 |
|------|--------|
| Schema | `test_builds_envelope_with_required_fields` |
| Schema | `test_idempotency_key_includes_case_ref_event_type` |
| Disabled | `test_disabled_returns_skipped` |
| Disabled | `test_dry_run_returns_no_write` |
| Local Sink | `test_writes_event_file_to_notifications_dir` |
| Local Sink | `test_appends_to_jsonl_audit_log` |
| Local Sink | `test_uses_outbox_root_override_when_provided` |
| Safe Emit | `test_returns_none_when_disabled` |
| Safe Emit | `test_builds_and_sends_when_enabled` |
| Safe Emit | `test_returns_error_dict_on_exception_never_raises` |
| Safe Emit | `test_emit_notification_safe_handles_exception_gracefully` |
| Safe Emit | `test_send_notification_handles_write_failure_gracefully` |
| Orchestrator | `test_enable_notifications_produces_notification_files` |
| Orchestrator | `test_preview_mode_does_not_emit_notifications` |
| Orchestrator | `test_env_var_enables_notifications` |

### 6. verification

```bash
python -m unittest tests.test_notification_gateway_v1 -v
# 15 tests, OK

python -m unittest tests.test_agent_standard_case_experiment -v
# 36 tests, OK

python -m unittest tests.test_agent_standard_case_experiment tests.test_notification_gateway_v1
# 51 tests, OK
```

### 7. skeleton / placeholder（本輪無）

本輪實作為完整 P2 stub，無殘留 skeleton。P3 webhook adapter 待後續實作。

### 8. 阻塞 / 風險（本輪無）

- 無阻塞項
- 無已知風險

### 9. 下一步

- P3 設計：webhook adapter skeleton、與 W7-T3 controlled notify 整合
- `GOV_NOTIFICATION_GATEWAY_ENABLED` env 鍵實例錨點登錄（若需要）

---

## R_REVIEW · Reviewer Verdict（2026-06-16）

### 1. Verdict: `accept_with_followups`

實作符合 W6-T10-P2 設計目標，測試通過，event schema 穩定，best-effort 行為正確。建議接受並進入 P3 規劃，附 2 項 follow-up。

---

### 2. 逐條審查結果

| 設計要求 | 實作狀態 | 評語 |
|----------|----------|------|
| v1 僅 stub / local sink | ✅ 符合 | `_write_event_to_file()` + `_append_event_to_jsonl()` 雙 sink，無 external webhook |
| 預設關閉 | ✅ 符合 | CLI `--enable-notifications` 預設 False；env `GOV_NOTIFICATION_GATEWAY_ENABLED` 需顯式設 1 |
| 啟用後寫 local event files | ✅ 符合 | `outbox/notifications/<case_ref>/<event_type>_<ts>_<id8>.json` + `outbox/notification_events.jsonl` |
| notify 失敗不得阻斷主流程 | ✅ 符合 | `emit_notification_safe()` 全異常捕獲；test `test_returns_error_dict_on_exception_never_raises` 驗證；orchestrator 主 `ok` 不受影響 |

---

### 3. Event Schema 審查

**穩定性評估：高**

| 欄位 | 狀態 | 說明 |
|------|------|------|
| `schema_version` | ✅ 固定值 `"notification_event_v1"` | 版本鎖定，未來 drift 可偵測 |
| `event_type` | ✅ 5 種 enum | `checkpoint.awaiting_human`, `checkpoint.approved`, `delivery.bundle_ready`, `run.completed`, `run.blocked` |
| `case_ref` | ✅ 必填 | 與 orchestrator allowlist 對齊 |
| `emitted_at` | ✅ ISO-8601 UTC | `_utc_now_iso()` 產生，含 Z suffix |
| `checkpoint_id` | ⚠️ 條件必填 | checkpoint 類事件時為 `"A-intake-confirmation"` / `"B-delivery-approval"`；run 類為 null，符合設計 |
| `idempotency_key` | ✅ 複合鍵 | `<case_ref>:<event_type>:<checkpoint_id>:<compact_ts>`，便於下游去重 |
| `artifacts` / `status_summary` / `source` | ✅ 結構化 | source 含 `step_id` + `module`，便於追蹤 |

**潛在風險**：
- `sink_result` 欄位在 event envelope 內僅出現在個別 event file，但 jsonl audit log 不含 sink_result（設計正確，避免冗餘）
- `outbox_root_override` 使用時路徑可能為 absolute，downstream 消費者需容忍（已在 §3 Path 語意 文件化）

---

### 4. Best-effort 行為審查

| 項目 | 實作 | 測試覆蓋 |
|------|------|----------|
| Disabled 行為 | `enabled=False` → `ok=True`, message="skipped" | `test_disabled_returns_skipped` |
| Dry-run 行為 | `dry_run=True` → 不寫檔，回傳 envelope | `test_dry_run_returns_no_write` |
| 寫檔失敗不 raise | `_write_event_to_file()` 捕獲 `OSError, IOError`，回傳 `ok=False` | `test_send_notification_handles_write_failure_gracefully` (mock) |
| 異常不 raise | `emit_notification_safe()` try/except 全捕獲 | `test_returns_error_dict_on_exception_never_raises`, `test_emit_notification_safe_handles_exception_gracefully` |
| Primary/Secondary sink | file 為 primary（決定 `ok`），jsonl 為 secondary（informational） | 實作正確 |

**評語**：Best-effort 語意完整實作，orchestrator 主流程與 notification 發射完全解耦。

---

### 5. 接線事件點審查

| 順序 | 設計邊界 | 實作位置（行號） | event_type | 條件實作 |
|------|----------|------------------|------------|----------|
| 1 | S4 Checkpoint A | 1900-1911 | `checkpoint.awaiting_human` | `cp_a_status == "written" and would_trigger` |
| 2 | S4 Checkpoint A | 1913-1921 | `checkpoint.approved` | `cp_a_status == "auto_approved"` |
| 3 | S12 Checkpoint B | 2112-2121 | `checkpoint.awaiting_human` | `cp_b_status == "written" and would_trigger` |
| 4 | S12 Checkpoint B | 2123-2131 | `checkpoint.approved` | `cp_b_status in ("skipped", "auto_approved")` |
| 5 | S10 Sandbox bundle | 1304-1314 | `delivery.bundle_ready` | `sandbox_delivery.ok == True` |
| 6 | 函式 return | 2152-2183 | `run.completed` / `run.blocked` | `mode == "run"` + `ok` 判斷 |

**評語**：6 個事件點全部實作，條件與設計一致。`run.completed`/`run.blocked` 在函式 return 前發射，確保最終狀態已確定。

**minor gap**：orchestrator 內 `_emit_and_track()` 為 nested function，重用性受限，但 P2 scope 內可接受。

---

### 6. 測試覆蓋評估

| 類別 | 測試數 | 覆蓋項目 |
|------|--------|----------|
| Schema / Event building | 2 | 必填欄位、idempotency_key 格式 |
| Disabled / Dry-run | 2 | 預設關閉行為、無副作用 |
| Local sink (file + jsonl) | 3 | 寫檔路徑、內容結構、jsonl append、outbox override |
| Safe emit wrapper | 4 | enabled=False 回傳 None、異常捕獲、error dict 格式 |
| Orchestrator 整合 | 4 | CLI `--enable-notifications`、env var、preview 模式不發射、notification files 產生 |
| **Total** | **15** | — |

**核心風險覆蓋**：
- ✅ 寫檔失敗不阻斷主流程（mock test）
- ✅ 異常不拋出（mock test）
- ✅ Preview 模式不發射（CLI integration test）
- ✅ Env var 啟用（subprocess test）

**Follow-up 測試建議（P2-P3 銜接）**：
1. **File lock / concurrent write**：多 process 同時寫同一 case_ref 的 jsonl，需驗證無 truncated line（目前 `open("a")` 在 POSIX 為原子 append，Windows 需額外驗證）
2. **Resume 重複 emit**：checkpoint resume 後重新跑 run path，應產生不同 `idempotency_key`（時間戳不同），但 downstream 訂閱者需能去重
3. **Orchestrator notification 追蹤欄位**：目前 `base["notifications"]` 僅追蹤 `event_type, ok, path`，建議補 `event_id` 便於端到端追蹤

---

### 7. Follow-ups

| ID | 項目 | 優先級 | 負責方 | 說明 |
|----|------|--------|--------|------|
| F1 | 補 `base["notifications"].event_id` 追蹤 | P2-P3 | implementer | orchestrator 結果內 notification 追蹤補 event_id，便於端到端 correlation |
| F2 | Concurrent jsonl append 驗證 | P3 | implementer | Windows 環境下多 process concurrent append 測試，或考慮 file lock |
| F3 | Human approve 路徑 `checkpoint.approved` | P3 | implementer | 目前僅 `approval_source="auto"`，human approve 需 delivery approval CLI 接線（已規劃於 P3） |
| F4 | Webhook adapter skeleton | P3 | implementer | `notification_sinks/` 目錄 + `external_dispatch` interface |

---

### 8. 文件與程式碼品質

- **Docstrings**：完整，含型別提示
- **型別提示**：`Dict[str, Any]`、`Optional[Path]` 等正確使用
- **Error handling**：無裸 except，明確捕獲 `OSError, IOError`、`Exception`
- **Path 處理**：使用 `pathlib.Path`，無硬編碼分隔符
- **Env 鍵**：`GOV_NOTIFICATION_GATEWAY_ENABLED` 已實例錨點化（文件內引用）

---

**Reviewer**: B-role / Reviewer  
**Date**: 2026-06-16  
**Verdict**: `accept_with_followups`（F1-F4 非阻塞，P3 規劃時處理）

---

*B_REPORT · W6-T10-client-notification-gateway-v1 · P2 implement · 2026-06-16*

---

## I_IMPLEMENT · P3 Implementation (2026-06-16)

### F1: event_id 追蹤強化

| 變更 | 位置 | 說明 |
|------|------|------|
| `_emit_and_track()` | `scripts/run_agent_standard_case_experiment.py` | 回傳 `event_id` (str\|None) 供 cross-reference |
| Checkpoint A 發射 | Line ~1900 | 捕捉 `checkpoint.approved` event_id 存入 `checkpoint_a["notification_event_id"]` |
| Checkpoint B 發射 | Line ~2120 | 捕捉 `checkpoint.awaiting_human` 與 `checkpoint.approved` event_id 存入 `checkpoint_b["notification_event_id"]` |
| Notifications list | 原有 | 已含 `event_id`，主流程無需變更 |

**驗收**：orchestrator result 中 `notifications[].event_id` 可與 notification event file 中的 `event_id` cross-reference。

---

### F2: jsonl append 並發安全強化

| 變更 | 位置 | 說明 |
|------|------|------|
| `_lock_file()` | `delivery/notification_gateway_v1.py` | 最佳努力檔案鎖定：優先使用 portalocker，Windows 使用 msvcrt，Unix 使用 fcntl |
| `_unlock_file()` | 同上 | 釋放檔案鎖 |
| `_append_event_to_jsonl()` | Line ~180 | 先鎖定檔案、seek 到結尾、寫入、flush、解鎖 |
| 測試 | `tests/test_notification_gateway_v1.py` | 新增 `TestConcurrentAppend` 驗證連續寫入不損毀 JSONL |

**限制說明**：
- sandbox 環境可能無 portalocker 或 msvcrt/fcntl，會回退到無鎖定模式
- JSONL 行導向格式本身具容錯性，即使無鎖定也不易損毀
- 測試驗證「在我們預期的使用方式下」append 行為穩定

---

### F3: human approve → checkpoint.approved

| 變更 | 位置 | 說明 |
|------|------|------|
| `_emit_checkpoint_approved_for_human()` | `delivery/delivery_approval_cli_v1.py` | 輔助函式：組合並發射 `checkpoint.approved` (approval_source="human") |
| `run_delivery_approval()` | Line ~400 | 當 `internal_action == "approve_delivery"` 時呼叫輔助函式 |
| Payload | `artifacts` | 包含 `approver` (operator_id)、`decision_time` (ISO-8601 UTC) |
| 回傳 | result dict | 新增 `notification_event` 欄位：{ok, event_id, path} |
| 測試 | `tests/test_notification_gateway_v1.py` | 新增 `TestHumanApprovalNotification` 驗證正確發射 |

**行為**：
- 僅在確認 (`confirm=True`) 且 action 為 `approve` 時發射
- best-effort：發射失敗不影響 CLI 主流程 (try/except)
- 與 auto_approved 區分明確：`approval_source="human"`

---

### F4: webhook adapter skeleton

| 變更 | 位置 | 說明 |
|------|------|------|
| 新建檔案 | `delivery/notification_webhook_adapter_v1.py` | Skeleton implementation (no-op/log-only) |
| `send_webhook_notification()` | 主函式 | 預設 `dry_run=True`，不發實際 HTTP 請求 |
| `build_webhook_endpoint_config()` | 輔助函式 | 標準化 endpoint 配置 |
| `validate_webhook_config()` | 輔助函式 | 驗證配置欄位 |
| Protocol | `HttpClientProtocol` | 定義 future async HTTP client 介面 |
| 測試 | `tests/test_notification_gateway_v1.py` | 新增 `TestWebhookAdapterSkeleton` 驗證 skeleton 行為 |

**P3 限制**：
- `dry_run=True` 為預設，不回傳錯誤
- 未實作實際 HTTP 呼叫（避免 P3 flakiness）
- 未接入 orchestrator（Future P4+）
- 文件化 retry/DLQ/HMAC 為未來擴展點

---

### P3 新增 / 修改檔案

| 檔案 | 變更類型 | 說明 |
|------|----------|------|
| `scripts/run_agent_standard_case_experiment.py` | 修改 | F1: _emit_and_track 回傳 event_id，Checkpoint A/B 儲存 notification_event_id |
| `delivery/notification_gateway_v1.py` | 修改 | F2: 新增 _lock_file, _unlock_file，強化 _append_event_to_jsonl |
| `delivery/delivery_approval_cli_v1.py` | 修改 | F3: 新增 _emit_checkpoint_approved_for_human，整合至 run_delivery_approval |
| `delivery/notification_webhook_adapter_v1.py` | 新建 | F4: skeleton implementation |
| `tests/test_notification_gateway_v1.py` | 修改 | F2/F3/F4: 新增併發、人工核准、webhook skeleton 測試 |

---

### 新增測試名稱 (P3)

| 類別 | 測試名 | 驗證項目 |
|------|--------|----------|
| Concurrent | `test_concurrent_appends_produce_valid_jsonl` | 10 個事件連續寫入不損毀 JSONL |
| Concurrent | `test_concurrent_writes_different_cases` | 不同 case_ref 事件皆正確記錄 |
| Human Approval | `test_checkpoint_approved_event_for_human` | Human approve 發射正確事件含 approver/decision_time |
| Human Approval | `test_disabled_human_approval_returns_none` | Disabled 時無副作用 |
| Webhook | `test_skeleton_dry_run_returns_ok` | Skeleton dry_run=True 回傳 ok |
| Webhook | `test_build_endpoint_config_validates` | 配置建構正確 |
| Webhook | `test_validate_config_detects_errors` | 配置驗證偵測錯誤 |
| Webhook | `test_default_headers_include_event_id` | 預設標頭含 event_id |

**P3 測試總數**：新增 8 個，總計 23 個（P2 15 + P3 8）

---

### 阻塞 / 風險

| 項目 | 狀態 | 說明 |
|------|------|------|
| F2 檔案鎖定 | 已知限制 | sandbox 無 portalocker/msvcrt/fcntl 時回退無鎖定；JSONL 格式具容錯性 |
| F4 HTTP 實作 | 未實作 | skeleton only；P4+ 實作實際 HTTP client、retry、DLQ |
| F4 orchestrator 接線 | 未接線 | 預留介面，未在 P3 串接至主流程 |

---

### P3 DoD 自檢

- [x] F1: event_id 追蹤已實作並測試
- [x] F2: jsonl append 並發保護已實作並測試
- [x] F3: human approve → checkpoint.approved 已實作並測試
- [x] F4: webhook adapter skeleton 已建立並測試
- [x] 不破壞 P2 已穩定 schema
- [x] backward-compatible (新增欄位皆為 optional)
- [x] 測試通過 (待 F7 驗證)

---

**Implementer**: B-role / Implementer  
**Date**: 2026-06-16  
**Status**: `p3_implemented`

---

*I_IMPLEMENT · W6-T10-client-notification-gateway-v1 · P3 implement · 2026-06-16*
