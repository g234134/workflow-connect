# Multi-Phase 80% — Integrated Execution Plan

> **Role**: Program Planner  
> **Date**: 2026-06-16  
> **Scope**: Planning & sequencing only — **no runtime code changes**  
> **Inputs**: `P8.9-outbox-feedback-to-80-plan.md` · `phase-7.5-intake-gate-to-80-plan.md` · `phase-8-commercial-delivery-to-80-plan.md` · `docs/WAVE_PROGRESS_DASHBOARD.md` · `W7-standard-case-v2_tech-roadmap-draft.md`

---

## 1. Executive summary

Three parallel product-technical tracks must reach **~80% runtime** from current baselines:

| Track | Baseline | Target | Ticket count (80% slice) |
|-------|----------|--------|--------------------------|
| **P8.9** Outbox / Feedback | ~62% | **80%** | **3** (T1–T3); T4 optional |
| **Phase 7.5** Intake Gate | ~62% | **80%** | **4** (G1–G4) |
| **Phase 8** Commercial Delivery | ~68% | **80%** | **2** (P8-T1, P8-T2); P8-T3 deferred |

**Critical reconciliation**: Phase 8 original plan lists **P8-T3 Notify v1.5** (live webhook + retry + DLQ) for 75–80%. P8.9 plan explicitly states **80% does not require real HTTP webhook** — local dispatch registry (P8.9-T3) satisfies M5. **Integrated 80% for Phase 8** = bundle schema + operator CLI surface + **event-driven local notify via P8.9-T3**, not full NOTIFY-v2. Defer **P8-T3** and **P8.9-T4** to post-80% stretch (85%+ / W7 Package 3).

**Recommended overall sequence**: Unblock PM → Foundation wave (contracts + ledger + bundle) → Wiring wave (gate layer + feedback + operator) → Closure wave (dispatch + notify events + regression smoke).

---

## 2. Three-track dependency graphs (text)

### 2.1 P8.9 — Outbox / Feedback (62% → 80%)

```
[W6-T10 gateway · WB-T3 contract · WB-T5 audit]  (done)
                    │
                    ▼
         ┌──────────────────────┐
         │  P8.9-T1             │  ◄── START (no upstream blockers)
         │  Event ledger +      │
         │  tracking consumer   │
         └──────────┬───────────┘
                    │
         ┌──────────┴───────────┐
         ▼                      ▼
┌─────────────────┐   ┌─────────────────┐
│  P8.9-T2        │   │  (design only)  │
│  Feedback ingest│   │  T3 prep: YAML   │
│  + downstream   │   │  handler registry│
│  ack            │   └────────┬────────┘
└────────┬────────┘            │
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌──────────────────────┐
         │  P8.9-T3             │
         │  Dispatch registry   │──────► W7-T3 controlled_notify (handler v1)
         │  + local handler     │        P8-T1 bundle_ready payload (soft)
         └──────────┬───────────┘
                    │
                    ▼ (optional · post-80%)
         ┌──────────────────────┐
         │  P8.9-T4             │
         │  Webhook sandbox     │
         └──────────────────────┘
```

**Parallelism**: T2 design can start during T1 contract review; **do not implement T3 before T1 lands**.

---

### 2.2 Phase 7.5 — Intake Gate (62% → 80%)

```
                    ┌──────────────────────┐
                    │  PM-D1 … PM-D6       │  ◄── PM BLOCKING (see §6)
                    └──────────┬───────────┘
                               │
                               ▼
         ┌─────────────────────────────────────────┐
         │  P75-G1  Contract + vocabulary SSOT      │  ◄── START (draft w/o PM)
         └──────────┬──────────────────┬────────────┘
                    │                  │
         ┌──────────▼──────────┐      │
         │  P75-G3             │      │  (parallel after G1 schema draft)
         │  Policy allow/deny  │      │
         │  YAML + loader      │      │
         └──────────┬──────────┘      │
                    │                  │
                    └────────┬─────────┘
                             ▼
         ┌─────────────────────────────────────────┐
         │  P75-G2  Gate layer + outbox record      │
         │  orchestrator S3 rewire                  │
         └──────────┬──────────────────────────────┘
                    │
                    ▼
         ┌─────────────────────────────────────────┐
         │  P75-G4  intake.gate_decision notify     │──────► W6-T10 gateway
         │  + upstream CLI entry                    │        P8.9-T1 consumer (read)
         └─────────────────────────────────────────┘
```

**Parallelism**: G3 policy loader skeleton ∥ G2 after G1 draft; G3 deny content needs PM-D3. G4 requires G2 outbox record paths.

---

### 2.3 Phase 8 — Commercial Delivery (68% → 80%)

```
[W6-T5/T6 checkpoints · W7-T3 controlled notify · W12-T1 sandbox bundle]  (done/partial)
                    │
                    ▼
         ┌──────────────────────┐
         │  P8-T1               │  ◄── START (align W7-T3 client summary)
         │  Delivery bundle     │
         │  schema v1           │
         └──────────┬───────────┘
                    │
         ┌──────────┴───────────┐
         ▼                      ▼
┌─────────────────┐   ┌─────────────────┐
│  P8-T2          │   │  P8.9-T3        │  (cross-track: bundle_ready handler)
│  Operator       │   │  local dispatch │
│  surface CLI    │   │  (not P8-T3)    │
└─────────────────┘   └─────────────────┘
         │
         ▼ (post-80% · 85%+)
┌─────────────────┐
│  P8-T3          │
│  Notify v1.5    │  webhook + retry + DLQ
│  (deferred)     │
└─────────────────┘
```

**Overlap with W7 Package 1 (HITL-OPS)**: P8-T2 subsumes pending index, resume convenience, batch approve — map 1:1 to W7 roadmap Package 1 scope.

---

### 2.4 Cross-track integration graph

```
                    PM-D1…D6
                        │
    ┌───────────────────┼───────────────────┐
    ▼                   ▼                   ▼
P75-G1              P8.9-T1              P8-T1
(contract)          (consumer)           (bundle schema)
    │                   │                   │
    ├──────► P75-G3 ────┤                   │
    │                   │                   │
    └──────► P75-G2 ────┼───────────────────┤
                        │                   │
                        ▼                   ▼
                    P8.9-T2              P8-T2
                   (feedback ack)    (operator CLI)
                        │                   │
            P75-G4 ◄────┼───────────────────┘
         (gate notify)  │
                        ▼
                    P8.9-T3
              (dispatch + bundle_ready)
                        │
                        ▼
              80% verification bundle (§8)
```

**Shared mutation surfaces** (serialize or coordinate Implementer tickets):

| Surface | Tickets touching it | Coordination rule |
|---------|---------------------|-------------------|
| `delivery/notification_gateway_v1.py` | P75-G4 · P8.9-T3 | **Single gateway ticket owner per wave**; G4 lands event type first, T3 adds post-emit hook |
| `scripts/run_agent_standard_case_experiment.py` S3 | P75-G2 · P8.9-T3 | G2 owns S3 gate rewire; T3 owns post-emit only |
| Audit / investigation view | P8.9-T1 · P8.9-T2 · P75-G4 (read) | T1 owns spec extension; others consume |
| Bundle artifacts | P8-T1 · P8.9-T3 · W12-T1 | P8-T1 is schema SSOT; align with existing `sandbox_delivery_bundle_v1` |

---

## 3. Wave execution plan

### Wave 1 — Foundation & PM unblock

**Goal**: Freeze vocabulary, make events discoverable, define delivery artifact shape. Target phase deltas: P8.9 ~62→68%, 7.5 ~62→68%, Phase 8 ~68→74%.

| # | Ticket | Track | Est. | Can parallel? |
|---|--------|-------|------|---------------|
| 1 | **PM workshop** — PM-D1…D6 decisions recorded | 7.5 | 0.5d | — (first) |
| 2 | **P75-G1** intake-gate-contract-and-vocabulary-v1 | 7.5 | 3–5d | ∥ #3, #4 |
| 3 | **P8.9-T1** workflow-event-ledger-and-tracking-consumer-v1 | P8.9 | 1–1.5w | ∥ #2, #4 |
| 4 | **P8-T1** delivery-bundle-schema-v1 | Phase 8 | 1–1.5w | ∥ #2, #3 |

**Wave 1 ticket count: 3 implementer tickets + 1 PM gate** (4 work items).

**Wave 1 exit criteria**:
- PM-D1…D6 written into G1 contract (or explicit defaults adopted)
- Consumer CLI returns merged checkpoint + notification timeline
- `delivery_bundle_v1` schema + builder CLI produces valid manifest for `demo_phase`
- G1 schema passes fixture validation

**Optional parallel (low priority, non-blocking)**: `checkpoint_path` semantics docs (Dashboard follow-up) — helps P8-T2 but not 80% gate.

---

### Wave 2 — Core wiring

**Goal**: Gate becomes durable product surface; feedback loop closes; operator can see pending work. Target: P8.9 ~68→74%, 7.5 ~68→78%, Phase 8 ~74→78%.

| # | Ticket | Track | Est. | Depends on |
|---|--------|-------|------|------------|
| 1 | **P75-G3** intake-gate-policy-allowlist-denylist-v1 | 7.5 | 1w | G1 (+ PM-D3 deny list) |
| 2 | **P75-G2** intake-gate-layer-and-outbox-record-v1 | 7.5 | 1–1.5w | G1; G3 policy hook (can stub deny) |
| 3 | **P8.9-T2** feedback-ingest-and-downstream-ack-v1 | P8.9 | 1w | T1 |
| 4 | **P8-T2** operator-surface-pending-visibility-v1 | Phase 8 | 1.5–2w | T1 (bundle); soft: T1 consumer for notify filter |

**Wave 2 ticket count: 4 tickets**.

**Parallelism within Wave 2**:
- **Pair A** (7.5): G3 ∥ G2 start (G2 uses v2 rules first; G3 policy merges mid-wave)
- **Pair B** (P8.9 + Phase 8): T2 ∥ P8-T2 (different modules; share audit read paths only)

**Wave 2 exit criteria**:
- `run_intake_gate_cli.py` preview/run with outbox record on run
- Orchestrator S3 calls gate layer; reject skips CP-A
- Feedback ack round-trip unittest green
- `list_pending_checkpoints.py` shows CP-A/B pending with case_ref / waiting_time

---

### Wave 3 — Closure to 80%

**Goal**: End-to-end observable chain intake → run → checkpoint → bundle → dispatch → ack. Target: all three tracks **≥80%**.

| # | Ticket | Track | Est. | Depends on |
|---|--------|-------|------|------------|
| 1 | **P75-G4** intake-gate-notify-and-upstream-entry-v1 | 7.5 | 3–5d | G2 |
| 2 | **P8.9-T3** downstream-dispatch-handler-registry-v1 | P8.9 | 1–1.5w | T1 · T2 · P8-T1 (soft) |
| 3 | **P8.9-REGRESSION** integration smoke doc + matrix G-6/G-7/G-11 | P8.9 | 2–3d | T3 · G4 |
| 4 | **PHASE-80-SCRIBE** dashboard + verification bundle update | cross | 1d | all above |

**Wave 3 ticket count: 3 implementer tickets + 1 scribe/doc ticket** (4 work items).

**Explicitly deferred from 80% slice**:
- P8.9-T4 webhook sandbox
- Phase 8 P8-T3 Notify v1.5 (webhook + DLQ)
- W7 Package 2 HITL-SURFACE (web UI)
- W6-T10 orchestrator cleanup (High priority but non-blocking for 80%)

**Wave 3 exit criteria**: Run verification bundle §8; Dashboard Phase rows updated with evidence commands.

---

## 4. Suggested overall order (single-threaded critical path)

| Step | Item | Track | Cumulative % (est.) |
|------|------|-------|---------------------|
| 0 | PM-D1…D6 workshop | 7.5 | — |
| 1 | P8.9-T1 | P8.9 | 62→68% |
| 2 | P75-G1 | 7.5 | 62→65% |
| 3 | P8-T1 | Phase 8 | 68→74% |
| 4 | P8.9-T2 | P8.9 | 68→72% |
| 5 | P75-G2 | 7.5 | 65→74% |
| 6 | P75-G3 | 7.5 | 74→78% |
| 7 | P8-T2 | Phase 8 | 74→78% |
| 8 | P75-G4 | 7.5 | 78→80% |
| 9 | P8.9-T3 | P8.9 | 72→80% |
| 10 | Regression smoke + Dashboard | all | **80%** |

**Calendar estimate** (1 senior + partial support, with Wave 2 parallelism): **~5–7 weeks** wall clock vs **~8–10 weeks** if strictly sequential.

---

## 5. High-leverage, low-risk tasks

| Ticket | Why high leverage | Risk | When |
|--------|-------------------|------|------|
| **P8.9-T1** | Unblocks entire P8.9 chain; extends audit quickview; enables correlation for G4 events | **Low** — read-only consumer + contract docs | Wave 1 |
| **P75-G1** | Unblocks all 7.5 tickets; eliminates four-vocabulary confusion | **Low** — doc/schema only (implementation follows) | Wave 1 |
| **P8-T1** | Defines "what we deliver"; unblocks operator preview + dispatch handler content | **Low–Med** — align with W12-T1 sandbox bundle | Wave 1 |
| **P75-G2** | Largest 7.5 % jump (~65→74%); makes gate auditable | **Med** — orchestrator S3 touch; regression required | Wave 2 |
| **P8-T2** (subset: pending list + resume-latest) | High operator value; maps to W7 Package 1 core | **Low** — read-mostly + existing resume path | Wave 2 |

**High leverage but higher risk** (schedule after foundation):

| Ticket | Risk source | Mitigation |
|--------|-------------|------------|
| **P8.9-T3** | Post-emit hook on orchestrator; gateway coordination | Fail-open invariant; feature flag off by default |
| **P75-G3** | Policy drift vs v2 rules | Regression anchors on demo_phase / sampleco |
| **P75-G4** | Gateway event type addition | Extend unittest only; no retry/DLQ |

---

## 6. PM blocking items

| ID | Decision | Blocks | Default if no response by Wave 1 end |
|----|----------|--------|--------------------------------------|
| **PM-D1** | `review_needed` covers v2 `needs_review` + Phase7.5 `defer`? | G1 schema freeze | **Yes** — merge defer into review_needed |
| **PM-D2** | Unknown `task_type` → reject or review_needed? | G3 deny rules | **reject** + `unsupported_task_type` |
| **PM-D3** | Deny list subset from WAVE6 eligibility | G3 policy content | PHI, web_scraping, audio_video, scale_exceeds |
| **PM-D4** | non-tabular without extended flag → reject or review? | G3 + orchestrator | **reject** |
| **PM-D5** | Gate reject writes outbox + notify? | G2/G4 | **Yes** |
| **PM-D6** | New client default strategy | G3 | **review_needed** |
| **PM-D7** *(integrated)* | Phase 8 @ 80%: defer P8-T3 webhook to post-80%? | Scope of Wave 3 | **Yes** — local dispatch via P8.9-T3 satisfies Phase 8 notify slice |
| **PM-D8** *(integrated)* | P8-T1 vs W12-T1 sandbox bundle: one schema or extension? | P8-T1 AC | **Extend** W12 sandbox manifest toward `delivery_bundle_v1` |

**Hard stop**: If PM-D1/D2/D3 unresolved by end of Wave 1, **do not close G1** — proceed with P8.9-T1 and P8-T1 only.

---

## 7. Tasks that block other waves if delayed

| If delayed… | Blocks… | Impact severity |
|-------------|---------|-----------------|
| **PM-D1…D6** | P75-G1 freeze → G2/G3/G4 | **Critical** — 7.5 cannot reach 80% |
| **P8.9-T1** | T2, T3, G4 consumer correlation, audit timeline | **Critical** — P8.9 stuck at ~68% |
| **P75-G1** | G2, G3 implementation | **High** — 7.5 schema drift |
| **P8-T1** | P8-T2 bundle preview, P8.9-T3 handler payload | **High** — Phase 8 stuck ~74% |
| **P75-G2** | G4 notify (needs outbox record path) | **High** — 7.5 stuck ~74% |
| **P8.9-T2** | T3 dispatch ack visibility | **Medium** — T3 can stub ack but loses M4 |
| **P8.9-T3** | Phase 8 event-driven delivery closure | **Medium** — Phase 8 needs alternate proof for 80% |
| **P8-T2** | Operator 80% UX criterion | **Medium** — Phase 8 ~78% without it |

**Non-blocking deferrals** (safe to postpone):
- P8.9-T4, Phase 8 P8-T3, W6-T10 cleanup, checkpoint_path docs-only

---

## 8. Verification bundle (@ 80% target state)

```bash
# --- Phase 7.5 Intake Gate ---
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview --format json
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp --case-dir cases/unknown_client --mode run --format json
python -m unittest tests.test_intake_gate_layer_v1 tests.test_intake_decision_rules_v2 \
  tests.test_agent_standard_case_experiment -v

# --- P8.9 Outbox / Feedback ---
python -m unittest tests.test_workflow_event_consumer_v1 tests.test_feedback_ingest_v1 \
  tests.test_notification_dispatch_v1 -v
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp --case-dir cases/demo_phase \
  --mode run --auto-approve-intake --enable-notifications --format json
python scripts/inspect_workflow_events.py --case-ref demo_phase --format json
python scripts/run_feedback_ingest.py --case-ref demo_phase --dry-run
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json

# --- Phase 8 Commercial Delivery ---
python scripts/build_case_delivery_bundle_v1.py --case-dir cases/demo_phase --format json
python scripts/list_pending_checkpoints.py --format table
python -m unittest tests.test_delivery_bundle_v1 tests.test_operator_surface_v1 -v

# --- Contract regression ---
python -m unittest tests.test_outbox_and_feedback_layer_contract_v1 \
  tests.test_audit_quickview_and_case_history_spec_v1 -v
```

---

## 9. Ticket inventory summary

| Wave | Open tickets | Tracks covered |
|------|--------------|----------------|
| **Wave 1** | 3 (+ PM gate) | P75-G1 · P8.9-T1 · P8-T1 |
| **Wave 2** | 4 | P75-G2 · P75-G3 · P8.9-T2 · P8-T2 |
| **Wave 3** | 3 (+ scribe) | P75-G4 · P8.9-T3 · regression/doc |
| **Post-80%** | 2+ | P8.9-T4 · P8-T3 · W7 NOTIFY-v2 |

**Total implementer tickets for 80%: 10** (7.5: 4 · P8.9: 3 · Phase 8: 2 · cross: 1 scribe/regression).

---

## 10. Risk register (integrated)

| Risk | Tracks | Mitigation |
|------|--------|------------|
| Gateway merge conflicts (G4 + T3) | 7.5 · P8.9 | Same wave owner for gateway; G4 before T3 |
| Phase 8 vs P8.9 webhook scope creep | Phase 8 · P8.9 | PM-D7: defer P8-T3; 80% = local dispatch |
| Bundle schema fork (P8-T1 vs W12-T1) | Phase 8 | PM-D8: single schema SSOT |
| v1/v2 intake drift | 7.5 | G2 forces v2 default + demo/sampleco regression |
| W4-T1 ticket name confusion | 7.5 | Use **P75-G*** prefix only |

---

## 11. Reference index

| Artifact | Path |
|----------|------|
| P8.9 plan | `04_Workflows/plans/P8.9-outbox-feedback-to-80-plan.md` |
| Phase 7.5 plan | `04_Workflows/plans/phase-7.5-intake-gate-to-80-plan.md` |
| Phase 8 plan | `04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md` |
| Dashboard SSOT | `docs/WAVE_PROGRESS_DASHBOARD.md` |
| W7 tech roadmap | `04_Workflows/roadmaps/W7-standard-case-v2_tech-roadmap-draft.md` |

---

*Program Planner · Multi-Phase 80% integrated execution · plan-only · 2026-06-16*
