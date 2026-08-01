# Phase 8.5 / 8.6 — Orchestration Bridge Smoke Runbook (v1)

> **Ticket**: WD-P85-T2-bridge-runbook-index-closure-v1  
> **Flow key**: `minimal_intake_browser`  
> **Related specs**: `04_Workflows/PHASE8_6_MINIMAL_ORCHESTRATION_BRIDGE_MVP_v0.1.md` · `04_Workflows/PHASE8_6A_MINIMAL_BRIDGE_API_ENDPOINT_MVP_v0.1.md` · `WORKFLOW_INDEX.md` §1.4

## Purpose

One-page, copy-paste smoke path for the minimal orchestration bridge: Phase 7.5 intake → Phase 6.5 `phase6_5_pre_state` → optional Phase 8.5 in-memory browser plan. Covers core bridge unit tests (P85-T1) and optional live HTTP against `POST /api/orchestration/bridge`.

## §0.3 CI advisory (non-blocking)

GitHub Actions workflow **`.github/workflows/bridge-smoke.yml`** (Actions UI: **P85 Bridge Smoke CI (advisory)**) runs two **advisory** jobs (neither is a branch-protection required check):

| Job id | Actions display name | Scope | Expected | Skip when |
|--------|---------------------|-------|----------|-----------|
| **`p85-bridge-smoke-a`** | **P85 Bridge Smoke A (advisory · 20/20)** | `python -m unittest tests.test_minimal_orchestration_bridge -v` (core bridge) | **20/20** | `gov_core_system` tree missing · pip install failed · `fastapi` or core imports unavailable |
| **`p85-bridge-smoke-b`** | **P85 Bridge Smoke B (advisory · HTTP API)** | `python -m unittest tests.test_app_api_orchestration_bridge -v` (HTTP API / `TestClient`) | **7/7** | Same tree/deps gates · `tests.test_app_api_orchestration_bridge` import fails |

| Item | Detail |
|------|--------|
| **cwd** | `gov_core_system` venv root (same as manual Smoke A / B) |
| **Triggers** | Daily schedule (UTC 06:00) · `workflow_dispatch` · path-filtered `pull_request` on bridge-related paths (incl. `orchestration_bridge_run_record.py`, `test_app_api_orchestration_bridge.py`, `app_api.py`, `tests/fixtures/browser_dom/**`) |
| **Skip** | Each job logs `::notice title=Bridge Smoke … skipped::reason=…` and **exits success** when deps are insufficient |
| **Failure** | Both jobs use `continue-on-error: true` — test failures **do not block merge**; treat as early warning only |
| **Not in CI** | **Smoke C** (live curl against running uvicorn) remains **manual** only |

### Scenario 1 vs Scenario 2 (GA)

| Scenario | Trigger | Jobs | Expected |
|----------|---------|------|----------|
| **Scenario 1 — happy path** (default) | Daily cron · path-filtered PR · `workflow_dispatch` with **scenario = default** | `p85-bridge-smoke-a` · `p85-bridge-smoke-b` | A **20/20** · B **7/7** · log `Bridge Smoke A/B passed` · no skip |
| **Scenario 2 — deps skip probe** | `workflow_dispatch` only · **scenario = scenario2** | `p85-bridge-smoke-a-scenario2` · `p85-bridge-smoke-b-scenario2` | Both jobs **skip by design** · exit **0** · non-blocking |

**Scenario 2 conditions (intentional deps gap)**

- Each Scenario 2 job sets `GOV_CORE` to a **non-existent path** (`/tmp/p85-scenario2-force-missing-gov-core-<run_id>`), simulating a checkout where `gov_core_system` is unavailable.
- This hits the same deps gate as production skip logic (directory missing) without altering Scenario 1 job scripts.

**Scenario 2 expected Actions log**

1. `::notice title=Bridge Smoke Scenario 2::Scenario 2 skipped by design (gov_core_system directory missing — Smoke A/B deps gate probe)`
2. Smoke A: `::notice title=Bridge Smoke Skipped::bridge smoke skipped: gov_core_system venv not built`
3. Smoke B: `::notice title=Bridge Smoke B skipped::reason=gov_core_system directory missing`
4. Step **exit code 0** · workflow run **completed** · jobs remain **advisory** (`continue-on-error: true` · not required checks).

### How to run Scenario 2（human dispatch checklist）

> **勿選 `default`** — 選 `default` 會跑 Scenario 1 jobs，**不是** deps-skip 探針。  
> 詳細 ops 步驟亦見 `04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md` FRAME。

| Step | 動作 | 完成信號 |
|------|------|----------|
| **1** | GitHub → Repo → **Actions** → 左欄 **P85 Bridge Smoke CI (advisory)** → 右欄 **Run workflow** | UI 出現新 run |
| **2** | **Use workflow from**：**`main`** · **scenario** 下拉選 **`scenario2`**（**勿**選 `default`）→ **Run workflow** | dispatch 已提交 |
| **3** | 等待 workflow run **completed**（advisory · 不阻 merge） | 可複製 **run URL** + **run id** |
| **4** | 驗收 jobs：**僅** `p85-bridge-smoke-a-scenario2` · `p85-bridge-smoke-b-scenario2` · Scenario 1 jobs **不跑** · 各 job 含 design-skip + deps-gate notice · step **exit 0** | 兩 job **success** |
| **5** | 回填 ops-run B_REPORT `ga_run` / `job_results` · Progress 末尾 append（見 ops-run Progress 模板） | AC 證據齊 |

**可選 CLI**（同等權限）：`gh workflow run bridge-smoke.yml --ref main -f scenario=scenario2`

Skip in Scenario 2 is **expected behavior**, not a CI bug. Scenario 1 jobs do **not** run on a Scenario 2 dispatch (mutually exclusive inputs).

### Recorded GA-remote（EVD-GR-P85-S2 · 已回填 · 非本節「待跑」）

| 欄 | 值 |
|----|-----|
| **run_id** | `29157178993` |
| **run_url** | `https://github.com/g234134/workflow-connect/actions/runs/29157178993` |
| **scenario** | `scenario2` |
| **結果** | Scenario2 A/B **success** · Scenario1 skipped · advisory · **≠** required CI · **≠** Phase closure |
| **票** | `WH-P85-SMOKE-B-scenario2-ops-run-v1` · wave-H+2 `WH-P85-wave-H2-closure-scribe-v1` **done_with_gaps** |

> 重跑 Scenario2 仍用上方 checklist；**勿**把本表當「未跑」狀態。Evidence Schema 見 ops-run STATE。

### Scenario 1 / Scenario 2 (GA first-run · Progress templates)

Cross-ref **`04_Workflows/tickets/WH-P85-CI-LAND-v1_state.md`** B_REPORT §5 · **`WH-P85-SMOKE-B-scenario2-v1`** · **`W4-P85-S2-GA-RUNBOOK-v1`**（本節 checklist SSOT）。

| Scenario | Condition | Record in Progress |
|----------|-----------|-------------------|
| **Scenario 1 — happy path** | Both jobs not skipped · A **20/20** · B **7/7** · workflow run **completed** | Append run URL · job table (A 20/20 · B 7/7) · note **non-blocking / not required** |
| **Scenario 2 — skip or advisory fail** | Any job **skipped** (deps gate) or unittest **failed** but workflow still **completed** | Append run URL · per job: `skipped` + `skip_reason` **or** `failed` + `::warning` summary · note **does not block merge** |

> **Historical note**: older Progress entries (e.g. Wave-D P85-T2) may still say **10 tests** / Wave-H **14/14** / run-record era **17/17** for Smoke A; authoritative count is **20/20** (this runbook Smoke A · `EXPECTED_TEST_COUNT` in `tests/test_minimal_orchestration_bridge.py`, includes WH-P85-bridge-fixture-dom-port-v1). Do not rewrite historical Progress paragraphs—use this runbook as SSOT for current counts. CI job display names / echo / dispatch description in `bridge-smoke.yml` aligned to **20/20** by `WH-P85-bridge-ci-hardening-v2` (v1 had aligned to **17/17** only).

## Working directory (dark cabin cwd)

All commands below assume **current working directory = `gov_core_system` venv root** (path key `cabins.gov_core_system.venv_dir` in `Master_Map.json`; typically `01_Environments/python_venvs/gov_core_system`).

1. From repo root, activate the unified dark cabin venv (see `04_Workflows/Enter-Main.ps1` or your local venv activation for `gov_core_system`).
2. `cd` into the venv root so imports resolve as `core.*`, `tests.*`, and `app_api` do in CI.
3. Do **not** run these from repo root or `04_Workflows` — `ModuleNotFoundError` for `core` / `fastapi` is expected otherwise.

## Smoke A — Core bridge unittest (required)

Validates `run_minimal_orchestration_bridge()` without HTTP.

**Authoritative test count**: **20** (`tests/test_minimal_orchestration_bridge.py` → `EXPECTED_TEST_COUNT = 20`). Index entries (e.g. `WORKFLOW_INDEX.md` §1.4) should cite this runbook or that constant; do not hard-code a stale count elsewhere.

```powershell
# cwd: gov_core_system venv root
python -m unittest tests.test_minimal_orchestration_bridge -v
```

**Pass criteria**: **20/20** tests OK; response dict includes at least:

| Key | Expected |
|-----|----------|
| `ok` | `true` or `false` (business outcome; not HTTP status) |
| `schema_version` | `orchestration_bridge_v1` |
| `flow` | `minimal_intake_browser` |
| `intake` | Phase 7.5 gate output object |
| `phase6_5_pre_state` | Same object as `intake.phase6_5_pre_state` |
| `browser` | `{skipped, skip_reason, plan_id, validated, result}` |
| `stages` | Array of stage summaries |

**Suggested regression** (upstream stages only):

```powershell
python -m unittest tests.test_intake_decider tests.test_browser_runner -v
```

## Smoke B — HTTP API unittest (required when FastAPI deps available)

Uses `TestClient` against `POST /api/orchestration/bridge` (no separate server process).

```powershell
# cwd: gov_core_system venv root; requires fastapi in venv
python -m unittest tests.test_app_api_orchestration_bridge -v
```

**Pass criteria**: all tests OK; HTTP **200** for valid bridge runs; **422** for invalid `intake` shape.

## Smoke C — Live HTTP curl (optional; dev server)

Start API in a second shell (same cwd):

```powershell
python -m uvicorn app_api:app --host 127.0.0.1 --port 8000
```

Minimal accept-without-browser request:

```powershell
curl.exe -s -X POST "http://127.0.0.1:8000/api/orchestration/bridge" `
  -H "Content-Type: application/json" `
  -d "{\"intake\":{\"explicit_task_type\":\"chariot.factory\",\"description\":\"wave smoke\"}}"
```

**Expected HTTP**: `200`

**Expected top-level JSON keys** (same shape as `run_minimal_orchestration_bridge()`):

```json
{
  "ok": true,
  "message": "...",
  "schema_version": "orchestration_bridge_v1",
  "flow": "minimal_intake_browser",
  "intake": { "...": "..." },
  "phase6_5_pre_state": { "...": "..." },
  "browser": {
    "skipped": true,
    "skip_reason": "no_browser_section",
    "plan_id": null,
    "validated": null,
    "result": null
  },
  "stages": [ "..."]
}
```

Invalid `intake` (empty object) should return **422** with FastAPI `detail` array — not a bridge dict.

## Master_Map runners

| Runner key | Role |
|------------|------|
| `phase8_5_bridge_smoke_runbook` | This document |
| `bridge_smoke_unittest` | Core bridge test module |
| `bridge_smoke_http` | API bridge test module |

## Updating the bridge unittest count (checklist)

When adding or removing tests in `tests/test_minimal_orchestration_bridge.py`:

1. Update `EXPECTED_TEST_COUNT` in that module (must match `def test_*` method count).
2. Update **Authoritative test count** in this runbook (Smoke A).
3. Update `WORKFLOW_INDEX.md` §1.4「最近一次通過紀錄」or point readers to this runbook.
4. Append a one-line note to `04_Workflows/00_Agent_Work_Progress.md` (do not rewrite historical entries).

## Fixture DOM vs in-memory (WH-P85-bridge-fixture-dom-port-v1)

| Mode | How DOM is seeded | When to use | Fail behavior |
|------|-------------------|-------------|---------------|
| **In-memory inline** | `navigate.html_fixture` = HTML string in plan JSON | Unit tests / ad-hoc plans; default when no `dom_fixture_ref` | Parse errors → navigate fail (`NAVIGATION_FAILED`) |
| **File-backed fixture** | `dom_fixture_ref` on plan, navigate step, or `browser.dom_fixture_ref` (repo-/cabin-relative path) | Shared snapshots under `tests/fixtures/browser_dom/` | Missing / unsafe ref → fail-closed (`DOM_FIXTURE_MISSING` / `DOM_FIXTURE_INVALID_REF`); **no** empty-page fallback |
| **Empty navigate** | Neither `html_fixture` nor `dom_fixture_ref` | Placeholder page only | InMemory builds empty “Empty page at {url}” body |

**Priority**: step `dom_fixture_ref` → plan `dom_fixture_ref` → bridge `browser.dom_fixture_ref` → inline `html_fixture`.

**Index** (P85-T1 smoke fixtures + DOM snapshots):

| Path | Role |
|------|------|
| `tests/fixtures/orchestration_bridge/*.json` | Plan JSON for bridge smoke (inline HTML still valid) |
| `tests/fixtures/browser_dom/happy_login.html` | File-backed happy DOM |
| `tests/fixtures/browser_dom/negative_sparse.html` | File-backed sparse / negative DOM |

`run_plan` / bridge result **dict keys unchanged** (`ok`, `plan_id`, `steps_total`, `steps_ok`, `failed_step_index`, `steps`, `context`, …). Not Playwright.

## Non-goals

- No Playwright or external browser dependencies.
- No changes to bridge business logic beyond optional `dom_fixture_ref` (see P85-T1 / Phase 8.6 specs).
- Outbox PG persistence is off in unit tests (`GOV_CORE_ORCHESTRATION_BRIDGE_OUTBOX_PG_ENABLED=false`).
- Smoke 測試執行期間可能寫入 outbox jsonl 側車（in-memory stub 可接受副作用；見 WD-P85-T1 Orchestrator 裁決）。
- **Opt-in run record**（`GOV_BRIDGE_RUN_RECORD_ENABLED` · default **0**）：啟用時 append `outbox/orchestration_bridge/runs.jsonl`（`schema_id=orchestration_bridge_run_v1`）· fail-open · **≠** Phase 8.7e outbox PG／always-on mirror（`WH-P85-bridge-run-record-jsonl-v1`）；**亦 ≠** DOM file-backed fixture port（本節）。
