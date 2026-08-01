# W5-D-CI-GAP-1 — eval_export/v1 JSONL 無 CI 生產者 · 方案卡

> **票號**：W5-D-CI-GAP-1-PLAN-01（只讀方案卡）  
> **源頭**：eval_exporter readonly scan 發現 CI-GAP-1  
> **範圍**：評估是否在 CI 中補進 `eval_export/v1` JSONL 生產鏈  
> **不處理**：實際 CI YAML 修改、gate 語義變更、prod user data 擴散  

---

## (1) 背景摘要

**CI-GAP-1 是什麼**：  
目前 `eval_export/v1` JSONL（由 `eval_exporter` 產生）**完全沒有 CI 生產者**。  
- `eval_exporter` 在 CI 中從未被呼叫（兩個 job 都只跑 `eval_ci_check`）。  
- `eval_stats.py`（以及它的報告 `eval_stats_report.md`）依賴 `eval_export/v1` 作為輸入，但目前只能讀取 fixture 資料（N=3）。  
- 所有可用的 eval_export/v1 JSONL 檔案都是手動或 fixture 產生的：  
  - `tests/fixtures/eval/eval_export_sample.jsonl`（N=3，固定的 fixture）  
  - `artifacts/eval/smoke_eval_results.jsonl`（N=3，等於 fixture）  

**對 eval_stats_report 的影響**：  
報告中目前的 thresholds 建議基於 N=3 的 fixture 資料（67% needs_review），完全不具代表性。  
報告自己寫了：「Real dev/staging nightly batches from Chat A are not yet attached」。  
報告期待的是「CI 自動生產的 `eval_results.YYYYMMDD.jsonl`」，但這條生產鏈不存在。

**缺失的數據鏈**：

```
CI shadow nightly (ibridge_exporter → shadow_ibridge_records.latest.jsonl)
    ↓
eval_ci_check ✅ (直接讀 shadow ibridge records)
eval_exporter ❌ (沒有被呼叫 → 沒有 eval_export/v1 JSONL)
    ↓
eval_stats ❌ (無 eval_export/v1 可消費)
    ↓
eval_stats_report ❌ (只能展示 N=3 fixture data)
```

---

## (2) 目標與邊界

### 目標（若未來要修復 CI-GAP-1）

至少 nightly 在內部 scope（shadow spool 或 fixture）下產生一份 `eval_export/v1` JSONL：  
- 讓 `eval_stats` 可在不手動跑 `eval_exporter` 的情況下消費真實資料。  
- 讓 `eval_stats_report.md` 可在有 N≥10 的 baseline 上更新 threshold 建議。  
- 不改變現有 `eval-gate` 和 `eval-shadow-nightly` 的 CI 判斷邏輯（gate verdict 不改）。  

### 不會做的事

- 不在每次 PR 都產生 `eval_export/v1`（成本/時間考量，nightly 級即可）。  
- 不擴散到 prod user data（僅限 staging-internal / shadow 資料）。  
- 不改現有 `eval_ci_check` 的 gate 語義或 exit code 行為。  
- 不新增獨立的 gate 或 CI 關卡 — 只補 data 生產鏈。  
- 不在本次只讀方案卡中給出具體 YAML patch。  

---

## (3) 只讀調查結果摘要

### 發現 1：CI 中的兩條 job 均未呼叫 `eval_exporter`

| CI job | 觸發 | 產出 ibridge 資料 | 呼叫 eval_exporter |
|--------|------|-------------------|-------------------|
| `eval-gate` | PR/push | 讀 fixture `ibridge_records.latest.jsonl`` | ❌ |
| `eval-shadow-nightly` | schedule / workflow_dispatch | `ibridge_exporter` → `shadow_ibridge_records.latest.jsonl` | ❌ |

`eval_ci_check` 直接在兩個 job 中被呼叫（讀取 raw ibridge records），但 `eval_exporter` **從未被放在任何 CI step 中**。  

### 發現 2：`eval_shadow_nightly` 已產出 ibridge JSONL，只差一步就是 eval_export/v1

- `eval-shadow-nightly` step `Export prod shadow spool to flat ibridge JSONL` 產生 `shadow_ibridge_records.latest.jsonl`。  
- 這個檔案已經是 `eval_exporter` 可接受的輸入格式（`iter_records` 可讀 ibridge JSONL）。  
- 直接追加一個 `python -m observability.eval_exporter <input> -o <output>` step 即可生產 `eval_export/v1`。  

### 發現 3：`eval_stats.py` 的 CLI 已支援 `--write-report`，但無 CI 呼叫

- `eval_stats` 的 CLI 參數包括：  
  - `--format text|json`（human 或 machine readable）  
  - `--group-by date|none|exported_date|file`  
  - `--min-samples`（預設 10）  
  - `--write-report path`（追加 markdown 段到報告檔案）  
- 但目前只能在本地手動呼叫（因為無 eval_export/v1 生產者）。

### 發現 4：`eval_stats_report.md` 依賴的 eval_export/v1 檔案分三級，全部不存在或僅 fixture

| 預期檔案 | 存在？ | 生產者 |
|---------|-------|--------|
| `tests/fixtures/eval/eval_export_sample.jsonl` | ✅ N=3 fixture | 手動 |
| `artifacts/eval/smoke_eval_results.jsonl` | ✅ N=3 (同 fixture) | 手動 |
| `artifacts/eval/eval_results.latest.jsonl`（或 `eval_results.YYYYMMDD.jsonl`） | ❌ | 無 CI 生產者 |

報告 §Limitations 明確寫了「Sample size: N=3 is sufficient for tooling verification only, not production threshold lock-in」。

### 發現 5：`ci_gate_wire.md`（W3-C）描述的是不同 JSONL 軌道

- `ci_gate_wire.md` 描述的是 `gov-metrics-0.1` schema 的 JSONL（由 `wf_gov_gate.ps1` / `wf_check_cross_ref.ps1` 產生），雖然已經在 gov-gate-metrics.yml 中實裝。  
- 這與 `eval_export/v1` schema（由 `eval_exporter` 產生）**是完全不同的軌道**。  
- `eval_export/v1` 的生產者（`eval_exporter`）未被任何 CI job 呼叫，即使它與gov-gate-metrics.yml 在同一倉庫。

### 發現 6：`eval_exporter` 可接受多種輸入，包括 ibridge JSONL、目錄、單 JSON

- `eval_exporter.export_eval_jsonl()` 支援：  
  - `.jsonl` 檔案（逐行 JSON）  
  - `.json` 檔案（單一 JSON 或陣列）  
  - 目錄（遞迴掃描所有 `.jsonl`/`.json`）  
- 這意味著無需新增任何 adapter — 直接把現有 `shadow_ibridge_records.latest.jsonl` 餵給它即可。

### 發現 7：`eval_ci_check` 內部已使用 `eval_exporter.build_export_line`，但只做 runtime 評估不寫入檔案

- `eval_ci_check.run_ci_check()` 對每個 record 呼叫 `build_export_line(record, gate=gate)` 做 gate 評估，但結果只存在記憶體中（用來算 ratio/tag_hits），**從不寫成 JSONL**。  
- 所以 CI 中其實已經有 gate 評估的邏輯在跑，只是沒有序列化成 `eval_export/v1` JSONL。

---

## (4) 建議的實作方向（高層，3 個選項）

### 選項 A — 在 `eval-shadow-nightly` job 中追加 eval_exporter step（推薦）

**描述**：在 `eval-gate-ci.yml` 的 `eval-shadow-nightly` job 中，在「Phase 1 shadow eval_ci_check」之後追加一個 step：  
```
python -m observability.eval_exporter ${SHADOW_EXPORT_OUT} -o artifacts/eval/eval_results.latest.jsonl
```
這一步純粹是資料生產，不改變 CI 的 pass/fail 判斷。  
可選擇同步產出 `eval_results.YYYYMMDD.jsonl`（日期版）供歷史分析。

**優點**：
- 改動最小（同一 job 內加一行 step）
- 輸入已經是 CI 存在的 `shadow_ibridge_records.latest.jsonl`
- 不影響 PR job（不增加 PR 成本）
- 讓 `eval_stats` 可直接消費 nightly 產出的 `eval_results.latest.jsonl`

**缺點**：
- 資料來源僅限 shadow spool（K-2 側車），可能不反映 full prod 分布
- 需要決定是否上傳 artifact，增加 artifact 數量（很小，N≤100 的 JSONL）

### 選項 B — 建立獨立的 nightly workflow（週期性 stats 更新）

**描述**：新增一個獨立的 workflow（例如 `eval-export-nightly.yml`），只在 schedule 上跑：  
1. `ibridge_exporter --source shadow`（復用 `eval-shadow-nightly` 的 export step）  
2. `eval_exporter` → `eval_export/v1` JSONL  
3. `eval_stats` → JSON 輸出  
4. 可選 `eval_stats --write-report` 更新 `eval_stats_report.md`

**優點**：
- 與現有 CI gate 判決解耦（不擔心改動影響 gate 行為）
- 可獨立控制排程（如每天 UTC 07:00，在 shadow nightly 之後）
- 專注於 data pipeline，不混入 gate 邏輯

**缺點**：
- 增加一個 workflow 檔案和維護成本
- 第一步的 `ibridge_exporter` 與 `eval-shadow-nightly` job 有重複
- 較選項 A 的改動量大

### 選項 C — 維持現狀，更新 eval_stats_report.md 說明

**描述**：不改 CI，但在 `eval_stats_report.md` 中補充：  
- 明確寫出「eval_export/v1 目前僅能手動產生，命令為：…」  
- 將 CI-GAP-1 記錄在已知限制中  
- 報告的 thresholds 標註為「僅基於 N=3 fixture，不具代表性」

**優點**：
- 零 CI 改動
- 不增加 CI 時間/成本
- 誠實反映現狀

**缺點**：
- 永遠無法自動獲得真實 baseline
- `eval_stats` 工具寫了但只能手動跑
- 隨著 Wave 4/5 rollout 擴張，缺失會更明顯

---

## (5) 風險與驗收要點

### 風險

| # | 風險 | 影響 | 緩解方式 |
|---|------|------|---------|
| R1 | 選項 A 追加 step 後 CI 時間增加（`eval_exporter` 處理 N≤100 條僅 ~1–2s，可忽略） | 可接受 | 若實作，量測 step 耗時 |
| R2 | 選項 A 的 artifact 可能包含 shadow spool 中的敏感資料 | 隱私/安全 | `eval_exporter` 只匯出摘要（`metrics` 無完整 record），但仍應確認無 PII |
| R3 | 選項 B 的新 workflow 可能與 `eval-shadow-nightly` 並行爭搶 spool 檔案 | 競爭條件 | 使用 concurrency group 或依賴 eval-shadow-nightly 的 artifact |
| R4 | 資料量不足（shadow 樣本太少）時，`eval_stats` 的 `suggest_ci_thresholds` 仍給低 confidence 建議 | 無效分析 | `min_samples` 預設 10，低於此會自動標 low confidence |
| R5 | 選項 C 維持現狀後，容易被新開發者誤以為「eval_stats_report 已有完整 baseline」 | 誤導 | 報告中已標 N=3 限制，但仍需確保閱讀者看到 |

### 驗收要點

| # | 驗收條件 | 如何驗證 |
|---|---------|---------|
| A1 | CI 中至少存在一條可重複執行的 `eval_export/v1` JSONL 生產路徑 | 在 CI run log 中看到 `exported X line(s) from Y record(s)` 輸出 |
| A2 | `eval_stats` 可在不手動跑 exporter 的情況下顯示至少一次 CI 產生的 baseline | `python -m observability.eval_stats artifacts/eval/eval_results.latest.jsonl` 回傳 N≥1 |
| A3 | `eval_stats_report.md` 可在 baseline N≥10 後用 `--write-report` 更新 | 手動或 CI 執行一次 `eval_stats --write-report` | 
| A4 | 現有 CI gate 的 pass/fail 行為不因新增 exporter step 而改變 | 對比新增前後的同一次 shadow nightly run 的 `eval_ci_check` 結果 |
| A5 | 不增加 PR job 的成本（生產鏈僅限於 nightly/schedule scope） | 確認 `eval-gate` job（PR trigger）無新增 step |

---

## (6) 未來實作票骨架

```markdown
票名：W4-C-FIX-* — CI eval_export/v1 JSONL 生產鏈補全
前置：W5-D-CI-GAP-1 方案卡（本文件）
Lane：runtime（CI 變更）

候選方向（三選一）：
  - 選項 A：在 eval-gate-ci.yml eval-shadow-nightly job 內追加 eval_exporter step
  - 選項 B：新增獨立的 eval-export-nightly.yml workflow
  - 選項 C：僅更新文檔，不改 CI

要改的檔案（依選項不同）：
  - .github/workflows/eval-gate-ci.yml（選項 A）
  - .github/workflows/eval-export-nightly.yml（選項 B，新增）
  - observability/eval_stats_report.md（所有選項皆可補充說明）

允許的操作：
  - 在 eval-shadow-nightly job 中追加 step（選項 A）
  - 新增獨立的 nightly workflow（選項 B）
  - 調整 artifact 路徑或命名（不改變 eval_ci_check 的 EVAL_CI_INPUT）

禁止事項：
  - 不改 eval-gate job（PR trigger）— 不增加 PR 成本
  - 不改 eval_ci_check 的 gate 邏輯或 exit code 行為
  - 不將 eval_export/v1 資料用於 prod 或 customer-facing 場景
  - 不改 ibridge_exporter shadow spool 來源或 bootstrap 邏輯

回報要求：
  - CI run log 片段：eval_exporter step 的 stdout（exported X lines）
  - eval_stats 的一次 baseline 結果（JSON 或 text 格式）
  - 對比新增前後的 eval_ci_check 結果（確認 gate 行為未變）
```

---

## 附錄 A — 關鍵檔案速查

| 檔案 | 角色 | 是否在 CI 中被呼叫 |
|------|------|-------------------|
| `.github/workflows/eval-gate-ci.yml` | CI workflow（PR + nightly） | — |
| `observability/eval_exporter.py` | 產生 eval_export/v1 JSONL | ❌ |
| `observability/eval_ci_check.py` | CI gate 判決（內部呼叫 build_export_line） | ✅（PR + nightly） |
| `observability/eval_stats.py` | 分布分析 + CI threshold 建議 | ❌ |
| `observability/eval_stats_report.md` | 報告文檔（目前基於 N=3 fixture） | ❌（無 CI 更新） |
| `observability/ibridge_exporter.py` | 將 shadow spool 轉為 flat ibridge JSONL | ✅（nightly 僅） |
| `artifacts/eval/smoke_eval_results.jsonl` | 現有 eval_export/v1 範例（N=3，fixture 級） | 手動 |
| `tests/fixtures/eval/eval_export_sample.jsonl` | 同上（手工 fixture） | 手動 |

## 附錄 B — 缺失資料鏈圖

```
現狀：
  ibridge_exporter → shadow_ibridge_records.latest.jsonl → eval_ci_check ✅
                                                          → eval_exporter ❌
                                                          → eval_stats ❌

選項 A（推薦）：
  ibridge_exporter → shadow_ibridge_records.latest.jsonl → eval_ci_check ✅
                                                          → eval_exporter → eval_results.latest.jsonl → eval_stats ✅

選項 B：
  [獨立 workflow]
  ibridge_exporter → shadow_ibridge_records.latest.jsonl → eval_exporter → eval_results.latest.jsonl → eval_stats → report update

選項 C：
  完全放任 — 所有依賴 eval_export/v1 的工具維持 fixture-only baseline
```
