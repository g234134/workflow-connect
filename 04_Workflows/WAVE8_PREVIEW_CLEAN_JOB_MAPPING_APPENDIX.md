# Wave 8 – Preview CleanJob Mapping 本地驗證附錄（v0.1）

> **票號**：`W8-PREVIEW-MAPPING-APPENDIX`  
> **受众**：工程師、QA  
> **性质**：工具使用說明（非規格正文）  
> **範圍**：本地驗證 intake JSON → CleanJob → Wave7 inputs 映射鏈路，不執行實際作業  
> **不做**：跑 `run_wave7_job()`、寫生產資料、新增複雜依賴

---

## 1. 背景與目的

在開發或調試 intake gate 時，工程師/QA 需要快速驗證一份 intake JSON 是否能正確映射為 CleanJob，再轉換為 Wave7 runner 所需的 `job_record` + `raw_files[]`。

本附錄說明如何使用 `_wave8_preview_clean_job_mapping.py` CLI 工具進行本地驗證。

---

## 2. 前置條件

### 2.1 工作目錄與 Python

- **工作目錄**：戰車根（含 `04_Workflows/Master_Map.json`）
- **解釋器**：暗部 `gov_core_system` venv

```powershell
# 戰車根下設置別名
$GovPy = ".\01_Environments\python_venvs\gov_core_system\Scripts\python.exe"
```

### 2.2 依賴檢查

CLI 工具依賴以下暗部模組：
- `core.wave8_clean_intake_mapper`
- `core.wave8_clean_job_bridge`

```powershell
$GovPy -c "from core.wave8_clean_intake_mapper import map_intake_to_clean_job; print('mapper OK')"
$GovPy -c "from core.wave8_clean_job_bridge import build_wave7_inputs_from_clean_job; print('bridge OK')"
```

---

## 3. CLI 使用說明

### 3.1 基本用法

```powershell
python 04_Workflows/_wave8_preview_clean_job_mapping.py --intake-json path/to/intake.json
```

### 3.2 輸出格式

stdout 輸出結構化 JSON：

```json
{
  "ok": true,
  "clean_job": { ... },
  "job_record": { ... },
  "raw_files": [ ... ],
  "sidecar": { ... },
  "message": "Mapping chain completed successfully",
  "error_code": null,
  "schema_version": "wave8_preview_v0.1"
}
```

| 欄位 | 說明 |
|------|------|
| `ok` | 映射成功 `true` / 失敗 `false` |
| `clean_job` | 第一階段輸出（CleanJob 結構）|
| `job_record` | 第二階段輸出（Wave7 job 最小結構）|
| `raw_files` | 第二階段輸出（檔案陣列）|
| `sidecar` | bridge 附加資訊（options、trace 等）|
| `message` | 人類可讀說明 |
| `error_code` | 錯誤碼（成功時為 `null`）|

### 3.3 常用選項

| 選項 | 說明 |
|------|------|
| `--intake-json PATH` | 必要，intake JSON 檔案路徑 |
| `--pretty` | 美化輸出 JSON |
| `--verbose` | 額外診斷資訊輸出到 stderr |

### 3.4 完整範例

```powershell
# 驗證 BASIC 類型 intake
python 04_Workflows/_wave8_preview_clean_job_mapping.py `
  --intake-json 04_Workflows/fixtures/intake_basic_sample.json `
  --pretty

# 驗證 ENRICH 類型 intake，含詳細診斷
python 04_Workflows/_wave8_preview_clean_job_mapping.py `
  --intake-json 04_Workflows/fixtures/intake_enrich_sample.json `
  --pretty --verbose
```

---

## 4. 退出碼

| 退出碼 | 含義 |
|--------|------|
| `0` | 映射成功 |
| `1` | 映射失敗（驗證錯誤、檔案不存在、JSON 解析失敗、import 錯誤等）|

**CI/自動化使用**：

```powershell
python 04_Workflows/_wave8_preview_clean_job_mapping.py --intake-json test.json
if ($LASTEXITCODE -ne 0) { Write-Host "Mapping validation failed" }
```

---

## 5. Fixture 範例檔案

### 5.1 BASIC 類型

路徑：`04_Workflows/fixtures/intake_basic_sample.json`

最小有效 intake，適用 `CLEAN-BASIC` SKU：
- 單一 data_source
- 無 PII
- 無 enrich_configuration

### 5.2 ENRICH 類型

路徑：`04_Workflows/fixtures/intake_enrich_sample.json`

完整 ENRICH intake，適用 `CLEAN-ENRICH` SKU：
- 含 PII 欄位標記
- 含 enrich_configuration
- api_key_status = "ready"

---

## 6. 故障排查

### 6.1 ImportError: 找不到 core 模組

**症狀**：
```
Failed to import mappers: No module named 'core'
```

**排查**：
1. 確認工作目錄為戰車根
2. 確認 `01_Environments/python_venvs/gov_core_system` 存在
3. 確認 `gov_core_system/core/` 目錄含 `wave8_clean_intake_mapper.py`

**修復**：
```powershell
# 手動指定 venv
.\01_Environments\python_venvs\gov_core_system\Scripts\python.exe `
  04_Workflows/_wave8_preview_clean_job_mapping.py --intake-json ...
```

### 6.2 驗證錯誤：缺少必填欄位

**症狀**：
```json
{
  "ok": false,
  "error_code": "missing_required",
  "validation_errors": [{"field": "client_ref", "code": "missing_required", ...}]
}
```

**排查**：
- 對照 `test_wave8_clean_intake_mapper.py` 中的 `_basic_intake_record()` 結構
- 確認 intake_status = "complete"
- 確認 product_sku 為 `CLEAN-BASIC` 或 `CLEAN-ENRICH`

### 6.3 ENRICH 驗證失敗

**常見錯誤**：
- `ERR_MISSING_ENRICH_PLAN_REF` — enrich_configuration 缺少 `enrich_plan_ref`
- `ERR_ENRICH_API_NOT_READY` — `api_key_status` 不是 "ready"
- `ERR_BASIC_MUST_OMIT_ENRICH_PLAN` — BASIC 類型不應有 enrich_plan_ref

---

## 7. 與生產流程的區別

| 項目 | 本 CLI | 生產流程 |
|------|--------|----------|
| 執行 `run_wave7_job()` | ❌ 否 | ✅ 是 |
| 寫入 delivery / staging | ❌ 否 | ✅ 是 |
| 實際讀取 data source 檔案 | ❌ 否 | ✅ 是 |
| 生成 envelope / manifest | ❌ 否 | ✅ 是 |
| 執行 M1 / M2 QA | ❌ 否 | ✅ 是 |
| 驗證映射邏輯 | ✅ 是 | ✅ 是 |

---

## 8. 延伸閱讀

| 文件 | 內容 |
|------|------|
| `WAVE7_RUNBOOK_CLI_AND_QA_v0.1.md` | Wave 7 完整 CLI 與 QA 說明 |
| `WAVE8_M2_RUNBOOK_v0.1.md` | Wave 8 M2 抽樣 QA 運維手冊 |
| `core/wave8_clean_intake_mapper.py` | intake → CleanJob 映射實作 |
| `core/wave8_clean_job_bridge.py` | CleanJob → Wave7 inputs 橋接實作 |
| `tests/test_wave8_clean_intake_mapper.py` | 映射器單元測試與 fixture 範例 |

---

*Wave 8 Preview CleanJob Mapping 附錄 · `04_Workflows/WAVE8_PREVIEW_CLEAN_JOB_MAPPING_APPENDIX.md` · v0.1*
