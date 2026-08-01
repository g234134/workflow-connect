# W5-A-RUNTIME-03-C3-05-L1-INFRA-RISK-SUCCESS-DESIGN-01 — C3-05 L1 Warning 規則設計

> **票號**：W5-A-RUNTIME-03-C3-05-L1-INFRA-RISK-SUCCESS-DESIGN-01
> **日期**：2026-05-31
> **來源**：W5-A-RUNTIME-03-POLICY-MINING-03.1_INFRA-RISK.md §4.1
> **對齊**：W5-A-RUNTIME-03-LIMITED-DENY_plan.md（Enforceability Ladder L0/L1/L2）
> **硬邊界**：僅規劃設計，不改 repo、CI、規則實作。

---

## 1. 規則意圖與範圍

### 1.1 為何需要 C3-05

從 MINING-03.1 的真實資料分析中發現：

| 觀測 | 說明 |
|------|------|
| **2/2 真實 prod-shadow 記錄** | 都帶有 `infra_risk` tag，但 dryrun 判定為 `gate_ok_score_high → allow` |
| **K2 推理無誤** | score=1.0, error_type=null, success=true — 代理正確完成任務 |
| **風險在基礎設施，不在推理** | `infra_risk` tag 是 K2 對所處基礎設施狀態的觀測（資源緊張、網路不穩等），不是推理錯誤 |
| **ENF-RULE-1 不命中是正確的** | 規則需要 `gate_fail_deny + error_type`，而這些案例不符合。強行 block 會產生 100% FP |

**結論**：這些案例不應 deny，但 infra 異常狀態值得被記錄與追蹤。C3-05 提供一條 L1 warning 通道，在不影響 verdict 的前提下讓操作員知道「有成功記錄但 infra 被標記」。

### 1.2 不做的事

| 不做的 | 原因 |
|--------|------|
| ❌ 不改變 verdict | L1 規則定位，僅 advisory |
| ❌ 不影響 CI exit code | 永遠 exit 0 |
| ❌ 不修改 ENF-RULE-1/2 | 既有 L1/L2 規則邏輯不動 |
| ❌ 不修改 dryrun score / ideal | C3-05 是 post-classification 的附加檢查 |
| ❌ 不加入 `observability_gap` 等其他 tags | 暫無樣本，待未來擴展 |

### 1.3 規則定位（Enforceability Ladder）

```
L2: ENF-RULE-1 (block candidate) — gate_fail_deny + error_type + risk tag
L1: ENF-RULE-2 (warn)           — gate_fail_needs_review + high_retry + retry≥2
L1: C3-05 (warn, additive)       — infra_risk in tags + allow ← NEW
L0: (observability only)
```

**關鍵差異**：ENF-RULE-2 是**取代 verdict**（exclusive warn），C3-05 是**附加 warning**（additive — 在原有 allow 上疊加 warning，不改 verdict）。

---

## 2. 觸發條件

### 2.1 觸發條件（精確版）

C3-05 的觸發條件以 dryrun per_record JSON 的欄位為準：

```
條件 1: "infra_risk" in record["tags"]
         tags 欄位來自 dryrun 合併後的 tags（原始 K2 tags + synthetic tags）
         類型：list[str]，空 [] 或 ["infra_risk"] 等

條件 2: record["actual_verdict"] == "allow"
         per_record 中由 dryrun 判定的最終 verdict
         注意：allow 可能對應 dryrun_rule 值 "gate_ok_score_high" 或 "gate_ok_score_low"

條件 3（隱含）: 不重複匹配 ENF-RULE-1 已處理的 case
         若同一記錄已被 ENF-RULE-1 判定為 block，C3-05 仍可觸發（warning 可疊加在 block 上？
         但設計上更合理：block 已經是 deny 層級，加 infra_risk warning 意義不大。
         ➡ 建議：當 outcome 為 block 時跳過 C3-05，避免 redundant warning。
```

**完整判定邏輯（Python 偽代碼）：**

```python
def check_c3_05(record: dict, existing_outcome: str) -> dict | None:
    """C3-05: infra_risk + allow → L1 additive warning.
    
    Args:
        record: per_record dict from dryrun
        existing_outcome: current ENF classification ("block"|"warn"|"noop")
    
    Returns:
        dict with rule/message/level if triggered, else None
    """
    # Skip if already blocked — C3-05 is for successful records only
    if existing_outcome == "block":
        return None
    
    tags = list(record.get("tags") or [])
    if "infra_risk" not in tags:
        return None
    
    actual_verdict = record.get("actual_verdict")
    if actual_verdict != "allow":
        return None
    
    return {
        "rule": "C3-05",
        "rule_name": "C3-05-L1-INFRA-RISK-SUCCESS",
        "message": "infra_risk detected in successful record — review infrastructure state",
        "level": "L1",
        "task_id": record.get("task_id"),
        "actual_verdict": actual_verdict,
        "tags": tags,
    }
```

### 2.2 不該觸發的情況

| 情況 | 行為 | 原因 |
|------|------|------|
| `infra_risk` in tags + already `block` | 跳過 | Block 已是更嚴重的狀態，疊加 infra_risk warning 不必要且可能混亂 |
| `infra_risk` in tags + `actual_verdict == "deny"` | 跳過 | Deny 已知有問題，不需要再提醒 infra |
| `infra_risk` in tags + `actual_verdict == "warn"`（如 ENF-RULE-2 觸發） | **觸發** | Warn + infra_risk 是更強的信號，兩個 warning 同時存在合理 |
| 無 `infra_risk` tag（空 [] 或其他 tags 如 `high_retry`） | 跳過 | 規則只針對 infra_risk，其他 tags 有各自的規則（如 ENF-RULE-2） |
| `infra_risk` in tags + `actual_verdict == "allow"`（但已經是 ENF-RULE-2 warn） | 跳過？| 目前不可能：ENF-RULE-2 只在 `gate_fail_needs_review` 時觸發，此時 actual_verdict 為 warn 非 allow |

### 2.3 與既有規則的互動

```
記錄進入 classify_preview_outcome()
    │
    ├── ENF-RULE-1: dryrun_rule == gate_fail_deny + error_type + risk tag → block
    │         ↓ 跳過 C3-05（block 已是最嚴重狀態）
    │
    ├── ENF-RULE-2: dryrun_rule == gate_fail_needs_review + high_retry → warn
    │         ↓ C3-05 可疊加（若 tags 也含 infra_risk）
    │
    └── noop: 未匹配任何規則
              ↓ C3-05 可觸發（若 tags 含 infra_risk + verdict = allow）
```

**已知互動案例**：prod-shadow-9469a97892-k2 與 prod-shadow-1bab7f91d5-k2 目前都為 noop + infra_risk + allow → C3-05 應觸發。

---

## 3. Warning 輸出格式

### 3.1 LOG 行格式

使用既有 `_emit()` 函式，擴展新的 `rule` 命名空間：

```
# 典型觸發（verbose mode）
[GOV-ENF-PREVIEW] [WARN] event=c3_05_warning rule=C3-05 task_id=prod-shadow-9469a97892-k2 actual_verdict=allow tags=["infra_risk"]

# 摘要行（summary 階段）
[GOV-ENF-PREVIEW] event=detail rule=C3-05 c3_05_warnings=2
```

### 3.2 結構化 JSON 輸出格式

在 `output_path` JSON payload 中擴展 `rules` 區塊：

```json
{
    "input": "observability/dryrun/20260531T030106Z_per_record.jsonl",
    "min_score": 0.7,
    "total": 9,
    "would_block": 1,
    "would_warn": 1,
    "would_noop": 7,
    "c3_05_warnings": 2,
    "rules": {
        "ENF-RULE-1": {"would_block": 1},
        "ENF-RULE-2": {"would_warn": 1},
        "C3-05": {"c3_05_warnings": 2}
    },
    "c3_05_samples": [
        {
            "task_id": "prod-shadow-9469a97892-k2",
            "actual_verdict": "allow",
            "tags": ["infra_risk"],
            "message": "infra_risk detected in successful record — review infrastructure state"
        },
        {
            "task_id": "prod-shadow-1bab7f91d5-k2",
            "actual_verdict": "allow",
            "tags": ["infra_risk"],
            "message": "infra_risk detected in successful record — review infrastructure state"
        }
    ],
    "exit_policy": "preview_only"
}
```

### 3.3 不該改變的既有格式

| 既有產出 | 是否受影響 | 說明 |
|---------|-----------|------|
| `[GOV-ENF-PREVIEW] event=summary total=...` | ❌ 不變 | 總計 count 不變；C3-05 是子計數 |
| `[GOV-ENF-PREVIEW] event=detail rule=ENF-RULE-1` | ❌ 不變 | 既有規則 detail 不動 |
| `event=would_block` / `event=would_warn` | ❌ 不變 | 既有 per-record verbose 輸出不動 |
| exit code | ❌ 永遠 0 | 不變 |
| `actual_verdict` / `ideal_verdict` | ❌ 不變 | 規則不得修改 verdict |

---

## 4. 預期行為驗證

### 4.1 基於現有樣本的預測

| task_id | tags | actual_verdict | ENF 結果 | 預期 C3-05 | 預期行為 |
|---------|------|---------------|----------|-----------|---------|
| prod-shadow-9469a97892-k2 | ["infra_risk"] | allow | noop | ✅ 觸發 | `c3_05_warnings += 1` |
| prod-shadow-1bab7f91d5-k2 | ["infra_risk"] | allow | noop | ✅ 觸發 | `c3_05_warnings += 1` |
| t-infra | ["infra_risk"] | fail (deny) | block | ❌ 跳過（block 已觸發）| 不受影響 |
| t-retry | ["high_retry"] | warn | warn (R2) | ❌ 跳過（無 infra_risk）| 不受影響 |
| shadow-retry | ["high_retry"] | warn | warn (R2) | ❌ 跳過（無 infra_risk）| 不受影響 |
| shadow-greeting | [] | allow | noop | ❌ 跳過（無 tags）| 不受影響 |
| t-healthy | [] | allow | noop | ❌ 跳過（無 tags）| 不受影響 |

### 4.2 跨 run 一致性預測

所有包含 prod-shadow 記錄的 post-fix per_record JSONL：
- `_dryrun_verify/20260531T030106Z` → 2 筆 C3-05 warning
- `_dryrun_ac2/20260531T030111Z` → 2 筆 C3-05 warning
- 任意只含 fixture（無 prod-shadow）的 run → 0 筆 C3-05 warning

---

## 5. 風險分析

| 風險 | 等級 | 說明 | 緩解 |
|------|------|------|------|
| C3-05 意外修改 verdict | **高** | 最常見的實作 bug：在 warning 邏輯中不小心動了 verdict | 禁止在 `check_c3_05` 函式中修改 `row` dict 的 verdict 欄位 |
| C3-05 疊加在 ENF-RULE-2 上造成混亂 | 低 | warn + infra_risk warning 同時出現 | 這是合理行為（兩個信號），log 格式可清晰區分 |
| C3-05 未來擴展為 L2 時忘記移除 flip 保護 | 低 | L1→L2 升級需經由 POLICY-MINING + 設計流程 | 本設計已明確定位為 L1；升級需另開設計票 |
| infra_risk tag 誤判（假的 positive） | 極低 | 若 infra_risk tag 是誤標，C3-05 只是多一條 warning | 不影響 prod。warning 可被 dashboard 過濾 |
| 新增 C3 規則後 `rules` payload 結構不一致 | 低 | `c3_05_warnings` 作為頂層欄位可能與既有 `would_warn` 混淆 | 設計中明確區分 `c3_05_warnings`（additive）vs `would_warn`（ENF-RULE-2 exclusive） |

---

## 6. 實作建議（高層）

### 6.1 建議修改的檔案

| 檔案 | 修改類型 | 說明 |
|------|---------|------|
| `tools/enf_preview_wrapper.py` | 新增函式 + 修改 `run_preview` | 新增 `check_c3_05()` 函式，在 `run_preview` 的 row loop 中加入 C3-05 檢查 |
| `tools/enf_preview_wrapper.py` | 新增常數 | `C3_05_RULE_NAME`、`C3_05_TAG` |

### 6.2 建議不修改的檔案

| 檔案 | 原因 |
|------|------|
| `tools/dryrun/core.py` | 不涉及 enforcement 規則 |
| `tools/dryrun_ci_wrapper.py` | CI wrapper 只負責呼叫 dryrun，不處理 ENF |
| `.github/workflows/eval-gate-ci.yml` | C3-05 在 ENF preview step 內部處理，不需新增 CI step |
| 任何 `tests/` 檔案 | CI-GAP-CHECKLIST 建議後續補測試，不在本設計範圍 |
| 任何 `observability/` 檔案 | 不涉及規則變更 |
| `tools/enf_preview_wrapper.py` 中的 `classify_preview_outcome()` | 既有規則邏輯不動，新增獨立函式 |

### 6.3 實作規模估計

| 度量 | 值 |
|------|-----|
| 新增函式數 | 1（`check_c3_05`）|
| 新增常數數 | 2（`C3_05_RULE_NAME`、`C3_05_TAG`）|
| 修改的函式 | 1（`run_preview`）|
| 新增的 Python 行數 | ~15-25 |
| 修改的測試 | 0（本輪不強制補測試）|
| 對既有行為的影響 | 0（additive only）|

---

## 附錄 A — 與 MINING-03.1 建議的對照

| MINING-03.1 建議 | 本設計實作 | 差異 |
|-----------------|-----------|------|
| 條件：infra_risk in tags + actual_verdict == allow | ✅ 完全採用 | 無 |
| 觸發位置：enf_preview_wrapper.py，ENF-RULE-2 同層級 | ✅ 採用，但為獨立函式 | 建議獨立函式而非 inline 以利測試 |
| 輸出：warnings 陣列 {"rule": "C3-05", "message": ...} | ✅ 採用，但擴展為完整 JSON payload + log | 多了 log 行格式與 payload 整合 |
| 不改 verdict / exit code | ✅ 採用，加 explicit skip on block | 多了「跳過 block」的限制 |

## 附錄 B — 版本歷史

| 版本 | 日期 | 變更說明 |
|------|------|---------|
| v0.1 | 2026-05-31 | 基於 MINING-03.1 §4.1 建議 + enf_preview_wrapper.py v0.1 實作的首版設計。定義 C3-05 為 additive L1 warning，不替 verdict，不影響 exit code。 |
