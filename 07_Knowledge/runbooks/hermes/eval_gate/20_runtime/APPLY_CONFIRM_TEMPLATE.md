# APPLY_CONFIRM_TEMPLATE.md — 套用確認回報模板

> 用途：人類或 Cursor 在完成 repo 套用後，回報給 Hermes Agent 的結構化模板。
> 填寫完成後，Hermes 會據此更新 DEBT_LOG 與 run 紀錄。

---

## 回報摘要

```yaml
report_date: YYYY-MM-DD
applied_by: <姓名 / Cursor>
apply_plan_ref: 90_runs/2026-05-30_apply_plan_v1.md
```

---

## 1. 目標 repo 檔案

| 項目 | 值 |
|------|-----|
| Repo 目標路徑 | `observability/eval_gate.py` |
| Workspace 來源 | `20_runtime/eval_gate.suggested.v1.py` |
| 是否已套用 | ⬜ 是 / ⬜ 否（原因：___） |
| 套用方式 | ⬜ 直接覆寫 / ⬜ 手動 patch / ⬜ git diff+apply / ⬜ 其他：___ |

---

## 2. 測試驗證結果

### 2.1 靜態驗證

| # | 驗證項目 | 結果 |
|:-:|----------|:----:|
| 1 | 檔案可載入（importable） | ⬜ PASS / ⬜ FAIL / ⬜ N/A（環境不可用） |
| 2 | 介面簽名未變 | ⬜ PASS / ⬜ FAIL / ⬜ N/A |
| 3 | 回傳 keys 一致 | ⬜ PASS / ⬜ FAIL / ⬜ N/A |
| 4 | logging 不造成 error | ⬜ PASS / ⬜ FAIL / ⬜ N/A |
| 5 | 無新增第三方依賴 | ⬜ PASS / ⬜ FAIL / ⬜ N/A |

### 2.2 測試（如有執行）

| 測試 | 結果 | 備註 |
|------|:----:|------|
| `tests/test_eval_gate.py` | ⬜ PASS / ⬜ FAIL / ⬜ N/A | _ |
| `tests/test_eval_gate_contract.py` | ⬜ PASS / ⬜ FAIL / ⬜ N/A | _ |
| `tests/test_eval_exporter.py` | ⬜ PASS / ⬜ FAIL / ⬜ N/A | _ |
| `tests/test_eval_ci_check.py` | ⬜ PASS / ⬜ FAIL / ⬜ N/A | _ |

### 2.3 測試失敗詳細（如適用）

```
失敗的測試名稱：
錯誤訊息：
是否為已知 flaky / regression：
```

---

## 3. 版本控制

| 項目 | 值 |
|------|-----|
| 是否已 commit | ⬜ 是（commit hash：___）/ ⬜ 否 |
| 是否已 PR | ⬜ 是（PR #：___）/ ⬜ 否 |
| branch 名稱 | ___ |
| base branch | ___ |

---

## 4. DEBT_LOG 更新

| Debt ID | 目前狀態 | 應更新為 | 說明 |
|---------|:--------:|:--------:|------|
| D-001 | fixed_suggested | ⬜ fixed_in_repo / ⬜ 保留 fixed_suggested / ⬜ open | — |
| D-003 | fixed_suggested | ⬜ fixed_in_repo / ⬜ 保留 fixed_suggested / ⬜ open | — |
| D-010 | fixed_suggested | ⬜ fixed_in_repo / ⬜ 保留 fixed_suggested / ⬜ open | — |

---

## 5. 障礙記錄

| 障礙類型 | 描述 |
|----------|------|
| （例如：venv 無法 activate） | — |
| （例如：測試指令失敗） | — |
| （例如：建議版與 repo 有不預期差異） | — |

---

## 6. 是否需要回退

- ⬜ 不需要，套用成功
- ⬜ 需要：`fixed_suggested` → `open`（完全回退）
- ⬜ 需要：`fixed_in_repo` → `fixed_suggested`（保留建議版但暫難套用）
- ⬜ 需要：部分 debt_id 保留 `fixed_suggested`（見 §4）

---

## 7. Hermes 收到後動作

> 此段由 Hermes 在收到回報後填寫。

- [ ] DEBT_LOG.md 狀態更新（`fixed_suggested` → `fixed_in_repo`）
- [ ] `90_runs/2026-05-30_fix_round1.md` 追加套用結果章節
- [ ] `apply_plan_v1.md` §7 人工確認欄位填入
- [ ] 統計摘要更新
- [ ] 若有回退或障礙，更新 DEBT_LOG 對應 debt_id 備註