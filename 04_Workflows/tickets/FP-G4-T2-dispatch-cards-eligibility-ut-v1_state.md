# TICKET STATE · FP-G4-T2-dispatch-cards-eligibility-ut-v1 · unresolved-dependency UT

> Full-Phase · group_id **G4** · **build** · execute 2026-07-11
> 對齊：`W-MASTER-full-phase-plan_state.md#G4` · WC-T1-INTEGRATION deferred UT
> 收口：`branch_ai_closed` ≠ Phase closure

---

## FRAME
<!-- Orchestrator 填：2026-07-11 凍結 -->

- Goal: 補齊 dispatch cards eligibility gate 對 **unresolved-dependency** 的集成 UT（WC-T1-INTEGRATION deferred）。
- Scope:
  - MUST：`tests/test_dispatch_cards.py` 增 unresolved-dependency + `--eligibility-gate block` 場景（跳過寫卡 + reasons 含 `dependency_unresolved:`）
  - MUST：依賴已 done 時 gate=block 仍可寫卡（對照）
  - MUST：fixtures under `tests/fixtures/dispatch/`（TEST-DEP / plan / done prereq）
  - MAY：本票 STATE B/C/D_REPORT；QUEUE 同步
- NonScope:
  - 改 `ticket_eligibility.py` 判定規則（除非 blocker bug）
  - 入口 B（hooks）／入口 C（build_dispatch_plan annotate）
  - 代跑 GA／改 workflows／Phase%／暗部
- AllowedPaths:
  - `tests/test_dispatch_cards.py`
  - `tests/fixtures/dispatch/**`
  - `04_Workflows/tickets/FP-G4-T2-dispatch-cards-eligibility-ut-v1_state.md`
  - `04_Workflows/command_queue/QUEUE.yaml`（Orchestrator／Scribe）
  - `04_Workflows/command_queue/SESSION.md`（append）
- BlockedPaths:
  - `04_Workflows/ticket_eligibility.py`（除非 blocker）
  - `.cursor/hooks/**` · `04_Workflows/dispatch_executor.py` 分桶邏輯大改
  - `core/**` · 暗部 · `.github/workflows/**` · Dashboard Phase% 數字格
  - 治理母本全文 · `master_status.md`／`handoff.md`
  - `00_Agent_Work_Progress.md`（僅 Scribe 末尾）
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 其他票 FRAME／STATE（除本票報告區）
- Dependencies:
  - WC-T1-INTEGRATION（accepted_with_gaps · 已關）
- AcceptanceCriteria:
  - AC-1：`gate=block` + unresolved dep fixture → `cards_generated=0` · `eligibility_blocked` 含 `dependency_unresolved:W9-T9`
  - AC-2：同 fixture 且 prereq `overall_status=done` → `cards_generated=1` · 無 `eligibility_blocked`
  - AC-3：`python -m unittest tests.test_dispatch_cards tests.test_ticket_eligibility -v` 全綠
  - AC-4：non_claims 明示 ≠ Phase closure／GA／Round-2 GO

### Wave Master 擴展

- wave_id: null
- group_id: G4
- lifecycle_phase: O
- phase_targets: [P4]
- ticket_class: build
- evidence_tier: L-local
- parallel_ok: true
- non_claims:
  - UT 就緒 ≠ Phase closure／prod flip／required CI
  - ≠ Round-2 GO · ≠ WC-PRE approved · ≠ GA 已跑
  - ≠ 入口 B/C 已實作
- closure_tags:
  - branch_ai_closed: true
  - forbid_phase_closure_claim: true

---

## STATE

- overall_status: done
- implementation_status: ut_delivered · reviewer_accepted · scribe_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 無 · 本票已關；human H1/H2（GA／P6）仍見 QUEUE human_ops_sequence
- last_updated: 2026-07-11 · D（scribe_closed · overall done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  2026-07-11 繼續工作：Batch-3 AI 已空；解鎖 unplanned FP-G4-T2（WC-T1 已關）同輪 O→B→C→D。
- reviewer_notes: >-
  AC-1–AC-4 PASS；conclusion=accepted；交棒 scribe。
- closure_tag: branch_ai_closed

---

## B_REPORT

- changed_files:
  - tests/test_dispatch_cards.py（TestDispatchCardsEligibilityUnresolvedDep ×2）
  - tests/fixtures/dispatch/dep_unresolved_ticket.md（新建）
  - tests/fixtures/dispatch/dep_unresolved_plan.json（新建）
  - tests/fixtures/dispatch/dep_done_prereq.md（新建）
  - 04_Workflows/tickets/FP-G4-T2-dispatch-cards-eligibility-ut-v1_state.md
  - 04_Workflows/command_queue/QUEUE.yaml
- artifacts:
  - unittest L-local · 23/23 OK（dispatch_cards + ticket_eligibility）
- verification:
  - cmd: `python -m unittest tests.test_dispatch_cards tests.test_ticket_eligibility -v`
  - result: ok · Ran 23 tests · OK（含 unresolved-dep skip + dep-done allow）
- behavior_notes: >-
  未改 ticket_eligibility 規則／hooks／workflows／Phase%／暗部；
  僅補 WC-T1 deferred 集成 UT。
- deferred_items: 入口 B/C · human H1–H7

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
  AC-1 PASS：gate=block + TEST-DEP → cards_generated=0 · dependency_unresolved:W9-T9
  AC-2 PASS：W9-T9 done → cards_generated=1 · eligibility_blocked=[]
  AC-3 PASS：23/23 OK
  AC-4 PASS：non_claims 置頂；未越權改 workflows／Phase%／core／eligibility 規則
- risk_level: low
- suggestions: 入口 B/C 仍另票；勿把本 UT 當 Phase／GA 收口

---

## D_REPORT

- docs_updated:
  - 04_Workflows/command_queue/QUEUE.yaml（NOT_PLANNED→DONE · stats · priority_next）
  - 04_Workflows/command_queue/SESSION.md（append）
  - 04_Workflows/00_Agent_Work_Progress.md（末尾 append）
- progress_appended: true
- notes: >-
  branch_ai_closed · ≠ Phase closure · ≠ GA 已跑 · ≠ Round-2 GO；
  下一步仍 human H1/H2（07-11 GA + P6 開窗）。
