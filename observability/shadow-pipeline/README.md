# Shadow CI data pipeline (v0)

> **票號**：`W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-01`  
> **Workflow**：`.github/workflows/eval-gate-ci.yml` · job `eval-shadow-nightly`

Ephemeral GitHub Actions runner 每次啟動時 spool 為空。v0 管線在 fixture bootstrap **之前**嘗試載入 repo 內最新 prod shadow batch；僅在無可用 batch 時才退回 fixture。

## v0 資料來源（SHADOW_DATA_BUCKET）

| 項 | 值 |
|----|-----|
| 抽象名 | `SHADOW_DATA_BUCKET` |
| v0 路徑 | `artifacts/eval/shadow_batch_*.jsonl` |
| 命名 | `shadow_batch_YYYYMMDD.jsonl`（字典序最大 = 最新） |
| Spool | `artifacts/eval/k2_shadow_spool.jsonl` |
| Fixture fallback | `tests/fixtures/eval/shadow_raw_records.jsonl`（4 行） |

## 準備 batch（人工，v0）

1. 從 prod shadow 匯出 spool 相容 JSONL（schema 見 `observability/eval_export.md`）。
2. 命名為 `shadow_batch_<date>.jsonl` 並放入 `artifacts/eval/`。
3. Commit 或 rsync 到 CI checkout 可見的位置。

樣本：`artifacts/eval/shadow_batch_20260530.jsonl`（含 `prod-shadow-*` 記錄，行數 > fixture）。

## Fetch 腳本

```bash
export SHADOW_BATCH_DIR=artifacts/eval
export SHADOW_SPOOL=artifacts/eval/k2_shadow_spool.jsonl
bash scripts/fetch_latest_shadow_batch.sh
```

| Log | 語意 |
|-----|------|
| `[SHADOW-PIPELINE] mode=shadow batch=<stamp>` | 已覆寫 spool，跳過 fixture bootstrap |
| `[SHADOW-PIPELINE] mode=fixture` | 無 batch；由 nightly bootstrap step 複製 fixture |

## 本地模擬 nightly spool 步驟

```bash
# 有 batch
bash scripts/fetch_latest_shadow_batch.sh
test -s artifacts/eval/k2_shadow_spool.jsonl && wc -l artifacts/eval/k2_shadow_spool.jsonl

# 無 batch（空目錄）
SHADOW_BATCH_DIR=/tmp/empty_batch bash scripts/fetch_latest_shadow_batch.sh
# 再跑 bootstrap 等價邏輯：
cp tests/fixtures/eval/shadow_raw_records.jsonl artifacts/eval/k2_shadow_spool.jsonl
```

## 不變的下游

fetch / bootstrap 之後的 export、`eval_ci_check`、`[DRYRUN-LOG]`、`[GOV-ENF-PREVIEW]` **邏輯與 exit code 不變**；僅 spool 內容來源可能從 fixture 換成真實 batch。
