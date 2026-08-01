# W5-D-FIXTURE-PROVENANCE Brief — Fixture 溯源 line_index 修正（給 Cursor 的簡短任務卡）

> **源頭**：eval_export_sample.jsonl 中 2/3 記錄的 `source_ref.line_index` 指向「匯出檔行號」而非 `ibridge_records.jsonl` 原始行號，造成 traceability 誤導。  
> **風險**：低 — 無測試依賴 line_index、程式碼邏輯正確、不影響 CI。  
> **目標**：用「改 2 個數字 + 補 schema 說明」修正 fixture 溯源資訊，不改程式、不改測試、不改 CI。  
> **關聯方案**：`W5-D-FIXTURE-PROVENANCE_plan.md`（完整調查與風險） +  `W5-D-FIXTURE-PROVENANCE_IMPLEMENTATION_TEMPLATE.md`（完整步驟與回報格式）。

---

## 任務說明

`tests/fixtures/eval/eval_export_sample.jsonl` 中 t-infra 和 t-healthy 的 `source_ref.line_index` 記錄的是匯出檔案自身的行號（1 和 3），而非 `ibridge_records.jsonl` 中該記錄的原始行號（應為 3 和 1）。這讓 traceability 不對：t-infra 實際來自 ibridge_records 的第 3 行，但 line_index=1 讓讀者誤以為它是第 1 行。風險評級為低（無測試依賴、無 runtime bug），但修正是個快贏（改 2 個數字 + 補一兩行 schema 說明）。

---

## 允許操作

- 編輯 `eval_export_sample.jsonl` 中個別記錄的 `source_ref.line_index` 數字（t-infra: 1→3, t-healthy: 3→1）
- 可選：對 `shadow_eval_results.latest.jsonl` 做對應修正（4 條全部偏移，修正後在文檔註明「因 schema 轉換只能到 ibridge 中間格式」）
- 在 `eval_export_schema.md` 中補充 `source_ref.line_index` 的溯源語義說明
- 在 `eval_stats_report.md` §Limitations 中記錄 fixture provenance 處理狀態
- 跑相關測試確認全部通過

## 禁止操作

- 修改 `eval_exporter.py` / `ibridge_exporter.py` / `eval_ci_check.py` / `eval_stats.py` 等程式碼邏輯
- 修改任何測試斷言或增加新的測試案例
- 修改 fixture 的記錄結構、schema_version、tags、gate_result、metrics 等非 line_index 欄位
- 增加或刪除 fixture 中的記錄
- 修改 `ibridge_records.jsonl` 或 `shadow_raw_records.jsonl`（參考基準不動）
- 將此 cleanup 擴大成「重建整個 fixture pipeline」

---

## 實作步驟 Checklist

1. **比對確認**：比對 `ibridge_records.jsonl` 3 行的 task_id 順序 → 確認 `eval_export_sample.jsonl` 中 t-infra 對應原始第 3 行、t-healthy 對應原始第 1 行
2. **修正 eval_export_sample.jsonl**：用安全的 JSON 編輯方式（python json load/dump 或 jq，非手動 sed）將 t-infra 的 `line_index` 從 1 改為 3，t-healthy 的從 3 改為 1
3. **可選修正 shadow_eval_results.latest.jsonl**：4 條記錄的 line_index 全部偏移（1→4, 2→3, 3→2, 4→1），修正後在文檔註明「因 schema 轉換僅到 ibridge 中間格式」
4. **文檔補充**：在 `eval_export_schema.md` 的 `source_ref.line_index` 說明處強化語義（指向輸入檔案行號，非匯出檔自身行號），如有修正 shadow 則補充中間格式限制
5. **跑測試**：`python -m unittest tests.test_eval_exporter tests.test_eval_stats tests.test_eval_ci_check` — 全部應 pass 且輸出與修正前完全一致
6. **全域確認**：`git diff --stat` 確認只改了授權檔案，無意外修改

---

## 驗收條件

- **AC1**：至少 t-infra 和 t-healthy 的 line_index 能從 `eval_export_sample.jsonl` 精準追到 `ibridge_records.jsonl` 的原始行號
- **AC2**：所有相關測試全部通過，測試輸出與修正前一致
- **AC3**：`eval_export_schema.md` 中對 `source_ref.line_index` 的語義有明確說明，包含「只到中間格式」的限制（若有修正 shadow 檔案）
- **AC4**：修改僅限於授權檔案（fixture JSON + schema markdown），無程式邏輯/測試斷言/其他 fixture 變更
- **AC5**：所有 JSON 檔案通過格式驗證（無 syntax error）

---

## 回報格式框架

```markdown
## Execution Report — W5-D-FIXTURE-PROVENANCE

### 修改檔案清單
- tests/fixtures/eval/eval_export_sample.jsonl（line_index 修正）
- artifacts/eval/shadow_eval_results.latest.jsonl（選用）
- observability/eval_export_schema.md（文檔補充）
- observability/eval_stats_report.md（選用）

### line_index 修前/修後
| 記錄 | 匯出檔行 | 修前 | 修後 | ibridge_records 實際行 |
| t-infra | 1 | 1 | 3 | 3 |
| t-retry | 2 | 2 |（不變）2 | 2 |
| t-healthy | 3 | 3 | 1 | 1 |

### 文檔更新摘要
<簡述在 schema.md 補充了哪些 line_index 語義說明>

### 測試結果
python -m unittest tests.test_eval_exporter tests.test_eval_stats tests.test_eval_ci_check
<貼全部 OK 的輸出>

### 自檢勾選
- [AC1] line_index 對上實際行號：<OK/FAIL>
- [AC2] 測試全部通過且一致：<OK/FAIL>
- [AC3] schema 說明完整：<OK/FAIL>
- [AC4] 僅改授權檔案：<OK/FAIL>
- [AC5] JSON 格式通過驗證：<OK/FAIL>

### 已知殘留
- shadow 檔案僅到 ibridge 中間格式（schema 轉換無法 1:1 到 raw source）
- smoke_eval_results.jsonl 未修正（artifact 目錄，非 fixture）
```
