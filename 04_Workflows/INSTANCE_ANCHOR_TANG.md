# 本戰車實例錨點（大唐）

> **角色**：**僅**承載 W0 所列 23 條實例錨點與本機可操作路徑；可移植制度見三件套（W1–W3），條目索引見 `_PORTABLE_CORE_INDEX.md`。  
> **對照**：`_PORTABLE_CORE_INDEX.md` §2（I01–I23）；路徑權威 `04_Workflows/Master_Map.json`（唯讀）。  
> **版本**：由尚書省裁決；本文不自標定稿號。

---

## 1. 文件定位與三件套交叉引用

| 項目 | 說明 |
|------|------|
| **讀者** | 副官接戰、執行 worker、盲測 W4、尚書省驗收 |
| **禁止** | 把本文條文複製進三件套正文；**禁止**在本文重寫憲法級可移植原則（見下表「原則歸屬」） |
| **權威** | 路徑／runner／cabin／artifacts／`war_status` 以 `04_Workflows/Master_Map.json` 為準；本文為**本戰車快照與操作錨點** |

### 1.1 三件套分工（一句＋章節）

| 檔名 | 職責 | 本檔承接之 W0 |
|------|------|----------------|
| `HARNESS_CONSTITUTION.md`（W1） | 禁區**類型**（Z-*）、四域、HQ 角色、Pipeline **制度** | I03／I07 的**具體路徑** → 本文 §4 |
| `ENGINEERING_CONTRACT.md`（W2） | 工程流派、12-rule、Work Report、附錄 B **JSON 形狀** | I22 **鍵名／斷言字串** → 本文 §7.1 |
| `DEPARTMENT_MAP.md`（W3） | 六部鍵、aliases、cabin **角色**、artifacts **類型名** | I15／I16／I17 **實例落點** → 本文 §6、§3、§7 |
| `00_Agent_Work_Conditions.md` | 長期制度母本（仍含待遷移之實例段，見 Work Report） | I01–I06 實例已收斂至本文 |
| `00_Agent_Work_Progress.md` | 當輪迭代、阻塞、QA 列 | I04／I05／I09 狀態以 Progress 為準；本文 §10 為快照 |
| `AGENTS.md` | 接戰／封存口令與初始化入口 | I10–I13 → 本文 §9 |

### 1.2 原則歸屬（本文不展開）

| 主題 | 讀哪裡 |
|------|--------|
| 黑板僅末尾追加、停工、衝突位階 | W1 §5–§6、§11 |
| `dict` 契約、fallback、DoD、Work Report 格式 | W2 §2、§7、§10、附錄 A |
| 六部／cabin 角色／四 Agent 邊界 | W3 §3、§6–§7；細則 W1 §9 |
| C01–C38 全文索引 | `_PORTABLE_CORE_INDEX.md` §1 |

---

## 2. 專案根與暗部根（I01–I02）

| 錨點 | 絕對路徑 |
|------|----------|
| **戰車專案根** | `D:\大唐三省六部\` |
| **暗部唯一工作區根** | `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\` |

**定案約束**：

- 同目錄承載 venv（環境層）與業務層（`core\`、`Departments\`、`dark_ops\`、`output\` 等）。
- **不得**假設、建立或搬移至 `D:\大唐三省六部\gov_core_system\`。
- 遷移須另開戰役並更新 `04_Workflows\Master_Map.json` 與 `00_Agent_Work_Progress.md`。

---

## 3. Cabins：venv 與進入方式（I16）

| 艙 | venv 目錄 | Python 直執 | 進入方式 |
|----|-----------|-------------|----------|
| **gov_main** | `D:\大唐三省六部\01_Environments\python_venvs\gov_main` | `...\gov_main\Scripts\python.exe` | 戰車根執行：`. .\04_Workflows\Enter-Main.ps1`（點源後 activation 持續） |
| **gov_agency** | `D:\大唐三省六部\01_Environments\python_venvs\gov_agency` | `...\gov_agency\Scripts\python.exe` | `. .\04_Workflows\Enter-Agency.ps1` |
| **gov_core_system** | `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system` | `...\gov_core_system\Scripts\python.exe` | 手動：`cd` 至 venv 目錄後 `.\Scripts\Activate.ps1`；暗部 agent 多在此 venv 下執行 |

**鎖檔**：`01_Environments\requirements.main.lock.txt`、`requirements.agency.lock.txt`；統包艙 freeze 備份見戰車根 `requirements.txt`。

**體檢 runner**：`python .\04_Workflows\_doctor_main_cabin.py`／`_doctor_agency_cabin.py`（地圖鍵 `doctor_main_cabin`／`doctor_agency_cabin`）。

---

## 4. 禁區具體路徑與憲法 Z-* 對照（I03、I07）

> 類型定義與違規後果見 `HARNESS_CONSTITUTION.md` §7；下表為**本戰車逐條路徑**。

| Z-* 類型 | 憲法語意 | 本戰車路徑（絕對） |
|----------|----------|-------------------|
| **Z-VENV-TREE** | 暗部 venv 解釋器／套件樹 | `...\gov_core_system\Scripts\`、`Lib\`、`Include\`、`share\` |
| **Z-ENV** | 環境與密鑰檔 | `...\gov_core_system\.env`、`...\gov_core_system\.env.example`（除非單獨開票） |
| **Z-RUNTIME-CP** | 執行態檢查點 | `...\gov_core_system\runtime\checkpoints\` |
| **Z-ORCH-DESTRUCT** | 編排破壞性腳本／模組 | `...\Departments\01_Orchestration\scripts\prune_checkpoints.ps1`、`...\Departments\01_Orchestration\workflow\checkpoint.py` |
| **Z-DARK-OPS** | 暗部維運清理腳本 | `...\gov_core_system\dark_ops\scripts\small_keepnewest.ps1` |
| **Z-HQ-LIQUIDATION** | 總部清算／破壞測試 | `D:\大唐三省六部\04_Workflows\Cleanup_Check.py`、`_cleanup_and_recovery.py`、`_execute_liquidation.py`、`_dry_run_liquidation.py`、`_destruction_test.py` |
| **Z-HQ-ENV-EDIT** | 全域禁止：改根 env、刪驗證腳本、搬目錄 | **根 env**：`D:\大唐三省六部\01_Environments\.env`（嚴禁未授權修改）；**Phase1 驗證腳本（禁刪）**：`...\Departments\04_Infrastructure\scripts\phase1_verify.py`；**目錄結構**：六部根與 `gov_core_system` 下既有 `Departments\01–06` 不得擅自搬移 |

### 4.1 暗部硬禁區清單（與上表對齊）

- `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Scripts\`
- `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Lib\`
- `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Include\`
- `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\share\`
- `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\.env`（含 `.env.example`，除非單獨開票）
- `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\runtime\checkpoints\`
- `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Departments\01_Orchestration\scripts\prune_checkpoints.ps1`
- `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Departments\01_Orchestration\workflow\checkpoint.py`
- `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\dark_ops\scripts\small_keepnewest.ps1`

### 4.2 總部清算類

- `D:\大唐三省六部\04_Workflows\Cleanup_Check.py`
- `D:\大唐三省六部\04_Workflows\_cleanup_and_recovery.py`
- `D:\大唐三省六部\04_Workflows\_execute_liquidation.py`
- `D:\大唐三省六部\04_Workflows\_dry_run_liquidation.py`
- `D:\大唐三省六部\04_Workflows\_destruction_test.py`

### 4.3 戰車級 `.env`（Z-ENV／Z-HQ-ENV-EDIT）

- `D:\大唐三省六部\01_Environments\.env` — 由 `gov_paths.get_secret` 載入；**嚴禁**在對話／log 印出全文。

---

## 5. HQ worker 可碰絕對路徑（I06）

| Worker | 可碰路徑 |
|--------|----------|
| **HQ-Governance-Worker** | `D:\大唐三省六部\04_Workflows\00_Agent_Work_Conditions.md`、`D:\大唐三省六部\04_Workflows\00_Agent_Work_Progress.md`（僅末尾追加） |
| **HQ-Tooling-Worker** | `D:\大唐三省六部\01_Environments\config\services\`、`tools\`、`mcp\`、`mcp\_registry\` |
| **DarkOps-Worker** | 暗部根內 — **第一階段 Blocked** |
| **QA-Reviewer** | 全樹唯讀；Progress 末尾 QA 列 |

---

## 6. 執行態 Artifacts（I15、C37 實例）

> W3 僅列類型名；下表對齊 `Master_Map.json` → `artifacts`（2026-05-19 快照）。

| 地圖鍵 | 相對路徑 | 絕對路徑 |
|--------|----------|----------|
| `master_map` | `04_Workflows/Master_Map.json` | `D:\大唐三省六部\04_Workflows\Master_Map.json` |
| `current_plan` | `04_Workflows/current_plan.json` | `D:\大唐三省六部\04_Workflows\current_plan.json` |
| `status_json` | `04_Workflows/Status.json` | `D:\大唐三省六部\04_Workflows\Status.json` |
| `maps_legacy` | `04_Workflows/maps/Master_Map.json` | `D:\大唐三省六部\04_Workflows\maps\Master_Map.json` |
| `chariot_registry` | `04_Workflows/Chariot_Registry.db` | `D:\大唐三省六部\04_Workflows\Chariot_Registry.db` |
| `cursor_agent_rules` | `04_Workflows/CURSOR_AGENT_RULES.md` | `D:\大唐三省六部\04_Workflows\CURSOR_AGENT_RULES.md` |
| `engineering_contract_mdc` | `.cursor/rules/engineering-contract.mdc` | `D:\大唐三省六部\.cursor\rules\engineering-contract.mdc` |

**禁新建**：`hashes.txt`（指紋只走 `chariot_registry`；制度見 W1 §7.3）。

---

## 7. Pipeline 元資料帳本（I17、I22）

| 項目 | 值 |
|------|-----|
| **SDK 模組** | `D:\大唐三省六部\02_Agents_Core\pipeline_meta.py` |
| **DEFAULT_DB（程式常數）** | `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Departments\05_Data_Vault\pipeline_meta\code_cleaning_pipeline_v2_meta.db` |
| **地圖鍵** | `runners.pipeline_meta_db`（同上相對路徑） |
| **初始化腳本** | `04_Workflows\_init_pipeline_meta.py` |
| **查詢腳本** | `04_Workflows\_pipeline_meta_query.py` |
| **README** | `...\Departments\05_Data_Vault\pipeline_meta\README.md` |
| **預設 pipeline 名** | `code_cleaning_pipeline_v2`（`PIPELINE_NAME_DEFAULT`） |
| **接入範例** | `02_Agents_Core\Code_Cleaner_Throttled_Agent.py`（`job_run` context） |

**docker-compose（暗部基設）**：`01_Environments\python_venvs\gov_core_system\Departments\04_Infrastructure\docker-compose.yml`

### 7.1 驗證／ingest 相關鍵名（形狀對照源碼，I22）

| 用途 | 鍵／集合名 |
|------|-----------|
| Qdrant collection（Phase1 範例） | `document_chunks` |
| Postgres 連線語意 | `pg_ok`（`DATABASE_URL` 驅動） |
| Phase1 斷言字串 | `ASSERT: OK (INV1–INV4 satisfied for phase1 seed)`、`OK: verify passed` |
| ingest 彙總語意 | `verify_ok` |

---

## 8. 環境變數與密鑰（I23、I19）

**`.env` 路徑**：`D:\大唐三省六部\01_Environments\.env`

| 鍵名 | 用途 | 盲測 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI | `_smoke_test_keys.py` → `[OK]`／`[FAILED]` |
| `GROQ_API_KEY` | Groq | 同上 |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot | 同上 |
| `DATABASE_URL` | Postgres | Infra／`phase1_verify` 路徑 |
| `QDRANT_URL` | Qdrant（缺省可 `http://127.0.0.1:6333`） | Infra health |
| `POSTGRES_PASSWORD` | Docker Postgres（compose env_file） | 輪替：`04_Workflows\_rotate_postgres_password.py` |

**擴充盲測**：`04_Workflows\_smoke_test_keys_extended.py`（多供應商，**不含** Gemini）。

**輪替戰史（快照）**：`Master_Map.json` → `secrets_status.rotated_at` = `2026-05-09`；三鍵 `rotated_and_verified`。

**政策**：嚴禁將金鑰字串輸出至 stdout／stderr 或事件 log。

---

## 9. 常用 Runner 與 AGENTS 錨點（I10–I13、I11、I15）

### 9.1 交接句（I10）

- **接戰**：`大唐副官：D:\大唐三省六部\AGENTS.md 載入後依 §初始化校準執行，待命。`
- **封存**：`大唐副官：依 D:\大唐三省六部\AGENTS.md §封存協議執行記憶封裝。`

### 9.2 初始化相關檔名（I13）

| 檔案 | 用途 |
|------|------|
| `04_Workflows\Status.json` | 最後管線／評估狀態 |
| `04_Workflows\.telegram_listener.lock` | Telegram 監聽 PID（禁雙開） |
| `04_Workflows\Chariot_Registry.db` | 指紋 registry（禁新建 `hashes.txt`） |
| `02_Agents_Core\Base_Agent.py` | Run_ID、`get_path` 律法 |

### 9.3 Runners 全表（I11、I15；摘自 `Master_Map.json` → `runners`）

| 鍵 | 相對路徑 |
|----|----------|
| `enter_main` | `04_Workflows/Enter-Main.ps1` |
| `enter_agency` | `04_Workflows/Enter-Agency.ps1` |
| `telegram_listener_start` | `04_Workflows/Start-TelegramListener.ps1` |
| `telegram_listener_stop` | `04_Workflows/Stop-TelegramListener.ps1` |
| `smoke_test_keys` | `04_Workflows/_smoke_test_keys.py` |
| `smoke_test_keys_extended` | `04_Workflows/_smoke_test_keys_extended.py` |
| `doctor_main_cabin` | `04_Workflows/_doctor_main_cabin.py` |
| `doctor_agency_cabin` | `04_Workflows/_doctor_agency_cabin.py` |
| `factory_wave_01` | `04_Workflows/_factory_wave_01.py` |
| `factory_pipeline_yaml` | `01_Environments/config/factory_pipeline.yaml` |
| `model_registry_groq` | `01_Environments/config/model_registry.yaml` |
| `readme_handoff` | `README_Refresher.md` |
| `register_fingerprints_baseline` | `04_Workflows/_register_fingerprints.py` |
| `inbound_watchdog_py` | `04_Workflows/_inbound_watchdog.py` |
| `inbound_watchdog_start` | `04_Workflows/Start-InboundWatchdog.ps1` |
| `scout_engine_py` | `04_Workflows/_scout_engine.py` |
| `scout_engine_start` | `04_Workflows/Start-ScoutEngine.ps1` |
| `build_elite_index` | `04_Workflows/_build_elite_index.py` |
| `report_generator_closeout` | `04_Workflows/_report_generator.py` |
| `integration_v256_closeout` | `04_Workflows/_integration_v256_scout_closeout.py` |
| `launch_warpath` | `04_Workflows/Launch-Warpath.ps1` |
| `setup_schedule_warpath` | `04_Workflows/Setup-Schedule.ps1` |
| `stop_warpath_schedule` | `04_Workflows/Stop-WarpathSchedule.ps1` |
| `scheduler_last_run_log` | `06_Exports_Output/reports/scheduler/last_run.log` |
| `scheduler_setup_audit_log` | `06_Exports_Output/reports/scheduler/setup_register.log` |
| `warpath_alert` | `04_Workflows/_warpath_alert.py` |
| `tang_http_smart_failover` | `04_Workflows/_tang_http.py` |
| `groq_quota_state` | `06_Exports_Output/reports/groq_quota_state.json` |
| `docker_compose_gov_core_system` | `01_Environments/python_venvs/gov_core_system/Departments/04_Infrastructure/docker-compose.yml` |
| `requirements_gov_core_freeze` | `requirements.txt` |
| `code_cleaning_pipeline_v2_spec` | `01_Environments/python_venvs/gov_core_system/Departments/06_Strategy/code_cleaning_pipeline_v2.md` |
| `pipeline_meta_sdk` | `02_Agents_Core/pipeline_meta.py` |
| `pipeline_meta_init` | `04_Workflows/_init_pipeline_meta.py` |
| `pipeline_meta_db` | `01_Environments/python_venvs/gov_core_system/Departments/05_Data_Vault/pipeline_meta/code_cleaning_pipeline_v2_meta.db` |
| `pipeline_meta_readme` | `01_Environments/python_venvs/gov_core_system/Departments/05_Data_Vault/pipeline_meta/README.md` |
| `code_cleaner_throttled_agent` | `02_Agents_Core/Code_Cleaner_Throttled_Agent.py` |
| `download_dept_docs` | `04_Workflows/_download_dept_docs.py` |
| `scan_dept_refs` | `04_Workflows/_scan_dept_refs.py` |
| `rotate_postgres_password` | `04_Workflows/_rotate_postgres_password.py` |
| `gov_core_orchestration_smoke` | `01_Environments/python_venvs/gov_core_system/Departments/01_Orchestration/smoke_test.py` |
| `gov_core_orchestration_main` | `01_Environments/python_venvs/gov_core_system/Departments/01_Orchestration/main.py` |
| `gov_core_checkpoint_module` | `01_Environments/python_venvs/gov_core_system/Departments/01_Orchestration/workflow/checkpoint.py` |
| `gov_core_prune_checkpoints_ps1` | `01_Environments/python_venvs/gov_core_system/Departments/01_Orchestration/scripts/prune_checkpoints.ps1` |
| `gov_core_checkpoint_readme` | `01_Environments/python_venvs/gov_core_system/Departments/01_Orchestration/README_gov_core_checkpoint.md` |
| `agents_md` | `AGENTS.md` |
| `hq_config_root` | `01_Environments/config` |
| `hq_superpowers` | `01_Environments/config/cursor/superpowers` |
| `hq_graphify` | `01_Environments/config/tools/graphify` |
| `hq_9router` | `01_Environments/config/tools/9router` |
| `hq_spec_kit_reserved` | `01_Environments/config/tools/spec-kit` |
| `hq_playwright_mcp` | `01_Environments/config/mcp/playwright` |
| `hq_mcp_registry` | `01_Environments/config/mcp/_registry` |
| `hq_agentmemory_service` | `01_Environments/config/services/agentmemory` |
| `hq_agentmemory_compose` | `01_Environments/config/services/agentmemory/repo/docker-compose.yml` |
| `hq_reserved_cloakbrowser` | `05_Temp_Cache/staging/reserved/cloakbrowser` |
| `hq_reserved_multica` | `05_Temp_Cache/staging/reserved/multica` |
| `cursor_agent_rules` | `04_Workflows/CURSOR_AGENT_RULES.md` |
| `engineering_contract_mdc` | `.cursor/rules/engineering-contract.mdc` |
| `harness_constitution` | `04_Workflows/HARNESS_CONSTITUTION.md` |
| `engineering_contract` | `04_Workflows/ENGINEERING_CONTRACT.md` |
| `department_map` | `04_Workflows/DEPARTMENT_MAP.md` |
| `instance_anchor_tang` | `04_Workflows/INSTANCE_ANCHOR_TANG.md` |

地圖升版後以 JSON diff 更新本表；禁止在程式硬編絕對路徑。

### 9.4 封存 SOP 錨點（I12）

- **SOP 憲法版本**：`README_Refresher.md` 標 **v2.61**（與 `Master_Map.version` 對齊）。
- **點火**：`cd D:\大唐三省六部` → `Enter-Main.ps1` 或 `Enter-Agency.ps1`（見 `README_Refresher.md` §1）。
- **指紋**：`python 04_Workflows\_register_fingerprints.py`。

---

## 10. 進度與戰史錨點（I04–I09、I14、I18–I21）

### 10.1 當前總目標／階段（I04）

- Phase1 基線：Postgres、Qdrant、`.env` 對齊、`phase1_verify` 已 `ASSERT: OK`。
- 第二階段進行中：真實 ingest、RAG 問答、Governance 一鍵流與狀態檔自動寫回（**詳見** `00_Agent_Work_Progress.md`）。

### 10.2 HQ 輪定案（I05）

- **日期定案**：2026-05-17  
- **DarkOps-Worker**：**Blocked**（第一階段僅總部治理層與工具層施工）

### 10.3 Master_Map 版本與戰史（I08、I14、I18）

| 項目 | 值（`Master_Map.json` 快照） |
|------|------------------------------|
| `Master_Map.version` | **2.61** |
| `war_status.constitution_version` | v2.61 |
| `war_status.as_of` | 2026-05-17 |
| `war_status.frozen_at_iso_utc` | 2026-05-17T09:30:38Z |
| **headline** | v2.61 封存：Phase 2 工程規則轉制（`CURSOR_AGENT_RULES.md` + `engineering-contract.mdc`）；Gov Core V1 smoke 基線維持；精煉 run_id=c0fa044a…；Telegram lock 仍缺席 |

**description 戰史摘要（節錄 v2.51→v2.61）**：雙艙 venv、金鑰輪換、Launch-Warpath 排程、Groq 撥彈、刑部哨兵／偵察兵、elite_cache／結案報告、gov_core_system 統包艙與 docker-compose、pipeline_meta SDK、06_Strategy、Postgres 密碼輪替、upstream docs 同步、checkpoint prune、Phase2B Cursor rules 條文化。

**里程碑摘要（節錄，全文見 `war_status.milestones`）**：

- Chariot_Registry 全艦掃描 20074 targets，failures=0  
- 三鑰盲測 OpenAI／Groq／Telegram = [OK]  
- pipeline_meta SDK + Code_Cleaner job_run 煙測  
- gov_core LangGraph + checkpoint mock  
- v2.60 HQ 工具層 config 集中  
- v2.61 Phase2B：`CURSOR_AGENT_RULES.md` + `engineering-contract.mdc`（81 段 alwaysApply）

**Phase2B 規則錨點（`war_status.wave_phase2_harness`）**：

| 鍵 | 相對路徑 |
|----|----------|
| `human_readable` | `04_Workflows/CURSOR_AGENT_RULES.md` |
| `cursor_rule` | `.cursor/rules/engineering-contract.mdc` |
| `mother_contract` | `04_Workflows/ENGINEERING_CONTRACT.md` |
| `constitution` | `04_Workflows/HARNESS_CONSTITUTION.md` |

**Telegram 監聽（封存快照）**：`war_status.telegram_listener.lock_exists_at_freeze` = false；接戰前執行 `Start-TelegramListener.ps1`（見地圖 `runners.telegram_listener_start`）。

### 10.4 Progress 里程碑代號（I09）

| Agent | 代號 | 狀態（Progress 基線） |
|-------|------|------------------------|
| Infra | I0／I1 | 已完成 |
| Data | D1–D3 | 已完成 |
| RAG | R1／R2 | 已完成 |
| Governance | G1 | 已完成 |
| Gov Core V1 | — | 已封版（2026-05-15）；後續歸 V2／維運專案 |

### 10.5 模型與配額（I20）

- **登記檔**：`01_Environments\config\model_registry.yaml`  
- **Groq 429 換模順序（快照）**：`llama-3.3-70b-versatile` → `qwen/qwen3-32b` → `llama-3.1-8b-instant`  
- **RPD 狀態檔**：`06_Exports_Output\reports\groq_quota_state.json`  

### 10.6 Wave／業務指標（I21）

| 來源 | 快照 |
|------|------|
| 末筆 Asset_Value（`war_status` 2026-05-17 條目） | `run_id=c0fa044acf1c40c1a3570fd5d5abbcac`，sampled=100，avg≈5.019 |
| `wave_01` | run_id `25c67a4d…`，avg≈5.101 |
| `wave_02_scheduled` | run_id `c78fbe28…`，avg≈5.067 |
| `Status.json` | `business_metrics` 等欄位見當期 JSON |

---

## 11. 暗部 Departments 實例路徑（I15 延伸）

| 編號 | 絕對路徑 |
|------|----------|
| 01_Orchestration | `D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Departments\01_Orchestration` |
| 02_Brain_GraphRAG | `...\Departments\02_Brain_GraphRAG` |
| 03_Observability | `...\Departments\03_Observability` |
| 04_Infrastructure | `...\Departments\04_Infrastructure` |
| 05_Data_Vault | `...\Departments\05_Data_Vault` |
| 06_Strategy | `...\Departments\06_Strategy` |

**checkpoint 根（相對暗部 venv）**：`runtime\checkpoints`（完整路徑見地圖 `war_status.gov_core_orchestration.checkpoint_root_relative`）。

---

## 12. 工具層與 IDE 路徑（I19、使用者家目錄）

| 項目 | 路徑 |
|------|------|
| HQ config 根 | `D:\大唐三省六部\01_Environments\config` |
| Cursor MCP（使用者層） | `%USERPROFILE%\.cursor\mcp.json` |
| Superpowers 插件 | `%USERPROFILE%\.cursor\plugins\superpowers`（v5.1.0 快照；HQ 登記 `config\cursor\superpowers`） |
| Agentmemory compose | `01_Environments\config\services\agentmemory\repo\docker-compose.yml` |
| 排程任務名 | `Tang_Chariot_Auto_Refine`（每日 03:00 + AtLogOn，見 `Setup-Schedule.ps1`） |

**暗部 venv 政策**：嚴禁 pip／uv 向 `gov_core_system` 安裝 HQ 工具套件（地圖 `war_status.hq_tools.dark_venv_policy`）。

---

## 13. 本戰車錨點（一頁總表）

| 類別 | 錨點 |
|------|------|
| 根 | `D:\大唐三省六部\` |
| 暗部根 | `...\python_venvs\gov_core_system\` |
| 主艙進入 | `. .\04_Workflows\Enter-Main.ps1` |
| 副艙進入 | `. .\04_Workflows\Enter-Agency.ps1` |
| 統包艙 Python | `...\gov_core_system\Scripts\python.exe` |
| `.env` | `01_Environments\.env` |
| pipeline DB | `...\05_Data_Vault\pipeline_meta\code_cleaning_pipeline_v2_meta.db` |
| 指紋 DB | `04_Workflows\Chariot_Registry.db` |
| 地圖版本 | Master_Map **2.61** |
| 盲測 | `python 04_Workflows\_smoke_test_keys.py` |
| 接戰入口 | `AGENTS.md` @ 戰車根 |
| 三件套 | `HARNESS_CONSTITUTION.md`／`ENGINEERING_CONTRACT.md`／`DEPARTMENT_MAP.md` |

---

## 附錄：W0 實例條目對照

| 條號 | 本章節 |
|------|--------|
| I01–I02 | §2 |
| I03、I07 | §4 |
| I04 | §10.1 |
| I05 | §10.2 |
| I06 | §5 |
| I08–I09 | §10.3–10.4 |
| I10–I13 | §9.1–9.2 |
| I11、I14–I15 | §9.3–9.4、§10.3、§6、§11 |
| I16 | §3 |
| I17、I22 | §7 |
| I18、I21 | §10.3、§10.6 |
| I19–I20 | §8、§10.5、§12 |
| I23 | §8 |

---

*W5 定稿候選；地圖權威檔：`04_Workflows/Master_Map.json`。升版後請 diff 地圖並更新 §6、§9.3、§10.3。*
