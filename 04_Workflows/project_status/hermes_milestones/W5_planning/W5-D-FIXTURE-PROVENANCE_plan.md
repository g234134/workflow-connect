# W5-D-FIXTURE-PROVENANCE — Fixture 溯源缺口 · 方案卡

> **票號**：W5-D-FIXTURE-PROVENANCE-PLAN-01（只讀方案卡）  
> **源頭**：eval_exporter readonly scan 發現 fixture 內 `source_ref.line_index` 與原始輸入行號不一致  
> **範圍**：僅 fixture 溯源關係的修正／標記策略設計  
> **不處理**：更改程式邏輯、重寫測試、批量改寫 fixture 結構  

---

## (1) 背景摘要

**FIXTURE-PROVENANCE 的問題本質**：

`tests/fixtures/eval/eval_export_sample.jsonl` 中的 `source_ref.line_index` 字段記錄的是**匯出檔案自身的行號**，而非**原始 ibridge_records.jsonl 中的行號**。這違反了 `source_ref.line_index` 的設計語義 — 它應該指向輸入檔案中的行位置，讓讀者可以反向追蹤每一筆 export 記錄的來源。

具體表現：

| eval_export_sample 行 | task_id | source_ref.line_index (目前值) | ibridge_records.jsonl 實際行號 | 匹配？ |
|----------------------|---------|-------------------------------|-------------------------------|--------|
| 1（匯出檔順序第1） | t-infra | 1 | 3 | ❌ |
| 2（匯出檔順序第2） | t-retry | 2 | 2 | ✅ |
| 3（匯出檔順序第3） | t-healthy | 3 | 1 | ❌ |

**影響範圍評估 → 低風險**：
- 沒有任何測試斷言（assert）依賴 fixture 中的 `source_ref.line_index`。
- 三份相關測試（`test_eval_exporter.py`、`test_eval_stats.py`、`test_eval_ci_check.py`）均只檢查 counts、tags、gate_result 等業務字段。
- 唯一的 `line_index` 斷言在 `test_build_export_line_pass`——但它用的是 `build_export_line(_healthy_record(), line_index=1)`（自己傳入的 1），不讀 fixture。
- 因此，這個問題影響的是**可追溯性（traceability）而不是程式正確性**。fixture 依然能正確演示 `eval_export/v1` schema 的結構、tags 分布、gate_result 等。

**類似的問題也出現在 `artifacts/eval/shadow_eval_results.latest.jsonl`**（非嚴格 fixture，是一份手動產生的 artifact），它的 `line_index` 同樣是匯出檔行號而非原始 shadow_raw_records.jsonl 行號。

---

## (2) 目標與邊界

### 目標（若未來要修復）

讓 fixture 在文件層或資料層清楚標明其原始來源：  
- 至少有一處（fixture 檔案註解或相關文件的 schema 說明）明確指出 `source_ref.line_index` 的語義、以及 fixture 中該欄位是否為**真實**溯源。  
- 讓讀者在 traceability 上不會被誤導（例如以為 t-infra 來自 ibridge_records.jsonl 的第 1 行）。

### 不會做的事

- 不批量改寫 fixture JSONL 內容（不重新產生整個檔案）。  
- 不改變 fixture 的紀錄順序或 schema 結構。  
- 不重寫測試邏輯（測試不依賴 line_index，本來就 pass）。  
- 不在這個方案中提供具體的 fixture patch diff。  

---

## (3) 只讀調查結果摘要

### 發現 1：eval_export_sample.jsonl 的 3 條記錄中 2 條的 line_index 是錯的

比對結果：

| 記錄 | 匯出檔行號 | source_ref.line_index | ibridge_records.jsonl 實際行 | 偏差 |
|------|-----------|----------------------|---------------------------|------|
| t-infra | 1 | **1** | **3** | -2 |
| t-retry | 2 | **2** | **2** | 0 ✅ |
| t-healthy | 3 | **3** | **1** | +2 |

t-infra 和 t-healthy 的 line_index 互換了 — 因為匯出檔是**反序**（t-infra 最早 timestamp → 最前），而 ibridge_records.jsonl 是**正序**（t-healthy → t-infra）。fixture 建立者直接把匯出檔行號寫入 line_index，而非追蹤 ibridge_records 中的原始行號。

### 發現 2：shadow_eval_results.latest.jsonl 也有相同的偏移問題（4 條全部偏移）

| 記錄 | 匯出檔行號 | source_ref.line_index | shadow_raw_records.jsonl 實際行 | 偏差 |
|------|-----------|----------------------|-------------------------------|------|
| shadow-retry | 1 | **1** | **4** | -3 |
| shadow-greeting | 2 | **2** | **3** | -1 |
| shadow-merge-2 | 3 | **3** | **2** | +1 |
| shadow-k2-flow-1 | 4 | **4** | **1** | +3 |

這裡更嚴重 — line_index 不僅是反序，而且 shadow_raw_records 的最後兩行（case_name=shadow-greeting、case_name=shadow-retry）在 ibridge_exporter 處理時被轉換為標準 ibridge 格式（包含 task_id/trace_id 而非 case_name）。所以 baseline 無法直接逐行對應。

### 發現 3：沒有測試依賴 fixture 的 source_ref.line_index

逐一檢查三個測試檔案：

| 測試檔案 | 使用 fixture？ | 檢查 line_index？ |
|---------|---------------|-------------------|
| `test_eval_exporter.py` | `ibridge_records.jsonl`（`test_export_jsonl_all`） | ❌ — 只檢查 count、gate_result、tags、metrics |
| `test_eval_stats.py` | `eval_export_sample.jsonl` | ❌ — 只檢查 counts、ratios、tag_counts、suggest_ci_thresholds |
| `test_eval_ci_check.py` | `ibridge_records.jsonl` | ❌ — 只檢查 ok/fail、semgled count、ratio_triggered、tag_triggered |

唯一有 line_index 斷言的 `test_build_export_line_pass` 使用手建字典 + 自傳 line_index=1。

**結論**：line_index 的錯誤**不影響任何測試結果**。測試 infra 無風險。

### 發現 4：程式碼中的 line_index 語義是正確的

- `iter_records()`（eval_exporter.py line 178）：`for line_no, raw in enumerate(path.read_text().splitlines(), start=1)` — 使用原始檔案行號，正確。
- `build_export_line()` line 112-113：`line_index` 被寫入 `source_ref` 如果傳入。正確。
- `export_eval_jsonl()` line 219：`build_export_line(record, line_index=line_index)` — 將 iter_records 得到的 line_no 傳入。正確。

所以 fixture 的錯誤來自於建立時的人為疏忽，程式邏輯本身無 bug。

### 發現 5：`source_ref` 的設計目的是「去重 + 溯源」

查看 `build_export_line()` 的 source_ref 區塊：它是一個字典，可能包含 `task_id`、`trace_id`、`line_index`。其中 `line_index` 只有在 JSONL 輸入時才有意義（單 JSON 輸入時為 None）。

在實際使用場景中，`iter_records` 從目錄或檔案讀取記錄時，`line_index` 是**檔案內行號**。fixture 的正確值應該也是這個語義。

### 發現 6：shadow_eval_results.latest.jsonl 的 source_ref 還有另一個問題

shadow_raw_records.jsonl 中有兩條記錄使用 `case_name` 而非 `task_id`（shadow-greeting、shadow-retry），而在 `shadow_eval_results.latest.jsonl` 中這些變成了 `task_id`。這意味著 ibridge_exporter 在轉換時重新分配了 `task_id`。因此，即使 line_index 正確，單純靠 line_index 也無法完整追蹤到 shadow_raw_records 中的原始記錄（因為 schema 格式不同）。

---

## (4) 建議的實作策略選項

### 選項 A — 在 fixture 檔案上方加入註解說明（最輕量）

**做法**：在 `eval_export_sample.jsonl` 的首行之前加入註解行（以 `#` 開頭），說明：
- 此 fixture 是手動建立的示範資料
- `source_ref.line_index` 為匯出檔自身行號，**非** ibridge_records.jsonl 中的原始行號
- 正確的對應關係：t-infra↔ibridge_records.jsonl line 3、t-healthy↔line 1
- 如需精確溯源，請執行 `export_eval_jsonl(ibridge_records.jsonl, ...)` 產生真實匯出

**優點**：零結構改動，不影響任何 JSON parser（`iter_export_lines` 會跳過以 `#` 開頭的行嗎？不 — 它會嘗試 `json.loads` 並失敗，然後 raise ValueError。所以這個選項實際上行不通，除非改 parser）。

**缺點**：JSONL 不支援註解。加 `//` 或 `#` 開頭的行會破壞 `iter_export_lines` 的 JSON 解析。如果改 parser，又會擴散變更範圍。因此此選項**不可行**。

### 選項 B — 調整 fixture 的 line_index 讓關鍵記錄對得上（精確修正）

**做法**：修改 `eval_export_sample.jsonl` 中 t-infra 和 t-healthy 的 `source_ref.line_index` 值：
- t-infra (line 1)：`line_index: 1` → `line_index: 3`（對應 ibridge_records.jsonl 的第 3 行）
- t-healthy (line 3)：`line_index: 3` → `line_index: 1`（對應 ibridge_records.jsonl 的第 1 行）

**優點**：修正後 fixture 的 line_index 與程式產出的行為一致。所有測試不會受到影響（因為沒有測試斷言 line_index）。

**缺點**：改 fixture 的 JSON 內容可能讓以後的人誤以為「fixture 是自動產生的」。需要同步修正 schema 文件中的說明。

### 選項 C — 保留錯誤，在 schema 文件或相關 markdown 中補充說明

**做法**：不修改 fixture 內容，而是在以下位置補充溯源說明：
- `observability/eval_export.md`（若存在，作為 schema 文件）或 `eval_export_schema.md`
- 在 `source_ref.line_index` 的 schema 說明中標註「fixture 中此欄位僅為示範，實際值為匯出檔行號而非原始檔案行號」
- 同時在 `eval_stats_report.md` 的 Limitations 節中補充 fixture provenance 註記

**優點**：不改 fixture JSON，風險最低。
**缺點**：讀者如果只看 fixture 不看 schema 文件，依然會被誤導。

### 選項 D — 用真實 export_eval_jsonl 重新產生 fixture（最完整）

**做法**：在一個隔離的工作空間內：
1. 讀取 `ibridge_records.jsonl`
2. 執行 `export_eval_jsonl(ibridge_records.jsonl, output)` 
3. 將結果寫回 `tests/fixtures/eval/eval_export_sample.jsonl`
4. 確認輸出的 source_ref.line_index 與 ibridge_records 原始行號一致

**優點**：line_index 完全正確；產出方式透明可複現。全部 3 條記錄都匯出，無需篩選。

**缺點**：輸出順序與目前 fixture 不同（目前是反序，真實輸出是正序：t-healthy → t-retry → t-infra）。這會導致：
- `test_eval_stats` 中按 tag_counts 斷言的不受影響（tags 分布不變）
- `test_eval_stats` 中 `group_by="date"` 的測試依賴 `timestamp` 字段，不受順序影響
- `test_eval_exporter.test_export_jsonl_all` 讀取的是 ibridge_records.jsonl 而非 eval_export_sample.jsonl，不受影響
- 但如果有人**依賴 eval_export_sample 的特定行順序**來推斷 gate_result 分布（例如 line 1=needs_review），就需要調整認知

---

## (5) 風險與驗收要點

### 風險

| # | 風險 | 影響 | 緩解方式 |
|---|------|------|---------|
| R1 | 選項 B 改 fixture JSON 後，與 CI 產出的真實 eval_export 順序不同（真實為正序，fixture 為逆序） | 示範性下降 | 選項 D 更徹底，但變動較大 |
| R2 | 選項 C 僅補充文檔，讀者仍可能只看 fixture 而忽略 schema 文件 | 誤導持續 | 在 fixture 附近（README）加醒目說明 |
| R3 | 選項 D 可能改變 fixture 格式或順序，進而影響僅依賴行順序的測試（雖然目前沒有） | 測試不穩定 | 先跑完整測試套件確認 |
| R4 | 目前 fixture 的 line_index 錯誤持續越久，越多人可能透過 fixture 學習 schema | 知識傳遞偏差 | 在 Wave 5 相關的開發者 onboarding 文件中標記 |
| R5 | 真實風險為「低」：沒有測試斷言，沒有 runtime bug | 決策遲緩 | 如實描述風險程度，不做不必要修復 |

### 驗收要點

| # | 驗收條件 | 如何驗證 |
|---|---------|---------|
| A1 | 至少有一個示範樣本（如 t-retry）的 `source_ref.line_index` 確實對得上 ibridge_records.jsonl 的原始行號 | 比對 eval_export_sample.jsonl line_index=2 的 t-retry 與 ibridge_records.jsonl line 2 ← ✅ 目前已成立 |
| A2 | 若選取選項 B/D，修正後 fixturer 的 `source_ref.line_index` 全部對應正確 | 逐行比對 fixturer 的 line_index 與 ibridge_records.jsonl |
| A3 | 所有現有測試在修正後仍通過（`python -m unittest tests/test_eval_exporter tests/test_eval_stats tests/test_eval_ci_check`） | 執行完整測試套件 |
| A4 | 若選項 C，schema 文件或相關 markdown 中已明確說明 fixturer 的 line_index 語義 | 讀 `eval_export_schema.md` 或 `eval_export.md` 中 `source_ref.line_index` 字段說明 |
| A5 | 若不修正（選項 C or 不做），須在 `eval_stats_report.md` 或 `README` 中記錄此已知缺口 | 搜尋文檔中的 `FIXTURE-PROVENANCE` 或 `line_index` 相關註記 |

---

## (6) 未來實作票骨架

```markdown
票名：W4-E-FIX-FIXTURE-PROVENANCE — Fixture 溯源線 index 修正
前置：W5-D-FIXTURE-PROVENANCE 方案卡（本文件）
Lane：doc-sync（僅 fixture 與文檔修正）
建議選項：B（精確修正 line_index）或 D（重新產生 fixture）

要改的檔案（依選項）：
  - tests/fixtures/eval/eval_export_sample.jsonl（選項 B/D）
  - observability/eval_export_schema.md 或 eval_export.md（選項 C）
  - artifacts/eval/shadow_eval_results.latest.jsonl（選項 B/D，可選）

允許的操作：
  - 修改 JSONL 中 source_ref.line_index 的數值（選項 B）
  - 用 export_eval_jsonl() 重新產生 fixture（選項 D）
  - 在 schema 文件或相關 markdown 中補充註釋（選項 C）

禁止事項：
  - 不改 eval_exporter.py / ibridge_exporter.py 程式碼（程式邏輯是正確的）
  - 不改測試邏輯或斷言
  - 不改 fixture 的記錄結構、schema_version、tags、gate_result
  - 不改 ibridge_records.jsonl 內容

回報要求：
  - 若選項 B：貼出 line_index 的 before/after 對照表
  - 若選項 D：貼出重新產生的命令與 stdout
  - 確認所有相關測試通過的輸出
  - 若選項 C：貼出修改的 schema 文件段落

已知限制：
  - shadow_eval_results.latest.jsonl 的 source_ref.line_index 也有偏移且有 schema 轉換（case_name→task_id），修正該檔案可能需要額外判斷
  - 目前沒有測試斷言依賴 line_index，所以無論選哪個選項都不會破壞 CI
```

---

## 附錄 A — 檔案對照速查

| 檔案 | 角色 | 行數 | 問題 |
|------|------|------|------|
| `tests/fixtures/eval/ibridge_records.jsonl` | 原始輸入 fixture | 3 | 作為參考 baseline |
| `tests/fixtures/eval/eval_export_sample.jsonl` | eval_export/v1 示範 fixture | 3 | line_index 錯誤（2/3 條偏移） |
| `tests/fixtures/eval/shadow_raw_records.jsonl` | shadow 原始輸入 fixture | 4 | 作為參考 baseline |
| `artifacts/eval/shadow_eval_results.latest.jsonl` | shadow eval_export 示例 artifact | 4 | line_index 錯誤（全 4 條偏移） |
| `tests/test_eval_exporter.py` | eval_exporter 測試 | 111 | 不斷言 fixture 的 line_index |
| `tests/test_eval_stats.py` | eval_stats 測試 | 87 | 不斷言 line_index |
| `tests/test_eval_ci_check.py` | eval_ci_check 測試 | 74 | 不斷言 line_index |
| `observability/eval_export_schema.md` (若存在) | schema 文件 | — | 可在此補充說明 |
| `artifacts/eval/smoke_eval_results.jsonl` | 等同於 eval_export_sample.jsonl | 3 | 同問題（內容相同） |

## 附錄 B — 真實風險評估

```
高風險情況（不存在）       目前實際情況（低風險）
─ ─ ─ ─ ─ ─ ─ ─         ─ ─ ─ ─ ─ ─ ─ ─
測試依賴 line_index      ✓ 無測試斷言 line_index
原始資料行號變更           ✓ 3 行 fixture 穩定不變
影響 gate 判決邏輯        ✓ line_index 不參與 gate 決策
阻礙 CI 運行             ✓ 不影響任何 CI job
```

**建議優先級**：低。本問題不阻礙 Wave 5 開發，但建議在涉及 fixture 修改的其他工作（如 CI-GAP-1 補上 CI 生產者）時一併處理。付出的修正成本極低（改 2 個數字），但能讓 fixture 可追溯性恢復一致。