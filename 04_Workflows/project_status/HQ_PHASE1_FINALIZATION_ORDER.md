# Phase 1 定稿令

> **裁決者**：尚書省總管  
> **裁決日**：2026-05-19  
> **依據**：W0–W5 審稿通過；W4 盲測 `HQ-P1-W4-BLIND-10` **10/10**（QA-Reviewer，唯讀）

---

## 一、定稿宣告

自本令發布起，下列檔案為戰車 **HQ 治理 Phase 1** 之**正式權威**（可移植層 + 本戰車實例層）：

| 代號 | 正式檔 | 層級 |
|------|--------|------|
| W0 | `04_Workflows/_PORTABLE_CORE_INDEX.md` | 索引 |
| W1 | `04_Workflows/HARNESS_CONSTITUTION.md` | 憲法（可移植） |
| W2 | `04_Workflows/ENGINEERING_CONTRACT.md` | 合約（可移植） |
| W3 | `04_Workflows/DEPARTMENT_MAP.md` | 部門地圖（可移植） |
| W5 | `04_Workflows/INSTANCE_ANCHOR_TANG.md` | 實例錨點 |

**權威位階**（不變）：尚書省當次指令 ＞ 憲法 ＞ 合約 ＞ Progress 當期敘述。

**路徑與 runner**：仍以 `04_Workflows/Master_Map.json` 為準（當前 `version`：**2.61**）。

---

## 二、退役與取代

| 檔案 | 狀態 | 取代為 |
|------|------|--------|
| `HARNESS_Constitution_v0.1.md` | **SUPERSEDED** | `HARNESS_CONSTITUTION.md` |
| `ENGINEERING_CONTRACT_v0.1.md` | **SUPERSEDED** | `ENGINEERING_CONTRACT.md` |

接戰、審稿、盲測**不得**再以 v0.1 為 P0 必讀。歷史稽核可唯讀 v0.1。

**Runbook 線**（`runbooks/*_v0.1.md`）維持檔名；其內三件套引用已同步改指向正式檔（本令執行項）。

---

## 三、本令已執行之同步票

| 票號 | 內容 | 狀態 |
|------|------|------|
| `HQ-P1-RETIRE-V01` | v0.1 檔首 SUPERSEDED；`WORKFLOW_INDEX`、runbooks、W0 母本列更新 | **Done** |
| `HQ-P1-AGENTS-SYNC` | `AGENTS.md` §初始化校準 憲法／合約改指正式檔 | **Done** |
| `HQ-P1-CONDITIONS-DEDUP` | `00_Agent_Work_Conditions.md` HQ 輪實例路徑改引用 W5 | **Done** |
| `HQ-P1-W0-W2-ALIGN` | W0 §3「Blocked 旗標」與 W2 §7.3 測項 #7 對齊裁決 | **Done** |
| `HQ-P1-PROGRESS-W4` | `00_Agent_Work_Progress.md` 末尾 W4 QA 列 | **Done** |

---

## 四、W0／W2 對齊裁決（QA 備註）

### 4.1 W2 §7.3 盲測測項 #7

**裁決**：可移植正文**允許**寫入 **Phase 制度性**角色預設（如「第一階段 DarkOps-Worker **Blocked**」），**須無日期、無 Done 敘述**。

**禁止**寫入三件套者：Progress／war 當輪旗標（如「2026-05-17 registry Done」）。

W2 §7.3 表已修訂；與 W4 10/10 結論一致。

### 4.2 W0 §3 禁止清單

**裁決**：「階段 Blocked／Done 旗標」改為**當輪**狀態旗標；**不禁止** Phase 1 結構性 Blocked 寫入憲法 §5／§6。

---

## 五、Phase 2 升格審查（裁決，非本令施工）

| 項目 | 現況 | 裁決 |
|------|------|------|
| `CURSOR_AGENT_RULES.md` | 2026-05-17 草案存在 | **准予列為 Phase 2 執行母本**；須與**本令定稿**之 `ENGINEERING_CONTRACT.md` diff 對齊後，由尚書省另發 **Phase 2 定稿令** |
| `.cursor/rules/engineering-contract.mdc` | `alwaysApply: true` | **維持啟用**；檔頭標「對齊 ENGINEERING_CONTRACT 定稿」；重大修訂走 Phase 2 票 |
| Phase 2 解鎖語義 | W4 10/10 已達 | **Phase 1 閘門已解鎖**；Phase 2 **規則升格審查**可開工，**不等同**暗部 DarkOps 解禁 |

**下一輪建議票**：`HQ-P2-RULES-FINALIZE`（合約 ↔ CURSOR_AGENT_RULES ↔ .mdc 三方 diff + 指紋登錄）。

---

## 六、後續專案（未在本令執行）

| Phase | 內容 | 票號建議 |
|-------|------|----------|
| Phase 3 | 多智能體任務路由制度 | `HQ-P3-TASK-ROUTING` |
| Phase 4 | 戰報／封存／回顧／自我進化 | `HQ-P4-OPS-CYCLE` |

---

## 七、接戰入口（副官）

憲法／合約／地圖／實例錨點之 P0 必讀，以 `AGENTS.md` §初始化校準為準；細節見 W5 §13 一頁總表。

**本令存檔**：`04_Workflows/project_status/HQ_PHASE1_FINALIZATION_ORDER.md`
