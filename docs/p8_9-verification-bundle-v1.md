# P8.9 Verification Bundle v1

> **Ticket**: P8.9-REGRESSION-standard-case-verification-bundle-v1  
> **Related**: `04_Workflows/plans/P8.9-outbox-feedback-to-80-plan.md` §8 · M7  
> **Status**: v1 operator + unittest smoke

---

## Purpose

Single-command regression that exercises P8.9 **consumer / feedback / dispatch** closure on the standard-case experiment line (`demo_phase` by default). Aggregates existing CLI JSON outputs — no new producer schemas.

---

## Operator command

```bash
python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json
```

Optional flags:

| Flag | Default | Meaning |
|------|---------|---------|
| `--output-dir` | `outbox/verification/<case_slug>/` | Bundle artifact directory |
| `--outbox-root` | `<output-dir>/outbox/` | Isolated outbox for experiment + consumers |
| `--disable-notifications` | off | Skip W6-T10 emit during experiment |
| `--disable-dispatch` | off | Do not set `GOV_NOTIFICATION_DISPATCH_ENABLED=1` |
| `--skip-experiment` | off | Collect-only mode (tests / re-scan) |
| `--no-auto-approve-intake` | off | Pause at Checkpoint A |

During the experiment step, notifications are enabled and dispatch env is set unless disabled.

---

## Artifact bundle

Written to `outbox/verification/<case_slug>/` (or `--output-dir`):

| File | Source | Purpose |
|------|--------|---------|
| `p8.9_verification_run.json` | bundle script | Run summary (`schema_version`: `p8_9_verification_run_v1`) |
| `events.json` | `load_workflow_events` / `inspect_workflow_events` | Merged notification + checkpoint timeline |
| `audit_quickview.json` | `run_agent_audit_quickview` + workflow merge | Investigation view with `workflow_notifications` |
| `acks.json` | `ingest_pending_events` + on-disk ack files | Pending + recorded downstream acks (`p8_9_verification_acks_v1`) |

### Summary shape (`p8.9_verification_run.json`)

Key fields:

- `ok`, `case_ref`, `run_at`, `outbox_root`, `output_dir`
- `experiment` — full orchestrator result dict (when not `--skip-experiment`)
- `events_summary` — `event_types[]`, `tracking_statuses[]`, `count`
- `acks_summary` — `ack_count`, `pending_count`
- `artifact_paths` — map of bundle filenames → absolute paths

### Acks shape (`acks.json`)

- `ingest` — same dict as `run_feedback_ingest.py --format json`
- `ack_records[]` — parsed `outbox/feedback/<case_ref>/acks/*.json`
- `ack_count`, `pending_count`

---

## Verification

```bash
python -m unittest tests.test_p8_9_verification_bundle_v1.py -v
python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json
```

Expected for `demo_phase` with notifications + dispatch:

- Notification `event_type` includes `checkpoint.approved` and `run.completed`
- `run.completed` row has `tracking_status=acked` when dispatch handlers run
- All four bundle files present under output directory

**Executed report (2026-06-27)**: `docs/p8_9-verification-report-v1.md` — bundle re-run `ok: true` on `demo_phase`.

---

## Functional gaps (`true_with_known_limits`)

> **Manifest**: `functional_gaps: true_with_known_limits` — bundle regression **passes** on the anchor case; the following limits are **explicit and intentional**.

| Gap | Status | Operator impact |
|-----|--------|-----------------|
| **P8.9-T4 HTTP webhook dispatch** | **Deferred** | No live webhook adapter; dry-run skeleton only — **do not configure prod webhooks against this line** |
| **Multi-case fleet sweep** | **Optional** | REGRESSION anchor is `demo_phase` only; use `MC-SMOKE` / multi-case CLI for extended profiles |
| **GA-remote / CI bundle job** | **Out of scope** | Evidence tier remains **`L-local`** (`EVD-LL-P89-BND`); no GitHub workflow gate for this bundle |

**Non-claims**: Passing this bundle does **not** mean T4 webhook is available, prod-ready, or covered by advisory CI.

> **Advisory footnote（W3-P8-ADV）**：bundle / MP-SMOKE / `run_ci_smoke_check_v1` 綠燈 = **L-local / advisory sanity** · **≠** GitHub required workflow · **≠** merge gate。索引 → `docs/P8_P89_ADVISORY_CI_INDEX.md`。

---

## Observability cross-ref（W3-P89-OBS）

> **Trace / artifact SSOT**：`docs/p8_p89_delivery_observability_contract_v1.md` — 本 bundle 四檔與 `events_summary` / `acks_summary` 鍵見該約 §1–§2；失敗對應 CLI 見 §3。  
> **Evidence tier**：本機 bundle 綠 = **L-local**（`docs/p8_p89_evidence_index_v1.md`）· **≠** GA-remote / required CI。

---

## References

| Artifact | Path |
|----------|------|
| Plan §8 command bundle | `04_Workflows/plans/P8.9-outbox-feedback-to-80-plan.md` |
| Audit spec | `docs/audit-quickview-and-case-history-spec-v1.md` |
| Outbox contract | `docs/outbox-and-feedback-layer-contract-v1.md` |
| Delivery observability contract | `docs/p8_p89_delivery_observability_contract_v1.md` |
| Test matrix REGRESSION row | `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7.3 |
