# W5-D-FIXTURE-PROVENANCE_IMPLEMENTATION_TEMPLATE.md — Fixture 溯源缺口（實作票模板）

> **用途**：這份模板是給實作者（Cursor／開發者）開工用的任務卡。  
> **源頭**：`W5-D-FIXTURE-PROVENANCE_plan.md`（方案卡）→ 第 (4) 節四個選項 + 第 (5) 節風險/驗收。  
> **範圍**：僅 fixture JSONL 的 source_ref.line_index 修正 + 相關 schema 文檔補充；**不改**程式邏輯、測試斷言、或 fixture 結構。  
> **Lane 推定**：`doc-sync`（僅 fixture 與文檔修正，不動 runtime）。

---

## 1) 基本資訊

| 欄位 | 值 |
|------|-----|
| **任務名稱** | W5-D-FIXTURE-PROVENANCE-IMPLEMENTATION-01 |
| **任務說明** | 修正 eval_export_sample.jsonl（及相關 artifact/shadow 檔）中 source_ref.line_index 偏移問題，或在文檔中明確標註該偏移，讓 fixture 的溯源關係可被正確理解 |
| **主標的文件** | `tests/fixtures/eval/eval_export_sample.jsonl`（3 行，N=3） |
| **次要範圍** | `artifacts/eval/shadow_eval_results.latest.jsonl`（4 行，N=4）、`artifacts/eval/smoke_eval_results.jsonl`（3 行，N=3） |
| **參考基準** | `tests/fixtures/eval/ibridge_records.jsonl`（3 行原始輸入，N=3）、`tests/fixtures/eval/shadow_raw_records.jsonl`（4 行原始 shadow 輸入，N=4） |
| **文件範圍** | `observability/eval_export_schema.md`、`observability/eval_stats_report.md`（可選補充說明） |
| **非範圍** | `observability/eval_exporter.py`、`observability/eval_ci_check.py`、`observability/eval_stats.py`、`observability/ibridge_exporter.py`、任何測試檔案、任何 CI YAML |

### 允許的操作類型

- 修改 JSONL 中 `source_ref.line_index` 的數值（選項 B）
- 用 `export_eval_jsonl()` 重新產生整個 fixture（選項 D）
- 在 schema 文件 `eval_export_schema.md` 中補充 `source_ref.line_index` 的溯源說明（選項 C）
- 在 `eval_stats_report.md` 或 README 中記錄 Fixture-provenance 已知缺口（選項 C / 不做）
- 對 `shadow_eval_results.latest.jsonl` 執行同樣的修正策略（選項 B/D，若實作有時間）

### 不允許的操作

- **不改任何 Python 程式碼**（`eval_exporter.py`、`ibridge_exporter.py`、`eval_ci_check.py`、`eval_stats.py` — 程式邏輯是正確的）
- **不改測試邏輯或測試斷言**（測試目前已 pass 且不依賴 line_index）
- **不改 fixture 的記錄結構**（schema_version、tags、gate_result、reasons、metrics 等非 line_index 欄位）
- **不改 fixture 的記錄順序**（目前是反序：t-infra → t-retry → t-healthy；選項 D 重新產生後會變正序：t-healthy → t-retry → t-infra，這是可接受的例外）
- **不改 `ibridge_records.jsonl` 或 `shadow_raw_records.jsonl`**（它們是參考 baseline，不是修正目標）
- **不改檔名或目錄結構**
- **不大規模重構 fixture 結構**（不在本次增加/刪除記錄）

---

## 2) 前提與不變條件

### 實作前須成立

- [ ] `tests/fixtures/eval/ibridge_records.jsonl` 存在且 3 行內容穩定
- [ ] `tests/fixtures/eval/eval_export_sample.jsonl` 存在且 3 行的 line_index 錯誤已確認（t-infra line_index=1 → 應為 3，t-healthy line_index=3 → 應為 1）
- [ ] `tests/fixtures/eval/shadow_raw_records.jsonl` 存在且 4 行內容穩定
- [ ] `artifacts/eval/shadow_eval_results.latest.jsonl` 的 4 行全部 line_index 偏移已確認（1→4, 2→3, 3→2, 4→1）
- [ ] 所有相關測試（`test_eval_exporter`、`test_eval_stats`、`test_eval_ci_check`）在當前狀態下全部 pass → 以便修正後可對比
- [ ] 實作者理解：沒有任何測試斷言依賴 fixture 的 line_index（修正後測試結果應完全一致）

### 不得改動的事項（不變條件）

1. **不改程式邏輯**：`iter_records()`、`build_export_line()`、`export_eval_jsonl()` 的 line_index 生成方式正確。fixture 的錯誤是 fixture 建立時的人為疏忽，不是程式 bug。
2. **不改測試斷言**：所有斷言目前 pass，修正後也應 pass。不因 line_index 修正而增加新的測試斷言。
3. **不改 fixture 的業務欄位**：`gate_result`、`tags`、`reasons`、`metrics`、`schema_version` 等在修正中保持不變。
4. **不改實體檔案數量**：不新增或刪除 fixture 檔案，不移動目錄。
5. **不要為了「絕對正確」而擴大範圍**：本問題風險評級為「低」，不要為了追求 ideal fixture 而引入過多變更（如重構測試架構、重寫 fixture 產生腳本等）。

---

## 3) 具體步驟（實作 checklist）

以下步驟以 **選項 B（精確修正 line_index）為主要路線，輔以選項 C（文檔補充）** 作為組合。實作者若決定選 D 或純 C，請跳到每個步驟末尾的「若選 D/C 差異」標記。

### Step 1 — 確認參考基準與 fixture 的逐行對應

| 項 | 內容 |
|---|------|
| **做什麼** | 用一個簡單的擷取腳本（在 workspace 執行，不修改 repo）確認以下對應關係： |
| | (1) 讀 `ibridge_records.jsonl` 的 3 行，記錄每行的 task_id（或第一筆字段） |
| | (2) 讀 `eval_export_sample.jsonl` 的 3 行，比對 source_ref.task_id 與參考基準的行號對應 |
| | (3) 記錄正確的 `line_index` 值（t-infra=3、t-retry=2、t-healthy=1） |
| | (4) 同樣方法確認 `shadow_eval_results.latest.jsonl` 的 4 行對應關係 |
| **輸出** | 一個對照表記錄在回報中：**
| | eval_export_sample line 1 (t-infra): line_index 1 → 3 ✅（ibridge_records 第 3 行） |
| | eval_export_sample line 2 (t-retry): line_index 2 → 2 ✅（ibridge_records 第 2 行） |
| | eval_export_sample line 3 (t-healthy): line_index 3 → 1 ✅（ibridge_records 第 1 行） |
| **若選 D** | 不需要做逐行對應，因為會直接重新產生。但為了回報中的 before/after 對比，仍建議記錄現狀。 |
| **若選 C** | 也需要確認對應關係，以便在 schema 文件中寫出正確的說明。 |

### Step 2 — 修正 eval_export_sample.jsonl 的 line_index（選項 B 核心）

| 項 | 內容 |
|---|------|
| **目標文件** | `tests/fixtures/eval/eval_export_sample.jsonl` |
| **做什麼** | 修改該 JSONL 中兩條記錄的 `source_ref.line_index`： |
| | - 第 1 行（t-infra）：`"line_index": 1` → `"line_index": 3` |
| | - 第 3 行（t-healthy）：`"line_index": 3` → `"line_index": 1` |
| | 第 2 行（t-retry）「line_index=2」不變（原本就是對的）。 |
| **注意** | (1) 只改 `source_ref` 區塊內的 `line_index`，不改其他 key/值 |
| | (2) 不變改 JSON 的格式或縮排（但 JSONL 內單行 JSON 不應有縮排） |
| | (3) 修改後再次執行 `python -m json.tool` 確認 JSONL 仍合法 |
| **若選 D** | 跳過此步驟，見 Step 5。 |
| **若選 C** | 跳過此步驟，見 Step 4。 |

### Step 3 — 可選修正 shadow_eval_results.latest.jsonl 的 line_index

| 項 | 內容 |
|---|------|
| **目標文件** | `artifacts/eval/shadow_eval_results.latest.jsonl` |
| **做什麼** | 修正該檔案中 4 條記錄的 `source_ref.line_index`： |
| | - 第 1 行（shadow-retry）：`line_index: 1` → `line_index: 4` |
| | - 第 2 行（shadow-greeting）：`line_index: 2` → `line_index: 3` |
| | - 第 3 行（shadow-merge-2）：`line_index: 3` → `line_index: 2` |
| | - 第 4 行（shadow-k2-flow-1）：`line_index: 4` → `line_index: 1` |
| **注意** | (1) 這個檔案的 line_index 偏移更複雜：shadow_raw_records 的最後兩行（shadow-greeting、shadow-retry）在 ibridge_exporter 處理時從 `case_name` 轉為 `task_id`，schema 不同。因此即使 line_index 修正後，也不是 1:1 可追蹤到 shadow_raw_records 的「同一個記錄」，只能追蹤到 ibridge 格式轉換後的行號。 |
| | (2) 如果修正這個檔案，應在文件（schema 或 README）中標明這個「schema 轉換」的前後關係。 |
| | (3) 如果時間不足或有疑慮，可以**暫不修正**此檔案，僅在回報中記錄偏移現狀。 |
| **若選 D** | 用 `export_eval_jsonl()` 重新產生時，shadow 的輸入是 `shadow_raw_records.jsonl`？還是 `ibridge_records.jsonl`？方案卡寫的是「在一個隔離的工作空間內執行 export_eval_jsonl(ibridge_records.jsonl)」，所以 shadow 檔案不在選項 D 的自動覆蓋範圍內。需要手動處理（同選項 B 的方法）。 |
| **若選 C** | 僅在文檔中記錄此偏移，不修改 JSON。 |

### Step 4 — 在 schema 文檔中補充 line_index 說明（選項 C 核心，或作為選項 B/D 的補充）

| 項 | 內容 |
|---|------|
| **目標文件** | `observability/eval_export_schema.md`（若存在，主要目標） |
| | `observability/eval_stats_report.md` §Limitations（可選） |
| **做什麼** | 在 `eval_export_schema.md` 的 `source_ref.line_index` 字段說明處補充／強化溯源語義： |
| | (1) 說明 `line_index` 指的是**輸入檔案中的行號**（從 1 開始），而非匯出檔自身的行號 |
| | (2) 如果選項 B 已執行：補充一則「fixture 的 line_index 已修正為正確值」 |
| | (3) 如果選項 C 僅文檔不修正：補充「fixture 中此欄位為匯出檔行號而非原始檔案行號，請以 ibridge_records.jsonl 為參考基準」 |
| | (4) 如果 shadow 檔案未修正：在 schema 中補充註明 shadow_eval_results.latest.jsonl 的 line_index 偏移已確認，且因 schema 轉換（case_name→task_id）無法 1:1 溯源 |
| **若選 D** | 同樣建議執行此步驟，因為選項 D 重新產生的 fixture 是基於 ibridge_records.jsonl，不含 shadow 檔案。shadow 的偏移仍需在文檔中說明。 |

### Step 5 — 若選 D：用 export_eval_jsonl 重新產生 eval_export_sample.jsonl

| 項 | 內容 |
|---|------|
| **目標文件** | `tests/fixtures/eval/eval_export_sample.jsonl`（覆蓋寫入） |
| **做什麼** | (1) 在 workspace 內執行 `python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl -o /tmp/eval_export_regenerated.jsonl` |
| | (2) 確認輸出結果：3 行，正序（t-healthy → t-retry → t-infra），line_index 分別為 1、2、3 |
| | (3) 對比新輸出與現有 fixture 的差異：僅 line_index 值和順序不同，gate_result/tags/metrics 等業務欄位應一致 |
| | (4) 將 `/tmp/eval_export_regenerated.jsonl` 複製到 `tests/fixtures/eval/eval_export_sample.jsonl` |
| **注意** | (1) 新檔案的記錄順序是相反的（正序 vs 現有反序），這是選項 D 最大的變動。確認沒有任何測試依賴記錄順序。 |
| | (2) 執行 `python -m unittest tests.test_eval_exporter tests.test_eval_stats tests.test_eval_ci_check` 確認全部 pass。如果任何測試失敗，檢查是否無意中依賴了行順序。 |
| **若選 B** | 跳過此步驟。 |
| **若選 C** | 跳過此步驟。 |

### Step 6 — 在 eval_stats_report.md 中記錄 Fixture-Provenance 狀態

| 項 | 內容 |
|---|------|
| **目標文件** | `observability/eval_stats_report.md` |
| **做什麼** | 在 §Limitations 中明確記錄： |
| | (1) Fixtures 的 source_ref.line_index 已修正／或已知偏移 |
| | (2) shadow_eval_results.latest.jsonl 的 schema 轉換（case_name→task_id）對溯源的影響 |
| | (3) 實作者選擇的修正策略（B/C/D）與未修正的殘留項 |
| **注意** | 這一步是選項 C 的核心，對選項 B/D 也是「nice to have」的補充。如果時間有限，可以跳過，但建議至少在回報中記錄。 |

### Step 7 — 跑測試確認全部通過

| 項 | 內容 |
|---|------|
| **做什麼** | 執行完整的相關測試套件： |
| | `python -m unittest tests.test_eval_exporter tests.test_eval_stats tests.test_eval_ci_check` |
| | 輸出應與修正前完全一致（因為沒有任何測試斷言依賴 line_index）。 |
| **預期結果** | 全部 pass，輸出與修正前相同。 |
| **若選 D** | 同上，但應特別注意 `test_eval_stats` 中是否有與 group_by / order 相關的斷言受到記錄順序變動的影響。如果有，應在回報中記錄（但不修改測試）。 |

---

## 4) 風險與注意事項

### 實作端須留意清單

| # | 風險 | 注意事項 |
|---|------|---------|
| **R1** | **選項 B 只改了 2 個數字，但 JSONL 編輯必須確保不破壞 JSON 結構** | 不要用 `sed` 或簡單的字串取代來改 JSONL — line_index 值可能與其他數字重疊。較安全的方式是用 `json.loads` → 修改 → `json.dumps` 輸出（在 workspace 隔離環境執行），或手動確認搜尋的上下文（如 `"line_index": 1` 而非 `line_index: 1`）。 |
| **R2** | **shadow_eval_results.latest.jsonl 有 schema 轉換（case_name→task_id）** | 即使 line_index 修正了，也無法透過 line_index 反向 1:1 追蹤到 shadow_raw_records 的原始記錄（因為 ibridge_exporter 在轉換時重新分配了 task_id）。修正 line_index 只能保證「匯出檔行號」與「ibridge 中間格式行號」一致，不等於「能溯源到 raw records」。在回報中應明確說明此限制。 |
| **R3** | **選項 D 會改變 fixture 的記錄順序** | 目前 fixture 是反序（t-infra → t-retry → t-healthy），選項 D 重新產出的是正序（t-healthy → t-retry → t-infra）。雖然目前沒有測試依賴順序，但團隊成員可能習慣了 fixture 現有順序。如果選擇 D，應在 commit message 中明確提醒此變動。 |
| **R4** | **不要為了「絕對正確」而擴大範圍** | 本問題風險評級為「低」（無測試依賴、無 runtime 影響、不影響 CI）。如果修正過程發現了其他 fixture 問題（如與 schema 不一致的字段），應記錄在回報中的「已知殘留」而非順手修正。開新票處理。 |
| **R5** | **smoke_eval_results.jsonl（artifacts/eval/）的內容與 eval_export_sample.jsonl 相同** | 目前 `artifacts/eval/smoke_eval_results.jsonl` 的 3 行內容與 `tests/fixtures/eval/eval_export_sample.jsonl` 完全一致。如果是因為複製產生的，應考慮是否一併修正。但這屬於 artifact 而非 fixture，變更邊界視實作者的判斷。建議在回報中記錄而不強制修正。 |
| **R6** | **schema 文件的範例可能也用了錯誤的 line_index 值** | `eval_export_schema.md` 第 71 行的範例中 `line_index: 3` 只是一個示範值，不來自真實 fixture。但如果實作者發現這個值與修正後的 fixture 有衝突（如讀者會以為 fixture 的某行對應此 line_index），可在 schema 文檔中調整範例值或補充說明。 |

### 通用原則

- **這是一個低風險 cleanup，不要在修正中引入過多變更。** 如果發現還有其他小問題，在回報中記錄，不順手修復。
- **所有 JSONL 編輯應先備份原檔案**（或在 git branch 中做），確保可以快速恢復。
- **shadow 檔案的修正可以選擇「不做」**，但必須在回報中記錄為何跳過（如時間不足、schema 轉換增加複雜度）。
- **測試結果必須與修正前完全一致**。如果測試失敗，一定是因為非 line_index 的變動產生了 side-effect，請立即回退。

---

## 5) 驗收條件

實作者完成選定路線後，逐項檢查並填入結果。

| # | 驗收條件 | 如何驗證 | 實測結果 |
|---|---------|---------|---------|
| AC1 | 修正後，`eval_export_sample.jsonl` 中至少 t-retry 的 `source_ref.line_index` 對得上 `ibridge_records.jsonl` 的同名 task_id 行號 | 比對 t-retry 的 line_index=2 ↔ ibridge_records 第 2 行（原本就是對的） | |
| AC2 | 若選 B/D：`eval_export_sample.jsonl` 的 `source_ref.line_index` 全部正確對應 ibridge_records.jsonl（t-infra=3、t-retry=2、t-healthy=1） | 逐行比對 JSONL 的 line_index 與 ibridge_records 的行號 | |
| AC3 | 若選 C：`eval_export_schema.md` 或相關 schema 文件中已補充 `source_ref.line_index` 的溯源說明 | 讀 schema 文件中 `line_index` 字段描述，確認有 fixture provenance 的說明 | |
| AC4 | 所有相關測試（`test_eval_exporter`、`test_eval_stats`、`test_eval_ci_check`）全部通過 | `python -m unittest tests.test_eval_exporter tests.test_eval_stats tests.test_eval_ci_check` 回傳 OK | |
| AC5 | 測試結果與修正前一致（輸出相同） | 將 fixture 修正前後的測試輸出對比（可用 git stash / branch 對比） | |
| AC6 | 若選 B/D：eval_export_sample.jsonl 的 JSONL 格式仍合法 | `head -1 tests/fixtures/eval/eval_export_sample.jsonl \| python -m json.tool` 成功 | |
| AC7 | `eval_stats_report.md` 的 §Limitations 中已記錄 fixture provenance 狀態（修正策略 + 殘留項） | 讀取 `eval_stats_report.md` Limitations 節 | |
| AC8 | 未修改任何 Python 程式、測試斷言、CI YAML、或其他非授權檔案 | `git diff --stat` 或等效確認僅限 fixture JSONL + schema markdown | |

---

## 6) 回報格式模板

實作者完成後，按以下框架填寫回報。貼在實作票的 comment 或 Workspace 戰報中。

```markdown
### 實作回報 — W5-D-FIXTURE-PROVENANCE-IMPLEMENTATION-01

**實作日期**：YYYY-MM-DD
**實作者**：<role>
**選擇策略**：選項 B（line_index 精確修正） / 選項 C（僅文檔補充） / 選項 D（重新產生 fixture）
**是否同時處理 shadow_eval_results.latest.jsonl**：是 / 否

#### 修改檔案清單

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `tests/fixtures/eval/eval_export_sample.jsonl` | line_index 修正 / 重新產生 / 不修改 | 簡述變更範圍 |
| `observability/eval_export_schema.md` | 補充說明 / 不修改 | |
| `artifacts/eval/shadow_eval_results.latest.jsonl` | line_index 修正 / 不修改 | |
| `observability/eval_stats_report.md` | 補充說明 / 不修改 | |

#### Fixture line_index 修前/修後對照

| 記錄 | 匯出檔行 | 修前 line_index | 修後 line_index | ibridge_records 實際行 | 匹配？ |
|------|---------|----------------|----------------|-----------------------|--------|
| t-infra | 1 | 1 | 3 | 3 | ✅ |
| t-retry | 2 | 2 | 2 | 2 | ✅（不變） |
| t-healthy | 3 | 3 | 1 | 1 | ✅ |

#### Shadow 檔案處理情況

| 記錄 | 匯出檔行 | 原始 line_index | 修正後 line_index | 說明 |
|------|---------|----------------|------------------|------|
| shadow-retry | 1 | 1 | 4 | 已修正 |
| shadow-greeting | 2 | 2 | 3 | 已修正（但 schema 轉換 case_name→task_id，非 1:1 溯源） |
| shadow-merge-2 | 3 | 3 | 2 | 已修正 |
| shadow-k2-flow-1 | 4 | 4 | 1 | 已修正 |

#### 測試結果

```
$ python -m unittest tests.test_eval_exporter tests.test_eval_stats tests.test_eval_ci_check -v
...
<貼上測試輸出>
...
OK (pass/fail counts)
```

#### 驗收條件檢查

| # | 通過？ | 備註 |
|---|-------|------|
| AC1 | [ ] | |
| AC2 | [ ] | |
| AC3 | [ ] | |
| AC4 | [ ] | |
| AC5 | [ ] | 修正前後的測試輸出一致？ |
| AC6 | [ ] | JSONL 格式合法？ |
| AC7 | [ ] | |
| AC8 | [ ] | `git diff --stat` 結果： |

#### 已知殘留

- 列舉驗收條件中未完全通過的項及原因
- 列舉未處理的相關問題（如 shadow 檔案未修正、smoke_eval_results.jsonl 有相同問題等）
- 列舉實作過程發現的、但不屬於本票範圍的擴充發現
```

---

## Extra Notes for Implementer

### 路線選擇建議

**優先選項 B + C 組合**。原因：

- **選項 B**（改 2 個數字）是最低成本的精確修正：只改 eval_export_sample.jsonl 中 t-infra 和 t-healthy 的 line_index 值。全部變更不到 5 秒鐘的編輯作業，不改變 fixture 結構或順序，測試一如既往全部通過。
- **選項 C**（文檔補充）作為 B 的補充：在 schema 文件中強化 `source_ref.line_index` 的語義說明，並在 Limitations 中記錄 shadow 的殘留偏移。讓讀者從文檔層面清楚 fixture 的溯源關係。
- **不建議純選項 C**（僅文檔不改 fixture）：因為修正成本極低（2 個數字），純選 C 等同於保留一個已知的、可輕易修正的資訊錯誤。
- **選項 D**（重新產生）的適合時機：當你對 fixture 的「正序 vs 反序」不在意，且想要一個可複現的產生命令。但 D 會改變記錄順序，可能讓習慣現有 fixture 順序的團隊成員需要重新適應。如果選擇 D，請在 commit 中明確說明順序變動。

### shadow_eval_results.latest.jsonl 的處理建議

這個檔案的處理比較「建議做但不做也可以」：
- 它的 line_index 偏移更嚴重（4 條全部偏移），且多了一層 schema 轉換（case_name→task_id），使得 line_index 即使修正也不是完美的 1:1 溯源。
- 如果時間允許，建議和 eval_export_sample.jsonl 一併修正（同樣是改數字）。但必須在文檔中額外說明 schema 轉換的限制。
- 如果時間有限或擔心 schema 轉換的複雜度，可以跳過 shadow 檔案的修正，只在 schema 文檔中記錄偏移事實。

### 關於 smoke_eval_results.jsonl

`artifacts/eval/smoke_eval_results.jsonl` 的內容與 `eval_export_sample.jsonl` 完全相同（3 行，同一份資料）。目前不強制修正此檔案（屬於 artifact 目錄而非 fixture 目錄）。但如果順手的話，可以一併修正。在回報的「已知殘留」中記錄即可。

### 關於工具選擇

因為本票只改 JSONL 中的 2~4 個數字，可以直接用編輯器修改。不建議用程式化的批量重寫（除非選 D。不建議用 sed，因為 `line_index: 1` 可能與其他 JSON key 或 value 中的 `1` 字串重疊。最安全的方式是用編輯器的 find/replace 定位到 `"source_ref": { ... "line_index": 1 ... }` 這段上下文。
```
