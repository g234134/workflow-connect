# W0 覆蓋率稽核表

> **任務 ID**：HQ-P1-W0-AUDIT-01  
> **產出角色**：HQ-Governance-Worker（W0 可移植索引稽核）  
> **稽核日**：2026-05-19  
> **範圍**：唯讀；未修改三件套正文、`Master_Map.json`、`.cursor/rules`、`AGENTS.md`、暗部程式。

---

## 稽核摘要

| 維度 | 結論 |
|------|------|
| C01–C38 對 W1/W2/W3 | **38/38 皆有結論**；其中 **35 是**、**3 部分**（C16、C30、C35） |
| I01–I23 對 W5 | **23/23 是**（`INSTANCE_ANCHOR_TANG.md` 附錄對照完整） |
| 三件套絕對路徑 | **零** `D:\`／`C:\Users` |
| 三件套實例殘留 | **6 處**邊界語意（見 §3）；多數為**類型／禁寫自我說明**，非 W5 級實例 |
| v0.1 vs 正式檔 | **12 類衝突**；建議 v0.1 雙檔退役封存（見 §4） |

---

## §1 可移植核心 C01–C38 覆蓋對照

**圖例**：覆蓋＝是／否／部分｜主責檔：W1＝`HARNESS_CONSTITUTION.md`｜W2＝`ENGINEERING_CONTRACT.md`｜W3＝`DEPARTMENT_MAP.md`

| 條號 | W0 歸檔 | 覆蓋 | 對應章節 | 備註 |
|------|---------|------|----------|------|
| C01 | W1 | 是 | W1 §1.1 | 長期原則 vs 過期細節 |
| C02 | W1 | 是 | W1 §5.2 | 當次指令優先＋末尾留痕 |
| C03 | W1 | 是 | W1 §9.2、§9.3 | 四板塊檔案歸屬／互踩 |
| C04 | W1 | 是 | W1 §9.2 | 擁有／負責／不負責表 |
| C05 | W2 | 是 | W2 §2.2、§5#4、附錄 B | W1 §9.3 交叉提及 `dict` |
| C06 | W2 | 是 | W2 §2.2 | W1 §2 節奏一句呼應 |
| C07 | W2 | 是 | W2 §2.2、§7.1 | skeleton／placeholder 分欄 |
| C08 | W1 | 是 | W1 §7.1 Z-HQ-ENV-EDIT、§9.3 | 全域禁止事項 |
| C09 | W2 | 是 | W2 §11.1 | fallback；W1 §11 原則引用 |
| C10 | W2 | 是 | W2 §7.2 | 暗部本輪 DoD 四欄 |
| C11 | W2 | 是 | W2 §10.4 | 五項回報；Phase1 文檔工單用 §10 |
| C12 | W1 | 是 | W1 §9.1；W3 §7 末段 | 暗部三層 |
| C13 | W1 | 是 | W1 §6.1 | HQ 五角色 |
| C14 | W1 | 是 | W1 §6.2 | 黑板僅末尾追加 |
| C15 | W1 | 是 | W1 §11 | 停工條件 |
| C16 | W2 | 部分 | W1 §9.2（建議順序） | **W0 規劃歸 W2，正文落在 W1**；W2 附錄 C 標主責但正文未列順序 |
| C17 | W2 | 是 | W1 §9.2 互踩；W3 §7 | 跨模組欄位 Governance 對齊 |
| C18 | W1 | 是 | W1 §6.3 | master_status／handoff 獨占寫 |
| C19 | W1 | 是 | W1 §2 | HARNESS 定義 |
| C20 | W1 | 是 | W1 §3 | 四域 HQ／Dark／Chariot／Tools |
| C21 | W3 | 是 | W3 §6 | 三艙角色／用途／套件邊界 |
| C22 | W1 | 是 | W1 §5.3、§7.2 | override＋高風險先警示 |
| C23 | W1 | 是 | W1 §10 | 版本層級 |
| C24 | W1 | 是 | W1 §7.3 | Chariot_Registry；禁 hashes.txt |
| C25 | W2 | 是 | W2 §4 | 四大工程流派 |
| C26 | W2 | 是 | W2 §5 | 12-rule |
| C27 | W2 | 是 | W2 §6 | 起手→實作→驗收→Work Report |
| C28 | W1 | 是 | W1 §5.3 | 衝突位階 |
| C29 | W2 | 是 | W2 §7.1–7.2 | 單次 DoD vs 板塊 DoD；里程碑以 Progress 為準 |
| C30 | W1 | 部分 | W1 §12；W3 §11 | **口令語義＋入口是**；**初始化四段逐步**僅引用 `AGENTS.md`，未在三件套展開 |
| C31 | W1 | 是 | W1 §7.3 | 戰車級紅線 |
| C32 | W3 | 是 | W1 §4.3；W3 §3 | gov_paths／get_path |
| C33 | W3 | 是 | W3 §3 | 六部鍵 01–06 |
| C34 | W3 | 是 | W3 §3 | aliases／xing_bu |
| C35 | W3 | 部分 | W3 §6 | **角色／用途／禁絕對路徑是**；W0 建議不帶 `Scripts\python.exe`（已達） |
| C36 | W3 | 是 | W3 §3 | tang_gov_root 空則上層為根 |
| C37 | W3 | 是 | W3 §8；W1 §8 | artifacts 類型名；帳本制度 W1 §8 |
| C38 | W1 | 是 | W1 §6.3 | Conditions／Progress／master_status 分離 |

---

## §2 實例錨點 I01–I23 對 W5 覆蓋

| 條號 | 覆蓋 | W5 章節 | 證據摘要 |
|------|------|---------|----------|
| I01 | 是 | §2 | 戰車根 `D:\大唐三省六部\` |
| I02 | 是 | §2 | 暗部根＋禁止錯誤 `gov_core_system\` 假設 |
| I03 | 是 | §4.1–4.2 | 暗部／總部清算絕對路徑清單 |
| I04 | 是 | §9.1 | Phase1 基線＋第二階段目標 |
| I05 | 是 | §9.2 | 2026-05-17 定案；DarkOps Blocked |
| I06 | 是 | §5 | HQ worker 可碰絕對路徑表 |
| I07 | 是 | §4 | 與憲法禁區類型對照之具體路徑 |
| I08 | 是 | §9.3 | Master_Map 2.60、war_status 錨點 |
| I09 | 是 | §9.4 | I0/I1、D1–D3、R1/R2、G1 |
| I10 | 是 | §8.1 | 接戰／封存交接句 |
| I11 | 是 | §8.3 | runners 鍵與相對路徑表 |
| I12 | 是 | §8.4 | 封存 `cd`、README SOP |
| I13 | 是 | §8.2 | Status.json、lock、Chariot_Registry |
| I14 | 是 | §9.3 | version 字串與 changelog 節錄 |
| I15 | 是 | §8.3、§10 | runners 全表＋Departments 絕對路徑 |
| I16 | 是 | §3 | 三艙 venv／python／Enter-*.ps1 |
| I17 | 是 | §6 | DEFAULT_DB、pipeline_meta、compose |
| I18 | 是 | §9.3 | war_status 全文錨點 |
| I19 | 是 | §7 | secrets_status.rotated_at |
| I20 | 是 | §9.5 | model_registry、Groq 換模、quota |
| I21 | 是 | §9.6 | Wave／Asset_Value、business_metrics |
| I22 | 是 | §6.1 | document_chunks、pg_ok、ASSERT 字串 |
| I23 | 是 | §7 | 三鑰盲測供應商與 [OK] 判準 |

---

## §3 三件套殘留路徑／DB／env 掃描

**掃描檔**：`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`DEPARTMENT_MAP.md`  
**模式**：`D:\`、`C:\Users`、`Scripts\python`、具體 env 鍵、`.db` 檔名、`DEFAULT_DB` 實值

### 3.1 絕對路徑

| 檔名 | 行號 | 語意 | 判定 |
|------|------|------|------|
| （無） | — | — | **通過**：三件套零 `D:\`／`C:\Users` |

### 3.2 邊界殘留（非絕對路徑，供審稿留意）

| 檔名 | 行號 | 摘錄 | 語意 | 判定 |
|------|------|------|------|------|
| HARNESS_CONSTITUTION.md | 59 | 禁止清單含 `DEFAULT_DB`／`.db`／env 鍵原文 | **可移植禁寫規則自我說明** | 可接受 |
| HARNESS_CONSTITUTION.md | 127–133 | Z-ENV：`.env`；Z-HQ-ENV-EDIT：刪 `phase1_verify` | **禁區類型名**（非實例路徑） | 可接受 |
| HARNESS_CONSTITUTION.md | 155 | 分流：`DEFAULT_DB`、env 鍵 → W5 | **指向 W5，非實值** | 可接受 |
| DEPARTMENT_MAP.md | 55 | `.env` 承載（01_Environments 職責） | 職責類型詞 | 可接受 |
| DEPARTMENT_MAP.md | 77 | `phase1_verify` 域；Postgres／Qdrant | **runner／驗證域名**偏實例 | **輕微**：建議改「Phase1 驗證域（runner 見 W5）」 |
| DEPARTMENT_MAP.md | 119 | Postgres／Qdrant／Phase1 verify | 技術棧＋驗證語意 | 可接受（無連線字串／埠） |
| ENGINEERING_CONTRACT.md | — | （無 DB/env 實例鍵） | — | **通過** |

---

## §4 v0.1 與正式檔衝突及退役建議

### 4.1 衝突條目

| # | 主題 | v0.1（`HARNESS_Constitution_v0.1.md`／`ENGINEERING_CONTRACT_v0.1.md`） | 正式三件套 | 衝突性質 |
|---|------|--------------------------------------------------------------------------|------------|----------|
| 1 | 專案／暗部根 | §2.1–2.2 內嵌 `D:\大唐三省六部\` 絕對路徑 | 已遷 W5 §2 | **高**：違反可移植邊界 |
| 2 | 硬禁區 | §4.3 相對路徑＋清算腳本檔名列表 | W1 §7 **類型表**；清單在 W5 §4 | **中**：粒度不同 |
| 3 | HQ 可碰路徑 | §4.2 相對路徑 | W5 §5 絕對路徑 | **中**：v0.1 不完整 |
| 4 | 進度錨點 | §6.4 `Master_Map 2.60`、DarkOps Blocked | W5 §9；W1 不寫戰史 | **高**：過期風險 |
| 5 | 里程碑 | §5 開頭 I0/I1、D1–D3 完成敘述 | 僅 Progress／W5 §9.4 | **中**：應短命化 |
| 6 | 必讀檔名 | EC §2.1 引用 `HARNESS_Constitution_v0.1` | 應為 `HARNESS_CONSTITUTION.md` | **高**：引用錯誤 |
| 7 | 驗證鍵名範例 | EC 附錄 B 內嵌 `document_chunks`、`pg_ok` | W2 附錄 B 改指向 W5 | **中**：v0.1 洩實例鍵 |
| 8 | Runner 檔名 | 憲法附錄 B `_smoke_test_keys.py` | W1 §12「名見 W5」 | **低–中** |
| 9 | project_status | v0.1「可選、Phase2 目標」 | W1 §6.3 已定義路徑職責 | **低**：表述升級 |
| 10 | Phase 2 觸發 | v0.1 未寫 W4 10/10 閘門 | W2 §8 明確閘門 | **中**：正式更嚴 |
| 11 | 檔名規範 | `HARNESS_Constitution` vs `HARNESS_CONSTITUTION` | 正式採大寫底線 | **低**：並存混淆 |
| 12 | 自我定位 | 兩份均標「v0.1 草稿、不取代 Conditions」 | 正式為 Phase1 交付主檔 | **中**：權威位階衝突 |

### 4.2 建議退役清單（尚書省裁決後執行）

| 動作 | 對象 | 建議 |
|------|------|------|
| **封存** | `04_Workflows/HARNESS_Constitution_v0.1.md` | 移 `04_Workflows/archive/phase1_draft/` 或檔首加 `SUPERSEDED → HARNESS_CONSTITUTION.md` |
| **封存** | `04_Workflows/ENGINEERING_CONTRACT_v0.1.md` | 同上 → `ENGINEERING_CONTRACT.md` |
| **保留唯讀** | `00_Agent_Work_Conditions.md`、`00_Agent_Work_Progress.md` | 母本／黑板，**不退役** |
| **保留** | `AGENTS.md` | 戰車接戰入口（I10） |
| **更新引用** | 全 repo grep `*_v0.1` | 改指向正式三件套＋W5 |
| **不動** | `runbooks/*_v0.1.md` | 屬 runbook 線，與三件套分軌；可另開票標 superseded |

---

## §5 邊界模糊條目裁決建議（尚書省）

| 條號 | 問題 | 裁決建議 |
|------|------|----------|
| **C35 ↔ I16** | W3 是否可留相對 venv 語意 | **採 W0 §5 建議**：W3 僅 cabin 角色＋用途一句；`Scripts\python.exe`、Enter-*.ps1 **僅 W5 §3**。現狀 W3 已合規。 |
| **C22 ↔ I03** | 硬禁區類型 vs 逐條路徑 | **採分流**：W1 §7 類型表（現狀）＋ W5 §4 實例清單（現狀）。**不必**另建 `FORBIDDEN_ZONES_W5.md`，除非 W5 §4 過長需拆分。 |
| **C37 ↔ I17** | pipeline 帳本類型 vs DEFAULT_DB | **採分流**：W1 §8／W3 §8 制度＋類型名；W5 §6 實際 `.db`、env、`pipeline_meta_db` runner。**W2 附錄 B** 僅形狀、鍵名對照 W5（正式檔已如此）。 |
| **C16 檔位** | W0 寫 W2，正文在 W1 | **二選一**：(A) 在 W2 §11 增「暗部建議順序」1 段；或 (B) 修 W0 索引將 C16 主責改 W1。**建議 (A)**，避免附錄與正文分裂。 |
| **C30 四段** | 三件套未展開初始化 | **維持引用式**：W1 §12＋`AGENTS.md` 為準；**不**在三件套複製四段全文（防與 AGENTS 雙源）。 |
| **DEPARTMENT_MAP L77** | `phase1_verify` 字樣 | **可選微修**（非本工單）：改抽象表述，避免 runner 檔名進 W3。 |

---

## §6 稽核方法

1. 通讀 W0 索引、三件套、W5 全文。  
2. 對 C01–C38／I01–I23 逐條人工對照章節。  
3. `rg` 掃描三件套：`D:\\`、`C:\\Users`、`DEFAULT_DB`、`OPENAI`、`GROQ`、`\.db`。  
4. 並讀 `HARNESS_Constitution_v0.1.md`、`ENGINEERING_CONTRACT_v0.1.md` 差異。  

---

*W0 產出完畢；供尚書省審稿。*
