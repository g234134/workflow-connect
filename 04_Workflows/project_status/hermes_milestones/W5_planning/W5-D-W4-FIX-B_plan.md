# W5-D-W4-FIX-B PLAN — W2-1_case 真實 Index 回填方案卡

> **設計者**：WAVE5-PLANNING 專線（2026-05-31）
> **用途**：提供 W5-D-W4-FIX-B 實作前的「方案設計 + 風險分析 + 任務卡骨架」。
> **硬邊界**：不修改任何 repo 檔案；不執行實際腳本；不改變既有的 index scheme。
> **控制面對齊**：`workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`（planning → runtime → review → doc-sync）
> **父票**：`workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md`（W5-A 父票，間接）
> **鄰接**：`workflow_v2/40_ticket_memory/CHK-W4-WAVE4-CLOSURE.memory.md`（§W4-B GAP-1）

---

## (1) 背景摘要

W4-B-INDEX-INTEGRATION（minimal v1）在 CHK-W4 中被判定為 `OK_WITH_KNOWN_GAPS`，其中唯一的已知 gap **GAP-W4-B1** 是：

> `index_status_W2-1.json` 的 `file_count=0`、`chunk_count=0`——這份狀態文件是樣本資料，不是真實 indexing 的結果。

具體來說：
- `wf_kb_index_sync.ps1` 從 `index_status_W2-1.json` 讀取欄位（包括 `result_summary.file_count` / `chunk_count`），然後寫入 `W2-1_case.md` 的 `kb_index_current` 區段。
- `wf_kb_index_gate.ps1` 讀取 `W2-1_case.md` 的 `kb_index_*` 欄位來決定 allow/deny——但 gate 只檢查 `kb_index_status`（ready/stale/missing），**不檢查** file_count / chunk_count。
- 因此目前的狀態是：gate 邏輯通過（`status=ready` → `allow`），但底層的 index 資料（file_count=0 / chunk_count=0）是假的，無法支撐任何對「真實 index 覆蓋了哪些檔案」的宣稱。

**W5-D-W4-FIX-B 的目的**：在 W2-1_case 上完成一次真實的 index 回填，讓 `index_status_W2-1.json` 反映真實的檔案計數（非零 file_count/fragment），並通過現有的 sync / gate 腳本鏈確認行為正確。

---

## (2) 目標與邊界

### 完成定義（Done Definition）

下列條件**全部滿足**方可標記 W5-D-W4-FIX-B 為 DONE：

- [ ] `index_status_W2-1.json` 的 `result_summary.file_count > 0` 且 `result_summary.chunk_count > 0`，且值與實際 scope 內的檔案數量合理一致（非樣本 0）。
- [ ] `wf_kb_index_sync.ps1` 成功執行一次並將 `index_status_W2-1.json` 的資訊回填到 `W2-1_case.md` 的 `kb_index_current` 區段。
- [ ] `wf_kb_index_gate.ps1`（對 `IMP-AI-READY`）對更新後的 `W2-1_case.md` 回傳 `verdict=allow`。
- [ ] 原有 `index_status_W2-1.failed_infra.json` 不受影響（保留 infra 阻斷的示範用例）。
- [ ] 未修改任何非本票 write_set 的檔案（如 `.github/workflows/*`、暗部腳本、`00/90/99` 全局黑板）。

### 不做的範圍（Out of Scope / Frozen Constraints）

- **不改變既有的 index scheme**：仍使用 `repo_index_status_v0.1` schema，不新增欄位。
- **不修改 sync / gate 腳本**：僅使用現有的 `wf_kb_index_sync.ps1` 和 `wf_kb_index_gate.ps1` 來驗證。
- **不擴面到其他 case**：本票僅針對 W2-1_case。
- **不觸碰暗部 `repo_index_v1` job 本體**：不修改 indexer 程式碼、不新增 CI job、不觸碰 production env。
- **不修改 `00_master_plan.md` / `90_run_queue.md` / `99_latest_status.md`**：doc-sync 屬於另一張票（W5-D-DOCSYNC-SOP 或後續 doc-sync lane）。
- **不改 G7/G8 治理語義**。
- **不執行任何 production 敏感操作**。

---

## (3) 只讀調查結果摘要

從 `workflow_v2/20_pilot/W2-1_case/`、`workflow_v2/20_pilot/W3-B/`、`workflow_v2/tools/` 中讀取的關鍵事實：

### a) 案卷 scope 定義
- W2-1 是 CHG-GOV-DOC（治理文檔變更），primary scope 為 `workflow_v2/10_governance/G7_state_machine/` 和 `G8_artifact_contract/` 的子集（見 `04_art_eng_ctx.md` §allowed_scope）。
- `kb_index_subtree=core`：這是指 repo 中的 `core/` 目錄（非 `workflow_v2/` 本身）。

### b) 既有的 index_status 文件
- `index_status_W2-1.json`（成功樣本）：`file_count=0, chunk_count=0, status=succeeded`—**這是樣本資料**。
- `index_status_W2-1.failed_infra.json`（infra 故障樣本）：`status=failed, error_type=infra_unavailable`—保留為 infra 阻斷示範。

### c) Sync 腳本行為（wf_kb_index_sync.ps1）
- 從 `index_status_<CASE>.json` 讀取 `result_summary.file_count` / `chunk_count` 等欄位。
- 這些欄位被**直接寫入** `W2-1_case.md` 的 `kb_index_current` 區段嗎？**否**——sync 腳本只回填 `kb_index_*` 固定欄位（status、job_id、last_updated、scope 等），**不包含** `file_count` 或 `chunk_count` 欄位。
- 換句話說，`file_count` / `chunk_count` 在 sync 過程中**僅存在於** `index_status_*.json`，**不會**被複製到案卷 markdown 中。gate 腳本也只讀 `kb_index_*` 欄位，**不需要** file_count。
- sync 腳本 exit code: 0=updated, 1=no_change, 2=schema/input error, 3=config error。

### d) Gate 腳本行為（wf_kb_index_gate.ps1）
- 只讀取 `W2-1_case.md` 的 `kb_index_*` 欄位（從 `### KB / Repo Index` 區段的 markdown 表格解析）。
- 決策邏輯：`ready`→allow, `missing`→deny, `stale`→看不同條件。
- exit code: 0=allow, 1=require-human-override, 2=deny, 3=error。
- **file_count 不對 gate 決策產生任何影響**——gate 不看 result_summary 欄位。

### e) Observability 關聯
- `workflow_v2/observability/gov_gate_metrics/local.jsonl` 目前只包含 3 條 metrics 行，與 W4-C CI 有關，**不包含** index 相關的指標。
- 暫無 index 專屬的 metrics JSONL 檔案。

### f) 現有 run_records
- `20_pilot/W3-A_case/run_records/` 下有 6 個 run id 目錄，全部是 W4-A rollout 相關（shadow/canary），**不包含** index 相關的 run 記錄。
- 尚無專屬 index 的 run_records 目錄。

---

## (4) 建議的實作步驟（高層）

以下步驟描述未來 runtime 開工時應該怎麼做。每一步只寫「要做什麼」，不寫具體命令。

### Step 1：確認 scope 範圍

實作方先確認 W2-1_case 的 `kb_index_subtree=core` 實際涵蓋哪些檔案。直接方法：
（a）從 `04_art_eng_ctx.md` 讀取 `allowed_scope`，確認 `core/` 目錄的範圍。
（b）快速統計 `core/` 下的檔案總數與估計的 chunk 數（可根據檔案大小與類型推算）。
（c）記錄 scope 的實際 file_count 與 chunk_count，供後續驗證比對。

**產出**：一個簡單的數字（如 `core/` 下 N 個檔案、約 M 個 chunk），寫入實作日誌。

### Step 2：產出真實的 index_status_W2-1.json

在**不修改暗部 indexer** 的前提下，根據 Step 1 的真實數字更新 `index_status_W2-1.json`：

（a）保留原始的 `schema_version`, `case_id`, `job_type`, `job_id`, `scope`, `scope_digest` 等欄位。
（b）將 `result_summary.file_count` 從 `0` 改為實際檔案數（N）。
（c）將 `result_summary.chunk_count` 從 `0` 改為實際 chunk 數（M / 估計值）。
（d）可選：更新 `manifest_ref` 指向一個真實存在的 manifest 或略過（仍用 `sample.json` 但改 content）。
（e）**保留** `status: succeeded`，讓 sync/gate 視為真實成功。
（f）更新後的文件路徑不變：`workflow_v2/20_pilot/W3-B/index_status_W2-1.json`。

**產出**：更新後的 `index_status_W2-1.json`（file_count > 0, chunk_count > 0）。

### Step 3：執行 sync 腳本回填案卷

在 repo root 執行 `wf_kb_index_sync.ps1`：

（a）先以 `-DryRun` 確認變更集與預期一致。
（b）確認無 DryRun 後，執行正式 sync（無 `-DryRun`）。
（c）確認 exit code = 0（success/updated）且 stdout 顯示 `updated`。
（d）檢查 `W2-1_case.md` 的 `kb_index_current` 區段已更新，特別注意 `kb_index_evidence_refs` 指向的狀態 JSON 路徑。

**產出**：成功執行的 sync log + 更新後的 `W2-1_case.md`。

### Step 4：執行 gate 腳本驗證

在 repo root 執行 `wf_kb_index_gate.ps1`：

（a）對 `IMP-AI-READY` 執行 gate，確認 `verdict=allow`。
（b）確認 exit code = 0。
（c）記錄 stdout 輸出（包含 `kb_index_status=ready` 等）。

**產出**：成功的 gate run log + exit code 0。

### Step 5：可選—新增 index run_records

可選但建議：在 `20_pilot/W3-B_case/run_records/`（或類比路徑）下新增一個 run id 目錄：
- 包含 sync 與 gate 的執行日誌。
- 包含本次 index 的檔案統計摘要。
- 確保 CHK-W4 可引用這個 run record 作為「W4-B GAP-1 已修復」的證據。

**產出**：一個新的 run_records 目錄（如 `index_backfill_2026-05-31/`）含 log。

### 步驟總結流程圖

```
確認 scope
  ↓（Step 1: 統計 file_count / chunk_count）
更新 index_status_W2-1.json
  ↓（Step 2: file_count → N, chunk_count → M）
執行 wf_kb_index_sync.ps1（dry-run → 正式）
  ↓（Step 3: exit 0）
執行 wf_kb_index_gate.ps1
  ↓（Step 4: verdict=allow, exit 0）
新增 run_record（可選）
  ↓（Step 5: 證據留痕）
DONE
```

---

## (5) 風險與驗收要點

### 風險點

| 風險 | 說明 | 建議緩解措施 |
|------|------|-------------|
| **R1：scope 範圍模糊** | `kb_index_subtree=core` 未明確界定 src / test / docs 等是否納入。若 `core/` 實際包含大量非文字檔（如 venv、binary），chunk 數可能膨脹 | Step 1 先對 `core/` 做一次快速檔案類型統計。索引範圍以「文字檔 + 可被 repo_index_v1 chunk 的檔案類型」為限。若 chunk_count 估計困難，可以不加 chunk_count（或者 sync 腳本不檢查 chunk_count） |
| **R2：sync 腳本依賴 powershell** | `wf_kb_index_sync.ps1` 需要在 Windows PowerShell 環境執行。Linux/WSL 可能無法原生跑 ps1 | 確認執行環境為 Windows / WSL 內的 PowerShell `powershell.exe`（非 pwsh），或使用 `pwsh` 跨平台版。若無法執行，可在 WSL 用 `pwsh -NoProfile -File ...` 或改用 Python 等效實作（若另行授權） |
| **R3：file_count / chunk_count 數值主觀** | 若無真實 indexer 跑過，file_count 和 chunk_count 是人工給定的估計值，可能與真實 index 結果有出入 | 在 run_record 中明確記錄「本數值為根據 scope 手動統計，非真實 repo_index_v1 輸出」。若未來有真實 index run，可以覆蓋本數值 |
| **R4：不影響其他 case** | 若未來 W5-B 擴面到其他 case，W2-1 的 index 回填可能成為模板 | 在 run_record 中記錄「這是 W2-1 專用的真實回填」，並在 Ticket Memory 中標明「不設定 precedent」除非尚書省授權 |
| **R5：gate 仍通過但 file_count 仍為 0（遺漏更新）** | 若實作方忘了更新 index_status.json（仍為 0），sync 和 gate 仍會通過（因為 gate 不看 file_count） | Step 2 完成後應檢查 `index_status_W2-1.json` 的 `result_summary.file_count` 確實變更了；Step 3 的 dry-run 也應確認。**如需在 gate 層驗證**，可另開增強票（W5-B-GATE-STRENGTHEN） |
| **R6：observability 缺口** | `gov_gate_metrics/` 下目前無 index 相關 metrics 序列 | 本票**不**修這個缺口（屬 W5-C 範圍）。但須在戰報中記錄「index 層尚無觀測指標時間序列」 |

### 驗收 Criteria

執行方完成後，至少須滿足以下驗收點：

| # | 驗收點 | 證據 |
|---|--------|------|
| V1 | `index_status_W2-1.json` 的 `file_count > 0` 且 `chunk_count > 0`，且值合理 | 讀取 JSON 的 `result_summary` 欄位，比對 `core/` 目錄的實際檔案數 |
| V2 | `wf_kb_index_sync.ps1` 執行後 exit code 0，且 stdout 顯示 `updated` | 終端機輸出的 log 截圖 |
| V3 | `W2-1_case.md` 的 `kb_index_current` 區段中 `kb_index_evidence_refs` 指向更新後的狀態 JSON | 讀取 `W2-1_case.md` 的 `kb_index_evidence_refs` 欄位 |
| V4 | `wf_kb_index_gate.ps1`（對 IMP-AI-READY）exit code 0（verdict=allow） | 終端機輸出的 log（含 `VERDICT=allow`） |
| V5 | `index_status_W2-1.failed_infra.json` 未被修改 | 對比該檔案的 git diff（或 checksum） |
| V6 | 未修改 `00`/`90`/`99`、`.github/workflows/*`、暗部腳本 | 全域 git diff 確認 |
| V7 | 可選：run_record 目錄存在且有執行摘要 log | 目錄內容 list |

---

## (6) 給未來實作票的任務卡骨架

> 以下為「給 Cursor / 實作端的任務卡骨架」。開 runtime 票時可複製此骨架，填入具體路徑與參數。

```
# Task Card — W5-D-W4-FIX-B Runtime

## 目的
在 W2-1_case 上完成一次真實 index 回填（修復 CHK-W4 GAP-W4-B1）。

## 操作範圍（允許觸及的檔案）

### 讀取（read_set）
- `workflow_v2/20_pilot/W2-1_case/W2-1_case.md`（特別看 kb_index_current 區段）
- `workflow_v2/20_pilot/W2-1_case/04_art_eng_ctx.md`（看 scope 定義）
- `workflow_v2/20_pilot/W3-B/index_status_W2-1.json`（更新對象）
- `workflow_v2/20_pilot/W3-B/index_status_W2-1.failed_infra.json`（只讀，不修改）
- `workflow_v2/tools/wf_kb_index_sync.ps1`（使用它，不修改）
- `workflow_v2/tools/wf_kb_index_gate.ps1`（使用它，不修改）
- `workflow_v2/20_pilot/W3-B/W4-B_orch_integration.md`（參考）

### 寫入（write_set）
- `workflow_v2/20_pilot/W3-B/index_status_W2-1.json`：更新 file_count / chunk_count
- `workflow_v2/20_pilot/W3-B/W2-1_case/W2-1_case.md`：經由 `wf_kb_index_sync.ps1` 更新（非直接編輯）
- `workflow_v2/20_pilot/W3-B_case/run_records/index_backfill_<DATE>/`（可選）：新增 run record

## 允許的操作類型
- 使用 `wf_kb_index_sync.ps1` 執行 sync（不修改腳本本身）
- 使用 `wf_kb_index_gate.ps1` 執行驗證（不修改腳本本身）
- 編輯 `index_status_W2-1.json` 的 `result_summary.file_count` / `chunk_count`（基於真實統計）
- 可選：建立 run_record 目錄與日誌

## 禁止的操作
- 修改 `wf_kb_index_sync.ps1`、`wf_kb_index_gate.ps1` 本身
- 修改 `00_master_plan.md`、`90_run_queue.md`、`99_latest_status.md`
- 修改 `.github/workflows/*`、暗部腳本、venv、`.env`
- 觸碰 G7/G8 治理語義
- 執行任何 production 敏感操作

## 必須完成的測試與回報格式

測試命令（預期在 repo root 執行）：

```
# Step 1: Check scope
ls core/ | wc -l              # 確認 file_count 基數

# Step 2: Dry-run sync
pwsh -NoProfile -File workflow_v2/tools/wf_kb_index_sync.ps1 -CaseDir workflow_v2/20_pilot/W2-1_case -StatusJson workflow_v2/20_pilot/W3-B/index_status_W2-1.json -DryRun

# Step 3: Actual sync
pwsh -NoProfile -File workflow_v2/tools/wf_kb_index_sync.ps1 -CaseDir workflow_v2/20_pilot/W2-1_case -StatusJson workflow_v2/20_pilot/W3-B/index_status_W2-1.json

# Step 4: Gate verify
pwsh -NoProfile -File workflow_v2/tools/wf_kb_index_gate.ps1 -CaseDir workflow_v2/20_pilot/W2-1_case -TargetImpState IMP-AI-READY
```

回報格式（最少內容）：
```
## Execution Report — W5-D-W4-FIX-B

### Step 1: Scope check
- core/ file count: <N>
- Estimated chunks: <M>
- Scope summary: <2–3 行描述 scope 範圍>

### Step 2: index_status update
- Updated index_status_W2-1.json → file_count=<N>, chunk_count=<M>
- (選填) manifest_ref 更新情況

### Step 3: Sync
- Dry-run output: <貼結果>
- Actual sync exit code: <0/1/2/3>
- Actual sync stdout: <貼結果>

### Step 4: Gate
- Gate exit code: <0/1/2/3>
- Gate stdout (VERDICT=): <貼結果>

### Step 5: Run record (可選)
- Run record 路徑: <路徑>

### 自檢
- [ ] file_count > 0 且與 scope 一致
- [ ] sync exit 0 (updated)
- [ ] gate verdict=allow, exit 0
- [ ] failed_infra.json 未被修改
- [ ] 00/90/99/CI/暗部 未被修改
```

## 完成後的通報
完成後將執行報告貼回本票的 Notes，等待 Review lane（W5-D-REVIEW-01 或等價 reviewer）做 doc-sync 前的 only-read 審查。
```

---

## 附錄 A — CHK-W4 GAP 原文引用

> 摘自 `CHK-W4-WAVE4-CLOSURE.memory.md` **§W4-B Check Record** GAP-1：
>
> `index_status.json` 的 file_count/chunk_count=0 — 樣本資料，非真實 indexing 結果
>
> → 建議票：**W4-B-FIX-01**（在 W2-1 case 上執行一次真 index 回填）

本方案即針對此 gap。W4-B-FIX-01 在 Wave 5 的命名為 **W5-D-W4-FIX-B**（Wave 5 清理軸下的 W4-B fix）。
