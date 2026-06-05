# Wave 6 – DATA-CLEANING · R3 附錄（v0.1 · spec only）

> **輪次**：W6-R3 · **範圍**：manifest 抽樣 QA · Phase 8.6 鍵名對照 · BASIC→ENRICH 補跑 delta · 財務填表對齊  
> **不做**：code · runner · orchestrator 節點／流程圖 · 改寫 R1／R2 **FROZEN** 條文  
> **承接**：`WAVE6_DATA_CLEANING_R2_APPENDICES_v0.1.md`（R2 附錄 A–D 視為不可變）  
> **權威對齊**：W6-R1 交付物／Done·Chargeable · Phase 8.6 `orchestration_bridge_v1` · Phase 6.5 `delivery`／`invoice`

---

## 0. W6-R3 範圍說明

| 項 | 說明 |
|----|------|
| **目標** | 把 Wave 6 收斂到**可執行、可驗收、可交接**的規則層（QA 抽樣、橋接鍵名、升級補跑、財務填表） |
| **本輪新增** | 附錄 G（QA）· H（8.6 對照）· I（補跑 delta）· J（billing_table 填表） |
| **本輪不碰** | R2 §A–D 數值與算法 · `enrichment_v0.1` 欄位表 · `Q_min` · `quality_score` 扣分表 |
| **R2 §F 結案** | R2 列為 W6-R3 的四項，本檔 **結案** |
| **出口狀態** | **R3-CLOSED-BY-R4**；TBD 見 `WAVE6_DATA_CLEANING_R4_RATIFICATIONS_v0.1.md`；財務 `list.*` 填值不屬 spec 封口 |

**交接物**：本檔可整段貼入 roadmap／`master_status` Wave 6 小節；實作工單：`W6-IMPL-QA`／`W6-IMPL-BRIDGE-MAP`／`W6-IMPL-UPGRADE`／`W6-IMPL-BILLING-TABLE`（僅索引，本輪不開工）。

---

## 1. manifest 抽樣 QA（附錄 G · 員工 A）

### G.1 兩層驗證（必須區分）

| 層級 | 代碼 | 範圍 | 對象 | 與抽樣關係 |
|------|------|------|------|------------|
| **全量 manifest 完整性** | **M1** | `manifest.json` **每一列** | manifest 列（非 envelope 檔內容） | **不抽樣**；100% 列檢查 |
| **信封深度校驗** | **M2** | 抽樣列對應之 envelope 檔 | `deliverables/` 內 JSON | **抽樣**；依 §G.2 |

**禁止**把 M1 稱為「抽查」；**禁止**用 M2 抽樣結果代替 M1。

### G.2 抽樣規模（R1 #2 · 本輪裁定）

設 `N` = manifest 中 `clean_status=ok` 列數（= W6-R1 `accepted_units`）。

| 符號 | 公式 |
|------|------|
| `sample_size` | `min(N, max(20, ⌈0.10 × N⌉))` |
| 下限 | 當 `N > 0` 時至少抽 **20** 列（若 `N < 20` 則 `sample_size = N` 全抽） |
| 比例 | **10%** 向上取整，與下限取大 |

**抽樣對象**：manifest 內 **`clean_status=ok`** 列（成功單位）；**不**對 `failures_index` 列做 M2（除非整 job `failed` 調查）。

**抽樣方法（可重跑）**：

1. 以 `job_id` + `billing_table_version`（缺則用字串 `w6_billing_v0.1`）為 seed；  
2. 對 ok 列按 `content_sha256` 字典序排序；  
3. 均勻間隔抽取 `sample_size` 列（deterministic stride）；  
4. 若 `N > 500`，另保證至少 **5** 列來自 `extension` 前綴長度 ≥4 的**不同**副檔名桶（分層覆蓋，見 §G.2.1）。

#### G.2.1 分層覆蓋（僅 `N > 500`）

| 桶 | 條件 | 至少抽樣列數 |
|----|------|-------------|
| 程式碼 | `.py` `.js` `.ts` `.rs` `.go` | 3 |
| 標記／設定 | `.md` `.json` `.yaml` `.yml` `.toml` | 3 |
| 其他 | 其餘 | 2（併入 stride 主抽樣） |

桶內不足則抽該桶全部。

### G.3 M1 全量檢查項（每列必過）

| check_id | 規則 | 嚴重度 |
|----------|------|--------|
| M1-KEYS | 必填鍵存在：`file_id`、`content_sha256`、`clean_status`、`extension`、`stored_logical_path`、`schema_version` | P0 |
| M1-OK-ONLY | 計入 `accepted_units` 的列僅 `clean_status=ok` | P0 |
| M1-SHA | `content_sha256` 為 64 位 hex | P0 |
| M1-SKU-BASIC | `job_record.sku=CLEAN-BASIC` ⇒ 列上 **不得** 有 `enrichment` 鍵（manifest 層宣告） | P0 |
| M1-SKU-ENRICH | `job_record.sku=CLEAN-ENRICH` ⇒ 列上 `has_enrichment=true`（manifest 摘要旗標） | P0 |
| M1-DEDUP | 同 job 內 `content_sha256` 唯一 | P0 |
| M1-COUNT | ok 列數 = `report.summary.accepted_units` | P0 |

### G.4 M2 深度檢查項（僅抽樣列）

| check_id | 規則 | 嚴重度 |
|----------|------|--------|
| M2-SCHEMA-20 | 檔內 `schema_version=2.0` | P0 |
| M2-GROQ-BASIC | BASIC job ⇒ `groq_used=false`（R2 §D R-GROQ-1） | P0 |
| M2-ENRICH-BLOCK | ENRICH job ⇒ 存在 `enrichment` 且 `enrichment.schema_version=enrichment_v0.1`（R2 §C） | P0 |
| M2-QUALITY | `quality_score` 可用 R2 §C.4 重算，誤差 **0** | P1 |
| M2-PATH-LEAK | `source_path`／`stored_path` 若存在，不得含磁碟根特徵（`:\`、`://`）於**交付**副本 | P1 |
| M2-PREVIEW-LEN | `content_summary.preview_lines` ≤10 行 | P2 |

### G.5 失敗回報格式（`qa_failure_record`）

每筆失敗 **一列一物件**，寫入 `report.json` → `qa.failures[]`：

```json
{
  "layer": "M1|M2",
  "check_id": "M2-GROQ-BASIC",
  "severity": "P0|P1|P2",
  "file_id": "string|null",
  "content_sha256": "hex64|null",
  "stored_logical_path": "string|null",
  "message": "human readable <= 200 chars",
  "remediation_hint": "enum code"
}
```

| `remediation_hint` | 含義 |
|--------------------|------|
| `rerun_basic` | 重跑 BASIC 產線 |
| `rerun_enrich` | 補跑 ENRICH（§I） |
| `fix_manifest` | 僅重算 manifest |
| `reject_row` | 該列改判 rejected |
| `waive_with_approval` | 須尚書省／客戶書面豁免 |

### G.6 進入 report 的欄位（`ART-DATA-CLEAN-REPORT` / `report.json`）

| 區塊 | 鍵 | 必填 | 內容 |
|------|-----|------|------|
| `qa` | `manifest_integrity` | 是 | `{ok, checked_rows, failed_rows, failed_checks: int}` |
| `qa` | `sample_validation` | 是 | `{ok, N, sample_size, seed, failed_checks, failures: qa_failure_record[]}` |
| `qa` | `overall_ok` | 是 | `manifest_integrity.ok ∧ sample_validation.ok` |
| Summary | `qa_status` | 是 | `pass` \| `pass_with_warnings` \| `fail`（見 §G.7） |

**`qa_status` 衍生**：

| 條件 | `qa_status` |
|------|-------------|
| 無 P0／P1 | `pass`（允許 P2） |
| 無 P0，有 P1 | `pass_with_warnings` |
| 任一 P0 | `fail` |

### G.7 對 Done / Chargeable 的影響（與 W6-R1 對齊）

| 結果 | Done（W6-R1 §3.4） | Chargeable（W6-R1 §3.5 + R2 §A） |
|------|-------------------|----------------------------------|
| M1 任一 P0 失敗 | **否** | **否** |
| M2 任一 P0 失敗 | **否** | **否** |
| 僅 M2 P1 失敗 | **是**，但 `job_record.status` 必須為 `completed_with_failures` | **否**，直至修復或 `waive_with_approval` 寫入 `open_questions` |
| 僅 P2 | **是** | **是**（其餘 C1–C5 仍須滿足） |
| `qa.overall_ok=false` | **否** | **否** |

**明確**：抽樣 QA **不是**「可選加分項」；`qa` 區塊為 Done 第 2 條「通過欄位校驗」的組成部分。

### G.8 全量 schema 驗證邊界（交接用語）

| 項 | 全量 M1 | 抽樣 M2 |
|----|---------|---------|
| manifest 列鍵／計數／去重 | ✓ | — |
| envelope 檔案內容 | — | ✓ |
| `enrichment` 算法正確性 | 旗標存在性（M1） | 重算驗證（M2） |

---

## 2. Phase 8.6 鍵名對照（附錄 H · 員工 B）

> **聲明**：下表為 **SPEC-ONLY 對照**；`orchestration_bridge_v1` **現行**僅含 `intake`／`browser`／`phase6_5_pre_state`。標 **`[BRIDGE-V1]`** = 已有或可直接落入 `intake` 巢狀；標 **`[BRIDGE-EXT]`** = 未來擴展鍵（**不代表**已實作）；標 **`[P65]`** = Phase 6.5 實體欄位（非 bridge 頂層）。

### H.1 intake（請求／閘道）

| Wave 6 來源欄位 | 目標鍵（Phase 8.6） | 必填 | 備註 |
|-----------------|---------------------|------|------|
| `client_ref` | `bridge_request.intake.client_ref` | 建議 | `[BRIDGE-EXT]` 待 `intake_gate_v1` 擴充 |
| `product_sku` | `bridge_request.intake.product_sku` | accept 時是 | `[BRIDGE-EXT]` R2 §B |
| `enrichment_profile` | `bridge_request.intake.enrichment_profile` | ENRICH 時是 | `[BRIDGE-EXT]` |
| `description` | `bridge_request.intake.description` | 條件 | `[BRIDGE-V1]` |
| `tags` | `bridge_request.intake.tags` | 條件 | `[BRIDGE-V1]` |
| `explicit_task_type` | `bridge_request.intake.explicit_task_type` | 條件 | `[BRIDGE-V1]` |
| `batch_size_hint` | `bridge_request.intake.batch_size_hint` | 否 | `[BRIDGE-V1]` → `[P65]` `order.line_items[0].quantity` |
| `source_channel` | `bridge_request.intake.source_channel` | 否 | `[BRIDGE-V1]` |
| `file_extension_hints` | `bridge_request.intake.file_extension_hints` | 否 | `[BRIDGE-V1]` |
| `inbound_path_hint` | `bridge_request.intake.inbound_path_hint` | 否 | `[BRIDGE-V1]` |
| `work_category`（回傳） | `bridge_result.intake.work_category` | 是 | `[BRIDGE-V1]` 期望 `data_cleaning` |
| `decision` | `bridge_result.intake.decision` | 是 | `[BRIDGE-V1]` |
| `suggested_pipeline` | `bridge_result.intake.suggested_pipeline` | accept 時是 | `[BRIDGE-V1]` 恒 `code_cleaning_pipeline_v2` |
| `suggested_product_sku` | `bridge_result.intake.suggested_product_sku` | accept 時是 | `[BRIDGE-EXT]` |
| `product_sku` → order | `bridge_result.phase6_5_pre_state.order.field_mapping` | accept 時是 | `[BRIDGE-V1]` 語意對照 R2 §B.6 |
| `phase6_5_pre_state` | `bridge_result.phase6_5_pre_state` | 是 | `[BRIDGE-V1]` 頂層重複 |

### H.2 manifest（交付索引）

| Wave 6 來源欄位 | 目標鍵（Phase 8.6） | 必填 | 備註 |
|-----------------|---------------------|------|------|
| `manifest.json`（整包） | `bridge_result.wave6.manifest.logical_ref` | Done 時是 | `[BRIDGE-EXT]` 不透明 ref，**非**內嵌全文 |
| `job_id` | `bridge_result.wave6.manifest.job_id` | 是 | `[BRIDGE-EXT]` |
| `sku` | `bridge_result.wave6.manifest.product_sku` | 是 | `[BRIDGE-EXT]` = `job_record.sku` |
| `accepted_units` | `bridge_result.wave6.manifest.accepted_units` | 是 | `[BRIDGE-EXT]` |
| `billing_units.U` | `bridge_result.wave6.manifest.billable_u` | 開票前是 | `[BRIDGE-EXT]` 對照 R2 §A.2；**#H-1 裁定：不納入** sha 列表（R4 §2） |
| `billing_units.L` | `bridge_result.wave6.manifest.billable_l` | ENRICH | `[BRIDGE-EXT]` |

### H.3 report（人讀＋機讀）

| Wave 6 來源欄位 | 目標鍵（Phase 8.6） | 必填 | 備註 |
|-----------------|---------------------|------|------|
| `ART-DATA-CLEAN-REPORT` | `bridge_result.wave6.report.artifact_ref` | Done 時是 | `[BRIDGE-EXT]` |
| `report.json` | `bridge_result.wave6.report.json_ref` | Done 時是 | `[BRIDGE-EXT]` |
| `report.summary.job_id` | `bridge_result.wave6.report.job_id` | 是 | `[BRIDGE-EXT]` |
| `report.qa.overall_ok` | `bridge_result.wave6.report.qa_ok` | 是 | `[BRIDGE-EXT]` |
| `report.qa.sample_validation.sample_size` | `bridge_result.wave6.report.qa_sample_size` | 是 | `[BRIDGE-EXT]` |
| `customer_ack` | `bridge_result.wave6.report.customer_ack` | Chargeable 前是 | `[BRIDGE-EXT]` |
| `billing_dispute_flag` | `bridge_result.wave6.report.billing_dispute_flag` | 是 | `[BRIDGE-EXT]` 預設 `false` |

### H.4 delivery（Phase 6.5 對齊）

| Wave 6 來源欄位 | 目標鍵 | 必填 | 備註 |
|-----------------|--------|------|------|
| 交付包整體 | `[P65] delivery.artifact_refs[]` | submitted 時是 | 含 report／manifest refs |
| `manifest.json` ref | `[P65] delivery.artifact_refs[]` | 是 | `w6://delivery/{job_id}/manifest`（R4 §3） |
| `report.json` ref | `[P65] delivery.artifact_refs[]` | 是 | `w6://delivery/{job_id}/report_json` |
| `ART-DATA-CLEAN-REPORT` ref | `[P65] delivery.artifact_refs[]` | 是 | `w6://delivery/{job_id}/report_md` |
| `deliverables/` ref | `[P65] delivery.artifact_refs[]` | 是 | `w6://delivery/{job_id}/deliverables` |
| `customer_ack` 時間 | `[P65] delivery.accepted_at` | accepted 時是 | ISO-8601 |
| `delivery.status` | `[P65] delivery.status` | — | `submitted` → `accepted`／`rejected` |
| `job_id` | `[P65] delivery.job_id` | 是 | FK → `job` |
| bridge 摘要 | `bridge_result.wave6.delivery.status` | 否 | `[BRIDGE-EXT]` 鏡像 `[P65]`，方便觀測 |

**命名空間裁決（本輪）**：Wave 6 專用欄位統一掛 **`bridge_result.wave6.*`**；不修改 `orchestration_bridge_v1` 既有 required 陣列（實作時以 `additionalProperties` 或 sidecar 檔落地，**留待實作工單**）。

### H.5 對照狀態圖例

| 標記 | 含義 |
|------|------|
| `[BRIDGE-V1]` | 與現行 Phase 8.6 文件一致，可映射到現有 `intake` 巢狀 |
| `[BRIDGE-EXT]` | 僅 R3 登記；**未實作** |
| `[P65]` | Phase 6.5 實體；由商業層寫入，非 bridge 必須輸出 |

---

## 3. BASIC → ENRICH 補跑 delta（附錄 I · 員工 C）

### I.1 作業代碼

| 代碼 | 含義 |
|------|------|
| `JOB-B` | 已完成之 `CLEAN-BASIC` 合同 job（`job_id_B`） |
| `JOB-E` | 補跑 ENRICH 之**新** job（`job_id_E`） |
| `upgrade_mode` | 恒 `basic_to_enrich_delta`（**非**新 SKU） |

**允許**：同一 `client_ref`、同一批 `content_sha256` 集合，在 **JOB-B Done 之後** 開 JOB-E。  
**禁止**：在同一 `job_id` 內把 SKU 從 BASIC 改標 ENRICH（違反 R2 §A SKU 真相）。

### I.2 欄位重用／重算

| 區塊 | 重用（COPY） | 必須重算（RECOMPUTE） |
|------|-------------|------------------------|
| v2.0 基底 | `content_sha256`、`name`、`extension`、`original_type`、`size_bytes`、`encoding`、`content_summary`（若來源檔未變） | — |
| 清洗狀態 | `clean_status=ok` 之列可沿用 | 若觸發 LLM 重解析則 `parse_strategy`、`warnings` |
| `groq_used`／`groq_reason` | 僅當 `llm_assist=off` 可沿用 false | `on_failures_only` 失敗觸發時 **RECOMPUTE** |
| `enrichment` | **禁止 COPY** | 整塊依 R2 §C **RECOMPUTE** |
| `quality_score` 等 | — | 依 §C.4 **RECOMPUTE** |
| manifest 列 | `file_id` 可新；`content_sha256` **不變** | `has_enrichment`、`billable_*` 旗標 |
| `enrichment_batch_summary.json` | — | 全檔 **RECOMPUTE** |
| report `Stats` | `by_extension` 可引用 JOB-B | `groq_used_count`、`enrichment_coverage_pct` **RECOMPUTE** |

**源檔變更**：若 `content_sha256` 與 JOB-B 不同 → 視為**新 unit**，非補跑（走全新 intake）。

### I.3 intake 補跑前要件

| # | 條件 |
|---|------|
| 1 | 新 intake：`product_sku=CLEAN-ENRICH` + `enrichment_profile` 合法（R2 §B） |
| 2 | 請求帶 `upgrade_from_job_id=job_id_B`（**[BRIDGE-EXT]** 鍵，見 §H.1） |
| 3 | `tags` 含 `upgrade:basic_to_enrich` |
| 4 | JOB-B 已 Done 且 `qa.overall_ok=true` |
| 5 | 客戶合同或 `open_questions` 載明「補跑 ENRICH 計費條款」（§I.5） |

### I.4 manifest／report 對齊

| 檔案 | JOB-B | JOB-E |
|------|-------|-------|
| `manifest.json` | 保留歸檔，**不修改** | 新檔；列集為 JOB-B ok 列之子集或相等 |
| `report.json` | 保留 | 新檔；`summary.sku=CLEAN-ENRICH` |
| `report.upgrade` | — | 必填：`{from_job_id, from_sku, shared_sha256_count, mode}` |
| `job_record.parent_job_id` | null | `job_id_B` |
| `qa` | 原結果 | **重跑** M1+M2（§G）；可縮 M2 抽樣但 **不得** 低於 §G.2 公式 |

**對齊驗收**：JOB-E manifest 中每個 `content_sha256` 必須 ∈ JOB-B manifest ok 集合；否則 P0 `upgrade_sha_mismatch`。

### I.5 防重複開票

| 規則 ID | 內容 |
|---------|------|
| **R-UPG-1** | JOB-B 已開票之 `content_sha256`，在 JOB-E 發票中 **不得** 再計 `CLEAN-BASIC` 行項 |
| **R-UPG-2** | JOB-E 僅計 **`CLEAN-ENRICH` 行項**（U）與 **`CLEAN-ENRICH-LLM`（L）**（R2 §A.4） |
| **R-UPG-3** | JOB-E 的 `U` = JOB-E manifest ok 列數；**不要求** 再次滿足 BASIC 的 `Q_min=100`（ENRICH `Q_min=50` 仍適用） |
| **R-UPG-4** | `invoice` 須附 `upgrade_credit_refs: [{job_id, sku, credited_sha256_count}]` |
| **R-UPG-5** | JOB-B 已開票 ⇒ JOB-E **僅** ENRICH 行項（R-UPG-1／2）。JOB-B 未開票 ⇒ 允許 JOB-E **單張合併票** `consolidation_mode=basic_unbilled_merge`（R4 §4）；或 `job_b_invoice_waived` 豁免則僅 ENRICH |

**計費語意（預設）**：補跑為 **「ENRICH 升級費」**，不是第二遍 BASIC；內部帳用 `upgrade_mode` 區分。

### I.6 不引入新產品包

補跑 **不** 創建 `CLEAN-UPGRADE` SKU；對外仍為 `CLEAN-ENRICH`，以 `upgrade_from_job_id` 與 report 區塊區分。

### I.7 與 R2 frozen schema 關係

- **不修改** `enrichment_v0.1` 欄位定義；補跑僅**新增實例**。  
- **不修改** R-GROQ-* 規則；JOB-E 允許 `groq_used=true` 計 L。  
- JOB-B 歷史交付 **不回寫** enrichment（R2 §D.4 策略 A 仍有效）。

---

## 4. 財務填表對齊（附錄 J · 員工 D）

### J.1 原則（產品規格 vs 財務填值）

| 類別 | 誰定義 | 誰填值 | 範例 |
|------|--------|--------|------|
| **結構鍵** | 產品規格（R2 §A.4.2 + 本附錄） | 工程／規格檔 | `billing_table_version` |
| **金額鍵** | 產品規格定義**存在** | **財務**填數字 | `list.basic_per_u` |
| **治理鍵** | 產品＋尚書省 | 財務或運營 | `effective_from`、`approved_by` |
| **運行時** | 交付／manifest | 系統計算 | `billable_u`、`billable_l` |

### J.2 `billing_table` 完整結構（v0.1 · 對齊 R2 不增刪 A.4.2 核心鍵）

```json
{
  "billing_table_version": "w6_billing_v0.1",
  "currency_default": "USD",
  "effective_from": null,
  "effective_to": null,
  "approved_by": null,
  "approved_at": null,
  "floor": {
    "basic_per_u": null,
    "enrich_per_u": null,
    "enrich_per_l": null
  },
  "list": {
    "basic_per_u": null,
    "enrich_per_u": null,
    "enrich_per_l": null
  },
  "line_item_labels": {
    "CLEAN-BASIC": null,
    "CLEAN-ENRICH": null,
    "CLEAN-ENRICH-LLM": null
  },
  "minimum_job_fee": {
    "amount": null,
    "currency": null,
    "contract_required": true
  },
  "upgrade_policy": {
    "allow_basic_to_enrich_invoice": true,
    "double_basic_enrich_line_for_same_sha": false
  },
  "invoice_rules": {
    "auto_issue_enabled": false,
    "require_billing_table_complete": true
  }
}
```

### J.3 欄位分類表

| 欄位路徑 | 產品規格 | 財務填 | 允許 null | 自動開票 |
|----------|----------|--------|-----------|----------|
| `billing_table_version` | ✓ 固定 | — | 否 | — |
| `currency_default` | ✓ | 可覆 | 否 | — |
| `effective_from`／`to` | ✓ 鍵存在 | ✓ 日期 | 是（未核定前） | null ⇒ **禁止** |
| `approved_by`／`at` | ✓ | ✓ | 是 | null ⇒ **禁止** |
| `floor.*` | ✓ | ✓ 金額 | 是 | null ⇒ **禁止** |
| `list.*` | ✓ | ✓ 金額 | 是 | null ⇒ **禁止** |
| `line_item_labels.*` | ✓ | ✓ 顯示名 | 是 | 僅影響 PDF |
| `minimum_job_fee.amount` | ✓ | ✓ | 是 | 未啟用合同則忽略 |
| `upgrade_policy.*` | ✓ 預設 | 尚書省可改 | 否 | — |
| `invoice_rules.auto_issue_enabled` | ✓ 預設 **false** | — | 否 | true 仍須 `require_billing_table_complete` |
| `billable_u`／`l`（運行時） | ✓ 公式 | 系統算 | 否 | 依 R2 §A.4.3 |

**自動開票禁止條件（任一即停）**：

1. `list.basic_per_u`／`enrich_per_u`／`enrich_per_l` 任一為 null（ENRICH 無 L 時 `enrich_per_l` 可為 0.00，**非** null）；  
2. `approved_by` 為 null；  
3. `invoice_rules.auto_issue_enabled=false`（預設）；  
4. `report.qa.overall_ok=false`；  
5. `billing_dispute_flag=true`。

### J.4 `list.*` 與 R2 行項對應

| R2 `line_item.sku` | `billing_table.list` 鍵 | `unit_price` 取用 |
|--------------------|-------------------------|-------------------|
| `CLEAN-BASIC` | `basic_per_u` | 單價 = `list.basic_per_u` |
| `CLEAN-ENRICH` | `enrich_per_u` | 單價 = `list.enrich_per_u` |
| `CLEAN-ENRICH-LLM` | `enrich_per_l` | 數量 = `L`；單價 = `list.enrich_per_l` |

**公式**（與 R2 §A.4.3 不變）：  
`amount_total = Σ(line_quantity × list.<key>) + minimum_fee_adjustment`。

### J.5 財務填表步驟（交接清單）

1. 編輯權威檔 `04_Workflows/wave6/billing_table_w6_v0.1.json`（邏輯名 `wave6_billing_table`，R4 §5）。  
2. 填 `list.*` 與 `floor.*`（`floor ≤ list`）。  
3. 填 `effective_from`、`approved_by`、`approved_at`。  
4. 設 `invoice_rules.auto_issue_enabled`（建議維持 false 直至 W6-IMPL-BILLING）。  
5. 運營驗證：選一筆試算 job，`manifest.billable_u` × `list.enrich_per_u` 與手算誤差 ≤0.01。

**本輪不填實際金額**。

---

## 5. 檢查員：問題與修正結果（CHK-R3）

| ID | 嚴重度 | 問題 | 修正 |
|----|--------|------|------|
| CHK-R3-01 | P0 | A 草案曾將 M2 失敗仍標 Done | §G.7 明確 P0⇒否 |
| CHK-R3-02 | P0 | C 草案可能在同一 job 改 SKU | §I.1 禁止；JOB-E 新 job |
| CHK-R3-03 | P1 | B 將 manifest 內嵌 bridge 全文 | 改 `logical_ref` `[BRIDGE-EXT]` |
| CHK-R3-04 | P1 | C 與 R2 `Q_min` 衝突 | §I.5 R-UPG-3 僅 ENRICH Q_min |
| CHK-R3-05 | P1 | J 改動 R2 `billing_table` 根鍵 | §J.2 **僅增** 治理鍵，R2 四鍵不變 |
| CHK-R3-06 | P2 | `qa_status` 與 `job_record.status` 混淆 | report 用 `qa_status`；job 用 `completed_with_failures` |
| CHK-R3-07 | — | 四份初稿無未解 P0 衝突 | **PASS-WITH-TBD** |

### 5.1 標記衝突（未吞）

| 衝突 | 說明 | 處置 |
|------|------|------|
| **CONF-R3-01** | `#H-1` | **結案** → R4 §2 採 B（不帶 sha 列表） |
| **CONF-R3-02** | `#I-1` | **結案** → R4 §4 分情形合併／分票 |

---

## 6. 下一輪還需要補什麼

| 優先 | 內容 | 建議 |
|------|------|------|
| — | ~~#H-1 #H-2 #I-1 #J-1~~ | **R4 已裁定**（`WAVE6_DATA_CLEANING_R4_RATIFICATIONS_v0.1.md`） |
| P0 | 財務填妥 `list.*`／`approved_by` | 營運／財務；非 spec |
| P1 | `W6-IMPL-QA`：M1/M2 檢查器 | 實作波 |
| P1 | `intake_gate_v1` + `[BRIDGE-EXT]` 鍵落地 | 依 R2 §B.8 |
| P2 | Wave 6 總覽 README 合併 R1+R2+R3 索引頁 | 文檔工單 |
| — | orchestrator 節點圖 | **不在 Wave 6 範圍** |

---

## 7. 待確認項

**無**（#H-1／#H-2／#I-1／#J-1 已由 R4 裁定，見 `WAVE6_DATA_CLEANING_R4_RATIFICATIONS_v0.1.md`）。

---

## 8. Roadmap 條目（可貼 `master_status`）

```text
Wave 6 – DATA-CLEANING [spec-complete · R1–R4]
- R3：QA / 8.6 對照 / 補跑 delta / billing 結構
- R4：#H-1 B · #H-2 w6:// · #I-1 分情形合併票 · #J-1 04_Workflows/wave6/
- 未含：runner · orchestrator · 財務 list 填值 · Master_Map 登錄（→ W6-R5）
```

---

*Wave 6 R3 · spec only · `04_Workflows/WAVE6_DATA_CLEANING_R3_APPENDICES_v0.1.md`*
