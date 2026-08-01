# STYLE — eval_exporter 編碼風格觀察

> 基於 `eval_exporter.py` + `eval_gate.py` + `eval_ci_check.py` + `eval_stats.py` + `ibridge_exporter.py` 的靜態分析。

---

## 1. 命名慣例

| 層級 | 樣式 | 範例 | 一致性 |
|------|------|------|--------|
| 模組常數 | `UPPER_SNAKE_CASE` + `Final` | `SCHEMA_VERSION`, `MAX_TOTAL_TOKEN_BUDGET` | 高度一致 |
| 公有函式 | `snake_case` | `build_export_line`, `export_eval_jsonl`, `run_ci_check` | 高度一致 |
| 內部函式 | `_prefixed_snake_case` | `_iso_now`, `_unwrap_record`, `_parse_json_line` | 高度一致 |
| 型別別名 | `PascalCase` + `Literal` | `GateResult`, `GateFilter` | 一致 |
| 參數 | `snake_case` | `input_path`, `gate_filter`, `line_index` | 高度一致 |
| 私有模組計數器 | `Capitalized_Snake_Case`（單例） | `_REQUIRED_FIELDS`, `_RULES` | 僅見於 eval_gate，非全模組風格 |

**無不規則命名，整體一致。**

---

## 2. 錯誤處理模式

| 模式 | 使用場景 | 範例 |
|------|----------|------|
| **ValueError**（手動 raise） | 格式/輸入錯誤 | `_parse_json_line`: `raise ValueError(f"{source}:{line_no}: invalid JSON: {exc}")` |
| **FileNotFoundError**（自然拋出） | 路徑不存在 | `iter_records`: `raise FileNotFoundError(str(path))` |
| **try/except + fallback** | 型別轉換容錯 | `_context_tokens_total`: `try: return int(raw) except ... return 0` |
| **None/falsy 檢查**（非異常） | 鍵不存在或值為空 | `_record_timestamp`: `if raw is not None and str(raw).strip():` |
| **型別守衛 isinstance** | 嵌套結構不存在 | `_trace_completeness_score`: `if not isinstance(tc, dict): return None` |
| **回傳 error dict（不拋）** | 業務邏輯驗證 | `export_eval_jsonl` 回傳 `ok: True/False` + `message` |

**暫無集中錯誤處理類別或自訂 Exception。** 所有異常若不是直接 raise 就是回傳結構化的 dict 給呼叫端自己判斷。

---

## 3. 日誌模式

| 模組 | logging 用法 | 詳細程度 |
|------|-------------|----------|
| `eval_gate.py` | `logger = logging.getLogger(__name__)` → `info`, `warning` | 有結構化；入口 `logger.info(...)` + 規則觸發 `logger.info(...)` |
| `eval_exporter.py` | **無 logging** | 純 CLI `print(json.dumps(...))`；無模組級 logger |
| `eval_ci_check.py` | **無 logging** | 純 CLI `print(json.dumps(...))` |
| `eval_stats.py` | **無 logging** | 純 CLI `print(...)` 或 `json.dumps(...)` |
| `ibridge_exporter.py` | **無 logging** | 純 CLI `print(json.dumps(...))` |

**觀察：** 只有 eval_gate 使用了標準 logging。eval_exporter 及其同級模組完全靠 stdout JSON/plain text 輸出。這可能是因為這些模組設計為 CLI-first、非長期運行的 daemon 服務。

---

## 4. 函式拆分粒度

- **eval_exporter.py**: 278 行，14 個函式（8 內部 + 6 公開）。每個內部函式平均 3–12 行，單一職責明確。
- **eval_gate.py**: 351 行，14 個函式（規則/輔助）。每條規則一個獨立函式，職責單一清晰。
- **eval_stats.py**: 589 行，12+ 函式。較大函式如 `suggest_ci_thresholds`（~80 行）混合了多種邏輯。
- **eval_ci_check.py**: 193 行，3 個函式。相對簡潔，`run_ci_check` 約 80 行。
- **ibridge_exporter.py**: 554 行，15+ 函式。較大函式如 `export_ibridge_jsonl` 約 80 行。

**尚無充分樣本判斷模組特有風格規範**，但觀察到每個模組的 CLI `main()` 函式結構一致：`_build_cli()` → `main(argv)` → `result = ...` → `print(json.dumps(result))` → `return 0/1`。

---

## 5. 型別註釋採用度

- 所有模組均使用 `from __future__ import annotations` + 完整型別註釋。
- 廣泛使用 `Final`、`Literal`、`frozenset` 約束常量。
- `dict[str, Any]` 是 record 的通用型別（未使用 TypedDict）。

---

## 6. 模組邊界與分層

- **eval_exporter** 處於「轉接層」：讀取 ibridge 格式 → 透過 eval_gate 評估 → 輸出 eval_export/v1 格式。
- **eval_ci_check** 處於「消費層」：讀取 ibridge 格式 → 評估 + 聚合 → 產出 CI verdict。
- **ibridge_exporter** 處於「生產層」：從 collector/file/shadow 讀取 → 歸一化 → 產出 ibridge JSONL。
- **eval_stats** 處於「分析層」：讀取 eval_export/v1 JSONL → 統計 → 建議 CI 參數。

**職責分層合理**，但各模組之間存在共用邏輯的重複（見 DEBT_LOG D-005 / CROSS-DUP-* / JSONL-PARSE-DUP）。

---

## 7. 總結

整體風格平實、一致、以 CLI 為主。無大型 class 或繼承（全部是函式 + dict）。缺少集中的 utils 層導致解析邏輯在三個模組中重複。
