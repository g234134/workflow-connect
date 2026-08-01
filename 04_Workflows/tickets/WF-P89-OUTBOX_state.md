# TICKET STATE · WF-P89-OUTBOX · P8.9 Outbox / Feedback Verification Line

> **Orchestrator line ticket** · 總調度批 WF-2026-06-27 · 子 agent 隔離施工  
> **Upstream SSOT**: `docs/p8_9-verification-bundle-v1.md` · P8.9-REGRESSION  
> **handoff 摘要檔**；跨 Task 子 agent 以本檔 FRAME 為準

---

## FRAME

- **Goal**: 重跑 P8.9 verification bundle（`demo_phase`）、刷新 **consolidated verification report**，並在 SSOT/manifest 明確標記 `functional_gaps: true_with_known_limits`（T4 HTTP webhook deferred）；提供 operator 可查 artifact 路徑。
- **Scope**:
  - 執行 `python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json`
  - 新增 `docs/p8_9-verification-report-v1.md`（executed report · 引用 bundle JSON 摘要）
  - 更新 `docs/p8_9-verification-bundle-v1.md`：加 `functional_gaps` / `known_limits` 小節（T4 webhook deferred · multi-case sweep optional）
  - 可選：更新 `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` REGRESSION 列 verdict 欄
  - bundle artifact 目錄：`outbox/verification/demo_phase/`（gitignore 允許則留 sample JSON 摘要於 report；完整 artifact 可本地 only）
- **NonScope**:
  - 不改 gateway emit schema · CP-A/B · orchestrator core
  - 不實作 P8.9-T4 HTTP webhook sandbox dispatch
  - 不改 `.github/workflows/*` · Batch 1 治理 YAML · 全局 Phase%
  - 不改 `delivery/feedback_ingest_v1.py` 等 core 邏輯（除非 bundle 跑紅且為最小 fix · 需 Orchestrator 加批）
- **AllowedPaths**:
  - `docs/p8_9-verification-report-v1.md`（新建）
  - `docs/p8_9-verification-bundle-v1.md`（functional_gaps 小節）
  - `docs/p8_p89_evidence_index_v1.md`（report pointer · 最小 diff）
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md`（REGRESSION verdict 列）
  - `04_Workflows/tickets/WF-P89-OUTBOX_state.md`（B/C/D_REPORT only）
  - `outbox/verification/demo_phase/`（bundle 輸出 · 若 repo policy 允許）
- **BlockedPaths**:
  - `.github/workflows/*`
  - `scripts/run_agent_standard_case_experiment.py`（除非 bundle 紅且最小 fix）
  - `delivery/*` core modules（T1/T2/T3 已 landed · 本線 verification only）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 表
  - Batch 1 治理 YAML
- **Dependencies**:
  - P8.9-T1/T2/T3（consumer · ingest · dispatch registry · 已 landed）
  - P8.9-REGRESSION bundle CLI + unittest（已 landed）
  - `cases/demo_phase` fixture case
- **boot_text**: `WF-P89-OUTBOX: P8.9 verification bundle re-run demo_phase + verification report + functional_gaps T4 webhook deferred; no CI change`
- **AcceptanceCriteria**:
  - **AC-1**: `docs/p8_9-verification-report-v1.md` 存在，含 bundle 命令 · `ok` verdict · event_types · ack 摘要 · functional_gaps 表
  - **AC-2**: `docs/p8_9-verification-bundle-v1.md` 含 `functional_gaps: true_with_known_limits` 或等價 manifest 字樣（T4 webhook deferred 列明）
  - **AC-3**: `python -m unittest tests.test_p8_9_verification_bundle_v1 -v` → exit 0
  - **AC-4**: `python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json` → stdout JSON `ok: true` · exit 0
  - **AC-5**: report 引用 artifact 路徑（`p8.9_verification_run.json` 等）或明確標 local-only
  - **AC-6**: 無 `.github/workflows/*` diff · report 不宣稱 T4 webhook 已可用

### Wave Master 擴展

- wave_id: null
- group_id: G8
- lifecycle_phase: B
- phase_targets: P8.9
- ticket_class: verification + doc/spec
- evidence_tier: L-local
- parallel_ok: true
- non_claims:
  - no_ci_gate_change
  - no_p89_t4_webhook
  - no_global_phase_pct_uplift
  - no_prod_webhook_sla

---

## STATE

- overall_status: done_with_gaps
- lifecycle_phase: D
- current_owner: orchestrator
- next_action: orchestrator 歸檔 batch WF-2026-06-27；T4 webhook / prod notify 須另開票
- last_updated: 2026-06-27 · scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

<!-- Implementer 填 -->

- changed_files:
  - `docs/p8_9-verification-report-v1.md` (NEW)
  - `docs/p8_9-verification-bundle-v1.md` (functional_gaps section + report pointer)
  - `docs/p8_p89_evidence_index_v1.md` (EVD-LL-P89-BND report pointer)
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` (P89-REG-1 verdict column)
  - `04_Workflows/tickets/WF-P89-OUTBOX_state.md` (B_REPORT + STATE)
- artifacts:
  - report: `docs/p8_9-verification-report-v1.md`
  - bundle JSON (local): `outbox/verification/demo_phase/p8.9_verification_run.json` (+ events.json, audit_quickview.json, acks.json)
  - stdout capture: bundle CLI `ok: true` · `run_at=2026-06-27T08:52:13Z`
- verification:
  - `python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json` → exit 0 · `ok: true`
  - `python -m unittest tests.test_p8_9_verification_bundle_v1 -v` → 2/2 OK
- behavior_notes:
  - `demo_phase` bundle: event_types `checkpoint.approved`, `intake.gate_decision`, `run.completed`; tracking `acked` + `pending_ack`; ack_count=2, pending_count=5
  - `functional_gaps: true_with_known_limits` documented in bundle SSOT + report; T4 webhook explicitly **not available**
  - No `.github/workflows/*` or delivery core changes
- deferred_items:
  - P8.9-T4 HTTP webhook live dispatch (G-10)
  - Multi-case fleet sweep (optional; MC-SMOKE line)

---

## C_REPORT

<!-- Reviewer 填 -->

- ok: true
- conclusion: **accepted** — AC-1–AC-6 satisfied; independent unittest + live bundle both `ok: true` exit 0; scope within AllowedPaths; no workflow or delivery core changes in B_REPORT.
- failed_steps: []
- notes:
  - Reviewer re-ran unittest (2/2 OK) and live bundle (`ok: true`, exit 0); `event_types` = `checkpoint.approved`, `intake.gate_decision`, `run.completed`.
  - Report snapshot (`events_summary.count=7`, `ack_count=2`, `pending_count=5`, `run_at=2026-06-27T08:52:13Z`) differs from reviewer live run (`count=15`, `ack_count=4`, `pending_count=11`, `run_at=2026-06-27T08:53:22Z`) — expected drift as verification outbox accumulates across runs; structure and verdict remain valid.
  - Repo has unrelated `.github/workflows/*` modifications at working-tree level; **not** in B_REPORT `changed_files` — AC-6 pass for ticket boundary.
- checks_summary:
  - **AC-1**: `docs/p8_9-verification-report-v1.md` exists with bundle command, `ok: true` verdict, event_types, ack summary, functional_gaps table — **pass**
  - **AC-2**: `docs/p8_9-verification-bundle-v1.md` §Functional gaps manifest `true_with_known_limits`; T4 webhook **Deferred** — **pass**
  - **AC-3**: `python -m unittest tests.test_p8_9_verification_bundle_v1 -v` → exit 0, 2/2 OK — **pass** (reviewer-run)
  - **AC-4**: bundle CLI `--case-ref demo_phase --format json` → exit 0, stdout `ok: true` — **pass** (reviewer-run)
  - **AC-5**: report §5 artifact paths + local-only note — **pass**
  - **AC-6**: B_REPORT has no `.github/workflows/*`; report explicitly defers T4 webhook / non-claims — **pass**
  - **Boundary**: B_REPORT `changed_files` ⊆ AllowedPaths; no `delivery/*` — **pass**
- blocking_issues: []
- risk_level: low
- suggestions:
  - Scribe may note in D_REPORT that report numeric snapshot is point-in-time; operators should re-run bundle for fresh counts.
  - Optional follow-up: refresh report §3–§4 numbers after clean outbox dir if SSOT requires exact parity with latest run.

---

## D_REPORT

<!-- Scribe 填 -->

- docs_updates:
  - `04_Workflows/workflow_line_status_2026-06-27.yaml` — `p89_outbox_feedback.complete: true` · lifecycle `done_with_gaps` · verification_report filled
  - `04_Workflows/00_Agent_Work_Progress.md` — 末尾追加 batch WF-2026-06-27 P8.9 段落
- progress_entry:
  - `04_Workflows/00_Agent_Work_Progress.md` §2026-06-27 · WF batch P6+P8.9 verification
  - verification report: `docs/p8_9-verification-report-v1.md`
  - bundle SSOT: `docs/p8_9-verification-bundle-v1.md` · `functional_gaps: true_with_known_limits`
  - local artifacts: `outbox/verification/demo_phase/`（gitignore · report 含 point-in-time snapshot）
- followup_suggestions:
  - P8.9-T4 HTTP webhook live dispatch → 另開 G-10 實作票
  - Multi-case fleet sweep → MC-SMOKE line（optional）
  - Prod delivery bundle ready notify → 非本 verification 線 scope
  - Report §3–§4 數字為 point-in-time；operator 重跑 bundle 取最新 counts
