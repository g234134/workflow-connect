# Tabular Cleaning Profiles v1

> **Role**: Low-risk **cleaning profile** registry for tabular MVP mainline  
> **Status**: v1 · doc + code registry · **非** prod gate  
> **Date**: 2026-06-27  
> **Upstream**: `docs/tabular-cleaning-automation-manifest-v1.md` · `docs/TABULAR_MVP_SSOT.md`  
> **Code**: `notebooks/csv_cleaning/cleaning_profiles_v1.py` · consumed by `clean_phase_demo.py` (dispatches `clean.generic` when configured)

---

## 0. Purpose

Cleaning profiles decouple **case-specific column roles and rule parameters** from hard-coded runners. The unified automation driver resolves `profile_id` from `intake.json` (or case-dir fallback) and records it in `reports/automation_run_log.json` and E2E summaries.

**v1 scope**: three low-risk profiles — `phase_demo_v1`, `sampleco_order_profile`, `generic_low_risk_profile`.

---

## 1. Profile index

| `profile_id` | Case | `risk_level` | Runner | HITL CP-B default |
|--------------|------|--------------|--------|-------------------|
| `phase_demo_v1` | `cases/demo_phase/` | low | `clean.phase_demo` | Skip when `output_guard.ok` |
| `sampleco_order_profile` | `cases/sampleco/2026-0001/` | low | `clean.phase_demo` | **Required** on `output_guard.warning` |
| `generic_low_risk_profile` | `cases/internal/generic-low-risk/` (+ future cases) | low | `clean.generic` | Skip when `output_guard.ok` |

---

## 2. `phase_demo_v1`

**Anchor**: C2-D1 internal demo · 7-row Phase CSV.

### 2.1 Identity

| Field | Value |
|-------|-------|
| `profile_id` | `phase_demo_v1` |
| `risk_level` | **low** |
| `runner` | `clean.phase_demo` |
| `intake.json` key | `"cleaning_profile": "phase_demo_v1"` |

### 2.2 Field roles

| Column | Role | Notes |
|--------|------|-------|
| `Phase` | `segment_key` | One logical row per phase value after dedup |
| `名稱` | `label` | Human-readable milestone name |
| `之前` | `percent_before` | Prior completion % (0–100) |
| `現在（建議）` | `percent_target` | Target % (0–100); dedup tie-breaker |

### 2.3 Rules

| Category | Policy |
|----------|--------|
| **Missing** | Drop when Phase **and** 名稱 blank; reject when Phase blank |
| **Duplicate** | Dedup by `Phase`; keep row with max `現在（建議）` |
| **Anomaly** | Flag percent ∉ [0, 100]; retain row with warning |
| **Format** | Normalize `Phase N` casing; parse `%` and 0–1 fractions |

### 2.4 HITL requirements

| Checkpoint | When required | When can skip |
|------------|---------------|---------------|
| **CP-A** | Always (automation driver default) | Never on first run |
| **CP-B** | `output_guard.status=warning` | `output_guard.status=ok` (ratio ≥ 0.5) |

### 2.5 Expected outcome (regression)

- Input: 7 rows → output: 5 accepted · `qa_status=pass_with_warnings`
- Gate: `review_needed` (`rows<100`) — driver may need `--force` on standalone clean; automation continues after CP-A approve
- `output_guard`: `ok` (ratio 0.7143)

---

## 3. `sampleco_order_profile`

**Anchor**: first near-real client fixture · 115-row milestone export.

### 3.1 Identity

| Field | Value |
|-------|-------|
| `profile_id` | `sampleco_order_profile` |
| `risk_level` | **low** |
| `runner` | `clean.phase_demo` |
| `intake.json` key | `"cleaning_profile": "sampleco_order_profile"` |

### 3.2 Field roles

| Column | Role | Notes |
|--------|------|-------|
| `Phase` | `milestone_phase` | Sprint phase bucket (non-unique in raw export) |
| `名稱` | `workstream_name` | Module / workstream label |
| `之前` | `percent_before` | Prior progress % |
| `現在（建議）` | `percent_target` | Suggested target % |

### 3.3 Rules

| Category | Policy |
|----------|--------|
| **Missing** | Same as phase demo; tolerate sparse percent fields with warnings |
| **Duplicate** | Dedup by `Phase` only (v1); keep max `現在（建議）` — **high collapse ratio** on multi-row exports |
| **Anomaly** | Flag out-of-range percents; expect `output_guard` warning on removal ratio |
| **Format** | Phase casing normalize · percent parse · trim whitespace |

### 3.4 HITL requirements

| Checkpoint | When required | When can skip |
|------------|---------------|---------------|
| **CP-A** | Always | Never on first run |
| **CP-B** | **`output_guard.warning`** (ratio 0.0696 < 0.5) | Only when guard returns `ok` |

### 3.5 Expected outcome (regression)

- Input: 115 rows → output: 8 accepted · `qa_status=pass_with_warnings`
- Gate: `accepted` — no `--force` required on clean step
- `output_guard`: `warning` · `delivery_ready=false` after approve (by design)

### 3.6 Known limits

- `multi_row_milestone_export` — raw has many rows per phase
- `phase_dedup_semantics_unstable` — business key is Phase+名稱; v1 uses phase-only dedup
- `marginal_cleaning_quality` — low accepted ratio by design in v1

---

## 4. `generic_low_risk_profile`

**Anchor**: internal dummy case · simple primary-key + numeric table for new low-risk cases.

### 4.1 Identity

| Field | Value |
|-------|-------|
| `profile_id` | `generic_low_risk_profile` |
| `risk_level` | **low** |
| `runner` | `clean.generic` |
| `intake.json` key | `"cleaning_profile": "generic_low_risk_profile"` |
| Schema source | `intake.json` → `schema.column_roles` (or `primary_key` + typed column lists) |

### 4.2 Allowed column types

| Type | Purpose | Required |
|------|---------|----------|
| `primary_key` | Unique row identifier; dedup key | **Yes** (exactly one column) |
| `numeric` | Parseable numbers; optional range check | Optional |
| `category` | Low-cardinality labels; trim only | Optional |
| `text` | Free text; trim whitespace | Optional |

**Constraints**: 2–20 columns · all declared roles must exist in CSV header · no PII columns in v1 generic path.

### 4.3 Example schema (intake.json)

```json
"schema": {
  "primary_key": "order_id",
  "column_roles": {
    "order_id": "primary_key",
    "product": "category",
    "amount": "numeric",
    "notes": "text"
  },
  "numeric_range": {
    "amount": { "min": 0, "max": 10000 }
  }
}
```

Alternative: use `numeric_columns`, `category_columns`, `text_columns` arrays instead of `column_roles`.

### 4.4 Rules

| Category | Policy |
|----------|--------|
| **Missing** | Drop row when `primary_key` blank; blank category/text retained with `_flags` warning |
| **Duplicate** | Dedup by `primary_key`; keep row with highest first `numeric` compare column |
| **Anomaly** | Flag numeric outside optional `numeric_range`; flag unparseable numeric strings |
| **Format** | Trim category/text · parse numeric (strip commas) |

### 4.5 HITL requirements

| Checkpoint | When required | When can skip |
|------------|---------------|---------------|
| **CP-A** | Always on automation mainline | Never on first run |
| **CP-B** | `output_guard.warning` | `output_guard.ok` when accepted ratio ≥ 0.5 |

### 4.6 Expected outcome (fixture regression)

- Case: `cases/internal/generic-low-risk/`
- Input: 7 rows → output: 5 accepted · `qa_status=pass_with_warnings`
- Gate: `review_needed` (`rows<100`) — same as demo_phase
- `output_guard`: `ok` (ratio ≈ 0.7143)

---

## 5. Resolution order

1. CLI `--profile-id` (override)
2. `intake.json` → `cleaning_profile`
3. Case-dir fallback map in `cleaning_profiles_v1.py` → `_CASE_DIR_PROFILE`

For `generic_low_risk_profile`, runtime config is merged via `build_runtime_profile()` from intake schema + CSV headers.

---

## 6. Case → profile mapping

| Case dir | `profile_id` | Notes |
|----------|--------------|-------|
| `cases/demo_phase` | `phase_demo_v1` | C2-D1 regression anchor |
| `cases/sampleco/2026-0001` | `sampleco_order_profile` | Near-real milestone export |
| `cases/internal/generic-low-risk` | `generic_low_risk_profile` | Internal dummy · generic schema demo |

Future cases: set `"cleaning_profile": "generic_low_risk_profile"` in `intake.json` and declare `schema.column_roles` matching CSV headers.

---

## 7. Low-risk allowlist boundary

**In allowlist (v1 profiles)**:

- `demo_phase` / `phase_demo_v1`
- `sampleco/2026-0001` / `sampleco_order_profile`
- `internal/generic-low-risk` / `generic_low_risk_profile` (internal fixture)

**Not in low-risk allowlist (require `--force` or CP-A approve)**:

- `additional_demo`
- `sandbox_client`
- `reviewer-test/*`
- Unknown / unregistered profiles
- Non-tabular or experimental fixtures

---

## 8. Observability

| Artifact | `profile_id` field |
|----------|-------------------|
| `reports/automation_run_log.json` | Top-level `cleaning_profile_id` |
| `reports/cleaning_stats.json` | `cleaning_profile_id` in before/after/meta |
| `reports/report.json` | `meta.cleaning_profile_id` + top-level |
| E2E validation summary | `cleaning_profile_id` (when cleaning step runs) |

---

## 9. Cross-references

| Doc | Section |
|-----|---------|
| `docs/TABULAR_MVP_SSOT.md` | Mainline + profile note |
| `docs/tabular-cleaning-automation-manifest-v1.md` | §1.1 allowlist |
| `docs/tabular-mainline-e2e-verification-report-v1.md` | Latest E2E including generic case |
| `docs/C2-P2_RUNBOOK.md` | §3.4 automation overlay |
| `cases/index.json` | `cleaning_profile` per registered case |
