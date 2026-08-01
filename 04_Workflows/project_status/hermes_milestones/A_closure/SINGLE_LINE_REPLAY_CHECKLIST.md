# SINGLE_LINE_REPLAY_CHECKLIST.md

> 用於驗證一條單線 owner 閉環是否完整可回放。
> 每個檢查點都有可操作指令，不需要猜測。

---

## 前置檢查（在開始 replay 之前）

| # | 檢查項 | 通過條件 | 如果失敗 |
|---|--------|----------|----------|
| 0.1 | 模組原始碼路徑已知 | `ls <repo>/<module_path>` 回傳檔案列表 | 確認真實 repo 位置，更新 ARCH.md |
| 0.2 | 測試檔案存在 | `ls <repo>/tests/test_<module>*` 回傳至少 1 個 `.py` | 標記「無測試」到 PIPELINE.md |
| 0.3 | workspace 目錄結構就緒 | `ls infra_owner/<module>/` 含 00_skill/ 10_memory/ 20_runtime/ 90_runs/ | 執行 NEXT_MODULE_BOOTSTRAP_TEMPLATE.md |

---

## Step 1: Bootstrap

| # | 檢查項 | 通過指令 | 預期結果 |
|---|--------|----------|----------|
| 1.1 | SKILL 檔案存在 | `ls 00_skill/` | 至少 1 個 `.md` |
| 1.2 | 4 份記憶檔案存在 | `ls 10_memory/` | ARCH / STYLE / DEBT_LOG / PLAYBOOK |
| 1.3 | 2 份模板存在 | `ls 20_runtime/` | TASK_INTAKE_TEMPLATE / REPORT_TEMPLATE |
| 1.4 | bootstrap run note 存在 | `ls 90_runs/*bootstrap*` | 至少 1 份 |

**閘門**：1.1–1.4 全部通過後，才能進入 Step 2。

---

## Step 2: Discovery

| # | 檢查項 | 通過指令 | 預期結果 |
|---|--------|----------|----------|
| 2.1 | 模組路徑已確認 | `grep -c "實際路徑" ARCH.md` 或 `grep -c "observability" ARCH.md` | 輸出不為 0 |
| 2.2 | 公開介面已記錄 | `grep -c "公開介面" ARCH.md` | ≥ 1 |
| 2.3 | 依賴鏈已記錄 | `grep -c "外部依賴" ARCH.md` | ≥ 1 |
| 2.4 | 消費者已記錄 | `grep -c "消費者" ARCH.md` | ≥ 1 |
| 2.5 | 測試指令有推測 | `grep -c "needs-confirmation" PIPELINE.md` | ≥ 1 |
| 2.6 | discovery run note 存在 | `ls 90_runs/*discovery*` | 至少 1 份 |

**閘門**：2.1–2.3 是強制項；2.5 若為 0 表示 PIPELINE.md 未更新。

---

## Step 3: Readonly Scan

| # | 檢查項 | 通過指令 | 預期結果 |
|---|--------|----------|----------|
| 3.1 | DEBT_LOG 有條目 | `grep -c "^| D-" DEBT_LOG.md` | ≥ 3（建議 5–10） |
| 3.2 | 6 維度都已掃描 | `grep -c "合約檢查\|錯誤處理\|型別與介面\|日誌與可觀測\|測試穩定性\|技術債" scan_readonly.md` | 6 個不同匹配 |
| 3.3 | 嚴重度區分存在 | `grep -c "P1\|P2\|P3" scan_readonly.md` | ≥ 5 |
| 3.4 | scan run note 存在 | `ls 90_runs/*scan*` | 至少 1 份 |

**閘門**：3.1（至少 3 條 debt）。0 條表示掃描未執行或未記錄。

---

## Step 4: Fix Round

| # | 檢查項 | 通過指令 | 預期結果 |
|---|--------|----------|----------|
| 4.1 | suggested 檔存在 | `ls 20_runtime/*suggested*` | 至少 1 個 `.py` |
| 4.2 | debt 轉 `fixed_suggested` | `grep "fixed_suggested" DEBT_LOG.md` | ≥ 1 條 |
| 4.3 | 靜態比對有記錄 | `grep -c "靜態比對\|AST" fix_round*.md` | ≥ 1 |
| 4.4 | 未處理債務有說明原因 | `grep "不處理原因\|本輪未處理" fix_round*.md` | ≥ 1 |

**閘門**：4.1（有 suggested 檔） + 4.2（至少 1 條 debt 轉狀態）。

---

## Step 5: Review Gate

| # | 檢查項 | 通過指令 | 預期結果 |
|---|--------|----------|----------|
| 5.1 | 審查結論存在 | `grep "裁決\|接受\|處置" review*.md` | ≥ 1 |
| 5.2 | 有 like/dislike | `grep "喜歡\|不喜歡" review*.md` | ≥ 2（各至少 1） |
| 5.3 | STYLE 有更新（如適用） | `grep "confirmed\|proposed→" review*.md` | ≥ 1 或 N/A 備註 |
| 5.4 | PLAYBOOK 有更新（如適用） | `grep "PLAYBOOK" review*.md` | ≥ 1 或 N/A 備註 |

**閘門**：5.1（有接受/拒絕裁決）。無裁決 = 審查未完成。

---

## Step 6: Apply

| # | 檢查項 | 通過指令 | 預期結果 |
|---|--------|----------|----------|
| 6.1 | apply_plan 存在 | `ls 90_runs/*apply_plan*` | 至少 1 份 |
| 6.2 | apply_result 存在 | `ls 90_runs/*apply_result*` | 至少 1 份 |
| 6.3 | debt 轉 `fixed_in_repo` | `grep "fixed_in_repo" DEBT_LOG.md` | ≥ 1 條 |
| 6.4 | 測試結果有記錄 | `grep -c "PASS\|失敗\|N/A" apply_result*.md` | ≥ 1 |
| 6.5 | approved 欄位已簽署 | `grep "approved" apply_plan*.md` | 包含 `yes` |

**閘門**：6.1 + 6.2 + 6.3。缺任一表示 apply 未完成。

---

## Step 7: 一致性檢查

| # | 檢查項 | 通過指令 | 預期結果 |
|---|--------|----------|----------|
| 7.1 | DEBT_LOG 統計已更新 | `grep "統計摘要" DEBT_LOG.md` | 包含數字（total / fixed / open） |
| 7.2 | 所有 debt 狀態值合法 | `grep "^| D-" DEBT_LOG.md` | 所有狀態在 `open / planned / fixed_suggested / fixed_in_repo / rejected / deferred / superseded / wontfix` 內 |
| 7.3 | run notes 日期與事件匹配 | `ls 90_runs/*.md \| xargs grep -l "日期"` | 每個 note 有日期 |

**閘門**：7.1（統計必須有數字，不能是空白）。

---

## 總閘門（全部必須為 YES）

```
能否從 bootstrap 走到 applied fix？     YES / NO
能否在 30 分鐘內定位任何一步的文件？     YES / NO
能否在下一個模組完全複製本流程？         YES / NO
```

如果以上任一 NO → 回 SOP 檢查缺口。
