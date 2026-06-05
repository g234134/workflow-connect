# Workflow Upgrade — Master Plan (Sprint 0)

> **角色（F 線）**：本目錄總控層；定目標、主線邊界、依賴順序與完成定義。  
> **不取代**：戰車根 `00_master_plan.md`（企業化補強戰役封存）、`_workflow_upgrade/90_run_queue.md`（歷史隊列）。  
> **派工黑板**：`workflow_upgrade/90_run_queue.md`（本輪 Sprint 0 任務狀態）。

---

## 1. 本輪 Workflow Upgrade 目標

在**不擴 production 程式、不做 UI** 的前提下，為下一階段工作流治理補齊**文字骨架**：

- 主線 A–E 職責清楚、命名穩定、依賴可追蹤；
- Sprint 0 先落地 **F（總控）+ A（Context Entry 規格層）**；
- 後續 chat 可從 `90_run_queue.md` 單挑一條 A 線任務接手，無需重複發明目錄結構。

---

## 2. 主線 A–E 簡述

| 線 | 代號 | 職責（高層） |
|----|------|----------------|
| **A** | Context Entry | 根／子樹上下文規格、ignore／deny、導航圖模板、runbook（文件層；對齊既有 `build_rooted_context` 合同） |
| **B** | （預留） | 工作流編排／handoff 治理文件（Sprint 0 不展開） |
| **C** | （預留） | 可觀測／eval 治理文件（Sprint 0 不展開） |
| **D** | （預留） | Skills／能力包治理文件（Sprint 0 不展開） |
| **E** | （預留） | 外部連接／通道邊界文件（Sprint 0 不展開） |

---

## 3. F 線：總控層角色

| 項 | 說明 |
|----|------|
| **擁有** | `workflow_upgrade/00_master_plan.md`、`workflow_upgrade/90_run_queue.md` |
| **不做** | A–E 各線正文規格、implementation 細節、程式與 UI |
| **要做** | 主線邊界、Sprint 切分、依賴順序、隊列狀態、與戰車根既有戰役的索引關係 |
| **分離** | F 文件 ≠ A 文件；禁止把 Context Entry 規格寫進本 Master Plan 正文 |

---

## 4. Sprint 0 = F + A 的定位

| 層 | Sprint 0 範圍 | 不在 Sprint 0 |
|----|----------------|----------------|
| **F** | 目錄、`00_master_plan.md`、`90_run_queue.md` 初版與狀態機 | B/C/D/E 細任務展開 |
| **A** | `01_context-entry/` 目錄 + overview + A-1～A-5 規格稿 + runbook（見隊列） | 改 `core/`、hooks、connector、dashboard |

**原則**：文件優先、文字治理優先；結構與命名先穩，內容後續增量。

---

## 5. 依賴順序與 Phase 10.5 關聯

### 5.1 Sprint 0 內依賴（F → A）

```
F-1 (master plan) → F-2 (run queue) → A-0 (overview)
    → A-1 (root spec) → A-2 (subtree spec)
    → A-3 (ignore/deny) ─┐
    → A-4 (nav map)     ├→ A-5 (runbook) → A-6 (queue 回寫)
```

- **A-3 / A-4** 可與 **A-2** 部分並行，但 **A-5** 須待 A-1～A-4 至少有可引用草案。
- **A-6** 僅更新 `90_run_queue.md` 狀態，不改規格正文。

### 5.2 與戰車根既有能力（只索引、不重寫）

| 既有產物 | 關係 |
|----------|------|
| `context/context_entry_contract.md` + `core/context_entry.py` | 執行期**權威**；A 線文件為治理層補充，不得與合同衝突 |
| 根 `00_master_plan.md` §4（H 線 done） | 能力已落地；Sprint 0 A 線做**可派工規格化**，非重開 H 實作票 |
| `_workflow_upgrade/` | **歷史**企業化補強隊列；與本目錄 `workflow_upgrade/` **不同路徑**，勿混用 |

### 5.3 Phase 10.5（ask 圖路由）關聯

`skills/skills_contract.md` **§10.5 Graph routing (ask)** 定義：

`health → selector → [use_rag? retrieve → answer : answer] → END`

**關聯語意**：

- **A 線**規定上下文如何組裝（root／subtree／deny／nav），是 selector 與 retrieve 的**上游輸入契約**；
- **Phase 10.5**是下游**路由與節點順序**；A 線文件須標註哪些 context 欄位會被 selector／retrieve／answer 消費，但不改寫 §10.5 路由表本身；
- Sprint 0 **不**實作圖或改 `langgraph_flow`；僅確保規格層與 §10.5、§8 `context_entry_contract` 場景表可對賬。

---

## 6. 各主線完成定義（高層）

| 線 | 完成定義（DoD · 高層） |
|----|------------------------|
| **F** | `00_master_plan.md` 與 `90_run_queue.md` 職責分離；隊列含 A–E 邊界；F 票狀態可追溯 |
| **A** | `01_context-entry/` 內 overview + 四份 spec 模板 + runbook 存在且互相引用一致；新 chat 可單票接手 A-1～A-5 任一項 |
| **B** | （Sprint 0 後）編排／handoff 治理文件集齊，並在隊列掛票 |
| **C** | （Sprint 0 後）觀測／eval 治理文件集齊，並在隊列掛票 |
| **D** | （Sprint 0 後）Skills 治理文件集齊，並在隊列掛票 |
| **E** | （Sprint 0 後）外部通道邊界文件集齊，並在隊列掛票 |

**Sprint 0 出口**：F 骨架 + A 線隊列初始化完成；B/C/D/E 僅 placeholder，無細規格正文。

---

## 7. 目錄索引

| 路徑 | 用途 |
|------|------|
| `workflow_upgrade/00_master_plan.md` | 本檔（F） |
| `workflow_upgrade/90_run_queue.md` | 任務隊列（F 維護狀態） |
| `workflow_upgrade/01_context-entry/` | A 線產物目錄（規格與 runbook） |
| 根 `00_master_plan.md` §4.11 | Sprint 4 · O-2 monitoring subagent 戰役封存（程式 + 制度） |
| 根 `00_master_plan.md` §4.12 | Sprint 5 · monitoring graph 治理（selector／SLO 條款；L0 only） |
| `workflow_upgrade/90_run_queue.md` · O 線 | C-1／O-2a／O-2b／O-2c 狀態 |
