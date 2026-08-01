# TICKET STATE · W4-GUARD-G2-G4-reviewer-sample · G2–G4 Reviewer 抽樣

> **授權**：尚書省「全授權」B1 · 2026-07-29  
> **角色**：Reviewer（C）· 可跑測 · **不改** required CI · **勿**誤開 strict 進 CI  
> **上游**：`FP-G1-T3-guard-schema-ratio-escalation-frame-v1`（opt-in DONE）

---

## FRAME

- Goal: Reviewer 確認 G2–G4 **預設 off** 與 `--strict-guards` opt-in 行為；寫 C_REPORT；不改 workflows。
- Scope:
  - MUST：複跑 `tests.test_w4_guard_escalation_v1`
  - MUST：本票 C_REPORT（verdict + evidence + non_claims）
  - MAY：抽樣讀 `scripts/w4_guard_escalation_v1.py`／`docs/w4-guard-g2-g4-escalation-frame-v1.md`
- NonScope:
  - 改 `.github/workflows/**` · 把 `--strict-guards` 寫進 required CI
  - 改 escalation 預設為 on
  - Phase%／Round-2／DarkOps
- AllowedPaths:
  - `04_Workflows/tickets/W4-GUARD-G2-G4-reviewer-sample_state.md`
  - `04_Workflows/tickets/FP-G1-T3-guard-schema-ratio-escalation-frame-v1_state.md`（notes 一句 · 可選）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
  - 只讀：`scripts/w4_guard_escalation_v1.py` · `tests/test_w4_guard_escalation_v1.py` · `docs/w4-guard-g2-g4-escalation-frame-v1.md`
- AcceptanceCriteria:
  - AC-1：預設 observation_only · `e2e_fail=false` · `applied={}`
  - AC-2：`strict_guards=True` + G4 candidate → `e2e_fail=true`
  - AC-3：C_REPORT 明示 ≠ required CI／≠ 默開 strict

---

## STATE

- **overall_status**: `done`
- **current_owner**: closed
- **last_updated**: 2026-07-29T00:50+08:00
- **next_action**: closed · tip#1 仍 P6_WATCH · **勿**升 required CI

---

## C_REPORT

**verdict**: `accepted`  
**role**: Reviewer（same_chat · 全授權 B1）  
**ts**: 2026-07-29T00:50+08:00  
**scope**: G2–G4 opt-in 預設 off + strict 行為抽樣

### 結論

1. **預設安全**：`evaluate_guard_escalation(...)` 無旗標時 `message=observation_only_default_safe` · `applied={}` · `e2e_fail=False` · `flags.strict_guards=False`。  
2. **strict opt-in**：`strict_guards=True` 且 G4 candidate（pass_with_warnings + G3）→ `e2e_fail=True` · `applied.e2e=fail`。  
3. **無 G4 信號時** strict 亦不 fail（測 `test_strict_guards_without_g4_signal_does_not_fail`）。  
4. **CI 邊界**：本輪**未**改任何 workflow；**禁止**將 `--strict-guards` 默進 required checks（須另票＋尚書省批文）。

### 驗證

```
python -m unittest tests.test_w4_guard_escalation_v1 -v
```

（結果見全授權戰報 §驗證）

### gaps

無功能 gap。可選後續：E2E CLI 抽樣一行（非本票必須）。

### non_claims

≠ required CI 默升 · ≠ 預設開 G2/G3/G4 · ≠ Phase% · ≠ Round-2 GO · ≠ DarkOps
