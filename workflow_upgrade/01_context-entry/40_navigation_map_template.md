# A4 — Navigation Map 模板（Sprint 0 · Context Entry）

| 項目 | 值 |
|------|-----|
| **票號** | A-4 |
| **版本** | v0.1-template |
| **狀態** | 治理層模板（非實例檔、非程式輸出） |
| **上游** | A-1 `navigation`（§3.4）；A-2 `entry_refs`／`nav_map_ref`（§5.3、§8.2） |
| **下游** | A-5 runbook（組裝順序、接戰必讀清單、驗收對賬） |
| **非目標** | ignore／deny 細則（A-3）、runbook 步驟（A-5）、UI、production code、實際 nav map 實例檔 |

---

## 1. 文件目的

本檔定義 **Navigation Map（導航圖）** 的**文字模板**，用來描述：

1. **root** 與 **subtree** 兩類節點在上下文治理中的掛載關係；  
2. 每個節點的 **`entry_refs`**（必讀邏輯檔）與 **`nav_map_ref`**（指向本圖或子圖）；  
3. 從 **任務線（Line）／隊列票號** 到 **應載入哪棵 context 節點** 的標準導航路徑；  
4. 與 **`workflow_upgrade/00_master_plan.md`**、**`workflow_upgrade/90_run_queue.md`** 的對帳規則。

**執行期聲明（v0.1）**：

- `core/context_entry.py` → `build_rooted_context` 現行輸出為 **root／working／long_term_memory** 三層；**不含** `subtree_context` 頂層鍵，也**不**自動產出 navigation map 檔案或 JSON。  
- 本模板供 **治理／派工／新 chat 接戰** 使用；映射至組裝契約由 **A-5** 操作化，不在本票宣稱 builder 已實作。

---

## 2. Navigation Map 是什麼

| 維度 | 說明 |
|------|------|
| **語義** | 一張**邏輯索引表**，把「穩定作用域」對應到「必讀檔案列表」與「父節點」，避免每次派工重發目錄樹 |
| **不是** | 檔案系統樹、UI 站點地圖、HTTP 路由表、RAG 知識庫目錄 |
| **與 A-1／A-2 關係** | A-1 `root_context.navigation` 可**引用**本圖 root 節點的 `entry_refs`；A-2 每棵 subtree 以 `nav_map_ref` **指向**本模板或子圖邏輯名 |
| **實例化** | Sprint 0 **只**維護本模板 + §8 最小示例；各線實際 nav map 實例檔（若需要）另開票，檔名建議 `nav_map_<scope_slug>.md` |

---

## 3. 節點類型

| `type` | 說明 | 對應上下文層 | 典型 `node_id` 前綴 |
|--------|------|----------------|---------------------|
| **`root`** | 全系統唯一根節點；制度／紅線／全局 runner 索引 | `root_context`（A-1） | `root` |
| **`subtree`** | 附著於 line／dept／module／theme 的子域節點 | 治理層第四片段（A-2）；**待 A-5 映射** | `subtree.<mount>.*` |

**規則**：

1. 每張 nav map **有且僅有一個** `type=root` 節點（`node_id` 建議固定為 `root`）。  
2. `type=subtree` 節點的 `node_id` **應與** A-2 `subtree_id` **一致**（見 A-2 §8.1）。  
3. 禁止以 `type=file` 或單次票號作為節點類型；票號放在 `notes` 或 working，不進 node_id。

---

## 4. 欄位定義（模板列）

下列欄位用於 **Markdown 表格** 或日後 YAML／JSON 實例化；本票不鎖死序列化格式。

| 欄位 | 必填 | 適用 `type` | 說明 |
|------|------|-------------|------|
| **`node_id`** | 是 | root, subtree | 節點唯一 id；root 固定 `root`；subtree 對齊 `subtree_id` |
| **`type`** | 是 | root, subtree | `root` \| `subtree` |
| **`line`** | root：可空；subtree：建議 | 主線代號 `A`～`E` 或 `F`（對齊 `00_master_plan.md` §2） |
| **`dept`** | 否 | subtree | 部門／cabin 邏輯鍵（見 `DEPARTMENT_MAP.md`）；無則 `-` |
| **`module`** | 否 | subtree | 模組／子目錄邏輯名；無則 `-` |
| **`theme`** | 否 | subtree | 跨目錄主題（如 `sprint0-f-a`）；無則 `-` |
| **`mount_type`** | subtree 必填 | subtree | `line` \| `dept` \| `module` \| `theme`（A-2 §3） |
| **`scope_label`** | subtree 建議 | subtree | 人類可讀一句話（新 chat 首屏） |
| **`parent_node_id`** | subtree 建議 | subtree | 父節點；通常為 `root` |
| **`entry_refs`** | 是 | root, subtree | 有序邏輯檔名列表（3～7 項）；repo 相對路徑，**禁止**本機絕對路徑 |
| **`nav_map_ref`** | 建議 | root, subtree | 指向**本導航圖**或子圖的邏輯名；root 可指向本檔 |
| **`queue_ids`** | 否 | subtree | 相關 `90_run_queue.md` 票號（如 `A-4`）；多個用逗號分隔 |
| **`master_plan_anchor`** | 否 | root, subtree | `00_master_plan.md` 章節錨點語意（如 `§5.1`） |
| **`active_default`** | 否 | subtree | 接戰時是否預設載入：`true` \| `false` |
| **`notes`** | 否 | root, subtree | 派工備註、阻塞、與他節點差異（一句話為宜） |

### 4.1 `entry_refs` 填寫規則

1. **順序**：接戰必讀 → 本線／本票規格 → 執行期合同（若本輪會動入口）→ 驗收引用。  
2. **數量**：建議 3～7 條；超過 7 條應拆 subtree 或改指向子 `nav_map_ref`。  
3. **內容**：僅邏輯路徑；不貼全文、不貼金鑰、不貼 CLI 完整輸出。  
4. **與 deny 的關係**：`entry_refs` 所列檔案**可讀**；檔內 deny 類內容仍不得注入 prompt（A-3，本檔不展開細則）。

### 4.2 `nav_map_ref` 填寫規則

| 情境 | `nav_map_ref` 語意 |
|------|-------------------|
| 節點為全局根 | 指向本模板檔邏輯名（如 `workflow_upgrade/01_context-entry/40_navigation_map_template.md`） |
| 節點為某線專屬 | 指向該線 nav map **實例**邏輯名（Sprint 0 可仍指向本模板 + `notes` 標「待實例化」） |
| 子圖嵌套 | 父 subtree 的 `nav_map_ref` 指向子圖；子圖內再列 subtree 節點（**禁止**超過 2 層嵌套） |

---

## 5. 從任務線 → Context 節點的標準導航路徑

### 5.1 文字流程（新 chat／接戰）

```
尚書省指令 / 任務卡
    → 查 90_run_queue.md（票號、Line、Status、Output File）
    → 查 00_master_plan.md（主線邊界、Sprint 依賴）
    → 解析 Line → 定位 nav map 中 type=subtree 節點（或僅 root）
    → 讀 root 節點 entry_refs（全局制度摘要）
    → 讀活躍 subtree 節點 entry_refs + handoff_digest（A-2，不在本圖重複）
    → 執行期若組裝上下文：build_rooted_context（合同權威；subtree 映射待 A-5）
    → 開 working（本輪 query／task_input）
```

### 5.2 決策表（任務線 → 節點）

| 輸入（任務來源） | 第一步查詢 | 應載入節點 | 必讀來源 |
|------------------|------------|------------|----------|
| 口令「接戰」、無具體票 | `AGENTS.md` + root `entry_refs` | **`root` only** | root 表 + `context/context_entry_contract.md` |
| `90_run_queue` 票號 `A-*` | 該行 `Line`=`A` | **`root` + `subtree`（`line.a.*`）** | root 表 + A 線 subtree 的 `entry_refs` |
| `90_run_queue` 票號 `F-*` | `Line`=`F` | **`root` + 可選 `subtree`（`line.f.*` 若已定義）** | root 表 + F 線 notes |
| 暗部／部門票（`dept.*`） | 任務卡明示部門鍵 | **`root` + `subtree`（`dept.<key>`）** | 部門 subtree；root 禁則不跳過 |
| 單模組重構票 | 任務卡 `module` 邏輯名 | **`root` + `subtree`（`module.<name>`）** | 模組 subtree |
| 跨線主題（如 Sprint 0） | `theme.*` 標籤 | **`root` + 最多 2 個活躍 subtree** | 見 A-2 §7 活躍上限 |
| 僅讀碼、不調 LLM | — | **可不載入 nav map** | 無 prompt 組裝則跳過 |

### 5.3 與上下文層的對應（治理語意）

| 導航階段 | 消費的 nav map 欄位 | 落入的上下文層 |
|----------|---------------------|----------------|
| 全局接戰 | root.`entry_refs` | 指導載入 **`root_context`** 內容類型（A-1 §3） |
| 線／票施工 | subtree.`entry_refs` | 指導 **subtree** 片段（A-2；執行期映射 A-5） |
| 本輪問答 | （不在 nav map） | **`working_context`** |
| 檢索增強 | （不在 nav map） | **`long_term_memory`** |

---

## 6. 與 Master Plan / Run Queue 的對帳方式

### 6.1 對帳原則

| 權威檔 | 角色 | nav map 如何對齊 |
|--------|------|------------------|
| **`workflow_upgrade/00_master_plan.md`** | 主線邊界、Sprint 依賴、DoD | 每個 `type=subtree` 且 `mount_type=line` 的節點，`line` 欄與 §2 主線表一致；`master_plan_anchor` 填章節語意 |
| **`workflow_upgrade/90_run_queue.md`** | 可派工票狀態 | `queue_ids` 列當前活躍票；票 **DONE** 後更新 subtree.`notes`，**不刪**歷史節點 |
| **本模板** | 欄位與路徑標準 | 實例檔不得與本模板欄位定義衝突；衝突以尚書省裁決 |

### 6.2 對帳步驟（治理／A-6 可用）

1. **隊列 → 節點**：在 `90_run_queue.md` 取 `ID`、`Line`、`Output File`；在 nav map 找 `queue_ids` 匹配或 `notes` 含該 ID 的 subtree。  
2. **節點 → 隊列**：每個 `active_default=true` 的 subtree 應至少對應一張 **TODO／DOING** 票或明確標「維護態」於 `notes`。  
3. **Master Plan → 依賴**：`00_master_plan.md` §5.1 依賴圖變更時，檢查相關 subtree 的 `entry_refs` 是否仍含依賴票產物路徑。  
4. **版本**：root／subtree 摘要變更時，同步 bump A-1 `root_version` 或 A-2 `subtree_version`（不在 nav map 重複全文）。

### 6.3 不一致時的裁決

| 不一致 | 裁決 |
|--------|------|
| 隊列 `Output File` 不在 `entry_refs` | 以隊列為準**追加** `entry_refs`（末尾追加，不覆蓋既有順序前段） |
| nav map 有節點但隊列無票 | 標 `active_default=false` 或 `notes: 維護態/無活躍票` |
| 兩 subtree 的 `entry_refs` 大量重疊 | 合併為一棵或抽共用子圖（`nav_map_ref` 指向子圖） |
| 與 `context_entry_contract` 衝突 | 尚書省 ＞ 憲法 ＞ **合同** ＞ 本模板 |

---

## 7. 空白模板表（複製使用）

> 填寫新線／新子域時複製下表；**勿**在本檔下方直接累積大量實例（實例另檔）。

| node_id | type | line | dept | module | theme | mount_type | scope_label | parent_node_id | entry_refs | nav_map_ref | queue_ids | master_plan_anchor | active_default | notes |
|---------|------|------|------|--------|-------|------------|-------------|----------------|------------|-------------|-----------|-------------------|----------------|-------|
| `root` | root | - | - | - | - | - | 全局制度與入口索引 | - | （見 §8 示例） | `workflow_upgrade/01_context-entry/40_navigation_map_template.md` | - | `§2,§5` | - | 全系統唯一 |
| | subtree | | | | | | | `root` | | | | | | |

---

## 8. 最小示例（root + 2 subtree）

下列為 **Sprint 0 · A 線** 示意；路徑均為 repo 相對邏輯名。

| node_id | type | line | dept | module | theme | mount_type | scope_label | parent_node_id | entry_refs | nav_map_ref | queue_ids | master_plan_anchor | active_default | notes |
|---------|------|------|------|--------|-------|------------|-------------|----------------|------------|-------------|-----------|-------------------|----------------|-------|
| `root` | root | - | - | - | - | - | 戰車全局接戰與 H 線入口 | - | `AGENTS.md`; `context/context_entry_contract.md`; `04_Workflows/HARNESS_CONSTITUTION.md`（§7 類型）; `workflow_upgrade/00_master_plan.md`; `workflow_upgrade/90_run_queue.md` | `workflow_upgrade/01_context-entry/40_navigation_map_template.md` | - | `§2,§5.2` | - | 不替代 A-1 全文 digest |
| `line.a.context-entry` | subtree | A | - | - | sprint0-f-a | line | Sprint 0 · Context Entry 規格層 | `root` | `workflow_upgrade/01_context-entry/A0_context_entry_overview.md`; `workflow_upgrade/01_context-entry/A1_root_context_spec.md`; `workflow_upgrade/01_context-entry/A2_subtree_context_spec.md`; `context/context_entry_contract.md` | `workflow_upgrade/01_context-entry/40_navigation_map_template.md` | A-4,A-5 | `§4,§5.1` | true | A-4 產出本模板；A-5 待 runbook |
| `line.f.workflow-upgrade` | subtree | F | - | - | sprint0 | line | Sprint 0 總控（F 線） | `root` | `workflow_upgrade/00_master_plan.md`; `workflow_upgrade/90_run_queue.md`; `workflow_upgrade/01_context-entry/A0_context_entry_overview.md` | `workflow_upgrade/01_context-entry/40_navigation_map_template.md` | F-1,F-2 | `§3,§6` | false | 無獨立施工時僅維護隊列 |

**示例解讀**：

- 接 **A-4** 票：先鎖定 `line.a.context-entry`，再按該行 `entry_refs` 順序閱讀；全局禁則仍經 `root`。  
- 接 **F-2** 票：可僅讀 `line.f.workflow-upgrade` 三檔 + root 之合同／憲法類型引用。  
- `nav_map_ref` 均指向**本模板檔**；未來若拆 `nav_map_line_a.md`，僅改 subtree 列之 `nav_map_ref`，不改 `node_id`。

---

## 9. 與執行期 builder 的邊界（v0.1）

| 項目 | 現狀（僅描述） | 本模板 |
|------|----------------|--------|
| `build_rooted_context` 輸出 | `root_context` / `working_context` / `long_term_memory` | 不新增頂層鍵 |
| `context_builder` mock `navigation` | 內嵌少量邏輯名（`AGENTS.md` 等） | 治理層可**超集**規劃；實作對齊另開票 |
| `subtree_context` | **未**作為合同頂層欄位 | 節點表先行；A-5 定映射 |
| nav map 檔案產出 | **無**自動生成 | 人工或 A-6 維護實例檔（若需要） |

---

## 10. 驗收對照（本票 A-4）

| 檢查項 | 通過標準 |
|--------|----------|
| 節點類型 | §3 定義 root／subtree |
| 欄位完整 | §4 含 `node_id`、`type`、`line`／`dept`／`module`／`theme`、`entry_refs`、`nav_map_ref`、`notes` |
| 導航路徑 | §5 含文字流程 + 決策表 |
| 對帳 | §6 含 master plan + run queue 規則 |
| 最小示例 | §8 含 root + 2 subtree 表格 |
| 不越界 | 無 ignore/deny 細則、無 runbook 步驟、無程式變更 |
| 不假裝實作 | §9 明確標註 builder 未輸出 subtree／nav 檔 |

---

## 11. 留給 A-5 的缺口（本票不寫）

| 缺口 | 負責票 |
|------|--------|
| 接戰／派工 **逐步** CLI 與檢查清單 | A-5 |
| `subtree_context` 映射至 `build_rooted_context` 回傳形狀 | A-5 |
| ignore／deny 在組裝前的掃描順序 | A-5（引用 A-3） |
| Phase 10.5 上游欄位消費表 | A-5 |
| nav map **實例檔** 是否必要、放置目錄 | A-5 或尚書省裁決 |
| unittest／煙測與 nav map 一致性自動檢查 | A-5 或後續實作票 |

---

## 12. 引用索引（邏輯名）

- `workflow_upgrade/01_context-entry/A1_root_context_spec.md` — §3.4 `navigation`  
- `workflow_upgrade/01_context-entry/A2_subtree_context_spec.md` — `entry_refs`、`nav_map_ref`、`subtree_id`  
- `workflow_upgrade/01_context-entry/A3_ignore_and_deny_rules.md` — deny 邊界（本檔不複製）  
- `workflow_upgrade/00_master_plan.md` — 主線 A–E、§5.1 依賴  
- `workflow_upgrade/90_run_queue.md` — 票號與 `Line` 欄  
- `context/context_entry_contract.md` — H 線唯一入口  

---

## 變更紀錄

| 日期 | 變更 |
|------|------|
| 2026-05-25 | A-4 初版：nav map v0.1 模板、欄位、路徑、對帳、最小示例 |
