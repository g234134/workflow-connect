# Testing — Phase 6 (P6) agent workflow & CI

> **Scope**: Core agent workflows at repo root + optional `gov_core_system` dark tier.  
> **INT gate SSOT**: `docs/phase6-int-regression-gate-contract-v1.md`（过 gate 命令、Tier 表、CI 矩阵、失败诊断）。  
> **INT verification report**: `docs/phase6-int-regression-verification-report-v1.md`（Tier-A executed JSON · verdict · matrix `TS-INT-TIER-A`）。  
> **INT CI design (design-only)**: `docs/ci-design-p6-int-gate-v1.md`（PR optional / nightly / release 三轨 · **非** live CI）。  
> **Implementation appendix**: `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md`（逐测试不变量）。  
> **Not in scope**: Legacy vendored trees under `02_Agents_Core/repos/`.

---

## 1. Test pyramid

| Layer | What | Where | When |
|-------|------|-------|------|
| **Unit** | Pure logic, mocks, contract `dict` shapes | `tests/` (root), `gov_core_system/tests/` | Every PR |
| **Smoke** | 3–5 critical workflows, no live PG/LLM | `_core_agent_smoke.py` tiers | PR (`PR`) + manual (`DARK`/`ALL`) |
| **Integration (INT gate)** | Wave 6/7/8 装配 + M2 契约 | `_wave7_regression_gate.py --tier A` | **Local mandatory**（装配变更）；release 推荐；**非** PR CI |
| **Regression** | Wave 6/7/8 module bundles（Tier-A/B/ALL） | `core/wave7_regression_gate.py` | Pre-release / manual |
| **Eval / shadow** | P+ `eval_ci_check`, shadow spool | `.github/workflows/eval-gate-ci.yml` | PR + nightly schedule |

> **Gate 分类 SSOT（Phase 3.5）**：mandatory / optional / shadow-only 三类及主链影响见 `docs/phase3-5-cost-model-governance-contract-v1.md` §2；本 pyramid **不重写**。

```text
                    ┌─────────────────┐
                    │ Eval / shadow   │  nightly + PR (eval-gate-ci)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ INT Tier-A gate  │  local mandatory · see phase6 contract
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
| `python 04_Workflows/_wave7_regression_gate.py --tier A` | **INT gate pass**（authoritative）— Wave 6/7/8 Tier-A；见 `docs/phase6-int-regression-gate-contract-v1.md` §2 |
| `python 04_Workflows/_wave7_regression_gate.py --tier B` \| `ALL` | Tier-B / full integration（optional pre-release） |
| `python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v` | Phase 6 INT gate contract 结构校验 |
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

## 5. PR Smoke Tier (W2-T1 · Phase 6 收口)

> **一句話邊界**：PR smoke 驗證 **7 個 ROOT agent workflow 模組**；**不**代表發版就緒——Release 前仍須 [W2-T4](#51-pr-smoke-vs-release-tier-a-w2-t4) Tier-A 與可選 DARK／ALL。

### 目的

- **Fast PR gate**（目標 &lt; ~2 min on GitHub-hosted runners）：每次 PR 自動跑 H-line、subagent routing、HQ routing、K-2、eval-gate 子集，防止企業化補強層回歸。
- **與 `eval-gate-ci.yml` 互補**：eval 側重 P+ `eval_ci_check` fixture + 更廣 eval unittest；本 tier 側重 agent workflow 契約子集（見下方模組表）。
- **不依賴暗部 venv**：PR tier 僅在 repo 根執行；不 install `requirements-ci-minimal.txt`、不跑 `DARK` / `DARK_FULL`。

### 執行方式

| 環境 | 命令 |
|------|------|
| **本地** | `python 04_Workflows/_core_agent_smoke.py --tier PR` |
| **本地（verbose）** | `python 04_Workflows/_core_agent_smoke.py --tier PR -v` |
| **本地（可讀 JSON）** | `python 04_Workflows/_core_agent_smoke.py --tier PR --pretty` |
| **CI** | `.github/workflows/core-agent-smoke.yml` → job **`Agent workflow smoke (PR tier)`** (`agent-smoke-pr`) |

**模組來源**：`core/agent_workflow_smoke.py` → `TIER_ROOT_MODULES`（`PR` ≡ `ROOT`）。

### 覆蓋模組

| 模組 | 領域 | 權威檔 | 備註 |
|------|------|--------|------|
| `tests.test_context_entry` | H-line context entry | `core/context_entry.py` | **AC 必達** |
| `tests.test_context_subagent_routing` | Subagent routing (C-1) | `subagents/context_routing.py` | monitoring → `monitoring_subagent` |
| `tests.test_monitoring_executor` | O-2 monitoring sidecar | `subagents/monitoring_executor.py` | adapter mock / stub fallback |
| `tests.test_langgraph_flow_k2` | K-2 routing | `core/langgraph_flow_k2.py` | 無 compiled graph e2e |
| `tests.test_hq_task_routing_smoke` | HQ task routing | `02_Agents_Core/task_routing.py` | **AC 必達** |
| `tests.test_eval_gate` | P+ eval gate | `observability/eval_ci_check.py` 等 | **AC 必達** |
| `tests.test_eval_ci_check` | P+ eval CI check | `observability/eval_ci_check.py` | 與 `eval-gate-ci.yml` 部分重疊 |

Happy / edge 代表測試見 [§2 Core workflows under smoke](#2-core-workflows-under-smoke-5)。

### Exit codes

| exit | 語意 | JSON |
|------|------|------|
| `0` | 全綠 | `"ok": true` |
| `1` | 測試失敗 | `"ok": false`，stderr 含 `test_id=…` hint |
| `2` | tier／Master_Map／載入錯誤 | `"message"` 說明原因 |

### 5.1 PR smoke vs Release Tier-A (W2-T4)

| 層級 | 票號 | 命令 | 觸發 | 範圍 |
|------|------|------|------|------|
| **PR fast** | **W2-T1** | `python 04_Workflows/_core_agent_smoke.py --tier PR` | 每 PR（GHA required） | ROOT agent smoke（7 模組）；無 PG/LLM；無 Wave7 Tier-A |
| **P+ eval** | existing | `eval-gate-ci.yml` | 每 PR | eval unittest + `eval_ci_check` fixture |
| **Pre-release INT** | **WA-T6** | `python 04_Workflows/_wave7_regression_gate.py --tier A` | Release checklist / manual（装配变更 **mandatory**） | INT Tier-A 14 模块；SSOT → `docs/phase6-int-regression-gate-contract-v1.md` §2 |
| **Dark optional** | — | `--tier DARK` / `workflow_dispatch` | 手動 / pre-release | gov_core 子集；**非** PR 預設 |

### Excluded / Not covered by PR smoke

| 類別 | 不在 PR smoke 的項目 | 替代 gate／備註 |
|------|----------------------|-----------------|
| **全量 unit** | `python -m unittest discover -s tests` | 本地／專票；PR 僅 ROOT 7 模組 |
| **Dark tier** | `--tier DARK`、`DARK_FULL`、gov_core 135+ 全矩陣 | `workflow_dispatch` 或本地 venv |
| **INT Tier-A gate** | `_wave7_regression_gate.py --tier A` | **WA-T6** contract §2；PR CI **未**接入 |
| **Live I/O** | PostgreSQL、Qdrant、OpenAI 實連 | mock／fixture only |
| **Ask e2e** | `tests.test_ask_selector_and_answer` | 需 gov_core `langgraph`；eval-gate-ci 部分覆蓋 |
| **Keys／runbook** | `_smoke_test_keys.py`、Telegram listener | 手動 runbook；禁 CI 印 secret |
| **Eval nightly** | prod shadow spool、`eval-shadow-nightly` cron | `eval-gate-ci.yml` schedule job |
| **workflow_v2** | `gov-gate-metrics.yml` 路徑 gate | 觸 `workflow_v2/**` 時另跑 |
| **純文檔 PR** | 僅 `**/*.md` 等 paths-ignore 變更 | workflow 不觸發（by design） |

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
3. Job 產出 `smoke_ci_summary.json`（含 `workflow_name`、`failed_modules[]`、`duration_ms`）；失敗時 artifact `core-agent-smoke-pr-<run_id>` 保留 14 天  

**CI 失敗摘要 schema（`smoke_ci_summary.json`）**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `workflow_name` | string | 固定 `"Core agent smoke"` |
| `job_name` | string | `"agent-smoke-pr"` |
| `tier` | string | `"PR"` |
| `ok` | boolean | smoke CLI exit 0 且 `"ok": true` |
| `duration_ms` | integer | smoke step 牆鐘時間（ms） |
| `failed_modules` | array | 由 `failed_tests[].test_id` 推導；成功時 `[]` |
| `smoke_result` | object | CLI stdout 完整 dict |

---

## 7. Adding tests

1. Prefer **one happy + one edge** per new workflow; mock external I/O.  
2. Root tests: add under `tests/test_*.py`, register in `core/agent_workflow_smoke.py` → `TIER_ROOT_MODULES` if PR-critical.  
3. Dark tests: under `gov_core_system/tests/`, register in `TIER_DARK_MODULES`.  
4. Do not widen PR tier without review — keep PR job &lt; ~2 min on GitHub-hosted runners.

---

## 8. Related docs

- `docs/phase3-5-cost-model-governance-contract-v1.md` — **Phase 3.5** gate 分类 SSOT（mandatory / optional / shadow-only；PR vs nightly）  
- `docs/WAVE_A_EXECUTION_PLAN.md` — A-P0-4 CI matrix  
- `AGENTS.md` — Monitoring subagent / graph governance  
- `docs/phase6-int-regression-gate-contract-v1.md` — **INT gate SSOT**（WA-T6）  
- `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md` — Tier 逐测试不变量（implementation 附录）  
- `.github/workflows/eval-gate-ci.yml` — P+ eval + shadow spool smoke

---

## 9. Multi-Chat Ticket State 驗收

> **SSOT**：`04_Workflows/tickets/README.md` · **角色邊界**：`.cursor/rules/multi_chat_roles.mdc`  
> **參照子票**：`04_Workflows/tickets/W2-REF-001_state.md`（母票 `W2-T2`）

制度票無 unittest；驗收以 **state 檔結構 + 四角色寫入權限** 為準。

### 9.1 四角色區塊權限

| 區塊 | 維護者 | Implementer | Reviewer | Scribe | Orchestrator |
|------|--------|-------------|----------|--------|--------------|
| FRAME | Orchestrator | 讀 | 讀 | 讀 | **寫** |
| STATE | Orchestrator | 讀 | 讀 | 讀 | **寫** |
| B_REPORT | Implementer | **寫** | 讀 | 讀 | 讀 |
| C_REPORT | Reviewer | 讀 | **寫** | 讀 | 讀 |
| D_REPORT | Scribe | 讀 | 讀 | **寫** | 讀 |

**警示**：各角色 **必須 Write state 檔**；不可只在 chat 輸出 REPORT 全文代替寫檔（備援流程見 `tickets/README.md`）。

### 9.2 Loop-back 驗收表

| C_REPORT 結論 | 下一步 | B_REPORT 要求 |
|---------------|--------|---------------|
| `accepted` / `accepted_with_gaps` | → Scribe (D) → Orchestrator 關票 | 保留歷史 |
| `needs_changes` | **回到 Implementer (B)** | **追加** B_REPORT 段落，**不刪**舊段 |
| `rejected` | Orchestrator 介入 | 記錄原因於 C_REPORT |

### 9.3 VerificationCommands（目視）

1. 開啟 `<ticket_id>_state.md`：FRAME / STATE / B_REPORT / C_REPORT / D_REPORT 區塊存在。
2. Loop-back 後：B_REPORT 含 **兩段以上**施工歷史（例如 Run 1 + Run 2），舊段仍在。
3. 子票 `overall_status` 曾至 `done` 或母票 B_REPORT 引述等價證據。
4. Reviewer spot-check：**無 code diff**（僅 C_REPORT 更新）；Implementer diff 限 FRAME.AllowedPaths。
5. Cross-ref：`tickets/README.md` walkthrough 與 `multi_chat_roles.mdc` 角色小節一致。

