# ARCH — eval_exporter 模組架構

> 本文件基於 2026-05-30 readonly discovery 撰寫；所有未知項已標明。

---

## 1. 模組職責

- **主要職責**：讀取 ibridge/metrics record JSON/JSONL，經 eval_gate 評估後輸出 eval_export/v1 JSONL。
- **定位**：P+ pipeline 的「批式後處理」步驟——下游為 CI 檢查與分佈分析，上游為 ibridge_exporter 或 fixture 資料。
- **不處理**：in-process collector 直接輸出（由 ibridge_exporter 處理）、metric 收集（MetricsCollector）、replay 決策（eval_pipeline.md 設計稿）。

---

## 2. 主要輸入/輸出

### 輸入
| 項目 | 說明 |
|------|------|
| **格式** | `.json`（單筆或陣列）、`.jsonl`（逐行）、目錄（遞迴 `.json` / `.jsonl`） |
| **欄位對齊** | `tests/fixtures/eval/ibridge_records.jsonl` 定義了必備形狀：`task_id`、`trace_id`、`end_time`、`success`、`retry_count`、`handoff_count`、`error_type`、`context_token_usage`、`trace_completeness` |
| **包裝處理** | 如果記錄包在 `ibridge_record` / `record` / `metrics_record` 鍵下，`_unwrap_record` 會自動解開 |
| **來源路徑** | `artifacts/eval/ibridge_records.latest.jsonl`（CI 預設）、`artifacts/eval/shadow_ibridge_records.latest.jsonl`（shadow nightly） |

### 輸出
| 項目 | 說明 |
|------|------|
| **格式** | JSONL，每行一個 `eval_export/v1` 物件 |
| **Schema** | `observability/eval_export_schema.md` 正式定義 |
| **行內容** | `schema_version`、`trace_id`、`task_id`、`timestamp`、`exported_at`、`gate_result`、`tags`、`reasons`、`metrics`（摘要）、`source_ref`（可選） |
| **產物路徑** | 透過 CLI `-o` 參數指定；預設 `./eval_results.jsonl` |
| **返回結果** | 結構化 JSON dict：`ok`、`message`、`written`、`skipped_filter`、`total_read`、`output_path`、`gate_filter` |

---

## 3. 關鍵依賴

| 依賴對象 | 型別 | 使用方式 |
|----------|------|----------|
| `observability.eval_gate.evaluate_task_record` | Python function | `build_export_line()` default gate 參數（實作內部呼叫） |
| `argparse` | 標準庫 | CLI 參數解析 |
| `json` | 標準庫 | JSON 序列化/反序列化 |
| `pathlib.Path` | 標準庫 | 路徑操作、遞迴目錄遍歷 |
| `datetime` / `timezone` | 標準庫 | 時間戳生成 |
| `typing` (Final, Iterator, Literal) | 標準庫 | 型別註釋 |
| `contract.constants.MAX_TOTAL_TOKEN_BUDGET` | 本地模組 | 間接依賴（透過 eval_gate 使用） |

**反向依賴**（其他模組引用 eval_exporter）：
- `observability.eval_ci_check`：import `build_export_line`, `iter_records`
- `observability.ibridge_exporter`：import `iter_records`
- `tests.test_eval_exporter`：import `SCHEMA_VERSION`, `build_export_line`, `export_eval_jsonl`, `iter_records`

---

## 4. 與 eval_gate 的耦合點

| 耦合位置 | 說明 | 風險 |
|----------|------|------|
| `build_export_line(record, gate=…)` | gate 參數預設由 `evaluate_task_record(record)` 產生 | 低風險；gate 為純函數，接口穩定 |
| `gate_result_label(gate)` | 將 `evaluate_task_record` 的 `pass` bool 映射為 `"pass"` / `"needs_review"` | 低風險；僅依賴 `gate["pass"]` 鍵 |
| **D-005 跨檔案重複** | `_context_tokens_total`（eval_exporter）與 `_total_context_tokens`（eval_gate）邏輯完全相同 | **中風險**；兩處若不同步更新會導致產出不一致 |
| **unwrap 邏輯重複** | `_unwrap_record`（eval_exporter）與 `ibridge_exporter.normalize_ibridge_record` 的第一段 unwrap 相似 | 中風險；記錄包裝層級變化時需同步改兩處 |

---

## 5. 內部函式分層

### 公用（exported）
| 函式 | 職責 |
|------|------|
| `summarize_metrics(record)` | 萃取 `success`, `retry_count`, `handoff_count`, `error_type`, `context_tokens_total`, `trace_completeness_score` |
| `gate_result_label(gate)` | `pass`/`needs_review` 映射 |
| `build_export_line(record, *, gate, line_index, exported_at)` | 建構完整 JSONL 行 |
| `iter_records(path)` | 遞迴走訪 JSON/JSONL（檔案或目錄） |
| `export_eval_jsonl(input_path, output_path, *, gate_filter)` | 主處理流程 |
| `main(argv)` | CLI 入口 |

### 內部（private）
| 函式 | 職責 |
|------|------|
| `_iso_now()` | UTC ISO 時間戳 |
| `_record_timestamp(record)` | 從 `end_time` → `start_time` → `timestamp` 選擇 |
| `_context_tokens_total(record)` | **與 eval_gate._total_context_tokens 重複** |
| `_trace_completeness_score(record)` | 萃取 `trace_completeness.score` |
| `_unwrap_record(raw)` | 解開 `ibridge_record`/`record`/`metrics_record` 包裝 |
| `_parse_json_line(raw, *, source, line_no)` | 單行 JSONL 解析 |
| `_records_from_json_file(path)` | JSON 陣列或單物件 |
| `_matches_filter(gate_result, gate_filter)` | 篩選邏輯 |
| `_build_cli()` | argparse 建構 |

---

## 7. CI 觀點下的 eval_exporter

CI（`eval-gate-ci.yml`）**從不直接呼叫 `python -m observability.eval_exporter`**。`eval-gate` job 與 `eval-shadow-nightly` job 均直接使用 `eval_ci_check`，後者內部 import `build_export_line` 與 `iter_records`。eval_export/v1 JSONL 在 CI 中無自動生產者——產出只能靠手動執行或獨立 script。

**實務影響**：`eval_stats` 分析的 `eval_export/v1` JSONL（如 `eval_stats_report.md` 所用的）不存在自動 CI 管線；目前僅有 fixture sample（N=3）可作為分析輸入。

## 6. 未知項（更新後）

- **已澄清：CI 從不直接呼叫 eval_exporter** — 詳見 §7。
- **已澄清：D-005 token 重複邏輯已確認** — 在 eval_gate.py 註解中有標記，無獨立 ticket。
- `artifacts/eval/` 目錄的實際存在與內容 — **仍 unknown**（僅從文檔推測）。
- `utils` / `metrics` 模組的實際 API — **仍 unknown**（`ibridge_exporter.py` 引用 `metrics.get_collector()`，本輪未讀取）。
- eval_stats_report.md 的閾值建議內容 — **仍 unknown**（已知該檔案存在但本輪未讀取）。
