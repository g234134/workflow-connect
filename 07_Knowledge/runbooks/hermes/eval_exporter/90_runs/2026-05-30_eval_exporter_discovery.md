# Run Note: 2026-05-30 eval_exporter discovery

> 戰船：B-side P0 · eval_exporter discovery（readonly-only）

---

## 任務來源

任務卡：B-side P0 · eval_exporter discovery。目標：對 `observability/eval_exporter.py` 與其依賴做只讀盤點，產出 mapping 與初始問題盤點。

---

## 實際執行步驟

1. **讀取 primary target**：`observability/eval_exporter.py`（278 行）
2. **追蹤 direct import**：`observability/eval_gate.py`（351 行）
3. **追蹤 downstream/upstream 模組**：
   - `ibridge_exporter.py`（553 行）— import `iter_records` from exporter
   - `eval_ci_check.py`（192 行）— import `build_export_line`, `iter_records`
   - `eval_stats.py`（588 行）— 消費 eval_export/v1 JSONL
4. **讀取支援文檔**：
   - `eval_export_schema.md`（94 行）— schema
   - `eval_export.md`（234 行）— pipeline + CI 整合
   - `eval_gate_rules.md`（96 行）— 規則定義
   - `eval_pipeline.md`（265 行）— D4 設計稿
5. **讀取測試**：`tests/test_eval_exporter.py`（111 行）
6. **讀取間接依賴**：
   - `observability/__init__.py`（27 行）
   - `contract/constants.py`（1 行）
7. **產生交付物**（6 個檔案寫入 workspace）

## 產出檔案

| 檔案 | 摘要 |
|------|------|
| `10_memory/ARCH.md` | 模組架構：職責、輸入輸出、依賴圖、eval_gate 耦合點、D-005 連線、未知項 |
| `10_memory/STYLE.md` | 編碼風格：命名一致（snake_case+Final）、無集中 logging（僅 eval_gate 有）、函式拆分合理 |
| `10_memory/PIPELINE.md` | 管線圖：ibridge_exporter→eval_exporter→eval_ci_check/eval_stats；CI 文檔已知但 YAML 未讀 |
| `10_memory/DEBT_LOG.md` | 10 條 NEW_CANDIDATE 技術債 |D-005 核心重複、3 組跨模組重複、2 組測試缺口、1 格式不一致 |
| `20_runtime/eval_exporter_discovery_report.md` | 總結報告：模組結構、主要風險、D-005 直接證據（eval_gate.py:113 自標）、未知項、下一步 |
| `90_runs/2026-05-30_eval_exporter_discovery.md` | （本檔案）run note |

## 證據來源

所有結論直接來自上述 7 個 repo 檔案的靜態原始碼閱讀。D-005 證據來自 `eval_gate.py` line 113 的程式碼內註解與 `eval_exporter.py` line 36-43 的逐行比對。

## 阻塞與風隱

- **CI YAML 未讀**：文檔中有 `.github/workflows/eval-gate-ci.yml` 的參數摘要，但未實際讀取該檔案確認。
- **一次 truncation 事故**：初次 search_files 時間過長導致回應被截斷，後續改為直接利用已有上下文寫入。
- **無 D-005 ticket**：在 repo 檔案中未找到獨立 D-005 追蹤票（僅在 eval_gate.py 註解中標註 D-005）。

---

## CI/fixture 補充觀察（EVAL_EXPORTER-READONLY-SCAN-01）

### 本輪讀取的檔案

| 檔案 | 行/筆數 | 摘要 |
|------|--------|------|
| `.github/workflows/eval-gate-ci.yml` | 317 行 | 2 jobs：eval-gate（push/PR）、eval-shadow-nightly（schedule + wf_dispatch） |
| `tests/fixtures/eval/ibridge_records.jsonl` | 3 筆 | t-healthy（pass）、t-retry（high_retry）、t-infra（infra_risk/timeout） |
| `tests/fixtures/eval/eval_export_sample.jsonl` | 3 筆 | 與上同組但已轉成 eval_export/v1 |
| `tests/fixtures/eval/shadow_raw_records.jsonl` | 4 筆 | 混合格式：flat、k2_metrics_record、k2_summary |
| `observability/eval_stats_report.md` | 127 行 | 基於 fixture N=3 的閾值建議：0.72–0.87 |

### 關鍵發現

1. **CI 從不直接呼叫 eval_exporter** — 兩個 job 都只跑 `eval_ci_check`（內部 import exporter 函式）。這意味著 eval_export/v1 JSONL 無自動 CI 生產者（已記錄為 CI-GAP-1 NEW_CANDIDATE）。
2. **eval_export_sample.jsonl 的 line_index 與 ibridge_records.jsonl 對不上** — 前者 t-infra=1, t-retry=2, t-healthy=3，後者順序為 t-healthy(L1), t-retry(L2), t-infra(L3)（已記錄為 FIXTURE-PROVENANCE NEW_CANDIDATE）。
3. **eval_stats_report.md 數據不足** — 僅 N=3（壓測用），報告自身也說「Re-run after real eval_results.latest.jsonl lands」。目前無法鎖定 production CI 閾值。
4. **shadow_raw_records.jsonl（4 筆）** 涵蓋三種 shadow 格式：flat ibridge、k2_metrics_record、k2_summary。這些是 `ibridge_exporter.normalize_shadow_record` 的測試輸入。

### DEBT_LOG 更新

新增 2 條 NEW_CANDIDATE：CI-GAP-1（eval_export/v1 無 CI 生產者）、FIXTURE-PROVENANCE（fixture line_index 不匹配）。總數由 10 條增至 12 條。
