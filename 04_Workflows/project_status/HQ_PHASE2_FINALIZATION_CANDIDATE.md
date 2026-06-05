# Phase 2 定稿候選 — HQ-P2-RULES-FINALIZE

> **呈報**：尚書省  
> **執行**：大唐副官（HQ-P2-RULES-FINALIZE）  
> **日期**：2026-05-19  
> **前置**：Phase 1 定稿令（`HQ_PHASE1_FINALIZATION_ORDER.md`）；W4 盲測 **10/10**（`HQ-P1-W4-BLIND-10`）

---

## 一、裁決請求

請尚書省裁決下列項目是否升格為 **Phase 2 正式權威**：

| 代號 | 檔案 | 建議裁決 |
|------|------|----------|
| P2-M | `04_Workflows/CURSOR_AGENT_RULES.md` | **定稿**（執行母本，對齊 W2 定稿） |
| P2-C | `.cursor/rules/engineering-contract.mdc` | **定稿**（`alwaysApply: true`，82 規則段） |

**權威位階**（不變）：尚書省當次指令 ＞ 憲法（W1）＞ 合約（W2）＞ 本規則檔／`.mdc` ＞ 任務 `brief`／`notes`。

**不取代**：`HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`AGENTS.md` 接戰入口。

---

## 二、三方對照結論（W2 ↔ P2-M ↔ P2-C）

### 2.1 對齊矩陣

| 主題 | W2 `ENGINEERING_CONTRACT.md` | P2-M | P2-C | 對齊 |
|------|------------------------------|------|------|------|
| 四流派（§4.1–§4.4 + §4.5 閘門） | §4 | §3.1–§3.5 | §3 + GATE-3.5.1 | ✓ |
| 12-rule（§5） | 表格式 12 條 | §4 [RULE 1]–[12] | §4 RULE-1–12 | ✓ |
| 起手→實作→驗收→收尾（§6） | §6.1–§6.4 | §6 FLOW-6.1–6.4 | §6 FLOW-6.1–6.4 | ✓ |
| 單次 DoD（§7.1，含四流派） | 8 項 checklist | FLOW-6.5（本輪補第 8 項） | FLOW-6.5（本輪補） | ✓ |
| 暗部板塊 DoD（§7.2） | C10 | FLOW-6.6 | FLOW-6.6 | ✓ |
| 協調官 DoD（§7.4） | — | FLOW-6.7 | FLOW-6.7 | ✓ |
| 暗部協作順序（§7.5） | C16–C17 | FLOW-6.9（本輪新增） | FLOW-6.9（本輪新增） | ✓ |
| 審稿／W4／Phase 升格 | §7.3、§8 | FLOW-6.8、§10 | FLOW-6.8、§10 | ✓ |
| Work Report 模板 | 附錄 A | §7 OUT-7.2 全文 | OUT-7.2 引用母本／W2 附錄 A | ✓ |
| 文檔工單自檢（APP-DOC） | §10.3 七項 | 附錄要點 | APP-DOC 區塊 | ✓ |
| fallback／停工（§11） | §11.1–§11.2 | §8 | §8 | ✓ |
| dict 形狀（附錄 B） | 附錄 B | OUT-7.5 | OUT-7.5 | ✓ |

### 2.2 本輪修補（相對 2026-05-17 草案）

1. **FLOW-6.5**：補齊 W2 §7.1 第八項「四流派最低覆蓋」（對應 GATE-3.5.1／§4.5）。
2. **FLOW-6.9**：轉制 W2 §7.5 暗部建議順序（Infra → Data → RAG → Governance）與 Governance 欄位對齊責任。
3. **META-0.4**：移除違例範例中之磁碟路徑樣式字串，避免可移植審計誤判。

### 2.3 刻意分流（不視為缺口）

| 內容 | 保留於 W2 | 不寫入 P2-M／P2-C 原因 |
|------|-----------|-------------------------|
| W4 盲測 10 項量表全文 | §7.3 | QA 流程；執行層僅 FLOW-6.8 引用裁決 |
| W1–W3–W5 並行工單表 | §9 | 專案編排，非 Agent 每輪 MUST |
| W0 附錄 C 條目表 | 附錄 C | 索引見 REF-9.6；避免重複貼表 |
| 實例路徑／venv／DB／env 鍵 | W5 | 憲法 §4；規則僅 FORBID + 指向錨點 |

---

## 三、P2-M ↔ P2-C 一致性驗證

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| 規則段 ID 一一對應 | **PASS** | 82 個 `###` 段；母本條目 ID 與 `.mdc` 同名（RULE 1→RULE-1 等） |
| 四流派 MUST／FORBID 語意一致 | **PASS** | CD／SD／IN／DB／GATE 段對照 |
| 12-rule 全覆蓋 | **PASS** | RULE-1–12 |
| DoD 三層 + 四流派閘門 | **PASS** | FLOW-6.5–6.7、6.9 |
| Work Report 七節 | **PASS** | OUT-7.2；模板權威在 W2 附錄 A／P2-M §7 |
| 可移植：正文零絕對路徑 | **PASS** | 機掃 P2-M／P2-C 正文無 `D:\`、`C:\Users\` |
| `alwaysApply: true` | **PASS** | `.mdc` frontmatter |
| 檔頭 Phase 2／母本標識 | **PASS** | `.mdc` description + §10 PH-10.x |

**計分**：**8/8 PASS**（母本↔機器規則一致性）

---

## 四、APP-DOC 自檢（本輪修訂檔）

| # | 檢查項 | 結果 | 證據 |
|---|--------|------|------|
| 1 | 正文零本機絕對路徑 | **是** | P2-M／P2-C 正文無磁碟代號路徑 |
| 2 | 組織引用地圖、未複製全表 | **是** | REF-9.3 指向 `DEPARTMENT_MAP.md` |
| 3 | Cabin 僅角色／用途 | **是** | 未寫 venv 進入方式 |
| 4 | 禁區僅類型 | **是** | RULE-5、BAN-5.3 引用憲法 §7 |
| 5 | Pipeline 制度在可移植層 | **是** | 未寫 DB／env 實例 |
| 6 | 已對齊 W0／未與 Conditions／Progress／AGENTS 衝突 | **是** | 對照 W2 定稿與 Phase 1 令 |
| 7 | 未自標 v1.0 定稿號 | **是** | 本候選檔請求裁決，檔內無 worker 自封版本 |

---

## 五、交付路徑與變更摘要

### 5.1 檔案路徑

- `04_Workflows/CURSOR_AGENT_RULES.md`（修改）
- `.cursor/rules/engineering-contract.mdc`（修改）
- `04_Workflows/project_status/HQ_PHASE2_FINALIZATION_CANDIDATE.md`（新建，本檔）
- `04_Workflows/00_Agent_Work_Progress.md`（末尾追加 HQ-P2 工報）
- `04_Workflows/project_status/master_status.md`（末尾追加候選狀態）

### 5.2 變更摘要（每檔）

**`CURSOR_AGENT_RULES.md`**

1. FLOW-6.5 補齊四流派 DoD 項，與 W2 §7.1 八項一致。
2. 新增 FLOW-6.9，轉制 W2 §7.5 暗部協作順序與欄位對齊。
3. META-0.4 違例範例改為無磁碟樣式之表述。
4. 文末自檢表更新 DoD 覆蓋列。
5. 其餘 §0–§10、四流派、12-rule、Work Report、停工條款與 2026-05-17 母本一致，已對照 W2 定稿無結構性缺口。

**`engineering-contract.mdc`**

1. 與母本同步 FLOW-6.5、FLOW-6.9。
2. 規則段計數 **81 → 82**（新增 FLOW-6.9）。
3. `alwaysApply: true` 維持；檔頭 description 仍標母本 `CURSOR_AGENT_RULES.md`。

---

## 六、指紋與驗證（待執行／已執行）

| 項目 | 狀態 | 備註 |
|------|------|------|
| 指紋補登 `_register_fingerprints.py` | **Done** | 3 檔 `newly_inserted={raw_inbound:3}`，`registry_total_rows=36473`，`failures=0` |
| 新 Agent 對話 Rules 面板 | **建議人工抽測** | 確認 `engineering-contract` always applied |
| W2 原文 | **未改** | 本輪僅修 P2 層；W2 已為 Phase 1 定稿權威 |

---

## 七、建議尚書省裁決文案（候選）

若核准定稿，建議發布 **Phase 2 定稿令**，宣告：

1. `CURSOR_AGENT_RULES.md` 為 **Phase 2 執行母本**（對齊 `ENGINEERING_CONTRACT.md` 定稿）。
2. `.cursor/rules/engineering-contract.mdc` 為 **Cursor 強制執行規則**（`alwaysApply: true`）。
3. Phase 2 規則升格 **不等同** 暗部 DarkOps 解禁（維持 Phase 1 令 §五語義）。
4. 後續規則修訂須與 W2 同步審核；版本號由尚書省裁決。

**本候選檔存檔**：`04_Workflows/project_status/HQ_PHASE2_FINALIZATION_CANDIDATE.md`

---

## Work Report

**任務**：HQ-P2-RULES-FINALIZE — 合約↔母本↔.mdc 對齊與定稿候選  
**角色**：大唐副官  
**日期**：2026-05-19（本地）

### 1. 變更檔案

- **修改**：`04_Workflows/CURSOR_AGENT_RULES.md`
- **修改**：`.cursor/rules/engineering-contract.mdc`
- **新建**：`04_Workflows/project_status/HQ_PHASE2_FINALIZATION_CANDIDATE.md`
- **修改**：`04_Workflows/00_Agent_Work_Progress.md`（末尾）
- **修改**：`04_Workflows/project_status/master_status.md`（末尾）

### 2. 可執行 skeleton

- 無

### 3. placeholder（未完成）

- 尚書省正式 **Phase 2 定稿令**（待裁決）
- 新 Agent 對話 Rules 面板抽測（待人工）

### 4. 驗證證據

- 三方對照矩陣：§二（全項 ✓）
- P2-M↔P2-C：**8/8 PASS**（§三）
- APP-DOC 七項：**是**（§四）

### 5. 阻塞

- 無

### 6. 下一步建議

1. 尚書省審閱本候選檔並發布 Phase 2 定稿令或退回修補項。
2. 核准後執行指紋補登與新 Agent 對話 Rules 抽測。
3. 可開 `HQ-P3-TASK-ROUTING` 或 `HQ-P4-OPS-CYCLE`。

### 7. 憲法／合約

- override：無
- 留痕位置：`00_Agent_Work_Progress.md` 末尾 HQ-P2 節
