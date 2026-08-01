# W6-T7 — Experiment Eval & Replay Guide v1

> **Ticket**: W6-T7 · experiment-eval-and-replay-guide-v1  
> **Role**: Architect + Scribe  
> **Date**: 2026-06-10  
> **Type**: Docs-only (no code changes)  
> **Scope**: Evaluation, replay, and failure analysis documentation for W6-T3/T4/T5/T6

---

## FRAME

### Goal
為 W6-T3 / W6-T4 / W6-T5 / W6-T6 這條 Agent-run 標準案實驗線，補齊「如何驗收、如何 replay、如何做失敗分析」的文檔。

### Scope
- ✅ 新增 `docs/agent-run-experiment-eval-guide-v1.md`
- ✅ 更新 `04_Workflows/WORKFLOW_INDEX.md` (新增 W6-T7)
- ✅ 更新 `docs/WAVE_PROGRESS_DASHBOARD.md` (新增 W6-T7)
- ✅ 本 state 文件

### NonScope
- ❌ 不修改任何程式碼
- ❌ 不新增 unittest
- ❌ 不修改既有 orchestrator / checkpoint / integration 實作
- ❌ 不涉及 main-chain E2E 或 UI

### AllowedPaths
- `docs/*`
- `04_Workflows/*.md`
- `04_Workflows/tickets/*_state.md`

### BlockedPaths
- `scripts/*` (除 read-only 驗證外)
- `hitl/*` (除 read-only 驗證外)
- `tools/*` (除 read-only 驗證外)
- `routing/*` (除 read-only 驗證外)

### AC (Acceptance Criteria)

| AC | 描述 | 驗證方法 |
|----|------|----------|
| AC-1 | 指南包含 §1-6 完整章節 | 檢查 `docs/agent-run-experiment-eval-guide-v1.md` 目錄 |
| AC-2 | 成功定義分三級 (Preview/Auto/Full HITL) | 檢查 §2.2 |
| AC-3 | 最小驗證命令清單含 5+ 命令 | 檢查 §3 |
| AC-4 | Replay 章節覆蓋 5 個階段 (Decision/CP-A/Route/CP-B/Delivery) | 檢查 §4 |
| AC-5 | 常見失敗類型 ≥3 種，各有排查順序 | 檢查 §5 |
| AC-6 | 升級條件含可量化門檻 | 檢查 §6.1 G1-G7 |
| AC-7 | WORKFLOW_INDEX 已新增 W6-T7 | 檢查索引 |
| AC-8 | WAVE_PROGRESS_DASHBOARD 已新增 W6-T7 | 檢查 dashboard |

---

## STATE

### status_by_role

| Role | Status | Date | Notes |
|------|--------|------|-------|
| Architect (Scribe) | done | 2026-06-10 | 文件撰寫完成 |
| Reviewer | pending | — | 待 Reviewer 驗收 |
| Implementer | N/A | — | 本票無程式碼 |
| Orchestrator | done | 2026-06-10 | 任務分派與追蹤 |

### overall_status
`implementer_done` — 等待 Reviewer 驗收 AC-1~AC-8。

---

## B_REPORT (Build Report)

### changed_files
- `docs/agent-run-experiment-eval-guide-v1.md` (new)
- `04_Workflows/tickets/W6-T7-experiment-eval-and-replay-guide-v1_state.md` (new)
- `04_Workflows/WORKFLOW_INDEX.md` (modified — 新增 W6-T7 索引)
- `docs/WAVE_PROGRESS_DASHBOARD.md` (modified — 新增 W6-T7 Wave 6 區塊)

### verification_commands

```bash
# AC-1~AC-6: 文件結構檢查
grep -E "^## §[1-6]" docs/agent-run-experiment-eval-guide-v1.md | wc -l
# 預期: 6 (§1-§6)

# AC-3: 最小驗證命令數
grep -E "^python " docs/agent-run-experiment-eval-guide-v1.md | wc -l
# 預期: ≥5

# AC-5: 失敗類型數
grep -E "^### 5\.[2-9] " docs/agent-run-experiment-eval-guide-v1.md | wc -l
# 預期: ≥3
```

### test_results
N/A — 本票無程式碼，無 unittest。

---

## C_REPORT (Checker / Reviewer Report)

### conclusion
`pending` — 等待 Reviewer 驗收。

### checks_summary

| Check | Status | Evidence |
|-------|--------|----------|
| AC-1: 六章結構完整 | pending | 見 B_REPORT verification |
| AC-2: 三級成功定義 | pending | §2.2 table |
| AC-3: 驗證命令清單 | pending | §3 命令區塊 |
| AC-4: 五階段 replay | pending | §4.1 table |
| AC-5: 失敗類型 ≥3 | pending | §5.1 table + §5.2-5.7 |
| AC-6: 升級條件量化 | pending | §6.1 G1-G7 table |
| AC-7: INDEX 更新 | pending | WORKFLOW_INDEX.md diff |
| AC-8: DASHBOARD 更新 | pending | WAVE_PROGRESS_DASHBOARD.md diff |

### suggestions
- S1: 未來可補充實際 replay 腳本（`scripts/replay_experiment.sh`）作為 W6-T12 參考
- S2: 建議與 `docs/multi-agent-replay-guide-v1.md` 交叉引用是否完整

---

## D_REPORT (Delivery / Scribe Report)

### docs_updates
- `docs/agent-run-experiment-eval-guide-v1.md` — 新建：Agent-run 實驗線驗收、replay、失敗分析完整指南
- `04_Workflows/WORKFLOW_INDEX.md` — 修改：§1.8 Skill Card & Skill Map 區塊新增 W6-T7
- `docs/WAVE_PROGRESS_DASHBOARD.md` — 修改：Wave 6 區塊新增 W6-T7 完成度

### progress_entry
```markdown
**W6-T7 · Experiment Eval & Replay Guide**（2026-06-10）— Architect+Scribe `implementer_done`
交付 `docs/agent-run-experiment-eval-guide-v1.md`（§1-§6 完整指南）：
- §2 三級成功定義（Preview/Auto/Full HITL）
- §3 最小驗證命令清單（orchestrator + integration + regression）
- §4 五階段 replay 方法論（Decision/CP-A/Route/CP-B/Delivery）
- §5 六類失敗排查（F1-F6 診斷順序與命令）
- §6 升級條件 G1-G7（可量化門檻）
更新索引：WORKFLOW_INDEX §1.8、WAVE_PROGRESS_DASHBOARD Wave 6 區塊。
```

### followup_suggestions
- W6-T12: Resume Framework — 本指南 §4 預設 `--resume-from-checkpoint` CLI，待 W6-T12 實作
- W6-T2-REVIEW: Wave 6 回顧時使用本指南 G1-G7 驗收實驗線穩定度

---

## O_NOTES (Orchestrator Notes)

### run_log
- 2026-06-10 07:08 UTC+8: 尚書省指派 Architect + Scribe 啟動 W6-T7
- 2026-06-10 07:10 UTC+8: 唯讀閱讀 8 份上游文件完成
- 2026-06-10 07:15 UTC+8: 建立 `docs/agent-run-experiment-eval-guide-v1.md`（§1-§6）
- 2026-06-10 07:18 UTC+8: 建立 `04_Workflows/tickets/W6-T7-experiment-eval-and-replay-guide-v1_state.md`
- 2026-06-10 07:20 UTC+8: 更新 `WORKFLOW_INDEX.md` §1.8
- 2026-06-10 07:22 UTC+8: 更新 `WAVE_PROGRESS_DASHBOARD.md` Wave 6 區塊
- 2026-06-10 07:25 UTC+8: 戰報提交，等待 Reviewer 驗收

### blockers
無。

### decisions
- 本指南定位為「實驗線操作手冊」，而非「Multi-Chat 票 replay 指南」（後者已存在於 `docs/multi-agent-replay-guide-v1.md`）
- 失敗類型 F1-F6 基於 W6-T3 §8 卡住點擴展，增加診斷順序與命令
- 升級條件 G1-G7 對應 95% 藍圖 `docs/ninety-five-percent-automation-blueprint-v1.md` §6.1 gap 驗收標準

---

*W6-T7 State · 2026-06-10 · Architect + Scribe*
