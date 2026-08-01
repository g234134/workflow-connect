# W5-A-RUNTIME-03-POLICY-MINING-03 — 第三輪 policy mining（首批真實 shadow 樣本）

> **票號**：W5-A-RUNTIME-03-POLICY-MINING-03
> **分析日期**：2026-05-31
> **源頭資料**：shadow_batch_20260530.jsonl（6 條記錄，其中 2 條為真實 prod-shadow）→ CI pipeline（ibridge → dryrun → enf_preview）
> **對齊**：W5-A-RUNTIME-03-LIMITED-DENY_plan.md §2（Enforceability Ladder）
> **硬邊界**：僅 workspace 分析報告，不修改 repo。不在此決定 blocking，僅提供建議與統計支撐。

---

## 1. 概述（Objectives & Context）

### 1.1 背景

- **CI Data Pipeline v0** 已上線（W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-01）。eval-shadow-nightly 優先消費 `artifacts/eval/shadow_batch_*.jsonl`（`mode=shadow`），無 batch 時 fallback fixture（`mode=fixture`）。
- **初始 shadow 批次**（`shadow_batch_20260530.jsonl`）包含 6 條記錄：4 條 fixture（shadow-k2-flow-1, shadow-merge-2, shadow-greeting, shadow-retry）＋2 條**真實 prod-shadow 記錄**（prod-shadow-9469a97892-k2, prod-shadow-1bab7f91d5-k2）。
- **真實 prod-shadow 記錄的特征**：k2_summary.ok=true + k2_summary.tags=["infra_risk"] + k2_merge.gate_result="needs_review" + k2_merge.k2_eval_tags=["infra_risk"]。ask pipeline 實際失敗（health_node: healthcheck failed），但 k2 層成功。
- **前三輪（MINING-01／MINING-02）限制**：僅基於 smoke fixture（4 條固定記錄）。MINING-02 明確建議「等真實 nightly 資料累積至 N≥30–50 再做第三輪」。本輪首次加入真實 prod-shadow 記錄。

### 1.2 本輪目標

1. ENF-RULE-1 在真實樣本下是否仍然「幾乎沒有 FP」？
2. 是否出現實質 FN（infra_risk success cases 應被視為 risk？）？
3. ENF-RULE-2 在真實樣本裡是否仍只適合 L1？
4. 是否有新 pattern 值得作為 L2/L1 候選？
5. 對 limited blocking canary 的具體建議。

---

## 2. 資料集描述（Dataset）

### 2.1 分析的 shadow 批次

本輪分析使用了 **5 個 dryrun run**（均由 CI pipeline 產出），覆蓋 3 組不同的輸入資料：

| 批次標識 | per_record JSONL | 記錄數 | 資料來源 | 內容說明 |
|---------|-----------------|--------|---------|---------|
| A | 20260530T185213Z | 8 | shadow_eval_results + smoke_eval_results + ibridge | 全量 — 4 fixture + 2 prod-shadow + 3 smoke(t/t-infra/t-retry) |
| B | 20260530T210035Z | 5 | shadow_ibridge_records only | ibridge only：4 fixture + 1 prod-shadow-9469 |
| C | 20260530T213707Z | 3 | eval_export_sample.jsonl | smoke only：t-healthy/t-infra/t-retry（全是已見過的） |
| D | 20260530T220600Z | 6 | shadow_ibridge_records.latest.jsonl | 最新：4 fixture + 2 prod-shadow（新增 1bab7f91d5） |
| E | 20260530T220615Z | 4 | shadow_ibridge_records.latest.jsonl | 最新子集：4 fixture only（prod-shadow 未出現） |

### 2.2 總規模

| 指標 | 值 |
|------|-----|
| **跨 run 總記錄數** | 26（去重前） |
| **Unique task_ids** | **9** |
| **Fixture-only 唯一記錄** | 7（shadow-k2-flow-1, shadow-merge-2, shadow-greeting, shadow-retry, t-healthy, t-infra, t-retry） |
| **真實 prod-shadow 記錄** | **2**（prod-shadow-9469a97892-k2, prod-shadow-1bab7f91d5-k2） |
| **不同批次數** | 3 種不同輸入（A=全量, B/D/E=ibridge only, C=smoke only） |
| **跨 run 一致性** | 相同 task_id 跨 run 分類一致：100% |

### 2.3 Fixture vs Shadow 比例

| 類別 | Unique 記錄數 | 佔比 |
|------|-------------|------|
| Smoke fixture（t-*） | 3 | 33.3% |
| K2 shadow fixture（shadow-*） | 4 | 44.4% |
| **真實 prod-shadow（prod-shadow-*）** | **2** | **22.2%** |
| **合計** | **9** | **100%** |

### 2.4 限制（本輪資料缺口仍存在）

| 缺口 | 現況 | 影響 |
|------|------|------|
| score < 0.875 的記錄 | **0 筆** | 無從評估 gate_ok_score_low 或低分 threshold |
| edge_unknown 記錄 | **0 筆** | 無從評估 unknown fallback |
| ENF-RULE-1 命中在真實記錄（非 fixture） | **0 筆** | 唯一命中 t-infra 為 smoke fixture |
| N_unique=9（含 2 真實） | 仍遠低於 30-50 | 統計信心極有限 |
| 僅單日資料（2026-05-30） | 所有 dryrun 同一天 | 無跨日 drift 評估 |

---

## 3. ENF-RULE-1 分析（L2 候選，重點章節）

### 3.1 規則條件回顧

**ENF-RULE-1**（來自 POLCY-MINING-01 C-01）：
- `dryrun_rule == "gate_fail_deny"`
- `error_type` 非 null
- 風險 tag 存在（`infra_risk` / `security:critical`）
- `trace_completeness_score >= 0.7`

### 3.2 跨 run 統計

| per_record JSONL | total | would_block | ENF-RULE-1 命中的 task_id | 同一記錄跨 run 一致性 |
|-----------------|-------|-------------|--------------------------|---------------------|
| 185213Z (全量) | 8 | **1** | t-infra | 僅此 run |
| 210035Z (ibridge) | 5 | **0** | — | t-infra 不存在於輸入 |
| 213707Z (smoke) | 3 | **1** | t-infra | ✅ 一致 |
| 220600Z (ibridge, latest) | 6 | **0** | — | t-infra 不存在於輸入 |
| 220615Z (ibridge, subset) | 4 | **0** | — | t-infra 不存在於輸入 |

**跨 run 統計**：

| 指標 | 值 |
|------|-----|
| Unique matching records | **1**（t-infra） |
| 跨 run 一致性 | ✅ 所有包含 t-infra 的 run 都正確 block |
| 真實 positive（合理應 deny） | 1（timeout + infra_risk → deny） |
| **False Positive** | **0**（N=1，脆弱） |
| FP 率 | 0%（統計不顯著） |
| 真實記錄命中 | **0**（t-infra 是 smoke fixture） |

**結論**：ENF-RULE-1 在 5/5 run 中 0 FP。但**唯一命中 t-infra 是 smoke fixture**，不是真實記錄。規則條件本身 binary，結構上仍適合作 L2 候選，但「0 FP」的結論仍然脆弱。

### 3.3 灰區案例分析：infra_risk + success=true + 無 error_type

#### 3.3.1 原始資料（shadow_batch_20260530.jsonl L5/L6）

| 欄位 | prod-shadow-9469a97892-k2 | prod-shadow-1bab7f91d5-k2 |
|------|--------------------------|--------------------------|
| **k2_summary.ok** | true | true |
| **k2_summary.status** | success | success |
| **k2_summary.tags** | ["infra_risk"] | ["infra_risk"] |
| **k2_summary.error_type** | null | null |
| **k2_summary.retry_count** | 1 | 0 |
| **ask_summary.ok** | false | false |
| **ask_summary.status** | fail | fail |
| **ask_summary.error_type** | "health_node: healthcheck failed" | "health_node: healthcheck failed" |
| **k2_merge.gate_result** | needs_review | needs_review |
| **k2_merge.k2_eval_tags** | ["infra_risk"] | ["infra_risk"] |

#### 3.3.2 經 ibridge→dryrun 後的 dryrun 結果

| dryrun 欄位 | prod-shadow-9469a97892-k2 | prod-shadow-1bab7f91d5-k2 |
|-----------|--------------------------|--------------------------|
| dryrun_rule | gate_ok_score_high | gate_ok_score_high |
| ideal_verdict | allow | allow |
| actual_verdict | allow | allow |
| tags | **[]**（已清空） | **[]**（已清空） |
| error_type | None | None |
| success | true | true |
| score | 1.0 | 1.0 |
| **ENF-RULE-1 命中？** | **否** | **否** |
| **ENF-RULE-2 命中？** | **否** | **否** |

#### 3.3.3 根因：ibridge normalization 遺漏風險 tag

`_k2_summary_to_ibridge()`（ibridge_exporter.py L238-248）在建構 flat ibridge record 時 **沒有傳遞 `tags`**。`k2_summary.tags=["infra_risk"]` 和 `k2_merge.k2_eval_tags=["infra_risk"]` 在 `normalize_shadow_record` → `_k2_summary_to_ibridge` 路徑中被完全丟失。

這是一個**資料豐富度缺口（data enrichment gap）**，不是規則邏輯問題。

#### 3.3.4 判定：這是否構成 false negative？

**綜合判定：目前不算 FN，但存在資料失真的風險。**

| 考量 | 說明 |
|------|------|
| ENF-RULE-1 的條件邏輯 | 要求 `gate_fail_deny` + error_type + risk tag。這兩條記錄在 dryrun 層級是 `gate_ok_score_high`（allow），根本不在規則的適用範圍。這不是規則選擇性忽略，而是資料前置處理丟失了觸發所需的欄位。 |
| 是否應該被視為 risk？ | **是**。原始資料顯示 k2 merge gate_result=needs_review + k2_eval_tags=["infra_risk"]，代表系統本身已將這些記錄標記為需審閱。ask pipeline 實際失敗（health_node error）。這些記錄確實有風險訊號。 |
| 修復順位 | **ibridge pipeline 先修**（補 `tags` 傳遞），再觀察修復後的 ENF-RULE-1 行為。在原圖標籤被丟棄的情況下，不適合用來決定規則是否該改。 |
| 是否需要一條 L1 警示替代？ | **建議加入 C3-01**（見 §5.1）：當 raw shadow 包含 `infra_risk` 標籤但 ibridge 產出遺漏時，印一條 L1 示警。這不需要改變 ENF-RULE-1 的條件。 |

### 3.4 ENF-RULE-1 結論

**結論：B — 暫不建議進 blocking，維持強 L2 候選。**

#### 結論細節

| 選項 | 是否建議 | 理由 |
|------|---------|------|
| **A. 建議進 limited blocking canary** | ❌ 暫不 | 唯一命中是 smoke fixture；真實 infra_risk 記錄因 pipeline 缺口無法被規則捕捉；無法驗證規則在真實 world 的行為。 |
| **B. 維持強 L2 候選** | ✅ 是 | 0 FP/5 run，條件 binary；t-infra 記錄在規則下確實應該 deny。結構上仍完美。 |
| **C. 需回退/調整條件** | ❌ 否 | 規則條件本身不需調整。需要修的是 ibridge pipeline 的 tag 傳遞，不是規則邏輯。 |

---

## 4. ENF-RULE-2 與其他既有規則

### 4.1 ENF-RULE-2 跨 run 統計

**ENF-RULE-2**（L1 觀察：`gate_fail_needs_review + high_retry + retry_count ≥ 2`）

| per_record JSONL | total | would_warn | 命中的 task_ids | 一致性 |
|-----------------|-------|-----------|----------------|--------|
| 185213Z (全量) | 8 | 2 | shadow-retry, t-retry | ✅ |
| 210035Z (ibridge) | 5 | 1 | shadow-retry | ✅ (t-retry 不存在) |
| 213707Z (smoke) | 3 | 1 | t-retry | ✅ (shadow-retry 不存在) |
| 220600Z (ibridge, latest) | 6 | 1 | shadow-retry | ✅ (t-retry 不存在) |
| 220615Z (ibridge, subset) | 4 | 1 | shadow-retry | ✅ |

| 指標 | 值 |
|------|-----|
| Unique matching records | **2**（shadow-retry, t-retry） |
| 跨 run 一致性 | 100% — 每個包含該記錄的 run 都正確 warn |
| True positives | 2（ideal=warn, actual=warn） |
| False positives | 0 |
| 真實記錄命中 | shadow-retry 是 fixture（但 high_retry tag 為真實語意） |
| L2 path | 不適用 — per plan §2.3 needs_review 永不進 L2 |

**判定**：ENF-RULE-2 穩定、0 FP、適合作為 L1 advisory warning。**不應考慮提升到 L2**。

### 4.2 既有規則 — 無其他已定義的 L0/L1

目前僅 ENF-RULE-1（L2 候選）和 ENF-RULE-2（L1 觀察）在 enf_preview_wrapper.py 中實現。無其他既有規則可供分析。本輪未發現需新增的 L0 規則。

---

## 5. 新候選規則探索（C3-xx）

### 5.1 C3-01：ibridge 遺漏風險 tag 的 L1 警示

| 項目 | 內容 |
|------|------|
| **規則條件** | 在 `observability.shadow_pipeline` 中，當 `normalize_shadow_record()` 處理 `k2_summary` 或 `k2_merge` 數據且原始資料包含風險 tag（如 `infra_risk`, `security:critical`）但 flat ibridge 輸出不含時，印一條 L1 結構化日誌。 |
| **建議層級** | **L1（advisory warning）** — 非 blocking，僅警示 pipeline 資料遺失。 |
| **樣本觀察** | 2/2 prod-shadow 記錄受影響（shadow_batch L5/L6）。影響率 100%（在所有包含 prod-shadow 的 dryrun 中）。 |
| **觸發位置** | `ibridge_exporter.py` 的 `_k2_summary_to_ibridge` 輸出後或 `normalize_shadow_record` 中。 |
| **備註** | 本規則不是 enforcement 規則，而是**資料完整性監控**。修復 pipeline tag 傳遞後本規則可降級或移除。 |

### 5.2 C3-02：gate_fail_needs_review + 任何 risk tag（不限 high_retry）

| 項目 | 內容 |
|------|------|
| **規則條件** | `dryrun_rule == gate_fail_needs_review` + 任一已知風險 tag 存在（如 `infra_risk`）+ `gate_result == needs_review`。 |
| **建議層級** | **暫不建議** — 目前無實際樣本。prod-shadow 記錄的 risk tag 在 dryrun 層已被清除，post-fix 後才可驗證。 |
| **樣本觀察** | 0 筆（port-pipeline-fix）。 |
| **備註** | 待 ibridge tag 修復後再評估。此模式可能覆蓋 ENF-RULE-1 目前的灰區。 |

### 5.3 C3-03：gate_ok_score_high + 實際失敗（success=false）

| 項目 | 內容 |
|------|------|
| **規則條件** | `dryrun_rule == gate_ok_score_high` + `metrics.success == false`。 |
| **建議層級** | **無法判定** — 所有 gate_ok_score_high 記錄的 success=true。0 筆樣本。 |
| **樣本觀察** | 0 筆。 |
| **備註** | 若未來出現此 pattern，可能代表 gate 分類錯誤。但目前無資料支持。 |

### 5.4 C3-04：Prod-shadow 中 ask pipeline 失敗但 k2 成功（多層級日誌）

| 項目 | 內容 |
|------|------|
| **規則條件** | `raw shadow data` 中 `ask_summary.ok == false` 但 `k2_summary.ok == true`，且 `k2_merge.gate_result == needs_review`。 |
| **建議層級** | **暫不建議作為 enforcement** — 建議在 `shadow_pipeline` 中增加一條 L0 observability 日誌（不影響打分）。 |
| **樣本觀察** | 2/2 prod-shadow 記錄。 |
| **備註** | 此 pattern 本身不代表 k2 層應被 deny，但若持續出現，可能是 ask-health 監控的信號。應由 runtime monitoring 而非 enforcement 處理。 |

### 5.5 新候選匯總

| 編號 | 描述 | 層級 | 樣本數 | 建議 |
|------|------|------|--------|------|
| **C3-01** | Ibriage 遺漏風險 tag 的 L1 警示 | **L1** | 2/2 prod-shadow | ✅ 建議在 ibridge_exporter 中實作資料完整性監控 |
| **C3-02** | needs_review + 任意 risk tag | ⚠️ 待定 | 0（post-fix 後評估） | ❌ 暫不建議，先修 ibridge tag 傳遞 |
| **C3-03** | gate_ok_score_high + success=false | ❌ 無法判定 | 0 | ❌ 無資料 |
| **C3-04** | ask fail + k2 ok + needs_review | **L0** 可選 | 2/2 prod-shadow | ⚠️ 僅 L0 observability，不進 enforcement |

---

## 6. 對 Limited Blocking Canary 的建議

### 6.1 是否以 ENF-RULE-1 作為第一批 canary blocking 規則？

**建議：目前不建議將 ENF-RULE-1 進入任何 blocking canary。**

#### 原因

| 阻礙 | 詳細說明 |
|------|---------|
| **無真實命中** | ENF-RULE-1 的唯一命中是 smoke fixture（t-infra）。無法確認其在真實 world 中有任何正樣本。 |
| **資料 pipeline 缺口** | 真實 infra_risk 記錄因 ibridge tag 遺漏而不進入規則。在修復 pipeline 前，無法評估規則對真實記錄的 FP/FN。 |
| **N 仍然太小** | Unique record 數從 MINING-02 的 8 增加到 9（僅 +1，新增的是 prod-shadow-1bab7f91d5-k2，但它在 dryrun 中是 allow，對規則無幫助）。 |
| **無跨日資料** | 所有 dryrun 來自同一天。無法評估跨日 drift 對規則行為的影響。 |

#### 如果仍要推進 blocking（替代方案）

若尚書省因時程壓力必須推進 blocking canary，建議附加以下條件：

| 條件 | 說明 |
|------|------|
| **限特定 workflow** | 僅在 eval-shadow-nightly（非 PR CI）中啟用，且設 `continue-on-error: true`。 |
| **常駐 kill-switch** | env var `ENF_RULE_1_BLOCKING_ENABLED=0`（預設關閉）。手動設為 1 才啟用。 |
| **限定 blocking 範圍** | 在 Phase A（preview）模式下再觀察至少 **7 次 nightly**。僅在確認 0 FP + ≥1 真實命中後才考慮進 Phase B。 |
| **先修 ibridge pipeline** | 在啟用 blocking **之前**修復 `_k2_summary_to_ibridge` 的 tag 遺漏問題，確保真實記錄能被規則評估。 |

### 6.2 ENF-RULE-1 進 canary 的推薦門檻（沿用 MINING-02）

1. ✅ **Fix ibridge tag propagation** — 讓真實 infra_risk 記錄可以正確被 ENF-RULE-1 評估。
2. ✅ **≥7 次 nightly CI** 中有本規則的 preview 記錄（非僅 0/7）。
3. ✅ **≥1 條**真實（非 fixture）記錄被本規則判定為 would_block。
4. ✅ **FP count ≤ 1**（可人工確認）。
5. ✅ **Kill-switch 已部署並驗證**。

### 6.3 對後續票的建議

| 票 | 建議 |
|----|------|
| **LIMITED-BLOCKING-PLAN-ADDENDUM** | 優先修復 ibridge tag 遺漏（`_k2_summary_to_ibridge` 補傳 `tags`）。設定 blocking canary 的具體啟用條件、kill-switch 行為、回退程序。 |
| **LIMITED-BLOCKING_BRIEF_FOR_CURSOR** | 說明 ENF-RULE-1 目前不準備 blocking。如果啓動，將在 ibridge fix + 7-nightly 觀察期後以特定 workflow + kill-switch 形式啟動。 |
| **後續 MINING**（如 MINING-04） | 在 ibridge tag 修復後重新收集 ≥7 nightly 的真實資料，重新評估 ENF-RULE-1 在真實記錄上的表現，以及 C3-02 是否值得進 L2。 |

---

## 附錄 A — Unique 記錄完整表

| task_id | dryrun_rule | ideal | actual | score | tags | error_type | success | retry | ENF 分類 | 來源 |
|---------|------------|-------|--------|-------|------|-----------|---------|-------|---------|------|
| prod-shadow-9469a97892-k2 | gate_ok_score_high | allow | allow | 1.0 | [] | None | True | 1 | noop | **真實 prod-shadow** |
| prod-shadow-1bab7f91d5-k2 | gate_ok_score_high | allow | allow | 1.0 | [] | None | True | 0 | noop | **真實 prod-shadow** |
| shadow-greeting | gate_ok_score_high | allow | allow | 1.0 | [] | None | True | 0 | noop | K2 fixture |
| shadow-k2-flow-1 | gate_ok_score_high | allow | allow | 0.95 | [] | None | True | 0 | noop | K2 fixture |
| shadow-merge-2 | gate_ok_score_high | allow | allow | 0.92 | [] | None | True | 0 | noop | K2 fixture |
| shadow-retry | gate_fail_needs_review | warn | warn | 1.0 | [high_retry] | None | True | 2 | **WARN-R2** | K2 fixture |
| t-healthy | gate_ok_score_high | allow | allow | 0.95 | [] | None | True | 0 | noop | smoke fixture |
| **t-infra** | **gate_fail_deny** | **deny** | **fail** | **0.95** | **[infra_risk]** | **timeout** | **False** | **0** | **BLOCK-R1** | smoke fixture |
| t-retry | gate_fail_needs_review | warn | warn | 0.90 | [high_retry] | None | True | 2 | **WARN-R2** | smoke fixture |

---

## 附錄 B — 跨 run 分類一致性

| task_id | 出現次數 | 分類 | 一致性 |
|---------|---------|------|--------|
| prod-shadow-9469a97892-k2 | 3/5 run | gate_ok_score_high/allow | ✅ |
| prod-shadow-1bab7f91d5-k2 | 1/5 run | gate_ok_score_high/allow | ✅ |
| shadow-retry | 4/5 run | gate_fail_needs_review/warn (R2) | ✅ |
| t-infra | 2/5 run | gate_fail_deny/deny (R1) | ✅ |
| t-retry | 2/5 run | gate_fail_needs_review/warn (R2) | ✅ |

所有跨 run 重複的記錄分類均一致。**無跨 run drift**。

---

## 附錄 C — 與 MINING-01/02 的變遷對照

| 指標 | MINING-01 | MINING-02 | MINING-03（本輪） | 變化 |
|------|-----------|-----------|-------------------|------|
| dryrun runs | 2 | 3 | **5** | +2 |
| Unique task_ids | 8 | 8 | **9** | +1 |
| 真實記錄（非 fixture） | 0 | 0 | **2** | ✅ 首批 |
| ENF-RULE-1 FP | 0 (N=1) | 0 (N=1) | 0 (N=1) | 不變 |
| ENF-RULE-1 真實命中 | 0 | 0 | **0** | 無變化 |
| ENF-RULE-2 FP | 0 (N=2) | 0 (N=2) | 0 (N=2) | 不變 |
| score<0.875 記錄 | 0 | 0 | 0 | 缺口未填 |
| edge_unknown 記錄 | 0 | 0 | 0 | 缺口未填 |
| 新 L2 候選 | 0 | 0 | **0** | 無新 L2 |
| **Data pipeline 缺口發現** | — | — | **ibridge tag 遺漏** | 本輪新發現 |

---

## 附錄 D — Ibriage tag 遺漏技術說明

### 問題位置

`observability/ibridge_exporter.py` → `_k2_summary_to_ibridge()`（L238-248）

### 問題

```python
record: dict[str, Any] = {
    "task_id": str(task_id),
    "trace_id": str(trace_id),
    "agent_name": "k2_shadow",
    "success": bool(ok_val),
    "retry_count": summary.get("retry_count", 0),
    "handoff_count": summary.get("handoff_count", 0),
    "error_type": summary.get("error_type"),
    "context_token_usage": ...,
    "trace_completeness": ...,
}
```

**缺少 `tags` 欄位**。`k2_summary.tags`（如 `["infra_risk"]`）未被傳遞到 flat output。

### 後續影響

- `shadow_ibridge_records.latest.jsonl` 中的 prod-shadow 記錄沒有 `tags` 欄位
- 經 `tools.dryrun.core` 處理後，per_record 中的 `tags=[]`
- ENF-RULE-1 無法觸發（缺少 risk tag）

### 修復建議

在 `_k2_summary_to_ibridge` 的 output dict 中加入：

```python
if summary.get("tags"):
    record["tags"] = list(summary["tags"])
```

（屬於 ibridge_exporter 的 PR，不影響本報告的票）

---

## 附錄 E — 版本歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.1 | 2026-05-31 | W5-A-POLICY-MINING-03 | 基於 5 個 dryrun run 的第三輪 mining。首批真實 prod-shadow 樣本（2 條）。ENF-RULE-1 維持強 L2 候選（0 FP/5 run）但暫不建議進 blocking。發現 ibridge tag 遺漏（C3-01）。無新 L2 候選。 |
