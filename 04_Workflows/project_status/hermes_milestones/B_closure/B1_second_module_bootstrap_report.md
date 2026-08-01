# B-1 Second Module Bootstrap Report

> 建立：2026-05-30
> 類型：milestone B-1 階段性報告
> 上層：`/mnt/d/hermes-workspace/milestones/B_closure/`

---

## 1. 選定的第二模組名稱與理由

| 項目 | 值 |
|------|-----|
| **模組名稱** | `eval_exporter` |
| **真實 repo 路徑**（推測） | `observability/eval_exporter.py` |

**理由（3 點）**：

1. **與 eval_gate 最接近**：在同一目錄（`observability/`）、同一模組群（D4 Observability）、直接 import `evaluate_task_record`。路徑已確認存在於 ARCH.md 的 repo 目錄結構圖中。
2. **體量適中**：推測 278 行（vs eval_gate 199 行），有對應測試 `tests/test_eval_exporter.py`（推測 111 行），適合做第 2 個閉環驗證。
3. **有已知的跨檔案耦合問題**：D-005（`_total_context_tokens` 重複實作）正好連接 eval_gate 和 eval_exporter。第二模組的 discovery/scan 自然能驗證這個跨檔案 debt，並為 B-3（跨檔案 debt 處理 SOP）提供實際案例。

---

## 2. 新建的目錄與檔案

### 目錄

```
/mnt/d/hermes-workspace/infra_owner/eval_exporter/
├── 00_skill/
├── 10_memory/
├── 20_runtime/
└── 90_runs/
```

### 檔案（16 份）

| # | 路徑 | 動作 | 來源 |
|---|------|:----:|------|
| 1 | `00_skill/SKILL_EVAL_EXPORTER_HYGIENE_OWNER.md` | 新建（基於 eval_gate 版替換名稱）| eval_gate |
| 2 | `10_memory/ARCH.md` | 新建（全部 unknown，佔位）| 自建 |
| 3 | `10_memory/STYLE.md` | 新建（通用慣例，eval_exporter 化）| eval_gate（改寫）|
| 4 | `10_memory/DEBT_LOG.md` | 新建（空表 + 完整狀態機）| eval_gate（清空 debt）|
| 5 | `10_memory/PLAYBOOK.md` | 新建（占位模板，保留通用 P-001~P-006）| eval_gate（清空特定內容）|
| 6 | `20_runtime/PIPELINE.md` | 新建（全部 unknown）| 自建 |
| 7 | `20_runtime/TASK_INTAKE_TEMPLATE.md` | **直接複製** | eval_gate |
| 8 | `20_runtime/REPORT_TEMPLATE.md` | **直接複製** | eval_gate |
| 9 | `20_runtime/APPLY_PLAYBOOK.md` | **直接複製** | eval_gate |
| 10 | `20_runtime/APPLY_CONFIRM_TEMPLATE.md` | **直接複製** | eval_gate |
| 11 | `eval_exporter_bootstrap_plan.md` | 新建（bootstrap 計畫 + 確認列表）| 自建 |
| 12 | `eval_exporter_discovery_task.md` | 新建（7 步驟任務說明 + 產出）| 自建 |
| 13 | `eval_exporter_readonly_scan_task.md` | 新建（6 維度檢查 + 特有檢查項）| 自建 |
| 14 | `90_runs/YYYY-MM-DD_eval_exporter_bootstrap.md` | 新建（bootstrap run note 佔位）| 自建 |
| 15 | `90_runs/YYYY-MM-DD_eval_exporter_discovery.TEMPLATE.md` | 新建（空白 discovery run note 模板）| 自建 |
| 16 | `90_runs/YYYY-MM-DD_eval_exporter_scan_readonly.TEMPLATE.md` | 新建（空白 scan run note 模板）| 自建 |

---

## 3. 直接復用 vs TODO 標記

### ✅ 直接復用的部分（不需修改）

| 項目 | 來源 | 備註 |
|------|------|------|
| `TASK_INTAKE_TEMPLATE.md` | eval_gate → cp | 完全通用 |
| `REPORT_TEMPLATE.md` | eval_gate → cp | 完全通用 |
| `APPLY_PLAYBOOK.md` | eval_gate → cp | 完全通用，內容不綁定模組名 |
| `APPLY_CONFIRM_TEMPLATE.md` | eval_gate → cp | 完全通用 |
| 目錄結構（00_skill / 10_memory / 20_runtime / 90_runs）| A_closure 模板 §2 | 完全照抄 |
| SKILL 檢查清單（§2 六個維度）| eval_gate | 通用清單，不綁定模組名 |
| DEBT_LOG 狀態機（8 種狀態 + 流轉圖 + 轉換慣例）| eval_gate | 通用定義 |
| PLAYBOOK P-001~P-006（flaky / except / docstring / type / deps / logging）| eval_gate | 通用情境 |

### ⚠️ 已替換但標 TODO 的部分

| 項目 | TODO 內容 | 何時完成 |
|------|----------|----------|
| `ARCH.md` 全部內容 | 標 unknown，需 discovery 後填入 | discovery 執行後 |
| `PIPELINE.md` 全部內容 | 標 unknown，需 discovery 後填入 | discovery 執行後 |
| `STYLE.md` §2/3/4/8 實際慣例 | 全為通用推測，待確認 | discovery 後 |
| `STYLE.md` §9 Logging 慣例 | placeholder 狀態（非 confirmed）| review gate 後 |
| `PLAYBOOK.md` P-007（eval_exporter 特有問題）| 現為空佔位 | scan 後 |
| `DEBT_LOG.md` 現有條目 | 空表，無 debt | scan 後填入 |
| `90_runs/` 下的 .TEMPLATE.md | 3 份佔位模板 | 實際執行時複製 |
| 4 份 run notes（fix_round / review / apply_plan / apply_result）| 尚未建立 | follow SOP 逐步建立 |

### 不同於 eval_gate bootstrap 的設計選擇

| 項目 | eval_gate 做法 | eval_exporter 做法 | 理由 |
|------|---------------|-------------------|------|
| **任務說明文件** | 無獨立的 task 文件（僅在 run note 中規劃下一步）| 新增 3 份 task 文件（bootstrap_plan + discovery_task + scan_task）| 讓未來執行時不需回頭讀 A_closure SOP，任務本身即包含說明 |
| **PIPELINE.md** | 有推測的測試指令（從只讀掃描推測）| 全部 unknown | 不重複推測（eval_exporter 尚未被只讀掃描）|
| **STYLE.md §9** | 直接標 proposed | 標 placeholder | 不假設值（eval_exporter 可能有不一樣的 logging pattern）|

---

## 4. 對未來開跑第二模組 owner 任務的建議（3 條，依優先順序）

### 建議 1（最高優先）：按 SOP Step 2 執行 discovery

這是第一步也是最重要的一步。重點驗證：

- `observability/eval_exporter.py` 是否確實存在（278 行）
- import 了哪些 eval_gate 的函數/常數
- 是否存在「與 eval_gate 重複的欄位存取邏輯」（D-005 的實際面貌）
- 測試 `tests/test_eval_exporter.py` 是否可執行

**準備工作**：已準備好 discovery task 說明文件 + 空白 run note 模板。執行時只需替換 `YYYY-MM-DD`。

### 建議 2（次優先）：利用 D-005（跨檔案重複）來檢驗 B-3 SOP

B-1 選 eval_exporter 的重要原因之一就是 D-005：
> `_total_context_tokens` 在 eval_gate 和 eval_exporter 中重複實作。

如果 discovery 確認這個重複確實存在，這就是 B-3（跨檔案 debt 處理 SOP）的第零號測試案例。建議 discovery 階段專門記錄：
- 兩處函數的簽名是否一致
- 回傳值型別是否一致
- 是否可直接由一個檔案 import 另一個

### 建議 3（低優先但值得做）：在 scan 階段產生至少 5 條 debt

eval_gate scan 產生了 10 條 debt（D-001 ~ D-010）。eval_exporter 比 eval_gate 大（278 vs 199 行）、有 CLI、有檔案 I/O，預期 debt 數量應在 5–8 條。

如果 scan 發現 debt < 3 條，可能是掃描深度不夠 — 建議檢視：
- 錯誤處理（檔案 I/O 路徑）
- 日誌覆蓋（CLI 工具常見零日誌）
- 型別（eval_gate 的回傳在 exporter 中如何消費）
