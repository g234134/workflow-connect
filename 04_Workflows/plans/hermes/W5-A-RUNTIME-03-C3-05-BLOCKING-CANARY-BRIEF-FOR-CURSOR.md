# W5-A-RUNTIME-03-C3-05 BLOCKING-CANARY — Cursor 實作簡報

> **用途**: 給 Cursor（或其他實作者）看的 scope 文件。Blocking 條件留 TODO，由 N 次 nightly 數據驅動後填入。
>
> **關聯**: `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` (完整 Phase B 設計)、`observability/enf_config.py` (runtime config)、`tools/enf_preview_wrapper.py` (current preview entry)

---

## 背景

ENF (Engagement Notification Framework) 的 Phase A 已上線 shadow-only preview 模式——CI 中執行所有規則判定、輸出 `[GOV-ENF-PREVIEW]` 與 `[GOV-ENF-SHADOW-SUMMARY]` 日誌，但永遠 exit 0，不影響 pipeline pass/fail。Phase B 的目標是在此基礎上引入 **limited blocking canary**：由兩層正交環境變數控制，允許操作者在特定條件下將 shadow decision 實際升級為 exit 1（CI job fail），從而驗證 blocking 機制的完整性，並為 Phase C（full enforcement）鋪路。

**Design rationale 濃縮**：
- 雙層開關（`GOV_ENF_ENABLE` + `GOV_ENF_BLOCKING_CANARY`）確保 orthogonality——ENF 要不要跑、能不能擋是兩個獨立維度，可獨立切換
- `GOV_ENF_ENABLE=0` 是 kill switch，在 canary 誤傷時可瞬間止血，不需關心 blocking canary 的值
- 預設值均為 `0`（ENF enabled / canary disabled shadow-only），這是最安全的 starting point

---

## 目標

實作一組可由 CI workflow `env:` 區塊直接控制的 blocking canary 機制。具體來說：當 `GOV_ENF_ENABLE=1` 且 `GOV_ENF_BLOCKING_CANARY=1` 時，wrapper 的 `exit_policy` 從 `preview_only` 切換為 `canary_blocking`，將符合 blocking 條件的記錄從印 log 升級為 exit 1。同時所有日誌與 summary 要明確標示 blocking 是否生效，讓 CI log 的第一眼就能判斷目前處於 shadow 還是 canary 模式。

---

## Env / Kill-Switch 設計

| 變數 | 語義 | 預設值 |
|---|---|---|
| `GOV_ENF_ENABLE` | **Master switch**：`1`=ENF 執行計算與 shadow logging；`0`=完全關閉（zero overhead，連 shadow log 都不寫） | `1` |
| `GOV_ENF_BLOCKING_CANARY` | **Canary switch**：`1`=blocking 啟用（wrapper 可在條件命中時 exit 1）；`0`=shadow-only 不 blocking（Phase A 現有行為） | `0` |

**優先級**：`GOV_ENF_ENABLE=0` > `GOV_ENF_BLOCKING_CANARY`。Master off 時 canary 無效。

**模式矩陣**：

| ENABLE | CANARY | 模式 | wrapper exit |
|---|---|---|---|
| 0 | 無效 | ENF skipped | 0 |
| 1 | 0 | shadow-only（Phase A 現狀） | 0 |
| 1 | 1 | blocking canary | 條件命中時 exit 1 |
| 1 | 1 | blocking canary（條件未命中） | 0 |

既有的 `ENF_ENABLE`（無 `GOV_` 前綴的 legacy key）保留向後相容，但由 `load_enf_config()` 統一解析——`GOV_ENF_ENABLE` 優先於 `ENF_ENABLE`。

---

## 修改範圍（預期 Cursor 會動到的檔案 / job）

### Python 來源檔

| 檔案 | 預期改動 |
|---|---|
| `observability/enf_config.py` | 在 `EnfMode` type 增加 `"canary-blocking"`；`should_run_enf` property 可能需要改名或新增 `should_block`；`format_config_log_line()` 顯示 blocking 狀態 |
| `tools/enf_preview_wrapper.py` | 讀取 config 後判斷 `blocking_canary`。若 blocking enabled 且記錄符合 blocking condition → exit 1。summary 輸出加入 `exit_policy=canary_blocking` 標記 |
| `tools/print_enf_env.py` | （可能不需改動，已註冊兩個 key。但若 blocking canary 引入新行為階段可在此加入備註） |

### CI workflow job

| Job / step | 預期改動 |
|---|---|
| `eval-gate` CI 中 wrapper 的 step | 在 `env:` 區塊加入 `GOV_ENF_BLOCKING_CANARY: "${{ vars.GOV_ENF_BLOCKING_CANARY }}"`，讓 repo variable 可控制（預設 `"0"`） |

### Tests

| 檔案 | 預期改動 |
|---|---|
| `tests/test_enf_config.py` | 增加 `GOV_ENF_ENABLE=1, GOV_ENF_BLOCKING_CANARY=1` 的測試案例；驗證 mode 為 `"canary-blocking"` |
| `tests/test_enf_preview_wrapper.py` | 增加 blocking canary enabled 時的 exit 1 行為測試；blocking condition 命中 ／ 未命中的兩種 case |

---

## Blocking 行為定義

### Shadow-only（GOV_ENF_ENABLE=1, GOV_ENF_BLOCKING_CANARY=0）
- 所有規則判定照常執行
- 輸出 `[GOV-ENF-PREVIEW]`、`[ENF-WARN]`、`[GOV-ENF-SHADOW-SUMMARY]`
- `exit_policy=preview_only`
- **永遠 exit 0**

### Future blocking（GOV_ENF_ENABLE=1, GOV_ENF_BLOCKING_CANARY=1）
- 所有規則判定照常執行
- 輸出 `[GOV-ENF-PREVIEW]`、`[ENF-WARN]`、`[GOV-ENF-CANARY-SUMMARY]`（注意：prefix 從 `SHADOW` 改為 `CANARY`）
- `exit_policy=canary_blocking`
- **符合 blocking condition 的記錄 → exit 1**

> **TODO**: Blocking condition 的詳細定義。預期路線：
> 1. 先對 `ENF-RULE-1`（`gate_fail_deny` + `infra_risk`/`security:critical` tag）做 limited blocking
> 2. 門檻值（min_score、樣本數）由 N 次 nightly 數據驅動後填入
> 3. 具體條件與 scope 在 `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` 的 §4 更新後補入此處
>
> 實作上：wrapper 在 blocking canary enabled 時，對 `would_block > 0` 的規則判斷是否在 blocking scope 內。Scope 未定之前可以先 **mock 為「只要有任何 would_block 記錄就 exit 1」** 來驗證 env/kill-switch chain，但 production CI 中 CURSOR 不能自己決定 blocking scope。

---

## 驗收標準（在 CI log 中可明確看到）

```
[1] Env 設定可見
    $ python -m tools.print_enf_env --group enf
    [enf]
    GOV_ENF_ENABLE=1 effective=on
    GOV_ENF_BLOCKING_CANARY=1 effective=on
    ...

[2] ENF config 摘要
    [ENF] config: GOV_ENF_ENABLE=1, GOV_ENF_BLOCKING_CANARY=1 (canary-blocking)

[3] Blocking 行為是否啟用（日誌 prefix 區別）
    shadow-only 模式 → [GOV-ENF-SHADOW-SUMMARY]
    blocking canary 模式 → [GOV-ENF-CANARY-SUMMARY]

[4] Exit code 正確
    shadow-only: exit code = 0（即使 would_block > 0）
    blocking canary + condition hit: exit code = 1
    blocking canary + no condition hit: exit code = 0

[5] Kill switch 測試
    同一次 run，只改 GOV_ENF_ENABLE=0，wrapper 應直接 exit 0 且不輸出任何 ENF 日誌
```

---

## Pseudo code（wrapper 核心邏輯）

```python
# 在 enf_preview_wrapper.py main() 中

config = load_enf_config()
log_enf_config(config)          # 輸出 [ENF] config: ...

if not config.enabled:
    print("[ENF] ENF skipped — zero overhead path")
    sys.exit(0)

# 讀取 dry-run JSONL，執行規則判定（與 Phase A 相同）
records = load_dryrun_records(input_path)
summary = evaluate_all_rules(records)

# 決定 exit_policy 與 summary prefix
summary.mode = "shadow" if not config.blocking_canary else "canary"
summary.exit_policy = "preview_only" if not config.blocking_canary else "canary_blocking"

# 輸出 summary（prefix 取決於模式）
if config.blocking_canary:
    print(f"[GOV-ENF-CANARY-SUMMARY] {json.dumps(summary.to_dict())}")
else:
    print(f"[GOV-ENF-SHADOW-SUMMARY] {json.dumps(summary.to_dict())}")

# Blocking gate（僅 blocking canary 模式啟用）
if config.blocking_canary and summary.would_block > 0:
    # TODO: 加入 blocking condition 過濾（scope、threshold、rule 白名單）
    # 目前 mock: 任何 would_block 都視為 blocking
    print(
        f"[ENF] Blocking canary triggered — {summary.would_block} "
        f"record(s) would block, exiting 1"
    )
    sys.exit(1)

sys.exit(0)
```

> **給 Cursor 的指令**: 以上 pseudo code 中 `TODO` 區塊與 blocking condition 邏輯不要寫死。產出程式碼時沿用現有 `enf_config.py` 的 `blocking_canary` boolean，wrapper 中只判斷模式切換 exit code。Blocking condition 的 scope 與 threshold 留給後續 nightly 數據驅動的 PR 補上。
