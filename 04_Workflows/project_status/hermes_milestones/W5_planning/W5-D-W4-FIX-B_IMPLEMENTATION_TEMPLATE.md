# Implementation Template — W5-D-W4-FIX-B-IMPLEMENTATION-01

> **任務名稱**：W2-1_case Index 真實回填  
> **來源方案卡**：`W5-D-W4-FIX-B_plan.md`（背景、調查、步驟、風險）  
> **範圍**：僅 W2-1_case，不觸碰其他 case，不動 production  
> **控制面 lane**：`runtime`（實作票）→ 完成後等待 `review` lane 審查 → 交付 `doc-sync` lane 回寫  
> **父票**：`W5-D-W4-FIX-B`（W5-D 清理軸下的殘留清理子票）

---

## 1. 前提與不變條件

### 開工前應成立的前提（不符合則須回報，不可自行跳過）

| # | 前提 | 檢查方式 |
|---|------|----------|
| P1 | W2-1_case 目錄結構完整（`W2-1_case.md`、`04_art_eng_ctx.md` 等存在） | 直接確認檔案存在 |
| P2 | `wf_kb_index_sync.ps1` 與 `wf_kb_index_gate.ps1` 可在本地執行環境跑（PowerShell 或 pwsh） | 試跑一個 help flag 確認腳本可載入 |
| P3 | `workflow_v2/20_pilot/W3-B/` 下有 `index_status_W2-1.json`（現狀：file_count=0, chunk_count=0） | 讀取 JSON 確認現狀 |
| P4 | `index_status_W2-1.failed_infra.json` 存在且未被修改 | 讀取確認 |

### 不得改動的項目（硬邊界，違反則 supervisor 可退回）

- **不可修改** `00_master_plan.md`、`90_run_queue.md`、`99_latest_status.md`（全局黑板屬 doc-sync lane）。
- **不可修改** `wf_kb_index_sync.ps1`、`wf_kb_index_gate.ps1` 本身（只能使用它們，不能改）。
- **不可修改** `.github/workflows/*`、暗部腳本、venv、`.env`。
- **不可修改** 其他 case 的 `index_status_*.json`（如 W3-A_case 或其他）。
- **不可修改** G7/G8 治理層的語義。
- **不可執行** production 敏感操作（如 deploy、connection to prod DB）。
- **不可擴面**到 W2-1 以外的 case（W5-B 軸才做多 case 擴面）。

---

## 2. 具體步驟（實作 Checklist）

請依序執行以下步驟。每一步的結果應記錄，用於最後的回報。

### Step 1：確認 Scope 範圍

**做什麼**：讀取 `04_art_eng_ctx.md` 的 `allowed_scope` 字段，確認 `kb_index_subtree=core` 涵蓋的真實目錄範圍。

**操作說明**：
- 讀 `workflow_v2/20_pilot/W2-1_case/04_art_eng_ctx.md` 的 `allowed_scope` 與 `forbidden_zone_types`。
- 找到 repo 根下 `core/` 目錄（`kb_index_subtree` 所指）。
- 快速統計 `core/` 下可被 index 的文字檔數量（可略過 venv、binary、`.git` 等）。
- 根據檔案數量與常見 chunk 策略（如每 500–1000 行一個 chunk）估計 chunk 數。

**產出**：兩個數字——`file_count = <實際文字檔數>`、`chunk_count = <估計 chunk 數>`。

### Step 2：更新 index_status_W2-1.json

**做什麼**：將 Step 1 的真實數字填入 `index_status_W2-1.json` 的 `result_summary`。

**操作說明**：
- 編輯 `workflow_v2/20_pilot/W3-B/index_status_W2-1.json`。
- **保留**所有既有欄位（`schema_version`、`case_id`、`job_type`、`job_id`、`scope`、`scope_digest`、`status=succeeded` 等）。
- 將 `result_summary.file_count` 從 `0` 改為 Step 1 計算的實際檔案數。
- 將 `result_summary.chunk_count` 從 `0` 改為 Step 1 估計的 chunk 數。
- 可選：更新 `manifest_ref` 路徑或保留原值。

**產出**：更新後的 `index_status_W2-1.json`（`file_count > 0`, `chunk_count > 0`）。

### Step 3：執行 Sync（Dry-Run → 正式）

**做什麼**：用 `wf_kb_index_sync.ps1` 將狀態 JSON 回寫到案卷 markdown。

**操作說明**：
- 先在 repo root 以 `-DryRun` flag 執行 sync 腳本，**確認輸出內容**與預期一致（特別是 `kb_index_evidence_refs` 路徑、`kb_index_status` 等）。
- Dry-run 確認無誤後，以正式模式（不含 `-DryRun`）執行 sync。
- 確認 exit code 為 `0`（success/updated）且 stdout 顯示 `updated`。
- 開啟 `W2-1_case.md` 的 `kb_index_current` 區段，確認 `kb_index_evidence_refs` 指向更新後的 `index_status_W2-1.json`。

**產出**：sync 執行 log + 更新後的 `W2-1_case.md`。

### Step 4：執行 Gate 驗證

**做什麼**：用 `wf_kb_index_gate.ps1` 確認更新後的案卷可通過 index gate。

**操作說明**：
- 在 repo root 以 `-TargetImpState IMP-AI-READY` 執行 gate 腳本。
- 確認 stdout 輸出包含 `VERDICT=allow`。
- 確認 exit code 為 `0`。
- 檢查 stdout 中的 `kb_index_status=ready`、`checks_failed` 為空。

**產出**：gate 執行 log（含 `VERDICT=allow`）。

### Step 5：（可選）新增 Run Record

**做什麼**：建立本次 index 回填的紀錄檔，供後續 CHK 可查。

**操作說明**：
- 在 `workflow_v2/20_pilot/W3-B_case/run_records/`（若目錄不存在則建立）下建一個以日期命名的目錄，如 `index_backfill_2026-05-31/`。
- 在目錄內放一個 `execution_log.md`，包含：
  - Step 1~4 的執行摘要。
  - 同步前後的 `index_status_W2-1.json` 的關鍵欄位變化。
  - sync / gate 的 exit code 與輸出摘要。
  - 如有無法確認的風險項目，如實記錄。

**產出**：run record 目錄與 log。

---

## 3. 風險與注意事項

實作過程中請特別留意以下風險：

| 風險代號 | 風險說明 | 建議處理方式 |
|----------|----------|-------------|
| **R1** | `core/` 目錄的範圍可能比預期大（含非文字檔、venv、binary），直接用 `wc -l` 會膨脹 file_count | 先對 `core/` 做檔案類型過濾，只計入文字檔。若不清楚哪些類型可被 index，以 `.py`、`.md`、`.json`、`.yaml`、`.toml`、`.cfg` 等常見文字檔為準 |
| **R2** | sync 腳本須 PowerShell 環境。WSL 的 `pwsh` 或 Windows `powershell.exe` 均可，但需確認可載入 `.ps1` | 試跑一次 help flag（如 `-?`）確認腳本可解析。若執行政策（ExecutionPolicy）阻擋，需先調整或用 `-ExecutionPolicy Bypass` |
| **R3** | file_count 和 chunk_count 是人工估計，不是真實 indexer 跑出來的。數值可能被後續真實 index run 推翻 | 在 run record 與最終回報中明確註明「本數值為手動統計，非暗部 `repo_index_v1` 輸出」。後續可用真實 run 覆蓋 |
| **R4** | 若 file_count 忘了改（仍為 0），sync 和 gate 仍然會通過（因為 gate 不看 file_count），造成「已修復」的假象 | Step 2 完成後**必須**開啟 `index_status_W2-1.json` 確認 file_count 已變更。Step 3 的 dry-run 也會反映，請仔細檢查輸出 |
| **R5** | 本票只修 W2-1_case。若過程中不小心改了其他 case 的文件或 index_status，會污染邊界 | 執行任何命令前，先確認參數中的 `-CaseDir` 和 `-StatusJson` 路徑是否指向 `W2-1`。不要同時開多個 case 的檔案 |
| **R6** | 本票完成後，index 層仍無觀測指標序列（`gov_gate_metrics/` 無 index 專屬 JSONL）。這不屬於本票範圍 | 在 run record 中如實記錄「index 觀測指標仍待 W5-C 處理」，不必在本票中補 |

**共識**：若有任何不確定（尤其是 scope 定義、file_count 的計入標準、或腳本執行異常），**先停下來**並回報 Supervisor / 尚書省，**不得自行擴大 scope**。

---

## 4. 驗收條件

執行完成後，逐項確認以下條件。**全部滿足方為 DONE**：

| # | 驗收條件 | 如何驗證 |
|---|----------|----------|
| **V1** | `index_status_W2-1.json` 的 `result_summary.file_count > 0` 且值合理（與 `core/` 文字檔數匹配 ±10%） | 讀取 JSON 的 `file_count` 欄位，對比 Step 1 的統計值 |
| **V2** | `wf_kb_index_sync.ps1` exit code 0（stdout 含 `updated`） | 查看終端機輸出或 run log |
| **V3** | `W2-1_case.md` 的 `kb_index_current` 區段 `kb_index_evidence_refs` 指向更新後的 `index_status_W2-1.json` | 讀取 markdown 的對應欄位 |
| **V4** | `wf_kb_index_gate.ps1` exit code 0（stdout 含 `VERDICT=allow`） | 查看終端機輸出或 run log |
| **V5** | `index_status_W2-1.failed_infra.json` 未被修改 | 檢查 git diff 或檔案 checksum 無變動 |
| **V6** | `00_master_plan.md`、`90_run_queue.md`、`99_latest_status.md` 未被修改 | git status / git diff 確認 |
| **V7** | `.github/workflows/*`、暗部腳本、venv、`.env` 未被修改 | git status 確認無 `.github/` 或暗部相關變更 |
| **V8**（可選） | 若建立了 run record 目錄，其內容與 Step 1~4 記錄一致 | 讀取目錄內 log 檔案 |

---

## 5. 回報格式模板

執行完成後，請將以下模板填寫後附在執行報告中：

```
## Execution Report — W5-D-W4-FIX-B-IMPLEMENTATION-01

### 修改檔案清單
- workflow_v2/20_pilot/W3-B/index_status_W2-1.json（更新 file_count / chunk_count）
- workflow_v2/20_pilot/W2-1_case/W2-1_case.md（經由 sync 腳本自動更新，非直接編輯）
- (可選) workflow_v2/20_pilot/W3-B_case/run_records/index_backfill_YYYY-MM-DD/

### index_status_W2-1.json 欄位變化
- file_count: 0 → <N>
- chunk_count: 0 → <M>
- manifest_ref: <變更說明，若無變更則寫「未變動」>

### Sync 執行摘要
- Dry-run 輸出：<2–3 行摘要>
- 正式執行 exit code：<0 / 1 / 2 / 3>
- 正式執行 stdout：<2–3 行關鍵輸出>

### Gate 執行摘要
- Exit code：<0 / 1 / 2 / 3>
- VERDICT：<allow / require-human-override / deny>
- checks_failed：<none 或清單>
- kb_index_status：<ready / stale / missing>

### 自檢清單
- [V1] file_count > 0 且值合理：<OK / FAIL>
- [V2] sync exit 0：<OK / FAIL>
- [V3] evidence_refs 指向正確：<OK / FAIL>
- [V4] gate exit 0：<OK / FAIL>
- [V5] failed_infra.json 未修改：<OK / FAIL>
- [V6] 00/90/99 未修改：<OK / FAIL>
- [V7] CI/暗部未修改：<OK / FAIL>
- [V8] (可選) run record 存在：<OK / SKIP>

### 備註
- 本報告中的 file_count/chunk_count 為人工統計，非暗部 indexer 輸出。
- 遇到的異常或疑問：<若有，如實記錄>
- 建議後續事項：<若有，如 W5-B 多 case 擴面 / W5-C observability>
```

---

## 附錄 A — 關鍵路徑速查

| 檔案 | 用途 | 路徑（相對 repo root） |
|------|------|------------------------|
| 案卷主文件 | kb_index_current 區段所在 | `workflow_v2/20_pilot/W2-1_case/W2-1_case.md` |
| 案卷 scope 定義 | 確認 allowed_scope | `workflow_v2/20_pilot/W2-1_case/04_art_eng_ctx.md` |
| 狀態 JSON（待更新） | 更新 file_count/chunk_count | `workflow_v2/20_pilot/W3-B/index_status_W2-1.json` |
| 狀態 JSON（不修改） | infra 失敗樣本 | `workflow_v2/20_pilot/W3-B/index_status_W2-1.failed_infra.json` |
| Sync 腳本（使用，不改） | 狀態 JSON → 案卷 | `workflow_v2/tools/wf_kb_index_sync.ps1` |
| Gate 腳本（使用，不改） | 案卷 → allow/deny | `workflow_v2/tools/wf_kb_index_gate.ps1` |
| ORCH 接線說明（參考） | 理解整體流程 | `workflow_v2/20_pilot/W3-B/W4-B_orch_integration.md` |
| 方案卡（本任務來源） | 背景 + 完整風險分析 | `milestones/W5_planning/W5-D-W4-FIX-B_plan.md`（workspace） |