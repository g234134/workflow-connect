# TICKET STATE · W4-P85-S2-GA-RUNBOOK-v1 · Scenario2 GA 證據鏈 runbook

> Wave 4 · P8.5 · **doc/spec** · same_chat O→B→C→D · 2026-07-13  
> 對齊：`W-MASTER-wave-plan_state.md#W4-P85-S2-GA-RUNBOOK-v1` · `docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3  
> **post-GA 適配**：human AC 已滿足（run_id=`29157178993`）· 本票只補 AI 段（runbook／Evidence Schema／INDEX）

---

## FRAME
<!-- Orchestrator 凍結 · 2026-07-13 -->

- Goal: 把 Scenario2 GA 證據鏈收成可重跑 SSOT：runbook §0.3 逐步 checklist + ops-run Evidence Schema + INDEX 誠實交叉引用（含已記錄 PASS）。
- Scope:
  - MUST：精修 `docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3（human dispatch 逐步 checklist · 預期 job id · 粗體勿選 default）
  - MUST：在 `WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md` 追加正式 **Evidence Schema** 小節（欄位定義；已填值可引用，禁止造假 URL）
  - MUST：`WORKFLOW_INDEX.md` §1.4 對齊 runbook 計數（Smoke A **20/20**）+ Scenario2 GA recorded 一句（advisory · ≠ required）
  - MAY：清除 ops-run 內過期「尚未跑／total_count=0」阻塞句（改為 recorded 狀態；歷史審計段可保留）
- NonScope:
  - 改 `.github/workflows/bridge-smoke.yml` · dispatch Actions · 改 Dashboard Phase% 數字格 · core／tests · 暗部 · .env
  - 宣稱 Phase closure／prod browser／required CI
- AllowedPaths:
  - `docs/phase8_5-bridge-smoke-runbook-v1.md`
  - `04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `04_Workflows/tickets/W4-P85-S2-GA-RUNBOOK-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（Scribe 末尾 append）
  - `04_Workflows/command_queue/QUEUE.yaml` · `SESSION.md`（Orchestrator／Scribe）
- BlockedPaths: 憲法 §7 禁區類型 · `WAVE_PROGRESS_DASHBOARD.md` 數字格 · `.github/workflows/**` · `core/**` · 他人 core
- Dependencies:
  - `WH-P85-SMOKE-B-scenario2-ops-run-v1`（GA done · run_id=29157178993）
  - `WH-P85-wave-H2-closure-scribe-v1`（done_with_gaps）
- relay_mode: same_chat
- evidence_tier: L-local + GA-remote（引用既有）
- phase_targets: [P8.5]
- baseline_pct: "07-13 SSOT · P8.5=18%"
- proposed_delta_pct: "0"
- evidence_gate: L-local
- apply_phase_pct: false
- AcceptanceCriteria:
  - AC-AI-1：runbook §0.3 含逐步 dispatch checklist（branch main · scenario=scenario2 · 兩 job id · 勿選 default）
  - AC-AI-2：ops-run STATE 含 `## Evidence Schema` · 欄位定義完整 · 已填 ga_run 與 Schema 一致 · 無假 URL
  - AC-AI-3：INDEX §1.4 Smoke A 計數與 runbook 一致（20/20）· Scenario2 GA recorded 語意 advisory／≠ required／≠ Phase closure
  - AC-HUMAN-1：✅ 已滿足 · run_id=29157178993（本票不重跑）

---

## STATE

- **overall_status**: `done`
- **lifecycle_phase**: O
- **current_owner**: none
- **next_action**: 無 · Reviewer accepted · Scribe 已封存 · 下一張建議 `W4-P85-P9-EVIDENCE-SSOT-v1`（兩線 URL 已齊）
- **last_updated**: 2026-07-13
- **status_by_role**:
  - **Orchestrator (O)**: done — FRAME 凍結（post-GA）
  - **Implementer (B)**: done
  - **Reviewer (C)**: accepted · risk=low
  - **Scribe (D)**: done
- **notes**:
  - human AC 已於 07-11 滿足；本票 = AI 段收口
  - **未**改 Phase% · **未**改 workflows
  - 歷史 06-24 blocked 審計段保留（RULE-11 留痕）

---

## B_REPORT
<!-- Implementer · 2026-07-13 -->

### changed_files

| 路徑 | 變更 |
|------|------|
| `docs/phase8_5-bridge-smoke-runbook-v1.md` | §0.3 新增 Scenario2 逐步 checklist + Recorded GA 表 |
| `04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md` | Human dispatch 狀態改 recorded · 新增 `## Evidence Schema` |
| `04_Workflows/WORKFLOW_INDEX.md` | §1.4 Smoke A **20/20** · GA recorded + 本票 cross-ref |
| `04_Workflows/tickets/W4-P85-S2-GA-RUNBOOK-v1_state.md` | 本票 STATE／報告 |

### verification

```text
rg "How to run Scenario 2|Evidence Schema|20/20|W4-P85-S2-GA-RUNBOOK|29157178993"
→ runbook / ops-run / INDEX 均命中
```

- AC-AI-1 ✅ · AC-AI-2 ✅ · AC-AI-3 ✅ · AC-HUMAN-1 ✅（既有）
- **未改** `core/**` · workflows · Dashboard 數字格 · 金鑰

### skeleton / placeholder

- 無

### Phase 影響

- **影響 Phase**：P8.5
- **baseline**：07-13 SSOT · 18%
- **proposed_delta**：0（證據已計入 W-PROG 07-13 · P8.5 +8）
- **實際上調**：否（`apply_phase_pct: false`）
- **non_claims**：≠ Phase closure · ≠ prod browser · ≠ required CI · ≠ 重跑 GA

---

## C_REPORT
<!-- Reviewer · 2026-07-13 -->

**verdict**: `accepted`  
**risk**: low

| AC | 結果 | 註 |
|----|------|-----|
| AC-AI-1 | pass | runbook checklist 含 main／scenario2／兩 job／勿選 default |
| AC-AI-2 | pass | Evidence Schema 欄位表 + 已回填 YAML 與 B_REPORT ga_run 一致 |
| AC-AI-3 | pass | INDEX 20/20 · recorded · advisory／≠ required／≠ Phase closure |
| AC-HUMAN-1 | pass | 引用既有 29157178993 · 本票未造 URL |

**越權檢查**：未改 Dashboard % · 未改 workflows · `apply_phase_pct` 維持 false。  
**過期阻塞句**：FRAME「当前状态」已改 recorded；檔內 06-24 歷史 blocked 審計段保留（可接受）。

### Phase 影響（Reviewer）

- 提案 Δ=0 · 未寫入 % · 通過

---

## D_REPORT
<!-- Scribe · 2026-07-13 -->

- Progress 末尾已 append 本票戰報（含 Phase 影響）
- QUEUE：`W4-P85-S2-GA-RUNBOOK-v1` BLOCKED → DONE（歸檔路徑由 Orchestrator 維護）
- SESSION 已註記
- **下一步建議**：開／施工 `W4-P85-P9-EVIDENCE-SSOT-v1`（P85+P9 URL 皆齊 · evidence_status→complete）

### Phase 影響（Scribe）

- 複述：P8.5 **proposed_delta +0** · **實際上調 否** · 本輪數字格不變
