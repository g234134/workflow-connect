# Multi-Agent Collaboration Specification v1

> **§0 上游 contract**：Phase 4 contract SSOT → [`docs/phase4-multi-agent-collaboration-contract-v1.md`](phase4-multi-agent-collaboration-contract-v1.md)（routing、关口、STATE 写入冻结）；本 spec 为操作层角色细节，冲突依 contract §1.2 层级裁决。

> **版本**：v1.0  
> **適用**：大唐三省六部 repo 內 Multi-Chat 四角色協作（Orchestrator / Implementer / Reviewer / Scribe）  
> **日期**：2026-06-10  
> **上游文件**：`.cursor/rules/multi_chat_roles.mdc` · `AGENTS.md` · `ENGINEERING_CONTRACT.md`

---

## §1 目的

本文件定義 Multi-Chat 模式下四角色（Orchestrator / Implementer / Reviewer / Scribe）的協作規格，包括：

- 各角色的目的、做什麼、不做什麼
- 典型輸入與輸出格式
- 驗收標準與 Definition of Done (DoD)
- 角色切換與 handoff 原則
- 與現行工程合約、票 state 機制的對齊方式

本文件為「已存在做法的文檔化」，不發明新流程，僅收斂現行實際運作方式。

---

## §2 角色清單

### 2.1 現行四角色

| 角色 | 代號 | 核心職責 | 對應 Cursor Subagent |
|------|------|----------|---------------------|
| **Orchestrator** | O | 排票、凍結 scope、協調衝突、收口關票 | `coordinator` + 父 agent |
| **Implementer** | B-* | 在 AllowedPaths 內實作功能、補測試、執行驗證 | `implementation-worker` |
| **Reviewer** | C | 唯讀審查 diff、對照合約驗收、判定結論 | `checker-reviewer` |
| **Scribe** | D | 整理文檔、更新戰報、維護 Progress 末尾條目 | （無對應 subagent） |

### 2.2 預留角色（尚未正式啟用）

| 角色 | 預期用途 | 現況 |
|------|----------|------|
| **Planner** | 專職需求拆解與 FRAME 設計 | 由 Orchestrator 兼任 |
| **Executor** | 專職 runner / CLI 執行與結果蒐集 | 由 Implementer 兼任 |
| **Judge** | LLM-based 自動判分 / eval | 預留，尚未實作 |
| **Subagent** | runtime 派工（非 Cursor IDE 內） | 見 `subagents/*`（H 線） |

---

## §3 角色詳細規格

### §3.1 Orchestrator (O)

#### 目的
確保票的生命週期有序推進：開票時凍結 scope 與邊界，執行中協調衝突，收尾時合併 REPORT、更新 STATE、關票。

#### 做什麼

| 項 | 說明 |
|----|------|
| 開票 | 複製 template → `04_Workflows/tickets/<id>_state.md`；填 FRAME（Goal/Scope/NonScope/AllowedPaths/BlockedPaths/AC） |
| 排票 | 排定票順序與依賴；凍結每張票的 `allowed_paths` / `blocked_paths` |
| 分派 | 為各 chat 指定角色（B/C/D）與模型（若尚書省有要求） |
| 協調 | 解跨票衝突、scope 重疊與優先級爭議；裁決「可開下一張票」 |
| 啟動 | 帶領各 chat 完成 `AGENTS.md` §初始化校準（含第 10 步 Multi-Chat）並閱讀 `multi_chat_roles.mdc` |
| 收口 | 彙整 B/C/D REPORT，對尚書省收口；**不**繞過 Reviewer 直接標票 done |
| 維護 STATE | 更新 `overall_status`、`current_owner`、`next_action`、`status_by_role` |

#### 不做什麼

- **不**撰寫功能程式或跑實作級 refactor（除非是修改計畫本身所需之極小文字）
- **不**大改 docs、戰報正文或 Progress 歷史段落（計畫調整除外）
- **不**繞過 Reviewer 直接宣告票項驗收通過或可交付
- **不**自行擴張票 scope 或覆寫尚書省指令

#### 典型輸入

- 尚書省指令 / 需求描述
- 上游票 STATE（依賴關係）
- B_REPORT / C_REPORT / D_REPORT（收口時）

#### 典型輸出

- `<ticket_id>_state.md` 的 FRAME 與 STATE 區塊
- 關票決策（`overall_status: done`）
- 對尚書省的結構化回報（變更摘要、風險、後續票建議）

#### 驗收標準 / DoD

- [ ] FRAME 填寫完整（Goal/Scope/NonScope/AllowedPaths/BlockedPaths/AC/VerificationCommands）
- [ ] STATE 初始化（`overall_status: draft`、`current_owner: orchestrator`）
- [ ] 角色分派明確（B/C/D 已指派）
- [ ] 收工時 STATE 反映最終狀態（`overall_status: done`，各 role 標 done）

---

### §3.2 Implementer (B-*)

#### 目的
在 FRAME 定義的邊界內，完成實作、補測試、執行驗證，並以結構化格式回報結果。

#### 做什麼

| 項 | 說明 |
|----|------|
| 讀取 | 讀 FRAME（AllowedPaths 為硬邊界）、STATE（當前狀態） |
| 實作 | 在 AllowedPaths 內寫 code / docs / tests；遵守 ENGINEERING_CONTRACT 四流派與 12-rule |
| 回傳結構 | 核心路徑回傳 `dict`（含 `ok` / `message` 或專案慣用鍵） |
| 起手報告 | 列已讀清單 + 2–5 行計畫 |
| 驗證 | 執行 FRAME.VerificationCommands，保留輸出證據 |
| 回報 | 填 B_REPORT（changed_files / artifacts / verification / behavior_notes / deferred_items） |
| 回報阻塞 | 發現 scope 不足或跨邊界需求時，回報 Orchestrator，**不**自行擴票 |

#### 不做什麼

- **不**順手改其他票範圍、無關檔案或 `blocked_paths`（Rule 3：最小觸及）
- **不**越權改 `AGENTS.md`、憲法、合約、`.cursor/rules`（本票明示授權除外）
- **不**改非本人 `core` 或他人 workspace 三件套（Rule 8）
- **不**推測寫死路徑、API 或 env（Rule 6）
- **不**碰憲法 §7 禁區類型（Rule 5）
- **不**直接標票 done 或可交付（Rule 11；須 Reviewer 審查）
- **不**寫 FRAME / STATE / C_REPORT / D_REPORT

#### 典型輸入

- `04_Workflows/tickets/<id>_state.md` 的 FRAME + STATE
- 上游依賴檔案（依 FRAME.Dependencies）
- `multi_chat_roles.mdc` §Implementer 邊界

#### 典型輸出

- B_REPORT 區塊（直接寫入 state 檔）
- 變更的檔案（在 AllowedPaths 內）
- 驗證命令輸出（貼入 B_REPORT.verification）

#### 驗收標準 / DoD

- [ ] B_REPORT 填寫完整（changed_files / artifacts / verification / behavior_notes / deferred_items）
- [ ] verification 含可重跑命令與關鍵結果語意（`ok` / `count` / `exit 0` 等）
- [ ] 所有變更在 AllowedPaths 內，無 BlockedPaths 誤觸
- [ ] 核心路徑回傳結構化 `dict`（非僅自然語言）
- [ ] skeleton / placeholder 已分欄標示（Rule 7）

---

### §3.3 Reviewer (C)

#### 目的
唯讀審查 Implementer 產出，對照合約與票規格判定「可接受 / 需修改 / 拒絕」。

#### 做什麼

| 項 | 說明 |
|----|------|
| 讀取 | 讀 FRAME（AC 為驗收標準）、STATE、B_REPORT |
| 對照 | 對照 `ENGINEERING_CONTRACT.md`（四流派、12-rule、Work Report 附錄 A） |
| spot-check | 必要時讀實際變更檔案（抽查），但**不改**任何內容 |
| 判定 | 結論 ∈ {`accepted`, `accepted_with_gaps`, `needs_changes`, `rejected`} |
| 列風險 | 列具體風險、遺漏驗證與修改建議（可引用 Rule 編號） |
| 確認 | skeleton / placeholder 已分欄、無證據不得標完成（Rule 11） |
| 回報 | 填 C_REPORT（conclusion / blocking_issues / checks_summary / risk_level / suggestions） |

#### 不做什麼

- **不**撰寫新功能、新增 code 檔案或實作修補
- **不**做大規模 refactor 或順手改 docs（審查意見以回報呈現）
- **不**替 Implementer 收尾實作以「幫忙過關」
- **不**自行宣告里程碑編號或寫入 `master_status.md` / `handoff.md`（Governance 獨占）
- **不**寫 FRAME / STATE / B_REPORT / D_REPORT
- **不**修改任何程式碼或文檔實體

#### 典型輸入

- `04_Workflows/tickets/<id>_state.md` 的 FRAME + STATE + B_REPORT
- 變更檔案的 diff（spot-check）
- `multi_chat_roles.mdc` §Reviewer 邊界
- `ENGINEERING_CONTRACT.md`（驗收權威）

#### 典型輸出

- C_REPORT 區塊（直接寫入 state 檔）
- 結論與建議（結構化，非僅自然語言）

#### 驗收標準 / DoD

- [ ] C_REPORT 填寫完整（conclusion / blocking_issues / checks_summary / risk_level / suggestions）
- [ ] conclusion 明確（四選一）
- [ ] checks_summary 對照 FRAME.AC 逐條說明 ✅ / ⚠️ / ❌
- [ ] 若 `needs_changes`，列出具體修改項（引用 Rule 或 AC 編號）

---

### §3.4 Scribe (D)

#### 目的
依 Implementer 與 Reviewer 的核定結果，整理文檔、更新戰報、維護進度索引，確保 v1 敘事一致。

#### 做什麼

| 項 | 說明 |
|----|------|
| 讀取 | 讀 FRAME、STATE、B_REPORT、C_REPORT |
| 整理 | 更新 docs（術語統一、交叉引用、連結修正） |
| 戰報 | 於 `04_Workflows/00_Agent_Work_Progress.md` **末尾追加**條目（不重排既有段落） |
| 格式 | 組裝戰報 JSON 草稿供 `_ops_cycle.py validate-report`（OPS_CYCLE.md 格式） |
| 引用 | 接戰／封存流程引用 `AGENTS.md`，**不**另立封存 SOP |
| 回報 | 填 D_REPORT（docs_updates / progress_entry / followup_suggestions） |

#### 不做什麼

- **不**偷偷改程式邏輯、測試或 config；發現實作問題應回報 Orchestrator，**不**自行開工修 code
- **不**刪除或重排 `00_Agent_Work_Progress.md`、`00_Agent_Work_Conditions.md` 既有段落（僅末尾追加）
- **不**未經 Orchestrator/Reviewer 確認即宣稱票項封存完成
- **不**覆寫 `project_status/master_status.md` 或 `handoff.md`（除非尚書省另授權 Governance 票）
- **不**寫 FRAME / STATE / B_REPORT / C_REPORT
- **不**代替 Reviewer 做 acceptance 裁決

#### 典型輸入

- `04_Workflows/tickets/<id>_state.md` 的 FRAME + STATE + B_REPORT + C_REPORT
- `04_Workflows/00_Agent_Work_Progress.md` 末尾（append 位置）
- `multi_chat_roles.mdc` §Scribe 邊界

#### 典型輸出

- D_REPORT 區塊（直接寫入 state 檔）
- 更新的 docs（cross-ref、術語統一）
- Progress 末尾條目（1–3 句摘要）

#### 驗收標準 / DoD

- [ ] D_REPORT 填寫完整（docs_updates / progress_entry / followup_suggestions）
- [ ] progress_entry 符合 `OPS_CYCLE.md` 格式（供 `_ops_cycle.py` 工具鏈消費）
- [ ] docs_updates 列明新增/更新路徑與要點
- [ ] 未重排 Progress 既有段落（僅末尾追加）

---

## §4 角色切換與 Handoff 原則

### 4.1 標準流程（B → C → D → O）

```
需求討論（任意 chat）
    ↓
Orchestrator 建 state 檔 → 填 FRAME、初始化 STATE
    ↓
[Step B] Implementer 讀 state → 施工 → 直接回寫 B_REPORT
    ↓
[Step C] Reviewer 讀 state → 審查 → 直接回寫 C_REPORT
    ↓
[Step D] Scribe 讀 state → 整理 → 直接回寫 D_REPORT
    ↓
[Step O] Orchestrator 讀各 REPORT → 更新 STATE → 關票（overall_status: done）
```

### 4.2 可重跑情境（loop back）

| 情境 | C_REPORT 結論 | 下一步 | 說明 |
|------|--------------|--------|------|
| 一次通過 | `accepted` 或 `accepted_with_gaps` | B → C → D → O | 無阻擋問題，流程繼續至 Scribe |
| 需修改 | `needs_changes` | **回到 B** | Reviewer 列出修改項，Implementer 重跑 Step B（更新 B_REPORT），再進 C |
| 嚴重問題 | `rejected` | Orchestrator 介入 | 可能重開票或調整 FRAME，重新走 B → C → D → O |
| Scribe 發現 | （Scribe 不回傳結論，但可標註） | 回報 Orchestrator | 若 Scribe 發現實作問題，回報 O，O 決定是否退回 B |

### 4.3 Handoff 要點

1. **單一真相來源**：每張票一份 `04_Workflows/tickets/<ticket_id>_state.md`
2. **直接讀寫**：各角色 chat 用 Cursor 讀檔／改檔，只寫自己被允許的區塊
3. **不重搬運**：人工不負責把 REPORT 從 chat 複製貼回 state（agent 直接寫檔）
4. **保留歷史**：重跑 B/C/D 時，**不刪除**既有 REPORT，而是在原區塊追加或更新內容

### 4.4 區塊讀寫權限表

| 區塊 | 維護者 | 讀 | 寫 |
|------|--------|----|----|
| FRAME | Orchestrator | 全角色 | 僅 Orchestrator |
| STATE | Orchestrator | 全角色 | 僅 Orchestrator |
| B_REPORT | Implementer | 全角色 | 僅 Implementer |
| C_REPORT | Reviewer | 全角色 | 僅 Reviewer |
| D_REPORT | Scribe | 全角色 | 僅 Scribe |

---

## §5 與現行工程合約 / Ticket State 的對齊

### 5.1 與 ENGINEERING_CONTRACT.md 的關係

| 合約項目 | Multi-Chat 對齊方式 |
|----------|---------------------|
| 四流派（Context/Source/Incremental/Debugging） | Implementer 遵守；Reviewer 審查時檢查四流派覆蓋 |
| 12-rule | 全角色遵守；Reviewer 以 Rule 編號引用問題 |
| Work Report 七節 | B_REPORT 為子集（變更/驗證/阻塞/下一步）；C/D_REPORT 為協作擴展 |
| Rule 3（最小觸及） | Implementer 僅改 AllowedPaths；Reviewer 檢查 diff 範圍 |
| Rule 8（邊界尊重） | Implementer 不改他人 core；Orchestrator 不寫 code |
| Rule 11（驗證後宣稱） | Implementer 不自標 done；Orchestrator 僅在 Reviewer 通過後關票 |

### 5.2 與 Ticket State 機制的對齊

| State 區塊 | 對應角色 | 對應合約 |
|------------|----------|----------|
| FRAME | Orchestrator | 合約 §6.1 起手節奏（Context → 邊界 → Source 列檔） |
| STATE | Orchestrator | 合約 §6.4 收尾（提交 Work Report） |
| B_REPORT | Implementer | 合約附錄 A Work Report（§1 變更 / §4 驗證 / §5 阻塞 / §6 下一步） |
| C_REPORT | Reviewer | 合約 §7.1（收尾含變更/skeleton/placeholder/阻塞/下一步） |
| D_REPORT | Scribe | 合約 §6.4（戰報封存） |

### 5.3 與 AGENTS.md 的對齊

| AGENTS.md 項目 | Multi-Chat 對齊方式 |
|----------------|---------------------|
| 接戰／封存口令 | 全角色適用；Orchestrator 啟動時帶領各 chat 完成 §初始化校準（含第 10 步） |
| 紅線（禁印金鑰、禁硬編路徑等） | 全角色遵守；Reviewer 審查時檢查 |
| OPS_CYCLE | Scribe 依 §封存協議組裝戰報 JSON |
| Cursor Subagents | Multi-Chat 四角色為 IDE 內協作；runtime subagents 為 H 線獨立機制 |

### 5.4 權威位階

```
尚書省當次指令 ＞ HARNESS_CONSTITUTION.md ＞ ENGINEERING_CONTRACT.md ＞ multi_chat_roles.mdc ＞ 本檔 ＞ 票 brief.md / notes.md
```

- 衝突時依位階向上裁決
- 高風險禁區 override 須**先明示風險**，再執行並於 Progress／notes **末尾**留痕

---

## §6 參考索引

| 主題 | 權威路徑 |
|------|----------|
| 角色邊界（完整版） | `.cursor/rules/multi_chat_roles.mdc` |
| 工程合約 | `04_Workflows/ENGINEERING_CONTRACT.md` / `.cursor/rules/engineering-contract.mdc` |
| 接戰／封存 | `AGENTS.md` |
| 票 state 模板 | `04_Workflows/tickets/_templates/ticket_state.template.md` |
| 票機制說明 | `04_Workflows/tickets/README.md` |
| Cursor Subagents | `.cursor/agents/DISPATCH_GUIDE.md` |

---

*本檔為 W5-T0 · Multi-Agent Collaboration Docs 交付物 · 2026-06-10*
