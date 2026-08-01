# MVP Mainline Regression (W1-T3)

> **Purpose**: Lightweight regression for the tabular cleaning main chain.  
> **Scope**: Flow smoke only — not full edge-case coverage.  
> **Authority chain**: `docs/MVP_CASE_E2E_DoD_v0.1.md` · `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`

---

## 1. What is covered

Each regression case runs the **existing E2E driver** (no duplicated pipeline logic):

```text
gate (P2) → cleaning (P3) → bundle (P4)
```

Entry point: `scripts/run_case_e2e_validation.py`

| Case | Path | Gate expectation | Notes |
|------|------|------------------|-------|
| **demo_phase** | `cases/demo_phase` | `review_needed` | E2E uses `--force-review`; cleaning runs with `--force` |
| **sampleco** | `cases/sampleco/2026-0001` | `accepted` | Ratio guard `warning` (115 → 8 rows) is expected |

---

## 2. How to run

### One command (recommended)

```bash
python scripts/run_mvp_mainline_regression.py
```

Verbose:

```bash
python scripts/run_mvp_mainline_regression.py -v
```

### Unittest directly

```bash
python -m unittest tests.test_mvp_mainline -v
```

### Single case (manual debug)

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json
```

**Success**: process exit code `0`; summary shows `overall_ok: True`.  
**Failure**: exit code `1`; stdout/stderr includes step-level hints (`gate` / `cleaning` / `bundle`).

---

## 3. When to re-run

Re-run this suite after changes to any of:

| Area | Typical paths |
|------|----------------|
| Eligibility gate | `scripts/check_case_eligibility.py`, `notebooks/csv_cleaning/case_eligibility.py` |
| Cleaning runner | `notebooks/csv_cleaning/clean_phase_demo.py`, `case_intake_loader.py` |
| Delivery bundle | `scripts/build_case_delivery_bundle.py`, `notebooks/csv_cleaning/case_delivery_bundle.py` |
| Output guard | `notebooks/csv_cleaning/output_guard.py` |
| E2E driver | `scripts/run_case_e2e_validation.py` |
| Standard fixtures | `cases/demo_phase/**`, `cases/sampleco/2026-0001/**` |

Optional but recommended before customer demos or Wave MVP releases.

**Not required for**: H-line ask routing, monitoring ingest, eval-gate CI, or dark `gov_core_system` changes unrelated to case cleaning.

**Also run** (Tabular main chain · HITL + control plane): `scripts/run_demo_phase_regression_smoke.py` — see `docs/tabular-demo_phase-regression-v1.md`. Required after changes to automation state, unified driver, HITL resume, or delivery approve (not covered by this MVP E2E-only suite).

---

## 4. First steps when a test fails

1. **Identify the failing step** — read unittest output or re-run with `--json`:
   ```bash
   python scripts/run_case_e2e_validation.py --case-dir cases/<case> --json
   ```
2. **Gate failure** — inspect `reports/eligibility_result.json` or run gate alone:
   ```bash
   python scripts/check_case_eligibility.py --case-dir cases/<case> --json
   ```
3. **Cleaning failure** — check stderr from `clean_phase_demo.py`; confirm `raw/` input exists per `intake.json`.
4. **Bundle failure** — confirm `reports/report.json` exists; check `output_guard` / signoff paths.
5. **Fixture drift** — if row counts changed intentionally, update assertions in `tests/test_mvp_mainline.py` and document in `cases/README.md` or case reports.

---

## 5. Related tests

| Module | Focus |
|--------|--------|
| `tests/test_case_eligibility.py` | Gate unit tests (includes demo_phase / sampleco probes) |
| `tests/test_case_runner.py` | Cleaning runner CLI |
| `tests/test_case_delivery_bundle.py` | Bundle structure |
| `tests/test_output_guard.py` | Ratio guard + single-case E2E JSON |
| `tests/test_new_cleaning_case.py` | Intake CLI (not part of this regression) |

This regression **complements** unit tests; it does not replace them.

---

## 6. CI note

Not wired into GitHub Actions by default (local / pre-release). To add to CI, invoke:

```yaml
- run: python scripts/run_mvp_mainline_regression.py
```

Requires no venv beyond repo-root Python 3.10+.
