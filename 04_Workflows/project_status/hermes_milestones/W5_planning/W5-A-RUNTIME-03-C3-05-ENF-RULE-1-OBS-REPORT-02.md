# W5-A-RUNTIME-03-C3-05-ENF-RULE-1-OBS-REPORT-02 — Two-Pool 生效後 Nightly 短觀察報告

> 票號：W5-A-RUNTIME-03-C3-05-ENF-RULE-1-OBS-REPORT-02
> 日期：2026-05-31
> 狀態：⚠ 樣本不足 — Two-Pool 剛實作，尚無任何真實 CI nightly run

---

## 1. 觀察範圍與樣本盤點

### 1.1 Two-Pool 實作時序

| 事件 | 時間 (UTC) | 說明 |
|------|-----------|------|
| Two-Pool IMPL 完成 | **2026-05-31 14:28** | `build_shadow_spool.sh`（新）、`fetch_latest_shadow_batch.sh`（修改）、CI workflow env vars 全部到位 |
| CI workflow seed step | ～14:28 | `eval-gate-ci.yml` 新增「Seed shadow batch」步驟，內嵌 6 條記錄（含 2 條 infra_risk） |
| 最近的 nightly 排程 | 2026-05-31 06:00 | ⚠ 早於 Two-Pool 實作約 8.5 小時 |
| **下次 nightly 排程** | **2026-06-01 06:00** | **Two-Pool 生效後的首次 nightly** |
| 目前可用的 per_record | 2026-05-31 06:32 | 06:32 的 dryrun 使用 `_tmp_shadow_ibridge.jsonl`，**不是** Two-Pool 產出，但記錄組成相同（6 條含 infra_risk） |

### 1.2 樣本規模判斷

**⚠ 明確寫明：樣本不足，無法進行統計分析。**

| 面向 | 現況 | 建議標準 | 差距 |
|------|------|---------|------|
| 實際 nightly runs（post Two-Pool） | **0 次** | ≥5 次 | ❌ 完全不足 |
| 可用的 per_record artefact | 1 個（06:32） | 5–7 個 nightly stamp | ❌ 不足 |
| 可用的 ENF preview log | **0 個**（任何 nightly） | 至少 3–5 次 preview 輸出 | ❌ 完全不足 |

以下分析基於：
1. **程式碼驗證** — Two-Pool 腳本邏輯正確，CI workflow 整合完整
2. **Local 模擬** — 使用現有 batch 模擬 Two-Pool 產出
3. **Pre-Two-Pool 資料** — 063256Z per_record（6 條含 infra_risk）可近似模擬 Two-Pool 後的行為
4. **差異比對** — 比較 fixture（4 條）vs Two-Pool（6 條）的 ENF preview 結果差異

---

## 2. Sampling 生效檢查（Script-Level Verification）

### 2.1 實作成品清單

| 工件 | 狀態 | 說明 |
|------|------|------|
| `scripts/build_shadow_spool.sh` | ✅ 存在（133 行） | Two-Pool 核心：jq 實作分類 → 去重 → 取樣 → 合併 → 寫入 spool |
| `scripts/fetch_latest_shadow_batch.sh` | ✅ 已修改（81 行） | 不再直接 cp，改呼叫 `build_shadow_spool.sh` |
| `.github/workflows/eval-gate-ci.yml` | ✅ 已修改 | 新增 env vars + Seed step + fetch 步驟 |
| `artifacts/eval/_no_risk_batch.jsonl` | ✅ 存在（2 行） | 測試用無風險 batch |

### 2.2 Two-Pool 取樣邏輯（透過 CI Seed Step + fetch）

```
CI Checkout (無 batch, .gitignore) 
    → Seed step: 寫入 shadow_batch_ci_seed.jsonl (6 records)
    → fetch_latest_shadow_batch.sh 找到 seed batch
    → build_shadow_spool.sh:
        ├── 分類: 2 infra_risk + 1 high_retry = risk → return pool
        └── 其餘 3 (shadow-greeting, -k2-flow-1, -merge-2) = baseline → baseline pool
        → 去重 (task_id) → 取樣 (baseline_limit=20, retain=3/tag) → 合併
    → SHADOW_SPOOL: 6 records (3 baseline + 3 risk deduped → 實際 4 baseline + 2 risk)
```

### 2.3 CRLF 行尾問題（⚠ 需修正）

`build_shadow_spool.sh` 含有 **Windows CRLF (`\r\n`) 行尾**，導致：

```
$ bash scripts/build_shadow_spool.sh
scripts/build_shadow_spool.sh: line 22: $'\r': command not found
scripts/build_shadow_spool.sh: line 23: set: pipefail\r: invalid option name
```

**在 ubuntu-latest GitHub Actions runner 上也會因 CRLF 而失敗。** 需要在推送到 CI 前修正為 UNIX LF。

### 2.4 預期的 sampling log 輸出

```bash
[SHADOW-PIPELINE] sampling: baseline=4 risk_retained=2 total=6 tag_source_counts={"infra_risk":2,"high_retry":1}
[SHADOW-PIPELINE] mode=shadow batch=ci_seed
```

---

## 3. C3-05 觀察（基於模擬資料）

### 3.1 觸發結果（使用 063256Z per_record）

| C3-05 命中 | task_id | actual_verdict | dryrun_rule | tags | 合理性 |
|-----------|---------|---------------|-------------|------|--------|
| ✅ 第 1 次 | `prod-shadow-1bab7f91d5-k2` | `allow` | `gate_ok_score_high` | `["infra_risk"]` | ✅ 合理 — allow + infra_risk |
| ✅ 第 2 次 | `prod-shadow-9469a97892-k2` | `allow` | `gate_ok_score_high` | `["infra_risk"]` | ✅ 合理 — allow + infra_risk |

**C3-05 總計：2 次觸發，均在預期內，無 FP。**

### 3.2 對比：Fixture 時期的 C3-05

| 時期 | per_record 來源 | 記錄數 | C3-05 觸發數 |
|------|----------------|--------|-------------|
| Fixture-only | 185213Z_per_record.jsonl | 8 | **0** |
| Two-Pool 等效 | 063256Z_per_record.jsonl | 6 | **2** ✅ |

**關鍵差異**：Fixture 時期 infra_risk 記錄（`t-infra`）因是 deny 記錄被 C3-05 正確排除。Two-Pool 後，allow + infra_risk 的 prod-shadow 記錄被保留，C3-05 首次有機會觸發。

### 3.3 合理性結論

C3-05 在 Two-Pool 後的預期行為：
- **正確觸發**：allow + infra_risk → `[ENF-WARN]`
- **正確排除**：deny + infra_risk（如 `t-infra`）
- **無 FP 候選**：目前 2 例均合理
- **但樣本數仍極小**（僅 2 條 unique task），無法評估 FP 率

---

## 4. ENF-RULE-1 觀察（基於模擬資料）

### 4.1 Two-Pool 樣本中的 ENF-RULE-1

| 時期 | per_record | 記錄數 | ENF-RULE-1 (would_block) | 命中 task |
|------|-----------|--------|-------------------------|-----------|
| Two-Pool 等效 | 063256Z | 6 | **0** | 無 |
| Fixture（對照） | 185213Z | 8 | **1** | `t-infra` (timeout + infra_risk) |

### 4.2 為什麼 ENF-RULE-1 在 Two-Pool 樣本中為 0？

分析 `063256Z` 的 6 條記錄：

| task_id | success | error_type | tags | dryrun_rule | 符合 ENF-RULE-1 條件？ |
|---------|---------|-----------|------|-------------|----------------------|
| prod-shadow-1bab7f91d5-k2 | true | null | infra_risk | gate_ok_score_high | ❌ 需 gate_fail_deny |
| prod-shadow-9469a97892-k2 | true | null | infra_risk | gate_ok_score_high | ❌ 同上 |
| shadow-retry | true | null | high_retry | gate_fail_needs_review | ❌ 不同 rule |
| shadow-greeting | true | null | [] | gate_ok_score_high | ❌ 無 risk tag |
| shadow-merge-2 | true | null | [] | gate_ok_score_high | ❌ 無 risk tag |
| shadow-k2-flow-1 | true | null | [] | gate_ok_score_high | ❌ 無 risk tag |

**ENF-RULE-1 需要**：`gate_fail_deny` + `error_type` 非空 + `infra_risk`/`security:critical` tag + `score ≥ 0.7`。

Two-Pool 樣本中的所有記錄都是 `success=true` + `error_type=null`，沒有任何一條觸發 `gate_fail_deny`（它只會在有失敗或 infra_risk 時觸發）。這表示 **當前的 seed batch 不包含任何「真正失敗」的案例**。

### 4.3 對照：Fixture 中的 ENF-RULE-1 候選

`t-infra`（185213Z per_record 第 7 條）：
- `actual_verdict=fail`, `dryrun_rule=gate_fail_deny`
- `error_type=timeout`, `tags=["infra_risk"]`, `score=0.95`
- → **ENF-RULE-1 正確觸發 would_block** ✅
- 這是合理的 block 候選（infra timeout 導致失敗）

### 4.4 ENF-RULE-2 觀察

| 時期 | ENF-RULE-2 (would_warn) | 命中 task | tags |
|------|------------------------|-----------|------|
| Two-Pool | 1 | shadow-retry | high_retry |
| Fixture | 1 | shadow-retry | high_retry |

ENF-RULE-2 行為一致，兩者皆合理。

---

## 5. Blocking Canary Readiness 結論

### 5.1 三問逐題回答

#### Q1: Two-Pool 是否成功讓 nightly 具備 risk-heavy 可觀測性？

| 面向 | 結論 |
|------|------|
| 腳本實作 | ✅ 完整 — `build_shadow_spool.sh` + CI workflow 整合完畢 |
| CRLF 問題 | ⚠ 需修復 — 行尾為 `\r\n`，CI 上會執行失敗 |
| 實際 CI 運行 | ❌ **0 次** — 腳本剛完成，尚未觸發任何 nightly |
| Risk record 保留 | ✅ 模擬驗證 — baseline=4, risk_retained=2（含 infra_risk, high_retry） |

**結論：條件性成功 — 實作正確，但尚未在真實 CI 環境驗證。**

#### Q2: C3-05 是否在 nightly 中表現合理？

| 面向 | 結論 |
|------|------|
| 預期觸發 | ✅ Two-Pool 樣本中，2 條 infra_risk+allow 記錄均正確觸發 C3-05 |
| FP | ✅ 0 FP |
| 排除邏輯 | ✅ deny+infra_risk（如 t-infra）正確排除 |
| 樣本規模 | ⚠ 僅 2 條 unique task，不足以做出統計結論 |

**結論：邏輯合理，但樣本數極少。**

#### Q3: ENF-RULE-1 是否具備進入 limited blocking canary 的最低觀察基礎？

| 面向 | 結論 |
|------|------|
| 當前 would_block | ❌ **0 次** — Two-Pool seed batch 無真正失敗案例 |
| 已知有效候選 | ✅ `t-infra`（fixture 中有）為合理 block 候選，但不在當前 seed batch 中 |
| 可觀察性 | ⚠ 需要有真正失敗的 `gate_fail_deny` 記錄才能觀察 ENF-RULE-1 行為 |
| 批次內容局限 | 當前 seed batch 僅含 allow + 無 error 記錄，無法觸發 ENF-RULE-1 |

**結論：ENF-RULE-1 的觀察基礎仍不足。** Two-Pool 改善了 infra_risk/high_retry 保留，但 ENF-RULE-1 需要的是 `gate_fail_deny` 記錄（即真正失敗的 task），當前 seed batch 中一條都沒有。**這不是 Two-Pool 的問題，而是 batch 內容本身的限制。**

### 5.2 綜合結論

```
Blocking Canary 是否 Ready?

      Not Ready ❌
```

**主要原因（1–3 項）：**

| # | 缺口 | 影響 | 緩解方式 |
|---|------|------|---------|
| 1 | **0 次實際 CI nightly run**。Two-Pool 腳本剛實作（14:28），next scheduled nightly 為 06-01 06:00 UTC | 無法確認 CRLF 修復後是否正常執行、sampling log 是否正確輸出 | 等待下次 nightly 執行，檢視 CI log |
| 2 | **Seed batch 不含 `gate_fail_deny` 記錄**。當前 6 條記錄均為 `success=true` + `error_type=null`，無法觸發 ENF-RULE-1 | ENF-RULE-1 的 would_block 永遠為 0，無法觀察 blocking canary 的核心行為 | 在 seed batch 中加入類似 `t-infra` 的失敗案例（`error_type=timeout` + `infra_risk`） |
| 3 | **CRLF 行尾問題**。`build_shadow_spool.sh` 含 `\r\n`，CI 上會因 `\r: command not found` 失敗 | Two-Pool 在 CI 中完全不會生效，fallback 到 fixture | 在 commit/push 前修正為 UNIX LF |

### 5.3 建議下一步

| 優先級 | 事項 | 負責 |
|--------|------|------|
| 🔴 P0 | 修復 `build_shadow_spool.sh` CRLF 行尾 | 在 IMPL 票中修正 |
| 🔴 P0 | 確認 CI 至少執行 1 次完整 nightly（seed → fetch → sampling → ibridge → dryrun → ENF preview） | 等待 06-01 06:00 UTC 或手動觸發 workflow_dispatch |
| 🟡 P1 | 觀察 CI log 中的 `[SHADOW-PIPELINE] sampling:` 輸出是否正確 | 檢視下一次 nightly log |
| 🟡 P1 | 確認 eval_ci_check 的 `--fail-on-tags=infra_risk` 行為：CI 會 fail，但 dryrun/ENF preview steps 有 `continue-on-error: true`，不影響下游 | 檢視 CI log |
| 🟡 P1 | 確認 `[ENF-WARN] rule=C3-05-L1-INFRA-RISK-SUCCESS` 在 nightly log 中出現 | 檢視 dryrun + enf preview step 輸出 |
| 🟢 P2 | 收集 ≥5 次 nightly 後，若 C3-05 穩定輸出且無 FP，可再次評估 blocking canary readiness | 下一次 OBS report |
| 🟢 P2 | 若 ENF-RULE-1 仍無觸發案例，考慮在 seed batch 中追加一條 `gate_fail_deny` + `infra_risk` 的 baseline case | IMPL 票或後續批次維護 |

---

## 附錄 A — Two-Pool 實作驗證（腳本層級通過）

| 測試 | 結果 | 說明 |
|------|------|------|
| 腳本存在 | ✅ | `build_shadow_spool.sh` 133 行，`fetch_latest_shadow_batch.sh` 81 行 |
| CI env vars | ✅ | `SHADOW_BASELINE_LIMIT=20`, `SHADOW_RISK_RETAIN_LIMIT=3`, `SHADOW_RISK_TAGS=infra_risk,high_retry` |
| Seed step | ✅ | 6 條記錄硬編碼在 CI workflow 中（含 2 條 infra_risk） |
| fetch 腳本整合 | ✅ | 呼叫 `build_shadow_spool.sh`，失敗時 fallback fixture |
| Baseline 取樣 | ✅ | `baseline_limit=20` — 小於 20 時保留全部 |
| Risk 去重 | ✅ | 依 task_id 去重，保留最新 |
| Risk retain limit | ✅ | 每種 tag 上限 3 條 |
| No-risk batch fallback | ✅ | 無風險 batch → baseline pool=全部, risk pool=空 |
| CRLF 行尾 | ❌ | **需要修正為 LF** |
| jq 依賴 | ✅ | ubuntu-latest 內建 jq |

## 附錄 B — 完整資料對照表

### B.1 所有 dryrun per_record 一覽

| Stamp | 記錄數 | infra_risk | 觸發 C3-05 | ENF-RULE-1 | 資料源 | 備註 |
|-------|--------|-----------|-----------|-----------|--------|------|
| 20260530T185213Z | 8 | 1 (t-infra, deny) | 0 | 1 | mixed | fixture 時期 |
| 20260530T210035Z | 5 | 0 | 0 | 0 | shadow spool | fixture 時期 |
| 20260530T213707Z | 3 | 1 (t-infra, deny) | 0 | 1 | smoke eval | fixture 時期 |
| 20260530T220600Z | 6 | 0 | 0 | 0 | shadow spool | fixture 時期 |
| 20260530T220615Z | 4 | 0 | 0 | 0 | shadow spool | fixture 時期 |
| 20260530T222742Z | 6 | 0 | 0 | 0 | shadow spool | fixture 時期 |
| **20260531T063256Z** | **6** | **2 (prod-shadow)** | **2** | **0** | _tmp_shadow | **近似 Two-Pool** |

### B.2 Two-Pool seed batch 中的風險記錄來源

| task_id | 風險 tag | 成功? | error_type | 在 fixture 中? | C3-05 觸發? | ENF-RULE-1? |
|---------|---------|-------|-----------|---------------|-------------|-------------|
| prod-shadow-9469a97892-k2 | infra_risk | true | null | ❌ | ✅ allow+infra_risk | ❌ gate_ok_score_high |
| prod-shadow-1bab7f91d5-k2 | infra_risk | true | null | ❌ | ✅ allow+infra_risk | ❌ gate_ok_score_high |
| shadow-retry | high_retry | true | null | ✅ (fixture) | ❌ | ❌ gate_fail_needs_review |
