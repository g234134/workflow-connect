# 00 Master Plan — 企業化補強層總藍圖

> **角色**：主代理／尚書省派工時的總覽索引。  
> **細節**：各 lane 實作與合同見對應模組文檔；任務隊列（若已建立）見 `_workflow_upgrade/90_run_queue.md`。  
> **迭代**：戰役進展以本文 §4 封存；日常戰報見 `04_Workflows/00_Agent_Work_Progress.md`。

---

## 1. 總體目標

把既有 ask／編排工作流升級為**企業化補強層 v1**：主代理可穩定派工、員工代理可接力、上下文可治理、能力可沉澱、外部系統連接有邊界。  
本輪不以「加功能點」為主，而以 **D1–D5 可度量、可複用入口** 為驗收軸。

**Repo 產品主線（2026-06-27 收斂）**：This repo's core product path is tabular data cleaning and delivery automation; governance / CI / GA lines are supporting rails, not the primary product outcome. 主鏈 SSOT：`docs/TABULAR_MVP_SSOT.md`（intake → gate → clean → bundle → deliver；錨案 `cases/demo_phase/`）。

---

## 2. 五大維度（D1–D5）

| 維度 | 語意 | 典型指標／產物 |
|------|------|----------------|
| **D1** | 長任務成功率與穩定性 | `retry_count`、`success_rate`、checkpoint／retry 政策 |
| **D2** | 上下文工程與記憶 | `context_token_usage`、`memory_hit_rate`、分層 context |
| **D3** | 多代理協作與編排 | `handoff_count`、agent 契約、LangGraph／橋接 |
| **D4** | 可觀測性與評估 | trace 完整度、Langfuse 映射、eval／eval_gate |
| **D5** | 治理／安全／外部通道 | `error_type`、`external_call_count`、dev-only 透傳閘門 |

權威欄位定義見 `metrics/metric_definition.md`、`metrics/metrics_schema.json`。

---

## 3. 企業化補強層（H / I / J / K / L）與支撐線（M / N / O / P / Q）

| Lane | 職責（摘要） | 支撐／鄰接 |
|------|--------------|------------|
| **H** | 上下文**入口合同**（禁止繞過的 `build_rooted_context`） | N 線底層 `build_context` |
| **I** | ask **主線橋接**（context／retry／trace／API 透傳） | 暗部 `ask_pipeline`、`/api/ask` |
| **J** | **metrics-aware skills** 與 skill runner 種子 | M／O／P 自動掛鉤 |
| **K** | **LangGraph** 編排示範與 e2e 圖 | M／N／O／P／Q 接線 |
| **L** | （預留）外部通道／hook 治理深化 | D5 |
| **M** | Agent 契約、handoff、角色邊界 | D3 |
| **N** | Context／memory 模型與路由 | D2 |
| **O** | Logging／trace／Langfuse 映射 | D4 |
| **P** | Retry／checkpoint／失敗分類 | D1 |
| **Q** | Metrics collector 與 schema | D1–D5 匯總 |

---

## 4. 企業化補強 · 2026-05 戰役封存

**封存日**：2026-05-23  
**範圍**：H／I／J 主線能力 + K-1 最小圖 + M／N／O／P／Q 支撐線接線（本輪五條關鍵交付線）。  
**狀態**：本節所列戰役線均 **done**（v0／v0.1）；歷史路徑全量遷移、生產級 eval 與 LangGraph 依賴安裝屬後續工單。

### 4.1 戰役線一覽

| 戰役線 | 狀態 | 主提升維度 | 核心產物簡述 |
|--------|------|------------|--------------|
| **K-1 e2e 圖** | done | D1／D2／D3／D4 | 最小 LangGraph：`Planner → Executor → Reviewer` StateGraph；掛接 M／N／O／P／Q（`core/langgraph_flow_k1.py`） |
| **I-bridge v0／v1** | done | D1／D2／D4／D5 | v0：`ask_pipeline` 鄰近入口掛 context／retry／trace；v1：`/api/ask` dev-only `ibridge_record` 透傳（雙閘門） |
| **P+ eval_gate v0** | done | D1／D2／D3／D4 | `evaluate_task_record(record)` 規則複查：`high_retry`、`context_heavy`、`many_handoffs`、`infra_risk`、`observability_gap` |
| **H v0.1** | done | D2／D5 | `build_rooted_context` 唯一上下文入口 + 禁止繞過條款（`context/context_entry_contract.md`、`AGENTS.md` H 線） |
| **J skills v0.1** | done | D1／D3／D4 | `run_metrics_aware_skill` + `retrieve`／`pg_query` 示範 skill；自動掛 retry／metrics／`external_call`（`skills/skills_contract.md`） |

### 4.2 各線補充（提綱）

- **K-1**：示範編排圖，不取代暗部既有 `ask`／`langgraph_flow` 生產圖；新編排應複用同一套 agent／metrics／trace 接線模式。  
- **I-bridge**：v0 強化執行期可觀測與重試；v1 僅在 dev／雙閘門下暴露 `ibridge_record`，避免生產 API 面擴張。  
- **P+ eval_gate**：與完整 eval verdict 並行，為**人工複查篩選**，不取代 `verdict=success` 硬規則（見 `observability/eval_pipeline.md` §6）。  
- **H**：新 ask-like、LangGraph 首節點、對外 API 上下文組裝**必須**走入口函數；細節見工程合約附錄 D。  
- **J**：新 skill 須聲明服務的 D 維度，並經 `skill_runner` 嵌入，禁止 ad-hoc logging。

### 4.3 能力層躍遷（本輪結論）

本輪目標不是堆功能，而是讓 ask 線具備：**可觀測、可重試、可控上下文入口、可統一評估、可 metrics-aware skill** 的企業底座。  
自此之後，所有**新入口**與**新 skill** 均須說明服務的 D 維度，並盡量複用本輪產出的入口／runner／eval_gate，避免再次發明平行欄位或繞過合同。

### 4.4 驗收索引（不展開實作）

| 戰役線 | 最小驗收（戰車根 unittest） |
|--------|------------------------------|
| K-1 | `tests.test_langgraph_flow_k1`（需安裝 `langgraph`） |
| H | `tests.test_context_entry` |
| P+ eval_gate | `tests.test_eval_gate` |
| J | `tests.test_skills_metrics` |
| I-bridge | 暗部 `tests.test_ask_pipeline_ibridge_v0`、`tests.test_app_api_ibridge_expose` |

### 4.5 企業化補強 · 2026-06 Wave 2 完成摘要

**封存日**：2026-06（第二輪企業化補強）  
**範圍**：I-bridge H 線遷移、ask 主線 skills 接線、P+ eval 匯出與 CI 信號、K-2 編排圖（與 K-1 並存）。  
**狀態**：本節四條戰役線均 **done**；預設 ask H 線 context 已於 **H-historical-migrate**（§4.10）收斂；K-2 尚未合流 ask 主線。

第二輪在 §4.1 首輪封存（K-1／I-bridge／P+／H／J v0.1）之上，把**入口／編排／觀測／評估／能力包**從「各線 isolate 可跑」推進到「opt-in ask 流程與 LangGraph 圖實際接線」。能力骨幹層（H／J／P+／K 合同與模組）與全面接線層（ibridge opt-in、langgraph_flow、eval 批次、K-2 圖內掛載）同步補齊，骨幹完成度由約 **70–80%** 提升至接近 **90–100%**（剩餘缺口見 §4.6）。

| 戰役線 | 狀態 | 主要提升層級 | 核心變更 |
|--------|------|--------------|----------|
| **I-bridge-v0-H-migrate** | done | **全面接線**：H 線 context 接入（opt-in 路徑） | ibridge_v0 ask 入口改走 `build_rooted_context(mode="ask_pipeline")`；collector metadata 對齊 H 線；預設 ask 保持 bypass，留待 H-historical-migrate |
| **I-ask-skills-wire** | done | **全面接線**：J 線 skills 接入 ask 主線 | `langgraph_flow` 的 retrieve／answer 節點改走 metrics-aware skills（`skill_retrieve_for_ask`／`skill_answer_for_ask`）；I-bridge 重複 retry／span 移除，統一委派給 `skill_runner` |
| **P+-eval-gate-export-ci** | done | **骨幹＋接線**：P+ 從分析工具升級為質控工序 | 新增 `eval_exporter`（輸出 `eval_export/v1` JSONL）與 `eval_ci_check`（CI signal）；可對 `ibridge_record` 批次產生 pass／needs_review + tags 報表 |
| **K-2 圖** | done | **骨幹**：K 線編排層深化 | 新增 `build_k2_graph()`／`run_k2_flow()`，圖內掛 H 線 context、J 線 skills、P 線 retry、P+ eval_gate；K-1 保留不動，K-2 作為下一階段實驗圖；定義 `ASK_MERGE_INTERFACE` |

### 4.6 企業化補強 · Wave 3 候選戰場（草案）

以下為**尚未實作**或**部分完成**、已在各線 Work Report 標為「下一步」的候選戰場；§4.5 已完成项已移至 §4.7。

- **CI 實掛 eval_ci_check**：在實際 CI YAML 中加上 `eval_ci_check`，針對最近 N 筆 run 控制 `needs_review` 比例與關鍵 tags。  
- **K-2 × ask 主線 shadow／合流**：在正式合流前先做 shadow invoke + 回歸夾具，對照 K-2 圖輸出與現有 ask 輸出的差異。（`K2-ask-shadow-merge` 已 done；prod rollout 見 §4.8）

Wave 3 以**全面接線與產品化**為主題：不再改寫第一輪／第二輪的完成定義，只在既有骨幹上疊加 CI、shadow、統一路徑等收斂工作。

### 4.7 企業化補強 · Wave 3 回答侧收敛（2026-05-24 封存）

**封存日**：2026-05-24  
**范围**：Chat A（answer skill 化）+ Chat B（selector + 无 context 场景）+ Chat C（文档／队列封存）。  
**状态**：`J-answer-skill-wire`、`J-selector-context-governance` 均 **done**；本 Chat 不改代码。

本轮把 ask 问答 pipeline 从「仅 retrieve 侧 metrics-aware」推进到 **问 + 检索 + 答** 三段均在同一治理骨架下：`build_rooted_context`（H）→ `decide_use_rag`（selector）→ `skill_retrieve_for_ask` / `skill_answer_for_ask`（J）→ `ibridge_record` / eval_export（P+）。retrieve 与 answer 的 metrics 对称：`call_site`、`external_call_count`、`retry_count`、D4 span／事件均可被 M-line record 与 eval 批次消费。

无 context 场景（问候、短闲聊）经 selector ASK-R2/R3 跳过 retrieve，仍走 `skill_answer_for_ask` + `perform_direct_answer`，保证 answer 步 observability 不缺口。retrieve 失败（S3）继续 answer 节点并打 `retrieve_fallback` / `retrieve_error_type`，`ibridge_v0.selector_decision` 可审计。

#### 4.7.1 能力矩阵（H / I / J / P / K / P+）

| Lane | context | retrieve | answer | selector | eval |
|------|---------|----------|--------|----------|------|
| **H** | **done**（預設 + opt-in 均 `build_rooted_context`） | — | — | — | — |
| **I** | bridge v0/v1 已完成 | 经 J skill 已完成 | 经 J skill 已完成 | 图内 selector 已完成 | — |
| **J** | — | skill + tool_executor bridge 已完成 | answer skill 已完成 | ASK-R1–R6 已完成 | — |
| **P** | — | retry 挂接已完成 | LLM retry 经 skill 已完成 | — | — |
| **K** | K-2 图内 H 挂接已完成 | K-2 stub 已完成 | K-2 stub 已完成 | ask 主线已完成；K-2 merge adapter（dev/test） | shadow + merge adapter（dev/test） |
| **P+** | — | — | answer metrics 纳入 export 视野 | selector_decision 可导出 | gate+export+shadow nightly CI **done** |

#### 4.7.2 最小验收索引

| 战役线 | 命令 |
|--------|------|
| J-answer-skill-wire | `python -m unittest tests.test_skills_ask_wire.py -v`；暗部 `tests.test_ask_skills_wire_e2e` |
| J-selector-context-governance | `python -m unittest tests.test_ask_selector_and_answer.py -v` |
| K-2 merge adapter | `python -m unittest tests.test_k2_merge_adapter tests.test_k2_ask_shadow -v` |
| H-historical-migrate | `tests.test_context_entry`；`tests.test_ask_selector_and_answer`；暗部 `tests.test_ask_pipeline_default_context` |
| 合同 | `skills/skills_contract.md` §9–§10；`context/context_entry_contract.md` §8 |

#### 4.7.3 K-2 合流策略（dev/test · 2026-05-24）

**状态**：Chat B **done**（adapter + 策略文档 + merge tests）；**未**启用生产合流。

- **单点 adapter**：`core/k2_merge_adapter.py` → `merge_ask_and_k2`；出口 hook 仍经 `core/k2_ask_shadow`（`ASK_MERGE_INTERFACE`）。
- **策略摘要**：双 ok 时 **ask 主答案**；K-2 `infra_risk` → 内容回退 ask 但 **`ok=False` + CI fail**；ask 失败时保守保留 ask 失败（K-2 恢复仅 metadata）。
- **文档**：`docs/k2_merge_strategy.md`（场景表 S1–S7）；行为基线 `docs/k2_behavior_profile.md`。
- **待治理**：Selector 桥接、greeting skip-RAG、answer LLM 对齐、partial traffic 批准 — 见策略文档 §4。

### 4.8 K-2 部署治理与 rollout 方案（2026-05-24 · Chat C）

**状态**：治理策略 **done**；**Phase 1 prod shadow 已启用（本地 prod-like 演練）**（2026-05-26 06:00 UTC · 批文 `HQ-GOV-K2-P1-SHADOW-20260525`）。  
**摘要**：戰車根 + `gov_core_system` venv 上跑滿 7 日 shadow 觀測（真流量樣式、user-facing 100% ask-only）；spool + nightly export + `eval_ci_check` 作治理演練。  
**Phase 1 scope（2026-06-05 裁決 `WAVE-CORE-P0-PHASE1-ROLLOUT-DECISION` · Option A）**：**local shadow only** — Phase 1 **出门 gate** 聚焦 **K1/K2 核心逻辑 parity**（本地 workstation shadow 验证通过即满足 Phase 1）；**不**将 remote prod cluster shadow 部署纳入 Phase 1 gate，**不阻塞** Phase 2 canary 进场。  
**Remote rollout**：另票 **`K2-phase1-remote-rollout`（P1）** — 目标为 remote prod cluster shadow 部署与 parity 验证；runbook 蓝图见 `docs/k2_phase1_remote_rollout_runbook.md`（Blueprint only，不代表已实施）。  
**权威文档**：`docs/k2_deployment_governance.md` · 部署 env 樣板 `observability/deploy/k2_phase1_prod_shadow.env`

| 项 | 摘要 |
|----|------|
| **当前 Phase** | **1** — **local-only gate** prod shadow（本地演練；用户 100% ask 主答案；K-2 异步复制 + spool + nightly export） |
| **Phase 1 完成标准** | 本地 workstation shadow parity 验证通过（含 7 日观测与治理 §6.2–§6.3 出门指标）；**不含** remote prod rollout |
| **範圍邊界** | **在範圍**：T+0 已完成的本地四鍵 + `/api/ask` → spool；7 日每日/週指標與回退演練；`master_plan` / Progress / `90_run_queue`。**不在範圍（Phase 1 gate）**：SSH/K8s 遠端設定、雲端 prod shadow 部署与验收 — 见 P1 工單 `K2-phase1-remote-rollout` |
| **T+0 啟用（2026-05-26 06:00 UTC）** | 部署層 env 四鍵（見 `k2_phase1_prod_shadow.env`）；本地 API 重載 + smoke → spool + export 三元組 exit 0 |
| **7 日觀測（本地）** | 觀測窗 **2026-05-26 06:00 UTC 起 7 自然日**；每日對 spool 跑 export + `eval_ci_check`（0.60 + `infra_risk`，與 `eval-gate-ci.yml` nightly 同參）；第 7 日對照治理 §6.2–§6.3 出門指標 |
| **Wave 1 hook（2026-05-25）** | `gov_core_system/app_api.py` fire-and-forget → `core/k2_prod_shadow_worker_cli`；spool `artifacts/eval/k2_shadow_spool.jsonl`；nightly export 改讀 spool |
| **角色** | 尚書省最终批准；工程实现／监控；产品体验；治理 eval/infra 审核 |
| **Rollout 模式** | Shadow → internal canary (5–10%) → tenant/扩面 → optional full switch |
| **指标** | P+ `eval_ci_check`：`needs_review` 比例、`--fail-on-tags infra_risk`、shadow `merge_safe` / `unacceptable` |
| **回退** | `infra_risk`、merge `ci_fail`、ok 率恶化等自动回退 ask-only；on-call 可先斩后奏 |
| **进门** | Phase 1 需 shadow 测试全绿 + 前置清单（§5）+ 尚書省批文 |
| **P+-eval-ci-wire（2026-05-24）** | **done** — `shadow_ibridge_records.latest.jsonl` + nightly `eval_ci_check`（0.60 + `infra_risk`）；PR 仍 0.72 / 无 tag gate |
| **Phase 2 批文草案（2026-05-25）** | **准备完成** — `docs/drafts/HQ-GOV-K2-P2-CANARY-DRAFT.md`（草案 · 暂不生效）；待 Phase 1 七日观测达标后送尚書省定稿；无实作票 |

与 Chat B 合流策略关系：本文件管 **何时、谁批准、多少流量**；`k2_merge_strategy.md` 管 **合流后 envelope 语义**。

### 4.9 Tool executor `llm.ask` skill 化（2026-05-24）

**状态**：`J-tool-executor-llm-ask-skill` **done**。

- **变更**：`tool_executor_skills_bridge` 将 catalog `llm.ask` 由 T6a stub 改为 `run_answer_via_skill` + `perform_direct_answer`（策略 A）；`call_site=tool_executor.ask_pipeline.llm.ask`。
- **对称**：与 §4.7 LangGraph `answer_node` 共用 `skill_answer_for_ask`；M-line `external_call_count` / `retry_count` 可被 eval export 按 call_site 消费。
- **验收**：`python -m unittest tests.test_tool_executor_skills_bridge tests.test_tool_executor -v`（暗部 `gov_core_system`）。

### 4.10 預設 ask H 線 context（H-historical-migrate · 2026-05-25）

**状态**：**done**（程式已切；本票驗收 + 文檔封存，**零 diff**）。

- **入口**：`langgraph_flow.run_ask_flow` → `run_ask_with_hline_context` → `build_rooted_context(..., mode="ask_pipeline")` → `_context_entry_payload`。
- **契約**：`context/context_entry_contract.md` §8.0；生產預設不啟用 `GOV_CORE_ASK_HLINE_CONTEXT_FALLBACK`。
- **验收**：`tests.test_context_entry` + `tests.test_ask_selector_and_answer` + 暗部 `tests.test_ask_pipeline_default_context`；`eval_ci_check` shadow 基線不退步。

### 4.11 Monitoring subagent · Sprint 4 O-2（2026-05-25 · 制度收口 O-2c）

**状态**：C-1 + O-2a + O-2b **done**（程式）；O-2c **done**（`AGENTS.md`／`TASK_ROUTING.md`／`50_context_entry_runbook.md` 對齊）。**未**启用独立 LangGraph monitoring 图或 HQ `hq.monitoring` 派工类型。

| 票 | 状态 | 产物（摘要） |
|----|------|----------------|
| **C-1** | done | `subagents/context_routing.py` — `metadata.subagent_route`，`signal_only=true` |
| **O-2a** | done | `subagents/monitoring_executor.py` — 只读 `monitoring_service` + `v0.1-stub` fallback |
| **O-2b** | done | `ask_pipeline_ibridge_v0.enrich_init_with_context_entry` — 预图 sidecar；`ibridge_v0.monitoring_executor` |
| **O-2c** | done | 制度层边界：见 `AGENTS.md` Monitoring Subagent；`TASK_ROUTING.md` §3.4（无 `hq.monitoring`） |

**制度语义**：`obs-only` / `signal_only` — ask 内附加结构化监控摘要，**不**接管 HQ 路由、Infra 维运、DarkOps 施工或 RAG selector。

**验收索引**：`tests.test_context_subagent_routing` · `tests.test_monitoring_executor`；暗部 `tests.test_ask_pipeline_ibridge_v0`。

**后续候选（未开工）**：持久化 executor 审计、LangGraph monitoring 节点图、与 `dark.infra` 票显式分工表 — 单开工单，勿在 O-2c 宣称已交付。

### 4.12 Monitoring graph · Sprint 5 治理（C 线 · selector／SLO 条款）

**状态**：M-1–M-3 **done**（程式 **v0.2-langgraph-min** + ibridge 摘要 + `/api/ask` 双闸门）；**C-GOV** **done**（制度，不改 selector）。

| 项 | 状态 | 产物（摘要） |
|----|------|----------------|
| **M-1–M-3** | done | `core/monitoring_graph.py`（v0.2-langgraph-min）；`GOV_MONITORING_GRAPH_ENABLED`；`ibridge_v0.monitoring_graph`；B 线顶層 `monitoring_graph` 双闸门 |
| **C-GOV** | done | `50_context_entry_runbook.md` §6.7–§6.8；`AGENTS.md` Monitoring Graph 治理摘要 |

**裁决**：**现在不能让 graph 参与 selector／SLO gate**；仅 **L0 observability**。升格 L1 shadow-advisory → L2 SLO gate 见 runbook §6.8.3–§6.8.5；每级单开实作票（`M-GOV-L*`）+ 尚书省批文。

**三級**：L0 observability（**已启用**）／L1 shadow-advisory（禁）／L2 SLO gate（禁）。HTTP 暴露走 **L0 Observability 閘門**（双闸门、默认关闭；**非**业务 contract）。`recommendation` ≠ SLO judgment。

**索引**：`workflow_upgrade/90_run_queue.md` Sprint 5 · O 线 · C-GOV。

#### Sprint 5 – Monitoring Graph L0

**状态**：Sprint 5 **封 Sprint**（2026-05-25）— 在 O-2 基线上交付 **monitoring graph v0.2-langgraph-min（L0 only）**，并为未来 L1/L2 gating 预留入口与治理；**未**改动 selector、主 ask LangGraph 或 `answer` 合成路径。  
**范围一句话**：只读 observability 侧车 — executor adapter 成功且 `GOV_MONITORING_GRAPH_ENABLED=1` 时可选跑 graph；默认 **OFF**；无 graph／flag OFF／非 monitoring 路由时**不**出现公开 `monitoring_graph` 键。

| 线 | 状态 | 产物（摘要） |
|----|------|----------------|
| **A** | done | `core/monitoring_graph.py` — LangGraph 四节点 `summarize`→`analyze`→`recommend`→`finalize`；只读 `service_summary`；fail-open；**仅** adapter 成功路径 |
| **B** | done | `/api/ask` 顶层 `monitoring_graph`（dev/debug）；双闸门 `GOV_CORE_API_EXPOSE_MONITORING_GRAPH=1` + `?expose_monitoring_graph=true`；L0 observability-only |
| **C** | done | `50_context_entry_runbook.md` §6.7–§6.8 + `AGENTS.md` — L0／L1／L2 三级、Observability Gate 规则、升级／回退楼梯 |

**裁决（站位）**：**现在不能让 graph 参与 selector／SLO gate**；仅 **L0 observability**。L1 shadow-advisory、L2 SLO gate **禁止**（未实作、无批文）。HTTP 暴露 ≠ 业务 contract；`recommendation` ≠ SLO judgment。任何 L1+ 升格须满足 runbook §6.8.4–§6.8.5 且**另开** `M-GOV-L*` 实作票 + 尚书省批文。  
**验收索引**：`tests.test_monitoring_graph` · `tests.test_monitoring_executor`（graph 路径）；`tests.test_app_api_monitoring_graph_expose`、`tests.test_ask_pipeline_ibridge_v0` 需在战车根 / 正确 `PYTHONPATH` 环境下验收。  
**后续候选（未排期 · 需尚书省批示，勿写成已承诺）**：
- **M-TEST-HARDEN** — 测试环境／PATH 与暗部 venv 对账硬化；
- **M-API-PATH** — `/api/ask` observability 暴露面的 prod 路径与安全边界；
- **M-GOV-L1** / **M-GOV-L2** — shadow／advisory 与 SLO gate（须 §6.8 门槛 + 专票）；
- **OBS-GATE-1** — 可选 umbrella observability alias（保留现有双闸门向后兼容）。

**索引**：`workflow_upgrade/90_run_queue.md` Sprint 5 · O 线；`50_context_entry_runbook.md` §6.7–§6.8。

---

## 5. 後續（非本輪）

- 其餘歷史非 ask 主線之 `build_context` 呼叫點仍**單開工單**遷移（合同 §7 非目標）。  
- eval_gate v0.2：擴充 D5 `error_type` 覆蓋與抽樣策略。  
- K-2+：在 K-1 骨架上擴展真實 tool／RAG 節點，仍遵守 M／N／O／P／Q 接線。  
- 若尚未建立：補齊 `_workflow_upgrade/90_run_queue.md` 與 `latest_status.md` 作為派工黑板。
