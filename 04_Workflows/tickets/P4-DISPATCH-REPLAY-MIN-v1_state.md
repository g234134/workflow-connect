# TICKET STATE · P4-DISPATCH-REPLAY-MIN-v1 · same_chat dispatch 最小 runtime

> Wave A 下一刀 · 2026-07-15 · 接 `P4-MULTI-CHAT-SMOKE-PACK-v1` deferred  
> handoff 摘要；跨 chat 以本檔為準

---

## FRAME

- Goal: 交付 same_chat／dispatch 最小 runtime：讀票 → 建議下一角色 → O→B→C→D checklist（結構化 dict）。
- Scope:
  - MUST：`scripts/run_p4_dispatch_replay_min_v1.py`
  - MUST：`docs/p4-dispatch-replay-min-v1.md`
  - MUST：`tests/test_p4_dispatch_replay_min_v1.py`
  - MUST：複用既有 `dispatch_executor`（唯讀）
- NonScope: ≠ prod crew；不裝主艙 crewai／langchain；不開真 chat；不寫 Dashboard Phase%
- AllowedPaths:
  - `scripts/run_p4_dispatch_replay_min_v1.py`
  - `docs/p4-dispatch-replay-min-v1.md`
  - `tests/test_p4_dispatch_replay_min_v1.py`
  - `04_Workflows/tickets/P4-DISPATCH-REPLAY-MIN-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（僅末尾 append）
- BlockedPaths:
  - `core/**`、暗部破壞性維運、venv、.env
  - `.github/workflows/*`
  - Dashboard Phase% 數字格
  - 憲法 §7：Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION
- Dependencies: `P4-MULTI-CHAT-SMOKE-PACK-v1`（smoke pack 已交 review）· phase4 contract · dispatch_executor
- relay_mode: same_chat
- phase_targets: P4
- baseline_pct: 77
- proposed_delta_pct: +1～+2
- apply_phase_pct: false
- AcceptanceCriteria:
  - AC-1: CLI `ok: true`（對已知票，如 P4-MULTI-CHAT-SMOKE-PACK-v1）
  - AC-2: `replay_sequence` 含 O→B→C→D 四步
  - AC-3: `python -m unittest tests.test_p4_dispatch_replay_min_v1 -v` 全綠
  - AC-4: non_claims 明示 ≠ prod multi-agent／≠ Phase% apply

---

## STATE

- overall_status: done
- current_owner: ops
- next_action: 無（本票封存完成）；Phase% 待另開 W-PROG 匯總 · **勿**重開 `W-PROG-wave013`
- last_updated: 2026-07-15 · scribe（same_chat D）
- status_by_role:
  - orchestrator: done — Wave A 下一刀（計劃 deferred）
  - implementer: done
  - reviewer: done — accepted
  - scribe: done — D_REPORT + Progress append

---

## B_REPORT

- changed_files:
  - `scripts/run_p4_dispatch_replay_min_v1.py`（新建）
  - `docs/p4-dispatch-replay-min-v1.md`（新建）
  - `tests/test_p4_dispatch_replay_min_v1.py`（新建）
  - `04_Workflows/tickets/P4-DISPATCH-REPLAY-MIN-v1_state.md`（新建）
- artifacts:
  - 無（stdout dict only；未寫 control_plane 產物）
- verification:
  - `python -m unittest tests.test_p4_dispatch_replay_min_v1 -v` → **Ran 5 tests · OK**
  - `python scripts/run_p4_dispatch_replay_min_v1.py --ticket-id P4-MULTI-CHAT-SMOKE-PACK-v1 --format text` → **ok: True** · recommended_role=reviewer · replay O→B→C→D
  - `python 04_Workflows/_phase_pct_apply.py read` → average_pct=57.89 · **未** apply
- behavior_notes:
  - 僅包裝 `build_dispatch_plan` + 固定 replay 序；不 spawn chat
  - proposed P4 +1～+2 · **未** apply
- deferred_items:
  - Reviewer／Scribe 收口
  - W-PROG 匯總 apply（與 Wave A 他票一併）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary:
  - AC-1：CLI `ok: true`（對 `P4-MULTI-CHAT-SMOKE-PACK-v1`）· Reviewer 重跑綠
  - AC-2：`replay_sequence` 含 O→B→C→D 四步 · 通過
  - AC-3：`python -m unittest tests.test_p4_dispatch_replay_min_v1 -v` → Ran 5 · OK
  - AC-4：non_claims 明示 ≠ prod multi-agent／≠ Phase% apply · 通過
  - 邊界：ChangedPaths ⊆ AllowedPaths；`apply_phase_pct=false`；未觸憲法 §7
  - SSOT：`_phase_pct_apply.py read` → average_pct=57.89 · **本輪未 authorize**
- risk_level: low
- suggestions:
  - Scribe 收口時標 proposed P4 +1～+2 · 實際上調=否／待 W-PROG
  - 下一寫碼票建議見尚書省收口（P2-INDEX-OBS 或 P3-TRACE-LOCAL）

---

## D_REPORT

- docs_updates: 無新增 docs（既有 `docs/p4-dispatch-replay-min-v1.md` 已足）；本輪僅 STATE／本區塊
- progress_entry: 見 Progress 末尾「2026-07-15 · Wave A Scribe 四票封存」合併條（含本票）
- followup_suggestions:
  - proposed P4 +1～+2 · 實際上調=否／待另開 W-PROG（≠ 重開 wave013）
  - 下一可寫碼：`P2-INDEX-OBS-FOOTNOTE-v1` 或 `P3-TRACE-LOCAL-HARDEN-v1`（須尚書省）
- Phase 影響:
  - 影響 Phase：P4
  - baseline：77
  - proposed_delta：+1～+2
  - 實際上調：否
  - non_claims：≠ Phase% apply · ≠ prod multi-agent · ≠ 重開 W-PROG-wave013 · ≠ 改 average（維持 ≈57.89）
- Reviewer：accepted · risk=low · C blocking=無
