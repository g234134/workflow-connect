# Tabular Tool Outbox Spec v1

> **Ticket**: W3-TL-T3 · Tabular Tool Executor + Outbox  
> **Contract SSOT (namespace index)**: `docs/outbox-and-feedback-layer-contract-v1.md` (WB-T3) — **this file is an implementation appendix**  
> **Implementation**: `tools/tabular_tool_executor.py` · `tools/tabular_outbox_writer.py`  
> **Catalog SSOT**: `tools/tabular_tool_catalog_v1.json` (W3-TL-T1) · `docs/tool-catalog-and-selector-contract-v1.md` (WB-T1)  
> **Execution / sandbox SSOT**: `docs/tool-executor-and-sandbox-safety-contract-v1.md` (WB-T2 · Phase 8.8)  
> **Date**: 2026-06-10

---

## §0 指针（WB-T2 · execution_mode 与 sandbox）

- **四级执行模式**（`dry_run` / `plan_only` / `execute` / `sandbox_end_to_end`）、case allowlist 矩阵、PR CI 上 `execute` 为 optional：见 **`docs/tool-executor-and-sandbox-safety-contract-v1.md` §2、§8**。
- **本 spec §3.5 / §4** 的 dry-run 不写盘规则，与 contract §4 一致；`sandbox_end_to_end` 额外 `outbox/sandbox_delivery/` 见 `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md`。
- **Sandbox 安全**（subprocess cwd、`..` 逃逸、超时 SSOT）：contract §5；本票 **不** 改 executor 实现。

---

## 1. Purpose and scope

This spec defines the **tabular MVP tool-layer outbox**: a repo-local append-friendly audit trail for individual tool runs invoked through `execute_tabular_tool()`.

**In scope (v1)**

- Per-run JSON at `outbox/<case_ref>/<run_id>.json`
- Append-only `outbox/events.jsonl` (one line per run)
- Dry-run planning without subprocess or on-disk outbox file
- Alignment with `cases/*/intake.json` and `cases/index.json` case identity

**Out of scope (v1)**

- Phase 8.8 `orchestration_bridge_outbox` / Langfuse / DLQ / replay CLI (W3-TL-T4 follow-up)
- Replacing MVP mainline CLI artifacts under `cases/<case>/reports/*`
- Modifying E2E driver or regression scripts

**Track separation**: Tabular outbox (`outbox/`) is **not** the Phase 8.8 orchestration event schema. Do not merge paths or replay tooling.

**WB-T3 pointer**: Unified outbox namespace table, feedback semantics, and machine-readable index → `docs/outbox-and-feedback-layer-contract-v1.md` · `docs/schemas/outbox_layer_v1.json`.

---

## 2. `case_ref` and `run_id` rules

### 2.1 `case_ref`

Primary slug for outbox directory layout. Resolution order:

1. `extra_args["case_ref"]` when provided to `execute_tabular_tool`
2. Otherwise, path of `case_dir` relative to `cases/` (POSIX slashes)

| Fixture | `case_dir` | `case_ref` |
|---------|------------|------------|
| demo_phase | `cases/demo_phase` | `demo_phase` |
| sampleco | `cases/sampleco/2026-0001` | `sampleco/2026-0001` |

**Alignment with intake**

- `intake.json` fields `client_ref` + `case_id` identify the business case (see `docs/mvp-standard-trace-path.md` §3).
- `case_ref` is the **filesystem slug** under `cases/`; for nested layouts it is `{client_ref}/{case_id}` when that matches the directory tree (e.g. `sampleco/2026-0001`).
- `cases/index.json` entries use the same relative path as `case_ref` for on-disk cases.

**Global tools** (no case directory, e.g. `index.cases`): caller may pass a placeholder `case_ref` such as `_global`; outbox still writes under that slug.

### 2.2 `run_id`

Format:

```text
{UTC_timestamp_compact}_{tool_slug}
```

- **UTC timestamp**: `YYYY-MM-DDTHH-MM-SSZ` (hyphens in time portion; no colons)
- **tool_slug**: last segment of catalog `tool_id` after the final dot  
  - `validate.eligibility` → `eligibility`  
  - `clean.phase_demo` → `phase_demo`  
  - `index.cases` → `cases`

**Example**: `2026-06-10T01-52-00Z_eligibility`

**Per-run file path**: `outbox/<case_ref>/<run_id>.json`

---

## 3. Per-run JSON schema

`schema_version`: **`tabular_outbox_v1`**

### 3.1 Required fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Always `tabular_outbox_v1` |
| `case_ref` | string | Case slug (§2.1) |
| `run_id` | string | Run identifier (§2.2) |
| `tool_id` | string | Catalog tool id |
| `started_at` | string | ISO-8601 UTC start time |
| `finished_at` | string | ISO-8601 UTC end time |
| `ok` | bool | Executor-level success (see §3.3) |
| `exit_code` | int \| null | Subprocess exit code; `null` when not executed |
| `message` | string | Human-readable summary |
| `artifacts` | array | Expected or observed outputs (§3.2) |
| `outbox_path` | string | Repo-relative path to this file |

### 3.2 `artifacts[]` entries

Each item:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | string | yes | e.g. `report`, `cleaned_csv`, `index` |
| `path` | string | yes | Repo-relative path |
| `logical_key` | string | no | Stable key for UI/agent lookup |

Artifacts are **pointers** to MVP case outputs; the outbox does not duplicate file contents.

### 3.3 `ok` semantics

| Scenario | `ok` | `exit_code` |
|----------|------|-------------|
| Dry-run plan | `true` | `0` (planned) |
| Unknown / disabled tool | `false` | `null` |
| Missing `intake.json` | `false` | `2` |
| `validate.eligibility` completed | `true` | `0`, `1`, or `2` (gate semantics) |
| Other CLI tools | `true` iff subprocess exit `0` | actual code |

### 3.4 Optional fields

| Field | When |
|-------|------|
| `dry_run` | `true` for dry-run plans (not written to disk) |
| `planned_command` | Dry-run: argv that would be executed |
| `stderr_tail` | Failed subprocess: last ≤500 chars of stderr |

### 3.5 Dry-run behavior

When `dry_run=True`:

- **No subprocess** is spawned
- **No** `outbox/<case_ref>/<run_id>.json` file is created
- **No** `events.jsonl` append
- Return dict includes `planned_command`, planned `artifacts`, and prospective `outbox_path`

---

## 4. `events.jsonl` format (implemented)

Append-only file: `outbox/events.jsonl`

One JSON object per line, written after each non-dry-run execute (including failures):

```json
{
  "case_ref": "demo_phase",
  "run_id": "2026-06-10T01-52-00Z_eligibility",
  "tool_id": "validate.eligibility",
  "ok": true,
  "exit_code": 2,
  "started_at": "2026-06-10T01:52:00Z",
  "finished_at": "2026-06-10T01:52:01Z",
  "dry_run": false
}
```

Dry-run plans do **not** append lines.

---

## 5. Relationship to MVP artifacts and trace

| Layer | Location | Role |
|-------|----------|------|
| **MVP L1 (authoritative)** | `cases/<case>/reports/*.json`, `cleaned/*`, etc. | Business outputs from gate / clean / bundle CLI |
| **Tabular outbox (additive)** | `outbox/<case_ref>/<run_id>.json` | Tool-layer audit: what ran, when, exit code, artifact pointers |

The outbox **does not replace** `reports/report.json`, `eligibility_result.json`, or E2E driver output. Agents and future UI may read outbox records to discover recent tool runs without parsing stdout.

Cross-reference: `docs/mvp-standard-trace-path.md` §5 (L1 trace tables).

---

## 6. Verification

```bash
python -m unittest tests.test_tabular_tool_executor -v
```

Merge gate (not modified by this ticket; run by Orchestrator / Reviewer):

```bash
python scripts/run_mvp_mainline_regression.py -v
```

---

## 7. Git hygiene

- `outbox/.gitignore` ignores all run artifacts except `.gitkeep` / `.gitignore`
- Tests MUST use `extra_args={"outbox_root": "<tmpdir>/outbox"}` to avoid polluting the repo outbox tree
