# ENF Shadow / Preview 值班與決策指南

> **票號**：W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE  
> **定位**：操作與判讀指南（doc-only；不改工具、不改 CI、不改 rule、不改 runtime 行為）  
> **Phase**：Phase 2（stable preview / logging-only / shadow-only）  
> **讀者**：值班者、reviewer、需讀 nightly report 並判斷訊號的任何人  
> **前提**：不須回頭讀完整設計史即可照做

---

## 1. Overview

### 用途

本指南說明如何在 **ENF shadow / preview 模式**下值班：每天／每週要跑哪些指令、如何從 CI log 抽出 `[GOV-ENF-SHADOW-SUMMARY]`、如何用 analyzer 聚合多日數據，以及哪些數字代表「可接受」、哪些代表「要追查」。

### 讀者

- **值班者**：確認 nightly pipeline 有產出 summary、status 正常。
- **Reviewer / policy-mining**：解讀 block rate、rule 分布、samples，決定是否延長觀察或建議開下一張 BLOCKING-CRITERIA 票。

### 明確聲明：本階段仍是 Phase 2（preview / logging-only）

| 項目 | 現況 |
|------|------|
| Blocking | **尚未啟用**。`GOV_ENF_BLOCKING_CANARY=0` 為 CI 預設。 |
| Pipeline 影響 | ENF preview wrapper **永遠 exit 0**；nightly step 另設 `continue-on-error: true`。 |
| `would_block` / `would_warn` | 皆為**觀測值**，不是實際阻斷。 |
| 本文件 | **不定義**正式 blocking policy、**不授權**任何人自行開啟 blocking。 |

---

## 2. Current Control Plane

### 2.1 核心 env 開關

解析邏輯見 `observability/enf_config.py`；值班時可用 `python -m tools.print_enf_env --group enf` 唯讀確認。

| 環境變數 | 含義 | unset 預設 |
|----------|------|------------|
| `GOV_ENF_ENABLE` | 主開關（優於 `ENF_ENABLE`） | 視為 `1`（啟用） |
| `ENF_ENABLE` | 舊別名；僅在 `GOV_ENF_ENABLE` 未設時生效 | 視為 `1` |
| `GOV_ENF_BLOCKING_CANARY` | blocking canary 旗標（**Phase 2 仍為 off**） | `0`（shadow-only） |
| `GOV_ENF_BLOCKING_CANARY_DISABLE` | 顯式禁用 canary（優先於 `GOV_ENF_BLOCKING_CANARY`） | unset |

**`GOV_ENF_BLOCKING_CANARY=0`（shadow-only）代表什麼**

- ENF preview **仍會執行**（若 `GOV_ENF_ENABLE` 為 on）：讀 dry-run per-record JSONL、分類 would_block / would_warn、印 `[GOV-ENF-PREVIEW]` 與 **`[GOV-ENF-SHADOW-SUMMARY]`**。
- **不影響** job pass/fail：wrapper 固定 **exit 0**；即使內部 exception 也只會 `status=error_logged`，不會 fail pipeline。
- 每次 run 開頭會印：`[ENF] config: GOV_ENF_ENABLE=1, GOV_ENF_BLOCKING_CANARY=0 (shadow-only)`。

**`GOV_ENF_BLOCKING_CANARY=1`**

- 屬未來 Phase B / BLOCKING-CRITERIA 票範疇；**本指南與 Phase 2 值班流程均假設其為 `0`**。請勿在 prod CI 自行改為 `1`。

**顯式 disable 時的 audit 警告**

若有人把 `GOV_ENF_ENABLE=0` 或 `GOV_ENF_BLOCKING_CANARY_DISABLE=1` 設進 CI，會印 `[ENF] WARNING:`（非 fatal）。值班若看到此類行，表示 ENF 可能被刻意關掉，需對照 workflow env。

### 2.2 哪些 CI job 會產生 ENF 相關 log

Workflow：`.github/workflows/eval-gate-ci.yml`

| Job | 觸發 | ENF 相關步驟 | 是否產出 `[GOV-ENF-SHADOW-SUMMARY]` |
|-----|------|--------------|--------------------------------------|
| **`eval-gate`** | push / PR / manual（非 schedule） | `ENF flags audit` → `python -m observability.enf_config` | **否**（僅 config 行） |
| **`eval-shadow-nightly`** | schedule（UTC 06:00 每日）或 manual + `run_shadow_nightly=true` | 完整 shadow pipeline → dry-run → **`Enforcement Preview (Phase A)`** | **是**（每 run 一條 JSON summary） |
| `shadow-spool-smoke` | push / PR | 無 ENF | 否 |

**Nightly pipeline 順序（與 ENF 有關的部分）**

1. Shadow batch / spool / export  
2. `eval_ci_check`（Phase 1 gate；與 ENF 分離）  
3. `dryrun_ci_wrapper` → 寫入 `observability/dryrun/<stamp>_per_record.jsonl`  
4. `enf_preview_wrapper` → 讀最新 per-record → emit summary  

兩個 job 的 env 預設均為 `GOV_ENF_ENABLE=1`、`GOV_ENF_BLOCKING_CANARY=0`。

### 2.3 Log 前綴速查

| 前綴 | 來源 | 用途 |
|------|------|------|
| `[ENF] config:` | `enf_config` | 確認 enable / canary / mode |
| `[GOV-ENF-PREVIEW]` | `enf_preview_wrapper` | 人讀事件（summary、detail、complete） |
| `[GOV-ENF-SHADOW-SUMMARY]` | `enf_preview_wrapper` | **analyzer 主輸入**（單行 JSON） |
| `[ENF-WARN]` | C3-05 / L1 警告 | allow + `infra_risk` 等；不影響 exit code |
| `[SHADOW-PIPELINE]` | shadow batch 腳本 | 取樣模式（shadow / fixture） |

Summary JSON 固定欄位（`status=ok` 時）：

```json
{
  "mode": "shadow",
  "status": "ok",
  "exit_policy": "preview_only",
  "total": 120,
  "would_block": 3,
  "would_warn": 2,
  "would_noop": 115,
  "min_score": 0.7,
  "rules": {
    "ENF-RULE-1": {"would_block": 3},
    "ENF-RULE-2": {"would_warn": 2, "shadow_retries": 2},
    "C3-05-L1-INFRA-RISK-SUCCESS": {"would_warn": 0}
  },
  "samples": {"would_block": [{"task_id": "...", "dryrun_rule": "gate_fail_deny", "error_type": "timeout", "tags": ["infra_risk"]}]}
}
```

`status` 非 `ok` 時常見 `reason`：`input_dir_not_found`、`no_per_record_artefact`、`input_not_found`、`no_records_loaded`、`env_disabled`、`error_logged`。

---

## 3. Operating Cadence

### 建議節奏

| 頻率 | 動作 | 目的 |
|------|------|------|
| **每日** | 確認 `eval-shadow-nightly` 成功；log 中有 `[GOV-ENF-SHADOW-SUMMARY]` 且 `"status":"ok"` | 避免 silent skip / 資料源中斷 |
| **每 2–3 天** | 合併數日 log，跑 analyzer | 看 block rate 與 rule 計數是否穩定 |
| **每週** | 整理 ENF-RULE-1 / ENF-RULE-2 / C3-05 趨勢與 samples 摘要 | 供 policy-mining 或 escalation 討論 |

### 每日檢查（約 5 分鐘）

1. 打開 GitHub Actions → workflow **Eval gate CI** → job **P+ prod shadow nightly**。  
2. 在 log 中搜尋 `[GOV-ENF-SHADOW-SUMMARY]`，確認最新一行的 `"status"` 為 `"ok"`。  
3. 順便確認同一 run 有 `[ENF] config: ... GOV_ENF_BLOCKING_CANARY=0 (shadow-only)`。

若 CI log 已下載到本機：

```bash
# 在 repo 根目錄執行；<PATH> 替換為 nightly raw log
grep '\[GOV-ENF-SHADOW-SUMMARY\]' <PATH>/nightly_ci.log | tail -1
```

或使用 tail 工具（若有 capture 到 `observability/enf-preview/*.log`）：

```bash
python -m tools.tail_enf_preview_logs --limit 10
python -m tools.tail_enf_preview_logs --from-dryrun --runs 3
```

**`status != ok` 時**：先看 JSON 的 `reason`；多數 skip 代表 dry-run artefact 缺失，需先修 shadow / dryrun pipeline，再解讀 ENF 數字。

### 每 2–3 天：跨日聚合

```bash
# 合併多日 log 後分析
grep '\[GOV-ENF-SHADOW-SUMMARY\]' nightly_day1.log nightly_day2.log nightly_day3.log \
  > /tmp/enf_summaries_only.log

python -m tools.analyze_enf_shadow_summaries --log /tmp/enf_summaries_only.log
```

### 每週：週報要點

記錄以下欄位（可直接從 analyzer 輸出複製）：

- `runs loaded`、`total records`、**block rate**
- 各 rule 的 `would_block` / `would_warn`
- Samples 中 dominant 的 `dryrun_rule` + `error_type` + `tags` 組合
- 本週是否有 `status=skipped` / spike 日

---

## 4. Analyzer Commands

僅使用 repo 內建工具，不依賴外部服務。

### 4.1 從 CI log 抽出 summary 行

```bash
# 單檔
grep '\[GOV-ENF-SHADOW-SUMMARY\]' <PATH>/eval-shadow-nightly.log > <PATH>/enf_summaries.log

# 多檔合併
grep -h '\[GOV-ENF-SHADOW-SUMMARY\]' <PATH>/nightly_*.log > <PATH>/enf_summaries.log
```

### 4.2 執行 analyzer

```bash
# 從檔案
python -m tools.analyze_enf_shadow_summaries --log <PATH>/enf_summaries.log

# 從 stdin pipe
grep '\[GOV-ENF-SHADOW-SUMMARY\]' <PATH>/nightly.log \
  | python -m tools.analyze_enf_shadow_summaries --stdin
```

### 4.3 本地 fixture 自測（熟悉輸出格式）

```bash
python -m tools.analyze_enf_shadow_summaries --log tests/fixtures/enf/shadow_summaries_sample.log
```

此 fixture **刻意含 spike 日**（would_block 從 2–3 跳到 15），用於練習辨識異常；勿當 prod 基線。

### 4.4 輔助唯讀工具

```bash
# ENF / nightly 相關 env（不修改環境）
python -m tools.print_enf_env --group enf
python -m tools.print_enf_env --group enf --json

# 從 dryrun artefact 即時重算（CI log 尚未下載時）
python -m tools.tail_enf_preview_logs --from-dryrun observability/dryrun --runs 5 --min-score 0.7
```

---

## 5. Reading the Report

### 5.1 Analyzer 輸出欄位

```
ENF Shadow Summary Report
──────────────────────────────────────────────────

Overall
  runs loaded         : N    ← 成功解析的 summary 行數（≈ 有 ENF 輸出的 nightly 次數）
  total records       : N    ← 跨 run 的 per-record 總筆數
  would_block (total) : N    ← 若啟用 blocking 會擋的總數（幾乎全來自 ENF-RULE-1）
  would_warn  (total) : N    ← ENF-RULE-2 + C3-05 的 warn 合計（analyzer 層級加總）
  would_noop  (total) : N
  block rate          : X.X% ← would_block / total_records

Per-Rule
  ENF-RULE-1 (block): would_block=N
  ENF-RULE-2 (warn)  : would_warn=N, shadow_retries=N
  C3-05-L1 (warn)    : would_warn=N

Samples (would_block)
  [task_id] rule=... error=... tags=...
```

| 欄位 | 意義 |
|------|------|
| `runs loaded` | 有幾次 nightly 產出了可解析的 summary；應接近觀測窗口內的天數 |
| `total records` | 樣本規模；nightly `EVAL_CI_LIMIT` 為 100，實際 per-record 可能略少 |
| `would_block` / `would_warn` / `would_noop` | 三類 preview  outcome 計數 |
| `block rate` | 全局 would_block 比例；**Phase 2 健康基線約 0.5–2%**（見下文） |
| Per-Rule 計數 | 各 rule 貢獻；目前 **ENF-RULE-1 是唯一 would_block 來源** |
| `shadow_retries` | 與 ENF-RULE-2 的 warn 數相同（高 retry 觀測） |
| **Samples** | 最多 5 條 would_block 樣本；用來判斷 **dominant pattern**（error_type + tags） |

**「triggered runs」怎麼看**

Analyzer 不單獨輸出 `triggered_runs`。實務上：

- 若 **多數 nightly** 的 summary JSON 裡 `would_block > 0`，表示 rule 在持續觸發（healthy signal）。
- 若 **連續多日** `would_block = 0` 且 `status=ok`，可能 rule 過窄或 traffic 無高風險 case。
- 若 **單日** would_block 遠高於其他日（fixture 中 T-spike 日 15 vs 平常 2–3），優先當 anomaly 調查。

**「dominant pattern」怎麼看**

看 Samples（或各日 summary JSON 的 `samples.would_block`）：

- 健康：多數為 `dryrun_rule=gate_fail_deny` + `tags` 含 `infra_risk` 或 `security:critical` + `error_type` 為 timeout / crash / healthcheck 類。
- 要小心：tags 擴散到 unrelated 類別，或 error_type 每日大幅換邊。

### 5.2 大致可以放心

- `[GOV-ENF-SHADOW-SUMMARY]` **每日一條**，`status=ok`，`exit_policy=preview_only`。
- **block rate 穩定**在約 **0.5–2%**（例如 ~700 筆里 ~7 筆 would_block ≈ 1%）。
- **ENF-RULE-1** 觸發集中於 `infra_risk` / `security:critical`；**ENF-RULE-2** 只在 `high_retry` + `retry_count≥2` 上 warn。
- **C3-05** 為 0 或極低（allow + infra_risk 的 L1 提示）。
- Samples 與人工預期的高風險場景一致（gate_fail_deny、有 error_type、風險 tag、trace score ≥ 0.7）。
- `runs loaded` 與觀測天數一致；`total records` 每日 ≥ ~30（理想接近 nightly limit）。

### 5.3 要小心

| 現象 | 可能原因 | 建議 |
|------|----------|------|
| `status=skipped` / `error_logged` | dryrun 缺失、wrapper 異常 | 先修 pipeline，暫不解讀 rate |
| block rate **單日暴增**（如 1% → 10%+） | infra 事故、新 service、rule 過敏 | 查 Samples + 當日 shadow batch |
| block rate **持續攀升**數日 | 真實風險上升或 rule 太寬 | 開票調查；**不**在此時討論 blocking |
| would_block 出現在**預期外的 tags** | false positive 風險 | 人工抽檢 samples，回報 policy-mining |
| **正常 case** 大量 would_block | rule 條件可能過寬 | 延長 shadow；勿開 canary |
| ENF-RULE-2 / C3-05 **短期暴增** | 重試風暴、infra_risk allow 增多 | 查後端 / 基礎設施，與 L2 blocking 分開處理 |
| `runs loaded` **少於**預期天數 | nightly 失敗或未存 log | 修 CI 排程或 log 留存 |
| `total records` **過低**（如 < 30/run） | 取樣失敗 | 查 `[SHADOW-PIPELINE]` 是否 fallback fixture |

---

## 6. ENF-RULE-1 / C3-05 現況（高階摘要 · L1 視角）

> 以下為 shadow 觀測的**保守描述**，不是 blocking 批准書。

### ENF-RULE-1（L2 候選 · would_block）

**觸發條件（摘要）**：`dryrun_rule=gate_fail_deny` + `error_type` 非空 + tags 含 `infra_risk` 或 `security:critical` + `trace_completeness_score ≥ 0.7`（nightly `--min-score 0.7`）。

**觀測傾向**：

- would_block **幾乎全部**來自 ENF-RULE-1；ENF-RULE-2 只產生 warn。
- 在累積樣本中，block rate **約 1% 量級**（例：~700 筆 per-record 中 ~7 筆 would_block）時，屬可接受 shadow 基線；须用 analyzer 對**自己的 log 窗口**重算，勿硬套單次數字。
- Samples 傾向 **`infra_risk`**（timeout、crash、healthcheck 類 `error_type`）與少量 **`security:critical`**，與「高風險 gate_fail_deny」直覺一致。
- **仍不足以下結論**：false positive 率已驗證、跨月穩定、或 min_score=0.7 已 sensitivity 調參。需更多 nightly + 人工抽檢 samples。

### C3-05-L1-INFRA-RISK-SUCCESS（L1 · would_warn）

**觸發條件（摘要）**：record 為 **allow/pass** + tags 含 **`infra_risk`**，且**不是**已 deny 的 gate_fail_deny case。

**觀測傾向**：

- 獨立於 ENF-RULE-1/2；只印 `[ENF-WARN]`，計入 summary 的 `C3-05-L1-INFRA-RISK-SUCCESS.would_warn`。
- 正常 shadow 期 often **0 或很低**；若連續升高，表示「帶 infra_risk 標籤卻 allow 通過」的 case 變多，值得查基礎設施品質，**不等同**於可以 block。

### 一句話

ENF-RULE-1 目前**看起來**咬在合理的高風險 pattern 上；C3-05 提供互補 L1 訊號。**兩者都仍需更多 nightly 觀察**，本階段只做記錄與判讀，不做 blocking。

---

## 7. Escalation Criteria（何時可「考慮」blocking）

以下為**建議啟動下一張 BLOCKING-CRITERIA 類 plan** 的原則門檻，**不是**本文件對 blocking 的定義或批准。

可考慮**提議**開票，當**全部**大致成立：

1. **連續觀測 ≥ 2 週**（nightly summary 穩定產出，非斷斷續續）。
2. **block rate 穩定**：窗口內日間波動小（例如大多落在 0.5–2%，無連續 spike）。
3. **dominant pattern 收斂**：ENF-RULE-1 的 samples ≥80% 落在 1–2 種已知高風險組合（gate_fail_deny + infra_risk/security:critical + 少數 error_type）。
4. **低誤攔迹象**：人工抽檢 ≥10 條 would_block samples，≥80% 認定「若真 blocking 也合理」。
5. **資料品質 OK**：`total records` 每日充足、少 skip/error。
6. **L1 規則無失控**：ENF-RULE-2 / C3-05 無未解釋的暴量（避免 L2/L1 混亂）。

**應延長 shadow、勿提 blocking 的情況**

- pattern 分散、rate 波動大、抽檢通過率低、summary 常 skip、樣本天數不足。
- 任何「先開 canary 試試」——须走 **尚書省 / governance** 與獨立 BLOCKING-CRITERIA 票，**不在值班範圍內自行改 env**。

---

## 8. Non-Goals

本指南**明確不做**：

| Non-goal | 說明 |
|----------|------|
| 不定義正式 blocking policy | threshold、rollback、審批鏈屬未來 BLOCKING-CRITERIA 票 |
| 不指示修改 CI env 或開啟 blocking | 含 `GOV_ENF_BLOCKING_CANARY=1`、workflow env 變更 |
| 不定義 / 不修改 rule 內部邏輯 | min_score、tags、dryrun_rule 條件以 `tools/enf_preview_wrapper.py` 為準；本文件只教「讀」 |
| 不取代 governance 裁決 | escalation 條件僅供「是否該開下一張票」參考 |
| 不修改任何程式 / workflow / config | 本票 doc-only |

---

## Appendix A — 每日 / 每週 checklist

**每日**

```
[ ] eval-shadow-nightly 成功
[ ] 存在 [GOV-ENF-SHADOW-SUMMARY] 且 status=ok
[ ] [ENF] config 顯示 GOV_ENF_BLOCKING_CANARY=0 (shadow-only)
[ ] 當日 would_block 與前日相比無異常 spike
```

**每週**

```
[ ] analyzer 聚合 ≥5 日 summary
[ ] 記錄 block rate + ENF-RULE-1/2/C3-05 計數
[ ] 更新 Samples dominant pattern 筆記
[ ] 若有 anomaly，開 issue / 票追踪（非改 env）
```

---

## Appendix B — 相關檔案索引（唯讀引用）

| 路徑 | 角色 |
|------|------|
| `tools/enf_preview_wrapper.py` | Shadow 引擎；產出 summary |
| `tools/analyze_enf_shadow_summaries.py` | 跨 run 聚合報表 |
| `tools/tail_enf_preview_logs.py` | Log / dryrun tail |
| `tools/print_enf_env.py` | Env 唯讀查詢 |
| `observability/enf_config.py` | ENF flag 解析 |
| `observability/enf-preview/README.md` | Preview 層簡介 |
| `.github/workflows/eval-gate-ci.yml` | nightly ENF step 所在 workflow |
| `tests/fixtures/enf/shadow_summaries_sample.log` | Analyzer 練習用 fixture（含 spike） |

---

*版本：Phase 2 shadow-only 值班指南 · 不具 blocking 授權效力*
