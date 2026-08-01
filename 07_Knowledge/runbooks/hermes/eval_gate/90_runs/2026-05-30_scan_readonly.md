# Run Note: 2026-05-30 — eval_gate 第一次 Infra Hygiene 掃描（只讀模式）

> **任務**：對 eval_gate 模組執行第一次 infra hygiene 掃描（只讀）。
> **執行者**：Hermes Agent
> **日期**：2026-05-30
> **模式**：read-only | 未修改任何 repo 原始碼
> **前提**：ARCH.md、PIPELINE.md 已在前次探路更新；DEBT_LOG.md 為空表。

---

## 1. Scope / Non-Scope

### Scope（本輪涵蓋）

| 類別 | 檔案 | 重點 |
|------|------|------|
| 核心引擎 | `observability/eval_gate.py` (199 行) | 5 條規則 + `evaluate_task_record` API |
| CLI 匯出 | `observability/eval_exporter.py` (278 行) | `eval_exporter` JSONL 入口 |
| CLI CI | `observability/eval_ci_check.py` (193 行) | `eval_ci_check` 取樣 + ratio 入口 |
| CLI 分析 | `observability/eval_stats.py` (588 行) | `eval_stats` 分布 + 建議入口 |
| 外部依賴 | `contract/constants.py` (1 行) | `MAX_TOTAL_TOKEN_BUDGET` |

檢查維度：
- §2 結構與依賴（分層、import、循環依賴風險）
- §3 規則設計與可維護性（命名、條件複雜度、隱性耦合）
- §4 CLI 介面一致性（參數命名、輸出格式、錯誤處理 / exit code）
- §5 各 hygiene 維度（合約、錯誤處理、型別、日誌、測試、技術債）

### Non-Scope（明確排除）

| 元件 | 排除原因 |
|------|----------|
| `core/langgraph_flow_k2.py` | 上游消費者 — 不屬 eval_gate 模組 |
| `core/k2_merge_adapter.py` | 下游消費者 — 不屬 eval_gate 模組 |
| `core/k2_ask_shadow.py` | 下游消費者 — 不屬 eval_gate 模組 |
| `observability/logging_adapter.py` | 周邊模組，非 eval_gate 規則引擎本體 |
| `observability/ibridge_exporter.py` | 周邊模組，非 eval_gate 規則引擎本體 |
| `tests/` 目錄全部檔案 | 測試 infra，本次只記錄測試存在性（不檢查測試品質） |
| CI/CD 管線定義 | PIPELINE.md 已記錄「無可用資訊」；本次不重複追查 |

---

## 2. 模組摘要

引用 `10_memory/ARCH.md` 關鍵資訊：

- **定位**：D4 Observability 之下的純規則引擎。
- **版本**：v0.2（`EVAL_GATE_VERSION = "0.2"`）。
- **輸入**：task record dict（來自 M-line 或 ibridge）。
- **輸出**：結構化 verdict `{pass, tags, reasons, eval_gate_version}`。
- **規則數**：5 條硬編碼規則，無 LLM，無第三方套件，無資料庫。
- **依賴**：僅 `contract.constants.MAX_TOTAL_TOKEN_BUDGET`（128,000）。
- **消費者鏈**：k2_langgraph_flow → eval_gate → verdict → merge_adapter / ask_shadow。
- **CLI**：3 個入口（exporter / ci_check / stats）。

---

## 3. 結構與依賴檢查

### 3.1 檔案內部分層

eval_gate.py（199 行）的內部結構：

| 區塊 | 行號 | 內容 | 評分 |
|------|------|------|------|
| Imports | 7–11 | `__future__`, `typing`, `contract.constants` | ✅ 乾淨 |
| Constants | 13–22 | 4 個門檻常數 + 1 個 frozenset | ✅ 清楚 |
| Schema 定義 | 24–28 | `_REQUIRED_FIELDS` tuple | ✅ 可讀 |
| Helper 函數 | 31–77 | `_collect_schema_issues`, `_int_field`, `_float_field`, `_total_context_tokens`, `_error_type` | ⚠️ 見下方 |
| Type alias | 80 | `RuleFn` | ✅ 清楚 |
| 規則函數 | 83–139 | 5 個 `_rule_*` 函數 | ⚠️ 無 docstring |
| 規則註冊表 | 133–139 | `_RULES` tuple | ⚠️ 無 docstring |
| 公開 API | 142–199 | `evaluate_task_record` | ✅ docstring 完整 |

**觀察**：分層合理，但存在可進一步分離的 util：

- `_int_field`、`_float_field` 是通用 dict-safe 取值函數，與具體規則無關 — 適合抽成 `_field_utils`。
- `_total_context_tokens`、`_error_type` 是 record-specific 欄位萃取器 — 與規則邏輯耦合，但本質是 schema adapters。
- `_collect_schema_issues` 是 schema validation — 邏輯上不同於規則評估，但放在同檔案可接受。

### 3.2 Import 依賴

| Import | 來源 | 類型 | 風險 |
|--------|------|------|------|
| `from __future__ import annotations` | stdlib | — | 無 |
| `from typing import Any, Callable, Final` | stdlib | — | 無 |
| `from contract.constants import MAX_TOTAL_TOKEN_BUDGET` | 內部模組 | 跨模組 | 低 |

**循環依賴風險**：`contract/constants.py` 僅一行常數定義，無任何 import，無循環依賴風險。

**第三方依賴**：無（100% stdlib）。

### 3.3 與周邊模組的耦合點

| 耦合點 | 檔案 | 問題 |
|--------|------|------|
| `_total_context_tokens` | `eval_gate.py:62–70` / `eval_exporter.py:35–43` | **重複實作** — 兩處邏輯幾乎相同 |
| `_trace_completeness_score` | `eval_exporter.py:46–54` | eval_gate 內無此函數，但 `_rule_observability_gap` 透過 `_float_field(record, ("trace_completeness", "score"))` 存取相同路徑 — 欄位路徑隱性耦合 |
| `KNOWN_GATE_TAGS` | `eval_stats.py:24–32` | 硬編碼 5 個 tag，若 eval_gate 新增規則需同步更新 |

---

## 4. 規則設計與可維護性檢查

### 4.1 命名品質

| 函數 | Tag | 評估 |
|------|-----|------|
| `_rule_high_retry` | `high_retry` | ✅ 清楚 |
| `_rule_context_heavy` | `context_heavy` | ✅ 清楚 |
| `_rule_many_handoffs` | `many_handoffs` | ✅ 清楚 |
| `_rule_infra_risk` | `infra_risk` | ✅ 清楚 |
| `_rule_observability_gap` | `observability_gap` | ✅ 清楚 |

Tag 命名一致使用 snake_case，語意明確，無前綴/命名空間衝突。

### 4.2 條件複雜度

所有 5 條規則均為**單一布林條件**（一行比較），無複合 `and/or/not`，無巢狀分支。複雜度極低 → 高維護性。

### 4.3 比較運算子一致性

| 規則 | 運算子 | 門檻 | 備註 |
|------|--------|------|------|
| `high_retry` | `>=` | 2 | 對稱 |
| `context_heavy` | `>` | 102,400 | **不一致** — 其他規則用 `>=` |
| `many_handoffs` | `>=` | 3 | 對稱 |
| `observability_gap` | `<` | 0.8 | 方向不同（反比），可接受 |

⚠️ **發現**：`context_heavy` 使用 `>`（strict），而 `high_retry`、`many_handoffs` 使用 `>=`（non-strict）。這不是 bug（80% 為 boundary，`>` vs `>=` 只差一個 token），但違反 uniformity 原則。見 DEBT_LOG **D-004**。

### 4.4 隱性耦合到上游欄位

| 規則 | 存取的欄位路徑 | 耦合風險 |
|------|----------------|----------|
| `high_retry` | `record["retry_count"]` | 低 — 頂層必填欄位 |
| `context_heavy` | `record["context_token_usage"]["total_tokens"]` | **中** — 雙層嵌套，假設存在 dict 且 key 為 `total_tokens` |
| `many_handoffs` | `record["handoff_count"]` | 低 — 頂層必填欄位 |
| `infra_risk` | `record["error_type"]` | 低 — 頂層可選欄位 |
| `observability_gap` | `record["trace_completeness"]["score"]` | **中** — 雙層嵌套，假設存在 dict 且 key 為 `score` |

⚠️ **發現**：兩條規則（context_heavy、observability_gap）透過嵌套欄位路徑存取上游結構，但未在程式碼或 docstring 中記錄預期的 schema contract。若上游 ibridge record 格式變更（例如重新命名 `context_token_usage` → `token_usage`），規則會靜默回傳 default 值而不報錯。見 DEBT_LOG **D-006**。

### 4.5 規則間互動

- 規則獨立執行，無彼此依賴 ✅
- 去重邏輯在 `evaluate_task_record` 第 190 行（`if tag not in tags`）— 防止同一 tag 因某些 edge case 出現兩次 ✅
- `disabled_tags` 機制可在呼叫端選擇性跳過特定規則 ✅

---

## 5. CLI 介面檢查

### 5.1 參數命名一致性

| 參數 | eval_exporter | eval_ci_check | eval_stats |
|------|:--:|:--:|:--:|
| `input_path` (positional) | ✅ | ✅ | ✅ (`paths`, nargs=+) |
| `--output` / `-o` | ✅ | — | `--write-report`（語意不同） |
| `--limit` | — | ✅ | — |
| `--max-needs-review-ratio` | — | ✅ | — |
| `--min-samples` | — | ✅ | ✅ (`--min-samples`) |
| `--filter` | ✅ (`gate_filter`) | — | — |
| `--fail-on-tags` | — | ✅ | — |
| `--group-by` | — | — | ✅ |
| `--format` | — | — | ✅ (json/text) |

**評估**：三個 CLI 入口參數命名整體一致，`--min-samples` 在 ci_check 和 stats 間匹配。`--output` vs `--write-report` 語意不同但合理（exporter 輸出資料，stats 輸出報告）。

### 5.2 輸出格式穩定性

| CLI | stdout 格式 | 可機器讀取 |
|-----|------------|:--:|
| eval_exporter | JSON（`json.dumps`） | ✅ |
| eval_ci_check | JSON（`json.dumps` with indent=2） | ✅ |
| eval_stats | JSON（default）或 text（`--format text`） | ✅ |

三個 CLI 都輸出結構化 JSON（至少預設模式），可被下游 script 解析。

### 5.3 錯誤處理與 Exit Code

| CLI | Exit 0 條件 | Exit 1 條件 | 錯誤處理範圍 |
|-----|------------|------------|-------------|
| eval_exporter | `result["ok"] == True` | `ok == False` | argparse error（argparse 內建） |
| eval_ci_check | `result["ok"] == True` | `ok == False` | argparse + `max_needs_review_ratio` range check + `OSError/ValueError/JSONDecodeError` |
| eval_stats | `result["ok"] == True` | `ok == False`（檔案不存在、讀取失敗、零列） | argparse + `OSError/ValueError` |

**評估**：三個 CLI 都使用 `main()` → `sys.exit(main())` 模式，exit code 語意一致（0=pass, 1=fail）。ci_check 和 stats 有基本的 I/O 錯誤捕捉；exporter 依賴 argparse 和內部 `FileNotFoundError`（會讓 Python crash 而非回傳結構化錯誤 — 見 DEBT_LOG **D-007** 相關）。

### 5.4 CLI docstring vs 實際行為

- eval_exporter: docstring 提到 `--filter` 但 CLI 定義是 `--filter`（匹配） ✅
- eval_ci_check: docstring 中的 usage 範例與參數定義一致 ✅
- eval_stats: docstring 中的 usage 範例與參數定義一致 ✅

---

## 6. Hygiene 逐項檢查

以下對齊 `00_skill/SKILL_INFRA_HYGIENE_OWNER.md` §2 的六個檢查維度。

### 6.1 合約檢查（Contract）

| 項目 | 狀態 | 備註 |
|------|:--:|------|
| 公開函數 docstring | ⚠️ | `evaluate_task_record` 有完整 docstring；5 條規則函數全部無 docstring |
| docstring 包含 Args/Returns/Raises | ⚠️ | `evaluate_task_record` 有 Args/Returns，但缺 Raises |
| 回傳型別註記 | ⚠️ | 回傳 `dict[str, Any]` 而非 TypedDict — 結構已知但未型別化 |
| 對外 API 有 OpenAPI/protocol 定義 | N/A | 非 HTTP API，不適用 |

### 6.2 錯誤處理（Error Handling）

| 項目 | 狀態 | 備註 |
|------|:--:|------|
| bare `except:` 或 `except Exception` | ✅ | 無裸 except；全部使用具體例外類型 |
| 檢查點拋出具體例外 | ✅ | 所有 raise 皆為 `ValueError` 或 `FileNotFoundError` |
| 遺漏的 I/O/網路/子程序路徑 | ✅ | eval_gate.py 無 I/O；CLI 工具有捕捉 `OSError` |
| 規則函數內未捕捉例外 | ⚠️ | 若規則函數拋出非預期例外，`evaluate_task_record` 不會攔截（見 **D-007**） |

### 6.3 型別與介面（Type & Interface）

| 項目 | 狀態 | 備註 |
|------|:--:|------|
| 新增或變更參數有 type hint | ✅ | 所有參數有 hint（`dict[str, Any]`、`frozenset[str]`） |
| 回傳值與 docstring 一致 | ✅ | 實際回傳結構與 docstring 描述吻合 |
| `Any` 過度使用 | ⚠️ | 輸入 `dict[str, Any]` 必要；回傳 `dict[str, Any]` 可用 TypedDict 改進 |
| Protocol / ABC 同步 | N/A | 無類別或繼承 |

### 6.4 日誌與可觀測性（Logging & Observability）

| 項目 | 狀態 | 備註 |
|------|:--:|------|
| 關鍵決策點有 INFO 日誌 | ❌ | **零日誌**。`evaluate_task_record` 無任何 logging 呼叫 |
| 錯誤路徑有 WARNING/ERROR 日誌 | ❌ | schema 失敗（invalid/malformed_record）無日誌 |
| 重複計算上游已記錄的資訊 | N/A | 無日誌可檢查 |
| 結構化日誌欄位一致 | N/A | 無日誌 |

⚠️ **重點發現**：eval_gate 為 Observability 模組，自身卻完全無 logging。規則觸發、schema 失敗、gate 判定均無任何可觀測紀錄。見 DEBT_LOG **D-001**。

### 6.5 測試穩定性（Test Hygiene）

| 項目 | 狀態 | 備註 |
|------|:--:|------|
| 新功能有對應測試 | ⚠️ | 受限於未知 CI / 測試環境 — 測試檔案存在（5 個 .py），但無法實際執行驗證通過率 |
| flaky 測試 | ⚠️ | **無法判斷** — 受限於未知 CI / 測試環境，無測試執行歷史可查 |
| 測試依賴外部服務未 mock | ✅ | 測試使用 `tests/fixtures/eval/ibridge_records.jsonl`，無外部服務依賴 |
| 測試 hardcoded fixture 過時 | ⚠️ | **無法判斷** — fixture 內容未經 diff 對照 |

**受限於未知 CI / 測試環境的影響**：
- 無 `.github/workflows/`、無 root Makefile、無 `.coveragerc`。
- 測試檔案存在（unittest + pytest runner），但無法確認：實際通過率、pytest 版本、coverage 數據。
- 因此本輪無法對 flaky 測試或 coverage 缺口給出精確判斷。

### 6.6 技術債（Debt Tracking）

| 項目 | 狀態 | 備註 |
|------|:--:|------|
| TODO / FIXME / HACK 註解 | ✅ | eval_gate.py 原始碼中無任何此類註解 |
| 暫行解法超過合理生命週期 | N/A | 未發現 |
| deprecated 程式碼清理排程 | N/A | 未發現 |

---

## 7. 問題總表（引用 DEBT_LOG）

| Debt ID | 檔案:行號 | 嚴重度 | 摘要 |
|---------|-----------|:--:|------|
| D-001 | `eval_gate.py:1–199` | **P1** | 零日誌 — 規則觸發與 schema 失敗皆無 logging |
| D-002 | `eval_gate.py:142–199` | P2 | 回傳型別 `dict[str, Any]` 可用 TypedDict 改進 |
| D-003 | `eval_gate.py:83–139` | P2 | 5 條規則函數與 helper 函數無 docstring |
| D-004 | `eval_gate.py:93–103` | P2 | `_rule_context_heavy` 使用 `>` 而其他規則用 `>=`（比較運算子不一致） |
| D-005 | `eval_gate.py:62–70` / `eval_exporter.py:35–43` | P2 | `_total_context_tokens` 邏輯在兩處重複實作 |
| D-006 | `eval_gate.py:93–130` | **P1** | 規則直接存取嵌套欄位（`context_token_usage.total_tokens`、`trace_completeness.score`）— 隱性耦合到上游 schema |
| D-007 | `eval_gate.py:183–192` | P2 | 規則迴圈無 try/except — 若規則函數拋出例外會穿透 `evaluate_task_record` |
| D-008 | `eval_stats.py:24–32` | P2 | `KNOWN_GATE_TAGS` 硬編碼 5 個標籤，需手動同步 |
| D-009 | `eval_gate.py:142–199` | P2 | `disabled_tags` 參數有實作但無呼叫端使用，且無測試覆蓋 |
| D-010 | `eval_gate.py:133–139` | P3 | `_RULES` 註冊表無 docstring 說明註冊慣例 |

---

## 8. 建議下一輪行動（最多 5 條，優先小步自動修正）

### N-1（最小風險）：為規則函數補 docstring
- 對象：`_rule_high_retry`、`_rule_context_heavy`、`_rule_many_handoffs`、`_rule_infra_risk`、`_rule_observability_gap`
- 內容：每條至少 `Returns: (tag, reason) tuple or None` + 觸發條件一句話
- 預估：∼30 行新增，不改變行為，可立即合併

### N-2（低風險）：為 eval_gate 加入 minimal logging
- 方案：`import logging; logger = logging.getLogger(__name__)`
- 在 `evaluate_task_record` 中：
  - `logger.info` 記錄 pass/fail 與觸發的 tags
  - `logger.warning` 記錄 malformed_record / invalid_record
- 預估：∼10 行新增 + 1 個 import

### N-3（低風險）：從 eval_exporter.py 消除 `_context_tokens_total` 重複
- 方案：eval_exporter.py 直接 import `_total_context_tokens` from eval_gate（或抽取共用 util）
- 預估：刪除 eval_exporter.py 的 `_context_tokens_total`，import eval_gate 版本

### N-4（中風險）：統一門檻比較運算子
- 對象：`_rule_context_heavy` — 將 `>` 改為 `>=`（或反之，擇一）
- 需確認：門檻 102,400 是否為 boundary value（80% of 128K）
- 預估：1 行修改 + 1 條測試調整

### N-5（中風險）：為嵌套欄位存取補 schema 合約文件
- 對象：`_rule_context_heavy`、`_rule_observability_gap`
- 方案：在 docstring / 註解中記錄預期的 record 結構（`context_token_usage` 為 dict 且含 `total_tokens: int`）
- 預估：∼6 行註解，無行為改變

---

## 9. 限制與免責聲明

- **無法實際執行測試**：受限於未知 CI / 測試環境（無 .github/workflows、無 Makefile），無法確認實際測試通過率、coverage、flaky 狀態。
- **無法驗證 venv**：本輪為只讀掃描，未 activate venv 或執行 `python --version`。
- **所有「待確認假設」項目**：見 `90_runs/2026-05-30_discovery.md` §5（Still-unknown list）。
- **本報告不包含**：對 eval_gate 規則邏輯正確性（correctness）的驗證 — 這屬於 functional owner 範疇，非 infra hygiene 範疇。
