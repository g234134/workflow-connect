# Tabular Cleaning Automation Manifest v1

> **Role**: 低風險 tabular cleaning **自動化邊界契約** — 人類只決定「做不做、何時開始、何時停止／暫停」  
> **Status**: v1 · doc-only · **非** prod gate · **非** closure 宣稱  
> **Date**: 2026-06-27  
> **Audience**: Tabular Cleaning Automation Planner · Orchestrator · Implementer · PM  
> **Upstream**: `docs/TABULAR_MVP_SSOT.md` · `docs/PRODUCT_TABULAR_CLEANING.md` · `tools/tabular_tool_catalog_v1.json`  
> **Related**: `docs/ninety-five-percent-automation-blueprint-v1.md` · `docs/hitl-checkpoints-v1.md`

---

## 0. 設計目標

| 項 | 定義 |
|----|------|
| **自動化目標** | 在 **低風險、重複性高、可快速交付** 的 tabular case 上，系統自動完成 intake 後鏈路；人類僅保留最少 checkpoint |
| **人類保留權** | （1）case 類型要不要接；（2）何時 start；（3）何時 stop / pause |
| **產品邊界** | Tabular MVP · **非** required/advisory CI gate · **非** Phase% · **非** prod-ready / full closure |
| **可落地定義** | 任一 stage 有明確 CLI/模組、結構化 `dict` 輸出、失敗可記錄、可重跑 |

**Governance guardrail（Batch 1 · 仍有效）**：本 manifest **不得**觸發 gate 升格、Dashboard Phase% 上調、branch protection / workflow yml 變更、或 prod / closure 宣稱。

---

## 1. Automation Manifest（機器可讀邊界）

### 1.1 `allowed_case_types`

僅下列 **case type** 可進入自動化主鏈（其餘一律 `rejected` 或 `human-only`）：

| `case_type` | 說明 | 清洗 runner | 備註 |
|-------------|------|-------------|------|
| `tabular.cleaning.mvp` | 標準 CSV/TSV 單表清洗 | `clean.phase_demo`（現況） | Phase-like 或已對齊 schema 的 fixture |
| `tabular.cleaning.regression` | 雙案回歸錨點 | `orchestrate.e2e` | `demo_phase` · `sampleco/2026-0001` |
| `tabular.intake.new_case` | 僅建案 + 可選 gate | `intake.new_case` | 不自動進 cleaning |

**允許的 fixture profile（v1 allowlist）**：

- Production regression：`demo_phase` · `sampleco/2026-0001`
- Cleaning profile registry：`docs/tabular-cleaning-profiles-v1.md`（`phase_demo_v1` · `sampleco_order_profile`）
- Experimental（不計入「接近 100%」達標）：`additional_demo` · `sandbox_client`

**允許的清洗問題類型**（四類，見 Product Spec）：

- `missing` · `duplicate` · `anomaly` · `format`

### 1.2 `allowed_inputs`

| 輸入 | 允許 | 限制 |
|------|------|------|
| **CSV / TSV** | ✅ | UTF-8 建議；RFC 4180；encoding 白名單見 `case_eligibility.py` |
| **Excel `.xlsx`** | ⚪ 個案 | 需 `intake.json` 明示；非預設自動路徑 |
| **Excel `.xls`** | ⚪ 視個案 | 同上 |
| **`intake.json`** | ✅ 必填 | 含 `case_id` · `client_ref` · `data_file` · `file_format` |
| **`raw/` 目錄** | ✅ 必填 | `data_file` 指向之檔案須存在 |
| **欄位 schema / 主鍵** | 建議 | 缺省時僅標記缺失，**不**自動猜測填補 |
| **規模** | ✅ | 單檔 ≤ 100 萬列 / 1 GB（accepted）；更大 → `review_needed` 或 `rejected` |

**拒收輸入（自動 `rejected`）**：

- OCR / PDF / 掃描件 / 非 2D tabular
- `provenance=web_scraping` · `sensitivity=phi` 等（見 eligibility 維度）
- 缺 `intake.json` 或 raw 檔不可讀

### 1.3 `allowed_mutations`

自動化流程**允許**寫入或更新：

| 類別 | 路徑 / 物件 | 操作 |
|------|-------------|------|
| **Case 目錄** | `cases/<client_ref>/<case_id>/` | 建案（intake stage） |
| **Case control state** | `cases/<case>/automation_state.json` | start / pause / resume / stop（v1 已落地；見 `docs/tabular-cleaning-control-plane-v1.md`） |
| **Gate 落盤** | `reports/eligibility_result.json` | 寫入 / 刷新 P2 判定 |
| **清洗產物** | `cleaned/*_cleaned.csv` | 覆寫清洗結果 |
| **統計** | `reports/cleaning_stats.json` | before/after profiling |
| **報告** | `reports/report.json` · `reports/report.md` | QC 與規則摘要 |
| **Bundle metadata** | `reports/report.json` → `output_guard` · `bundle` 段 | enrichment |
| **Signoff 草稿** | `delivery_signoff.md` | 模板生成 / 刷新（**非**最終對客承諾） |
| **索引** | `cases/index.json` | `build_cases_index.py` 掃描更新 |
| **Outbox** | `outbox/<case_ref>/` | tool run 記錄 · checkpoint state · events |
| **HITL 決策** | `outbox/<case_ref>/checkpoint_*.json` | 人工決策落盤 |
| **Automation run log** | `cases/<case>/reports/automation_run_log.json` | 每輪 run 摘要（driver 寫入 · v1） |

### 1.4 `forbidden_mutations`

自動化流程**禁止**（硬停 · 須人工 override 票）：

| 禁止項 | 原因 |
|--------|------|
| **required / advisory gate 升格** | Batch 1 `hard_no` |
| **Phase% 上調** | Dashboard / Progress 治理獨占 |
| **`project_status/master_status.md` closure 宣稱** | Governance 獨占 |
| **prod-ready / GA / SLA 文案寫入交付物** | 非 Tabular MVP 範圍 |
| **`.github/workflows/*.yml` 變更** | 本 manifest scope 外 |
| **branch protection 變更** | 同上 |
| **`.env` / 金鑰 / runtime checkpoint 暗部樹** | 憲法 §7 禁區 |
| **未授權修改他人 `core` 或 governance Batch 1 YAML** | Rule 8 · BAN-5.6 |
| **對 `cases/index.json` 寫 `status=delivered` 且無 CP-B approve 記錄** | 品質把關（v1 規劃約束） |
| **客戶-facing 自動通知（prod SMTP/Telegram send）** | 暫列 C 類；實驗線僅 simulated outbox |

### 1.5 `start_conditions`

自動化 **start** 須同時滿足：

1. **人類顯式 start**：`automation_state.json` → `"automation_status": "running"`（CLI `manage_tabular_automation_state.py start`）
2. **Case 結構完整**：`intake.json` + `raw/` + 可解析 data file
3. **Case type ∈ allowed_case_types** 且 `task_type=tabular.cleaning.mvp`
4. **Eligibility ≠ rejected**（`accepted` 或 `review_needed` + 授權 `--force` / CP-A approve）
5. **無進行中 blocking checkpoint**（status ≠ `awaiting_human`，除非 resume 路徑）
6. **Fixture profile** 在 allowlist 或 CP-A 已 `approve`

**Low-risk 快速路徑（可跳 CP-A）**：

- `decision=auto_accept` + `risk_level=low` + known allowlist + `eligibility=accepted`

### 1.6 `stop_conditions`

| 條件 | 行為 | 落盤 |
|------|------|------|
| **人類 stop** | 立即停；不啟動下一 stage | `automation_state.json` → `"automation_status": "stopped"` · `allowed_to_auto_proceed=false` |
| **人類 pause** | 完成當前 atomic step 後停 | `"automation_status": "paused"` · `pause_reason` · `current_step` 保留 |
| **`eligibility=rejected`** | 終止；不進 cleaning | `eligibility_result.json` + run log |
| **CP-A `reject`** | 終止 | `outbox/.../rejected_*.json` |
| **CP-B `hold` / `request_changes`** | 停於 delivery 前 | checkpoint B state |
| **Cleaning 硬失敗**（exit ≠ 0 且非 transient） | 停；可重試上限後 DLQ | `automation_run.json` · outbox error |
| **Output guard `error`** | 停；觸發 CP-B | report.json `output_guard` |
| **超出 retry 上限** | 停；標 `needs_human` | run log + outbox |

### 1.7 HITL requirements（最少人工 checkpoint）

| Checkpoint | 保留原因 | 可自動跳過條件 | 不可跳過條件 |
|------------|----------|----------------|--------------|
| **CP-A · Intake Confirmation** | 未知 profile · medium risk · 規則未對齊 | `auto_accept` + `low` + allowlist + `accepted` | `needs_review` · unknown profile · `review_needed` 且無 `--force` |
| **CP-B · Delivery Confirmation** | 品質把關 · 異常列比例 | `output_guard.status=ok` · removal_ratio ≤ 0.3 · 非 forced clean | `guard=warning/error` · removal_ratio > 0.5 · `qa_status=fail` · forced `--force` |

**人類操作面（僅 3 類）**：

1. **Type gate**：接不接此 case type（接案前）
2. **Start / Pause / Resume / Stop**：`scripts/manage_tabular_automation_state.py` · `automation_state.json`
3. **CP-A / CP-B 決策**：`run_hitl_checkpoint_cli.py --apply-decision ...`

**其餘 stage 目標為 auto**（見 §2 Runbook）。

### 1.8 `output_schema`

標準交付 schema（錨點：`cases/demo_phase/`）：

#### Cleaned CSV

```
cases/<case>/cleaned/{basename}_cleaned.csv
```

- UTF-8 · header row · 與 `intake.json` / cleaning rules 一致

#### `cleaning_stats.json`

```json
{
  "schema_version": "cleaning-stats-v0.1",
  "case_id": "<string>",
  "before": {
    "total_rows": 0,
    "missing_rate_by_field": {},
    "duplicate_rows_found": 0
  },
  "after": {
    "total_rows": 0,
    "accepted_rows": 0,
    "rejected_rows": 0,
    "duplicate_rows_removed": 0,
    "format_fixes_applied": {},
    "anomaly_count_by_rule": {}
  }
}
```

#### `report.json`（核心鍵）

```json
{
  "schema_version": "case-report-v0.1",
  "case_id": "<string>",
  "qa_status": "pass | pass_with_warnings | fail",
  "product_metrics": {},
  "cleaning_rules_applied": [],
  "cleaning_stats": {},
  "output_guard": {
    "status": "ok | warning | error",
    "removal_ratio": 0.0
  }
}
```

#### `report.md`

- 人讀摘要：前後指標 · 規則清單 · 警告項

#### Delivery bundle（邏輯集合）

| 元件 | 路徑 |
|------|------|
| cleaned CSV | `cleaned/*.csv` |
| reports | `reports/report.json` · `report.md` · `cleaning_stats.json` · `eligibility_result.json` |
| signoff 草稿 | `delivery_signoff.md` |
| guard sidecar | `report.json` → `output_guard` |

#### `eligibility_result.json`

- `schema_version`: `case-eligibility-result-v0.1`
- `status`: `accepted` | `review_needed` | `rejected`

### 1.9 Failure handling / retry policy

> **實作**：`scripts/tabular_automation_retry_dlq_lib.py` · driver 整合於 `tabular_automation_driver_lib.py`  
> **DLQ 路徑**：`cases/<case>/dlq/dlq.json`（索引）+ `cases/<case>/dlq/<entry_id>.json`（單筆）  
> **重要**：DLQ **僅收集問題**，不會自動重跑清洗、不觸發 delivery、不觸發 outbox replay。由運營／工程定期 triage 並標 `handled`。

| 失敗類型 | 判定 | Retry | DLQ | 記錄 |
|----------|------|-------|-----|------|
| **Transient** | I/O error · timeout · file lock · `resource temporarily unavailable` · connection reset | 最多 **3** 次 · backoff **1s → 2s → 4s** | retry 用盡後 **queued** | `automation_state.json` · `automation_run_log.json` · `dlq/` |
| **Eligibility rejected** | exit 1 · `terminal=true` | **0** | **否** | `eligibility_result.json` |
| **Review needed / HITL** | CP-A/B awaiting · `hitl_blocked` | **0** | **否** | pause + checkpoint state |
| **Cleaning / bundle hard fail** | exit ≠ 0 且非 transient 關鍵字 | **0** | **立即 queued** | run log + `dlq/` |
| **Schema / report missing** | Phase columns 不符 · 缺 report artifacts | **0** | **立即 queued** | run log + `dlq/` |
| **Guard warning/error** | ratio 超閾值 · 0 rows | **0** | **否**（進 CP-B） | `output_guard` |

**State / run log 欄位**（driver 寫入）：

| 欄位 | 位置 | 說明 |
|------|------|------|
| `retry_count` | state · run log · step | 當前 step 已消耗的 transient 重試次數 |
| `last_error` | state · run log · step | 最近一次錯誤摘要 |
| `last_error_at` | state · run log · step | ISO-8601 UTC |
| `dlq_status` | state · run log · step | `none` · `queued` · `handled` |
| `attempt` | run log · step | 本 step 最終嘗試序號（含 retry） |
| `error_if_any` | run log · step | step 失敗時之最終錯誤；成功則 `null` |
| `dlq_if_any` | run log · step | DLQ 入列時 `{ entry_id, entry_path, failure_class }`；否則 `null` |
| `retry_attempts[]` | run log · step | 每次失敗嘗試之 `attempt` · `error` · `failure_class` · 時間戳 |

**運營查 DLQ**：

```bash
# 索引（所有 queued 條目）
cat cases/demo_phase/dlq/dlq.json

# 單筆詳情
ls cases/demo_phase/dlq/*.json

# 與 state 交叉確認
python scripts/manage_tabular_automation_state.py status \
  --case-dir cases/demo_phase --json
```

**故意製造 transient 示例**（測試／演練）：對某 step 注入 `OSError: resource temporarily unavailable`；driver 會重試 3 次（sleep 1s/2s/4s）後寫入 DLQ 並設 `automation_status=failed` · `dlq_status=queued`。

#### DLQ 單筆 entry 示例（`cases/<case>/dlq/<entry_id>.json`）

```json
{
  "entry_id": "20260627T120000Z_a1b2c3d4_report",
  "status": "queued",
  "case_id": "demo_phase",
  "case_dir": "cases/demo_phase",
  "run_id": "20260627T115900Z_f00bar01",
  "step_name": "report",
  "error": "missing report artifacts: report.json",
  "failure_class": "immediate_dlq",
  "retry_count": 0,
  "last_error_at": "2026-06-27T12:00:00+00:00",
  "queued_at": "2026-06-27T12:00:00+00:00",
  "run_log_path": "cases/demo_phase/reports/automation_run_log.json",
  "cleaning_profile_id": "phase_demo_v1",
  "note": "collect-only; operator must triage and mark handled — no auto re-run"
}
```

**Transient vs persistent 判準（v1）**：

| 類別 | 關鍵字 / 信號 | Retry | DLQ |
|------|---------------|-------|-----|
| **Transient** | `i/o error` · `timeout` · `file locked` · `resource temporarily unavailable` · `connection reset` · `errno 11/35` · step 回傳 `transient=true` | 最多 3 次 · 1s→2s→4s | retry 用盡後 queued |
| **Permanent stop** | `hitl_blocked` · `terminal=true` · `awaiting human` · `intake decision reject` · `eligibility rejected` | 0 | 否（pause / terminal） |
| **Immediate DLQ** | `schema mismatch` · `missing report artifacts` · `clean exit` · `bundle exit` · `gate exit` · `e2e validation failed` · step 回傳 `transient=false` | 0 | 立即 queued |

### 1.10 `non_claims`

本自動化 manifest 及依其執行之流程 **不得** 宣稱：

- Prod-ready · GA · SLA · 7×24 託管
- Full-line closure · Phase% 達標 · required CI merge gate
- 零錯誤 · 全捕獲 · 無 HITL
- 通用 Excel / 任意 schema 清洗（現況 runner 為 Phase-demo  tight）
- 客戶已正式驗收（除非 CP-B approve + 人工 signoff 明示）

### 1.11 Internal notify hook（占位 · 非 prod 通知）

> **現狀**：僅寫入 case 根目錄 `internal_notify_log.json` + Python `INFO` log；**不**發送到 Telegram／SMTP／Slack 等外部系統。  
> **模組**：`scripts/tabular_internal_notify_lib.py` → `notify_internal(event, payload)`  
> **未來擴展**：prod 通知 adapter 可訂閱下列 event id，或替換 `notify_internal` 實作。

| Event id | 觸發時機 | 主要 payload 欄位 | 接線位置 |
|----------|----------|-------------------|----------|
| `case.idle_to_running` | `automation_status` 自 **`idle` → `running`**（`start`，非 `--restart` 來源） | `requested_by` · `previous_status` | `tabular_automation_state_lib.start_automation` |
| `checkpoint.pending` | **CP-A 或 CP-B** 進入 `pending`（driver HITL block） | `checkpoint` (`a`\|`b`) · `step_name` · `pause_reason` | `tabular_automation_driver_lib` |
| `checkpoint.rejected` | **CP-A 或 CP-B** 被 human **reject** | `checkpoint` · `command` · `operator_id` | `tabular_hitl_resume_lib.apply_tabular_checkpoint_decision` |
| `case.completed_delivery_ready` | `automation_status=completed` **且** `delivery_ready=true`（新達成） | `source` · `delivery_ready` | driver 鏈完成 · `maybe_update_delivery_readiness` · `approve_tabular_delivery` |
| `case.dlq_enqueued` | case 進入 **DLQ**（retry 耗盡或 immediate DLQ） | `run_id` · `step_name` · `entry_id` · `failure_class` | `tabular_automation_driver_lib`（`enqueue_dlq` 後） |

#### 示例 log 條目（`case.idle_to_running`）

```json
{
  "schema_version": "tabular-internal-notify-v1",
  "case_id": "demo_phase",
  "last_event_at": "2026-06-27T12:00:00+00:00",
  "entries": [
    {
      "event": "case.idle_to_running",
      "ts": "2026-06-27T12:00:00+00:00",
      "case_id": "demo_phase",
      "payload": {
        "previous_status": "idle",
        "requested_by": "operator",
        "restart": false
      }
    }
  ]
}
```

### 1.12 Warning guard 策略（profile × guard → delivery_ready）

> **程式 SSOT**：`scripts/tabular_warning_guard_lib.py` · driver CP-B 與 `evaluate_delivery_readiness` 共用同一策略表。

Tabular 主鏈以 `report.json` → `output_guard.status`（`ok` · `warning` · `error`）作為交付品質 sidecar。**不**改變 cleaning exit code；但 **明確決定** `delivery_ready`、CP-B 是否可 auto-skip、以及 warning 下是否僅供 internal use。

#### Profile 解析

| `warning_guard_profile` | 對應 case | 說明 |
|-------------------------|-----------|------|
| `demo_phase` | `cases/demo_phase/` | regression 錨點 · guard 預期 `ok` |
| `sampleco` | `cases/sampleco/*` | 邊際品質 regression · guard 預期 `warning` |
| `generic_low_risk_case` | allowlist 內其他低風險 fixture | 非 demo/sampleco 的 low-risk 路徑 |
| `unknown` | allowlist 外 / 無 report | **fail-closed** |

#### 策略表（profile × guard 結果 × delivery_ready）

| Profile | `output_guard` | CP-B auto-skip | `delivery_ready`（CP-B+e2e 亦過） | Internal use | 備註 |
|---------|----------------|----------------|-----------------------------------|--------------|------|
| **demo_phase** | `ok` | ✅ | **true** | ✅ | 可 auto `delivery_ready=true` |
| **demo_phase** | `warning` | ❌ | **false** | partial（internal only） | 須 CP-B 人工；不可對外 ready |
| **demo_phase** | `error` | ❌ | **false** | ❌ | fail-closed · 須 rework |
| **sampleco** | `ok` | ✅ | **true** | ✅ | 少見（高 removal 時通常 warning） |
| **sampleco** | `warning` | ❌ | **false** | partial（internal only） | **by design** · CP-B HITL 必經 |
| **sampleco** | `error` | ❌ | **false** | ❌ | fail-closed |
| **generic_low_risk_case** | `ok` | ✅ | **true** | ✅ | 標準低風險 auto 路徑 |
| **generic_low_risk_case** | `warning` | ❌ | **false** | partial（internal only） | fail-closed 對外 · 可 internal |
| **generic_low_risk_case** | `error` | ❌ | **false** | ❌ | fail-closed |
| **unknown** | 任意 | ❌ | **false** | ❌ | 完全 fail-closed |

**產品裁決（v1）**：

- **`partial_ready`**：自動化鏈可跑完、產物可 internal 參考，但 **`delivery_ready` 永遠 false**（含人工 `--approve` override 亦不可設 true）。
- **`sampleco` + warning**：全鏈 PASS 屬預期；`delivery_ready=false` 為 **策略符合**，非 bug。
- **Human approve 邊界**：`approve_tabular_delivery --approve` 可記錄審計，但 warning/error 下 **`delivery_ready` 仍 false**（fail-closed）。

#### sampleco warning 示例（策略符合）

```json
{
  "warning_guard_profile": "sampleco",
  "output_guard_status": "warning",
  "partial_ready": true,
  "internal_use_allowed": true,
  "delivery_ready": false,
  "readiness_gaps": [
    "output_guard:output_guard.warning",
    "warning_guard:partial_ready_internal_only"
  ]
}
```

### 1.13 Tool-executor 使用邊界（v1 占位）

> **模組**：`scripts/tabular_tool_executor_hook_lib.py` · 完整 executor：`tools/tabular_tool_executor.py`（實驗線）

| 項 | v1 現況 |
|----|---------|
| **預設路徑** | driver / E2E **直調**本地 subprocess CLI（`clean_phase_demo.py` 等） |
| **可選 tool 路徑** | 僅 **cleaning profile allowlist** 下可設 `use_tool_executor=True`（占位） |
| **v1 行為** | **不**呼叫外部 executor；僅 log「若未來接工具，從 hook 進入」 |
| **CLI** | `run_tabular_automation.py --use-tool-executor`（stub · 仍跑本地腳本） |
| **非目標** | prod outbox replay · 改 MVP mainline semantics |

**允許考慮 tool-executor 的 cleaning profile（規劃）**：`phase_demo_v1` · `sampleco_order_profile` — 預設仍 `use_tool_executor=False`。

---

## 2. 接案到交付 — 近全自動 Runbook

### 2.1 流程總覽

```text
[HUMAN] Type gate + Start
    ↓
[R1] Intake ──auto/HITL──► case_dir + intake.json + raw/
    ↓
[R2] Eligibility gate ──auto──► eligibility_result.json
    ↓
[CP-A?] Intake confirmation ──HITL if triggered──► approve | reject | revise
    ↓
[R3] Cleaning execute ──auto──► cleaned CSV + cleaning_stats + report.json/md
    ↓
[R4] Stats/report finalize ──auto──► enrich report + guard sidecar
    ↓
[R5] Delivery bundle ──auto──► delivery_signoff.md draft + bundle metadata
    ↓
[R6] E2E validation ──auto──► overall_ok dict
    ↓
[CP-B?] Delivery confirmation ──HITL if triggered──► approve_delivery | hold
    ↓
[HUMAN] Stop/Pause 可穿插任意 atomic step 之間
```

### 2.2 逐步詳解

#### R1 · Intake

| 項 | 內容 |
|----|------|
| **輸入** | 原始 CSV/TSV · `client_ref` · `product_sku` · 可選 schema 筆記 |
| **輸出** | `cases/<client>/<case_id>/` · `intake.json` · `raw/<file>` |
| **Entrypoint** | `scripts/new_cleaning_case.py` · `intake.new_case` |
| **可自動化程度** | **HITL** — 系統可建議 `case_id`；人類確認 client 對應後 **start** |
| **失敗記錄** | CLI stderr · 可選 `reports/intake_error.json`（規劃） |
| **Index** | 建議緊接 `scripts/build_cases_index.py`（**auto**） |

#### R2 · Eligibility gate

| 項 | 內容 |
|----|------|
| **輸入** | `case_dir` · `intake.json` · raw file |
| **輸出** | `reports/eligibility_result.json` · exit 0/1/2 |
| **Entrypoint** | `scripts/check_case_eligibility.py` · `validate.eligibility` |
| **可自動化程度** | **auto** |
| **失敗記錄** | JSON `status=rejected` · reasons[] · subprocess exit code |
| **Stop** | `rejected` → 終止；`review_needed` → CP-A 或 demo `--force` |

#### R3 · Cleaning execute

| 項 | 內容 |
|----|------|
| **輸入** | 通過 gate 的 case · signed rules（intake + schema） |
| **輸出** | `cleaned/*_cleaned.csv` · `cleaning_stats.json` · `report.json` · `report.md` |
| **Entrypoint** | `notebooks/csv_cleaning/clean_phase_demo.py` · `clean.phase_demo` |
| **可自動化程度** | **auto**（allowlist + accepted 或 force 授權） |
| **失敗記錄** | `report.json` → errors · non-zero exit · outbox run record |
| **Stop** | schema 不符 · 0 output rows → 停 |

#### R4 · Stats / report generation

| 項 | 內容 |
|----|------|
| **輸入** | cleaning 產物 |
| **輸出** | enriched `report.json` · `output_guard` sidecar |
| **Entrypoint** | 內嵌於 `clean_phase_demo.py` + `output_guard.compute_output_guard` |
| **可自動化程度** | **auto** |
| **失敗記錄** | `qa_status=fail` · guard status |
| **備註** | bundle 前可 `--refresh-eligibility` |

#### R5 · Delivery bundle build

| 項 | 內容 |
|----|------|
| **輸入** | cleaned + reports + eligibility |
| **輸出** | `delivery_signoff.md` · bundle metadata in `report.json` |
| **Entrypoint** | `scripts/build_case_delivery_bundle.py` · `export.delivery_bundle` |
| **可自動化程度** | **auto** |
| **失敗記錄** | CLI JSON `ok: false` · missing artifacts list |

#### R6 · E2E validation

| 項 | 內容 |
|----|------|
| **輸入** | `case_dir` |
| **輸出** | `{ ok, overall_ok, steps, eligibility, bundle }` dict |
| **Entrypoint** | `scripts/run_case_e2e_validation.py` · `orchestrate.e2e` |
| **可自動化程度** | **auto** |
| **失敗記錄** | stdout JSON · per-step exit codes |
| **Regression** | `scripts/run_mvp_mainline_regression.py`（雙案） |

### 2.3 Checkpoint A / B — 自動跳過 vs 必須保留

#### Checkpoint A

| 情境 | 動作 |
|------|------|
| `auto_accept` + `low` + allowlist + `eligibility=accepted` | **自動跳過** |
| `eligibility=review_needed`（如 rows<100） | **必須保留**（或 demo 內部 `--force-review` 明示 bypass） |
| unknown fixture / `needs_review` | **必須保留** |
| 人類 **stop** 後 resume | **必須保留**（重新確認 route） |

**CLI**：`scripts/run_hitl_checkpoint_cli.py` · `hitl/checkpoint_a_integration_v1.py`（實驗線）

#### Checkpoint B

| 情境 | 動作 |
|------|------|
| `output_guard.status=ok` · `qa_status=pass` · removal_ratio ≤ 0.3 | **自動跳過** |
| `guard=warning` · `pass_with_warnings` · sampleco 高 removal | **必須保留** |
| `forced cleaning`（`--force` on review_needed） | **必須保留** |
| `qa_status=fail` | **必須保留**（預設 `hold`） |

**CLI**：`scripts/run_hitl_checkpoint_cli.py` · `hitl/checkpoint_b_integration_v1.py`

**Timeout 政策（設計）**：

- CP-A：5 分鐘無操作 → 可配置 auto-approve（**僅 internal demo**）
- CP-B：**不** auto-approve（timeout → `hold`）

---

## 3. 現有腳本對照表

> **目的**：一眼看出離「接近 100% 自動化」還差哪幾塊。  
> **圖例**：✅ 已存在 · ⚠️ 部分 · ❌ 缺失 · 🔒 僅 preview / 未接主鏈

| 步驟 | 現有 script / module | 已存在 | 可直接自動化 | 還缺什麼 |
|------|----------------------|--------|--------------|----------|
| **Type gate（人類）** | — | — | HITL | manifest 即 SSOT；無 CLI |
| **Start / Pause / Resume / Stop** | `scripts/manage_tabular_automation_state.py` | ✅ | ✅ | control plane v1 |
| **Unified driver** | `scripts/run_tabular_automation.py` · `tabular_automation_driver_lib.py` | ✅ | ⚠️ | CP resume 已接主鏈（v1.1）；retry/DLQ · post-CP-B delivery readiness hook |
| **R1 Intake** | `scripts/new_cleaning_case.py` | ✅ | ⚠️ | 自動 case_id 建議已有；缺 start 觸發與 upload API |
| **Index refresh** | `scripts/build_cases_index.py` | ✅ | ✅ | 可 hook 到 intake 後 auto |
| **Decision evaluate** | `routing/intake_decision_rules_v1.py` · `_v2.py` | ✅ | ⚠️ | v2 profile 擴展；非 allowlist → CP-A |
| **CP-A** | `hitl/checkpoints_v1.py` · `run_hitl_checkpoint_cli.py` · `checkpoint_a_integration_v1.py` | ✅ | ⚠️ | **主鏈 resume v1.1**（`approve-a` + `resume-after-checkpoint`）；timeout auto-approve 未統一 |
| **Route plan** | `routing/intake_to_tabular_glue.py` | ✅ | 🔒 | dry-run only；未接 `run_case_e2e` |
| **Tool select** | `tools/tabular_tool_selector.py` | ✅ | 🔒 | preview via `run_tabular_intake_tool_path.py` |
| **R2 Eligibility** | `scripts/check_case_eligibility.py` · `case_eligibility.py` | ✅ | ✅ | Excel 路徑需個案標記 |
| **R3 Cleaning** | `notebooks/csv_cleaning/clean_phase_demo.py` | ✅ | ⚠️ | **Phase-schema tight**；非通用 cleaner |
| **Tool execute + outbox** | `tools/tabular_tool_executor.py` · `tabular_outbox_writer.py` | ✅ | 🔒 | run mode 在實驗線；主鏈仍 subprocess 直調 |
| **R4 Stats / guard** | `clean_phase_demo.py` · `output_guard.py` | ✅ | ✅ | live guard 在 run path；主鏈 E2E 已間接覆蓋 |
| **R5 Bundle** | `scripts/build_case_delivery_bundle.py` · `case_delivery_bundle.py` | ✅ | ✅ | — |
| **R6 E2E** | `scripts/run_case_e2e_validation.py` | ✅ | ✅ | driver 已串；retry · CP resume 仍缺 |
| **CP-B** | `hitl/checkpoint_b_integration_v1.py` · `run_hitl_checkpoint_cli.py` | ✅ | ⚠️ | driver 可判定 skip/block；**主鏈 resume v1.1**（`approve-b` → `approved_for_delivery`） |
| **Delivery approve** | `scripts/approve_tabular_delivery.py` · `tabular_delivery_approval_lib.py` | ✅ | ⚠️ | CP-B 後 index/signoff 結構化更新 · 非 prod send |
| **Regression** | `scripts/run_mvp_mainline_regression.py` | ✅ | ✅ | — |
| **Notify** | `delivery/controlled_notify_experiment_v1.py` | ⚠️ | 🔒 | simulated only · 非 prod send |
| **Outbox consumer** | `tools/tabular_outbox_consumer.py` | ✅ | 🔒 | 未接實驗線 index sync |
| **Runbook planner** | `notebooks/csv_cleaning/run_tabular_cleaning_plan.py` | ✅ | ✅ | 僅清單；不執行 |
| **Local UI** | `app/local_ui.py` | ✅ | HITL | localhost wrapper · NOT PROD |
| **History lookup** | `scripts/lookup_case_history.py` | ✅ | ✅ | 接案前推薦只讀 |

**自動化覆蓋率（保守估算）**：

- 步驟級 **auto-ready**：9 / 15 ≈ **60%**（R2–R6 + index + regression + guard）
- 含 HITL 可編排：**~75%**
- 距「接近 100%」：**差在 orchestrator 接線 + CP resume + start/stop + 通用 cleaner**

---

## 4. 缺口分類與保守排序

### A. 立即可補（doc / state / runbook 級）

| 序 | 缺口 | 交付物 | 預估 |
|----|------|--------|------|
| A1 | **Automation control state** | ✅ `cases/_TEMPLATE_case/automation_state.json` · `docs/tabular-cleaning-control-plane-v1.md` · CLI | done |
| A2 | **Runbook 交叉引用** | `docs/C2-P2_RUNBOOK.md` 追加 §「自動化模式」指向本檔 | 0.5d |
| A3 | **SSOT 索引** | `docs/TABULAR_MVP_SSOT.md` §9 已引用本 manifest | 0.25d |
| A4 | **CP 跳過決策表** | 運營一頁紙（§2.3 已含）→ 可貼入 `docs/hitl-checkpoints-v1.md` 附錄 | 0.25d |
| A5 | **Ticket / planner state** | `04_Workflows/tickets/TAB-AUTO-MANIFEST-v1_state.md` | 0.25d |

### B. 需要小量工程（schema · 統一輸出 · 接線）

| 序 | 缺口 | 交付物 | 預估 | 依賴 |
|----|------|--------|------|------|
| B1 | **Unified automation driver** | `scripts/run_tabular_automation.py` — start/pause/stop + 鏈式調用現有 CLI | 2–3d | A1 |
| B2 | **Automation run log** | `reports/automation_run_log.json` schema + driver 寫入 | 1d | B1 |
| B3 | **Delivery approve CLI** | `scripts/approve_tabular_delivery.py` — CP-B 後更新 index/signoff/state | 1–2d | CP-B |
| B4 | **Retry / transient policy** | driver 內 3x retry + case-local `dlq/` 記錄 | ✅ v1 | B1 |
| B5 | **CP resume 接主鏈** | driver + `tabular_hitl_resume_lib.py` · `docs/tabular-hitl-resume-flow-v1.md` | ✅ v1.1 | B1 · hitl |
| B6 | **Glue → E2E 接線** | driver 可選 `--via-tool-executor` | 2d | B1 |
| B7 | **Configurable cleaning profile** | `intake.json` → `cleaning_profile` 映射（仍 low-risk） | 3–5d | 產品 |

### C. 暫不做（高風險 / 超出 tabular MVP）

| 序 | 缺口 | 原因 |
|----|------|------|
| C1 | Intake API gateway / 客戶自助上傳 | 範圍外 · 需 prod 安全審查 |
| C2 | Prod Telegram / SMTP 自動通知 | 實驗線 simulated only |
| C3 | Required CI / merge gate 升格 | Batch 1 hard_no |
| C4 | Phase% / Dashboard / closure 更新 | Governance 獨占 |
| C5 | 通用 Excel 多 sheet pipeline | 高複雜 · 非 low-risk MVP |
| C6 | 7×24 無 HITL 無人值守 | 與 Product Spec 衝突 |
| C7 | workflow yml / branch protection 變更 | 本任務明示禁止 |

**保守实施順序**：A1 → A2/A3 → B1 → B2 → B5 → B3 → B4 → B6 → B7

---

## 5. 結論

### 5.1 能否視為「可收口中的主產品線」？

**可以（有條件）** — 作為 **Tabular MVP doc/state 主線**，不是 prod closure 主線。

| 維度 | 判斷 |
|------|------|
| **文檔 SSOT** | ✅ `TABULAR_MVP_SSOT.md` + 本 manifest 已收斂邊界 |
| **可重跑主鏈** | ✅ `run_case_e2e_validation.py` + 雙案 regression 6/6 |
| **交付物結構** | ✅ cleaned + stats + report + bundle 穩定 |
| **自動化編排** | ⚠️ 步驟可 auto，但缺 **單一 driver + start/stop + CP resume** |
| **清洗通用性** | ⚠️ `clean_phase_demo` 為 Phase tight；sampleco 為實驗邊界 |
| **Prod / closure** | ❌ 依 Batch 1 **不得**宣稱 |

**一句話**：這條鏈已是 **「可演示、可回歸、可文檔收口」的 tabular MVP 主產品線**；要稱 **「接近 100% 自動化運營線」** 還差 orchestrator 与控制面（見 §5.2）。

### 5.2 距「接近 100%」最關鍵的 5 個缺口

補完下列 5 項後，在 allowlist + low-risk case 上可達 **~95% 自動化**（僅 CP-A/B 與 start/stop 人工）：

| # | 缺口 | 類別 | 完成後效果 |
|---|------|------|------------|
| **1** | **Unified automation driver**（`run_tabular_automation.py`：串 R1–R6 + 讀 control state） | B1 | ✅ v1 已落地；CP resume ✅ · retry/DLQ ✅ |
| **2** | **CP-A/B resume 接主鏈**（checkpoint 決策後自動續跑，非僅 preview CLI） | B5 | HITL 不阻斷編排；消除手工 subprocess |
| **3** | **Start / Pause / Stop control plane**（`automation_state.json` + CLI） | A1 ✅ · B1 driver ✅ | 人類 3 類決策已可落盤；driver 已讀寫 state |
| **4** | **Delivery approve 自動化**（CP-B approve → index/signoff 結構化更新） | B3 | ✅ v1 CLI 已落地；Lead 對外 send 仍 HITL |
| **5** | **Cleaning profile 抽象**（intake 驅動規則集，脫離 Phase 硬編欄位） | B7 | allowlist 外低風險 case 可 auto |

**不纳入前 5 但值得随后**：B6 tool-executor 接線 · A 类 doc 同步。

### 5.3 驗收錨點（doc-only 本輪）

```bash
# 主鏈仍可重跑（不改 semantics）
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
python scripts/run_mvp_mainline_regression.py -v

# Unified driver（allowlist + control plane start）
python scripts/manage_tabular_automation_state.py start \
  --case-dir cases/demo_phase --requested-by operator --json
python scripts/run_tabular_automation.py --case-id demo_phase --force --json

# Runbook planner 可列出與本 manifest 對齊的 stages
python notebooks/csv_cleaning/run_tabular_cleaning_plan.py --json
```

---

## 6. 附錄

### 6.1 `automation_state.json`（control plane schema · A1 ✅）

> **權威**：`docs/tabular-cleaning-control-plane-v1.md` · **CLI**：`scripts/manage_tabular_automation_state.py`

放置：`cases/<client_ref>/<case_id>/automation_state.json`（與 `intake.json` 同層）。模板見 `cases/_TEMPLATE_case/automation_state.json`。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `schema_version` | string | `tabular-automation-state-v1` |
| `case_id` | string | 與 intake 一致 |
| `automation_status` | enum | `idle` · `running` · `paused` · `stopped` · `completed` · `failed` |
| `start_requested_by` | string \| null | 最近一次 start / restart |
| `stop_requested_by` | string \| null | 最近一次 stop |
| `pause_reason` | string \| null | pause 原因 |
| `resume_requested_by` | string \| null | 最近一次 resume |
| `last_transition_ts` | string \| null | ISO-8601 UTC |
| `current_step` | string \| null | driver stage（R1–R6 / CP-A/B） |
| `allowed_to_auto_proceed` | boolean | driver 可否推進下一 step |
| `requires_hitl_checkpoint` | boolean | 是否阻塞於 HITL |
| `checkpoint_a_status` | enum | `not_required` · `pending` · `approved` · `rejected` |
| `checkpoint_b_status` | enum | same |
| `checkpoint_a_decided_by` | string \| null | CP-A 決策者 |
| `checkpoint_b_decided_by` | string \| null | CP-B 決策者 |
| `checkpoint_a_decided_at` | string \| null | CP-A 決策時間 |
| `checkpoint_b_decided_at` | string \| null | CP-B 決策時間 |
| `checkpoint_resume_step` | string \| null | approve 後下一 driver step（如 `cleaning` · `approved_for_delivery`） |
| `last_error` | string \| null | 最近一次 hard 失敗 |
| `last_error_at` | string \| null | ISO-8601 UTC · 最近一次錯誤時間 |
| `retry_count` | integer | transient 重試次數（成功 step 或 restart 清零） |
| `dlq_status` | enum | `none` · `queued` · `handled`（DLQ 僅收集；不自動重跑） |

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
  "checkpoint_a_status": "not_required",
  "checkpoint_b_status": "not_required",
  "checkpoint_a_decided_by": null,
  "checkpoint_b_decided_by": null,
  "checkpoint_a_decided_at": null,
  "checkpoint_b_decided_at": null,
  "checkpoint_resume_step": null,
  "last_error": null,
  "last_error_at": null,
  "retry_count": 0,
  "dlq_status": "none"
}
```

**狀態規則（CLI v1）**：`start` ← `idle`|`paused`；`stopped` 須 `start --restart`；`pause` ← `running`；`resume` ← `paused`；`stop` → `allowed_to_auto_proceed=false`。

### 6.2 與現有藍圖的關係

| 文件 | 關係 |
|------|------|
| `ninety-five-percent-automation-blueprint-v1.md` | S1–S15 架構母本 |
| `ninety-five-percent-automation-blueprint-v2.md` | Wave 7 實驗線 overlay |
| **本 manifest** | **可執行邊界契約** — allowed/forbidden · start/stop · output · non-claims |

### 6.3 修訂

| 版本 | 日期 | 說明 |
|------|------|------|
| v1 | 2026-06-27 | 初版 · Tabular Cleaning Automation Planner |

---

*Tabular Cleaning Automation Manifest v1 · doc-only · NOT PROD GATE · NOT CLOSURE*
