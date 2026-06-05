# Phase 8.5 Browser Automation — DOM-based MVP (v0.1)

> **工單編號語意**：本檔的 **「Phase 8.5 Browser Automation」** 為瀏覽器 DOM 自動化抽象工單。  
> **不同軌**：`gov_core_system/output/phase5-8_roadmap.md` 表中 **8.5 Runbook 與 on-call** 為治理／營運路線，與本工單**無對應關係**；引用戰報或里程碑時請用完整工單名稱，避免僅寫「8.5」。

---

## 0. 定位

- **位置**：`04_Workflows/PHASE8_5_BROWSER_AUTOMATION_MVP_v0.1.md`
- **暗部實作**：`gov_core_system/core/browser_actions.py`、`browser_runner.py`
- **目標**：提供 **DOM-based** 的 Action / Runner 抽象與 InMemory adapter，**不綁定** Playwright、Selenium、CDP 或任何外部瀏覽器服務。
- **狀態**：MVP · dev；非 production browser farm。

---

## 1. 範圍

### 1.1 在範圍內

| 項目 | 說明 |
|------|------|
| Action 目錄（6 種） | `navigate`、`wait_for`、`click`、`fill`、`get_text`、`assert_text` |
| Locator 模型 | `strategy` + `value`；見 §3 |
| Plan / Runner | 可序列化 `dict` plan；`run_plan()` 回傳結構化 `dict` |
| InMemory adapter | 邏輯 DOM 樹 + 單元測試；`navigate` 支援 `url` + 可選 `html_fixture` |
| 單元測試 | `tests/test_browser_runner.py` |

### 1.2 非範圍（本輪不做）

- Playwright / Selenium adapter（建議 **8.5b**）
- 修改 `04_Workflows/_scout_engine.py`（HQ 副艙 Playwright）
- `app_api.py` 路由
- `WORKFLOW_INDEX.md` 更新
- `press`、`screenshot`、`evaluate_js`
- 真瀏覽器、網路請求、截圖二進位上傳

---

## 2. 與 roadmap「8.5」區隔

| 來源 | 8.5 含義 |
|------|----------|
| `output/phase5-8_roadmap.md` | Runbook 與 on-call（合併 ops-checklist、deployment-guide、DLQ SOP） |
| **本工單** | Browser Automation DOM-based MVP |

---

## 3. DOM Locator（v0.1）

### 3.1 結構

```json
{
  "strategy": "role",
  "value": "button:Submit",
  "match": "equals"
}
```

| 欄位 | 必填 | 說明 |
|------|------|------|
| `strategy` | 建議必填 | `role` \| `text` \| `css` \| `xpath` |
| `value` | 是 | 策略專用語法（見下表） |
| `match` | 否 | `equals`（預設）\| `contains`；主要用於 `text` / `assert_text` |

### 3.2 策略語法（MVP 子集）

| strategy | value 範例 | 匹配方式 |
|----------|------------|----------|
| `role` | `button` 或 `button:Submit` | `[role]` 或 `role`+可見名稱（`aria-label` / 元素文字） |
| `text` | `Sign in` | 元素累積文字 `equals` / `contains` |
| `css` | `#login`、`button.primary`、`input[name=email]` | CSS 子集（id / class / tag / 單一 `[attr=val]`） |
| `xpath` | `//button`、`//*[@id='x']` | XPath 子集（`//tag`、`//*[@id='…']`） |

### 3.3 Locator 優先順序（解析與 fallback）

當步驟中的 `locator` **未提供 `strategy`**（或 `strategy` 為空）時，Runner／Adapter 以**同一 `value`** 依下列順序嘗試解析，**首個唯一匹配**即採用：

1. **role**
2. **text**
3. **css**
4. **xpath**

若已明確指定 `strategy`，**僅**使用該策略，不再 fallback。

多候選節點且策略要求唯一時：回傳 `AMBIGUOUS_SELECTOR`；無匹配：`SELECTOR_NOT_FOUND`。

---

## 4. Action 目錄（v0.1）

| action | 必填欄位 | 說明 |
|--------|----------|------|
| `navigate` | `url` | 邏輯導頁；可選 `html_fixture`（HTML 字串）載入 InMemory DOM |
| `wait_for` | `locator` | 可選 `state`：`attached`（預設）\| `visible` \| `hidden` |
| `click` | `locator` | 點擊可見、可互動節點 |
| `fill` | `locator`, `value` | 寫入 `input` / `textarea` |
| `get_text` | `locator`, `store_as` | 文字寫入 run `context` |
| `assert_text` | `locator`, `expected` | 可選 `match`：`equals` \| `contains` |

**不包含** `press`（依尚書省拍板）。

### 4.1 Plan 格式

```json
{
  "plan_id": "demo-001",
  "stop_on_error": true,
  "steps": [
    {"action": "navigate", "url": "https://example.test/", "html_fixture": "<html><body><button role=\"button\">Submit</button></body></html>"},
    {"action": "wait_for", "locator": {"strategy": "role", "value": "button:Submit"}, "state": "visible"},
    {"action": "click", "locator": {"strategy": "role", "value": "button:Submit"}},
    {"action": "get_text", "locator": {"strategy": "text", "value": "Submit"}, "store_as": "label"},
    {"action": "assert_text", "locator": {"strategy": "text", "value": "Submit"}, "expected": "Submit"}
  ]
}
```

---

## 5. DomAutomationPort（Adapter 契約）

Adapter 須實作（各步驟回傳小 `dict`：`ok`, `message`, 可選 `error_code`, `data`）：

| 方法 | 對應 action |
|------|-------------|
| `navigate(url, html_fixture=None)` | `navigate` |
| `wait_for(locator, state=...)` | `wait_for` |
| `click(locator)` | `click` |
| `fill(locator, value)` | `fill` |
| `get_text(locator)` | `get_text` |
| `assert_text(locator, expected, match=...)` | `assert_text` |

本輪預設實作：`InMemoryDomAdapter`（無外部服務）。

---

## 6. Runner 回傳契約

`BrowserRunner.run_plan(plan)` → `dict`：

| 鍵 | 型別 | 說明 |
|----|------|------|
| `ok` | bool | 全 plan 是否成功 |
| `message` | str | 摘要 |
| `plan_id` | str \| null | 來自 plan |
| `steps_total` | int | 步驟數 |
| `steps_ok` | int | 成功步數 |
| `failed_step_index` | int \| null | 0-based；全成功為 null |
| `steps` | list | 每步 `{index, action, ok, message, error_code?, duration_ms, data?}` |
| `context` | dict | `get_text` 的 `store_as` 累積 |

### 6.1 錯誤碼（MVP）

| code | 說明 |
|------|------|
| `INVALID_ACTION` | 未知 action 或欄位驗證失敗 |
| `INVALID_PLAN` | plan 結構不合法 |
| `SELECTOR_NOT_FOUND` | 無匹配節點 |
| `AMBIGUOUS_SELECTOR` | 多於一個匹配 |
| `WAIT_STATE_FAILED` | `wait_for` 狀態不符 |
| `ASSERT_TEXT_FAILED` | 文字斷言失敗 |
| `NAVIGATION_FAILED` | 導頁／fixture 解析失敗 |

---

## 7. 驗收

在 `gov_core_system` venv 根目錄：

```text
python -m unittest tests.test_browser_runner -v
```

- 全部 OK
- `core/browser_runner.py`、`browser_actions.py` **不得** import `playwright` / `selenium`

---

## 8. 後續波次（8.5b 建議，本輪不實作）

| 項目 | 建議位置 |
|------|----------|
| PlaywrightDomAdapter | `gov_agency` 或 `Departments/04_Infrastructure/agents/` |
| `shared/schemas/browser_action_plan_v1.json` | Workbench / API 對接 |
| `WORKFLOW_INDEX.md` 索引節 | HQ 工作流地圖 |
| Orchestrator 掛鉤 | `core/orchestrator.py` 可選步驟 |
| `press` / `screenshot` | 需引擎能力後再定契約 |

---

## 9. 變更紀錄

| 日期 | 說明 |
|------|------|
| 2026-05-21 | v0.1 初稿：DOM MVP 四檔、6 actions、locator 優先順序、與 roadmap 8.5 區隔 |
