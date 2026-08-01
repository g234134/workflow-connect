# W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01 — prod-shadow → ibridge tags 傳遞驗證（確認＋文件化）

> **票號**：W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01
> **狀態**：驗證就緒。程式碼已正確處理 tags。本票目標調整為「驗證確認＋文件化」。
> **依賴**：W5-A-RUNTIME-03-POLICY-MINING-03（本驗證的發起源）
> **對齊**：本驗證完成前，ENF-RULE-1 不進 limited blocking canary（per MINING-03 §6.1）

---

## 1. 關鍵發現

### 1.1 W5-POLICY-MINING-03 根因假設 vs 實際程式碼

| 項目 | MINING-03 假設 | 實際程式碼 (2026-05-31 snapshot) |
|------|---------------|----------------------------------|
| `_k2_summary_to_ibridge()` 是否遺漏 tags | ✅ 假設為「未讀取 tags」 | ❌ **已正確處理**：L247 `tags = _coerce_tags(summary.get("tags") or [])`；L257 `"tags": tags` |
| `EXPORT_FIELD_NAMES` 是否遺漏 tags | ✅ 假設為「不在 tuple 中」 | ❌ **已包含**：L50 `"tags",` 已存在 |
| 是否有對應 unittest | — | ✅ **已有**：`test_k2_summary_tags_preserved_in_ibridge_record` (L140) + `test_k2_summary_missing_tags_defaults_to_empty_list` (L156) |

**結論**：MINING-03 的資料完整性缺口結論（「_k2_summary_to_ibridge() 沒有保留 tags」）與當前程式碼不符。`observability/ibridge_exporter.py` 的 `_k2_summary_to_ibridge()` 和 `EXPORT_FIELD_NAMES` **均已經正確處理 tags 傳遞**。

### 1.2 可能解釋

有三種可能：

1. **MINING-03 分析時的 shadow 樣本來自更早的程式碼版本**，當時 ibridge_exporter 尚未加入 tags 傳遞。後續 (1) `_k2_summary_to_ibridge` 被補上 tags、(2) `_coerce_tags` helper 被新增、(3) `EXPORT_FIELD_NAMES` 加入 `"tags"`、(4) 對應測試被補上。

2. **MINING-03 觀察到的「2 條 infra_risk 訊號被分類為 allow/allow」另有根因**（非 ibridge_exporter tags 缺失），可能是 K-2 流程本身未產出 `eval_metadata.eval_gate.tags`，或 shadow 比較 step 的 k2_summary 中 tags 就是空的。

3. **MINING-03 分析的原始 shadow batch 資料並非由當前 `_build_spool_line` 格式產生**，可能來自不同的 spool 格式或手動構造的測試資料。

---

## 2. 完整 tags 流確認

驗證路徑：從 K-2 輸出到 enf_preview 的最終消費。

### 2.1 流向圖（已確認）

```
k2_out (LangGraph K-2 flow)
  │
  │  eval_metadata.eval_gate.tags (source of truth)
  │
  ▼ [summarize_k2_output() — k2_ask_shadow.py:224]
  │
  │  tags = _normalize_tags(eval_gate.get("tags"))    ✅
  │  + "reviewer_fallback" / "retrieve_retry"          ✅
  │  k2_summary["tags"] = tags                         ✅
  │
  ▼ [compare_shadow_profiles() — k2_ask_shadow.py:354]
  │
  │  "k2_summary": dict(k2_summary)                    ✅
  │
  ▼ [_build_spool_line() — k2_prod_shadow_worker.py:36]
  │
  │  "k2_summary": comparison.get("k2_summary")        ✅
  │
  ▼ [normalize_shadow_record() → _k2_summary_to_ibridge() — ibridge_exporter.py:232]
  │
  │  tags = _coerce_tags(summary.get("tags") or [])   ✅ L247
  │  "tags": tags                                       ✅ L257
  │
  ▼ [normalize_ibridge_record() — ibridge_exporter.py:184]
  │
  │  EXPORT_FIELD_NAMES 含 "tags"                       ✅ L50
  │  record["tags"] 不被濾除                            ✅
  │
  ▼ [shadow_ibridge_records.latest.jsonl]              ← tags 完整保留
  │
  ▼ [dryrun/core.py]
  │
  │  tags = list(record.get("tags") or [])             ✅ L245
  │  "tags": record.get("tags") or []                   ✅ L294
  │
  ▼ [enf_preview_wrapper.py]
  │
  │  tags = list(row.get("tags") or [])                 ✅ L86
  │
  ▼ [GOV-ENF-PREVIEW 結構化日誌]
```

### 2.2 各節點型別安全

| 節點 | 輸入型別 | 處理 | 輸出型別 | 空值處理 |
|------|---------|------|---------|---------|
| `summarize_k2_output` | `eval_gate.tags: list[str]` | `_normalize_tags` → sorted+derep | `list[str]` | 無 tags → `[]` |
| `_k2_summary_to_ibridge` | `summary.tags: list[str]` | `_coerce_tags` → type guard | `list[str]` | null/非list → `[]` |
| `normalize_ibridge_record` | `dict` | EXPORT_FIELD_NAMES projection | `dict` | 不在record中 → 省略 |
| `dryrun/core.py` | `record.tags: list[str]` | `list(record.get("tags") or [])` | `list[str]` | None/missing → `[]` |
| `enf_preview_wrapper.py` | `row.tags: list[str]` | `list(row.get("tags") or [])` | `list[str]` | None/missing → `[]` |

---

## 3. 既有測試

### 3.1 `tests/test_ibridge_exporter.py`

| 測試方法 | 行號 | 驗證內容 | 狀態 |
|---------|------|---------|------|
| `test_k2_summary_tags_preserved_in_ibridge_record` | L140 | `k2_summary` 含 `tags: ["infra_risk", "foo"]` → 輸出 ibridge 的 `tags` 為 `["infra_risk", "foo"]` | ✅ 已通過 |
| `test_k2_summary_missing_tags_defaults_to_empty_list` | L156 | `k2_summary` 無 tags → 輸出 ibridge 的 `tags` 為 `[]` | ✅ 已通過 |
| `test_normalize_shadow_k2_summary` | L124 | 一般 k2_summary 路徑正常（不含 tags 欄位） | ✅ 已通過 |

### 3.2 `tests/fixtures/eval/shadow_raw_records.jsonl`

現有 fixture 的 line 3-4 已含 tags 欄位：
- Line 3: `"tags": []` (shadow-greeting)
- Line 4: `"tags": ["high_retry"]` (shadow-retry)

---

## 4. 建議後續動作

### 4.1 短期（本票範圍內）

| # | 動作 | 理由 |
|---|------|------|
| 1 | 在 `test_ibridge_exporter.py` 補上 `test_export_shadow_source_preserves_tags_in_artifact` | 覆蓋完整 `export_ibridge_jsonl(source="shadow")` 端到端路徑，確認 tags 從 fixture 到產出 JSONL 的完整遞送 |
| 2 | 在 `W5-A-RUNTIME-03-POLICY-MINING-03.md` 附錄中加註勘誤 | 標示 ibridge_exporter 的根因結論與實際程式碼不符，建議 revisiting |
| 3 | 文件化本票的驗證結果 | 即本文件 |

### 4.2 中期（下一階段）

| # | 建議 | 理由 |
|---|------|------|
| A | 檢查 `k2_ask_shadow.py:summarize_k2_output()` 的 `tags` 來源，確認 `eval_metadata.eval_gate.tags` 在真實 prod-shadow 中是否被填充 | 若 K-2 flow 不產出有意義的 `eval_gate.tags`，則下游的完整流向都不會收到 `infra_risk` 等訊號 |
| B | 檢查 `core/langgraph_flow_k2.py` 的 eval gate 邏輯 | 確認 `eval_out.get("tags")` 在真實 shadow 情境下包含 `infra_risk` |
| C | 檢查 `_build_spool_line()` 在 `k2_merge` 層的 `k2_eval_tags` 是否應同步傳入 `k2_summary.tags` | 在某些流程中，tags 可能在 merge 層才被賦值，而 `summarize_k2_output` 從 `k2_out.eval_metadata` 讀取時可能已太早 |

### 4.3 關於 ENF-RULE-1

**本驗證不改變 ENF-RULE-1 的 blocking 決策。** 即使 tags 流向正確：
- 若 K-2 flow 本身不產出 `eval_gate.tags` → ibridge 的 `tags=[]` → dryrun 收到 `tags=[]` → ENF-RULE-1 條件不滿足
- 若 K-2 flow 產出 `tags=["infra_risk"]` → ibridge 的 `tags=["infra_risk"]` → dryrun 收到 `tags=["infra_risk"]` → ENF-RULE-1 可正確評估

MINING-03 的結論仍然成立：**在首批真實 shadow 樣本中，2 條帶有 infra_risk 訊號的記錄最終被分類為 allow/allow**。根因可能不是 ibridge_exporter 的 tags 缺失，而是 K-2 flow 的 `eval_gate.tags` 未被填充，或 tags 在 shadow 比較流程的 `k2_summary` 層被丟失。

---

## 5. 風險與回退

| 風險 | 影響 | 緩解 |
|------|------|------|
| 本驗證變更了任務定位（從「修補」變成「驗證確認」） | 可能需重新路由 | 本文件已是「驗證確認」定位，不需實作 |
| MINING-03 的勘誤可能影響後續決策 | 需尚書省確認勘誤後更新 master_status | 勘誤已在 §4.2 列為建議，待排程 |
| 真實根因在 K-2 flow (eval_gate.tags 填充) | 下一階段需開新票 | 本票不涵蓋 K-2 flow 變更，僅做文件化與證據鏈 |

---

## 6. 相關文件

- W5-A-RUNTIME-03-POLICY-MINING-03.md（本驗證的發起源。**注意**：該報告對 ibridge_exporter 的根因結論與當前程式碼不符，需 revisiting。）
- W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-BRIEF-FOR-CURSOR.md（實作 BRIEF——已調整為驗證確認定位）
- `observability/ibridge_exporter.py`（L39-57 EXPORT_FIELD_NAMES，L223 _coerce_tags，L232-264 _k2_summary_to_ibridge）
- `tests/test_ibridge_exporter.py`（L140-169 tags 相關測試）

## 7. 版本歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.2 | 2026-05-31 | W5-A-IBRIDGE-TAG-FIX-01 | **全面修正。** 基於實際程式碼審查，任務從「修補 tags 缺失」調整為「驗證確認 tags 流向正確」。勘誤 MINING-03 的根因結論。 |
| v0.1 | 2026-05-31 | (前次) | 初始設計（基於 MINING-03 假設，與實際程式碼不符。已取代。） |
