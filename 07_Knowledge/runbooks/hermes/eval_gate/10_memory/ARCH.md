# ARCH.md — eval_gate 模組架構紀錄

> 狀態：第一次實際探路完成 | 2026-05-30
> 本文件在初版 bootstrap 後經由只讀掃描實際 repo 更新。所有帶「待確認假設」標籤的項目均為推論，非確認事實。

---

## 1. 模組定位

`eval_gate` 是「D4 Observability + Eval runtime」的次模組，負責**基於規則的評估閘門**：

- **輸入**：接收來自 M-line（metrics）或 ibridge 的 task record dict。
- **處理**：執行 5 條硬編碼規則（high_retry、context_heavy、many_handoffs、infra_risk、observability_gap），判斷該記錄是否需要人類審查。
- **輸出**：回傳結構化 verdict（`pass` / `tags` / `reasons` / `eval_gate_version`）。
- **不涉及**：LLM-as-judge、Langfuse SDK、資料庫寫入、排程。

### 在系統中的角色

```
metrics_collector / logging_adapter
        │
        ▼  ┌───【eval_gate 閘門】───┐
  task record → evaluate_task_record() → verdict (pass / tags)
        │                              │
        ▼                              ▼
  k2_langgraph_flow          eval_exporter → JSONL
  (P+ metadata)              eval_ci_check → CI verdict
```

---

## 2. 實際目錄結構

### 原始碼（真實 repo）

```
大唐三省六部/observability/
├── eval_gate.py              # 核心規則引擎 (199 行)
├── eval_exporter.py          # JSONL 匯出 CLI (278 行)
├── eval_ci_check.py          # CI 入口：取樣 + 閘門 (193 行)
├── eval_stats.py             # 分佈分析工具 (588 行)
├── ibridge_exporter.py       # ibridge → JSONL（參考 eval_gate 路徑做 repo root discovery）
├── logging_adapter.py        # trace lifecycle（contract test 依賴）
└── __init__.py               # 「D4 Observability + Eval runtime」

大唐三省六部/tests/
├── test_eval_gate.py         # 單元測試：5 條規則 + 邊界 (93 行)
├── test_eval_gate_contract.py # 合約測試：logging_adapter → eval_gate (280 行)
├── test_eval_exporter.py     # 匯出測試 (111 行)
├── test_eval_ci_check.py     # CI hook 測試 (74 行)
├── test_eval_stats.py        # stats 測試
└── fixtures/eval/            # 測試用 ibridge 記錄

大唐三省六部/contract/
└── constants.py              # MAX_TOTAL_TOKEN_BUDGET = 128_000
```

### 已確認發現

| 項目 | 路徑 | 檔案數 |
|------|------|--------|
| 核心模組 | `observability/eval_gate.py` | 1 |
| 周邊工具 | `observability/eval_exporter.py`、`eval_ci_check.py`、`eval_stats.py` | 3 |
| 測試套件 | `tests/test_eval_gate*.py` | 5 個 py 模組 |
| 測試 fixture | `tests/fixtures/eval/` | 1 個目錄 |
| 依賴 | `contract/constants.py` | 1 |

### 管理包（本目錄）

```
infra_owner/eval_gate/
├── 00_skill/SKILL_INFRA_HYGIENE_OWNER.md
├── 10_memory/ARCH.md           # 本檔案
├── 10_memory/STYLE.md
├── 10_memory/DEBT_LOG.md
├── 10_memory/PLAYBOOK.md
├── 20_runtime/PIPELINE.md
├── 20_runtime/TASK_INTAKE_TEMPLATE.md
├── 20_runtime/REPORT_TEMPLATE.md
└── 90_runs/                    # 探索與執行紀錄
```

---

## 3. 外部依賴

| 依賴 | 已知資訊 | 確認狀態 |
|------|----------|----------|
| 底層 Python 版本 | 推測 **3.14**（pycache: `cpython-314`）+ 亦有 3.10 殘留 | ⚠️ 待確認假設 |
| 框架 | 純 Python 模組，無 FastAPI/Flask | ✅ 確認 |
| 資料庫或儲存後端 | 無直接依賴；僅讀 JSONL/JSON 檔案 | ✅ 確認 |
| 其他內部模組 | `contract.constants.MAX_TOTAL_TOKEN_BUDGET`（128K） | ✅ 確認 |
| 呼叫者 | `core/langgraph_flow_k2.py`、`core/k2_merge_adapter.py`、`core/k2_ask_shadow.py` | ✅ 確認 |
| 測試框架 | **unittest** + **pytest runner**（pycache 顯示 `pytest-9.0.2`） | ✅ 確認 |
| fixture 路徑 | `tests/fixtures/eval/` | ✅ 確認 |
| CI/CD 系統 | 大唐三省六部 root 無 `.github/workflows/`、無 Makefile | ⚠️ 待確認 |
| 第三方套件 | `evaluate_task_record` 僅用 stdlib（`typing`, `functools`）；exporter 用 `argparse`、`json`、`pathlib`、`datetime` | ✅ 確認（無第三方套件依賴） |

---

## 4. 公開介面

以下為掃描實際程式碼後識別出的公開介面。所有推論均註明來源。

### 4.1 核心 API

| 名稱 | 類型 | 簽章 | 來源檔案 | 行數 | 被誰呼叫 |
|------|------|------|----------|------|----------|
| `evaluate_task_record(record, *, disabled_tags)` | function | `dict[str,Any] \| Any` → `dict[str,Any]` | `observability/eval_gate.py` | 142–199 | `eval_exporter.py`、`eval_ci_check.py`、`core/langgraph_flow_k2.py` |
| `EVAL_GATE_VERSION` | constant | `Final[str] = "0.2"` | `observability/eval_gate.py` | 13 | `eval_gate.py` 自身回傳 |
| `CONTEXT_HEAVY_TOKEN_THRESHOLD` | constant | `int(128_000 * 0.8) = 102_400` | `observability/eval_gate.py` | 16 | `test_eval_gate.py`、`test_eval_gate_contract.py`、`test_eval_exporter.py` |

### 4.2 回傳結構

```python
{
    "pass": bool,                # True = 無觸發 tag
    "tags": list[str],           # 觸發的規則標籤
    "reasons": list[str],        # 對應的人類可讀原因
    "eval_gate_version": str,    # 當前版本 "0.2"
}
```

### 4.3 五條規則清單

| 規則函數 | Tag | 觸發條件 | 門檻值 |
|----------|-----|----------|--------|
| `_rule_high_retry` | `high_retry` | `retry_count >= 2` | `HIGH_RETRY_THRESHOLD = 2` |
| `_rule_context_heavy` | `context_heavy` | `context_token_usage.total_tokens > 102_400` | `CONTEXT_HEAVY_TOKEN_THRESHOLD = 102_400` |
| `_rule_many_handoffs` | `many_handoffs` | `handoff_count >= 3` | `MANY_HANDOFFS_THRESHOLD = 3` |
| `_rule_infra_risk` | `infra_risk` | `error_type in {"context_overflow", "timeout"}` | `INFRA_RISK_ERROR_TYPES = frozenset(...)` |
| `_rule_observability_gap` | `observability_gap` | `trace_completeness.score < 0.8` | `TRACE_COMPLETENESS_THRESHOLD = 0.8` |

### 4.4 錯誤處理路徑

| 輸入狀況 | Tag | 行為 |
|----------|-----|------|
| 非 dict 輸入 | `invalid_record` | 立即回傳 pass=False，跳過規則 |
| 缺少 `success`/`retry_count`/`handoff_count` | `malformed_record` | 回傳 pass=False，列出缺失欄位 |
| 欄位型別錯誤（例：字串 retry_count） | `malformed_record` | 同上 |

### 4.5 CLI 入口

| CLI | 模組 | 指令 | 說明 |
|-----|------|------|------|
| `eval_exporter` | `observability/eval_exporter.py` | `python -m observability.eval_exporter <input> -o <output> [--filter]` | 執行 eval_gate 並匯出 JSONL |
| `eval_ci_check` | `observability/eval_ci_check.py` | `python -m observability.eval_ci_check <input> [--limit] [--max-needs-review-ratio]` | CI 取樣檢查，依 ratio 或 tag 失敗 |
| `eval_stats` | `observability/eval_stats.py` | `python -m observability.eval_stats <files...> [--format text]` | 匯出結果的分布分析 |

### 4.6 被其他模組消費的元資料欄位

| 消費方 | 檔案 | 消費方式 |
|--------|------|----------|
| `k2_merge_adapter.py` | `core/k2_merge_adapter.py` | 讀取 `eval_meta["eval_gate"]["pass"]` 做 MergeGateResult 分類（fail/pass/review） |
| `k2_ask_shadow.py` | `core/k2_ask_shadow.py` | 讀取 `eval_meta["eval_gate"]["tags"]` 做 shadow 上下文 enrichment |

---

## 5. 已知架構決策記錄

| 決策 | 日期 | 說明 |
|------|------|------|
| 規則引擎，無 LLM | 推測 v0.1 | 模組 docstring 明確表示「Rules-based, no LLM-as-judge, no Langfuse SDK」 |
| 版本 v0.2 | 推測 | `EVAL_GATE_VERSION = "0.2"`；contract test 斷言 v0.2 |
| 回傳結構含版本鎖定 | 推測 | 所有回傳路徑均包含 `eval_gate_version` 欄位 |

---

## 6. 待確認假設（Top Priority）

> 以下項目為**推論而非確認事實**。需後續透過人工確認或執行命令驗證。

### 🟡 高優先級

1. **Python 版本**
   - 推測：3.14（基於 pycache `cpython-314-pytest-9.0.2.pyc`）
   - 但亦有 `cpython-310` 殘留 → 可能有多版本環境
   - 驗證方式：`python --version` + `which python`（在對應 venv 下）

2. **CI/CD 系統與執行方式**
   - 大唐三省六部 root **無** `.github/workflows/`、無 root Makefile
   - `eval_ci_check.py` 設計為手動或 script-driven CI 呼叫（非 GitHub Actions 原生）
   - 推測：可能是自訂 shell script 或外部 CI 平台觸發 `python -m observability.eval_ci_check`
   - 驗證方式：搜尋 `eval_ci_check` 在 CI 腳本中的引用

3. **測試執行指令**
   - 推測：`python -m pytest tests/test_eval_gate.py tests/test_eval_gate_contract.py -v`
   - 但無 `pyproject.toml` 或 `pytest.ini` 可確認 pytest 配置
   - 驗證方式：實際在對應 venv 執行 pytest（唯讀模式下無法驗證）

### 🟡 中優先級

4. **formatter / linter 工具鏈**
   - 程式碼使用雙引號、Google-style docstring 推測
   - 無 pyproject.toml 或 `.pre-commit-config.yaml` 可確認
   - 驗證方式：查看 repo 根目錄的配置文件

5. **專案實際 pyproject.toml 位置**
   - 在子目錄 (`02_Agents_Core/`) 中有多份 pyproject.toml，但 root 無
   - 驗證方式：檢查 `01_Environments/python_venvs/gov_core_system/` 的安裝記錄或 setup 腳本

6. **`disabled_tags` 參數是否在生產中被使用**
   - 介面已提供 `disabled_tags: frozenset | None = None`
   - 但 k2 呼叫 `evaluate_task_record(record)` 時未傳入此參數
   - 驗證方式：掃描所有呼叫點確認

### 🟢 已確認（無需再查）

- ✅ 核心模組路徑：`observability/eval_gate.py`
- ✅ 公開介面：`evaluate_task_record(record, *, disabled_tags)`
- ✅ 五條規則與門檻值
- ✅ 外部依賴僅 `contract.constants.MAX_TOTAL_TOKEN_BUDGET`
- ✅ 測試框架：unittest + pytest runner
- ✅ 測試 fixture 路徑：`tests/fixtures/eval/`
- ✅ 消費者鏈：k2_langgraph_flow → eval_gate → verdict
