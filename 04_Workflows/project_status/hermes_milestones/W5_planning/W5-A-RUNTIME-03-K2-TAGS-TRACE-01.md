# W5-A-RUNTIME-03-K2-TAGS-TRACE-01 — K-2 / eval flow tags 來源與行為追蹤

> **票號**：W5-A-RUNTIME-03-K2-TAGS-TRACE-01
> **類型**：只讀分析報告（無程式碼修改）
> **依賴**：W5-A-RUNTIME-03-POLICY-MINING-03（發現源）→ W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01 v0.2（勘誤 ibridge 層）

---

## 1. 現況與動機

### 1.1 已知事實鏈

| 步驟 | 結論 | 來源 |
|------|------|------|
| MINING-03 觀察 | 真實 prod-shadow 有 2 條帶 `infra_risk` 訊號的記錄被分類為 allow/allow | W5-A-RUNTIME-03-POLICY-MINING-03 |
| IBRIDGE-TAG-FIX v0.2 勘誤 | ibridge_exporter 的 `_k2_summary_to_ibridge()` 和 `EXPORT_FIELD_NAMES` 均已正確傳遞 tags | W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01.md §1.1 |
| 本報告發現 | **真正斷點不在 ibridge_exporter，在 dryrun/core.py 的 `_normalize_export_row()`** | 本文件 §2 |

### 1.2 核心問題

> **為什麼 `shadow_batch_20260530.jsonl` 中 2 條 `k2_summary.tags=["infra_risk"]` 的 prod-shadow 記錄，最終被 ENF-RULE-1 分類為 `noop`？**

本報告完整追溯從 K-2 eval gate → k2_summary → ibridge JSONL → dryrun per_record → enf_preview 的全部 tags 變化。

---

## 2. 完整 Tags 流向（附真實資料驗證）

### 2.1 流向圖

```
K-2 LangGraph flow
  │
  ▼ [finalize_eval_node() → evaluate_task_record() → _RULES]
  │   - _rule_high_retry:  retry_count >= 2                  → tag "high_retry"
  │   - _rule_context_heavy: context_token_usage > 102400     → tag "context_heavy"
  │   - _rule_many_handoffs: handoff_count >= 3               → tag "many_handoffs"
  │   - _rule_infra_risk:    error_type in (context_overflow, timeout) → tag "infra_risk"
  │   - _rule_observability_gap: trace_completeness < 0.8     → tag "observability_gap"
  │
  │   eval_out = {"pass": bool, "tags": list[str], "reasons": list[str], ...}
  │   meta["eval_gate"] = eval_out
  │
  ▼ [run_k2_flow output]
  │   k2_out.eval_metadata.eval_gate.tags
  │
  ▼ [summarize_k2_output() — k2_ask_shadow.py:224]
  │   tags = _normalize_tags(eval_gate.get("tags"))          ✅
  │   + "reviewer_fallback" / "retrieve_retry"               ✅
  │   k2_summary["tags"] = tags                               ✅
  │
  ▼ [compare_shadow_profiles() — k2_ask_shadow.py:354]
  │   "k2_summary": dict(k2_summary)                          ✅
  │
  ▼ [_build_spool_line() — k2_prod_shadow_worker.py:36]
  │   "k2_summary": comparison.get("k2_summary")              ✅
  │   "k2_merge.k2_eval_tags": k2_tags                        ✅ (不同結構)
  │
  ▼ [shadow_batch_20260530.jsonl] — 原始資料
  │   k2_summary.tags = ["infra_risk"]                        ✅ (真實資料確認)
  │   k2_merge.k2_eval_tags = ["infra_risk"]                  ✅
  │
  ▼ [ibridge_exporter → normalize_shadow_record → _k2_summary_to_ibridge()]
  │   tags = _coerce_tags(summary.get("tags") or [])          ✅ L247
  │   "tags": tags                                             ✅ L257
  │
  ▼ [shadow_ibridge_records.latest.jsonl] — ibridge 輸出
  │   "tags": ["infra_risk"]                                   ✅ (真實資料確認)
  │
  ═══════════════════════════════════════════════════
  ▼ [dryrun/core.py → _normalize_export_row()]
  ║  ⚠  _synthetic_gate_from_metrics() 建立「新」的 tags，
  ║  僅從 metrics 計算，**不讀取原始 ibridge row.get("tags")**。
  ║  原始 tags=["infra_risk"] 被覆蓋為 []。
  ║
  ▼ [dryrun per_record.jsonl]
  ║  "tags": []                                                ❌ 原始 tags 遺失
  ║  "gate_result": "pass"                                     ❌ 應為 "needs_review"
  ║
  ▼ [compute_ideal_verdict()]
  ║  "infra_risk" in tags → False (tags=[])                    ❌
  ║  "gate_result == 'pass'" → True
  ║  return "allow", "gate_ok_score_high"
  ║
  ▼ [enf_preview_wrapper → classify_preview_outcome]
  ║  dryrun_rule == "gate_ok_score_high"
  ║  → ENF-RULE-1 pre-condition FAIL (需要 "gate_fail_deny")
  ║  → ENF-RULE-2 pre-condition FAIL (需要 "gate_fail_needs_review")
  ║  → return "noop", None
  ║
  ▼ [GOV-ENF-PREVIEW] 分類結果
      "noop" — 兩條 infra_risk 記錄完全未被任何規則打到
```

### 2.2 真實資料端到端對照（以 `prod-shadow-9469a97892-k2` 為例）

| 階段 | 檔案 | 關鍵欄位 | tags |
|------|------|---------|------|
| **原始 spool** | `shadow_batch_20260530.jsonl` L5 | `k2_summary.tags: ["infra_risk"]`, `k2_summary.ok: true`, `k2_summary.error_type: null`, `k2_summary.retry_count: 1` | ✅ `["infra_risk"]` |
| **原始 spool (merge)** | 同上 | `k2_merge.k2_eval_tags: ["infra_risk"]`, `k2_merge.gate_result: "needs_review"` | ✅ `["infra_risk"]` (另存) |
| **ibridge 輸出** | `shadow_ibridge_records.latest.jsonl` L2 | `success: true`, `tags: ["infra_risk"]`, `error_type: null`, `retry_count: 1` | ✅ `["infra_risk"]` |
| **dryrun per_record** | (執行 `python -m tools.dryrun`) | `gate_result: "pass"`, `tags: []`, `dryrun_rule: "gate_ok_score_high"` | ❌ `[]` |
| **enf_preview** | (執行 `python -m tools.enf_preview_wrapper`) | `dryrun_rule=gate_ok_score_high` → ENF-RULE-1 不檢查 | ❌ `noop` |

---

## 3. ENF-RULE-1/2 期待的 tags vs 實際 tags

### 3.1 ENF-RULE-1 條件（`tools/enf_preview_wrapper.py L22-25`）

```python
ENF_RULE_1_DRYRUN_RULE = "gate_fail_deny"
ENF_RULE_1_RISK_TAGS = frozenset({"infra_risk", "security:critical"})
ENF_RULE_1_DEFAULT_MIN_SCORE = 0.7

# 觸發邏輯 (L92-100):
if dryrun_rule == "gate_fail_deny":              # ← pre-condition (1)
    if error_type is not None:                    # ← pre-condition (2)
        if _record_has_risk_tag(tags):            # ← 檢查 tags 含 risk tag
            if score is not None and score >= min_score:
                return "block", "ENF-RULE-1"
```

### 3.2 ENF-RULE-2 條件（`tools/enf_preview_wrapper.py L28-31`）

```python
ENF_RULE_2_DRYRUN_RULE = "gate_fail_needs_review"
ENF_RULE_2_TAG = "high_retry"
ENF_RULE_2_MIN_RETRY = 2

# 觸發邏輯 (L103-105):
elif dryrun_rule == "gate_fail_needs_review":    # ← pre-condition
    if ENF_RULE_2_TAG in tags:                    # ← 檢查 tags 含 "high_retry"
        if retry_count >= ENF_RULE_2_MIN_RETRY:
            return "warn", "ENF_RULE-2"
```

### 3.3 名詞一致診斷

| Tag 名稱 | `eval_gate.py` 產出 | `dryrun/core.py` 消費 | `enf_preview_wrapper.py` 檢查 | 一致？ |
|----------|-------------------|---------------------|---------------------------|--------|
| `infra_risk` | `_rule_infra_risk`: `error_type in (context_overflow, timeout)` → `"infra_risk"` | `_synthetic_gate_from_metrics`: `error_type in INFRA_ERROR_TYPES` → `"infra_risk"` | `ENF_RULE_1_RISK_TAGS = {"infra_risk", "security:critical"}` | ✅ 命名一致 |
| `high_retry` | `_rule_high_retry`: `retry_count >= 2` → `"high_retry"` | `_synthetic_gate_from_metrics`: `retry_count >= 2` → `"high_retry"` | `ENF_RULE_2_TAG = "high_retry"` | ✅ 命名一致 |

**結論：tag 命名在各層完全一致。名稱不一致不是問題。**

### 3.4 真正的斷點（三層）

#### 斷點 1（主要）：dryrun `_normalize_export_row()` 覆蓋原始 tags

**檔案**：`tools/dryrun/core.py L84-111`

**機制**：`_normalize_export_row()` 從 ibridge row 讀取 metrics（`success`、`retry_count`、`error_type`等），呼叫 `_synthetic_gate_from_metrics(metrics, row)` 建立一組**全新**的 tags（僅從 metrics 計算，**不讀取 `row.get("tags")`**），然後用這組 tags 覆蓋輸出：

```python
# L92-100: metrics 來自 row 的頂層欄位，不包含 row.get("tags")
metrics = {
    "success": row.get("success"),        # True (prod-shadow)
    "retry_count": row.get("retry_count", 0),  # 1 or 0
    "error_type": row.get("error_type"),   # null (prod-shadow, k2 ok=true 所以無 error)
    ...
}
# L100: synthetic gate 只看 metrics，不看 row.tags
gate_result, tags, reasons = _synthetic_gate_from_metrics(metrics, row)
# 對於 prod-shadow-9469a97892: 
#   error_type=null → 不在 INFRA_ERROR_TYPES → infra_risk 不觸發
#   retry_count=1 < 2 → high_retry 不觸發
#   success=True → 不走 success=false 補償
# → tags=[], gate_result="pass"

return {
    ...
    "gate_result": gate_result,  # "pass"
    "tags": tags,                # [] ← 覆蓋原始 ibridge 的 ["infra_risk"]
    ...
}
```

**為什麼 `error_type=null`？** 因為 k2_summary.ok=true 表示 K-2 流程本身沒有錯誤。`infra_risk` tag 的來源不是 `error_type`（K-2 運作正常），而是 K-2 在第 5 層某個節點做了進一步評估後，判定該記錄雖成功但環境/基礎設施層級有風險→打了 `infra_risk` 標籤。但這個標籤在轉送到 ibridge 層時是透過 `eval_gate.tags`，而非 `error_type`。

#### 斷點 2（次）：`compute_ideal_verdict` 只看已空的 tags

**檔案**：`tools/dryrun/core.py L232-264`

```python
tags = list(record.get("tags") or [])  # [] (已被 _normalize_export_row 清空)
if success is False or "infra_risk" in tags or error_type in INFRA_ERROR_TYPES:
    return "deny", "gate_fail_deny"     # 不觸發，tags=[] 不含 infra_risk
```

#### 斷點 3（規則）：ENF-RULE-1 pre-condition 需要 `gate_fail_deny`

即使是修復斷點 1+2 後，`compute_ideal_verdict` 會回傳 `"deny", "gate_fail_deny"`。此時 ENF-RULE-1 的第一個 pre-condition (`dryrun_rule == "gate_fail_deny"`) 會通過，但第二個 pre-condition (`error_type is not None`) 不會通過——因為 k2_summary.error_type=null。

```python
if dryrun_rule == ENF_RULE_1_DRYRUN_RULE:          # "gate_fail_deny" ✅ (修復後)
    if error_type is not None:                       # null → ❌ 仍不通過
        ...
```

---

## 4. 根因總結

### 4.1 三層斷點匯總

| 斷點 | 位置 | 嚴重性 | 影響 |
|------|------|--------|------|
| **P1**: `_normalize_export_row` 不保留原始 ibridge tags | `tools/dryrun/core.py:84-111` | **主要** | 原始 tags 從 `["infra_risk"]` → `[]` |
| **P2**: `compute_ideal_verdict` 看已空的 tags | `tools/dryrun/core.py:232-264` | 次要 | 即使 P1 修復也無問題，但現在依賴 P1 |
| **P3**: ENF-RULE-1 需 `error_type is not None` | `tools/enf_preview_wrapper.py:92-93` | **主要** | prod-shadow 記錄 k2.ok=true 導致 error_type=null，即使 tags 正確也打不中 |

### 4.2 為何 MINING-03 觀察到 allow/allow

對於 `prod-shadow-9469a97892-k2`：

1. `shadow_batch_20260530.jsonl`: `k2_summary.tags=["infra_risk"]` ✅
2. `shadow_ibridge_records.latest.jsonl`: `tags=["infra_risk"]` ✅
3. dryrun `_normalize_export_row`: `tags=[]` ❌ (原始 tags 被覆蓋)
4. dryrun `compute_ideal_verdict`: `"allow", "gate_ok_score_high"`
5. enf_preview: `noop` (dryrun_rule != gate_fail_deny)
6. MINING-03 觀察到的實際 verdict: `allow`、ideal verdict: `allow` → **allow/allow**

### 4.3 「那 2 條真實記錄在源頭到底有沒有 tag？」

**有。** 真實 shadow batch 資料確認：

| 記錄 | 源頭 tag (shadow_batch) | Ibiridge tag (ibridge JSONL) | dryrun tag |
|------|------------------------|-----------------------------|------------|
| `prod-shadow-9469a97892-k2` | `k2_summary.tags: ["infra_risk"]` ✅ | `tags: ["infra_risk"]` ✅ | `tags: []` ❌ |
| `prod-shadow-1bab7f91d5-k2` | `k2_summary.tags: ["infra_risk"]` ✅ | `tags: ["infra_risk"]` ✅ | `tags: []` ❌ |

**但問題是：這兩個 infra_risk tag 在 `k2_summary` 中是怎麼被打上去的？**

再往上游追溯：
- `summarize_k2_output()` (k2_ask_shadow.py:224-265) 從 `eval_metadata.eval_gate.tags` 讀取 tags
- `eval_gate.tags` (eval_gate.py:286-352) 由 5 條規則產生
- `_rule_infra_risk` 要求 `error_type in ("context_overflow", "timeout")`

但這兩個記錄的 `k2_summary.error_type=null`，意味著 **`infra_risk` tag 不是由 eval_gate 的 `_rule_infra_risk` 產生的**。

更可能的路徑：
- LangGraph K-2 flow 的 `finalize_eval_node()` 在 `evaluate_task_record()` 中，`record` 的 `error_type` 可能是設定好的（即使 k2 ok=true）
- 或者 `infra_risk` tag 是由 K-2 流程在更早階段的某些邏輯（selector、context routing 等）產生並寫入 `eval_gate.tags` 的

**當前的追蹤限制：本報告無法看到 K-2 LangGraph 的完整執行記錄（即 k2_out 的完整結構），只能從 shadow_batch 的輸出推斷。**

### 4.4 真實場景演繹

這 2 條記錄的場景很可能是：

```
生產環境 healthcheck 失敗 (ask_summary.ok=false, "health_node: healthcheck failed")
  │
  ▼ K-2 流程獨立執行（不受 ask 失敗影響）
  │   k2 成功執行 (k2.ok=true)
  │   但在過程中檢測到某些 infra 異常 → eval_gate 打上 "infra_risk" tag
  │
  ▼ k2_merge 看到 ask 失敗、k2 有 infra_risk
  │   gate_result = "needs_review"（正確）
  │
  ▼ shadow_batch 儲存
  │   k2_summary.tags = ["infra_risk"] ✅
  │   k2_merge.k2_eval_tags = ["infra_risk"] ✅
  │
  ▼ ibridge_exporter 轉換
  │   tags = ["infra_risk"] ✅
  │
  ▼ dryrun/core 消費
  │   _normalize_export_row 從 metrics 重建 tags（不看原始 tags）
  │   metrics.error_type = null（因為 ibridge.success=true 時不設定 error_type）
  │   synthetic tags = [] ❌
  │
  ▼ enf_preview
  │   永遠打不到 ENF-RULE-1/2
```

---

## 5. 修復建議（下一階段）

### 5.1 建議票 A: `W5-A-RUNTIME-03-DRYRUN-K2-TAG-PRESERVE-01`

> **一句話**：修正 `tools/dryrun/core.py` 的 `_normalize_export_row()`，使其在為 k2_shadow ibridge 記錄建立輸出 tags 時，**合併**原始 ibridge record 的 tags（`row.get("tags") or []`）與 `_synthetic_gate_from_metrics` 的結果，而非完全覆蓋。

**修改範圍**：
- 檔案：`tools/dryrun/core.py`
- 位置：`_normalize_export_row()` 約 L100
- 方式：`synthetic_tags + list(row.get("tags") or [])` 或 `list(set(...))` 去重
- 不修改：`_synthetic_gate_from_metrics`、`compute_ideal_verdict` 的 tags 判斷邏輯

**預期效果**：
- 修復後：`compute_ideal_verdict` 的 `"infra_risk" in tags` → True → `return "deny", "gate_fail_deny"`
- ENF-RULE-1 的 `dryrun_rule == "gate_fail_deny"` pre-condition 通過
- 但 ENF-RULE-1 的 `error_type is not None` pre-condition 仍不通過（見建議票 B）

### 5.2 建議票 B: `W5-A-RUNTIME-03-ENF-RULE-1-CONDITION-ADJUST-01`

> **一句話**：調整 ENF-RULE-1 的第二個 pre-condition，當 `_record_has_risk_tag(tags)` 已成立時允許 `error_type=None`，使 risk tag 本身足以觸發 `block`（不受 error_type 限制）。

**修改範圍**：
- 檔案：`tools/enf_preview_wrapper.py`
- 位置：`classify_preview_outcome()` 約 L92-100
- 方式：`if error_type is not None and _record_has_risk_tag(tags)` → 可改為 `if _record_has_risk_tag(tags)`（若 accept risk tag 即為足夠訊號）或加入 `or (tags_only and tags)` 分支

**預期效果**：
- 修復後：prod-shadow 記錄 `tags=["infra_risk"]`、`dryrun_rule="gate_fail_deny"` → ENF-RULE-1 block
- 注意：需與建議票 A 同時實作（否則 dryrun tags 仍是空的）

### 5.3 不建議的調整

| 調整 | 理由 |
|------|------|
| 在 `eval_gate.py` 的 `_rule_infra_risk` 中放寬條件 | `_rule_infra_risk` 設計目的是 error_type 做觸發條件，與 prod-shadow 的 `infra_risk` 來源不同。改這個可能產生 FP。 |
| 在 `k2_summary_to_ibridge` 或 ibridge_exporter 中改動 | 已驗證正確。不需修改。 |
| 修改 ENF-RULE-2 去接 infra_risk | ENF-RULE-2 設計是 `high_retry` + `needs_review`，語意不匹配。 |

---

## 6. 風險與限制

| 項目 | 說明 |
|------|------|
| 本報告僅基於現有 artefact | `shadow_batch_20260530.jsonl` 的 prod-shadow 記錄可能不完整（缺少完整 k2_out 記錄），無法驗證 `eval_gate.tags` 在 K-2 flow 內部的分配邏輯 |
| `infra_risk` 在 k2_summary 的來源 | 目前僅能經由程式碼路徑推測：`eval_gate.tags` → `summarize_k2_output`→ `k2_summary`。但因無法看到 k2_out 的全量結構，無法確認 `eval_gate.tags` 是在哪個節點、基於什麼條件被設定的 |
| `_normalize_export_row` 的 tags 覆蓋行為可能是刻意的 | 設計目的可能是「dryrun 應從零開始評估，不信任上游資料標籤」。若屬實，則建議票 A 需要更謹慎的討論（例如僅合併 k2_shadow 來源的上游 tags，而非所有 ibridge tags） |
| 本報告僅為分析 | 不修改任何程式碼、workflow 或規則。 |

---

## 7. 相關文件

- `shadow_batch_20260530.jsonl`（L5-6：2 條含 infra_risk 的真實 prod-shadow 記錄）
- `shadow_ibridge_records.latest.jsonl`（L1-2：ibridge 輸出，tags 已正確保留）
- `observability/eval_gate.py`（L1-352：5 條規則的完整實作）
- `tools/dryrun/core.py`（L84-111：`_normalize_export_row` 覆蓋 tags；L114-143：`_synthetic_gate_from_metrics`；L232-264：`compute_ideal_verdict`）
- `tools/enf_preview_wrapper.py`（L22-31：ENF-RULE-1/2 定義；L74-107：`classify_preview_outcome`）
- `core/k2_merge_adapter.py`（L41-51：`_extract_k2_eval_tags` 從 k2_out.eval_metadata 讀取 tags）

---

## 8. 版本歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.1 | 2026-05-31 | W5-A-K2-TAGS-TRACE-01 | 初始 trace 報告。定位真正的斷點在 `dryrun/core.py _normalize_export_row`。 |
