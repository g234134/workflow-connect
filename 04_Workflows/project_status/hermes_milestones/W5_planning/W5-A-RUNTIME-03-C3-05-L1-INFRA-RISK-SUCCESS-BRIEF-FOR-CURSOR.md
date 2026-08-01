# C3-05-L1-INFRA-RISK-SUCCESS — BRIEF FOR CURSOR

> **票號**：W5-A-RUNTIME-03-C3-05-L1-INFRA-RISK-SUCCESS
> **日期**：2026-05-31
> **來源設計**：`W5-A-RUNTIME-03-C3-05-L1-INFRA-RISK-SUCCESS-DESIGN-01.md`
> **背景 Mining**：`W5-A-RUNTIME-03-POLICY-MINING-03.1_INFRA-RISK.md` §4.1
> **對齊規則**：W5-A-RUNTIME-03-LIMITED-DENY_plan.md（L1 advisory）
> **硬邊界**：C3-05 **只能** L1 warning。**嚴禁**影響 verdict / exit code。

---

## 1. 背景與目標

### 1.1 為什麼需要 C3-05

從真實 prod-shadow 資料分析（MINING-03.1）發現：

- 2/2 真實 prod-shadow 記錄帶有 `infra_risk` tag（例如 `tags: ["infra_risk"]`）
- 但 dryrun 正確判定為 `gate_ok_score_high → allow`（score=1.0, error_type=null, success=true）
- ENF-RULE-1（L2 候選）不命中是正確行為 — 它需要 `gate_fail_deny + error_type`，而這些記錄不符合

這些案例不應跟退，但 `infra_risk` 標籤代表基礎設施曾經處於風險狀態。需要一條 L1 advisory warning 來記錄這一訊號，**不改變 verdict，不影響 exit code**。

### 1.2 目標

在 `tools/enf_preview_wrapper.py` 中新增一條 additive L1 warning 規則 C3-05：

- 當 per_record 的 `tags` 包含 `"infra_risk"` 且 `actual_verdict` 為 `"allow"` 時
- 輸出一條 `[GOV-ENF-PREVIEW] [WARN] ...` 結構化 log line
- 在 JSON summary 中記錄 `c3_05_warnings` 計數與觸發樣本
- **不修改**任何現有 verdict / verdict 分類 / exit code

---

## 2. 允許修改的範圍

### ✅ 可以改的

| 目標 | 檔案 | 修改 |
|------|------|------|
| 新增常數 | `tools/enf_preview_wrapper.py` | `C3_05_RULE_NAME`、`C3_05_TAG`（`"infra_risk"`）|
| 新增函式 | `tools/enf_preview_wrapper.py` | `check_c3_05(record, existing_outcome) → dict | None` |
| 修改 `run_preview()` | `tools/enf_preview_wrapper.py` | 在 row loop 中加入 C3-05 檢查、計數、log、json payload 擴展 |

### ❌ 不能改的

| 項目 | 原因 |
|------|------|
| ❌ `classify_preview_outcome()` | 既有 ENF-RULE-1/2 邏輯不動。C3-05 應作為額外 check 而非 inline |
| ❌ `_emit()` 簽名 | 保持現有 log 格式不變 |
| ❌ exit code | 永遠 return 0 |
| ❌ `actual_verdict` / `ideal_verdict` | C3-05 不得修改 verdict |
| ❌ `dryrun_rule` | 不影響 dryrun 分類 |
| ❌ 任何 `tools/dryrun/` 檔案 | 不涉及 enforcement 規則 |
| ❌ 任何 `.github/workflows/` | C3-05 在 ENF preview step 內部處理 |
| ❌ 任何 `tests/` 檔案 | 本輪不強制補測試 |
| ❌ 任何 `observability/` 檔案 | 不涉及規則變更 |

---

## 3. 實作細節

### 3.1 新增常數

在 enf_preview_wrapper.py 的常數區（ENF-RULE-2 相關常數後方）新增：

```python
# C3-05 (L1 additive warning) — MINING-03.1 §4.1
C3_05_RULE_NAME: Final[str] = "C3-05"
C3_05_RULE_FULL_NAME: Final[str] = "C3-05-L1-INFRA-RISK-SUCCESS"
C3_05_TAG: Final[str] = "infra_risk"
```

### 3.2 新增函式

```python
def check_c3_05(record: dict, existing_outcome: str) -> dict | None:
    """C3-05: infra_risk in tags + allow → L1 additive warning.

    Args:
        record: per_record dict from dryrun.
        existing_outcome: current ENF classification ("block"|"warn"|"noop").

    Returns:
        dict with warning details if triggered, else None.
    """
    # Skip if already blocked — C3-05 is for successful records only
    if existing_outcome == "block":
        return None

    tags = list(record.get("tags") or [])
    if C3_05_TAG not in tags:
        return None

    if record.get("actual_verdict") != "allow":
        return None

    return {
        "rule": C3_05_RULE_NAME,
        "rule_name": C3_05_RULE_FULL_NAME,
        "message": "infra_risk detected in successful record",
        "level": "L1",
        "task_id": record.get("task_id"),
        "actual_verdict": record.get("actual_verdict"),
        "tags": tags,
    }
```

### 3.3 修改 `run_preview()` — row loop

在現有 row loop（L167-L180）中，在 `classify_preview_outcome` 呼叫之後、`if outcome == "block"` 等判斷之前，加入 C3-05 檢查與對應的計數邏輯：

```python
# --- 既有邏輯（不修改）---
for row in rows:
    outcome, rule_name = classify_preview_outcome(row, min_score=min_score)
    # ... 既有 block/warn/noop 計數 ...

    # --- 新增 C3-05 檢查 ---
    c3_05_warning = check_c3_05(row, outcome)
    if c3_05_warning is not None:
        c3_05_warnings += 1
        if verbose or len(c3_05_samples) < 5:
            c3_05_samples.append(c3_05_warning)
```

### 3.4 修改 `run_preview()` — 新增變數初始化

在 L159-L165 的變數宣告區新增：

```python
c3_05_warnings = 0
c3_05_samples: list[dict[str, Any]] = []
```

### 3.5 新增 Log 行（在 details 區塊）

在 L191-L201 的 `_emit("detail", ...)` 區塊後新增：

```python
if verbose and c3_05_warnings > 0:
    for sample in c3_05_samples:
        _emit(
            "c3_05_warning",
            rule=sample["rule"],
            task_id=sample.get("task_id"),
            actual_verdict=sample.get("actual_verdict"),
            tags=sample.get("tags"),
        )
```

### 3.6 修改 JSON output payload

在 L219-L237 的 output payload 區塊，擴展 `rules` 與新增 `c3_05_warnings`：

```python
# 在 payload["rules"] 中加入：
"C3-05": {"c3_05_warnings": c3_05_warnings},

# 在頂層新增：
"c3_05_warnings": c3_05_warnings,
```

### 3.7 完整變更摘要

```
tools/enf_preview_wrapper.py
├── 新增常數: C3_05_RULE_NAME, C3_05_RULE_FULL_NAME, C3_05_TAG
├── 新增函式: check_c3_05()
├── run_preview():
│   ├── 變數初始化: c3_05_warnings, c3_05_samples
│   ├── row loop: 加入 check_c3_05() 呼叫
│   ├── log: 加入 event=c3_05_warning 行
│   └── JSON payload: 加入 c3_05_warnings + rules.C3-05
└── (classify_preview_outcome, _emit, main 均不動)
```

---

## 4. 驗收條件（AC）

| AC ID | 條件 | 驗證方式 | 預期結果 |
|-------|------|---------|---------|
| **AC-1** | prod-shadow 記錄（infra_risk + allow）會觸發 C3-05 warning | 跑 enf_preview_wrapper 處理 `_dryrun_verify/20260531T030106Z_per_record.jsonl` | `c3_05_warnings == 2`，log 行包含 `rule=C3-05 task_id=prod-shadow-9469a97892-k2` |
| **AC-2** | deny 記錄（如 t-infra）不受 C3-05 影響 | 驗證 t-infra 的 outcome 仍為 "block" | t-infra 無 C3-05 warning。ENF-RULE-1 block 計數不變 |
| **AC-3** | 無 infra_risk tag 的記錄不產生 C3-05 warning | 驗證 shadow-greeting、shadow-k2-flow-1、t-healthy | 這些記錄的 `c3_05_warnings` 計數不增加 |
| **AC-4** | 既有 ENF-RULE-1/2 計數不變 | 比較修改前後的 `would_block` / `would_warn` | 完全一致 |
| **AC-5** | JSON output payload 包含 C3-05 資訊 | 檢查 `--output` 指定的 JSON | `rules.C3-05.c3_05_warnings` 存在。頂層 `c3_05_warnings` 存在 |
| **AC-6** | Exit code 永遠為 0（即使 C3-05 觸發）| 對任意有效輸入跑 wrapper | `echo $?` 為 0 |
| **AC-7** | `[GOV-ENF-PREVIEW]` prefix 不變 | 檢查所有 log 行 | 無其他 prefix |
| **AC-8** | C3-05 warning 在 block 記錄上被跳過 | 驗證 t-infra | `check_c3_05(t_infra_record, "block")` 回傳 None |

### 4.1 驗證用資料

post-fix per_record 資料位於：

| 檔案 | 路徑 | 預期 C3-05 觸發數 |
|------|------|------------------|
| 完整（含 smoke） | `artifacts/eval/_dryrun_verify/20260531T030106Z_per_record.jsonl` | 2（prod-shadow-* 兩筆）|
| AC2 子集 | `artifacts/eval/_dryrun_ac2/20260531T030111Z_per_record.jsonl` | 2（同上）|
| 舊版（pre-fix，tags 已清空） | `observability/dryrun/20260530T222742Z_per_record.jsonl` | **0**（tags=[] 已被清空）|

---

## 5. 不在此範圍內的事

| 事項 | 原因 |
|------|------|
| 增加 `security:critical` 等其他 risk tags | 暫無樣本，待未來擴展。僅 infra_risk |
| 升級 C3-05 到 L2 blocking | MINING-03.1 明確不建議（100% FP）|
| 新增 unittest / CI test | 不強制，但建議手動驗證後補 |
| 修改 CI workflow YAML | C3-05 在 ENF preview 內部處理，不需要新 CI step |
| 修改 dryrun core / CI wrapper | 不涉及 enforcement 規則 |
| 更新 observability/enf-preview/README.md | 可選，但建議本輪不做 |

---

## 附錄 A — 參考資料

| 文件 | 用途 |
|------|------|
| `W5-A-RUNTIME-03-C3-05-L1-INFRA-RISK-SUCCESS-DESIGN-01.md` | 完整設計 spec（觸發條件、輸出格式、風險分析） |
| `W5-A-RUNTIME-03-POLICY-MINING-03.1_INFRA-RISK.md` §4.1 | Mining 結論與建議 |
| `tools/enf_preview_wrapper.py` | 目標實作檔案（現有 302 行） |
| `artifacts/eval/_dryrun_verify/20260531T030106Z_per_record.jsonl` | 驗證用 per_record 資料 |

## 附錄 B — 版本歷史

| 版本 | 日期 | 變更說明 |
|------|------|---------|
| v0.1 | 2026-05-31 | 基於 DESIGN-01 與 enf_preview_wrapper.py v0.1 的首版 Cursor BRIEF。8 個 AC。 |
