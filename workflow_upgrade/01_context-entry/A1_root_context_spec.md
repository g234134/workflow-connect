# A1 — Root Context 規格（Sprint 0 · Context Entry）

| 項目 | 值 |
|------|-----|
| **票號** | A-1 |
| **版本** | v0.1-draft |
| **狀態** | 規格定稿候審（實作不在本票） |
| **上游** | F 線 `00_master_plan.md`（全局邊界）；戰車既有 `context/context_model.md`、`context/context_entry_contract.md` |
| **下游** | A-2（subtree context）、A-5（載入／組裝契約） |
| **非目標** | subtree 欄位細節、hooks／subagents／connectors、程式實作、UI |

---

## 1. 文件目的

本規格定義 **root context** 在企業化工作流升級（Sprint 0 · A 線）中的治理角色，供後續 A-2／A-5 與主代理派工直接引用。

具體要達成：

1. 讓所有入口對「什麼算全局制度層」有同一套命名與邊界，避免與 working／memory／subtree 混寫。  
2. 規定 root 應載入的**欄位類型**與**禁止內容**，對齊既有 H 線 `build_rooted_context` 合同，但不重複實作細節。  
3. 明確**誰讀、何時讀、誰可改**，降低多 agent 並行時的上下文污染。  

本檔可獨立閱讀；實作權威仍以 `core/context_entry.py` 與 `context/context_entry_contract.md` 為準，本檔補 **workflow_upgrade 層的治理語義**。

---

## 2. Root Context 定義

**Root context** 是送入模型前的 **全局、跨任務、跨 session 的制度與導航層**。  
它在一次 `build_context`／`build_rooted_context` 中**最先載入、最後裁撤**（裁剪優先級 P0），不因單次 RAG 未命中或某輪對話失敗而整層移除。

| 維度 | root context | 非 root（僅標邊界，細節見他檔） |
|------|----------------|--------------------------------|
| **壽命** | 跨 task、跨 chat；變更頻率低 | working：單輪／單 task；subtree：見 A-2 |
| **語義** | 「在所有任務上都成立的規則與索引」 | 「只對本輪決策有用的狀態與證據」 |
| **來源** | 憲法／合約／AGENTS／地圖**邏輯名**摘要 | 用戶輸入、tool 輸出、檢索命中 |
| **變更權** | 制度／Governance 裁決 | 執行 agent 可在 working 追加 |

**一句話**：root context = **讓 agent 合法開工的最小全局約束包**，不是任務日誌、不是檢索結果、不是部門子樹。

---

## 3. Root Context 應包含的欄位類型

以下為**類型清單**（非固定 JSON schema）；A-5 可將其映射為具體鍵名，本檔不鎖死鍵名以免與實作搶跑。

### 3.1 身份與權威位階（`identity`）

| 類型 | 說明 | 範例語意（非原文） |
|------|------|-------------------|
| `role_label` | 當前 agent 角色名 | 大唐副官、HQ worker、暗部 Data agent |
| `authority_stack` | 衝突時位階一句話 | 尚書省指令 ＞ 憲法 ＞ 工程合約 ＞ brief |
| `session_mode` | 接戰／封存／單票施工 | `boot` / `task` / `seal` |

### 3.2 禁則與紅線（`hard_rules`）

| 類型 | 說明 |
|------|------|
| `forbidden_content_types` | 禁止寫入上下文的**類型**（金鑰原文、checkpoint 二進位等） |
| `forbidden_action_types` | 禁止行為**類型**（手拼三層 context、雙 Telegram 監聽等） |
| `constitution_refs` | 憲法 §7 禁區**類型**引用（不含實例磁碟路徑） |

### 3.3 制度摘要（`governance_digest`）

| 類型 | 說明 |
|------|------|
| `constitution_digest` |  Harness 禁區類型、四域邊界要點 |
| `engineering_digest` | 四流派／12-rule 起手要點 |
| `agents_boot_digest` | 接戰九步、紅線、一致上下文入口要求 |

每條 digest 應為**摘要級**（條列、可裁剪的說明段），非全文鏡像。

### 3.4 導航與索引（`navigation`）

| 類型 | 說明 |
|------|------|
| `logical_doc_refs` | 邏輯文件名（如 `Master_Map.json` → `runners`） |
| `workflow_refs` | 當前 Sprint／runbook／隊列檔邏輯名 |
| `entry_contract_ref` | 上下文唯一入口指向（`build_rooted_context` 合同） |

**原則**：只放**邏輯名與索引**，不放全文、不放本機絕對路徑。

### 3.5 版本與溯源（`provenance`）

| 類型 | 說明 |
|------|------|
| `root_version` | root 組裝版本號（如 `v0.1`） |
| `assembled_at` | 組裝時間（ISO-8601） |
| `source_manifest` | 參與組裝的摘要片段 id／版本列表 |

### 3.6 可選：任務無關的全局參數（`global_params`）

僅當**全管道共用**且**非單票專屬**時允許，例如：

- 預設 `mode` 標籤語意（`ask_pipeline` / `long_task`）  
- 語言／回覆格式偏好（若為產品級設定）  

單票 `task_id`、`goal`、`work_order_id` 屬 **working**，不得塞入 root。

---

## 4. Root Context 不應包含的內容

| 類別 | 禁止內容 | 原因 |
|------|----------|------|
| **密鑰與連線** | `.env` 原文、token、完整連線字串 | 憲法 §7.3；僅允許 `[OK]`／`[FAILED]` 類糧草結論 |
| **實例路徑** | 磁碟代號、venv 絕對路徑、具體 `.db` 檔名 | 可移植性；實例見 `INSTANCE_ANCHOR` |
| **工作層** | 對話輪次、tool 原文、handoff 包、當輪 goal／query | 屬 `working_context` |
| **長期記憶** | RAG chunk、semantic hits、structured 工單行 | 屬 `long_term_memory` |
| **子樹層** | 部門／模組／子工作流專屬上下文 | 屬 subtree（A-2）；禁止在 root 展開 |
| **執行證據** | 完整 CLI 輸出、trace JSON、eval 樣本 | 屬 observability／Progress，非 prompt |
| **全文鏡像** | 憲法／合約／AGENTS 全文 | 超 token；應 digest + 邏輯引用 |
| **發明規格** | hooks、subagents、connectors 協議 | 非 Sprint 0 A-1 範圍 |

**硬規則**：若某欄位會隨「本輪 tool 呼叫」或「本票施工結果」變化，則**不得**寫入 root。

---

## 5. 誰會讀 Root Context

| 讀者 | 讀取目的 | 權限 |
|------|----------|------|
| **主代理（HQ Coordinator）** | 派工、對齊禁區、檢查是否繞過 H 線入口 | 讀；root 變更需 Governance |
| **新 chat（接戰 session）** | 起手校準、角色／紅線一致 | 讀；接戰時載入 digest |
| **Worker agent（暗部／專線）** | 施工前確認制度邊界與可碰範圍 | **只讀**；不可改 root |
| **上下文組裝器（邏輯角色）** | `build_rooted_context` 內載入 root 片段 | 按合同組裝，不手拼 |

Worker **不得**為通過本票驗收而私自增刪 `hard_rules`；需求寫入自身 `notes`／Progress 末尾，由 Governance 更新 root 來源摘要。

---

## 6. 什麼時機載入

| 時機 | 是否載入 root | 說明 |
|------|----------------|------|
| **新入口首次組裝上下文** | **必須** | 凡走 `build_rooted_context` 的 pipeline 首節點 |
| **接戰（Boot）** | **必須** | 新 session 起手；與 AGENTS 九步校準對齊 |
| **長任務跨步** | **必須** | 每輪刷新 working／memory 時 **重新帶上** root，不假設 session 記憶 |
| **單次 tool 回調** | 不單獨載入 | 僅透過已組裝的 context payload 間接可見 |
| **封存（Seal）** | 不寫入 root | 戰報寫 Progress／隊列，不反向污染 root |
| **僅讀程式碼、不調 LLM** | 可不載入 | 無 prompt 組裝則跳過 |

**與 H 線對齊**：程式入口已強制 `build_rooted_context` 者，root 載入時機 = 該函數被呼叫時；本規格不重定義呼叫點。

---

## 7. 更新規則

| 規則 | 說明 |
|------|------|
| **R1 版本化** | root 來源摘要變更須 bump `root_version` 或 `source_manifest` |
| **R2 治理權** | 僅 Governance／尚書省授權票可改制度 digest 與 `hard_rules` |
| **R3 Worker 只讀** | 施工 agent 不得在 runtime 改 root 層；單票資訊寫 working |
| **R4 禁止任務污染** | 禁止把本輪結論、測試輸出、臨時 flag 寫入 root |
| **R5 增量追加邊界** | H 線允許在入口返回後向 `task_input`／working **追加**；**不得替換整層 root**（見 `context_entry_contract.md` §4） |
| **R6 衝突處理** | 與實作合同衝突：尚書省 ＞ 憲法 ＞ `context_entry_contract.md` ＞ 本檔 |

**更新觸發範例**（治理動作，非 worker 日常）：

- 憲法／工程合約修訂 → 更新 `governance_digest`  
- Sprint 0 隊列或 master plan 結構變更 → 更新 `navigation.workflow_refs`  
- 新增全局紅線 → 更新 `hard_rules`  

---

## 8. 與 Subtree Context 的邊界

> Subtree 欄位與載入策略由 **A-2** 定義；本節只劃界，不展開 subtree。

| 問題 | Root | Subtree（A-2） |
|------|------|----------------|
| **作用域** | 全 repo／全編排 | 某部門、某工作流分支、某 cabin |
| **典型內容** | 憲法類型、全局紅線、runner 索引 | 部門 brief、專線 runbook 摘要、模組契約 |
| **載入順序** | 最先（P0） | 在 root 之後、working 之前（具體順序 A-5） |
| **裁剪** | 僅壓縮說明段，不低於 root 最小保留 | 按子樹優先級（A-2） |
| **重疊處理** | 全局禁則以 root 為準 | 子樹不得放寬 root 已禁止的類型 |

**判定口訣**：若拿掉當前部門／子流程仍應成立 → 放 root；僅在該子流程內有意義 → 放 subtree（等 A-2）。

**禁止**：在 root 內嵌套完整 subtree 樹狀結構或部門全文。

---

## 9. 最小範例（Markdown · 非程式）

下列為**治理向示意**，鍵名僅供 A-2／A-5 對齊語意，非執行契約。

```markdown
## root_context（示意）

### identity
- role_label: 大唐副官 · Sprint0-A1-worker
- authority_stack: 尚書省 > 憲法 > 工程合約 > 本票 brief
- session_mode: task

### hard_rules
- forbidden_content_types: [env_secret_plaintext, checkpoint_binary_blob]
- forbidden_action_types: [hand_assemble_three_layer_context, dual_telegram_listener]
- constitution_refs: [Z-env-secrets, Z-venv-tree, Z-checkpoint-unauthorized]

### governance_digest
- constitution_digest: 禁區僅類型引用；DarkOps blocked 不得改暗部根
- engineering_digest: 先 Context+Source；核心路徑回傳 dict
- agents_boot_digest: 新入口必須 build_rooted_context；嚴禁手拼三層

### navigation
- logical_doc_refs: [Master_Map.json/runners, context/context_entry_contract.md]
- workflow_refs: [workflow_upgrade/90_run_queue.md, workflow_upgrade/00_master_plan.md]
- entry_contract_ref: build_rooted_context

### provenance
- root_version: sprint0-a1-v0.1
- assembled_at: 2026-05-25T00:00:00Z
- source_manifest: [context_model.md#root_context, context_entry_contract.md#2.2]
```

**對照：以下不屬 root（應落他層）**

| 內容 | 應落層 |
|------|--------|
| `query: 用戶問題原文` | working |
| `semantic.hits[]` | long_term_memory |
| `xing_bu.runbook_digest` | subtree（A-2） |
| `RUNTIME_METRIC: latency_ms=120` | observability / 戰報 |

---

## 10. 驗收對照（本票）

| 檢查項 | 通過標準 |
|--------|----------|
| 獨立可讀 | 不開 A-2 即可理解 root 定義與禁則 |
| root vs subtree | §8 邊界表可回答「放哪一層」 |
| 下游可接力 | A-2 可只補 subtree；A-5 可對齊 §6–§7 載入／更新 |
| 不越界 | 無 subtree 細節、無 hooks／subagents、無程式碼 |

---

## 11. 依賴與缺口

| 依賴 | 狀態 | 影響 |
|------|------|------|
| `workflow_upgrade/00_master_plan.md`（F-1） | **未建立** | 全局 Sprint 邊界以本檔 + 90_run_queue 為準 |
| A-2 subtree 規格 | TODO | 子樹欄位不在本檔展開 |
| A-5 載入契約 | TODO | 組裝順序與 API 形狀待 A-5 |

---

## 12. 引用索引（邏輯名）

- `AGENTS.md` — 一致上下文入口、紅線  
- `context/context_model.md` §2.1 — 三層模型之 root 定義  
- `context/context_entry_contract.md` — H 線唯一入口與禁止繞過  
- `04_Workflows/HARNESS_CONSTITUTION.md` — 禁區類型（引用，不複製）  
