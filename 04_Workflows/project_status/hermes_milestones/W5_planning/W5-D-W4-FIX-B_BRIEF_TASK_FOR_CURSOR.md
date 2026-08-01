# W5-D-W4-FIX-B Brief — W2-1_case Index 真實回填（給 Cursor 的簡短任務卡）

> **源頭**：CHK-W4 GAP-W4-B1 — `index_status_W2-1.json` 目前 file_count=0 / chunk_count=0（樣本資料）。  
> **目標**：在 W2-1_case 範圍內完成一次真實回填，讓 file_count / chunk_count 反映真實的檔案計數。  
> **控制面 Lane**：`runtime` → 完成後等待 review → doc-sync。  
> **關聯方案**：`W5-D-W4-FIX-B_plan.md`（完整背景、風險、調查細節）。

---

## 任務說明

`index_status_W2-1.json` 的 `result_summary.file_count=0, chunk_count=0` 是 Wave 4 留下的樣本資料。Gate 雖然通過（`verdict=allow`，因為 Gate 不看 file_count），但底層 index 覆蓋宣稱是空的。本票的目標是：在 `W2-1_case` 範圍內（`kb_index_subtree=core`），根據真實的 scope 檔案數量更新 `index_status_W2-1.json`，然後跑 sync → gate → 確認全部 Allow。不動其他 case、不動 CI、不動暗部。

---

## 允許操作

- 編輯 `index_status_W2-1.json` 的 `result_summary.file_count` / `chunk_count`
- 使用 `wf_kb_index_sync.ps1` 執行 sync（dry-run → 正式）
- 使用 `wf_kb_index_gate.ps1` 執行驗證
- 可選：新增 run_record 目錄存放執行 log

## 禁止操作

- 修改 `00_master_plan.md` / `90_run_queue.md` / `99_latest_status.md`
- 修改 `wf_kb_index_sync.ps1` / `wf_kb_index_gate.ps1` 本身
- 修改 `.github/workflows/*`、暗部 Python 腳本、venv、`.env`
- 觸碰其他 case 的 `index_status_*.json` 或「順手修」相鄰檔案
- 觸碰 G7/G8 治理語義
- 執行任何 production 敏感操作

---

## 實作步驟 Checklist

1. **確認 scope**：讀 `W2-1_case/04_art_eng_ctx.md` 的 `allowed_scope`，統計 `core/` 下的文字檔數量，估算 chunk 數。
2. **更新 index_status**：將 `index_status_W2-1.json` 的 `file_count` 設為實際檔案數、`chunk_count` 設為估計 chunk 數，保留其他欄位。
3. **Dry-run sync**：跑 `wf_kb_index_sync.ps1 -DryRun`，確認輸出的變更集與預期一致（特別是 evidence_refs 路徑）。
4. **正式 sync**：跑正式 sync（exit code 應為 0），確認 `W2-1_case.md` 的 `kb_index_current` 區段已更新。
5. **Gate verify**：跑 `wf_kb_index_gate.ps1 -TargetImpState IMP-AI-READY`，確認 `VERDICT=allow` 且 exit code=0。
6. **可選：新增 run_record**：在 `W3-B_case/run_records/` 下建立日期目錄，存放執行 log 供 CHK 查閱。

---

## 驗收條件

- **V1**：`index_status_W2-1.json` 的 `file_count > 0` 且與 `core/` 文字檔數合理一致
- **V2**：`wf_kb_index_sync.ps1` exit code=0，stdout 含 `updated`
- **V3**：`W2-1_case.md` 的 `kb_index_evidence_refs` 指向更新後的 index_status JSON
- **V4**：`wf_kb_index_gate.ps1` exit code=0，stdout 含 `VERDICT=allow`
- **V5**：`index_status_W2-1.failed_infra.json` 未被修改
- **V6**：00/90/99/CI/暗部 未被修改

---

## 回報格式框架

```markdown
## Execution Report — W5-D-W4-FIX-B

### 修改檔案清單
- workflow_v2/20_pilot/W3-B/index_status_W2-1.json（file_count/chunk_count 更新）
- workflow_v2/20_pilot/W2-1_case/W2-1_case.md（經 sync 腳本自動更新）

### index_status 欄位變化
- file_count: 0 → <N>
- chunk_count: 0 → <M>

### Sync 結果
- Dry-run 輸出摘要：<2–3 行>
- 正式 exit code：<0/1/2/3>，stdout：<關鍵輸出>

### Gate 結果
- Exit code：<0/1/2/3>，VERDICT：<allow/deny>
- kb_index_status：<ready/stale/missing>

### 自檢勾選
- [V1] file_count > 0：<OK/FAIL>
- [V2] sync exit 0：<OK/FAIL>
- [V3] evidence_refs 正確：<OK/FAIL>
- [V4] gate exit 0：<OK/FAIL>
- [V5] failed_infra 未改：<OK/FAIL>
- [V6] 00/90/99/CI/暗部未改：<OK/FAIL>

### 備註
- file_count/chunk_count 為人工統計，非暗部 indexer 輸出
- 遇到的異常或疑問：
```
