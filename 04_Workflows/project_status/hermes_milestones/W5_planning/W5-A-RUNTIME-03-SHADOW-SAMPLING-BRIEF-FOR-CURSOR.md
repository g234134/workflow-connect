# W5-A-RUNTIME-03-SHADOW-SAMPLING-BRIEF-FOR-CURSOR — Nightly Shadow Sampling 實作 BRIEF

> 票號：W5-A-RUNTIME-03-SHADOW-SAMPLING-DESIGN-01 → 產出給 Cursor 實作
> 日期：2026-05-31

---

## 任務背景

### 為什麼非做不可？

Nightly CI（`eval-shadow-nightly`）目前完全看不到帶 `infra_risk` tag 的記錄：

1. **`.gitignore` 第 56 行** — `artifacts/eval/*.jsonl` 不被 git 追蹤 → CI checkout 後無 `shadow_batch_*.jsonl` → fetch 腳本永遠 `mode=fixture`
2. **Fixtue 只有 4 條記錄** — 0 條含 `infra_risk`，C3-05（`should_emit_c3_05_warning`）永遠不被觸發
3. **即使在本地完整 batch（6 條，含 2 條 `infra_risk`）**，現有 fetch 腳本也只是全量複製，沒有保留特定風險樣本的邏輯
4. **`eval_ci_check --fail-on-tags=infra_risk`** — 若 infra_risk 記錄真的進入 CI，eval_ci_check 會 `exit 1`，中斷 pipeline；dryrun / ENF preview 永不執行

**結論**：C3-05 的 `[ENF-WARN]` 在 nightly 中從未實際印出過。C3-05-OBS-REPORT-01 已證實「規則本身正確但缺少資料」。

### 本 BRIEF 的目標

在 `fetch_latest_shadow_batch.sh` 與 spool 之間加入一層 sampling，讓 spool 同時包含：
- 一般樣本（多數）
- 固定比例的風險樣本（`infra_risk`、`high_retry` 等）

不改變 downstream（ibridge_exporter → dryrun → enf_preview）的資料格式或行為。

---

## 允許修改的檔案與範圍

### 修改現有檔案

| 檔案 | 修改內容 | 備註 |
|------|---------|------|
| `scripts/fetch_latest_shadow_batch.sh` | 在 `cp "${SRC}" "${DST}"` 步驟後呼叫 `build_shadow_spool.sh` 做 sampling | 保留現有 mode=shadow/fixture 辨識邏輯 |
| `.github/workflows/eval-gate-ci.yml` | 新增 3 個 env vars（見下方） | 僅加變數，不改 step 順序或 continue-on-error |

### 新增檔案

| 檔案 | 說明 |
|------|------|
| `scripts/build_shadow_spool.sh` | 核心 sampling 腳本：讀取 batch、分類、去重、取樣、合併、寫入 spool |
| `artifacts/eval/shadow_batch_latest_risk.jsonl`（範例） | 測試用含風險記錄的 batch（若需驗證） |

### 新增 CI env vars（在 eval-shadow-nightly job 的 env 區塊）

```yaml
SHADOW_BASELINE_LIMIT: "20"       # 一般樣本上限
SHADOW_RISK_RETAIN_LIMIT: "3"     # 每種風險 tag 最多保留條數
SHADOW_RISK_TAGS: "infra_risk,high_retry"  # 逗號分隔
```

---

## 禁止修改的範圍

```
❌ tools/enf_preview_wrapper.py        — C3-05 規則不動
❌ tools/dryrun/core.py                 — dryrun 近似規則不動
❌ tools/dryrun/output.py               — dryrun 輸出格式不動
❌ observability/eval_gate.py           — gate tag 規則不動
❌ observability/eval_ci_check.py       — CI check 邏輯不動（含 fail-on-tags）
❌ observability/ibridge_exporter.py    — export 邏輯不動
❌ observability/eval_exporter.py       — eval export 格式不動
❌ observability/eval_stats.py          — 統計腳本不動
❌ tests/**                              — 測試不動（CI pipeline 不回歸即可）
```

**特別注意**：`eval_ci_check` 的 `--fail-on-tags=infra_risk` 仍然保留。本 BRIEF 只改變 spool 的資料組成，不改變 CI gate 的 fail 行為。若未來需要讓 infra_risk 記錄通過 gate 但繼續 dryrun/ENF preview，那是另一張票的 scope。

---

## 推薦實作步驟

### Step 1 — 撰寫 `scripts/build_shadow_spool.sh`

**輸入**：`shadow_batch_*.jsonl`（完整 batch）
**輸出**：`SHADOW_SPOOL`（sampling 後的 JSONL）
**env vars**：
- `SHADOW_BASELINE_LIMIT`（預設 20）
- `SHADOW_RISK_RETAIN_LIMIT`（預設 3）
- `SHADOW_RISK_TAGS`（預設 `infra_risk,high_retry`）

**邏輯（bash + jq 實作，無 Python 依賴）：**

```bash
# 1. 讀取 batch 所有記錄
# 2. 分類: infra_risk / high_retry / baseline
#    - 若記錄的 tags 中有任一 risk tag → risk_records[tag]
#    - 否則 → baseline
# 3. 去重: 同一 task_id 只保留最後一筆（最新）
# 4. 取樣 baseline: 取最後 BASELINE_LIMIT 條（tail）
# 5. 取樣 risk: 每種 tag 最多 RISK_RETAIN_LIMIT 條
# 6. 合併: baseline + risk（保持原始順序）
# 7. 寫入 SHADOW_SPOOL
# 8. 印 [SHADOW-PIPELINE] 結構化行
```

**建議使用 `jq`（已預裝在 ubuntu-latest runner 上）而非 Python**，減少依賴和執行時間。

### Step 2 — 修改 `scripts/fetch_latest_shadow_batch.sh`

在現有的 `cp "${SRC}" "${DST}"` 之後追加：

```bash
# After cp succeeds, apply sampling
if [[ -s "${DST}" ]]; then
    bash scripts/build_shadow_spool.sh
fi
```

確保：
- 保留既有的 `mode=shadow` / `mode=fixture` 日誌
- Sampling 步驟失敗時不應阻止 CI exit 0（可 `|| true`）
- sampling 額外的日誌 prefix 使用 `[SHADOW-PIPELINE]`

### Step 3 — 修改 `.github/workflows/eval-gate-ci.yml`

在 `eval-shadow-nightly` job 的 env 區塊新增：

```yaml
SHADOW_BASELINE_LIMIT: "20"
SHADOW_RISK_RETAIN_LIMIT: "3"
SHADOW_RISK_TAGS: "infra_risk,high_retry"
```

### Step 4 — 建立本地驗證 batch

在 `artifacts/eval/` 中準備一個含 `infra_risk` 記錄的 `shadow_batch_*.jsonl`（可複用現有 `shadow_batch_20260530.jsonl`，其已有 2 條 infra_risk 記錄）。

### Step 5 — 本地跑一次完整模擬

```bash
bash scripts/fetch_latest_shadow_batch.sh
python -m observability.ibridge_exporter \
  --source shadow --profile shadow --force \
  artifacts/eval/k2_shadow_spool.jsonl \
  -o /tmp/verify_shadow_ibridge.jsonl --no-latest
python -m tools.dryrun_ci_wrapper \
  --input /tmp/verify_shadow_ibridge.jsonl \
  --output-dir /tmp/verify_dryrun
python -m tools.enf_preview_wrapper \
  --input-dir /tmp/verify_dryrun \
  --min-score 0.7
```

預期結果：`[GOV-ENF-PREVIEW] event=detail rule=C3-05-L1-INFRA-RISK-SUCCESS would_warn=2`。

---

## 驗收條件

共 8 條，由簡到難：

| # | 條件 | 驗證方式 |
|---|------|---------|
| 1 | Nightly spool 不再系統性漏掉 `infra_risk` / `high_retry` 樣本 | 執行 `build_shadow_spool.sh` 後檢查 spool 內容含至少 1 條 infra_risk 記錄 |
| 2 | 一般樣本仍為多數（記錄總數 > 風險保留數 × 2） | `jq '.tags[]' spool.jsonl \| sort \| uniq -c` 統計 tag 分布 |
| 3 | 沒有改變 downstream artefact schema | dryrun 及 enf_preview 仍正常執行（不因 sampling 報错） |
| 4 | `eval-shadow-nightly` 仍可正常跑完 | CI workflow 模擬執行，所有 step exit 0 |
| 5 | Risk-heavy 樣本若存在，至少有最小數量被保留 | 準備含 5 條 infra_risk 的 batch，驗證 spool 含 3 條（上限） |
| 6 | 同一 task_id 去重 | 準備重複 task_id 的 batch，spool 只保留最新一筆 |
| 7 | Batch 不存在或為空時 fallback 到 fixture | 腳本驗證：無 batch → spool 內容 = fixture |
| 8 | 新增腳本印出 `[SHADOW-PIPELINE]` 結構化行 | 驗證 log 包含 `sampling: baseline=N risk_retained=M` |

---

## 已知陷阱

| 陷阱 | 說明 | 緩解 |
|------|------|------|
| **jq 版本差異** | ubuntu-latest 的 jq 版本可能不支援某些語法 | 使用基礎 jq（`select`, `group_by`, `unique_by`, `.[]`, `length`） |
| **JSONL 空行/空格** | batch 檔案可能有 trailing newline 或空白行 | 讀取時跳過空白行 |
| **task_id 不存在** | 某些記錄可能沒有 `task_id` | 此類記錄不納入去重，直接進入 baseline（或跳過） |
| **tags 欄位可能是 null** | 不是所有記錄都有 `tags` 陣列 | 腳本中處理 null → `[]` |
| **fetch 腳本與 sampling 分離** | 若 fetch 失敗（mode=fixture），sampling 不應執行 | `build_shadow_spool.sh` 不做 fallback，只負責轉換已存在的 batch |
| **eval_ci_check 仍會 fail** | 風險保留不改變 `--fail-on-tags infra_risk` 行為。若 infra_risk 記錄使 CI fail，那是預期行爲（與現在一致） | 本 BRIEF 不改變 gate 行為 |

---

## 成功畫面

完成後，在 nightly CI log 中應看到：

```
[SHADOW-PIPELINE] mode=shadow batch=20260530
[SHADOW-PIPELINE] sampling: baseline=4 risk_retained=2 tags={infra_risk:2,high_retry:1}
...
[GOV-ENF-PREVIEW] event=detail rule=C3-05-L1-INFRA-RISK-SUCCESS would_warn=2
[ENF-WARN] rule=C3-05-L1-INFRA-RISK-SUCCESS task_id=prod-shadow-9469a97892-k2 ...
[ENF-WARN] rule=C3-05-L1-INFRA-RISK-SUCCESS task_id=prod-shadow-1bab7f91d5-k2 ...
```

即：**C3-05 的 `[ENF-WARN]` 首次在 nightly pipeline 中實際觸發**。
