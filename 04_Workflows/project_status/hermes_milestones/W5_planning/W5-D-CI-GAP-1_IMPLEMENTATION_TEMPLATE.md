# W5-D-CI-GAP-1-IMPLEMENTATION-01 — eval_export/v1 baseline 生產鏈補全（實作票模板）

> **用途**：這份模板是給實作者（Cursor／開發者）開工用的任務卡。  
> **源頭**：`W5-D-CI-GAP-1_plan.md`（方案卡）→ 第 (4) 節三個選項 + 第 (5) 節風險/驗收。  
> **範圍**：僅 shadow/nightly 線路的 CI data pipeline；**不改** gate 判決邏輯、prod user data 擴散、PR workflow。  
> **Lane 推定**：`runtime`（CI workflow 變更）。

---

## 1) 基本資訊

| 欄位 | 值 |
|------|-----|
| **任務名稱** | W5-D-CI-GAP-1-IMPLEMENTATION-01 |
| **任務說明** | 補上 eval_export/v1 JSONL 的 CI 生產鏈，讓 eval_stats 可在不手動跑 exporter 的情況下消費真實資料，並在 eval_stats_report.md 上獲得 N≥10 的 baseline  |
| **缺失鏈路** | `shadow_ibridge_records.latest.jsonl` → ❌ eval_exporter → ❌ eval_stats / eval_stats_report |
| **主標的工作流** | `.github/workflows/eval-gate-ci.yml`（或等效 CI workflow，請依實際倉庫結構確認檔名） |
| **次標的檔案** | `observability/eval_stats_report.md`（可選更新 baseline） |
| **非範圍** | `eval_ci_check` gate verdict 邏輯、`ibridge_exporter` spool 來源、PR-level `eval-gate` job、任何 prod/customer-facing data path |

### 允許的操作類型

- 在現有 nightly CI job 中新增一個 step，執行 `python -m observability.eval_exporter <input> -o <output>`（選項 A）
- 新增獨立 nightly workflow，從頭生產 eval_export/v1 JSONL（選項 B）
- 調整 artifact 命名或上傳路徑（不改變 `eval_ci_check` 的輸入變數）
- 在 `eval_stats_report.md` 追加一節 CI 生產的 baseline 分析（選項 A/B 驗收後，或選項 C 的說明更新）

### 不允許的操作

- **不改 `eval-gate` job（PR trigger）** — 不增加每次 PR 的 heavyweight 成本
- **不改 `eval_ci_check` 的 gate 邏輯、exit code 行為或 verdict 輸出**
- **不將 `eval_export/v1` 資料用於 prod 或 customer-facing 場景**
- **不改 `ibridge_exporter` 的 shadow spool 來源或 bootstrap 參數**
- **不改現有 deny/allow semantics**
- **不改任何 YAML 以外的 repo 檔案**（如 Python 模組、fixture 資料等）
- **不得建立新的 gate 或 CI 關卡** — 只補 data 生產鏈

---

## 2) 前提與不變條件

### 實作前須成立

- [ ] `eval-shadow-nightly` job（或等效 nightly job）可順利執行，產出 `shadow_ibridge_records.latest.jsonl` 並上傳為 CI artifact
- [ ] `eval_ci_check` 在 current CI 上 pass/fail 行為穩定，無誤報或 flicker
- [ ] `python -m observability.eval_exporter --help` 可於 CI venv 中正常執行（確認 entry point 已安裝）
- [ ] `eval_exporter` 的 `iter_records` 可接受 `ibridge JSONL` 作為輸入（已知 ✅）
- [ ] 實作者能取得一個真實的 CI run log（含 `shadow_ibridge_records.latest.jsonl` artifact），供新增 step 前後的對比

### 不得改動的事項（不變條件）

1. **不改 gate verdict rule**：`eval_ci_check` 的 `--max-needs-review-ratio`、`--fail-on-tags` 的 threshold 在本次不調整。threshold 更新屬於 baseline 穩定後的第二迭代。
2. **不改現有 deny/allow semantics**：gate 的 pass/fail 判定邏輯在新增 step 前後必須完全一致。
3. **不將新 step 接到 prod data**：資料只從 `shadow_ibridge_records.latest.jsonl` 或 fixture 來，不連接 prod 串流或真實 user 資料庫。
4. **不增加 PR 每次必跑的 heavyweight job**：任何新增的 producer step 只限於 `schedule` / `workflow_dispatch` 觸發的 nightly/optional 流程。`pull_request` 觸發的 `eval-gate` job 不得新增 step。
5. **不改 `evaleval_` 以外的變數名或路徑常量**：`EVAL_CI_INPUT`、`EVAL_CI_LIMIT`、`eval_results.latest.jsonl` 等名稱以現有 CI 環境為準，不在本次新增未定義變數。

---

## 3) 具體步驟（實作 checkllist）

以下步驟以 **選項 A（在現有 nightly job 中追加 step）** 為主要路線。實作者若決定選 B 或 C，請跳到每個步驟末尾的「若選 B/C 差異」標記。

### Step 1 — 確認現有 nightly job 的結構與輸入輸出路徑

| 項 | 內容 |
|---|------|
| **目標文件** | `.github/workflows/eval-gate-ci.yml`（按實際路徑確認） |
| **做什麼** | 找出 `eval-shadow-nightly` job 的 step 序列，確認以下資訊： |
| | (1) `ibridge_exporter` step 輸出 `shadow_ibridge_records.latest.jsonl` 的完整路徑 |
| | (2) 該 JSONL 後續是否上傳為 artifact（artifact name 與上傳路徑） |
| | (3) `eval_ci_check` step 的 CLI 完整參數（確認其輸入是直接吃 JSONL 還是用變數） |
| | (4) job 的 `runs-on`、`timeout-minutes`、`concurrency` 等執行環境設定 |
| **輸出** | 記錄上述資訊，供 Step 2 設計 exporter step 時參考 |

### Step 2 — 在 `eval-shadow-nightly` job 中新增 eval_exporter step（核心）

| 項 | 內容 |
|---|------|
| **目標文件** | `.github/workflows/eval-gate-ci.yml` — `eval-shadow-nightly` job |
| **做什麼** | 在 `eval_ci_check` step 之後，新增一個 step，執行： |
| | `python -m observability.eval_exporter <現有ibridge_path> -o artifacts/eval/eval_results.latest.jsonl` |
| | 其中 `<現有ibridge_path>` 從 Step 1 的記錄取得（通常是 runner workspace 內的路徑） |
| **step 名稱建議** | `Export eval_results JSONL (eval_export/v1)` |
| **附加動作** | (1) step 的 stdout 中應輸出 `exported X line(s)` 等確認訊息（eval_exporter 預設已有） |
| | (2) 可選同步輸出一個日期版 `eval_results.%YYYYMMDD%.jsonl`（用 `%` 或 jq 格式化當日日期） |
| | (3) 若 CI 有 artifact upload 機制，考慮將輸出的 JSONL 上傳為 artifact |
| **若選 B** | 不在此 job 新增 step。改為新增獨立的 workflow（見 Step 5）。 |
| **若選 C** | 不修改任何 CI YAML。跳至 Step 6。 |

### Step 3 — 可選：新增 eval_stats 呼叫產生簡短 baseline

| 項 | 內容 |
|---|------|
| **目標文件** | `.github/workflows/eval-gate-ci.yml` — `eval-shadow-nightly` job（選項 A） |
| **做什麼** | 在 exporter step 之後，可選追加一個 step 執行： |
| | `python -m observability.eval_stats artifacts/eval/eval_results.latest.jsonl --format json --min-samples 10` |
| **step 名稱建議** | `Short eval_stats baseline (optional)` |
| **注意** | (1) 如果 N<10，`eval_stats` 會自動標 low confidence，不影響 exit code |
| | (2) 這一步**不是** gate，只是可觀測性輸出。將 stdout/log 儲存在 CI run log 中供人查閱即可 |
| | (3) 如果 CI 時間成本敏感，這一步可跳過（只在 exporter step 完成後手動呼叫 stats） |
| **若選 B** | 在獨立 workflow 中，可將此 step 設為必要（因為是該 workflow 的主要目的）。 |
| **若選 C** | 跳過。 |

### Step 4 — 驗證 gate verdict 不變

| 項 | 內容 |
|---|------|
| **做什麼** | 用**同一個 artifact（同一次 nightly run）** 分別跑一次有/無 exporter step 的 CI 對比： |
| | (1) 確認 `eval_ci_check` 的 verdict（pass/fail）前後一致 |
| | (2) 確認 `shadow_ibridge_records.latest.jsonl` 的輸出不受 exporter step 影響 |
| | (3) 記錄 exporter step 的耗時（預期 1–2s 可忽略） |
| **方法** | 更好的做法：先在 branch 上開一個 dry-run workflow，對同一個 artifact 同時跑「有 exporter step」和「純 eval_ci_check」，並比較兩者的 gate 輸出。如果 CI 不支援這種並行，至少在同一 run log 中先記錄 eval_ci_check verdict，再記錄 exporter 輸出，然後確認 verdict 未因 exporter 的 import 或 side-effect 而變。 |
| **若選 B** | 獨立 workflow 無此風險（不與 gate job 共用 python 行程式）。但仍然應記錄獨立 workflow 中的 eval_stats 輸出。 |
| **若選 C** | N/A。 |

### Step 5 — 若選 B：建立獨立的 nightly workflow

| 項 | 內容 |
|---|------|
| **目標文件** | `.github/workflows/eval-export-nightly.yml`（新增） |
| **做什麼** | 新增一個只跑 schedule / workflow_dispatch 的 workflow，包含： |
| | (1) `ibridge_exporter --source shadow` step（復用 `eval-shadow-nightly` 的 export 步驟，可依賴其 artifact 或重新執行） |
| | (2) `eval_exporter` → `eval_results.latest.jsonl` |
| | (3) 可選 `eval_stats --json` → 上傳 JSON artifact |
| | (4) 可選 `eval_stats --write-report observability/eval_stats_report.md`（自動追加新的 baseline 段） |
| **排程建議** | 每天 UTC 07:00（在 shadow nightly 之後，避免並行爭搶 spool） |
| **concurrency** | 設定 `concurrency.group` 確保不會與 `eval-shadow-nightly` 同時讀取同一份 spool |
| **若選 A** | 跳過此步驟。 |
| **若選 C** | 跳過此步驟。 |

### Step 6 — 若選 C：更新 eval_stats_report.md 說明

| 項 | 內容 |
|---|------|
| **目標文件** | `observability/eval_stats_report.md` |
| **做什麼** | 不修改 CI，但在報告中補充： |
| | (1) 在 §Limitations 或 §How to reproduce 中補上一段「eval_export/v1 目前僅能手動產出」的說明 |
| | (2) 給出完整的參考命令（ibridge_exporter → eval_exporter → eval_stats 整條鏈） |
| | (3) 明確標註所有 thresholds 為「基於 N=3 fixture，不具代表性」 |
| | (4) 將 CI-GAP-1 狀態記錄在已知限制中 |
| **若選 A/B** | 可選執行此步驟（在驗收後追加一次真實 baseline 的 `--write-report`）。 |

### Step 7 — 驗收巡檢（全量檢查）

| 項 | 內容 |
|---|------|
| **目標文件** | 所有修改過的 CI YAML / markdown |
| **做什麼** | 走一遍下方的驗收條件（§5），在回報模板（§6）中逐條記錄結果。 |

---

## 4) 風險與注意事項

### 實作端須留意清單

| # | 風險 | 注意事項 |
|---|------|---------|
| **R1** | **CI 時間增加（選項 A）** | eval_exporter 處理 N≤100 條 record 通常只需 ~1–2s，可接受。但仍建議在 step 內加上 `echo` 輸出耗時，或在 PR description 中記錄一次耗時實測值。 |
| **R2** | **shadow spool 敏感資料（選項 A/B）** | eval_exporter 只匯出摘要欄位（`metrics` subset，無完整 user record），但實作者仍應先確認 `build_export_line()` 的輸出**不含 PII**。若不確定，請先請示 reviewer/data owner，不得自行切換 data source。 |
| **R3** | **並發 workflow 搶檔案（選項 B）** | 若獨立 workflow 與 `eval-shadow-nightly` 同時讀取同一個 spool 檔案，可能產生不完整的 ibridge JSONL。解決方式：(1) 設定 `concurrency.group` 序列化；(2) 或讓獨立 workflow 依賴 `eval-shadow-nightly` 的 artifact 而非直接讀 spool。 |
| **R4** | **影子資料量不足時的低 confidence baseline** | `eval_stats` 的 `min_samples` 預設為 10，低於此會自動標 low confidence。實作後第一次跑可能 N<10（shadow spool 樣本少），屬正常現象。不要因為 N 小就調低 `min_samples` 或強制 pass。 |
| **R5** | **artifact 命名衝突或覆蓋（選項 A）** | 如果多個 workflow 同時寫入 `eval_results.latest.jsonl`，後跑的會覆蓋前一個。解決方式：同步使用日期版 `eval_results.YYYYMMDD.jsonl`，`latest` 只做 soft link 或 artifact alias。 |
| **R6** | **eval_stats_report.md 的 --write-report 附加寫入** | `--write-report` 是 append markdown section 到報告檔。如果 CI 跑多次，報告會累積多段 baseline 區塊。實作時應確認這是否為期望行為，或是否需要在每次執行前清空舊 Baseline 區塊。 |
| **R7** | **CI workflow 檔名不一定是 eval-gate-ci.yml** | 方案卡中使用的 `eval-gate-ci.yml` 是推測名。實作者須在倉庫 `.github/workflows/` 下確認實際檔名。如果找不到，應搜尋 `ibridge_exporter` 或 `shadow` 等關鍵字來定位。 |

### 通用原則

- **如果對資料敏感度不確定 → 請示 reviewer / data owner，不得自行切換 data source。**
- **新增的 step 必須在 log 中印清楚輸入檔路徑、輸出檔路徑、行數。**
- **所有 CI 變更應先在 fork/feature branch 上獨立測試，確認 `eval-shadow-nightly` job 的 `schedule` 或 `workflow_dispatch` 都能正常跑完。**
- **選項 A/B 完成後，至少保留一次 CI run log 作為「新增前後的 gate verdict 對比」證據。**

---

## 5) 驗收條件

實作者完成選定路線後，逐項檢查並填入結果。

| # | 驗收條件 | 如何驗證 | 實測結果 |
|---|---------|---------|---------|
| AC1 | CI log 中有清楚的 `exported X line(s) from Y record(s)` 輸出 | 在 CI run log 中搜尋 `exported` 字串 | |
| AC2 | `eval_stats` 可直接消費 CI 產出的 `eval_results.latest.jsonl`，回傳 N≥1 | `python -m observability.eval_stats artifacts/eval/eval_results.latest.jsonl --format json` 回傳非 zero N | |
| AC3 | 新增 step 前後的 `eval_ci_check` gate verdict 完全一致 | 用同一個 nightly artifact 對比有/無 exporter step 時 `eval_ci_check` 的 exit code 與 verdict message | |
| AC4 | 新增 job/step 僅影響 `schedule` / `workflow_dispatch`，不影響 `pull_request` | 確認 `eval-gate` job(PR trigger) 的 step 序列無新增項 | |
| AC5 | 若選 A/B：artifact 可下載且 JSONL schema 與 `tests/fixtures/eval/eval_export_sample.jsonl` 相容 | `head -1 artifacts/eval/eval_results.latest.jsonl | python -m json.tool` 可列印並包含 `exported_at` / `needs_review` / `tags` / `metrics` 等預期欄位 | |
| AC6 | 若選 B：獨立 workflow 的 concurrency 設定可防止與 `eval-shadow-nightly` 並行讀取 spool | 手動觸發兩個 workflow，確認不會同時進入 `ibridge_exporter` step | |
| AC7 | `eval_stats_report.md` 中至少有一段 baseline 基於 CI 產生的 eval_export/v1 資料（N≥1 即可，不強制 N≥10） | 讀取 `--write-report` 追加後的報告，確認新增的 Analysis run 區塊中有 `N=` 欄位且 `N` > 3 | |
| AC8 | 所有變更僅限於授權範圍（CI YAML + 可選的 `eval_stats_report.md`），未觸及 gate 邏輯或 prod data | `git diff --stat` 或等效檢查 | |

---

## 6) 回報格式模板

實作者完成後，按以下框架填寫回報。貼在實作票的 comment 或 Workspace 戰報中。

```markdown
### 實作回報 — W5-D-CI-GAP-1-IMPLEMENTATION-01

**實作日期**：YYYY-MM-DD
**實作者**：<role>
**選擇路線**：選項 A / 選項 B / 選項 C

#### 修改檔案清單

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `.github/workflows/<實際檔名>` | step 追加 / 新增 workflow / 無修改 | 簡述改了什麼 step 或加了多少行 |

#### 修改的工作流 / step 對照表

| 工作流 / job | Step 名稱（改動前） | Step 名稱（改動後） | 類型 |
|-------------|------------------|------------------|------|
| <eval-shadow-nightly> | — | `Export eval_results JSONL (eval_export/v1)` | 新增（選項 A） |
| <eval-export-nightly> | — | （完整 workflow 新增） | 新增（選項 B） |

#### 新增輸出檔路徑與 sample 片段

- **檔案**：`artifacts/eval/eval_results.latest.jsonl`（或等效路徑）
- **行數**：N = ?
- **Sample（第一行）**：
  ```json
  {"exported_at": "2026-05-31T12:00:00Z", "needs_review": false, ...}
  ```

#### CI run log 關鍵輸出

```
# exporter step stdout
exported 42 line(s) from 50 record(s)

# eval_stats baseline
N=42  needs_review=12  ratio=28.57%
suggested range: 0.35 – 0.55
```

#### gate verdict 對比摘要（前/後）

| 項目 | 改動前 | 改動後 | 一致？ |
|------|-------|-------|-------|
| eval_ci_check exit code | 0 | 0 | ✅ |
| eval_ci_check verdict message | `pass (needs_review ratio 12/42=28.57%, under ceiling 0.80)` | 同上 | ✅ |
| eval_ci_check 耗時（秒） | 5.2 | 5.3 | 可接受 |

#### 驗收條件檢查

| # | 通過？ | 備註 |
|---|-------|------|
| AC1 | [ ] | |
| AC2 | [ ] | `N=` |
| AC3 | [ ] | |
| AC4 | [ ] | |
| AC5 | [ ] | |
| AC6 | [ ] | （選項 B only） |
| AC7 | [ ] | （若使用 `--write-report`） |
| AC8 | [ ] | `git diff --stat` 結果： |

#### 已知殘留風險

- 列舉驗收條件中未完全通過的項及原因
- 列舉實作過程發現的可能改善點（如 artifact 命名衝突、spool 來源切換等）
- 列舉對資料敏感度（PII）的確認結果（已確認 / 請示後確認 / 待進一步審核）
```

---

## Extra Notes for Implementer

### 路線選擇建議

**優先考慮選項 A**（在 `eval-shadow-nightly` job 中追加一個 step）。原因：

- 改動最小（同一 job 內加一個 step，約 5–8 行 YAML）
- 輸入（`shadow_ibridge_records.latest.jsonl`）已經是 CI 執行中存在的檔案，無需新增獨立資料獲取步驟
- 不增加 PR job 成本（nightly-only）
- 如果後來發現選項 A 有問題（如 CI 時間增加不可接受、artifact 管理複雜），可以隨時退化到選項 C

**選項 B 適合的場景**：
- 你預期 future 需要獨立的排程控制（例如每天在不同時間跑 exporter + stats + report update）
- 你認為將 data pipeline 與 gate 流程解耦的維護成本值得付出
- CI runner 資源足夠承擔額外的 workflow 執行（獨立 workflow 需要額外的一組 runner minute）

**選項 C 適合的場景**：
- 當前 CI runner 資源或時間成本極度敏感
- eval_stats_report.md 短期內不需要真實 baseline（例如還在 feature development 階段，threshold 不具生產意義）
- 作為第一迭代，先誠實記錄限制，等資源到位後再切到 A/B

### 關於 eval_stats_report.md 的 --write-report

建議實作選項 A/B 通過驗收（AC2 達成）後，手動執行一次：

```bash
python -m observability.eval_stats artifacts/eval/eval_results.latest.jsonl \
  --group-by date --format text \
  --write-report observability/eval_stats_report.md
```

確認追加的 Analysis run 區塊中 `N=` 欄位 > 3。這樣 `eval_stats_report.md` 的 §Executive summary 就可以更新為基於真實資料的 baseline。

### 測試用的對比資料

在修改 CI 前，用一個真實的 CI nightly run 下載其 `shadow_ibridge_records.latest.jsonl` artifact，在本地跑一遍 exporter 確認輸出與預期相符：

```bash
python -m observability.eval_exporter <下載的jsonl> -o /tmp/eval_results.test.jsonl
wc -l /tmp/eval_results.test.jsonl
python -m observability.eval_stats /tmp/eval_results.test.jsonl --format json
```

這樣做可以在不碰 CI 的情況下先驗證整條鏈的可用性。

### 關於 artifact 命名

建議兩種命名策略都支援：
- `eval_results.latest.jsonl`（固定名，每次覆蓋，便於 CI 外部引用）
- `eval_results.20260531.jsonl`（日期版，保留歷史，便於回溯分析）

如果選項 A，至少要有 `latest` 版本；選項 B 可以兩者都產出。實作時應與 reviewer 確認 artifact retention policy。
