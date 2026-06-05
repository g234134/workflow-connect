# Wave 6 – DATA-CLEANING · R4 裁定（v0.1 · closure only）

> **輪次**：W6-R4 · **範圍**：#H-1 · #H-2 · #I-1 · #J-1  
> **不做**：code · runner · orchestrator · README · 新規則 · 改寫 R1／R2／R3 凍結正文  
> **權威**：本檔為四項 TBD 之**尚書省拍板**；回寫見 §6  
> **狀態**：**RATIFIED-v0.1**（2026-06-04）

---

## 1. 本輪裁定範圍

| ID | 議題 | 裁定檔 |
|----|------|--------|
| #H-1 | bridge 是否帶 `content_sha256_list[]` | §2 |
| #H-2 | `delivery.artifact_refs` 邏輯 URI | §3 |
| #I-1 | JOB-B 未開票時是否單張合併發票 | §4 |
| #J-1 | `billing_table` 權威路徑 | §5 |

---

## 2. #H-1 裁定結果

**問題**：`bridge_result.wave6.manifest` 是否包含完整 `content_sha256_list[]`？

| 方案 | 內容 |
|------|------|
| **A** | 納入全量 sha256 列表（與 manifest 同 cardinality） |
| **B** | **不納入**；僅 `logical_ref`、`job_id`、`product_sku`、`accepted_units`、`billable_u`、`billable_l` |

**裁定（尚書省拍板）**：**採 B**。

**理由（硬）**：計費真相在交付包 `manifest.json`（R2 §A.1）；bridge 為觀測側車，大批量會膨脹回應且與 `[BRIDGE-EXT]` 非必填契約衝突。

**影響回寫**：

- R3 §H.2：刪除 `content_sha256_list[]` 列；CONF-R3-01 **結案**。  
- 實作：`bridge_result.wave6.manifest` **不得**要求 sha 列表；需全量 sha 時讀 `logical_ref` 指向之 manifest。

---

## 3. #H-2 裁定結果

**問題**：`[P65] delivery.artifact_refs[]` 元素之邏輯 URI 格式。

| 方案 | 內容 |
|------|------|
| **A** | 自由字串（`OpaqueRef`），無格式約束 |
| **B** | 固定 scheme **`w6://delivery/{job_id}/{artifact_kind}`** |

**裁定（尚書省拍板）**：**採 B**。

**`artifact_kind` 枚舉（封閉）**：

| kind | 對應交付物 |
|------|------------|
| `manifest` | `manifest.json` |
| `report_json` | `report.json` |
| `report_md` | `ART-DATA-CLEAN-REPORT`（Markdown） |
| `deliverables` | `deliverables/` 封存包或目錄 ref |

**範例**（邏輯，非磁碟路徑）：`w6://delivery/{job_id}/manifest`

**約束**：

- `job_id` = 該次交付之 `job_record.job_id`（UUID 字串）。  
- 單 ref 長度 ≤ **200**（對齊 Phase 6.5 `OpaqueRef`）。  
- **禁止** 磁碟絕對路徑、`:\`、`file://` 實例根。

**`delivery.artifact_refs[]` 最低集合（Done 提交時）**：四種 `artifact_kind` 各至少 1 條 URI（`deliverables` 可為 bundle ref）。

**影響回寫**：R3 §H.4；R2 §A.6 MVP 證據鍵改為 **w6 URI**（語意不變）。

---

## 4. #I-1 裁定結果

**問題**：JOB-B 已 Done 但**未** `invoice.issued` 時，JOB-E 是否允許**單張合併發票**？

| 方案 | 內容 |
|------|------|
| **A** | **禁止合併**；JOB-E 開票前 JOB-B 須已開票或書面豁免 |
| **B** | 允許 JOB-E 單張合併票（追溯 BASIC + 當次 ENRICH） |

**裁定（尚書省拍板）**：**分情形，非二選一全局**：

| JOB-B 狀態 | 採用 | 發票行為 |
|------------|------|----------|
| 已 `invoice.issued` | **A** | JOB-E **僅** `CLEAN-ENRICH` + `CLEAN-ENRICH-LLM`（R3 §I.5 R-UPG-1／2 **不變**） |
| 未開票且無豁免 | **B** | JOB-E **一張**合併發票，`invoice.consolidation_mode=basic_unbilled_merge` |
| 未開票但有豁免 | **A** | `open_questions` 載明 `job_b_invoice_waived=true` → JOB-E 僅 ENRICH 行項 |

**方案 B 合併票硬條件（全部）**：

1. JOB-B、JOB-E 均 Done 且 `qa.overall_ok=true`；  
2. 同一 `client_ref`；  
3. `report.upgrade.mode=basic_to_enrich_delta`；  
4. 行項：**(i)** `CLEAN-BASIC` × `U_B`（來自 JOB-B manifest） **(ii)** `CLEAN-ENRICH` × `U_E` **(iii)** `L` 來自 JOB-E；  
5. `upgrade_credit_refs=[]`（因 BASIC 尚未開票，無抵扣）；  
6. **禁止** 對同一 `content_sha256` 出現兩行 `CLEAN-BASIC`；  
7. JOB-B **不再** 單獨開票（合併票覆蓋 BASIC 帳務）。

**JOB-E Chargeable**：合併票僅在 **B 條件** 或 **A+JOB-B 已開票** 下成立；否則 **阻塞**。

**影響回寫**：R3 §I.5 **R-UPG-5** 替換 TBD；CONF-R3-02 **結案**。不新增 SKU。

---

## 5. #J-1 裁定結果

**問題**：`billing_table` JSON 檔權威落點。

| 方案 | 內容 |
|------|------|
| **A** | 戰車 `04_Workflows/wave6/billing_table_w6_v0.1.json` |
| **B** | 暗部 `gov_core_system/shared/config/` |

**裁定（尚書省拍板）**：**採 A**。

**邏輯名（地圖）**：`wave6_billing_table` → `04_Workflows/wave6/billing_table_w6_v0.1.json`（`Master_Map.json` `gov_paths` 登錄由 **W6-R5／地圖工單** 執行，**非 R4 實作**）。

**約束**：

- 財務只寫該檔 `list`／`floor`／`approved_*`；runner **不** 內嵌牌價。  
- 檔不存在或 `list.*` 仍 null → R3 §J.3 **禁止自動開票**（不變）。

**影響回寫**：R3 §J.5 步驟 1；#J-1 **結案**。

---

## 6. 檢查員：衝突與修正

| ID | 結果 |
|----|------|
| CHK-R4-01 | #H-1 B 與 R2 計費真相 **無衝突** — PASS |
| CHK-R4-02 | #H-2 `w6://` 與 R3 `logical_ref`（manifest）**並存** — PASS；`logical_ref` **不取代** `artifact_refs` |
| CHK-R4-03 | #I-1 分情形 **不違反** R-UPG-1（已開票 JOB-B 仍僅 ENRICH）— PASS |
| CHK-R4-04 | #I-1 B 合併票 **非**「同一 sha 兩次 BASIC」— PASS（一行 BASIC + 一行 ENRICH 不同 SKU） |
| CHK-R4-05 | #J-1 A 與暗部無耦合 **符合** Wave 6 產品線在 04_Workflows — PASS |
| CHK-R4-06 | 無「假裁定」：四項均可機讀驗收 — PASS |

**修正**：無需改 R2／R3 凍結條文；僅 §6 回寫表所列段落。

---

## 7. 需要回寫的附錄位置

| 檔案 | 段落 | 動作 |
|------|------|------|
| `WAVE6_DATA_CLEANING_R3_APPENDICES_v0.1.md` | §0 出口 | R3 TBD → **CLOSED-BY-R4** |
| 同上 | §H.2 | 移除 `content_sha256_list` 列 |
| 同上 | §H.4 | 填入 `w6://` 四 kind |
| 同上 | §I.5 R-UPG-5 | 替換為 R4 §4 裁定 |
| 同上 | §J.5 | 路徑 `04_Workflows/wave6/billing_table_w6_v0.1.json` |
| 同上 | §5.1 CONF-R3 | 標 **結案** |
| 同上 | §7 | 改為「無待確認項」 |
| 同上 | §8 roadmap | `spec-complete` 掛點 |
| `WAVE6_DATA_CLEANING_R2_APPENDICES_v0.1.md` | §A.6 一句 | artifact_refs 改 w6 URI（**不動** A.1–A.5 凍結數字） |

**不回寫**：R1（若僅存於 chat）；orchestrator；runner。

---

## 8. Wave 6 是否可封存為 spec-complete

| 門檻 | 狀態 |
|------|------|
| R1 產品矩陣 + Done／Chargeable | ✓（對話／索引；可 R5 單檔化） |
| R2 FROZEN 附錄 A–D | ✓ |
| R3 G–J + QA／bridge／upgrade／billing 結構 | ✓ |
| R4 四項 TBD | ✓ **本檔** |
| 財務 `list.*` 非 null | ✗ **營運**；不阻擋 spec-complete |
| 程式實作 | ✗ **W6-IMPL-***；不屬 spec 封存 |

**裁定**：Wave 6 制度 spec 可封存為 **`spec-complete`**（**不含**實作與牌價數字）。

**W6-R5 建議入口**：`Master_Map` 登錄 `wave6_billing_table` + 可選單頁索引（README）；**非**本輪。

---

*Wave 6 R4 · closure only · `04_Workflows/WAVE6_DATA_CLEANING_R4_RATIFICATIONS_v0.1.md`*
