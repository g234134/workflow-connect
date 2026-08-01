# W5-A-RUNTIME-03-CI-DATA-PIPELINE Brief — 給 Cursor 的 v0 實作任務卡（prod shadow → CI spool）

> **源頭**：`W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01.md`（問題與 v0 資料流設計）  
> **實作票**：`W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-01`（CI fetch + fallback；不含 prod 端匯出腳本）  
> **風險**：低–中 — 僅改 `eval-shadow-nightly` job 的 spool 來源邏輯；下游 export / eval_ci_check / dryrun / enf_preview **不動**。  
> **目標**：在 nightly CI 中**優先**消費真實 shadow batch，僅在無可用批次時才退回 fixture bootstrap。  
> **硬邊界**：不修改 ENF-* 規則、不修改 dry-run / preview CLI 與 exit code、不影響其他 workflow job。

---

## 任務說明（可直接貼給 Cursor）

你是 **implementation-worker**，任務是完成 **CI data pipeline v0**：讓 `eval-shadow-nightly` 不再每次從 fixture 重播，而是優先載入 `SHADOW_DATA_BUCKET` 中的最新 `shadow_batch_*.jsonl`。

**現況（Void Loop）**

| 環節 | 現況 |
|------|------|
| GitHub Actions runner | **ephemeral** — 每次 run 在全新 VM，`k2_shadow_spool.jsonl` 從不存在 |
| Bootstrap | `if [[ ! -s "${SHADOW_SPOOL}" ]]; then cp fixture; fi` — **永遠觸發** |
| Fixture | `tests/fixtures/eval/shadow_raw_records.jsonl` — 4 條靜態記錄（時間戳 `2026-05-24`） |
| 結果 | nightly 治理鏈（export → eval_ci_check → dryrun → enf_preview）**永遠看到相同資料** |

**v0 目標**

1. 在 fixture bootstrap **之前**插入 fetch step。
2. 若成功取得非空 `shadow_batch_*.jsonl` → 覆寫 spool → **跳過** fixture bootstrap。
3. 若無可用 batch → 維持現有 fixture bootstrap（行為與改動前一致）。
4. 以 `[SHADOW-PIPELINE]` log 明確標示 `mode=shadow` 或 `mode=fixture`。

---

## 1. 背景與目標

### 1.1 資料流（改動後）

```
Checkout
  → [新增] Fetch latest shadow_batch_*.jsonl（SHADOW_DATA_BUCKET）
  → [保留] Bootstrap from fixture（僅當 spool 仍為空）
  → Export ibridge（既有，不動）
  → eval_ci_check（既有，不動）
  → dryrun_ci_wrapper（既有，不動）
  → enf_preview_wrapper（既有，不動）
```

### 1.2 v0 的 SHADOW_DATA_BUCKET 定義（B1 — repo 內批次檔）

v0 **不引入** S3 / 外部 bucket 權限。`SHADOW_DATA_BUCKET` 在 v0 具體映射為：

| 抽象名 | v0 實際路徑 | 說明 |
|--------|------------|------|
| `SHADOW_DATA_BUCKET` | `artifacts/eval/` | 目錄內含 `shadow_batch_*.jsonl` |
| 批次命名 | `shadow_batch_YYYYMMDD.jsonl` | 字典序最大 = 最新（例：`shadow_batch_20260530.jsonl`） |
| 目標 spool | `artifacts/eval/k2_shadow_spool.jsonl` | 與現有 nightly env 一致 |

**樣本檔（已存在，供驗收）**：`artifacts/eval/shadow_batch_20260530.jsonl`（7 行，含 prod-shadow 記錄與 `infra_risk` tag，**不同於** 4 行 fixture）。

**人工餵食流程（v0，不在本票範圍）**：運維從 prod 匯出 spool 相容 JSONL → 命名 `shadow_batch_<date>.jsonl` → commit 或 rsync 到 `artifacts/eval/`。本票只實作 **CI 消費端**。

### 1.3 既有 repo 錨點（實作前先讀）

| 項目 | 路徑 |
|------|------|
| Nightly workflow | `.github/workflows/eval-gate-ci.yml` → job `eval-shadow-nightly` |
| Spool env | `SHADOW_SPOOL=artifacts/eval/k2_shadow_spool.jsonl` |
| Fixture bootstrap env | `SHADOW_SPOOL_BOOTSTRAP=tests/fixtures/eval/shadow_raw_records.jsonl` |
| Bootstrap step 名稱 | `Bootstrap prod shadow spool when empty (CI wiring only)` |
| Fetch 腳本（可能已存在草稿） | `scripts/fetch_latest_shadow_batch.sh` |
| Export 下游 | `python -m observability.ibridge_exporter --source shadow …` |

---

## 2. 允許 / 禁止操作

### 2.1 允許

- 新增或修改 `scripts/fetch_latest_shadow_batch.sh`（或等價 bash / Python 腳本）。
- 在 `.github/workflows/eval-gate-ci.yml` 的 **`eval-shadow-nightly` job 內**新增 / 調整 steps（fetch 在 bootstrap 之前）。
- 在 `eval-shadow-nightly` job 的 `env:` 區塊新增 `SHADOW_BATCH_DIR`（預設 `artifacts/eval`）。
- 新增或更新**簡短**文檔（建議 `observability/dryrun/README.md` 追加一節，或新增 `observability/shadow-pipeline/README.md`），說明 v0 fetch-fallback 與 log 格式。
- 本地驗證：用 bash 模擬 fetch + bootstrap 條件分支。

### 2.2 禁止

- **嚴禁**修改任何 **ENF-RULE-*** 定義或 `tools/enf_preview_wrapper.py` 內規則邏輯。
- **嚴禁**修改 `tools/dryrun/**`、`tools/dryrun_ci_wrapper.py` 的 CLI 介面、報表格式、或 **exit code 行為**。
- **嚴禁**修改 `tools/enf_preview_wrapper.py` 的 **exit code 行為**（Phase A 必須永遠 exit 0）。
- **嚴禁**修改 `eval-shadow-nightly` 中 **Export / eval_ci_check / Dry-run / Enforcement Preview** 四個 step 的 CLI 參數、exit code 語意、或 `continue-on-error` 設定。
- **嚴禁**修改 **`eval-gate` job**（PR / push）或其他 workflow 檔（如 `gov-gate-metrics.yml`）。
- **嚴禁**修改既有 fixture 內容（`tests/fixtures/eval/shadow_raw_records.jsonl`）或 unittest 斷言（除非尚書省另開票）。
- **嚴禁**在本票引入 S3 / AWS credentials / 外部 secret（留給 v1）。
- **嚴禁**修改 `.cursor/rules/**` 或 governance rule 檔。

---

## 3. 建議實作步驟（Checklist）

### Step 0 — 路徑盤點（必做）

- [ ] 讀 `.github/workflows/eval-gate-ci.yml`，定位 job `eval-shadow-nightly` 與 bootstrap step（約 L239–253）。
- [ ] 確認 spool / fixture env 變數名稱。
- [ ] 檢查 `scripts/fetch_latest_shadow_batch.sh` 是否已存在；若存在，對照下方規格決定「沿用 + 接線」或「修正後接線」。

### Step 1 — 實作 `fetch_latest_shadow_batch.sh`

**位置**：`scripts/fetch_latest_shadow_batch.sh`（可執行 `chmod +x`）。

**環境變數**：

| 變數 | 預設 | 說明 |
|------|------|------|
| `SHADOW_BATCH_DIR` | `artifacts/eval` | v0 的 `SHADOW_DATA_BUCKET` 目錄 |
| `SHADOW_SPOOL` | `artifacts/eval/k2_shadow_spool.jsonl` | 覆寫目標 |

**行為**：

1. 掃描 `${SHADOW_BATCH_DIR}/shadow_batch_*.jsonl`。
2. 取檔名字典序最大者為 latest（`sort \| tail -1`）。
3. **若找到且非空**：
   - `cp` 到 `${SHADOW_SPOOL}`（`mkdir -p` 父目錄）。
   - 印：`[SHADOW-PIPELINE] mode=shadow batch=<stamp> src=... dst=...`
   - **exit 0**
4. **若目錄不存在 / 無匹配檔 / 檔案為空**：
   - **不觸碰** `${SHADOW_SPOOL}`（留空給 fixture bootstrap）。
   - 印：`[SHADOW-PIPELINE] mode=fixture reason=<no_batch_found|batch_dir_not_found|batch_file_empty>`
   - **exit 0**（fetch 失敗不是 CI 失敗；由 fallback 處理）

**注意**：腳本本身 **不可** 因「無 batch」而 exit 非 0；僅 genuine error（如 `set -e` 下無法 `mkdir`）才可非 0。

### Step 2 — 修改 `eval-shadow-nightly` workflow

在 **Checkout + Set up Python 之後**、**Bootstrap step 之前**插入：

```yaml
      - name: Fetch latest prod shadow batch (v0 data pipeline)
        shell: bash
        env:
          SHADOW_BATCH_DIR: artifacts/eval
          SHADOW_SPOOL: artifacts/eval/k2_shadow_spool.jsonl
        run: |
          set -euo pipefail
          bash scripts/fetch_latest_shadow_batch.sh
```

**修改既有 Bootstrap step** — 邏輯保持不變，僅確保註解清楚：

```yaml
      - name: Bootstrap prod shadow spool when empty (CI wiring only)
        shell: bash
        run: |
          set -euo pipefail
          mkdir -p "$(dirname "${SHADOW_SPOOL}")"
          if [[ ! -s "${SHADOW_SPOOL}" ]]; then
            cp "${SHADOW_SPOOL_BOOTSTRAP}" "${SHADOW_SPOOL}"
            echo "[SHADOW-PIPELINE] mode=fixture reason=bootstrap_fallback src=${SHADOW_SPOOL_BOOTSTRAP}"
          fi
```

**關鍵語意**：

- Fetch 成功 → spool 非空 → bootstrap 的 `if [[ ! -s ... ]]` **不執行** → 自動跳過 fixture。
- Fetch 失敗 → spool 空 → bootstrap **照常** cp fixture。
- Bootstrap 額外印一行 `mode=fixture reason=bootstrap_fallback` 以便與 fetch 階段的 `reason=no_batch_found` 區分（可選但建議）。

**不要**用 workflow `if:` 條件去跳過 bootstrap job — 用 spool 是否為空作為唯一判斷，與現有邏輯相容。

### Step 3 — `[SHADOW-PIPELINE]` log 規格

| 情境 | 預期 log 行 |
|------|------------|
| 有 batch | `[SHADOW-PIPELINE] mode=shadow batch=20260530 src=... dst=...` |
| 無 batch（fetch 階段） | `[SHADOW-PIPELINE] mode=fixture reason=no_batch_found dir=artifacts/eval` |
| 無 batch（bootstrap 階段） | `[SHADOW-PIPELINE] mode=fixture reason=bootstrap_fallback src=tests/fixtures/eval/shadow_raw_records.jsonl` |

Reviewer 應能從 CI log **一眼看出** 本次 nightly 用的是 shadow 還是 fixture。

### Step 4 — 本地驗證（必做，再開 PR）

**場景 A — 有 shadow batch（AC1）**

```bash
# 在 repo 根目錄
export SHADOW_BATCH_DIR=artifacts/eval
export SHADOW_SPOOL=/tmp/test_spool.jsonl
rm -f "$SHADOW_SPOOL"
bash scripts/fetch_latest_shadow_batch.sh
# 預期：mode=shadow，/tmp/test_spool.jsonl 非空
wc -l "$SHADOW_SPOOL"   # 應 > 4（fixture 只有 4 行）
```

**場景 B — 無 shadow batch（AC2）**

```bash
export SHADOW_BATCH_DIR=/tmp/empty_batch_dir
mkdir -p "$SHADOW_BATCH_DIR"
export SHADOW_SPOOL=/tmp/test_spool2.jsonl
rm -f "$SHADOW_SPOOL"
bash scripts/fetch_latest_shadow_batch.sh
# 預期：mode=fixture reason=...，spool 仍不存在
# 模擬 bootstrap：
cp tests/fixtures/eval/shadow_raw_records.jsonl "$SHADOW_SPOOL"
wc -l "$SHADOW_SPOOL"   # 應 = 4
```

**場景 C — 下游不受影響（AC3）**

```bash
# 用場景 A 產出的 spool 跑 export（與 nightly 相同參數）
python -m observability.ibridge_exporter \
  --source shadow --profile shadow --force \
  /tmp/test_spool.jsonl \
  -o /tmp/shadow_export.jsonl --no-latest
python -m observability.eval_ci_check /tmp/shadow_export.jsonl \
  --limit 100 --max-needs-review-ratio 0.60 --fail-on-tags infra_risk
# exit code 與改動前語意一致即可
```

**場景 D — PR job 不受影響（AC4）**

```bash
git diff --stat
# 確認僅 eval-gate-ci.yml（eval-shadow-nightly 區段）、fetch 腳本、可選 README
# eval-gate job 區段 diff 應為空
```

### Step 5 — 自檢清單

- [ ] `eval-gate` job（PR/push）step 序列與改動前一致。
- [ ] dryrun / enf_preview step 仍設 `continue-on-error: true`。
- [ ] 未改 ENF-RULE、dryrun CLI、preview wrapper exit policy。
- [ ] fetch 腳本「無 batch」時 exit 0。
- [ ] `git diff` 範圍在允許清單內。

---

## 4. 驗收條件（AC1–AC4，對應 IMPL-01）

### AC1 — 有 shadow 批次 → 使用 shadow

**Given**：repo 內存在非空 `artifacts/eval/shadow_batch_*.jsonl`（現有 `shadow_batch_20260530.jsonl` 即可）。  
**When**：執行 fetch + bootstrap 流程（本地或 `workflow_dispatch` + `run_shadow_nightly=true`）。  
**Then**：

- spool 行數 **>** fixture 的 4 行（或含 fixture 沒有的 `task_id`，如 `prod-shadow-9469a97892-k2`）。
- CI log 含 `[SHADOW-PIPELINE] mode=shadow batch=<stamp>`。
- bootstrap step **未** cp fixture（log 無 `bootstrap_fallback`，或 spool mtime 來自 fetch）。

### AC2 — 無 shadow 批次 → 使用 fixture

**Given**：暫時移走 / 更名所有 `shadow_batch_*.jsonl`（**僅本地驗證**；勿 commit 刪除樣本檔）。  
**When**：執行 fetch + bootstrap。  
**Then**：

- spool 內容與 `tests/fixtures/eval/shadow_raw_records.jsonl` 一致（4 行）。
- CI log 含 `[SHADOW-PIPELINE] mode=fixture`（`reason=no_batch_found` 和/或 `reason=bootstrap_fallback`）。
- nightly **仍成功完成** export → eval_ci_check → dryrun → preview（與改動前行為一致）。

### AC3 — 不影響 governance / dry-run / preview 核心路徑

**Then**：

- `tools/dryrun_ci_wrapper`、`tools/enf_preview_wrapper` **無 diff**（或僅 README 交叉引用，無邏輯變更）。
- dryrun 仍印 `[DRYRUN-LOG]`；preview 仍印 `[GOV-ENF-PREVIEW]`；兩者 exit 0 + `continue-on-error: true`。
- `eval_ci_check` 的 `--limit`、`--max-needs-review-ratio`、`--fail-on-tags` 參數**不變**。
- 當 spool 來源從 fixture 換成 shadow batch 時，下游 log **內容可變**（這是預期），但 **step 成敗語意不變**。

### AC4 — fetch bug 不破坏非 shadow workflows

**Then**：

- `eval-gate` job（PR / push）**無新增 step**。
- 其他 workflow 檔 **無 diff**。
- 若 fetch 腳本 crash（`set -e` 下極端錯誤），**僅** `eval-shadow-nightly` job 失敗；不影響 `eval-gate` 或 repo 其他 CI。
- fetch 對「無 batch」必須優雅降級（exit 0 + fixture fallback），**不得**讓 nightly 無資料可跑。

---

## 5. 回報格式（Cursor 完成後）

```markdown
## Execution Report — W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-01

### 修改/新增檔案
- scripts/fetch_latest_shadow_batch.sh（新增或修改）
- .github/workflows/eval-gate-ci.yml（eval-shadow-nightly 區段）
- observability/shadow-pipeline/README.md（可選）

### 本地驗證
<場景 A/B 命令與 [SHADOW-PIPELINE] log 摘錄>

### AC 自檢
- [AC1] mode=shadow + spool 行數 > 4：<OK/FAIL>
- [AC2] mode=fixture + 4 行 fixture：<OK/FAIL>
- [AC3] dryrun/preview/enf 無邏輯 diff：<OK/FAIL>
- [AC4] eval-gate job 無變更：<OK/FAIL>

### git diff --stat
<貼輸出>
```

---

## 6. 不在本票範圍（留給後續票）

| 票 | 內容 |
|----|------|
| IMPL-02 | prod 端 `export_shadow_batch.py` 匯出腳本 |
| IMPL-03 / v1 | S3 bucket 自動 upload + CI `aws s3 cp` |
| MINING 重跑 | 管線通後另開票重跑 POLICY-MINING |

---

## 7. 參考

- 設計全文：`W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01.md`
- 既有 nightly 說明：`observability/dryrun/README.md`（workflow 名稱與 job 索引）
- Spool schema：`observability/eval_export.md`（prod spool 與 bootstrap 說明）

---

*版本：v0.1 · 2026-05-31 · W5-A-RUNTIME-03-CI-DATA-PIPELINE-BRIEF-FOR-CURSOR*
