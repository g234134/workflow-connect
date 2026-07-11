# TICKET STATE · WC-DEMO-1 · Wave C M2 E2E demo (test only)

> handoff 摘要檔；**仅用于 E2E walkthrough / nightly smoke**，非生产票。  
> 权威 fixture 路径：`tests/fixtures/e2e_walkthrough/WC-DEMO-1_state.md`  
> 手工 walkthrough 时复制至 `04_Workflows/tickets/WC-DEMO-1_state.md`（见 runbook §1）。

---

## FRAME

- Title: WC-DEMO-1 — Wave C Control Plane M2 E2E demo ticket
- Goal: 供 WC-T7 runbook / runner dry-run 与本地 E2E smoke 使用的简化 demo 票。
- Scope:
  - eligibility → dispatch cards → comms → order intake 链路的 demo 态
  - 产物隔离在 `artifacts/e2e/WC-DEMO-1/`
- NonScope:
  - **非生产票**；不进真实 outbox / order ledger / Progress 里程碑
  - 不修改 live 生产票 STATE；不写入 `artifacts/ticket_comms/` 或 `artifacts/order_ledger/` 默认路径
- AllowedPaths:
  - `artifacts/e2e/WC-DEMO-1/**`
  - `tests/fixtures/e2e_walkthrough/WC-DEMO-1_state.md`
- Dependencies: 无
- VerificationCommands:
  - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`
  - `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run`

---

## STATE

- overall_status: in_progress
- implementation_status: in_progress
- current_owner: implementer
- next_action: ready_for_e2e_walkthrough — Implementer runs M2 E2E smoke per WC-T7 runbook
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: in_progress
  - reviewer: pending
  - scribe: n/a

---

## B_REPORT

- changed_files: （demo fixture · 占位）
- verification: （n/a · test fixture only）

---

## C_REPORT

- conclusion: <!-- n/a · demo fixture -->

---

## D_REPORT

- docs_updates: <!-- n/a · demo fixture -->
