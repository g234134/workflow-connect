# TICKET STATE · P8-T4-worker-api-batch-v1

> handoff 摘要檔。補齊 P8→100 缺口：**真 Worker API** 接 batch orchestrator。

---

## FRAME

**Goal:**
- 以真實可呼叫 HTTP Worker API 取代 batch 僅 mock 路徑，對齊既有 batch 契約（ExecutionResult／collector／reporter）。

**Scope:**
- `04_Workflows/_batch_orchestrator/worker_api.py`（`POST /api/batch/worker/run`）
- `04_Workflows/_batch_orchestrator/runner_worker_api.py`
- CLI `--mode worker_api` + `serve-worker`
- tests + docs

**NonScope:**
- 不 spawn Cursor Multi-Chat；不自動寫 `*_state.md`／Progress
- 不改暗部 `core`／app_api bridge
- 不宣稱遠端 production fleet

**AllowedPaths:**
- `04_Workflows/_batch_orchestrator/**`
- `tests/test_batch_worker_api.py`
- `docs/batch-worker-api-v1.md`
- `04_Workflows/tickets/P8-T4-worker-api-batch-v1_state.md`

**BlockedPaths:**
- `core/**` · 暗部 · `.env` · venv · checkpoint

**AcceptanceCriteria:**
1. Worker HTTP 可起、可 POST，回傳穩定 dict（`ok`／`message`／`status`）
2. CLI `--mode worker_api` E2E 綠；`writes_ticket_state=false`
3. 缺 URL fail-close
4. `python -m unittest tests.test_batch_worker_api -v` 全綠

---

## STATE

- **overall_status:** accepted
- **current_owner:** scribe
- **next_action:** W-PROG uplift
- **last_updated:** 2026-07-13 · same_chat
- **status_by_role:**
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `04_Workflows/_batch_orchestrator/worker_api.py` (new)
  - `04_Workflows/_batch_orchestrator/runner_worker_api.py` (new)
  - `04_Workflows/_batch_orchestrator/cli.py` (mode worker_api + serve-worker)
  - `04_Workflows/_batch_orchestrator/__init__.py`
  - `tests/test_batch_worker_api.py` (new)
  - `docs/batch-worker-api-v1.md` (new)
- verification: |
    ```powershell
    $env:PYTHONPATH = "04_Workflows"
    python -m unittest tests.test_batch_worker_api -v
    # → 6 tests OK
    ```
- deferred_items: Cursor Multi-Chat spawn；遠端 worker fleet
- **proposed_delta**：P8 +4
- **non_claims**：≠ Multi-Chat · ≠ auto state write · ≠ Phase closure alone

---

## C_REPORT

- conclusion: accepted
- checks_summary: AC-1～4 通過；真實 HTTP（ThreadingHTTPServer）+ CLI worker_api 綠；mock 回歸未破
- risk_level: low
