# W4-GUARD G2–G4 Escalation Frame v1（FP-G1-T3 · 可開關升格）

> **票**：`FP-G1-T3-guard-schema-ratio-escalation-frame-v1` · 父票 `W4-GUARD-01`  
> **授權**：尚書省口令「全開」（2026-07-28）＝批文 waive · 准許 opt-in 實作  
> **預設安全**：升格 **關閉**；**禁止**默升產線／required CI

---

## 0. non_claims

| 本檔 **不是** | 說明 |
|---------------|------|
| ≠ 產線必開 | 預設 observation-only |
| ≠ required CI | 不改 `.github/workflows` branch protection |
| ≠ 改 sampleco 默認 E2E exit | 無 `--strict-guards` 時 sampleco 仍可 `ok=true` |
| ≠ Round-2／DarkOps／L1／K-2 | 無關 |

---

## 1. 分項定義（對齊 W4-GUARD-01）

| ID | 觸發條件 | 預設（off） | Opt-in 行為 |
|----|----------|-------------|-------------|
| **G2** | `phase_like` + `multi_row_export` + `schema_ambiguous` | 僅 `signals` | `applied.gate_eligibility=review_needed` |
| **G3** | `accepted_ratio`＜0.5 → warn；G2 ∧ ratio＜0.1 → block | 僅 `signals` | `applied.delivery=manual_review`／`block_delivery` |
| **G4** | `qa_status=pass_with_warnings` + G3 signal | 僅 candidate | `--strict-guards` → `e2e_fail=true` |

常數：`scripts/w4_guard_escalation_v1.py` → `DEFAULT_RATIO_WARN=0.5` · `DEFAULT_RATIO_BLOCK=0.1`

---

## 2. 啟用方式（明確開關）

```bash
# 預設：旁路觀測欄位 guard_escalation（不改 exit）
python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json

# 套用 G2/G3 recommendations（仍可不 fail E2E）
python scripts/run_case_e2e_validation.py \
  --case-dir cases/sampleco/2026-0001 \
  --enable-guard-escalation --json

# G4：嚴格模式失敗（opt-in）
python scripts/run_case_e2e_validation.py \
  --case-dir cases/sampleco/2026-0001 \
  --strict-guards --json
```

Python：

```python
from w4_guard_escalation_v1 import evaluate_guard_escalation

esc = evaluate_guard_escalation(
    eligibility_raw=...,
    output_guard=...,
    qa_status="pass_with_warnings",
    enable_g2=False,
    enable_g3=False,
    enable_g4=False,
    strict_guards=False,  # MUST stay False in prod defaults
)
# esc["e2e_fail"] is False unless strict_guards + G4 signal
```

---

## 3. 回傳 `dict` 形狀（穩定）

| 鍵 | 語意 |
|----|------|
| `ok` | 評估本身成功 |
| `signals` | `g2_*`／`g3_*`／`g4_*` 布林 |
| `recommendations` | 建議（即使未 apply） |
| `applied` | 僅旗標開啟時非空 |
| `e2e_fail` | 僅 `--strict-guards` + G4 |
| `flags` | 本次啟用狀態（稽核） |
| `message` | `observation_only_default_safe`／`escalation_applied`／`strict_guards_fail` |

E2E 結果附加鍵：`guard_escalation`（見 `run_case_e2e_validation`）。

---

## 4. 驗收／證據

```bash
python -m unittest tests.test_w4_guard_escalation_v1 -v
```

- 預設 sampleco → `e2e_fail=False` · `applied={}`
- `--strict-guards` + sampleco 型訊號 → `e2e_fail=True`

---

## 5. 留痕

- Progress／本票 STATE：口令「全開」＝批文授權；**未**默升 CI
- 父票 `W4-GUARD-01`：T1 仍 accepted_with_gaps；G2–G4 本輪為 **opt-in landed**

---

## 6. Cross-ref

- `04_Workflows/tickets/FP-G1-T3-guard-schema-ratio-escalation-frame-v1_state.md`
- `04_Workflows/tickets/W4-GUARD-01_state.md`
- `docs/agent-and-non-tabular-lines-readme-v2.md` §2.3
