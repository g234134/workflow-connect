# eval_exporter Discovery Report

> 日期：2026-05-30 | 範圍：readonly-only | 作者：Hermes Agent (B-side P0)

---

## 讀取的 repo 檔案

| 檔案 | 行數 | 必要性 | 備註 |
|------|------|--------|------|
| `observability/eval_exporter.py` | 278 | ★ primary | 主目標 |
| `observability/eval_gate.py` | 351 | ★ direct import | 直接 import（`evaluate_task_record`） |
| `observability/ibridge_exporter.py` | 553 | ★ upstream dep | import `iter_records`；pipeline 上游 |
| `observability/eval_ci_check.py` | 192 | ★ sibling dep | import `build_export_line`, `iter_records` |
| `observability/eval_stats.py` | 588 | ★ consumer dep | 消費 eval_export/v1 產物 |
| `tests/test_eval_exporter.py` | 111 | ★ test suite | 測試覆蓋範圍觀察 |
| `observability/eval_export_schema.md` | 94 | ★ schema doc | JSONL schema 定義 |
| `observability/eval_export.md` | 234 | ★ pipeline doc | CI pipeline 整合文檔 |
| `observability/eval_gate_rules.md` | 96 | ★ rules doc | eval_gate 規則說明 |
| `observability/eval_pipeline.md` | 265 | ★ design doc | D4 eval pipeline 設計稿 |
| `observability/__init__.py` | 27 | ◇ package | 僅 re-export logging_adapter |
| `contract/constants.py` | 1 | ◇ transitive dep | `MAX_TOTAL_TOKEN_BUDGET` |
| `.github/workflows/eval-gate-ci.yml` | — | ◇ CI YAML | 文檔讀過但未實際讀取檔案內容 |
| `tests/fixtures/eval/ibridge_records.jsonl` | — | ◇ fixture | 未讀內容，僅從測試推測結構 |

---

## 模組結構

```
observability/
├── eval_exporter.py       ← 目標模組（278 行）
├── eval_gate.py           ← 核心評估邏輯（351 行）
├── ibridge_exporter.py    ← 上游資料生產者（553 行）
├── eval_ci_check.py       ← CI 信號消費（192 行）
├── eval_stats.py          ← 分佈分析（588 行）
├── eval_export_schema.md  ← schema definition
├── eval_export.md         ← pipeline & CI 文檔
├── eval_gate_rules.md     ← 規則說明
├── eval_pipeline.md       ← D4 設計稿
├── eval_stats_report.md   ← [僅從文檔知道存在，本輪未讀]
└── __init__.py             ← 包入口

tests/
└── test_eval_exporter.py  ← 6 tests

contract/
└── constants.py            ← MAX_TOTAL_TOKEN_BUDGET = 128_000
```

---

## 主要風險

### 1. D-005 跨檔案重複（高優先）
`eval_exporter._context_tokens_total` 與 `eval_gate._total_context_tokens` 是完整的邏輯重複。**eval_gate.py 自己已經在本輪被讀取時就標註了 D-005**。這是在兩個文件中各自獨立維護的函式；若 token 萃取邏輯變更（例如改用 `total` 取代 `total_tokens`、或改走 `model_usage.usage` 嵌套），兩處需同時改。已確認 D-005 存在於 eval_gate.py line 113 的程式碼註解中。

### 2. 跨模組 JSONL parse 重複（中優先）
至少有 eval_exporter、eval_stats、ibridge_exporter 三個模組各自實作了 JSONL 行解析與 unwrap 邏輯。無共用 `utils` 層。

### 3. CI YAML 未讀（觀察項）
`eval-gate-ci.yml` 的具體內容本輪未讀取。pipeline 推測是從 `eval_export.md` 和 `eval_stats.md` 文中片段拼合，部分細節可能不準確。

---

## D-005 線索

### 直接證據
| 位置 | 內容 |
|------|------|
| `eval_gate.py:113` | `此函數與 eval_exporter.py 中的 _context_tokens_total 邏輯相同（見 DEBT_LOG D-005）` |
| `eval_exporter.py:36-43` | `_context_tokens_total` — exact same impl |
| `eval_gate.py:108-128` | `_total_context_tokens` — 逐行對比，完全一致 |

### 間接證據（潛在延伸）
| 比較對 | 相似度 | 影響面 |
|--------|--------|--------|
| `_unwrap_record` (exporter) vs `normalize_ibridge_record` (ibridge_exporter) unwrap 段 | ~85% | unwrap 協定變更需同步 |
| `_parse_json_line` (exporter) vs `_parse_json_line` (stats) | ~90% | 無統一 parse 層 |
| `_record_timestamp` (exporter) vs `normalize_ibridge_record` timestamp fallback | ~60% | 行為不一致（回寫 vs 不回寫） |

### 影響面評估
- **D-005 core**：直接導致產出不一致。若一方改而另一方未改，同一個 record 在 eval_exporter 和 eval_gate 中的 context_tokens_total 會不同。
- **延伸重複**：導致新增 JSONL 消費者時被迫 copy-paste 解析邏輯，增加維護成本。

### 待驗證
- D-005 是否已有獨立 ticket 或 tracking issue（未在 repo 檔案中找到）
- D-005 是否影響生產已確認的 metrics 欄位（無法從靜態分析確認）
- 是否有正在進行的重構計畫（如抽出共用 `utils/` 層）

**結論：證據充分可確認 D-005 是一組真正的跨檔案重複。延伸耦合（unwrap、parse）需 further readonly scan 驗證。**

---

## 未知項

- `.github/workflows/eval-gate-ci.yml` 完整 CI 步驟內容
- `artifacts/eval/` 目錄是否存在與實際內容
- eval_exporter 是否有 cron/daemon 排程
- `eval_stats_report.md` 的實際 threshold 建議內容
- `metrics` module 的實際 API（`get_collector`、`list_tasks`）
- `observability/logging_adapter.py` 的實際 trace API
- D-005 是否已有正式 ticket

---

## 下一步建議（最多 3 條）

1. **readonly scan**：補讀 `.github/workflows/eval-gate-ci.yml`、`tests/fixtures/eval/ibridge_records.jsonl`、`eval_stats_report.md`，補齊 CI 與 fixture 維度。
2. **debt validation**：對 D-005（`_context_tokens_total` vs `_total_context_tokens`）做實際 diff 與 impact 分析，確認是否需要開票 unified `_safe_token_total()` 到共用層。
3. **D-005 拆票**：若 validation 確認 D-005 為真，拆成兩張票—(a) 建立共用 `observability/_eval_utils.py` 收納重複邏輯，(b) 先為重複邏輯加上註解追蹤。
