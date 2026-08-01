# Run Note: 2026-05-30 — eval_gate Infra Hygiene 第一次實際探路（只讀模式）

> **任務**：eval_gate 模組 infra hygiene 的第一次實際探路（只讀模式）
> **執行者**：Hermes Agent
> **日期**：2026-05-30
> **模式**：read-only | 未修改任何 repo 原始碼
> **前提**：ARCH.md 與 PIPELINE.md 在 bootstrap 階段含有大量 unknown

---

## 1. 探路摘要

本次探路執行以下動作：
1. 掃描 `/mnt/d/hermes-workspace/infra_owner/eval_gate/` 管理包結構（已存在的 9 份文件）
2. 搜尋 `eval_gate` 在 `/mnt/d/大唐三省六部/` 中的實際原始碼位置
3. 讀取所有相關原始碼檔案（含相依、測試、CI）
4. 確認模組定位、公開介面、規則清單、依賴鏈、消費者
5. 更新 ARCH.md 與 PIPELINE.md

---

## 2. 已找到的路徑與檔案

### 原始碼（大唐三省六部 repo）

| 類別 | 路徑 | 重要性 |
|------|------|--------|
| 核心模組 | `observability/eval_gate.py` (199 行) | **主體** — 5 條規則引擎 |
| 匯出工具 | `observability/eval_exporter.py` (278 行) | JSONL 匯出 + CLI |
| CI 入口 | `observability/eval_ci_check.py` (193 行) | 取樣 + threshold 檢查 |
| 統計分析 | `observability/eval_stats.py` (588 行) | 分布分析 + 閾值建議 |
| 依賴常數 | `contract/constants.py` (1 行) | `MAX_TOTAL_TOKEN_BUDGET = 128_000` |
| 單元測試 | `tests/test_eval_gate.py` (93 行) | 5 條規則單點測試 |
| 合約測試 | `tests/test_eval_gate_contract.py` (280 行) | logging_adapter → eval_gate |
| 匯出測試 | `tests/test_eval_exporter.py` (111 行) | 匯出管線測試 |
| CI 測試 | `tests/test_eval_ci_check.py` (74 行) | CI hook 行為測試 |
| 測試 fixture | `tests/fixtures/eval/ibridge_records.jsonl` | 測試用記錄 |

### 消費者（呼叫 eval_gate 的檔案）

| 消費者 | 路徑 | 消費方式 |
|--------|------|----------|
| K2 LangGraph flow | `core/langgraph_flow_k2.py` | `from observability.eval_gate import evaluate_task_record`（Line 65） |
| K2 merge adapter | `core/k2_merge_adapter.py` | 讀取 `eval_meta["eval_gate"]["pass"]` |
| K2 ask shadow | `core/k2_ask_shadow.py` | 讀取 `eval_meta["eval_gate"]["tags"]` |

---

## 3. 已識別的公開介面

### 核心函數

```python
def evaluate_task_record(
    record: dict[str, Any] | Any,
    *,
    disabled_tags: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Screen a single metrics_record or ibridge_record for human review."""
```

### 回傳結構

```python
{
    "pass": bool,                # True = 無觸發 tag
    "tags": list[str],           # 例: ["high_retry", "context_heavy"]
    "reasons": list[str],        # 例: ["retry_count=2 >= 2", "..."]
    "eval_gate_version": str,    # "0.2"
}
```

### 五條規則

| Tag | 觸發條件 | 門檻 |
|-----|----------|------|
| `high_retry` | `retry_count >= 2` | 2 |
| `context_heavy` | `context_token_usage.total_tokens > 102_400` | 102,400 (80% of 128K) |
| `many_handoffs` | `handoff_count >= 3` | 3 |
| `infra_risk` | `error_type in {"context_overflow", "timeout"}` | frozenset |
| `observability_gap` | `trace_completeness.score < 0.8` | 0.8 |

### CLI 入口

| CLI | 指令模式 |
|-----|----------|
| eval_exporter | `python -m observability.eval_exporter <input> -o <output> [--filter]` |
| eval_ci_check | `python -m observability.eval_ci_check <input> [--limit] [--max-needs-review-ratio]` |
| eval_stats | `python -m observability.eval_stats <files...> [--format text]` |

---

## 4. 文件更新摘要

### ARCH.md — 從 bootstrap → 第一次探路完成

| 區塊 | 原狀態 | 更新後 |
|------|--------|--------|
| 模組定位 | 3 條推測用途 | **確認**：D4 Observability 次模組，規則型評估閘門 |
| 目錄結構 | 「尚不知實際路徑」 | **確認**：`observability/eval_gate.py` + 周邊 6 檔 |
| 外部依賴 | 全部 unknown | ✅ 7/8 項確認，僅 CI/CD 系統仍待確認 |
| 公開介面 | 4 條推測類別名 | **確認**：完整 API 簽章、回傳結構、5 條規則、3 個 CLI |
| 架構決策 | 無條目 | 新增 3 條（規則引擎、v0.2、版本鎖定回傳） |
| 待確認項目 | 6 條全 unknown | 拆分為高/中優先級 + 已確認清單 |

### PIPELINE.md — 新增「目前已知執行/測試指令」§7

| 區塊 | 原狀態 | 更新後 |
|------|--------|--------|
| 管線概覽 | unknown | **無可用資訊**（無 .github、無 Makefile），標記 needs-confirmation |
| CI/CD 系統 | unknown | `eval_ci_check.py` 為 CI 入口；推測為外掛 script 或外部平台 |
| 檢查階段 | 全部 unknown | Lint/Type/Coverage 仍 unknown；Unit Test 已確認部分資訊 |
| **§7 測試指令** | **不存在** | **新增**：框架 = unittest + pytest-9.0.2；fixture 路徑；推測指令 3 條 |
| **§8 推論方向** | **不存在** | **新增**：2 個方向供人工確認 |

---

## 5. Still-unknown / Needs-Confirmation 項目（完整清單）

### 高優先級

| # | 項目 | 原因 | 驗證方式 |
|---|------|------|----------|
| 1 | **Python 版本** | pycache 顯示 3.14 和 3.10 並存 | 在對應 venv 下 `python --version` |
| 2 | **CI/CD 平台與管線定義位置** | 無 `.github/workflows/`、無 Makefile | 搜尋 `eval_ci_check` 在 shell script / CI config 中的引用 |
| 3 | **實際測試執行指令** | 有 unittest 檔案但無 `pyproject.toml` 或 `pytest.ini` | 在 gov_core_system venv 下實際嘗試 `python -m pytest tests/test_eval_gate.py -v` |

### 中優先級

| # | 項目 | 原因 | 驗證方式 |
|---|------|------|----------|
| 4 | **formatter / linter 工具鏈** | 風格統一但無 config 檔佐證 | 查看 repo root 工具配置 |
| 5 | **pyproject.toml 位置** | root 無，子目錄有多份 | 檢查 venv 的安裝記錄 |
| 6 | **`disabled_tags` 生產使用狀況** | 介面有提供但 k2 呼叫未傳入 | 掃描所有呼叫點 |

### 低優先級 / 觀察項

| # | 項目 | 說明 |
|---|------|------|
| 7 | coverage 配置 | 無 `.coveragerc` 或 coverage 輸出檔 |
| 8 | pre-commit hook | 無 `.pre-commit-config.yaml` |
| 9 | `eval_stats.py` 的生產使用狀況 | 目前僅做測試用？ |
| 10 | `ibridge_exporter.py` 與 eval_gate 的 interaction | ibridge_exporter 使用 eval_gate 路徑做 repo discovery |

---

## 6. 已確認無需再查的項目

- ✅ 核心模組路徑與角色：`observability/eval_gate.py` — 規則型評估閘門
- ✅ 公開 API 簽章：`evaluate_task_record(record, *, disabled_tags)` → dict
- ✅ 五條規則名稱、觸發條件、門檻值（見 §3 表格）
- ✅ 外部依賴：僅 `contract.constants.MAX_TOTAL_TOKEN_BUDGET`，無第三方套件
- ✅ 測試框架：unittest + pytest runner（pytest-9.0.2）
- ✅ 測試 fixture 路徑：`tests/fixtures/eval/`
- ✅ 消費者：k2_langgraph_flow、k2_merge_adapter、k2_ask_shadow
- ✅ 版本：v0.2（`EVAL_GATE_VERSION = "0.2"`）
- ✅ 三個 CLI 入口：eval_exporter、eval_ci_check、eval_stats
- ✅ 錯誤處理：invalid_record / malformed_record 兩種路徑

---

## 7. 下一輪最小行動（最多 5 條，按優先級排序）

### N-1：驗證 Python 版本與 venv

```
確認 gov_core_system venv 的 Python 版本：
cd /mnt/d/大唐三省六部
. 01_Environments/python_venvs/gov_core_system/Scripts/activate
python --version
```

### N-2：實際執行 eval_gate 測試

```
在 gov_core_system venv 下執行最小測試：
python -m pytest tests/test_eval_gate.py tests/test_eval_gate_contract.py -v --tb=short
```

記錄真實輸出，確認測試是否通過、以及實際 pytest 版本與配置。

### N-3：尋找 CI 腳本

```
搜尋 eval_ci_check 的參考：
grep -rn "eval_ci_check" /mnt/d/大唐三省六部/ --include="*.sh" --include="*.yml" --include="*.yaml"
```

若無結果，擴展搜尋至 `/mnt/d/hermes-workspace/` 上層目錄。

### N-4：補齊 STYLE.md 的實際工具鏈

- 如果找到 formatter/linter 配置（pyproject.toml、.pre-commit-config.yaml），更新 STYLE.md
- 如果找到實際 docstring 格式（Google / NumPy / Sphinx），更新 STYLE.md §4

### N-5：執行第一次 Hygiene 掃描

```
基於 SKILL_INFRA_HYGIENE_OWNER.md §2 執行完整檢查清單：
1. 合約檢查 → 確認所有公開函數的 docstring 與 type hint
2. 錯誤處理 → 檢查 bare except 與例外類型
3. 型別與介面 → Protocol / ABC 同步
4. 日誌與可觀測性 → 關鍵決策點日誌
5. 測試穩定性 → flaky 測試掃描
6. 技術債 → TODO/FIXME/HACK 對應 DEBT_LOG
```

將發現填入 `DEBT_LOG.md`，產出第一份 hygiene 報告（使用 `REPORT_TEMPLATE.md`）。