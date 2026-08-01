# TICKET STATE · W5-T6-ticket-schema-relay-ops-ssot-v1 · Schema SSOT：relay_mode / awaiting_ops / ops_checklist

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> **Schema SSOT**：`docs/ticket-schema-master-v1.md` · `W5-T2-wave-master-ticket-template-v1` · 欄位規範見 `docs/wave-master-ticketing-playbook.md`

---

## FRAME
<!-- Orchestrator / Operator (O) 填 -->

- Goal: 將 `relay_mode`、`awaiting_ops`、`ops_checklist` 正式寫入 ticket schema SSOT 與 wave playbook，與現有模板／skill 對齊。
- Scope:
  - MUST：更新 `docs/ticket-schema-master-v1.md`（FRAME.`relay_mode`；STATE.`awaiting_ops`／`ops_checklist`／`current_owner` 含 ops）
  - MUST：更新 `docs/wave-master-ticketing-playbook.md` §3（填寫規範 + 狀態流一句）
  - MUST：Changelog 記一筆；對照 `_templates/ticket_state.template.md` 已有欄位
  - MAY：一句交叉引用 multi-chat-ticket-workflow skill（不複製全文）
- NonScope:
  - 不改憲法／ENGINEERING_CONTRACT 正文
  - 不改 Phase%／required CI／暗部 core
  - 不重寫歷史票 STATE
  - 不實作 P7 push／Round-2
- AllowedPaths:
  - `docs/ticket-schema-master-v1.md`
  - `docs/wave-master-ticketing-playbook.md`
  - `docs/wave-master-ticket-template-v1.md`（若需索引一句）
  - `04_Workflows/tickets/W5-T6-ticket-schema-relay-ops-ssot-v1_state.md`
- BlockedPaths:
  - `AGENTS.md`（除非僅交叉引用一句且 O 另批）
  - `.cursor/rules/engineering-contract.mdc`、`HARNESS_CONSTITUTION.md`
  - `.github/workflows/*`、暗部 `core/*`、env／venv／runtime checkpoints（憲法 §7）
  - 他人票 `*_state.md`；本票以外 FRAME／STATE
- Dependencies: skill／template 已落地 relay_mode／ops_checklist（2026-07-12）；本票只升 SSOT
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1: `ticket-schema-master-v1.md` FRAME 表含 `relay_mode`（`same_chat`|`multi_chat`）與語義
  - AC-2: 同檔 STATE 枚舉含 `awaiting_ops`；含 `ops_checklist`；`current_owner` 可含 `ops`
  - AC-3: `wave-master-ticketing-playbook.md` §3 有對應填寫規範（或明確「見 schema master」）
  - AC-4: Changelog 有 2026-07-12（或當日）條目；non_claims 不宣稱 Phase%／Round-2
  - AC-5: Reviewer 對照 template 欄位名一致（無平行別名）

### Wave Master 擴展

- wave_id: W5
- group_id: G5
- lifecycle_phase: B
- phase_targets:
  - P6
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W5-T2-wave-master-ticket-template-v1]
  - downstream_waves: []
  - blocks_if_missing: []
- risks:
  - id: RSK-SCHEMA-DRIFT-01
    description: schema 與 template／skill 欄位名不一致
    likelihood: L
    impact: M
    mitigation: AC-5 對照 template；禁止自造別名
    residual: accept
- observability:
  - verify_commands:
    - "rg -n \"relay_mode|awaiting_ops|ops_checklist\" docs/ticket-schema-master-v1.md docs/wave-master-ticketing-playbook.md"
  - evidence_artifacts:
    - "本票 B_REPORT verification"
  - trace_fields: []
  - success_signals:
    - "三欄位均在 schema master 有定義"
  - failure_signals:
    - "僅改 template 未改 schema master"
- non_claims:
  - 不宣稱 Phase% 上調
  - 不宣稱 Round-2 GO／required CI
  - 不宣稱歷史票已回填新欄位
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- lifecycle_phase: O
- current_owner: none
- next_action: 無（doc/spec 已關；QUEUE 移 archive）
- last_updated: 2026-07-12 · same_chat O/B/C/D
- ops_checklist: 無
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `docs/ticket-schema-master-v1.md` — FRAME 加 `relay_mode`；STATE 加 `awaiting_ops`／`ops_checklist`／`current_owner: ops` + 狀態流一句；Changelog 2026-07-12
  - `docs/wave-master-ticketing-playbook.md` — §3.1 `relay_mode`；§3.2.1 awaiting_ops／ops_checklist／ops；§3.3 狀態流對齊
  - `docs/wave-master-ticket-template-v1.md` — STATE 索引一句指向 schema master（MAY）
- artifacts: 無
- verification:
  - `rg -n "relay_mode|awaiting_ops|ops_checklist" docs/ticket-schema-master-v1.md docs/wave-master-ticketing-playbook.md 04_Workflows/tickets/_templates/ticket_state.template.md` → 三檔欄位名一致命中
- behavior_notes: 僅升 SSOT／playbook／索引；未改 template 本體（已有欄位）；skill 僅交叉引用一句，未複製全文
- deferred_items: 歷史票 STATE 不回填（NonScope）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    AC-1 PASS：schema master FRAME 表含 relay_mode（same_chat|multi_chat）+ 語義摘要
    AC-2 PASS：STATE 枚舉含 awaiting_ops；含 ops_checklist；current_owner 含 ops
    AC-3 PASS：playbook §3.1／§3.2.1 有填寫規範 + 狀態流一句；權威指向 schema master
    AC-4 PASS：Changelog 2026-07-12；non_claims ≠ Phase%／Round-2／歷史回填
    AC-5 PASS：對照 ticket_state.template.md 欄位名一致（relay_mode／awaiting_ops／ops_checklist／ops），無平行別名
- risk_level: low
- suggestions: 後續新票開 FRAME 時務必填 relay_mode；舊票不強制回填

---

## D_REPORT

- docs_updates:
  - `docs/ticket-schema-master-v1.md` · `docs/wave-master-ticketing-playbook.md`（本票交付）
  - QUEUE／Progress 末尾摘要（本輪）
- progress_entry: >-
    2026-07-12 · W5-T6 done · schema SSOT 納入 relay_mode／awaiting_ops／ops_checklist ·
    Reviewer accepted · ≠ Phase%／Round-2
- followup_suggestions: 無
