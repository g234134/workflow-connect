# PLAYBOOK — eval_exporter 修復方案草案

> 基於 D-005-VALIDATION-01 結果撰寫。本文件僅提出修復方案草案，**非實作合約**。
> 所有小票需經審查後才能執行。

---

## 前提

D-005 已通過 VALIDATED_CANDIDATE：`eval_exporter._context_tokens_total` 與 `eval_gate._total_context_tokens` 為 100% 相同邏輯的跨檔案拷貝。修復目標是將共用的 context token total 萃取邏輯統一至單一位置，消除未來因不同步維護導致的產出不一致風險。

**修復緊急性**：低（無運行時 bug）
**修復難度**：低（~6 行純函式 + 2 處 import 替換）
**修復風險**：低（private helper + 已有 unittest 保護）

---

## 建議小票清單

### 票 1：建立共用層 `observability/_eval_utils.py`

| 項目 | 內容 |
|------|------|
| **範圍** | 新增 `observability/_eval_utils.py` |
| **內容** | 定義 `safe_token_total(record: dict[str, Any]) -> int`，邏輯完全複製目前 `_context_tokens_total` / `_total_context_tokens` 的實作 |
| **測試** | 在 `tests/test_eval_gate.py` 或獨立 `tests/test_eval_utils.py` 補測試：正常 dict → 回傳 int、`context_token_usage` 不存在 → 回傳 0、`total_tokens` 非 int → 回傳 0 |
| **出口** | `__all__ = ["safe_token_total"]` |
| **依賴** | 無 |
| **風險** | 新增檔案需確認 `observability/` 的 import lint 與 `__init__.py` 是否需更新 |

### 票 2：替換 eval_exporter 中的 `_context_tokens_total`

| 項目 | 內容 |
|------|------|
| **範圍** | 修改 `observability/eval_exporter.py` |
| **操作** | 在檔案頂部加入 `from observability._eval_utils import safe_token_total`；將 `_context_tokens_total` 函式替換為對 `safe_token_total` 的單行委派，或直接刪除原始函式並在 `summarize_metrics` 中呼叫 `safe_token_total` |
| **測試** | `tests/test_eval_exporter.py` 現有 6 個 test 應全部通過（邏輯不變） |
| **風險** | 若選擇「在檔案內保留 function 並委派」，則是保守路線；若選擇「刪除原始函式並改呼叫處」，則是激進路線。建議第一版走保守路線（保留 function 殼委派），下一輪再清理 |

### 票 3：替換 eval_gate 中的 `_total_context_tokens`

| 項目 | 內容 |
|------|------|
| **範圍** | 修改 `observability/eval_gate.py` |
| **操作** | 在檔案頂部加入 `from observability._eval_utils import safe_token_total`；將 `_total_context_tokens` 函式替換為對 `safe_token_total` 的委派 |
| **更新註解** | 刪除 `_total_context_tokens` docstring 中的「此函數與 eval_exporter.py 中的 _context_tokens_total 邏輯相同（見 DEBT_LOG D-005）」註解，改為 `# 已統一：safe_token_total` |
| **測試** | `tests/test_eval_gate.py` 現有測試應全部通過 |

### 票 4（可選）：清理過渡期的函式殼

| 項目 | 內容 |
|------|------|
| **範圍** | 修改 `observability/eval_exporter.py` 和 `observability/eval_gate.py` |
| **操作** | 刪除票 2、3 中保留的委派函式（`_context_tokens_total`、`_total_context_tokens`），直接改寫呼叫處（`summarize_metrics` 和 `_rule_context_heavy`）為 `safe_token_total()` |
| **前提** | 票 1–3 已合併且運行一輪正常 |
| **風險** | 最低，但不做也無影響 |

---

## 實作順序建議

```
票 1 (建立) → 票 2 (exporter 替換) → 票 3 (gate 替換) → [可選] 票 4 (清理)
```

無並行依賴；票 2 和 3 可以交換順序，因為各自獨立 import 共用函式。

---

## 不建議的修復路線

| 路線 | 理由 |
|------|------|
| 將 token 萃取邏輯放到 `contract/constants.py` | 邏輯不是常量，是運算函式；放入 contract 層違反分層 |
| 合併 eval_exporter 和 eval_gate | 兩者職責不同，token 萃取只是它們的小部分功能 |
| 同時「統一 D-005 + 統一 core/ 的 token 萃取」 | core/ 的 token 萃取操作不同鍵路徑（`token_usage` vs `context_token_usage`）且有 `total` fallback，不屬於同一 debt。應分開處理 |

---

## 對 core/ token 萃取的觀察（非 D-005）

本次驗證中發現 `core/context_entry.py`、`core/langgraph_flow_k1.py`、`core/langgraph_flow_k2.py` 還有另一組 token 萃取：

```python
total = int(usage.get("total_tokens") or usage.get("total") or 0)
```

這組與 D-005 的函式操作**不同鍵名稱**（`token_usage` vs `context_token_usage`）且有 `total` fallback。**不建議放入本次 D-005 修復範圍。** 若未來重構將 token 資料結構統一，可開新的 debt ticket 跟蹤。
