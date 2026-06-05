eval_gate Code Review — 2026-05-30

審查範圍
--------

檔案: 評分閘主體  
路徑: observability/eval_gate.py  
行數: 155  
角色: 任務紀錄評分入口  

────────────────────────────────────────
檔案: trace 生命週期  
路徑: observability/logging_adapter.py  
行數: 579  
角色: trace/span 模型，產出 eval_gate 的輸入 record  

────────────────────────────────────────
檔案: token 預算定義  
路徑: context/context_builder.py  
行數: 395  
角色: 定義 eval_gate 重複引用的 token 上限常數  

────────────────────────────────────────
檔案: 指標收集器  
路徑: metrics/metrics_collector.py  
行數: 383  
角色: record 實體的最終組裝者（end_task）  

────────────────────────────────────────
檔案: 現有單元測試  
路徑: tests/test_eval_gate.py  
行數: 93  
角色: 僅測人工構造的 _healthy_record()，未測真實 trace 輸出  

────────────────────────────────────────
檔案: 現有單元測試  
路徑: tests/test_logging_adapter.py  
行數: 68  
角色: 僅測 trace lifecycle 正確性，未將 record 餵進 eval_gate  


發現的問題
----------

### P0 — 必須修復，否則 prod 會發生不可偵測的誤判

**P0-1: token 上限常數重複定義（DRY 違反 + 隱性耦合）**

- eval_gate.py:12: `MAX_TOTAL_TOKEN_BUDGET = 128_000`  
- context/context_builder.py:21: `MAX_TOTAL_TOKEN_BUDGET = 128_000`  
- 註解寫「not imported to avoid cross-layer coupling」，但這造成了 cross-layer drift：兩邊獨立修改時不會互相報錯。  
- 若有人在 context_builder 將上限調成 200_000，eval_gate 的 context_heavy 規則仍用舊值 128_000 的 80%（= 102,400），導致該規則比預期更容易觸發。  
- 建議：抽出 `contract/constants.py` 或直接在 eval_gate `from context.context_builder import MAX_TOTAL_TOKEN_BUDGET`。

  **處理狀態（2026-05-30）：**
  已新增 `contract/constants.py`，`MAX_TOTAL_TOKEN_BUDGET = 128_000` 僅在此定義。
  `context/context_builder.py` 與 `observability/eval_gate.py` 均已改為
  `from contract.constants import MAX_TOTAL_TOKEN_BUDGET`（含 re-export 路徑
  `context/__init__.py`）。`tests/test_eval_gate_contract.py` 13/13 PASS。

---

### P1 — 會在特定邊界條件下造成行為錯誤

**P1-1: 輸入 record 缺少 schema 驗證，畸型 dict 靜默通過**

- `evaluate_task_record` 只檢查 `isinstance(record, dict)`（第 132 行）。  
- 五條規則的 helper function（`_int_field`, `_float_field`, `_total_context_tokens`）全部有 silent default：欄位不存在或型別錯誤時返回 0 / 1.0 / None。  
- 實例：若 `logging_adapter.end_trace` 因 bug 未寫入 `context_token_usage`，`eval_gate` 的 `_total_context_tokens` 返回 0 → 不會觸發 `context_heavy` → 該記錄通過。  
- 建議：在 L132 的 dict 檢查後，加入最小 schema 驗證（至少有 `success` 為 bool、`retry_count` 為 int），不合法者標記 `"malformed_record"`。

  **處理狀態（2026-05-30）：**
  已實作 `_collect_schema_issues()` helper，強制檢查三個必備欄位：
  `success: bool`、`retry_count: int`、`handoff_count: int`。
  任一缺失或型別錯誤 → 短路回傳 fail，tag 為 `"malformed_record"`，
  reasons 枚舉每個問題。empty dict 不再沉默通過。
  測試：`test_empty_dict_record_fails_malformed`、
  `test_missing_success_field_malformed`、
  `test_retry_count_wrong_type_malformed`。全部 PASS。

**P1-2: `trace_completeness` 為 None 時 `_float_field` 返回 default 1.0，掩蓋真實的觀測缺口**

- `_rule_observability_gap`（L104-111）用 `_float_field(record, ("trace_completeness", "score"), default=1.0)`。  
- 若 `trace_completeness` 欄位為 None（不是 dict），`_float_field` 的 `isinstance(node, dict)` 檢查失敗，返回 default 1.0 → `>= 0.8` → 不觸發。  
- 此時的語意是「完全沒有 trace_completeness 資料」卻被判成「完整度 100%」。  
- 建議：`_float_field` 在遇到非 dict 的 intermediate node 時，不僅返回 default，也應有 logging 或至少讓 `_rule_observability_gap` 區分「值低」與「值缺失」。  

**P1-3: `retry_count` / `handoff_count` 透過 log_metric 的 flush 機制有數據丟失風險**

- `log_metric("retry_count", ...)` 並非直接寫入 collector，而是暫存在 `ctx.custom_metrics`，等到 `end_trace` 時才 flush（logging_adapter.py L181-187）。  
- 若 `end_trace` 之前拋出未捕獲異常（context manager 的 except 分支走了 `raise`），flush 不會發生。  
- 這意味著 `eval_gate` 會看到 `retry_count=0`，但實際上可能有重試行為未被記錄。  
- 建議：`log_metric` 對 `"retry_count"` 和 `"memory_hit_rate"` 應直接寫 collector，而非透過 `custom_metrics` 延遲 flush。  

---

### P2 — 建議改善，不影響正確性但影響維護性與營運彈性

**P2-1: 規則沒有執行期開關**

- `_RULES` 是 module-level `tuple`，無法在執行期動態停用個別規則。  
- 若某規則在 prod 開始大量誤報，運維需要改程式碼、重跑 CI、重新部署才能關掉它。  
- 建議：`evaluate_task_record` 加入 `disabled_tags: frozenset[str] = frozenset()` 參數，在 rule loop 中跳過被禁用 tag 的規則。  

**P2-2: eval_gate 輸出缺少版本號**

- eval_gate.py 頂部有 v0.1 註解，但 `evaluate_task_record` 的輸出 dict 中沒有 `eval_gate_version` 欄位。  
- 這使得下游無法區分不同版本的 gate 輸出，在升級規則時容易混淆。  
- 建議：在回傳 dict 中增加 `"eval_gate_version": "0.1"`。  

**P2-3: `context_heavy` 規則的 `CONTEXT_HEAVY_RATIO` (0.8) 無文件說明來源**

- eval_gate.py:13 硬編碼 `CONTEXT_HEAVY_RATIO = 0.8`，與 context_builder 的 ROOT_RESERVED_TOKENS / MAX_TOTAL_TOKEN_BUDGET（12000/128000 ≈ 0.094）不是同一概念。  
- 這個 0.8 是從何而來？是經驗值、SLA 門檻、還是任意選擇？沒有註解說明。  
- 建議：加上解釋（例如：「當 context 使用超過 80% 預算時，下游 agent 的推理空間不足，標記為 heavy」）。  


不變的部分（設計良好，值得保留）
----------------------------------

1. **純函數風格**：`evaluate_task_record` 無副作用、無全域狀態、無 IO。這是觀測層最正確的設計選擇。  
2. **規則組合模式**：每條規則是獨立的 `RuleFn = Callable[[dict], tuple[str, str] | None]`，可任意增減而不影響其他規則。這個介面設計是 SOLID 的典範。  
3. **輸出契約一致性**：回傳總是 `{"pass": bool, "tags": [...], "reasons": [...]}`，即使輸入非法也不拋例外。下游可以安全地對任何輸入做結構化處理。  
4. **門檻值使用 `>=` 與 `>` 的語意區分**：`retry_count >= 2`（高重試）、`context_heavy > threshold`（嚴格大於）、`trace_completeness < 0.8`（嚴格小於）。這些比較運算符的選擇展現了對每個維度門檻語意的思考。  
5. **`INFRA_RISK_ERROR_TYPES` 使用 `frozenset`**：不可變集合避免誤改，並使用 `in` 進行 O(1) 查找。  


建議的優先修復順序
------------------

1. ~~抽出 `contract_constants.py`~~ — **已完成**（見 P0-1 處理狀態）。
2. ~~加入 record schema 驗證~~ — **已完成**（見 P1-1 處理狀態）。
3. **將 `retry_count` / `memory_hit_rate` 改為直接寫 collector**
4. **加入整合測試** — 將本次 review 產出的 `tests/test_eval_gate_contract.py` 合入 CI，確保 logging_adapter 與 eval_gate 的合約不會在未來漂移。  
5. **加入執行期規則開關** — 為 `evaluate_task_record` 增加 `disabled_tags` 參數，提供運維在 prod 中動態關閉單一規則的能力。  
6. **補上版本號與門檻值註解** — 次要但成本極低，提升程式碼的可理解性。  