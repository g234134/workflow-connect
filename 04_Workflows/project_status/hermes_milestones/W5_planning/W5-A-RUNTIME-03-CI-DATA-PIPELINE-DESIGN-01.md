# W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01 — prod shadow → CI spool 資料管線設計

> **票號**：W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01
> **日期**：2026-05-31
> **處境**：POLICY-MINING-02 已證實 MINING 缺資料，NIGHTLY-STATUS-CHECK-01 已證實 CI 沒有真實資料餵入機制。
> **定位**：設計方案（workspace-only），不寫 code，不修改 repo。
> **硬邊界**：不決定具體技術選型，可用 `SHADOW_DATA_BUCKET` 等抽象名稱占位；允許設計成「人工同步 + CI 消費」的最簡版本。

---

## 1) 問題描述

### 1.1 資料流現狀（Void Loop）

```
                         每年夜間重播
                              │
                              ▼
  fixture ──→ bootstrap ──→ spool ──→ ibridge_exporter ──→ dryrun ──→ enf_preview
  (static)    (if empty)    (4-6 rec)   (export to JSONL)    (always same)   (always same)
```

**為什麼 MINING 永遠只有 fixture：**

| 環節 | 問題 |
|------|------|
| GitHub Actions runner | **ephemeral** — 每次 CI run 啟動在全新 VM 上，無持久檔案系統。`k2_shadow_spool.jsonl` 從不存在。 |
| Bootstrap 邏輯 | `if [[ ! -s "${SHADOW_SPOOL}" ]]; then cp "${SHADOW_SPOOL_BOOTSTRAP}" "${SHADOW_SPOOL}"; fi` — 永遠觸發，永遠從 fixture 複製。 |
| Fixture 內容 | `tests/fixtures/eval/shadow_raw_records.jsonl` — 4 條靜態記錄（shadow-k2-flow-1, shadow-merge-2, shadow-greeting, shadow-retry），所有時間戳為 `2026-05-24`。 |
| 結果 | 即使 nightly 每日 UTC 06:00 順利執行，治理鏈看到的資料**從未變過**。MINING-02 觀察到 N=8 unique 與 MINING-01 完全相同，無須驚訝。 |

### 1.2 真正的資料源在哪？

`k2_shadow_spool.jsonl` 的原始設計意圖是「prod shadow K-2 管線的輸出匯總」。本地檔案 `artifacts/eval/k2_shadow_spool.jsonl` 含有 6 條記錄，部分記錄（如 prod-shadow-9469a97892-k2 附帶 `infra_risk` tag）**不在** bootstrap fixture 中。這 6 條記錄暗示了真實 prod shadow 的資料格式，但**這條管道從未被接上 CI**。

---

## 2) 資料來源盤點

### 2.1 現有資料來源

| 來源 | 位置（抽象） | 格式 | 記錄量（推估） | 更新頻率 | 狀態 |
|------|------------|------|--------------|---------|------|
| **K-2 prod shadow spool** | `artifacts/eval/k2_shadow_spool.jsonl`（本機） | K-2 spool schema（多行 JSON：`ok`+`record`、平鋪 `task_id` + `success` + `retry_count` 等） | 6 records（樣本） | 人工手動 | ✅ 存在但未自動化 |
| **Shadow ibridge export** | `artifacts/eval/shadow_ibridge_records.latest.jsonl`（本機） | ibridge 平鋪格式（`task_id`, `success`, `trace_completeness`, `retry_count` 等） | 5 records（樣本） | ibridge_exporter 產出 | ✅ 存在 |
| **Shadow eval results** | `artifacts/eval/shadow_eval_results.latest.jsonl`（本機） | eval_export/v1（`gate_result`, `tags`, `metrics` 含 `trace_completeness_score`） | 4 records（樣本） | eval_exporter 產出 | ✅ 存在 |
| **eval_export_sample.jsonl（fixture）** | `tests/fixtures/eval/eval_export_sample.jsonl` | eval_export/v1 | 3 records（t-healthy, t-infra, t-retry） | 靜態 | ✅ 已檢驗 |
| **smoke_eval_results.jsonl（fixture）** | `artifacts/eval/smoke_eval_results.jsonl` | eval_export/v1 | 3 records | 靜態 | ✅ 已檢驗 |

### 2.2 預期存在的 prod shadow 資料源（需實地確認）

| 來源 | 假設位置 | 說明 | 假設依賴 |
|------|---------|------|---------|
| **Prod shadow K-2 即時輸出** | 可透過 API / batch export 取得的每小時或每日產出 | K-2 Phase 1 的 shadow 管線（ask + k2）在 prod 環境中持續執行，產出可被外部讀取的 trace + verdict 記錄。 | K-2 prod shadow infra 已正常運作 |
| **Eval export 生產版** | 假設有對應 `shadow_eval_results.<date>.jsonl` | prod 版本的 `eval_exporter` 會將最新的 shadow trace 匯出為 `eval_export/v1` 格式。 | eval_exporter 已佈署在 prod 上游 |
| **Gate metrics 輸出** | `workflow_v2/observability/gov_gate_metrics/` | W4-C gov-gate-metrics.yml 的輸出。格式不同（metrics 為主的 JSONL），但可作為治理判定的輔助來源。 | gov-gate-metrics nightly 正確執行 |

---

## 3) 資料流設計 v0（最小可行流）

### 3.1 設計原則

| 原則 | 說明 |
|------|------|
| **P1 — 現有 schema 不動** | CI 端的 `ibridge_exporter`、`dryrun_ci_wrapper`、`enf_preview_wrapper` 均不改動。只改變 spool 的資料來源。 |
| **P2 — 人先通，機器再追** | v0 允許人工操作（手動下載、手動上傳）。待證實資料流有意義後再半自動化。 |
| **P3 — 不可覆蓋唯一 fixture** | fixture 留作 bootstrap fallback（當資料源出問題時仍可回到已知 fixture）。 |
| **P4 — 每次 CI 吃最新一批，不累積** | 不維護歷史累積（那是 MINING 的責任）。CI 只吃最新一期 batch。 |

### 3.2 資料流拓撲（v0）

```
           Prod 端                          共享儲存層 (SHADOW_DATA_BUCKET)                 CI 端 (GitHub Actions)
             │                                      │                                            │
   K-2 shadow 輸出（每小時 / 每日）                     │                                      eval-shadow-nightly job
             │                                      │                                            │
             ▼                                      │                                            ▼
  ┌─────────────────────┐                            │                              ┌───────────────────────────┐
  │ 批次匯出腳本 (v0:    │  手動執行                   │                              │ 步驟 1: Fetch latest      │
  │ 人工操作, v1: cron)  │ ──→ shadow_batch_YYYYMMDD  │                              │ shadow_batch_<datestamp>  │
  │                     │     .jsonl（到 SHADOW_DATA  │  ←──────────────────────     │ 到 SHADOW_SPOOL 位置       │
  │ 讀取 prod shadow     │     _BUCKET 或共享路徑）    │                              │                           │
  │ 管線的最近 N 筆      │                            │                              │ 步驟 2: 若 fetch 成功，   │
  │ 轉為 spool 相容格式  │                            │                              │ 跳過 bootstrap (fixture)  │
  └─────────────────────┘                            │                              │                           │
             │                                      │                              │ 步驟 3: 繼續既有流程      │
             │                                      │                              │ → ibridge_exporter       │
             ▼                                      │                              │ → eval_ci_check          │
  ┌─────────────────────┐                            │                              │ → dryrun_ci_wrapper      │
  │ 批次清單             │                            │                              │ → enf_preview_wrapper    │
  │ shadow_batch_20260530│                            │                              └───────────────────────────┘
  │ shadow_batch_20260531│                            │
  │ shadow_batch_...      │                            │
  └─────────────────────┘                            │
```

### 3.3 最小可行 v0 的實際操作步驟

#### Step A — 人工匯出（Prod 端，人在 prod 環境執行）

```bash
# 這是 v0 的假設指令，實際由人工或半自動腳本執行
python export_shadow_batch.py \
    --output /shared/storage/shadow_batch_20260531.jsonl \
    --max-records 500 \
    --lookback-hours 24
```

產出檔格式須相容於既有 `k2_shadow_spool.jsonl` schema（每一行是一個 record，含 `task_id`、`success`、`retry_count`、`error_type`、`trace_completeness.score`、`tags` 等欄位）。

#### Step B — 放置到共享儲存層

v0 共享儲存層選項（由團隊決定一個即可）：

| 選項 | 優點 | 缺點 |
|------|------|------|
| **方案 B1: 直接 push 到 repo**（`artifacts/eval/shadow_batch_*.jsonl`） | 不需要外部儲存，git pull 即取得 | 可能讓 repo 膨脹；JSONL 若大不適合 git |
| **方案 B2: 手動上傳到公開/私有 S3 bucket（SHADOW_DATA_BUCKET）** | 大檔案無壓力 | 需額外權限設定 |
| **方案 B3: 使用 GitHub Releases / Artifacts** | 不需外部 infra | 尚無處理 pipeline |
| **方案 B4: 存放在 WSL 本機 (e.g. /mnt/d/大唐三省六部/shadow_data/) 然後手動 scp/rsync** | 現有流量路徑 | 需要 CI 可存取 |

#### Step C — CI 消費（nightly 啟動時）

```
現有流程（無資料管線）：
  Checkout → Bootstrap spool from fixture → Export ibridge → Dryrun → Preview

v0 流程（有資料管線）：
  Checkout
    → [新增] Fetch latest shadow batch from SHADOW_DATA_BUCKET
    → [新增] If fetched: cp to SHADOW_SPOOL (override)
    → [保留] Bootstrap spool from fixture (only if fetch failed)
    → Export ibridge → Dryrun → Preview
```

關鍵變更：**bootstrap 從「預設行為」變成「fallback行為」**。若 fetch 成功（有真實資料），則不使用 fixture。

---

## 4) CI 消費模式

### 4.1 批次選擇策略

CI nightly 啟動時，需要決定吃哪一批資料。

| 策略 | 做法 | 優點 | 缺點 | v0 建議 |
|------|------|------|------|---------|
| **S1 — 吃最新一期** | 找 `shadow_batch_<最大日期>.jsonl` | 簡單，每次都是最新資料 | 無法跨期追蹤 trend | ✅ **v0 唯一策略** |
| **S2 — 吃最近 N 期合併** | 合併最近 7 天的 batch | 樣本數多 | 流程複雜、日期邊界模糊 | v2 考慮 |
| **S3 — 固定 slot 輪替** | 用日期格線（如每週一吃上週彙整） | 週期性固定 | 新增複雜度 | 不需要 |

v0 實作：CI 步驟中找 `SHADOW_DATA_BUCKET` 下檔名字典序最大（或 metadata 標記 `latest`）的 batch。

### 4.2 CI 側的 fetch 步驟設計（抽象示意）

```yaml
# 現有 bootstrap 步驟（修改前）：
- name: Bootstrap prod shadow spool when empty
  run: |
    if [[ ! -s "${SHADOW_SPOOL}" ]]; then
      cp "${SHADOW_SPOOL_BOOTSTRAP}" "${SHADOW_SPOOL}"
    fi

# v0 修改後：
- name: Fetch latest shadow batch and bootstrap
  run: |
    # Step 1: Try to fetch the latest real batch
    LATEST=$(fetch_latest_batch "${SHADOW_DATA_BUCKET}" 2>/dev/null || true)
    if [[ -n "${LATEST}" && -s "${LATEST}" ]]; then
      cp "${LATEST}" "${SHADOW_SPOOL}"
      echo "[SHADOW-PIPELINE] Loaded real batch: ${LATEST}"
    else
      # Step 2: Fallback to fixture if no real data available
      cp "${SHADOW_SPOOL_BOOTSTRAP}" "${SHADOW_SPOOL}"
      echo "[SHADOW-PIPELINE] WARN: No real batch, using fixture fallback"
    fi
```

### 4.3 `fetch_latest_batch` 的實作方式（v0 abstraction）

`fetch_latest_batch` 是抽象函數，v0 中可以是一個 bash 函數或 Python 腳本，根據共享儲存層方案選擇而異：

| 儲存層方案 | fetch_latest_batch 實作 |
|-----------|------------------------|
| **B1: Git repo** | `ls -t artifacts/eval/shadow_batch_*.jsonl \| head -1` |
| **B2: S3 bucket** | `aws s3 ls s3://my-bucket/shadow_batch_*.jsonl \| sort \| tail -1; aws s3 cp ...` |
| **B3: GitHub Artifacts** | 需先由另一個 daily job 上傳 artefact，再用 `gh run download` 下載 |
| **B4: 本機 WSL 路徑** | `scp user@host:/path/shadow_batch_*.jsonl /tmp/` + `ls -t /tmp/ \| head -1` |

### 4.4 當 batch 為空或失敗時的行為

| 情境 | CI 行為 | 治理鏈 |
|------|---------|--------|
| **Fetch 成功** → 批次檔有真實資料 | 使用 real batch | `[DRYRUN-LOG]` 與 `[GOV-ENF-PREVIEW]` 基於真實資料 |
| **Fetch 失敗**（無權限 / bucket 不存在 / 無批次檔） | Fallback 到 fixture | 與現在行為一致（fixture） |
| **Fetch 成功但檔案空** | Fallback 到 fixture | 同上 |
| **Fetch 成功但 JSONL 解析錯誤** | Fallback 到 fixture + 印 WARN | 同上 |

CI 步驟應在 fetch 失敗時印明確的 WARN 訊息（例如 `[SHADOW-PIPELINE] WARN: fetch failed — using fixture fallback`），讓 reviewer 可以從 nightly run log 看出資料來源。

### 4.5 治理鏈的假設

當 batch 資料流運作時，治理鏈（dryrun + enf_preview）不需要任何改動。它們原本就消費 `SHADOW_SPOOL` 指向的檔案。只要 spool 的內容變成真實資料：

```
真實 batch → SHADOW_SPOOL → ibridge_exporter → dryrun_ci_wrapper → enf_preview_wrapper
```

輸出的 `[DRYRUN-LOG]` 和 `[GOV-ENF-PREVIEW]` 行就會反映真實資料的分布。

---

## 5) 管線成熟度階梯

```
v0 ───────────────→ v1 ────────────────→ v2 ──────────────→ v3
人工匯出            半自動匯出             自動匯出             自動匯出 + 累積
手動上傳            排程 + 上傳            排程 + 上傳          排程 + 歷史累積
CI 被動消費          CI 被動消費            CI 主動拉取           CI 主動拉取 + archive
```

### v0 — 手工餵食（當務之急，1–2 天）

| 項目 | 說明 |
|------|------|
| **誰做** | 人工（在 prod 端執行一次匯出腳本） |
| **頻率** | 每次需要新 MINING 分析時手動匯出一次 |
| **共享** | 放到 `SHADOW_DATA_BUCKET`（任何一種方案） |
| **CI 消費** | nightly 自動抓最新的一批 |
| **驗收** | 至少 1 次 nightly 成功印出 `[DRYRUN-LOG] event=summary` 且記錄數 > 已有的 8 條 |

### v1 — 半自動（3–5 天）

| 項目 | 說明 |
|------|------|
| **誰做** | 生產環境排程（如 cron job 或 CI workflow 在 prod repo 上執行） |
| **頻率** | 每日 UTC 05:00（在 eval-shadow-nightly 排程的一小時前） |
| **共享** | 同上（同一 bucket） |
| **CI 消費** | 同上 |
| **驗收** | 連續 7 天 nightly run 都自動吃到不同日期的 batch |

### v2 — 自動化（1–2 週）

| 項目 | 說明 |
|------|------|
| **誰做** | 完全自動（production pipeline 輸出直接寫入共享儲存） |
| **頻率** | 每次 K-2 shadow 產出結束即觸發 |
| **驗收** | 無人工介入，連續 N 天穩定產出不同的治理鏈報表 |

---

## 6) 後續票建議

| 票號 | 名稱 | 時序 | 內容 |
|------|------|------|------|
| **W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-01** | v0 實作 — CI fetch + fallback | （下一張） | 在 `eval-shadow-nightly` job 中新增 fetch step，實現「先抓真實 batch，失敗才 fallback fixture」。含以下工件：fetch_latest_batch 腳本、CI YAML 的 step 變更、CI log 的 `[SHADOW-PIPELINE]` 輸出。不包含 prod 端匯出腳本（人工作業）。 |
| **W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-02** | v0 實作 — prod 端匯出腳本 | （IMPL-01 之後） | 撰寫「從 prod shadow K-2 管線匯出最新 batch」的腳本（可複用現有 `ibridge_exporter` 或 `eval_exporter`）。含：匯出腳本、README 說明手動執行步驟、schema 相容性驗證。 |
| **W5-B-RUNTIME-PIPELINE-AUTO-02**（或 W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-03） | v1 自動化 — 排程匯出 + upload | （IMPL-01/02 驗證後） | 在 prod 端佈署定時匯出 job（cron / workflow）。驗證連續 N 天自動產出不同資料。若可，移除 fetch 步驟的 fallback 印 WARN（改為印 INFO）。 |
| **W5-C-OBSERVABILITY-06**（或 RUNTIME-04 系列） | 治理鏈跨日趨勢觀測 | （管線穩定後） | 在 observability 中加入跨日 batch 的指標（每日記錄數、dryrun_rule 分布變異、score 分布 shift）。可復用 MINING 分析思路但做成 dashboard。 |

---

## 7) 風險與考量

### 7.1 風險矩陣

| 風險 | 機率 | 影響 | 緩解 |
|------|------|------|------|
| **prod shadow 管線未產出相容資料** | 高（未確認） | 高 — 資料流不通 | v0 階段先做一次人工驗證：從 prod 手動匯出一批，確認 schema 可餵給 ibridge_exporter |
| **batch 檔案過大（> 100MB）** | 中 | 中 — CI step 延遲或 timeout | 在 fetch 腳本中加入 `--max-records` 限制；或只取最近 24h 資料 |
| **CI 吃到過期的 batch（如上週的）** | 低（S1 策略下） | 低 — 仍比 fixture 好 | v0 可接受；v1 加入 date 一致性檢查 |
| **bucket 權限在 CI 中不可用** | 中 | 高 — fetch 總是 fallback | 先使用 B1（git push）或 B4（WSL 路徑）繞過權限問題 |

### 7.2 不在此設計中處理的事項

| 事項 | 原因 |
|------|------|
| **批次累積歷史** | MINING 腳本可以自行從多個 batch 累積，CI 不需要管歷史。 |
| **gate verdict 寫入 prod** | 本管線只是資料餵入，不動 gate verdict。 |
| **多 region / multi-colo** | 超出 v0 範圍。v0 先單一 prod 來源。 |
| **資料 schema 版本控制** | 假設現有 `shadow_ibridge_records` 與 `k2_shadow_spool` schema 為穩定格式。若有 schema 變更，由 IMPL-02 票處理相容性。 |

### 7.3 與 W5-A-RUNTIME-PLAYBOOK 的對應

本設計完成後，建議在 PLAYBOOK 中新增第 5 節「CI Data Pipeline Pattern」，定義：
- 資料管線的抽象結構（source → store → fetch → fallback）。
- 每條管線的預設 timeout 與 fallback 行為。
- 與既有 AC-DRY 的對應（AC-DRY 仍要求 fixture fallback 可獨立測試）。

---

## 附錄 A — 資料格式對照

### A.1 現行 k2_shadow_spool 格式（CI 的 spool 消費端期望的 schema）

來自 `artifacts/eval/k2_shadow_spool.jsonl` 的觀察：

```json
// 格式 1: 帶 ok/record 包裹（純 shadow trace）
{"ok": true, "record": {"task_id": "shadow-k2-flow-1", "trace_id": "tr-sk-1", ...}}

// 格式 2: 平鋪式（eval export 後）
{"task_id": "prod-shadow-9469a97892-k2", "trace_id": "...", "success": true, ...}

// 格式 3: case_name 為索引（K-2 summary 節點）
{"case_name": "shadow-retry", "k2_summary": {"pipeline": "k2", ...}}
```

### A.2 ibridge_exporter 消費的格式（SHADOW_EXPORT_OUT 的格式）

來自 `artifacts/eval/shadow_ibridge_records.latest.jsonl`：

```json
{"task_id": "prod-shadow-9469a97892-k2", "success": true, "retry_count": 0,
 "trace_completeness": {"score": 1.0}, ...}
```

### A.3 批次檔應該用哪種格式？

| 格式 | 建議 | 原因 |
|------|------|------|
| **k2_shadow_spool 原始格式**（含 ok/record 包裹） | ✅ **v0 推薦** | CI 現有 `ibridge_exporter` 可以直接吃 spool 原始格式。產出匯出時直接複製 prod 端 spool 即可，不需要額外轉換。 |
| **ibridge 平鋪格式** | 也可用 | 跳過 ibridge_exporter 步驟，直接餵給 dryrun。但會改變既有的步驟鏈，建議 v2 再考慮。 |

---

## 附錄 B — 與 W5-OVERVIEW 的對齊

| W5_OVERVIEW 現行結論 | 本設計的回應 |
|---------------------|-------------|
| 「資料累積機制不存在」 | ✅ v0 設計建立了最小資料流 |
| 「所有資料來自 fixture」 | ✅ fetch-fallback 機制讓 fixture 成為 fallback |
| 「MINING-03 無法取得真實樣本」 | ✅ 管線通後即可取得真實樣本 |
| 「需要 infra 改善」 | ✅ v0 改動極小 — 只加一個 CI fetch step + bash 腳本 |

---

## 附錄 D — IMPL-01 實作決策摘要

### D.1 SHADOW_BATCH_DIR 實體

`artifacts/eval/` — 與既有 spool 和 ibridge export 同目錄，且已被 `.gitignore` 涵蓋（`artifacts/eval/*.jsonl`），批次檔不會被 git 追蹤。

### D.2 Fetch 腳本

`scripts/fetch_latest_shadow_batch.sh` — 搜尋 `artifacts/eval/shadow_batch_*.jsonl`（檔名字典序 = 日期最大），複製到 `SHADOW_SPOOL`。印出 `[SHADOW-PIPELINE] mode=shadow batch=<stamp>` 或 `[SHADOW-PIPELINE] mode=fixture reason=...`。

### D.3 CI Workflow 變更

在 `eval-gate-ci.yml` 的 `eval-shadow-nightly` job 中：
1. 新增 `SHADOW_BATCH_DIR: artifacts/eval` env var
2. 將原本的「Bootstrap prod shadow spool when empty」步驟拆分為：
   - 「Fetch latest shadow batch (real data before fixture)」— 執行 fetch 腳本
   - 「Bootstrap shadow spool from fixture (fallback)」— 僅在 spool 仍為空時複製 fixture

Fallback 使用原有的 `! -s "${SHADOW_SPOOL}"` 判斷，先執行 fetch（可填滿 spool），再跑 fallback（判斷空再複製），天然形成「真實批次優先 → fixture 備援」的優先序。

### D.4 實測驗證結果

| 測試 | 輸入 | fetch log | 後續 pipeline | 通過 |
|------|------|-----------|---------------|------|
| **AC1 — Shadow mode** | `shadow_batch_20260530.jsonl`（6 records, 2324 bytes） | `[SHADOW-PIPELINE] mode=shadow batch=20260530` | ibridge 6 records → dryrun 6/6 matches → enf_preview: would_block=0, would_warn=1 | ✅ |
| **AC2 — Fixture mode** | 無批次檔 | `[SHADOW-PIPELINE] mode=fixture reason=no_batch_found` | fallback bootstrap (911 bytes) → ibridge 4 records → dryrun 4/4 → enf_preview: would_block=0, would_warn=1 | ✅ |
| **AC3 — Pipeline 完整性** | 兩種模式皆驗證 | 兩種 log prefix 均正確 | `[DRYRUN-LOG]` / `[GOV-ENF-PREVIEW]` step 皆正常 exit 0 | ✅ |

### D.5 實測意外發現

使用 shadow batch（6 records）時 `would_block=0`，即使批次中有 2 條附帶 `infra_risk` tag 的 prod-shadow 記錄。原因是這些記錄在 k2 層的 `success=true`、無 `error_type`，被 dryrun 規則分類為 `gate_ok_score_high`（allow）而非 `gate_fail_deny`（deny）。這驗證了：

- ENF-RULE-1 的條件（`gate_fail_deny + error_type + risk tag + score≥0.7`）比預期嚴格
- infra_risk tag 單獨存在不足以觸發 deny — 需要同時有 `error_type`
- 這是真實 pipeline 帶來的第一個新 insight：**ENF-RULE-1 可能遺漏了帶 infra_risk 但非 timeout 失敗的記錄**

### D.6 IMPL-01 產出檔案

| 路徑 | 說明 |
|------|------|
| `.github/workflows/eval-gate-ci.yml` | 新增 `SHADOW_BATCH_DIR` env var；替換 bootstrap step 為 fetch + fallback |
| `scripts/fetch_latest_shadow_batch.sh` | 新增 fetch 腳本 |
| `artifacts/eval/shadow_batch_20260530.jsonl` | 範例批次檔（6 records，真實資料 mock） |

## 附錄 E — 版本歷史（更新）

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.1 | 2026-05-31 | W5-A-CI-DATA-PIPELINE | 首版設計 |
| v0.2 | 2026-05-31 | W5-A-CI-DATA-PIPELINE-IMPL-01 | IMPL-01 實作後補：增加附錄 D（實作決策、實測結果、產出檔案清單） |
