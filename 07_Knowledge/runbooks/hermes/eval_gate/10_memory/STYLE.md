# STYLE.md — eval_gate 程式碼風格慣例

> 狀態：bootstrap | 2026-05-30
> ⚠ 本文件目前為通用建議，待實際探索程式碼後應更新為專案實際慣例。

---

## 1. 語言與編碼

- 程式碼使用 Python（版本待確認）
- 所有字串文字使用雙引號（`"`）優先（專案慣例待確認）
- 編碼：UTF-8

---

## 2. 命名慣例

| 類別 | 慣例 | 範例 |
|------|------|------|
| 類別名稱 | PascalCase | `EvalGate`, `GateResult` |
| 函式與方法 | snake_case | `validate_result()`, `apply_rules()` |
| 私有成員 | 前置底線 `_` | `_rules`, `_apply_gate()` |
| 常數 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| 模組全域變數 | 避免，必要時用 `MODULE_VAR` | — |

**實際慣例待確認**。

---

## 3. Import 順序

```
# 1. 標準函式庫
import os
import json
from dataclasses import dataclass
from typing import Optional

# 2. 第三方套件
import pytest
import yaml

# 3. 內部模組
from eval_gate.core import Gate
from eval_gate.models import EvalResult
```

**實際慣例待確認**。

---

## 4. Docstring 格式

建議使用 Google-style docstring：

```python
def validate_result(result: EvalResult, rules: list[GateRule]) -> bool:
    """評估結果是否符合所有閘門規則。

    Args:
        result: 待驗證的評估結果。
        rules: 要套用的閘門規則列表。

    Returns:
        通過所有規則回傳 True，否則 False。

    Raises:
        ValidationError: 當 result 或 rules 格式不正確時。
    """
```

**實際使用格式待確認**。

---

## 5. Type Hint

- 所有公開函數必須有完整 type hint
- 優先使用 `list[X]`、`dict[K, V]` 而非 `typing.List[X]`、`typing.Dict[K, V]`
- 避免過度使用 `Any`，除非真的無法給出具體型別
- 回傳值為 `None` 的函數需標註 `-> None`

**實際型別規範待確認**。

---

## 6. 錯誤處理風格

- 只捕捉你能處理的例外，捕捉後記錄（logging）並轉換為具體例外類型
- 避免裸 `except:` 或 `except Exception`
- 自訂例外繼承自具體異常（如 `ValueError`、`RuntimeError`）或自訂基礎例外

```python
class GateValidationError(ValueError):
    """閘門驗證失敗時拋出。"""
```

---

## 7. 註解風格

- `# TODO(username): YYYY-MM-DD: 說明` — 即將處理的事項
- `# FIXME: 說明` — 已知有問題但暫不解
- `# HACK: 說明` — 不優雅的暫行解法
- `# XXX: 說明` — 危險或需要注意的程式碼
- 所有 TODO / FIXME / HACK 必須在 DEBT_LOG.md 中有對應條目

---

## 8. 格式化工具

待確認專案是否使用：
- Ruff / Black（formatter）
- Ruff / Flake8 / pylint（linter）
- mypy / pyright（type checker）
- isort（import 排序）

**確認後更新本節**。

---

## 9. Logging 慣例

> 確認日期：2026-05-30（v1 patch review） | 狀態：confirmed

### 9.1 Logger 取得方式

模組層級建立 logger，使用 `__name__`：

```python
import logging

logger = logging.getLogger(__name__)
```

### 9.2 等級使用原則

| 等級 | 使用時機 | 範例 |
|------|----------|------|
| `INFO` | 評估開始/結束、規則觸發、關鍵決策點 | `logger.info("eval_gate v%s: evaluating task record", EVAL_GATE_VERSION)` |
| `WARNING` | schema 驗證失敗、欄位型別不符預期、fallback 到 default 值 | `logger.warning("eval_gate: malformed record: %s", schema_issues)` |
| `ERROR` | 非預期例外、無法恢復的錯誤 | `logger.error("eval_gate: unexpected error in rule %s: %s", rule_name, exc)` |
| `DEBUG` | 欄位萃取細節、個別規則判定（不觸發的 case 不記錄） | `logger.debug("_rule_high_retry: count=%d threshold=%d", count, threshold)` |

### 9.3 訊息格式

- 前綴模組名（`eval_gate`），後接具體描述。
- 使用 `%s` / `%d` 延遲格式化（`logger.info("msg %s", val)`），避免在日誌等級關閉時仍計算字串。
- 不記錄整個 record dict（可能含敏感資料），僅記錄關鍵摘要欄位。
- 結構化欄位命名使用 snake_case。

### 9.4 不打日誌的情境

- 每條規則的「不觸發」路徑（避免 log 洪水）。
- Helper 函數內部（`_int_field`、`_float_field` 等）— 它們只是取值工具，不是決策點。
- 單一 record 處理中不超過 3 條 INFO log（進入點 + 觸發摘要 or pass）。

### 9.5 數量原則（confirmed by v1 review）

對一個 `evaluate_task_record` 調用，總 log 數量不超過：
- **INFO**：2–3 條（進入 1 條 + 結果 1 條；schema 正常時）。
- **WARNING**：0–2 條（僅當 schema 驗證失敗或資料異常時）。
- **DEBUG**：可選，限於規則內部的靜默 fallback 路徑（見 D-006）。

單次調用總計：**2–5 條**（正常路徑 2–3 條，異常路徑 +1–2 條）。
