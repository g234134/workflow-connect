# PIPELINE.md — eval_gate CI/CD 管線與檢查流程

> 狀態：第一次實際探路完成 | 2026-05-30
> ⚠ 實際 CI/CD 平台尚未確認。本文件基於只讀掃描結果，標記所有仍屬推論的項目。

---

## 1. 管線概覽

**實際 CI/CD 系統**：⚠️ 待確認假設。

掃描結果：
- 大唐三省六部 repo root **無** `.github/workflows/` 目錄
- **無** root Makefile
- **無** `.gitlab-ci.yml` 或 `Jenkinsfile`
- `eval_ci_check.py` 的 docstring 開頭為「CI entry for P+ eval_gate」，意圖明確——它是設計給 CI pipeline 呼叫的模組（exit code 0/1）
- 推測 CI 為外掛 script 或外部平台（非 GitHub Actions 原生），透過 `python -m observability.eval_ci_check <path>` 觸發

**管線定義檔位置**：**無可用資訊**。需人工確認以下方向：
1. 搜尋 `eval_ci_check` 在 shell script 或 CI 配置中的引用
2. 檢查大唐三省六部外層 workspace 是否有 CI 配置

---

## 2. 預期檢查階段

> 以下為 **建議**（Infra Hygiene Owner 角度），非目前實際 CI 階段。

### 2.1 Lint / Format
- **目前狀態**：⚠️ 待確認
- 原始碼風格統一（雙引號、Google-style docstring），但無 config 檔佐證工具選擇
- 建議工具：Ruff（通用建議）

### 2.2 Type Check
- **目前狀態**：⚠️ 待確認
- 原始碼使用完整 type hint（`Final`、`Callable`、`Literal`、`frozenset` 等）
- 但無 `mypy.ini` 或 `pyproject.toml` 確認工具

### 2.3 Unit Test
- **目前狀態**：✅ 已確認部分資訊（見 §7 目前已知執行 / 測試指令）

### 2.4 Coverage
- **目前狀態**：**無可用資訊**
- 未發現 `.coveragerc`、`pyproject.toml` 或 coverage 輸出

### 2.5 Hygiene Check（自訂）
- 建議保留，但目前無對應實作

---

## 3. 本地開發檢查（Pre-commit / Pre-push）

**是否使用 pre-commit**：**無可用資訊**。無 `.pre-commit-config.yaml` 在 repo root。

---

## 4. 健康檢查指令（基於掃描結果）

> ⚠ 以下指令為**推測**，未經實際執行驗證。

```bash
# 推測：eval_gate 核心單元測試
# 需要在對應 venv 下執行（gov_core_system 或類似）
python -m pytest tests/test_eval_gate.py tests/test_eval_gate_contract.py -v

# 推測：完整 eval 相關測試
python -m pytest tests/test_eval_gate.py tests/test_eval_gate_contract.py tests/test_eval_exporter.py tests/test_eval_ci_check.py -v

# 推測：CI 信號檢查（給定記錄檔）
python -m observability.eval_ci_check tests/fixtures/eval/ibridge_records.jsonl

# 推測：JSONL 匯出
python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl -o /tmp/eval_out.jsonl
```

---

## 5. 管線失敗處理

| 檢查階段 | 常見原因 | 動作 |
|----------|----------|------|
| lint | 未格式化、未使用的 import | 執行 formatter，或修正 import |
| type check | 型別不一致、missing stub | 更新 type hint 或加 stub |
| test | 功能變更未更新 test | 更新測試 fixtures 或 assertion |
| coverage | 新程式碼未測試 | 補測試 |

---

## 6. 待確認事項

- [ ] CI/CD 平台為何？
- [ ] 管線定義檔在哪裡？
- [ ] 目前有哪些檢查階段？
- [ ] 有無 pre-commit 設定？
- [ ] 有無 CI 腳本引用 `eval_ci_check`？
- [ ] coverage 閾值與工具為何？

---

## 7. 目前已知執行 / 測試指令

> 本節為本次探路（2026-05-30）的實際發現摘要。所有指令均為**推測，需人工確認**。

### 7.1 測試框架與執行方式

| 項目 | 資訊 | 確認狀態 |
|------|------|----------|
| 測試框架 | **unittest**（所有測試檔案繼承 `unittest.TestCase`） | ✅ 確認 |
| 測試 runner | **pytest**（pycache: `pytest-9.0.2`） | ✅ 確認 |
| 測試 fixture 目錄 | `tests/fixtures/eval/`（含 `ibridge_records.jsonl`） | ✅ 確認 |
| 測試檔案數 | 5 個 py 模組：`test_eval_gate.py`、`test_eval_gate_contract.py`、`test_eval_exporter.py`、`test_eval_ci_check.py`、`test_eval_stats.py` | ✅ 確認 |
| pytest 配置檔 | **無**（無 `pyproject.toml`、`pytest.ini`、`conftest.py` 在 repo root） | ⚠️ 待確認 — 可能藏在 venv 或子目錄 |
| 執行環境 | 需要 `gov_core_system` venv（含 `observability` package 路徑） | ⚠️ 待確認 |
| Python 版本 | 推測 3.14（pycache 顯示 `cpython-314`；亦有 3.10 殘留） | ⚠️ 待確認 |

### 7.2 推測測試指令

```bash
# 執行 eval_gate 專屬測試（最保險的範圍）
python -m pytest tests/test_eval_gate.py tests/test_eval_gate_contract.py -v --tb=short

# 執行完整 eval 相關測試
python -m pytest tests/test_eval_gate*.py tests/test_eval_exporter.py tests/test_eval_ci_check.py -v --tb=short

# 純 unittest（不使用 pytest，備用方案）
python -m unittest tests.test_eval_gate tests.test_eval_gate_contract -v
```

### 7.3 推測 CI 指令

```bash
# CI 入口（取樣最近記錄，檢查 review rate）
python -m observability.eval_ci_check /path/to/records.jsonl --limit 100 --max-needs-review-ratio 0.5

# JSONL 匯出（批次分析用）
python -m observability.eval_exporter /path/to/records.jsonl -o eval_results.jsonl --filter needs_review
```

### 7.4 驗證方式建議

如果尚書省或人工確認，建議按以下順序驗證：

1. **確認 venv**：在 `01_Environments/python_venvs/gov_core_system/` 下 `pip list | grep pytest`
2. **試跑最小測試**：`python -m pytest tests/test_eval_gate.py -v --tb=short`
3. **尋找 CI 腳本**：搜尋 `eval_ci_check` 在 repo 內的 shell script 中
4. **確認 Python 版本**：`python --version`（在 venv activate 後）

---

## 8. 推論方向（當完全未知時）

若上述指令全部不可用，建議以下兩個推論方向供人工確認：

### 方向 A：pytest + venv 驅動
- 推測測試是在 `gov_core_system` venv 下執行
- 指令類似：`python -m pytest tests/test_eval_gate.py -v`
- 原因：所有 unittest 檔案結構完整、無外部服務依賴

### 方向 B：外部 CI 平台（非 GitHub Actions）
- `eval_ci_check.py` 的設計暗示 CI 透過 shell script 直接呼叫
- 無 `.github/workflows/` → 可能使用自架 runner 或 GitLab CI
- 驗證：搜尋 workspace 外層的 CI 配置目錄