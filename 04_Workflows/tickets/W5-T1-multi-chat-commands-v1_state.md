# TICKET STATE · W5-T1-multi-chat-commands-v1 · Multi-Chat Cursor Slash Commands

> Master CP commands SSOT · Wave 5 · 方案 A

---

## FRAME

- Goal: 交付 `.cursor/commands/` Multi-Chat 四角色 slash commands + Wave Master 编排命令，使 Orchestrator/Implementer 不必每次手贴 instruction 模板。
- Scope:
  - 新建 `.cursor/commands/README.md`（命令索引 · paths SSOT）
  - 四角色：`ticket-orchestrator` · `ticket-implementer` · `ticket-reviewer` · `ticket-scribe`
  - Wave Master：`wave-master-orchestrator` · `wave-master-planner` · `wave-master-implementer`
  - 各命令 cross-ref W5-T2 schema · playbook · multi_chat_roles
- NonScope:
  - 不覆盖 wave-next `/orchestrate-wave-next` 等（W-ORCH commands-builder 另线）
  - 不改 `multi-chat-ticket-workflow/SKILL.md` 正文（仅 commands 层）
  - 不改 W-MASTER 结构 · Dashboard Phase% · W5-WC-PRE-06/07
  - 不宣稱 commands 覆盖所有 future cases
- AllowedPaths:
  - `.cursor/commands/**`
  - `04_Workflows/tickets/W5-T1-multi-chat-commands-v1_state.md`
- BlockedPaths:
  - `.github/workflows/**`
  - `core/**`
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md`（除非尚書省另授权）
- Dependencies:
  - `.cursor/rules/multi_chat_roles.mdc`
  - `.cursor/skills/multi-chat-ticket-workflow/SKILL.md`
  - `04_Workflows/tickets/_templates/*_instruction.template.md`（语义对齐 · 只读参考）
  - W5-T2 schema doc（并行 · cross-ref）
- AcceptanceCriteria:
  - AC-1: `.cursor/commands/` 含 ≥4 个 ticket 角色命令 + ≥3 个 wave-master 命令
  - AC-2: `README.md` 列 SSOT 位阶（W5-T1 commands · W5-T2 schema）
  - AC-3: 各命令含必读清单 + 读写范围 + 交棒下一命令
  - AC-4: `rg 'W5-T2' .cursor/commands` 命中 schema cross-ref

### Wave Master 擴展

- wave_id: W5
- lifecycle_phase: C
- phase_targets: [P10]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- observability:
  - verify_commands:
    - "Get-ChildItem .cursor/commands/*.md | Measure-Object | Select-Object -ExpandProperty Count"
    - "rg 'ticket-orchestrator' .cursor/commands/README.md"
  - evidence_artifacts:
    - .cursor/commands/README.md
  - trace_fields: [command_name, role]
  - success_signals: [≥7 command md files · README 索引四角色+Wave Master]
  - failure_signals: [缺 README · 命令无 cross-ref multi_chat_roles]
- non_claims:
  - 非 wave-next 战术 lane 全套 commands
  - 非 Cursor Subagents DISPATCH_GUIDE 替代品

---

## STATE

- overall_status: done
- implementation_status: closed · C_accepted · D_scribe_done · orch_closed
- lifecycle_phase: closed
- current_owner: orchestrator
- next_action: 无（本票收口完成）· Downstream 见 D_REPORT followup（W5-T5／arrange-tasks 可选）
- last_updated: 2026-07-09 · Orchestrator（读 D_REPORT → 标 done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  B/C/D 齐 · C_REPORT `accepted`（AC-1–AC-4 PASS · risk=low）·
  D_REPORT + Progress 末尾已 append · O 抽查 commands 计数与 W5-T2 rg 绿。
  未改 FRAME／B／C 正文 · Phase% · Dashboard。本票 overall_status=done。

---

## B_REPORT

- changed_files:
  - `.cursor/commands/README.md`（新建）
  - `.cursor/commands/ticket-orchestrator.md`
  - `.cursor/commands/ticket-implementer.md`
  - `.cursor/commands/ticket-reviewer.md`
  - `.cursor/commands/ticket-scribe.md`
  - `.cursor/commands/wave-master-orchestrator.md`
  - `.cursor/commands/wave-master-planner.md`
  - `.cursor/commands/wave-master-implementer.md`
  - `04_Workflows/tickets/W5-T1-multi-chat-commands-v1_state.md`（本档）
- artifacts:
  - 7 个 slash command 文件 + README 索引
- verification:
  - `.cursor/commands/*.md` 计数 = 8（7 commands + README）
  - 四角色 ticket-* 命令存在
  - wave-master-* 三命令存在
  - README 列 W5-T1/T2 SSOT 与命令表
- behavior_notes:
  - 命令为 plain markdown（无 frontmatter）· 与 Cursor 1.6+ slash 规范一致
  - 语义对齐 `_templates/*_instruction.template.md` 与 role-prompts，不 duplicate SKILL 全文
  - W5-T5 将链接本 README 作为 commands paths SSOT
- deferred_items:
  - W5-T5 WORKFLOW_INDEX / Dashboard 叙事索引
  - wave-next playbook 命令名与 W-ORCH commands-builder 统一（另票）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
    独立重跑（2026-07-09 Reviewer）：
    - AC-1 PASS：`.cursor/commands/` 含 ticket-*×4 + wave-master-*×3（另有 README + arrange-tasks，计数=9 ≥7）
    - AC-2 PASS：README 文首列 W5-T1 commands · W5-T2 schema SSOT 位阶
    - AC-3 PASS：四角色 ticket-* 均含「必读」「读写范围」「交棒」；wave-master-* 同构
    - AC-4 PASS：`rg 'W5-T2' .cursor/commands` 命中 README / wave-master-orchestrator / wave-master-implementer
    - FRAME.observability.verify_commands 抽查：命令计数与 README `ticket-orchestrator` 命中均绿
    - AllowedPaths 抽查：交付物均在 `.cursor/commands/**` + 本 state；未见越界改 AGENTS／workflows／core
    - non_claims 诚实：README「不覆盖」段与 FRAME 一致（非 wave-next 全套 · 非 DISPATCH 替代）
- risk_level: low
- suggestions: |
    非阻塞：`arrange-tasks.md` 未入 README 命令表 — 可另票或 W5-T5 索引时补一行；不挡本票关票。

---

## D_REPORT

- docs_updates: |
    本票交付物即 `.cursor/commands/README.md`（commands paths SSOT）+ 七 slash 命令；
    无需另开产品 doc。W5-T5 全 Wave rollup 时链接本 README。
- progress_entry: |
    已 append Progress「2026-07-09 · W5-T1-multi-chat-commands-v1 · Scribe 收口」。
- followup_suggestions: |
    1. Orchestrator 读 D_REPORT → overall_status: done
    2. Downstream：W5-T5 索引本 README；可选 README 补 `arrange-tasks` 一行（C 非阻塞）
    3. 并行：W5-T2 Scribe／关票后可开 W2-P7-advisory 或 W5-T5
