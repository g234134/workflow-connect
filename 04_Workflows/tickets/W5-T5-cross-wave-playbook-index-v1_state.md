# TICKET STATE · W5-T5-cross-wave-playbook-index-v1 · Cross-wave Playbook Index

> Master CP · Wave 5 · 全 Wave playbook / lane rollup 索引（doc-only）  
> Schema SSOT：`docs/ticket-schema-master-v1.md` · `W5-T2`

---

## FRAME

- Goal: Planner / Orchestrator / 新 chat 接戰時從單一索引找到該讀哪份 playbook、哪條 traversal、哪張票是 SSOT。
- Scope:
  - `04_Workflows/WORKFLOW_INDEX.md` 新節「Wave Master · Wave-next · Multi-Chat」：SSOT 位階 · traversal · ≥6 有效相對路徑
  - `docs/WAVE_PROGRESS_DASHBOARD.md` 新增 §Wave Master 編排敘事（3–8 要點 · **不改 Phase%**）· 含 P10/P10.5 非-runtime 邊界 · WC-PRE-06/07 design/pending_approval
  - 鏈接：wave-master-ticketing-playbook · wave-next-playbook · multi-chat SKILL · multi_chat_roles · W5-T1 commands README · W5-T2 template doc · P7.5 upstream entry（並列 · 非替代）
- NonScope:
  - 不重寫 playbook 正文 · 不合并 W-MASTER 與 W-ORCH state
  - 不排 P10 S1–S15 runtime · 不宣稱 WC-PRE approved · 不上調 Phase%
  - 不改 `.github/workflows/**` · core · tests
- AllowedPaths:
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（敘事 only）
  - `04_Workflows/tickets/W5-T5-cross-wave-playbook-index-v1_state.md`
- BlockedPaths:
  - `.github/workflows/**`
  - `core/**` · `tests/**`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 數字格
  - `W-MASTER-wave-plan_state.md` / `W-ORCH-*_state.md` 正文結構（只讀）
- Dependencies:
  - W5-T1 / W5-T2（commands + schema paths · **已 done**）
  - W1-P75-UPSTREAM-ENTRY-INDEX（並列 P7.5 入口 · 已 done）
  - W-MASTER · W-ORCH · WC-PRE-06/07（敘事 cross-ref）
- AcceptanceCriteria:
  - AC-1：WORKFLOW_INDEX 含 SSOT 位階 + traversal + ≥6 條有效相對路徑
  - AC-2：Dashboard 新節含規劃 vs 執行 vs Reviewer 三階段 · Phase% 不變 · 含 P10 gap 誠實句
  - AC-3：與 W-ORCH lane 表無 hard conflict（衝突以子票 STATE 為準）
  - AC-4：Orchestrator 讀索引即可決定開 Wave Master 還是 Wave-next chat
  - AC-5：commands 路徑引用 **W5-T1**（`.cursor/commands/README.md`）— 原 Master Plan 寫 W1-T2 已按方案 A 刪除/defer → W5-T1（已 done；見 orch_notes）
  - AC-6：non-claims 含「索引就緒 ≠ P10 runtime 排期 ≠ WC-PRE approved ≠ Phase% 上調」

### Wave Master 擴展

- wave_id: W5
- group_id: G4
- lifecycle_phase: B
- phase_targets: [P10]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W5-T1-multi-chat-commands-v1, W5-T2-wave-master-ticket-template-v1, W1-P75-UPSTREAM-ENTRY-INDEX-v1]
  - downstream_waves: [W5-T3 observer 可消費本索引路徑]
  - blocks_if_missing: []
- risks:
  - id: RSK-W5-T5-01
    description: Dashboard 敘事與 Phase% 表混淆
    likelihood: M
    impact: H
    mitigation: 新節標題含「敘事 · Phase% 不變」
    residual: accept
  - id: RSK-W5-T5-02
    description: Master Plan AC-5 仍寫 W1-T2
    likelihood: L
    impact: L
    mitigation: FRAME AC-5 對齊方案 A → W5-T1；orch_notes 留痕
    residual: accept
- observability:
  - verify_commands:
    - "rg \"Wave Master\" 04_Workflows/WORKFLOW_INDEX.md"
    - "rg \"Wave Master\" docs/WAVE_PROGRESS_DASHBOARD.md"
    - "rg \"W5-T1|commands/README\" 04_Workflows/WORKFLOW_INDEX.md"
  - evidence_artifacts:
    - 04_Workflows/WORKFLOW_INDEX.md
    - docs/WAVE_PROGRESS_DASHBOARD.md（敘事節）
  - trace_fields: [index_section, ssot_tier]
  - success_signals: [WORKFLOW_INDEX 鏈接可達 · 無死鏈]
  - failure_signals: [索引聲稱 Phase% 變更 · 與 W-ORCH 矛盾且無註明]
- non_claims:
  - 非 Wave 1–4 功能交付
  - 非 P10/P10.5 runtime 施工排期
  - 非 CI governance required 升格（WC-PRE-06/07 僅索引提及）
  - 非 Phase% 上調
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- implementation_status: closed · C_accepted · D_scribe_done · orch_closed
- lifecycle_phase: closed
- current_owner: orchestrator
- next_action: 无（本票收口完成）· Downstream 见 D_REPORT（W5-T3／W2-P7-matrix）
- last_updated: 2026-07-09 · Orchestrator（读 D_REPORT → 标 done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  同轮 B→C→D→O。AC-5 对齐方案 A（W5-T1）。C=accepted · AC-1–AC-6 PASS。
  未改 Phase% 数字 · 未改 workflows/core。overall_status=done。

---

## B_REPORT

- changed_files:
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.55 Wave Master · Wave-next · Multi-Chat）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（§Wave Master 編排敘事 · Phase% 不變）
  - `04_Workflows/tickets/W5-T5-cross-wave-playbook-index-v1_state.md`
- artifacts:
  - INDEX §1.55 SSOT 位階表 + traversal 三階段 + 8 條相對路徑
  - Dashboard 6 點敘事（含 P10 gap · WC-PRE pending_approval）
- verification:
  - `rg "Wave Master" 04_Workflows/WORKFLOW_INDEX.md` → 命中 §1.55
  - `rg "Wave Master" docs/WAVE_PROGRESS_DASHBOARD.md` → 命中新節
  - `rg "W5-T1|commands/README" 04_Workflows/WORKFLOW_INDEX.md` → 命中 commands SSOT
  - 8 路徑 `Test-Path` 全 True
- behavior_notes:
  - AC-5 寫 W5-T1（非歷史 W1-T2）· 與方案 A／orch_notes 一致
  - §1.6 既有 Wave-next／P7.5 條目改指向 §1.55
- deferred_items:
  - W5-T3 evidence observer 消費本索引路徑
  - playbook §7 可選二次補鏈（非本票必須）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
    独立重跑（2026-07-09 Reviewer）：
    - AC-1 PASS：§1.55 含位階表 + traversal + ≥6 路徑（實測 8 · Test-Path 全 True）
    - AC-2 PASS：Dashboard「Wave Master 編排敘事」含三階段 · P10 gap · WC-PRE design/pending · 標題明示 Phase% 不變；抽查 P10 表行數字未因本票改寫
    - AC-3 PASS：明示衝突以子票 STATE 為準 · 與 W-ORCH 入口並列無 hard conflict
    - AC-4 PASS：決策句「Wave Master vs Wave-next」可操作
    - AC-5 PASS：commands → `.cursor/commands/README.md`（W5-T1）· 非 W1-T2
    - AC-6 PASS：INDEX／Dashboard／FRAME non-claims 齊
    - AllowedPaths 抽查：僅 INDEX · Dashboard 敘事 · 本 state
- risk_level: low
- suggestions: |
    非阻塞：W-MASTER 正文 AC-5 仍寫 W1-T2 — 以本票 FRAME override 為準；可另票 scrub Master Plan 字面。

---

## D_REPORT

- docs_updates: |
    已落地 INDEX §1.55 + Dashboard Wave Master 敘事；§1.6 反向指向 §1.55。
    无需另开产品 doc。
- progress_entry: |
    已 append Progress「2026-07-09 · W5-T5-cross-wave-playbook-index-v1 · Scribe 收口」。
- followup_suggestions: |
    1. Downstream：`W2-P7-matrix-G1-G5-resume-loop-v1`（spec-only）或 `W5-T3` observer
    2. 可选：scrub W-MASTER AC-5 字面 W1-T2 → W5-T1（另票）
