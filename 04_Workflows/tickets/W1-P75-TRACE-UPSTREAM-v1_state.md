# W1-P75-TRACE-UPSTREAM-v1 — Gate→Outbox→MP-SMOKE Upstream Trace Contract (evolved W1-T5)

> handoff 摘要檔 · Wave 1 · P7.5 upstream · doc-only trace SSOT

---

## FRAME

- Goal: 定義 P7.5 intake gate **上游** observability trace 欄位為全系統唯一 SSOT；Reviewer 可不跑 staging 即審計 gate CLI → outbox → MP-SMOKE step 1–2 → metrics 鏈；G-1–G-5 僅列上游觀測欄。
- Scope:
  - `docs/p75-intake-gate-control-plane-trace-v1.md`：canonical trace schema（name / type / required / semantics）· 使用場景 · Non-goals · governance 規則
  - cross-ref（已存在 · 本輪確認對齊）：`04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7.4.1 · `docs/wave-master-ticketing-playbook.md` §4.3 P7.5 範例 · deny MVP · intake CLI doc
- NonScope:
  - **不**重做 `W1-P75-POLICY-DENY-MVP-v1`（deny enum / bridge / unittest 已收口）
  - **不**做 G-1–G-5 resume-loop **runtime**（Wave 2 `W2-P7-matrix-G1-G5-resume-loop-v1`）
  - **不**改 gate layer / notify gateway **runtime** · **不**跑 staging POST
  - **不**改 Phase% · Dashboard · `W-MASTER-wave-plan_state.md`
  - **不**宣稱 runtime trace pipeline 已完成（僅 spec + doc）
- AllowedPaths:
  - `docs/p75-intake-gate-control-plane-trace-v1.md`
  - `04_Workflows/tickets/W1-P75-TRACE-UPSTREAM-v1_state.md`
- BlockedPaths:
  - `routing/intake_gate_layer_v1.py` · `routing/intake_gate_policy_bridge_v1.py`（POLICY-DENY 已收口）
  - `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md` · `AGENTS.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` · `04_Workflows/00_Agent_Work_Progress.md` · `project_status/master_status.md`
  - `.github/workflows/**` · `core/**`
- Dependencies:
  - `W1-P75-POLICY-DENY-MVP-v1`（done · accepted）— deny trace 欄位 cross-ref
  - `P75-G2` · `P75-G4` · `MP-SMOKE` · `MC-SMOKE`（只讀參考）
  - downstream: Wave 2 P7 notify · **W5-T3** evidence observer
- AcceptanceCriteria:
  - AC-1：**上述規格檔** `docs/p75-intake-gate-control-plane-trace-v1.md` **已存在**，含 canonical schema 表（≥8 欄位行 · 分 §A–F）· 使用場景（P7.5 / P8 / P8.5 / P8.9 / P9）· Non-goals · **且通過 Reviewer 審查**
  - AC-2：**未來任何新 upstream trace 欄位必須在此表增量記錄**（doc §Governance rules + Changelog）；禁止 shadow 欄位名
  - AC-3：**Wave 3 / Wave 5 / observer CLI 只消費此表**，禁止自創欄位；矩陣 §7.4.1 · playbook §4.3 引用本 SSOT
  - AC-4：MP-SMOKE step 1–2 各 ≥1 verify_command（引用既有 runner）；G-1–G-5 標 **upstream observability only · runtime = Wave 2**
  - AC-5：non-claims 含「local slot / smoke ok ≠ staging prod-ready」·「doc-only ≠ runtime pipeline 完成」· 不重寫 deny MVP

---

## STATE

- overall_status: done
- implementation_status: doc_complete · verify_evidence_landed · scribe_closed
- lifecycle_phase: closed
- current_owner: orchestrator
- next_action: >-
  本票已關。Downstream：`W1-P75-UPSTREAM-ENTRY-INDEX-v1` 匯總 trace／CLI 入口；
  Wave 2／W5-T3 只消費 `docs/p75-intake-gate-control-plane-trace-v1.md`（禁止自創欄位）。
- last_updated: 2026-07-09 · Orchestrator（Scribe D_REPORT + Progress 收口 → done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  收口核對：C=`accepted`（AC-1–AC-5 PASS · risk=low · blocking 無）·
  D_REPORT 已寫 · Progress 末尾「2026-07-09 · W1-P75-TRACE-UPSTREAM-v1 · Scribe 收口」已存在。
  標 overall_status=done。未改 B/C/D_REPORT／FRAME／code · Phase% · Dashboard。

---

## B_REPORT

- changed_files:
  - `docs/p75-intake-gate-control-plane-trace-v1.md`（升級為 canonical SSOT：§A–F schema · 使用場景 · Non-goals · governance · changelog）
  - `04_Workflows/tickets/W1-P75-TRACE-UPSTREAM-v1_state.md`（新建 · FRAME + AC 具體化）
- artifacts:
  - `docs/p75-intake-gate-control-plane-trace-v1.md`
- verification:
  - `rg "intake_decision_id|Canonical trace schema|Non-goals" docs/p75-intake-gate-control-plane-trace-v1.md` → matches §Canonical trace schema · §Non-goals · governance rules
  - `rg "W1-P75-TRACE-UPSTREAM-v1" 04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md docs/wave-master-ticketing-playbook.md` → matrix §7.4.1 · playbook §4.3 cross-ref 已對齊 SSOT 路徑
  - **D-phase（2026-06-27 · Groundwork Technical Closer · evidence_tier=L-local · re-run）**:
    - `python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json` → `ok=true` · steps `gate_preview`/`gate_run_notify` `ok=true` · `intake_decision_id=igd_*` · `event_type=intake.gate_decision`
    - `python scripts/run_intake_gate_cli.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview --format json` → gate JSON 含 `intake_decision_id` · `decision` · `mode=preview`
    - `python scripts/run_intake_gate_cli.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode run --enable-notifications --format json` → `outbox_record_path` 非 null · notify 已 emit
    - `python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json` → `std_case_metrics_v1.notifications_*_ack_count` 可读
    - `python -m unittest tests.test_multi_phase_smoke_v1 tests.test_export_std_case_metrics_v1 tests.test_intake_gate_policy_integration_v1 -v` → 11/11 OK
    - AC-4 G-1–G-5：§F 仅 observability 名 · matrix YAML `gate_trace_status=active` cross-ref SSOT
- behavior_notes:
  - **Spec（B）**：盤點 deny MVP + gate layer + outbox contract + MP-SMOKE/MP-METRICS 既有欄位；合併為 §A–F canonical 表；`intake_decision_id` 為正式 intake id（`intake_id` 標 deprecated alias）；`run_at` 為 smoke observability id（v1 無獨立 `run_id` 鍵）。
  - **Deny MVP 未改**：`p75_policy_decision` · `deny_reason` 語意仍引用 `docs/p75-policy-deny-path-mvp-v1.md`。
  - **Cross-phase §D**：僅列 P8/P8.9/P9 必需關聯欄（`case_ref` · `intake_decision_id` · ack metrics）；P8.5/P9 專屬欄位明示 out of scope。
- deferred_items:
  - MC-SMOKE summary 頂層 `gate_status` 鍵（doc 標 deferred · 消費 step detail）
  - Reviewer C_REPORT · Scribe 关票
  - Runtime trace pipeline（本票 doc-only · 非 blocking）

---

## C_REPORT

- conclusion: accepted
- reviewer_date: 2026-07-09 · Reviewer (C)
- verdict: accepted
- blocking_issues: 無
- checks_summary: |
    **已讀**：FRAME / B_REPORT / O_OBSERVE · `docs/p75-intake-gate-control-plane-trace-v1.md` · matrix §7.4.1 · playbook §4.3 · 憲法 §7 類型（本票未觸禁區）· multi_chat_roles §Reviewer。
    **邊界（Rule 3/8）**：B 變更僅 AllowedPaths 內 doc + state；未改 gate/policy runtime、Phase%、Dashboard、CI、憲法／合約。
    **AC-1 PASS**：SSOT 存在 · §A–F schema（每節 ≥ 多欄位行）· Usage（P7.5/P8/P8.5/P8.9/P9）· Non-goals。
    **AC-2 PASS**：§Governance rules（新欄位必須增量入表 + changelog）· Changelog 2026-06-26 條目。
    **AC-3 PASS**：matrix §7.4.1 CP-T1–T4 + Doc SSOT 句引用本票路徑；playbook §4.3 P7.5 example `evidence_artifacts` / `verify_commands` 指向同 SSOT。
    **AC-4 PASS（Reviewer 2026-07-09 獨立重跑）**：
      - MP-SMOKE `ok=true` · `gate_preview`/`gate_run_notify` 皆 `ok=true` · join keys `intake_decision_id=igd_*` · `event_type=intake.gate_decision`（run+notify）
      - Gate preview：`ok=true` · `mode=preview` · `decision=review_needed` · `intake_decision_id` 存在
      - Gate run：`outbox_record_path=outbox/demo_phase/intake_gate_decision_*.json` 非 null
      - Metrics：`notifications_failed_ack_count` / `notifications_with_pending_ack_count` 可讀（repo outbox 歷史值）
      - §F / CP-T4：G-1–G-5 標 upstream observability only · runtime = Wave 2
    **AC-5 PASS**：Non-goals 含 doc-only ≠ runtime pipeline · 無 `run_id` 頂層鍵 · 不重寫 deny MVP · 非 prod-ready / Phase%。
    **四流派**：Context+Source 可追溯 · Incremental=doc SSOT · Debugging=verify_commands 可重跑（Rule 11）。
- risk_level: low
- suggestions: |
    1. **非阻塞**：`tests.test_intake_gate_policy_integration_v1` 今日重跑 **9/11**（`test_golden_demo_phase_snapshot` · `test_golden_deny_fixtures_snapshot` FAIL — `reason_codes` 順序／多一碼 `manual_review_required`）。屬 POLICY-DENY／golden 漂移，**不在本票 AllowedPaths**，亦不否定 SSOT 欄位契約；建議另票或 deny MVP 維護者重對 golden，勿在本票修 runtime。
    2. Scribe：Progress 末尾摘要標 **doc-only SSOT accepted** · 指向 `docs/p75-intake-gate-control-plane-trace-v1.md` · 下游 `W1-P75-UPSTREAM-ENTRY-INDEX-v1`。
    3. Orchestrator：讀本 C_REPORT → `overall_status: scribe` · `current_owner: scribe`（Reviewer 不改 STATE）。

---

## D_REPORT

- scribe_date: 2026-07-09 · Scribe (D)
- finisher_verify_date: 2026-06-27 · Groundwork Technical Closer；Reviewer 獨立重跑 2026-07-09
- verdict_echo: Reviewer `accepted` · risk=low · blocking 無 · AC-1–AC-5 紙面 + L-local 重跑 PASS
- test_results:
  - doc SSOT §A–F · governance · changelog · Non-goals 已落地
  - matrix §7.4.1 CP-T1–T4 · playbook §4.3 · deny／intake-CLI docs 已交叉引用本 SSOT（本輪無需再改 xref）
  - Reviewer 2026-07-09：MP-SMOKE step 1–2 `ok=true` · gate preview/run join keys · metrics ack counts 可讀
  - **非阻塞備註（C）**：`test_intake_gate_policy_integration_v1` golden 2 FAIL（`reason_codes` 漂移）— 不在本票 scope；另票維護
- verify_commands:
  ```bash
  python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json
  python scripts/run_intake_gate_cli.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview --format json
  python scripts/run_intake_gate_cli.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode run --enable-notifications --format json
  python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json
  rg "intake_decision_id|intake.gate_decision|Canonical trace schema" docs/p75-intake-gate-control-plane-trace-v1.md
  ```
- evidence_tier: L-local
- known_boundaries:
  - v1 無 `run_id` 頂層鍵；gate 用 `intake_decision_id` + `created_at`，smoke 用 `run_at`
  - P8.5 bridge 僅 `case_ref` 關聯；G-1–G-5 runtime = Wave 2
- docs_updates:
  - `docs/p75-intake-gate-control-plane-trace-v1.md` — 本票 SSOT（B 已交；本輪僅 Changelog 收口一行）
  - matrix §7.4.1 / playbook §4.3 / deny·CLI docs — 既有 xref，本輪不重寫
- non_claims_echo: >-
  **doc-only SSOT** · **非 runtime pipeline 完成** · **非 prod-ready** ·
  **非 Phase% 上調** · deny MVP 未重寫 · G-1–G-5 僅 observability 名
- progress_entry: >-
  見 `04_Workflows/00_Agent_Work_Progress.md` 末尾 —
  **2026-07-09 · W1-P75-TRACE-UPSTREAM-v1 · Scribe 收口**
- followup_suggestions:
  - Orchestrator：讀本 D_REPORT → 已標 `overall_status: done`（本輪併收）
  - Downstream：`W1-P75-UPSTREAM-ENTRY-INDEX-v1` 匯總 CLI + trace 入口
  - 可選另票：對齊 `test_intake_gate_policy_integration_v1` golden `reason_codes`（非本票）

---

## O_OBSERVE

| 观测点 | 路径 / 命令 | 期望字段 | 2026-06-27 实测 |
|--------|-------------|----------|-----------------|
| Gate CLI preview | `run_intake_gate_cli.py --mode preview --format json` | §A + §B | `ok=true` · `intake_decision_id=igd_*` · `decision=review_needed` · `mode=preview` |
| Gate CLI run | `run_intake_gate_cli.py --mode run --enable-notifications --format json` | §A–C | `ok=true` · `outbox_record_path=outbox/demo_phase/intake_gate_decision_*.json` |
| MP-SMOKE step detail | steps `gate_preview`/`gate_run_notify` in smoke JSON | §A–C | both `ok=true` · `intake_decision_id=igd_2026-06-26T20-00-36Z_*` · `event_type=intake.gate_decision` |
| Outbox gate record | logical `outbox/<case_ref>/intake_gate_decision_*.json` | §A–B | written on run mode (path echoed in gate CLI) |
| Notify artifact | `outbox/notifications/<case_ref>/intake.gate_decision_*.json` | `event_type` · `checkpoint_id` | `event_type=intake.gate_decision` (smoke step detail) |
| Post-smoke metrics | `export_std_case_metrics_v1.py --case-ref demo_phase` | §D ack counts | `std_case_metrics_v1.notifications_failed_ack_count=1` · `notifications_with_pending_ack_count=49` · `operator_status=pending` |
| Matrix cross-ref | `standard-case-hitl-resume-notify-matrix.md` §7.4.1 CP-T1–T4 | SSOT join keys | CP-T1–T3 verify_commands match D_REPORT · CP-T4 §F upstream-only |
| Playbook cross-ref | `docs/wave-master-ticketing-playbook.md` §4.3 | trace_fields list | references `docs/p75-intake-gate-control-plane-trace-v1.md` |
| Reviewer 纸面审计 | `docs/p75-intake-gate-control-plane-trace-v1.md` | AC-1–AC-5 | §A–F · governance · changelog · Non-goals · verify_commands block |

### Reviewer AC checklist (paper audit)

| AC | Evidence location | Finisher status |
|----|-------------------|-----------------|
| AC-1 | `docs/p75-intake-gate-control-plane-trace-v1.md` §A–F · usage · Non-goals | **ready** — ≥8 field rows per section |
| AC-2 | same doc §Governance rules + Changelog | **ready** — incremental-only rule + 2026-06-26 entry |
| AC-3 | matrix §7.4.1 · playbook §4.3 P7.5 example | **ready** — both cite SSOT path |
| AC-4 | D_REPORT verify_commands · MP-SMOKE step 1–2 · metrics | **ready** — L-local re-run 2026-06-27 |
| AC-5 | Non-goals table · D_REPORT non_claims_echo | **ready** — doc-only · no delivery/GA · deny MVP untouched |
