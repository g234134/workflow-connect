# Enforcement preview (`observability/enf-preview/`)

> **⚠ PREVIEW — 未實施 enforcement，不影響任何 CI/pipeline 決策**

Wave 5-A RUNTIME-03 Phase A（`W5-A-RUNTIME-03-ENF-PREVIEW`）的**唯讀** enforcement 預覽層。在 RUNTIME-02 `[DRYRUN-LOG]` 之後執行，讀取 dry-run per-record JSONL，依 ENF-RULE 候選計算「若開始 enforcement 會擋到誰」，僅印 `[GOV-ENF-PREVIEW]` 結構化行。

## CI

**Workflow**：`.github/workflows/eval-gate-ci.yml` · job `eval-shadow-nightly`

在 **Dry-run governance log (logging-only)** 之後追加 preview step：

```bash
python -m tools.enf_preview_wrapper \
  --input-dir observability/dryrun \
  --min-score 0.7
```

| 項 | 說明 |
|----|------|
| Wrapper | `tools/enf_preview_wrapper.py` |
| 輸入 | 最新 `observability/dryrun/<stamp>_per_record.jsonl`（由 RUNTIME-02 產生） |
| Pipeline 影響 | **零** — wrapper **永遠 exit 0** + step 設 **`continue-on-error: true`** |
| 與 Phase B | 本票**不含** blocking；Phase B 需另開票且不得在本 wrapper 預留 exit 1 邏輯 |

## ENF-RULE 候選（Phase A）

| 規則 | 層級 | 條件（摘要） | 計數 |
|------|------|--------------|------|
| **ENF-RULE-1** | L2 候選 | `dryrun_rule=gate_fail_deny` + `error_type` 非空 + 風險 tag（如 `infra_risk`）+ `trace_completeness_score ≥ --min-score` | `would_block` |
| **ENF-RULE-2** | L1 觀察 | `dryrun_rule=gate_fail_needs_review` + `high_retry` tag + `retry_count ≥ 2` | `would_warn` |
| （其餘） | — | 含 `edge_unknown` | `would_noop` |

來源：POLICY-MINING-01 §3.1 C-01 / C-03。新規則待後續 POLICY-SELECTION 票擴充 wrapper 常數與 `elif` 分支。

## `[GOV-ENF-PREVIEW]` 行格式

```
[GOV-ENF-PREVIEW] ⚠ PREVIEW — 未實施 enforcement，不影響 pipeline 結果
[GOV-ENF-PREVIEW] event=summary total=8 would_block=1 would_warn=2 would_noop=5 input=observability/dryrun/20260530T185213Z_per_record.jsonl
[GOV-ENF-PREVIEW] event=detail rule=ENF-RULE-1 would_block=1 min_score=0.7
[GOV-ENF-PREVIEW] event=detail rule=ENF-RULE-2 would_warn=2
[GOV-ENF-PREVIEW] event=complete status=ok exit_policy=preview_only
```

缺 artefact 或例外時印 `[GOV-ENF-PREVIEW] [WARN]`，仍 **exit 0**。

## 本地驗證

```bash
python -m tools.enf_preview_wrapper \
  --input observability/dryrun/20260530T185213Z_per_record.jsonl \
  --verbose
```

## 相關文件

- Dry-run 報表目錄：`observability/dryrun/README.md`
- RUNTIME-02 logging step：`tools/dryrun_ci_wrapper.py`
