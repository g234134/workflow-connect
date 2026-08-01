# eval_exporter Readonly Scan Task

> 本任務定義第一次只讀衛生檢查要做的事。
> 基於 A_closure SINGLE_LINE_OWNER_SOP.md Step 3。
> 建立：2026-05-30 | 狀態：task（未執行）
> ⚠ 必須在 discovery 完成後才可執行本任務。

---

## 前提

- [ ] discovery 已完成（`90_runs/` 下有 discovery run note）
- [ ] ARCH.md 已從 bootstrap 更新為實際資訊
- [ ] 已知道模組的行數、公開介面、外部依賴

---

## 執行步驟

### 1. 6 維度衛生檢查（對照 SKILL §2）

#### 1.1 合約檢查（Contract）
- [ ] 所有公開函數／類別是否有 docstring？
- [ ] docstring 是否包含 Args、Returns、Raises？
- [ ] 回傳型別是否有 type hint？
- [ ] 是否需要 OpenAPI / protocol 定義？

#### 1.2 錯誤處理（Error Handling）
- [ ] 是否存在 bare `except:` 或 `except Exception`？
- [ ] 檢查點是否拋出具體例外類型？
- [ ] 是否有遺漏的 try/except 路徑（I/O、子程序）？

#### 1.3 型別與介面（Type & Interface）
- [ ] 參數有 type hint？
- [ ] 回傳值與 docstring 一致？
- [ ] 是否使用 `Any` 但可更具體？

#### 1.4 日誌與可觀測性（Logging & Observability）
- [ ] 關鍵決策點有 INFO 日誌？
- [ ] 錯誤路徑有 WARNING/ERROR 日誌？
- [ ] 結構化欄位一致？

#### 1.5 測試穩定性（Test Hygiene）
- [ ] 測試檔案存在？
- [ ] 測試有無外部服務依賴？
- [ ] fixture 是否過時？

#### 1.6 技術債（Debt Tracking）
- [ ] TODO / FIXME / HACK 註解掃描
- [ ] 所有發現建立 DEBT_LOG 條目（D-XXX 格式）

### 2. 專注於 eval_exporter 特有的檢查項

- [ ] **與 eval_gate 的耦合度**：是否重複實作了 eval_gate 已有的欄位存取函數？
- [ ] **CLI 參數命名一致性**：與其他 CLI（eval_ci_check、eval_stats）比較
- [ ] **錯誤處理完整性**：檔案 I/O 路徑是否保護？
- [ ] **輸出格式穩定性**：JSONL 格式是否與下游期望一致？

### 3. 更新 DEBT_LOG.md

- [ ] 所有發現填入 DEBT_LOG（含位置、類型、嚴重度）
- [ ] 統計摘要更新為實際數字

---

## 產出

- `90_runs/YYYY-MM-DD_eval_exporter_scan_readonly.md`（掃描報告）
- `10_memory/DEBT_LOG.md` 填入首次 debt 條目
- `10_memory/PLAYBOOK.md`（如有特有問題情境，新增條目）

---

## 與 eval_gate 掃描的差異

| 項目 | eval_gate 做法 | eval_exporter 預期差異 |
|------|---------------|----------------------|
| 5 條規則 docstring 檢查 | 核心規則函數無 docstring | 不適用（eval_exporter 不是規則引擎） |
| CLI 入口數 | 3 個 | 預期 1 個（`eval_exporter`） |
| 嵌套欄位耦合 | `context_token_usage.total_tokens` | 預期無嵌套欄位（僅讀 eval_gate 回傳） |
| 與上游耦合 | 無 | **預期強耦合** — 直接 import eval_gate |
| 重複實作風險 | D-005（`_total_context_tokens`） | **預期發現** — 可能與 eval_gate 有重複欄位邏輯 |

---

## 注意

- 本輪只讀，不修改任何 repo 檔案
- 每個 debt 條目需附檔案:行號
- 嚴重度評估用 P1（高）~ P3（低）
