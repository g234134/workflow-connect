# TICKET STATE · <ticket_id> · <ticket_title>

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> **Schema SSOT**：`docs/ticket-schema-master-v1.md` · `W5-T2-wave-master-ticket-template-v1` · 欄位規範見 `docs/wave-master-ticketing-playbook.md` · `W-MASTER-wave-plan_state.md` §Shared Ticket Schema

---

## FRAME
<!-- Orchestrator 填：票的邊界與驗收標準；開票時寫，施工前凍結 -->

- Goal: <!-- 這張票要達成什麼（一句話） -->
- Scope: <!-- 要做什麼（條列） -->
- NonScope: <!-- 明確不做什麼 -->
- AllowedPaths: <!-- 允許改動的路徑 -->
- BlockedPaths: <!-- 禁止碰的路徑 -->
- Dependencies: <!-- 前置票、阻塞項、外部依賴；無則寫「無」 -->
- relay_mode: <!-- same_chat | multi_chat — 見 multi-chat-ticket-workflow skill「relay_mode」 -->
- AcceptanceCriteria: <!-- 怎樣算完成（可驗收條件） -->
### Wave Master 擴展（Wave Master 子票 · 必填）
<!-- 一般 Multi-Chat 票可省略本小節；開 W1–W5 執行子票時 Orchestrator 必須填寫。欄位規範：docs/wave-master-ticketing-playbook.md §3.2 -->

- wave_id: <!-- W1 | W2 | W3 | W4 | W5 | null -->
- group_id: <!-- G1 | G2 | ... | G10 — Full-Phase 票必填 -->
- lifecycle_phase: <!-- B | C | D | O — 開票時通常 B -->
- phase_targets: <!-- 如 P7.5 — 只列 Dashboard Phase 名；不写 % -->
- estimated_cycles: <!-- 1 | 2 -->
- mvp_allowed: <!-- true | false -->
- human_only_prereqs: <!-- [] 或列負責方 + 交付物 -->
- infra_only_prereqs: <!-- [] -->
- security_only_prereqs: <!-- [] -->
- dependencies_detail:
  - upstream_tickets: []
  - downstream_waves: []
  - blocks_if_missing: []
- risks: <!-- id · description · likelihood · impact · mitigation · residual -->
- observability:
  - verify_commands: []
  - evidence_artifacts: []
  - trace_fields: []
  - success_signals: []
  - failure_signals: []
- non_claims: <!-- 本票禁止宣稱的能力；复制适用 global non-claims + 票专属 -->
- ticket_class: <!-- build | doc/spec | scribe/ops | blocked/planning -->
- evidence_tier: <!-- L-local | CI-advisory | GA-remote | n/a — 见 docs/evidence-tier-contract-v1.md -->
- parallel_ok: <!-- true | false -->

---

## STATE
<!-- Orchestrator 維護：當前進度與下一棒；每次角色交棒後更新 -->

- overall_status: <!-- draft | frame_ready | in_progress | review | scribe | awaiting_ops | done | blocked | done_with_gaps -->
- lifecycle_phase: <!-- B | C | D | O — 与 FRAME.wave_id 扩展栏对齐 -->
- current_owner: <!-- orchestrator | implementer | reviewer | scribe | ops -->
- next_action: <!-- 下一棒要做的事（一句話） -->
- last_updated: <!-- YYYY-MM-DD · 角色縮寫 -->
- ops_checklist: <!-- awaiting_ops 時條列 human／ops；否則「無」 -->
  - [ ] <!-- 例：commit／push -->
  - [ ] <!-- 例：workflow_dispatch → 貼 run_url -->
- status_by_role:
  - orchestrator: <!-- pending | done | n/a -->
  - implementer: <!-- pending | in_progress | done | n/a -->
  - reviewer: <!-- pending | in_progress | done | n/a -->
  - scribe: <!-- pending | in_progress | done | n/a -->

---

## B_REPORT
<!-- Implementer 填：施工結果；只寫本區塊，不改 FRAME / STATE -->

- changed_files: <!-- 實際變更的檔案路徑（條列） -->
- artifacts: <!-- 新建模板、報告、截圖等產物；無則「無」 -->
- verification: <!-- 跑過的命令與關鍵結果（ok / 失敗原因） -->
- behavior_notes: <!-- 行為變更或設計取捨（簡短） -->
- deferred_items: <!-- 刻意留到下一張票的項目；無則「無」 -->

---

## C_REPORT
<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- conclusion: <!-- accepted | accepted_with_gaps | needs_changes | rejected -->
- blocking_issues: <!-- 必須修的問題；無則「無」 -->
- checks_summary: <!-- 對照 FRAME 邊界與驗收的檢查摘要 -->
- risk_level: <!-- low | medium | high -->
- suggestions: <!-- 非阻塞建議；無則「無」 -->

---

## D_REPORT
<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->

- docs_updates: <!-- 建議新增或更新的文檔路徑與要點 -->
- progress_entry: <!-- 建議寫入 Progress 末尾的摘要（1–3 句） -->
- followup_suggestions: <!-- 後續票或尚書省待裁決事項；無則「無」 -->
