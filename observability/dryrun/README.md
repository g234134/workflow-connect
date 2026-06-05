# Dry-run reports (`observability/dryrun/`)

> **⚠ DRY-RUN — 不影響任何 CI/pipeline 決策**

Wave 5-A 第一條 runtime 線（`W5-A-RUNTIME-01-DRYRUN`）的**唯讀**比對輸出目錄。CLI 只讀既有 artefact，將簡化治理規則推算的 `ideal_verdict` 與 artefact 中的 `actual_verdict` 對照，寫入本目錄下的時間戳報表。

## CLI

從 repo 根執行：

```bash
python -m tools.dryrun --input-dir artifacts/eval/ --output-dir observability/dryrun/
```

或指定單一檔案：

```bash
python -m tools.dryrun artifacts/eval/shadow_eval_results.latest.jsonl
```

### 參數

| 參數 | 預設 | 說明 |
|------|------|------|
| `artefacts` | — | 可選：一個或多個 JSONL / 目錄路徑 |
| `--input-dir` | `artifacts/eval` | 掃描 shadow eval / ibridge / gate state |
| `--output-dir` | `observability/dryrun` | 報表輸出目錄 |
| `--min-score` | `0.875` | `gate_ok_score_high` 的 trace 完整度門檻 |
| `--verbose` | off | 逐筆列印到 stdout |

## 輸入 artefact（只讀）

| 類型 | 典型檔名 | 格式 |
|------|----------|------|
| Eval export | `shadow_eval_results.latest.jsonl` | `eval_export/v1` JSONL |
| Ibridge | `shadow_ibridge_records.latest.jsonl` | M-line JSONL（CLI 內建簡化 gate 推導） |
| Aggregate gate | `shadow_state.json` | 僅寫入 summary 附註，不產 per-record 列 |

同一 `task_id` 多來源時，**eval export 優先**於 ibridge 衍生列。

## 輸出

每次執行產生兩個檔案（UTC 時間戳前綴）：

- `<stamp>_per_record.jsonl` — 每行一筆比對
- `<stamp>_summary.md` — 總數、match 比例、差異清單、免責聲明

### Per-record 欄位

| 欄位 | 說明 |
|------|------|
| `task_id` | 任務 ID |
| `actual_verdict` | 由 `gate_result` / `success` / 明示 `verdict` 映射：`allow` / `warn` / `fail` / `unknown` |
| `ideal_verdict` | 簡化規則桶：`allow` / `warn` / `deny` / `unknown` |
| `verdict_match` | 是否一致（`fail` 與 `deny` 視為匹配） |
| `dryrun_rule` | 觸發規則名 |
| `metrics` | 精簡指標快照 |

### 治理規則（v0.1 近似）

| `dryrun_rule` | 條件（摘要） |
|---------------|----------------|
| `gate_ok_score_high` | `gate_result=pass` 且 trace score ≥ `--min-score` → ideal `allow` |
| `gate_ok_score_low` | `gate_result=pass` 且 trace score < `--min-score` → ideal `warn` |
| `gate_fail_deny` | `success=false` 或 `infra_risk` / infra `error_type` → ideal `deny` |
| `gate_fail_needs_review` | `needs_review` 或 review tags → ideal `warn` |
| `edge_unknown` | 缺 `task_id` / 無法判定 score / 未知 gate → ideal `unknown` |

## 限制與免責

- 規則為 **近似推導**，不完整對應 G10 rulebook 或 `observability.eval_gate` 全表。
- **不**寫入 CI、PR check、gate verdict 檔或 pipeline 狀態。
- **不**呼叫外部 API 或 production DB。
- 後續 `W5-A-RUNTIME-02+` 才可能將驗證通過的規則接到 prod CI；本目錄報表僅供人工審閱。

## CI（logging-only）

**Workflow**：`.github/workflows/eval-gate-ci.yml` · job `eval-shadow-nightly`（UTC 06:00 schedule / `workflow_dispatch` + `run_shadow_nightly`）

**Spool 資料來源（v0）**：nightly 優先載入 `artifacts/eval/shadow_batch_*.jsonl`（`[SHADOW-PIPELINE] mode=shadow`），無 batch 時退回 fixture（`mode=fixture`）。詳見 `observability/shadow-pipeline/README.md`。

在 **Phase 1 shadow eval_ci_check 之後**追加唯讀步驟；**不**讀取或改寫 gate verdict / exit code。

```bash
python -m tools.dryrun_ci_wrapper \
  --input artifacts/eval/shadow_ibridge_records.latest.jsonl \
  --output-dir observability/dryrun
```

| 項 | 說明 |
|----|------|
| Wrapper | `tools/dryrun_ci_wrapper.py` |
| 輸入 | 與 nightly gate 相同：`SHADOW_EXPORT_OUT`（`shadow_ibridge_records.latest.jsonl`） |
| 輸出 | 同 CLI：`observability/dryrun/<stamp>_per_record.jsonl` + `_summary.md` |
| Pipeline 影響 | **零** — wrapper **永遠 exit 0** + step 設 **`continue-on-error: true`**；僅印 `[DRYRUN-LOG]` 結構化行 |
| 禁止 | 不得用本步驟 `if` / matrix 決定成敗；不得改 `eval_ci_check` 邏輯 |

### `[DRYRUN-LOG]` 行格式

每行以 `[DRYRUN-LOG]` 開頭，`key=value` 空白分隔，例如：

```
[DRYRUN-LOG] event=start disclaimer=⚠ DRY-RUN — … input=artifacts/eval/shadow_ibridge_records.latest.jsonl min_score=0.875
[DRYRUN-LOG] event=summary records=8 matches=8 mismatches=0 match_ratio=100.0% min_score=0.875
[DRYRUN-LOG] event=artefact per_record=observability/dryrun/20260530T185213Z_per_record.jsonl summary=observability/dryrun/20260530T185213Z_summary.md stamp=20260530T185213Z
[DRYRUN-LOG] event=complete status=ok exit_policy=logging_only
```

## Enforcement preview（Phase A · RUNTIME-03）

在 nightly `[DRYRUN-LOG]` step **之後**追加唯讀 preview（**不**改本節 CLI 或 `[DRYRUN-LOG]` 行為）：

- Wrapper：`tools/enf_preview_wrapper.py`
- 文件：`observability/enf-preview/README.md`
- Log 前綴：`[GOV-ENF-PREVIEW]`（與 `[DRYRUN-LOG]` 分開）
- Pipeline 影響：**零**（永遠 exit 0 + `continue-on-error: true`）

## 測試

```bash
python -m unittest tests.test_dryrun_basic -v
```
