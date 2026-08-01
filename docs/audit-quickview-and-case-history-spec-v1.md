# Audit Quickview and Case History Spec v1

> **Ticket**: WB-T5 · audit-quickview-and-case-history-spec-v1  
> **Phase**: 5（Audit 觀測面）· 8.9（Case history join · Feedback 追溯）  
> **Date**: 2026-06-11  
> **Status**: Contract SSOT — **read-only investigation view**; no writers or checkpoint mutations  
> **Implementation**: `scripts/run_agent_audit_quickview.py` (wire format)  
> **Supersedes narrative**: `docs/agent-lines-audit-quickview-v1.md` → implementation appendix pointer only

---

## §1 Purpose and scope

Formalize the **read-only trace contract** for Agent Lines audit quickview:

```
decision → route → CP-A → CP-B → delivery approval → outbox join
```

Aligned with:

- **WB-T3** — `docs/outbox-and-feedback-layer-contract-v1.md` §2 namespace table
- **WB-T4** — optional consumption of `audit_sections_found` / `audit_gaps_count` in toolchain health dashboard
- **Wave C** — investigation playbook cross-references this spec (not ticket STATE files)

**In scope (v1)**

- `--case-ref` input contract
- Wire JSON (`agent_audit_quickview_v1`) emitted by CLI
- Canonical **investigation view** (`audit_investigation_view_v1`) with `sections[]`, `timeline[]`, `gaps[]`
- Data-source priority and timestamp sort rules
- Case history join fields aligned with `cases/index.json` / `lookup_case_history`
- Observability counters for optional dashboard merge

**Out of scope (v1)**

- Web UI / Grafana panels
- Full-text search or PG queries
- Non-tabular heavy tool execution records
- Writes to outbox, checkpoint state, or `cases/index.json`
- Blocking PR gate behavior (audit remains **optional** / investigation-only)

---

## §2 CLI input and output shapes

### §2.1 Input (`--case-ref`)

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `--case-ref` | yes | string | Case slug under `cases/` (POSIX path), e.g. `demo_phase`, `sampleco/2026-0001` |
| `--format` | no | `text` \| `json` | Default `text`; JSON emits wire format (§2.2) |
| `--repo-root` | no | path | Repo root override for unittest / offline scratch |

**Exit code**: `0` when at least one run artifact, checkpoint, or sandbox delivery bundle exists; else `1`.  
**Stderr**: read errors only (summaries); **must not** print secrets or env keys.

### §2.2 Wire format (`agent_audit_quickview_v1`)

Emitted by `python scripts/run_agent_audit_quickview.py --case-ref <ref> --format json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ok` | bool | yes | Any auditable material found |
| `read_only` | bool | yes | Always `true` |
| `schema_version` | string | yes | Always `agent_audit_quickview_v1` |
| `case_ref` | string | yes | Echo of input |
| `message` | string | yes | Human summary |
| `latest_run` | object | yes | Newest agent-line run artifact metadata |
| `decision` | object | yes | Normalized decision block |
| `planned_route` | object | yes | Normalized route / tools |
| `checkpoint_a` | object | yes | CP-A merged view (inline + on-disk) |
| `checkpoint_b` | object | yes | CP-B merged view |
| `delivery_approval` | object \| null | yes | Delivery signoff when recorded |
| `sandbox_delivery` | object | optional | Present when sandbox bundle found (W12-T1) |
| `sources_read` | string[] | yes (CLI only) | Repo-relative paths consulted |

Nested blocks match W10-T3; see `docs/agent-lines-audit-quickview-v1.md` §4 for examples.

### §2.3 Investigation view (`audit_investigation_view_v1`)

**Canonical shape** for Wave C playbooks, dashboard optional merge, and contract tests.  
Produced by **deterministic projection** from wire format (§2.4) — not a second on-disk artifact.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ok` | bool | yes | Same as wire `ok` |
| `read_only` | bool | yes | Always `true` |
| `schema_version` | string | yes | `audit_investigation_view_v1` |
| `case_ref` | string | yes | Echo of input |
| `sections` | array | yes | Logical audit sections (§2.3.1) |
| `timeline` | array | yes | Ordered trace events (§2.3.2) |
| `gaps` | array | yes | Explicit missing links (§2.3.3) |
| `audit_sections_found` | int | yes | Count of `sections[]` where `found === true` |
| `audit_gaps_count` | int | yes | `len(gaps)` |
| `case_history` | object | optional | Join block from `cases/index.json` (§4) |
| `message` | string | yes | Same as wire `message` |

#### §2.3.1 `sections[]` item

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `section_id` | string | yes | Stable id (see table below) |
| `step_ids` | string[] | yes | S1–S15 anchors (may be empty) |
| `found` | bool | yes | Whether this section has evidence |
| `fixture_maturity` | string | yes | `stable` \| `experimental` \| `sandbox` \| `unknown` |
| `namespace_prefix` | string | yes | WB-T3 namespace discriminator |
| `summary` | object | yes | Section-specific subset (decision, status, tools, …) |
| `source_paths` | string[] | yes | Repo-relative paths backing this section |

| `section_id` | `step_ids` | `namespace_prefix` | Source |
|--------------|------------|--------------------|--------|
| `latest_run` | `S1`, `S2` | `agent_ci` \| `agent_experiment_regression` \| `non_tabular_experiment` | Newest run artifact per §3 |
| `decision` | `S3` | same as run | Wire `decision` + optional `intake_gate` block; durable SSOT: `outbox/<case_ref>/intake_gate_decision_*.json` (P75-G2) |
| `planned_route` | `S5`, `S6` | same as run | Wire `planned_route` |
| `checkpoint_a` | `S4` | `outbox/<case_ref>/` | Wire `checkpoint_a` + checkpoint JSON |
| `checkpoint_b` | `S12` | `outbox/<case_ref>/` | Wire `checkpoint_b` |
| `delivery_approval` | `S13` | `outbox/<case_ref>/` | Wire `delivery_approval` |
| `sandbox_delivery` | `S10`, `S11` | `outbox/sandbox_delivery/` | Wire `sandbox_delivery` when present |
| `tabular_outbox` | `S9` | `outbox/<case_ref>/` | Optional; from tabular per-run JSON scan |
| `workflow_notifications` | `S3`, `S4`, `S10`, `S12`, `S14` | `outbox/notifications/` | Wire `workflow_notifications` from T1 consumer merge; includes `intake.gate_decision` at S3 when gate run + notify enabled |

**Operator backlog (cross-case index, P8-T2)**: For multi-case pending/blocked/completed queue view, use `scripts/list_operator_backlog_v1.py` — spec `docs/phase-8-operator-backlog-v1.md`. Per-case drill-down remains `inspect_workflow_events.py` and audit quickview.

**`fixture_maturity` rules**

| Condition | Value |
|-----------|-------|
| `latest_run.source_kind === non_tabular_experiment` | `sandbox` |
| `sandbox_delivery.found === true` or `latest_run.flow_family === non_tabular` | `sandbox` |
| `latest_run.mode === preview` | `experimental` |
| Known stable fixtures (`demo_phase`, `sampleco/2026-0001`) with run mode | `stable` |
| Otherwise | `unknown` |

#### §2.3.2 `timeline[]` item

Sorted **ascending** by effective timestamp; ties broken by `step_id` lexicographic order.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step_id` | string | yes | `S1`–`S15` (see README v2 §2.1) |
| `event_kind` | string | yes | e.g. `decision`, `intake_gate_decision`, `route_planned`, `checkpoint_a`, `checkpoint_b`, `delivery_approval`, `tabular_run`, `agent_run`, `workflow_notification` |
| `timestamp` | string \| null | yes | ISO-8601 or compact UTC from artifact; `null` if unknown |
| `source_path` | string \| null | yes | Repo-relative file path |
| `namespace_prefix` | string | yes | WB-T3 namespace (§8) |
| `summary` | string | yes | One-line human label |

**Timestamp resolution order**

1. Embedded JSON field (`written_at`, `human_decision.timestamp`, `started_at` / `finished_at`)
2. Filename timestamp token (`YYYYMMDDTHHMMSSZ` or ISO in checkpoint name)
3. File `mtime` (UTC ISO-8601) — **last resort**; add gap note `timestamp_from_mtime`

#### §2.3.3 `gaps[]` item

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gap_id` | string | yes | Stable machine id |
| `step_ids` | string[] | yes | Affected steps |
| `reason` | string | yes | Why the chain is incomplete |
| `severity` | string | yes | `info` \| `warning` |

**Required gap rules (when condition met, gap MUST appear)**

| `gap_id` | Condition | `step_ids` |
|----------|-----------|------------|
| `missing_run_artifact` | No agent-line run artifact | `S3`–`S6` |
| `missing_checkpoint_a_on_disk` | CP-A `would_trigger` true but `on_disk` false | `S4` |
| `missing_checkpoint_b_on_disk` | CP-B `would_trigger` true but `on_disk` false | `S12` |
| `missing_delivery_approval` | CP-B approved path but no `delivery_approval` | `S13` |
| `timeline_break_after_cp_a` | Decision present, CP-A missing inline and on-disk | `S4` |
| `case_not_in_index` | `cases/index.json` has no entry for `case_ref` | `S2` |
| `missing_downstream_ack` | Workflow notification row with `tracking_status=pending_ack` | `S14` (or event `source_step`) |
| `downstream_ack_failed` | Workflow notification row with `tracking_status=failed` | `S14` (or event `source_step`) |

**Dispatch + ack lifecycle (P8.9-T3)** — investigation view derives `tracking_status` from ack files:

| `tracking_status` | After dispatch + ack |
|-------------------|----------------------|
| `pending_ack` | Emit recorded; dispatch off or handler skipped; no ack file |
| `acked` | Handler succeeded; ack `status=received` |
| `failed` | Handler failed; ack `status=failed`; gap `downstream_ack_failed` when surfaced |

Dispatch itself is not a separate timeline row in v1; ack merge on notification ledger rows closes the loop.

**FORBID**: inferring missing checkpoint status without a `gaps[]` entry.

### §2.4 Projection: wire → investigation view

Implementers and contract tests **must** use this algorithm (pure function; no I/O):

1. Copy `ok`, `read_only`, `case_ref`, `message` from wire.
2. Build `sections[]` from wire blocks per §2.3.1 table.
3. Build `timeline[]` from sections + `latest_run.artifact_path` + checkpoint paths.
4. Compute `gaps[]` per §2.3.3 rules.
5. Set `audit_sections_found = count(sections where found)`.
6. Set `audit_gaps_count = len(gaps)`.
7. Optionally attach `case_history` when index join requested (§4).

CLI v1 emits wire format only; investigation view is derived by consumers (tests, Wave C playbook, WB-T4 optional hook).

---

## §3 Data source priority

When multiple agent-line artifacts match `--case-ref`, select **one** newest run using:

| Priority (high → low) | Namespace | `schema_id` |
|----------------------|-----------|-------------|
| 1 | `outbox/agent_ci/` | `agent_lines_ci_suite_v1` |
| 2 | `outbox/agent_experiment_regression/` | `agent_experiment_regression_v1` |
| 3 | `outbox/non_tabular_experiment/` | `non_tabular_experiment_preview_v1` |

Within the same priority tier, pick the artifact with the **lexicographically greatest** filename timestamp prefix (`YYYYMMDDTHHMMSSZ`).

**Checkpoint JSON** (`outbox/<case_ref>/checkpoint_*.json`) is always merged **in addition** to the chosen run artifact — not competing for “latest run”.

**Tabular per-run outbox** (`outbox/<case_ref>/<run_id>.json`) supplies §2.3.1 `tabular_outbox` section and timeline `S9` events; priority **below** agent-line namespaces for decision/route authority.

**Authority for human decisions** (feedback): on-disk checkpoint JSON **over** nested experiment summary — per WB-T3 §4.1.

---

## §4 Case history join

Read-only join aligned with WB-T3 §5 and Wave 4A lookup.

### §4.1 Index lookup

| Function | Module | Role |
|----------|--------|------|
| Index SSOT | `cases/index.json` | Registry (`schema_version: gov-cases-index-v0.1`) |
| Filtered view | `scripts/cases_index_lib.lookup_cases` | Same semantics as `scripts/lookup_case_history.py` |

Match key: `case_dir == cases/<case_ref>` (normalize slashes).

### §4.2 `case_history` block (investigation view)

| Field | Type | Source |
|-------|------|--------|
| `ok` | bool | `true` when index entry found |
| `case` | object \| null | Subset of index entry (fields below) |
| `history` | object | `lookup_cases(client_ref=case.client_ref)` when case present |
| `notes` | string[] | e.g. `case_not_in_index` when absent |

**`case` object fields** (when present):

| Field | Index key |
|-------|-----------|
| `case_dir` | `case_dir` |
| `client_ref` | `client_ref` |
| `case_id` | `case_id` |
| `product_sku` | `product_sku` |
| `gate_status` | `gate_status` |
| `schema_headers` | `schema_headers` |
| `known_limits` | `known_limits` |

When `case` is null: emit `gaps[]` entry `case_not_in_index`; **still return** outbox-derived sections.

### §4.3 Tabular outbox join (optional section)

When tabular per-run files exist under `outbox/<case_ref>/`, populate `sections[]` item `tabular_outbox` using the same field subset as `tools/tabular_outbox_consumer.join_with_case_history` → `runs[]` summaries (`run_id`, `tool_id`, `started_at`, `finished_at`, `ok`, `outbox_path`). Chronological order **oldest first** in timeline `S9` events.

---

## §5 Read-only · investigation-only

Aligned with C1-P1 Product Spec tone (`docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` §1.3):

- Audit quickview is **dev / staging investigation tooling** — **not** production SLA evidence.
- Output **must not** be cited in client-facing documents as compliance proof or delivery warranty.
- **No writes**: no outbox, checkpoint, index, or ticket STATE mutation.
- **No side effects**: no executor, notify gateway, or external API calls.
- **Optional gate**: does not block PR merge or MVP mainline (same class as WB-T4 `gate_class: optional`).

### §5.1 WA-T4 Scribe / ticket STATE boundary (AC-9)

Per `docs/phase4-multi-agent-collaboration-contract-v1.md` §5.1:

- **FRAME** and **STATE** in `04_Workflows/tickets/*_state.md` are **Orchestrator-only**.
- This audit spec is an **Implementer deliverable** and investigation SSOT.
- Scribe indexes spec paths in Dashboard / WORKFLOW_INDEX / Progress — Scribe **must not** treat audit JSON output as ticket STATE authority or overwrite STATE blocks.

---

## §6 Observability

| Channel | Contract |
|---------|----------|
| **logs** | CLI stderr: read error summaries only; no secrets |
| **metrics** | Investigation view emits `audit_sections_found`, `audit_gaps_count` (WB-T4 may consume optionally) |
| **traces** | `timeline[]` carries `step_id`, `source_path`, `timestamp`; optional `trace_id` from agent payloads — **not guaranteed** |

---

## §7 Cross-references

| Document | Relationship |
|----------|--------------|
| `docs/outbox-and-feedback-layer-contract-v1.md` | §2 namespace table · §4 feedback · §5 join (WB-T3) |
| `docs/toolchain-health-dashboard-v1.md` | Optional `audit_*` counter consumption (WB-T4) |
| `docs/agent-lines-audit-quickview-v1.md` | W10-T3 implementation appendix |
| `docs/agent-and-non-tabular-lines-readme-v2.md` | §4 pointer only (no dual maintenance) |
| `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` | Investigation-only tone (C1-P1) |
| `docs/phase4-multi-agent-collaboration-contract-v1.md` | STATE write freeze (WA-T4) |
| `docs/p8_9-verification-bundle-v1.md` | P8.9 REGRESSION bundle includes `audit_quickview.json` snapshot (M7) |

### §7.1 WB-T3 namespace prefix table (audit cross-ref)

| Path prefix | Namespace prefix constant | `schema_id` |
|-------------|---------------------------|-------------|
| `outbox/agent_ci/` | `agent_ci` | `agent_lines_ci_suite_v1` |
| `outbox/agent_experiment_regression/` | `agent_experiment_regression` | `agent_experiment_regression_v1` |
| `outbox/non_tabular_experiment/` | `non_tabular_experiment` | `non_tabular_experiment_preview_v1` |
| `outbox/<case_ref>/` | `outbox/<case_ref>/` | `tabular_outbox_v1` + `hitl_checkpoint_v1` |
| `outbox/sandbox_delivery/` | `sandbox_delivery` | `sandbox_delivery_bundle_v1` |

Same-name fields in different namespaces **must** be disambiguated with `namespace_prefix` in `sections[]` / `timeline[]`.

---

## §8 Verification

```bash
python -m unittest tests.test_audit_quickview_and_case_history_spec_v1 -v
python -m unittest tests.test_agent_audit_quickview_v1 -v
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json
python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json
```

Minimum example: run CLI with `--case-ref demo_phase --format json`, project to investigation view (§2.4), assert `sections`, `timeline`, `gaps`, `audit_sections_found`, `audit_gaps_count` present and typed.

---

*WB-T5 · Audit Quickview and Case History Spec v1 · 2026-06-11*
