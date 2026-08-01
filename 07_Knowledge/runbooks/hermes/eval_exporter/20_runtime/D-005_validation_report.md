# D-005 Validation Report — _context_tokens_total vs _total_context_tokens

> 本報告為 D-005-VALIDATION-01 只讀驗證的成果物。
> 所有結論來自靜態原始碼比對，無 runtime 測試。

---

## 1. 比對對象清單

### 直接比對（core D-005）

| 函式 | 檔案 | 行號 | 型別 |
|------|------|------|------|
| `_context_tokens_total` | `observability/eval_exporter.py` | 35–43 | private helper |
| `_total_context_tokens` | `observability/eval_gate.py` | 108–128 | private helper |

### 間接相關（相同領域但不同 key/邏輯）

| 函式/位置 | 檔案 | 行號 | 萃取鍵 |
|-----------|------|------|--------|
| `build_internal_data_frame` token 萃取 | `core/context_entry.py` | 662–668 | `token_usage.get("total_tokens") or token_usage.get("total")` |
| k2 流程 token 萃取 | `core/langgraph_flow_k2.py` | 194–195 | 同上 |
| k1 流程 token 萃取 (1) | `core/langgraph_flow_k1.py` | 202 | 同上 |
| k1 流程 token 萃取 (2) | `core/langgraph_flow_k1.py` | 212–213 | 同上 |
| ibridge_exporter fallback | `observability/ibridge_exporter.py` | 246, 291 | `{"total_tokens": 0}`（預設值注入） |

---

## 2. 逐行比對結果

### 2.1 `eval_exporter._context_tokens_total` (L35–43)

```python
def _context_tokens_total(record: dict[str, Any]) -> int:
    usage = record.get("context_token_usage")
    if not isinstance(usage, dict):
        return 0
    raw = usage.get("total_tokens", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0
```

### 2.2 `eval_gate._total_context_tokens` (L108–128)

```python
def _total_context_tokens(record: dict[str, Any]) -> int:
    """...此函數與 eval_exporter.py 中的 _context_tokens_total 邏輯相同（見 DEBT_LOG D-005）。..."""
    usage = record.get("context_token_usage")
    if not isinstance(usage, dict):
        return 0
    raw = usage.get("total_tokens", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0
```

### 2.3 比對結論

| 維度 | 結果 | 說明 |
|------|------|------|
| **函式簽章** | 完全相同 | 均為 `(record: dict[str, Any]) -> int` |
| **萃取 key** | 完全相同 | `record["context_token_usage"]["total_tokens"]` |
| **型別守衛** | 完全相同 | `isinstance(usage, dict)` |
| **預設值** | 完全相同 | `.get("total_tokens", 0)` |
| **例外處理** | 完全相同 | `try: int(raw) except (TypeError, ValueError): return 0` |
| **回傳值** | 完全相同 | `int`（轉換失敗時 `0`） |
| **docstring** | 不同 | eval_exporter：無 docstring；eval_gate：有中文 docstring 且包含 D-005 註解 |
| **函式名稱** | 不同 | `_context_tokens_total` vs `_total_context_tokens` |

**逐行 diff：0 行差異。** 函式體（不含 docstring）完全一致。

---

## 3. 被呼叫的位置

| 函式 | 被誰呼叫 | 使用方式 |
|------|---------|----------|
| `_context_tokens_total` | `eval_exporter.summarize_metrics` (L64) | 寫入 `eval_export/v1` 的 `metrics.context_tokens_total` 欄位 |
| `_total_context_tokens` | `eval_gate._rule_context_heavy` (L198) | 與 `CONTEXT_HEAVY_TOKEN_THRESHOLD` (102,400) 比較，觸發 `context_heavy` tag |

**重要觀察**：這兩個函式的**結果最終會在同一個 call chain 中被同時看到**。當 `eval_exporter.export_eval_jsonl` 被呼叫時，`build_export_line` 內部會：
1. 呼叫 `evaluate_task_record(record)` → 走 `_total_context_tokens`（決定 `gate_result` 與 `tags`）
2. 呼叫 `summarize_metrics(record)` → 走 `_context_tokens_total`（決定 `metrics.context_tokens_total`）

所以同一個 record 經過同樣的 pipeline，用了兩個完全相同的函式來讀取同一個欄位——但各有一份獨立的程式碼。

---

## 4. 對維護與風險的實際影響

| 風險 | 影響程度 | 情境 |
|------|---------|------|
| **不一致的雙重維護** | 中 | 若未來改成 `usage.get("total")` fallback（像 core/ 的做法），或改成支援 `usage.get("completion_tokens") + usage.get("prompt_tokens")`，需要同時改 2 處。忘記改一處會導致同一個 record 的 `context_heavy` gate 結果與 JSONL 輸出的 `context_tokens_total` 不一致。 |
| **新增第三處的慣性** | 中 | 如果將來要加 `metrics` 模組的 token 統計或 dashboard 聚合，發現已經有兩個函式做同一件事，新開發者可能再 copy-paste 一個或多 import 其中一處，導致混亂。 |
| **重構風險** | 低 | 這兩個函式都是 private helper（`_` 前綴），不是公共 API。但因為跨檔案使用，export 層級的依賴傳播需要確認 import 路徑。 |
| **當前功能正確性** | 無影響 | 目前兩處邏輯完全相同，無運行時問題。D-005 是維護性 debt，非功能 bug。 |

---

## 5. 間接相關 token 萃取（core/ 模組）

比對中發現 `core/context_entry.py`, `core/langgraph_flow_k1.py`, `core/langgraph_flow_k2.py` 還有另一組 token 萃取邏輯：

```python
# core/context_entry.py:662
total = int(usage.get("total_tokens") or usage.get("total") or 0)
```

這組與 D-005 的函式**操作不同鍵路徑**：
- D-005 系列：`record["context_token_usage"]["total_tokens"]`
- core 系列：`token_usage.get("total_tokens") or token_usage.get("total") or 0`

這兩個路徑是**不同的資料來源**（一個是 metrics/ibridge 層的 `context_token_usage`，一個是 runtime 層的 `token_usage`）。**不建議將它們視為同一筆 debt。** 但值得記錄為「觀察項」——如果未來 refactor 將 token 資料結構統一，核心函式可以共用。

---

## 6. 結論

> **D-005 確認是一組 100% 相同邏輯的跨檔案重複。**
>
> 逐行 diff = 0 差異（不含 docstring）。兩個函式完全一致，且在同一 call chain 中被用於同一個 record 的不同欄位產出。這不是「只是相似」，是確定的邏輯拷貝。
>
> **建議將 D-005 從 NEW_CANDIDATE 升級為 VALIDATED_CANDIDATE。**

---

## 7. D-005 修復風險評級

| 項目 | 評級 | 說明 |
|------|------|------|
| 修復緊急性 | 低 | 非功能 bug，當前無運行時錯誤 |
| 修復難度 | 低 | 建立一個 6 行共用函式，在兩個模組改 import |
| 修復風險 | 低 | 私有函式 + 純字面比對 + 已有 unittest 保護 |
| 累積影響 | 中 | 若不及早統一，可能隨 mod 擴張出現第三、第四處 |

**不建議立即實作**的合理原因：目前無使用上的痛點，兩個函式各自穩定且測試覆蓋。修復的好處是長期維護性。建議將實作順序排在「近期有空」而非「緊急 P0」。
