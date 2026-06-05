# Testing — Phase 6 (P6) agent workflow & CI

> **Scope**: Core agent workflows at repo root + optional `gov_core_system` dark tier.  
> **Not in scope**: Legacy vendored trees under `02_Agents_Core/repos/`, full Wave 6/7 regression (see `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md`).

---

## 1. Test pyramid

| Layer | What | Where | When |
|-------|------|-------|------|
| **Unit** | Pure logic, mocks, contract `dict` shapes | `tests/` (root), `gov_core_system/tests/` | Every PR |
| **Smoke** | 3–5 critical workflows, no live PG/LLM | `_core_agent_smoke.py` tiers | PR (`PR`) + manual (`DARK`/`ALL`) |
| **Integration** | Orchestrator job lifecycle, envelope QA | `_wave7_regression_gate.py` Tier-A/B | Local / release gate |
| **Regression** | Wave 6/7/8 module bundles | `core/wave7_regression_gate.py` | Pre-merge / nightly (local) |
| **Eval / shadow** | P+ `eval_ci_check`, shadow spool | `.github/workflows/eval-gate-ci.yml` | PR + nightly schedule |

```text
                    ┌─────────────────┐
                    │ Eval / shadow   │  nightly + PR (eval-gate-ci)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Wave7 regression │  local / manual (Tier A/B)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Agent smoke ALL  │  workflow_dispatch
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ PR smoke (ROOT + HQ tests)  │  core-agent-smoke.yml
              └──────────────┬──────────────┘
                             │
                    ┌────────▼────────┐
                    │ Unit (per module)│  pytest / unittest
                    └─────────────────┘
```

---

## 2. Core workflows under smoke (5)

| # | Workflow | Authority | Smoke module(s) | Happy path | Edge case(s) |
|---|----------|-----------|-----------------|------------|--------------|
| 1 | **H-line context entry** | `core/context_entry.py` | `tests.test_context_entry` | `test_minimal_task_input_fills_ids_and_layers` | `test_invalid_task_input_returns_contract_error` |
| 2 | **Subagent routing (C-1)** | `subagents/context_routing.py` | `tests.test_context_subagent_routing` | monitoring → `monitoring_subagent` | general query → default; selector not overridden |
| 3 | **HQ task routing** | `02_Agents_Core/task_routing.py` | `tests.test_hq_task_routing_smoke` | `hq.governance` assignable | `dark.infra` blocked; unknown type |
| 4 | **K-2 routing** | `core/langgraph_flow_k2.py` | `tests.test_langgraph_flow_k2` | planner handoff route | executor timeout retry |
| 5 | **Tool call chain** | `core/tool_executor.py`, bridge | `tests.test_minimal_orchestration_bridge_tool_flow` + tool executor contract tests (**DARK**) | whitelist bridge flow | empty tools; invalid `decision_id` |

**Also in PR tier (eval + monitoring sidecar):**

- **P+ eval gate** — `tests.test_eval_gate`, `tests.test_eval_ci_check` (overlaps `eval-gate-ci.yml`).
- **O-2 monitoring executor** — `tests.test_monitoring_executor` (adapter mock / stub fallback).

**Dark tier (CI `workflow_dispatch` or local venv):**

- Subset runs in isolated subprocess (avoids repo `tests/` package clash).  
- **Monitoring HTTP** — `test_healthz_lists_monitoring_routes`, schema example validation.  
- Full modules: `--tier DARK_FULL` (requires `gov_core_system` venv + `requirements-ci-minimal.txt` or full venv).

---

## 3. Unified entry points

| Command | Purpose |
|---------|---------|
| `python 04_Workflows/_core_agent_smoke.py --tier PR` | **Default PR gate** — repo-root agent smoke |
| `python 04_Workflows/_core_agent_smoke.py --tier DARK` | Gov-core **subset** (bridge + tool contract + monitoring shape) |
| `python 04_Workflows/_core_agent_smoke.py --tier DARK_FULL` | Full dark modules (local venv recommended) |
| `python 04_Workflows/_core_agent_smoke.py --tier ALL` | ROOT + HQ + DARK subset |
| `python 04_Workflows/_wave7_regression_gate.py --tier A` | Wave 6/7 integration regression |
| `python -m unittest discover -s tests -p "test_*.py"` | Full root test tree (slower) |

Runner index: `04_Workflows/Master_Map.json` → `runners.core_agent_smoke`.

---

## 4. Run tests locally

### 4.1 PR-fast (no venv)

From repo root:

```powershell
python 04_Workflows/_core_agent_smoke.py --tier PR -v
python -m unittest tests.test_hq_task_routing_smoke -v
```

### 4.2 Dark tier (gov_core_system)

Activate `gov_core_system` venv, or install CI-minimal deps:

```powershell
pip install -r requirements-ci-minimal.txt
python 04_Workflows/_core_agent_smoke.py --tier DARK -v
```

### 4.3 Eval gate (existing)

```powershell
python -m unittest tests.test_eval_gate tests.test_eval_ci_check -v
python -m observability.eval_ci_check tests/fixtures/eval/ibridge_records.jsonl --limit 50
```

### 4.4 Keys / runbook smoke (manual, not CI)

- `python 04_Workflows/_smoke_test_keys.py` — never prints secrets; local only.
- Gov Core / RAG: `04_Workflows/runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md`.

---

## 5. Smoke test scope (PR tier `PR`)

**Included**

- Context entry contract + deny gates  
- Subagent routing vs RAG selector isolation  
- HQ `route_task` explicit / blocked / default  
- K-2 routing helpers (no compiled graph e2e without `langgraph`)  
- Eval gate + eval CI check modules  
- Monitoring executor (mocked service adapter)

**Excluded (by design)**

- Live PostgreSQL / Qdrant / OpenAI  
- `tests.test_ask_selector_and_answer` (requires `gov_core_system` `core.langgraph_flow`)  
- Full Wave 7 Tier-A/B regression (separate gate)  
- Telegram listener / `.env` key materialization

---

## 6. CI acceptance

| Workflow | Trigger | Required for merge |
|----------|---------|-------------------|
| `core-agent-smoke.yml` → **agent-smoke-pr** | push / PR | **Yes** — `PR` tier exit 0 |
| `eval-gate-ci.yml` → **eval-gate** | push / PR | **Yes** (existing P+ gate) |
| `core-agent-smoke.yml` → **agent-smoke-dark** | `workflow_dispatch` only | Optional / pre-release |
| `gov-gate-metrics.yml` | `workflow_v2/**` PR paths | When touching workflow_v2 |

**Pass criteria (agent-smoke-pr)**

1. `python 04_Workflows/_core_agent_smoke.py --tier PR` → JSON `"ok": true`  
2. `tests_run` ≥ 1, `failed` = 0, `errors` = 0  
3. HQ routing unittest step green  

---

## 7. Adding tests

1. Prefer **one happy + one edge** per new workflow; mock external I/O.  
2. Root tests: add under `tests/test_*.py`, register in `core/agent_workflow_smoke.py` → `TIER_ROOT_MODULES` if PR-critical.  
3. Dark tests: under `gov_core_system/tests/`, register in `TIER_DARK_MODULES`.  
4. Do not widen PR tier without review — keep PR job &lt; ~2 min on GitHub-hosted runners.

---

## 8. Related docs

- `docs/WAVE_A_EXECUTION_PLAN.md` — A-P0-4 CI matrix  
- `AGENTS.md` — Monitoring subagent / graph governance  
- `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md` — orchestrator integration  
- `.github/workflows/eval-gate-ci.yml` — P+ eval + shadow spool smoke
