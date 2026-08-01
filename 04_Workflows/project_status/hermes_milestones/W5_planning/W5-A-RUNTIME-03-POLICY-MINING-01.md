# W5-A-RUNTIME-03-POLICY-MINING-01 — 從 dry-run 報表挖掘 limited deny 候選規則

> **票號**：W5-A-RUNTIME-03-POLICY-MINING-01
> **源頭資料**：RUNTIME-01 dry-run per-record JSONL（2 次執行，合計 13 筆記錄）
> **對齊**：W5-A-RUNTIME-03-LIMITED-DENY_plan.md §2（Enforceability Ladder）
> **硬邊界**：本報告僅標記 candidate，不宣告任何 rule 已升級 L2。具體 L2 selection 留給後續 POLICY-SELECTION 票。
> **免責**：資料量偏小（13 records），以下結論僅供初步參考。

---

## 1) 輸入盤點

### 1.1 可用報表

| 時間戳 | per-record JSONL | summary MD | 記錄數 | 來源 artefact |
|--------|-----------------|------------|--------|---------------|
| `20260530T185213Z` | `observability/dryrun/20260530T185213Z_per_record.jsonl` | `20260530T185213Z_summary.md` | 8 | shadow_eval_results + smoke_eval_results + ibridge |
| `20260530T210035Z` | `observability/dryrun/20260530T210035Z_per_record.jsonl` | `20260530T210035Z_summary.md` | 5 | shadow_ibridge_records only |

**合計**：13 筆記錄（含 8 筆來自 185213Z 的全量執行、5 筆來自 210035Z 的 ibridge-only 執行。部分記錄（prod-shadow、shadow-greeting、shadow-k2-flow-1、shadow-merge-2、shadow-retry）在兩次執行中皆出現）。

### 1.2 Schema 確認

per-record JSONL 欄位（來自 README + 實際資料）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `task_id` | str | 任務 ID（跨 run 可對照） |
| `trace_id` | str | 追蹤 ID |
| `actual_verdict` | str | `allow` / `warn` / `fail` / `unknown` |
| `ideal_verdict` | str | `allow` / `warn` / `deny` / `unknown` |
| `verdict_match` | bool | actual 與 ideal 是否一致（fail vs deny 視為匹配） |
| `dryrun_rule` | str | `gate_ok_score_high` / `gate_ok_score_low` / `gate_fail_deny` / `gate_fail_needs_review` / `edge_unknown` |
| `gate_result` | str | `pass` / `needs_review` |
| `tags` | list[str] | 如 `["high_retry"]`、`["infra_risk"]` |
| `metrics` | dict | `success`, `retry_count`, `handoff_count`, `error_type`, `trace_completeness_score` |
| `source_file` | str | 原始 artefact 檔名 |

---

## 2) 聚合統計

### 2.1 按 dryrun_rule 分布（合計 13 筆）

| dryrun_rule | 計數 | 佔比 | ideal_verdict 分布 | actual_verdict 分布 | match |
|------------|------|------|-------------------|-------------------|-------|
| `gate_ok_score_high` | 9 | 69.2% | 9× allow | 9× allow | 100% |
| `gate_fail_needs_review` | 3 | 23.1% | 3× warn | 3× warn | 100% |
| `gate_fail_deny` | 1 | 7.7% | 1× deny | 1× fail | 100% |
| `gate_ok_score_low` | 0 | 0% | — | — | — |
| `edge_unknown` | 0 | 0% | — | — | — |

### 2.2 按 trace_completeness_score 區間分布（對 gate_ok_score_high 記錄）

| score 區間 | 計數 | ideal_verdict | min_score threshold | 是否觸及邊界 |
|-----------|------|--------------|-------------------|-------------|
| 1.0 | 2 | allow (100%) | 0.875 | 高於 threshold，正常 |
| 0.95–0.99 | 4 | allow (100%) | 0.875 | 高於 threshold，正常 |
| 0.90–0.94 | 3 | allow (100%) | 0.875 | 高於 threshold，正常 |
| **<0.875** | **0** | — | 0.875 | **無資料 — 未觸及 threshold 邊界** |

### 2.3 按 error_type / tags 分布

| pattern | 計數 | dryrun_rule | ideal_verdict | 佔比 |
|---------|------|------------|--------------|------|
| `tags=["high_retry"]`（retry_count=2） | 3 | `gate_fail_needs_review` | warn | 23.1% |
| `tags=["infra_risk"]` + `error_type=timeout` | 1 | `gate_fail_deny` | deny | 7.7% |
| 無 tag 且 success=true | 9 | `gate_ok_score_high` | allow | 69.2% |

### 2.4 關鍵發現

1. **100% match ratio** — 在現有資料規模下，所有記錄的 `actual_verdict` 與 `ideal_verdict` 一致。這可能是好事（規則對齊），但因為 N 很小，也可能是語料偏誤（樣本均為通過案例）。
2. **gate_ok_score_low 與 edge_unknown 未被觸發** — 沒有記錄落在 score < 0.875 的範圍或無法被規則匹配。這代表 **threshold 邊界（0.875）仍未經過真實資料驗證**。
3. **單一 gate_fail_deny 記錄** — `t-infra`（smoke fixture）是目前唯一觸發 deny 的記錄。它是 timeout + infra_risk tag 的明確失敗案例。
4. **資料規模不足** — 13 records（其中 5 筆與另 5 筆重疊）不足以做統計顯著的 enforcement 決策。

---

## 3) Candidate 規則分析

### 3.1 Candidate 表格

| 編號 | 描述 | N（樣本數） | M（ideal=deny/block） | 實際 FP 觀察 | 初步評語 |
|------|------|-----------|----------------------|------------|---------|
| **C-01** | `dryrun_rule=gate_fail_deny` + `error_type` 非 null + `tags` 含風險標記 | 1（t-infra） | 1（ideal=deny, actual=fail） | 0 | **強 L2 候選**。條件 binary（timeout + infra_risk → deny）、無 FP、gate 已判 `needs_review`。N 極小但結構性明確。 |
| **C-02** | `dryrun_rule=gate_fail_deny` + `success=false`（不限 error_type） | 1（與 C-01 相同記錄） | 1 | 0 | 同上，C-01 的超集。若後續發現 `success=false` 但有非 timeout error_type，需再評估。 |
| **C-03** | `dryrun_rule=gate_fail_needs_review` + `tags=["high_retry"]` + `retry_count≥2` | 3（shadow-retry 2×, t-retry 1×） | 0（ideal=warn 非 deny） | 0（但本來就不 block） | **L1（Advisory）**。needs_review 依 RUNTIME-03 plan 定義為 L0（Observability-only），不應進 L2。如需 improvement，可考慮降級為 L1 advisory warning。 |
| **C-04** | `dryrun_rule=gate_ok_score_high` + `trace_completeness_score` 在 `[0.875, 0.92)` | 0 | 0 | — | **無法判定** — 無資料點。threshold 邊界（0.875）尚未被真實記錄測試。需要更多 low-score 記錄才能評估是否適合 L2。 |
| **C-05** | `dryrun_rule=gate_ok_score_high` + `trace_completeness_score` 在 `[0.92, 1.0]` | 9 | 0（所有 ideal=allow） | 0 | **非 L2 候選**（正常範圍，不應 block）。如果後續需要 enforcement，應針對此範圍以外的記錄（即 gate_ok_score_low），而非本範圍。 |
| **C-06** | `dryrun_rule=edge_unknown` | 0 | — | — | **無法判定** — 此規則從未觸發。若後續出現 unknown 記錄，應先分析資料缺失原因（schema 不對？artefact 不完整？），而非直接 enforce。 |

### 3.2 總結：強 L2 候選

| 候選 | dryrun_rule | 條件 | 強度 | 備註 |
|------|------------|------|------|------|
| **C-01** | `gate_fail_deny` | error_type=timeout（或等價明確 failure）+ infra_risk tag | ⭐⭐⭐ | 唯一可直接考慮進 L2 的模式。條件 binary、FP 率 0%、gate 已判定為 needs_review |
| **C-03** | `gate_fail_needs_review` | retry_count≥2 + high_retry tag | ⭐ | L1 Adivisory，不進 L2。可考慮 Enhancement：讓這類記錄在 CI 中印出更明顯的 review signal |

### 3.3 資料缺口

下列缺口阻礙了更完整的 enforcement 分析：

| 缺口 | 影響 | 建議 |
|------|------|------|
| 缺少 score < 0.875 的記錄 | 無法驗證 `gate_ok_score_low` 的行為 | 累積更多 nightly CI run；或人工製造 edge case fixture |
| 缺少 `edge_unknown` 記錄 | 無法驗證 unknown 的 fallback 行為 | 同上 |
| N=13（去重後約 8 unique） | 統計信心不足 | 持續累積 nightly 資料；目標 ≥50 records 再做二次 mining |
| 100% match ratio | 可能反映語料偏誤而非規則完美 | 加入更多型態的 fail/high_retry/timeout case 來測試規則邊界 |
| 無 PR workflow 的資料 | 無法評估 enforcement 在 PR 情境的影響 | 後續考慮對 PR CI 也 run dry-run |

---

## 4) 對 L2 的建議（僅供後續 POLICY-SELECTION 票參考）

### 4.1 可直接討論進 L2 的模式

**模式：`gate_fail_deny + 明確 infra failure（timeout / infra_risk）`**

- 現有證據：1 record（t-infra），0 FP，結構性明確。
- 建議：在 POLICY-SELECTION 票中，將此模式列為 L2 第一條候選，但在實作前需確認：
  - 是否有更多類似記錄（在真實 nightly 而非 smoke fixture 中）。
  - `infra_risk` tag 的產生邏輯是否穩定（不會因 upstream bug 而大量 false trigger）。
- 若確認：可在下一張實作票中讓此模式在 Phase A（preview）中觀察 7 個 nightly CI，FP 率確認後再進 Phase B。

### 4.2 不建議現在進 L2 的模式

- **`gate_fail_needs_review` 全系列** — 依 RUNTIME-03 plan §2.3 定義，needs_review 應保持 L0。即使未來考慮，也應先升級至 L1（advisory warning），再評估是否有 L2 的可能。
- **`gate_ok_score_high` 全系列** — 正常範圍，不應 block。
- **`edge_unknown`** — 該先診斷資料問題，而非 block。

### 4.3 建議的後續行動

1. **持續累積資料** — 讓 nightly CI 多跑 7–14 次，等待更多真實 fail / low-score 記錄出現，再做二次 mining。
2. **增加 edge case fixture** — 在 smoke fixture 中加入 score=0.7、score=0.5 的記錄，以測試 `gate_ok_score_low` 規則的行為。
3. **POLICY-SELECTION 票** — 在上述資料足夠後，開一張獨立的 policy selection 票，正式決定哪些模式進入 L2，並設定 N（觀察期數）與 FP 率閾值。

---

## 附錄 A — 原始資料摘要（去重後 unique 記錄）

以下為 13 筆記錄中去重後的 unique 記錄（以 task_id 為鍵），共 8 筆 unique：

| task_id | dryrun_rule | ideal | actual | score | tags / error | 出現於 |
|---------|------------|-------|--------|-------|--------------|--------|
| prod-shadow-9469a97892-k2 | gate_ok_score_high | allow | allow | 1.0 | — | 兩次 run |
| shadow-greeting | gate_ok_score_high | allow | allow | 1.0 | — | 兩次 run |
| shadow-k2-flow-1 | gate_ok_score_high | allow | allow | 0.95 | — | 兩次 run |
| shadow-merge-2 | gate_ok_score_high | allow | allow | 0.92 | — | 兩次 run |
| shadow-retry | gate_fail_needs_review | warn | warn | 1.0 | high_retry | 兩次 run |
| t-healthy | gate_ok_score_high | allow | allow | 0.95 | — | 185213Z only |
| t-infra | gate_fail_deny | deny | fail | 0.95 | infra_risk + timeout | 185213Z only |
| t-retry | gate_fail_needs_review | warn | warn | 0.9 | high_retry | 185213Z only |

---

## 附錄 B — RUNTIME-01 資料的治理規則對照

對照 RUNTIME-01 plan §4.1 的五條規則——本分析中實際觸發的規則：

| 規則編號 | 規則名 | 本分析中觸發？ | 被觸發的條件 |
|---------|--------|--------------|-------------|
| 規則 1 | gate_ok_score_high | ✅ | score ≥ 0.92（皆 > min_score=0.875） |
| 規則 2 | gate_ok_score_low | ❌（0 筆） | 無 score < 0.875 的記錄 |
| 規則 3 | gate_fail_deny | ✅（1 筆） | `success=false` + `error_type=timeout` + `tags=[infra_risk]` |
| 規則 4 | gate_fail_needs_review | ✅（3 筆） | `retry_count≥2` + `tags=[high_retry]`、`gate_result=needs_review` |
| 規則 5 | edge_unknown | ❌（0 筆） | 所有記錄皆有完整 task_id / gate / score 欄位 |
