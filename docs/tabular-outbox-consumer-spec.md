# Tabular Outbox Consumer Spec v1

> **Ticket**: W3-TL-T4 · Tabular Outbox Consumer / Debug / History Join  
> **Contract SSOT (namespace index)**: `docs/outbox-and-feedback-layer-contract-v1.md` (WB-T3) — **this file is an implementation appendix**  
> **Implementation**: `tools/tabular_outbox_consumer.py` · `tools/inspect_tabular_outbox.py`  
> **Per-run write SSOT**: `docs/tabular-tool-outbox-spec.md` (W3-TL-T3)  
> **Date**: 2026-06-10

---

## 1. Purpose and scope

This spec defines a **read-only consumer layer** for the Tabular MVP outbox tree at `outbox/<case_ref>/<run_id>.json`.

**In scope (v1)**

- List and filter outbox run summaries by `case_ref`, `tool_id`, and optional time window
- Load a single run record with schema validation
- Join outbox runs with `cases/index.json` and the Wave 4A `lookup_case_history` view
- CLI for developer / agent debugging (`inspect_tabular_outbox.py`)

**Out of scope (v1)**

- Phase 8.8 `orchestration_bridge_outbox`, Langfuse, DLQ, replay pipeline
- Spawning tools or writing outbox records (see W3-TL-T3 executor)
- MVP mainline CLI changes, Local UI, CI gates

**Track separation**: This consumer reads **only** the tabular MVP outbox under repo `outbox/`. It does not read or replay Phase 8.8 orchestration events.

**WB-T3 pointer**: `join_with_case_history` contract fields and list-mode JSON shape → `docs/outbox-and-feedback-layer-contract-v1.md` §3–§5 · `docs/schemas/outbox_layer_v1.json`.

---

## 2. API interface

Module: `tools/tabular_outbox_consumer.py`

All functions are **read-only**. Paths resolve via `gov_paths`-style repo root discovery (module parent) and optional `outbox_root_override` for tests.

### 2.1 `list_outbox_runs`

```python
def list_outbox_runs(
    case_ref: Optional[str] = None,
    tool_id: Optional[str] = None,
    *,
    started_after: Optional[str] = None,
    started_before: Optional[str] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> List[Dict[str, Any]]:
```

| Parameter | Description |
|-----------|-------------|
| `case_ref` | When set, scan only `outbox/<case_ref>/`. When `None`, scan all case subdirectories. |
| `tool_id` | Filter to a catalog tool id (e.g. `validate.eligibility`). |
| `started_after` / `started_before` | Optional ISO-8601 bounds on `started_at` (inclusive). |
| `outbox_root_override` | Test / custom root; repo-relative unless absolute. |

**Returns**: `list[dict]` — run **summaries**, newest first. Each item includes:

| Field | Type | Description |
|-------|------|-------------|
| `case_ref` | string | Case slug |
| `run_id` | string | Run identifier |
| `tool_id` | string | Catalog tool id |
| `started_at` | string | ISO-8601 UTC |
| `finished_at` | string | ISO-8601 UTC |
| `ok` | bool | Executor-level success |
| `exit_code` | int \| null | Subprocess exit code |
| `message` | string | Summary message |
| `outbox_path` | string | Repo-relative path |

Empty list when no matches (not an error).

### 2.2 `get_outbox_run`

```python
def get_outbox_run(
    case_ref: str,
    run_id: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
```

**Success** (`ok: true`):

```json
{
  "ok": true,
  "record": { "... full tabular_outbox_v1 record ..." }
}
```

**Failure** (`ok: false`):

| `message` | When |
|-----------|------|
| `invalid_case_ref_or_run_id` | Empty slug or run id |
| `run_not_found` | File missing under `outbox/<case_ref>/` |
| `invalid_run_json` | JSON parse failure |
| `missing_required_keys:[...]` | Required fields absent |
| `unsupported_schema_version` | `schema_version` ≠ `tabular_outbox_v1` |
| *(ValueError text)* | `validate_record()` failure |

Failure payloads include `case_ref`, `run_id`, and often `outbox_path`.

### 2.3 `join_with_case_history`

```python
def join_with_case_history(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    index_path: Optional[Path] = None,
) -> Dict[str, Any]:
```

**Returns** (`ok: true` when `case_ref` is valid):

| Field | Type | Description |
|-------|------|-------------|
| `ok` | bool | `false` only for invalid `case_ref` |
| `case_ref` | string | Normalized slug |
| `case` | object \| null | Subset from `cases/index.json` (`client_ref`, `product_sku`, `gate_status`, …) |
| `history` | object | Same shape as `lookup_cases()` from `scripts/cases_index_lib.py` |
| `runs` | array | Outbox summaries, **chronological** (oldest first) |
| `last_by_tool_id` | object | Map `tool_id` → latest run summary for this case |
| `run_count` | int | Length of `runs` |

When the case is absent from the index, `case` is `null` and `history.ok` may be `false` with note `case_not_in_index`; outbox `runs` are still returned.

---

## 3. CLI usage

Entrypoint: `tools/inspect_tabular_outbox.py`

### 3.1 List runs for a case

```bash
python tools/inspect_tabular_outbox.py --case-ref demo_phase
python tools/inspect_tabular_outbox.py --case-ref demo_phase --json
```

**Table output (default)** — columns: `run_id`, `tool_id`, `ok`, `exit_code`, `started_at`.

**JSON output** (`--json`):

```json
{
  "ok": true,
  "case_ref": "demo_phase",
  "tool_id": null,
  "count": 2,
  "runs": [ "... summaries ..." ]
}
```

### 3.2 Filter by tool

```bash
python tools/inspect_tabular_outbox.py --case-ref demo_phase --tool-id validate.eligibility --json
```

### 3.3 Single run

```bash
python tools/inspect_tabular_outbox.py --case-ref demo_phase --run-id 2026-06-10T01-52-00Z_eligibility --json
```

Exit code `1` when `get_outbox_run` returns `ok: false`.

### 3.4 History join view

```bash
python tools/inspect_tabular_outbox.py --case-ref demo_phase --join-history --json
```

Includes `case`, `history`, chronological `runs`, and `last_by_tool_id`.

### 3.5 Overrides

| Flag | Purpose |
|------|---------|
| `--outbox-root` | Point at a test or alternate outbox tree |
| `--started-after` / `--started-before` | Time filter (list mode only) |

---

## 4. Relationship to cases/index.json and lookup_case_history

| Layer | SSOT? | Role in join |
|-------|-------|--------------|
| **`cases/index.json`** | **Yes** (case registry) | Supplies `client_ref`, `product_sku`, `gate_status`, `schema_headers`, etc. Matched by `case_dir` = `cases/<case_ref>`. |
| **`lookup_case_history`** (`scripts/cases_index_lib.lookup_cases`) | **View** | Filtered index lookup by `client_ref`; included as `history` for cross-case context. Does not scan disk. |
| **`outbox/<case_ref>/*.json`** | **Yes** (tool-run audit) | Per-run tool execution audit from W3-TL-T3 executor. Consumer reads only; does not mutate. |
| **`join_with_case_history` result** | **Derived view** | Combines the three sources for agent / debug use; not persisted. |

**Alignment rule**: `case_ref` slug equals the path under `cases/` (POSIX slashes), e.g. `demo_phase` → `cases/demo_phase`, `sampleco/2026-0001` → `cases/sampleco/2026-0001`.

---

## 5. Limitations and future work

| Item | Status |
|------|--------|
| Replay / re-execute from outbox | **Not implemented** — Phase 8.8 / future W3-TL ticket |
| Langfuse / task_runs integration | **Out of scope** |
| CI merge gate hook | **Out of scope** — run unit tests locally |
| `events.jsonl` streaming consumer | **Optional future** — v1 scans per-run JSON files |
| Local UI surfacing | **Partial** — replay report CLI + HTML (see below) |
| Pagination for large outbox trees | **Deferred** — v1 loads all matching files |
| Offline replay report (MD/HTML) | **Implemented** — `scripts/build_tabular_outbox_replay_report.py` · `docs/tabular-outbox-replay-report-v1.md` |

**Git hygiene**: Real runs under repo `outbox/` are gitignored (W3-TL-T3). Tests use `outbox_root_override` or `tests/fixtures/outbox/`.

---

## 6. Verification

```bash
python -m unittest tests.test_tabular_outbox_consumer -v
python -m unittest tests.test_build_tabular_outbox_replay_report -v
```

Example manual check (when outbox contains runs):

```bash
python tools/inspect_tabular_outbox.py --case-ref demo_phase --join-history --json
python scripts/build_tabular_outbox_replay_report.py --case-ref demo_phase --format both
```

Fixture-based smoke (no repo outbox required):

```bash
python scripts/build_tabular_outbox_replay_report.py \
  --case-ref demo_phase \
  --outbox-root tests/fixtures/outbox \
  --output-dir /tmp/tabular_replay_test \
  --format both
```
