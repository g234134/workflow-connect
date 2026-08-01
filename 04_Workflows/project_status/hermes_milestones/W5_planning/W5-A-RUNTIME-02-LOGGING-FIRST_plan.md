# W5-A-RUNTIME-02-LOGGING-FIRST — Wave 5-A 第二條 runtime 線（logging-first design）

> **票號**：W5-A-RUNTIME-02-LOGGING-FIRST-PLAN-01（設計方案卡）
> **位置**：W5-A 軸的第二條 runtime 線 — **只寫 log、不 deny、不改 verdict**
> **範圍**：選一條 CI workflow 掛 logging step，調用 dry-run CLI 並將其摘要資訊印到 CI log + 附加 artefact；不修改任何 gate 行為或 exit code
> **不處理**：任何形式的 gate deny / block PR / pipeline 停止 / verdict override
> **先決**：
>   - W5-A-RUNTIME-01-DRYRUN 已落地（dry-run CLI + per-record/summary 報表 + README）
>   - W5-A-RUNTIME-PLAYBOOK 已建立（乾跑治理模式標準化）
>   - AC-DRY-1~6 全部通過（RUNTIME-01 驗收完成）
> **參考**：
>   - `W5-A-RUNTIME-01-DRYRUN_plan.md`（乾跑設計完整稿）
>   - `W5-A-RUNTIME-PLAYBOOK.md`（乾跑治理模式條目，含 AC-DRY）
>   - `W5-A-RUNTIME-01-DRYRUN_BRIEF_TASK_FOR_CURSOR.md`（乾跑實作 brief）

---

## (1) 目的與定位

### 1.1 RUNTIME-02 在 W5-A 軸中的位置

```
RUNTIME-01 (乾跑)      RUNTIME-02 (logging)      RUNTIME-03 (deny)
┌──────────────┐       ┌──────────────┐          ┌──────────────┐
│ 只讀 artefact│  ──→  │ CI 內印 log  │  ──→     │ 限域 deny    │
│ 產本地報表   │       │ + 附加 JSON  │          │ + override   │
│ 不碰 CI      │       │ 不碰 verdict │          │ + rollback   │
└──────────────┘       └──────────────┘          └──────────────┘
     v0.1 done              本票                  未來（下一張）
```

每一層的安全性擔保：

- **RUNTIME-01**：完全不接觸 CI。即使 rules 全錯或 bug 全炸，也不影響任何產線流程。
- **RUNTIME-02**：首次進入 CI，但 **只寫入 observability 面**（log、artefact）。即使 step 掛掉或 log 格式錯，也不改變 pipeline 成功/失敗狀態或 gate verdict 值。
- **RUNTIME-03**：開始在有限 scope 內改變 pipeline 行為（特定 gate tag → deny）。這一步需要 RUNTIME-01/02 的實戰數據來支持 threshold 選擇與 override 設計。

### 1.2 為什麼需要 logging-first 而非直接跳到 deny

五個理由：

1. **CI workflow 首次接上治理邏輯** — RUNTIME-01 完全不碰 CI，RUNTIME-02 是第一次有程式碼在 CI 環境中調用治理規則。必須先確認 CI 環境中的路徑、權限、依賴、乾跑 CLI 行為都正確，才能在後續票中開始影響 pipeline 決策。

2. **觀測 baseline 從本地 ➝ CI 可索引** — RUNTIME-01 的報表存在本地檔案系統，只有手動執行的人才看得到。RUNTIME-02 把乾跑摘要寫入 CI log + artefact，讓團隊成員可以在 CI run 頁面上直接看到治理快照，不需登入任何機器。

3. **規則 threshold 的 CI 環境校準** — 乾跑規則在本地 artefact 上表現良好（match ratio 高），但在 CI 環境的 artefact snapshot 上是否也一樣？RUNTIME-02 可以在每次 CI run 時自動確認。

4. **為 RUNTIME-03 建立歷史記錄** — RUNTIME-02 的 log artefact 會隨每個 CI run 累積，形成一份「治理差異趨勢」的時間序列。RUNTIME-03 的 threshold 選擇需要這份資料作為決策依據。

5. **強制團隊習慣治理可視化** — 在 CI 中看到治理 log 的團隊，會自然形成「治理差異是日常運營資料的一部分」的認知，降低後續導入 deny 時的文化阻力。

### 1.3 主要風險：被誤解為已 enforce

**RUNTIME-02 最真實的風險不是技術面，而是溝通面** — 團隊看到 CI log 中有 `DENY` 字樣，可能以為這條 pipeline 已經在 block 什麼東西了。因此本計劃的每一層設計（log 格式、免責文字、step 命名）都要防止這種誤解。

> **一句話定位**：RUNTIME-02 讓治理訊號進入 CI，但它只是「燈號」，不是「閘門」。

---

## (2) 範圍與輸入輸出

### 2.1 目標 CI workflow

**抽象名稱**：`k2-shadow-nightly-CI`（一條 nightly 或 per-merge shadow eval workflow，已有 shadow_eval_results / gate verdict artefact 產出）

選擇這條 workflow 的理由：
- 它是 RUNTIME-01 讀取的 artefact 的直接來源，output/input 對齊最簡單。
- 這是一條 nightly（非每 commit 觸發），頻率低，初期容錯高。
- 它不直接處理 production release，降低溝通誤解風險。

> 注意：這只是抽象名稱。未來實作時，實作者需用 `find` / `ls` 確認實際 CI workflow 的路徑與 job 結構。

### 2.2 輸入

RUNTIME-02 logging step 的輸入有兩種可行方案：

**方案 A（建議）— 直接調用 dry-run CLI：**

```
CI workflow nightly job
   └── logging step
        ├── 執行：python -m tools.dryrun --input-dir <artifacts/eval/> --output-dir <temporary>
        ├── 讀取 stdout（總記錄數、match_ratio、unknown 佔比）
        └── 讀取產出的 summary JSONL/markdown
```

- 優點：重用已驗證的 CLI，不需要再維護一套 parser。
- 依賴：CI 環境需安裝 dry-run module 的依賴（Python + 標準庫，無額外 heavy dep）。

**方案 B（備選）— 讀取 dry-run CLI 預先產出的報表：**

```
CI workflow nightly job
   └── logging step
        ├── 讀取：observability/dryrun/<latest>_summary.md
        └── 解析：從 markdown 中擷取統計數據
```

- 優點：即使 dry-run CLI 在 CI 環境中無法安裝（錯的 Python 版本等），logging step 仍可運作。
- 缺點：markdown 解析脆弱；需要額外邏輯來定位「最新報表」。

**本 plan 建議實作選擇方案 A**（方案 A 更穩健），但不在本 plan 中鎖死 — 實作票可以自行決定。

### 2.3 輸出

RUNTIME-02 的輸出全部在 CI 的 observability 面，不會寫入任何 prod/pipeline 決策狀態。

**強制輸出：CI log 中的簡短摘要**

每次 step 執行時，在 CI log 中印出以下內容（一行或多行）：

```
[DRYRUN-LOG] ⚠ DRY-RUN — 不影響任何 CI/pipeline 決策
[DRYRUN-LOG] Total records: 847 | Match: 91.3% | Unknown: 1.2% | Mismatch: 63 (7.5%)
[DRYRUN-LOG] Ideal breakdown: allow=520 warn=210 deny=80 needs_review=25 unknown=12
[DRYRUN-LOG] Gate tag analysis — 5 records with security:critical flagged under deny
[DRYRUN-LOG] ⚠ Differences found: 63 records where gate_verdict ≠ ideal_verdict
[DRYRUN-LOG]   Top-gap rule: gate_ok_score_low (38 records — actual=allow, ideal=warn)
```

每一行都要以 `[DRYRUN-LOG]`（或等價標籤）開頭，讓 logs 可被 grep 快速過濾。

**可選輸出：附加 CI artefact**

- 將 per-record JSONL 或 summary JSON 上傳為 CI run 的附加 artefact（如 `observability/dryrun-ci/<run-id>_summary.json`）。
- 命名慣例應包含 CI run ID，避免不同 run 的 artefact 互相覆蓋。
- 保留策略：可沿用 RUNTIME-01 的 `observability/dryrun/` 保留策略，或由後續 DOCSYNC 票統一決定。

---

## (3) 邊界與風險控制

### 3.1 硬邊界（6 條）

| # | 邊界 | 說明 | 違反實例 |
|---|------|------|---------|
| L1 | **不改 gate verdict / exit code** | logging step 的 `exit 0` 或 `exit 1` 不得影響 pipeline 最終結果。step 永遠設定 `continue-on-error: true` 或等價機制。 | step 失敗時 pipeline 也跟著紅掉 |
| L2 | **不讓 logging step 決定 pipeline 成功/失敗** | pipeline 的成功/失敗判斷權力完全保留在原有的 gate 步驟。logging step 只是旁觀者。 | logging step 的 exit code 被傳遞到 job 層級 |
| L3 | **step 自身失敗只印 warning** | 若 dry-run CLI 本身 crash（輸入 artefact 不存在、路徑錯誤、依賴缺失），logging step 應捕捉此異常、印出 [DRYRUN-LOG] [WARN] 訊息，然後正常結束。 | step 失敗導致整個 workflow 變紅或需要人工重跑 |
| L4 | **所有 log line 帶顯眼 tag** | 每一行 CI log 前綴 `[DRYRUN-LOG]`（或等價標籤），讓讀者在 log 中一眼看出這是模擬/觀察用資訊，非正式 gate 訊息。 | log 混在既有 pipeline 的 INFO/WARN 行中，無從區分 |
| L5 | **不寫入任何 prod 資料庫 / CI check API** | artefact 只寫到 CI 內建的 artifact storage（如 `actions/upload-artifact`）或本地 temp 路徑，不上傳到外部資料庫、check API、或 production dashboards。 | step 把 summary 寫入外部 MySQL / Prometheus / Datadog |
| L6 | **不修改 RUNTIME-01 既有的 CLI / 報表 / README** | RUNTIME-02 新增 CI workflow step，但保留乾跑 CLI 本身不動。不為 logging-first 修改 dry-run CLI 的原有介面或輸出格式。 | 為了讓 CI 解析更方便，改寫 `summary.md` 的格式 |

### 3.2 風險 scenario 與緩解

| # | 風險 | 影響 | 緩解 |
|---|------|------|------|
| R1 | **log 中的 deny/needs_review 字樣被團隊誤解為已 enforce** | 開發者以為這些記錄已被 gate 阻擋，產生錯誤的安全感 | ① 每行 log 前綴 `[DRYRUN-LOG]`；② 首行免責文字；③ 在 README 或 ONBOARDING 文件中說明 logging-first 階段的定位 |
| R2 | **CI 環境路徑/權限與本地不同，導致 dry-run CLI 執行失敗** | logging step 變成純 warning，無輸出 | 使用 `continue-on-error: true` + `[DRYRUN-LOG] [WARN]` 輸出。不在 CI 環境中首次執行時才發現問題 — 實作票應含「本地模擬 CI 環境測試」步驟 |
| R3 | **累積的 CI artefact 越來越多，沒有清理機制** | 磁碟使用量緩慢成長 | 建立 artefact 保留政策（如保留最近 30 天或最近 100 次 run）；可在實作票中加入一個簡單的清理腳本，或由後續 DOCSYNC 票統一處理 |
| R4 | **log 格式變更導致下游 script 解析失敗** | 依賴 log 格式的自動化工具中斷 | log 輸出格式應寫在 README 中作為契約；格式變更必須通過至少一次 PR review，且應保留至少一個 CI run 的相容性過渡期 |

---

## (4) 與 PLAYBOOK 的對應

### 4.1 哪些 PLAYBOOK 內容可重用

RUNTIME-02 直接站在 RUNTIME-PLAYBOOK 的肩膀上：

| PLAYBOOK § | RUNTIME-02 的使用方式 |
|------------|----------------------|
| **§3 標準輸入/輸出** | RUNTIME-02 直接消費乾跑 CLI 的輸出（per-record JSONL + summary）作為 logging step 的資料來源。輸出格式與 RUNTIME-01 保持相容。 |
| **§4 邊界 B1–B7** | RUNTIME-02 新增 L1–L6 邊界（專屬於 logging-first CI step），但保留 B1–B7 作為底線（特別是 B1「僅新增檔案」— RUNTIME-02 只改選定的 CI YAML 檔案，不修改既有程式碼）。 |
| **§5 治理規則模式** | 乾跑 CLI 內的治理規則引擎（五 bucket + edge_unknown）原封不動。RUNTIME-02 不新增或修改規則。 |
| **§6 AC-DRY-1~6** | AC-DRY-1~6 是 RUNTIME-02 的**前置依賴**— 只有在 AC-DRY 全過（即乾跑 CLI 已驗證）的情況下，才允許將它接進 CI。 |

### 4.2 前置依賴：AC-DRY 全過

在開始 RUNTIME-02 實作前，必須確認以下條件全部成立：

- [ ] AC-DRY-1：乾跑 CLI 存在且可被 `python -m tools.dryrun` 呼叫
- [ ] AC-DRY-2：per-record JSONL + summary markdown 欄位齊全
- [ ] AC-DRY-3：五 bucket 規則覆蓋完整，且有 edge_unknown 出口
- [ ] AC-DRY-4：乾跑 CLI 僅新增檔案，未改既有 code/CI/artefact
- [ ] AC-DRY-5：乾跑 CLI 通過至少一組 unit test
- [ ] AC-DRY-6：免責聲明在 CLI stdout / 報表 / README 三處明確

### 4.3 實作票可引用的 PLAYBOOK 段落

未來 W5-A-RUNTIME-02-IMPLEMENTATION-01 票在撰寫時，應直接引用：

- `W5-A-RUNTIME-PLAYBOOK.md §3`：輸入/輸出格式的參考規範
- `W5-A-RUNTIME-PLAYBOOK.md §4`：底線邊界（與 §3 的新 L1–L6 合併使用）
- `W5-A-RUNTIME-PLAYBOOK.md §6`：前置驗收條件（AC-DRY checklist）
- `W5-A-RUNTIME-PLAYBOOK.md §7`：如何沿用到其他 repo（若 RUNTIME-02 需要跨多個 repo 部署）

---

## (5) 草擬未來 Implementation 骨架

### 5.1 未來「W5-A-RUNTIME-02-IMPLEMENTATION-01」的高層骨架

> 以下僅為未來實作票的大致形狀，不是本 plan 的約束。實作時實作者有權選擇具體的 CI YAML 語法、step 順序、artefact 上傳方式。

```
Step 0：前置確認
  確認 RUNTIME-01 已落地（dry-run CLI 可呼叫、報表格式正確）
  確認 AC-DRY-1~6 全部通過
  確認目標 CI workflow 的 artefact 路徑可被 CLI 讀取

Step 1：CI YAML 中新增 logging step
  ┌─ 在選定的 .github/workflows/<目標>.yml 中新增一個 step
  │  位置：在 shadow_eval_results 產生之後、gate 步驟之前
  │  名稱：Dry-run governance logging (observability only)
  │  條件：continue-on-error: true
  │  腳本：python -m tools.dryrun --input-dir ${{ env.ARTIFACTS_DIR }} --output-dir ${{ runner.temp }}/dryrun-ci/
  │
  │  產出：
  │    ① CI log 中印出摘要行（[DRYRUN-LOG] 前綴）
  │    ② 可選：上傳 summary JSON 為 CI artefact

Step 2：異常處理
  若 step 執行失敗（例如 artifact 路徑不存在、CLI crash）：
    └→ 印出 [DRYRUN-LOG] [WARN] 訊息
    └→ continue-on-error: true 確保 pipeline 不紅
    不做：重試機制、告警、通知、改寫 pipeline 狀態

Step 3：log 格式確認
  人工確認 CI run 中的 log 行：是否帶 [DRYRUN-LOG] 標籤、有免責文字、
  有總記錄數 / match_ratio / unknown / mismatch 統計

Step 4：測試與回報
  至少手動觸發 CI 一次 確認 step 正確執行
  若無法觸發真實 CI（需額外權限），提供 dry-run 的本地模擬方法
  回報格式：CI run URL / 本地模擬輸出 / artefact 下載鏈接（若適用）
```

### 5.2 本 plan 不做的最終決策

由於具體 CI 環境細節超出純設計稿範圍，以下事項由未來實作票決定：

- 具體 target workflow 的檔案路徑與 YAML job 名稱
- 使用 GitHub Actions `continue-on-error` 或等價機制
- 用 `actions/upload-artifact` 還是用本地 mount 來附加 artefact
- 是否要為 logging step 建立獨立的 job（與原有 shadow eval job 分離）或直接嵌入既有 job 的 step 列表中
- 是否要使用 Python 腳本包裝器還是直接 call CLI

---

## (6) 後續擴展 slot

| 後續票 | 預期行為 | 與本票的關係 |
|--------|---------|-------------|
| **W5-A-RUNTIME-02-IMPLEMENTATION-01** | 在選定的 CI workflow 中掛上 logging step，完成 log + artefact | 本 plan 的直接實作票 |
| **W5-A-RUNTIME-03**（Limited gate deny） | 在有限 scope 下啟用真正的 gate deny + override/rollback | RUNTIME-02 累積的 CI log 資料將作為 threshold 選擇與 deny scope 的設計依據 |
| **W5-A-DOCSYNC-01** | artefact 保留策略、CI artefact 管理 SOP | RUNTIME-02 產出的 CI artefact 累積策略由本票定義 |
| **W5-A-RUNTIME-DESIGN-REVIEW-02** | 審查 RUNTIME-02 的 CI 設計與 log 格式是否適合長期運作 | 本 plan 交付後可排 reviewer |

---

## 附錄 A — 與既有文件的對應

| 文件 | 關係 | 注意 |
|------|------|------|
| `W5-A-RUNTIME-01-DRYRUN_plan.md` | RUNTIME-01 的完整設計。RUNTIME-02 站在它的輸出之上。 | 不修改原文。RUNTIME-02 引用其 §(5) 後續擴展 slot 中對 RUNTIME-02 的描述。 |
| `W5-A-RUNTIME-PLAYBOOK.md` | 治理/PLAYBOOK 條目。RUNTIME-02 直接引用其 §3、§4、§6。 | 不修改原文。RUNTIME-02 將其視為前置依賴。 |
| `W5-A-RUNTIME-01-DRYRUN_BRIEF_TASK_FOR_CURSOR.md` | 乾跑實作 brief。實作票可參考其回報格式框架。 | 不修改原文。 |
| `W5_OVERVIEW.md` | Wave 5 總覽。RUNTIME-02 完成後應更新進度小節。 | 本計劃不更新 overview（屬於未來 DOCSYNC 票）。 |
| `W5_TICKET_TEMPLATES.md` | 票模板。未來 RUNTIME-02-IMPLEMENTATION-01 票可使用模板 1 (W5-A 型) 作為骨架。 | 不修改原文。 |

---

## 附錄 B — 版本歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.1 | 2026-05-31 | W5-A-PLANNING | 首版 RUNTIME-02-LOGGING-FIRST 設計方案卡。定義目的、範圍、邊界、與 PLAYBOOK 的對應、未來實作骨架。 |
