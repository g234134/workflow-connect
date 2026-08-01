# W5-A-RUNTIME-03-POLICY-MINING-03.1 — infra_risk 成功案例深度分析（tags 管線修復後）

> **票號**：W5-A-RUNTIME-03-POLICY-MINING-03.1
> **分析日期**：2026-05-31
> **前置條件驗證狀態**：
>   - ✅ W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01 / -IMPL：prod-shadow→ibridge 的 `tags` 欄位已可正確傳遞（`_ac2_shadow_ibridge.jsonl` 中 prod-shadow 記錄顯示 `"tags": ["infra_risk"]`）
>   - ✅ W5-A-RUNTIME-03-DRYRUN-K2-TAG-PRESERVE-01：dryrun/core.py `_normalize_export_row()` 已合併原始 ibridge tags 與 synthetic tags（`_dryrun_verify/20260531T030106Z_per_record.jsonl` 中 prod-shadow 記錄顯示 `"tags": ["infra_risk"]`）
>   - ⚠️ eval-shadow-nightly 已持續運行但收集到的真實 per_record 樣本量仍然有限
> **對齊**：W5-A-RUNTIME-03-POLICY-MINING-03.md（mining-03 結論建議在 tags 修復後重新評估）
> **硬邊界**：僅 workspace 分析報告，不修改 repo。不在此決定 blocking，僅提出 L1/L2 規則調整建議與數據依據。

---

## 1. 概覽（Overview）

### 1.1 目的

本輪 mining 的直接目的是：在 ibridge tag 傳遞與 dryrun tags 合併都已修復的前提下，重新聚焦分析 **infra_risk 成功案例**（即帶有 `infra_risk` tag 但 dryrun 判定為 allow/success 的記錄），回答三個關鍵問題：

1. 這些成功案例在真實 shadow 中實際長什麼樣？dryrun ideal/verdict/ENF 行為是什麼？
2. 是否存在合理的切點，新增一條 L1 warning 規則專門針對 infra_risk 成功案例，或調整 ENF-RULE-1 的前置條件讓某些案例有機會進 L2 blocking？
3. 目前樣本量（N=2 真實 infra_risk 成功案例）是否足夠支撐這些結論？

### 1.2 相對於 MINING-03 的新增觀測點

| 項目 | MINING-03（前輪） | MINING-03.1（本輪） | 變化 |
|------|------------------|---------------------|------|
| Ibriage tag 傳遞 | ❌ 遺漏（`_k2_summary_to_ibridge` 未傳 tags） | ✅ 已修復（`ac2_shadow_ibridge.jsonl` 含 tags） | 修復確認 |
| Dryrun tags 合併 | ❌ 未合併（per_record tags=[] 清空） | ✅ 已合併（_dryrun_verify 中 tags=["infra_risk"]） | 修復確認 |
| 可用 infra_risk 成功案例 | 2 筆但 tags 被清空 → 無從分析 | 2 筆且 tags 正確保留 | 可分析性提升 |
| 樣本總量 | N=9 unique（2 真實） | N=9 unique（2 真實） | 無新增 |
| 跨日資料 | 僅 2026-05-30 | 仍僅 2026-05-30 | 無新增 |

### 1.3 分析的資料來源

本輪分析使用了以下 post-fix 資料集：

| 資料集 | 路徑 | 記錄數 | 說明 |
|--------|------|--------|------|
| Ibriage output (post-fix) | `artifacts/eval/_ac2_shadow_ibridge.jsonl` | 6 | Ibriage 輸出，tags 已正確保留 |
| Dryrun verify (post-fix) | `artifacts/eval/_dryrun_verify/20260531T030106Z_per_record.jsonl` | 9 | 完整 dryrun 產出（含 smoke fixtures），tags 正確合併 |
| Dryrun AC2 (post-fix) | `artifacts/eval/_dryrun_ac2/20260531T030111Z_per_record.jsonl` | 6 | AC2 子集 dryrun，tags 正確合併 |
| Shadow ibridge records (latest) | `artifacts/eval/shadow_ibridge_records.latest.jsonl` | 6 | Ibriage 輸出（tags 已修復） |
| Shadow batch（原始輸入） | `artifacts/eval/shadow_batch_20260530.jsonl` | 6 | K2 raw shadow 資料，含原始 tags |

---

## 2. 樣本統計（Sample Statistics）

### 2.1 跨資料集的 risk tags 出現頻率

下表基於 **post-fix dryrun per_record**（`_dryrun_verify/20260531T030106Z`）的 9 條記錄：

| Risk Tag | 記錄數 | success=true | success=false | 來源 |
|----------|--------|-------------|--------------|------|
| **infra_risk** | **3** | **2**（prod-shadow 真實） | **1**（t-infra smoke fixture） | K2 summary + k2_merge |
| **high_retry** | **2** | **2**（shadow-retry fixture + t-retry smoke） | 0 | K2 summary |
| observability_gap | 0 | — | — | 未發現 |
| security:critical | 0 | — | — | 未發現 |

### 2.2 分層統計（按來源）

| 來源類別 | Unique 記錄 | infra_risk 出現 | infra_risk success | infra_risk deny |
|----------|-------------|----------------|-------------------|----------------|
| **真實 prod-shadow** | **2** | **2**（100%） | **2**（100%） | **0** |
| K2 shadow fixture | 4 | 0 | 0 | 0 |
| Smoke fixture | 3 | 1（t-infra） | 0 | 1（timeout） |
| **總計** | **9** | **3** | **2** | **1** |

### 2.3 infra_risk 記錄的跨資料集一致性

| task_id | 原始 tags（shadow_batch） | Ibriage tags（ac2） | Dryrun per_record tags（_dryrun_verify） | 一致性 |
|---------|--------------------------|---------------------|------------------------------------------|--------|
| prod-shadow-9469a97892-k2 | ["infra_risk"] | ["infra_risk"] | ["infra_risk"] | ✅ 全鏈路一致 |
| prod-shadow-1bab7f91d5-k2 | ["infra_risk"] | ["infra_risk"] | ["infra_risk"] | ✅ 全鏈路一致 |
| t-infra | N/A（smoke fixture） | N/A（smoke fixture） | ["infra_risk"] | ✅ 單步一致 |

**結論**：tags 管線修復已在全鏈路（shadow_batch → ibridge → dryrun → per_record）驗證通過。2/2 真實 infra_risk 記錄在 per_record 中的 tags 欄位正確反映原始值。**無資料遺失**。

### 2.4 主要限制（與 MINING-03 相同或更嚴峻）

| 限制 | 現況 | 影響 |
|------|------|------|
| **實時 infra_risk 成功樣本數** | **N=2**（仍遠低於 30-50 目標） | 統計信心極低；無法做 FP/FN 率估計 |
| **唯一來源** | 僅 2026-05-30 一批 nightly shadow | 無跨日 drift 評估、無變化趨勢 |
| **無 edge_unknown 案例** | 0 筆 | 無法評估 unknown fallback |
| **無 score < 0.875 案例** | 0 筆 | 無法評估低分 threshold |
| **infra_risk deny 案例** | 1（t-infra smoke fixture，非真實） | 真實 deny 模式依然未知 |

---

## 3. infra_risk 成功案例分析（Core Analysis）

### 3.1 受影響的真實記錄

兩條真實 prod-shadow 記錄在本輪中可直接分析（因 tags 已正確保留）。

#### 原始 K2 層資料（shadow_batch_20260530.jsonl L5-L6）

| 欄位 | prod-shadow-9469a97892-k2 | prod-shadow-1bab7f91d5-k2 |
|------|--------------------------|--------------------------|
| **k2_summary.ok** | true | true |
| **k2_summary.status** | success | success |
| **k2_summary.tags** | ["infra_risk"] | ["infra_risk"] |
| **k2_summary.error_type** | null | null |
| **k2_summary.retry_count** | 1 | 0 |
| **ask_summary.ok** | false | false |
| **ask_summary.error_type** | "health_node: healthcheck failed" | "health_node: healthcheck failed" |
| **k2_merge.gate_result** | needs_review | needs_review |
| **k2_merge.k2_eval_tags** | ["infra_risk"] | ["infra_risk"] |

#### Dryrun 層資料（_dryrun_verify，post-fix）

| Dryrun 欄位 | prod-shadow-9469a97892-k2 | prod-shadow-1bab7f91d5-k2 |
|-----------|--------------------------|--------------------------|
| **dryrun_rule** | gate_ok_score_high | gate_ok_score_high |
| **ideal_verdict** | allow | allow |
| **actual_verdict** | allow | allow |
| **verdict_match** | true | true |
| **gate_result** | pass | pass |
| **tags（per_record）** | **["infra_risk"]** ✅ | **["infra_risk"]** ✅ |
| **metrics.success** | true | true |
| **metrics.retry_count** | 1 | 0 |
| **metrics.error_type** | null | null |
| **metrics.trace_completeness_score** | 1.0 | 1.0 |

### 3.2 ENF 規則命中情況

| ENF 規則 | prod-shadow-9469a97892-k2 | prod-shadow-1bab7f91d5-k2 |
|----------|--------------------------|--------------------------|
| **ENF-RULE-1**（gate_fail_deny + error_type + risk tag） | **❌ 未命中** — gate_ok_score_high, error_type=null | **❌ 未命中** — 同上 |
| **ENF-RULE-2**（gate_fail_needs_review + high_retry + retry≥2） | **❌ 未命中** — gate_ok_score_high, high_retry not in tags | **❌ 未命中** — 同上 |
| **C3-01-IBRIDGE-TAG-LOSS**（MINING-03 提議） | **N/A** — Tags 已正確保留 | **N/A** — 同上 |

**關鍵行為總結**：
- 這兩條記錄在 dryrun 層被視為 **完全正常的高分 allow 記錄**
- ENF-RULE-1 的條件（gate_fail_deny + error_type 非 null）**與此 pattern 無關**
- 這是 MINING-03 描述過的 **灰區**：infra_risk 存在但 K2 成功完成

### 3.3 是否構成「潛在危險，但可接受」？

**綜合判定：是。這些記錄屬於「基礎設施被標記為風險狀態，但 K2 代理正常完成」的模式。**

| 分析維度 | 說明 |
|---------|------|
| **K2 代理行為** | K2 在 infra_risk 標記下仍成功完成。retry_count=1 的記錄曾重試一次後成功。這代表 K2 代理具有基礎設施 jitter 的容錯能力。 |
| **infra_risk tag 的語義** | 這不是 K2 推理錯誤，而是 K2 自身對其所處基礎設施的觀測（如資源緊張、網絡不穩）。標籤的語義是「注意基礎設施狀態」，不是「回答錯了」。 |
| **ask pipeline 失敗** | 這是獨立的健康檢查（health_node），不是 K2 請求失敗。ask pipeline 的失敗不應影響 K2 產出的乾跑分類。 |
| **score=1.0** | 信心分數最高。K2 對其回答的正確性有完全信心。 |
| **gate_result=pass** | 閘門判定為通過。這與 score 一致。 |
| **ENF-RULE-1 不命名的合理性** | 正確。如果只是因為基礎設施被標記風險而 deny 一條 score=1.0、gate=pass 的記錄，會產生明顯 FP。規則不命中不是缺陷。 |

### 3.4 是否有「其實應該被 deny」的案例？

**本輪樣本中無此案例。**

兩條記錄都是：
- K2 完成了任務（score=1.0, ok=true）
- 沒有 K2 層錯誤（error_type=null）
- 基礎設施風險被標記為 tags，但代理行為正常

要在 infra_risk 成功案例中找到「應該被 deny」的候選，需要以下條件之一在未來樣本中出現：
1. infra_risk + K2 層錯誤（error_type 非 null）+ 但 dryrun 誤判為 allow — 目前無此案例
2. infra_risk + 低 score + gate=needs_review + 但 dryrun 仍判 allow — 無低 score 案例
3. infra_risk + 多次重試（retry ≥ 3）+ 但 K2 仍然 allow — 目前 retry max=1

---

## 4. 規則建議（C3-xx Candidates）

### 4.1 C3-05-L1-INFRA-RISK-SUCCESS（✅ 建議 — L1 Warning）

| 項目 | 內容 |
|------|------|
| **規則 ID** | C3-05-L1-INFRA-RISK-SUCCESS |
| **層級** | **L1（advisory warning）** — 不改變 verdict，僅輸出結構化 warning |
| **條件** | `tags` 包含 `"infra_risk"`（或後續擴展為 any risk-level tag）+ `actual_verdict == "allow"` |
| **觸發位置** | `enf_preview_wrapper.py` 的 per_record 處理循環中，在 ENF-RULE-2 同層級 |
| **行為** | 當條件匹配時，在 enf_preview 輸出中加入 `warnings` 數組：`{"rule": "C3-05", "message": "infra_risk detected in successful record — review infrastructure state", "level": "L1"}` |
| **理想輸出** | per_record 輸出中新增 `enf_warnings: [{"rule": "C3-05", ...}]`，保持 `actual_verdict` / `ideal_verdict` 不變 |
| **樣本數** | 2/2 真實 prod-shadow 記錄（100% 符合條件） |
| **合理動機** | 這些記錄雖然 allow 正確，但 infra_risk tag 代表基礎設施有異常。L1 warning 讓操作員知道「有成功記錄但 infra 狀態 flagged」，可以主動檢查 infra 而不影響 K2 產出。 |
| **FP 風險** | **極低** — 不改變 verdict，僅附加 warning 欄位。即使 FP（infra_risk 標記本身有誤），也不影響生產。 |
| **實作需求** | 需在 enf_preview_wrapper.py 中新增 C3-05 規則評估。約 10-15 行邏輯。 |

#### 條件設計細節

```python
def rule_c3_05_infra_risk_success(record: dict) -> Optional[dict]:
    """C3-05: infra_risk in tags + allow → L1 warning (no verdict change)."""
    tags = record.get("tags", []) or []
    if "infra_risk" in tags and record.get("actual_verdict") == "allow":
        return {
            "rule": "C3-05",
            "message": "infra_risk detected in successful record",
            "level": "L1",
        }
    return None
```

### 4.2 C3-06-L1-INFRA-RISK-LOW-SCORE（❌ 暫不建議）

| 項目 | 內容 |
|------|------|
| **條件** | `infra_risk` in tags + score < 0.875 + actual_verdict == "allow" |
| **樣本數** | 0（目前無 score < 0.875 的 infra_risk 記錄） |
| **判斷** | **暫不建議**。雖然邏輯上合理（低分 + infra_risk 是更強的信號），但目前無任何樣本可驗證行為。 |
| **建議** | 延後至有樣本後再評估。 |

### 4.3 C3-07-L2-INFRA-RISK-ERROR（❌ 暫不建議 — 未來候選）

| 項目 | 內容 |
|------|------|
| **條件** | `infra_risk` in tags + `error_type` not null + `dryrun_rule == gate_ok_score_high` |
| **層級** | **L2（potential blocking candidate）** |
| **樣本數** | 0（無此組合樣本） |
| **判斷** | **暫不建議**。雖然邏輯上「infra_risk + actual error → 比純 tag 更強的信號」，但 ENF-RULE-1 已經涵蓋 gate_fail_deny + error_type 的情況。目前此組合未出現。 |
| **建議** | 如果未來出現此 pattern（K2 error 但 gate 給高分，如 gate 分類錯誤），可視為 ENF-RULE-1 的補強。 |

### 4.4 新候選匯總

| 編號 | 描述 | 層級 | 樣本數 | 建議 |
|------|------|------|--------|------|
| **C3-05-L1-INFRA-RISK-SUCCESS** | infra_risk tag + allow → L1 warning | **L1** | 2/2 真實 prod-shadow | ✅ **建議作為第一批 post-fix L1 規則實作** |
| **C3-06-L1-INFRA-RISK-LOW-SCORE** | infra_risk + score<0.875 + allow | L1 | 0 | ❌ 暫不建議，無樣本 |
| **C3-07-L2-INFRA-RISK-ERROR** | infra_risk + error_type + gate_ok | L2 | 0 | ❌ 暫不建議，無樣本 |

---

## 5. ENF-RULE-1 條件調整的可行性評估

### 5.1 現行條件回顧

**ENF-RULE-1**（來自 MINING-01 C-01）：
- `dryrun_rule == "gate_fail_deny"`
- `error_type` 非 null
- 風險 tag 存在（`infra_risk` / `security:critical`）
- `trace_completeness_score >= 0.7`

### 5.2 是否可放寬到「包含 infra_risk tag 即視為候選 deny」？

**建議：目前不宜調整。** 理由如下：

#### 核心分歧

infra_risk 成功案例（2/2 真實 prod-shadow）與 ENF-RULE-1 的目標模式有**質的差異**：

| 維度 | ENF-RULE-1 目標（t-infra 模式） | infra_risk 成功案例（prod-shadow 真實） |
|------|--------------------------------|---------------------------------|
| **dryrun_rule** | gate_fail_deny | gate_ok_score_high |
| **ideal_verdict** | deny | allow |
| **error_type** | "timeout"（非 null） | null |
| **success** | false | true |
| **score** | 0.95 | 1.0 |
| **infra_risk 含義** | 代理因 infra 問題而失敗 | 代理在風險 infra 中成功完成 |
| **規則命中** | 應 deny | 應 allow（加 warning） |

#### 量化風險

如果將 ENF-RULE-1 的條件放寬為：
- `"infra_risk" in tags` + `dryrun_rule in ["gate_fail_deny", "gate_ok_score_high"]`

則基於現有樣本的估算 FP 增加：

| 場景 | 現有命中 | 放寬後新增命中 | 新增 FP 風險 |
|------|---------|---------------|-------------|
| 僅 `infra_risk` tag + allow | 0 | 2（100% 的 prod-shadow infra_risk 記錄） | **極高** — 這些記錄明顯不應 deny |
| `infra_risk` + error_type + gate_ok | 0 | 0（無樣本） | 無法評估 |
| `infra_risk` + low score + gate_ok | 0 | 0（無樣本） | 無法評估 |

**結論**：僅僅因為有 `infra_risk` tag 就 block 一條 score=1.0、gate=pass 的成功記錄，會產生 **100% FP**。

### 5.3 是否有其他更安全的放寬路徑？

可能的放寬方向按風險排序：

| 方向 | 風險 | 建議 |
|------|------|------|
| 僅 L1 warning（C3-05） | 極低 ✅ | ✅ **建議** — 不改變 verdict |
| 放寬 gate_fail_deny 範圍（如加入 gate_fail_deny_low） | 低 | ⚠️ 樣本不足，無法評估 |
| infra_risk + error_type（不限 gate 分類） | 中 | ❌ 0 樣本 |
| infra_risk + 無條件 | 極高 | ❌ 會產生明顯 FP |

### 5.4 未來需要觀察的指標

若要最終決定 ENF-RULE-1 的條件調整，需要：

| 指標 | 所需條件 | 目前狀態 |
|------|---------|---------|
| 更多 infra_risk 成功案例 | N ≥ 30 | N=2 ❌ |
| infra_risk + error_type 的案例 | 至少出現 1 筆 | 0 ❌ |
| infra_risk + retry≥3 的案例 | 至少出現 1 筆 | 0 ❌ |
| 跨日資料中的 pattern 一致性 | ≥ 7 次 nightly CI | 1 次 nightly ❌ |
| C3-05 在更多記錄上的 performance | N ≥ 50 per_record | 9 ❌ |

---

## 6. 下一步建議

### 6.1 短期（本次報告後可直接執行的）

| 建議 | 優先級 | 關聯票 |
|------|--------|--------|
| **實作 C3-05-L1-INFRA-RISK-SUCCESS** — 在 enf_preview_wrapper.py 新增 L1 warning 規則 | **高** | 建議開 `W5-A-RUNTIME-03-C3-05-IMPL` |
| 繼續收集 nightly shadow 資料，累積真實 infra_risk 樣本 | 高 | 現有 CI pipeline 已自動收集 |
| 在 enf_preview 輸出中確認 C3-05 warning 的正確格式（`enf_warnings` 數組） | 中 | C3-05-IMPL 票的 subset |

### 6.2 中期（需更多資料後再決定）

| 建議 | 前提 | 關聯票 |
|------|------|--------|
| 重新評估 ENF-RULE-1 前置條件調整（如 error_type + infra_risk 組合） | 出現 ≥3 筆相關記錄 + N≥30 | `W5-A-RUNTIME-03-ENF-RULE-1-CONDITION-ADJUST-01` |
| 評估 C3-06（低分 + infra_risk） | 出現 score < 0.875 的 infra_risk 記錄 | 暫無票號 |
| 考慮 C3-05 的 tags 擴展（如加入 observability_gap, security:critical） | 出現至少 1 筆帶其他 risk tag 的成功案例 | 暫無票號 |

### 6.3 長期（如 C3-05 運行穩定後）

| 建議 | 前提 |
|------|------|
| 若 C3-05 在 ≥7 次 nightly 中 0 FP，可評估是否升級到 L2（blocking） | C3-05 運行穩定 + 確認 infra_risk 成功案例數量已足夠區分 L1/L2 邊界 |
| 建立「risk tag 目錄」：統一 infra_risk、high_retry、security:critical 等 tag 的語義與規則映射 | 更多風險標籤類型出現 |

### 6.4 局限性總結

> **本報告的最重要結論：樣本嚴重不足。** N=2 的真實 infra_risk 成功案例（全部從同一批 nightly 資料中收集）遠低於建議的 30-50 筆最低門檻。所有建議（尤其 L1/L2 候選與 ENF-RULE-1 調整可行性）都建立在極小樣本的觀察上，結論的統計顯著性有限。

| 已確認 | 尚待驗證 |
|--------|---------|
| Tags 管線修復運作正常，infra_risk 可正確傳遞到 per_record | C3-05 在更大量樣本上的 FP 率 |
| infra_risk 成功案例都是「K2 在風險基礎設施上成功完成」的模式 | ENF-RULE-1 條件調整的安全性 |
| C3-05 L1 warning 有合理動機且 0 樣本 FP | 其他 risk tag（observability_gap 等）的行為 |
| ENF-RULE-1 目前不宜放寬前置條件 | 跨日 drift 對 pattern 的影響 |

---

## 附錄 A — 完整 Unique 記錄表（Post-Fix）

基於 `_dryrun_verify/20260531T030106Z_per_record.jsonl`，包含 post-fix tags。

| task_id | dryrun_rule | ideal | actual | verdict_match | score | tags | error_type | success | ENF 命中 | 來源 |
|---------|------------|-------|--------|---------------|-------|------|-----------|---------|---------|------|
| prod-shadow-9469a97892-k2 | gate_ok_score_high | allow | allow | ✅ | 1.0 | **[infra_risk]** | null | ✅ | noop | **真實 prod-shadow** |
| prod-shadow-1bab7f91d5-k2 | gate_ok_score_high | allow | allow | ✅ | 1.0 | **[infra_risk]** | null | ✅ | noop | **真實 prod-shadow** |
| shadow-greeting | gate_ok_score_high | allow | allow | ✅ | 1.0 | [] | null | ✅ | noop | K2 fixture |
| shadow-k2-flow-1 | gate_ok_score_high | allow | allow | ✅ | 0.95 | [] | null | ✅ | noop | K2 fixture |
| shadow-merge-2 | gate_ok_score_high | allow | allow | ✅ | 0.92 | [] | null | ✅ | noop | K2 fixture |
| shadow-retry | gate_fail_needs_review | warn | warn | ✅ | 1.0 | [high_retry] | null | ✅ | **WARN-R2** (ENF-RULE-2) | K2 fixture |
| t-healthy | gate_ok_score_high | allow | allow | ✅ | 0.95 | [] | null | ✅ | noop | smoke fixture |
| **t-infra** | **gate_fail_deny** | **deny** | **fail** | ✅ | **0.95** | **[infra_risk]** | **timeout** | ❌ | **BLOCK-R1** (ENF-RULE-1) | smoke fixture |
| t-retry | gate_fail_needs_review | warn | warn | ✅ | 0.90 | [high_retry] | null | ✅ | **WARN-R2** (ENF-RULE-2) | smoke fixture |

## 附錄 B — Tags 管線修復前後對照

| task_id | 修復前 ibridge tags | 修復前 per_record tags | 修復後 ibridge tags | 修復後 per_record tags |
|---------|-------------------|----------------------|-------------------|----------------------|
| prod-shadow-9469a97892-k2 | 遺漏 | []（清空） | ["infra_risk"] ✅ | ["infra_risk"] ✅ |
| prod-shadow-1bab7f91d5-k2 | 遺漏 | []（清空） | ["infra_risk"] ✅ | ["infra_risk"] ✅ |
| shadow-retry | ["high_retry"] | ["high_retry"] | ["high_retry"] | ["high_retry"] |

## 附錄 C — 與 MINING-03 的變遷對照

| 指標 | MINING-03 | MINING-03.1（本輪） | 變化 |
|------|-----------|-------------------|------|
| dryrun runs | 5 | 2（post-fix）+ 5（pre-fix，參考） | -3（post-fix 新產出） |
| Unique task_ids | 9 | 9 | 相同 |
| 真實 prod-shadow 記錄 | 2 | 2 | 相同但不變 |
| infra_risk 成功案例 | 2（但 tags 清空，無法分析） | 2（tags 可分析） | ✅ 可分析性提升 |
| infra_risk 成功案例行為 | allow（推測） | gate_ok_score_high→allow（已確認） | ✅ 確認 |
| ENF-RULE-1 命中（真實） | 0（因 tags 遺漏） | 0（即使 tags 存在，條件不符） | ➡️ 確認非 pipeline 問題 |
| tag 遺漏 C3-01 | ✅ 建議實作 | ✅ 已修復，可降級或移除 | 修復完成 |
| C3-05 L1 warning | 不存在 | ✅ **新建議** | 新發現 |

## 附錄 D — 資料來源索引

| 資料 | 路徑 | 作為 |
|------|------|------|
| Shadow batch（原始） | `artifacts/eval/shadow_batch_20260530.jsonl` | 原始 K2 raw 輸入 |
| Ibriage output（ac2） | `artifacts/eval/_ac2_shadow_ibridge.jsonl` | Ibriage 輸出（post-fix） |
| Ibriage output（latest） | `artifacts/eval/shadow_ibridge_records.latest.jsonl` | Ibriage 輸出（post-fix，same data） |
| Dryrun verify（post-fix） | `artifacts/eval/_dryrun_verify/20260531T030106Z_per_record.jsonl` | 完整 per_record（含 smoke） |
| Dryrun AC2（post-fix） | `artifacts/eval/_dryrun_ac2/20260531T030111Z_per_record.jsonl` | AC2 per_record subset |
| 先前的 dryrun（pre-fix） | `observability/dryrun/20260530T*.jsonl` | 參考對照（pre-fix） |
| 前輪 mining 報告 | `milestones/W5_planning/W5-A-RUNTIME-03-POLICY-MINING-03.md` | 背景與假設 |

## 附錄 E — 版本歷史

| 版本 | 日期 | 變更說明 |
|------|------|---------|
| v0.1 | 2026-05-31 | 基於 post-fix per_record 的首版 infra_risk 深度分析。確認 tags 管線修復成功。N=2 infra_risk 成功案例為「K2 在風險 infra 上成功完成」模式。建議新增 C3-05 L1 warning 規則。ENF-RULE-1 前置條件調整不建議。樣本嚴重不足（N=2 vs 目標 30-50）。 |
