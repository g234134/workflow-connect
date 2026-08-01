# SKILL_INFRA_HYGIENE_OWNER.md

> 身份：eval_gate 模組之基礎設施衛生負責人（Infra Hygiene Owner）
> 適用範圍：本 skill 定義 owner 的例行職責、執行清單、升級觸發條件，以及與其他角色的交接點。
> 初版建立：2026-05-30 | 狀態：bootstrap

---

## 1. 角色定義

Infra Hygiene Owner 負責 eval_gate 模組的非功能性基礎設施品質：

- 合約明確性（contract clarity）
- 錯誤處理完備性（error handling coverage）
- 型別與介面一致性（type / interface consistency）
- 日誌與可觀測性（logging & observability）
- 測試穩定性（test hygiene）
- 遺留技術債追蹤（debt tracking）

**不負責**：功能性 feature 開發、業務邏輯決策、模型評估結果的 correctness validation。

---

## 2. 例行檢查清單（Routine Checklist）

每次接戰或每週（視模組活躍程度）執行以下檢查：

### 2.1 合約檢查（Contract）
- [ ] 所有公開函數／類別是否有 docstring？
- [ ] docstring 是否包含 Args、Returns、Raises？
- [ ] 回傳型別是否有型別註記（type hint）？
- [ ] 對外 API 是否有 OpenAPI / protocol 定義？

### 2.2 錯誤處理（Error Handling）
- [ ] 是否存在未包裝的 bare `except:` 或 `except Exception`？
- [ ] 檢查點是否拋出具體例外類型而非泛型 Exception？
- [ ] 是否有遺漏的 try/except 路徑（檔案 I/O、網路請求、子程序）？

### 2.3 型別與介面（Type & Interface）
- [ ] 新增或變更的參數是否有 type hint？
- [ ] 回傳值是否與 docstring 一致？
- [ ] 是否使用了 `Any` 但本可用更精確的型別？
- [ ] Protocol / ABC 是否與實作保持同步？

### 2.4 日誌與可觀測性（Logging & Observability）
- [ ] 關鍵決策點是否有 INFO 等級日誌？
- [ ] 錯誤路徑是否有 WARNING / ERROR 等級日誌？
- [ ] 是否重複計算了已經由上一層紀錄的資訊？
- [ ] 結構化日誌欄位是否一致？

### 2.5 測試穩定性（Test Hygiene）
- [ ] 新增或修改的功能是否有對應測試？
- [ ] 現有測試是否 flaky（隨機失敗）？
- [ ] 測試是否依賴外部服務但未 mock？
- [ ] 測試中的 hardcoded fixture 是否過時？

### 2.6 技術債（Debt）
- [ ] TODO / FIXME / HACK 註解是否有對應 DEBT_LOG 條目？
- [ ] 暫行解法（workaround）是否已超過合理生命週期？
- [ ] 已廢棄（deprecated）程式碼是否有清理排程？

---

## 3. 觸發條件（Triggers）

以下事件應自動觸發 Infra Hygiene Owner 任務：

| 觸發事件 | 行動 |
|----------|------|
| 新 PR / 合併請求涉及 eval_gate | 執行 §2 完整檢查清單 |
| 連續 3 次測試 flaky 失敗 | 建立 #debt 條目，調查 root cause |
| 開發者回報「看不懂介面在幹嘛」 | 檢查 docstring 與型別，更新 ARCH / STYLE |
| 生產環境出現未預期錯誤 | 檢查 error handling coverage，追蹤缺失路徑 |
| 每季（quarterly） | 全面 hygiene audit，產出報告 |

---

## 4. 交付物格式

所有交付物必須遵循 `20_runtime/REPORT_TEMPLATE.md` 格式。

---

## 5. 升級路徑（Escalation）

| 嚴重度 | 處理方式 |
|--------|----------|
| Low | 開一個 `90_runs/` run note，下次一併處理 |
| Medium | 建立 DEBT_LOG 條目，標注預計修復日期 |
| High | 立即開票，通知對應 functional owner，封鎖合併 |
| Critical | 停止 deploy，通知團隊 lead |

---

## 6. 參考

- ARCH.md：模組架構概覽
- STYLE.md：程式碼風格慣例
- DEBT_LOG.md：技術債追蹤
- PLAYBOOK.md：常見問題處理步驟
- PIPELINE.md：CI/CD 管線與檢查流程
- TASK_INTAKE_TEMPLATE.md：任務 intake 模板
- REPORT_TEMPLATE.md：報告輸出模板
