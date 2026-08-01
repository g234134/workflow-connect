# Apply Plan: eval_gate.suggested.v1.py → Repo

> 建立日期：2026-05-30 | 狀態：ready_for_review
> 對應 review：90_runs/2026-05-30_review_v1.md（結論：接受）

---

## 1. 本次來源

| 項目 | 路徑 |
|------|------|
| **Workspace suggested 檔** | `/mnt/d/hermes-workspace/infra_owner/eval_gate/20_runtime/eval_gate.suggested.v1.py` |
| **Repo 目標檔** | `/mnt/d/大唐三省六部/observability/eval_gate.py` |
| **確認來源** | `90_runs/2026-05-30_discovery.md` §2（原始掃描）；`10_memory/ARCH.md` §2（目錄結構確認） |

目標路徑已由掃描確認（ARCH.md §2），無 needs-confirmation 項目。

---

## 2. Patch 類型

| 項目 | 類型 | 語意變更？ | 風險 |
|------|------|:----------:|:----:|
| 規則函數 docstring（5 條 `_rule_*`） | **docstring** | 否 | 零 |
| 工具函數 docstring（5 個 helper） | **docstring** | 否 | 零 |
| `_RULES` 區塊註解 | **註解** | 否 | 零 |
| INRA_RISK_ERROR_TYPES 旁 inline 註解 | **註解** | 否 | 零 |
| `import logging` + `logger = ...` | **import 新增** | 否（stdlib 模組） | 零 |
| `evaluate_task_record` 內 5 條 log 呼叫 | **logging 補強** | 否（不影響回傳值） | 低 |
| `CONTEXT_HEAVY_RATIO` 旁 inline 註解 | **註解** | 否 | 零 |

**總分類**：docstring + logging + 註解（無語意變更）

---

## 3. 已知不變項（靜態比對已確認）

以下項目在 `2026-05-30_fix_round1.md` §3 已完成 AST + regex 自動比對，全部 PASS：

| 不變項 | 狀態 |
|--------|:----:|
| `evaluate_task_record(record, *, disabled_tags)` 簽名 | ✅ 一致 |
| 回傳 keys：`pass` / `tags` / `reasons` / `eval_gate_version` | ✅ 一致 |
| `EVAL_GATE_VERSION = "0.2"` | ✅ 一致 |
| `CONTEXT_HEAVY_TOKEN_THRESHOLD = 102400` | ✅ 一致 |
| `HIGH_RETRY_THRESHOLD = 2` | ✅ 一致 |
| `MANY_HANDOFFS_THRESHOLD = 3` | ✅ 一致 |
| `TRACE_COMPLETENESS_THRESHOLD = 0.8` | ✅ 一致 |
| `CONTEXT_HEAVY_RATIO = 0.8` | ✅ 一致 |
| `INFRA_RISK_ERROR_TYPES = frozenset({"context_overflow", "timeout"})` | ✅ 一致 |
| `_REQUIRED_FIELDS` 結構 | ✅ 一致 |
| `_RULES` 元素順序 | ✅ 一致 |
| `_rule_high_retry`: `count >= HIGH_RETRY_THRESHOLD` | ✅ 一致 |
| `_rule_context_heavy`: `total > CONTEXT_HEAVY_TOKEN_THRESHOLD` | ✅ 一致 |
| `_rule_many_handoffs`: `count >= MANY_HANDOFFS_THRESHOLD` | ✅ 一致 |
| `_rule_infra_risk`: `err in INFRA_RISK_ERROR_TYPES` | ✅ 一致 |
| `_rule_observability_gap`: `score < TRACE_COMPLETENESS_THRESHOLD` | ✅ 一致 |

---

## 4. 建議人工套用順序

為了降低逐段比對的認知負擔，建議按此順序套用：

### 第 1 步：先套 docstring（5 條規則函數 + 5 個 helper）

| 函數 | 建議檔行號（約數） | 新增內容 | 原始檔行號 |
|------|:------------:|----------|:------:|
| `_collect_schema_issues` | 41–58 | Google-style docstring 擴充 | 31 |
| `_int_field` | 64–81 | 完整 Google-style docstring | 42 |
| `_float_field` | 87–111 | 完整 Google-style docstring（含 default=1.0 設計意圖） | 50 |
| `_total_context_tokens` | 117–137 | 完整 Google-style docstring（含 D-005 提示） | 62 |
| `_error_type` | 143–158 | 完整 Google-style docstring | 73 |
| `_rule_high_retry` | 172–188 | 觸發條件 + 依賴欄位 + 意圖 | 83 |
| `_rule_context_heavy` | 190–216 | 同上（含 D-004 不一致提示） | 93 |
| `_rule_many_handoffs` | 218–234 | 同上 | 106 |
| `_rule_infra_risk` | 236–250 | 同上 | 116 |
| `_rule_observability_gap` | 252–270 | 同上（含 default=1.0 靜默 fallback 提示） | 123 |

**做法建議**：對每個函數，在原始檔的 `def` 行後插入對應 docstring。不修改任何原始邏輯行。

### 第 2 步：再套 import + logging 初始化

| 位置 | 新增內容 |
|------|----------|
| imports 區塊（第 7–11 行後） | `import logging` |
| constants 區塊前（第 13 行前） | `logger = logging.getLogger(__name__)` |

### 第 3 步：套 `evaluate_task_record` 內的 logging 呼叫

| 原始行號 | 插入位置 | 等級 | 訊息 |
|:--------:|----------|:----:|------|
| 162 前 | 進入點（`if not isinstance(record, dict)` 之前） | INFO | `eval_gate v%s: evaluating task record` |
| 163 後 | `invalid_record` 回傳之前 | WARNING | `eval_gate: invalid record (not a dict)` |
| 171 後 | `malformed_record` 回傳之前 | WARNING | `eval_gate: malformed record — %s` |
| 193 前 | tags 迴圈結束、回傳 verdict 之前 | INFO | `eval_gate: tags fired — %s`（if tags） |
| 193 前 | 同上（else 分支） | INFO | `eval_gate: passed, no tags fired` |

### 第 4 步：最後核對註解、import 與邊界

- [ ] `# ── 模組級 logger ──` 註解存在
- [ ] `# 80% of ...` 註解在 `CONTEXT_HEAVY_RATIO` 旁
- [ ] `# 基礎設施風險錯誤類型：...` 註解在 `INFRA_RISK_ERROR_TYPES` 旁
- [ ] `# 規則函數型別別名：...` 註解在 `RuleFn = ...` 旁
- [ ] `# ── 五條核心規則 ──` 區塊分隔存在
- [ ] `# 規則註冊表（tuple，不可變）...` 區塊註解在 `_RULES` 前
- [ ] `import logging` 在 import 區塊內
- [ ] `logger = logging.getLogger(__name__)` 在 constants 前

---

## 5. 套用後最小驗證清單

### 5.1 靜態驗證（不需 venv）

| # | 驗證項目 | 方式 | 預期結果 |
|:-:|----------|------|----------|
| 1 | 檔案可載入 | `python -c "from observability.eval_gate import evaluate_task_record; print('OK')"` | `OK` |
| 2 | evaluate_task_record 介面未變 | `python -c "import inspect; sig=inspect.signature(evaluate_task_record); print(sig)"` | `(record, *, disabled_tags=None)` |
| 3 | 回傳 keys 一致 | `python -c "r=evaluate_task_record({'success':True,'retry_count':0,'handoff_count':0}); assert set(r.keys())=={'pass','tags','reasons','eval_gate_version'}"` | 無 assert error |
| 4 | logging 不造成 import error | `python -c "import logging; logging.basicConfig(level=logging.INFO); from observability.eval_gate import *"` | `OK` |
| 5 | 無新增第三方依賴 | `python -c "import observability.eval_gate; print(__import__('sys').modules)"` 檢查無 site-packages 新增 | 僅 stdlib 模組 |

⚠️ **指令 #1–5 依賴對應 venv / PYTHONPATH**。若無法執行，在下方「套用後障礙」記錄。

### 5.2 測試驗證（推測指令，需確認環境）

```bash
# 推測：在 gov_core_system venv 下執行
python -m pytest tests/test_eval_gate.py tests/test_eval_gate_contract.py -v --tb=short
```

| 測試檔案 | 覆蓋範圍 | 通過條件 |
|----------|----------|----------|
| `tests/test_eval_gate.py` | 5 條規則 + boundary | 全部 PASS |
| `tests/test_eval_gate_contract.py` | logging_adapter → eval_gate 整合 | 全部 PASS |

若測試環境不可用，註記 `needs-confirmation`。

### 5.3 CLI 入口名稱未變

| CLI | 驗證方式 |
|-----|----------|
| eval_exporter | `python -m observability.eval_exporter --help` |
| eval_ci_check | `python -m observability.eval_ci_check --help` |
| eval_stats | `python -m observability.eval_stats --help` |

（三個 CLI 入口皆不依賴 `eval_gate.py` 的內部函數結構，僅依賴 `evaluate_task_record` 簽名 — 該簽名未變。）

---

## 6. 套用後障礙記錄

> 執行套用後由人類 / Cursor 填寫。

| # | 障礙類型 | 描述 | 如何解決 |
|:-:|----------|------|----------|
| — | — | — | — |

---

## 7. 人工確認欄位

| 項目 | 值 |
|------|-----|
| **approved** | ⬜ yes / ⬜ no / ⬜ partial |
| **approver** | （姓名 / agent） |
| **date** | YYYY-MM-DD |
| **note** | — |
| **applied_at** | YYYY-MM-DD HH:MM |
| **test_result** | （PASS / FAIL / N/A） |
| **commit_ref** | （git hash 或 PR #） |

---

## 8. 套用後的 DEBT_LOG 更新建議

| Debt ID | 目前狀態 | 套用後狀態 |
|---------|:--------:|:----------:|
| D-001 | `fixed_suggested` | → `fixed_in_repo` |
| D-003 | `fixed_suggested` | → `fixed_in_repo` |
| D-010 | `fixed_suggested` | → `fixed_in_repo` |

---

## 9. 下一步

- [ ] 人類 / Cursor 閱讀 APPLY_PLAYBOOK.md 瞭解流程。
- [ ] 執行 Step 2：人工 diff 審核（可對照 §3 不變項清單）。
- [ ] 在 §7 簽署 `approved`。
- [ ] 執行 Step 4：套入 repo（建議按 §4 順序：docstring → import/logging → log 呼叫 → 註解）。
- [ ] 執行 Step 5：最小驗證（§5.1）。
- [ ] 若測試環境可用，執行 Step 6（§5.2）。
- [ ] 回報結果：使用 APPLY_CONFIRM_TEMPLATE.md。
- [ ] 若環境不可用，在 §6 記錄障礙。