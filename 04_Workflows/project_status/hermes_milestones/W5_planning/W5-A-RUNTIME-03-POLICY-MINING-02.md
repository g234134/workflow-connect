# W5-A-RUNTIME-03-POLICY-MINING-02 — 第二輪 enforcement 規則挖掘報告

> **票號**：W5-A-RUNTIME-03-POLICY-MINING-02
> **分析日期**：2026-05-31
> **源頭資料**：RUNTIME-01 dry-run per-record JSONL（3 次執行，合計 16 筆記錄，8 unique task_ids）
> **對齊**：W5-A-RUNTIME-03-LIMITED-DENY_plan.md §2（Enforceability Ladder）
> **硬邊界**：本報告僅提供建議與統計；不宣告任何 rule 已升級 L2。真正提升決策留給後續 POLICY-SELECTION-02 或 LIMITED-BLOCKING_plan。
> **與 MINING-01 的關係**：MINING-01（N=13, 8 unique）建議等待多次 nightly 再做第二輪。本報告確認資料尚未累積，暫無新結論。

---

## 1) 資料盤點

### 1.1 可用 per-record JSONL 清單

| # | 時間戳 | per_record path | summary | 記錄數 | 來源 artefact | 是否新增於 MINING-01 之後 |
|---|--------|----------------|---------|--------|---------------|--------------------------|
| 1 | `20260530T185213Z` | `observability/dryrun/20260530T185213Z_per_record.jsonl` | MD | 8 | shadow_eval_results + smoke_eval_results + ibridge | 已在 MINING-01 |
| 2 | `20260530T210035Z` | `observability/dryrun/20260530T210035Z_per_record.jsonl` | MD | 5 | shadow_ibridge_records only | 已在 MINING-01 |
| 3 | `20260530T213707Z` | `observability/dryrun/20260530T213707Z_per_record.jsonl` | MD | 3 | eval_export_sample.jsonl | 新增，但全是 **已見過** 的 record |

### 1.2 [GOV-ENF-PREVIEW] 保存狀況

| 項 | 現況 |
|----|------|
| **README** | `observability/enf-preview/README.md` 存在，定義 ENF-RULE-1/2 條件與輸出格式 |
| **wrapper** | `tools/enf_preview_wrapper.py` 存在，已可在本地執行，永遠 exit 0 |
| **實際 log 保存** | **無** — enf-preview 目錄下僅有 README，無任何輸出 artefact |
| **CI log 匯出** | 未找到已匯出的 CI log 檔案（無 `*GOV-ENF-PREVIEW*` 檔名） |
| **本地實測輸出** | 見下列 §2，所有 3 個 per_record JSONL 均已實測 |

### 1.3 資料規模變化

```
MINING-01 (May 30):  2 runs, 13 records, 8 unique task_ids
MINING-02 (May 31):  3 runs, 16 records, 8 unique task_ids ← 無成長
```

**關鍵事實**：第 3 個 run（213707Z）讀取 `eval_export_sample.jsonl`，產出 3 筆記錄（t-healthy, t-infra, t-retry），**全部已在 185213Z 中見過**。3 次執行均發生在同一天（2026-05-30），非多個 nightly CI 週期。

**資料缺口仍與 MINING-01 完全相同**：

| 缺口 | 狀態 |
|------|------|
| 缺少 score < 0.875 的記錄 | ❌ 仍無任何記錄 |
| 缺少 edge_unknown 記錄 | ❌ 仍無任何記錄 |
| N=8 unique | ❌ 無增長 |
| 100% match ratio | ❌ 可能反映語料偏誤 |
| 無 PR workflow 資料 | ❌ 未改變 |
| **無真正 nightly CI 資料** | ❌ **所有資料均來自 smoke fixture** |

---

## 2) ENF-RULE-1/2 聚合統計

### 2.1 ENF-RULE-1（L2 候選：`gate_fail_deny + error_type + risk tag + score ≥ 0.7`）

#### 跨 run 結果

| per_record JSONL | total records | would_block | would_warn | would_noop | ENF-RULE-1 block |
|-----------------|---------------|-------------|------------|------------|------------------|
| 20260530T185213Z | 8 | 1 | 2 | 5 | t-infra |
| 20260530T210035Z | 5 | 0 | 1 | 4 | (t-infra not in input) |
| 20260530T213707Z | 3 | 1 | 1 | 1 | t-infra |

**ENF-RULE-1 統計**：

| 指標 | 值 |
|------|-----|
| Unique matching records | 1 (t-infra) |
| Multi-run consistency | would_block=1 in 2/2 runs where record present |
| True positives | 1 (t-infra: timeout + infra_risk → deny) |
| False positives | **0** |
| FP rate | 0% (但 N=1，極不顯著) |
| gate_fail_deny family coverage | 100% (唯一 gate_fail_deny 記錄即被覆蓋) |
| Score threshold | 0.95 (遠高於 min_score=0.7) |

**判定**：ENF-RULE-1 在所有 run 中 0 FP。但樣本數 N=1 使得 FP 率無法做統計推論。規則本身條件 binary，**結構上仍適合 L2**，但「0 FP」的結論在目前資料規模下是脆弱的。

#### 與 MINING-01 的變化

| 項目 | MINING-01 | MINING-02 | 變化 |
|------|-----------|-----------|------|
| 獨特記錄數 | 1 (t-infra) | 1 (t-infra) | 無變化 |
| 跨 run 一致性 | 2 runs | 3 runs, 2/2 一致 | ✅ 每 run 一致 |
| FP 率 | 0% | 0% | 不變 |
| 信心水準 | 低 (N=1) | 仍低 (N=1) | **未改善** |

### 2.2 ENF-RULE-2（L1 觀察：`gate_fail_needs_review + high_retry + retry_count ≥ 2`）

#### 跨 run 結果

| per_record JSONL | would_warn | ENF-RULE-2 records |
|-----------------|------------|-------------------|
| 20260530T185213Z | 2 | shadow-retry, t-retry |
| 20260530T210035Z | 1 | shadow-retry (t-retry not in input) |
| 20260530T213707Z | 1 | t-retry (shadow-retry not in input) |

**ENF-RULE-2 統計**：

| 指標 | 值 |
|------|-----|
| Unique matching records | 2 (shadow-retry, t-retry) |
| Multi-run consistency | 100% — every run that includes the record produces the expected `warn` |
| True positives | 2 (ideal=warn, actual=warn) |
| False positives | 0 |
| gate_fail_needs_review coverage | 100% (2/2 records match) |
| **L2 path** | **無** — per plan §2.3, `needs_review` bucket 永不進 L2 |

**判定**：ENF-RULE-2 穩定，適合作為 L1 advisory warning。不應考慮提升到 L2。若後續需要增強，可考慮加 score 閾值細分 warn 強度（例如 t-retry score=0.9 < shadow-retry score=1.0）。

#### 與 MINING-01 的變化

| 項目 | MINING-01 | MINING-02 | 變化 |
|------|-----------|-----------|------|
| 獨特記錄數 | 2 | 2 | 無變化 |
| 跨 run 一致性 | 2 runs | 3 runs | ✅ 每 run 一致 |
| L2 path | 無 | 無 | 不變 |

---

## 3) 新 pattern 探索

### 3.1 所有可能的組合檢查

| 候選 # | 描述 | 資料 | 判定 |
|--------|------|------|------|
| **C2-01** | `gate_ok_score_low` (score < 0.875) | 0 筆 — 從未觸發 | ❌ 無法判定。需更多資料 |
| **C2-02** | `edge_unknown` | 0 筆 — 從未觸發 | ❌ 無法判定。應先診斷資料缺失原因 |
| **C2-03** | `gate_fail_deny` + error_type 非 null（移除 risk tag 條件） | 1 筆（與 ENF-RULE-1 相同） | ❌ 被 ENF-RULE-1 子集覆蓋。保留 risk tag 是正確的安全閘門 |
| **C2-04** | `gate_fail_needs_review` + `high_retry` + score < 0.95 (僅 t-retry, score=0.9) | 1 筆（t-retry） | ⚠️ 僅建議 L1 增強（區分 high/low confidence warn），不進 L2 |
| **C2-05** | `success=false` + `gate_result=pass`（靜默失敗） | 0 筆 | ❌ 無資料 — 所有 pass 記錄的 success=true |

### 3.2 關鍵發現

1. **無新的 L2 候選規則** — 在全部 8 個 unique `task_id` 中，ENF-RULE-1 和 ENF-RULE-2 已覆蓋所有非 trivial 記錄。沒有任何未被覆蓋的 `ideal=deny` 記錄或 `actual=fail` 記錄。
2. **Score 邊界（0.875）完全未測試** — 所有記錄的 score 都在 0.9 以上。`gate_ok_score_low` 規則（score < 0.875）從未被觸發，無法評估其行為。
3. **edge_unknown 無資料** — 所有記錄均有完整欄位。無法評估 fallback 行為。

---

## 4) 更新後的 Candidate 規則表（相對於 MINING-01 的 C-01~C-06）

### 4.1 完整候選清單（MINING-01 + 本輪）

| 編號 | 描述 | 層級 | 變化 | 判定 |
|------|------|------|------|------|
| **ENF-RULE-1** (原 C-01) | `gate_fail_deny + error_type + infra_risk + score≥0.7` | **L2 候選** | ✅ 3 run 一致，0 FP | **仍適合作 L2 候選**，但 N=1 信心不足 |
| **ENF-RULE-2** (原 C-03) | `gate_fail_needs_review + high_retry + retry≥2` | **L1 觀察** | ✅ 3 run 一致，0 FP | 不進 L2（per plan §2.3） |
| **C-02** (MINING-01) | `gate_fail_deny + success=false`（不限 error_type） | L2 候選 | 與 ENF-RULE-1 重疊 | 子集，不另列 |
| **C-04** | score in [0.875, 0.92) | 無法判定 | 仍無資料 | ❌ |
| **C-05** | score in [0.92, 1.0] | 非 L2 | 不變 | ❌ |
| **C-06** | `edge_unknown` | 無法判定 | 仍無資料 | ❌ |
| **C2-01** | `gate_ok_score_low` | 無法判定 | 新嘗試，無資料 | ❌ |
| **C2-03** | deny+error only （無 risk tag） | 與 RULE-1 重疊 | 子集 | ❌ |
| **C2-04** | warn + score<0.95 | L1 增強 | 僅 t-retry | ⚠️ 可選 L1 |

### 4.2 強 L2 候選（重申 MINING-01 結論）

僅 **ENF-RULE-1** 仍然維持。無新 L2 候選。

---

## 5) 建議下一步

### 5.1 即期阻礙：資料不足

**MINING-02 無法定義任何新規則，也無法實質提升對 ENF-RULE-1 的信心。** 根本原因：

1. **所有資料來自 smoke fixture** — 3 次執行均為本地人為產生，非真實 nightly CI 累積。
2. **N=8 unique 不夠** — 無人見過 score<0.875 的記錄，無人見過 edge_unknown，無人見過 verdict_mismatch。
3. **ENF-RULE-1 的「0 FP」脆弱** — N=1 的 0% FP 率在真實 CI 資料中可能完全不成立。

### 5.2 具體行動方案

#### 選項 A（推薦）：先讓 nightly CI 真正累積資料

| # | 行動 | 預期效果 |
|---|------|---------|
| 1 | 確認 nightly CI 的 `eval-shadow-nightly` job 成功執行 7+ 次 | 累積真實資料（非 smoke fixture） |
| 2 | 確認 dryrun step 在每個 nightly 成功產出 per_record JSONL | 累積跨天 baseline |
| 3 | 確認 enf-preview step 穩定輸出 `[GOV-ENF-PREVIEW]` log 行 | 累積 preview 證據 |
| 4 | 在本機架 cron：每日自動收集 dryrun JSONL 到 archive 目錄 | 建立分析資料集 |
| 5 | 待 N_unqiue ≥ 30-50 再做第三輪 mining | 足夠統計基礎 |

#### 選項 B（可並行）：增加 edge case fixture

| # | 行動 | 預期效果 |
|---|------|---------|
| 6 | 在 eval_export_sample.jsonl 中加入 score=0.7、score=0.5 的記錄 | 測試 `gate_ok_score_low` 的行為 |
| 7 | 加入缺少 task_id/score 的記錄 | 測試 `edge_unknown` 的 fallback |
| 8 | 加入 `gate_result=pass` 但 `success=false` 的記錄 | 測試 silent failure 模式 |

### 5.3 ENF-RULE-1 能否直接進 blocking 試點？

**建議：暫緩。** 雖然 ENF-RULE-1 結構上完美，但：

| 考慮因素 | 風險 | 緩解 |
|---------|------|------|
| N=1 unique record | 若 infra_risk tag 產生邏輯有變，可能 FP | 先在 Phase A preview 再多觀察幾次 nightly |
| 唯一命中是 smoke fixture | 可能不反映真實 CI 語料 | 等真實 nightly 資料出現 |
| 無其他 deny 記錄 | 可能 gate_fail_deny 在真實 world 從未被觸發 | 或一旦觸發就是真的，但無法確認 |

**推薦門檻**：ENF-RULE-1 進 Phase B blocking 試點前，應滿足：
- 至少 **5 次 nightly CI** 中有本規則的 preview 記錄
- 其中至少 **1 條**非 smoke-fixture 的真實 per-minute / per-request 記錄
- FP count = 0（或 ≤1 且已人工確認可接受）
- kill-switch 已部署並驗證過（可另開 LIMITED-BLOCKING_plan 票處理 kill-switch 實作）

### 5.4 對後續票的建議

| 票 | 建議 |
|----|------|
| **POLICY-SELECTION-02** | 暫無新規則可選。應先界定「資料達標門檻」與「FP 率接受閾值」 |
| **LIMITED-BLOCKING_plan** | 可開始設計 kill-switch 與 override 機制，但先不綁定具體 rule |
| **IMPLEMENTATION-01** | 若 LIMITED-BLOCKING_plan 已定位，先實作 kill-switch + CI step 結構，rule 條件留 config variable |

---

## 附錄 A — 原始資料摘要

### 8 個 unique 記錄（跨 3 個 per-record JSONL 去重後）

| task_id | dryrun_rule | ideal | actual | score | tags/error | retry | 出現於 |
|---------|------------|-------|--------|-------|------------|-------|--------|
| prod-shadow-9469a97892-k2 | gate_ok_score_high | allow | allow | 1.0 | — | 0 | 185Z, 210Z |
| shadow-greeting | gate_ok_score_high | allow | allow | 1.0 | — | 0 | 185Z, 210Z |
| shadow-k2-flow-1 | gate_ok_score_high | allow | allow | 0.95 | — | 0 | 185Z, 210Z |
| shadow-merge-2 | gate_ok_score_high | allow | allow | 0.92 | — | 0 | 185Z, 210Z |
| shadow-retry | gate_fail_needs_review | warn | warn | 1.0 | high_retry | 2 | 185Z, 210Z |
| t-healthy | gate_ok_score_high | allow | allow | 0.95 | — | 0 | 185Z, 213Z |
| t-infra | gate_fail_deny | deny | fail | 0.95 | infra_risk + timeout | 0 | 185Z, 213Z |
| t-retry | gate_fail_needs_review | warn | warn | 0.9 | high_retry | 2 | 185Z, 213Z |

### ENF-RULE-1 跨 run 打點追蹤

| per_record JSONL | ENF-RULE-1 would_block | 規則判定 | CID |
|-----------------|----------------------|---------|-----|
| 20260530T185213Z | 1 (t-infra) | ✅ | 2/2 runs host |
| 20260530T210035Z | 0 (no t-infra) | ✅ no-op | — |
| 20260530T213707Z | 1 (t-infra) | ✅ | 2/2 runs host |

### ENF-RULE-2 跨 run 打點追蹤

| per_record JSONL | ENF-RULE-2 would_warn | 規則判定 |
|-----------------|----------------------|---------|
| 20260530T185213Z | 2 (shadow-retry, t-retry) | ✅ |
| 20260530T210035Z | 1 (shadow-retry) | ✅ (t-retry not present) |
| 20260530T213707Z | 1 (t-retry) | ✅ (shadow-retry not present) |

---

## 附錄 B — 與 W5-A-RUNTIME-03-LIMITED-DENY_plan.md 的對齊

| Plan 段落 | 本報告對應 | 狀態 |
|----------|-----------|------|
| §2.1 Enforceability Ladder (L0/L1/L2) | §3 Candidate 規則表 | 已對齊 |
| §2.2 L2 具體條件（binary判定、≥N週期、FP<X%、明確action） | §5.3 | ENF-RULE-1 滿足 binary + 明確 action；N 和 FP 信心不足 |
| §2.3 明確排除（needs_review, unknown, allow） | §3 C2-04、C2-02 | 已遵循 |
| §3.1 Phase A 退出條件 | §5.3 | 建議 ≥5 nightly + ≥1 真實記錄 + 0 FP |
| AC-ENF-6（Phase A 觀察期證據） | §5.2 | 資料尚未滿足 |
| POLICY-SELECTION 票（獨立票，與本報告正交） | §5.4 | 建議先界定資料准入門檻 |

---

## 附錄 C — 版本歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.1 | 2026-05-31 | W5-A-POLICY-MINING-02 | 基於 3 個 per_record JSONL 的第二輪 mining。確認 ENF-RULE-1 (0 FP/3 runs)、ENF-RULE-2 (0 FP/3 runs)。無新 L2 候選。建議先累積真實 nightly 資料再做第三輪。 |
