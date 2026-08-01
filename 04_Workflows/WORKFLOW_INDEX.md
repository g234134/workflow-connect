# WORKFLOW_INDEX — Workflow & Smoke Test Map（v0.1）

本文件是 Gov Core / HQ 的「工作流地圖首頁」。
目標：讓人類與 Agent 進場時，能先知道有哪些主要工作流、對應的 runbook 與 smoke test 戰史。

---

## 0. 文件定位

- 位置：`04_Workflows/WORKFLOW_INDEX.md`
- 角色：工作流與 smoke test 索引首頁。
- **產品主線敘事**：This repo's core product path is **tabular data cleaning and delivery automation**; governance / CI / GA lines are **supporting rails**, not the primary product outcome. 權威 SSOT：`docs/TABULAR_MVP_SSOT.md` · supporting/deferred 对照：`docs/TABULAR_MVP_NARRATIVE_MAPPING.md`。
- 關係：
  - 結構層：`HARNESS_CONSTITUTION.md`（國家架構與禁區）
  - 行為層：`ENGINEERING_CONTRACT.md`（四大流派與 12-rule）
  - 實例層：`INSTANCE_ANCHOR_TANG.md`（路徑、runner、禁區清單）
  - 操作層：各 workflow runbook + smoke test 戰報（本文件即為入口）
- **接戰讀法（v1.1）**：**禁止**預設通讀本檔全文。先跑 `python 04_Workflows/_boot_context.py --text "<指令>" --pretty`，再只讀 `workflow_index_hint` 所列 **§1.x** 一節。對照表：`docs/GOVERNANCE_ONBOARDING_v1.md`。

---

## 1. 已定義的核心工作流（v0.1）

### 1.1 Gov Core V1 最小 Smoke Test（Infra → Data → Governance）

- Runbook：
  - `04_Workflows/runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md`
- 簡述：
  - 驗證「Gov Core V1 底盤是否活著」：
    - Infra health → 單檔 ingest（AGENTS.md）→ Governance ingest_verify → master_status。
- 主要入口與檔案：
  - `core/infra_health.py`
  - `core/data_pipeline.py`
  - `core/orchestrator.py`
  - `Departments/04_Infrastructure/agents/data_pipeline_agent.py`
  - `Departments/04_Infrastructure/agents/orchestrator_agent.py`
- Smoke Test 標準：
  - 見：`00_Agent_Work_Conditions.md` 中「Gov Core V1 最小 Smoke Test」條目。
- 最近一次通過紀錄：
  - 見：`00_Agent_Work_Progress.md` 中 `2026-05-17 — Gov Core V1 最小 Smoke Test` 條目。
  - 另有：`04_Workflows/project_status/master_status.md` 之 `## 2026-05-17 — ingest_verify 里程碑（AGENTS.md）`。

---

### 1.2 RAG_Smoke_Test（Gov Core V1 / document_chunks / AGENTS.md）

- Runbook：
  - `04_Workflows/runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md`
- 簡述：
  - 在 `AGENTS.md` 已被 ingest 至 `document_chunks` 的前提下，驗證：
    - 能對該 collection 發出 RAG 查詢；
    - 能檢索到至少一筆 AGENTS 相關 chunk；
    - answer 模式可以產出 grounded 回覆。
- 主要入口與檔案：
  - `core/rag_backend.py`
  - `Departments/04_Infrastructure/agents/rag_query_agent.py`
- Smoke Test 標準：
  - 見：`00_Agent_Work_Conditions.md` 中「Gov Core V1 — RAG Smoke Test 標準（v0.1）」條目。
- 最近一次通過紀錄：
  - 見：`00_Agent_Work_Progress.md` 中 `2026-05-17 — RAG_Smoke_Test（Gov Core V1）` 條目。

---

### 1.3 Phase 5 Probe — `task_runs` / `seed_pg` 鎖排查與 shortest-path 驗收

- Runbook：
  - `01_Environments/python_venvs/gov_core_system/Departments/05_Data_Vault/README.md`
- 簡述：
  - `05_Data_Vault/README.md`：Phase 5 probe、`task_runs` / `seed_pg` 鎖排查與 shortest-path 驗收 Runbook。
- 主要入口與檔案：
  - `Departments/05_Data_Vault/phase5_live_pg_soak.py`（`--probe`；工作目錄：`gov_core_system` 根；API `http://127.0.0.1:8000`）
  - `output/phase5_probe_report.json`（probe 報告）
- 觸發時機：
  - probe 卡在 `seed_pg`；PG `lock wait` / `idle in transaction` 涉及 `task_runs`；或 `failed_stage` 為 `seed_pg_from_asks` / `monitoring`。
- 驗收標準：
  - 終端 JSON：`ok: true`、`report_kind: probe_complete`、`failed_stage: null`、`message: probe shortest path ok`（細節見 README §4–§5）。

---

### 1.4 Phase 8.6 — Minimal Intake Browser Bridge（6.5 + 7.5 + 8.5 + 8.6 / 8.6a）

- **Flow key**：`minimal_intake_browser`（與 `run_minimal_orchestration_bridge()` 回應欄位 `flow` 一致）
- Runbook：
  - **`docs/phase8_5-bridge-smoke-runbook-v1.md`** — 一鍵 smoke（暗部 cwd、unittest、可選 curl；Master_Map runners：`bridge_smoke_unittest` / `bridge_smoke_http`）
  - `04_Workflows/PHASE8_6_MINIMAL_ORCHESTRATION_BRIDGE_MVP_v0.1.md`
  - `04_Workflows/PHASE8_6A_MINIMAL_BRIDGE_API_ENDPOINT_MVP_v0.1.md`（HTTP：`POST /api/orchestration/bridge`）
- 簡述：
  - Minimal orchestration：intake（Phase 7.5）→ `phase6_5_pre_state`（Phase 6.5）→ optional DOM browser plan（Phase 8.5）；對外 **`POST /api/orchestration/bridge`** 轉交 `run_minimal_orchestration_bridge()`，回傳結構化 bridge `dict`（`schema_version: orchestration_bridge_v1`）。
- 主要入口與檔案：
  - `01_Environments/python_venvs/gov_core_system/core/minimal_orchestration_bridge.py`（`run_minimal_orchestration_bridge()`）
  - `01_Environments/python_venvs/gov_core_system/app_api.py`（`POST /api/orchestration/bridge`；本輪索引僅登錄，不改實作）
  - `01_Environments/python_venvs/gov_core_system/core/intake_decider.py`（Phase 7.5 `parse_and_decide`）
  - `01_Environments/python_venvs/gov_core_system/core/browser_runner.py`（Phase 8.5 `validate_plan` / `run_plan`）
  - `01_Environments/python_venvs/gov_core_system/shared/schemas/orchestration_bridge_v1.json`
- Smoke Test / 驗收（**首選** `docs/phase8_5-bridge-smoke-runbook-v1.md`；工作目錄：`gov_core_system` 根）：
  - Smoke A：`python -m unittest tests.test_minimal_orchestration_bridge -v` — **20/20**（權威計數見 runbook · `EXPECTED_TEST_COUNT`）
  - Smoke B：`python -m unittest tests.test_app_api_orchestration_bridge -v` — **7/7**
  - Smoke C：live curl（**manual only** · runbook §0.3）
  - 建議回歸：`python -m unittest tests.test_intake_decider tests.test_browser_runner -v`
- CI advisory（non-blocking · 非 branch protection required）— **SSOT** `docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3 · `.github/workflows/bridge-smoke.yml`：
  - Actions UI：**P85 Bridge Smoke CI (advisory)**
  - Job **`p85-bridge-smoke-a`** · display **P85 Bridge Smoke A (advisory · 20/20)** · Smoke A **20/20**
  - Job **`p85-bridge-smoke-b`** · display **P85 Bridge Smoke B (advisory · HTTP API)** · Smoke B **7/7**
  - GA 模板：**Scenario 1**（happy path · 20/20 + 7/7）· **Scenario 2**（deps-skip probe · `scenario=scenario2`）→ runbook §0.3 checklist · 票 `W4-P85-S2-GA-RUNBOOK-v1`／`WH-P85-CI-LAND-v1` B_REPORT §5
- 最近一次通過紀錄：
  - **2026-07-11 · Scenario2 GA-remote（EVD-GR-P85-S2）**：**recorded** · `workflow_dispatch` · `scenario=scenario2` · run_id=`29157178993` · Scenario2 A/B **success** · Scenario1 skipped · wave-H+2 **done_with_gaps** · Evidence Schema 見 `WH-P85-SMOKE-B-scenario2-ops-run-v1` · **advisory · ≠ required CI · ≠ Phase closure · ≠ prod browser** · 票 `WH-P85-SMOKE-B-scenario2-ops-run-v1`／`WH-P85-wave-H2-closure-scribe-v1`／`W4-P85-S2-GA-RUNBOOK-v1`。
  - **2026-06-24 · Wave-H+1 · P85 Bridge Smoke CI (advisory)**：**`bridge-smoke.yml` 已 landing `origin/main`** · Actions UI 可見 P85 Bridge Smoke A/B (advisory)；本機 smoke 當時 **14/14 · 7/7**（其後 fixture-dom／hardening 升至 **20/20** · 見 runbook）；詳見 `00_Agent_Work_Progress.md` 2026-06-24 增量與 `master_status.md` 2026-06-24 段。
  - **2026-06-20 · Wave-E · WD-P85-T3**：bridge unittest 計數收口 — 當時 **14/14 OK**（現行權威 **20/20** · 見 runbook）。
  - 歷史 Progress（Wave-D 等）若仍寫 **10／14 tests**，以 runbook §0.3 歷史註腳為準（**20/20** supersede · 不重寫舊段）。
- **non-stub 能力水位（wave-H+2 · 一句）**：遠端 GA 已覆蓋 Scenario2 deps-skip 探測；**仍** in-memory stub bridge · **無** Smoke C CI · optional hardening／第二負例另票 · **≠** prod browser。
- **Phase 8 Operator Backlog 邊界（W3-P8-BRG）**：bridge 為 **optional advisory 側線**（in-memory stub · ≠ Phase 8 release gate）· **≠** Operator Backlog／MP-SMOKE 前置 → 見 `docs/phase-8-operator-backlog-v1.md` §Bridge advisory · plan 脚注 `04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md` §7。
- **Wave 4 證據 SSOT（2026-07-13）**：`docs/wave4-p85-p9-evidence-ssot-v1.md` — P8.5 Scenario2 + P9 sandbox CI 兩線 run URL／non-claims 對照 · `evidence_status=complete` · 票 `W4-P85-P9-EVIDENCE-SSOT-v1` · **advisory · ≠ required · ≠ Phase closure · ≠ Phase% 寫入**。

---

### 1.45 P7 · Notification · Advisory CI vs gate（Wave 2 SSOT）

> **SSOT 正文**：`docs/P7_ADVISORY_CI_INDEX.md` · 施工票 `W2-P7-advisory-ci-ssot-index-v1_state.md` · P8/P8.9 advisory **分線** Wave 3 `W3-P8-ADV-advisory-ci-ssot-index-v1`。

**Non-claims（摘要）**：indexed GitHub workflow **均 advisory · non-gate · non-prod** · **≠** Round-2 execute GO · **≠** staging S1–S4 物证 · **≠** required CI（G8 仍 `open`）。

| 路徑 | ci_class | 用途 | 觸發 | 結果類型 | 標籤 |
|------|----------|------|------|----------|------|
| `.github/workflows/p7-notification-smoke.yml` · job `p7-notification-smoke` | **advisory CI** | 全鏈 notify unittest + `127.0.0.1:8080` mock | PR path filter · daily cron · `workflow_dispatch` | unittest exit · `::warning` · log artifact | **advisory · non-gate · non-prod · sandbox-only** |
| `WH-P7-PROD-staging-smoke-runbook-v1_state.md` B_REPORT | **human-env-only** | staging S1–S4 手動 smoke | ops 手動 env flip | 人工 log / execute 物证 | **non-CI · non-gate · ≠ advisory CI 替代** |
| `tests.test_orchestrator_dispatch_full_smoke_v1` 等三模組 | **local_smoke** | 同上鏈本機回歸 | 本機 `python -m unittest …` | pass/fail 計數 | **≠ merge gate · ≠ staging POST** |
| bootstrap **G8** · `WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md` | **governance_template** | future required CI 升格證據 | 尚書省批文 + Wave-P7-6 | **`open`** · default advisory | **非 workflow · 未升格** |

- **CI 形狀**：`continue-on-error: true` · localhost mock · 預設無 retry/HMAC prod env · **非 branch protection required check**。
- **Round-2**：`WH-P7-NOTIF-staging-integration-execute-v2` 仍 **`blocked`**；advisory CI 綠 **不等同** execute GO。
- **驗證**：`rg "P7 advisory" docs/P7_ADVISORY_CI_INDEX.md` · `rg "continue-on-error" .github/workflows/p7-*.yml`
- **P7 resume-loop G-1–G-5（Wave 2 · spec-only）**：`docs/p7-resume-loop-g1-g5-spec-v1.md` · YAML `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml` · matrix §9 Observability · `scripts/verify_g_matrix.py` · 票 `W2-P7-matrix-G1-G5-resume-loop-v1`。gate trace SSOT → `docs/p75-intake-gate-control-plane-trace-v1.md`（**分表** · **≠** G-* runtime unittest 已落地）。

---

### 1.46 P8 / P8.9 · Advisory CI vs gate（Wave 3 SSOT · W3-P8-ADV）

> **SSOT 正文**：`docs/P8_P89_ADVISORY_CI_INDEX.md` · 施工票 `W3-P8-ADV-advisory-ci-ssot-index-v1_state.md` · **分線** P7 → §1.45 / `docs/P7_ADVISORY_CI_INDEX.md`。

**Non-claims（摘要）**：P8/P8.9 相關 CI／smoke **均 advisory 或 local-gate · 非 branch protection required** · **landing ≠ GA pass** · **local sanity ≠ prod-ready** · **≠** Phase% 上調。

| 路徑 | ci_class | 用途 | 標籤 |
|------|----------|------|------|
| `.github/workflows/bridge-smoke.yml` | **advisory CI** | P8.5 bridge Smoke A/B | **advisory · 非 required** · Scenario2 GA-remote **recorded** `29157178993`（仍 ≠ Phase closure／required） |
| `.github/workflows/p9-payment-sandbox-smoke.yml` | **advisory CI** | P9 sandbox payment happy-path（DRAFT→PAID） | **advisory · sandbox-only · ≠ INT／prod／required** · GA-remote PASS `29159159265` · 票 `WH-P9-CI-payment-sandbox-smoke-v1` |
| `scripts/run_ci_smoke_check_v1.py` | **local-only** | MP-SMOKE + metrics 本機／可選 CI wrapper | **repo local release sanity · ≠ GitHub required workflow**（無 required 綁定） |
| `scripts/run_multi_phase_smoke_v1.py` | **local-gate** | 七步跨 phase 接線 | **local-gate · non-prod · ≠ merge gate** |

- **Reviewer**：對照 `wave-next-code-inspector-v1.md` §3.2 三項 non-claims（無反向敘事）。
- **驗證**：`rg "advisory|local-only|local-gate|required" 04_Workflows/WORKFLOW_INDEX.md` · `rg "P8_P89_ADVISORY" docs/P8_P89_ADVISORY_CI_INDEX.md`

---

### 1.5 Governance Onboarding & OPS Cycle（Wave 1）

- Onboarding：
  - `docs/GOVERNANCE_ONBOARDING_v1.md` — 三層接戰指南（Tier 1：`_boot_context.py`）
- OPS 制度：
  - `04_Workflows/OPS_CYCLE.md` — 戰報／封存／回顧
- CLI（runner 見 `Master_Map.json` → `runners.ops_cycle_py`）：
  - `python 04_Workflows/_ops_cycle.py checklist --mode full` — 接戰就緒一鍵自檢
- 操作地圖：
  - `04_Workflows/runbooks/GOV_CORE_OPERATING_MAP_v0.1.md` — 總部 vs 暗部路徑
- 注意：暗部實作 CLI 工作目錄為 `gov_core_system` 根；本索引列 HQ 總部相對路徑。
- MVP 標準 trace 路徑（demo_phase / sampleco）：
  - **`docs/TABULAR_MVP_SSOT.md`** — Tabular MVP **產品主線 SSOT / landing**（定位、主鏈、非目標、入口索引）
  - `docs/mvp-standard-trace-path.md` — tabular MVP 主鏈 L1 trace 對照 spec（狀態節點、L1 CLI／artifacts、rerun 與最小回歸；L2 adjacent `[待確認]`）
- MVP 主鏈回歸測試：
  - `docs/mvp-mainline-regression.md` — 一鍵 `python scripts/run_mvp_mainline_regression.py`；覆蓋 `demo_phase` + `sampleco/2026-0001` E2E smoke
- **Tool Catalog + Selector Contract（Toolchain Wave B · WB-T1 · 跨轨 SSOT）**：
  - `docs/tool-catalog-and-selector-contract-v1.md` — Tabular / Non-Tabular / Gov Registry / Phase 8.8 四轨分轨 · `governed_by` · `tool_id` 命名 · selector dict 形状 · `plan_only` · Wave C 假设
  - 验证：`python -m unittest tests.test_tool_catalog_and_selector_contract_v1 -v`
  - 票 state：`04_Workflows/tickets/WB-T1-tool-catalog-and-selector-contract-v1_state.md`
- Tabular 工具 Catalog（Tabular MVP · 实现附录）：
  - `docs/tabular-tool-catalog-v1.md` — 人讀 spec；機器權威 `tools/tabular_tool_catalog_v1.json`（與 Phase 8.8 `W3-T1`–`T4` 分軌；跨轨边界见 WB-T1 contract）
- Tabular 工具 Selector（case_dir / intake → tool plan · 实现附录）：
  - `docs/tabular-tool-selector-spec.md` — `select_tabular_tools` 規則表（v1 僅推薦，不驅動 E2E；形状 SSOT 见 WB-T1 contract §4.1）
- Tabular 工具 Executor + Outbox（工具執行與 outbox schema）：
  - `docs/tabular-tool-outbox-spec.md` — `execute_tabular_tool`、per-run JSON、`outbox/events.jsonl`（≠ Phase 8.8 orchestration outbox）
- Tabular outbox consumer / debug（read-only 檢視與 history join）：
  - `docs/tabular-outbox-consumer-spec.md` — `inspect_tabular_outbox` CLI、`list_outbox_runs`／`get_outbox_run`／`join_with_case_history` API；與 `cases/index.json`／`lookup_case_history` 對齊（≠ Phase 8.8 replay）
- Tabular 工具層單元驗證（Catalog / Selector / Executor / Consumer）：
  - `python -m unittest tests.test_tabular_tool_catalog tests.test_tabular_tool_selector tests.test_tabular_tool_executor tests.test_tabular_outbox_consumer -v`
- Intake / Routing Catalog（Wave 2 · 跨 family 任務類型 → tool family / entrypoint）：
  - `docs/intake-routing-catalog-v1.md` — 人讀 spec；機器 SSOT `routing/intake_routing_catalog_v1.yaml`（rules + index only，≠ routing engine）
- Routing Eval Guide & Cases（Wave 2 · 如何編寫 routing eval case 與事後對照）：
  - `docs/routing-eval-guide-v1.md` — 人讀指南；機器 SSOT `routing/routing_eval_cases_v1.yaml`；驗證 `tests/test_routing_eval_cases.py`
- Routing → Tabular Tool Layer Glue（Wave 4 · W4-T1 · plan_only）：
  - `docs/routing-tool-layer-glue-v1.md` — `tabular.*` `task_type` → Selector／Executor 計畫 dict（`plan_tabular_route`）；feature flag `TABULAR_ROUTING_GLUE_ENABLED` 預設 off，未改主鏈
  - 實作：`routing/intake_to_tabular_glue.py`；驗證 `python -m unittest tests.test_routing_tabular_glue -v`
- Routing Eval Runner（Wave 4 · W4-T2 · dry-run）：
  - `docs/routing-eval-runner-v1.md` — 消費 `routing/routing_eval_cases_v1.yaml`，對照 catalog／glue／Gov policy（plan only，≠ routing engine）
  - CLI：`scripts/run_routing_eval.py`（預設 `--dry-run`）；驗證 `python -m unittest tests.test_routing_eval_runner -v`
- Tabular Intake Tool Path CLI（Wave 4 · W4-T3-A · dry-run）：
  - `docs/tabular-intake-tool-path-v1.md` — Tabular intake 獨立 CLI 路徑預演（glue → Selector → executor plan；不寫 outbox、不改主鏈 intake）
  - CLI：`scripts/run_tabular_intake_tool_path.py`（dry-run only，預演 glue + Selector + executor_plan）；驗證 `python -m unittest tests.test_tabular_intake_tool_path -v`
- Routing CI Hooks（Wave 4 · W4-T4 · dry-run + release checklist）：
  - PR CI：`.github/workflows/eval-gate-ci.yml` → job `eval-gate` → step `Routing eval dry-run (W4-T4)`（`tests.test_routing_eval_runner` + `run_routing_eval.py --dry-run --format json`；**無** `--execute`、**無** mainline regression）
  - Release checklist：`docs/tabular-mvp-release-checklist.md` — 發版前人工必跑項（主鏈 6/6、Wave 2/3-TL unittest、routing eval dry-run）
- **Tabular automation control plane（v1 · start/pause/stop）**：
  - `docs/tabular-cleaning-control-plane-v1.md` — `automation_state.json` schema · 狀態機 · 放置規則
  - `docs/tabular-cleaning-automation-manifest-v1.md` — allowed/forbidden · R1–R6 runbook 邊界
  - CLI：`python scripts/manage_tabular_automation_state.py status|start|pause|resume|stop --case-dir cases/demo_phase --json`
  - 驗證：`python -m unittest tests.test_tabular_automation_state -v`
  - **現狀**：CLI + state 已落地；`run_tabular_automation.py` unified driver **未**接線
  - 票 state：`04_Workflows/tickets/W4-T4-routing-ci-hooks_state.md`
- Phase 3.5 Cost / Model / Risk Governance Contract（Wave A · WA-T3 · gate SSOT）：
  - `docs/phase3-5-cost-model-governance-contract-v1.md` — mandatory / optional / shadow-only 分类总表；PR vs nightly 路径；**不含** prod canary 授权
  - 验证：`python -m unittest tests.test_phase3_5_governance_contract_v1 -v`
  - 票 state：`04_Workflows/tickets/WA-T3-phase3-5-cost-model-governance-contract-v1_state.md`
  - **交叉索引**（FP-G1-T4）：`docs/phase3-5-gate-crossref-index-v1.md` — eval-gate／K-2／ENF · blocking? · non_claims；≠ blocking canary／K-2 prod 主答案
- Tool Executor & Sandbox Safety Contract（Wave B · WB-T2 · Phase 8.8）：
  - `docs/tool-executor-and-sandbox-safety-contract-v1.md` — 四级 `execution_mode`（dry_run / plan_only / execute / sandbox_end_to_end）、case allowlist 矩阵、outbox 写入条件、sandbox 安全边界；**≠** 暗部 `core/tool_executor.py`
  - 交叉引用：`docs/tabular-tool-outbox-spec.md` §0
  - 验证：`python -m unittest tests.test_tool_executor_and_sandbox_contract_v1 -v`
  - 票 state：`04_Workflows/tickets/WB-T2-tool-executor-and-sandbox-safety-contract-v1_state.md`
- Outbox & Feedback Layer Contract（Wave B · WB-T3 · Phase 8.9 · 跨命名空間 SSOT）：
  - `docs/outbox-and-feedback-layer-contract-v1.md` — 六個 `outbox/` 命名空間表、`schema_id`、feedback 語意、`join_with_case_history`、`cases/index.json` 對齊、退化規則；**≠** Phase 8.8 `orchestration_bridge_outbox`
  - 機器索引：`docs/schemas/outbox_layer_v1.json`
  - 實作附錄（降級指針）：`docs/tabular-tool-outbox-spec.md` · `docs/tabular-outbox-consumer-spec.md`
  - 验证：`python -m unittest tests.test_outbox_and_feedback_layer_contract_v1 -v`
  - 票 state：`04_Workflows/tickets/WB-T3-outbox-and-feedback-layer-contract-v1_state.md`
- Toolchain Health Dashboard（Wave B · WB-T4 · Phase 5/6 · optional observability）：
  - `docs/toolchain-health-dashboard-v1.md` — `toolchain_health_v1` schema；合併 agent CI / metrics / monthly head / fixture maturity / catalog health / 可選 wf_status
  - CLI：`scripts/run_toolchain_health_dashboard.py`（預設 `--dry-run` 只讀 outbox；`gate_class=optional` · `blocks_mainline=false`）
  - Phase 6 附录：`docs/phase6-int-regression-gate-contract-v1.md` 附录 A — Tool-chain optional smoke matrix
  - 验证：`python -m unittest tests.test_toolchain_health_dashboard_v1 -v` · `python scripts/run_toolchain_health_dashboard.py --format json --dry-run`
  - 票 state：`04_Workflows/tickets/WB-T4-agent-lines-ci-and-metrics-dashboard-v1_state.md`
- Intake Decision Rules（Wave 5 · W5-T1 · decision helper）：
  - `docs/intake-decision-rules-v1.md` — Tabular intake 接案決策（`auto_accept` / `needs_review` / `reject`）；消費 W4-T1 glue，**不**改主鏈 routing
  - 實作：`routing/intake_decision_rules_v1.py`（`evaluate_intake_decision`）；CLI demo 同模組 `--task-type` / `--case-dir` / `--json`
  - 驗證：`python -m unittest tests.test_intake_decision_rules_v1 -v`
- Agent Intake Decision Entry（Wave 5 · W5-T1B · Agent/Orchestrator 入口）：
  - `docs/intake-decision-rules-v1.md` — 同上 W5-T1 spec；本票僅加 Agent/工具層 CLI，不改主鏈
  - CLI：`scripts/run_agent_intake_decision_demo.py`（`--task-type` / `--case-dir` / `--format text|json`）；呼叫 W4-T1 glue + W5-T1 `evaluate_intake_decision`，輸出 decision summary；plan-only，不 spawn Executor、不寫 outbox
  - 驗證：`python -m unittest tests.test_agent_intake_decision_demo -v`
- Intake Decision Rules v2（Wave 8 · W8-T2 · profile tiers + reject reduction）：
  - `docs/intake-decision-rules-v2.md` — A/B/C/D fixture profile · tiered signals · explicit reject table · non-Tabular shadow-flow hook
  - 實作：`routing/intake_decision_rules_v2.py`（`evaluate_intake_decision_v2` · `use_v1_fallback=True`）；CLI 同模組 `--task-type` / `--case-dir` / `--json`
  - Agent demo opt-in：`scripts/run_agent_intake_decision_demo.py --use-v2`（**默認仍 v1**）
  - 驗證：`python -m unittest tests.test_intake_decision_rules_v2 -v`
  - 票 state：`04_Workflows/tickets/W8-T2-decision-rules-v2-profile-and-reject-reduction_state.md`
- Intake Decision Rules v2 · Non-Tabular extension（Wave 9 · W9-T2 · NT-A/NT-B helper）：
  - `docs/intake-decision-rules-v2.md` — §3.1 NT-A/NT-B · R-NT1 reject · `non_tabular.*` output shape
  - 實作：同上 `routing/intake_decision_rules_v2.py`（`non_tabular.*` 分支；Tabular 不變）
  - Agent demo：`scripts/run_agent_intake_decision_demo.py --use-v2 --task-type non_tabular.document.extract`
  - 驗證：`python -m unittest tests.test_intake_decision_rules_v2 -v`
  - 票 state：`04_Workflows/tickets/W9-T2-non-tabular-decision-rules-v1_state.md`
- **Intake Gate layer（Phase 7.5 · P75-G2 · canonical gate + outbox）**：
  - `docs/intake-gate-contract-v1.md` — 對外三態 `accept` / `review_needed` / `reject`；`intake_gate_result_v1`；CP-A 邊界
  - 實作：`routing/intake_gate_layer_v1.py`（`evaluate_intake_gate` · v2 預設 + v1 fallback）
  - CLI：`scripts/run_intake_gate_cli.py`（`--mode preview|run` · run 寫 `outbox/<case_ref>/intake_gate_decision_*.json` + `outbox/intake_gate_events.jsonl`）
  - P7.5 intake upstream 入口：`docs/p75-intake-cli-upstream-mvp-v1.md`（`new_cleaning_case --run-p75-gate` → gate CLI）
  - Orchestrator S3：`scripts/run_agent_standard_case_experiment.py` 改走 gate layer；`result["intake_gate"]`
  - 驗證：`python scripts/run_intake_gate_cli.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview --format json` · `python -m unittest tests.test_intake_gate_layer_v1 -v`
  - 票 state：`04_Workflows/tickets/P75-G2-intake-gate-layer-and-outbox-record-v1_state.md`
- **Intake Gate Policy（Phase 7.5 · P75-G3 · allowlist/denylist）**：
  - `routing/intake_gate_policy_v1.yaml` — Policy SSOT（fixture tier、task_type family、deny reason_code）
  - `shared/schemas/intake_gate_policy_v1.json` — JSON Schema loader
  - 實作：`routing/intake_gate_policy_loader_v1.py` · `routing/intake_gate_policy_evaluator_v1.py` · `routing/intake_gate_policy_bridge_v1.py`
  - Golden fixtures：`tests/golden/intake_gate_policy/`（demo_phase / sampleco / deny_phi / deny_web_scraping / deny_audio_video / deny_scale_exceeds）
  - 驗證：`python -m unittest tests.test_intake_gate_policy_loader_v1 tests.test_intake_gate_policy_evaluator_v1 tests.test_intake_gate_policy_bridge_v1 tests.test_intake_gate_policy_integration_v1 -v`
  - 票 state：`04_Workflows/tickets/P75-G3-intake-gate-policy-allowlist-denylist-v1_state.md`
- **Intake Gate E2E regression（Phase 7.5 · P75-REGRESSION · gate + CP-A + notify）**：
  - `docs/phase-7.5-gate-checkpointA-notify-e2e-v1.md` — 三態 + CP-A + `intake.gate_decision` 行為樣本
  - 測試：`tests/test_intake_gate_checkpointA_notify_e2e_v1.py`（accept / review_needed / policy-deny reject）
  - 驗證：`python -m unittest tests.test_intake_gate_checkpointA_notify_e2e_v1.py -v`
  - 票 state：`04_Workflows/tickets/P75-REGRESSION-gate-checkpointA-notify-e2e-v1_state.md`
- **P7.5 Alert Sink（P75-G6 · 本地 file／stub HTTP · ≠ UI／prod）**：
  - `docs/p75-alert-sink-contract-v1.md` · `shared/schemas/p75_alert_sink_event_v1.json` · `delivery/p75_alert_sink_v1.py`
  - CLI：`scripts/run_p75_alert_sink_v1.py`（`--from-probe`／`--alert-json` · `--mode file|stub_http`）
  - 驗證：`python -m unittest tests.test_p75_alert_sink_v1 -v`
  - 票 state：`04_Workflows/tickets/P75-G6-alert-sink-contract-v1_state.md`
- **P7.5 Intake Gate HTTP stub（P75-G7 · loopback `POST /api/intake/gate` · ≠ prod／UI）**：
  - `docs/p75-intake-gate-http-stub-v1.md` · `shared/schemas/intake_gate_http_request_v1.json` · `routing/intake_gate_http_stub_v1.py`
  - CLI：`scripts/run_intake_gate_http_stub_v1.py`（`--once`／`--serve` · 預設 `preview`）
  - 驗證：`python -m unittest tests.test_intake_gate_http_stub_v1 -v`
  - 票 state：`04_Workflows/tickets/P75-G7-intake-gate-http-stub-v1_state.md`
- **Wave 3 煙霧串線（W3-SMOKE · G7→gate→notify→G6 sink→MP-SMOKE · ≠ UI／prod）**：
  - `docs/wave3-smoke-g7-gate-notify-mp-chain-v1.md` · `delivery/wave3_smoke_chain_v1.py`
  - CLI：`scripts/run_wave3_smoke_chain_v1.py --case-ref demo_phase --format json`
  - 驗證：`python -m unittest tests.test_wave3_smoke_chain_v1 -v`
  - 票 state：`04_Workflows/tickets/W3-SMOKE-g7-gate-notify-mp-chain-v1_state.md`
- **P8.6–8.8 Runtime Inspect（Wave 2 · P868-W2 · catalog→selector→executor dry_run · ≠ UI／prod browser）**：
  - `docs/p868-runtime-inspect-catalog-selector-executor-v1.md` · `delivery/p868_runtime_inspect_v1.py`
  - CLI：`scripts/inspect_p868_runtime_v1.py --case-ref demo_phase --format json`
  - 驗證：`python -m unittest tests.test_p868_runtime_inspect_v1 -v`
  - 票 state：`04_Workflows/tickets/P868-W2-runtime-inspect-catalog-selector-executor-v1_state.md`
- **Wave 5 Human／staging 清單（WAVE5 · H1–H5＝Round-2 五前置 · 文件 only · ≠ 已解阻／prod）**：
  - `04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.md` · `.yaml`
  - 驗證：`python -m unittest tests.test_wave5_human_staging_checklist_v1 -v`
  - 票 state：`04_Workflows/tickets/WAVE5-human-staging-checklist-v1_state.md`
- **Workflow Event Consumer（P8.9-T1 · read-only event ledger）**：
  - `delivery/workflow_event_consumer_v1.py` — 合併 `notification_events.jsonl` + `checkpoint_events.jsonl` → normalized timeline
  - `scripts/inspect_workflow_events.py` — CLI：`--case-ref` · `--event-type` · `--event-id` · `--since` · `--format json|text`
  - 驗證：`python scripts/inspect_workflow_events.py --case-ref demo_phase --format json` · `python -m unittest tests.test_workflow_event_consumer_v1 -v`
  - 票 state：`04_Workflows/tickets/P8.9-T1-workflow-event-ledger-and-tracking-consumer-v1_state.md`
- **Feedback Ingest（P8.9-T2 · downstream ack）**：
  - `delivery/feedback_ingest_v1.py` — `ingest_pending_events()` · `record_downstream_ack(event_id, handler_id, status, message)`
  - `scripts/run_feedback_ingest.py` — CLI：`--case-ref` · `--dry-run`
  - 存儲：`outbox/feedback/<case_ref>/acks/<event_id>_<handler_id>.json`
  - 驗證：`python scripts/run_feedback_ingest.py --case-ref demo_phase --dry-run` · `python -m unittest tests.test_feedback_ingest_v1 -v`
  - 票 state：`04_Workflows/tickets/P8.9-T2-feedback-ingest-and-downstream-ack-v1_state.md`
- **P8.9 Operator Fields 投影（Wave 2 · P89-W2 · 只讀 · T4=WD-P7-T2 敘事）**：
  - `docs/p89-operator-fields-projection-v1.md` · `delivery/p89_operator_fields_v1.py`
  - CLI：`scripts/inspect_p89_operator_fields_v1.py --case-ref demo_phase --format json`
  - 驗證：`python -m unittest tests.test_p89_operator_fields_v1 -v`
  - 票 state：`04_Workflows/tickets/P89-W2-narrative-t4-obs-projection-v1_state.md`
- **Operator Backlog（Phase 8 · P8-T2 · pending visibility v1）**：
  - `docs/phase-8-operator-backlog-v1.md` — pending/blocked/completed 分類規則與 JSON 形狀
  - `scripts/list_operator_backlog_v1.py` — CLI：`--case-ref` · `--status pending|blocked|completed` · `--format json|table`
  - 資料源：合併 `workflow_event_consumer_v1` timeline + checkpoint A 狀態 + intake gate record
  - 驗證：`python scripts/list_operator_backlog_v1.py --status pending --format json` · `python -m unittest tests.test_operator_backlog_v1 -v`
  - 票 state：`04_Workflows/tickets/P8-T2-operator-pending-visibility-v1_state.md`
  - **P8.5 bridge 邊界（W3-P8-BRG）**：Operator Backlog **不**以 bridge smoke 為前置；bridge = optional advisory（§1.4 · `docs/phase8_5-bridge-smoke-runbook-v1.md`）· **≠** Phase 8 release gate。
- **Operator Backlog HTTP API（Phase 8 · P8-API · read-only）**：
  - `scripts/operator_http_api_v1.py` — dev/sandbox HTTP：`GET /operator/backlog`（query：`status` · `case_ref`）；JSON 形狀同 CLI `--format json`
  - `GET /health` — liveness；**只讀**、無 mutation
  - 驗證：`python scripts/operator_http_api_v1.py --port 8080` · `curl 'http://127.0.0.1:8080/operator/backlog?status=pending'` · `python -m unittest tests.test_operator_http_api_v1 -v`
  - 文檔：`docs/phase-8-operator-backlog-v1.md` §HTTP API v1
  - 票 state：`04_Workflows/tickets/P8-API-operator-backlog-http-endpoint-v1_state.md`
- **P8.9 Verification Bundle（REGRESSION v1 · consumer / feedback / dispatch smoke）**：
  - `scripts/run_p8_9_verification_bundle_v1.py` — 一鍵跑 `demo_phase` experiment + 聚合 events / audit / acks
  - 產物：`outbox/verification/<case_slug>/`（`p8.9_verification_run.json` · `events.json` · `audit_quickview.json` · `acks.json`）
  - 驗證：`python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json` · `python -m unittest tests.test_p8_9_verification_bundle_v1.py -v`
  - 文檔：`docs/p8_9-verification-bundle-v1.md`
  - 票 state：`04_Workflows/tickets/P8.9-REGRESSION-standard-case-verification-bundle-v1_state.md`
  - **Observability**：交付鏈 trace／artifact 地圖 → `docs/p8_p89_delivery_observability_contract_v1.md`（W3-P89-OBS）
- **Multi-Phase Smoke Runner（MP-SMOKE v1 · 跨 P7.5 / Phase 8 / P8.9 的 smoke 腳本）**：
  - `scripts/run_multi_phase_smoke_v1.py` — 跨 7.5 / 8 / 8.9 的 smoke 腳本；七步串接：gate preview → gate run+notify → std-case experiment → events inspect → feedback dry-run → P8.9 bundle collect → operator backlog
  - 產物：`outbox/verification/<case_slug>/multi_phase_smoke_run.json`（+ P8.9 bundle artifacts when step 6 runs）
  - 驗證：`python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --enable-dispatch --format json` · `python -m unittest tests.test_multi_phase_smoke_v1 -v`
  - 票 state：`04_Workflows/tickets/MP-SMOKE-std-case-multi-phase-smoke-v1_state.md`
  - **Observability**：七步 artifact／`multi_phase_smoke.ok` 等 trace → `docs/p8_p89_delivery_observability_contract_v1.md`（W3-P89-OBS）
  - **Release-sanity 操作單頁**（FP-G6-T2）：`docs/phase6-release-sanity-runbook-v1.md`（MP→MC→CI-SMOKE；契約 SSOT 仍為 `docs/smoke-and-regression-contract-v1.md`）
- **Standard-Case Metrics Exporter（MP-METRICS · 標準 case metrics exporter · read-only）**：
  - `scripts/export_std_case_metrics_v1.py` — 標準 case metrics exporter；per-case 輕量指標：backlog pending/blocked/completed + notification ack 計數
  - CLI：`--case-ref` · `--format json|text|prometheus`
  - 資料源：只讀 `list_operator_backlog_v1` · `workflow_event_consumer_v1` · `feedback_ingest_v1`（不寫 outbox）
  - 驗證：`python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json` · `python -m unittest tests.test_export_std_case_metrics_v1 -v`
  - 票 state：`04_Workflows/tickets/MP-METRICS-std-case-metrics-exporter-v1_state.md`
- **Standard-Case Metrics HTTP Endpoint（MP-METRICS-HTTP · Prometheus scrape · read-only）**：
  - `scripts/metrics_http_endpoint_v1.py` — `GET /metrics?case_ref=<slug>` 回傳 Prometheus text；預設 `demo_phase`；錯誤以 `# error:` 註解 + HTTP 200
  - 重用：`export_std_case_metrics` · `format_std_case_metrics_prometheus`
  - 驗證：`python scripts/metrics_http_endpoint_v1.py --port 9090` · `curl 'http://127.0.0.1:9090/metrics?case_ref=demo_phase'` · `python -m unittest tests.test_metrics_http_endpoint_v1 -v`
  - 票 state：`04_Workflows/tickets/MP-METRICS-HTTP-std-case-metrics-endpoint-v1_state.md`
- **Multi-Case Metrics Aggregator（MC-METRICS · fleet rollup · read-only）**：
  - `scripts/aggregate_multi_case_metrics_v1.py` — 對多 case 呼叫 `export_std_case_metrics`（library）並聚合 pending/blocked/completed + notification ack 總計
  - CLI：`--cases`（逗號分隔；預設 `demo_phase,sampleco/2026-0001`）· `--format json|text` · `--no-per-case`
  - 輸出：`schema_version=multi_case_metrics_v1` · `metrics.total_*` · 可選 `per_case` drill-down
  - 驗證：`python scripts/aggregate_multi_case_metrics_v1.py --format json` · `python -m unittest tests.test_aggregate_multi_case_metrics_v1 -v`
  - 票 state：`04_Workflows/tickets/MC-METRICS-multi-case-metrics-aggregation-v1_state.md`
  - **Fleet operator 讀法**（FP-G5-T1）：`docs/fleet-metrics-dashboard-operator-v1.md`（≠ Grafana 已上線 · ≠ P5 closure）
- **P5 Metrics Grafana Stub（P5-metrics-grafana-stub-v1 · 本地 JSON 對照 · ≠ 真 Grafana／PG soak）**：
  - `docs/p5-metrics-grafana-stub-contract-v1.md` · `shared/schemas/p5_metrics_grafana_stub_v1.json` · `observability/p5_metrics_grafana_stub_v1.py`
  - CLI：`scripts/run_p5_metrics_grafana_stub_v1.py`（`--case-ref` · `--format json|text` · `--write`）
  - 驗證：`python -m unittest tests.test_p5_metrics_grafana_stub_v1 -v` · `python scripts/run_p5_metrics_grafana_stub_v1.py --format json`
  - 票 state：`04_Workflows/tickets/P5-metrics-grafana-stub-v1_state.md`
  - **Grafana／PG soak deferred 索引**（FP-G5-T2）：`docs/grafana-pg-soak-deferred-index-v1.md`（planning；≠ soak 已跑）
  - **Lane Progress 末尾模板**（FP-G5-T3）：`docs/lane-progress-append-template-v1.md`（append-only · evidence_tier）
- **CI Smoke Check（CI-SMOKE v1 · multi-phase smoke + metrics gate）**：
  - `scripts/run_ci_smoke_check_v1.py` — CI 專用 wrapper；單 case 串跑 MP-SMOKE + MP-METRICS，套用 pass/fail 規則，失敗 non-zero exit
  - CLI：`--case-ref`（default `demo_phase`）· `--format text|json` · optional `--enable-dispatch` · `--outbox-root`
  - Pass：`multi_phase_smoke ok=true` · `std_case_metrics ok=true` · `notifications_failed_ack_count == 0`
  - 驗證：`python scripts/run_ci_smoke_check_v1.py --format text` · `python -m unittest tests.test_ci_smoke_check_v1 -v`
  - 票 state：`04_Workflows/tickets/CI-SMOKE-multi-phase-smoke-and-metrics-hook-v1_state.md`
- **Multi-Case Smoke Runner（MC-SMOKE v1 · 多 case / 多 profile smoke orchestration）**：
  - `scripts/run_multi_case_smoke_v1.py` — 內建代表性 case 列表（`demo_phase` · `sampleco/2026-0001` · `phi_demo` policy deny）；逐案呼叫 MP-SMOKE 並聚合 summary
  - CLI：`--cases`（comma-separated，可覆蓋內建列表）· `--format text|json` · optional `--enable-dispatch` · `--outbox-root`
  - 產物：`outbox/verification/multi_case_smoke_run.json`（聚合 summary；不改 per-case MP-SMOKE artifact 行為）
  - 驗證：`python scripts/run_multi_case_smoke_v1.py --format json` · `python -m unittest tests.test_multi_case_smoke_v1 -v`
  - 票 state：`04_Workflows/tickets/MC-SMOKE-multi-case-smoke-runner-v1_state.md`

### 1.55 Wave Master · Wave-next · Multi-Chat（W5-T5 · 全 Wave rollup）

> **票**：`W5-T5-cross-wave-playbook-index-v1` · **doc-only** · **不改 Phase%**  
> **用途**：接戰時決定開 **Wave Master**（W1–W5 規劃／Master CP）還是 **Wave-next**（P7／P8.5／P9 戰術 lane）。

#### SSOT 位階（高 → 低）

| 位階 | 路徑 | 角色 |
|------|------|------|
| 1 · Phase% | `docs/WAVE_PROGRESS_DASHBOARD.md` | 完成度數字唯一 SSOT（本節**不改**） |
| 2 · Wave Master 規劃 | `04_Workflows/tickets/W-MASTER-wave-plan_state.md` | Wave 1–5 票 FRAME 母本 |
| 3 · Wave-next 戰術 | `04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md` | P7／P8.5／P9 lane 編排 |
| 4 · 子票 STATE | `04_Workflows/tickets/<ticket_id>_state.md` | 執行真相（衝突以子票為準） |
| 5 · Command Queue | `04_Workflows/command_queue/QUEUE.yaml` | 總指揮操作索引（不重複 FRAME） |

#### Traversal（三階段）

| 階段 | 讀什麼 | 開哪種 chat |
|------|--------|-------------|
| **規劃** | W-MASTER · `docs/wave-master-ticketing-playbook.md` · W5-T2 template | `/wave-master-planner` 或 `/ticket-orchestrator` 開 Wave 子票 |
| **執行** | 子票 STATE · W5-T1 commands · Multi-Chat SKILL | `/ticket-implementer` → reviewer → scribe |
| **Reviewer 收口** | FRAME AC · `wave-next-code-inspector-v1.md`（戰術線）或票內 C_REPORT | Wave-next 並行 lane 用 inspector；Master CP 用票 AC；**over-claim 抽样加速** → `docs/phase6-inspector-overclaim-spotcheck-v1.md`（FP-G6-T4 · 不取代 inspector SSOT） |

**決策一句話**：要排 **Wave 1–5 / Master CP 資產** → Wave Master；要推 **P7 Round-2／P8.5 GA／P9 首跑** 戰術 → 先讀 W-ORCH（Wave-next）。衝突時 **子票 STATE ＞** 本索引摘要。  
**G1 解阻／批文／寫入邊界**（FP-G1 · doc）：`docs/governance-dual-unblock-checklist-v1.md`（五頂 · ≠ Round-2 GO）· `docs/wc-pre-06-07-approval-tracker-v1.md`（approved 僅 human）· `docs/progress-dashboard-append-protocol-v1.md`（append-only · 禁改 Phase%）· **Phase 影響協議** `docs/phase-progress-impact-protocol-v1.md`（提案 Δ vs 寫入 % · `apply_phase_pct` 預設 false · 僅 W-PROG 可寫數字格 · §9 自動估 Δ heuristic）· **Phase% apply runner** `04_Workflows/_phase_pct_apply.py`（`estimate` → `verify` → `apply --authorize`；開工先估、檢查後再寫 · 預設 dry-run · ≠ 普通票自動 uplift）。  
**Batch-3 G3/G4 對齊**（2026-07-10）：`docs/evidence-tier-contract-v1.md`（FP-G3-T1）· `docs/dual-cp-narrative-alignment-v1.md`（FP-G4-T1）· `docs/trace-canonical-schema-append-process-v1.md`（FP-G3-T4）。

#### 有效路徑（≥6）

1. `docs/wave-master-ticketing-playbook.md` — Wave Master 開票／observability 規範  
2. `docs/wave-next-playbook.md` — Wave-next 戰術 playbook  
3. `.cursor/skills/multi-chat-ticket-workflow/SKILL.md` — Multi-Chat 工作流 skill  
4. `.cursor/rules/multi_chat_roles.mdc` — 四角色邊界  
5. `.cursor/commands/README.md` — slash commands SSOT（**W5-T1** · 非歷史 W1-T2）  
6. `docs/wave-master-ticket-template-v1.md` — schema 消費說明（**W5-T2**）  
7. `docs/p75-upstream-entry-index-v1.md` — **僅 P7.5 上游**（並列 · 非本節替代）  
8. `04_Workflows/review_checklists/wave-next-code-inspector-v1.md` — Wave-next Reviewer  
8b. `docs/phase6-inspector-overclaim-spotcheck-v1.md` — over-claim 抽样对照（FP-G6-T4 · 加速层 · ≠ 替代 #8）  
8c. `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md` — **全線到 100 Wave 0–6**（2026-07-13 · 契約／後端先 · UI→Wave 4 · 匯總票 `W-PROG-full-line-to-100-wave-plan-2026-07-13`）  
8c′. `docs/wave4-ui-visual-freeze-v1.md` — **Wave 4 UI 視覺凍結**（2026-07-27 · `unified_P1–P5` · 票 `W4-UI-FREEZE`／`W4-UI-A`–`E` accepted_with_gaps · **A–E 靜態殼完成** · ≠ UI 全量交付）  
8c″. `docs/wave4-ui-b-p5-swimlane-runbook-v1.md` — Wave4-B P5 泳道開啟／mock／驗證  
8c‴. `docs/wave4-ui-c-p4-command-desk-runbook-v1.md` — Wave4-C P4 三省指揮台開啟／mock／驗證  
8c⁗. `docs/wave4-ui-d-p3-dark-loop-runbook-v1.md` — Wave4-D P3 暗部執行閉環開啟／mock／驗證  
8c⁵. `docs/wave4-ui-e-p2-skills-resources-runbook-v1.md` — Wave4-E P2 技能與資源開啟／mock／驗證  
8d. `04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.md` — **Wave 5 Human／staging 清單**（H1–H5＝P7 Round-2 五前置 · ≠ 已解阻／prod GO · 票 `WAVE5-human-staging-checklist-v1`）  

#### Non-claims

索引就緒 **≠** P10／P10.5 runtime 排期 **≠** WC-PRE-06/07 `approved` **≠** Phase% 上調 **≠** 合并 W-MASTER／W-ORCH。

---

### 1.6 Multi-Agent Collaboration（Wave 5 · W5-T0 · orchestration docs）

> Multi-Chat 四角色協作文檔（Orchestrator / Implementer / Reviewer / Scribe）；不改程式碼/測試，僅文檔化已存在做法。

- **Wave-next control plane entry（2026-06-24）**：並行 P7 / P8.5 / P9 + Reviewer 收口時，Orchestrator 與各 chat **先讀** `04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md`；Reviewer 只讀驗收見 `04_Workflows/review_checklists/wave-next-code-inspector-v1.md`。全 Wave rollup 見 **§1.55**（W5-T5）。
- **P7.5 upstream entry（2026-07-09）**：P7.5 上游接戰入口索引 → `docs/p75-upstream-entry-index-v1.md`（gate CLI · policy · intake CLI · deny · trace · MP-SMOKE step 1）；trace SSOT → `docs/p75-intake-gate-control-plane-trace-v1.md`。**僅 P7.5 上游** · 全 Wave rollup 見 **§1.55 W5-T5**（非本節）。

| 文件 | 用途 | 票號 |
|------|------|------|
| `docs/multi-agent-collaboration-spec-v1.md` | 四角色規格（目的/做什麼/不做什麼/輸入輸出/DoD） | W5-T0 |
| `docs/multi-agent-handoff-runbook-v1.md` | 票生命週期、角色切換、拆票/合票、常見錯誤 | W5-T0 |
| `docs/multi-agent-replay-guide-v1.md` | 如何 replay 已完成票（以 W4-T2 為範例） | W5-T0 |
| **`docs/phase4-multi-agent-collaboration-contract-v1.md`** | **Phase 4 contract SSOT**（四角色 contract 表、O→B→C→D 工作流、routing 决策树、STATE 写入冻结） | **WA-T4** |
| `.cursor/rules/multi_chat_roles.mdc` | 角色邊界母本（機器層） | （pre-existing） |
| `04_Workflows/tickets/README.md` | 票機制、區塊權限、標準流程 | （pre-existing） |

- **层级关系**：**contract（WA-T4）** ＞ `multi_chat_roles.mdc`（机器 FORBID/MUST）＞ W5-T0 spec ＞ handoff runbook ＞ replay guide
- 上游文件：`.cursor/rules/multi_chat_roles.mdc` · `AGENTS.md` · `ENGINEERING_CONTRACT.md`
- 參考實例：W4-T1 / W4-T2 / W4-T3-A / W4-T4 state（四角色協作實際執行）
- 票 state：`04_Workflows/tickets/W5-T0-multi-agent-collaboration-docs_state.md`

### 1.7 Tabular MVP Wave Dashboard（Wave 1 / 2 / 3-TL / 4 / 5 完成度）

- **Dashboard**：`docs/WAVE_PROGRESS_DASHBOARD.md` — Tabular MVP 治理／Routing／Tool Layer 完成度總覽（**≠** Observability `docs/WAVE1-3_HISTORY_STATUS.md`；**≠** 最小接案 MVP Wave 1–4，見 `00_Agent_Work_Progress.md` 該段）
- **Phase% SSOT（2026-07-13 收工 · 2026-07-14 驗證對齊）**：全轨见 Dashboard §Phase 完成度表／Gauge — **P1 90 · P2 66（+1）· P3 82 · P3.5 55 · P4 77（+2）· P5 72（+2）· P6 83 · P7 30 · P7.5 49（+4）· P8 100（+55）· P8.5 20（+10）· P8.6 66（+1）· P8.7 61（+1）· P8.8 59（+1）· P8.9 41（+1）· P9 24（+4）· P10 37（+2）· P10.5 30**（括號＝相對 07-13 開工／W-PROG A prev；平均 ≈58%）。寫入鏈：W-PROG A/B · triple · P8-80／toward-100／to-100 · wave013。**≠** prod／required CI／Round-2 GO／06-23 虛高。協議：`docs/phase-progress-impact-protocol-v1.md` · runner `04_Workflows/_phase_pct_apply.py` · `Master_Map.war_status` **v2.62**
  - **脚注（W3-P89-SSOT · 2026-07-10 · 敘事 · 數字以 07-13 表為準）**：P8／P8.9 能力摘要沿用 06-19 敘事；五子票 STATE → `P8-T2` · `P8-API` · `P8.9-T2` · `P8.9-T3` · `P8.9-REGRESSION`。**T4 webhook = WD-P7-T2 landed**（2026-07-13 敘事對齊 · `P89-W2`）；Deferred 仍：batch／resume-latest／staging-prod SLA／Wave 4 UI。OBS → `docs/p8_p89_delivery_observability_contract_v1.md` · EVD → `docs/p8_p89_evidence_index_v1.md` · ADV → `docs/P8_P89_ADVISORY_CI_INDEX.md`／§1.46。
  - **P8.9 Operator Fields 投影（Wave 2 · P89-W2 · 只讀 · ≠ UI）**：`docs/p89-operator-fields-projection-v1.md` · `delivery/p89_operator_fields_v1.py` · `scripts/inspect_p89_operator_fields_v1.py` · `python -m unittest tests.test_p89_operator_fields_v1 -v`
  - **P8.6–8.8 Runtime Inspect（Wave 2 · P868-W2 · ≠ UI／prod browser）**：`docs/p868-runtime-inspect-catalog-selector-executor-v1.md` · `scripts/inspect_p868_runtime_v1.py` · `python -m unittest tests.test_p868_runtime_inspect_v1 -v`
- **Wave 1（done）**：`docs/governance-constitution-v1.md` · `docs/mvp-standard-trace-path.md` · `docs/mvp-mainline-regression.md`
- **Wave 2（done）**：`docs/intake-routing-catalog-v1.md` · `docs/routing-eval-guide-v1.md`
- **Wave 3-TL（4/4 done）**：T1–T4 done（`accepted_with_gaps`）— consumer／debug 見 §1.5；票表見 Dashboard
- **Wave 4（4/4 done）**：W4-T1–T3-A done（`accepted_with_gaps`）— 見 §1.5；W4-T4 done — PR CI routing eval dry-run + `docs/tabular-mvp-release-checklist.md`
- **Wave 5（docs + HITL impl）**：W5-T0-multi-agent-collaboration-docs — `docs/multi-agent-collaboration-spec-v1.md` · `docs/multi-agent-handoff-runbook-v1.md` · `docs/multi-agent-replay-guide-v1.md`；W5-T1-intake-decision-rules-v1 — `docs/intake-decision-rules-v1.md`（decision helper only）；W5-T1B-intake-decision-agent-entry — `scripts/run_agent_intake_decision_demo.py`（Agent CLI 入口）；W5-T2-hitl-checkpoints-v1 — `docs/hitl-checkpoints-v1.md`（design only）；**HITL Checkpoints v1 impl · W5-T2B** — `hitl/checkpoints_v1.py` · `scripts/run_hitl_checkpoint_cli.py` · `tests/test_hitl_checkpoints_v1.py`（檔案型 state/events + CLI；不 resume 主鏈）

### 1.8 Skill Card & Skill Map（Wave 6 — 文檔化與模組映射）

> **Track**：Tabular MVP 工作流抽象 → 可重用 Skill Card + 模組流程映射

| 文件 | 用途 | 票號 |
|------|------|------|
| `docs/skill-cards-v1.md` | Skill Card A/B：demo_phase / sampleco 標準清洗案（10 欄位模板） | W6-T1 |
| `docs/skill-map-v1.md` | Skill Map：8 步驟模組映射表（intake → decision → glue → selector → executor → outbox → inspect → release） | W6-T1 |
| `04_Workflows/tickets/W6-T1-skill-card-and-skill-map-v1_state.md` | 本票 state / AC / 驗證 | W6-T1 |
| `docs/agent-run-standard-case-experiment-v1.md` | 15 步標準實驗線設計（S1-S15）：完整流程規格、Checkpoint A/B 整合、驅動者分布 | W6-T3 |
| `04_Workflows/tickets/W6-T3-agent-run-standard-case-experiment-v1_state.md` | W6-T3 票 state | W6-T3 |
|| `docs/agent-run-standard-case-orchestrator-v1.md` | Agent-run 實驗線 orchestrator CLI（preview/run）| W6-T4 |
|| `scripts/run_agent_standard_case_experiment.py` | W6-T4 CLI 實作 | W6-T4 |
|| `04_Workflows/tickets/W6-T4-agent-run-standard-case-orchestrator-v1_state.md` | W6-T4 票 state | W6-T4 |
|| `docs/checkpoint-a-integration-v1.md` | Checkpoint A 整合層：W5-T1 decision → W5-T2B state/resume | W6-T5 |
|| `hitl/checkpoint_a_integration_v1.py` | Checkpoint A integration · `maybe_create_checkpoint_a` / `resume_plan_from_checkpoint_a` | W6-T5 |
|| `tests/test_checkpoint_a_integration_v1.py` | W6-T5 unittest | W6-T5 |
|| `04_Workflows/tickets/W6-T5-integrate-checkpoint-a-intake-confirmation_state.md` | W6-T5 票 state | W6-T5 |
|| `docs/checkpoint-b-integration-v1.md` | Checkpoint B 整合層：output_guard → HITL delivery gate → `delivery_plan` | W6-T6 |
|| `hitl/checkpoint_b_integration_v1.py` | Checkpoint B integration · `maybe_create_checkpoint_b` / `delivery_plan_from_checkpoint_b` | W6-T6 |
|| `tests/test_checkpoint_b_integration_v1.py` | W6-T6 unittest | W6-T6 |
|| `04_Workflows/tickets/W6-T6-integrate-checkpoint-b-delivery-gate_state.md` | W6-T6 票 state | W6-T6 |
| `docs/agent-run-experiment-eval-guide-v1.md` | 實驗線驗收、replay、失敗分析完整指南（三級成功定義/五階段replay/六類失敗/G1-G7升級條件） | W6-T7 |
| `04_Workflows/tickets/W6-T7-experiment-eval-and-replay-guide-v1_state.md` | W6-T7 票 state | W6-T7 |
| `docs/agent-standard-case-regression-v1.md` | Agent-run 實驗線輕量回歸鉤子（preview/run JSON 紀錄）| W6-T8 |
| `scripts/run_agent_standard_case_regression.py` | W6-T8 回歸 helper CLI | W6-T8 |
| `tests/test_agent_standard_case_regression.py` | W6-T8 unittest | W6-T8 |
| `04_Workflows/tickets/W6-T8-agent-standard-case-experiment-regression-v1_state.md` | W6-T8 票 state | W6-T8 |
| `docs/agent-standard-line-governance-view-v1.md` | Agent-run 標準線治理觀點：15 步決策權分佈 / audit log / 風險 safeguard / 升級路徑治理原則 | W6-T9 |
| `04_Workflows/tickets/W6-T9-agent-standard-line-governance-view-v1_state.md` | W6-T9 票 state | W6-T9 |
| `cases/additional_demo/` · `cases/sandbox_client/` | W7-T1 實驗線擴展 Tabular fixtures（非 production contract） | W7-T1 |
| `04_Workflows/tickets/W7-T1-extend-agent-standard-line-more-fixtures_state.md` | W7-T1 票 state | W7-T1 |
| `04_Workflows/tickets/W7-T2-increase-agent-run-mode-coverage-v1_state.md` | W7-T2 run 覆蓋擴大票 state | W7-T2 |
| `scripts/run_agent_standard_case_experiment.py`（W7-T2 run_path_profile）| demo_phase / sampleco 受控 run 執行 | W7-T2 |
| `scripts/run_agent_standard_case_regression.py`（`--run-mode run-all-allowed`）| 全 allowlist run 回歸 | W7-T2 |
| `delivery/controlled_notify_experiment_v1.py` | 受控 S15 notify 試驗：讀 signoff/bundle → 模擬 client summary → outbox JSON | W7-T3 |
| `scripts/run_controlled_delivery_notify_experiment.py` | W7-T3 CLI（`--case-dir`，`--dry-run` 預設 true） | W7-T3 |
| `docs/controlled-delivery-notify-experiment-v1.md` | W7-T3 目的、allowlist、命令、JSON 樣例 | W7-T3 |
| `tests/test_controlled_delivery_notify_experiment_v1.py` | W7-T3 unittest | W7-T3 |
| `04_Workflows/tickets/W7-T3-controlled-delivery-and-notify-experiment-v1_state.md` | W7-T3 票 state | W7-T3 |
| `delivery/delivery_approval_cli_v1.py` | S13 一鍵交付確認：signoff/guard 摘要 + CP-B 決策 + 可選 notify 試驗 | W8-T3 |
| `scripts/run_delivery_approval_cli.py` | W8-T3 CLI（`--action approve|request_changes|hold`，`--confirm` 才寫入） | W8-T3 |
| `docs/delivery-approval-one-click-cli-v1.md` | W8-T3 目的、命令、resume_context 樣例 | W8-T3 |
| `tests/test_delivery_approval_cli_v1.py` | W8-T3 unittest | W8-T3 |
| `04_Workflows/tickets/W8-T3-delivery-approval-one-click-cli-v1_state.md` | W8-T3 票 state | W8-T3 |

**一句話**：將 Wave 1–5 穩定的 Tabular MVP 工作流抽象為 **Skill Cards**（可重用工作流卡片），並建立 **Skill Map**（模組 → 流程步驟映射），供未來 Agent 快速定位實作入口。

**Skill Card 結構**（10 欄位）：
1. Skill 名稱
2. 適用條件
3. 輸入
4. 路由 / glue
5. Selector / planned_tools
6. Executor / 預期產物
7. Outbox / trace 關聯
8. 完成定義（DoD）
9. 常見失敗模式
10. Human checkpoint（HITL 預留）

**Skill Map 步驟**（8 步驟）：
| Step | Module | Maturity |
|------|--------|----------|
| intake | `scripts/new_cleaning_case.py` | done |
| decision | `routing/intake_decision_rules_v1.py` | done |
| glue | `routing/intake_to_tabular_glue.py` | done |
| selector | `tools/tabular_tool_selector.py` | done |
| executor | `tools/tabular_tool_executor.py` | done |
| outbox | `tools/tabular_outbox_writer.py` | done |
| inspect/replay | `tools/tabular_outbox_consumer.py` | done / planned (replay) |
| release/regression | `scripts/run_mvp_mainline_regression.py` | done |

- 上游文件：`docs/mvp-standard-trace-path.md` · `docs/tabular-tool-catalog-v1.md` · `docs/tabular-tool-selector-spec.md`
- 完成度總覽：`docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 6
- 票 state：`04_Workflows/tickets/W6-T1-skill-card-and-skill-map-v1_state.md`

### 1.9 Agent Standard Line Wave 7 — Run Path · Extended Fixtures · Controlled Notify（W7-T1/T2/T3 · 設計收斂 W7-T4）

> **Track**：Tabular MVP 實驗線能力擴展 + v2 藍圖／Skill／治理對齊

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `cases/additional_demo/` · `cases/sandbox_client/` | W7-T1 擴展實驗 fixture（preview allowlist） | W7-T1 |
| `scripts/run_agent_standard_case_experiment.py` | W7-T2 run path（`_RUN_PATH_PROFILES`：demo→bundle · sampleco→CP-B） | W7-T2 |
| `scripts/run_agent_standard_case_regression.py` | `--run-mode run-all-allowed` · `--include-extended-fixtures` | W7-T2 |
| `delivery/controlled_notify_experiment_v1.py` | W7-T3 Controlled Notify（simulated · outbox only） | W7-T3 |
| `scripts/run_controlled_delivery_notify_experiment.py` | W7-T3 CLI | W7-T3 |
| `docs/ninety-five-percent-automation-blueprint-v2.md` | 95% 藍圖 v2 · S1–S15 Wave 7 分佈 + Wave 8 缺口 | W7-T4 |
| `docs/skill-cards-v2.md` · `docs/skill-map-v2.md` | Skill Card C/D/N + run_path/notify 映射 | W7-T4 |
| `docs/agent-standard-line-governance-view-v2.md` | 治理視角 v2 · R6–R8 | W7-T4 |
| `04_Workflows/tickets/W7-T4-update-ninety-five-percent-blueprint-and-skills-wave7-v1_state.md` | W7-T4 票 state | W7-T4 |

**驗證（Wave 7 smoke）**

```bash
python -m unittest tests.test_agent_standard_case_experiment tests.test_controlled_delivery_notify_experiment_v1 -v
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --auto-approve-intake --format json
python scripts/run_agent_standard_case_regression.py --include-extended-fixtures --format json
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --include-extended-fixtures --auto-approve-intake --format json
```

- 完成度總覽：`docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 7

### 1.10 Agent Standard Line Wave 8 — Experimental Fixture Run Paths（W8-T1）

> **Track**：W7-T1 擴展 fixture 受控 run path；不改錨點案型邊界

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `scripts/run_agent_standard_case_experiment.py` | W8-T1 `_RUN_PATH_PROFILES`：additional_demo→CP-B · sandbox→cleaning_preview | W8-T1 |
| `scripts/run_agent_standard_case_regression.py` | `run-all-allowed` + `--include-extended-fixtures` · `experimental_run` summary | W8-T1 |
| `docs/agent-run-experiment-eval-guide-v1.md` §2.5 | C/D run 成功定義與 CLI | W8-T1 |
| `docs/skill-cards-v2.md` · `docs/skill-map-v2.md` | Card C/D run path 成熟度 | W8-T1 |
| `04_Workflows/tickets/W8-T1-extend-run-path-profiles-for-experimental-fixtures-v1_state.md` | W8-T1 票 state | W8-T1 |

**驗證（Wave 8 smoke）**

```bash
python -m unittest tests.test_agent_standard_case_experiment tests.test_agent_standard_case_regression -v
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --include-extended-fixtures --auto-approve-intake --format json
```

- 完成度總覽：`docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 8
- v1 基線（仍有效）：§1.8 Skill Card & Agent Standard Line

### 1.11 Non-Tabular Shadow Flow Design — Wave 8 擴展設計（W8-T4）

> **Track**：Non-Tabular 家族 Shadow Flow v1 設計，僅設計層、不觸及 Tabular 主鏈，繼承 Agent 標準線治理與 HITL 思路

| 文件 | 用途 | 票號 |
|------|------|------|
| `docs/non-tabular-shadow-flow-blueprint-v1.md` | Non-Tabular Shadow Flow 藍圖：§1 目的/範圍、§2 典型案型、§3 S1-S15 對照、§4 治理策略、§5 Skill/Module 需求、§6 Wave 9 建議票 | W8-T4 |
| `04_Workflows/tickets/W8-T4-non-tabular-shadow-flow-blueprint-v1_state.md` | W8-T4 票 state | W8-T4 |

**設計要點**

| 維度 | Tabular v2 | Non-Tabular Shadow v1 |
|------|------------|----------------------|
| **Input** | CSV / 結構化表格 | Documents, logs, images, JSON blobs |
| **Schema** | Fixed columns | Schema-free / flexible |
| **S3 Decision** | `tabular.cleaning.mvp` rules | 擴展 `non-tabular.*` family rules（設計） |
| **S5 Route** | `plan_tabular_route()` | `plan_non_tabular_route()`（設計） |
| **S7-S8** | Row cleaners | Content processors（設計） |
| **S11 Guard** | `removal_ratio` | `extraction_coverage`, `quality_score`（設計） |
| **治理** | Checkpoint A/B HITL | **沿用**相同 HITL 模式 |

**Wave 9 規劃銜接**

見藍圖 §6：9 張票（W9-T1~T9）涵蓋 routing catalog 擴展、decision rules v2、tool catalog、glue layer、fixtures、orchestrator preview。

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| **W9-T2-non-tabular-decision-rules-v1** | **implementer done · Reviewer pending** | v2 擴展 `non_tabular.*` · NT-A/NT-B profile · conservative `needs_review` · R-NT1 reject · Tabular 不變 |
| **W9-T3-non-tabular-tool-catalog-and-selector-stub-v1** | **implementer done · Reviewer pending** | `non_tabular_tool_catalog_v1.json` · `select_non_tabular_tools` stub · symbolic `planned_tools` only |

- 上游缺口：`docs/ninety-five-percent-automation-blueprint-v2.md` §6 G8-5
- 完成度總覽：`docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 9

### 1.12 Non-Tabular Routing Catalog — Wave 9（W9-T1）

> **Track**：Non-Tabular 家族 Routing Catalog v1 結構設計，承接 W8-T4 Shadow Blueprint

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `docs/non-tabular-routing-catalog-v1.md` | Routing catalog 人讀規格：NT-A/NT-B 案型、欄位定義、Tabular 差異對照 | W9-T1 |
| `routing/non_tabular_routing_catalog_v1.yaml` | 機器 readable catalog skeleton（3 entries: NT-A, NT-B, generic） | W9-T1 |
| `04_Workflows/tickets/W9-T1-non-tabular-routing-catalog-v1_state.md` | W9-T1 票 state | W9-T1 |

**設計要點**

| 維度 | W8-T4 藍圖 | W9-T1 Catalog 結構 |
|------|------------|-------------------|
| **task_type 前綴** | `non-tabular.{domain}.{action}` | Catalog 定義 3 條目 (NT-A, NT-B, generic) |
| **routing 欄位** | 概念設計 | 正式欄位：`family`, `task_type`, `case_profile`, `intake_schema`, `target_tools` |
| **target_tools** | 概念清單 | Symbolic names only（實作在 W9-T3） |
| **與 Tabular 關係** | 對照表 | Spec §4 詳細差異對照 |

**驗證命令**

```bash
# YAML 語法檢查
python -c "import yaml; yaml.safe_load(open('routing/non_tabular_routing_catalog_v1.yaml'))"

# 檔案存在確認
ls -la docs/non-tabular-routing-catalog-v1.md
ls -la routing/non_tabular_routing_catalog_v1.yaml
ls -la 04_Workflows/tickets/W9-T1-non-tabular-routing-catalog-v1_state.md
```

### 1.13 Non-Tabular Decision Rules — Wave 9（W9-T2）

> **Track**：Non-Tabular 家族 intake decision rules v2 擴展，NT-A/NT-B profile 支援

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `routing/intake_decision_rules_v2.py` | `evaluate_intake_decision_v2` 擴展 `non_tabular.*` 分支 | W9-T2 |
| `docs/intake-decision-rules-v2.md` | §3.1 NT-A/NT-B · R-NT1 reject · `non_tabular.*` output shape | W9-T2 |
| `04_Workflows/tickets/W9-T2-non-tabular-decision-rules-v1_state.md` | W9-T2 票 state | W9-T2 |

**驗證命令**

```bash
python -m unittest tests.test_intake_decision_rules_v2 -v
python scripts/run_agent_intake_decision_demo.py --task-type non_tabular.document.extract --case-dir cases/docu-corp/2026-0001 --use-v2 --format json
```

### 1.14 Non-Tabular Tool Catalog & Selector Stub — Wave 9（W9-T3）

> **Track**：Non-Tabular shadow 工具層 symbolic stub；不執行 heavy tools、不接外部 API

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `tools/non_tabular_tool_catalog_v1.json` | NT-A / NT-B 四工具 catalog SSOT（experimental） | W9-T3 |
| `tools/non_tabular_tool_selector_v1.py` | `select_non_tabular_tools(task_type, case_profile)` → symbolic `planned_tools` | W9-T3 |
| `tests/test_non_tabular_tool_selector_v1.py` | Selector stub 單元測試 | W9-T3 |
| `04_Workflows/tickets/W9-T3-non-tabular-tool-catalog-and-selector-stub-v1_state.md` | W9-T3 票 state | W9-T3 |

**驗證命令**

```bash
python -m unittest tests.test_non_tabular_tool_selector_v1 -v
```

### 1.13 Non-Tabular Preview Orchestrator — Wave 9（W9-T4）

> **Track**：Preview-only CLI；decision v2 → glue → selector stub；sandbox outbox only

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `docs/non-tabular-orchestrator-preview-v1.md` | Preview orchestrator 用法與輸出形狀 | W9-T4 |
| `scripts/run_non_tabular_experiment_preview.py` | Non-tabular preview CLI | W9-T4 |
| `routing/intake_to_non_tabular_glue.py` | `plan_non_tabular_route()` glue planner | W9-T4 |
| `tests/test_non_tabular_orchestrator_preview_v1.py` | Preview orchestrator 單元測試 | W9-T4 |
| `04_Workflows/tickets/W9-T4-non-tabular-orchestrator-preview-v1_state.md` | W9-T4 票 state | W9-T4 |

**驗證命令**

```bash
python -m unittest tests.test_non_tabular_orchestrator_preview_v1 -v
python scripts/run_non_tabular_experiment_preview.py --task-type non_tabular.document.extract --case-dir cases/_experiment_samples/nt_docu_stub --format json
```

### 1.14 Agent Lines CI Suite — Wave 10（W10-T1）

> **Track**：可選 CI helper；合併 Tabular agent regression + Non-Tabular preview；**不**改 mainline regression  
> **Deferred 索引**（FP-G6-T3）：`docs/phase6-agent-lines-nightly-deferred-index-v1.md` — Landed vs Deferred（nightly／`run-all-allowed`）；≠ required CI／INT Tier-A

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `docs/agent-lines-ci-suite-v1.md` | CI 適用場景、安全邊界、JSON 形狀 | W10-T1 |
| `scripts/run_agent_lines_ci_suite.py` | `--scope tabular\|non_tabular\|all` 合併 CI 入口 | W10-T1 |
| `tests/test_agent_lines_ci_suite_v1.py` | CI suite unittest | W10-T1 |
| `cases/_experiment_samples/nt_docu_stub/` · `nt_log_stub/` | NT-A / NT-B safe stub fixtures | W10-T1 |
| `04_Workflows/tickets/W10-T1-integrate-agent-lines-into-ci-v1_state.md` | W10-T1 票 state | W10-T1 |

**驗證命令**

```bash
python -m unittest tests.test_agent_lines_ci_suite_v1 -v
python scripts/run_agent_lines_ci_suite.py --scope all --format json
```

### 1.15 Agent Lines Offline Metrics — Wave 10（W10-T2）

> **Track**：Read-only outbox / regression JSON metrics · CSV + JSON summary · no external monitoring

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `docs/agent-lines-metrics-and-monitoring-v1.md` | 離線指標抽取用法與 schema | W10-T2 |
| `scripts/analyze_agent_lines_metrics.py` | 掃描 regression / agent_ci / non_tabular outbox → `outbox/agent_metrics/` | W10-T2 |
| `tests/test_analyze_agent_lines_metrics_v1.py` | Fake outbox 統計單元測試 | W10-T2 |
| `04_Workflows/tickets/W10-T2-agent-lines-metrics-and-monitoring-v1_state.md` | W10-T2 票 state | W10-T2 |

**驗證命令**

```bash
python -m unittest tests.test_analyze_agent_lines_metrics_v1 -v
python scripts/analyze_agent_lines_metrics.py
python scripts/analyze_agent_lines_metrics.py --format json
```

### 1.16 Agent-Lines Audit Quickview — Wave 10（W10-T3）

> **Track**：只讀審計快查；聚合 regression / agent_ci / non-tabular artifact + checkpoint A/B

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `docs/agent-lines-audit-quickview-v1.md` | Audit quickview 用法、資料來源、輸出形狀 | W10-T3 |
| `scripts/run_agent_audit_quickview.py` | 審計快查 CLI（`--case-ref` · `--format`） | W10-T3 |
| `tests/test_agent_audit_quickview_v1.py` | 只讀 quickview 單元測試 | W10-T3 |
| `04_Workflows/tickets/W10-T3-agent-lines-audit-quickview-cli-v1_state.md` | W10-T3 票 state | W10-T3 |

**驗證命令**

```bash
python -m unittest tests.test_agent_audit_quickview_v1 -v
python scripts/run_agent_audit_quickview.py --case-ref demo_phase
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json
```

- 完成度總覽：`docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 10

### 1.17 Agent Lines README — Wave 10（W10-T4）

> **Track**：統整 Tabular Standard Line v2 + Non-Tabular Shadow Flow v1 的 README 級總覽；給未來合作者與新 Agent 的快速入口

|| 文件 / 模組 | 用途 | 票號 |
||-------------|------|------|
|| `docs/agent-and-non-tabular-lines-readme-v1.md` | README 主檔：§1 Overview、§2 Tabular v2、§3 Non-Tabular v1、§4 CI/Metrics/Audit、§5 Governance/HITL、§6 Roadmap | W10-T4 |
|| `04_Workflows/tickets/W10-T4-agent-and-non-tabular-lines-readme-v1_state.md` | W10-T4 票 state | W10-T4 |

**本文件定位**

- **非操作手冊**：不取代個別 runbook 或 `--help` 輸出
- **非技術規格**：細節參見 `docs/agent-standard-line-v1-summary.md`、`docs/non-tabular-shadow-flow-blueprint-v1.md` 等上游文件
- **是入口地圖**：幫助讀者判斷「我要用 Tabular 還是 Non-Tabular」、「CI 怎麼跑」、「governance 邊界在哪」

**快速引用**

```bash
# Tabular 快速預覽
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp --case-dir cases/demo_phase \
  --mode preview --format json

# Non-Tabular Preview
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.document.extract \
  --case-dir cases/_experiment_samples/nt_docu_stub --format json

# CI 合併驗證
python scripts/run_agent_lines_ci_suite.py --scope all --format json
```

- 完成度總覽：`docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 10

### 1.18 Controlled Experimental Fixtures — Wave 11（W11-T1）

> **Track**：C/D fixture 從純實驗升格為 `controlled_experimental` 受控準正式線；不改 demo_phase / sampleco 錨點行為

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `scripts/run_agent_standard_case_experiment.py` | C/D `run_path_profile` · `fixture_maturity` · `regression_bundle_probe` | W11-T1 |
| `scripts/run_agent_standard_case_regression.py` | `controlled_experimental_run` summary · `guard_sanity` · extended run-all-allowed | W11-T1 |
| `docs/skill-cards-v2.md` · `docs/skill-map-v2.md` | C/D maturity → `controlled_experimental` | W11-T1 |
| `docs/ninety-five-percent-automation-blueprint-v2.md` | run coverage 註記（不計入 95% 達標） | W11-T1 |
| `tests/test_agent_standard_case_experiment.py` · `tests/test_agent_standard_case_regression.py` | C/D run path + regression summary | W11-T1 |
| `04_Workflows/tickets/W11-T1-promote-experimental-tabular-fixtures-to-controlled-line-v1_state.md` | W11-T1 票 state | W11-T1 |

**Run path 摘要（W11-T1）**

| case_ref | stop_at | maturity | W11-T1 增量 |
|----------|---------|----------|------------|
| `demo_phase` | bundle | stable | 不變 |
| `sampleco/2026-0001` | checkpoint_b | stable | 不變 |
| `additional_demo` | checkpoint_b | controlled_experimental | cleaning+outbox · regression `bundle_probe` |
| `sandbox_client` | cleaning_preview | controlled_experimental | gate+clean · live guard · CP-B 不評估 |

**驗證命令**

```bash
python -m unittest tests.test_agent_standard_case_experiment tests.test_agent_standard_case_regression -v
python scripts/run_agent_standard_case_regression.py \
  --run-mode run-all-allowed --include-extended-fixtures --auto-approve-intake --format json
```

### 1.19 Non-Tabular Lightweight Content Checks — Wave 11（W11-T2）

> **Track**：Non-Tabular shadow preview 的 metadata-only 案型目錄掃描；不讀內容、不跑 OCR / log parser

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `tools/non_tabular_lightweight_inspector_v1.py` | `inspect_non_tabular_case_dir()` — ext/size/pattern stats | W11-T2 |
| `scripts/run_non_tabular_experiment_preview.py` | Preview 輸出 `content_summary`（S4_lite） | W11-T2 |
| `docs/non-tabular-orchestrator-preview-v1.md` | §3.2 `content_summary` 欄位說明 | W11-T2 |
| `tests/test_non_tabular_lightweight_inspector_v1.py` | Inspector 單元測試 | W11-T2 |
| `tests/test_non_tabular_orchestrator_preview_v1.py` | Preview + content_summary 整合測試 | W11-T2 |
| `04_Workflows/tickets/W11-T2-non-tabular-lightweight-content-checks-v1_state.md` | W11-T2 票 state | W11-T2 |

**驗證命令**

```bash
python -m unittest tests.test_non_tabular_lightweight_inspector_v1 tests.test_non_tabular_orchestrator_preview_v1 -v
```

### 1.20 Agent Lines Monthly Report — Wave 11（W11-T3）

> **Track**：離線月度 Markdown 報表 · 僅讀 `metrics_summary.json` · 不連外部服務

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `docs/agent-lines-metrics-and-monitoring-v1.md` §8 | 月度報表用法與聚合語意 | W11-T3 |
| `scripts/generate_agent_lines_monthly_report.py` | `metrics_summary.json` → `monthly_report_YYYY-MM.md` | W11-T3 |
| `tests/test_generate_agent_lines_monthly_report_v1.py` | Fake summary 驗證 Markdown 輸出 | W11-T3 |
| `04_Workflows/tickets/W11-T3-agent-lines-monthly-metrics-report-v1_state.md` | W11-T3 票 state | W11-T3 |

**驗證命令**

```bash
python -m unittest tests.test_generate_agent_lines_monthly_report_v1 -v
python scripts/analyze_agent_lines_metrics.py
python scripts/generate_agent_lines_monthly_report.py
python scripts/generate_agent_lines_monthly_report.py --month 2026-06
```

- 完成度總覽：`docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 11

### 1.20a Sandbox End-to-End Controlled Delivery — Wave 12（W12-T1）

> **Track**：`additional_demo` 受控真實交付線 · sandbox bundle 僅落 `outbox/sandbox_delivery/` · 不改 demo/sampleco

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md` | Allowlist · run_path · 與 production 差異 · 可觀察指標 | W12-T1 |
| `delivery/sandbox_delivery_bundle_v1.py` | Sandbox manifest 寫入 · CP-B gate helper | W12-T1 |
| `scripts/run_agent_standard_case_experiment.py` | `--sandbox-end-to-end` · `end_to_end_sandbox` profile | W12-T1 |
| `scripts/run_agent_audit_quickview.py` | `sandbox_delivery` audit 區塊 | W12-T1 |
| `tests/test_sandbox_delivery_bundle_v1.py` · `tests/test_agent_standard_case_experiment.py` | Allowlist · e2e bundle · anchor 不變 | W12-T1 |
| `04_Workflows/tickets/W12-T1-tabular-controlled-end-to-end-delivery-sandbox-v1_state.md` | W12-T1 票 state | W12-T1 |

**驗證命令**

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp --case-dir cases/additional_demo \
  --mode run --auto-approve-intake --sandbox-end-to-end --format json
python -m unittest tests.test_sandbox_delivery_bundle_v1 tests.test_agent_standard_case_experiment -v
python scripts/run_agent_audit_quickview.py --case-ref additional_demo --format json
```

### 1.20b Fixture Maturity Metrics & CI — Wave 12（W12-T2）

> **Track**：Tabular fixture maturity tier 聚合 · metrics / CI / monthly report · 向後兼容 W10-T2 schema

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| `scripts/analyze_agent_lines_metrics.py` | `by_fixture_maturity` + per-run `fixture_maturity` | W12-T2 |
| `scripts/run_agent_lines_ci_suite.py` | Tabular case `fixture_maturity` + text tier rollup | W12-T2 |
| `scripts/generate_agent_lines_monthly_report.py` | Monthly tier 表格 | W12-T2 |
| `docs/agent-lines-metrics-and-monitoring-v1.md` §8 | Fixture maturity 語意與 fallback | W12-T2 |
| `docs/agent-lines-ci-suite-v1.md` | CI summary maturity 欄位 | W12-T2 |
| `tests/test_analyze_agent_lines_metrics_v1.py` | Metrics tier 單元測試 | W12-T2 |
| `tests/test_agent_lines_ci_suite_v1.py` | CI maturity 單元測試 | W12-T2 |
| `tests/test_generate_agent_lines_monthly_report_v1.py` | Monthly tier 表格測試 | W12-T2 |
| `04_Workflows/tickets/W12-T2-tabular-fixture-maturity-aware-metrics-and-ci-v1_state.md` | W12-T2 票 state | W12-T2 |

**驗證命令**

```bash
python -m unittest tests.test_analyze_agent_lines_metrics_v1 tests.test_agent_lines_ci_suite_v1 tests.test_generate_agent_lines_monthly_report_v1 -v
python scripts/analyze_agent_lines_metrics.py --format text
python scripts/run_agent_lines_ci_suite.py --scope tabular
```

### 1.21 Agent Lines README v2 — Wave 11（W11-T4）

> **Track**：在 v1 README 基礎上，更新整體說明到 Wave 10 對齊狀態；納入 W10-T1 CI suite、W10-T2 metrics、W10-T3 audit；為 Wave 11+ 留出 future work 區

|| 文件 / 模組 | 用途 | 票號 |
||-------------|------|------|
|| `docs/agent-and-non-tabular-lines-readme-v2.md` | README v2：§1 Overview（系統現狀一句話摘要）、§2 Tabular v2（multi-fixture/run/HITL）、§3 Non-Tabular v1（routing/decision/tool selector/preview）、§4 CI/Metrics/Audit（W10-T1/T2/T3）、§5 Governance/HITL、§6 Roadmap（Wave 11+ 方向）| W11-T4 |
|| `04_Workflows/tickets/W11-T4-agent-and-non-tabular-lines-readme-v2_state.md` | W11-T4 票 state | W11-T4 |

**v2 相對 v1 主要更新**

| 更新項 | 說明 |
|--------|------|
| 系統現狀一句話摘要 | 新增頂部快速摘要段落 |
| Wave 10 CI Suite | §4.1 完整 CLI、產出、邊界說明 |
| Wave 10 Metrics | §4.2 指標清單、schema、輸出檔案 |
| Wave 10 Audit | §4.3 CLI、JSON shape、範例 |
| 典型開發者流程 | §4.4 新增 PR → CI → Metrics → Audit 流程圖 |
| Wave 11+ Roadmap | §6 結構化表格 + 藍圖引用 |
| 保留 v1 | `docs/agent-and-non-tabular-lines-readme-v1.md` 不覆蓋 |

**驗證命令**

```bash
# 文件存在檢查
ls -la docs/agent-and-non-tabular-lines-readme-v2.md
ls -la 04_Workflows/tickets/W11-T4-agent-and-non-tabular-lines-readme-v2_state.md

# 章節完整性檢查
grep "^## §" docs/agent-and-non-tabular-lines-readme-v2.md | wc -l
# 預期輸出: 6

# Wave 10 內容覆蓋檢查
grep -c "W10-T1\|W10-T2\|W10-T3\|Wave 10" docs/agent-and-non-tabular-lines-readme-v2.md
```

- 完成度總覽：`docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 11

### 1.24 Phase 2 / Knowledge Layer — Indexing Contract（Wave A · WA-T1）

- **收录契约 SSOT**：`docs/phase2-knowledge-indexing-contract-v1.md` — indexed / catalogued / excluded 三态；`document_chunks` / `repo_chunks` 双 pipeline 边界；metadata v0.1；Wave/Phase 标注；登记流程（WORKFLOW_INDEX 优先于 docs/index）
- **实现细节**：`docs/knowledge-layer.md` — PG+Qdrant 主方案、ingest/retrieve CLI、payload 映射
- **Gap 审计（Full-Phase G2 · FP-G2-T2 · 审计 ≠ 已修复）**：`docs/phase2-index-contract-gap-audit-v1.md` — WA-T1 vs 实际能力；建议票 T1／T3／T4／T5
- **Index job hook（Full-Phase G2 · FP-G2-T1 · skeleton ≠ 生产 cron）**：`docs/phase2-index-job-hook-v1.md` — dry-run CLI `scripts/run_index_job_hook_v1.py`
- **RAG E2E 问答 FRAME（Full-Phase G2 · FP-G2-T3 · planning ≠ E2E 已验收）**：`docs/phase2-rag-e2e-answer-frame-v1.md` — MVP/stretch · GAP-E2E · non_claims
- **graphrag_jobs 状态机（Full-Phase G2 · FP-G2-T4 · 设计 doc ≠ GraphRAG 主路）**：`docs/phase2-graphrag-jobs-state-machine-v1.md` — queued／running／succeeded／failed · GAP-GRAPH
  - **thin runner（P2-GRAPHRAG-THIN-RUNNER-v1 · fixture MVP · ≠ 正式 smoke）**：`docs/phase2-graphrag-thin-runner-v1.md` · 見 §2.1 R4 修正
- **Legacy 户籍化（catalogued · ≠ Qdrant）**：`04_Workflows/_indexing_and_audit.py` → `metadata_index.json`
- **Repo index 试点（catalogued / experimental）**：`workflow_v2/20_pilot/W3-B/` · `W3-B_index_pipeline_runbook.md`
- **验证**：
  - `python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 -v`
- **票 state**：`04_Workflows/tickets/WA-T1-phase2-knowledge-indexing-contract-v1_state.md` · `04_Workflows/tickets/FP-G2-T2-phase2-index-contract-gap-audit-v1_state.md`

| phase_tag | wave_tag | content_class | index_tier | path |
|-----------|----------|---------------|------------|------|
| P2 | WA | spec | A | `docs/phase2-knowledge-indexing-contract-v1.md` |

---

### 1.25 Phase 6 — INT-REGRESSION-GATE Contract（Wave A · WA-T6）

> **Track**：Phase 6 自动化测试 / regression gate SSOT；Tier-A/B/ALL 与 PR smoke / eval-gate / agent-lines 分工

| 文件 | 用途 | 票号 |
|------|------|------|
| **`docs/phase6-int-regression-gate-contract-v1.md`** | **INT gate SSOT** — 过 gate 命令、Tier 表、CI 矩阵、失败诊断、runbook §8 | **WA-T6** |
| `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md` | Implementation 附录 — 逐测试不变量、JSON 示例 | INT-REGRESSION-GATE |
| `04_Workflows/_wave7_regression_gate.py` | CLI 聚合入口（`Master_Map` → `runners.wave7_regression_gate`） | INT-REGRESSION-GATE |
| `docs/testing.md` | Phase 6 开发者入口 — 金字塔 §1、entry points §3 | W2-T1 / WA-T6 |
| `tests/test_phase6_int_regression_gate_contract_v1.py` | Contract 结构 + CLI `--help` smoke | WA-T6 |
| `04_Workflows/tickets/WA-T6-phase6-int-regression-gate-runbook-and-ci-integration-v1_state.md` | WA-T6 票 state | WA-T6 |

**Authoritative 过 INT Tier-A gate**

```bash
python 04_Workflows/_wave7_regression_gate.py --tier A
# stdout JSON ok: true · exit 0
```

**验证命令**

```bash
python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v
python 04_Workflows/_wave7_regression_gate.py --help
# 可选（需 gov_core venv）：
python 04_Workflows/_wave7_regression_gate.py --tier A --pretty
```

- 完成度：`docs/WAVE_A_EXECUTION_PLAN.md` — P6 **72%→90%**（WB-T4 附录 A smoke matrix）
- 交叉引用：`04_Workflows/WAVE7_RUNBOOK_CLI_AND_QA_v0.1.md` §7 · `WAVE7_CLEAN_RUNNER_ORCH_OVERVIEW_v0.1.md` §6

---

### 1.23 Wave 1–12 Architecture Retrospective — Wave 12（W12-T4）

> **Track**：高層架構演進回顧；紀錄從「手動流程」到「多 fixture Agent 線 + Non-tabular shadow + CI/Metrics/Audit」的完整演變

| 文件 | 用途 | 票號 |
|------|------|------|
| `docs/wave1-to-wave12-architecture-retrospective-v1.md` | 架構回顧主文件：§1 Timeline、§2 Tabular 演進、§3 Non-Tabular 演進、§4 Governance/CI/Metrics 演進、§5 設計原則、§6 未來風險 | W12-T4 |
| `04_Workflows/tickets/W12-T4-wave1-to-wave12-architecture-retrospective-v1_state.md` | W12-T4 票 state | W12-T4 |

**文件結構**

| 章節 | 內容 |
|------|------|
| §1 | Wave 1–12 Timeline Overview（每 Wave 一行摘要） |
| §2 | Tabular 線演進（MVP → v1 → v2 → controlled E2E） |
| §3 | Non-Tabular 線演進（blueprint → shadow → metadata → first step） |
| §4 | Governance/HITL/Eval/CI/Metrics/Audit 演進 |
| §5 | 核心設計原則（incremental/outbox/fixture sandbox/dict 契約） |
| §6 | 未來風險與建議（Fixture 組合爆炸/Heavy tools 資源/CI 時間/Decision drift/資料累積） |

**驗證命令**

```bash
# 文件存在檢查
ls -la docs/wave1-to-wave12-architecture-retrospective-v1.md
ls -la 04_Workflows/tickets/W12-T4-wave1-to-wave12-architecture-retrospective-v1_state.md

# 章節完整性檢查
grep "^## §" docs/wave1-to-wave12-architecture-retrospective-v1.md | wc -l
# 預期輸出: 7

# Timeline 行數檢查
grep "^| W" docs/wave1-to-wave12-architecture-retrospective-v1.md | wc -l
# 預期: 12
```

- 完成度總覽：`docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 12

---

### 1.26 Wave B Toolchain — Bottom Layer Contract & Readme（WB-T6）

> **Track**：Toolchain Wave B（`WB-T*`）底層 contract 收口 · 与 Observability `WAVE-B-P*`、Tabular `W3-TL-*` **分轨**

| 文件 | 用途 | 票号 |
|------|------|------|
| **`docs/wave-b-toolchain-readme-v1.md`** | **快速入口** — 系统现状、开发者流程、Wave C 可假设能力、上位契约 | **WB-T6** |
| **`docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md`** | WB-T1–T8 票表、依赖图、验证命令、Wave C 稳定能力索引 | **WB-T6** |
| `docs/tool-catalog-and-selector-contract-v1.md` | Catalog + Selector SSOT | WB-T1 |
| `docs/tool-executor-and-sandbox-safety-contract-v1.md` | Executor + Sandbox SSOT | WB-T2 |
| `docs/outbox-and-feedback-layer-contract-v1.md` | Outbox + Feedback SSOT | WB-T3 |
| `docs/toolchain-health-dashboard-v1.md` | Toolchain health dashboard spec | WB-T4 |
| `docs/audit-quickview-and-case-history-spec-v1.md` | Audit quickview + case history join spec | WB-T5 |
| `routing/toolchain_smoke_matrix_v1.yaml` | P6 toolchain optional smoke matrix SSOT | WB-T7 |
| `04_Workflows/tickets/WB-T8-toolchain-wave-b-review-and-progress-closure-v1_state.md` | Toolchain Wave B review-and-progress closure handoff | WB-T8 |
| `04_Workflows/tickets/WC-PRE-01-wave-b-doc-hygiene-and-closure-index-v1_state.md` | Wave C PRE · Wave B doc/索引 hygiene（WC-PRE-01） | WC-PRE-01 |
| `04_Workflows/tickets/WB-T6-wave-b-bottom-layer-readme-and-phase-progress-alignment-v1_state.md` | WB-T6 票 state | WB-T6 |

**命名空间对照**

| 轴 | 票前缀 | 入口 |
|----|--------|------|
| Observability Wave B | `WAVE-B-P*` | `docs/WAVE_B_EXECUTION_PLAN.md` |
| **Toolchain Wave B** | **`WB-T*`** | 本节 · `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` |
| Tabular Tool Layer | `W3-TL-*` | §1.5 Tabular 附录 |

**验证命令（Toolchain 汇总）**

```bash
python -m unittest tests.test_tool_catalog_and_selector_contract_v1 tests.test_tool_executor_and_sandbox_contract_v1 tests.test_outbox_and_feedback_layer_contract_v1 tests.test_toolchain_health_dashboard_v1 -v
python scripts/run_toolchain_health_dashboard.py --format json --dry-run
```

- Phase% SSOT：`docs/WAVE_PROGRESS_DASHBOARD.md` §Phase 完成度表
- Wave C 对照（唯读）：`docs/WAVE_C_EXECUTION_PLAN.md`
- 票务索引：`04_Workflows/tickets/README.md` §Wave B Toolchain · §Wave C PRE

> **注**：票面原指定 §1.21；§1.21 已分配给 W11-T4 Agent Lines README v2，故本索引登錄为 **§1.26**。

---

### 1.27 Toolchain Local Gaps Quickview — Wave C C1（WC-C1-01）

> **Track**：Toolchain local gaps quickview · **Wave C C1 核心票** · developer-facing 只讀聚合；**local only · optional · non-gating**

| 文件 / 模組 | 用途 | 票號 |
|-------------|------|------|
| **`docs/toolchain-local-gaps-quickview-v1.md`** | Gaps quickview CLI、schema、`toolchain_local_gaps_v1` 區塊表、Must-Not-Assume（PROD/CI） | **WC-C1-01** |
| `scripts/run_toolchain_local_gaps_quickview.py` | 本地 gaps 聚合 CLI（selector plan_only · executor timeout · audit investigation · smoke matrix dry-run · 可選 health embed） | WC-C1-01 |
| `tests/test_toolchain_local_gaps_quickview_v1.py` | Quickview unittest（17 tests） | WC-C1-01 |
| `04_Workflows/tickets/WC-C1-01-toolchain-local-gaps-quickview-v1_state.md` | WC-C1-01 票 state | WC-C1-01 |

**依賴**：Wave B（WB-T1～T8 contracts/runtime）· **WC-PRE-02～05**（selector `plan_only` · executor timeout · audit investigation CLI · smoke matrix local runner）

**性質**：**local only** · **optional** · **non-gating** — 頂層 `gate_class=optional` · `blocks_mainline=false`；**不得**當 PR required / CI gate；`OG-TOOLCHAIN-HEALTH` required 與 mandatory smoke CI 仍 **blocked** 於 WC-PRE-06/07 批文後治理票。

**驗證命令**

```bash
python -m unittest tests.test_toolchain_local_gaps_quickview_v1 -v
python scripts/run_toolchain_local_gaps_quickview.py --format json
python scripts/run_toolchain_local_gaps_quickview.py --case-ref demo_phase --format json
```

- 交叉引用：`docs/toolchain-health-dashboard-v1.md`（WB-T4）· `04_Workflows/tickets/README.md` §Wave C C1 · §Wave C PRE
- 票務狀態：**accepted_with_gaps**（owner: orchestrator）

---

## 2. 預留／部分落地工作流

以下工作流尚無**正式專用 smoke runbook**，或僅有 thin／fixture 入口。  
**R4（2026-07-15）**：勿把「尚無正式專用 runbook」讀成「上游依賴不存在」——見 `docs/p1-index-r4-false-neg-doc-v1.md`。

### 2.1 GraphRAG Job Smoke Test（正式 runbook 預留 · thin 已有）

- 目標（草案）：
  - 驗證 GraphRAG job 能對一小批文件建圖、完成任務、輸出基礎圖統計，並支援一個最小的圖上 query。
- 狀態（R4 假陰性修正 · 票 `P1-INDEX-R4-FALSE-NEG-DOC-v1`）：
  - **RAG_Smoke_Test v0.1 已落地**（舊「待 RAG 穩定後另立」為假陰性）→ §1.2 · `04_Workflows/runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md`
  - **GraphRAG 本地 thin runner**（≠ 正式 GraphRAG Job Smoke runbook · ≠ primary retrieval）→ `docs/phase2-graphrag-thin-runner-v1.md` · CLI `scripts/run_p2_graphrag_thin_runner_v1.py` · 票 `P2-GRAPHRAG-THIN-RUNNER-v1`
  - **仍預留**：完整 GraphRAG Job Smoke runbook（建圖＋圖上 query 戰報）尚未立；本節不再宣稱 RAG 未就緒。

### 2.2 DarkOps Minimal Task Smoke Test（預留）

- 目標（草案）：
  - 在有限解禁的前提下，為暗部設計一個極小的、風險可控的任務驗證流程。
- 狀態：
  - **Blocked**：目前依憲法，DarkOps 為 Blocked；待尚書省明確解禁與 runbook 設計後再啟用。

---

## 3. 如何使用這份索引（給 Agent / 人類）

### 3.1 接戰（推薦 · 三層模型）

1. **Tier 1 — 一條 CLI**（必跑）：
   ```powershell
   python 04_Workflows/_boot_context.py --text "<尚書省指令>" --pretty
   ```
2. 依 JSON **`read_plan`** 讀檔；依 **`skip`** 跳過全文制度檔。
3. 若 `workflow_index_hint.sections` 有值 → **只讀本檔對應 §1.x 節**（例：§1.7 Tabular MVP）。
4. `progress_tail` 已含 Progress 末段 → **勿通讀** `00_Agent_Work_Progress.md`。

### 3.2 深入某條工作流時

1. 在 §1 找到對應小節 → 打開該節列出的 runbook：
   - Gov Core V1 → `04_Workflows/runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md`（§1.1）
   - RAG → `04_Workflows/runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md`（§1.2）
   - 治理入口 → `docs/GOVERNANCE_ONBOARDING_v1.md`（§1.5）
   - Phase 5 probe／`task_runs` 鎖 → `05_Data_Vault/README.md`（§1.3）
2. 戰史：boot `progress_tail` 或 grep Progress 日期；里程碑查 `project_status/master_status.md` 最近段。

### 3.3 治理／制度票（Tier 4）

觸及憲法、合約、部門地圖、實例錨點全文時，boot 對 `hq.governance` 等會自動升級 `read_plan`；仍**不必**通讀本索引全文。

---

## 4. 更新規則（v0.1）

- 當以下任一情況發生時，需更新本索引：
  - 新增一條正式 runbook。
  - 既有工作流的主要入口 / 路徑 / 命名發生變更。
  - 某條 smoke test 被宣告 deprecated 或被新版本取代。
- 更新流程建議：
  - 先在 `00_Agent_Work_Progress.md` 中記錄變更背景。
  - 再同步更新：
    - 本檔 `WORKFLOW_INDEX.md`
    - 對應 runbook
    - `00_Agent_Work_Conditions.md`（如涉及驗收標準）
- 版本命名：
  - 索引本身以 `v0.x` 管理；runbook 以各自版本管理（如 `GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1`）。
