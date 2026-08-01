# DEBT_LOG — eval_exporter 候選技術債

> 本文件僅記錄本輪 readonly discovery 能直接看出的候選技術債。
> 條目狀態均為 **NEW_CANDIDATE**（待後續 readonly scan 或 debt validation 確認/升級）或 **VALIDATED_CANDIDATE**（已確認）。

---

| ID | 標題 | 位置 | 描述 | 影響 | 狀態 |
|----|------|------|------|------|------|
| D-005 | context token total 邏輯重複（已驗證） | `eval_exporter._context_tokens_total` vs `eval_gate._total_context_tokens` | 兩函式的 context token 萃取邏輯完全相同。**2026-05-30 D-005-VALIDATION-01 逐行比對確認：逐行 diff=0（不含 docstring）**，且在同一 call chain 中針對同一個 record 被用於不同欄位。eval_gate 本身也已在註解中標註 D-005。 | 若 token 結構升級或計算邏輯變更，兩處需同步修改。該邏輯已存在於 2 處，新增第三處的風險高。核心邏輯相同但函式名稱不同（`_context_tokens_total` vs `_total_context_tokens`）。 | VALIDATED_CANDIDATE |
| CROSS-DUP-1 | unwrap 邏輯重複 | `eval_exporter._unwrap_record` vs `ibridge_exporter.normalize_ibridge_record`（第一段） | 兩者都對 `ibridge_record` / `record` / `metrics_record` 三把 key 做 unwrap。`normalize_ibridge_record` 額外做了 timestamp fallback 和 trace_id fallback，比 `_unwrap_record` 更完整。 | unwrap 協定變更時需改兩處，且有行為分歧風險（一個只 unwrap，一個 unwrap + normalize）。 | NEW_CANDIDATE |
| JSONL-PARSE-DUP | JSONL 行解析重複 | `eval_exporter._parse_json_line` vs `eval_stats._parse_json_line` | 兩個模組各自實作了幾乎相同的 JSONL 行解析：skip blank → `json.loads` → check dict type → 回傳/raise。除了 unwrap 環節（eval_stats 不做 unwrap），其餘邏輯完全一致。 | 無統一 parse 層；新增第三個 JSONL 消費者必定再 copy-paste。 | NEW_CANDIDATE |
| CROSS-DUP-3 | timestamp fallback 重複 | `eval_exporter._record_timestamp` 的 `end_time→start_time→timestamp` vs `ibridge_exporter.normalize_ibridge_record` 的 `end_time→timestamp→start_time` | 兩個 timestamp fallback 順序與實施方式不同：一個是純萃取（回傳原始 str），另一個是寫入 record 的 `end_time` 欄位。 | 行為不一致：exporter 選第一個非空值；ibridge_exporter 強制將非 `end_time` 值寫回 `end_time` 欄位。 | NEW_CANDIDATE |
| NO-LOG-EXP | exporter 無 logging | `eval_exporter.py`, `eval_ci_check.py`, `eval_stats.py`, `ibridge_exporter.py` | 這四個模組完全依靠 stdout JSON 輸出，無模組級 `logging.getLogger`。只有 eval_gate 使用了標準 logging。 | CLI 執行時若排程器需要結構化日誌而非 stdout，需自行解析 JSON；無 log level 控制。 | NEW_CANDIDATE |
| TEST-GAP-1 | iter_records 目錄分支未測 | `tests/test_eval_exporter.py` | 測試只用了單一 JSONL fixture 檔；`iter_records` 對目錄遞迴（`.json` + `.jsonl`）、JSON 陣列、空檔案邊界等均無覆蓋。 | 邊界行為（空目錄、混合格式、空白行）在生產環境可能導致意外中斷。 | NEW_CANDIDATE |
| TEST-GAP-2 | 無 gate=None 路徑測 | `tests/test_eval_exporter.py` | `build_export_line` 測試均傳入 gate 或依賴預設值；沒有測試 `gate=None` 時內部呼叫 `evaluate_task_record` 的回退路徑被正確觸發。 | `evaluate_task_record` 的介面變更（新增參數 `disabled_tags`）不會被 exporter 測試捕獲。 | NEW_CANDIDATE |
| CLI-DEFAULT-PATH | 預設輸出路徑不安全 | `eval_exporter.py` line 253 | `-o` 的 default 是 `Path("eval_results.jsonl")`（CWD）。若排程在非預期目錄執行，產物會散落在各處。 | 非關鍵，但 CI 如不指定 `-o` 會寫到 CWD 而非 `artifacts/eval/`。 | NEW_CANDIDATE |
| SCHEMA-VERSION-HARDCODE | schema_version 硬編碼 | `eval_exporter.py` line 18 + `eval_stats.py` line 22 | `SCHEMA_VERSION = "eval_export/v1"` 在兩個模組中各自定義（值相同但非共享）。 | 升級 schema 時需同時改兩處（exporter 寫入 + stats 驗證），若未同步會導致 stats 誤報 schema 警告。 | NEW_CANDIDATE |
| CONTEXT-HEAVY-OP | `>` vs `>=` 不一致 | `eval_gate.py` context_heavy 規則（`>`）vs high_retry / many_handoffs（`>=`） | 嚴格大於會比大於等於「少」觸發一行（剛好等於閾值時）。目前 `102_400` 這個值本身是 80% 無條件進位的產物，實際影響極小。 | 低影響；但若未來精確閾值政策需要調整運算子，此處可能被遺忘。 | NEW_CANDIDATE |

## 新增（2026-05-30 CI/fixture 補充）

| ID | 標題 | 位置 | 描述 | 影響 | 狀態 |
|----|------|------|------|------|------|
| CI-GAP-1 | eval_export/v1 JSONL 無 CI 自動生產者 | `eval-gate-ci.yml`（兩個 job） | CI 從不執行 `python -m observability.eval_exporter`。eval-gate job 直接餵 ibridge records 給 `eval_ci_check`；shadow nightly 也是 ibridge_exporter → `eval_ci_check`。`eval_stats` 所需的 eval_export/v1 JSONL 只能手動或獨立腳本產生。 | `eval_stats_report.md` 的閾值建議依賴於 eval_export/v1 JSONL，但 CI 無自動產出該格式。目前只有 fixture N=3 樣本可分析，無法鎖定生產閾值。 | NEW_CANDIDATE |
| FIXTURE-PROVENANCE | eval_export_sample.jsonl line_index 與 ibridge_records.jsonl 對不上 | `tests/fixtures/eval/eval_export_sample.jsonl` vs `tests/fixtures/eval/ibridge_records.jsonl` | ibridge_records.jsonl 的順序為：L1 t-healthy, L2 t-retry, L3 t-infra。eval_export_sample.jsonl 的 source_ref.line_index 卻為：t-infra=1, t-retry=2, t-healthy=3，與來源不符。 | 若 eval_export_sample 不是由 eval_exporter 從 ibridge_records.jsonl 產生，則 traceability 中斷。fixture 可能手動構建或來源不同。 | NEW_CANDIDATE |

## 2026-05-30 D-005 升級記錄

D-005 從 **NEW_CANDIDATE** 升級為 **VALIDATED_CANDIDATE**。原因：eval_exporter._context_tokens_total 與 eval_gate._total_context_tokens 經逐行比對確認 diff=0（不含 docstring），且在同一 call chain 中被用於同一個 record。
