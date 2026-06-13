#!/usr/bin/env bash
#
# run_wave_c_nightly_smoke.sh — Wave C M2 nightly smoke (~20 min manual sweep)
#
# Demo ticket : WC-DEMO-1
# Artifacts   : artifacts/e2e/WC-DEMO-1/  (isolated; does not touch default outbox/ledger)
# Runbook SSOT: docs/wave_c/WC_T7_e2e_walkthrough_runbook.md
# Log marker  : [WC-SMOKE]  (grep-friendly)
#
# Prerequisites (user-configured — no venv activation in this script):
#   - Run from repo root (AGENTS.md present).
#   - Python on PATH with repo scripts importable. Options:
#       export PYTHON=/path/to/python
#       # or activate gov main cabin first, e.g.:
#       #   . ./04_Workflows/Enter-Main.ps1   (PowerShell)
#       #   source <venv>/bin/activate        (bash)
#   - Bash with heredoc support (Git Bash / WSL / Linux / macOS).
#
# Usage:
#   bash scripts/run_wave_c_nightly_smoke.sh
#
# Boundary: Control Plane E2E pass ≠ INT Tier-A (see WC-T7 runbook §INT gate).
#

set -u
# Intentionally no set -e: some steps may warn non-zero for evening log review.

TICKET="WC-DEMO-1"
ARTIFACT_ROOT="artifacts/e2e/${TICKET}"
TICKET_STATE="04_Workflows/tickets/${TICKET}_state.md"
# Resolve Python: set PYTHON before running, or rely on `python` on PATH after venv activation.
PY="${PYTHON:-python}"

echo "[WC-SMOKE] STEP-00 begin ticket=${TICKET} artifacts=${ARTIFACT_ROOT}"

# ── 0. Working directory and isolated artifact dirs ─────────────────────
echo "[WC-SMOKE] STEP-01 cwd_check"
pwd
test -f AGENTS.md || { echo "[WC-SMOKE] FATAL: not repo root"; exit 1; }

echo "[WC-SMOKE] STEP-02 reset_artifacts_dir"
mkdir -p "${ARTIFACT_ROOT}/cards" "${ARTIFACT_ROOT}/comms" "${ARTIFACT_ROOT}/reports" "${ARTIFACT_ROOT}/governance_snapshot"
# Clean demo isolation dir only; never touch artifacts/ticket_comms/, order_ledger/, control_plane/
rm -f "${ARTIFACT_ROOT}/before_review.md" \
      "${ARTIFACT_ROOT}/orders.jsonl" \
      "${ARTIFACT_ROOT}/dispatch_cards_run.json" \
      "${ARTIFACT_ROOT}/skill_distillation.json" \
      "${ARTIFACT_ROOT}/skill_distillation.fixture_fallback.json"
rm -f "${ARTIFACT_ROOT}/cards/"*.cursor.md 2>/dev/null || true
rm -f "${ARTIFACT_ROOT}/comms/ticket_comms.jsonl" 2>/dev/null || true

# ── 1. Seed demo ticket state (implementer / in_progress) ───────────────
echo "[WC-SMOKE] STEP-03 seed_demo_ticket_state_in_progress"
cat <<'EOF' > 04_Workflows/tickets/WC-DEMO-1_state.md
# TICKET STATE · WC-DEMO-1 · Wave C M2 end-to-end regression demo

> handoff 摘要檔；跨 chat 交棒以本檔為準。仅用于晚间 smoke，非生产票。

---

## FRAME

- Goal: 本地跑通 Wave C M2 Control Plane 链（eligibility → dispatch → comms → order intake）
- Scope:
  - 晚间 smoke 验证；产物写入 artifacts/e2e/WC-DEMO-1/
- NonScope:
  - 生产票 STATE 变更；PR required gate；prod SLA
- AllowedPaths:
  - docs/wave_c/**
  - scripts/**
  - artifacts/e2e/WC-DEMO-1/**
- BlockedPaths:
  - 04_Workflows/tickets/*_state.md（除本 demo 票）
  - artifacts/ticket_comms/**
  - artifacts/order_ledger/**
- Dependencies: 无
- AcceptanceCriteria:
  - docs/wave_c/WC_T7_e2e_walkthrough_runbook.md §1–§4 可串联
- VerificationCommands:
  - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`
  - `python -m unittest tests.test_ticket_eligibility tests.test_dispatch_cards tests.test_ticket_comms tests.test_order_ledger -v`

---

## STATE

- overall_status: in_progress
- implementation_status: in_progress
- current_owner: implementer
- next_action: Implementer runs M2 E2E smoke
- last_updated: 2026-06-13 · orch
- status_by_role:
  - orchestrator: done
  - implementer: in_progress
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- changed_files: 无
- artifacts: 无
- verification: 无
- behavior_notes: demo smoke seed
- deferred_items: 无

---

## C_REPORT

- conclusion: pending
- blocking_issues: 无
- checks_summary: 待 Reviewer 晚间 smoke 后填写
- risk_level: low
- suggestions: 无

---

## D_REPORT

- docs_updates: 无
- progress_entry: 无
- followup_suggestions: 无
EOF

echo "[WC-SMOKE] STEP-03b optional_walkthrough_dry_run"
${PY} scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket "${TICKET}" \
  --artifacts-root artifacts/e2e \
  --dry-run || echo "[WC-SMOKE] WARN: walkthrough dry-run non-zero"

# ── 2. Eligibility ──────────────────────────────────────────────────────
echo "[WC-SMOKE] STEP-04 eligibility_implementer"
${PY} scripts/run_ticket_eligibility.py \
  --ticket "${TICKET}" \
  --requested-role implementer \
  --format json || echo "[WC-SMOKE] WARN: eligibility implementer non-zero"

echo "[WC-SMOKE] STEP-04b eligibility_reviewer_precheck"
${PY} scripts/run_ticket_eligibility.py \
  --ticket "${TICKET}" \
  --requested-role reviewer \
  --format json || echo "[WC-SMOKE] WARN: eligibility reviewer precheck non-zero (expected before review transition)"

# ── 3. Dispatch cards (dry-run → write + eligibility gate) ───────────────
echo "[WC-SMOKE] STEP-05 dispatch_dry_run"
${PY} scripts/run_dispatch_cards.py \
  --refresh-plan \
  --ticket "${TICKET}" \
  --role implementer \
  --eligibility-gate block \
  --dry-run \
  --pretty || echo "[WC-SMOKE] WARN: dispatch dry-run non-zero"

echo "[WC-SMOKE] STEP-06 dispatch_cards_write"
${PY} scripts/run_dispatch_cards.py \
  --refresh-plan \
  --ticket "${TICKET}" \
  --role implementer \
  --eligibility-gate block \
  --out-dir "${ARTIFACT_ROOT}/cards/" \
  --json-summary "${ARTIFACT_ROOT}/dispatch_cards_run.json" \
  --pretty \
|| {
  echo "[WC-SMOKE] WARN: dispatch blocked; retry with force-eligibility (HITL override)"
  ${PY} scripts/run_dispatch_cards.py \
    --refresh-plan \
    --ticket "${TICKET}" \
    --role implementer \
    --eligibility-gate block \
    --force-eligibility \
    --out-dir "${ARTIFACT_ROOT}/cards/" \
    --json-summary "${ARTIFACT_ROOT}/dispatch_cards_run.json" \
    --pretty \
  || echo "[WC-SMOKE] WARN: dispatch force-eligibility still non-zero"
}

# ── 4. Comms (before/after snapshot → dry-run → write JSONL) ────────────
echo "[WC-SMOKE] STEP-07 comms_snapshot_before_review"
cp "${TICKET_STATE}" "${ARTIFACT_ROOT}/before_review.md"
cp "${TICKET_STATE}" "${ARTIFACT_ROOT}/reports/01_in_progress.md"

echo "[WC-SMOKE] STEP-08 comms_seed_review_state"
cat <<'EOF' > 04_Workflows/tickets/WC-DEMO-1_state.md
# TICKET STATE · WC-DEMO-1 · Wave C M2 end-to-end regression demo

> handoff 摘要檔；跨 chat 交棒以本檔為準。仅用于晚间 smoke，非生产票。

---

## FRAME

- Goal: 本地跑通 Wave C M2 Control Plane 链（eligibility → dispatch → comms → order intake）
- Scope:
  - 晚间 smoke 验证；产物写入 artifacts/e2e/WC-DEMO-1/
- NonScope:
  - 生产票 STATE 变更；PR required gate；prod SLA
- AllowedPaths:
  - docs/wave_c/**
  - scripts/**
  - artifacts/e2e/WC-DEMO-1/**
- BlockedPaths:
  - 04_Workflows/tickets/*_state.md（除本 demo 票）
  - artifacts/ticket_comms/**
  - artifacts/order_ledger/**
- Dependencies: 无
- AcceptanceCriteria:
  - docs/wave_c/WC_T7_e2e_walkthrough_runbook.md §1–§4 可串联
- VerificationCommands:
  - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`
  - `python -m unittest tests.test_ticket_state_update_cli -v`

---

## STATE

- overall_status: review
- implementation_status: in_review
- current_owner: reviewer
- next_action: Reviewer validates comms JSONL
- last_updated: 2026-06-13 · impl
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: in_progress
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `artifacts/e2e/WC-DEMO-1/cards/WC-DEMO-1__implementer.cursor.md`
- artifacts:
  - `artifacts/e2e/WC-DEMO-1/dispatch_cards_run.json`
- verification:
  - `python scripts/run_dispatch_cards.py --ticket WC-DEMO-1 --dry-run --pretty` → ok
- behavior_notes: M2 dispatch smoke complete
- deferred_items: 无

---

## C_REPORT

- conclusion: pending
- blocking_issues: 无
- checks_summary: 待 comms JSONL 验证
- risk_level: low
- suggestions: 无

---

## D_REPORT

- docs_updates: 无
- progress_entry: 无
- followup_suggestions: 无
EOF
cp "${TICKET_STATE}" "${ARTIFACT_ROOT}/reports/02_review.md"

echo "[WC-SMOKE] STEP-09 comms_dry_run"
${PY} scripts/run_ticket_state_update_with_comms.py \
  --before "${ARTIFACT_ROOT}/before_review.md" \
  --after "${TICKET_STATE}" \
  --dry-run || echo "[WC-SMOKE] WARN: comms dry-run non-zero"

echo "[WC-SMOKE] STEP-10 comms_write_jsonl"
${PY} scripts/run_ticket_state_update_with_comms.py \
  --before "${ARTIFACT_ROOT}/before_review.md" \
  --after "${TICKET_STATE}" \
  --outbox-dir "${ARTIFACT_ROOT}/comms" || echo "[WC-SMOKE] WARN: comms write non-zero"

# ── 5. Order intake (ready_for_order → create + lookup + replay) ───────
echo "[WC-SMOKE] STEP-11 order_seed_ready_for_order_state"
cat <<'EOF' > 04_Workflows/tickets/WC-DEMO-1_state.md
# TICKET STATE · WC-DEMO-1 · Wave C M2 end-to-end regression demo

> handoff 摘要檔；跨 chat 交棒以本檔為準。仅用于晚间 smoke，非生产票。

---

## FRAME

- Goal: 本地跑通 Wave C M2 Control Plane 链（eligibility → dispatch → comms → order intake）
- Scope:
  - 晚间 smoke 验证；产物写入 artifacts/e2e/WC-DEMO-1/
- NonScope:
  - 生产票 STATE 变更；PR required gate；prod SLA
- AllowedPaths:
  - docs/wave_c/**
  - scripts/**
  - artifacts/e2e/WC-DEMO-1/**
- BlockedPaths:
  - 04_Workflows/tickets/*_state.md（除本 demo 票）
  - artifacts/ticket_comms/**
  - artifacts/order_ledger/**
- Dependencies: 无
- AcceptanceCriteria:
  - order create + lookup 在隔离 JSONL 成功
- VerificationCommands:
  - `python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl lookup --ticket-id WC-DEMO-1`

---

## STATE

- overall_status: review
- implementation_status: done
- current_owner: orchestrator
- next_action: ready_for_order — create order for WC-DEMO-1 E2E demo
- last_updated: 2026-06-13 · rev
- status_by_role:
  - orchestrator: in_progress
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `artifacts/e2e/WC-DEMO-1/comms/ticket_comms.jsonl`
- artifacts:
  - `artifacts/e2e/WC-DEMO-1/comms/ticket_comms.jsonl`
- verification:
  - `python scripts/run_ticket_state_update_with_comms.py --dry-run` → ok
- behavior_notes: comms transition in_progress→review recorded
- deferred_items: 无

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues: 无
- checks_summary: comms JSONL 含 overall_status 变更
- risk_level: low
- suggestions: 晚间 smoke 不跑关票

---

## D_REPORT

- docs_updates: 无
- progress_entry: 无
- followup_suggestions: 无
EOF
cp "${TICKET_STATE}" "${ARTIFACT_ROOT}/reports/03_ready_for_order.md"

echo "[WC-SMOKE] STEP-12 order_create"
${PY} scripts/run_order_intake.py \
  --jsonl-path "${ARTIFACT_ROOT}/orders.jsonl" \
  create \
  --ticket "${TICKET}" \
  --amount-minor 10000 \
  --currency TWD || echo "[WC-SMOKE] WARN: order create non-zero"

echo "[WC-SMOKE] STEP-13 order_lookup"
${PY} scripts/run_order_intake.py \
  --jsonl-path "${ARTIFACT_ROOT}/orders.jsonl" \
  lookup \
  --ticket-id "${TICKET}" || echo "[WC-SMOKE] WARN: order lookup non-zero"

echo "[WC-SMOKE] STEP-14 order_replay_idempotency"
${PY} scripts/run_order_intake.py \
  --jsonl-path "${ARTIFACT_ROOT}/orders.jsonl" \
  create \
  --ticket "${TICKET}" \
  --amount-minor 10000 \
  --currency TWD || echo "[WC-SMOKE] WARN: order replay non-zero"

# ── 6. Governance snapshot (local · non-blocking · isolated output) ─────
echo "[WC-SMOKE] STEP-15 governance_snapshot"
${PY} scripts/generate_toolchain_governance_snapshot.py \
  --ci-context eval-gate-pr \
  --output-dir "${ARTIFACT_ROOT}/governance_snapshot" \
  --write \
  --non-blocking \
  --format json || echo "[WC-SMOKE] WARN: governance snapshot non-zero (non-blocking mode should still exit 0)"

# ── 7. Skill distillation lite (e2e artifacts first; fixture fallback) ──
echo "[WC-SMOKE] STEP-16 distillation_e2e_artifacts"
${PY} scripts/distill_control_plane_skills_lite.py \
  --cards-dir "${ARTIFACT_ROOT}/cards" \
  --comms-jsonl "${ARTIFACT_ROOT}/comms/ticket_comms.jsonl" \
  --reports-dir "${ARTIFACT_ROOT}/reports" \
  --json-out "${ARTIFACT_ROOT}/skill_distillation.json" \
  --pretty \
|| {
  echo "[WC-SMOKE] WARN: e2e distillation insufficient_signals; fallback fixtures"
  ${PY} scripts/distill_control_plane_skills_lite.py \
    --cards-dir tests/fixtures/skill_distillation/cards \
    --comms-jsonl tests/fixtures/skill_distillation/comms/one_comms.jsonl \
    --json-out "${ARTIFACT_ROOT}/skill_distillation.fixture_fallback.json" \
    --pretty \
  || echo "[WC-SMOKE] WARN: fixture distillation non-zero"
}

# ── 8. Module unittest cross-check (not an E2E substitute) ─────────────
echo "[WC-SMOKE] STEP-17 unittest_crosscheck"
${PY} -m unittest \
  tests.test_ticket_eligibility \
  tests.test_dispatch_cards \
  tests.test_ticket_comms \
  tests.test_ticket_state_update_cli \
  tests.test_order_ledger \
  tests.test_order_ledger_integration \
  tests.test_wc_t5_automation_coverage_contract_v1 \
  tests.test_distill_control_plane_skills_lite \
  -v || echo "[WC-SMOKE] WARN: unittest crosscheck had failures"

# ── 9. Summary ──────────────────────────────────────────────────────────
echo "[WC-SMOKE] STEP-99 done"
echo "[WC-SMOKE] artifacts:"
ls -la "${ARTIFACT_ROOT}" || true
ls -la "${ARTIFACT_ROOT}/cards" 2>/dev/null || true
ls -la "${ARTIFACT_ROOT}/comms" 2>/dev/null || true
echo "[WC-SMOKE] grep_summary_hint: grep '\\[WC-SMOKE\\]' <your_log_file>"
echo "[WC-SMOKE] boundary: Control Plane E2E pass ≠ INT Tier-A (see WC_T7 runbook §INT gate)"
