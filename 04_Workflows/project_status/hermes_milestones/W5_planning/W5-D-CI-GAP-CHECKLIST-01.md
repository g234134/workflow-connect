# W5-D-CI-GAP-CHECKLIST-01 — W5 CI Gap & Plumbing Checklist

> **Status:** Read-only survey (只讀＋文件)
> **Scope:** All CI / plumbing / data pipeline gaps discovered during W5-A and W5-D delivery.
> **Hard boundary:** No CI modifications, no new implementations, no speculation stated as fact.

---

## A. Gap Overview

| Gap ID | Short Name | Status | W5 Ticket(s) | Impact |
|--------|-----------|--------|-------------|--------|
| **G1** | CI data pipeline v0 (shadow_batch → spool) | ✅ **已修復** | W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-01 | Nightly CI no longer loops static fixture forever |
| **G2** | ibridge_exporter tags pipeline (suspected → confirmed code is correct) | ✅ **已勘誤** | W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01 v0.2 | Tags correctly flow through ibridge_exporter; root cause is elsewhere |
| **G3** | dryrun/core.py `_normalize_export_row()` overwrites real tags with synthetic tags | ⚠️ **已發現未修** | W5-A-RUNTIME-03-K2-TAGS-TRACE-01 | Real infra_risk tags lost before ENF-RULE-1 evaluation |
| **G4** | eval_export/v1 JSONL has no CI producer (CI-GAP-1) | ⚠️ **已發現未修** | W5-D-CI-GAP-1_plan.md (方案卡，未實現) | eval_stats can never see real data |
| **G5** | K-2 eval_gate.tags may not be populated in real prod shadow (upstream uncertainty) | 🔍 **待確認** | W5-A-RUNTIME-03-K2-TAGS-TRACE-01 | If upstream tags never generated, all downstream fixes are moot |
| **G6** | Only single-day data available (2026-05-30), no cross-day drift | ⚠️ **已發現未修** | W5-A-RUNTIME-03-POLICY-MINING-03 | Cannot assess ENF-RULE stability across time |
| **G7** | Missing edge case fixtures (score < 0.875, edge_unknown) | ⚠️ **已發現未修** | W5-A-RUNTIME-03-POLICY-MINING-01/02/03 | gate_ok_score_low rule never validated |
| **G8** | ENF-RULE-1 not yet in any blocking canary | ⚠️ **已發現未修** | W5-A-RUNTIME-03-LIMITED-DENY_plan.md | Intentionally deferred; conditional on ≥7 nightly runs + real data hit |
| **G9** | eval-shadow-nightly can only see smoke fixture in PR (no shadow data) | ✅ **已修復（部分）** | W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-01 | CI data pipeline fetches latest batch; PR path still uses fixture |
| **G10** | Fixture provenance: smoke_eval_results.jsonl source_ref.line_index skew | ✅ **已修復** | W5-D-SMOKE-FIXTURE-PROVENANCE-IMPLEMENTATION-01 | Schema docs updated; line_index corrected |
| **G11** | Fixture provenance: eval_export_sample.jsonl source_ref.line_index skew | ✅ **已修復** | W5-D-FIXTURE-PROVENANCE-IMPLEMENTATION-01 | Schema docs updated; line_index corrected |
| **G12** | W4-FIX-B: index_status.json had file_count=0 / chunk_count=0 (sample data) | ✅ **已修復** | W5-D-W4-FIX-B-IMPLEMENTATION-01 | Real file index backfilled |
| **G13** | Pipeline: spool contains 3 different JSON formats (ok/record, flat, case_name) | ⚠️ **已發現未修** | W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01 | `normalize_shadow_record()` handles it but format chaos makes debugging harder |
| **G14** | No automated alerting on CI data pipeline health (spool staleness) | ⚠️ **已發現未修** | W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01 | If no batch uploaded, CI silently falls back to fixture with no alert |
| **G15** | No cross-reference between gov-gate-metrics.yml and eval_export/v1 tracks | ⚠️ **已發現未修** | W5-D-CI-GAP-1_plan.md | Two parallel JSONL schemas (gov-metrics-0.1 vs eval_export/v1) never correlated |
| **G16** | fail-on-deny governance design deferred (no implementation in W5) | 🔍 **待確認** | W5-C-FAIL-ON-DENY-DESIGN | Design only; actual enforcement deferred to W6+ |

---

## B. Detailed Gap Descriptions

### B1. ✅ G1 — CI Data Pipeline v0 (shadow_batch → spool)

**What was wrong:**
- `eval-shadow-nightly` had a bootstrap step that always copied from fixture because GitHub Actions runner is ephemeral → `k2_shadow_spool.jsonl` never persists between runs.
- Every nightly saw the same 4–6 fixture records. Zero real data ever entered the governance chain.
- Confirmed by W5-A-RUNTIME-03-NIGHTLY-STATUS-CHECK-01: all dry-run / preview outputs came from smoke fixture only.

**What was fixed:**
- Added `scripts/fetch_latest_shadow_batch.sh` — searches `artifacts/eval/shadow_batch_*.jsonl` by date suffix, copies latest to `SHADOW_SPOOL`.
- Added `Fetch latest shadow batch (real data before fixture)` step in `eval-gate-ci.yml` eval-shadow-nightly job (L241-249).
- Fallback bootstrap still exists: only fires when spool is empty after fetch step.
- Initial batch: `shadow_batch_20260530.jsonl` with 6 records (4 fixture + 2 real prod-shadow).

**Evidence:** `scripts/fetch_latest_shadow_batch.sh` exists; CI YAML shows "Fetch latest shadow batch" + "Bootstrap from fixture" steps; MINING-03 confirms 2 real prod-shadow records processed.

---

### B2. ✅ G2 — ibridge_exporter Tags Pipeline (Confirmed Correct)

**What was suspected:**
- MINING-03 §3.3 claimed `_k2_summary_to_ibridge()` did not propagate `k2_summary.tags` to flat ibridge output.
- Initial design proposed fixing the "missing tags" in ibridge_exporter.

**What the code review found:**
- `_k2_summary_to_ibridge()` (L247): `tags = _coerce_tags(summary.get("tags") or [])` ✅
- `EXPORT_FIELD_NAMES` (L50): includes `"tags"` ✅
- Tests: `test_k2_summary_tags_preserved_in_ibridge_record` + `test_k2_summary_missing_tags_defaults_to_empty_list` both pass ✅
- Real data confirms: `shadow_ibridge_records.latest.jsonl` for prod-shadow records has `tags: ["infra_risk"]` ✅

**Evidence:** `W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01.md` §1.1 full table; real data comparison in §2.2.

---

### B3. ⚠️ G3 — dryrun/core.py Overwrites Real Tags with Synthetic Tags

**The actual break in the chain:**
- `_normalize_export_row()` in `dryrun/core.py` calls `_synthetic_gate_from_metrics()` which creates a **new** `tags` list **solely from metrics** — it does NOT read the original `record.get("tags")` from the ibridge JSONL.
- Real tags like `["infra_risk"]` are silently overwritten with `[]`.
- Result: ENF-RULE-1 sees `tags=[]` and never fires on real prod-shadow records with `infra_risk`.

**Impact:**
- ENF-RULE-1 "0 FP" is meaningless — it never evaluated real records because tags were stripped before rules checked them.
- All MINING-03 ENF-RULE-1 statistics only apply to the path where tags survive (smoke fixture records with tags set directly in metrics).

**Fix needed:** In `_normalize_export_row()`, merge original `record.get("tags")` with synthetic tags, or pass-through the original tags.

---

### B4. ⚠️ G4 — eval_export/v1 JSONL Has No CI Producer (CI-GAP-1)

**What's missing:**
- `eval_exporter` is called by **no CI job** — it only runs manually.
- `eval_stats` and `eval_stats_report.md` can only consume fixture data (N=3).
- The data chain is: `ibridge_exporter → shadow_ibridge_records.latest.jsonl → eval_ci_check ✅` but `→ eval_exporter ❌ → eval_stats ❌ → report update ❌`.

**Options (per W5-D-CI-GAP-1_plan.md):**
- **Option A (recommended):** Add one `python -m observability.eval_exporter` step in eval-shadow-nightly job.
- **Option B:** Create standalone `eval-export-nightly.yml` workflow.
- **Option C:** Document and defer.

**Status:** No decision has been made. The plan exists but no implementation ticket opened.

---

### B5. 🔍 G5 — K-2 eval_gate.tags Upstream Uncertainty

**What's unknown:**
- The K-2 LangGraph flow generates tags via `_RULES` in `eval_gate.py` (`_rule_infra_risk`, `_rule_high_retry`, etc.).
- It's unclear whether real prod shadow K-2 invocations actually populate `eval_metadata.eval_gate.tags` meaningfully.
- The 2 real prod-shadow records in `shadow_batch_20260530.jsonl` show `k2_summary.tags = ["infra_risk"]` → tags do exist in this batch. But is this representative?

**Needs:** Check `k2_ask_shadow.py:summarize_k2_output()` upstream; confirm `eval_metadata.eval_gate.tags` is reliably populated in real prod conditions.

---

### B6. ⚠️ G6 — Only Single-Day Data Available

**Observation:**
- All 5 dryrun runs in MINING-03 are from 2026-05-30. No cross-day data exists.
- `eval-shadow-nightly` has cron schedule (`0 6 * * *`) but each run repeats fixture + same `shadow_batch_20260530.jsonl`.
- No historical accumulation: no mechanism to persist or compare data across days.

**Effect:** Any conclusion about ENF-RULE stability or drift resistance is statistically meaningless.

---

### B7. ⚠️ G7 — Missing Edge Case Fixtures

**Specific gaps:**
- No record with `score < 0.875` → cannot validate `gate_ok_score_low` rule.
- No record triggering `edge_unknown` → cannot validate unknown fallback.
- Only 1 ENF-RULE-1 hit ever: `t-infra` (smoke fixture, timeout + infra_risk).

**Effect:** 2 out of 5 governance rules (`gate_ok_score_low` and `edge_unknown`) have never been exercised.

---

### B8. ⚠️ G8 — ENF-RULE-1 Not in Blocking Canary

**Per MINING-03 §6.1:**
- **Decision:** Do NOT enter blocking canary yet.
- **Prerequisites before canary:**
  1. Fix `dryrun/core.py` tag propagation (G3) → real records can be evaluated.
  2. Accumulate ≥7 nightly runs with real data.
  3. At least 1 real (non-fixture) record matches ENF-RULE-1.
  4. FP count ≤ 1 during observation.
  5. Kill-switch deployed and verified.
- **If forced to start (contingency):** limit to eval-shadow-nightly only, `continue-on-error: true`, ENF_RULE_1_BLOCKING_ENABLED=0 (default off).

---

## C. Pipeline Data Flow Diagram (Current State)

```
Prod K-2 shadow output
    │
    │  (manual upload / batch export)
    ▼
shadow_batch_YYYYMMDD.jsonl           ──→  artifacts/eval/
    │                                        (fetch by script)
    ▼
[k2_shadow_spool.jsonl]               ──→  ephemeral CI spool
    │
    ├──→ ibridge_exporter              ──→  shadow_ibridge_records.latest.jsonl ✅
    │       │
    │       ├──→ eval_ci_check           ──→ gate verdict (no output file) ✅
    │       │
    │       ├──→ dryrun_ci_wrapper      ──→ per_record.jsonl + summary.md ✅
    │       │       │
    │       │       └──→ _normalize_export_row() ❌ G3: tags overwritten
    │       │
    │       ├──→ eval_exporter           ──→ ❌ G4: never called in CI
    │       │
    │       └──→ enf_preview_wrapper     ──→ GOV-ENF-PREVIEW log ✅
    │
    └──→ eval_exporter (manual only)    ──→ eval_export/v1 JSONL (N=3 fixture)
```

---

## D. Priority Recommendations for Next Milestone (W6 priority)

| Priority | Gap | Action | Why Now |
|----------|-----|--------|---------|
| **P0** | **G3 — dryrun/core.py tags overwritten** | Fix `_normalize_export_row()` to merge original ibridge tags | Blocks all real-data evaluation: ENF-RULE-1, ENF-RULE-2, C3-01, C3-02 all depend on correct tags |
| **P0** | **G4 — eval_export/v1 CI producer** | Implement Option A (add one step in eval-shadow-nightly) | Unlocks eval_stats + eval_stats_report with real data; needed for threshold recommendations |
| **P1** | **G14 — Spool staleness alerting** | Add log warning when mode=fixture and batch files exist | Silent fallback is worse than noisy failure; team needs to know when pipeline is idle |
| **P1** | **G7 — Edge case fixtures** | Add score=0.7, score=0.5 records to smoke fixture | Validates gate_ok_score_low and edge_unknown rules; quick win (read-only; just update catalog) |
| **P2** | **G5 — K-2 upstream tag investigation** | Code review / log inspection on prod shadow K-2 flow | Must confirm tags are generated upstream; otherwise G3 fix is moot |
| **P2** | **G15 — Cross-track metadata** | Add traceability between gov-metrics and eval_export | Required for unified governance picture in W6 |

---

## E. File & Workflow Reference

| File | Role | Gaps Referenced |
|------|------|----------------|
| `.github/workflows/eval-gate-ci.yml` | CI workflow (PR + nightly) | G1, G4, G9 |
| `scripts/fetch_latest_shadow_batch.sh` | CI data pipeline fetch | G1 |
| `observability/eval_exporter.py` | eval_export/v1 producer | G4 |
| `observability/eval_ci_check.py` | CI gate judgement | G4 (builds export line but never serialises) |
| `observability/eval_stats.py` | Distribution analysis + threshold recommender | G4, G7 |
| `observability/ibridge_exporter.py` | K-2 spool → flat ibridge converter | G2 (confirmed correct), G13 |
| `tools/dryrun/core.py` | Dry-run CLI core | G3 (tags overwritten), G13 |
| `tools/enf_preview_wrapper.py` | ENF preview classifier | G3, G8 |
| `artifacts/eval/shadow_batch_20260530.jsonl` | Initial shadow batch (6 records) | G1, G6 |
| `artifacts/eval/k2_shadow_spool.jsonl` | K-2 spool (local; not CI-persistent) | G1 |
| `artifacts/eval/smoke_eval_results.jsonl` | Smoke fixture (N=3) | G7, G10 |
| `tests/fixtures/eval/shadow_raw_records.jsonl` | Spool bootstrap fixture (N=4, 3 formats) | G13 |
| `workflow_v2/observability/gov_gate_metrics/local.jsonl` | Gov gate metrics (gov-metrics-0.1) | G15 |

---

## F. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v0.1 | 2026-05-31 | W5-D-CI-GAP-CHECKLIST-01 | Initial catalog: 16 gaps (5 ✅ fixed, 8 ⚠️ discovered but unfixed, 2 🔍 pending confirmation, 1 deferred) |

---

*Generated: 2026-05-31 by W5-D-CI-GAP-CHECKLIST-01*
