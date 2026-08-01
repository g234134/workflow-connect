# Ticket Reviewer Checklist Template（附頁）

> **Schema 對齊**：`docs/ticket-schema-master-v1.md` · `_templates/ticket_state.template.md`（**W5-T2**；原 Master 文稱 W1-T1 已方案 A 歸併）  
> **用途**：Reviewer 逐條 AC 勾選 · skeleton／placeholder 分欄 · over-claim 攔截。  
> **票**：`W5-T4-wave-plan-reviewer-checklist-v1`

---

## Meta

| 欄 | 值 |
|----|-----|
| ticket_id | |
| reviewer_date | |
| wave_id | |
| evidence_tier | L-local / CI-advisory / GA-remote / n/a |

---

## Acceptance Criteria（逐條）

| AC# | 條件摘要 | 驗證命令／證據 | Pass? | 備註 |
|-----|----------|----------------|-------|------|
| AC-1 | | | ☐ | |
| AC-2 | | | ☐ | |
| AC-3 | | | ☐ | |
| AC-4 | | | ☐ | |
| AC-5 | | | ☐ | |
| AC-6 | | | ☐ | |
| AC-7 | | | ☐ | |

---

## Verification 占位

```text
命令：
預期：
實際：
```

---

## Skeleton / Placeholder 分欄

| 類型 | 路徑／說明 | 是否冒充完成？ |
|------|------------|----------------|
| skeleton | | ☐ 否（須標明） |
| placeholder | | ☐ 否 |

---

## Over-claim 攔截

- [ ] 無「CI landing = GA pass」（無 run URL）
- [ ] 無「local unittest = 遠端 validated」
- [ ] 無自行上調 Phase%
- [ ] 無 required check／merge gate（無批文）
- [ ] human-only 證據未標 AI verified

---

## C_REPORT 草稿欄（貼回子票）

- conclusion: accepted | accepted_with_gaps | needs_changes | rejected
- blocking_issues:
- checks_summary:
- risk_level: low | medium | high
- suggestions:
