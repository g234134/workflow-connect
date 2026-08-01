# TICKET STATE · W5-T2-wave-master-ticket-template-v1 · Wave Master Ticket Schema Template

> Master CP schema SSOT · Wave 5 · 方案 A

---

## FRAME

- Goal: 交付 Wave Master 子票统一 schema 模板（FRAME 扩展栏 + STATE lifecycle + B/C/D/O 区块），使 Wave 1–5 Implementer **只消费、不维护** 主版本。
- Scope:
  - 扩展 `04_Workflows/tickets/_templates/ticket_state.template.md`（Wave Master 扩展占位 + STATE.lifecycle_phase）
  - 新建 `_templates/wave_master_frame_block.template.yaml`（YAML 复制块）
  - 新建 `docs/wave-master-ticket-template-v1.md`（消费说明 SSOT）
  - 四角色 `*_instruction.template.md` 追加 Wave Master 子票提示（各 1–2 句）
- NonScope:
  - 不交付 `ticket_reviewer_checklist.template.md`（**W5-T4**）
  - 不改 `W-MASTER-wave-plan_state.md` 结构
  - 不改 Dashboard Phase%
  - 不动 W5-WC-PRE-06/07
- AllowedPaths:
  - `04_Workflows/tickets/_templates/ticket_state.template.md`
  - `04_Workflows/tickets/_templates/wave_master_frame_block.template.yaml`
  - `04_Workflows/tickets/_templates/*_instruction.template.md`
  - `docs/wave-master-ticket-template-v1.md`
  - `04_Workflows/tickets/W5-T2-wave-master-ticket-template-v1_state.md`
- BlockedPaths:
  - `W-MASTER-wave-plan_state.md`（他 Wave 区块）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 数字
  - `.github/workflows/**`
  - `core/**`
- Dependencies: `W-MASTER-wave-plan_state.md` §Shared Ticket Schema · `docs/wave-master-ticketing-playbook.md` §3.2
- AcceptanceCriteria:
  - AC-1: `ticket_state.template.md` 含 Wave Master 扩展小节（wave_id · observability · non_claims 等）
  - AC-2: `wave_master_frame_block.template.yaml` 存在且与 playbook §3.2 字段一致
  - AC-3: `docs/wave-master-ticket-template-v1.md` 含 Wave 1/2/Wave-next 消费表
  - AC-4: 四 instruction 模板含 Wave Master 子票 cross-ref

### Wave Master 擴展

- wave_id: W5
- lifecycle_phase: C
- phase_targets: [P10]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W-MASTER-wave-plan_state.md §Shared Ticket Schema]
  - downstream_waves: [W5-T4 reviewer checklist 附页对齐]
  - blocks_if_missing: []
- risks:
  - id: RSK-W5-T2-01
    description: 与旧票 FRAME 格式不兼容
    likelihood: M
    impact: L
    mitigation: 扩展栏为可选小节；一般 Multi-Chat 票可省略
    residual: accept
- observability:
  - verify_commands:
    - "rg 'wave_id' 04_Workflows/tickets/_templates/ticket_state.template.md"
    - "rg 'Wave Master' docs/wave-master-ticket-template-v1.md"
  - evidence_artifacts:
    - docs/wave-master-ticket-template-v1.md
    - _templates/wave_master_frame_block.template.yaml
  - trace_fields: [ticket_id, wave_id, lifecycle_phase]
  - success_signals: [template 含 observability 占位 · doc 含消费表]
  - failure_signals: [缺 verify_commands 占位 · 与 W-MASTER §Shared schema 字段不一致]
- non_claims:
  - 不宣稱 template 覆盖所有 future ticket 类型
  - 不交付 W5-T4 reviewer 附页

---

## STATE

- overall_status: done
- implementation_status: closed · C_accepted · D_scribe_done · orch_closed
- lifecycle_phase: closed
- current_owner: orchestrator
- next_action: 无（本票收口完成）· Downstream 见 D_REPORT followup（W5-T4／W5-T5）
- last_updated: 2026-07-09 · Orchestrator（读 D_REPORT → 标 done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  B/C/D 齐 · C_REPORT `accepted`（AC-1–AC-4 PASS · risk=low）·
  D_REPORT + Progress 末尾已 append · O 抽查 template／doc 路径与 instruction xref 绿。
  未改 FRAME／B／C 正文 · Phase% · Dashboard。本票 overall_status=done。

---

## B_REPORT

- changed_files:
  - `04_Workflows/tickets/_templates/ticket_state.template.md`（Wave Master 扩展 + STATE.lifecycle_phase + SSOT 文首指针）
  - `04_Workflows/tickets/_templates/wave_master_frame_block.template.yaml`（新建）
  - `docs/wave-master-ticket-template-v1.md`（新建）
  - `04_Workflows/tickets/_templates/orchestrator_instruction.template.md`
  - `04_Workflows/tickets/_templates/implementer_instruction.template.md`
  - `04_Workflows/tickets/_templates/reviewer_instruction.template.md`
  - `04_Workflows/tickets/_templates/scribe_instruction.template.md`
  - `04_Workflows/tickets/W5-T2-wave-master-ticket-template-v1_state.md`（本档）
- artifacts:
  - Wave Master FRAME YAML 复制块
  - schema 消费说明 doc
- verification:
  - `rg "wave_id" 04_Workflows/tickets/_templates/ticket_state.template.md` → 命中 Wave Master 扩展栏
  - `rg "observability" 04_Workflows/tickets/_templates/ticket_state.template.md` → 命中
  - `Test-Path docs/wave-master-ticket-template-v1.md` → True
  - `Test-Path 04_Workflows/tickets/_templates/wave_master_frame_block.template.yaml` → True
  - 四 instruction 模板均含 `wave-master-ticket-template-v1` 或 Wave Master 子票提示
- behavior_notes:
  - Wave Master 扩展为 FRAME 下可选小节；一般 Multi-Chat 票 backward compatible
  - instruction 层仅追加 cross-ref，不重写 role-prompts/SKILL
- deferred_items:
  - W5-T4 `ticket_reviewer_checklist.template.md` 字段对齐
  - W5-T5 WORKFLOW_INDEX rollup 链接本 doc

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
    独立重跑（2026-07-09 Reviewer）：
    - AC-1 PASS：`ticket_state.template.md` 含 `wave_id` · `lifecycle_phase` · `observability` 等 Wave Master 扩展占位
    - AC-2 PASS：`wave_master_frame_block.template.yaml` 存在；字段与 playbook §3.2／§4.3（wave_id · observability.verify_commands · non_claims 等）一致
    - AC-3 PASS：`docs/wave-master-ticket-template-v1.md` 含 Wave 1 / Wave 2–4 / Wave-next 消费表
    - AC-4 PASS：四 `*_instruction.template.md` 均含 Wave Master 子票提示或 `wave-master-ticket-template-v1` cross-ref
    - FRAME.observability.verify_commands 抽查：`rg wave_id` / `rg Wave Master` 绿；两路径 Test-Path True
    - AllowedPaths 抽查：变更限于 `_templates/**` · `docs/wave-master-ticket-template-v1.md` · 本 state
    - non_claims：doc MVP 边界明示 defer W5-T4／W5-T5，未冒充全类型覆盖
- risk_level: low
- suggestions: |
    非阻塞：W5-T4 reviewer checklist 附页仍 defer — 与 FRAME NonScope 一致，不挡本票。

---

## D_REPORT

- docs_updates: |
    SSOT 已落地：`docs/wave-master-ticket-template-v1.md` + `_templates/ticket_state.template.md` 扩展 +
    `wave_master_frame_block.template.yaml` + 四 instruction cross-ref。
    无需另改 WORKFLOW_INDEX（defer W5-T5 rollup 链接）。
- progress_entry: |
    已 append Progress「2026-07-09 · W5-T2-wave-master-ticket-template-v1 · Scribe 收口」。
- followup_suggestions: |
    1. Orchestrator 读 D_REPORT → overall_status: done
    2. Downstream：W5-T4 reviewer checklist 附页对齐本 schema；W5-T5 链接本 doc
    3. Wave 2+ 开票一律消费本 template（禁止自建 schema 主版本）
