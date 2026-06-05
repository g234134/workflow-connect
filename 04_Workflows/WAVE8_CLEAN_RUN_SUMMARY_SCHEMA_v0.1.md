# Wave 8 – CLEAN-RUN-SUMMARY 派生摘要結構（v0.1）

> **票號**：`W8-CLEAN-RUN-SUMMARY-SCHEMA`  
> **性質**：spec / schema planning（**不寫程式**、**不修改** Wave 6/7/8 真相層 schema）  
> **受眾**：Outbox 發佈、BI／運營分析、Skill 蒸餾、Bridge 匯出預處理  
> **前置**：`WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`、`WAVE7_CLEAN_ORCH_STATE_MACHINE_v0.1.md`、`WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md`、`WAVE7_CLEAN_ORCH_INPUT_MAPPING_v0.1.md`、`WAVE8_CLEAN_ORDER_MODEL_v0.1.md`、`WAVE8_CLEAN_BILLING_FIELDS_v0.1.md`  
> **實現錨點**（只讀對照）：暗部 `core/wave7_orch_job_lifecycle.py`、`core/wave7_report_summary_producer.py`、`core/wave7_artifact_storage.py`、`core/wave8_m2_execution_engine.py`、`core/wave8_report_md_renderer.py`  
> **狀態**：**DRAFT-v0.1**

---

## 0. 文件目的與邊界

### 0.1 目的

定義 **`CLEAN-RUN-SUMMARY`**：單次 CLEAN job 跑完後，供 **Outbox／BI／運營分析／Skill 蒸餾** 消費的**派生摘要 JSON**。內容必須能從現有 Wave 6/7/8 **真相層**推導，不反向修改 `report.json`、`job_record`（runner 擴展欄位）、`manifest.json`、intake 契約。

### 0.2 邊界（必讀）

| 本文件是 | 本文件不是 |
|----------|------------|
| Outbox／analytics／knowledge distillation 用的**摘要視圖** | 新的真相層或 `report.json` 替代品 |
| 欄位映射與 `future_optional` 標註規劃 | 已落地的 Outbox producer 實作（另票） |
| 單 job 粒度（與 lifecycle 回傳對齊） | Order 主表全文（見 `WAVE8_CLEAN_ORDER_MODEL_v0.1.md`） |

**真相層權威**（本摘要僅引用、不擴欄）：

- `report.json`：`wave7_report_summary_producer.build_wave7_report`（當前含 `schema_version`、`job_id`、`summary`、`qa`）
- `job_record`：runner `build_runner_job_input`（`job_id`、`sku`、`client_ref`、`created_at`；終態時 lifecycle 附加 `status`、`completion_variant`）
- `manifest.json`：`ManifestV20`（`accepted_units`、`billing_units`、`rows[]`）
- lifecycle 回傳：`run_wave7_job` → `{ok, status, stage, artifacts, qa, job_record, checkpoint, storage_attempts, envelope_compute_count, …}`
- 可選：`intake_record`（`intake_id`）、Order 側車（`order_id`）、`WAVE8_CLEAN_BILLING_FIELDS` Order 級 `cost_estimate`

### 0.3 產出時機（建議）

在 **S5 finalize 成功** 或 **失敗終態** 且已有可稽核真相時，由 **Outbox adapter**（未實作）組裝；組裝輸入建議為：

1. `run_wave7_job` 結構化回傳  
2. 已落盤的 `report.json`（若存在）  
3. 可選 Order／intake 側車  

---

## 1. 頂層結構

```text
CLEAN-RUN-SUMMARY
├── schema_version          # 固定 "clean_run_summary_v0.1"
├── generated_at            # 摘要組裝時刻（ISO-8601 UTC）
├── identity                # 作業與商務身份
├── input_volume            # 輸入規模（可空）
├── outcome                 # 結果與質量總覽
├── qa_layers               # M1/M2 蒸餾
├── runtime_stats           # 執行時序與重試
├── artifacts               # 邏輯引用（w6://）
├── costs                   # 成本與計費提示
└── provenance              # 可選：真相來源指針（BI 血緣）
```

### 1.1 頂層欄位總表

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `schema_version` | string | ✅ | 本契約版本；v0.1 固定 `clean_run_summary_v0.1` |
| `generated_at` | string (ISO-8601) | ✅ | 摘要文件生成時間（**非** job 開始時間） |
| `identity` | object | ✅ | §2 |
| `input_volume` | object | ✅ | §3；子欄位可為 `null` |
| `outcome` | object | ✅ | §4 |
| `qa_layers` | object | ✅ | §5 |
| `runtime_stats` | object | ✅ | §6；部分子欄位 `future_optional` |
| `artifacts` | object | ✅ | §7 |
| `costs` | object | ✅ | §8 |
| `provenance` | object | — | §9；建議 Outbox 填寫 |

---

## 2. `identity` — 作業與商務身份

| 欄位 | 類型 | 必填 | 含義 | 典型來源 | 穩定性 |
|------|------|------|------|----------|--------|
| `job_id` | string | ✅ | 全局唯一 CLEAN job ID | `job_record.job_id`；`report.job_id` | **stable** |
| `product_sku` | enum | ✅ | `CLEAN-BASIC` / `CLEAN-ENRICH` | `job_record.sku`；`report.summary.sku` | **stable** |
| `intake_id` | string \| null | — | Intake 對話／表單 UUID | `intake_record.intake_id`；**未**寫入 `job_record` 時為 null | **future_optional**（映射已規劃，runner 未寫） |
| `order_id` | string \| null | — | 商務訂單 ID（一單多 job） | Order 主表 `jobs[].job_id` 反查；Bridge 注入 | **future_optional** |
| `client_ref` | string | ✅ | 客戶／專案引用（非 secret） | `job_record.client_ref`；Order `client_ref` | **stable**（runner 已寫） |
| `batch_tag` | string \| null | — | 訂單內批次標籤 | Order `jobs[].batch_tag` | **future_optional** |

**約束**：

- `product_sku` 與 manifest `product_sku`、report `summary.sku` 必須一致；不一致時 Outbox **不得** 發佈摘要，應標阻塞。  
- 禁止在摘要中嵌入 inbound 實體路徑或 env 原文（對齊憲法 §7 類型）。

---

## 3. `input_volume` — 輸入規模

描述 **進入 S3 前／entry 時** 的輸入規模；與 manifest **處理後** 行數分離。

| 欄位 | 類型 | 必填 | 含義 | 典型來源 | 穩定性 |
|------|------|------|------|----------|--------|
| `file_count` | int \| null | — | 有效輸入文件數 | runner `input_count`；`len(raw_files)` | **derived** |
| `row_count` | int \| null | — | 估計或實際輸入行數 | intake `data_profile.row_count_estimate`；manifest `summary.total_rows`（處理後，僅作 fallback） | **derived** |
| `size_bytes` | int \| null | — | 輸入總字節 | `sum(raw_files[].size_bytes)`（欄位可選）；intake 檔案清單 | **derived** / **future_optional**（`size_bytes` 常缺） |
| `skipped_file_count` | int | — | entry 跳過檔數 | runner `skipped[]` 長度 | **derived** |

**nullable 語義**：無掃描／無 intake 估計時填 `null`，**禁止** 以 0 冒充「已度量」。

---

## 4. `outcome` — 結果與質量總覽

| 欄位 | 類型 | 必填 | 含義 | 典型來源 | 穩定性 |
|------|------|------|------|----------|--------|
| `accepted_units` | int | ✅ | manifest ok 行數（計費 U 基數） | `manifest.accepted_units`；`report.summary.accepted_units` | **stable** |
| `rejected_units` | int | ✅ | 非 ok 行數 | `report.summary.rejected_units`；manifest rows 計數 | **stable** |
| `billing_units` | object | ✅ | `{U, L}` | `report.summary.billing_units`；`manifest.billing_units` | **stable** |
| `qa_status` | enum | ✅ | `pass` / `pass_with_warnings` / `fail` | `report.summary.qa_status` | **stable**（report 已產出時） |
| `completion_variant` | enum \| null | — | `completed` / `completed_with_failures`；僅 `status=done` | `job_record.completion_variant`；lifecycle `completion_variant`；缺省視為 `completed` | **derived**（**未**寫入當前 `report.summary`） |
| `overall_ok` | bool | ✅ | M1∧M2 合併 OK | `report.qa.overall_ok` | **stable** |
| `orch_status` | enum | ✅ | `PENDING`/`RUNNING`/`DONE`/`FAILED`/`BLOCKED` | `job_record.status` 映射（見 `WAVE7_CLEAN_ORCH_STATE_MACHINE_v0.1.md` §3.1） | **derived** |
| `job_status` | enum | ✅ | lifecycle 原值：`pending`/`running`/`done`/`failed`/`blocked` | `job_record.status` | **stable** |

**`completion_variant` 推導規則**（與實作一致）：

- `job_status=done` 且 lifecycle 設 `completed_with_failures` → `completion_variant=completed_with_failures`（manifest 有 rejected 且 M1 無 P0）。  
- `job_status=done` 且無該欄位 → `completed`。  
- 非 `done` → `completion_variant=null`。

**失敗終態**：`qa_status` 可為 `fail` 或缺失（report 未生成）；`overall_ok=false`；Outbox 仍可依政策發佈「失敗摘要」供分析。

---

## 5. `qa_layers` — M1 / M2 蒸餾

從 `report.qa` 蒸餾；**不**複製完整 `failures[]`（大列表留在 `report.json`）。

### 5.1 `m1_summary`

| 欄位 | 類型 | 必填 | 含義 | 典型來源 | 穩定性 |
|------|------|------|------|----------|--------|
| `ok` | bool | ✅ | M1 manifest 完整性 | `report.qa.manifest_integrity.ok` | **stable** |
| `checked_rows` | int | ✅ | M1 檢查行數 | `report.qa.manifest_integrity.checked_rows` | **stable** |
| `failed_rows` | int | — | M1 失敗行數 | `manifest_integrity.failed_rows` | **stable** |
| `failed_checks` | int | — | M1 失敗檢查項計數 | `manifest_integrity.failed_checks` | **stable** |
| `p0_failure_count` | int | — | `failures[]` 中 `layer≠M2` 且 `severity=P0` 條數 | 由 `report.qa.failures` **derived** | **derived** |
| `p1_failure_count` | int | — | 同上 P1 | **derived** | **derived** |

### 5.2 `m2_summary`

| 欄位 | 類型 | 必填 | 含義 | 典型來源 | 穩定性 |
|------|------|------|------|----------|--------|
| `status` | enum | ✅ | `skipped` / `completed` / `error` | `report.qa.sample_validation.status` | **stable** |
| `ok` | bool | ✅ | 抽樣深檢是否通過 | `sample_validation.ok` | **stable** |
| `N` | int \| null | — | 母體 ok 行數 | `sample_validation.N` | **stable** |
| `sample_size` | int \| null | — | 抽樣數 | `sample_validation.sample_size` | **stable** |
| `seed` | int \| null | — | 抽樣種子 | `sample_validation.seed` | **stable** |
| `failed_checks` | int | — | M2 失敗檢查計數 | `sample_validation.failed_checks` | **stable** |
| `p0_failure_count` | int | — | M2 failures P0 條數 | `report.qa.failures` 過濾 `layer=M2` | **derived** |
| `p1_failure_count` | int | — | M2 failures P1 條數 | **derived** | **derived** |
| `reason` | string \| null | — | `skipped`/`error` 原因 | `sample_validation.reason` | **stable** |

**Wave 7 無 M2**：`status=skipped`，`reason` 常為 Wave 7 deferred 文案（見 `M2_SAMPLE_VALIDATION_SKIPPED`）。

**交付模板中的** `m1_checks_summary` / `m2_checks_summary`：**未**由當前 `build_wave7_report` 寫入 report → 摘要**不包含**（若未來 report 擴充，可另開 v0.2 摘要票）。

---

## 6. `runtime_stats` — 執行時序與重試

| 欄位 | 類型 | 必填 | 含義 | 典型來源 | 穩定性 |
|------|------|------|------|----------|--------|
| `started_at` | string \| null | — | job 開始（UTC ISO-8601） | `job_record.started_at` | **future_optional**（lifecycle **未** 寫入；renderer 僅讀取） |
| `completed_at` | string \| null | — | job 結束 | `job_record.completed_at` | **future_optional** |
| `duration_ms` | int \| null | — | `completed_at - started_at` | 計算欄位 | **future_optional** |
| `lifecycle_schema_version` | string | — | lifecycle 契約版本 | lifecycle `schema_version` | **stable** |
| `final_stage` | string | — | 終止時 stage | lifecycle `stage` | **stable** |
| `storage_retry_count` | int | — | storage finalize 嘗試次數 | lifecycle `storage_attempts` | **stable** |
| `envelope_compute_count` | int | — | envelope 計算次數（重跑指標） | lifecycle `envelope_compute_count` | **stable** |
| `checkpoint` | enum | — | `none` / `manifest` | lifecycle `checkpoint` | **stable** |
| `checkpoint_hit` | bool | — | 是否曾在 manifest checkpoint 後 resume | `checkpoint=manifest` 且 `envelope_compute_count` 未增加等策略 | **derived** |
| `error_code` | string \| null | — | 終態錯誤碼 | lifecycle `error_code` | **stable**（失敗時） |
| `message` | string | — | 人讀摘要 | lifecycle `message` | **stable** |

**`checkpoint_hit` 建議語義（v0.1）**：`checkpoint=manifest` 且 `storage_retry_count>1` 或 hook 標記 resume → `true`；否則 `false`。

**`report.summary` / deliverable 模板中的 `processing_time_ms`**：當前 report 生產者**未**輸出 `stats` 區塊 → 摘要層標 **future_optional**（不納入 v0.1 必填）。

---

## 7. `artifacts` — 邏輯引用

一律使用 **`w6://delivery/{job_id}/{kind}`** 邏輯 ref（見 `wave7_artifact_storage.w6_logical_ref`），禁止實體絕對路徑。

| 欄位 | 類型 | 必填 | 含義 | 典型來源 | 穩定性 |
|------|------|------|------|----------|--------|
| `report_json_ref` | string \| null | — | report.json | lifecycle `artifacts.report_ref` | **stable**（finalize 成功） |
| `report_md_ref` | string \| null | — | report.md | `artifacts.report_md_ref`；僅 `render_report_md=true` 且寫入成功 | **derived** |
| `manifest_ref` | string | ✅ | manifest.json | `artifacts.manifest_ref` | **stable** |
| `deliverable_refs` | string[] | — | 信封目錄等 | `[artifacts.deliverables_ref]`；可擴 manifest 行級 ref | **stable** |
| `report_md_rendered` | bool | — | MD 是否成功渲染 | lifecycle store `report_md_render.ok` | **derived** |

失敗終態且未 finalize：`report_json_ref` / `report_md_ref` 可為 `null`，`manifest_ref` 仍可有（checkpoint manifest）。

---

## 8. `costs` — 成本與計費提示

| 欄位 | 類型 | 必填 | 含義 | 典型來源 | 穩定性 |
|------|------|------|------|----------|--------|
| `billing_table_version` | string | — | 計費表版本 | `report.summary.cost.billing_table_version` | **stable** |
| `billing_units` | object | — | `{U, L}` 快照 | `report.summary.billing_units` | **stable** |
| `chargeable_hint` | bool | — | 結構就緒、價格非 null 時可開票提示 | `report.summary.chargeable_hint` 或 `cost.chargeable_hint` | **stable** |
| `tool_cost_estimate` | number \| null | — | 工具成本預估 | Order `cost_estimate.tool_cost_estimate` | **future_optional**（job 級未寫入 report） |
| `human_hours_estimate` | number \| null | — | 人力工時預估 | Order `cost_estimate.human_hours_estimate` | **future_optional** |
| `currency` | string | — | 幣別 | `report.summary.cost.currency` | **stable**（預設 USD） |

**約束**：

- `chargeable_hint` **≠** 最終 Chargeable 裁定（見 R3／DELIVERABLE_TEMPLATES §3）。  
- `tool_cost_estimate` / `human_hours_estimate` 在 Order 規格已定義，**當前主鏈不寫入 report**；摘要可從 Order 側車 JOIN，無 Order 則 `null`。

---

## 9. `provenance` — 真相血緣（建議）

| 欄位 | 類型 | 必填 | 含義 |
|------|------|------|------|
| `report_schema_version` | string \| null | — | 如 `wave7_report_v0.1` |
| `lifecycle_schema_version` | string \| null | — | 如 `wave7_orch_job_lifecycle_v0.1` |
| `source_event` | string | — | 如 `wave7.job.finalized` / `wave7.job.failed` |
| `truth_refs` | object | — | `{report_json, manifest}` 邏輯 ref 副本 |

---

## 10. 來源映射總表

**圖例**：**stable** = 真相層直接欄位；**derived** = 規則計算；**future_optional** = 規格／側車有、主鏈未寫或 Outbox 未接。

| CLEAN-RUN-SUMMARY 路徑 | 上游來源（模組／文檔） | 穩定性 |
|------------------------|------------------------|--------|
| `schema_version` | 本文件固定 | stable |
| `generated_at` | Outbox 組裝時鐘 | derived |
| `identity.job_id` | `job_record` / `report` · `wave7_runner_entry_job_input` | stable |
| `identity.product_sku` | `job_record.sku` · `WAVE6_CLEAN_PRODUCT_MATRIX` | stable |
| `identity.intake_id` | `intake_record` · `WAVE7_CLEAN_ORCH_INPUT_MAPPING` §2 | future_optional |
| `identity.order_id` | `WAVE8_CLEAN_ORDER_MODEL` §4.1 | future_optional |
| `identity.client_ref` | `job_record.client_ref` · runner | stable |
| `identity.batch_tag` | Order `jobs[]` | future_optional |
| `input_volume.file_count` | runner `input_count` / `raw_files` | derived |
| `input_volume.row_count` | intake estimate / manifest `total_rows` | derived |
| `input_volume.size_bytes` | `raw_files[].size_bytes` / intake | future_optional |
| `input_volume.skipped_file_count` | runner `skipped[]` | derived |
| `outcome.accepted_units` | manifest / `report.summary` · `wave7_report_summary_producer` | stable |
| `outcome.rejected_units` | `report.summary` | stable |
| `outcome.billing_units` | manifest / `report.summary` | stable |
| `outcome.qa_status` | `report.summary` · R3 §G.6–G.7 | stable |
| `outcome.completion_variant` | lifecycle / `job_record` · `wave7_orch_job_lifecycle` | derived |
| `outcome.overall_ok` | `report.qa` | stable |
| `outcome.orch_status` | `WAVE7_CLEAN_ORCH_STATE_MACHINE` §3.1 | derived |
| `outcome.job_status` | lifecycle `status` | stable |
| `qa_layers.m1_summary.*` | `report.qa.manifest_integrity` · `wave6_qa_manifest_m1` | stable |
| `qa_layers.m1_summary.p0/p1_failure_count` | `report.qa.failures` 聚合 | derived |
| `qa_layers.m2_summary.*` | `report.qa.sample_validation` · `wave8_m2_execution_engine` | stable |
| `qa_layers.m2_summary.p0/p1_failure_count` | `report.qa.failures` 過濾 M2 | derived |
| `runtime_stats.started_at` / `completed_at` / `duration_ms` | `job_record` 擴展 | future_optional |
| `runtime_stats.storage_retry_count` | lifecycle `storage_attempts` | stable |
| `runtime_stats.envelope_compute_count` | lifecycle | stable |
| `runtime_stats.checkpoint` | lifecycle `checkpoint` | stable |
| `runtime_stats.checkpoint_hit` | lifecycle 推導 | derived |
| `runtime_stats.error_code` / `message` | lifecycle | stable |
| `artifacts.*_ref` | lifecycle `artifacts` · `wave7_artifact_storage` | stable / derived |
| `costs.chargeable_hint` | `report.summary` · `wave7_report_summary_producer` | stable |
| `costs.billing_table_version` | `report.summary.cost` | stable |
| `costs.tool_cost_estimate` | `WAVE8_CLEAN_BILLING_FIELDS` Order 級 | future_optional |
| `costs.human_hours_estimate` | 同上 | future_optional |

---

## 11. JSON 範例

### 11.1 CLEAN-BASIC — 成功案例

```json
{
  "schema_version": "clean_run_summary_v0.1",
  "generated_at": "2026-06-04T18:05:12Z",
  "identity": {
    "job_id": "w7-basic-acme-corp-2026-a1b2c3d4",
    "product_sku": "CLEAN-BASIC",
    "intake_id": "c1b2a3d4-5678-90ab-cdef-1234567890ab",
    "order_id": null,
    "client_ref": "acme-corp-2026Q2",
    "batch_tag": null
  },
  "input_volume": {
    "file_count": 12,
    "row_count": 9840,
    "size_bytes": 2457600,
    "skipped_file_count": 0
  },
  "outcome": {
    "accepted_units": 9720,
    "rejected_units": 120,
    "billing_units": { "U": 9720, "L": 0 },
    "qa_status": "pass",
    "completion_variant": "completed",
    "overall_ok": true,
    "orch_status": "DONE",
    "job_status": "done"
  },
  "qa_layers": {
    "m1_summary": {
      "ok": true,
      "checked_rows": 9840,
      "failed_rows": 120,
      "failed_checks": 0,
      "p0_failure_count": 0,
      "p1_failure_count": 0
    },
    "m2_summary": {
      "status": "completed",
      "ok": true,
      "N": 9720,
      "sample_size": 97,
      "seed": 42,
      "failed_checks": 0,
      "p0_failure_count": 0,
      "p1_failure_count": 0,
      "reason": null
    }
  },
  "runtime_stats": {
    "started_at": null,
    "completed_at": null,
    "duration_ms": null,
    "lifecycle_schema_version": "wave7_orch_job_lifecycle_v0.1",
    "final_stage": "storage",
    "storage_retry_count": 1,
    "envelope_compute_count": 1,
    "checkpoint": "manifest",
    "checkpoint_hit": false,
    "error_code": null,
    "message": "wave7_job_done"
  },
  "artifacts": {
    "report_json_ref": "w6://delivery/w7-basic-acme-corp-2026-a1b2c3d4/report_json",
    "report_md_ref": "w6://delivery/w7-basic-acme-corp-2026-a1b2c3d4/report_md",
    "manifest_ref": "w6://delivery/w7-basic-acme-corp-2026-a1b2c3d4/manifest",
    "deliverable_refs": [
      "w6://delivery/w7-basic-acme-corp-2026-a1b2c3d4/deliverables"
    ],
    "report_md_rendered": true
  },
  "costs": {
    "billing_table_version": "wave6_billing_v0.1",
    "billing_units": { "U": 9720, "L": 0 },
    "chargeable_hint": false,
    "tool_cost_estimate": null,
    "human_hours_estimate": null,
    "currency": "USD"
  },
  "provenance": {
    "report_schema_version": "wave7_report_v0.1",
    "lifecycle_schema_version": "wave7_orch_job_lifecycle_v0.1",
    "source_event": "wave7.job.finalized",
    "truth_refs": {
      "report_json": "w6://delivery/w7-basic-acme-corp-2026-a1b2c3d4/report_json",
      "manifest": "w6://delivery/w7-basic-acme-corp-2026-a1b2c3d4/manifest"
    }
  }
}
```

> 註：`intake_id` 在範例中展示欄位形狀；若無 intake 側車接入 Outbox，生產環境應為 `null`。`chargeable_hint=false` 反映當前 billing_table 價格為 null 的實作行為。

### 11.2 CLEAN-ENRICH — `completed_with_failures` + `pass_with_warnings`

```json
{
  "schema_version": "clean_run_summary_v0.1",
  "generated_at": "2026-06-04T20:41:03Z",
  "identity": {
    "job_id": "w7-enrich-acme-corp-2026-e5f6a7b8",
    "product_sku": "CLEAN-ENRICH",
    "intake_id": "e5f6g7h8-1234-5678-90ab-cdef12345678",
    "order_id": "ORD-20260604-E001",
    "client_ref": "acme-corp-2026Q2",
    "batch_tag": "batch-1"
  },
  "input_volume": {
    "file_count": 48,
    "row_count": 125000,
    "size_bytes": null,
    "skipped_file_count": 2
  },
  "outcome": {
    "accepted_units": 118400,
    "rejected_units": 6600,
    "billing_units": { "U": 118000, "L": 3200 },
    "qa_status": "pass_with_warnings",
    "completion_variant": "completed_with_failures",
    "overall_ok": true,
    "orch_status": "DONE",
    "job_status": "done"
  },
  "qa_layers": {
    "m1_summary": {
      "ok": true,
      "checked_rows": 125000,
      "failed_rows": 6600,
      "failed_checks": 0,
      "p0_failure_count": 0,
      "p1_failure_count": 0
    },
    "m2_summary": {
      "status": "completed",
      "ok": true,
      "N": 118400,
      "sample_size": 384,
      "seed": 20260604,
      "failed_checks": 3,
      "p0_failure_count": 0,
      "p1_failure_count": 3,
      "reason": null
    }
  },
  "runtime_stats": {
    "started_at": null,
    "completed_at": null,
    "duration_ms": null,
    "lifecycle_schema_version": "wave7_orch_job_lifecycle_v0.1",
    "final_stage": "storage",
    "storage_retry_count": 2,
    "envelope_compute_count": 1,
    "checkpoint": "manifest",
    "checkpoint_hit": true,
    "error_code": null,
    "message": "wave7_job_done"
  },
  "artifacts": {
    "report_json_ref": "w6://delivery/w7-enrich-acme-corp-2026-e5f6a7b8/report_json",
    "report_md_ref": "w6://delivery/w7-enrich-acme-corp-2026-e5f6a7b8/report_md",
    "manifest_ref": "w6://delivery/w7-enrich-acme-corp-2026-e5f6a7b8/manifest",
    "deliverable_refs": [
      "w6://delivery/w7-enrich-acme-corp-2026-e5f6a7b8/deliverables"
    ],
    "report_md_rendered": true
  },
  "costs": {
    "billing_table_version": "wave6_billing_v0.1",
    "billing_units": { "U": 118000, "L": 3200 },
    "chargeable_hint": false,
    "tool_cost_estimate": 2500.00,
    "human_hours_estimate": 6.0,
    "currency": "USD"
  },
  "provenance": {
    "report_schema_version": "wave7_report_v0.1",
    "lifecycle_schema_version": "wave7_orch_job_lifecycle_v0.1",
    "source_event": "wave7.job.finalized",
    "truth_refs": {
      "report_json": "w6://delivery/w7-enrich-acme-corp-2026-e5f6a7b8/report_json",
      "manifest": "w6://delivery/w7-enrich-acme-corp-2026-e5f6a7b8/manifest"
    }
  }
}
```

> 註：`completion_variant=completed_with_failures` 來自 lifecycle（有 rejected 行且 M1 無 P0）；`qa_status=pass_with_warnings` 來自 M2 P1 failures（`wave7_report_summary_producer._map_qa_status_from_failures`）。`costs.tool_cost_estimate` / `human_hours_estimate` 在範例中展示 **Order 側車 JOIN** 形狀；無 Order 接入時應為 `null`。`order_id` / `batch_tag` 同為 **future_optional**。

---

## 12. Outbox / 消費方契約（規劃）

| 消費方 | 建議用法 | 禁止 |
|--------|----------|------|
| **Outbox** | job 終態事件 payload；附 `provenance.truth_refs` | 把摘要寫回 manifest／report |
| **BI** | 按 `product_sku`、`qa_status`、`orch_status` 聚合；join Order 用 `order_id` | 用摘要覆蓋 `accepted_units` 真相 |
| **運營** | 儀表板：成功率、`pass_with_warnings` 占比、`completed_with_failures` 占比 | 將 `chargeable_hint` 當收款狀態 |
| **Skill 蒸餾** | 高信噪比特徵：`qa_layers`、`outcome`、精簡 `runtime_stats` | 依賴未實現欄位訓練（`started_at` 等） |

**事件名建議**（非實作）：`clean.run.summary.v0.1`（成功）、`clean.run.summary_failed.v0.1`（失敗終態）。

---

## 13. 版本與後續票

| 項目 | 說明 |
|------|------|
| v0.2 候選 | report 增加 `stats`／`completion_variant` 進 `summary` 後，縮減 derived 規則 |
| Outbox producer | 另票：讀 lifecycle + report + 可選 Order → 校驗本 schema |
| JSON Schema 落盤 | 另票；本稿不帶 `$schema` 檔 |

---

## Work Report

| 節 | 內容 |
|----|------|
| **§1 變更檔案** | 新增 `04_Workflows/WAVE8_CLEAN_RUN_SUMMARY_SCHEMA_v0.1.md` |
| **§2 skeleton** | 無（本輪為完整 spec 草稿，非程式 skeleton） |
| **§3 placeholder** | `provenance` 消費約定、`source_event` 枚舉、Outbox producer 為規劃占位，未宣稱已實作 |
| **§4 驗證證據** | 文檔工單自檢（APP-DOC）：可移植正文零本機絕對路徑 — **是**；禁區僅類型 — **是**；未改真相層 schema — **是**；`future_optional` 未寫成已實現 — **是**（對照暗部 `wave7_report_summary_producer`、`wave7_orch_job_lifecycle`、`WAVE7_CLEAN_ORCH_INPUT_MAPPING` §2）；地圖／任務範圍對齊 Wave 8 清洗鏈 — **是** |
| **§5 阻塞** | 無 |
| **§6 下一步** | （1）尚書省評審 v0.1；（2）另票 Outbox adapter + 可選 JSON Schema；（3）若 `job_record.started_at`／`intake_id` 落地，升級映射表穩定性標記 |
| **§7 override** | 無 |

---

*Wave 8 spec · `04_Workflows/WAVE8_CLEAN_RUN_SUMMARY_SCHEMA_v0.1.md` · DRAFT-v0.1*
