# Tabular Cleaning Control Plane v1

> **Role**: Start / Pause / Resume / Stop 人類控制面 — tabular cleaning 主鏈  
> **Status**: v1 · state + CLI · **非** unified driver · **非** prod gate  
> **Date**: 2026-06-27  
> **Audience**: Operator · Orchestrator · Implementer  
> **Upstream**: `docs/tabular-cleaning-automation-manifest-v1.md` · `docs/TABULAR_MVP_SSOT.md`  
> **CLI**: `scripts/manage_tabular_automation_state.py`  
> **Library**: `scripts/tabular_automation_state_lib.py`

---

## 0. 設計目標

| 項 | 定義 |
|----|------|
| **人類決策** | 要不要做 · 何時開始 · 何時暫停 / 停止 |
| **系統決策** | R1–R6 各 stage 在 `allowed_to_auto_proceed=true` 時自動推進（由未來 unified driver 消費） |
| **本票範圍** | `automation_state.json` schema · 放置規則 · CLI · 文檔索引 |
| **本票外** | `run_tabular_automation.py` driver · CP resume 接線 · workflow yml · Dashboard |

**Governance guardrail**：本控制面 **不得** 觸發 required CI gate 升格 · Phase% 上調 · closure 宣稱。

---

## 1. 檔案放置規則

### 1.1 路徑

每個 case 在 **case 根目錄**（與 `intake.json` 同層）放置單一檔：

```text
cases/<client_ref>/<case_id>/automation_state.json
cases/demo_phase/automation_state.json          # 遗留 demo 锚点（合法）
```

| 規則 | 說明 |
|------|------|
| **一 case 一檔** | 禁止放在 `reports/` 或 outbox |
| **建案時** | 複製 `cases/_TEMPLATE_case/automation_state.json` 並更新 `case_id` |
| **缺檔時** | CLI `status` 回報 synthetic `idle`；`start` 會自動建立 |
| **case_id 權威** | 以 `intake.json` → `case_id` 為準；寫入時同步 |

### 1.2 模板

- 模板：`cases/_TEMPLATE_case/automation_state.json`
- 示例：`cases/demo_phase/automation_state.json`

---

## 2. Schema — `automation_state.json`

`schema_version`: **`tabular-automation-state-v1`**

| 欄位 | 類型 | 說明 |
|------|------|------|
| `schema_version` | string | 固定 `tabular-automation-state-v1` |
| `case_id` | string | 與 `intake.json` 一致 |
| `automation_status` | enum | `idle` · `running` · `paused` · `stopped` · `completed` · `failed` |
| `start_requested_by` | string \| null | 最近一次 start / restart 操作者 |
| `stop_requested_by` | string \| null | 最近一次 stop 操作者 |
| `pause_reason` | string \| null | 暫停原因（pause 時寫入） |
| `resume_requested_by` | string \| null | 最近一次 resume 操作者 |
| `last_transition_ts` | string \| null | ISO-8601 UTC · 最近一次狀態轉換 |
| `current_step` | string \| null | 驅動器當前 stage（見 §2.1） |
| `allowed_to_auto_proceed` | boolean | driver 是否可啟動下一 atomic step |
| `requires_hitl_checkpoint` | boolean | 是否阻塞於 CP-A / CP-B |
| `last_error` | string \| null | 最近一次 hard 失敗摘要（driver 寫入） |
| `last_error_at` | string \| null | ISO-8601 UTC · 最近一次錯誤時間 |
| `retry_count` | integer | transient 重試計數（driver 寫入；restart 清零） |
| `dlq_status` | enum | `none` · `queued` · `handled` — DLQ 條目狀態；**不**觸發自動重跑 |

### 2.1 `current_step` 枚舉

| 值 | 對應 manifest stage |
|----|---------------------|
| `intake` | R1 |
| `eligibility` | R2 |
| `checkpoint_a` | CP-A |
| `cleaning` | R3 |
| `report` | R4 |
| `bundle` | R5 |
| `e2e` | R6 |
| `checkpoint_b` | CP-B |
| `delivery` | post CP-B approve |
| `null` | 尚未開始或已 reset |

### 2.2 完整範例（idle）

```json
{
  "schema_version": "tabular-automation-state-v1",
  "case_id": "demo_phase",
  "automation_status": "idle",
  "start_requested_by": null,
  "stop_requested_by": null,
  "pause_reason": null,
  "resume_requested_by": null,
  "last_transition_ts": null,
  "current_step": null,
  "allowed_to_auto_proceed": false,
  "requires_hitl_checkpoint": false,
  "last_error": null,
  "last_error_at": null,
  "retry_count": 0,
  "dlq_status": "none"
}
```

### 2.3 執行中範例（running · mid-chain）

```json
{
  "schema_version": "tabular-automation-state-v1",
  "case_id": "demo_phase",
  "automation_status": "running",
  "start_requested_by": "operator",
  "stop_requested_by": null,
  "pause_reason": null,
  "resume_requested_by": null,
  "last_transition_ts": "2026-06-27T10:15:00+00:00",
  "current_step": "cleaning",
  "allowed_to_auto_proceed": true,
  "requires_hitl_checkpoint": false,
  "last_error": null,
  "last_error_at": null,
  "retry_count": 0,
  "dlq_status": "none"
}
```

---

## 3. 狀態機

### 3.1 人類 CLI 轉換

```text
idle ──start──► running
paused ──start / resume──► running
running ──pause──► paused
running | paused | idle ──stop──► stopped
stopped | completed | failed ──start --restart──► running
```

### 3.2 規則摘要

| 命令 | 允許來源狀態 | 目標 | 備註 |
|------|--------------|------|------|
| **start** | `idle` · `paused` | `running` | 設 `allowed_to_auto_proceed=true` |
| **start --restart** | `stopped` · `completed` · `failed` | `running` | 清零 `retry_count` · `last_error` · `last_error_at` · `dlq_status=none` · `current_step` |
| **pause** | `running` | `paused` | 不 rollback 已完成步驟；僅阻新步 |
| **resume** | `paused` | `running` | 僅 paused → running |
| **stop** | `idle` · `running` · `paused` | `stopped` | `allowed_to_auto_proceed=false` |
| **status** | 任意 | — | 只讀 |

**禁止**：

- `stopped` 上直接 `start`（無 `--restart`）— 須明確重啟，不可原位 resume
- `running` 上重複 `start`
- 非 `running` 時 `pause`
- 非 `paused` 時 `resume`

### 3.3 Driver 專用轉換（v1 · unified driver）

| 事件 | 轉換 |
|------|------|
| 全鏈成功 | `running` → `completed` |
| Hard 失敗 | `running` → `failed` + `last_error` + `last_error_at` |
| Transient 重試中 | `retry_count` 遞增 · `last_error*` 更新 |
| Retry 用盡 / 立即 DLQ | `dlq_status=queued` · 寫入 `dlq/dlq.json` |
| 命中 CP-A/B | `requires_hitl_checkpoint=true` · `allowed_to_auto_proceed=false` · **不**進 DLQ |

**DLQ 非自動化**：`dlq/` 條目僅供運營 triage；清理後可手動設 `dlq_status=handled` 或更新 `dlq/*.json` → `status=handled`。須 `start --restart` 後才可重新跑主鏈。

---

## 4. CLI 用法

### 4.1 命令

```bash
# 查詢（缺檔時回 synthetic idle）
python scripts/manage_tabular_automation_state.py status \
  --case-dir cases/demo_phase --json

# 開始（idle 或 paused）
python scripts/manage_tabular_automation_state.py start \
  --case-dir cases/demo_phase --requested-by operator --json

# 暫停（僅 running）
python scripts/manage_tabular_automation_state.py pause \
  --case-dir cases/demo_phase --requested-by operator \
  --reason "awaiting client confirmation" --json

# 恢復（僅 paused）
python scripts/manage_tabular_automation_state.py resume \
  --case-dir cases/demo_phase --requested-by operator --json

# 停止
python scripts/manage_tabular_automation_state.py stop \
  --case-dir cases/demo_phase --requested-by operator --json

# 明確重啟（stopped / completed / failed 後）
python scripts/manage_tabular_automation_state.py start \
  --case-dir cases/demo_phase --requested-by operator --restart --json
```

### 4.2 結構化輸出

每次命令 stdout 為 JSON（`--json` 時僅 JSON；預設為一行摘要 + JSON）：

| 鍵 | 說明 |
|----|------|
| `ok` | 命令是否成功 |
| `command` | `start` · `pause` · `resume` · `stop` · `status` |
| `case_dir` | 解析後 case 目錄 |
| `state_path` | `automation_state.json` 絕對路徑 |
| `previous_status` | 轉換前 `automation_status` |
| `automation_status` | 轉換後狀態 |
| `state` | 完整 state 物件 |
| `message` | 人讀說明 |

Exit code：`0` = `ok: true` · `1` = `ok: false`

### 4.3 驗證

```bash
python -m unittest tests.test_tabular_automation_state -v
```

---

## 5. 與主鏈的關係

| 元件 | 現狀 |
|------|------|
| **Control plane CLI** | ✅ 本票 |
| **Unified driver** (`run_tabular_automation.py`) | ✅ v1 · 串 R1–R6 + CP-A/B 判定 |
| **E2E runner** | ✅ `run_case_e2e_validation.py`（**不**讀 control state；driver e2e step 會調用） |
| **HITL CP resume** | ⚠️ driver `--resume` 可續跑；`apply-decision` 後完整接線仍規劃 B5 |
| **Automation run log** | ✅ `reports/automation_run_log.json` |

**運營模式**：

1. 人類 `start` → `run_tabular_automation.py`（或過渡期仍可直接 `run_case_e2e_validation.py`）
2. driver 迴圈讀 `allowed_to_auto_proceed` + `automation_status=running`；步驟間 respect pause/stop

### 5.1 Internal notify hook（占位）

狀態變化若無主動查檔不易被發現。v1 在 driver / state lib 預留 **`notify_internal(event, payload)`**（`scripts/tabular_internal_notify_lib.py`）：

- **現狀**：append 至 case 根 `internal_notify_log.json` + `INFO` log；**不**發外部訊息。
- **可掛事件**：見 manifest §1.11（`idle→running` · CP pending/rejected · `completed`+`delivery_ready` · DLQ）。
- **未來**：Telegram / 郵件 / 告警可從同一 event id 擴展 adapter。

---

## 6. 交叉引用

| 文件 | 關係 |
|------|------|
| `docs/tabular-cleaning-automation-manifest-v1.md` | allowed/forbidden · start/stop 條件 |
| `docs/C2-P2_RUNBOOK.md` §3.4 | 自動化 overlay |
| `docs/TABULAR_MVP_SSOT.md` §9 | 索引 |
| `cases/README.md` | case 目錄約定 |
| `04_Workflows/WORKFLOW_INDEX.md` §1.5 | workflow 索引 |

---

## 7. 修訂

| 版本 | 日期 | 說明 |
|------|------|------|
| v1 | 2026-06-27 | 初版 · schema + CLI + 模板 |

---

*Tabular Cleaning Control Plane v1 · NOT PROD GATE · NOT CLOSURE*
