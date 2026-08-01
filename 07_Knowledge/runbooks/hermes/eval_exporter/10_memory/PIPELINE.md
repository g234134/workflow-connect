# PIPELINE — eval_exporter 執行管線

> 僅基於 code + 文檔分析；CI/CD 與 cron 細節部分標未知。

---

## 1. 執行入口

| 入口方式 | 指令 | 來源 |
|----------|------|------|
| **CLI (python -m)** | `python -m observability.eval_exporter <input_path> -o <output>` | `__main__` → `main()` |
| **CLI (python)** | `python observability/eval_exporter.py <input_path> …` | script top-level |
| **程式 API** | `export_eval_jsonl(input_path, output_path, *, gate_filter)` | 直接 import 呼叫 |

### CLI 參數
```
usage: python -m observability.eval_exporter [-h] [-o OUTPUT] [--filter {all,pass,needs_review}] input_path

positional arguments:
  input_path             Input .json / .jsonl file or directory of record files

options:
  -o, --output           Output JSONL path (default: eval_results.jsonl)
  --filter               Only write rows matching gate_result (default: all)
```

---

## 2. 被誰呼叫

| 呼叫者 | 方式 | 目的 |
|--------|------|------|
| **GitHub Actions (eval-gate-ci.yml)** eval-gate job | `eval_ci_check`（內部 import `build_export_line`、`iter_records`） | PR/push CI。**注意：eval_exporter 本身不被 CI 直接呼叫**——CI 只跑 eval_ci_check，後者直接 import exporter 函式。eval_export/v1 JSONL 非 CI 產物。 |
| **GitHub Actions (eval-gate-ci.yml)** eval-shadow-nightly job | `ibridge_exporter --source shadow` → `eval_ci_check` | 排程 shadow nightly。同樣**不**直接呼叫 eval_exporter。 |
| **手動/開發者** | 終端機直接執行 `python -m observability.eval_exporter` | 臨時批次評估特定資料 |
| **pytest（indirect）** | `tests.test_eval_exporter` | 測試中呼叫 `export_eval_jsonl()` |

**CI 實際步驟**（已讀取 `.github/workflows/eval-gate-ci.yml`）：
- `eval-gate` job（push/PR）：resolve params → unit tests（4 個 test） → eval_ci_check（`--limit 50 --max-needs-review-ratio 0.72`）
- `eval-shadow-nightly` job（schedule + workflow_dispatch）：bootstrap spool → ibridge_exporter → unit tests → eval_ci_check（`--limit 100 --max-needs-review-ratio 0.60 --fail-on-tags infra_risk`）

---

## 3. 產物去向

| 產物 | 去向 | 消費方 |
|------|------|--------|
| `eval_export/v1` JSONL（CLI 指定路徑） | `-o` 參數決定 | `observability.eval_ci_check`（PR CI）、`observability.eval_stats`（分佈分析） |
| stdout JSON 結果 dict | 終端機輸出 | 人類檢查、上層排程（解析 `ok` 與 `written`） |

**典型完整管線示意**（從已讀檔案確認）：
```
ibridge_exporter (collector/file/shadow)
  → artifacts/eval/ibridge_records.latest.jsonl
  → eval_exporter (手動或本機指令；CI 從不直接呼叫)
  → artifacts/eval/eval_results.jsonl
  → eval_stats (分析與閾值建議)

CI 實際流程（eval-gate-ci.yml）：
  eval-gate (push/PR):
    ibridge_records.latest.jsonl → eval_ci_check (內部 import eval_exporter)
  eval-shadow-nightly (schedule):
    k2_shadow_spool → ibridge_exporter → eval_ci_check
  eval_exporter → eval_export/v1 JSONL 不在 CI 自動管線中
```

---

## 4. 與 CI/CD 的關係

| 層面 | 現狀 | 已知程度 |
|------|------|----------|
| **GitHub Action 名稱** | `Eval gate CI`（`eval-gate-ci.yml`） | ✅ 已確認 |
| **觸發事件** | push, pull_request, schedule (UTC 06:00), workflow_dispatch | ✅ 已確認 |
| **Job 1: eval-gate**（push/PR） | resolve params → unit tests（4 tests）→ eval_ci_check `--limit 50 --max-needs-review-ratio 0.72` | ✅ 已讀 YAML |
| **Job 2: eval-shadow-nightly**（schedule + wf_dispatch with flag） | bootstrap spool → ibridge_exporter --source shadow → unit tests → eval_ci_check `--limit 100 --ratio 0.60 --fail-on-tags infra_risk` | ✅ 已讀 YAML |
| **eval_exporter 在 CI 中的角色** | **CI 從不直接呼叫 eval_exporter**。兩個 job 都只跑 `eval_ci_check`（內部 import exporter 函式）。eval_export/v1 JSONL 只能透過手動或獨立腳本產生。 | ✅ 已確認，重要差異 |
| **CI 預設輸入（eval-gate）** | `artifacts/eval/ibridge_records.latest.jsonl`（可被 `use_fixture` 覆蓋） | ✅ 已確認 |
| **CI 預設輸入（eval-shadow-nightly）** | `artifacts/eval/k2_shadow_spool.jsonl`（空時 bootstrap from fixture） | ✅ 已確認 |
| **產物清理政策** | 未查 | **unknown** |

---

## 5. 與 eval_gate 的整合時序

```
eval_exporter 啟動
  → iter_records(input_path)    # 遞迴讀取 JSONL/JSON
  → for each record:
       build_export_line(record)
         → evaluate_task_record(record)   # 呼叫 eval_gate
         → gate_result_label(gate_dict)    # pass / needs_review
         → summarize_metrics(record)       # 萃取摘要
         → _matches_filter(gate_result, gate_filter)  # 篩選
       → write JSONL line
  → 回傳 result dict
  → print(json.dumps(result))
```

---

## 6. 測試管線

| 測試檔 | 測試項數量 | 測試範圍 |
|--------|-----------|----------|
| `tests/test_eval_exporter.py` | 6 個 test case | `build_export_line`（pass/needs_review）、unwrap、批量 export（all/filter）、context_heavy |
| fixture | 3 條 ibridge_record（pass / needs_review / infra_risk） | `tests/fixtures/eval/ibridge_records.jsonl` |

**測試覆蓋率觀察**：
- ✅ gate filter 邏輯（`all` vs `needs_review`）
- ✅ unwrap `ibridge_record` 包裝
- ✅ context_heavy gate 與 summary 整合
- ❌ 目錄遞迴輸入（`iter_records` 目錄分支在測試中未覆蓋）
- ❌ JSON 陣列輸入（`_records_from_json_file` 未直接測試）
- ❌ 無效 JSON / 空行 / 空白檔案邊界情況
- ❌ `gate=None` 時自動呼叫 eval_gate 的路徑 vs 傳入 gate dict 的路徑
- ❌ exporter 在非 ok 情境下的行為（如 eval_gate 拋異常）

---

## 7. 未知項彙整（更新後）

- `artifacts/eval/` 目錄是否存在、有何實際資料 — **仍 unknown**
- eval_exporter 產生的 JSONL 是否有外部 dashboard/grafana/splunk 消費 — **仍 unknown**
- 產物 retention policy — **仍 unknown**
- 命名約定：`eval_results.latest.jsonl` 是否也存在 — **仍 unknown**（僅 `artifacts/eval/eval_results.jsonl` 在文檔中出現）
- **已澄清**：CI 從不直接呼叫 eval_exporter；push/PR 與 shadow nightly 均走 eval_ci_check 路徑。
