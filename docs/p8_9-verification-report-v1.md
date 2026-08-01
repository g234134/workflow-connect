# P8.9 Verification Report v1

> **Ticket**: WF-P89-OUTBOX · P8.9-REGRESSION re-run  
> **Date**: 2026-06-27  
> **Evidence tier**: `L-local`  
> **SSOT**: `docs/p8_9-verification-bundle-v1.md` · `docs/p8_p89_evidence_index_v1.md` §2.1 **EVD-LL-P89-BND**

---

## 1. Executive summary

| Field | Value |
|-------|-------|
| **Verdict** | **`ok: true`** |
| **functional_gaps** | **`true_with_known_limits`** |
| **case_ref** | `demo_phase` |
| **run_at** | `2026-06-27T08:52:13Z` |

P8.9 consumer / feedback / dispatch closure was re-run via the standard-case verification bundle on `demo_phase`. Experiment, event consumer, audit quickview, and ack aggregation all passed. Known limits remain: **T4 HTTP webhook dispatch is not implemented**; multi-case fleet sweep is optional and out of scope for this report.

---

## 2. Bundle command

```powershell
python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json
```

Flags used (defaults): notifications **on**, dispatch **on** (`GOV_NOTIFICATION_DISPATCH_ENABLED=1`), auto-approve intake **on**.

---

## 3. Events summary

| Field | Value |
|-------|-------|
| `events_summary.ok` | `true` |
| `events_summary.count` | 7 |
| **event_types** | `checkpoint.approved`, `intake.gate_decision`, `run.completed` |
| **tracking_statuses** | `acked`, `pending_ack` |
| `streams_read` | `outbox/notification_events.jsonl` |

**Regression checks (P89-REG-1)**:

- Notification stream includes `checkpoint.approved` and `run.completed`.
- `run.completed` row has `tracking_status=acked` when dispatch enabled.

---

## 4. Acks summary

| Field | Value |
|-------|-------|
| `acks_summary.ack_count` | 2 |
| `acks_summary.pending_count` | 5 |
| `acks.json` schema | `p8_9_verification_acks_v1` |

Downstream ack records were written for dispatched terminal events; pending count reflects events not yet ingested/acked in the isolated verification outbox.

---

## 5. Artifact bundle

Written under `outbox/verification/demo_phase/` (local-only; typically gitignored):

| File | Purpose |
|------|---------|
| `p8.9_verification_run.json` | Run summary (`schema_version`: `p8_9_verification_run_v1`) |
| `events.json` | Merged notification + checkpoint timeline |
| `audit_quickview.json` | Investigation view with `workflow_notifications` |
| `acks.json` | Pending scan + on-disk ack records |

**Operator path**: `outbox/verification/demo_phase/p8.9_verification_run.json` — full stdout JSON from the bundle CLI is equivalent to this summary file after each run.

---

## 6. Functional gaps

| Gap ID | Limit | Status | Notes |
|--------|-------|--------|-------|
| **G-10 / P8.9-T4** | HTTP webhook live dispatch | **Deferred** | Skeleton dry-run only; **not available** for operator use |
| **Multi-case sweep** | Fleet verification across all case profiles | **Optional / deferred** | Single-case `demo_phase` is the REGRESSION anchor; see `MC-SMOKE` for fleet smoke |
| **GA-remote CI** | GitHub Actions bundle job | **Not in scope** | P8.9 bundle is **L-local** only; no `.github/workflows/*` change this wave |

**Non-claims**:

- T4 webhook is **not** production-ready or sandbox-validated.
- This report does **not** assert prod webhook SLA or INT Tier-A closure.
- `ok: true` here means **local bundle regression pass**, not GA-remote or merge-gate pass.

---

## 7. Verification commands

| Command | Result |
|---------|--------|
| `python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json` | exit 0 · stdout `ok: true` |
| `python -m unittest tests.test_p8_9_verification_bundle_v1 -v` | 2/2 OK |

---

## 8. References

| Artifact | Path |
|----------|------|
| Bundle operator spec | `docs/p8_9-verification-bundle-v1.md` |
| Evidence index | `docs/p8_p89_evidence_index_v1.md` |
| Test matrix REGRESSION row | `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7.3 |
| Plan §8 | `04_Workflows/plans/P8.9-outbox-feedback-to-80-plan.md` |
