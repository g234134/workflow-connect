# P4 Multi-Chat Smoke Pack v1

> **Ticket**: `P4-MULTI-CHAT-SMOKE-PACK-v1`  
> **Date**: 2026-07-15 · Wave A  
> **Goal**: 四角色＋一票 walkthrough **可重跑**驗收包（≠ prod crewai／langchain）

---

## Assets（須齊）

| Layer | Path |
|-------|------|
| Roles | `.cursor/rules/multi_chat_roles.mdc` |
| Skill | `.cursor/skills/multi-chat-ticket-workflow/SKILL.md` |
| Commands | `.cursor/commands/ticket-orchestrator.md` · `ticket-implementer.md` · `ticket-reviewer.md` · `ticket-scribe.md` |
| Contract | `docs/phase4-multi-agent-collaboration-contract-v1.md` |
| State template | `04_Workflows/tickets/_templates/ticket_state.template.md` |
| Walkthrough ticket（本包） | `04_Workflows/tickets/P4-MULTI-CHAT-SMOKE-PACK-v1_state.md` |

---

## One-page walkthrough（same_chat）

```text
1) Orchestrator：開／凍結 FRAME（AllowedPaths／AC／apply_phase_pct=false）
2) Implementer：AllowedPaths 內施工 → 寫 B_REPORT.verification
3) Reviewer：唯讀 diff + B_REPORT → C_REPORT.conclusion
4) Scribe：D_REPORT + Progress 末尾 append（不重排歷史）
```

交棒三行（multi_chat 時每棒貼）：

```text
角色：<orchestrator|implementer|reviewer|scribe>
票號：P4-MULTI-CHAT-SMOKE-PACK-v1
State 路徑：04_Workflows/tickets/P4-MULTI-CHAT-SMOKE-PACK-v1_state.md
```

---

## Re-run commands

```powershell
# Light boot（續棒）
python 04_Workflows/_boot_context.py --mode light --ticket-id P4-MULTI-CHAT-SMOKE-PACK-v1 --role implementer --pretty

# Contract + smoke pack
python -m unittest tests.test_phase4_multi_agent_contract_v1 tests.test_p4_multi_chat_smoke_pack_v1 -v
```

**Expected**：unittest 全綠；light boot `ok: true`（或 ticket 可解析）；**≠** 主艙裝 crewai／langchain。

---

## non_claims

- ≠ prod multi-agent runtime  
- ≠ 繞過 Reviewer 標 done  
- ≠ 自動寫 Dashboard Phase%（`apply_phase_pct=false`）

---

## Phase% proposal (not applied)

| Field | Value |
|-------|-------|
| phase_targets | P4 |
| baseline_pct | 77 |
| proposed_delta_pct | +3 ～ +5 |
| apply_phase_pct | **false** |

---

*P4-MULTI-CHAT-SMOKE-PACK-v1 · smoke runbook*
