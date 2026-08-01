# eval_exporter Discovery Task

> 本任務定義第一次只讀探路要做的事。
> 基於 A_closure SINGLE_LINE_OWNER_SOP.md Step 2。
> 建立：2026-05-30 | 狀態：task（未執行）

---

## 目標

對 `observability/eval_exporter.py` 執行第一次只讀探路，定位模組在系統中的角色、公開介面、依賴鏈、消費者、測試環境。

---

## 執行步驟

### 1. 確認模組位置

- [ ] 確認 `observability/eval_exporter.py` 存在（repo 路徑）
- [ ] 記錄檔案行數與主要區塊（imports / constants / functions / CLI）
- [ ] 記錄檔案 docstring（模組定位描述）

### 2. 公開介面掃描

- [ ] 列出所有公開函數名稱與簽章
- [ ] 列出所有公開常數
- [ ] 列出 CLI 入口（`def main` / `if __name__`）
- [ ] 記錄回傳結構（如果與 eval_gate 有關，記錄關係）

### 3. 依賴鏈

- [ ] 列出所有 import（區分 stdlib vs 內部 vs 第三方）
- [ ] 特别留意是否 import `evaluate_task_record` from eval_gate
- [ ] 確認是否有第三方套件依賴

### 4. 消費者

- [ ] 搜尋誰 import / 使用 eval_exporter
- [ ] 記錄呼叫方式（CLI 直接執行 vs 程式庫 import）

### 5. 測試

- [ ] 確認 `tests/test_eval_exporter.py` 存在
- [ ] 記錄測試檔案行數與測試數量
- [ ] 記錄測試 fixture 路徑（如有）
- [ ] 記錄測試框架（unittest / pytest）

### 6. 更新 ARCH.md

- [ ] 模組定位（填入 §1）
- [ ] 目錄結構（填入 §2）
- [ ] 外部依賴（填入 §3）
- [ ] 公開介面（填入 §4，含 API 簽章 + 回傳結構表 + CLI 表）

### 7. 更新 PIPELINE.md

- [ ] 填入測試指令（推測，標 `needs-confirmation`）
- [ ] 填入 CI/CD 資訊（如果找到）

---

## 產出

- `90_runs/YYYY-MM-DD_eval_exporter_discovery.md`
- `10_memory/ARCH.md` 更新（bootstrap → 實際資訊）
- `20_runtime/PIPELINE.md` 更新（加入測試指令推測）

---

## 注意

- 本輪只讀，不修改任何 repo 檔案
- 所有推測的測試指令必須標 `needs-confirmation`
- 如果 `eval_exporter.py` 實際路徑與推測不同，立即停止並記錄
