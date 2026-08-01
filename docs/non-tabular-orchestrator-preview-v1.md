# Non-Tabular Orchestrator Preview v1

> **Ticket**: W9-T4 · non-tabular-orchestrator-preview-v1  
> **Implementation**: `scripts/run_non_tabular_experiment_preview.py`  
> **Upstream**: `docs/non-tabular-shadow-flow-blueprint-v1.md` · `docs/non-tabular-routing-catalog-v1.md` · `docs/agent-run-experiment-eval-guide-v1.md`  
> **Date**: 2026-06-10  
> **Status**: preview-only — **not** wired to Tabular main chain or production intake

---

## 1. Purpose

W9-T4 delivers a **preview-only** orchestrator CLI for the Non-Tabular shadow flow. It chains:

1. **S3** — `evaluate_intake_decision_v2` (non-tabular branch)
2. **S5** — `plan_non_tabular_route()` from `routing/intake_to_non_tabular_glue.py`
3. **S6** — `select_non_tabular_tools()` stub from `tools/non_tabular_tool_selector_v1.py`

**Explicitly does not:**

- Execute heavy tools (OCR, log parsers, bundle builders)
- Write Tabular main-chain outbox or checkpoint state
- Modify `scripts/run_mvp_mainline_regression.py` or Agent standard-line defaults

---

## 2. CLI usage

```bash
# NT-A document extraction preview (JSON)
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.document.extract \
  --case-dir cases/_experiment_samples/nt_docu_stub \
  --format json

# NT-B log analysis preview (text summary)
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.log.analyze \
  --case-dir cases/_experiment_samples/nt_log_stub \
  --format text

# Skip sandbox outbox write
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.document.extract \
  --case-dir cases/_experiment_samples/nt_docu_stub \
  --format json --no-outbox

# W12-T3: preview+meta — sandbox metadata extraction (NT-A allowlist only)
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.document.extract \
  --case-dir cases/_experiment_samples/nt_docu_stub \
  --with-metadata-extraction --format json

# Equivalent mode alias
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.document.extract \
  --case-dir cases/_experiment_samples/nt_docu_stub \
  --mode preview+meta --format json
```

| Flag | Default | Description |
|------|---------|-------------|
| `--task-type` | (required) | `non_tabular.document.*` or `non_tabular.log.*` |
| `--case-dir` | (required) | Case directory with `intake.json` |
| `--format` | `text` | `text` summary or full `json` |
| `--no-outbox` | off | Skip writing preview JSON |
| `--outbox-root` | `outbox/non_tabular_experiment/` | Sandbox outbox override |
| `--with-metadata-extraction` | off | W12-T3: run sandbox metadata extractor (NT-A allowlist) |
| `--mode` | `preview` | `preview` or `preview+meta` (alias for metadata flag) |

---

## 3. Output shape

### 3.1 Top-level keys

| Key | Description |
|-----|-------------|
| `ok` | Orchestrator completed without internal failure |
| `experiment_id` | UUID for this preview run |
| `task_type` | Requested non-tabular task type |
| `decision` | v2 decision summary (decision, risk_level, rationale) |
| `planned_route` | Glue route plan (selector_task_type, skill_card, notes) |
| `planned_tools` | Ordered tool_id list from routing catalog |
| `selector_view` | Selector stub candidates (all `planned_only`) |
| `content_summary` | **W11-T2** metadata-only case scan (`inspect_non_tabular_case_dir`) |
| `processing_summary` | **W12-T3** optional sandbox document metadata extraction |
| `risk` | Aggregated risk / signals / gate notes |
| `mode` | `preview` (default) or `preview+meta` when metadata extraction enabled |
| `final_status` | `preview_ready` or `blocked` |
| `outbox_path` | Relative path when sandbox outbox written |

### 3.2 `content_summary` (W11-T2 lightweight inspector)

Populated by `tools/non_tabular_lightweight_inspector_v1.py` during step `S4_lite_content_summary`.
Uses **path + stat only** — no file content reads, no OCR, no log parsing.

| Field | Description |
|-------|-------------|
| `ok` | Inspector completed (case dir exists) |
| `metadata_only` | Always `true` for v1 |
| `inspection_method` | Always `stat_only` |
| `file_count` | Total files under `case_dir` (recursive) |
| `total_size_bytes` | Sum of `st_size` |
| `largest_file_bytes` | Max single-file size |
| `extension_distribution` | Map of extension → count (e.g. `pdf`, `log`, `(no_ext)`) |
| `type_tag_distribution` | Coarse tags from extension heuristics (`document`, `image`, `log`, …) |
| `filename_pattern_hints` | Detected name patterns (`date_in_filename`, `log_like_name`, …) |
| `notes` | Warnings (e.g. empty case dir) |

**NT-A example** (mixed documents):

```json
{
  "ok": true,
  "metadata_only": true,
  "inspection_method": "stat_only",
  "file_count": 4,
  "total_size_bytes": 226,
  "extension_distribution": {"docx": 1, "json": 1, "pdf": 1, "png": 1},
  "type_tag_distribution": {"document": 2, "image": 1, "structured": 1},
  "filename_pattern_hints": []
}
```

**NT-B example** (log stub):

```json
{
  "ok": true,
  "metadata_only": true,
  "inspection_method": "stat_only",
  "file_count": 3,
  "total_size_bytes": 142,
  "extension_distribution": {"json": 1, "log": 2},
  "type_tag_distribution": {"log": 2, "structured": 1},
  "filename_pattern_hints": ["date_in_filename", "log_like_name"]
}
```

### 3.3 Sandbox outbox

Written to:

```text
outbox/non_tabular_experiment/<timestamp>_<case_stub>.json
```

Contains preview metadata only (no secrets, no raw file contents). When `--with-metadata-extraction` / `--mode preview+meta` is used, includes `processing_summary`.

---

## 3.4 `processing_summary` (W12-T3 sandbox metadata extraction)

Optional step `S7_metadata_extraction` runs only when **all** gates pass:

1. CLI flag `--with-metadata-extraction` or `--mode preview+meta`
2. `task_type` = `non_tabular.document.extract` (NT-A)
3. `case_dir` on allowlist (`cases/_experiment_samples/nt_docu_stub` or path containing `nt_docu_stub`)
4. `intake.json` `client_ref` = `docu-corp`

Implemented by `tools/document_metadata_extractor_v1.py` (`document_metadata_extractor_v1`).

**Allowed fields per document:** `size_bytes`, `mime_type`, `page_count` (PDF/DOCX), `encoding` (text). **No OCR or full-text parse.**

| Field | Description |
|-------|-------------|
| `ok` | Extraction completed |
| `executed` | `true` when gates passed and files scanned |
| `tool_id` | `document_metadata_extractor_v1` |
| `sandbox_only` | Always `true` |
| `files_processed` | Count of document files scanned |
| `documents` | List of per-file metadata dicts |
| `eligibility` | Gate result when flag set but not executed |

**NT-A preview+meta example:**

```json
{
  "processing_summary": {
    "ok": true,
    "tool_id": "document_metadata_extractor_v1",
    "sandbox_only": true,
    "experimental": true,
    "extraction_method": "metadata_only",
    "enabled": true,
    "executed": true,
    "files_processed": 2,
    "documents": [
      {
        "path": "docs/sample.pdf",
        "size_bytes": 128,
        "extension": "pdf",
        "mime_type": "application/pdf",
        "page_count": 3
      },
      {
        "path": "docs/brief.docx",
        "size_bytes": 512,
        "extension": "docx",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "page_count": 2
      }
    ],
    "message": "extracted metadata for 2 document(s)"
  }
}
```

**NonScope:** does not write Tabular outbox, production notify, or agent checkpoint state.

---

## 4. Supported task types

| Task type | Skill | Selector intent |
|-----------|-------|-----------------|
| `non_tabular.document.extract` | NT-A | `document_extract` |
| `non_tabular.log.analyze` | NT-B | `log_analyze` |

All other families (e.g. `tabular.cleaning.mvp`) → **`blocked`** at orchestrator entry.

---

## 5. Verification

```bash
python -m unittest tests.test_non_tabular_lightweight_inspector_v1 -v
python -m unittest tests.test_document_metadata_extractor_v1 -v
python -m unittest tests.test_non_tabular_orchestrator_preview_v1 -v
```

Covers NT-A / NT-B preview, JSON structure, sandbox outbox path, Tabular task_type blocking, W11-T2 `content_summary`, and W12-T3 `processing_summary` gating.

---

## 6. Related artifacts

| Artifact | Path |
|----------|------|
| Routing catalog | `routing/non_tabular_routing_catalog_v1.yaml` |
| Tool catalog | `tools/non_tabular_tool_catalog_v1.json` |
| Glue planner | `routing/intake_to_non_tabular_glue.py` |
| Selector stub | `tools/non_tabular_tool_selector_v1.py` |
| Lightweight inspector | `tools/non_tabular_lightweight_inspector_v1.py` |
| Metadata extractor (W12-T3) | `tools/document_metadata_extractor_v1.py` |
| Decision v2 | `routing/intake_decision_rules_v2.py` |
| Ticket state | `04_Workflows/tickets/W9-T4-non-tabular-orchestrator-preview-v1_state.md` |
| W11-T2 state | `04_Workflows/tickets/W11-T2-non-tabular-lightweight-content-checks-v1_state.md` |
| W12-T3 state | `04_Workflows/tickets/W12-T3-non-tabular-first-real-processing-step-sandbox-v1_state.md` |

---

*Non-Tabular Orchestrator Preview v1 · W9-T4 + W12-T3 · 2026-06-10*
