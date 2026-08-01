# P4 Dispatch Replay Min v1

> **Ticket**: `P4-DISPATCH-REPLAY-MIN-v1`  
> **Date**: 2026-07-15 · Wave A 下一刀（接 `P4-MULTI-CHAT-SMOKE-PACK-v1`）  
> **Goal**: same_chat／dispatch **最小 runtime** — 讀票 → 建議下一角色 → 印 **O → B → C → D** checklist（≠ prod crew）

---

## What it does

| 步驟 | 行為 |
|------|------|
| 1 | 呼叫既有 `04_Workflows/dispatch_executor.build_dispatch_plan`（唯讀掃票） |
| 2 | 篩出 `--ticket-id` 的 `recommended_role`／`next_action`／bucket |
| 3 | 附上契約固定 replay 序：Orchestrator → Implementer → Reviewer → Scribe |
| 4 | 回傳結構化 `dict`（`ok`／`message`／`non_claims`） |

**不做**：開 Cursor chat、裝 crewai／langchain、改票 STATE、寫 Dashboard Phase%。

---

## Re-run commands

```powershell
python scripts/run_p4_dispatch_replay_min_v1.py --ticket-id P4-MULTI-CHAT-SMOKE-PACK-v1 --pretty
python scripts/run_p4_dispatch_replay_min_v1.py --ticket-id P4-MULTI-CHAT-SMOKE-PACK-v1 --format text
python -m unittest tests.test_p4_dispatch_replay_min_v1 tests.test_dispatch_executor -v
```

**Expected**：`ok: true` · `recommended_role` 非空（或 bucket 可解析）· unittest 全綠。

---

## Upstream

| 層 | 路徑 |
|----|------|
| Contract | `docs/phase4-multi-agent-collaboration-contract-v1.md` §3／§7 |
| Replay guide | `docs/multi-agent-replay-guide-v1.md`（事後分析；本 CLI 為最小 runtime 入口） |
| Smoke pack | `docs/p4-multi-chat-smoke-pack-v1.md` |
| Executor | `scripts/run_dispatch_executor.py` · `04_Workflows/dispatch_executor.py` |

---

## non_claims

- ≠ prod multi-agent runtime  
- ≠ 主艙 crewai／langchain  
- ≠ auto-spawn chats  
- ≠ Dashboard Phase% apply（`apply_phase_pct=false`）

---

## Phase% proposal (not applied)

| Field | Value |
|-------|-------|
| phase_targets | P4 |
| baseline_pct | 77 |
| proposed_delta_pct | +1 ～ +2 |
| apply_phase_pct | **false** |

---

*P4-DISPATCH-REPLAY-MIN-v1 · minimal dispatch replay*
