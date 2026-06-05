# Phase 2 定稿令

> **裁決者**：尚書省總管  
> **裁決日**：2026-05-19  
> **依據**：`HQ_PHASE1_FINALIZATION_ORDER.md`（W2 定稿權威）；`HQ_PHASE2_FINALIZATION_CANDIDATE.md`（HQ-P2-RULES-FINALIZE）；W4 盲測 `HQ-P1-W4-BLIND-10` **10/10**（Phase 1 已裁決）

---

## 一、定稿宣告

自本令發布起，下列檔案為戰車 **HQ 治理 Phase 2** 之**正式執行權威**（對齊 Phase 1 定稿之 `ENGINEERING_CONTRACT.md`）：

| 代號 | 正式檔 | 層級 |
|------|--------|------|
| P2-M | `04_Workflows/CURSOR_AGENT_RULES.md` | 執行母本（人類可讀） |
| P2-C | `.cursor/rules/engineering-contract.mdc` | Cursor 強制規則（`alwaysApply: true`，**82** 規則段） |

**權威位階**（不變）：尚書省當次指令 ＞ 憲法（W1）＞ 合約（W2）＞ 本規則檔／`.mdc` ＞ 任務 `brief`／`notes`。

**不取代**：`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`AGENTS.md` 接戰入口；W0–W3、W5 仍以 Phase 1 定稿令為準。

**路徑與 runner**：仍以 `04_Workflows/Master_Map.json` 為準。

---

## 二、尚書省裁決審查結論

| 裁決標準 | 結果 | 證據 |
|----------|------|------|
| 四流派（§4 + §4.5 閘門）對齊 | **PASS** | W2 §4.1–§4.5 ↔ P2-M §3 ↔ P2-C §3 + `GATE-3.5.1` |
| 十二條（§5）對齊 | **PASS** | W2 表格式 12 條 ↔ P2-M `[RULE 1]`–`[12]` ↔ P2-C `RULE-1`–`12` |
| DoD（§7.1–§7.5）對齊 | **PASS** | `FLOW-6.5`（含第八項四流派）、`FLOW-6.6`–`6.7`、`FLOW-6.9`（§7.5 本輪新增） |
| Work Report（附錄 A）對齊 | **PASS** | P2-M `OUT-7.2` 全文模板；P2-C `OUT-7.2` 引用母本／W2 附錄 A |
| 82 段規則與 W2 無衝突 | **PASS** | 候選 §二對照矩陣全項 ✓；機掃 P2-M／P2-C 正文零 `D:\`、`C:\Users\` |
| `.mdc` `alwaysApply: true` | **PASS** | frontmatter 已確認；`.cursor/rules/` 僅此一強制規則檔 |

**P2-M ↔ P2-C 一致性**：**8/8 PASS**（候選 §三；機掃 `.mdc` **82** 個 `###` 規則段）。

**指紋**：`HQ-P2-RULES-FINALIZE` 已補登 3 檔，`registry_total_rows=36473`，`failures=0`。

---

## 三、與 Phase 1 令之銜接

| 項目 | Phase 1 令（2026-05-19） | 本令裁決 |
|------|--------------------------|----------|
| `CURSOR_AGENT_RULES.md` | 准予列為 Phase 2 母本，須與 W2 diff 對齊後另發令 | **已定稿**（P2-M） |
| `engineering-contract.mdc` | 維持啟用；重大修訂走 Phase 2 票 | **已定稿**（P2-C，82 段） |
| Phase 2 解鎖語義 | 規則升格審查可開工；**不等同**暗部 DarkOps 解禁 | **維持**（見 §五） |

**取代敘述**：2026-05-17「Phase 2B 轉制完成／待裁決」之 `master_status` 條目，以本令為準；規則段計數由 81 更正為 **82**（新增 `FLOW-6.9`）。

---

## 四、本令已確認之修補項（HQ-P2-RULES-FINALIZE）

| 項 | 內容 | 狀態 |
|----|------|------|
| 1 | `FLOW-6.5` 補齊 W2 §7.1 第八項「四流派最低覆蓋」 | **Done** |
| 2 | `FLOW-6.9` 轉制 W2 §7.5 暗部協作順序與 Governance 欄位對齊 | **Done** |
| 3 | `META-0.4` 違例範例移除磁碟路徑樣式字串 | **Done** |
| 4 | P2-M ↔ P2-C 同步（81→82 段） | **Done** |
| 5 | 指紋補登 | **Done** |

**W2 原文**：本輪**未改**；仍以 Phase 1 定稿為權威。

---

## 五、暗部與 Phase 升格語義（重申）

| 語義 | 裁決 |
|------|------|
| Phase 2 **規則升格** | **已生效**（本令） |
| Phase 2 **暗部 DarkOps 解禁** | **未解禁**；`DarkOps-Worker` 仍依憲法 §5.2／§6.1 與路由閘門 `assignable: false` |
| W4 盲測 10/10 | Phase 1 已達；本令不重複盲測 |

後續暗部解禁須尚書省另票，不得因本令自動解鎖。

---

## 六、刻意分流（不視為缺口）

| 內容 | 保留於 | 不寫入 P2-M／P2-C 原因 |
|------|--------|------------------------|
| W4 盲測 10 項量表全文 | W2 §7.3 | QA 流程；執行層僅 `FLOW-6.8` 引用 |
| W1–W3–W5 並行工單表 | W2 §9 | 專案編排，非每輪 MUST |
| W0 附錄 C 條目表 | W0 附錄 C | 索引見 `REF-9.6` |
| 實例路徑／venv／DB／env 鍵 | W5 | 憲法 §4；規則僅 FORBID + 錨點引用 |

---

## 七、營運抽測（建議，非本令阻塞項）

| 項 | 責任 | 說明 |
|----|------|------|
| 新 Agent 對話 Rules 面板 | 副官／接戰人 | 確認 `engineering-contract` 顯示 **Always applied** |
| 接戰後首輪 | 副官 | 起手式含「已讀合約／本規則」 |

結構要件已滿足；抽測未 PASS 不撤回本令，但須於 Progress 末尾記錄。

---

## 八、後續專案

| Phase | 內容 | 狀態 |
|-------|------|------|
| Phase 3 | 多智能體任務路由 | `HQ-P3-TASK-ROUTING` **Done**（見 Progress） |
| Phase 4 | 戰報／封存／回顧／自我進化 | `HQ-P4-OPS-CYCLE` **Done**（見 Progress） |
| 規則維護 | P2-M 與 W2 同步修訂 | 重大變更須尚書省裁決 + 指紋補登 |

---

## 九、接戰入口（副官）

1. P0 必讀仍以 `AGENTS.md` §初始化校準為準（憲法／合約／地圖／實例錨點）。  
2. **工程執行節奏**：以本令定稿之 `CURSOR_AGENT_RULES.md` 與 `.cursor/rules/engineering-contract.mdc` 為準；衝突依權威位階。  
3. 每輪收尾須附 Work Report（W2 附錄 A／P2-M `OUT-7.2`）。

**本令存檔**：`04_Workflows/project_status/HQ_PHASE2_FINALIZATION_ORDER.md`
