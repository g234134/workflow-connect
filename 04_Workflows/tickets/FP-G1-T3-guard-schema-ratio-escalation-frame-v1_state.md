# TICKET STATE · FP-G1-T3-guard-schema-ratio-escalation-frame-v1 · W4-GUARD G2–G4 升格 FRAME

> Full-Phase G1 · P3.5 · **opt-in landed**（2026-07-28 · 尚書省「全開」＝批文授權）
> 對齊：`W-MASTER-full-phase-plan_state.md#G1` · 父票 `W4-GUARD-01`
> 收口標籤：`branch_ai_closed`（AI 可達段）≠ Phase closure；**禁**默升產線／required CI

---

## FRAME
<!-- Orchestrator 原凍結 2026-07-10 · 2026-07-28 全開解阻施工 -->

- Goal: W4-GUARD G2–G4（schema／ratio／strict）做成**可開關**升格；預設安全 off；文件寫清啟用方式。
- Scope:
  - MUST：`docs/w4-guard-g2-g4-escalation-frame-v1.md`
  - MUST：`scripts/w4_guard_escalation_v1.py` + E2E 旗標（`--enable-guard-escalation`／`--strict-guards`）
  - MUST：`tests/test_w4_guard_escalation_v1.py`
  - MUST：README §2.3 啟用說明 · Progress／本票留痕
- NonScope:
  - 默認開 strict · 改 required CI／workflows · 改 Phase%
  - 重寫 T1 fixture guard
  - Round-2／DarkOps／L1／K-2
- AllowedPaths（全開後）:
  - `docs/w4-guard-g2-g4-escalation-frame-v1.md`
  - `docs/agent-and-non-tabular-lines-readme-v2.md`（§2.3 一段）
  - `scripts/w4_guard_escalation_v1.py`
  - `scripts/run_case_e2e_validation.py`
  - `tests/test_w4_guard_escalation_v1.py`
  - `04_Workflows/tickets/FP-G1-T3-guard-schema-ratio-escalation-frame-v1_state.md`
  - `04_Workflows/tickets/W4-GUARD-01_state.md`（notes／next_action 一句）
- BlockedPaths:
  - `.github/workflows/**` required／branch protection
  - Dashboard Phase% 數字格
  - 憲法 §7 類型 · DarkOps 根 · `.env`
- Dependencies:
  - **授權**：尚書省「全開」（waive WC-PRE／PM 批文阻塞）
  - 上游：W4-GUARD-01 T1 landed
- AcceptanceCriteria:
  - AC-1：G2/G3/G4 分項 + 開關預設 off
  - AC-2：unittest 綠 · 預設不 fail sampleco E2E
  - AC-3：non_claims：≠ required CI · ≠ 默升產線
  - AC-4：文件寫清如何啟用

### Wave Master 擴展

- group_id: G1
- lifecycle_phase: D
- phase_targets: [P3.5]
- ticket_class: implementer
- evidence_tier: L-local
- non_claims:
  - opt-in landed ≠ GUARD 產線必開 · ≠ required CI
  - ≠ Phase closure
- closure_tags:
  - branch_ai_closed: yes（opt-in 實作）
  - forbid_phase_closure_claim: true

---

## STATE

- overall_status: done
- lifecycle_phase: D
- current_owner: closed
- next_action: closed · opt-in G2–G4 landed · 預設 off · ≠ required CI · tip#1 仍 P6
- last_updated: 2026-07-28T23:55+08:00 · Implementer（全開）
- status_by_role:
  - orchestrator: done（原 arrange + 全開解阻）
  - implementer: done
  - reviewer: pending（可另排）
  - scribe: pending
- auth: 尚書省「全開」＝批文授權（原 blocked_on_approval waived）
- blocked_reason: （已解除）

---

## B_REPORT

- changed_files:
  - `scripts/w4_guard_escalation_v1.py`（新建）
  - `scripts/run_case_e2e_validation.py`（旗標 + sidecar）
  - `tests/test_w4_guard_escalation_v1.py`（新建）
  - `docs/w4-guard-g2-g4-escalation-frame-v1.md`（新建）
  - `docs/agent-and-non-tabular-lines-readme-v2.md`（§2.3）
- verification:
  ```text
  python -m unittest tests.test_w4_guard_escalation_v1 -v
  ```
- behavior_notes:
  - 預設 `evaluate_guard_escalation` → `observation_only_default_safe` · `e2e_fail=False`
  - `--strict-guards` 才會在 G4 訊號下 fail E2E
- deferred_items:
  - Reviewer 收口另排
  - CI required 接入（明確非本票 · 禁默升）

---

## C_REPORT

- conclusion: （待 Reviewer）
- blocking_issues: 無
- risk_level: low（預設 off）

---

## D_REPORT

- docs_updates: `docs/w4-guard-g2-g4-escalation-frame-v1.md` · README §2.3
- progress_entry: 全開戰報
- followup_suggestions: Reviewer 抽樣 sampleco `--strict-guards` vs 預設
