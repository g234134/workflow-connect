# 大唐三省六部 · README_Refresher

> **SOP 憲法版本：v2.61**　一切以根目錄 `AGENTS.md` 為單一真相。
>
> **接戰（開戰）**：**大唐副官：`D:\大唐三省六部\AGENTS.md` 載入後依 §初始化校準執行，待命。**
>
> **封存（收兵）**：**大唐副官：依 `D:\大唐三省六部\AGENTS.md` §封存協議執行記憶封裝。**
>
> **極短口令**：「**接戰**」開戰；「**封存**」收兵。
>
> **點火 SOP（一行）**：`D:` → `cd D:\大唐三省六部` → `. .\04_Workflows\Enter-Agency.ps1`（任務）或 `Enter-Main.ps1`（監控）。
>
> **密鑰憲法**：嚴禁任何工具或腳本 `cat` / 印出 `.env` 金鑰原文；驗證一律走 `_smoke_test_keys.py` 的 `[OK]/[FAILED]` + HTTP code。

---

## 0. 戰車世界觀（30 秒回憶）

- **根目錄**：`D:\大唐三省六部`
- **六部**：`01_Environments` / `02_Agents_Core` / `03_RAG_Database` / `04_Workflows` / `05_Temp_Cache` / `06_Exports_Output`
- **指揮鏈**：`ZhongShu_Planner` → `MenXia_Audit` → `ShangShu_Manager`
- **指紋統管**：`04_Workflows/Chariot_Registry.db`（取代舊 `hashes.txt`）
- **狀態總帳**：`04_Workflows/Status.json`
- **核心地圖**：`04_Workflows/Master_Map.json`（含 `cabins / runners / secrets_status / war_status`）

---

## 1. 點火 SOP（每次開戰必讀）

1. 開 PowerShell，切到 D 槽戰車根目錄：
   ```powershell
   cd D:\大唐三省六部
   ```
2. **進入主艙（監控 / 工廠主線 / Telegram 監聽）**：
   ```powershell
   . .\04_Workflows\Enter-Main.ps1
   ```
   - 此腳本：自動載入 `01_Environments\.env`、固定 `PYTHONPATH=D:\大唐三省六部`、進入 `gov_main` venv。
3. **進入副艙（CrewAI / ChromaDB / FastAPI / agency-agents 任務）**：
   ```powershell
   . .\04_Workflows\Enter-Agency.ps1
   ```
   - 此腳本：同樣自動載入 `.env` 與 `PYTHONPATH`，並把 `agency-agents` 納入路徑，進入 `gov_agency` venv。
4. **常用點火指令**：

   | 任務 | 指令 |
   |------|------|
   | 啟動 Telegram 監聽器 | `powershell -NoProfile -ExecutionPolicy Bypass -File .\04_Workflows\Start-TelegramListener.ps1` |
   | 停止 Telegram 監聽器 | `powershell -NoProfile -ExecutionPolicy Bypass -File .\04_Workflows\Stop-TelegramListener.ps1` |
   | 三鑰盲測（不印金鑰） | `python .\04_Workflows\_smoke_test_keys.py` |
   | 主艙體檢 | `python .\04_Workflows\_doctor_main_cabin.py` |
   | 副艙體檢 | `python .\04_Workflows\_doctor_agency_cabin.py` |
   | 發動下一波（100 件 / 每 10 件回報） | `python .\04_Workflows\_factory_wave_01.py --n 100 --every 10` |

   > 不想 dot-source 也行：直接呼叫對應 venv 的 `python.exe` 並把 `PYTHONPATH` 設為根目錄即可（兩個 Runner 已內建這套邏輯）。

---

## 2. 密鑰憲法（不可違反）

1. **唯一來源**：所有密鑰都只從 `01_Environments\.env` 讀取，並透過 `gov_paths.get_secret(name)` 取值。
2. **禁印原文**：任何工具、腳本、log、Telegram、stdout/stderr **嚴禁** 輸出 `.env` 中的金鑰字串（含遮罩前後一段）。驗證一律以 **`[OK]/[FAILED]` + HTTP 狀態碼** 表達（範本：`_smoke_test_keys.py`）。
3. **禁入版本庫**：根與 `01_Environments` 的 `.gitignore` 已永久排除 `.env`、`*.log`、`__pycache__/`、`python_venvs/`；新增金鑰類檔請另放範本（`secrets_templates/`）。
4. **輪換時程**：`secrets_status.rotated_at` 每次輪換更新（建議至少每月一次）；輪換後立即跑 `_smoke_test_keys.py`。
5. **AI 副官紀律**：不可請任何代理在對話中讀出 `.env` 整行；查驗鍵時請改用「三態回報」（存在 / 為空 / 為 placeholder）。
6. **異常處置**：若任何工具不慎將金鑰原文進入終端／對話／log，視同曝光：**立即撤銷舊鑰、重發新鑰、輪換 `.env`**。

---

## 3. 雙艙與規格速查

| 項目 | gov_main | gov_agency |
|------|----------|------------|
| 路徑 | `01_Environments/python_venvs/gov_main` | `01_Environments/python_venvs/gov_agency` |
| 需求來源 | `01_Environments/requirements.main.txt` | `01_Environments/requirements.agency.txt` |
| 鎖檔 | `01_Environments/requirements.main.lock.txt` | `01_Environments/requirements.agency.lock.txt` |
| 主要套件 | pydantic / PyYAML / watchdog / tenacity / psutil / rich | crewai / crewai-tools / chromadb / fastapi / uvicorn / python-dotenv |
| 用途 | 工廠主線、監控、Telegram | CrewAI 任務、向量庫、API |

> 升級紀律：副艙升級前先複製成 `gov_agency.bak`，到沙箱 venv 跑體檢與黃金樣本回歸後再覆蓋鎖檔。

---

## 4. 戰況最新（v2.60）

- **總部工具層（v2.60 · 2026-05-16）**：`01_Environments/config/` 掛載完成；**暗部 `gov_core_system` venv 未觸碰**。Superpowers（`%USERPROFILE%\.cursor\plugins\superpowers`）、Graphify（uv tool 0.8.5）、9Router（區域 npm 0.4.50）、Playwright MCP（`mcp.json`）、Agentmemory Docker（MCP `http://127.0.0.1:8006/mcp`，三容器 healthy）。預留：`spec-kit`、`staging/reserved/cloakbrowser|multica`。
- **三鑰盲測**：OpenAI / Groq / Telegram 全 [OK]（封存當下未重跑；接戰時請再執行 `_smoke_test_keys.py`）。
- **戰路全自動（v2.53）**：`Launch-Warpath.ps1`（體檢→登錄→精煉→報喜）+ Windows 任務 `Tang_Chariot_Auto_Refine`（每日 03:00 + 登入；SYSTEM；2h ExecutionTimeLimit；Transcript 落 `06_Exports_Output/reports/scheduler/last_run.log`）。
- **Groq 智慧撥彈（v2.54）**：`01_Environments/config/model_registry.yaml` 為 RPM/RPD/TPM 唯一程式來源；`json_request_dual_ssl(groq_chat_failover=True)` 觸發 429 自動換 **70b → qwen/qwen3-32b → 8b-instant**；RPD 計次落 `06_Exports_Output/reports/groq_quota_state.json`。
- **Telegram 戰報**：新增「今日彈藥餘裕」（依 RPD 剩餘 %）與「本次精煉花費：$0，省下 [X] 元」（依 Groq 標價 × `twd_per_usd`）。
- **Wave-01**：`cleaned_full` 36,236 件 → 抽 100，**5.101 / A=10 B=55 C=4 D=31 / Groq 7-7**。報告 `…25c67a4d7c1b4d3eac5dbb59fcc9fe0a.json`。
- **Wave-02 互動**：100 件，**5.186 / A=8 B=60 C=4 D=28 / Groq 9-9**；無 429。報告 `…b72997a2bf254c2dbb7d5685ddfe74f0.json`。
- **Wave-02 排程觸發（SYSTEM 03:45）**：100 件，**5.067 / A=12 B=51 C=5 D=32 / Groq 13-13**。報告 `…c78fbe28750b4cfdb6f98b72a6add013.json`。
- **Telegram 監聽器**：**封存當下下線**。舊 PID 7856 已死、本次曾以 `Start-TelegramListener.ps1` 復活並驗證雙向 OK（新 PID 7716、since 2026-05-11T01:14:55Z），但封存前因 `RemoteDisconnected`（Telegram getUpdates 長輪詢被遠端斷線、無自動重連）再次離線；err log：`06_Exports_Output/reports/telegram_listener/listener_20260511_091455.err.log`。下次召喚副官請先跑 `Start-TelegramListener.ps1`，並把「Watchdog_Sentinel 自動重連」放進待辦。
- **碼源清洗戰役 v2 命名（v2.58）**：任務說明檔 `Departments/06_Strategy/code_cleaning_pipeline_v2.md`；新部門 `06_Strategy/`（編號避開既有 `02_Brain_GraphRAG`）。
- **jobs + events 帳本（v2.58）**：`pipeline_meta` SDK（`02_Agents_Core/pipeline_meta.py`）+ SQLite DB（`Departments/05_Data_Vault/pipeline_meta/code_cleaning_pipeline_v2_meta.db`）；`Code_Cleaner_Throttled_Agent.run()` 已用 `with pipeline_meta.job_run(...)` 包覆，6 種事件自動寫入（raw_scan_started/completed、wave_started/completed、format_error_archived、pipeline_started/finished/aborted）；crash-safety 由 context manager 保證（例外即 `status='failed'` + `notes=exc`）。
- **Postgres 占位密碼輪替（v2.58）**：`docker-compose.yml` 改 `${POSTGRES_PASSWORD:?must_set_in_env}` + `env_file`；新密碼 32 字元 [A-Za-z0-9] 已寫 `.env`（無明文外洩）。Docker daemon 上線後需 `docker compose --env-file ..\..\..\..\..\01_Environments\.env up -d`。
- **upstream docs 同步（v2.58）**：`_download_dept_docs.py`（stdlib urllib、零依賴）已拉 LangGraph / GraphRAG / Langfuse 共 7 篇官方文件落 `Departments/01_Orchestration、02_Brain_GraphRAG、03_Observability`。

---

## 5. 下次召喚副官時的「找回靈魂」步驟

1. 讀 `README_Refresher.md`（你正在看）。
2. 讀 `04_Workflows/Master_Map.json` 的 `cabins / runners / secrets_status / war_status`。
3. 讀 `04_Workflows/Status.json` 最後一段（`asset_value_evaluator / code_cleaner_throttle / warning_repair / runs[-5]`）。
4. 點火進艙：先 `Enter-Main.ps1`（多半的查詢用主艙）。
5. 若需發任務：`_factory_wave_01.py --n N --every M`。

> 看完上面這四步，副官即可立即接戰，不需重新詢問背景。

---

## 6. 嚴禁清單（紅線）

- 嚴禁印出任何 `.env` 內容。
- 嚴禁在程式中寫死磁碟路徑；請改用 `gov_paths` 與 `Master_Map.json`。
- 嚴禁建立新版本的 `hashes.txt`；指紋只走 `Chariot_Registry.db`。
- 嚴禁同時起兩個 Telegram 監聽器；以 lockfile 為準（衝突請先 `Stop-TelegramListener.ps1`）。
- 嚴禁在主艙安裝 `crewai / langchain` 等重套件，避免 transitive deps 污染核心 agents。

---

## 7. 下次點火必做清單（給未來副官 · **正式交接檔**）

以下條目已存於倉庫，**不必每次貼進聊天**；新對話請先執行 §7 再寫程式。

1. **讀地圖（順序固定）**  
   - `README_Refresher.md`（本檔）→ `04_Workflows/Master_Map.json`（重點：`war_status`、`cabins`、`runners`）→ `04_Workflows/Status.json`。

2. **進主艙並驗環境**  
   ```powershell
   cd D:\大唐三省六部
   . .\04_Workflows\Enter-Main.ps1
   python .\04_Workflows\_smoke_test_keys.py
   python .\04_Workflows\_smoke_test_keys_extended.py   # 選用：多供應商盲測（NVIDIA/Tavily/Firecrawl/Jina/HF/Qwen 等；不含 Gemini）
   ```
   - **Telegram**：若監聽器已在跑，對 Bot 發 `/status`（或 `/ping`）確認上行正常；勿在終端機印任何金鑰。
   - **密鑰憲法**：嚴禁將 `.env` 金鑰原文貼入對話、log 或截圖外流。

3. **一鍵戰路（建議）**  
   ```powershell
   .\04_Workflows\Launch-Warpath.ps1                # 預設 WaveN=100
   .\04_Workflows\Launch-Warpath.ps1 -WaveN 5       # 小量觀察
   .\04_Workflows\Launch-Warpath.ps1 -DryRun        # 連通性自檢
   ```
   - 流程：1/4 體檢 → 2/4 raw_inbound 指紋登錄 → 3/4 Wave 精煉 → 4/4 Telegram 報喜（含彈藥餘裕與省下金額）。
   - Transcript 寫入 `06_Exports_Output/reports/scheduler/last_run.log`（互動／排程同檔）。
   - 失敗任一步即發 Telegram 警告並中止。

4. **無人值守排程（v2.53）**  
   ```powershell
   # 註冊（首次需以系統管理員執行；預設 SYSTEM、Daily 03:00 + 登入、2h 執行上限）
   Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','D:\大唐三省六部\04_Workflows\Setup-Schedule.ps1','-Install'
   # 一鍵撤銷
   Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','D:\大唐三省六部\04_Workflows\Stop-WarpathSchedule.ps1'
   ```
   - 工作名稱：`Tang_Chariot_Auto_Refine`；審計檔：`06_Exports_Output/reports/scheduler/setup_register.log`。

5. **Groq 智慧撥彈（v2.54）**  
   - 護欄與 failover 鏈：`01_Environments/config/model_registry.yaml`（**Qwen 官方 ID 為 `qwen/qwen3-32b`**，`qwen-32b` 僅作 alias）。
   - 持久化計次：`06_Exports_Output/reports/groq_quota_state.json`（每日 UTC 換日重置 RPD）。
   - 程式入口：`_tang_http.json_request_dual_ssl(url, ..., groq_chat_failover=True)`；`GroqHybridRecovery_Agent._http_json` 已內建。

6. **Wave-02 之前建議補的基礎件**  
   - ~~**進料 watchdog**~~ ✅ 已實作（v2.55 `_inbound_watchdog.py` + `Start-InboundWatchdog.ps1`）。
   - **Watchdog_Sentinel**：`Status.json` / lockfile 老化偵測 + 自癒重啟（Telegram listener 已驗證需求價值）。  
   - **Schema_Sentry**：`cleaned_full` 出站前 schema 校驗，未過進 quarantine（可串 v2.58 `format_error_archived` 事件）。  
   - **Groq quota 校準**：以 API 回應 header / dashboard 自動修正 RPM/RPD（v2.54b）。

7. **碼源清洗戰役 v2 — jobs / events 帳本（v2.58 新增）**  
   - **任務說明檔**：`01_Environments/python_venvs/gov_core_system/Departments/06_Strategy/code_cleaning_pipeline_v2.md`。
   - **SDK 入口**：`from pipeline_meta import job_run, record_event, init_db`（位於 `02_Agents_Core/pipeline_meta.py`，stdlib-only、WAL）。
   - **DB 檔**：`Departments/05_Data_Vault/pipeline_meta/code_cleaning_pipeline_v2_meta.db`（jobs 17 欄 / events 8 欄 / 8 索引）。
   - **接入點**：`Code_Cleaner_Throttled_Agent.run()` 已以 `with pipeline_meta.job_run(...)` 包覆 `_run_inner()`；新增 agent 接入請循同樣 pattern 走 `wave_started → wave_completed → format_error_archived`。
   - **每次點火後查最新 job**：
     ```sql
     SELECT job_id, status, total_files_seen, cleaned_success_count, cleaned_failed_count, started_at, finished_at
     FROM jobs ORDER BY started_at DESC LIMIT 1;
     ```
   - **暫未實作的下一波（N1.5 / N2 / N3 / N4）**：動態 `triggered_by`、殭屍 reaper、events.jsonl 影子寫、`_pipeline_meta_query.py` CLI — 詳見 `Master_Map.json.war_status.next_priorities`。

8. **部門引用掃描器（v2.58 新增）**  
   - 通用版：`04_Workflows/_scan_dept_refs.py --needle "<片段>" [--db <Chariot_Registry.db>] [--limit N]`。
   - 改名／搬遷部門前後跑一遍，確認無殘留路徑。

9. **PID / 鎖檔即時核對**  
   - Telegram：`04_Workflows/.telegram_listener.lock`（**封存當下 2026-05-16：仍缺席**；最後一條 PID=7716、since 2026-05-11T01:14:55Z 已因 `RemoteDisconnected` 下線）。  
   - 換機或重開後 PID 會變，以鎖檔與 `Start-TelegramListener.ps1` 為準。

10. **總部工具層（v2.60 · 吏部 config）**  
   - **掛載根**：`01_Environments/config/`（`cursor/`、`tools/`、`mcp/`、`services/`）。  
   - **嚴禁**：任何 HQ 工具 `pip`/`uv` 進 **暗部** `python_venvs/gov_core_system`。  
   - **Cursor MCP**：使用者層 `%USERPROFILE%\.cursor\mcp.json`（`playwright` + `agentmemory` URL `http://127.0.0.1:8006/mcp`）。  
   - **Agentmemory 服務**：`config/services/agentmemory/repo` → `docker compose ps`；啟停勿動暗部 compose。  
   - **接戰驗收**：MCP 面板 Connected；Superpowers 新 Agent 自測；Phase 8 Spec-Kit 見 `Master_Map.war_status.next_priorities`。

11. **gov_core_system 編排骨架（2026-05-13 封存補記 · v2.59 補 runners）**  
   - **venv**：`01_Environments/python_venvs/gov_core_system/Scripts/python.exe`（已含 `langgraph==1.2.0`，屬尚書省核准之個案安裝）。  
   - **Smoke**：`Departments/01_Orchestration/smoke_test.py`（第二次加 `--second-smoke` 驗證 JSON checkpoint）。  
   - **CLI**：`Departments/01_Orchestration/main.py --resume <RUN_ID>`；checkpoint 目錄：`gov_core_system/runtime/checkpoints`（**禁寫** `Departments/05_Data_Vault`）。  
   - **Checkpoint 維運**：`Departments/01_Orchestration/scripts/prune_checkpoints.ps1`（乾跑預設；實刪須於 checkpoints 目錄放置 `CONFIRM_DELETE`）；說明見同層 `README_gov_core_checkpoint.md`；日誌 `runtime/checkpoints/prune.log`。  
   - **地圖**：`Master_Map.json` → `runners.gov_core_*` / `gov_core_prune_checkpoints_ps1` / `gov_core_checkpoint_readme` 與 `war_status.gov_core_orchestration`。

12. **HARNESS Phase 2 — Cursor 工程規則（2026-05-17 封存 · v2.61）**  
   - **人類母本**：`04_Workflows/CURSOR_AGENT_RULES.md`（§0–§10 + 附錄；對照 `ENGINEERING_CONTRACT.md`）。  
   - **Cursor 規則**：`.cursor/rules/engineering-contract.mdc`（`alwaysApply: true`，81 規則段）。  
   - **憲法／合約／地圖／實例錨點**：`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`DEPARTMENT_MAP.md`、`INSTANCE_ANCHOR_TANG.md`（路徑見 `Master_Map.runners`）。  
   - **接戰時**：Agent 須遵守工程規則起手式（已讀清單 → 四流派 → Work Report）；禁區類型見憲法 §7，具體路徑僅查實例錨點。  
   - **驗收**：新對話 Rules 面板確認 `engineering-contract` 為 always applied。

> **交接一句話**：「先讀 §7 → 三鑰盲測 → `Launch-Warpath -DryRun` → 再決定 Wave 或補基礎件。」
