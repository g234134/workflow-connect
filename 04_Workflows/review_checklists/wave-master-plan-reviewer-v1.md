# Wave Master Plan Reviewer Checklist v1

> **Ticket**: `W5-T4-wave-plan-reviewer-checklist-v1` · **Wave 5** · Master CP  
> **用途**：Master Reviewer 驗收 Chat 1–5 **規劃質量**（對照 `docs/wave-master-ticketing-playbook.md` §5.3）。  
> **分線**：戰術 lane Reviewer → `wave-next-code-inspector-v1.md`（**勿混用**）。

---

## 0. 職責分界

| 工具 | 層級 | 何時用 |
|------|------|--------|
| **本檔** `wave-master-plan-reviewer-v1.md` | Master Plan / Wave Master 規劃 | 審 `W-MASTER-wave-plan_state.md` · 五 Wave 區塊 |
| `wave-next-code-inspector-v1.md` | Wave-next 戰術 lane | 審 P7 / P8.5 / P9 子票施工與 advisory CI |
| `wave-cross-rollup-inspector-v1.md` | 跨 Wave 執行後 rollup | Wave 1–4 施工完成後 spot-check 證據（引用 W5-T3） |

---

## 1. Master Plan Review Checklist（playbook §5.3 · 全部 9 項）

| # | 檢查項 | Blocking | ☐ |
|---|--------|----------|---|
| 1 | 每 Wave ≥1 條 planned ticket 或 explicit「本 Wave 僅 blocked/解阻」說明 | **Y** | ☐ |
| 2 | 所有 ticket ID 前綴與 Wave 一致 · 無跨 Wave ID 篡改 | **Y** | ☐ |
| 3 | 每條 ticket `estimated_cycles` ≤2 或已拆票 | **Y** | ☐ |
| 4 | Phase ≥80% 的票僅補 AC 缺口 · 無重開大工程 | **Y** | ☐ |
| 5 | human/infra/security prereqs 完整 · 無偽完成 AC | **Y** | ☐ |
| 6 | `dependencies_detail` / `risks` / `observability` 抽樣合格（playbook §4） | **Y** | ☐ |
| 7 | 無 Phase% 上調 · 無 required CI 升格（無批文） | **Y** | ☐ |
| 8 | Cross-wave 依賴與 `W-MASTER` §Cross-wave dependencies 一致 | N | ☐ |
| 9 | 與 `W-ORCH` 戰術線子票 STATE 無 hard conflict | **Y** | ☐ |

任一 **Blocking=Y** 失敗 → 不得給 `PLAN_READY`。

---

## 2. Observability 抽樣規則（playbook §4.1–4.3）

### 2.1 合格示例

```yaml
observability:
  verify_commands:
    - "python scripts/observe_wave_evidence_v1.py --wave W5 --format json"
    - "rg 'PLAN_READY|PLAN_REJECT' 04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md"
  evidence_artifacts:
    - "docs/wave-evidence-ingestion-spec-v1.md"
    - "子票 B_REPORT verification"
  trace_fields:
    - "run_id"
    - "ticket_id"
    - "gap_reason"
  success_signals:
    - "CLI ok=true 且 gaps honest"
  failure_signals:
    - "偽造 run URL 為 verified"
```

### 2.2 不合格示例

```yaml
observability:
  verify_commands: []   # 缺命令
  success_signals:
    - "测试通过"         # 無命令 / 無 artifact
  # 無 failure_signals · 無 evidence_artifacts
```

**規則**：Reviewer 不跑代碼也能判斷完成條件；缺 `verify_commands` 或僅口號 → §5.3 #6 **fail**。

---

## 3. Cross-wave dependency 抽樣

- [ ] 對照 `W-MASTER-wave-plan_state.md` §Cross-Wave Dependencies 表
- [ ] 下游票未重定義上游 SSOT 欄位（例：W5-T3 只消費 P7.5 trace · 不重寫）
- [ ] human-blocked 票未寫成 AI AC 已完成

---

## 4. Verdict 輸出模板（貼 W-MASTER C_REPORT）

```markdown
## Master Plan Review Verdict

- **reviewer_date**: YYYY-MM-DD
- **verdict**: PLAN_READY | PLAN_WITH_GAPS | PLAN_REJECT
- **waves_reviewed**: W1–W5
- **summary**: （2–4 句）
- **blocking_issues**: 無 | （列項）
- **over_claims_found**: 無 | （列項）
- **per_wave_notes**:
  - W1: …
  - W2: …
  - W3: …
  - W4: …
  - W5: …
- **next_action**: 開執行 Implementer chats | 退回 Planner 修訂
```

僅讀本 checklist 即可填寫上段（AC-4）。

---

## Changelog

| 日期 | 說明 |
|------|------|
| 2026-07-09 | 初版 · W5-T4 |
