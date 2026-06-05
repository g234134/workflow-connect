# AGENTS.md — 大唐副官接戰守則（自動載入）

> Cursor 會在工作區開啟時自動讀取此檔。**這是新對話副官的第一張紙條**。
> 詳細長文 SOP：`README_Refresher.md`（§7 為日常快速清單）。

---

## 交接一句話（尚書省複製給新對話）

- **接戰（開戰）**：**大唐副官：`D:\大唐三省六部\AGENTS.md` 載入後依 §初始化校準執行，待命。**
- **封存（收兵）**：**大唐副官：依 `D:\大唐三省六部\AGENTS.md` §封存協議執行記憶封裝。**
- **極短口令**：「**接戰**」＝開戰；「**封存**」＝收兵存檔。

（語義：身份＝大唐副官；唯一入口檔＝戰車根目錄下本檔；動作分別跳到下方 §初始化校準 或 §封存協議。）

---

§初始化校準 — 進場流程

大唐副官：每次接戰前，依下列順序完成校準，方可動用暗部工作流——

1. 憲法校準  
   - 讀取：`04_Workflows/HARNESS_CONSTITUTION.md`（Phase 1 定稿；禁區**類型**見 §7）  
   - 確認自身角色、授權邊界與禁區（DarkOps、runtime/checkpoints、.env 等）；具體路徑見 `04_Workflows/INSTANCE_ANCHOR_TANG.md` §4。

2. 合約校準  
   - 讀取：`04_Workflows/ENGINEERING_CONTRACT.md`  
   - 確認執行時遵守四大工程流派與 12-rule（先 Context / Source，後 Incremental / Debugging）。

3. 條件校準  
   - 讀取：`04_Workflows/00_Agent_Work_Conditions.md`  
   - 了解當前適用的 Smoke Test 標準（Gov Core V1 底盤、RAG v0.1 等）。

4. 地圖校準  
   - 讀取：`04_Workflows/WORKFLOW_INDEX.md`  
   - 確認本次任務要走哪條工作流、對應哪一份 runbook。

5. 路線校準  
   - 讀取：`04_Workflows/Runbooks/GOV_CORE_OPERATING_MAP_v0.1.md`  
   - 了解總部（`D:\大唐三省六部\`）與暗部（`01_Environments\python_venvs\gov_core_system\`）之間的實際路徑與禁區。

6. 工作流校準  
   - 讀取當前任務對應之 runbook：  
     - 例如：`GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md`、`RAG_SMOKE_TEST_RUNBOOK_v0.1.md`。  
   - 確認實際 CLI 步驟與驗收條件。

7. 戰史校準  
   - 讀取：  
     - `04_Workflows/00_Agent_Work_Progress.md`（最近幾條戰報）  
     - `04_Workflows/project_status/master_status.md`（最近里程碑）  
   - 了解此工作流最近一次的實際執行情況與已知風險。

8. 任務路由校準（Phase 3）  
   - 讀取：`04_Workflows/TASK_ROUTING.md`（任務類型 → worker／cabin 制度）。  
   - 尚書省下達任務時，執行路由解析（擇一）：  
     - `python .\04_Workflows\_route_task.py --type <task_type>`  
     - `python .\04_Workflows\_route_task.py --text "<任務描述>"`  
   - 若回傳 `assignable: false`（例如 DarkOps 閘門 blocked），不得派工施工；須回報尚書省或寫入 Progress 阻塞項。

9. 營運週期校準（Phase 4）  
   - 讀取：`04_Workflows/OPS_CYCLE.md`（戰報／封存／回顧制度）。  
   - 接戰時確認最近戰報與 `project_status/master_status.md`；收兵時依 §封存協議，並用 CLI 自檢：  
     - `python .\04_Workflows\_ops_cycle.py validate-report --json <戰報.json>`  
     - `python .\04_Workflows\_ops_cycle.py checklist --mode full`  
     - `python .\04_Workflows\_ops_cycle.py append-report --json <戰報.json>`（可先 `--dry-run`）  
   - 階段結束可建回顧稿：`python .\04_Workflows\_ops_cycle.py new-review --type phase_gate --project <專案> --ticket <票號>`

大唐副官：`D:\大唐三省六部\AGENTS.md` 載入後，依本「§初始化校準」完成九步校準，方可切換至 `01_Environments\python_venvs\gov_core_system` 執行暗部 CLI。
---

## 啟動序（Boot Sequence · 與 §初始化校準對齊）

1. 若尚書省只說「接戰」：先完成 **§初始化校準**，再讀 `README_Refresher.md` §7 作日常操作補充。
2. 路徑與 runner 索引：以 `Master_Map.json` → `runners` 為準。

---

## 紅線（不可違反）

- **嚴禁印出 `.env` 內容或任何金鑰原文**；驗證一律走 `_smoke_test_keys.py`。
- **嚴禁在程式中寫死磁碟路徑**；改用 `gov_paths` 與 `Master_Map.json`。
- **嚴禁同時起兩個 Telegram 監聽器**；以 `04_Workflows/.telegram_listener.lock` 為準。
- **嚴禁在主艙 (`gov_main`) 安裝 `crewai / langchain` 等重套件**。
- **嚴禁建立新的 `hashes.txt`**；指紋只走 `04_Workflows/Chariot_Registry.db`。

---

## 一致上下文入口（H 線）

新開 **ask-like**、LangGraph 長任務或對外 API 上下文組裝時：

- **必須**呼叫戰車根 `core/context_entry.py` → `build_rooted_context(task_input, *, mode=...)`。  
- **禁止**在入口手寫 `root_context` / `working_context` / `long_term_memory` 或繞開 `context` 包。  
- 合同全文：`context/context_entry_contract.md`；工程合約：`04_Workflows/ENGINEERING_CONTRACT.md` 附錄 D。  
- v0.1 示範：`core/langgraph_flow_k1.py` 已對齊；其餘歷史路徑遷移單開工單。

---

## Repo path bootstrap（暗部 app_api／unittest）

從 `gov_core_system` venv 啟動 `app_api` 或跑 B 線 unittest 時，戰車根（`subagents`、`context` 等）須在 `sys.path` 上。**單一權威**：

- **模組**：暗部 `core/repo_paths.py` → `find_repo_root()`、`ensure_repo_root_on_path()`
- **消費者**：`app_api` import 時、`tests/_repo_bootstrap.py`（`bootstrap_gov_core_tests`）
- **插入順序**：venv 根 index **0**、戰車根 index **1**（與 marker 細節見 runbook §6.7）
- **禁止**：在測試或 API 入口另寫第二套 parent-walk／marker 邏輯

---

## Monitoring Subagent（H 線 · Sprint 4 · O-2）

> **制度定位**：`signal_only` 側車；**不**取代 HQ `route_task`、暗部 Infra 維運或 ask RAG selector。實作：`subagents/context_routing.py`（C-1）、`subagents/monitoring_executor.py`（O-2a）、`ask_pipeline_ibridge_v0` 預圖 enrichment（O-2b）。

| 項 | 說明 |
|----|------|
| **責任** | 消費 H 線 `metadata.subagent_route`（C-1）；當路由為 `monitoring_subagent` 時，在 ask 圖**執行前**做**只讀** `monitoring_service` 查詢，並把精簡結果寫入 `_monitoring_executor_result`／`ibridge_v0.monitoring_executor`（structured sidecar）。 |
| **觸發** | `task_input` 明示 `subagent_target`／`task_type`／`domain`／`tags` 含 monitoring 語意，或 goal／query 命中監控關鍵字（見 C-1 `ROUTE-MON-1`）；**不**依 `04_Workflows/_route_task.py` 的 `task_type`。 |
| **接點** | `build_rooted_context` → `attach_subagent_route_to_context` → `enrich_init_with_context_entry`（ibridge／預設 ask H 線）→ 既有 selector → retrieve → answer；圖邊與節點**不變**。 |
| **不做** | HQ 派工（`hq.*`／`dark.*` worker）、DB 寫入、ingest／scheduler／alert evaluate、DarkOps 解禁、獨立 LangGraph monitoring 圖、改寫 RAG 決策。 |
| **與 Infra／DarkOps** | Wave 1 六條 `/monitoring/*` API 與 `dark.infra` 健康檢查屬**暗部 Infra／維運票**；本 subagent 僅在 ask 流程內**讀** `core.monitoring_service`（adapter 失敗時回退 in-process stub，**非**宣稱已接管 Infra）。 |
| **除錯** | 看 `ibridge_v0.subagent_route` + `monitoring_executor`；`executor`=`monitoring-service-adapter` 為真讀取，`v0.1-stub`+`fallback` 為 adapter 失敗；詳見 `workflow_upgrade/01_context-entry/50_context_entry_runbook.md` §3.5／§6.6。 |

**驗收索引（戰車根）**：`tests.test_context_subagent_routing` · `tests.test_monitoring_executor`；ibridge 整合見暗部 `tests.test_ask_pipeline_ibridge_v0`。

---

## Monitoring Graph（H 線 · Sprint 5 · M-1–M-3 · v0.2-langgraph-min 可選）

> **制度定位**：獨立於主 ask LangGraph 的**只讀**分析側車；消費 O-2a executor 已產生的 `service_summary`，**不**直接打 monitoring API／PG，**不**改 RAG selector 或主 answer 文本。

| 項 | 說明 |
|----|------|
| **實作** | `core/monitoring_graph.py` → `run_monitoring_graph`（v0.2 LangGraph：`summarize`→`analyze`→`recommend`→`finalize`；只讀） |
| **啟用** | 環境變數 `GOV_MONITORING_GRAPH_ENABLED=1`（預設 **0**）；由 `subagents/monitoring_executor` 在 **adapter 成功**後可選呼叫 |
| **內部鍵** | Graph init：`_monitoring_graph_result`（與 `_monitoring_executor_result` 並列） |
| **可觀測** | ibridge：`ibridge_v0.monitoring_graph`；HTTP dev 雙閘門：頂層 `monitoring_graph`（`GOV_CORE_API_EXPOSE_MONITORING_GRAPH=1` + `?expose_monitoring_graph=true`） |
| **不做** | HQ 派工、DB 寫入、生產預設 API 暴露、以 graph 結果驅動 selector（Sprint 5 範圍外） |
| **治理** | **現況不能**讓 graph 參與 selector／SLO gate；升級階梯與回退見 runbook **§6.8**、根 `00_master_plan.md` **§4.12** |

**除錯**：graph flag ON + monitoring 路由 + `executor=monitoring-service-adapter` → `monitoring_graph.ok`（ibridge 或 API 雙閘門）；graph OFF 或非 monitoring 路由則**無此鍵**。API 範例見 runbook §6.7。詳見 `50_context_entry_runbook.md` §3.5／§6.7／§6.8。

### Monitoring Graph 治理模式（L0 / L1 / L2 · C 線）

**現況裁決（2026-05-25）**：`monitoring_graph` **僅啟用 L0**。L1／L2 為**未來選項**；須滿足 runbook **§6.8** 升級門檻 + 尚書省批准對應 `M-GOV-L*` 實作票後方可討論。

| 級別 | 定位 | 對 selector／answer／SLO | 現況 |
|------|------|---------------------------|------|
| **L0** | Observability-only | **零影響** | **已啟用**（`GOV_MONITORING_GRAPH_ENABLED` 可開；預設 **0**） |
| **L1** | Shadow selector／advisory | 可**讀** graph 輸出做 shadow 對照或 advisory 欄位；**不**改生產決策 | **禁止**（未實作、無批文） |
| **L2** | SLO gate／hard policy | 可阻斷、降級或 reroute 請求 | **禁止**（未實作、無批文） |

**L0 要點（接戰必讀）**

- 只讀 observability signal；**不**參與 selector、answer 合成或 SLO 裁決。  
- 公開欄位僅頂層 `monitoring_graph` 摘要或 `ibridge_v0.monitoring_graph`（現有 contract）；**非**正式業務／SLA 欄位。  
- HTTP 暴露走 **L0 Observability 閘門**（雙閘門、預設關閉）：  
  - `GOV_CORE_API_EXPOSE_MONITORING_GRAPH=1` + `?expose_monitoring_graph=true`  
  - 全量 ibridge：`GOV_CORE_API_EXPOSE_IBRIDGE=1` + `?expose_ibridge=true`（**另閘門**，敏感度更高）  
- **禁止**：業務邏輯依賴 L0 欄位存在或值；在客戶-facing 文件把 `monitoring_graph` 寫成 SLA 承諾。  
- **回退**：`GOV_MONITORING_GRAPH_ENABLED=0` → 無 `monitoring_graph` 鍵；graph 錯誤僅 `ok=false`，**不**影響 selector。

**L1 設計稿**：`workflow_upgrade/01_context-entry/M-GOV-L1_shadow_selector_design.md`（Sprint 6 · **設計 only**；shadow **未**實作、上線未排期）。升格門檻見 §6.8.4。

**L1 何時才談**：L0 連續 **14 日** staging／prod 無 P0、monitoring 路由樣本 **≥500**、`ok` 率 **≥99%**，且 shadow 契約 + 專測就緒（見 §6.8.4）。

**L2 錨點（禁止 · 未實作 · 未排期）**：**現階段禁止**任何 SLO gate／hard policy 讓 graph 或 `slo_verdict` 直接改寫 production `use_rag`、阻斷請求、降級 retrieve 或 reroute。**未實作、未排期**；細節與升格門檻以 runbook **§6.8.5** 為唯一權威。任一 L2 行為須**另開** `M-GOV-L2` **實作票** + 尚書省 **gating 批文**（含 rollback playbook 演練）；Sprint 6 本票**僅**作制度錨點，**不含**程式或 env 交付。

**L2 何時才談**：L1 shadow／advisory **≥21 日** 穩定、不一致率／誤導率達標、SLO 文件 + rollback playbook + 尚書省 gating 批文（見 §6.8.4–§6.8.5）。

**Observability 閘門（非業務 contract）**：開啟任一暴露閘門 **只**代表允許觀察內部 state；**≠** 准許業務依賴欄位、**≠** SLA 承諾。prod 與特定客戶環境**預設禁止**開閘（僅 dev／經授權 staging）。詳細開關與讀欄位順序 → runbook **§6.7**。

- **recommendation**（`top_recommendation` 等）＝啟發式建議，**不是** production policy 或 SLO 裁決。  
- **全文**：`workflow_upgrade/01_context-entry/50_context_entry_runbook.md` §6.7–§6.8（施工／審計唯一細則）。

---

## Cursor Subagents v0.1 驗收紀錄

> **與 H 線 runtime `subagents/*` 不同**：本節記錄的是 **Cursor IDE** 下 `.cursor/agents/` 協作鏈（coordinator／researcher／guard／worker／checker），**不**取代 ask 管線上的 monitoring 側車。

**三張測試票（2026-05-25 封存）**

- **TEST-SUB-001（單檔 bugfix）**：`implementation-worker` 只改戰車根 `subagents/context_routing.py` 一處 regex（`kpis?).` → 詞邊界 `\bkpi?s?\b`），其餘邏輯不動；`checker-reviewer` 跑兩條 unittest 與 one-liner route 驗證全綠。結論：**`accepted_with_gaps`**（建議另票補 KPI-only regression test）。
- **TEST-SUB-002（文檔澄清）**：`governance-guard` **`allow`**，條件鎖在 `50_context_entry_runbook.md` §6.7；worker 僅在該節補「HTTP `expose_monitoring_graph` 閘門 ≠ 保證頂層 `monitoring_graph` 鍵」與管線前提 cross-ref；**未**改 AGENTS／core／暗部。checker：**`accepted`**，23 tests OK。
- **TEST-SUB-003（過度擴張）**：proposal 單票同時動 AGENTS、合約、`.cursor/rules`、monitoring_graph selector、暗部 adapter；guard **`stop_work`**，`allowed_worker=none`。未進 worker／checker。

**派工三原則**

| 情境 | 做法 |
|------|------|
| **何時直派 worker** | 票面 `primary_target` 為**單檔／單模組**、路徑已在 guard `allowed_paths`、不涉及制度檔或憲法 §7 禁區類型；可先 `repo-researcher`（可選）→ `implementation-worker` → `checker-reviewer`。 |
| **何時必經 governance-guard** | 觸及 `AGENTS.md`、`ENGINEERING_CONTRACT.md`、`.cursor/rules`、暗部 `core`、跨多檔／多域、selector／L0–L2 升格、或 runbook 未明示邊界之制度變更。 |
| **何種 proposal → stop_work** | 單票捆綁多制度檔 + 實作 + 暗部；違 Rule-3／8、STOP-8.8、本檔 Monitoring Graph **僅 L0**、runbook §6.8 升格門檻等；guard 標 **`allowed_worker=none`** 時**不得**派 worker。 |

**索引**：`.cursor/agents/DISPATCH_GUIDE.md` · `04_Workflows/OPS_CYCLE.md`（Subagents 工單與戰報）· `workflow_upgrade/90_run_queue.md`（`TEST-SUB-00X` 列）。

---

## 常用 Runner（索引：`Master_Map.json` → `runners`）

| 用途 | 指令 |
|------|------|
| 進主艙 | `. .\04_Workflows\Enter-Main.ps1` |
| 進副艙 | `. .\04_Workflows\Enter-Agency.ps1` |
| 三鑰盲測 | `python .\04_Workflows\_smoke_test_keys.py` |
| 雙艙體檢 | `python .\04_Workflows\_doctor_main_cabin.py` / `_doctor_agency_cabin.py` |
| Telegram 啟停 | `Start-TelegramListener.ps1` / `Stop-TelegramListener.ps1` |
| 發動下一波 | `python .\04_Workflows\_factory_wave_01.py --n 100 --every 10` |
| 任務路由 | `python .\04_Workflows\_route_task.py --type hq.governance` |
| 營運週期 | `python .\04_Workflows\_ops_cycle.py checklist --mode full` |

---

## 使用者口令

- **「接戰」** → 等同執行 §初始化校準。
- **「封存」** → 等同執行 §封存協議。
- **標準交接**：複製檔首 **§交接一句話** 給新對話即可。

---

§封存協議 — 退場與寫回流程

大唐副官：每次作戰結束時，依下列順序完成封存，確保工作流記憶與制度同步——

1. 執行證據封存  
   - 保留本輪實際執行之 CLI 輸出與結構化結果（包含 `ok` 欄位與 `RUNTIME_METRIC`）。

2. 里程碑封存  
   - 如涉及 Gov Core 流程（例如 `ingest_verify`），確認或追加：  
     - `04_Workflows/project_status/master_status.md` 中對應日期的里程碑區塊。

3. 戰報封存  
   - 於 `04_Workflows/00_Agent_Work_Progress.md` 文末 append 一條本輪戰報，至少包含：  
     - 執行了哪些檔案與命令。  
     - 關鍵結構化結果（例如 chunks、sources、hits、latency）。  
     - 阻塞與風隠。  
     - 下一步建議。  
   - 建議先以 `OPS_CYCLE.md` 欄位組裝 JSON，執行 `_ops_cycle.py validate-report`／`append-report`（見 §初始化校準第 9 步）。  

4. Runbook 校正  
   - 若本輪實際執行步驟與既有 runbook 差異重大：  
     - 先於戰報中說明差異與原因。  
     - 再提出 runbook 更新建議（版本升級或補充說明），由尚書省裁決後更新正式檔案。

5. 標準校正  
   - 若本輪驗收標準有變動（例如新增欄位或判定條件）：  
     - 於戰報中標記。  
     - 經裁決後更新 `04_Workflows/00_Agent_Work_Conditions.md` 中相應條目。

6. 禁區確認  
   - 封存前再次確認：本輪未違反憲法禁區（DarkOps、.env、`runtime/checkpoints/**` 等）。  
   - 若曾接觸邊界，須在戰報中留下明確紀錄與理由。

大唐副官：`D:\大唐三省六部\AGENTS.md` 載入後，依本「§封存協議」完成記憶封裝，始得視為本輪作戰正式封箱。
