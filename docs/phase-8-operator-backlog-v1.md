# Phase 8 Operator Backlog v1 (P8-T2)

> **Scope**: Read-only operator-facing pending / blocked / completed index for standard-case line.  
> **Implementation**: `scripts/list_operator_backlog_v1.py`  
> **Data sources**: `workflow_event_consumer_v1`, checkpoint JSON under `outbox/<case_ref>/`, intake gate records.

---

## CLI

```bash
python scripts/list_operator_backlog_v1.py --status pending --format json
python scripts/list_operator_backlog_v1.py --status blocked --format table
python scripts/list_operator_backlog_v1.py --case-ref demo_phase --format json
```

| Flag | Description |
|------|-------------|
| `--case-ref` | Optional single case slug; omit to scan all discovered cases |
| `--status` | Filter: `pending`, `blocked`, or `completed` |
| `--format` | `json` (default) or `table` |
| `--repo-root` | Optional repo root override |
| `--outbox-root` | Optional outbox root override |
| `--batch-approve` | **P8-T2b**: approve all awaiting_human CP-A for `--task-type` (same type only) |
| `--resume-latest-approved` | **P8-T2b**: resolve latest approved CP-A path; **fail-close** if multiple without `--case-ref` |
| `--task-type` | Required for `--batch-approve`; optional filter for resume-latest |
| `--dry-run` | With `--batch-approve`: preview only |

```bash
python scripts/list_operator_backlog_v1.py --batch-approve --task-type tabular.cleaning.mvp --format json
python scripts/list_operator_backlog_v1.py --batch-approve --task-type tabular.cleaning.mvp --dry-run
python scripts/list_operator_backlog_v1.py --resume-latest-approved --task-type tabular.cleaning.mvp --format json
python scripts/list_operator_backlog_v1.py --resume-latest-approved --case-ref demo_phase --format json
```

**T2b notes**

- `--batch-approve` mutates checkpoint JSON under `outbox/<case_ref>/` only (approve + event append). It does **not** auto-run the standard-case orchestrator.
- `--resume-latest-approved` resolves `checkpoint_path` / `resume_context` and prints a `resume_hint`; `executed_resume=false` (path resolution only). Multiple approved → `ok=false` + `options[]`.

### Checkpoint preview CLI（P8-T2c）

Read-only preview before human decide. **No mutations.**

```bash
python scripts/preview_checkpoint_v1.py --checkpoint-path outbox/<case_ref>/<checkpoint>.json --format json
python scripts/preview_checkpoint_v1.py --checkpoint-id A-intake-confirmation --case-ref demo_phase --format text
```

| Flag | Description |
|------|-------------|
| `--checkpoint-path` | Path under `outbox/` (fail-close if outside) |
| `--checkpoint-id` | Resolve by id（optional `--case-ref` filter） |
| `--format` | `json` (default) or `text` |

Output shape includes `ok` · `read_only=true` · `mutated=false` · `schema_version=checkpoint_preview_v1` · `preview`（`review_summary` + human_decision／resume_from）。

驗收：`python -m unittest tests.test_preview_checkpoint_v1 -v`

---

## Status classification rules

| Status | When assigned | Primary signals |
|--------|---------------|-----------------|
| **pending** | Operator action likely needed soon | Checkpoint A `status=awaiting_human`; **or** intake gate `decision=review_needed` without resolved CP-A; **or** CP-A resolved but latest terminal run event is not `run.completed` (mid-run) |
| **blocked** | Run stopped or intake rejected | Latest terminal notification event is `run.blocked` or `run.failed`; **or** CP-A `status=rejected`; **or** intake gate `decision=reject` |
| **completed** | No open HITL and run finished | Latest terminal notification event is `run.completed` and CP-A is not `awaiting_human` |

**Notes**

- Terminal run events are the latest among `run.completed`, `run.blocked`, `run.failed` in the merged workflow timeline.
- Gate `review_needed` without a checkpoint file still surfaces as **pending** (operator should confirm or trigger CP-A).
- Checkpoint **preview** CLI：見上方 **P8-T2c**（`tests/test_preview_checkpoint_v1.py`）。
- Batch approve + resume-latest path resolution: see **P8-T2b** flags above (`tests/test_operator_backlog_t2b_v1.py`).

---

## JSON output shape

```json
{
  "ok": true,
  "read_only": true,
  "schema_version": "operator_backlog_v1",
  "status_filter": "pending",
  "count": 1,
  "items": [
    {
      "case_ref": "demo_phase",
      "task_type": "tabular.cleaning.mvp",
      "status": "pending",
      "last_event_type": "checkpoint.awaiting_human",
      "last_updated_at": "2026-06-19T12:00:00Z",
      "intake_decision": "review_needed",
      "checkpoint_a_status": "awaiting_human"
    }
  ],
  "message": "found 1 backlog row(s) for filter=pending"
}
```

---

## Verification

```bash
python -m unittest tests.test_operator_backlog_v1 tests.test_operator_backlog_t2b_v1 tests.test_preview_checkpoint_v1 -v
```

---

## HTTP API v1 (P8-API)

Read-only dev/sandbox HTTP wrapper around the same `list_operator_backlog()` read model. **No mutations.**

| Item | Value |
|------|-------|
| Script | `scripts/operator_http_api_v1.py` |
| Start | `python scripts/operator_http_api_v1.py --port 8080` |
| Endpoint | `GET /operator/backlog` |
| Query | `status=pending\|blocked\|completed` (optional), `case_ref=<slug>` (optional) |
| Body | Same JSON as CLI `--format json` (`schema_version: operator_backlog_v1`) |
| Health | `GET /health` → `{"ok": true, "service": "operator_http_api_v1", "read_only": true}` |

**Errors**

- Invalid `status` → `400` + `{"error": "invalid status"}`
- No matching cases → `200` + `items: []`

```bash
curl 'http://127.0.0.1:8080/operator/backlog?status=pending'
curl 'http://127.0.0.1:8080/operator/backlog?case_ref=demo_phase'
python -m unittest tests.test_operator_http_api_v1 -v
```

> **Note**: Stdlib `http.server` only; not production-hardened. For Web UI or external systems, bind on localhost in dev or place behind an authenticated reverse proxy in staging.

---

## Related tools

- Per-case timeline: `python scripts/inspect_workflow_events.py --case-ref <case_ref> --format json`
- Downstream ack pending: `python scripts/run_feedback_ingest.py --case-ref <case_ref> --dry-run`
- Audit quickview: `python scripts/run_agent_audit_quickview.py --case-ref <case_ref> --view investigation --format json`

> **Advisory footnote（W3-P8-ADV）**：本 backlog CLI 與相關 MP/CI smoke 屬 **local / advisory 觀測**；**≠** branch protection required check · **≠** prod gate。P8/P8.9 advisory 索引 → `docs/P8_P89_ADVISORY_CI_INDEX.md`。

### Bridge advisory（W3-P8-BRG · Release sanity）

> **Bridge advisory footnote**：P8.5 minimal orchestration bridge（`docs/phase8_5-bridge-smoke-runbook-v1.md`）為 **optional advisory 側線** — **in-memory stub** · advisory CI · **≠ prod** browser。**bridge ≠ operator backlog 前置** · **≠ Phase 8 release gate**（本 backlog／MP-SMOKE 七步不依賴 bridge smoke）。INDEX 雙向 → `WORKFLOW_INDEX.md` §1.4。

### Observability cross-ref（W3-P89-OBS）

Operator backlog 為 MP-SMOKE **step 7** 與交付鏈尾觀測點。追 `case_ref` · backlog `count` · 與上游 `multi_phase_smoke.ok` / P8.9 `acks_summary` 的對照，見 **`docs/p8_p89_delivery_observability_contract_v1.md`** §2.3 / §3（`F_BACKLOG`）。本節不新增 metrics 欄位。
