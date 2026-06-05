# Wave 6 – DATA-CLEANING · R2 附錄（v0.1 · spec only）

> **輪次**：W6-R2 · **範圍**：計費附錄、intake SKU 校驗表、ENRICH schema 凍結、`groq_used` 歷史衝突裁決  
> **不做**：orchestrator、runner、程式、JSON Schema 檔落盤（僅本檔契約文字）  
> **承接**：W6-R1 產品矩陣／交付物／Done·Chargeable 分界  
> **權威對齊**：`code_cleaning_pipeline_v2` · `PHASE7_5_INTAKE_GATE_MVP_PLAN_v0.1.md` · `intake_gate_v1` · `phase6_5_entities_v1` · `DATA_CONTRACT_AND_EVENT_MODEL_v0.1.md`

---

## 0. R2 出口狀態

| 附錄 | 狀態 | 尚書省待裁（若有） |
|------|------|-------------------|
| A 計費附錄 | **FROZEN-v0.1** | 牌價數字（§A.4 為結構，非採購承諾） |
| B intake SKU 校驗表 | **FROZEN-v0.1** | 實作波次才改 `intake_gate_v1` |
| C ENRICH schema | **FROZEN-v0.1** | `quality_score` 權重調整須新工單 |
| D `groq_used` 裁決 | **RATIFIED-v0.1** | 無 |

**R1 待確認項 closure（本輪可結）**

| R1 # | 裁定（R2） |
|------|------------|
| 3 `min_billable_units` | §A.3 |
| 4 部分失敗最低處理費 | §A.5 |
| 5 沉默 `customer_ack` | §A.6 |
| 6 `quality_score` 算法 | §C.4 |
| 7 歷史 `groq_used` vs BASIC | §D |
| 1 單檔上限 | §B.3（intake 拒絕規則） |
| 2 抽樣率 | **留 W6-R3**（QA 工單，非 R2 範圍） |

---

## 附錄 A — 計費附錄（Billing Appendix）

### A.1 計費原則

1. **計費真相來源** = 交付包 `manifest.json`（`clean_status=ok` 列）+ `job_record.sku`；**禁止**以 intake `batch_size_hint` 單獨計費。  
2. **SKU 真相** = intake `product_sku`（見附錄 B）；與 `order.line_items[].sku` 一致方可開票。  
3. **完成與可收費** 仍依 W6-R1 §3.4／§3.5；本附錄只定義 **可開票數量與行項**。  
4. 牌價為 **內部結算表 v0.1**；對外報價單可覆寫 `unit_price`，但不得低於 §A.4 **floor**  без 尚書省備註。

### A.2 計費單位定義

| 計費鍵 | 符號 | 定義 | 適用 SKU |
|--------|------|------|----------|
| 成功單位 | `U` | manifest 中一列：`clean_status=ok` 且通過 SKU 交付規則（§D）且 `schema_version=2.0` | BASIC、ENRICH |
| LLM 觸發次數 | `L` | 同上列且 `groq_used=true` 且 `groq_reason` 非空 | **僅 ENRICH** |
| 批次最低量 | `Q_min` | 合同層：未達則不開票或改收最低費（§A.5） | 兩 SKU |

**去重**：同一 `content_sha256` 在同一 `job_id` 內只計 **1×U**；重複列不計費。

### A.3 `min_billable_units`（R1 #3 裁定）

| SKU | `Q_min`（成功單位 U） | 說明 |
|-----|----------------------|------|
| `CLEAN-BASIC` | **100** | 低於 100 且無 §A.5 最低費合同 → **不可開票**（可 Done 交付） |
| `CLEAN-ENRICH` | **50** | 語意增強單價較高；低於 50 同 BASIC 規則 |

**驗收**：`invoice` 草稿生成時 `sum(U) >= Q_min` 或 `minimum_fee_applied=true`。

### A.4 行項結構（Phase 6.5 `order.line_items` → `invoice`）

#### A.4.1 標準行項（可開票）

| line_item.sku | 數量來源 | unit_price 來源 | 備註 |
|---------------|----------|-----------------|------|
| `CLEAN-BASIC` | `U` | 結算表 `price.basic_per_u` | 單一主行項 |
| `CLEAN-ENRICH` | `U` | 結算表 `price.enrich_per_u` | 主行項 |
| `CLEAN-ENRICH-LLM` | `L` | 結算表 `price.enrich_per_l` | **分項**；`L=0` 時省略該行 |

#### A.4.2 結算表欄位（v0.1 結構 · 數字由財務填）

```json
{
  "billing_table_version": "w6_billing_v0.1",
  "currency_default": "USD",
  "floor": { "basic_per_u": null, "enrich_per_u": null, "enrich_per_l": null },
  "list": { "basic_per_u": null, "enrich_per_u": null, "enrich_per_l": null }
}
```

**規則**：`list.*` 為報價參考；`floor.*` 為折扣下限；null 表示尚未由尚書省／財務核定 — **不得**對外自動開票。

#### A.4.3 發票金額（可驗收公式）

- `amount_basic = U × unit_price(CLEAN-BASIC)`  
- `amount_enrich = U × unit_price(CLEAN-ENRICH) + L × unit_price(CLEAN-ENRICH-LLM)`  
- `amount_total = amount_* + minimum_fee_adjustment`（§A.5）  
- 與 `invoice.amount` 誤差 **≤ 0.01**（同幣別）

### A.5 部分失敗與最低處理費（R1 #4 裁定）

| 合同類型 | 代碼 | 計費行為 | 預設 |
|----------|------|----------|------|
| 按成功計費 | `per_success_unit` | 僅對 `U` 計價；`rejected_units` 不計 | **預設** |
| 最低處理費 | `minimum_job_fee` | 若 `U < Q_min` 且 job `status=completed_with_failures`，可收 `minimum_fee` 一次，**不** 按 U 補足 | 須合同勾選 |

**`minimum_job_fee` 觸發條件（全部）**：

1. 合同 `billing_mode=minimum_job_fee`；  
2. `job_record.status=completed_with_failures`；  
3. `U > 0` 且 `U < Q_min`；  
4. `customer_ack` 已成立（W6-R1 §3.6）；  
5. 發票附 `minimum_fee_applied=true` 與 `open_questions` 記錄原因。

**禁止**：`U=0` 仍收 `minimum_job_fee`（改判 `failed`，不可 Chargeable）。

### A.6 客戶確認與開票時序（R1 #5 裁定）

| 規則 | 設定 |
|------|------|
| 沉默確認 | **預設關閉**（`customer_ack_implied=false`） |
| 開票前置 | `delivery.status=accepted` **且** `customer_ack` 非空 |
| 發票事件 | `invoice.issued` 不得早於 `delivery.accepted` 時間戳 |
| 付款事件 | `payment.captured` 僅在 `invoice.issued` 之後 |

**MVP 證據鍵**：`delivery.artifact_refs[]` 須含四類 `w6://delivery/{job_id}/{kind}`（`manifest`／`report_json`／`report_md`／`deliverables`；見 R4 §3）。

### A.7 Chargeable → Invoice 勾選表

| W6-R1 條件 | 計費附錄欄位／規則 |
|------------|-------------------|
| C1 計費單位下限 | §A.3 `U >= Q_min` 或 §A.5 |
| C2 客戶確認 | §A.6 |
| C3 無爭議 | `billing_dispute_flag=false` |
| C4 SKU 一致 | `job_record.sku == order.line_items[0].sku` |
| C5 ENRICH 覆蓋率 | `enrichment_coverage_pct >= 95`（見附錄 C.5） |

### A.8 與 Observability 成本線關係

- Wave 2 成本欄位 **partial** → **不得**作為 Wave 6 對客開票依據。  
- 內部毛利核算可用 `task_runs`／Langfuse **僅內部**；對外只認 §A.4 公式。

---

## 附錄 B — intake SKU 校驗表

### B.1 問題修正（相對 Phase 7.5 v0.1）

| 現行映射（錯誤） | R2 裁定映射 |
|------------------|-------------|
| `suggested_pipeline` → `order.line_items[0].sku` | `product_sku` → `order.line_items[0].sku` |
| （遺失） | `suggested_pipeline` → `requirement_profile.constraints.tags` 加標 `pipeline:code_cleaning_pipeline_v2` |
| `batch_size_hint` → `quantity` | **不變** |

**說明**：產線名 ≠ 商品 SKU；accept 時兩者皆須可稽核。

### B.2 請求擴展（`IntakeGateRequest` · R2 增補欄位）

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `product_sku` | string | **accept 時必填** | 枚舉：`CLEAN-BASIC` \| `CLEAN-ENRICH` |
| `enrichment_profile` | object | ENRICH 時必填 | 見 B.4；BASIC 必須為 null 或省略 |
| `client_ref` | string | 建議必填 | 對齊 `ART-DATA-CLEAN-REPORT`；≤128 字 |

其餘欄位同 Phase 7.5 v0.1。

### B.3 Gate 校驗表（`data_cleaning` 專用）

| check_id | 通過條件 | 失敗 → decision | detail 模板 |
|----------|----------|-----------------|-------------|
| `SKU-PRESENT` | `product_sku` 非空 | **defer** | `missing_product_sku` |
| `SKU-ENUM` | `product_sku` ∈ {`CLEAN-BASIC`,`CLEAN-ENRICH`} | **reject** | `invalid_product_sku:{value}` |
| `PIPELINE-ANCHOR` | 清洗信號成立（沿用 v0.1 accept 規則） | reject／defer | 同 v0.1 |
| `ENRICH-PROFILE` | ENRICH ⇒ `enrichment_profile` 合法（B.4） | **defer** | `invalid_enrichment_profile` |
| `BASIC-NO-ENRICH` | BASIC ⇒ 無 `enrichment_profile` 或 `llm_assist` 缺失 | **defer** | `basic_must_not_carry_enrichment_profile` |
| `BATCH-HINT-POSITIVE` | 若提供 `batch_size_hint` 則 ≥1 | **defer** | `invalid_batch_size_hint` |
| `SIZE-POLICY-DECL` | 客戶在 `tags` 或 description 聲明知悉單檔上限 **2_097_152** bytes（2MiB） | **defer**（未聲明且無 enterprise 標籤） | `size_policy_not_acknowledged` |
| `ABS-PATH-BAN` | 同 v0.1 | reject | 同 v0.1 |

**accept 必要集合**：`SKU-PRESENT` + `SKU-ENUM` + `PIPELINE-ANCHOR` + (`ENRICH-PROFILE` 或 `BASIC-NO-ENRICH`) + `ABS-PATH-BAN`。

### B.4 `enrichment_profile`（intake 最小形狀）

| 鍵 | 類型 | 必填 | 規則 |
|----|------|------|------|
| `language_hint` | string | 否 | ISO 639-1 或 `auto` |
| `domain_tags` | string[] | 否 | ≤8 項，每項 ≤32 字 |
| `risk_scan_level` | enum | 是 | `none` \| `metadata_only` |
| `llm_assist` | enum | 是 | **僅允許** `off` \| `on_failures_only` |

### B.5 標籤別名（可選，輔助 SKU-PRESENT）

| tag 模式 | 映射 |
|----------|------|
| `sku:clean-basic` | `CLEAN-BASIC` |
| `sku:clean-enrich` | `CLEAN-ENRICH` |
| `sku:CLEAN-BASIC` | `CLEAN-BASIC` |

**規則**：`product_sku` 與 tag 別名 **衝突** → **defer**（`sku_tag_conflict`）。

### B.6 Accept 回傳增補（`IntakeGateResult`）

| 欄位 | 值 |
|------|-----|
| `suggested_pipeline` | 恒 `code_cleaning_pipeline_v2` |
| `suggested_product_sku` | = 請求 `product_sku` |
| `work_category` | `data_cleaning` |
| `phase6_5_pre_state.order.field_mapping` | `intake.product_sku` → `order.line_items[0].sku`；`intake.batch_size_hint` → `order.line_items[0].quantity` |

### B.7 defer／reject 速查

| 情境 | decision |
|------|----------|
| 有清洗信號、無 `product_sku` | **defer** |
| 有 `product_sku`、無清洗信號 | **reject**（`sku_without_cleaning_intent`） |
| `product_sku=CLEAN-ENRICH` 但 `llm_assist=off` 且無 domain_tags | **defer**（`enrich_requires_llm_or_domain`） |
| 僅 RAG／ingest 語意 | **reject**（沿用 v0.1） |

### B.8 實作波次聲明（非 R2）

- 更新 `intake_gate_v1.json` 增欄位與 `gate_checks` 枚舉 → **W6-IMPL-INTAKE** 工單。  
- **本 R2 不修改** `intake_decider.py`。

---

## 附錄 C — ENRICH schema 凍結（`envelope_v2.0+enrichment_v0.1`）

### C.1 版本策略

| 層級 | 值 | 說明 |
|------|-----|------|
| 基底信封 | `schema_version: "2.0"` | 與現行 `cleaned_full` 相容 |
| 增強區塊 | `enrichment.schema_version: "enrichment_v0.1"` | 僅 **CLEAN-ENRICH** 交付包允許出現 |
| 凍結日 | R2 落盤日 | 變更須 `enrichment_v0.2` 新工單 |

### C.2 頂層規則

| SKU | `enrichment` 鍵 |
|-----|-----------------|
| `CLEAN-BASIC` | **禁止存在**（manifest 含則 **拒收** 該列計入 U） |
| `CLEAN-ENRICH` | **必填**（每個 `clean_status=ok` 列） |

**基底欄位**：C.1 不改名、不刪除 v2.0 既有鍵（`content_summary`、`groq_used` 等保留）。

### C.3 `enrichment` 物件 — 凍結欄位表

| 欄位 | 類型 | 必填 | 約束 |
|------|------|------|------|
| `schema_version` | string | 是 | const `enrichment_v0.1` |
| `detected_language` | string | 是 | ISO 639-1 或 `unknown` |
| `domain_tags` | string[] | 是 | 0–8 項；可空陣列 |
| `content_kind` | enum | 是 | `code` \| `doc` \| `config` \| `binary_like` \| `unknown` |
| `quality_score` | integer | 是 | 0–100 含端點 |
| `review_priority` | enum | 是 | `low` \| `medium` \| `high` |
| `enrichment_provenance` | enum | 是 | `rules` \| `llm` \| `mixed` |
| `signals` | object | 是 | 見 C.3.1；`additionalProperties: false` |

#### C.3.1 `signals`（固定鍵）

| 鍵 | 類型 | 說明 |
|----|------|------|
| `has_parse_warnings` | bool | `warnings.length > 0` |
| `used_llm` | bool | = 頂層 `groq_used` |
| `line_count` | int | = `content_summary.line_count` |
| `import_count` | int | = `len(content_summary.imports)` |

### C.4 `quality_score` 算法（R1 #6 · 確定性 · v0.1）

**輸入**：僅讀 v2.0 既有欄位 + `enrichment_profile`（intake 快照寫入 job 元資料）。

**初值** `S = 100`，依序扣分（下限 0）：

| 條件 | 扣分 |
|------|------|
| `clean_status != ok` | 該列不產生 enrichment（整列失敗） |
| `warnings.length > 0` | −10 |
| `parse_strategy` 為 null 且 `original_type` 含 `python` | −5 |
| `content_summary.line_count == 0` | −40 |
| `content_summary.char_count < 50` | −15 |
| `groq_used=true` 且 `groq_reason` 含 `failure` 子串（大小寫不敏感） | −20 |
| `extension` ∈ {`.bin`,`.exe`,`.dll`,`.so`} | −30 並強制 `content_kind=binary_like` |

**加分（上限 100）**：無。

**輸出**：`quality_score = max(0, min(100, S))`（整數）。

**`review_priority` 衍生**：

| 條件 | priority |
|------|----------|
| `quality_score < 50` | `high` |
| `50 ≤ quality_score < 80` | `medium` |
| `quality_score ≥ 80` | `low` |
| `risk_scan_level=metadata_only` 且 `warnings` 含 `secret` 子串 | 至少 `high` |

**`enrichment_provenance`**：`groq_used=true` → `llm` 或 `mixed`（若同時有規則衍生標籤）；否則 `rules`。

### C.5 批次附錄 `enrichment_batch_summary.json`（凍結）

| 欄位 | 類型 | 必填 |
|------|------|------|
| `schema_version` | const `enrichment_batch_v0.1` | 是 |
| `job_id` | string | 是 |
| `accepted_units` | int | 是 |
| `enrichment_coverage_pct` | int | 是 | = round(100 × 含有效 enrichment 的 ok 列 / accepted_units) |
| `language_distribution` | object | 是 | 鍵=`detected_language`，值=count |
| `top_failure_reasons` | array | 是 | ≤5 項 `{code,count}` |
| `duplicate_clusters` | array | 是 | `{sha256,count}`；count>1 的簇 |

**Chargeable C5**：`enrichment_coverage_pct >= 95`，否則須書面豁免寫入 `open_questions`。

### C.6 BASIC 交付 schema 驗收（抽樣規則引用）

- 單列：**不得**含 `enrichment`。  
- `groq_used` 必須 `false`（見附錄 D）。  
- 全量 manifest 校驗由 W6-R3 QA 附錄定義抽樣率。

---

## 附錄 D — 歷史 `groq_used` 衝突裁決（CONF-01 · RATIFIED）

### D.1 事實基線（2026-06-04 盤點 · 制度層）

| 庫區 | `groq_used=true` | 說明 |
|------|------------------|------|
| `cleaned_full` 現網成品 | **0 筆**（抽樣 grep） | 歷史成品可視為 BASIC 相容 |
| `06_Exports_Output/reports/asset_value_eval_*.json` | **少量** | 評估報告，**非** Wave 6 交付 manifest |
| 未來 runner | 可能 >0 | 依 ENRICH `llm_assist` |

**裁決焦點**：制度上防止「標 BASIC 卻含 LLM 痕跡」計費爭議，而非回溯清洗三萬餘件。

### D.2 三車道模型

| 車道 | 代碼 | 定義 | 可對外 SKU 計費 |
|------|------|------|-----------------|
| 客戶合同車道 | `contracted` | 有 `client_ref` + intake `product_sku` + Wave 6 交付包 | **是** |
| 內部運維車道 | `internal_ops` | `chariot.factory`／哨兵／wave runner 無 `product_sku` | **否** |
| 歷史未分類 | `legacy_unclassified` | R6 前已存在之 `cleaned_full` 無 job SKU 標記 | **否**（除非走 D.4 重分類工單） |

### D.3 列級規則（manifest 計費真相）

| 規則 ID | 條件 | 裁定 |
|---------|------|------|
| **R-GROQ-1** | `product_sku=CLEAN-BASIC` 且 `groq_used=true` | 該列 **不得計入 U**；計入 `rejected_units` 原因碼 `basic_groq_violation` |
| **R-GROQ-2** | `product_sku=CLEAN-ENRICH` 且 `groq_used=true` | 允許計入 U；另計 **L**（§A.2） |
| **R-GROQ-3** | `product_sku=CLEAN-BASIC` 且 `groq_used=false` | 正常計入 U |
| **R-GROQ-4** | `product_sku=CLEAN-ENRICH` 且缺 `enrichment` 區塊 | 不計 U；`enrich_schema_missing` |
| **R-GROQ-5** | `legacy_unclassified` 任一列 | 不計 U；僅供內部資產統計 |

### D.4 歷史成品重貼 SKU（R1 #7）

| 策略 | 允許 | 條件 |
|------|------|------|
| **A 原樣保留** | 是（預設） | 留在 `legacy_unclassified`；不進客戶 manifest |
| **B 重分類交付** | 是 | 新開 `job_id`；重跑 **僅 ENRICH 增強** 或 **僅 manifest 重算**（不改 content_sha256）；須新 intake `product_sku` + 客戶 `client_ref` |
| **C 把舊檔直接標 BASIC 開票** | **禁止** | 無 intake SKU 與交付包 → 違反 §A.1 |

**禁止**：為「變可收費」而批量修改 `cleaned_full` 內 `groq_used` 或事後插入假 `enrichment`。

### D.5 與產線 `code_cleaning_pipeline_v2` 的關係

- 產線 **仍可** 在內部運維寫入 `groq_used` 欄位；Wave 6 **SKU 交付** 以 D.3 過濾。  
- 內部 wave 實驗若觸發 Groq，**不得** 使用客戶 `client_ref` 同一 `job_id` 混合開票。

### D.6 爭議處理

- 客戶聲稱「應按 BASIC 單價」但 manifest 出現 `basic_groq_violation` → **以 manifest 為準**；補救為重跑 BASIC（`llm_assist` 關閉）或改合同 ENRICH。  
- 內部評估報告 `groq_used=true` **不構成** 客戶交付證據。

---

## 附錄 E — R2 一致性複審（檢查員）

| ID | 結果 |
|----|------|
| E-01 | 計費 U/L 與 SKU 校驗、D.3 對齊 — **PASS** |
| E-02 | Phase 7.5 sku 映射錯誤已在 B.1 修正 — **PASS** |
| E-03 | ENRICH `quality_score` 可重算、可驗收 — **PASS** |
| E-04 | 未引入 orchestrator／runner — **PASS** |

---

## 附錄 F — 留待 W6-R3（本輪不處理）

- manifest 抽樣校驗率（R1 #2）  
- Phase 8.6 bridge 鍵名對照表  
- BASIC→ENRICH 補跑 delta  
- `billing_table` 財務核定具體金額  

---

*Wave 6 R2 · spec only · 建議路徑：`04_Workflows/WAVE6_DATA_CLEANING_R2_APPENDICES_v0.1.md`*
