# W5-D-SMOKE-FIXTURE-PROVENANCE Brief — Smoke Fixture 溯源 line_index 修正（給 Cursor 的簡短任務卡）

> **源頭**：`smoke_eval_results.jsonl`（或等價路徑）中部分記錄的 `source_ref.line_index` 指向匯出檔自身行號而非原始輸入檔案（ibridge_records / shadow_raw）行號，造成 traceability 誤導。  
> **風險**：低 — 無測試依賴 line_index、程式碼邏輯正確、不影響 CI。  
> **目標**：用「改少量 line_index 數字 + 補 schema 說明」修正 smoke fixture 的溯源資訊，不改程式、不改測試、不改 CI。  
> **關聯方案**：`W5-D-SMOKE-FIXTURE-PROVENANCE_plan.md`（完整調查與風險評估） + `W5-D-FIXTURE-PROVENANCE_plan.md`（前次 eval 版完整調查可作方法論參考）。  

---

## 任務說明

`tests/fixtures/eval/smoke_eval_results.jsonl`（佔位路徑，請用 `find` 確認實際名稱）中存在與 `eval_export_sample.jsonl` 完全同類的 line_index 偏移問題：部分記錄的 `source_ref.line_index` 記錄是匯出檔案自身的行號，而非原始 ibridge_records / shadow_raw 檔案中該記錄的原始行號。這讓 traceability 不正確。本任務延續 W5-D-FIXTURE-PROVENANCE-01 的 same pattern，但對象換成 smoke 類 fixture。風險評級為低（無測試依賴、無 runtime bug），修正是個快贏（改 1–6 個數字 + 補一兩行 schema 說明）。

---

## 允許操作

- 編輯 `smoke_eval_results.jsonl`（或等價路徑）中個別記錄的 `source_ref.line_index` 數字
- 可選：對對應的 shadow smoke artifact（如 `smoke_eval_results.latest.jsonl`）做 minimal 對齊修正，修正後在文檔註明「因 schema 轉換僅到 ibridge 中間格式」
- 在 `eval_export_schema.md`（或 `smoke_eval_schema.md`）中補充 `source_ref.line_index` 的 smoke 特定淵語義說明（可重用 eval 版表述但加上 smoke-specific 說明）
- 跑與 smoke fixture 相關的測試確認全部通過
- 先用 `find` / `ls` 確認 smoke fixture 系列的實際路徑名稱（**這是第一步，請先做**）

## 禁止操作

- 修改 `eval_exporter.py` / `ibridge_exporter.py` / `smoke_gate.py` / `eval_ci_check.py` 等任何程式碼邏輯
- 修改任何測試斷言或增加新的測試案例
- 修改 fixture 的記錄結構、schema_version、tags、gate_result、metrics 等非 line_index 欄位
- 增加或刪除 fixture 中的記錄
- 修改 `ibridge_records.jsonl` 或 `shadow_raw_records.jsonl`（參考基準不動）
- 將此 cleanup 擴大成「重寫所有 smoke 類 fixture」或「重建 smoke pipeline」

---

## 實作步驟 Checklist

1. **路徑確認**：先用 `find tests/fixtures/eval/ -name '*smoke*'` 和 `find artifacts/eval/ -name '*smoke*'` 確認 smoke fixture 的實際檔案名稱與結構
2. **比對確認**：比對 smoke fixture 與對應原始輸入檔案（可能是 `ibridge_records.jsonl` 或 `shadow_raw_records.jsonl`），找出 line_index 偏移的記錄及其正確行號
3. **修正主要 smoke fixture**：用安全的 JSON 編輯方式（python json load/dump 或 jq，非手動 sed）修正偏移的 line_index 數值
4. **可選修正 shadow smoke artifact**：若 artifact 也有偏移，做 minimal 對齊修正，並在文檔註明中間格式限制
5. **文檔補充**：在相關 schema/markdown（`eval_export_schema.md` 的 `source_ref.line_index` 段落或獨立 `smoke_eval_schema.md`）中強化 line_index 的 smoke 特定淵語義，包含「smoke fixture 的 line_index 是手動修正的（非 exporter runtime 自動產生）」的說明
6. **跑測試**：執行與 smoke fixture 相關的測試（如 `python -m unittest tests.test_smoke_eval tests.test_smoke_gate` 等），確認全部 pass 且輸出與修正前一致
7. **全域確認**：`git diff --stat` 確認只改了授權檔案，無意外修改；所有 JSON/JSONL 通過格式驗證

---

## 驗收條件

- **AC1**：至少一條 smoke fixture 記錄可以精準追到對應原始輸入檔案（ibridge_records / shadow_raw）的行號
- **AC2**：所有相關 smoke 測試全部通過，測試輸出與修正前一致
- **AC3**：schema/markdown 中對 smoke line_index 的語義有明確說明，包含「smoke fixture 的 line_index 是手動修正的（非 exporter runtime 產生）」的註記，以及（若有修正 shadow 檔案）中間格式限制
- **AC4**：修改僅限於授權檔案（smoke fixture JSON + shadow artifact + schema markdown），無程式邏輯/測試斷言/其他 fixture 變更
- **AC5**：所有 JSON/JSONL 檔案通過格式驗證（無 syntax error）
- **AC6**（可選）：若確認 smoke fixture 完全無法追溯到唯一原始 source（例如資料是綜合產生的），則在文檔中明確寫明「smoke fixture 為綜合示意資料，line_index 僅為近似對齊」

---

## 回報格式框架

```markdown
## Execution Report — W5-D-SMOKE-FIXTURE-PROVENANCE

### 修改檔案清單
- tests/fixtures/eval/<smoke_fixture_實際名稱>.jsonl（line_index 修正）
- artifacts/eval/<smoke_shadow_artifact_實際名稱>.jsonl（選用）
- observability/eval_export_schema.md（或 smoke_eval_schema.md，文檔補充）

### line_index 修前/修後
| 記錄 | fixture 行 | 修前 | 修後 | 原始檔案實際行 | 備註 |
|------|-----------|------|------|---------------|------|
| <task_id> | 1 | N | M | M | |
| <task_id> | 2 | N | M | M | |
| （如有更多請續列） |

### 文檔更新摘要
<簡述在 schema.md 補充了哪些 line_index 語義說明，特別強調 smoke 特定修改>

### 測試結果
python -m unittest <相關測試模組名>
<貼全部 OK 的輸出>

### 自檢勾選
- [AC1] line_index 對上實際行號：<OK/FAIL>
- [AC2] 測試全部通過且一致：<OK/FAIL>
- [AC3] schema 說明完整（含 smoke 語義 + 中間格式限制）：<OK/FAIL>
- [AC4] 僅改授權檔案：<OK/FAIL>
- [AC5] JSON 格式通過驗證：<OK/FAIL>
- [AC6] （選用）綜合示意說明已補：<OK/N/A>

### 已知殘留
- （若有）shadow smoke artifact 僅到 ibridge 中間格式，無法 1:1 到原始 raw source
- （若有）smoke fixture 為綜合示意資料，line_index 僅近似對齊
- （若有）其餘小型 smoke 子 fixture 未在本票範圍內處理
```
