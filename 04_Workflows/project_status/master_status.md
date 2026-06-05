# Master Status — 大唐三省六部

## 2026-05-14 — ingest_verify 成功（smoke_corpus）

- Milestone：四大板塊第一版完成
- Command：`'D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Scripts\python.exe' 'D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Departments\04_Infrastructure\agents\orchestrator_agent.py' ingest_verify 'D:\大唐三省六部\02_Data\smoke_corpus'`
- Summary：
  - health.ok = True, all_ok = True
  - ingest.ok = True（files_total=3, files_ok=2, files_skipped=1）
  - verify.ok = True, message = "verify_ok"

## 2026-05-15 — V1 Baseline 封版完成

- **Milestone**：V1 Baseline 封版完成
- **Final status**：全鏈路第一版 + live API 接通，驗收完成
- **Scope**：
  - LangGraph orchestration（`ask` / `ingest_verify`）
  - GraphRAG backend / job flow
  - PostgreSQL / Qdrant integration
  - Langfuse observability
  - UI workbench（`gov-core-workbench.html`）
  - FastAPI facade：`GET /healthz`、`POST /api/ask`、`POST /api/ingest-verify`、`POST /api/graphrag/run`
- **Acceptance**：
  - API 契約與 JSON shape 已驗證
  - Workbench live mode 已對接
  - E2E 驗收已完成
- **Hardening completed**：
  - **ENV-1** completed（`.env.example`、`requirements.txt`、`env-readiness-checklist.md`）
  - **DEPLOY-1** completed（`deployment-guide.md`、`run-local-api.ps1` / `run-local-api.bat`、README 啟動說明）
  - **SEC-1** completed（`app_api.py` 可設定 CORS、`security-notes.md`、`.env.example` 與 README 安全說明）
  - **OPS-1** completed（`smoke-test.py`、`smoke-test.ps1`、`ops-checklist.md`、README smoke test 說明）
- **Baseline rule**：
  - 自此版本起，**V1 視為封版完成**。
  - 後續新增需求、產品化能力、部署強化、安全擴展、監控深化，一律歸類為 **V2** 或 **部署／維運專案**，不再回溯計入 V1 缺口。

## 2026-05-17 — Phase 2 工程規則轉制完成

- **Milestone**：Phase 2B — Cursor / Agent 執行規則轉制
- **Deliverables**：
  - `04_Workflows/CURSOR_AGENT_RULES.md`（人類可讀母本）
  - `.cursor/rules/engineering-contract.mdc`（`alwaysApply: true`，82 規則段 — 2026-05-19 定稿）
- **Scope**：自 `ENGINEERING_CONTRACT.md` 條文化；覆蓋四流派、12-rule、禁止項、DoD、停工、Work Report
- **Freeze**：`2026-05-17T09:30:38Z`；`Master_Map` v2.61；指紋 `newly_inserted={governance_doc:4}`，`registry_total_rows=36468`
- **Pending**：尚書省裁決定稿；Telegram lock 仍缺席（接戰時 `Start-TelegramListener.ps1`）

## 2026-05-19 — HQ Phase 1 治理三件套定稿

- **Milestone**：Phase 1 定稿（W0–W5 + W4 盲測 10/10）
- **令檔**：`04_Workflows/project_status/HQ_PHASE1_FINALIZATION_ORDER.md`
- **定稿權威**：
  - `HARNESS_CONSTITUTION.md`
  - `ENGINEERING_CONTRACT.md`
  - `DEPARTMENT_MAP.md`
  - `INSTANCE_ANCHOR_TANG.md`
- **退役**：`HARNESS_Constitution_v0.1.md`、`ENGINEERING_CONTRACT_v0.1.md`（SUPERSEDED）
- **同步**：`AGENTS.md` §初始化校準；Conditions HQ 實例段 → W5 引用
- **Phase 2**：已定稿（見下方 2026-05-19 Phase 2 令）

## 2026-05-19 — HQ Phase 2 執行規則定稿

- **Milestone**：Phase 2 定稿（P2-M + P2-C，對齊 W2）
- **令檔**：`04_Workflows/project_status/HQ_PHASE2_FINALIZATION_ORDER.md`
- **定稿權威**：
  - `04_Workflows/CURSOR_AGENT_RULES.md`（P2-M）
  - `.cursor/rules/engineering-contract.mdc`（P2-C，`alwaysApply: true`，**82** 規則段）
- **修補**：FLOW-6.5 四流派 DoD；FLOW-6.9 暗部協作順序；P2-M↔P2-C **8/8** 一致
- **指紋**：`registry_total_rows=36473`（HQ-P2-RULES-FINALIZE）
- **語義**：規則升格已生效；**暗部 DarkOps 未解禁**
- **Rules 面板抽測**：**Completed**（`HQ-P2-RULES-PANEL-VERIFICATION`，`2026-05-19T04:16:00`）

## 2026-05-19 — HQ-P3-TASK-ROUTING（Phase 3）

- **Ticket**：`HQ-P3-TASK-ROUTING`
- **Status**：**Completed**
- **Completed at**：`2026-05-19T03:41:00`
- **Milestone**：Phase 3 多智能體任務路由
- **Deliverables**：`TASK_ROUTING.md`、`task_routing_table.json`、`02_Agents_Core/task_routing.py`、`_route_task.py`
- **Evidence**：`test_task_routing.py` **6/6 OK**；見 Progress 與 `HQ_P3_TASK_ROUTING_REPORT.md`
- **Master_Map**：version **2.62**

## 2026-05-19 — HQ-P4-OPS-CYCLE（Phase 4）

- **Ticket**：`HQ-P4-OPS-CYCLE`
- **Status**：**Completed**
- **Completed at**：`2026-05-19T03:44:00`
- **Milestone**：Phase 4 營運週期（戰報／封存／回顧）
- **Deliverables**：`OPS_CYCLE.md`、`ops_cycle_schema.json`、`02_Agents_Core/ops_cycle.py`、`_ops_cycle.py`
- **Evidence**：`test_ops_cycle.py` **8/8 OK**；見 Progress 與 `HQ_P4_OPS_CYCLE_REPORT.md`
- **Master_Map**：version **2.63**

## 2026-05-19 — HQ-P2-RULES-PANEL-VERIFICATION

- **Ticket**：`HQ-P2-RULES-PANEL-VERIFICATION`
- **Status**：**Completed**
- **Completed at**：`2026-05-19T04:16:00`
- **Summary**：Rules 面板抽測 **4/4 PASS**；`engineering-contract.mdc` **82** 段、`alwaysApply: true`
- **Evidence**：見 Progress「Rules 面板抽測」；對齊 `HQ_PHASE2_FINALIZATION_ORDER.md` §七

---

## HQ 工單登錄（Phase 2–4 · 2026-05-19）

| Ticket | Status | Completed at |
|--------|--------|--------------|
| `HQ-P2-RULES-FINALIZE` | Completed | 2026-05-19（見上方 Phase 2 定稿條目） |
| `HQ-P2-RULES-PANEL-VERIFICATION` | Completed | `2026-05-19T04:16:00` |
| `HQ-P3-TASK-ROUTING` | Completed | `2026-05-19T03:41:00` |
| `HQ-P4-OPS-CYCLE` | Completed | `2026-05-19T03:44:00` |

## 2026-05-19 — gov_core_system · Wave 1 Monitoring + Alert v1（dev-ready 封板）

- **Scope**：`gov_core_system` Observability V2 · Wave 1 — Monitoring schema／ingest、六條 `/monitoring/*`、Alert + Budget evaluator、dashboard budget 狀態
- **Status**：**dev-ready · Monitoring + Alert v1 文件封板完成**（Chat A / B / HQ Reviewer 驗收寫回）
- **Not claimed**：**production-ready**；全系統 **Completed** 不適用本條
- **Role**：
  - 為 **Phase 3 / Phase 5** 提供可觀測真底座（task／step runs、monitoring API、dashboard）
  - 為 **Phase 3.5 / Phase 7** 成本、usage、歸因治理之前置里程碑
- **Evidence**：migration 005／006／004 已套用；五表齊備；`wave1_monitoring_acceptance.ps1` exit 0；`/healthz` + 六 monitoring 入口 + dashboard HTTP 200；受控 `daily_cost_usd` critical 告警可見且無 unresolved `smoke_probe`
- **Thresholds v1**（seed = 正式基準，調整須新工單）：`daily_cost_usd` 40/50 · `error_rate_15m` 0.10/0.15 · `dlq_backlog` 5/10
- **Deferred**：
  - Langfuse usage／成本欄位覆蓋 → 後續治理
  - `daily_cost_usd` 雙資料源（evaluator：`daily_cost_summary` vs overview：`task_runs` SUM）→ **下一波治理工單**，本輪不統一
- **Wave 2**：HQ 判定 **Wave 2 可開工**；**不等於** Wave 2 已交付或成本線就緒
- **Detail**：`04_Workflows/00_Agent_Work_Progress.md` →「Wave 1 封板戰報：Monitoring + Alert v1（dev-ready）」

## 2026-05-19 — Wave 2 · 成本 / usage 實測 v1（partial · 低樣本 · Chat C 寫回）

- **Ticket / 線別**：Wave 2 — Cost Story（Chat A ingest 補齊 + Chat B 成本視圖 + Chat C Phase 複核）
- **Status**：**partial** — Chat C 文件／實測寫回完成；**成本線未就緒**；待 Chat A/B 收斂
- **Scope**：成本覆蓋率、分布、Phase 3.5／7 對照；**僅文件**（Chat C 未改程式）
- **Coverage（實測 · 粗略）**：
  - `task_runs`（7d／30d）：**~0%** 具 `total_cost_usd > 0`；合計 **~$0**
  - Langfuse 樣本 n=50：**100%** 缺 `usage`；治理 metadata 大量缺失
  - 有意義成本觀測區間：**約 0%–10%**（欄位多為 0 填充）
- **Distribution**：現樣本僅 **`mode=ask`**、**`department=dark_ops`**；帳面 **~$55/30d** 來自 **`daily_cost_summary` smoke 列**，非 task 流量
- **Dual-source（延續 Wave 1）**：同日 DCS **$0（task_count=2）** 與 **$55（task_count=0）** 並存；overview **$0** vs cost-trend **$55** 分歧 → **治理工單未關**
- **Phase 3.5**：**partial** — 底座 dev-ready（Wave 1）、資料未就緒；**成本觀測未達決策級**
- **Phase 7**：**partial** — 優先靶區已列（①–④），**均未達決策級／未收斂**
- **Blocked / Next**：Chat A backfill 報表入檔；Chat B `kpis.cost` 驗收；雙資料源單獨工單；Wave 3 錯誤路徑 cost 標記
- **Detail**：`04_Workflows/00_Agent_Work_Progress.md` →「### Wave 2 – 成本 / usage 實測小結（partial · 低樣本 · 僅文件複核）」

## 2026-05-19 — Wave 3 · Error Handling & Auto-Recovery v1（Chat A–D 文件封板）

- **Scope**：`gov_core_system` — Error Taxonomy（Chat A）、DLQ + Retry Policy v1 enriched（Chat B）、Auto-Recovery hook（Chat C）、HQ Error Playbook 寫回（Chat D）
- **Status**：**dev-ready · partial · 文件封板**（程式與測試基線在庫；**預設旗標 off**；staging soak 未完成）
- **Runtime**：預設 **無** retry／DLQ 持久化／auto-recovery；見下方 Flags。
- **Role**：
  - **Phase 3 · 錯誤觀測 slice**：觀測分類就緒（`error_category` 入 monitoring metadata）；路由自動派工**未**接線（**與** `HQ-P3-TASK-ROUTING` **Completed** 之「路由 CLI」**不同條線**）
  - **Phase 5**：**dev-ready · partial** — DLQ 審計欄位 + taxonomy 對齊；手動 `POST /api/dlq/retry/{task_id}` 沿用 Phase 7 契約；真機 DLQ 200／409 待 `GOV_CORE_DLQ_ENABLED=true` + 失敗種子
  - **Phase 7**：**partial** — `dlq_backlog`／`error_rate_15m` 可告警；錯誤路徑成本治理 **deferred**
- **Taxonomy v1**：`system_error` · `llm_error` · `validation_error` · `config_error` · `unknown`
- **Flags（預設 off）**：`GOV_CORE_RETRY_POLICY_ENABLED` · `GOV_CORE_DLQ_ENABLED` · `GOV_CORE_AUTO_RECOVERY_ENABLED`；Wave 4a `GOV_CORE_DLQ_AUTO_RETRY_ENABLED` 不在本輪
- **Auto boundary**：僅窄域 `system_error` transient → retry 耗盡後 **≤1** immediate re-invoke；`validation_error`／`config_error`／`HUMAN_REJECTED` → DLQ 待人工；interrupt → 不進 DLQ、須人工 resume
- **Evidence**：`test_retry_policy` Gate 0 · `test_dlq_wave3` · `test_auto_recovery`（8）；`output/wave3_retry_policy_report.md`
- **Deferred**：staging soak；DLQ 真機 200／409；錯誤路徑 cost；DLQ UI／背景 auto-retry（Wave 4a+）
- **Detail**：`04_Workflows/00_Agent_Work_Progress.md` →「### Wave 3 – Error Handling & Auto-Recovery v1（dev-ready · partial · 文件封板）」

## 2026-05-19 — Wave 4A · ask_pipeline 實測 v1（dev-run · partial）

- **Scope**：`gov_core_system` · Wave 4A — `ask_pipeline` live dev-run（Chat A 20 題 + Chat B Monitoring／Cost 收口 + Chat C 寫回）
- **Status**：**dev-run · partial** — pipeline **有效批次**通過；**Monitoring／成本 PG 收口未完成**；**非** production SLO／**非** production-ready
- **Sample**：`POST /api/ask` · **n=20**（short／long／edge／system 各 5）· session `wave4a-A01`…`A20` · UTC **10:45–10:48**（API 重啟後）
- **Pipeline result（有效批次 · Chat A）**：
  - **biz_ok**：**20/20（100%）**
  - **trace_id**：**20/20**；`langfuse_enabled: true`；節點 `health → retrieve → answer`
  - **Latency（端對端）**：p50 **~3.7s** · p95 **~7.9s** · max **~13.4s**
- **Monitoring result（Chat B · PG／ingest）**：
  - PG `wave4a-%`：**0** `task_runs`／`step_runs` → overview／`kpis.cost` **未**反映本次流量
  - 重啟前批次：**20/20** `config_error` 形態（`ENV_FEATURE_AUTO_RECOVERY` import；舊進程）
  - Wave 2 合成 **~$0.0136/trace** — **不可**與本輪 PG 同口径比較（無 wave4a 成本列）
- **Phase 3**（可觀測性）：**partial** — Langfuse **live trace 路徑已驗**（20 條）；營運表／dashboard **未同步**；不足以宣稱 production observability SLO
- **Phase 5**（營運／DLQ）：**dev-ready · partial** — 本輪無 DLQ 積壓；旗標仍 off；暴露 **deploy／熱進程** 與契約常數一致性風險
- **Phase 7**（成本治理）：**partial** — **仍不足** SLO／SLA 決策數據；須 ingest + backfill 後重驗；DCS 雙資料源 **延續** Wave 1–2
- **Blocked / Next**：契約常數與運行進程一致 → **monitoring ingest** 對 20 `trace_id` → Chat B cost／overview 重驗；可選 Wave 4A 重跑
- **Evidence**：`output/wave4a_ask_pipeline_live_run.json` · Chat A／B 報告（`gov_core_system/output/`）
- **Detail**：`04_Workflows/00_Agent_Work_Progress.md` →「### Wave 4A – ask_pipeline 實測小結（dev-run · partial）」

## 2026-05-19 — Wave 4C · ask_pipeline Dev SLO 草案（dev · 非 production SLA）

- **Scope**：`gov_core_system` · Wave 4C — 依 Wave 4A 實測（n=20）訂立 **dev / staging** 最小 SLO；Wave 4B ingest 假設已收口 PG／overview（本輪未重驗 ingest）
- **Status**：**草案 · dev-only** — **非** production SLA；**非** production-ready
- **SLO（dev 草案 v1）**：
  - **成功率**（`biz_ok`）：**≥ 95%**（實測 **20/20 · 100%**）
  - **p95 延遲**（端對端）：**≤ 8 s**（實測 **~8.1 s** Chat A · **~7.9 s** Langfuse）
  - **平均 cost / trace**：**≤ $0.005**（實測 **~$0.0043**，Langfuse generations rollup）
- **適用**：`ask_pipeline` · `POST /api/ask` · dev／staging · 基準 cohort `wave4a-A01`…`A20`；**不含** production
- **演進**：Wave 5 staging soak（n≥100）· Phase 7 成本／告警聯動 · production SLA 須獨立裁決與 soak
- **Evidence**：Wave 4A `output/wave4a_ask_pipeline_live_run.json` · `wave4a_ask_pipeline_monitoring_report.md`
- **Detail**：`04_Workflows/00_Agent_Work_Progress.md` →「### Wave 4C – ask_pipeline Dev SLO / SLA 草案」

## 2026-05-19 — Phase 5 · Dashboard / Alert / Security v1（dev/staging · ~80% ops baseline）

- **Scope**：`gov_core_system` — 儀表板與告警、資料安全合規（在 Wave 1 monitoring 上擴充，不重做 schema）
- **Status**：**約 80%** · **dev/staging ops baseline** — **NOT production-ready**（不可宣稱 production SLA／on-call 就緒）
- **Summary**：
  - **Dashboard**：`GET /monitoring/dashboard-summary` 與 `GET /monitoring/latency-trend`（ask／all cohort · p50／p95 · 15m／60m bucket）已接線；靜態頁 live 模式優先 latency-trend，mock／error 衍生序列有明確 badge；Security hooks 面板可顯示 encryption／Langfuse scrub／logger sanitize 旗標。僅 dev／staging 營運視圖，**無** production SLA。
  - **Alerts**：`POST /monitoring/alerts/evaluate` 對外一律 **HTTP 200**；規則來源 PG + `alert_rule_loader` YAML fallback，壞列跳過並計入 `skipped_invalid_rows`；`evaluate_response` 含 `alerts_fired`／`alerts_suppressed`／`notifications`／`notifier_summary`；`GOV_CORE_ALERT_COOLDOWN_MINUTES` 搭配 per-rule metadata 抑制重複告警。Notifier 已支援 mock／console／log／mock_webhook；Slack／email／PagerDuty 仍為 stub。
  - **Security**：`security_compliance` 提供 EncryptionHook（noop／stub／kms skeleton）、Langfuse outbound scrub、ingest `errors[]` sanitize、DLQ `error_message` mask + stub encrypt；`GOV_CORE_PII_POLICY_CONFIG` JSON policy + `gov_core` logger sanitize filter；`GET /monitoring/security-status` 回報 hooks 接線狀態。dev／staging baseline，**尚未** production 資安審核／KMS 上線。
- **尚未完成**：live PG soak（n≥100）、真實 Slack／email／PagerDuty notifier、KMS-backed `EncryptionHook`、Langfuse SDK 全量 I/O scrub、正式 production SLA／on-call runbook、雙資料源成本統一等。
- **Evidence**：`unittest` **53/53 OK**（monitoring API+alerts **26** · security+notifier+sanitize **27**）；無 `DATABASE_URL` 時 latency-trend／alerts/evaluate／security-status 以 `ok:false`+`message` 或 YAML fallback 優雅降級，不崩潰。
- **Doc**：`output/phase5_dashboard_alert_security_v1.md` · `phase5_alerting_v1.md` · `phase5_data_security_compliance_v1.md`
- **Detail**：`04_Workflows/00_Agent_Work_Progress.md` →「### Phase 5 Wave-Next – latency trend / alert cooldown / security 深化（dev/staging v1）」

## 2026-05-19 — Phase 5 · Shared contracts + parallel integration (tech lead)

- **Status**：**dev/staging v1 · integrated · NOT production-ready**
- **Contracts**：`phase5_dashboard_api_v1.json` · `alert_event_v1.json` · `security_sanitize_v1.json` · `core/contracts/phase5_monitoring.py`
- **Coordination**：`output/phase5_parallel_coordination.md` — Agents A/B/C/D **done**, merge-safe boundaries enforced
- **Integration**：dashboard 5-domain **Pass** · alert write path **Pass** (code) · `observability_v2.log_event` sanitize **Pass**
- **Evidence**：`unittest` **23/23 OK**
- **Blocked**：live PG `monitoring_alert_smoke.py` without `DATABASE_URL`

## 2026-05-19 — Phase 5 · Agent D · Data security compliance v1

- **Status**：**dev/staging baseline · NOT production-ready** — masking only; **no** encryption at rest / KMS / production compliance sign-off
- **Authority**：`core/security_compliance.py` · `shared/schemas/security_sanitize_v1.json`
- **Doc**：`output/phase5_data_security_compliance_v1.md`（surface audit · residual risks · next steps）
- **Wired (v1)**：`observability_v2.log_event` · monitoring read models · `error_adapter.finalize_errors_for_api` · `alert_notifier` · DLQ audit log
- **Not wired**：Langfuse trace bodies · PG at-rest · HTTP body middleware
- **Config**：`GOV_CORE_PII_REDACTION_ENABLED` · `GOV_CORE_PII_DENYLIST_EXTRA` · `GOV_CORE_PII_ALLOWLIST_EXTRA`
- **Detail**：`04_Workflows/00_Agent_Work_Progress.md` →「### Phase 5 · Agent D — 資料安全合規 v1」

## 2026-05-23 — 企業化補強層首輪封存完成

- **Milestone**：企業化補強層首輪封存完成
- **Final status**：
  - **K-1** / **I-bridge v0／v1** / **P+ eval_gate v0** / **H context_entry v0.1** / **J skills seed v0.1** 已完成並寫入治理文檔
- **Scope**：
  - ask 線已具備最小**可觀測**（trace／ibridge_record／eval_gate）、**可重試**（P 線 retry 掛接）、**可控上下文入口**（H 線 `build_rooted_context`）、**可評估**（P+ rule-based eval_gate）、**可 metrics-aware skill**（J 線 `run_metrics_aware_skill`）的企業化骨幹
  - 本輪為 v0／v0.1 基線；**非** production-ready
- **Governance note**：
  - 根目錄 `00_master_plan.md` 為總藍圖（§4 戰役封存）
  - `_workflow_upgrade/90_run_queue.md` 為隊列與 backlog 對賬基線（Done 6 線 + Backlog 條目）
- **Next phase**：
  - 後續工作轉入 backlog 條目逐票推進（I-bridge-v0-H-migrate · I-ask-skills-wire · P+-eval-gate-export-ci · H-historical-migrate · K-2），**不回溯改寫**本輪完成定義
- **Detail**：`04_Workflows/00_Agent_Work_Progress.md` →「## 2026-05-23 — 企業化補強戰役封存完成（H / I / J / K / P+）」

## 2026-05-31 — Wave 4 · W4-A K2 rollout integration（workflow_v2）

**W4-A current status:**
GAP-1（gate vs trace 命名）與 GAP-2（rollback_path_valid 語義）已由 W4-A-FIX-01 / W4-A-FIX-02 修正為「命名與語義對齊」，維持 v0.1 minimal 實作不誇大能力，其餘能力缺口拆票至 W4-A-FIX-03/04 與 Wave 5 結構票。

## 2026-05-31 — Wave 5 · W5-A-RUNTIME ENF（shadow-only）

**W5-A ENF runtime status:**
Phase 2 shadow-only 已完成 wiring + analyzer + 值班指南，BLOCKING-CRITERIA-01 計畫書已成文，第一波 blocking canary 僅鎖 ENF-RULE-1 × {infra_risk, security:critical}，需累積 ≥14 日 shadow 證據通過 O/C/F/G 門檻後，才會開 LIMITED-DENY 實作票。
