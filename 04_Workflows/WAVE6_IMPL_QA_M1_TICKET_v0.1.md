# Wave 6 - IMPL Ticket · QA-M1（manifest only）

> **票號**：`W6-IMPL-QA-M1`  
> **性質**：implementation ticket  
> **範圍**：只做 `manifest.json` 全量完整性 QA（M1）  
> **依據**：R3 §G.3 / §G.5 / §G.7；R2 §A.1 / §A.2 / §D.3  
> **不做**：M2 抽樣規則、`deliverables/` envelope 深檢、`qa.overall_ok`、`ENVELOPE` 結構調整

---

## 0. 目標

把 `W6-IMPL-QA-M1` 收斂成一張可直接派工的實作票，交付一個 **manifest-only** QA 檢查器：

- 100% 掃描 `manifest.json` 每一列。
- 只驗證 manifest 層的鍵、SHA、去重、BASIC/ENRICH 邊界與 `accepted_units` 對齊。
- 只輸出 `qa.manifest_integrity` 和 `qa.failures[]`。
- **不得**打開 `deliverables/` 內 envelope JSON。
- **不得**把 M1 做成整體 QA。
- **不得**輸出或推導 `qa.overall_ok`。

一句話定義：**QA-M1 = manifest integrity gate，不是整包 QA verdict。**

---

## 1. 範圍與非範圍

| 類別 | 內容 |
|------|------|
| **M1 要做** | 全量掃 manifest 列；執行 `M1-KEYS` / `M1-SHA` / `M1-OK-ONLY` / `M1-SKU-BASIC` / `M1-SKU-ENRICH` / `M1-DEDUP` / `M1-COUNT`；輸出 M1 失敗清單 |
| **M1 不做** | 不抽樣、不讀 envelope、不驗 `enrichment` 內容正確性、不重算 `quality_score`、不做 `M2-*` |
| **明確禁止** | 不宣告 `qa.overall_ok`；不把 `qa.manifest_integrity` 當成整體 QA 最終結論；不修改 `manifest`/`report`/`envelope` schema |
| **下游關係** | M1 完成後優先 handoff 給 `QA-M2`；其次 handoff 給 `BRIDGE-MAP` 消費 M1 輸出 |

---

## 2. 輸入定義

M1 僅依賴以下三個輸入：

### 2.1 必要輸入

| 輸入 | 型別 | 用途 |
|------|------|------|
| `manifest.json` | array<object> | M1 主檢查對象；逐列掃描 |
| `job_record.sku` | string | 決定 BASIC/ENRICH 邊界檢查 |
| `report.summary.accepted_units` | int | 與 manifest ok 列數對帳 |

### 2.2 M1 實際消費的 manifest 列鍵

| 鍵 | 用途 |
|----|------|
| `file_id` | row identity |
| `content_sha256` | SHA 格式與去重 |
| `clean_status` | ok 列判定 |
| `extension` | 必填鍵檢查 |
| `stored_logical_path` | 必填鍵檢查與 failure 定位 |
| `schema_version` | 必填鍵檢查 |
| `has_enrichment` | ENRICH manifest 邊界 |
| `enrichment` | BASIC manifest 邊界（只檢查是否出現，不檢查內容） |

### 2.3 輸入前提

- `manifest.json` 可為空陣列；M1 仍需回傳結構化輸出。
- `job_record.sku` 只接受 `CLEAN-BASIC` 或 `CLEAN-ENRICH`；若上游傳入其他值，本票不新增新規則，交由上游 intake / job contract 處理。
- M1 不依賴 `report.qa.*` 既有欄位，不讀 `qa.overall_ok`。

---

## 3. 輸出定義

### 3.1 僅允許的輸出

```json
{
  "qa": {
    "manifest_integrity": {
      "ok": true,
      "checked_rows": 0,
      "failed_rows": 0,
      "failed_checks": 0
    },
    "failures": []
  }
}
```

### 3.2 `qa.manifest_integrity`

| 鍵 | 型別 | 定義 |
|----|------|------|
| `ok` | bool | `failed_checks == 0` 時為 `true`；否則 `false` |
| `checked_rows` | int | 實際掃描的 manifest 列數 |
| `failed_rows` | int | 具有至少一個 row-scoped M1 failure 的**去重後列數** |
| `failed_checks` | int | `qa.failures[]` 物件總數 |

### 3.3 `qa.failures[]`

每個失敗必須輸出為一筆 `qa_failure_record`：

```json
{
  "layer": "M1",
  "check_id": "M1-KEYS",
  "severity": "P0",
  "file_id": "string|null",
  "content_sha256": "hex64|null",
  "stored_logical_path": "string|null",
  "message": "human readable <= 200 chars",
  "remediation_hint": "fix_manifest"
}
```

### 3.4 嚴格限制

- 本票 **只輸出** `qa.manifest_integrity` 與 `qa.failures[]`。
- 本票 **不得新增** `qa.sample_validation`。
- 本票 **不得輸出** `qa.overall_ok`。
- 本票 **不得寫入** `qa_status`。

---

## 4. M1 檢查項列表（逐項可 unit test）

### 4.1 檢查矩陣

| check_id | 嚴重度 | 預期行為 |
|----------|--------|----------|
| `M1-KEYS` | P0 | 每列必須存在 `file_id`、`content_sha256`、`clean_status`、`extension`、`stored_logical_path`、`schema_version`；缺任一鍵即產生 1 筆 failure |
| `M1-SHA` | P0 | `content_sha256` 必須為 64 位小寫或大寫 hex 字串；非 hex、長度不為 64、空值皆失敗 |
| `M1-OK-ONLY` | P0 | 只有 `clean_status=ok` 的列可被視為 accepted row；非 `ok` 列不得被算入 ok 計數 |
| `M1-SKU-BASIC` | P0 | 當 `job_record.sku=CLEAN-BASIC` 時，manifest 列上 **不得**出現 `enrichment` 鍵；若出現即 failure |
| `M1-SKU-ENRICH` | P0 | 當 `job_record.sku=CLEAN-ENRICH` 時，每個 ok 列必須有 `has_enrichment=true`；缺值、`false`、非布林皆 failure |
| `M1-DEDUP` | P0 | 同一 job 內 `content_sha256` 必須唯一；重複 SHA 視為失敗 |
| `M1-COUNT` | P0 | `clean_status=ok` 的列數必須等於 `report.summary.accepted_units`；不一致即 failure |

### 4.2 BASIC / ENRICH 邊界

| SKU | M1 應檢查 | M1 不檢查 |
|-----|-----------|-----------|
| `CLEAN-BASIC` | manifest 層不得出現 `enrichment` 鍵 | 不打開 envelope 驗證 `groq_used`、`quality_score`、`enrichment.schema_version` |
| `CLEAN-ENRICH` | manifest 層 `has_enrichment=true` | 不驗證 `enrichment` 內容、coverage、quality |

### 4.3 去重語意

- 去重鍵只認 `content_sha256`。
- 同一 SHA 首列視為保留列；其後重複列各自產生 failure。
- `M1-DEDUP` 只檢查 **同一 job / 同一份 manifest** 內重複，不跨 job 比較。

---

## 5. failure 記錄與對帳規則

### 5.1 failure 產生規則

- **一個 row × 一個 check_id = 一筆 failure**。
- 同一列若同時違反 `M1-KEYS` 與 `M1-SHA`，應輸出 2 筆 failure。
- `M1-COUNT` 為 aggregate failure，允許輸出 1 筆 `file_id=null` / `content_sha256=null` / `stored_logical_path=null` 的 job-scoped failure。

### 5.2 `failed_rows` 對帳

- `failed_rows` = 具有至少一筆 **row-scoped** failure 的 distinct row 數。
- aggregate-only failure（例如 `M1-COUNT`）**增加 `failed_checks`，但不增加 `failed_rows`**。

### 5.3 對帳公式

| 指標 | 規則 |
|------|------|
| `checked_rows` | `len(manifest_rows)` |
| `failed_checks` | `len(qa.failures)` |
| `failed_rows` | `count(distinct row_key among row-scoped failures)` |
| `manifest_integrity.ok` | `failed_checks == 0` |

建議 row key 優先順序：

1. `file_id`
2. 若 `file_id` 缺失，退回 `content_sha256`
3. 若兩者都缺，使用 manifest row index（僅內部計數，不外露成 contract）

---

## 6. 驗收條件（unit-test 導向）

### 6.1 最低測試集合

| 測試名 | 期望 |
|--------|------|
| `test_m1_keys_pass_minimal_row` | 最小合法列通過，`failed_checks=0` |
| `test_m1_keys_fail_missing_required_key` | 每缺一個必填鍵會產生對應 failure |
| `test_m1_sha_fail_non_hex_or_wrong_length` | 非 64 hex 失敗 |
| `test_m1_ok_only_counts_only_clean_status_ok` | ok 列計數只認 `clean_status=ok` |
| `test_m1_sku_basic_rejects_enrichment_key` | BASIC 列出現 `enrichment` 時失敗 |
| `test_m1_sku_enrich_requires_has_enrichment_true` | ENRICH ok 列缺 `has_enrichment=true` 時失敗 |
| `test_m1_dedup_flags_duplicate_sha_after_first_row` | 重複 SHA 的後續列被標失敗 |
| `test_m1_count_matches_report_summary_accepted_units` | ok 列數與 `accepted_units` 對齊 |
| `test_manifest_integrity_counts_reconcile` | `checked_rows` / `failed_rows` / `failed_checks` 對帳正確 |
| `test_m1_never_emits_overall_ok` | 輸出不含 `qa.overall_ok` |
| `test_m1_never_reads_envelope` | M1 執行流程不依賴 `deliverables/` 或 envelope 內容 |

### 6.2 Done 驗收

本票 only 可在以下條件同時成立時標 Done：

1. 上表測試全綠。
2. 輸出 shape 僅包含本票允許欄位。
3. `M1-*` check_id 與 failure shape 與本票一致。
4. 未讀取 envelope 檔。
5. 未引入 `qa.overall_ok`。

---

## 7. P0 失敗時的阻斷規則

### 7.1 M1 對流程的硬阻斷

任一 `M1-*` P0 失敗時：

- `qa.manifest_integrity.ok=false`
- **不得**標記 job `Done`
- **不得**標記 job `Chargeable`
- **不得**以「M2 尚未發現問題」覆蓋 M1 結論

### 7.2 與整體 QA 的邊界語言

- `qa.manifest_integrity=false` 只表示 **manifest gate 未過**。
- 本票 **不負責**輸出 `qa.overall_ok`。
- 若未來需要整體 QA verdict，應由上層在 **M1 + M2** 完成後組裝；**不得**回填到 M1 票內。

---

## 8. 實作約束

### 8.1 必須遵守

- 檢查器必須是 deterministic。
- 同一輸入重跑，`qa.failures[]` 順序應穩定。
- `M1-COUNT` 只能依賴 manifest ok 列數與 `report.summary.accepted_units`，不得偷讀其他外部統計。

### 8.2 明確禁止

- 不打開 `deliverables/*.json`
- 不建立 `M2-*` 規則
- 不重定義 `qa_failure_record`
- 不修改 `manifest` / `report` schema
- 不輸出 `qa.overall_ok`
- 不把 `manifest_integrity` 命名成 `overall_ok`、`qa_ok` 或其他整體 verdict 名稱

---

## 9. 主要風險與緩解

| 風險 | 說明 | 緩解 |
|------|------|------|
| 上游 manifest 欄位漂移 | 上游若改鍵名或新增中介欄位，M1 容易誤擴 scope | 本票只認 §2.2 消費鍵；新增鍵不納入 contract |
| M1 被做成整體 QA | 實作者可能順手把 M2 或 `overall_ok` 也做進來 | 測試強制 `test_m1_never_emits_overall_ok`；票面明定 only M1 outputs |
| dedup 語意漂移 | 可能誤用 `file_id` 或 path 去重 | 寫死去重鍵為 `content_sha256`；單測覆蓋重複 SHA 案例 |
| BASIC/ENRICH 邊界外溢 | 可能去讀 envelope 驗 `enrichment` 內容 | 票面只允許 manifest 層旗標檢查；禁止打開 envelope |
| `accepted_units` 對帳被改成複合公式 | 可能偷摻 `schema_version`、`groq_used`、M2 結果 | `M1-COUNT` 只按 R3 G.3：ok 列數對 `accepted_units` |

---

## 10. Next Handoff

| 優先 | 對象 | handoff 內容 |
|------|------|--------------|
| 1 | `QA-M2` | 提供 `qa.manifest_integrity` 與 `qa.failures[]`，讓 M2 在不重做 M1 的前提下專注 envelope 抽樣深檢 |
| 2 | `BRIDGE-MAP` | 對接 `manifest_integrity.ok`、`checked_rows`、`failed_rows`、`failed_checks` 的 bridge 消費映射 |

---

## 11. 票面摘要（可直接派工）

```text
實作 W6-IMPL-QA-M1：只對 manifest.json 做全量完整性 QA。
輸入僅 manifest.json、job_record.sku、report.summary.accepted_units。
輸出僅 qa.manifest_integrity 與 qa.failures[]。
必做 M1-KEYS / M1-SHA / M1-OK-ONLY / M1-SKU-BASIC / M1-SKU-ENRICH / M1-DEDUP / M1-COUNT。
禁止讀 envelope、禁止定義 M2、禁止輸出 qa.overall_ok。
任一 P0 失敗即阻斷 Done / Chargeable。
```

---

*Wave 6 implementation ticket · manifest QA only · `04_Workflows/WAVE6_IMPL_QA_M1_TICKET_v0.1.md`*
