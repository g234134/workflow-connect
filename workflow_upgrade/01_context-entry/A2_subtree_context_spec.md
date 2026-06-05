# A2 — Subtree Context 規格（Sprint 0 · Context Entry）

| 項目 | 值 |
|------|-----|
| **票號** | A-2 |
| **版本** | v0.1-draft |
| **狀態** | 規格定稿候審（實作不在本票） |
| **上游** | A-1 `A1_root_context_spec.md` §8；F 線 `00_master_plan.md`；戰車 `context/context_model.md`、`context/context_entry_contract.md` |
| **下游** | A-4（navigation map template）、A-5（載入／組裝 runbook） |
| **非目標** | ignore／deny 細則（A-3）、navigation map 正文（A-4）、程式實作、UI |

---

## 1. 文件目的

本規格定義 **subtree context** 在 Sprint 0 · A 線中的治理角色，補足 A-1 僅劃界的「子樹層」，供後續 A-4／A-5 與新 chat 派工直接引用。

具體要達成：

1. **避免上下文膨脹**：限定子樹掛載單位、欄位類型與同時活躍數量，禁止把部門全文或任務證據塞入 subtree。  
2. **讓新 chat 快速接手**：每個 subtree 帶可導航的 `scope_label`、`entry_refs` 與穩定 `subtree_id`，接戰時不必重讀全 repo。  
3. **與 root 銜接清晰**：繼承全局禁則、不得放寬；子樹專屬約束僅在該作用域有效。  
4. **支撐下游**：為 A-4 導航圖模板提供「掛載點」語意；為 A-5 提供組裝順序與裁剪優先級輸入（本檔不寫 runbook 步驟）。

本檔可獨立閱讀；實作權威仍以 `core/context_entry.py` 與 `context/context_entry_contract.md` 為準。戰車 `context_model.md` v0.1 僅定義 root／working／memory 三層；**subtree 為治理層第四片段**，待 A-5 映射至組裝契約，本檔不搶跑鍵名鎖死。

---

## 2. Subtree Context 定義

**Subtree context** 是附著於某一**穩定作用域**（見 §3）的 **中壽命、半全局** 上下文片段。  
它在一次上下文組裝中位於 **root 之後、working 之前**，為當前子流程提供「在全局制度下、僅本子樹需要的導航與約束摘要」。

| 維度 | subtree context | 對照（邊界） |
|------|-----------------|--------------|
| **壽命** | 跨多個同作用域 task；變更頻率中於 root 與 working 之間 | root：跨 session 極慢變；working：單輪 |
| **語義** | 「離開本子樹就無意義的規則、runbook 摘要、模組契約索引」 | root：全 repo 成立；memory：檢索證據 |
| **來源** | 部門 brief 摘要、專線 runbook 要點、workspace 三件套索引、Sprint 子目錄規格 | 非用戶原文、非 tool 輸出 |
| **變更權** | 該子樹 Governance／線負責人；worker 只讀，需求寫 notes／Progress |

**一句話**：subtree context = **讓 agent 在某一子流程內合法施工的最小專域約束包**，不是全局憲法複本、不是對話日誌。

**雙目標對齊**：

| 目標 | 機制 |
|------|------|
| 避免膨脹 | 摘要級 digest、單次活躍子樹上限、禁止嵌套多層子樹樹 |
| 新 chat 接手 | 穩定 `subtree_id` + `entry_refs` + `handoff_digest`（一屏內可讀） |

---

## 3. Subtree 掛載單位

掛載單位描述「這棵子樹掛在哪裡」；**一次組裝建議只掛 0～2 個活躍 subtree**（見 §7）。

| 掛載類型 | 代號 | 說明 | 典型 `subtree_id` 語意 |
|----------|------|------|-------------------------|
| **主線（Line）** | `line` | workflow_upgrade A–E 或戰車編排主線 | `line.a.context-entry` |
| **部門／艙（Department / Cabin）** | `dept` | 六部鍵、暗部四 Agent、Master_Map `cabins` 用途域 | `dept.data-agent` |
| **模組／子目錄（Module）** | `module` | 單一 `core/` 包、單一 workspace 目錄 | `module.gov_paths` |
| **主題／票種（Theme）** | `theme` | 跨目錄的治理主題（如 Sprint 0、K-2 rollout） | `theme.sprint0-f-a` |

**掛載規則**：

1. 每個 subtree **必須** 選定一個**主掛載類型**（`mount_type`）；可選填次要標籤（如 `dept` + `theme`），但 `subtree_id` 仍以主類型為首段。  
2. 同一 `subtree_id` 在全系統**唯一**；不得用兩個 id 描述同一作用域。  
3. 掛載單位用**邏輯名**（部門鍵、線代號、目錄邏輯名），禁止本機絕對路徑。  
4. **禁止** 以「單次檔案路徑」「單次 commit」「單次 tool 輸出」作為掛載單位。

---

## 4. 與 Root Context 的繼承／覆寫原則

### 4.1 組裝順序（治理語意；細節由 A-5 落地）

```
root_context  →  subtree_context[]  →  working_context  →  long_term_memory
     P0              P0.5（可 0～n）         P1～P2              P3
```

- **root** 最先載入、最後裁撤（與 A-1 §6 一致）。  
- **subtree** 在 root 之後合併；裁剪時**不得**刪除 root 已載入的 `hard_rules` 類條目。  
- **working** 不得反向覆寫 root 或 subtree 中的禁則類型。

### 4.2 繼承（MUST）

| 項 | 規則 |
|----|------|
| **禁則** | subtree **繼承** root 的 `forbidden_content_types`、`forbidden_action_types`；子樹僅可**追加**更嚴條目，**禁止放寬** |
| **權威位階** | `authority_stack` 以 root 為準；subtree 可追加「本子樹負責人」但不改變憲法＞合約順序 |
| **入口合同** | `entry_contract_ref`（`build_rooted_context`）僅在 root 宣告；subtree 以 `inherits_entry: true` 標記服從，不重複發明入口 |

### 4.3 覆寫與追加（MAY · 受限）

| 允許 | 禁止 |
|------|------|
| 追加本子樹 `scope_constraints`（比 root 更窄） | 覆寫 root `hard_rules` 為較寬 |
| 提供本子樹 `navigation` 專屬 `logical_doc_refs` | 在 subtree 重貼憲法／合約全文 |
| 設定 `subtree_priority` 供裁剪排序 | 用 subtree 承載 `query`、tool 原文、RAG hits |
| `handoff_digest` 給新 chat 一屏摘要 | 嵌套第三層以上 subtree 樹狀結構 |

### 4.4 衝突處理

| 衝突 | 裁決 |
|------|------|
| root 與 subtree 對同一行為約束不一致 | **以較嚴者為準**；若無法判定，停工並記 Progress |
| 兩個 subtree 對同一模組給出不同 runbook 摘要 | 以 `subtree_id` 與任務卡明示作用域匹配者為準；另一棵標 `inactive` |
| subtree 與 `context_entry_contract` | 尚書省 ＞ 憲法 ＞ `context_entry_contract.md` ＞ A-1 ＞ **本檔** |

---

## 5. Subtree 最小欄位建議

以下為**類型清單**（非固定 JSON schema）；A-5 可映射為 `subtree_context[]` 或 `metadata.subtrees`。

### 5.1 識別與掛載（必填語意）

| 欄位類型 | 說明 |
|----------|------|
| `subtree_id` | 穩定唯一 id（見 §8 命名） |
| `mount_type` | `line` \| `dept` \| `module` \| `theme` |
| `scope_label` | 人類可讀一句話（新 chat 首屏） |
| `active` | 本輪是否載入（`true` / `false`） |

### 5.2 專域約束（建議）

| 欄位類型 | 說明 |
|----------|------|
| `scope_constraints` | 本子樹可碰／不可碰**類型**（不含實例路徑） |
| `module_contract_refs` | 邏輯名指向 brief／notes／core 契約 |
| `runbook_digest` | 專線 runbook **要點**（條列，非全文） |

### 5.3 導航與接手（建議 · 支撐 A-4）

| 欄位類型 | 說明 |
|----------|------|
| `entry_refs` | 新 chat 必讀 3～7 個邏輯檔名（見 A-4 模板） |
| `nav_map_ref` | 指向 A-4 產出的導航圖邏輯名（本票不寫模板正文） |
| `handoff_digest` | 上一輪交接要點（≤10 條 bullet） |
| `queue_ref` | 可選；指向 `90_run_queue.md` 中相關票號語意 |

### 5.4 溯源（建議）

| 欄位類型 | 說明 |
|----------|------|
| `subtree_version` | 子樹摘要版本 |
| `source_manifest` | 參與摘要的檔案邏輯名列表 |
| `parent_root_version` | 組裝時對齊的 `root_version`（對賬用） |

### 5.5 裁剪提示（可選）

| 欄位類型 | 說明 |
|----------|------|
| `subtree_priority` | 多棵子樹時的保留順序（整數，大者先保留） |
| `max_digest_tokens` | 建議上限語意（非實作常數） |

**禁止出現在 subtree 的欄位類型**（與 A-1 §4 對齊）：金鑰原文、實例磁碟路徑、完整 CLI 輸出、`semantic.hits`、用戶 `query` 原文、eval 樣本全文。

---

## 6. 何時應建立新的 Subtree

滿足**多數**條件時，應為作用域建立（或啟用）一棵 subtree：

| # | 條件 |
|---|------|
| S1 | 同一作用域預期有 **≥3 次** task 或 **≥2 個** 新 chat 接力 |
| S2 | 存在**專屬** runbook／brief／workspace 三件套，且內容**無法**用 root 一句 digest 覆蓋 |
| S3 | 派工需明示「僅限某部門／某線／某模組」的可碰邊界 |
| S4 | 需要與其他子樹**並行**施工，且要避免互相污染 working |
| S5 | A-4 導航圖需要一個**穩定掛載點**（`nav_map_ref`） |

**範例（語意）**：

- Sprint 0 的 `workflow_upgrade/01_context-entry/` → `line.a.context-entry`  
- 暗部 Data agent 長期票 → `dept.data-agent`  
- 單模組 `gov_paths` 重構系列 → `module.gov_paths`

---

## 7. 何時不應建立 Subtree

| # | 反例 | 應落層 |
|---|------|--------|
| N1 | 僅一輪問答、無接力 | working only |
| N2 | 內容已是全局制度（憲法、AGENTS 紅線） | root（A-1） |
| N3 | 檢索命中、歷史教訓段落 | long_term_memory |
| N4 | 單票臨時 goal、本輪 tool 輸出 | working |
| N5 | 與既有 `subtree_id` 重疊且僅差檔名 | 合併進既有 subtree，不新建 id |
| N6 | 為「多掛一層」而掛載，無專屬 digest | 不建；用 root `navigation` + working `task_input` |
| N7 | 同時活躍 >2 棵且無 `subtree_priority` | 違規；須合併或標 `inactive` |

**活躍數量硬建議**：單次組裝 **≤2** 棵 `active: true` 的 subtree；其餘保留 id 但 `active: false` 供隊列引用。

---

## 8. 命名與導航原則

### 8.1 `subtree_id` 命名

格式：`<mount_type>.<scope_slug>[.<facet>]`

| 規則 | 說明 |
|------|------|
| 字元 | 小寫英數與 `.`、`-`；禁止空格與中文 id |
| 穩定 | id 不隨單次票號變化；票號放 `handoff_digest` 或 working |
| 可讀 | `scope_slug` 應能對應部門鍵或線代號（如 `data-agent`、`context-entry`） |
| 唯一 | 全系統不重複 |

**示例 id（非 exhaustive）**：

- `line.a.context-entry`  
- `dept.governance`  
- `module.rag-pipeline`  
- `theme.k2-rollout-governance`

### 8.2 導航原則（支撐 A-4）

1. **entry_refs 有序**：按「接戰必讀 → 本票 → 驗收」排列；總數建議 ≤7。  
2. **只邏輯名**：與 A-1 `navigation.logical_doc_refs` 一致，不寫磁碟絕對路徑。  
3. **一圖一掛載點**：每個 A-4 導航圖對應恰好一個 `subtree_id`（或明確標註共享規則）。  
4. **新 chat 路徑**：接戰時讀 root digest → 讀**活躍** subtree 的 `handoff_digest` + `entry_refs` → 再開 working。  
5. **向下傳遞**：subtree 不得定義 selector／retrieve 路由表（Phase 10.5 屬下游）；僅標註哪些欄位類型可能被消費（A-5 對賬）。

---

## 9. 最小 Markdown 範例

下列為**治理向示意**；鍵名供 A-4／A-5 對齊語意，非執行契約。

```markdown
## subtree_context（示意 · 單棵）

### identity
- subtree_id: line.a.context-entry
- mount_type: line
- scope_label: Sprint 0 · A 線 Context Entry 規格層
- active: true
- subtree_priority: 10

### inheritance
- inherits_entry: true
- parent_root_version: sprint0-a1-v0.1

### scope_constraints
- may_touch: [workflow_upgrade/01_context-entry/*.md, 90_run_queue A 線 Status/Notes]
- must_not_touch: [A1_root_context_spec 正文, core/, production hooks]
- append_only_hard_rules: [no_hand_assemble_three_layer_context]

### runbook_digest
- 一次只接一票；狀態 TODO→DOING→DONE
- 執行期合同以 context_entry_contract 為準；本目錄為治理補充

### navigation
- entry_refs:
  - workflow_upgrade/01_context-entry/A1_root_context_spec.md
  - workflow_upgrade/01_context-entry/A2_subtree_context_spec.md
  - context/context_entry_contract.md
- nav_map_ref: workflow_upgrade/01_context-entry/40_navigation_map_template.md
- queue_ref: workflow_upgrade/90_run_queue.md#A-2

### handoff_digest
- A-1 DONE；A-2 定義 subtree 掛載與繼承
- 待 A-3 deny、A-4 nav template、A-5 runbook

### provenance
- subtree_version: sprint0-a2-v0.1
- source_manifest: [A1_root_context_spec.md#8, 00_master_plan.md#5.1]
```

**對照：以下不屬 subtree**

| 內容 | 應落層 |
|------|--------|
| `forbidden_content_types` 全局表 | root |
| `query: 用戶本輪問題` | working |
| `semantic.hits[]` | long_term_memory |
| ignore／deny 規則正文 | A-3（本檔不展開） |
| 完整 navigation map 節點表 | A-4 |

---

## 10. 與其他層／票號的邊界

| 對象 | 關係 |
|------|------|
| **A-1 root** | A-1 §8 劃界；本檔展開 subtree 欄位與掛載，不重複 root 欄位類型表 |
| **A-3 ignore/deny** | A-3 定義裁剪與拒絕規則；subtree 僅可**引用** deny 類型，不寫細則 |
| **A-4 navigation map** | 使用本檔 `entry_refs` / `nav_map_ref` 作為模板輸入 |
| **A-5 runbook** | 落實 §4.1 組裝順序與驗收 CLI；本檔不提供步驟正文 |
| **H 線合同** | 現行頂層三層輸出不含 `subtree_context` 鍵；映射為 A-5 增量，不與 v0.1 合同衝突宣稱 |

---

## 11. 驗收對照（本票）

| 檢查項 | 通過標準 |
|--------|----------|
| 獨立可讀 | 不開 A-1 亦可理解 subtree 定義（§2） |
| 與 A-1 不衝突 | §4 與 A-1 §8 邊界表一致；子樹不得放寬 root |
| 雙目標 | §2、§7 明確處理膨脹與新 chat 接手 |
| 下游可接力 | A-4 可用 §3、§8；A-5 可用 §4.1、§5 |
| 不越界 | 無 ignore/deny 細則、無 nav 模板正文、無程式 |

---

## 12. 依賴與缺口

| 依賴 | 狀態 | 影響 |
|------|------|------|
| A-1 `A1_root_context_spec.md` | DONE | §4 繼承規則已對齊 |
| A-0 overview | TODO | 可選總覽索引；不阻塞本檔 |
| A-3 ignore/deny | TODO | 裁剪時 deny 與 subtree 的交集待 A-3 |
| A-4 navigation template | TODO | `nav_map_ref` 目標檔尚未建立 |
| A-5 runbook | TODO | 組裝順序與 API 鍵名待 A-5 |
| `context_model.md` 三層 | 已存在 | subtree 為治理第四片段；實作映射待 A-5 |

---

## 13. 引用索引（邏輯名）

- `workflow_upgrade/01_context-entry/A1_root_context_spec.md` — root 邊界 §8  
- `workflow_upgrade/00_master_plan.md` — Sprint 0 依賴 §5.1  
- `context/context_entry_contract.md` — H 線入口與三層輸出  
- `context/context_model.md` — root／working／memory 三層模型  
- `04_Workflows/DEPARTMENT_MAP.md` — 部門鍵與 cabin 用途域（邏輯名）
