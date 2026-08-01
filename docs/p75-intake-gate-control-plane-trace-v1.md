# P7.5 Intake Gate Control-Plane Trace v1

> **Ticket**: `W1-P75-TRACE-UPSTREAM-v1` · **Wave 1** · **SSOT** for upstream intake/gate trace fields  
> **Scope**: doc-only observability contract — gate CLI → outbox → MP-SMOKE steps 1–2 → metrics  
> **Not**: G-1–G-5 resume-loop **runtime** · staging POST · prod-ready · Phase% change · runtime pipeline completion claims

## Purpose

This document is the **single authoritative registry** of upstream intake/gate trace fields for the control plane:

`run_intake_gate_cli` / `evaluate_intake_gate` → durable outbox record → `intake.gate_decision` notify → MP-SMOKE steps 1–2 → `export_std_case_metrics_v1` → ticket STATE / matrix cross-refs.

**Governance rules**

1. Any **new** upstream trace field MUST be added to §Canonical trace schema (incremental row + changelog note).
2. **Wave 3 / Wave 5 / observer CLI** and Master Reviewer evidence rollups MUST consume field names from this table only — **no ad-hoc field invention**.
3. Deny-path semantics remain owned by `docs/p75-policy-deny-path-mvp-v1.md`; this doc **references** deny fields, does not redefine PM-D3 `reason_code` enum.

G-1–G-5 resume-loop fields appear here as **upstream observability only**; runtime tests remain Wave 2 (`W2-P7-matrix-G1-G5-resume-loop-v1`).

---

## Trace chain (upstream)

```text
[intake CLI / gate CLI]
        ↓ evaluate_intake_gate (preview | run)
        ↓ outbox gate record (run mode only)
        ↓ intake.gate_decision notification (run + notifications enabled)
        ↓ MP-SMOKE step gate_preview | gate_run_notify
        ↓ export_std_case_metrics_v1 (post-smoke drift)
        ↓ ticket STATE / matrix §7.4.1
```

---

## Canonical trace schema (SSOT)

> **Types**: JSON scalar unless noted. **Required** applies when the field's source layer is active (see §Usage scenarios).

### A. Intake request identification

| Name | Type | Required | Semantics |
|------|------|----------|-----------|
| `intake_decision_id` | string | yes (gate result) | Stable id for one gate evaluation; built from `case_ref` + `task_type` + `created_at`. Primary join key to notify envelope (`checkpoint_id` slot) and outbox record. **Alias (deprecated)**: `intake_id` → use `intake_decision_id`. |
| `case_ref` | string | yes | Case slug (e.g. `demo_phase`, `sampleco/2026-0001`); universal join key across P7.5 → P8 → P8.9 → P9. |
| `case_dir` | string | yes (gate) | Repo-relative case directory passed to gate CLI. |
| `task_type` | string | yes | Intake task type (e.g. `tabular.cleaning.mvp`). |
| `schema_version` | string | yes (gate) | Gate result schema id (`intake_gate_result_v1`). |
| `mode` | string | yes | `preview` (no outbox) \| `run` (durable record + optional notify). |
| `created_at` | string (ISO-8601 UTC) | yes (gate) | Gate evaluation timestamp. |

### B. Gate decision fields

| Name | Type | Required | Semantics |
|------|------|----------|-----------|
| `decision` | string | yes | Canonical gate outcome: `accept` \| `review_needed` \| `reject`. **Doc alias**: `gate_decision` ≡ `decision`; `gate_status` ≡ `decision` on CLI/smoke summaries. |
| `reason_codes` | string[] | yes | Ordered deduped policy + v2 reason codes (includes `policy_deny_*` on deny path). |
| `p75_policy_decision` | string | yes (when policy evaluated) | Policy layer trace: `policy_deny` \| `policy_review` \| `policy_pass`. See deny MVP. |
| `deny_reason` | string \| null | yes (when policy evaluated) | Primary PM-D3 `reason_code` when `p75_policy_decision=policy_deny`; else `null`. |
| `gate_checks` | object[] | yes | Rule rows (`rule_id`, `passed`, …) from v2 + policy evaluator. |
| `ok` | boolean | yes (gate) | Gate **evaluation** succeeded (rules + policy ran). **Not** synonymous with `decision=accept`. |
| `risk_level` | string | no | Rules-engine risk tier (`low` \| `medium` \| `high`). |
| `policy_version` | string \| null | no | Loaded policy YAML version when present. |
| `decider` | string | no | Producer id (`intake_gate_layer_v1`). |

### C. Run / observability identification

| Name | Type | Required | Semantics |
|------|------|----------|-----------|
| `run_at` | string (ISO-8601 UTC) | yes (MP-SMOKE summary) | Smoke orchestration run timestamp; observability id for `multi_phase_smoke_run.json`. **Note**: there is no separate top-level `run_id` key in v1 runners — use `run_at` + `case_ref` for smoke runs, `intake_decision_id` for gate decisions. |
| `step_id` | string | yes (smoke step) | MP-SMOKE step id: `gate_preview` \| `gate_run_notify` (upstream scope). |
| `steps[].ok` | boolean | yes (per step) | Step pass/fail in smoke summary (`multi_phase_smoke_run.steps[]`). |
| `outbox_record_path` | string \| null | yes (gate run) | Durable gate JSON path when `mode=run`; `null` on preview. |
| `notification_ok` | boolean | no | Best-effort notify emit result on `gate_run_notify` step detail. |
| `event_type` | string | yes (notify) | Workflow notification type; upstream value: `intake.gate_decision`. |

### D. Cross-phase correlation (minimal · required only)

| Name | Type | Required | Phase | Semantics |
|------|------|----------|-------|-----------|
| `case_ref` | string | yes | P7.5 · P8 · P8.9 · P9 | Shared case key; do not introduce parallel case identifiers in upstream trace. |
| `intake_decision_id` | string | yes (run) | P7.5 → P8.9 | Links gate record, notify envelope, consumer timeline rows. |
| `outbox_record_path` | string | yes (run) | P7.5 · P8.9 audit | Durable gate artifact; referenced in notify `artifacts`. |
| `tracking_status` | string | no | P8.9 | Post-notify ack state: `recorded` \| `pending_ack` \| `acked` \| `failed` (consumer read model). |
| `notifications_failed_ack_count` | integer | no | P8 · P8.9 | Metrics exporter: failed downstream acks for case (post-smoke drift). |
| `notifications_with_pending_ack_count` | integer | no | P8 · P8.9 | Metrics exporter: pending acks after gate notify. |
| `backlog_status` | string | no | P8 (Operator) | Operator backlog rollup via metrics (`pending` \| `blocked` \| `completed` \| …). |

**P8.5 (Browser / bridge)**: no additional upstream gate fields in v1 — correlate by `case_ref` only if a future bridge step consumes gate output.

**P9 (Order / payment)**: upstream gate trace stops at `decision=reject` fail-closed; P9 fields (`order_id`, payment status) are **out of scope** for this SSOT.

### E. Deny-path extensions (cross-ref POLICY-DENY MVP)

| Name | Type | Required | Semantics |
|------|------|----------|-----------|
| `multi_case_smoke_run.cases[].failed_steps` | string[] | no (MC-SMOKE) | Downstream steps that fail after gate reject (e.g. `phi_demo` probe). |
| `multi_case_smoke_run.cases[].gate_decision` | string | no (MC-SMOKE) | Canonical gate outcome from `gate_run_notify` step detail (`decision` alias). |
| `multi_case_smoke_run.cases[].gate_status` | — | **deprecated alias** | Use `gate_decision`; do not add new consumers. |

Authoritative deny enum and golden fixtures: `docs/p75-policy-deny-path-mvp-v1.md`.

### F. G-1–G-5 upstream observability only (not gate steps 1–2)

| Name | Type | Runtime owner | Semantics |
|------|------|---------------|-----------|
| `resume_eligibility` | string | Wave 2 | e.g. `stale_checkpoint` |
| `resume_blocked_reason` | string | Wave 2 | e.g. `revise_needed`, `on_hold` |
| `checkpoint_load_error` | string | Wave 2 | Missing/invalid checkpoint file |
| `case_allowlist_block` | string | Wave 2 | Resume allowlist block |

**Rule**: Fields in §F MUST NOT be cited as proof of gate upstream behavior. See `docs/p7-resume-loop-g1-g5-spec-v1.md` §3.2.

---

## Usage scenarios

### P7.5 — Intake gate control plane

| Scenario | Active fields | Verify |
|----------|---------------|--------|
| Happy path preview | §A + §B (`mode=preview`, `outbox_record_path=null`) | `run_intake_gate_cli --mode preview` |
| Happy path run + notify | §A–C + `event_type=intake.gate_decision` | MP-SMOKE step `gate_run_notify` |
| Policy deny (`phi_demo`) | §B deny fields + §E `failed_steps` | `MC-SMOKE --cases phi_demo` · deny MVP unittest |
| Post-gate ack drift | §D metrics counts | `export_std_case_metrics_v1` |

### P8 — Operator backlog (downstream read)

| Scenario | Fields consumed | Notes |
|----------|-----------------|-------|
| Post-smoke sanity | `case_ref`, `backlog_status`, §D ack counts | MP-SMOKE step 7 + MP-METRICS; gate trace proves upstream only |

### P8.5 — Browser / bridge

| Scenario | Fields consumed | Notes |
|----------|-----------------|-------|
| v1 correlation | `case_ref` only | Bridge stub does not emit gate trace; no v1 extensions |

### P8.9 — Outbox / feedback / dispatch

| Scenario | Fields consumed | Notes |
|----------|-----------------|-------|
| Notify emit | `intake_decision_id`, `decision`, `reason_codes[]`, `outbox_record_path`, `event_type` | `docs/outbox-and-feedback-layer-contract-v1.md` §4.3 |
| Consumer / ack | `tracking_status`, metrics ack counts | Fail-open notify; ack drift via MP-METRICS |
| Verification bundle | `case_ref` | MP-SMOKE step 6; not a gate-field extension |

### P9 — Order / payment

| Scenario | Fields consumed | Notes |
|----------|-----------------|-------|
| Upstream gate block | `decision=reject`, `case_ref` | Payment sandbox runs only after gate accept path; no P9-specific keys in this SSOT |

---

## MP-SMOKE step 1–2 mapping

| Step ID | Gate mode | Outbox write | Notify | Key trace fields |
|---------|-----------|--------------|--------|------------------|
| `gate_preview` | `preview` | **No** | **No** | §A + §B |
| `gate_run_notify` | `run` | **Yes** | **Yes** (best-effort) | §A–C + `event_type=intake.gate_decision` |

### Verify commands (step 1–2)

```bash
# Full seven-step smoke (steps 1–2 = gate preview + run+notify)
python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json

# Gate CLI equivalents (spot-check upstream before smoke)
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview --format json

python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run --enable-notifications --format json

# Post-smoke metrics (ack drift)
python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json

# Doc / matrix keyword sanity
rg "intake_decision_id|intake.gate_decision|canonical trace schema" docs/p75-intake-gate-control-plane-trace-v1.md
```

**Unit tests (read-only references)**: `tests/test_multi_phase_smoke_v1.py` · `tests/test_export_std_case_metrics_v1.py` · `tests/test_intake_gate_policy_integration_v1.py` (deny trace alignment).

---

## Outbox / jsonl (logical paths)

| Artifact | Logical path | When written |
|----------|--------------|--------------|
| Gate outbox record | `outbox/<case_ref>/intake_gate_decision_*.json` (via `outbox_record_path`) | Gate `run` mode |
| Gate events index | `outbox/intake_gate_events.jsonl` | Gate `run` mode |
| Gate decision notify | `outbox/notifications/<case_ref>/intake.gate_decision_*.json` | Run + notifications enabled |
| Notification index | `outbox/notification_events.jsonl` | Notify emit |
| Smoke summary | `outbox/verification/<case_slug>/multi_phase_smoke_run.json` | MP-SMOKE default |

Exact filenames follow P75-G2/G4 implementations; this doc uses logical names only.

---

## Cross-references

| Ticket / doc | Role in trace chain |
|--------------|---------------------|
| `W1-P75-POLICY-DENY-MVP-v1` · `docs/p75-policy-deny-path-mvp-v1.md` | Deny-path fields: `p75_policy_decision` · `deny_reason` · `phi_demo` probe |
| `W1-P75-INTAKE-CLI-MVP-v1` · `docs/p75-intake-cli-upstream-mvp-v1.md` | Case create → gate CLI upstream commands |
| `P75-G2` · `P75-G4` · `P75-REGRESSION` | Gate layer + notify + E2E regression (implemented upstream) |
| `docs/outbox-and-feedback-layer-contract-v1.md` | P8.9 notify enum · ack · dispatch stages |
| `MP-SMOKE` · `MC-SMOKE` | Steps 1–2 orchestration · fleet deny probe |
| `W2-P7-matrix-G1-G5-resume-loop-v1` | Downstream consumer of **resume** fields only (§F) |
| `W5-T3` | Master Reviewer evidence rollup (read-only consumer) |
| Matrix §7.4.1 | CP-T1–CP-T4 control-plane trace rows |

---

## Failure signals

- Smoke step `gate_preview` or `gate_run_notify` `ok=false` while case profile expects accept (e.g. `demo_phase`).
- `notifications_failed_ack_count > 0` **delta** after successful gate run+notify on demo path when using **repo outbox** (CI-SMOKE `--use-repo-outbox` fails on delta>0 only).
- `notifications_failed_ack_count > 0` on **isolated** CI-SMOKE outbox after smoke (absolute rule — indicates smoke run introduced failed ack).
- Deny probe (`phi_demo`) with smoke top-level `ok=true` (should fail-closed).
- Doc or consumer cites G-1–G-5 **runtime** as proven by gate trace SSOT.
- New trace field used in Wave 3/5/observer CLI but **absent** from §Canonical trace schema.

---

## Non-goals (fields and capabilities **not** in this SSOT)

| Item | Reason |
|------|--------|
| `run_id` as a separate v1 key | Not emitted by gate or MP-SMOKE v1; use `intake_decision_id` / `run_at` |
| `intake_id` as canonical name | Deprecated alias; SSOT name is `intake_decision_id` |
| G-1–G-5 resume-loop **runtime** proof | Wave 2; §F is observability names only |
| Staging POST / prod notify SLA | Wave 2–3 transport tickets |
| P8.5 bridge-internal browser session ids | Out of P7.5 upstream scope |
| P9 `order_id` / payment provider fields | Downstream of gate; separate P9 contracts |
| Full gate SLA / UI / SLO / alert keys | Dashboard Phase% and P75 deferred capabilities |
| MC-SMOKE top-level `gate_status` | **Deprecated** — use `gate_decision` on per-case summary |
| Runtime pipeline completion | This ticket delivers **spec + doc only** |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-26 | v1 SSOT: canonical schema table (§A–F), cross-phase §D, governance rules, usage scenarios |
| 2026-07-09 | Reviewer `accepted` · Scribe closeout · AC-1–AC-5 paper + L-local re-run（ticket `W1-P75-TRACE-UPSTREAM-v1`） |
| 2026-07-09 | Cross-ref P7.5 upstream entry index → `docs/p75-upstream-entry-index-v1.md`（`W1-P75-UPSTREAM-ENTRY-INDEX-v1`） |

---

## Downstream consumers

- **Wave 2**: P7 notify / resume-loop runtime — consume gate fields from this SSOT; do not redefine deny trace.
- **Wave 3 / Wave 5 / observer CLI**: read-only; **must** map outputs to §Canonical trace schema only.
- **Wave 5 T3**: Master Reviewer evidence — rollup verify_commands + artifacts listed here.
- **P7.5 upstream entry**: Planner／Orchestrator 接戰入口 → `docs/p75-upstream-entry-index-v1.md`（僅上游 · 全 Wave rollup → W5-T5）。
